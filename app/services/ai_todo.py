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


async def get_ai_todos(
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


async def confirm_ai_todo(
    request: AiTodoConfirmRequest, current_user, db: Session
) -> AiTodoConfirmResponse:
    """AI 투두 확인"""
    confirmed_count = 0
    schedule_ids = []
    
    todos = db.query(AiTodo).filter(AiTodo.at_id.in_(request.at_ids)).all()
    for t in todos:
        if not t.is_checked:
            t.is_checked = True
            
            category_mapping = {
                'KPI 기반': '공지',
                '상담 일정 제안': '상담',
                '안부 연락 제안': '개인',
                '신규 상품 분석': '개인'
            }
            sched_cat = category_mapping.get(t.category, '상담')
            
            new_sched = Schedule(
                title=t.title,
                memo=t.memo or "AI To Do 추천에서 My To Do 및 일정으로 등록된 업무입니다.",
                category=sched_cat,
                execution_date=t.execution_date,
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


async def unconfirm_ai_todo(
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
