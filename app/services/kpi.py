from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.kpi import (
    SeasonalProductListResponse,
    SeasonalProductDetailResponse,
    PersonalKpiResponse,
    BranchKpiResponse,
)
from app.models.account import PbUser
from app.models.branch import Branch
from app.models.kpi import Kpi
from app.models.product import Product, ProductMatching
from app.models.in_charge import InCharge
from app.models.customer import Customer


def get_seasonal_products(
    u_id: Optional[str], current_user, db: Session
) -> SeasonalProductListResponse:
    """현재 시즌 주력상품 목록 조회"""
    # Product 테이블에서 주력상품(is_main = True) 조회
    products = db.query(Product).filter(Product.is_main == True).all()
    if not products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="등록된 주력 상품 없음",
        )

    formatted_products = []
    for p in products:
        formatted_products.append({
            "pd_id": p.pd_id,
            "name": p.name,
            "type": p.type,
            "update_date": p.update_date.strftime("%Y-%m-%d") if p.update_date else "",
        })

    return SeasonalProductListResponse(
        total_count=len(products),
        products=formatted_products,
    )


def get_seasonal_product_detail(
    product_id: int, current_user, db: Session
) -> SeasonalProductDetailResponse:
    """특정 주력상품 상세 정보 조회"""
    # 1. product_id 유효성 검증
    if product_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 product_id",
        )

    # 2. 상품 조회
    product = db.query(Product).filter(Product.pd_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 상품",
        )

    # 3. 로그인한 PB의 담당 고객 중 적합 판정을 받은 고객 리스트 조회
    suitable_customers_data = (
        db.query(
            Customer.c_id,
            Customer.name,
            Customer.grade,
            Customer.tendency,
            ProductMatching.reason,
        )
        .join(ProductMatching, Customer.c_id == ProductMatching.c_id)
        .join(InCharge, Customer.c_id == InCharge.c_id)
        .filter(
            ProductMatching.pd_id == product_id,
            ProductMatching.is_suitable == True,
            InCharge.u_id == current_user.id,
        )
        .all()
    )

    suitable_customers = [
        {
            "c_id": row.c_id,
            "name": row.name,
            "grade": row.grade,
            "tendency": row.tendency,
            "reason": row.reason,
        }
        for row in suitable_customers_data
    ]

    # 4. 로그인한 PB의 담당 적합 고객 수 산출
    matched_count = len(suitable_customers)
    return SeasonalProductDetailResponse(
        pd_id=product.pd_id,
        name=product.name,
        type=product.type,
        explanation=product.explanation,
        update_date=product.update_date.strftime("%Y-%m-%d") if product.update_date else "",
        issuer=product.issuer,
        features=product.features,
        target_customer=product.target_customer,
        expected_return=product.expected_return,
        return_type=product.return_type,
        season=product.season,
        is_main=product.is_main,
        matched_customer_count=matched_count,
        suitable_customers=suitable_customers,
    )


def get_personal_kpi(u_id: str, db: Session) -> PersonalKpiResponse:
    """로그인한 PB 개인의 당월 KPI 및 전월 대비 증감률 조회"""
    # 1. PB 사용자 검증 (없으면 400 Bad Request)
    pb_user = db.query(PbUser).filter(PbUser.u_id == u_id).first()
    if not pb_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 u_id",
        )

    # 2. 개인 KPI 최신 기록 조회 (kpi_type = 'PB')
    kpi_records = (
        db.query(Kpi)
        .filter(Kpi.u_id == u_id, Kpi.kpi_type == "PB")
        .order_by(Kpi.recorded_date.desc())
        .all()
    )
    if not kpi_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 사용자의 KPI 데이터 없음",
        )

    # 당월(가장 최신) 및 전월(두 번째 최신)
    cur = kpi_records[0]
    prev = kpi_records[1] if len(kpi_records) > 1 else None

    # --- 1. 고객 수 ---
    customer_count = int(cur.current_new_customer)
    customer_goal = int(cur.target_new_customer)
    customer_rate = 0.0
    if customer_goal > 0:
        customer_rate = float(round((customer_count / customer_goal) * 100, 1))

    customer_delta = None
    if prev and prev.current_new_customer > 0:
        customer_delta = float(
            round(
                ((customer_count - prev.current_new_customer) / prev.current_new_customer)
                * 100,
                1,
            )
        )

    # --- 2. AUM (1억 원 단위) ---
    aum = int(cur.current_aum / 100000000)
    aum_goal = int(cur.target_aum / 100000000)
    aum_rate = 0.0
    if cur.target_aum > 0:
        aum_rate = float(round((cur.current_aum / cur.target_aum) * 100, 1))

    aum_delta = None
    if prev and prev.current_aum > 0:
        aum_delta = float(
            round(((cur.current_aum - prev.current_aum) / prev.current_aum) * 100, 1)
        )

    # --- 3. 비이자이익 (1만 원 단위) ---
    non_interest = int(cur.current_non_interest / 10000)
    non_interest_goal = int(cur.target_non_interest / 10000)
    non_interest_rate = 0.0
    if cur.target_non_interest > 0:
        non_interest_rate = float(
            round((cur.current_non_interest / cur.target_non_interest) * 100, 1)
        )

    non_interest_delta = None
    if prev and prev.current_non_interest > 0:
        non_interest_delta = float(
            round(
                ((cur.current_non_interest - prev.current_non_interest)
                 / prev.current_non_interest)
                * 100,
                1,
            )
        )

    return PersonalKpiResponse(
        name=pb_user.name,
        customer_count=customer_count,
        customer_goal=customer_goal,
        customer_rate=customer_rate,
        customer_delta=customer_delta,
        aum=aum,
        aum_goal=aum_goal,
        aum_rate=aum_rate,
        aum_delta=aum_delta,
        non_interest=non_interest,
        non_interest_goal=non_interest_goal,
        non_interest_rate=non_interest_rate,
        non_interest_delta=non_interest_delta,
    )


