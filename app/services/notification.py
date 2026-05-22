import datetime
from sqlalchemy.orm import Session
from typing import List
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse


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


async def get_notifications(
    current_user, tab: str, db: Session
) -> List[NotificationResponse]:
    """유저 ID(u_id)에 따른 알림 리스트 조회 및 포맷팅"""
    query = db.query(Notification).filter(Notification.u_id == current_user.id)
    
    # 최신 알림 순 정렬
    notifs = query.order_by(Notification.created_time.desc()).all()
    
    today_date = datetime.date.today()
    response_list = []
    
    for n in notifs:
        created_date = n.created_time.date()
        is_today = (created_date == today_date)
        
        # 'today' 탭인 경우 오늘 알림만 필터링
        if tab == "today" and not is_today:
            continue
            
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
            )
        )
        
    return response_list


async def get_today_count(current_user, db: Session) -> int:
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
