import time
import socket
import httpx
import asyncio

async def test_conn():
    print("--- DNS and Socket Latency Test ---")
    
    # 1. Test DNS resolve & ping-like socket connect to DB_HOST (118.67.131.22)
    start = time.time()
    try:
        db_ip = socket.gethostbyname("118.67.131.22")
        print(f"DB Host IP resolved: {db_ip} in {(time.time() - start)*1000:.2f} ms")
    except Exception as e:
        print(f"DB Host DNS failed: {e}")
        
    start = time.time()
    try:
        s = socket.create_connection(("118.67.131.22", 3306), timeout=3.0)
        s.close()
        print(f"DB Port 3306 Connection success in {(time.time() - start)*1000:.2f} ms")
    except Exception as e:
        print(f"DB Port 3306 Connection failed: {e}")
        
    # 2. Test DNS resolve & ping-like socket connect to ES_HOST (team1elk.ap.loclx.io)
    start = time.time()
    try:
        es_ip = socket.gethostbyname("team1elk.ap.loclx.io")
        print(f"ES Host IP resolved: {es_ip} in {(time.time() - start)*1000:.2f} ms")
    except Exception as e:
        print(f"ES Host DNS failed: {e}")
        
    start = time.time()
    try:
        s = socket.create_connection(("team1elk.ap.loclx.io", 80), timeout=3.0)
        s.close()
        print(f"ES Port 80 Connection success in {(time.time() - start)*1000:.2f} ms")
    except Exception as e:
        print(f"ES Port 80 Connection failed: {e}")
        
    # 3. Test HTTP request speed
    print("\n--- HTTP Request Latency Test ---")
    async with httpx.AsyncClient(timeout=5.0) as client:
        for i in range(3):
            start = time.time()
            try:
                resp = await client.get("http://team1elk.ap.loclx.io/")
                print(f"ES HTTP request {i+1} status={resp.status_code} in {(time.time() - start)*1000:.2f} ms")
            except Exception as e:
                print(f"ES HTTP request {i+1} failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_conn())