def get_branch_kpi(u_id: str, db: Session) -> BranchKpiResponse:
    """로그인한 PB 소속 지점의 당월 KPI 및 전월 대비 증감률 조회"""
    # 1. PB 사용자 검증 (없으면 400 Bad Request)
    pb_user = db.query(PbUser).filter(PbUser.u_id == u_id).first()
    if not pb_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 u_id",
        )

    # 2. 지점 정보 조회
    b_id = pb_user.branch
    branch = db.query(Branch).filter(Branch.b_id == b_id).first()
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 지점 정보 없음",
        )

    # 3. 지점 KPI 최신 기록 조회 (kpi_type = 'BRANCH')
    kpi_records = (
        db.query(Kpi)
        .filter(Kpi.b_id == b_id, Kpi.kpi_type == "BRANCH")
        .order_by(Kpi.recorded_date.desc())
        .all()
    )
    if not kpi_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 지점의 KPI 데이터 없음",
        )

    # 당월(가장 최신) 및 전월(두 번째 최신)
    cur = kpi_records[0]
    prev = kpi_records[1] if len(kpi_records) > 1 else None

    # --- 1. 고객 수 ---
    customer_count = int(cur.current_new_customer)
    customer_goal = int(cur.target_new_customer)
    customer_rate = 0.0
    if customer_goal > 0:
        customer_rate = float(round((customer_count / customer_goal) * 100, 1))

    customer_delta = None
    if prev and prev.current_new_customer > 0:
        customer_delta = float(
            round(
                ((customer_count - prev.current_new_customer) / prev.current_new_customer)
                * 100,
                1,
            )
        )

    # --- 2. AUM (1억 원 단위) ---
    aum = int(cur.current_aum / 100000000)
    aum_goal = int(cur.target_aum / 100000000)
    aum_rate = 0.0
    if cur.target_aum > 0:
        aum_rate = float(round((cur.current_aum / cur.target_aum) * 100, 1))

    aum_delta = None
    if prev and prev.current_aum > 0:
        aum_delta = float(
            round(((cur.current_aum - prev.current_aum) / prev.current_aum) * 100, 1)
        )

    # --- 3. 비이자이익 (1만 원 단위) ---
    non_interest = int(cur.current_non_interest / 10000)
    non_interest_goal = int(cur.target_non_interest / 10000)
    non_interest_rate = 0.0
    if cur.target_non_interest > 0:
        non_interest_rate = float(
            round((cur.current_non_interest / cur.target_non_interest) * 100, 1)
        )

    non_interest_delta = None
    if prev and prev.current_non_interest > 0:
        non_interest_delta = float(
            round(
                ((cur.current_non_interest - prev.current_non_interest)
                 / prev.current_non_interest)
                * 100,
                1,
            )
        )

    return BranchKpiResponse(
        branch_name=branch.name,
        customer_count=customer_count,
        customer_goal=customer_goal,
        customer_rate=customer_rate,
        customer_delta=customer_delta,
        aum=aum,
        aum_goal=aum_goal,
        aum_rate=aum_rate,
        aum_delta=aum_delta,
        non_interest=non_interest,
        non_interest_goal=non_interest_goal,
        non_interest_rate=non_interest_rate,
        non_interest_delta=non_interest_delta,
    )

