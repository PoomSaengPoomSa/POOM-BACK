import sys
import os
from sqlalchemy import text

# Add the parent directory (POOM-BACK) to python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.database import engine

def update_analysis_time():
    update_query = "UPDATE CUSTOMER SET analysis_time = NOW();"
    with engine.begin() as conn:
        print("Updating analysis_time to current timestamp for all customers...")
        result = conn.execute(text(update_query))
        print(f"Update completed! Rows affected: {result.rowcount}")

if __name__ == "__main__":
    update_analysis_time()
