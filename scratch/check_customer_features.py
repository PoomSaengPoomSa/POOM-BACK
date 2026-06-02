import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.database import SessionLocal

def main():
    db: Session = SessionLocal()
    try:
        query = text("SELECT c_id, name, features, llm_insight FROM customer LIMIT 10")
        res = db.execute(query).fetchall()
        print("Customer features & insights:")
        for r in res:
            print(f"ID: {r.c_id}, Name: {r.name}, Features: {r.features}, LLM Insight: {r.llm_insight}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
