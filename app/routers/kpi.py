from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.kpi import (
    SeasonalProductListResponse,
    SeasonalProductDetailResponse,
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
