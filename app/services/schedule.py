from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from app.models.schedule import Schedule
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    MessageResponse,
)


async def create_schedule(
    request: ScheduleCreate, current_user, db: Session
) -> ScheduleResponse:
    """일정 생성"""
    new_sched = Schedule(
        title=request.content,
        memo=request.memo,
        category=request.category,
        execution_date=request.start_datetime,
        u_id=current_user.id,
        c_id=request.customer_id,
    )
    db.add(new_sched)
    db.commit()
    db.refresh(new_sched)
    return new_sched


async def get_schedules(
    current_user, db: Session
) -> List[ScheduleResponse]:
    """일정 목록 조회"""
    return db.query(Schedule).filter(Schedule.u_id == current_user.id).all()


async def get_schedule(
    schedule_id: int, current_user, db: Session
) -> ScheduleResponse:
    """일정 상세 조회"""
    sched = db.query(Schedule).filter(Schedule.s_id == schedule_id).first()
    if not sched:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일정을 찾을 수 없습니다.",
        )
    return sched


async def update_schedule(
    u_id: str,
    schedule_id: int,
    request: ScheduleUpdate,
    current_user,
    db: Session,
) -> ScheduleResponse:
    """일정 수정"""
    sched = db.query(Schedule).filter(Schedule.s_id == schedule_id).first()
    if not sched:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일정을 찾을 수 없습니다.",
        )
        
    if request.category is not None:
        sched.category = request.category
    if request.content is not None:
        sched.title = request.content
    if request.start_datetime is not None:
        sched.execution_date = request.start_datetime
    if request.memo is not None:
        sched.memo = request.memo
        
    db.commit()
    db.refresh(sched)
    return sched


async def delete_schedule(
    schedule_id: int, current_user, db: Session
) -> MessageResponse:
    """일정 삭제"""
    sched = db.query(Schedule).filter(Schedule.s_id == schedule_id).first()
    if not sched:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일정을 찾을 수 없습니다.",
        )
    db.delete(sched)
    db.commit()
    return MessageResponse(message="일정이 정상적으로 삭제되었습니다.")
