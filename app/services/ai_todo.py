import subprocess
import sys
import platform
import logging
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from app.models.ai_todo import AiTodo
from app.models.schedule import Schedule
from app.schemas.ai_todo import (
    AiTodoListResponse,
    AiTodoItem,
    AiTodoConfirmRequest,
    AiTodoConfirmResponse,
    AiTodoUnconfirmResponse,
)

logger = logging.getLogger(__name__)


def get_ai_todos(
    u_id: Optional[str], current_user, db: Session
) -> AiTodoListResponse:
    """AI 투두 목록 조회"""
    target_uid = u_id or current_user.id
    todos = db.query(AiTodo).filter(AiTodo.u_id == target_uid).all()
    todo_items = []
    for t in todos:
        todo_items.append(
            AiTodoItem(
                at_id=t.at_id,
                title=t.title,
                memo=t.memo,
                category=t.category,
                create_date=t.create_date,
                execution_date=t.execution_date,
                is_checked=t.is_checked,
                c_id=t.c_id,
            )
        )
    return AiTodoListResponse(todos=todo_items, total=len(todo_items))


def confirm_ai_todo(
    request: AiTodoConfirmRequest, current_user, db: Session
) -> AiTodoConfirmResponse:
    """AI 투두 확인"""
    confirmed_count = 0
    schedule_ids = []
    
    todos = db.query(AiTodo).filter(AiTodo.at_id.in_(request.at_ids)).all()
    
    from datetime import datetime, timedelta
    from fastapi import HTTPException, status
    
    # target_date 파싱 시도 (YYYY-MM-DD)
    parsed_target_date = None
    if request.target_date:
        try:
            parsed_target_date = datetime.strptime(request.target_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    
    # 1. 1차 패스로 모든 AI To-Do의 중복 여부를 정밀 검증
    for t in todos:
        if not t.is_checked:
            start_dt = t.execution_date
            if parsed_target_date:
                start_dt = datetime.combine(parsed_target_date, t.execution_date.time())
                
            # 안부 연락은 15분으로 가볍게 배치, 상담/분석/KPI는 1시간 심층 배치
            duration = timedelta(minutes=15) if t.category == '안부 연락 제안' else timedelta(hours=1)
            end_dt = start_dt + duration
            
            # DB 상에서 겹치는 일정이 있는지 검증 (날은 물론 시간대까지 겹치면 안 됨)
            overlap_exists = db.query(Schedule).filter(
                Schedule.u_id == t.u_id,
                Schedule.execution_date < end_dt,
                Schedule.end_datetime > start_dt
            ).first()
            
            if overlap_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"추천 일정 '{t.title}'의 시간대({start_dt.strftime('%H:%M')} ~ {end_dt.strftime('%H:%M')})에 이미 겹치는 일정이 존재합니다.",
                )
                
    # 2. 검증 통과 후 My To-Do(일정)로 안전하게 일괄 등록
    for t in todos:
        if not t.is_checked:
            t.is_checked = True
            
            start_dt = t.execution_date
            if parsed_target_date:
                start_dt = datetime.combine(parsed_target_date, t.execution_date.time())
                
            category_mapping = {
                'KPI 기반': '공지',
                '상담 일정 제안': '상담',
                '안부 연락 제안': '개인',
                '신규 상품 분석': '개인'
            }
            sched_cat = category_mapping.get(t.category, '상담')
            
            duration = timedelta(minutes=15) if t.category == '안부 연락 제안' else timedelta(hours=1)
            new_sched = Schedule(
                title=t.title,
                memo=t.memo or "AI 추천으로 등록된 일정",
                category=sched_cat,
                execution_date=start_dt,
                end_datetime=start_dt + duration,
                u_id=t.u_id,
                c_id=t.c_id,
                at_id=t.at_id
            )
            db.add(new_sched)
            db.flush()
            schedule_ids.append(new_sched.s_id)
            confirmed_count += 1
            
    db.commit()
    return AiTodoConfirmResponse(confirmed=confirmed_count, schedule_ids=schedule_ids)


def unconfirm_ai_todo(
    at_id: int, current_user, db: Session
) -> AiTodoUnconfirmResponse:
    """AI 투두 확인 취소"""
    todo = db.query(AiTodo).filter(AiTodo.at_id == at_id).first()
    if not todo:
        return AiTodoUnconfirmResponse(message="AI 투두를 찾을 수 없습니다.", success=False)
        
    todo.is_checked = False
    
    sched = db.query(Schedule).filter(Schedule.at_id == at_id).first()
    if sched:
        db.delete(sched)
        
    db.commit()
    return AiTodoUnconfirmResponse(message="성공적으로 취소되었습니다.", success=True)


def delete_ai_todo(at_id: int, current_user, db: Session) -> dict:
    """AI 투두 숨김 (DB 삭제)"""
    todo = db.query(AiTodo).filter(AiTodo.at_id == at_id).first()
    if not todo:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI 투두를 찾을 수 없습니다."
        )
    db.delete(todo)
    db.commit()
    return {"message": "추천 일정이 성공적으로 삭제되었습니다."}


def run_ai_todo_agent_subprocess(u_id: str, target_date: str) -> None:
    """POOM-AI LangGraph To-Do Agent를 API 호출하여 일정을 자동 기획하고 DB에 적재합니다."""
    import requests
    try:
        url = "http://poom-ai:8001/api/v1/ai-todo/run"
        payload = {"u_id": u_id, "date": target_date}
        logger.info(f"[Background Task] POOM-AI API 호출 시작: {url} payload: {payload}")
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        logger.info(f"[Background Task] POOM-AI API 성공 완료: {response.json()}")
    except Exception as e:
        logger.error(f"[Background Task] POOM-AI API 구동 중 예외 발생: {e}", exc_info=True)
