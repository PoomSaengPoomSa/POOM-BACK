from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    MessageResponse,
)
from app.services import schedule as schedule_service

router = APIRouter(tags=["Schedule"])


@router.get("/schedules", response_model=List[ScheduleResponse])
async def get_schedules(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """일정 전체 목록 조회"""
    return await schedule_service.get_schedules(current_user, db)


@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    request: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """일정 생성"""
    return await schedule_service.create_schedule(request, current_user, db)


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """일정 상세 조회"""
    return await schedule_service.get_schedule(schedule_id, current_user, db)


@router.patch(
    "/users/{u_id}/schedules/{schedule_id}", response_model=ScheduleResponse
)
async def update_schedule(
    u_id: str,
    schedule_id: int,
    request: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """일정 수정"""
    return await schedule_service.update_schedule(
        u_id, schedule_id, request, current_user, db
    )


@router.delete("/schedules/{schedule_id}", response_model=MessageResponse)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """일정 삭제"""
    return await schedule_service.delete_schedule(schedule_id, current_user, db)
