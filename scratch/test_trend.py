import sys
import os
import asyncio
from sqlalchemy.orm import Session

# Add the parent directory to python path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.services.trend import get_trend_dashboard

async def main():
    db: Session = SessionLocal()
    try:
        print("Fetching trend dashboard data...")
        res = await get_trend_dashboard(current_user=None, db=db)
        print("SUCCESS!")
        print("realtimeTrends:")
        for trend in res.get("realtimeTrends", []):
            print(trend)
        print("indicators:")
        print(res.get("indicators"))
    except Exception as e:
        print("FAILED with error:", e)
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
