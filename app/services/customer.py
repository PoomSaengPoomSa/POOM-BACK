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
    MessageResponse,
    VisitMonthCount,
    GenerateReportResponse,
    GenerateReportData,
    SaveReportRequest,
    SaveReportResponse,
    SimulatorChatRequest,
    SimulatorChatResponse,
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
    if tab == "today":
        # 데모용: c_id가 짝수인 고객들을 오늘 방문 고객으로 필터링하되,
        # 실제로 등록된 신규 고객(llm_insight == "신규 등록 고객입니다.")은 오늘 일정이 존재하지 않으면 오늘 방문 목록에서 제외
        from app.models.schedule import Schedule
        from datetime import datetime, time
        
        # 오늘 날짜 범위 계산
        today_start = datetime.combine(datetime.now().date(), time.min)
        today_end = datetime.combine(datetime.now().date(), time.max)
        
        # 오늘 상담 일정이 있는 고객 ID 조회
        today_scheduled_c_ids = [
            s.c_id for s in db.query(Schedule).filter(
                Schedule.u_id == current_user.id,
                Schedule.category == "상담",
                Schedule.execution_date >= today_start,
                Schedule.execution_date <= today_end
            ).all() if s.c_id is not None
        ]
        
        # 데모용 짝수 고객이면서 신규 고객이 아니거나, 오늘 실제 일정이 있는 고객 필터링
        query = query.filter(
            ((Customer.c_id % 2 == 0) & (Customer.llm_insight.is_(None) | (Customer.llm_insight != "신규 등록 고객입니다."))) |
            Customer.c_id.in_(today_scheduled_c_ids)
        )
        
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
                gender=c.gender,
                grade=c.grade,
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
        gender=request.gender or "M",
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
    if request.gender is not None:
        customer.gender = request.gender
        
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


def parse_report_content(report_text: str):
    key_needs = ""
    follow_up = ""
    next_consult = ""
    
    if not report_text:
        return {"key_needs": "", "follow_up": "", "next_consult": ""}
        
    import re
    parts = re.split(r'\[(.*?)\]', report_text)
    if len(parts) >= 3:
        for i in range(1, len(parts), 2):
            header = parts[i].strip()
            content = parts[i+1].strip() if i+1 < len(parts) else ""
            if "배경" in header or "니즈" in header:
                key_needs = content
            elif "진단" in header or "조치" in header or "계획" in header:
                if "진단" in header or "조치" in header:
                    follow_up = content
                else:
                    next_consult = content
            elif "반응" in header or "계획" in header or "상담" in header:
                next_consult = content
                
    if not key_needs and not follow_up and not next_consult:
        lines = [line.strip() for line in report_text.split('\n') if line.strip()]
        if len(lines) >= 1:
            key_needs = lines[0]
        if len(lines) >= 2:
            follow_up = lines[1]
        if len(lines) >= 3:
            next_consult = lines[2]
            
    return {
        "key_needs": key_needs or "상담 내용 분석 중",
        "follow_up": follow_up or "후속 조치 수립 중",
        "next_consult": next_consult or "차기 일정 계획 중"
    }


def extract_title(memo_text: str):
    if not memo_text:
        return "상담 내역"
    sentences = memo_text.split('.')
    first_sentence = sentences[0].strip()
    if len(first_sentence) > 40:
        return first_sentence[:40] + "..."
    return first_sentence + "."


async def get_customer_memos(
    customer_id: int,
    cursor: Optional[str],
    size: int,
    current_user,
    db: Session,
) -> MemoListResponse:
    """이전 상담 타임라인"""
    from app.models.consultation import ConsultationMemo, ConsultationReport
    from app.schemas.customer import TimelineItem, TimelineContent, ScrollInfo
    
    query = db.query(ConsultationMemo).filter(ConsultationMemo.c_id == customer_id)
    
    # Cursor pagination
    if cursor:
        try:
            cursor_id = int(cursor)
            cursor_memo = db.query(ConsultationMemo).filter(ConsultationMemo.cm_id == cursor_id).first()
            if cursor_memo:
                query = query.filter(ConsultationMemo.consult_date < cursor_memo.consult_date)
        except ValueError:
            pass
            
    query = query.order_by(ConsultationMemo.consult_date.desc())
    
    memos = query.limit(size + 1).all()
    has_next = len(memos) > size
    fetched_memos = memos[:size]
    
    timelines = []
    for m in fetched_memos:
        date_str = m.consult_date.strftime("%Y.%m.%d") if m.consult_date else ""
        
        # Fetch associated report to parse content preview
        report = db.query(ConsultationReport).filter(ConsultationReport.cm_id == m.cm_id).first()
        content_dict = {"key_needs": "", "follow_up": "", "next_consult": ""}
        if report and report.content:
            content_dict = parse_report_content(report.content)
            
        timelines.append(
            TimelineItem(
                timelineId=m.cm_id,
                date=date_str,
                memo=m.memo,
                content=TimelineContent(**content_dict)
            )
        )
        
    next_cursor = fetched_memos[-1].cm_id if (has_next and fetched_memos) else None
    
    return MemoListResponse(
        message="상담 타임라인 조회 성공",
        timelines=timelines,
        scrollInfo=ScrollInfo(
            nextCursor=next_cursor,
            hasNext=has_next
        )
    )


