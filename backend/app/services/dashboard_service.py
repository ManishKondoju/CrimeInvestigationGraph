# backend/app/services/dashboard_service.py
#
# Extracted from enhanced_dashboard.py's ~30 inline db.query() calls into
# named functions grouped by the 6 aggregate endpoints in routers/dashboard.py.
# Cypher text is copied verbatim from enhanced_dashboard.py - no query logic
# changed, this is a straight port (dashboard filters remain decorative per
# the confirmed plan decision; not wired up here).


def get_kpis(db):
    total_crimes = db.query("MATCH (c:Crime) RETURN count(c) as n")[0]["n"]
    open_cases = db.query(
        "MATCH (c:Crime) WHERE c.status IN ['open','under investigation'] RETURN count(c) as n"
    )[0]["n"]
    critical_crimes = db.query(
        "MATCH (c:Crime) WHERE c.severity IN ['critical','high','severe'] RETURN count(c) as n"
    )[0]["n"]
    solve_rate = db.query(
        """
        MATCH (c:Crime)
        WITH count(c) as total,
             count(CASE WHEN c.status IN ['solved','closed'] THEN 1 END) as solved
        RETURN (solved * 100.0 / total) as rate
        """
    )[0]["rate"]
    districts = [
        r["district"]
        for r in db.query(
            "MATCH (l:Location) WHERE l.district IS NOT NULL RETURN DISTINCT l.district as district ORDER BY district"
        )
    ]
    total_persons = db.query("MATCH (p:Person) RETURN count(p) as count")[0]["count"]
    total_orgs = db.query("MATCH (o:Organization) RETURN count(o) as count")[0]["count"]
    total_evidence = db.query("MATCH (e:Evidence) RETURN count(e) as count")[0]["count"]
    total_weapons = db.query("MATCH (w:Weapon) RETURN count(w) as count")[0]["count"]

    high_risk_suspects = db.query(
        """
        MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
        WITH p, count(c) as crimes
        WHERE crimes >= 3
        RETURN count(p) as count
        """
    )[0]["count"]
    active_gangs = db.query(
        """
        MATCH (o:Organization)<-[:MEMBER_OF]-(p:Person)-[:PARTY_TO]->(c:Crime)
        WHERE c.date >= '2024-06-01'
        RETURN count(DISTINCT o) as count
        """
    )[0]["count"]
    critical_evidence = db.query(
        "MATCH (e:Evidence) WHERE e.significance IN ['critical','high'] RETURN count(e) as count"
    )[0]["count"]
    weapons_recovered = db.query(
        "MATCH (w:Weapon) WHERE w.recovered = true RETURN count(w) as count"
    )[0]["count"]
    repeat_offenders = db.query(
        """
        MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
        WITH p, count(c) as crimes
        WHERE crimes >= 3
        RETURN count(p) as total, max(crimes) as max_crimes
        """
    )[0]
    armed_gang_members = db.query(
        """
        MATCH (p:Person)-[:MEMBER_OF]->(o:Organization)
        MATCH (p)-[:OWNS]->(w:Weapon)
        RETURN count(DISTINCT p) as total, count(DISTINCT o) as gangs, count(DISTINCT w) as weapons
        """
    )[0]
    network_hubs = db.query(
        """
        MATCH (p:Person)-[:KNOWS]-(other:Person)
        WITH p, count(DISTINCT other) as connections
        WHERE connections >= 6
        RETURN count(p) as total, max(connections) as max_connections
        """
    )[0]

    return {
        "total_crimes": total_crimes,
        "open_cases": open_cases,
        "critical_crimes": critical_crimes,
        "solve_rate": solve_rate,
        "districts": districts,
        "total_persons": total_persons,
        "total_organizations": total_orgs,
        "total_evidence": total_evidence,
        "total_weapons": total_weapons,
        "insights": {
            "high_risk_suspects": high_risk_suspects,
            "active_gangs": active_gangs,
            "critical_evidence": critical_evidence,
            "weapons_recovered": weapons_recovered,
            "repeat_offenders": repeat_offenders,
            "armed_gang_members": armed_gang_members,
            "network_hubs": network_hubs,
        },
    }


