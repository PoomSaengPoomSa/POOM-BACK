from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerListResponse,
    CustomerDetailResponse,
    CustomerProfileResponse,
    MainProductMatchResponse,
    CustomerFeatureResponse,
    MemoListResponse,
    MemoDetailResponse,
    VisitStatisticsResponse,
    ChurnRiskResponse,
    PortfolioResponse,
    MessageResponse,
)
from app.services import customer as customer_service

router = APIRouter(tags=["customer"])


@router.get("/", response_model=CustomerListResponse)
async def get_customers(
    tab: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """고객 목록 조회"""
    return await customer_service.get_customers(tab, page, size, current_user, db)


@router.post("/", response_model=CustomerProfileResponse)
async def create_customer(
    request: CustomerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """고객 등록"""
    return await customer_service.create_customer(request, current_user, db)


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """고객 자산 조회"""
    return await customer_service.get_customer(customer_id, current_user, db)


@router.patch("/{customer_id}", response_model=CustomerProfileResponse)
async def update_customer(
    customer_id: int,
    request: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """고객 프로필 수정"""
    return await customer_service.update_customer(
        customer_id, request, current_user, db
    )


@router.delete("/{customer_id}", response_model=MessageResponse)
async def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """고객 삭제"""
    return await customer_service.delete_customer(customer_id, current_user, db)


@router.get(
    "/{customer_id}/main_product_match", response_model=MainProductMatchResponse
)
async def get_main_product_match(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """주력 상품 매칭"""
    return await customer_service.get_main_product_match(
        customer_id, current_user, db
    )


@router.get("/{customer_id}/feature", response_model=CustomerFeatureResponse)
async def get_customer_feature(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """메모 기반 고객 특징"""
    return await customer_service.get_customer_feature(
        customer_id, current_user, db
    )


@router.get("/{customer_id}/memos", response_model=MemoListResponse)
async def get_customer_memos(
    customer_id: int,
    cursor: Optional[str] = Query(None),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """이전 상담 타임라인"""
    return await customer_service.get_customer_memos(
        customer_id, cursor, size, current_user, db
    )


@router.get("/{customer_id}/memos/{timeline_id}", response_model=MemoDetailResponse)
async def get_customer_memo_detail(
    customer_id: int,
    timeline_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """상담 타임라인 상세"""
    return await customer_service.get_customer_memo_detail(
        customer_id, timeline_id, current_user, db
    )


# NOTE: API 명세서에서는 /api/customers/... 경로이나, 통합 처리를 위해 동일 라우터에 포함
@router.get(
    "/{customer_id}/visits/statistics", response_model=VisitStatisticsResponse
)
async def get_visit_statistics(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """방문 주기 통계"""
    return await customer_service.get_visit_statistics(
        customer_id, current_user, db
    )


# NOTE: API 명세서에서는 /api/customers/... 경로이나, 통합 처리를 위해 동일 라우터에 포함
@router.get("/{customer_id}/churn-risk", response_model=ChurnRiskResponse)
async def get_churn_risk(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """이탈 위험도 분석"""
    return await customer_service.get_churn_risk(customer_id, current_user, db)


@router.get("/{customer_id}/portfolio", response_model=PortfolioResponse)
async def get_portfolio(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """자산 보유 현황"""
    return await customer_service.get_portfolio(customer_id, current_user, db)
