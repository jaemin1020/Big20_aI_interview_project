#!/usr/bin/env python3
"""Check PostgreSQL version using psycopg2.
This script connects to the database using the DATABASE_URL environment variable
or falls back to a default local connection string, then prints the server version.
"""
import os
import sys

try:
    import psycopg2
except ImportError:
    print("psycopg2 is not installed. Install it with 'pip install psycopg2-binary'.")
    sys.exit(1)

# Retrieve connection string from environment or use a default.
conn_str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234@localhost:5432/interview_db",
)

def get_pg_version(conn_str: str) -> str:
    """Return PostgreSQL server version string."""
    try:
        with psycopg2.connect(conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                return version
    except Exception as e:
        return f"Error connecting to PostgreSQL: {e}"

if __name__ == "__main__":
    print("Connecting to PostgreSQL...")
    version = get_pg_version(conn_str)
    print(f"PostgreSQL version: {version}")
