import sys
import os
from sqlalchemy.orm import Session, joinedload

# Add the parent directory (POOM-BACK) to python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.database import SessionLocal
from app.models.customer import Customer, CustomerRelationship

def test_relationship_query():
    db: Session = SessionLocal()
    try:
        # Fetch customer 1001 (김지훈) and eager load relationships
        customer = (
            db.query(Customer)
            .options(joinedload(Customer.relationships))
            .filter(Customer.c_id == 1001)
            .first()
        )
        
        if not customer:
            print("Customer 1001 not found.")
            return
            
        print("=== Customer Relationship Validation ===")
        print(f"Customer Name: {customer.name} (c_id: {customer.c_id})")
        print(f"Total relationships found: {len(customer.relationships)}")
        
        for idx, r in enumerate(customer.relationships, 1):
            print(f"\n[{idx}] Relation: {r.relationship_}")
            print(f"    Information: {r.information}")
            
            # Verify old fields do not exist on model instance
            has_birthday = hasattr(r, "birthday")
            has_job = hasattr(r, "job")
            has_spouse = hasattr(r, "is_spouse")
            
            if not has_birthday and not has_job and not has_spouse:
                print("    [SUCCESS] Old columns (birthday, job, is_spouse) are completely absent from the model!")
            else:
                print("    [WARNING] Some old columns still exist on the model attribute list!")
                
    except Exception as e:
        print(f"[FAILURE] Error encountered during validation: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_relationship_query()
