from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


class NotificationResponse(BaseModel):
    id: int
    type: str
    content: str
    date: str
    category: str
    today: bool
    isBriefing: bool = Field(alias="isBriefing")
    expandedContent: Optional[List[str]] = Field(default=None, alias="expandedContent")
    state_us: str
    u_id: str
    s_id: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class NotificationCountResponse(BaseModel):
    today_count: int = Field(alias="today_count")

    model_config = ConfigDict(
        populate_by_name=True
    )
