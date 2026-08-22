import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        connection = oracledb.connect(
            user=os.getenv("ORACLE_USER"),
            password=os.getenv("ORACLE_PASSWORD"),
            dsn=os.getenv("ORACLE_DSN")
        )
        return connection
    except oracledb.Error as e:
        print(f"CRITICAL: Could not connect to Oracle. Error: {e}")
        return None