async def get_customer_memo_detail(
    customer_id: int, timeline_id: int, current_user, db: Session
) -> MemoDetailResponse:
    """상담 타임라인 상세"""
    from app.models.consultation import ConsultationMemo, ConsultationReport
    from app.schemas.customer import TimelineContent
    
    memo = db.query(ConsultationMemo).filter(
        ConsultationMemo.c_id == customer_id,
        ConsultationMemo.cm_id == timeline_id
    ).first()
    
    if not memo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="상담 상세 내역을 찾을 수 없습니다.",
        )
        
    date_str = memo.consult_date.strftime("%Y.%m.%d") if memo.consult_date else ""
    title_str = extract_title(memo.memo)
    
    report = db.query(ConsultationReport).filter(ConsultationReport.cm_id == memo.cm_id).first()
    content_dict = {"key_needs": "", "follow_up": "", "next_consult": ""}
    if report and report.content:
        content_dict = parse_report_content(report.content)
        
    return MemoDetailResponse(
        message="상담 기록 상세 조회 성공",
        cm_id=memo.cm_id,
        date=date_str,
        title=title_str,
        memo=memo.memo,
        content=TimelineContent(**content_dict)
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



def format_assets_to_str(asset_val):
    if asset_val is None or asset_val == 0:
        return "0원"
    bill = asset_val // 100000000
    rest = asset_val % 100000000
    rest_ten_thousand = round(rest / 10000)
    
    if bill >= 1:
        if rest_ten_thousand > 0:
            return f"{bill}억 {rest_ten_thousand:,}만"
        return f"{bill}억"
    return f"{rest_ten_thousand:,}만"


async def generate_ai_report(
    customer_id: int,
    request,
    current_user,
    db: Session,
) -> GenerateReportResponse:
    """메모어시스턴트 AI 보고서 생성"""
    
    customer = db.query(Customer).filter(Customer.c_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="고객을 찾을 수 없습니다.",
        )
        
    memo_text = request.memo or ""
    
    # Intelligent keyword-based parser for mock LLM report generation
    key_needs = "포트폴리오 다각화 및 종합 세테크 솔루션 수립"
    follow_up = "맞춤형 글로벌 우량 자산 포트폴리오 제안서 작성"
    next_consult = "상담 후 2주일 이내 재방문 예약"
    
    if "달러" in memo_text or "리츠" in memo_text:
        key_needs = "달러 자산 비중 축소 / 국내 리츠 편입 검토"
        follow_up = "리츠 상품 비교안 및 자산 분산 포트폴리오 준비"
        next_consult = "2026.05 초순"
    elif "채권" in memo_text:
        key_needs = "안정적 수익 추구 및 우량 채권 편입 비중 확대"
        follow_up = "금리 인하 대비 장기 국채 및 우량 회사채 제안서 작성"
        next_consult = "2026.04 중순"
    elif "리밸" in memo_text or "리밸런싱" in memo_text or "주식" in memo_text:
        key_needs = "연초 포트폴리오 리밸런싱 및 국내 주식 저평가주 편입"
        follow_up = "국내외 주요 성장주/배당주 분석 보고서 발송 및 자산 재배분 실행"
        next_consult = "2026.02 중순"
    elif "절세" in memo_text or "ISA" in memo_text or "세금" in memo_text:
        key_needs = "연말 절세 솔루션 수립 및 중개형 ISA 활용 극대화"
        follow_up = "ISA 계좌 한도 추가 납입 안내 및 비과세/분리과세 상품 리스트 준비"
        next_consult = "2026.01 초순"
    else:
        clean_memo = memo_text.replace("\n", " ").strip()
        if len(clean_memo) > 10:
            preview = clean_memo[:20] + "..."
            key_needs = f"{preview} 관련 자산 리밸런싱 니즈"
            
    formatted_assets = format_assets_to_str(customer.total_assets)
    
    # Mask name for privacy (e.g. 강도현 -> 강OO, 김OO, etc.)
    customer_name = customer.name
    if customer_name and len(customer_name) >= 2:
        customer_name = customer_name[0] + "O" * (len(customer_name) - 1)
        
    return GenerateReportResponse(
        status=200,
        message="AI 보고서 생성 성공",
        data=GenerateReportData(
            customer_name=customer_name or "고객",
            grade=customer.grade or "일반",
            total_assets=formatted_assets,
            key_needs=key_needs,
            follow_up=follow_up,
            next_consult=next_consult
        )
    )


async def save_ai_report(
    customer_id: int,
    request: SaveReportRequest,
    current_user,
    db: Session,
) -> SaveReportResponse:
    """AI 보고서 및 원본메모 저장"""
    from app.models.consultation import ConsultationMemo, ConsultationReport
    from app.schemas.customer import SaveReportResponseData
    from datetime import datetime

    customer = db.query(Customer).filter(Customer.c_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="고객을 찾을 수 없습니다.",
        )

    # 1. Parse consult_date (expects "YYYY-MM-DD HH:mm:ss")
    try:
        parsed_date = datetime.strptime(request.consult_date, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            parsed_date = datetime.strptime(request.consult_date.split(" ")[0], "%Y-%m-%d")
        except ValueError:
            parsed_date = datetime.now()

    # 2. Save raw memo in consultation_memo
    new_memo = ConsultationMemo(
        consult_date=parsed_date,
        memo=request.memo,
        c_id=customer_id,
        u_id=current_user.id,
    )
    db.add(new_memo)
    db.flush()

    # 3. Format bracketed content for consultation_report
    content_text = (
        f"[주요 니즈]\n{request.content.key_needs}\n\n"
        f"[후속 조치]\n{request.content.follow_up}\n\n"
        f"[차기 상담]\n{request.content.next_consult}"
    )

    # 4. Save formatted report in consultation_report
    new_report = ConsultationReport(
        content=content_text,
        cm_id=new_memo.cm_id,
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_memo)
    db.refresh(new_report)

    # 5. Format created_at string
    created_at_str = new_memo.consult_date.strftime("%Y-%m-%d %H:%M:%S")

    return SaveReportResponse(
        status=201,
        message="보고서 저장 성공",
        data=SaveReportResponseData(
            cm_id=new_memo.cm_id,
            cr_id=new_report.cr_id,
            created_at=created_at_str,
        )
    )


async def simulator_chat(
    customer_id: int,
    request: SimulatorChatRequest,
    current_user,
    db: Session,
) -> SimulatorChatResponse:
    """시뮬레이터 AI 질의 및 자산 시뮬레이션"""
    from app.schemas.customer import SimulatorChatData
    
    customer = db.query(Customer).filter(Customer.c_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="고객을 찾을 수 없습니다.",
        )
        
    question = request.question or ""
    additional_notes = request.additional_notes or ""
    
    # 1. Mask name and format assets
    customer_name = customer.name
    if customer_name and len(customer_name) >= 2:
        customer_name = customer_name[0] + "O" * (len(customer_name) - 1)
    else:
        customer_name = "고객"
        
    formatted_assets = format_assets_to_str(customer.total_assets)
    tendency = customer.tendency or "위험중립형"
    grade = customer.grade or "VIP"
    
    # Gather holdings information
    holdings = []
    if customer.deposit and customer.deposit > 0:
        holdings.append("예적금")
    if customer.investment and customer.investment > 0:
        holdings.append("투자상품")
    if customer.pension and customer.pension > 0:
        holdings.append("연금보험")
    if customer.loan and customer.loan > 0:
        holdings.append("대출")
    holdings_str = " + ".join(holdings) if holdings else "예적금 + 투자상품"

    # Convert total assets in 100M units for simulation
    raw_assets = float(customer.total_assets) / 100000000.0 if customer.total_assets else 32.1234
    if raw_assets <= 0:
        raw_assets = 10.0
        formatted_assets = "10억"
    
    # Expected rate of return based on investment tendency
    expectation_rate = 6.5
    if "적극" in tendency:
        expectation_rate = 8.2
    elif "공격" in tendency:
        expectation_rate = 9.5
    elif "안정" in tendency:
        expectation_rate = 4.5
        
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 2. Intelligent Simulation Engine
    if "절세" in question or "세금" in question or "ISA" in question:
        answer = (
            f"{customer_name} 고객님의 {grade} 등급 특성 및 자산 포트폴리오({formatted_assets}, {holdings_str} 위주 구성)를 기반으로 도출된 맞춤형 절세 전략입니다.\n\n"
            f"1. 금융소득종합과세 대응 및 자산 세팅 방안:\n"
            f"- 현재 보유하신 총 자산 규모({formatted_assets})는 금융소득종합과세 기준선(연 2천만 원)을 상회할 가능성이 매우 높습니다.\n"
            f"- 이자 및 배당 소득 비중을 분리하기 위해 비과세 채권 편입 비중을 높이거나 분리과세 하이일드 펀드 등의 세테크 상품 배분을 확대하시는 것을 추천해 드립니다.\n\n"
            f"2. 중개형 ISA 적극 운용 제안:\n"
            f"- 국내 주식 거래와 저쿠폰 채권 투자를 중개형 ISA를 통해 실행하여 비과세 혜택 및 초과 이자·배당 소득에 대한 9.9% 분리과세 혜택을 극대화할 수 있습니다.\n\n"
            f"3. 추가 정보 검토 반영:\n"
        )
        if additional_notes:
            answer += f"- PB 추가 메모하신 '{additional_notes}' 사항을 고려할 때, 세무 진단을 병행하여 양도소득세 및 금융소득 분산 계획을 사전에 수립하는 것을 적극 권장합니다.\n"
        else:
            answer += f"- 향후 발생할 수 있는 부동산 매도나 거액의 현금성 자산 유입 시 양도세 및 금융소득 분산 계획을 수립해야 합니다.\n"

    elif any(kw in question for kw in ["10년", "수익", "시뮬레이션", "자산"]):
        year_1 = raw_assets * (1 + expectation_rate/100.0)
        year_5 = raw_assets * ((1 + expectation_rate/100.0) ** 5)
        year_10 = raw_assets * ((1 + expectation_rate/100.0) ** 10)
        
        answer = (
            f"{customer_name} 고객님의 {tendency} 성향과 현재 포트폴리오를 기반으로 분석한 향후 10개년 자산 성장 시뮬레이션 결과입니다.\n\n"
            f"[시뮬레이션 가정 및 기준]\n"
            f"- 초기 투자 자산: {formatted_assets}\n"
            f"- 고객 투자 성향: {tendency} (연평균 기대수익률 {expectation_rate}% 가정)\n"
            f"- 인플레이션 및 복리 효과 반영\n\n"
            f"[연도별 예상 자산 가치 추이]\n"
            f"- 1년 후: 약 {year_1:.1f}억 원 수준\n"
            f"- 5년 후: 약 {year_5:.1f}억 원 수준 (누적 수익률 약 +{(year_5/raw_assets-1)*100:.1f}%)\n"
            f"- 10년 후: 약 {year_10:.1f}억 원 수준 (누적 수익률 약 +{(year_10/raw_assets-1)*100:.1f}%)\n\n"
            f"[자산 배분 최적화 권장안]\n"
            f"- 고객님의 주요 보유 자산 유형인 {holdings_str}의 집중도를 다소 완화하고, 기대 변동성을 15% 감축시키면서 동등 수준의 기대수익률을 방어하기 위해 글로벌 분산 투자(미국 배당성장주 및 글로벌 회사채) 비중을 20~25% 수준으로 확대할 것을 제안합니다.\n"
        )
        if additional_notes:
            answer += f"\n[추가 검토 요구사항]: PB 추가 기입하신 '{additional_notes}' 조건에 맞추어 연도별 포트폴리오의 유동성 확보 계획 및 자산 유입 시점 조율 계획이 가미되었습니다."

    else:
        answer = (
            f"문의하신 질문에 대하여 {customer_name} {grade} 고객님의 최신 정보(자산 규모 {formatted_assets}, {tendency} 위험 등급)를 기초로 종합 컨설팅 진단을 실시했습니다.\n\n"
            f"현재 보유 자산군({holdings_str})의 전반적인 포트폴리오 밸런스는 양호한 편이나, 시장 금리 변동 주기 및 포트폴리오 변동성을 면밀히 감시하는 리밸런싱이 지속적으로 요구됩니다.\n\n"
            f"고객님의 투자 성향과 목표에 최적화된 자산 리포트 및 맞춤형 시뮬레이션을 생성하기 위해 구체적인 리밸런싱 시기나 목표 기대수익률을 채팅창에 추가 질문해주시면 상세히 비교 안내해 드리겠습니다.\n"
        )
        if additional_notes:
            answer += f"\n(참고: 추가 입력사항 '{additional_notes}'이 분석에 적극 반영되어 있습니다.)"

    return SimulatorChatResponse(
        status=200,
        message="시뮬레션 진단 성공",
        data=SimulatorChatData(
            answer=answer,
            simulated_at=now_str
        )
    )

