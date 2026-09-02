# backend/app/services/timeline_service.py
#
# Parameterized rewrite of timeline_viz.py's get_crime_timeline_data(),
# which built WHERE clauses via f-string interpolation (same injection
# pattern as geo_mapping.py). hour/day_of_week/week/month/date_only were
# already derived client-side in pandas in the original - kept here since
# that's the natural place for it, now just running once in the backend
# instead of per-Streamlit-rerun. get_timeline_summary() moves the
# aggregate computations the frontend needs (peak hour, busiest day,
# weekly trend, heatmap matrix) server-side too, so the new frontend
# doesn't need a pandas-equivalent in JS.

import pandas as pd


def get_crime_timeline_data(db, start_date=None, end_date=None, crime_types=None, locations=None, severity=None):
    # NOTE: filters must be applied in a WHERE that comes BEFORE the OPTIONAL
    # MATCHes below, not after. Cypher treats a WHERE immediately following
    # an OPTIONAL MATCH as part of that optional pattern's predicate, not a
    # filter over the whole row - since the match is optional, a row that
    # fails the predicate is kept anyway (with the optional fields null)
    # instead of being dropped. The original Streamlit code had this exact
    # bug (WHERE placed after both OPTIONAL MATCHes), which silently made
    # every timeline filter a no-op. Fixed here since the query has to be
    # rewritten for parameterization anyway.
    query = """
    MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
    WHERE 1=1
    """
    params = {}

    if start_date:
        query += " AND c.date >= date($start_date)"
        params["start_date"] = start_date
    if end_date:
        query += " AND c.date <= date($end_date)"
        params["end_date"] = end_date
    if crime_types:
        query += " AND c.type IN $crime_types"
        params["crime_types"] = crime_types
    if locations:
        query += " AND l.name IN $locations"
        params["locations"] = locations
    if severity:
        query += " AND c.severity IN $severity"
        params["severity"] = severity

    query += """
    OPTIONAL MATCH (c)<-[:PARTY_TO]-(p:Person)
    OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
    RETURN
        c.id as crime_id,
        c.type as crime_type,
        c.date as date,
        c.time as time,
        c.severity as severity,
        c.status as status,
        l.name as location,
        collect(DISTINCT p.name) as suspects,
        collect(DISTINCT o.name) as organizations
    ORDER BY c.date, c.time
    """

    results = db.query(query, params)
    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    df["datetime"] = pd.to_datetime(df["date"].astype(str) + " " + df["time"].astype(str), errors="coerce")
    df["hour"] = df["datetime"].dt.hour
    df["day_of_week"] = df["datetime"].dt.day_name()
    df["week"] = df["datetime"].dt.isocalendar().week
    df["month"] = df["datetime"].dt.month
    df["date_only"] = df["datetime"].dt.date.astype(str)
    return df


def get_crime_types(db):
    return [r["type"] for r in db.query("MATCH (c:Crime) RETURN DISTINCT c.type as type ORDER BY type")]


def get_locations(db):
    return [r["name"] for r in db.query("MATCH (l:Location) RETURN DISTINCT l.name as name ORDER BY name LIMIT 50")]


def get_timeline_summary(db, start_date=None, end_date=None, crime_types=None, locations=None, severity=None):
    df = get_crime_timeline_data(db, start_date, end_date, crime_types, locations, severity)
    if df.empty:
        return {"empty": True}

    peak_hour = int(df["hour"].mode()[0])
    peak_hour_count = int((df["hour"] == peak_hour).sum())
    peak_day = str(df["day_of_week"].mode()[0])
    peak_day_count = int((df["day_of_week"] == peak_day).sum())

    date_range_days = int((df["datetime"].max() - df["datetime"].min()).days)
    total = len(df)
    avg_daily = total / date_range_days if date_range_days > 0 else 0.0

    critical = int((df["severity"] == "critical").sum())
    solved = int((df["status"] == "solved").sum())
    active = int((df["status"] == "active").sum())

    # hour x day-of-week matrix for the heatmap
    heatmap = (
        df.groupby(["day_of_week", "hour"]).size().reset_index(name="count").to_dict(orient="records")
    )

    hourly = df.groupby("hour").size()
    dangerous_hours = hourly[hourly >= hourly.quantile(0.75)].index.tolist()

    weekly = df.groupby("week").size().sort_index()
    weekly_series = [{"week": int(w), "crimes": int(c)} for w, c in weekly.items()]
    first_half = weekly.iloc[: len(weekly) // 2].mean() if len(weekly) > 1 else weekly.mean()
    second_half = weekly.iloc[len(weekly) // 2 :].mean() if len(weekly) > 1 else weekly.mean()
    trend_pct = ((second_half - first_half) / first_half * 100) if first_half else 0.0

    severity_breakdown = df["severity"].value_counts().reset_index()
    severity_breakdown.columns = ["severity", "count"]

    crime_type_breakdown = df["crime_type"].value_counts().head(10).reset_index()
    crime_type_breakdown.columns = ["crime_type", "count"]

    return {
        "empty": False,
        "peak_hour": peak_hour,
        "peak_hour_count": peak_hour_count,
        "peak_day": peak_day,
        "peak_day_count": peak_day_count,
        "date_range_days": date_range_days,
        "total": total,
        "avg_daily": avg_daily,
        "critical_count": critical,
        "critical_pct": (critical / total * 100) if total else 0.0,
        "solved_count": solved,
        "solved_pct": (solved / total * 100) if total else 0.0,
        "active_count": active,
        "active_pct": (active / total * 100) if total else 0.0,
        "heatmap": heatmap,
        "dangerous_hours": dangerous_hours,
        "weekly": weekly_series,
        "weekly_avg": float(weekly.mean()) if len(weekly) else 0.0,
        "weekly_max_week": int(weekly.idxmax()) if len(weekly) else None,
        "weekly_max_crimes": int(weekly.max()) if len(weekly) else 0,
        "weekly_min_week": int(weekly.idxmin()) if len(weekly) else None,
        "weekly_min_crimes": int(weekly.min()) if len(weekly) else 0,
        "weekly_trend_pct": trend_pct,
        "severity_breakdown": severity_breakdown.to_dict(orient="records"),
        "crime_type_breakdown": crime_type_breakdown.to_dict(orient="records"),
    }
