from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
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
    MessageResponse,
    GenerateReportRequest,
    GenerateReportResponse,
    SaveReportRequest,
    SaveReportResponse,
    SimulatorChatRequest,
    SimulatorChatResponse,
)
from app.services import customer as customer_service

router = APIRouter(tags=["Customer"])


@router.get("/", response_model=List[CustomerListResponse])
def get_customers(
    tab: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(1000, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    """고객 목록 조회"""
    return customer_service.get_customers(tab, page, size, current_user, db)


@router.post("/", response_model=CustomerProfileResponse)
def create_customer(
    request: CustomerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """고객 등록"""
    return customer_service.create_customer(request, current_user, db)


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """고객 자산 조회"""
    return customer_service.get_customer(customer_id, current_user, db)


@router.patch("/{customer_id}", response_model=CustomerProfileResponse)
def update_customer(
    customer_id: int,
    request: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """고객 프로필 수정"""
    return customer_service.update_customer(
        customer_id, request, current_user, db
    )


@router.delete("/{customer_id}", response_model=MessageResponse)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """고객 삭제"""
    return customer_service.delete_customer(customer_id, current_user, db)


@router.get(
    "/{customer_id}/main_product_match", response_model=MainProductMatchResponse
)
def get_main_product_match(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """주력 상품 매칭"""
    return customer_service.get_main_product_match(
        customer_id, current_user, db
    )


@router.get("/{customer_id}/feature", response_model=CustomerFeatureResponse)
def get_customer_feature(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """메모 기반 고객 특징"""
    return customer_service.get_customer_feature(
        customer_id, current_user, db
    )


@router.get("/{customer_id}/memos", response_model=MemoListResponse)
def get_customer_memos(
    customer_id: int,
    cursor: Optional[str] = Query(None),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """이전 상담 타임라인"""
    return customer_service.get_customer_memos(
        customer_id, cursor, size, current_user, db
    )


@router.get("/{customer_id}/memos/{timeline_id}", response_model=MemoDetailResponse)
def get_customer_memo_detail(
    customer_id: int,
    timeline_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """상담 타임라인 상세"""
    return customer_service.get_customer_memo_detail(
        customer_id, timeline_id, current_user, db
    )


# NOTE: API 명세서에서는 /api/customers/... 경로이나, 통합 처리를 위해 동일 라우터에 포함
@router.get(
    "/{customer_id}/visits-statistics", response_model=VisitStatisticsResponse
)
def get_visit_statistics(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """방문 주기 통계"""
    return customer_service.get_visit_statistics(
        customer_id, current_user, db
    )


# NOTE: API 명세서에서는 /api/customers/... 경로이나, 통합 처리를 위해 동일 라우터에 포함
@router.get("/{customer_id}/churn-risk", response_model=ChurnRiskResponse)
def get_churn_risk(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """이탈 위험도 분석"""
    return customer_service.get_churn_risk(customer_id, current_user, db)


@router.post("/{customer_id}/reports/generate", response_model=GenerateReportResponse)
def generate_ai_report(
    customer_id: int,
    request: GenerateReportRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """메모어시스턴트 AI 보고서 생성"""
    return customer_service.generate_ai_report(
        customer_id, request, current_user, db
    )


@router.post("/{customer_id}/reports", response_model=SaveReportResponse, status_code=201)
def save_ai_report(
    customer_id: int,
    request: SaveReportRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """AI 보고서 및 원본메모 저장"""
    return customer_service.save_ai_report(
        customer_id, request, current_user, db
    )


@router.post("/{customer_id}/simulator/chat", response_model=SimulatorChatResponse)
def simulator_chat(
    customer_id: int,
    request: SimulatorChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """시뮬레이터 AI 질의 및 자산 시뮬레이션"""
    return customer_service.simulator_chat(
        customer_id, request, current_user, db
    )
