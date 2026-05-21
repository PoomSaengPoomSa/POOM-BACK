from sqlalchemy.orm import Session
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
    # TODO: 구현
    pass


async def get_schedule(
    schedule_id: int, current_user, db: Session
) -> ScheduleResponse:
    """일정 상세 조회"""
    # TODO: 구현
    pass


async def update_schedule(
    u_id: str,
    schedule_id: int,
    request: ScheduleUpdate,
    current_user,
    db: Session,
) -> ScheduleResponse:
    """일정 수정"""
    # TODO: 구현
    pass


async def delete_schedule(
    schedule_id: int, current_user, db: Session
) -> MessageResponse:
    """일정 삭제"""
    # TODO: 구현
    pass
