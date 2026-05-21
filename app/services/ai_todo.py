from typing import Optional
from sqlalchemy.orm import Session
from app.schemas.ai_todo import (
    AiTodoListResponse,
    AiTodoConfirmRequest,
    AiTodoConfirmResponse,
    AiTodoUnconfirmResponse,
)


async def get_ai_todos(
    u_id: Optional[str], current_user, db: Session
) -> AiTodoListResponse:
    """AI 투두 목록 조회"""
    # TODO: 구현
    pass


async def confirm_ai_todo(
    request: AiTodoConfirmRequest, current_user, db: Session
) -> AiTodoConfirmResponse:
    """AI 투두 확인"""
    # TODO: 구현
    pass


async def unconfirm_ai_todo(
    at_id: int, current_user, db: Session
) -> AiTodoUnconfirmResponse:
    """AI 투두 확인 취소"""
    # TODO: 구현
    pass
