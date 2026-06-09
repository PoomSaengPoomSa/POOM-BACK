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


def get_kst_now() -> datetime.datetime:
    """한국 시간(KST) 기준의 naive datetime을 반환합니다."""
    kst_tz = datetime.timezone(datetime.timedelta(hours=9))
    return datetime.datetime.now(kst_tz).replace(tzinfo=None)


def get_kst_today() -> datetime.date:
    """한국 시간(KST) 기준의 오늘 날짜를 반환합니다."""
    return get_kst_now().date()


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
    today_date = get_kst_today()
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
    """유저 ID(u_id)에 따른 알림 리스트 조회 및 포맷팅 (방문 브리핑은 30분 전부터 노출, 일반 알림은 고객/날짜별 묶음 처리)"""
    ensure_today_notifications(current_user, db)
    
    today_date = get_kst_today()
    query = db.query(Notification).filter(
        Notification.u_id == current_user.id
    )
    
    # 최신 알림 순 정렬
    notifs = query.order_by(Notification.created_time.desc()).all()
    
    # 정렬 기준 시간 계산 함수 (방문 예정 브리핑은 예약 시간 기준, 나머지는 생성 시간 기준)
    def get_sort_key(n_obj):
        if n_obj.category == "방문 예정 브리핑" and n_obj.schedule:
            return n_obj.schedule.execution_date
        return n_obj.created_time

    # 1차 필터링 및 묶을 것과 개별 표시할 것 분류
    # 묶음 키: (c_id, created_date)
    from collections import defaultdict
    grouped_notifs = defaultdict(list)
    standalone_notifs = []
    
    for n in notifs:
        created_date = n.created_time.date()
        is_today = (created_date == today_date)
        
        # 'today' 탭인 경우 오늘 알림만 필터링
        if tab == "today" and not is_today:
            continue
            
        # '방문 예정 브리핑'의 경우, 스케줄이 존재하면 예약 시간 30분 전부터 정각 사이일 때만 알림 제공하며, 스케줄 유무 관계없이 항상 단독 노출 처리합니다.
        if n.category == "방문 예정 브리핑":
            if n.schedule:
                now = get_kst_now()
                trigger_time = n.schedule.execution_date - datetime.timedelta(minutes=30)
                if not (trigger_time <= now <= n.schedule.execution_date):
                    continue
            standalone_notifs.append(n)
        elif n.c_id is not None:
            # 일반 알림은 고객 ID와 날짜별로 그룹화
            grouped_notifs[(n.c_id, created_date)].append(n)
        else:
            standalone_notifs.append(n)
            
    # 최종 반환할 응답 객체 리스트
    final_responses = []
    
    # 1. 단독 노출 알림들 변환
    for n in standalone_notifs:
        created_date = n.created_time.date()
        days_diff = (today_date - created_date).days
        is_today = (created_date == today_date)
        
        resp = NotificationResponse(
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
            tags=[{
                "type": n.category or "안부 연락",
                "category": map_category_color(n.category)
            }]
        )
        final_responses.append((get_sort_key(n), resp))
        
    # 2. 그룹화된 알림들 변환
    priority = {'이탈 위험': 0, '거액 거래 탐지': 1, '만기 알림': 2, '안부 연락': 3}
    
    for (c_id, created_date), n_list in grouped_notifs.items():
        # 우선순위가 높은 카테고리가 맨 위로 오도록 정렬
        n_list.sort(key=lambda x: priority.get(x.category, 99))
        
        primary_n = n_list[0]
        days_diff = (today_date - created_date).days
        is_today = (created_date == today_date)
        
        # 태그 목록 구성 (중복 제거)
        tags = []
        seen_categories = set()
        for x in n_list:
            cat = x.category or "안부 연락"
            if cat not in seen_categories:
                seen_categories.add(cat)
                tags.append({
                    "type": cat,
                    "category": map_category_color(cat)
                })
                
        # 카드 제목 구성
        customer_name = primary_n.customer.name if primary_n.customer else primary_n.title.split("고객")[0].strip()
        if len(tags) > 1:
            cat_titles = [t["type"] for t in tags]
            title_summary = " & ".join(cat_titles)
            unified_title = f"{customer_name} 고객 안내 ({title_summary})"
        else:
            unified_title = primary_n.title
            
        # 본문 병합
        merged_expanded = []
        for x in n_list:
            cat = x.category or "안부 연락"
            if len(n_list) > 1:
                merged_expanded.append(f"[{cat}] {x.title}")
                if x.content:
                    for line in x.content.split("\n"):
                        stripped = line.strip()
                        if stripped:
                            merged_expanded.append(f"  • {stripped}")
                merged_expanded.append("")  # 공백 라인 구분자
            else:
                # 1개만 있는 경우는 원본 형식 유지
                if x.content:
                    merged_expanded.extend([line.strip() for line in x.content.split("\n") if line.strip()])
                    
        # 다수 건 병합 시 마지막 빈 줄 제거
        if len(n_list) > 1 and merged_expanded and merged_expanded[-1] == "":
            merged_expanded.pop()
            
        resp = NotificationResponse(
            id=primary_n.n_id,
            type=primary_n.category or "안부 연락",
            content=unified_title,
            date=format_date(primary_n.created_time),
            category=map_category_color(primary_n.category),
            today=is_today,
            isBriefing=False,
            expandedContent=merged_expanded,
            state_us=primary_n.state_us,
            u_id=primary_n.u_id,
            s_id=primary_n.s_id,
            c_id=c_id,
            days_diff=days_diff,
            tags=tags
        )
        # 그룹의 정렬 기준 시간은 그룹 내 가장 최신 알림 시간으로 지정
        max_time = max(x.created_time for x in n_list)
        final_responses.append((max_time, resp))
        
    # 정렬 기준 시간에 따라 내림차순 정렬
    final_responses.sort(key=lambda x: x[0], reverse=True)
    return [resp for _, resp in final_responses]


def get_today_count(current_user, db: Session) -> int:
    """오늘 날짜의 알림 개수 조회 (방문 예정 브리핑은 30분 전부터 카운트 포함, 그룹화 반영)"""
    return len(get_notifications(current_user, "today", db))


def get_customer_briefing(current_user, customer_id: int, db: Session) -> Optional[NotificationResponse]:
    """특정 고객의 오늘 날짜 방문 예정 브리핑 조회 및 미생성 시 온디맨드 생성"""
    today_date = get_kst_today()
    
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

    # 2. 조회 및 반환 (s_id가 정상적으로 존재하는 유효 브리핑만 필터 조회)
    n = db.query(Notification).filter(
        Notification.u_id == current_user.id,
        Notification.c_id == customer_id,
        Notification.category == "방문 예정 브리핑",
        Notification.s_id.isnot(None)
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


def clear_notification_cache(u_id: str) -> None:
    """지정된 유저의 알림 생성 캐시 및 락을 초기화하여 실시간 재생성을 유도합니다."""
    import os
    import tempfile
    from pathlib import Path
    
    current_file_path = Path(__file__).resolve()
    # notification.py는 app/services/ 하위에 있으므로, root_dir은 부모의 부모의 부모 폴더(POOM-BACK)가 됨
    root_dir = current_file_path.parent.parent.parent
    
    scratch_dir = root_dir / "scratch"
    if not scratch_dir.exists():
        scratch_dir = Path(tempfile.gettempdir())
        
    lock_file = scratch_dir / f"generation_{u_id}.lock"
    last_run_file = scratch_dir / f"last_run_date_{u_id}.txt"
    
    for f in [lock_file, last_run_file]:
        if f.exists():
            try:
                os.remove(f)
            except Exception:
                pass
