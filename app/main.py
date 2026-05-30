import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
import logging
import time
import asyncio
import httpx
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cachetools import TTLCache

from app.routers import auth, admin, schedule, customer, trend, ai_todo, kpi, notification
from app.config import get_settings

import threading

def fire_and_forget(coro):
    """별도 스레드에서 비동기 작업 실행 (Windows 호환)"""
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()
    threading.Thread(target=run, daemon=True).start()

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

settings = get_settings()
ES_HOST = settings.ES_HOST

# 5초 유지, 최대 1만 개까지만 저장 (메모리 누수 방지)
_emp_log_dedup = TTLCache(maxsize=10000, ttl=5)

async def send_log_async(es_host: str, index: str, log_data: dict):
    """범용 비동기 ES 로그 적재 함수"""
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            await client.post(
                f"{es_host}/{index}/_doc",
                json=log_data,
                headers={"bypass-tunnel-reminder": "true"}
            )
        except Exception as e:
            logger.warning(f"[{index}] ES 적재 실패: {e!r}")

async def send_emp_log_with_info_async(user_id: str, feature: str, timestamp: str):
    """DB에서 PB 정보 조회 후 비동기 적재"""
    name = user_id
    branch = "미지정 지점"
    try:
        from app.database import SessionLocal
        from app.models.account import PbUser
        from sqlalchemy.orm import joinedload

        db = SessionLocal()
        try:
            pb = (
                db.query(PbUser)
                .options(joinedload(PbUser.branch_rel))
                .filter(PbUser.u_id == user_id)
                .first()
            )
            if pb:
                name = pb.name
                branch = pb.branch_rel.name if pb.branch_rel else "미지정 지점"
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"[employee_logs] PB 정보 조회 실패: {e!r}")

    log_data = {
        "timestamp": timestamp,
        "user_id": user_id,
        "name": name,
        "branch": branch,
        "feature": feature,
    }
    await send_log_async(ES_HOST, "employee_logs", log_data)


@app.middleware("http")
async def log_request_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    ms = int(process_time * 1000)

    path = request.url.path
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

    if "news" in path or "notification" in path or "admin" in path or is_admin:
        return response

    if path.startswith("/api/v1") or path.startswith("/api"):
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        log_data = {
            "timestamp": timestamp,
            "api": f"[{request.method}] {path}",
            "path": path,
            "method": request.method,
            "status": response.status_code,
            "ms": ms,
            "user_id": user_id,
        }
        print(f"[API LOG] [{request.method}] {path} - Status: {response.status_code} ({ms}ms)")
        
        # 비동기 Task로 system_logs 전송 (스레드 블로킹 없음)
        # asyncio.create_task(send_log_async(ES_HOST, "system_logs", log_data))
        fire_and_forget(send_log_async(ES_HOST, "system_logs", log_data))

        if user_id != "system" and "admin" not in user_id.lower() and not is_admin:
            feature = None
            if "news" in path or "archive" in path or "trend" in path:
                feature = "뉴스 아카이브"
            elif "todo" in path:
                feature = "AI TODO"
            elif "memo" in path:
                feature = "AI 메모"
            elif "customer" in path:
                feature = "고객 관리"
            elif "schedule" in path:
                feature = "캘린더"

            if feature:
                dedup_key = f"{user_id}:{feature}"
                # 캐시에 없으면(최근 5초 내 처음이면) 로직 실행 후 캐시에 등록
                if dedup_key not in _emp_log_dedup:
                    _emp_log_dedup[dedup_key] = True
                    fire_and_forget(send_emp_log_with_info_async(user_id, feature, timestamp)) # 속도개선 수정

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