from typing import Optional, List
from datetime import datetime
import os
from sqlalchemy import extract
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status, BackgroundTasks
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
    SimulatorInfoResponse,
)

_current_file = os.path.abspath(__file__)
_services_dir = os.path.dirname(_current_file)
_app_dir = os.path.dirname(_services_dir)
_back_dir = os.path.dirname(_app_dir)
_poom_root = os.path.dirname(_back_dir)

POOM_AI_DIR = os.path.join(_poom_root, "POOM-AI")




def get_customers(
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
        
        # 실제 오늘 일정이 존재하는 고객 정보만 정확하게 조회하도록 필터링
        query = query.filter(Customer.c_id.in_(today_scheduled_c_ids))
        
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


def create_customer(
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


def get_customer(
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


def update_customer(
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


def delete_customer(
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


def get_main_product_match(
    customer_id: int, current_user, db: Session
) -> MainProductMatchResponse:
    """주력 상품 매칭"""
    from app.models.product import ProductMatching, CustomerProduct, Product
    from app.schemas.customer import ProductMatchItem
    from app.models.customer import Customer

    # 1. is_main이 1 (True)인 주력 상품 목록 조회
    main_products = (
        db.query(Product)
        .filter(Product.is_main == True)
        .all()
    )

    # 2. 고객의 보유 상품 pd_id 목록 조회
    owned_product_ids = {
        cp.pd_id
        for cp in db.query(CustomerProduct.pd_id)
        .filter(CustomerProduct.c_id == customer_id)
        .all()
    }

    # 3. 고객의 상품 매칭 데이터 조회 (최신순)
    matchings = (
        db.query(ProductMatching)
        .filter(ProductMatching.c_id == customer_id)
        .order_by(ProductMatching.created_date.desc())
        .all()
    )

    unique_matchings = {}
    for m in matchings:
        if m.pd_id not in unique_matchings:
            unique_matchings[m.pd_id] = m

    # 4. 고객 투자성향 조회 (매칭 데이터 없을 때를 대비한 기본 사유 작성을 위함)
    customer = db.query(Customer).filter(Customer.c_id == customer_id).first()
    tendency = customer.tendency if customer and customer.tendency else "안정추구형"

    items = []
    # 5. 주력 상품을 기준으로 DTO 데이터 생성
    for prod in main_products:
        is_owned = prod.pd_id in owned_product_ids
        
        # 해당 주력 상품의 매칭 이력이 매칭 테이블에 존재하는지 확인
        matching = unique_matchings.get(prod.pd_id)
        if matching:
            is_suitable = matching.is_suitable
            reason = matching.reason
        else:
            is_suitable = 1 # 기본값 적합 (Integer)
            reason = f"고객님의 투자 성향({tendency})에 적합한 상품입니다."

        items.append(
            ProductMatchItem(
                product_name=prod.name,
                product_explanation=prod.explanation,
                is_suitable=is_suitable,
                reason=reason,
                product_type=prod.type,
                is_owned=is_owned,
            )
        )

    return MainProductMatchResponse(items=items)


def get_customer_feature(
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
    main_content = ""
    special_remarks = ""
    follow_up = ""
    
    if not report_text:
        return {"main_content": "", "special_remarks": "", "follow_up": ""}
        
    import re
    parts = re.split(r'\[(.*?)\]', report_text)
    if len(parts) >= 3:
        for i in range(1, len(parts), 2):
            header = parts[i].strip()
            content = parts[i+1].strip() if i+1 < len(parts) else ""
            if "내용" in header or "배경" in header or "니즈" in header:
                main_content = content
            elif "특이" in header or "상담" in header or "계획" in header:
                special_remarks = content
            elif "조치" in header or "진단" in header:
                follow_up = content
                
    if not main_content and not special_remarks and not follow_up:
        lines = [line.strip() for line in report_text.split('\n') if line.strip()]
        if len(lines) >= 1:
            main_content = lines[0]
        if len(lines) >= 2:
            special_remarks = lines[1]
        if len(lines) >= 3:
            follow_up = lines[2]
            
    return {
        "main_content": main_content or "-",
        "special_remarks": special_remarks or "-",
        "follow_up": follow_up or "-"
    }


def extract_title(memo_text: str):
    if not memo_text:
        return "상담 내역"
    sentences = memo_text.split('.')
    first_sentence = sentences[0].strip()
    if len(first_sentence) > 40:
        return first_sentence[:40] + "..."
    return first_sentence + "."


def get_customer_memos(
    customer_id: int,
    cursor: Optional[str],
    size: int,
    current_user,
    db: Session,
) -> MemoListResponse:
    """이전 상담 타임라인"""
    from app.models.consultation import ConsultationMemo, ConsultationReport
    from app.schemas.customer import TimelineItem, TimelineContent, ScrollInfo
    
    query = db.query(ConsultationMemo).outerjoin(ConsultationMemo.report).options(joinedload(ConsultationMemo.report)).filter(ConsultationMemo.c_id == customer_id)
    
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
        
        # Fetch associated report to populate preview
        report = m.report
        content_dict = {
            "main_content": report.key_contents if report else "",
            "special_remarks": report.special_notes if report else "",
            "follow_up": report.follow_up_actions if report else "",
            "summary": report.summary if report else ""
        }
            
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


def get_customer_memo_detail(
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
    content_dict = {
        "main_content": report.key_contents if report else "",
        "special_remarks": report.special_notes if report else "",
        "follow_up": report.follow_up_actions if report else "",
        "summary": report.summary if report else ""
    }
        
    return MemoDetailResponse(
        message="상담 기록 상세 조회 성공",
        cm_id=memo.cm_id,
        date=date_str,
        title=title_str,
        memo=memo.memo,
        content=TimelineContent(**content_dict)
    )


def get_visit_statistics(
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
        # Perform counting in Python memory instead of executing separate SQL count queries in a loop
        count = sum(1 for v in visits if v.execution_date and v.execution_date.year == y and v.execution_date.month == m)
        
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


def get_churn_risk(
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
            explain_reason=None,
            created_date=None,
        )

    return ChurnRiskResponse(
        customer_id=customer_id,
        grade=churn.grade,
        reason=churn.reason,
        explain_reason=churn.explain_reason,
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


def run_llm_structure_memo(memo_text: str):
    import requests
    try:
        response = requests.post("http://poom-ai:8001/api/v1/consult-assistant", json={"memo": memo_text}, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"AI API 실행 에러: {e}")
        raise e


def generate_ai_report(
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
    
    # 1. LLM 분석을 통한 구조화 실행 (Subprocess 연동)
    try:
        report_data = run_llm_structure_memo(memo_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 보고서 생성 중 오류가 발생했습니다: {str(e)}"
        )
        
    # 3. LLM 결과 매핑 및 줄바꿈 처리
    def clean_item(item: str) -> str:
        if not item:
            return ""
        item = item.strip()
        # 불필요한 마크다운 리스트 기호(-, *) 제거
        if item.startswith("-"):
            item = item[1:].strip()
        elif item.startswith("*"):
            item = item[1:].strip()
        # 숫자 번호형 리스트 접두사(예: "1. ") 제거
        import re
        item = re.sub(r'^\d+\.\s*', '', item)
        return item

    key_contents_list = [clean_item(x) for x in report_data.get("key_contents", []) if x]
    special_notes_list = [clean_item(x) for x in report_data.get("special_notes", []) if x]
    follow_up_list = [clean_item(x) for x in report_data.get("follow_up_actions", []) if x]
    summary = report_data.get("summary", "")
    
    main_content = "\n".join([f"- {item}" for item in key_contents_list if item]) if key_contents_list else "-"
    special_remarks = "\n".join([f"- {item}" for item in special_notes_list if item]) if special_notes_list else "-"
    follow_up = "\n".join([f"- {item}" for item in follow_up_list if item]) if follow_up_list else "-"
    
    # 고객 이름 그대로 표시
    customer_name = customer.name
        
    return GenerateReportResponse(
        status=200,
        message="AI 보고서 생성 성공",
        data=GenerateReportData(
            cm_id=None,
            customer_name=customer_name or "고객",
            main_content=main_content,
            special_remarks=special_remarks,
            follow_up=follow_up,
            summary=summary
        )
    )


def run_customer_feature_agent(customer_id: int):
    """POOM-AI 고객 특징 추출 및 상품 매칭 에이전트를 백그라운드 API 호출로 실행"""
    import requests
    try:
        print(f"[Background] Starting Customer Feature Agent for Customer ID: {customer_id}")
        response = requests.post("http://poom-ai:8001/api/v1/customer-feature", json={"c_id": customer_id}, timeout=120)
        response.raise_for_status()
        print(f"[+] Customer Feature Agent 실행 완료 (customer_id: {customer_id}): {response.json()}")
    except Exception as e:
        print(f"[-] Customer Feature Agent 실행 중 에러 발생 (customer_id: {customer_id}): {e}")


def save_ai_report(
    customer_id: int,
    request: SaveReportRequest,
    current_user,
    db: Session,
    background_tasks: BackgroundTasks = None,
) -> SaveReportResponse:
    """AI 보고서 및 원본 상담 메모 저장"""
    from app.models.consultation import ConsultationMemo, ConsultationReport
    from app.schemas.customer import SaveReportResponseData
    
    cm_id = request.cm_id
    memo_record = None
    
    if not cm_id:
        memo_text = request.memo or ""
        parsed_date = datetime.now()
        
        memo_record = ConsultationMemo(
            consult_date=parsed_date,
            memo=memo_text,
            c_id=customer_id,
            u_id=current_user.id
        )
        db.add(memo_record)
        db.commit()
        db.refresh(memo_record)
        cm_id = memo_record.cm_id
    else:
        # 전달받은 cm_id가 유효한지 검증
        memo_record = db.query(ConsultationMemo).filter(ConsultationMemo.cm_id == cm_id).first()
        if not memo_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="연관된 상담 메모를 찾을 수 없습니다.",
            )
        
    # consultation_report에 적재
    new_report = ConsultationReport(
        key_contents=request.content.main_content,
        special_notes=request.content.special_remarks,
        follow_up_actions=request.content.follow_up,
        summary=request.content.summary or "",
        cm_id=cm_id
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    
    # DB 트랜잭션 완료 후 백그라운드 태스크로 분석 에이전트 구동
    if background_tasks:
        background_tasks.add_task(run_customer_feature_agent, customer_id)
        
    created_at_str = memo_record.consult_date.strftime("%Y-%m-%d %H:%M:%S")
    
    return SaveReportResponse(
        status=201,
        message="보고서 저장 성공",
        data=SaveReportResponseData(
            cm_id=cm_id,
            cr_id=new_report.cr_id,
            created_at=created_at_str,
        )
    )


def simulator_chat(
    customer_id: int,
    request: SimulatorChatRequest,
    current_user,
    db: Session,
) -> SimulatorChatResponse:
    """시뮬레이터 AI 질의 및 자산 시뮬레이션 (FastAPI API 연동)"""
    from app.schemas.customer import SimulatorChatData
    import requests
    
    customer = db.query(Customer).filter(Customer.c_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="고객을 찾을 수 없습니다.",
        )
        
    question = request.question or ""
    
    try:
        response = requests.post(
            "http://poom-ai:8001/api/v1/simulator/chat", 
            json={"c_id": customer_id, "question": question},
            timeout=60
        )
        response.raise_for_status()
        answer = response.json()["answer"]
    except Exception as e:
        print(f"Simulator API 실행 에러: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 시뮬레이터 응답을 생성하는 중 오류가 발생했습니다: {str(e)}"
        )
        
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return SimulatorChatResponse(
        status=200,
        message="시뮬레이션 진단 성공",
        data=SimulatorChatData(
            answer=answer,
            simulated_at=now_str
        )
    )


def save_simulator_info(
    customer_id: int,
    request,
    current_user,
    db: Session,
) -> MessageResponse:
    """시뮬레이터 정보 및 추가 입력사항 저장 (txt 파일 생성)"""
    from app.schemas.customer import MessageResponse
    import os
    
    customer = db.query(Customer).filter(Customer.c_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="고객을 찾을 수 없습니다.",
        )
        
    # Format properties
    customer_name = customer.name or "고객"
    grade = customer.grade or "일반"
    birthday = customer.birthday.strftime("%Y.%m.%d") if customer.birthday else "-"
    job = customer.job or "무직"
    tendency = customer.tendency or "위험중립형"
    total_assets = format_assets_to_str(customer.total_assets)
    llm_insight = customer.llm_insight or "등록된 AI 인사이트가 없습니다."
    additional_notes = request.additional_notes or ""
    
    # Format markdown content
    md_content = (
        f"# 고객 시뮬레이션 정보 - {customer_name} ({grade})\n\n"
        f"## 고객 기본 정보\n"
        f"- **고객명(등급)**: {customer_name} ({grade})\n"
        f"- **생년월일**: {birthday}\n"
        f"- **직업**: {job}\n"
        f"- **투자 성향**: {tendency}\n"
        f"- **총자산**: {total_assets}\n\n"
        f"## AI 분석 인사이트\n"
        f"{llm_insight}\n\n"
        f"## 추가 입력사항 (PB 추가 메모)\n"
        f"{additional_notes}\n"
    )
    
    # Ensure directory exists and write markdown file
    ai_data_dir = os.path.join(POOM_AI_DIR, "agent", "simulator", "data")
    os.makedirs(ai_data_dir, exist_ok=True)
    
    md_path = os.path.join(ai_data_dir, f"customer_{customer_id}.md")
    try:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"임시 md 파일 저장 실패: {str(e)}"
        )
        
    # Reset conversation history by deleting the JSON history file
    history_path = os.path.join(ai_data_dir, f"customer_{customer_id}_history.json")
    if os.path.exists(history_path):
        try:
            os.remove(history_path)
        except Exception:
            pass
            
    return MessageResponse(message="시뮬레이터 정보 및 추가 입력사항이 정상적으로 저장되었습니다.")


def get_simulator_info(
    customer_id: int,
    current_user,
    db: Session,
) -> SimulatorInfoResponse:
    """시뮬레이터 정보 조회 및 추가 입력사항 파싱"""
    from app.schemas.customer import SimulatorInfoResponse
    import os
    import json
    
    customer = db.query(Customer).filter(Customer.c_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="고객을 찾을 수 없습니다.",
        )
        
    ai_data_dir = os.path.join(POOM_AI_DIR, "agent", "simulator", "data")
    
    md_path = os.path.join(ai_data_dir, f"customer_{customer_id}.md")
    txt_path = os.path.join(ai_data_dir, f"customer_{customer_id}.txt")
    
    exists = False
    additional_notes = ""
    
    if os.path.exists(md_path):
        exists = True
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            header_str = "## 추가 입력사항 (PB 추가 메모)\n"
            if header_str in content:
                additional_notes = content.split(header_str)[1].strip()
        except Exception:
            pass
    elif os.path.exists(txt_path):
        exists = True
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()
            header_str = "3. 추가 입력사항 (PB 추가 메모)\n"
            if header_str in content:
                additional_notes = content.split(header_str)[1].strip()
        except Exception:
            pass
            
    # Load conversation history if exists
    history = []
    history_path = os.path.join(ai_data_dir, f"customer_{customer_id}_history.json")
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            pass
            
    return SimulatorInfoResponse(
        exists=exists,
        additional_notes=additional_notes,
        history=history
    )

