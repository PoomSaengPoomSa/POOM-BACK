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
    start_datetime: Optional[datetime] = Field(default=None, alias="startDatetime")
    end_datetime: Optional[datetime] = Field(default=None, alias="endDatetime")
    color: Optional[str] = None
    customer_id: Optional[int] = Field(default=None, alias="customerId")
    memo: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)


class ScheduleResponse(BaseModel):
    s_id: int
    title: str
    memo: Optional[str] = None
    category: Optional[str] = None
    execution_date: datetime
    end_datetime: datetime
    u_id: str
    c_id: Optional[int] = None
    at_id: Optional[int] = None
    customer_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str
