from typing import Optional
from sqlalchemy.orm import Session
from app.schemas.kpi import (
    SeasonalProductListResponse,
    SeasonalProductDetailResponse,
)


async def get_seasonal_products(
    u_id: Optional[str], current_user, db: Session
) -> SeasonalProductListResponse:
    """시즌 상품 목록 조회"""
    # TODO: 구현
    pass


async def get_seasonal_product_detail(
    product_id: int, current_user, db: Session
) -> SeasonalProductDetailResponse:
    """시즌 상품 상세 조회"""
    # TODO: 구현
    pass
