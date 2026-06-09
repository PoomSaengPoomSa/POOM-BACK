import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
import logging
import time
import threading
import httpx
from datetime import datetime, timezone, date, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cachetools import TTLCache

from app.routers import auth, admin, schedule, customer, trend, ai_todo, kpi, notification
from app.config import get_settings

# ── 모듈 상단에서 한 번만 import ──────────────────────────────────────────────
from app.database import SessionLocal
from app.models.schedule import Schedule
from app.models.notification import Notification
from app.models.account import PbUser
from app.services.notification import run_notification_generator
from app.services.admin import ensure_system_logs_index, ensure_employee_logs_index
from app.utils.security import verify_token
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

# ── TTLCache + Lock (스레드 안전) ──────────────────────────────────────────────
_emp_log_dedup = TTLCache(maxsize=10000, ttl=5)
_emp_log_lock = threading.Lock()


# ── 백그라운드 스케줄러 ────────────────────────────────────────────────────────
async def start_periodic_visit_briefing_scheduler():
    logger.info("⏳ 방문 예정 브리핑 백그라운드 스케줄러가 시작되었습니다. (10분 주기)")
    while True:
        try:
            logger.info("[Scheduler] 백그라운드 방문 브리핑 주기 검사 시작")

            db = SessionLocal()
            try:
                today = date.today()
                now = datetime.now()
                forty_mins_later = now + timedelta(minutes=40)

                target_schedules = db.query(Schedule).filter(
                    Schedule.category == "상담",
                    Schedule.c_id.isnot(None),
                    Schedule.execution_date >= datetime.combine(today, datetime.min.time()),
                    Schedule.execution_date <= datetime.combine(today, datetime.max.time()),
                    Schedule.execution_date >= now,
                    Schedule.execution_date <= forty_mins_later
                ).all()

                for s in target_schedules:
                    dup = db.query(Notification).filter(
                        Notification.category == "방문 예정 브리핑",
                        Notification.s_id == s.s_id
                    ).first()

                    if not dup:
                        logger.info(
                            f"[Scheduler] 40분 이내 방문 예정 일정 발견! "
                            f"실시간 브리핑 백그라운드 생성 (s_id: {s.s_id}, 고객: {s.c_id})"
                        )
                        # await 추가 — async 함수이므로 반드시 필요
                        await run_notification_generator(
                            s.u_id, today.strftime("%Y-%m-%d"), db=db
                        )
                        db.commit()

            except Exception as e:
                db.rollback()  # 트랜잭션 오염 방지
                logger.error(f"[Scheduler] 백그라운드 스케줄러 처리 중 오류 발생: {e}", exc_info=True)
            finally:
                db.close()

            await asyncio.sleep(600)

        except asyncio.CancelledError:
            logger.info("⏳ 방문 예정 브리핑 백그라운드 스케줄러가 정상 종료되었습니다.")
            break
        except Exception as e:
            logger.error(f"[Scheduler] 백그라운드 루프 치명적 에러: {e}", exc_info=True)
            await asyncio.sleep(60)  # 치명적 에러 후 1분 대기 후 재시도


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 POOM API 서버가 시작되었습니다.")

    settings = get_settings()
    es_host = settings.ES_HOST

    # ES 인덱스 초기화 — 중요한 초기화이므로 완료 후 서버 시작
    await ensure_system_logs_index(es_host)
    await ensure_employee_logs_index(es_host)

    # 백그라운드 스케줄러 시작
    scheduler_task = asyncio.create_task(start_periodic_visit_briefing_scheduler())

    yield

    # 서버 종료 시 태스크 취소
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass

    logger.info("👋 POOM API 서버가 종료됩니다.")


# ── FastAPI 앱 ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="POOM API",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
ES_HOST = settings.ES_HOST
LOGSTASH_HOST = settings.LOGSTASH_HOST


# ── 로그 전송 유틸 ─────────────────────────────────────────────────────────────
async def send_log_async(es_host: str, index: str, log_data: dict):
    """범용 비동기 ES/Logstash 로그 적재 함수"""
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            if LOGSTASH_HOST:
                url = f"{LOGSTASH_HOST}/{index}"
                dest = "Logstash"
            else:
                url = f"{es_host}/{index}/_doc"
                dest = "ES"

            await client.post(
                url,
                json=log_data,
                headers={"bypass-tunnel-reminder": "true"}
            )
        except Exception as e:
            logger.warning(f"[{index}] {dest} 적재 실패: {e!r}")


async def send_emp_log_with_info_async(user_id: str, feature: str, timestamp: str):
    """DB에서 PB 정보 조회 후 비동기 적재"""
    name = user_id
    branch = "미지정 지점"
    try:
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


# ── HTTP 미들웨어 ──────────────────────────────────────────────────────────────
@app.middleware("http")
async def log_request_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    ms = int(process_time * 1000)

    path = request.url.path
    user_id = "system"
    is_superadmin = False

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = verify_token(token)
            if payload:
                user_id = payload.get("sub", "system")
                role = payload.get("role", "")
                if role.lower() == "superadmin" or "superadmin" in user_id.lower():
                    is_superadmin = True
        except Exception:
            pass

    if "admin" in path or is_superadmin:
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

        # 미들웨어는 async context이므로 create_task 사용 (불필요한 스레드 생성 제거)
        asyncio.create_task(send_log_async(ES_HOST, "system_logs", log_data))

        if user_id != "system" and not is_superadmin:
            from app.utils.online_tracker import mark_user_active
            mark_user_active(user_id)

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
            elif "notification" in path:
                feature = "알림"

            if feature:
                dedup_key = f"{user_id}:{feature}"
                # 스레드 안전 dedup 체크
                with _emp_log_lock:
                    should_log = dedup_key not in _emp_log_dedup
                    if should_log:
                        _emp_log_dedup[dedup_key] = True

                if should_log:
                    asyncio.create_task(send_emp_log_with_info_async(user_id, feature, timestamp))

    return response


# ── CORS ───────────────────────────────────────────────────────────────────────
origins = settings.cors_origins_list

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 라우터 등록 ────────────────────────────────────────────────────────────────
app.include_router(auth.router,         prefix="/api/v1/auth",      tags=["Auth"])
app.include_router(admin.router,        prefix="/api/v1/admin",     tags=["Admin"])
app.include_router(schedule.router,     prefix="/api/v1",           tags=["Schedule"])
app.include_router(customer.router,     prefix="/api/v1/customers", tags=["Customer"])
app.include_router(trend.router,        prefix="/api/v1/trend",     tags=["Trend"])
app.include_router(ai_todo.router,      prefix="/api/v1/ai-todo",   tags=["AI Todo"])
app.include_router(kpi.router,          prefix="/api/v1/kpi",       tags=["KPI"])
app.include_router(notification.router, prefix="/api/v1",           tags=["Notification"])


# ── 기타 엔드포인트 ────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


@app.post("/api/v1/customer-main/run")
async def run_customer_main_gateway(req: dict):
    from fastapi import HTTPException
    settings = get_settings()
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            resp = await client.post(f"{settings.POOM_AI_URL}/api/v1/customer-main/run", json=req)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI API gateway forwarding failed: {str(e)}")
