from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class CustomerCreate(BaseModel):
    name: str
    birth: Optional[date] = None
    job: Optional[str] = None
    grade: Optional[str] = None  # tendency
    phone: str
    email: str
    investment_type: Optional[str] = None
    address: str


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    birth: Optional[date] = None
    job: Optional[str] = None
    grade: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    investment_type: Optional[str] = None
    address: Optional[str] = None


class CustomerListResponse(BaseModel):
    c_id: int
    name: str
    phone: str
    email: str
    tendency: str
    total_assets: int
    model_config = ConfigDict(from_attributes=True)


class CustomerDetailResponse(BaseModel):
    c_id: int
    name: str
    number: str
    birthday: Optional[date] = None
    job: Optional[str] = None
    gender: Optional[str] = None
    email: str
    address: str
    tendency: str
    total_assets: int
    deposit: int
    investment: int
    pension: int
    loan: int
    net_worth: int
    marital_status: bool
    start_date: Optional[date] = None
    grade: str
    llm_insight: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ProductMatchResponse(BaseModel):
    product_name: str
    match_status: str
    product_type: str


class CustomerFeatureResponse(BaseModel):
    features: List[str]
    category_summary: dict


class VisitStatisticsResponse(BaseModel):
    customer_id: int
    avg_visit_cycle_days: Optional[int] = None
    last_visit_date: Optional[date] = None
    total_visits: int = 0


class ChurnRiskResponse(BaseModel):
    customer_id: int
    grade: Optional[str] = None
    reason: Optional[str] = None
    created_date: Optional[datetime] = None


class PortfolioItem(BaseModel):
    account_type: str
    balance: Decimal
    product_name: Optional[str] = None


class PortfolioResponse(BaseModel):
    customer_id: int
    items: List[PortfolioItem]
    total_balance: Decimal


# 상담 타임라인
class MemoTimelineItem(BaseModel):
    cm_id: int
    consult_date: datetime
    memo: str
    u_id: str
    model_config = ConfigDict(from_attributes=True)


class MemoTimelineResponse(BaseModel):
    memos: List[MemoTimelineItem]
    next_cursor: Optional[int] = None


class MemoDetailResponse(BaseModel):
    cm_id: int
    consult_date: datetime
    memo: str
    u_id: str
    report_content: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class PaginatedCustomerResponse(BaseModel):
    customers: List[CustomerListResponse]
    total: int
    page: int
    size: int


# Aliases for router/service compatibility
CustomerProfileResponse = CustomerDetailResponse
MainProductMatchResponse = ProductMatchResponse
MemoListResponse = MemoTimelineResponse


class MessageResponse(BaseModel):
    message: str
