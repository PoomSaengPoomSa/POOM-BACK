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


async def start_periodic_visit_briefing_scheduler():
    logger.info("⏳ 방문 예정 브리핑 백그라운드 스케줄러가 시작되었습니다. (10분 주기)")
    while True:
        try:
            logger.info("[Scheduler] 백그라운드 방문 브리핑 주기 검사 시작")
            from app.database import SessionLocal
            from app.models.schedule import Schedule
            from app.models.notification import Notification
            from datetime import datetime, date, timedelta
            
            db = SessionLocal()
            try:
                today = date.today()
                now = datetime.now()
                # 10분 주기에 맞추어 다음 40분 이내 일정을 조회하여 누락 방지
                forty_mins_later = now + timedelta(minutes=40)
                
                # 오늘 자 상담 일정 중 아직 브리핑 알림이 생성되지 않았고, 
                # 시작 시각이 현재~40분 뒤 범위 내에 들어오는 일정 조회
                target_schedules = db.query(Schedule).filter(
                    Schedule.category == "상담",
                    Schedule.c_id.isnot(None),
                    Schedule.execution_date >= datetime.combine(today, datetime.min.time()),
                    Schedule.execution_date <= datetime.combine(today, datetime.max.time()),
                    Schedule.execution_date >= now,
                    Schedule.execution_date <= forty_mins_later
                ).all()
                
                for s in target_schedules:
                    # 해당 일정에 대해 이미 브리핑 알림이 생성되었는지 체크
                    dup = db.query(Notification).filter(
                        Notification.category == "방문 예정 브리핑",
                        Notification.s_id == s.s_id
                    ).first()
                    
                    if not dup:
                        logger.info(f"[Scheduler] 40분 이내 방문 예정 일정 발견! 실시간 브리핑 백그라운드 생성 (s_id: {s.s_id}, 고객: {s.c_id})")
                        from app.services.notification import run_notification_generator
                        if run_notification_generator:
                            # 백그라운드에서 동적 생성 및 트랜잭션 커밋
                            run_notification_generator(s.u_id, today.strftime("%Y-%m-%d"), db=db)
                            db.commit()
            except Exception as e:
                logger.error(f"[Scheduler] 백그라운드 스케줄러 처리 중 오류 발생: {e}", exc_info=True)
            finally:
                db.close()
            
            # 검사 완료 후 10분 대기 (600초)
            await asyncio.sleep(600)
        except asyncio.CancelledError:
            logger.info("⏳ 방문 예정 브리핑 백그라운드 스케줄러가 정상 종료되었습니다.")
            break
        except Exception as e:
            logger.error(f"[Scheduler] 백그라운드 루프 치명적 에러: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 POOM API 서버가 시작되었습니다.")
    # Elasticsearch 인덱스 매핑 생성 비동기 처리
    from app.services.admin import ensure_system_logs_index, ensure_employee_logs_index
    asyncio.create_task(ensure_system_logs_index(ES_HOST))
    asyncio.create_task(ensure_employee_logs_index(ES_HOST))

    # 백그라운드 스케줄러 태스크 실행
    scheduler_task = asyncio.create_task(start_periodic_visit_briefing_scheduler())
    yield
    # 서버 종료 시 태스크 취소
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
    logger.info("👋 POOM API 서버가 종료됩니다.")


app = FastAPI(
    title="POOM API",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
ES_HOST = settings.ES_HOST
LOGSTASH_HOST = settings.LOGSTASH_HOST

# 5초 유지, 최대 1만 개까지만 저장 (메모리 누수 방지)
_emp_log_dedup = TTLCache(maxsize=10000, ttl=5)

async def send_log_async(es_host: str, index: str, log_data: dict):
    """범용 비동기 ES/Logstash 로그 적재 함수"""
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            if LOGSTASH_HOST:
                # Logstash HTTP 입력 플러그인에 맞게 전송 (경로가 인덱스 역할을 하도록 설계)
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
                if "admin" in user_id.lower() or role.lower() in ("admin", "superadmin"):
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


@app.post("/api/v1/customer-main/run")
async def run_customer_main_gateway(req: dict):
    import httpx
    from fastapi import HTTPException
    settings = get_settings()
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            resp = await client.post(f"{settings.POOM_AI_URL}/api/v1/customer-main/run", json=req)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI API gateway forwarding failed: {str(e)}")