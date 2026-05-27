from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date


class SeasonalProduct(BaseModel):
    pd_id: int
    name: str
    type: str
    update_date: str  # Format: "YYYY-MM-DD"

    model_config = ConfigDict(from_attributes=True)


class SeasonalProductListResponse(BaseModel):
    total_count: int
    products: List[SeasonalProduct]


class SuitableCustomerInfo(BaseModel):
    c_id: int
    name: str
    grade: str
    tendency: str
    reason: str

    model_config = ConfigDict(from_attributes=True)
class SeasonalProductDetailResponse(BaseModel):
    pd_id: int
    name: str
    type: str
    explanation: str
    update_date: str  # Format: "YYYY-MM-DD"
    
    # 🚀 Rich UI Developer Enhancements
    issuer: str
    features: str
    target_customer: str
    expected_return: float
    return_type: str
    season: str
    is_main: bool
    matched_customer_count: Optional[int] = None
    suitable_customers: List[SuitableCustomerInfo] = []

    model_config = ConfigDict(from_attributes=True)



class PersonalKpiResponse(BaseModel):
    name: str
    customer_count: int
    customer_goal: int
    customer_rate: float
    customer_delta: Optional[float] = None
    aum: int
    aum_goal: int
    aum_rate: float
    aum_delta: Optional[float] = None
    non_interest: int
    non_interest_goal: int
    non_interest_rate: float
    non_interest_delta: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class BranchKpiResponse(BaseModel):
    branch_name: str
    customer_count: int
    customer_goal: int
    customer_rate: float
    customer_delta: Optional[float] = None
    aum: int
    aum_goal: int
    aum_rate: float
    aum_delta: Optional[float] = None
    non_interest: int
    non_interest_goal: int
    non_interest_rate: float
    non_interest_delta: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


from app.schemas.schedule import ScheduleResponse
from app.schemas.ai_todo import AiTodoItem

class DashboardSummaryResponse(BaseModel):
    personal_kpi: PersonalKpiResponse
    branch_kpi: BranchKpiResponse
    seasonal_products: SeasonalProductListResponse
    schedules: List[ScheduleResponse]
    ai_todos: List[AiTodoItem]



