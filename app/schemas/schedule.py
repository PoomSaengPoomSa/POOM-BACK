from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class ScheduleCreate(BaseModel):
    category: str
    content: str
    start_datetime: datetime = Field(alias="startDatetime")
    end_datetime: datetime = Field(alias="endDatetime")
    color: Optional[str] = None
    customer_id: Optional[int] = None
    memo: Optional[str] = None


class ScheduleUpdate(BaseModel):
    category: Optional[str] = None
    content: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    color: Optional[str] = None
    memo: Optional[str] = None


class ScheduleResponse(BaseModel):
    s_id: int
    title: str
    memo: Optional[str] = None
    category: Optional[str] = None
    execution_date: datetime
    u_id: str
    c_id: Optional[int] = None
    at_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str