def get_trends(db):
    monthly_trends = db.query(
        """
        MATCH (c:Crime)
        WHERE c.date IS NOT NULL AND c.date >= '2024-01-01'
        WITH substring(c.date, 0, 7) as year_month,
             count(c) as total_crimes,
             count(CASE WHEN c.severity IN ['high','critical','severe'] THEN 1 END) as severe_crimes,
             count(CASE WHEN c.status IN ['solved','closed'] THEN 1 END) as solved_crimes
        RETURN year_month, total_crimes, severe_crimes, solved_crimes
        ORDER BY year_month
        """
    )
    pipeline = db.query(
        """
        MATCH (c:Crime)
        WITH count(c) as total,
             count(CASE WHEN c.status = 'open' THEN 1 END) as open,
             count(CASE WHEN c.status = 'under investigation' THEN 1 END) as investigating,
             count(CASE WHEN c.status IN ['solved','closed'] THEN 1 END) as solved,
             count(CASE WHEN c.status = 'cold case' THEN 1 END) as cold
        RETURN total, open, investigating, solved, cold
        """
    )[0]

    return {"monthly_trends": monthly_trends, "pipeline": pipeline}


def get_gangs(db):
    gangs = db.query(
        """
        MATCH (o:Organization)<-[:MEMBER_OF]-(p:Person)
        OPTIONAL MATCH (p)-[:PARTY_TO]->(c:Crime)
        OPTIONAL MATCH (p)-[:OWNS]->(w:Weapon)
        WITH o, count(DISTINCT p) as members, count(DISTINCT c) as crimes,
             count(DISTINCT w) as weapons,
             count(DISTINCT CASE WHEN c.severity IN ['high','critical','severe'] THEN c END) as severe_crimes
        RETURN o.name as gang, o.territory as territory, o.type as type,
               members, crimes, weapons, severe_crimes,
               CASE WHEN crimes>=45 AND weapons>=8 THEN 5
                    WHEN crimes>=35 AND weapons>=5 THEN 4
                    WHEN crimes>=25 THEN 3
                    WHEN crimes>=15 THEN 2
                    ELSE 1 END as threat_level
        ORDER BY threat_level DESC, crimes DESC
        """
    )
    return {"gangs": gangs}


def get_breakdowns(db):
    crime_types = db.query(
        "MATCH (c:Crime) RETURN c.type as type, count(c) as count ORDER BY count DESC LIMIT 8"
    )
    severity = db.query(
        """
        MATCH (c:Crime) RETURN c.severity as severity, count(c) as count
        ORDER BY
            CASE c.severity
                WHEN 'critical' THEN 1
                WHEN 'severe' THEN 2
                WHEN 'high' THEN 2
                WHEN 'moderate' THEN 3
                WHEN 'medium' THEN 3
                ELSE 4
            END
        """
    )
    districts = db.query(
        """
        MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
        WHERE l.district IS NOT NULL
        RETURN l.district as district, count(c) as crimes
        ORDER BY crimes DESC LIMIT 8
        """
    )
    weapon_status = db.query(
        """
        MATCH (w:Weapon)
        WITH w.type as type, count(w) as total,
             count(CASE WHEN w.recovered = true THEN 1 END) as recovered
        RETURN type, total, recovered, (total - recovered) as at_large
        ORDER BY total DESC
        """
    )
    evidence_significance = db.query(
        """
        MATCH (e:Evidence)
        WITH e.significance as significance, count(e) as total,
             count(CASE WHEN e.verified = true THEN 1 END) as verified
        RETURN significance, total, verified
        ORDER BY CASE significance WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END
        """
    )

    return {
        "crime_types": crime_types,
        "severity": severity,
        "districts": districts,
        "weapon_status": weapon_status,
        "evidence_significance": evidence_significance,
    }


