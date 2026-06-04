import sys
import os
from sqlalchemy.orm import Session

# Add the current directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.customer import Customer
from app.models.in_charge import InCharge

db: Session = SessionLocal()
try:
    print("--- IN_CHARGE ---")
    in_charges = db.query(InCharge).filter(InCharge.u_id == "user1").all()
    print(f"Total in-charges for user1: {len(in_charges)}")
    c_ids = [ic.c_id for ic in in_charges]
    print(f"c_ids: {c_ids}")
    
    print("\n--- CUSTOMERS ---")
    customers = db.query(Customer).filter(Customer.c_id.in_(c_ids)).all()
    print(f"Total customer records found for user1: {len(customers)}")
    for c in customers:
        print(f"ID: {c.c_id}, Name: {c.name}, Number: {c.number}")
finally:
    db.close()
