from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class ChartPoint(BaseModel):
    time: str
    value: float


class RecentErrorLog(BaseModel):
    time: str
    service: str
    error_detail: str


class MLPerformanceMetrics(BaseModel):
    name: str
    metric1_name: str
    metric1_val: str
    metric2_name: str
    metric2_val: str
    metric3_name: str
    metric3_val: str
    metric4_name: str
    metric4_val: str


# 대시보드 지표
class DashboardMetrics(BaseModel):
    period: Optional[str] = None
    server_status: str
    api_response_speed: float
    api_response_speed_change: float
    error_rate: float
    error_rate_change: float
    db_status: str
    es_status: str
    ai_status: str
    requests_chart: List[ChartPoint]
    latency_chart: List[ChartPoint]
    error_chart: List[ChartPoint]
    recent_errors: List[RecentErrorLog]
    ml_metrics: List[MLPerformanceMetrics]


# 기능별 사용량
class UsageResponse(BaseModel):
    period: Optional[str] = None


# 트랜잭션 로그
class LogEntry(BaseModel):
    id: str
    time: str
    api: str
    path: str
    ms: str
    status: str
    user_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class LogListResponse(BaseModel):
    logs: List[LogEntry]
    total: int


# 직원 대시보드
class EmployeeDashboard(BaseModel):
    active_count: int
    total_count: int
    access_rate: str
    avg_session_time: str
    total_employees: int
    total_employees_change: str
    active_employees: int
    active_employees_sub: str
    todo_approved_month: int
    todo_approved_month_total: int
    todo_approved_today: int
    todo_approved_today_total: int
    es_status: Optional[str] = "정상"


# 부서별 접속률
class BranchStats(BaseModel):
    branch_name: str
    access_rate: float


# 주간 접속률 추이
class WeeklyTrend(BaseModel):
    name: str
    value: float


# 최근 활동 로그
class RecentActivityLog(BaseModel):
    time: str
    name: str
    branch: str
    feature: str


# 직원별 기능 사용 현황
class EmployeeUsage(BaseModel):
    id: str
    name: str
    branch: str
    email: str
    status: str
    statusClass: str
    stat1: Optional[str] = None
    stat2: Optional[str] = None
    stat3: Optional[str] = None
    stat4: Optional[str] = None
    stat5: Optional[str] = None
    total: Optional[str] = None


# 권한설정 (직원목록)
class EmployeeListItem(BaseModel):
    id: str
    u_id: str
    name: str
    branch: str
    position: str
    status: str
    clients: str
    pending: bool
    branchNote: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class EmployeeListResponse(BaseModel):
    employees: List[EmployeeListItem]
    total: int


# 인수 가능 직원
class AvailableReceiver(BaseModel):
    id: str
    name: str
    clients: str


# 인수인계 이력
class HandoverRecord(BaseModel):
    id: str
    name: str
    title: str
    desc: str
    model_config = ConfigDict(from_attributes=True)


class HandoverListResponse(BaseModel):
    handovers: List[HandoverRecord]
    total: int


# 담당 고객 목록
class CustomerListItem(BaseModel):
    id: str
    name: str
    assets: str


# 발령 처리 요청
class TransferRequest(BaseModel):
    receiver_u_id: str
    customer_ids: List[int]
    target_branch: int


# Aliases & Wrappers for admin router compatibility
SystemDashboardResponse = DashboardMetrics
UsageDashboardResponse = UsageResponse
LogsDashboardResponse = LogListResponse
EmployeeDashboardResponse = EmployeeDashboard
PermissionListResponse = EmployeeListResponse


class BranchStatsResponse(BaseModel):
    stats: List[BranchStats]
    period: Optional[str] = None


class WeeklyTrendResponse(BaseModel):
    trends: List[WeeklyTrend]


class EmployeeUsageResponse(BaseModel):
    usage: List[EmployeeUsage]
    total: int
    recent_activities: List[RecentActivityLog]
    es_status: Optional[str] = "정상"


class AvailableReceiversResponse(BaseModel):
    receivers: List[AvailableReceiver]


class CustomerListResponse(BaseModel):
    customers: List[CustomerListItem]
    total: int


class TransferResponse(BaseModel):
    message: str
    success: bool = True
