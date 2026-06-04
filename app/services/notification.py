import datetime
import sys
import threading
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse

# POOM-AI의 visit_brief_generator 모듈 경로 추가
current_file_path = Path(__file__).resolve()
root_dir = current_file_path.parent.parent.parent.parent
poom_ai_brief_dir = root_dir / "POOM-AI" / "llm" / "visit_brief"

if str(poom_ai_brief_dir) not in sys.path:
    sys.path.insert(0, str(poom_ai_brief_dir))

try:
    from visit_brief_generator import run_notification_generator
except ImportError:
    run_notification_generator = None


# 중복 방지를 위한 스레드 락 정의
_notification_lock = threading.Lock()


def map_category_color(category: str) -> str:
    mapping = {
        "방문 예정 브리핑": "green",
        "거액 거래 탐지": "pink",
        "만기 알림": "blue",
        "이탈 위험": "red",
        "안부 연락": "indigo",
    }
    return mapping.get(category, "indigo")


def format_date(dt: datetime.datetime) -> str:
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]
    return f"{dt.day} {months[dt.month - 1]}, {dt.year}"


def ensure_today_notifications(current_user, db: Session):
    """오늘 자 알림이 아직 생성되지 않았다면 실시간으로 자동 생성합니다. (하루 1회 실행 보장 및 신규 상담일정 보완)"""
    if not run_notification_generator:
        return
        
    import os
    import time
    
    # scratch 폴더 위치 설정
    scratch_dir = root_dir / "POOM-BACK" / "scratch"
    if not scratch_dir.exists():
        scratch_dir = root_dir / "scratch"
    if not scratch_dir.exists():
        import tempfile
        scratch_dir = Path(tempfile.gettempdir())
        
    lock_file = scratch_dir / f"generation_{current_user.id}.lock"
    last_run_file = scratch_dir / f"last_run_date_{current_user.id}.txt"
    today_date = datetime.date.today()
    today_str = today_date.strftime("%Y-%m-%d")
    
    # 락 획득 시도 (타임아웃 15초)
    acquired = False
    start_time = time.time()
    timeout = 15.0
    
    # 오래된 락 파일 방지 (30초 이상 지난 락 파일은 무효화 및 강제 삭제)
    if lock_file.exists():
        try:
            mtime = os.path.getmtime(lock_file)
            if time.time() - mtime > 30.0:
                os.remove(lock_file)
        except Exception:
            pass
            
    while time.time() - start_time < timeout:
        try:
            # 원자적 파일 생성 시도
            fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            acquired = True
            break
        except FileExistsError:
            time.sleep(0.2)
            
    if not acquired:
        import logging
        logging.getLogger(__name__).warning(f"[OnDemandGeneration] 파일 락 획득 실패 (유저: {current_user.id})")
        return
        
    try:
        # DB 세션에 보관된 엔티티 캐시를 초기화하여 다른 프로세스가 이미 추가한 데이터를 새로 조회해 오도록 유도
        db.expire_all()
        
        already_run = False
        if last_run_file.exists():
            try:
                with open(last_run_file, "r", encoding="utf-8") as f:
                    if f.read().strip() == today_str:
                        already_run = True
            except Exception:
                pass
                
        # 오늘 자 상담 일정 중 방문 예정 브리핑이 누락된 건이 있는지 검사
        from app.models.schedule import Schedule
        start_of_today = datetime.datetime.combine(today_date, datetime.time.min)
        end_of_today = datetime.datetime.combine(today_date, datetime.time.max)
        
        today_schedules = db.query(Schedule).filter(
            Schedule.u_id == current_user.id,
            Schedule.category == "상담",
            Schedule.c_id.isnot(None),
            Schedule.execution_date >= start_of_today,
            Schedule.execution_date <= end_of_today
        ).all()
        
        need_regeneration = False
        for s in today_schedules:
            dup = db.query(Notification).filter(
                Notification.u_id == current_user.id,
                Notification.category == "방문 예정 브리핑",
                Notification.s_id == s.s_id
            ).first()
            if not dup:
                need_regeneration = True
                break
                
        if not already_run or need_regeneration:
            # 1차적으로 날짜 기록을 먼저 저장하여 다른 요청 진입을 즉시 방어
            try:
                scratch_dir.mkdir(parents=True, exist_ok=True)
                with open(last_run_file, "w", encoding="utf-8") as f:
                    f.write(today_str)
            except Exception:
                pass
            
            try:
                # 실시간으로 오늘 자 알림 및 브리핑 생성
                run_notification_generator(current_user.id, today_str, db=db)
                db.commit()
            except Exception as e:
                # 실패 시 다른 요청이 다시 시도할 수 있도록 캐시 파일 삭제 후 예외 전파
                if last_run_file.exists():
                    try:
                        os.remove(last_run_file)
                    except Exception:
                        pass
                raise e
    finally:
        # 락 파일 해제
        if lock_file.exists():
            try:
                os.remove(lock_file)
            except Exception:
                pass


