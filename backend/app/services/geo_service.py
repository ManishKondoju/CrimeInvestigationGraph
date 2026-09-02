# backend/app/services/geo_service.py
#
# Parameterized rewrite of geo_mapping.py's get_crime_locations(), which
# built its WHERE clauses via Python f-string interpolation of user-facing
# filter values (crime_types, dates, districts) straight into Cypher text -
# a real injection risk. Rewritten here with $params. predict_hotspots()
# is pure pandas/sklearn with no Cypher involved, so it's reused as-is from
# CrimeGeographicMapper rather than duplicated.

import pandas as pd

CHICAGO_BOUNDS = {"lat_min": 41.6, "lat_max": 42.1, "lon_min": -87.95, "lon_max": -87.5}


def get_crime_locations(db, crime_types=None, start_date=None, end_date=None, districts=None, limit=5000):
    query = """
    MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
    WHERE l.latitude IS NOT NULL AND l.longitude IS NOT NULL
    """
    params = {}

    if crime_types:
        query += " AND c.type IN $crime_types"
        params["crime_types"] = crime_types
    if start_date:
        query += " AND c.date >= $start_date"
        params["start_date"] = start_date
    if end_date:
        query += " AND c.date <= $end_date"
        params["end_date"] = end_date
    if districts:
        query += " AND l.district IN $districts"
        params["districts"] = districts

    query += """
    RETURN
        c.id as case_id,
        c.type as crime_type,
        c.date as date,
        c.severity as severity,
        c.status as status,
        c.arrest_made as arrest_made,
        l.latitude as latitude,
        l.longitude as longitude,
        l.name as location_name,
        l.district as district
    ORDER BY c.date DESC
    LIMIT $limit
    """
    params["limit"] = limit

    records = db.query(query, params)
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])
    df = df[
        (df["latitude"] >= CHICAGO_BOUNDS["lat_min"])
        & (df["latitude"] <= CHICAGO_BOUNDS["lat_max"])
        & (df["longitude"] >= CHICAGO_BOUNDS["lon_min"])
        & (df["longitude"] <= CHICAGO_BOUNDS["lon_max"])
    ]
    return df


def get_crime_types(db):
    return [r["type"] for r in db.query("MATCH (c:Crime) RETURN DISTINCT c.type as type ORDER BY type")]


def get_districts(db):
    return [
        r["district"]
        for r in db.query(
            "MATCH (l:Location) WHERE l.district IS NOT NULL RETURN DISTINCT l.district as district ORDER BY district"
        )
    ]


def get_all_locations(db):
    return db.query(
        """
        MATCH (l:Location)
        WHERE l.latitude IS NOT NULL AND l.longitude IS NOT NULL
        RETURN l.latitude as lat, l.longitude as lon, l.name as name,
               l.district as district, l.source as source
        """
    )
