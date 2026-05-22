import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.schedule import Schedule

db = SessionLocal()
try:
    schedules = db.query(Schedule).all()
    print(f"Total schedules in DB: {len(schedules)}")
    for s in schedules:
        print(f"ID: {s.s_id}, Title: {s.title}, Start: {s.execution_date} (tz: {s.execution_date.tzinfo}), End: {s.end_datetime} (tz: {s.end_datetime.tzinfo if s.end_datetime else None})")
finally:
    db.close()
