from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_admin
from app.schemas.admin import (
    SystemDashboardResponse,
    UsageDashboardResponse,
    LogsDashboardResponse,
    EmployeeDashboardResponse,
    BranchStatsResponse,
    WeeklyTrendResponse,
    EmployeeUsageResponse,
    PermissionListResponse,
    AvailableReceiversResponse,
    HandoverListResponse,
    CustomerListResponse,
    TransferRequest,
    TransferResponse,
)
from app.services import admin as admin_service

router = APIRouter(tags=["admin"])


@router.get("/system/dashboard", response_model=SystemDashboardResponse)
async def get_system_dashboard(
    period: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """시스템 대시보드 조회"""
    return await admin_service.get_system_dashboard(period, db)


@router.get("/system/dashboard/usage", response_model=UsageDashboardResponse)
async def get_system_usage(
    period: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """시스템 사용량 대시보드"""
    return await admin_service.get_system_usage(period, db)


@router.get("/system/dashboard/logs", response_model=LogsDashboardResponse)
async def get_system_logs(
    filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """시스템 로그 대시보드"""
    return await admin_service.get_system_logs(filter, db)


@router.get("/employees/dashboard", response_model=EmployeeDashboardResponse)
async def get_employee_dashboard(
    period: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """직원 대시보드 조회"""
    return await admin_service.get_employee_dashboard(period, db)


@router.get("/employees/dashboard/branch-stats", response_model=BranchStatsResponse)
async def get_branch_stats(
    period: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """지점별 통계 조회"""
    return await admin_service.get_branch_stats(period, db)


@router.get("/employees/dashboard/weekly-trend", response_model=WeeklyTrendResponse)
async def get_weekly_trend(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """주간 트렌드 조회"""
    return await admin_service.get_weekly_trend(db)


@router.get("/employees/dashboard/usage", response_model=EmployeeUsageResponse)
async def get_employee_usage(
    period: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """직원 사용량 조회"""
    return await admin_service.get_employee_usage(period, db)


@router.get("/permissions", response_model=PermissionListResponse)
async def get_permissions(
    search: Optional[str] = Query(None),
    branch: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """권한 목록 조회"""
    return await admin_service.get_permissions(search, branch, db)


@router.get(
    "/employees/{u_id}/available-receivers",
    response_model=AvailableReceiversResponse,
)
async def get_available_receivers(
    u_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """이관 가능한 수신자 목록 조회"""
    return await admin_service.get_available_receivers(u_id, db)


@router.get("/handovers", response_model=HandoverListResponse)
async def get_handovers(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """인수인계 목록 조회"""
    return await admin_service.get_handovers(search, status, db)


@router.get("/employees/{u_id}/customers", response_model=CustomerListResponse)
async def get_employee_customers(
    u_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """직원의 고객 목록 조회"""
    return await admin_service.get_employee_customers(u_id, db)


@router.post("/employees/{u_id}/transfer", response_model=TransferResponse)
async def transfer_customers(
    u_id: str,
    request: TransferRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """고객 이관 처리"""
    return await admin_service.transfer_customers(u_id, request, db)
