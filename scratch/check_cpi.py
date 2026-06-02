import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.database import SessionLocal

def main():
    db: Session = SessionLocal()
    try:
        # CPI
        query_cpi = text("SELECT kr_cpi, loaded_date FROM ml_gold_raw WHERE kr_cpi IS NOT NULL ORDER BY loaded_date DESC LIMIT 5")
        res_cpi = db.execute(query_cpi).fetchall()
        print("Non-null CPI:")
        for r in res_cpi:
            print(f"loaded_date: {r.loaded_date}, kr_cpi: {r.kr_cpi}")

        # KOSPI
        query_kospi = text("SELECT kospi200, loaded_date FROM ml_gold_raw WHERE kospi200 IS NOT NULL ORDER BY loaded_date DESC LIMIT 5")
        res_kospi = db.execute(query_kospi).fetchall()
        print("\nNon-null KOSPI:")
        for r in res_kospi:
            print(f"loaded_date: {r.loaded_date}, kospi200: {r.kospi200}")

        # SP500
        query_sp = text("SELECT sp500, loaded_date FROM ml_gold_raw WHERE sp500 IS NOT NULL ORDER BY loaded_date DESC LIMIT 5")
        res_sp = db.execute(query_sp).fetchall()
        print("\nNon-null SP500:")
        for r in res_sp:
            print(f"loaded_date: {r.loaded_date}, sp500: {r.sp500}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
