from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


# 대시보드 지표
class DashboardMetrics(BaseModel):
    period: Optional[str] = None
    # placeholder fields


# 기능별 사용량
class UsageResponse(BaseModel):
    period: Optional[str] = None


# 트랜잭션 로그
class LogEntry(BaseModel):
    id: int
    action: str
    timestamp: datetime
    user_id: str
    model_config = ConfigDict(from_attributes=True)


class LogListResponse(BaseModel):
    logs: List[LogEntry]
    total: int


# 직원 대시보드
class EmployeeDashboard(BaseModel):
    period: Optional[str] = None


# 부서별 접속률
class BranchStats(BaseModel):
    branch_name: str
    access_rate: float


# 주간 접속률 추이
class WeeklyTrend(BaseModel):
    week: str
    rate: float


# 직원별 기능 사용 현황
class EmployeeUsage(BaseModel):
    u_id: str
    name: str
    feature: str
    count: int


# 권한설정 (직원목록)
class EmployeeListItem(BaseModel):
    u_id: str
    name: str
    branch: str
    position: str
    status: str
    model_config = ConfigDict(from_attributes=True)


class EmployeeListResponse(BaseModel):
    employees: List[EmployeeListItem]
    total: int


# 인수 가능 직원
class AvailableReceiver(BaseModel):
    u_id: str
    name: str
    branch: str


# 인수인계 이력
class HandoverRecord(BaseModel):
    h_id: int
    from_u_id: str
    to_u_id: str
    customer_name: str
    status: str
    h_date: datetime
    model_config = ConfigDict(from_attributes=True)


class HandoverListResponse(BaseModel):
    handovers: List[HandoverRecord]
    total: int


# 담당 고객 목록
class CustomerListItem(BaseModel):
    c_id: int
    name: str
    grade: Optional[str] = None


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


class AvailableReceiversResponse(BaseModel):
    receivers: List[AvailableReceiver]


class CustomerListResponse(BaseModel):
    customers: List[CustomerListItem]
    total: int


class TransferResponse(BaseModel):
    message: str
    success: bool = True
