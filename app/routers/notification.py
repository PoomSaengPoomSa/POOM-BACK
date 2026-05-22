from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.notification import NotificationResponse, NotificationCountResponse
from app.services import notification as notification_service

router = APIRouter()


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    tab: str = "all",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """유저의 전체 또는 오늘 알림 리스트 조회"""
    return await notification_service.get_notifications(current_user, tab, db)


@router.get("/notifications/today-count", response_model=NotificationCountResponse)
async def get_today_count(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """유저의 오늘 알림 개수 조회"""
    count = await notification_service.get_today_count(current_user, db)
    return NotificationCountResponse(today_count=count)