def get_notifications(
    current_user, tab: str, db: Session
) -> List[NotificationResponse]:
    """유저 ID(u_id)에 따른 알림 리스트 조회 및 포맷팅"""
    ensure_today_notifications(current_user, db)
    
    today_date = datetime.date.today()
    query = db.query(Notification).filter(
        Notification.u_id == current_user.id
    )
    
    # 최신 알림 순 정렬
    notifs = query.order_by(Notification.created_time.desc()).all()
    
    response_list = []
    
    for n in notifs:
        created_date = n.created_time.date()
        is_today = (created_date == today_date)
        
        # 'today' 탭인 경우 오늘 알림만 필터링
        if tab == "today" and not is_today:
            continue
            
        days_diff = (today_date - created_date).days
        
        # 프론트엔드가 요구하는 형식으로 매핑
        response_list.append(
            NotificationResponse(
                id=n.n_id,
                type=n.category or "안부 연락",
                content=n.title,
                date=format_date(n.created_time),
                category=map_category_color(n.category),
                today=is_today,
                isBriefing=(n.category == "방문 예정 브리핑"),
                expandedContent=[line.strip() for line in n.content.split("\n") if line.strip()] if n.content else [],
                state_us=n.state_us,
                u_id=n.u_id,
                s_id=n.s_id,
                c_id=n.c_id,
                days_diff=days_diff,
            )
        )
        
    return response_list


def get_today_count(current_user, db: Session) -> int:
    """오늘 날짜의 알림 개수 조회 (방문 예정 브리핑 제외)"""
    ensure_today_notifications(current_user, db)
    
    today_date = datetime.date.today()
    
    # 쿼리에서 오늘 시작(00:00:00)부터 오늘 끝(23:59:59)까지 필터링
    start_of_today = datetime.datetime.combine(today_date, datetime.time.min)
    end_of_today = datetime.datetime.combine(today_date, datetime.time.max)
    
    count = (
        db.query(Notification)
        .filter(
            Notification.u_id == current_user.id,
            Notification.created_time >= start_of_today,
            Notification.created_time <= end_of_today,
        )
        .count()
    )
    return count


def get_customer_briefing(current_user, customer_id: int, db: Session) -> Optional[NotificationResponse]:
    """특정 고객의 오늘 날짜 방문 예정 브리핑 조회 및 미생성 시 온디맨드 생성"""
    today_date = datetime.date.today()
    
    # 1. 온디맨드 생성 처리
    if run_notification_generator:
        try:
            today_str = today_date.strftime("%Y-%m-%d")
            from app.models.schedule import Schedule
            
            start_of_today = datetime.datetime.combine(today_date, datetime.time.min)
            end_of_today = datetime.datetime.combine(today_date, datetime.time.max)
            
            schedule = db.query(Schedule).filter(
                Schedule.u_id == current_user.id,
                Schedule.category == "상담",
                Schedule.c_id == customer_id,
                Schedule.execution_date >= start_of_today,
                Schedule.execution_date <= end_of_today
            ).first()
            
            if schedule:
                dup = db.query(Notification).filter(
                    Notification.u_id == current_user.id,
                    Notification.category == "방문 예정 브리핑",
                    Notification.s_id == schedule.s_id
                ).first()
                if not dup:
                    run_notification_generator(current_user.id, today_str, db=db)
                    db.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[OnDemandGeneration] 특정 고객 브리핑 생성 실패: {e}", exc_info=True)

    # 2. 조회 및 반환
    n = db.query(Notification).filter(
        Notification.u_id == current_user.id,
        Notification.c_id == customer_id,
        Notification.category == "방문 예정 브리핑"
    ).order_by(Notification.created_time.desc()).first()
    
    if not n:
        return None
        
    created_date = n.created_time.date()
    is_today = (created_date == today_date)
    days_diff = (today_date - created_date).days
    
    return NotificationResponse(
        id=n.n_id,
        type=n.category or "안부 연락",
        content=n.title,
        date=format_date(n.created_time),
        category=map_category_color(n.category),
        today=is_today,
        isBriefing=(n.category == "방문 예정 브리핑"),
        expandedContent=[line.strip() for line in n.content.split("\n") if line.strip()] if n.content else [],
        state_us=n.state_us,
        u_id=n.u_id,
        s_id=n.s_id,
        c_id=n.c_id,
        days_diff=days_diff,
    )
