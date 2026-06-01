import datetime
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List
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


def get_notifications(
    current_user, tab: str, db: Session
) -> List[NotificationResponse]:
    """유저 ID(u_id)에 따른 알림 리스트 조회 및 포맷팅"""
    today_date = datetime.date.today()

    # 오늘 자 상담 일정 중 방문 예정 브리핑이 누락된 것이 있다면 실시간 생성
    if run_notification_generator:
        try:
            today_str = today_date.strftime("%Y-%m-%d")
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
            
            if need_regeneration:
                run_notification_generator(current_user.id, today_str)
                db.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[OnDemandGeneration] 실시간 방문 브리핑 생성 실패: {e}", exc_info=True)

    query = db.query(Notification).filter(Notification.u_id == current_user.id)
    
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
    """오늘 날짜의 알림 개수 조회"""
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
