import sys
import os
import time
from sqlalchemy.orm import Session

# Add the parent directory (POOM-BACK) to python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.database import SessionLocal
from app.models.customer import Customer

def test_migration_and_onupdate():
    db: Session = SessionLocal()
    try:
        # 1. Fetch one customer to verify columns exist
        customer = db.query(Customer).first()
        if not customer:
            print("No customers found in database to test with.")
            return
        
        print("=== Step 1: Initial State ===")
        print(f"Customer c_id: {customer.c_id}")
        print(f"Name: {customer.name}")
        print(f"update_time: {customer.update_time} (Type: {type(customer.update_time)})")
        print(f"analysis_time: {customer.analysis_time} (Type: {type(customer.analysis_time)})")
        
        initial_update_time = customer.update_time
        
        # 2. Wait a brief moment and update a field to test onupdate
        print("\n=== Step 2: Modifying Customer ===")
        original_name = customer.name
        customer.name = original_name + " Temp"
        db.commit()
        db.refresh(customer)
        
        updated_update_time = customer.update_time
        print(f"New Name: {customer.name}")
        print(f"New update_time: {updated_update_time}")
        
        # Check if update_time has changed (since it was updated)
        if initial_update_time != updated_update_time:
            print("[SUCCESS] update_time has been successfully updated on modification!")
        else:
            print("[WARNING] update_time did not change. (It might be due to fast execution or DB driver caching, or onupdate was not triggered)")
            
        # 3. Rollback the name change to keep the DB clean
        print("\n=== Step 3: Reverting Name ===")
        customer.name = original_name
        db.commit()
        db.refresh(customer)
        print(f"Reverted Name: {customer.name}")
        print(f"Final update_time: {customer.update_time}")
        
    except Exception as e:
        print(f"[FAILURE] Error encountered: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_migration_and_onupdate()
