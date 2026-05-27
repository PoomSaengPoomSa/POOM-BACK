from contextlib import asynccontextmanager
import logging
import time
import asyncio
import httpx
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, admin, schedule, customer, trend, ai_todo, kpi, notification

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 POOM API 서버가 시작되었습니다.")
    yield
    logger.info("👋 POOM API 서버가 종료됩니다.")


app = FastAPI(
    title="POOM API",
    version="1.0.0",
    lifespan=lifespan,
)

import urllib.request
import json
import concurrent.futures

from app.config import get_settings
settings = get_settings()
ES_HOST = settings.ES_HOST

# Thread pool executor to handle blocking network/DNS calls in background threads
executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)

def send_log_sync(log_data: dict):
    try:
        req = urllib.request.Request(
            f"{ES_HOST}/system_logs/_doc",
            data=json.dumps(log_data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        # Use a short timeout of 0.5s so background threads release quickly when down
        with urllib.request.urlopen(req, timeout=0.5) as response:
            response.read()
    except Exception:
        pass

@app.middleware("http")
async def log_request_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    ms = int(process_time * 1000)
    
    path = request.url.path
    
    # Authorization 헤더에서 토큰을 추출하여 user_id 및 role 확인
    user_id = "system"
    is_admin = False
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            from app.utils.security import verify_token
            payload = verify_token(token)
            if payload:
                user_id = payload.get("sub", "system")
                role = payload.get("role", "")
                if "admin" in user_id.lower() or role.lower() == "admin":
                    is_admin = True
        except Exception:
            pass

    # 'news', 'notification' (뉴스 버킷 관련) 및 'admin' (어드민 접근 관련) 경로 또는 admin 사용자 요청은 Elasticsearch에 적재하지 않음
    if "news" in path or "notification" in path or "admin" in path or is_admin:
        return response

    if path.startswith("/api/v1") or path.startswith("/api"):
        log_data = {
            "timestamp": datetime.now().isoformat() + "Z",
            "api": f"[{request.method}] {path}",
            "path": path,
            "method": request.method,
            "status": response.status_code,
            "ms": ms,
            "user_id": user_id
        }
        # 터미널에 로그 출력
        print(f"📝 [API LOG] [{request.method}] {path} - Status: {response.status_code} ({ms}ms) - User: {user_id}")
        
        # Run blocking DNS/HTTP log call in a background thread to prevent freezing the FastAPI event loop
        loop = asyncio.get_running_loop()
        loop.run_in_executor(executor, send_log_sync, log_data)
        
    return response

# CORS 설정
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(schedule.router, prefix="/api/v1", tags=["Schedule"])
app.include_router(customer.router, prefix="/api/v1/customers", tags=["Customer"])
app.include_router(trend.router, prefix="/api/v1/trend", tags=["Trend"])
app.include_router(ai_todo.router, prefix="/api/v1/ai-todo", tags=["AI Todo"])
app.include_router(kpi.router, prefix="/api/v1/kpi", tags=["KPI"])
app.include_router(notification.router, prefix="/api/v1", tags=["Notification"])



@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
