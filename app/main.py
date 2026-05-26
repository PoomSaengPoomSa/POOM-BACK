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

ES_HOST = "http://ap.loclx.io:9201"

async def send_log_to_elasticsearch(log_data: dict):
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            await client.post(
                f"{ES_HOST}/system_logs/_doc",
                json=log_data
            )
    except Exception as e:
        logger.warning(f"Failed to record access log in remote Elasticsearch: {e}")

@app.middleware("http")
async def log_request_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    ms = int(process_time * 1000)
    
    path = request.url.path
    # 'news' 및 'notification' (뉴스 버킷 관련) 경로는 Elasticsearch에 적재하지 않음
    if "news" in path or "notification" in path:
        return response

    if path.startswith("/api/v1") or path.startswith("/api"):
        log_data = {
            "timestamp": datetime.now().isoformat() + "Z",
            "api": f"[{request.method}] {path}",
            "path": path,
            "method": request.method,
            "status": response.status_code,
            "ms": ms,
            "user_id": "system"
        }
        asyncio.create_task(send_log_to_elasticsearch(log_data))
        
    return response

# CORS 설정
origins = [
    "http://localhost:5173",
    "http://localhost:5174",  # 이거 추가
    "http://localhost:3000",
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
