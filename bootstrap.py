from sqlalchemy import create_engine, text

from db_config import get_database_url

engine = create_engine(get_database_url())

with engine.begin() as conn:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                features TEXT NOT NULL,
                predicted INTEGER NOT NULL
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS datasets (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                path TEXT NOT NULL
            )
            """
        )
    )

print("RDS schema initialized.")
