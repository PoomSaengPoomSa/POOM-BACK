import sys
import os
from sqlalchemy import text

# Add the current directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal

def apply_indexes():
    db = SessionLocal()
    
    indexes = [
        ("economic_indicator_history", "idx_eih_type_recorded", "economic_indicator_history (type, recorded_at DESC)"),
        ("economic_indicator_prediction", "idx_eip_type_date", "economic_indicator_prediction (type, predicted_date ASC)"),
        ("trend_news", "idx_tn_cat_pub", "trend_news (category, published_at DESC)"),
        ("trend_news", "idx_tn_pub", "trend_news (published_at DESC)"),
        ("trend_news", "idx_tn_url", "trend_news (origin_url)"),
        ("pb_schedule", "idx_sched_u_cat_exec", "pb_schedule (u_id, category, execution_date DESC)"),
        ("pb_schedule", "idx_sched_c_cat_exec", "pb_schedule (c_id, category, execution_date DESC)"),
        ("in_charge", "idx_ic_cid", "in_charge (c_id)"),
        ("handover", "idx_ho_from_status", "handover (from_u_id, status)")
    ]
    
    print("--- Applying database indexes ---")
    for table, index_name, definition in indexes:
        sql = f"CREATE INDEX {index_name} ON {definition}"
        try:
            db.execute(text(sql))
            db.commit()
            print(f"[SUCCESS] Index '{index_name}' applied to table '{table}'.")
        except Exception as e:
            db.rollback()
            err_str = str(e)
            if "Duplicate key name" in err_str or "already exists" in err_str:
                print(f"[INFO] Index '{index_name}' already exists on table '{table}'. Skipping.")
            else:
                print(f"[ERROR] Error applying index '{index_name}' on table '{table}': {e}")
                
    db.close()

if __name__ == "__main__":
    apply_indexes()
