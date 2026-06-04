import sys
import os
from sqlalchemy import text

# Add the parent directory (POOM-BACK) to python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.database import engine

def migrate():
    alter_query = """
    ALTER TABLE CUSTOMER 
    ADD COLUMN update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    ADD COLUMN analysis_time DATETIME NULL;
    """
    with engine.begin() as conn:
        print("Applying migration to add datetime columns to CUSTOMER...")
        conn.execute(text(alter_query))
        print("Migration applied successfully!")

if __name__ == "__main__":
    migrate()
