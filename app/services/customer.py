from typing import Optional, List
from datetime import datetime
from sqlalchemy import extract
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.customer import Customer
from app.models.in_charge import InCharge
from app.models.schedule import Schedule
from app.models.churn_level import ChurnLevel
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
    VisitMonthCount,
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
    from sqlalchemy import func
    max_id = db.query(func.max(Customer.c_id)).scalar()
    new_id = (max_id or 0) + 1

    new_cust = Customer(
        c_id=new_id,
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
    db.flush()

    # 담당자 테이블(in_charge) 매핑 레코드 추가
    in_charge_mapping = InCharge(
        u_id=current_user.id,
        c_id=new_cust.c_id
    )
    db.add(in_charge_mapping)
    
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
    if request.birth is not None:
        customer.birthday = request.birth
    if request.investment_type is not None:
        customer.tendency = request.investment_type
        
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

    # 외래키 제약 조건으로 인한 삭제 실패를 방지하기 위해 자식 테이블 레코드 선제 삭제
    db.query(InCharge).filter(InCharge.c_id == customer_id).delete(synchronize_session=False)
    db.query(ChurnLevel).filter(ChurnLevel.c_id == customer_id).delete(synchronize_session=False)
    db.query(Schedule).filter(Schedule.c_id == customer_id).delete(synchronize_session=False)

    from app.models.customer import CustomerInformation, CustomerRelationship
    db.query(CustomerInformation).filter(CustomerInformation.c_id == customer_id).delete(synchronize_session=False)
    db.query(CustomerRelationship).filter(CustomerRelationship.c_id == customer_id).delete(synchronize_session=False)

    db.delete(customer)
    db.commit()
    return MessageResponse(message="고객 정보가 정상적으로 삭제되었습니다.")


async def get_main_product_match(
    customer_id: int, current_user, db: Session
) -> MainProductMatchResponse:
    """주력 상품 매칭"""
    from app.models.product import ProductMatching
    from app.schemas.customer import ProductMatchItem

    # Query all matching records for the customer, ordered by created_date desc
    matchings = (
        db.query(ProductMatching)
        .filter(ProductMatching.c_id == customer_id)
        .order_by(ProductMatching.created_date.desc())
        .all()
    )

    # Filter to get only the most recent matching for each unique pd_id
    unique_matchings = {}
    for m in matchings:
        if m.pd_id not in unique_matchings:
            unique_matchings[m.pd_id] = m

    items = []
    # Map the unique matchings to ProductMatchItem DTOs
    for m in unique_matchings.values():
        if m.product:
            items.append(
                ProductMatchItem(
                    product_name=m.product.name,
                    product_explanation=m.product.explanation,
                    is_suitable=m.is_suitable,
                    reason=m.reason,
                    product_type=m.product.type,
                )
            )

    return MainProductMatchResponse(items=items)


async def get_customer_feature(
    customer_id: int, current_user, db: Session
) -> CustomerFeatureResponse:
    """메모 기반 고객 특징"""
    from app.models.customer import CustomerInformation

    infos = (
        db.query(CustomerInformation)
        .filter(CustomerInformation.c_id == customer_id)
        .order_by(CustomerInformation.created_date.desc())
        .all()
    )

    CATEGORY_COLORS = {
        "기호": "#f97316",
        "관계": "#db2777",
        "상품": "#0284c7",
        "성향": "#8b5cf6",
        "건강": "#10b981",
        "기타": "#64748b",
    }

    from app.schemas.customer import CustomerFeatureItem

    features = []
    category_summary = {}

    for info in infos:
        date_str = (
            info.created_date.strftime("%Y.%m.%d")
            if info.created_date
            else datetime.now().strftime("%Y.%m.%d")
        )
        color = CATEGORY_COLORS.get(info.category, "#64748b")
        features.append(
            CustomerFeatureItem(
                category=info.category,
                text=info.contents,
                date=date_str,
                color=color,
            )
        )
        if info.category not in category_summary:
            category_summary[info.category] = info.contents

    return CustomerFeatureResponse(
        features=features,
        category_summary=category_summary,
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
    # 오늘 날짜 시간 기준으로 오늘 포함 이전의 상담 방문 기록만 조회 (마지막 방문일 계산용)
    now = datetime.now()
    visits = db.query(Schedule).filter(
        Schedule.u_id == current_user.id,
        Schedule.c_id == customer_id,
        Schedule.category == "상담",
        Schedule.execution_date <= now
    ).order_by(Schedule.execution_date.asc()).all()

    total_visits = len(visits)
    avg_visit_cycle_days = None
    last_visit_date = None

    if total_visits > 0:
        last_visit_date = visits[-1].execution_date.date()
        
    if total_visits >= 2:
        total_days = (visits[-1].execution_date - visits[0].execution_date).days
        avg_visit_cycle_days = round(total_days / (total_visits - 1))

    # 최근 8개월 월별 상담 횟수 계산 (오늘 기준 이전 상담 기록만 포함)
    curr_year = now.year
    curr_month = now.month

    months_to_query = []
    for _ in range(8):
        months_to_query.append((curr_year, curr_month))
        curr_month -= 1
        if curr_month == 0:
            curr_month = 12
            curr_year -= 1

    months_to_query.reverse()

    monthly_visits = []
    for y, m in months_to_query:
        count = db.query(Schedule).filter(
            Schedule.u_id == current_user.id,
            Schedule.c_id == customer_id,
            Schedule.category == "상담",
            Schedule.execution_date <= now,
            extract('year', Schedule.execution_date) == y,
            extract('month', Schedule.execution_date) == m
        ).count()
        
        monthly_visits.append(
            VisitMonthCount(
                month=f"{m:02d}월",
                count=count
            )
        )

    return VisitStatisticsResponse(
        customer_id=customer_id,
        avg_visit_cycle_days=avg_visit_cycle_days,
        last_visit_date=last_visit_date,
        total_visits=total_visits,
        monthly_visits=monthly_visits,
    )


async def get_churn_risk(
    customer_id: int, current_user, db: Session
) -> ChurnRiskResponse:
    """이탈 위험도 분석"""
    churn = db.query(ChurnLevel).filter(
        ChurnLevel.c_id == customer_id
    ).order_by(ChurnLevel.created_date.desc()).first()

    if not churn:
        return ChurnRiskResponse(
            customer_id=customer_id,
            grade=None,
            reason=None,
            created_date=None,
        )

    return ChurnRiskResponse(
        customer_id=customer_id,
        grade=churn.grade,
        reason=churn.reason,
        created_date=churn.created_date,
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

