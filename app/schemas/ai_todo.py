from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class AiTodoItem(BaseModel):
    at_id: int
    title: str
    memo: Optional[str] = None
    category: Optional[str] = None
    create_date: datetime
    execution_date: datetime
    is_checked: bool = False
    c_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class AiTodoListResponse(BaseModel):
    todos: List[AiTodoItem]
    total: int


class AiTodoConfirmRequest(BaseModel):
    u_id: str
    at_ids: List[int]


class AiTodoConfirmResponse(BaseModel):
    confirmed: int
    schedule_ids: List[int]


class MessageResponse(BaseModel):
    message: str
