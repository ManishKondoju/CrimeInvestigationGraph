from neo4j import GraphDatabase
import config

class Database:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
    
    def close(self):
        self.driver.close()
    
    def query(self, cypher, params=None):
        with self.driver.session() as session:
            result = session.run(cypher, params or {})
            return [dict(record) for record in result]
    
    def clear_all(self):
        self.query("MATCH (n) DETACH DELETE n")
        print("🗑️  Database cleared")
