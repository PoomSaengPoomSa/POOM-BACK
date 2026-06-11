import sys
import os
import time
import asyncio
from sqlalchemy.orm import Session

# Add the current directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.services.trend import get_trend_dashboard, get_news_list
from app.services.customer import get_customers, get_customer_memos, get_visit_statistics
from app.services.admin import get_permissions, get_employee_customers, get_employee_usage

# Mock user for testing
class MockUser:
    def __init__(self, id, role):
        self.id = id
        self.role = role

async def profile_function(name, func, *args, **kwargs):
    start = time.time()
    if asyncio.iscoroutinefunction(func):
        res = await func(*args, **kwargs)
    else:
        res = func(*args, **kwargs)
    elapsed = time.time() - start
    print(f"[TIME] {name:50s} : {elapsed*1000:8.2f} ms")
    return res

async def main():
    print("=================== PROFILING DB QUERIES & SERVICES ===================")
    db = SessionLocal()
    mock_user = MockUser("pb_b1_1", "user")
    mock_admin = MockUser("admin1", "admin")
    
    try:
        # Profile Trend services
        await profile_function("get_trend_dashboard", get_trend_dashboard, mock_user, db)
        await profile_function("get_news_list (all)", get_news_list, None, None, 1, 10, None, None, None, mock_user, db)
        
        # Profile Customer services
        await profile_function("get_customers (all)", get_customers, "all", 1, 30, mock_user, db)
        await profile_function("get_customers (today)", get_customers, "today", 1, 30, mock_user, db)
        
        # Let's pick a valid customer ID (c_id = 1)
        await profile_function("get_customer_memos", get_customer_memos, 1, None, 10, mock_user, db)
        await profile_function("get_visit_statistics", get_visit_statistics, 1, mock_user, db)
        
        # Profile Admin services
        await profile_function("get_permissions", get_permissions, None, None, db)
        await profile_function("get_employee_customers", get_employee_customers, "pb_b1_1", db)
        await profile_function("get_employee_usage", get_employee_usage, "month", db)
        
    except Exception as e:
        print(f"[ERROR] Error during profiling: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