def get_operations(db):
    investigators = db.query(
        """
        MATCH (i:Investigator)<-[:INVESTIGATED_BY]-(c:Crime)
        WITH i, count(c) as total_cases,
             count(CASE WHEN c.status IN ['solved','closed'] THEN 1 END) as solved,
             count(CASE WHEN c.status IN ['open','under investigation'] THEN 1 END) as active
        RETURN i.name as investigator, i.department as department, total_cases, solved, active,
               CASE WHEN total_cases > 0 THEN (solved * 100.0 / total_cases) ELSE 0 END as solve_rate
        ORDER BY solve_rate DESC, solved DESC
        """
    )
    district_heatmap = db.query(
        """
        MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
        WHERE l.district IS NOT NULL
        WITH l.district as district, count(c) as total,
             count(CASE WHEN c.severity IN ['high','critical','severe'] THEN 1 END) as severe
        RETURN district, total, severe, (total-severe) as other
        ORDER BY total DESC LIMIT 12
        """
    )
    hotspots = db.query(
        """
        MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
        RETURN l.name as location, l.district as district, count(c) as crimes,
               count(CASE WHEN c.severity IN ['high','critical','severe'] THEN 1 END) as severe
        ORDER BY crimes DESC LIMIT 10
        """
    )

    return {
        "investigators": investigators,
        "district_heatmap": district_heatmap,
        "hotspots": hotspots,
    }


def get_activity(db):
    recent_incidents = db.query(
        """
        MATCH (c:Crime)
        OPTIONAL MATCH (c)-[:OCCURRED_AT]->(l:Location)
        OPTIONAL MATCH (p:Person)-[:PARTY_TO]->(c)
        RETURN c.id as id, c.type as type, c.date as date, c.time as time,
               c.severity as severity, c.status as status,
               COALESCE(l.name,'Unknown Location') as location,
               COALESCE(l.district,'N/A') as district,
               collect(DISTINCT p.name)[0] as suspect
        ORDER BY c.date DESC, c.time DESC LIMIT 8
        """
    )
    peak_hour_rows = db.query(
        """
        MATCH (c:Crime) WHERE c.time IS NOT NULL
        WITH substring(c.time, 0, 2) as hour, count(c) as crimes
        RETURN hour, crimes ORDER BY crimes DESC LIMIT 1
        """
    )
    priority_targets = db.query(
        """
        MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
        WITH p, count(c) as crimes
        WHERE crimes >= 2
        OPTIONAL MATCH (p)-[:OWNS]->(w:Weapon)
        OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
        RETURN p.name as name, p.age as age, crimes, count(DISTINCT w) as weapons,
               COALESCE(o.name,'Independent') as gang,
               CASE WHEN crimes>=5 AND count(w)>0 THEN '🔴 CRITICAL'
                    WHEN crimes>=4 THEN '🟠 HIGH'
                    WHEN crimes>=2 THEN '🟡 MEDIUM'
                    ELSE '🟢 LOW' END as priority
        ORDER BY crimes DESC, weapons DESC LIMIT 10
        """
    )
    data_quality = {
        "orphaned_crimes": db.query(
            "MATCH (c:Crime) WHERE NOT EXISTS((c)-[:OCCURRED_AT]->()) RETURN count(c) as count"
        )[0]["count"],
        "no_evidence_crimes": db.query(
            "MATCH (c:Crime) WHERE NOT EXISTS((c)-[:HAS_EVIDENCE]->()) RETURN count(c) as count"
        )[0]["count"],
        "unsolved_severe": db.query(
            """
            MATCH (c:Crime) WHERE c.severity IN ['high','critical','severe']
              AND NOT c.status IN ['solved','closed']
            RETURN count(c) as count
            """
        )[0]["count"],
        "independent_suspects": db.query(
            """
            MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
            WHERE NOT EXISTS((p)-[:MEMBER_OF]->())
            WITH DISTINCT p RETURN count(p) as count
            """
        )[0]["count"],
    }

    return {
        "recent_incidents": recent_incidents,
        "peak_hour": peak_hour_rows[0]["hour"] if peak_hour_rows else None,
        "priority_targets": priority_targets,
        "data_quality": data_quality,
    }
