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
    gender: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    birth: Optional[date] = None
    job: Optional[str] = None
    grade: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    investment_type: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[str] = None


class CustomerListResponse(BaseModel):
    c_id: int
    name: str
    phone: str
    email: str
    tendency: str
    total_assets: int
    gender: Optional[str] = None
    grade: Optional[str] = None
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


class ProductMatchItem(BaseModel):
    product_name: str
    product_explanation: str
    is_suitable: bool
    reason: str
    product_type: str
    is_owned: Optional[bool] = False


class MainProductMatchResponse(BaseModel):
    items: List[ProductMatchItem]


class CustomerFeatureItem(BaseModel):
    category: str
    text: str
    date: str
    color: str


class CustomerFeatureResponse(BaseModel):
    features: List[CustomerFeatureItem]
    category_summary: dict


class VisitMonthCount(BaseModel):
    month: str
    count: int


class VisitStatisticsResponse(BaseModel):
    customer_id: int
    avg_visit_cycle_days: Optional[int] = None
    last_visit_date: Optional[date] = None
    total_visits: int = 0
    monthly_visits: Optional[List[VisitMonthCount]] = None


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
class TimelineContent(BaseModel):
    main_content: Optional[str] = None
    special_remarks: Optional[str] = None
    follow_up: Optional[str] = None
    summary: Optional[str] = None

class TimelineItem(BaseModel):
    timelineId: int
    date: str
    memo: str
    content: TimelineContent

class ScrollInfo(BaseModel):
    nextCursor: Optional[int] = None
    hasNext: bool

class MemoTimelineResponse(BaseModel):
    message: str
    timelines: List[TimelineItem]
    scrollInfo: ScrollInfo


class MemoDetailResponse(BaseModel):
    message: str
    cm_id: int
    date: str
    title: str
    memo: str
    content: TimelineContent


class PaginatedCustomerResponse(BaseModel):
    customers: List[CustomerListResponse]
    total: int
    page: int
    size: int


# Aliases for router/service compatibility
CustomerProfileResponse = CustomerDetailResponse
ProductMatchResponse = MainProductMatchResponse
MemoListResponse = MemoTimelineResponse


class MessageResponse(BaseModel):
    message: str


class GenerateReportRequest(BaseModel):
    memo: str
    consult_date: str


class GenerateReportData(BaseModel):
    cm_id: int
    customer_name: str
    main_content: str
    special_remarks: str
    follow_up: str
    summary: Optional[str] = None


class GenerateReportResponse(BaseModel):
    status: int
    message: str
    data: GenerateReportData


class SaveReportContent(BaseModel):
    main_content: str
    special_remarks: str
    follow_up: str
    summary: Optional[str] = None


class SaveReportRequest(BaseModel):
    cm_id: int
    memo: Optional[str] = None
    consult_date: Optional[str] = None
    content: SaveReportContent


class SaveReportResponseData(BaseModel):
    cm_id: int
    cr_id: int
    created_at: str


class SaveReportResponse(BaseModel):
    status: int
    message: str
    data: SaveReportResponseData


class SimulatorChatRequest(BaseModel):
    question: str
    additional_notes: Optional[str] = None


class SimulatorChatData(BaseModel):
    answer: str
    simulated_at: str


class SimulatorChatResponse(BaseModel):
    status: int
    message: str
    data: SimulatorChatData


class SaveSimulatorInfoRequest(BaseModel):
    additional_notes: str


class SimulatorInfoResponse(BaseModel):
    exists: bool
    additional_notes: str
