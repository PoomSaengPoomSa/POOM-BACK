from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.kpi import (
    SeasonalProductListResponse,
    SeasonalProductDetailResponse,
    PersonalKpiResponse,
    BranchKpiResponse,
)
from app.services import kpi as kpi_service

router = APIRouter(tags=["KPI"])


@router.get("/seasonal-products", response_model=SeasonalProductListResponse)
async def get_seasonal_products(
    u_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """시즌 상품 목록 조회"""
    return await kpi_service.get_seasonal_products(u_id, current_user, db)


@router.get(
    "/seasonal-products/{product_id}",
    response_model=SeasonalProductDetailResponse,
)
async def get_seasonal_product_detail(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """시즌 상품 상세 조회"""
    return await kpi_service.get_seasonal_product_detail(
        product_id, current_user, db
    )


@router.get("/personal", response_model=PersonalKpiResponse)
async def get_personal_kpi(
    u_id: str = Query(..., description="PB 사번"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """로그인한 PB 개인의 당월 KPI 합계 및 전월 대비 증감률 조회"""
    return await kpi_service.get_personal_kpi(u_id, db)


@router.get("/branch", response_model=BranchKpiResponse)
async def get_branch_kpi(
    u_id: str = Query(..., description="PB 사번"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """로그인한 PB 소속 지점의 당월 KPI 합계 및 전월 대비 증감률 조회"""
    return await kpi_service.get_branch_kpi(u_id, db)

