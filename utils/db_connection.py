# utils/db_connection.py
from sqlalchemy import create_engine, text

# SQLite database file will be created in project folder
DATABASE_URL = "sqlite:///cricket.db"

def get_engine(echo: bool = False):
    return create_engine(DATABASE_URL, echo=echo, future=True)

def test_connection():
    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    except Exception as e:
        print("❌ Database connection failed:", e)

if __name__ == "__main__":
    test_connection()