import time
import httpx
import asyncio
from sqlalchemy import text
import sys
import os

# Add the current directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.config import get_settings

settings = get_settings()
ES_HOST = settings.ES_HOST

async def profile_trend_dashboard_details():
    print("--- Profiling get_trend_dashboard Details ---")
    db = SessionLocal()
    
    # 1. Measure Elasticsearch sequential posts
    start = time.time()
    async with httpx.AsyncClient(timeout=3.0) as client:
        t0 = time.time()
        r1 = await client.post(f"{ES_HOST}/sbs_news/_search", json={"query": {"term": {"category": "경제"}}, "size": 5})
        print(f"ES Econ News took: {(time.time() - t0)*1000:.2f} ms")
        
        t0 = time.time()
        r2 = await client.post(f"{ES_HOST}/sbs_news/_search", json={"query": {"term": {"category": "정치"}}, "size": 5})
        print(f"ES Pol News took: {(time.time() - t0)*1000:.2f} ms")
        
        t0 = time.time()
        r3 = await client.post(f"{ES_HOST}/sbs_news/_search", json={"query": {"term": {"category": "머그"}}, "size": 5})
        print(f"ES Mug News took: {(time.time() - t0)*1000:.2f} ms")
    print(f"Total ES sequential requests took: {(time.time() - start)*1000:.2f} ms")
    
    # 2. Measure Elasticsearch parallel posts (asyncio.gather)
    start = time.time()
    async with httpx.AsyncClient(timeout=3.0) as client:
        res = await asyncio.gather(
            client.post(f"{ES_HOST}/sbs_news/_search", json={"query": {"term": {"category": "경제"}}, "size": 5}),
            client.post(f"{ES_HOST}/sbs_news/_search", json={"query": {"term": {"category": "정치"}}, "size": 5}),
            client.post(f"{ES_HOST}/sbs_news/_search", json={"query": {"term": {"category": "머그"}}, "size": 5})
        )
    print(f"Total ES parallel (gather) requests took: {(time.time() - start)*1000:.2f} ms")

    # 3. Measure DB queries
    start = time.time()
    t0 = time.time()
    db.execute(text("SELECT value FROM economic_indicator_history WHERE type = 'gold' ORDER BY recorded_at DESC LIMIT 2")).fetchall()
    print(f"DB Query 1 (gold hist) took: {(time.time() - t0)*1000:.2f} ms")
    
    t0 = time.time()
    db.execute(text("SELECT prob_rise, prob_fall FROM gold_predictions ORDER BY created_at DESC LIMIT 1")).fetchone()
    print(f"DB Query 2 (gold pred) took: {(time.time() - t0)*1000:.2f} ms")
    
    t0 = time.time()
    db.execute(text("SELECT house_price_idx FROM ml_realestate_preprocessed ORDER BY date_ym DESC LIMIT 2")).fetchall()
    print(f"DB Query 3 (re hist) took: {(time.time() - t0)*1000:.2f} ms")
    
    t0 = time.time()
    db.execute(text("SELECT predicted_value, predicted_index FROM realestate_predictions ORDER BY created_at DESC LIMIT 1")).fetchone()
    print(f"DB Query 4 (re pred) took: {(time.time() - t0)*1000:.2f} ms")
    
    t0 = time.time()
    db.execute(text("SELECT value FROM economic_indicator_history WHERE type = 'base_rate' ORDER BY recorded_at DESC LIMIT 2")).fetchall()
    print(f"DB Query 5 (br hist) took: {(time.time() - t0)*1000:.2f} ms")
    
    t0 = time.time()
    db.execute(text("SELECT prob_cut, prob_freeze, prob_hike FROM baserate_predictions ORDER BY created_at DESC LIMIT 1")).fetchone()
    print(f"DB Query 6 (br pred) took: {(time.time() - t0)*1000:.2f} ms")
    print(f"Total DB queries took: {(time.time() - start)*1000:.2f} ms")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(profile_trend_dashboard_details())
