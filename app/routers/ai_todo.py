from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.ai_todo import (
    AiTodoListResponse,
    AiTodoConfirmRequest,
    AiTodoConfirmResponse,
    AiTodoUnconfirmResponse,
    MessageResponse,
)
from app.services import ai_todo as ai_todo_service

router = APIRouter(tags=["AI Todo"])


@router.get("/", response_model=AiTodoListResponse)
def get_ai_todos(
    u_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """AI 투두 목록 조회"""
    return ai_todo_service.get_ai_todos(u_id, current_user, db)


@router.post("/confirm", response_model=AiTodoConfirmResponse)
def confirm_ai_todo(
    request: AiTodoConfirmRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """AI 투두 확인"""
    return ai_todo_service.confirm_ai_todo(request, current_user, db)


@router.patch("/{at_id}/unconfirm", response_model=AiTodoUnconfirmResponse)
def unconfirm_ai_todo(
    at_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """AI 투두 확인 취소"""
    return ai_todo_service.unconfirm_ai_todo(at_id, current_user, db)


@router.post("/run", response_model=MessageResponse)
def run_ai_todo_agent(
    u_id: str = Query(..., description="PB ID"),
    date: str = Query(..., description="분석 기준일 YYYY-MM-DD"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """AI 투두 에이전트 구동 및 적재 트리거"""
    background_tasks.add_task(ai_todo_service.run_ai_todo_agent_subprocess, u_id, date)
    return MessageResponse(message="LangGraph AI ToDo 에이전트 백그라운드 구동 시작")
