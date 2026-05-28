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

executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)


def send_log_sync(log_data: dict):
    """system_logs 인덱스에 API 요청 로그 적재"""
    try:
        req = urllib.request.Request(
            f"{ES_HOST}/system_logs/_doc",
            data=json.dumps(log_data).encode("utf-8"),
            headers={"Content-Type": "application/json", "bypass-tunnel-reminder": "true"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3.0) as response:  # 0.5s → 3.0s
            response.read()
    except Exception as e:
        logger.warning(f"[system_logs] ES 적재 실패: {e!r}")


def send_emp_log_sync(log_data: dict):
    """employee_logs 인덱스에 직원 활동 로그 적재"""
    try:
        req = urllib.request.Request(
            f"{ES_HOST}/employee_logs/_doc",
            data=json.dumps(log_data).encode("utf-8"),
            headers={"Content-Type": "application/json", "bypass-tunnel-reminder": "true"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3.0) as response:  # 0.5s → 3.0s
            response.read()
    except Exception as e:
        logger.warning(f"[employee_logs] ES 적재 실패: {e!r}")


def send_emp_log_with_info(user_id: str, feature: str, timestamp: str):
    """DB에서 PB name/branch 조회 후 employee_logs에 적재"""
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

    send_emp_log_sync({
        "timestamp": timestamp,
        "user_id": user_id,
        "name": name,
        "branch": branch,
        "feature": feature,
    })


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

    # admin 경로 및 admin 유저 요청은 로그 적재 제외
    if "news" in path or "notification" in path or "admin" in path or is_admin:
        return response

    if path.startswith("/api/v1") or path.startswith("/api"):
        timestamp = datetime.now().isoformat() + "Z"

        # system_logs: 모든 API 요청 기록
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
        loop = asyncio.get_running_loop()
        loop.run_in_executor(executor, send_log_sync, log_data)

        # employee_logs: PB 유저의 기능별 활동만 기록 (name/branch 포함)
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
                loop.run_in_executor(
                    executor, send_emp_log_with_info, user_id, feature, timestamp
                )

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