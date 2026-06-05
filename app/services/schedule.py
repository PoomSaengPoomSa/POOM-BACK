from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from typing import List
from app.models.schedule import Schedule
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    MessageResponse,
)


def create_schedule(
    request: ScheduleCreate, current_user, db: Session
) -> ScheduleResponse:
    """일정 생성"""
    # 중복 시간대 검사
    overlap_exists = db.query(Schedule).filter(
        Schedule.u_id == current_user.id,
        Schedule.execution_date < request.end_datetime,
        Schedule.end_datetime > request.start_datetime
    ).first()
    
    if overlap_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="선택하신 시간에 이미 다른 일정이 존재합니다. 중복 등록할 수 없습니다.",
        )
 
    new_sched = Schedule(
        title=request.content,
        memo=request.memo,
        category=request.category,
        execution_date=request.start_datetime,
        end_datetime=request.end_datetime,
        u_id=current_user.id,
        c_id=request.customer_id,
    )
    db.add(new_sched)
    db.commit()
    db.refresh(new_sched)
    return new_sched


def get_schedules(
    current_user, db: Session
) -> List[ScheduleResponse]:
    """일정 목록 조회"""
    schedules = (
        db.query(Schedule)
        .options(joinedload(Schedule.customer))
        .filter(Schedule.u_id == current_user.id)
        .all()
    )
    
    for s in schedules:
        s.customer_name = s.customer.name if s.customer else ""
        
    return schedules


def get_schedule(
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


def update_schedule(
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
        
    # 중복 시간대 검사
    new_start = request.start_datetime if request.start_datetime is not None else sched.execution_date
    new_end = request.end_datetime if request.end_datetime is not None else sched.end_datetime
    
    overlap_exists = db.query(Schedule).filter(
        Schedule.u_id == current_user.id,
        Schedule.s_id != schedule_id,
        Schedule.execution_date < new_end,
        Schedule.end_datetime > new_start
    ).first()
    
    if overlap_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="선택하신 시간에 이미 다른 일정이 존재합니다. 중복 등록할 수 없습니다.",
        )
        
    if request.category is not None:
        sched.category = request.category
    if request.content is not None:
        sched.title = request.content
    if request.start_datetime is not None:
        sched.execution_date = request.start_datetime
    if request.end_datetime is not None:
        sched.end_datetime = request.end_datetime
    if "customer_id" in request.model_fields_set:
        sched.c_id = request.customer_id
    if request.memo is not None:
        sched.memo = request.memo
        
    # 일정 정보가 수정되는 경우 기존에 생성된 방문 예정 브리핑 알림을 삭제하여,
    # 바뀐 일정 정보(시간, 메모 등)를 반영한 최신 브리핑이 실시간 자동 재구성되도록 유도합니다.
    from app.models.notification import Notification
    db.query(Notification).filter(
        Notification.s_id == schedule_id,
        Notification.category == "방문 예정 브리핑"
    ).delete(synchronize_session=False)
        
    db.commit()
    db.refresh(sched)
    return sched


def delete_schedule(
    schedule_id: int, current_user, db: Session
) -> MessageResponse:
    """일정 삭제"""
    from app.models.notification import Notification
    from app.models.ai_todo import AiTodo

    sched = db.query(Schedule).filter(Schedule.s_id == schedule_id).first()
    if not sched:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일정을 찾을 수 없습니다.",
        )
        
    # 1. 연관된 알림(Notification)도 함께 DB에서 완전히 삭제 (Cascade Delete)
    db.query(Notification).filter(Notification.s_id == schedule_id).delete(
        synchronize_session=False
    )
    
    # 2. AI To Do 추천을 통해 자동 생성되었던 일정일 경우, AI To Do 목록에서 복원되도록 처리
    if sched.at_id:
        todo = db.query(AiTodo).filter(AiTodo.at_id == sched.at_id).first()
        if todo:
            todo.is_checked = False

    db.delete(sched)
    db.commit()
    return MessageResponse(message="일정이 정상적으로 삭제되었습니다.")
