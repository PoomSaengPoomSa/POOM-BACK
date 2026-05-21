from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.customer import Customer
from app.models.in_charge import InCharge
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
) -> List[CustomerListResponse]:
    """고객 목록 조회"""
    query = db.query(Customer).join(InCharge, Customer.c_id == InCharge.c_id).filter(InCharge.u_id == current_user.id)
    
    # 탭별 필터링 기능 (오늘 방문, 전체 고객 등)
    # 오늘 방문인 경우 간단히 홀수 c_id 고객이 오늘 방문한 것으로 가상의 매칭을 처리하거나 전체를 노출
    if tab == "today":
        # 데모용: c_id가 짝수인 고객들을 오늘 방문 고객으로 필터링
        query = query.filter(Customer.c_id % 2 == 0)
        
    # 페이징 적용
    offset = (page - 1) * size
    customers = query.offset(offset).limit(size).all()
    
    # DTO 포맷 매핑 (number -> phone)
    result = []
    for c in customers:
        result.append(
            CustomerListResponse(
                c_id=c.c_id,
                name=c.name,
                phone=c.number,
                email=c.email,
                tendency=c.tendency,
                total_assets=c.total_assets,
            )
        )
    return result


async def create_customer(
    request: CustomerCreate, current_user, db: Session
) -> CustomerProfileResponse:
    """고객 등록"""
    # 데모용 기본값 기반 생성
    new_cust = Customer(
        c_id=db.query(Customer).count() + 2001,  # 신규 ID 자동 생성
        name=request.name,
        number=request.phone,
        birthday=request.birth,
        job=request.job or "무직",
        gender="M",
        email=request.email,
        address=request.address,
        tendency=request.investment_type or "위험중립형",
        total_assets=0,
        deposit=0,
        investment=0,
        pension=0,
        loan=0,
        net_worth=0,
        marital_status=False,
        grade=request.grade or "VIP",
        llm_insight="신규 등록 고객입니다.",
    )
    db.add(new_cust)
    db.commit()
    db.refresh(new_cust)
    return new_cust


async def get_customer(
    customer_id: int, current_user, db: Session
) -> CustomerDetailResponse:
    """고객 자산 조회"""
    customer = db.query(Customer).filter(Customer.c_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="고객을 찾을 수 없습니다.",
        )
    return customer


async def update_customer(
    customer_id: int,
    request: CustomerUpdate,
    current_user,
    db: Session,
) -> CustomerProfileResponse:
    """고객 프로필 수정"""
    customer = db.query(Customer).filter(Customer.c_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="고객을 찾을 수 없습니다.",
        )
    
    if request.name is not None:
        customer.name = request.name
    if request.phone is not None:
        customer.number = request.phone
    if request.email is not None:
        customer.email = request.email
    if request.job is not None:
        customer.job = request.job
    if request.address is not None:
        customer.address = request.address
    if request.grade is not None:
        customer.grade = request.grade
        
    db.commit()
    db.refresh(customer)
    return customer


async def delete_customer(
    customer_id: int, current_user, db: Session
) -> MessageResponse:
    """고객 삭제"""
    customer = db.query(Customer).filter(Customer.c_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="고객을 찾을 수 없습니다.",
        )
    db.delete(customer)
    db.commit()
    return MessageResponse(message="고객 정보가 정상적으로 삭제되었습니다.")


async def get_main_product_match(
    customer_id: int, current_user, db: Session
) -> MainProductMatchResponse:
    """주력 상품 매칭"""
    return MainProductMatchResponse(
        product_name="우리 테마형 국내 리츠 펀드",
        match_status="부적합",
        product_type="펀드",
    )


async def get_customer_feature(
    customer_id: int, current_user, db: Session
) -> CustomerFeatureResponse:
    """메모 기반 고객 특징"""
    return CustomerFeatureResponse(
        features=[
            "비타500 싫어함, 아메리카노 더블샷 선호",
            "배우자가 최근 퇴직 후 자산 재배치 관심 증가",
            "달러 자산 비중 너무 높다며 불안감 표현, 국내 상품 선호",
            "빠른 의사결정 선호, 서류 설명 길면 집중력 저하",
            "무릎 수술 후 장기 요양 중 - 방문 일정 오전 선호",
        ],
        category_summary={
            "기호": "아메리카노 더블샷 선호",
            "관계": "배우자 퇴직으로 자산 재배치 관심",
            "성향": "빠른 의사결정 선호",
            "상품": "국내 상품 선호",
            "건강": "장기 요양 중, 오전 방문 선호",
        },
    )


async def get_customer_memos(
    customer_id: int,
    cursor: Optional[str],
    size: int,
    current_user,
    db: Session,
) -> MemoListResponse:
    """이전 상담 타임라인"""
    # 데모용 빈 리스트 반환
    return MemoListResponse(memos=[], next_cursor=None)


async def get_customer_memo_detail(
    customer_id: int, timeline_id: int, current_user, db: Session
) -> MemoDetailResponse:
    """상담 타임라인 상세"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="상담 상세 내역을 찾을 수 없습니다.",
    )


async def get_visit_statistics(
    customer_id: int, current_user, db: Session
) -> VisitStatisticsResponse:
    """방문 주기 통계"""
    return VisitStatisticsResponse(
        customer_id=customer_id,
        avg_visit_cycle_days=53,
        total_visits=4,
    )


async def get_churn_risk(
    customer_id: int, current_user, db: Session
) -> ChurnRiskResponse:
    """이탈 위험도 분석"""
    return ChurnRiskResponse(
        customer_id=customer_id,
        grade="양호",
        reason="최근 상담 만족도 매우 높음",
    )


async def get_portfolio(
    customer_id: int, current_user, db: Session
) -> PortfolioResponse:
    """자산 보유 현황"""
    return PortfolioResponse(
        customer_id=customer_id,
        items=[],
        total_balance=0,
    )

