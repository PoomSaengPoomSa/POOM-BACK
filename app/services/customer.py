from typing import Optional
from sqlalchemy.orm import Session
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


async def get_customers(
    tab: Optional[str],
    page: int,
    size: int,
    current_user,
    db: Session,
) -> CustomerListResponse:
    """고객 목록 조회"""
    # TODO: 구현
    pass


async def create_customer(
    request: CustomerCreate, current_user, db: Session
) -> CustomerProfileResponse:
    """고객 등록"""
    # TODO: 구현
    pass


async def get_customer(
    customer_id: int, current_user, db: Session
) -> CustomerDetailResponse:
    """고객 자산 조회"""
    # TODO: 구현
    pass


async def update_customer(
    customer_id: int,
    request: CustomerUpdate,
    current_user,
    db: Session,
) -> CustomerProfileResponse:
    """고객 프로필 수정"""
    # TODO: 구현
    pass


async def delete_customer(
    customer_id: int, current_user, db: Session
) -> MessageResponse:
    """고객 삭제"""
    # TODO: 구현
    pass


async def get_main_product_match(
    customer_id: int, current_user, db: Session
) -> MainProductMatchResponse:
    """주력 상품 매칭"""
    # TODO: 구현
    pass


async def get_customer_feature(
    customer_id: int, current_user, db: Session
) -> CustomerFeatureResponse:
    """메모 기반 고객 특징"""
    # TODO: 구현
    pass


async def get_customer_memos(
    customer_id: int,
    cursor: Optional[str],
    size: int,
    current_user,
    db: Session,
) -> MemoListResponse:
    """이전 상담 타임라인"""
    # TODO: 구현
    pass


async def get_customer_memo_detail(
    customer_id: int, timeline_id: int, current_user, db: Session
) -> MemoDetailResponse:
    """상담 타임라인 상세"""
    # TODO: 구현
    pass


async def get_visit_statistics(
    customer_id: int, current_user, db: Session
) -> VisitStatisticsResponse:
    """방문 주기 통계"""
    # TODO: 구현
    pass


async def get_churn_risk(
    customer_id: int, current_user, db: Session
) -> ChurnRiskResponse:
    """이탈 위험도 분석"""
    # TODO: 구현
    pass


async def get_portfolio(
    customer_id: int, current_user, db: Session
) -> PortfolioResponse:
    """자산 보유 현황"""
    # TODO: 구현
    pass
