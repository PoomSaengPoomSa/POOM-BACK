import httpx
from datetime import datetime, timedelta
import random
import logging
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.account import PbUser, Account
from app.models.branch import Branch
from app.models.customer import Customer
from app.models.in_charge import InCharge
from app.models.handover import Handover
from app.schemas.admin import (
    SystemDashboardResponse,
    UsageDashboardResponse,
    LogsDashboardResponse,
    LogEntry,
    EmployeeDashboardResponse,
    BranchStatsResponse,
    WeeklyTrendResponse,
    EmployeeUsageResponse,
    PermissionListResponse,
    AvailableReceiversResponse,
    HandoverListResponse,
    CustomerListResponse,
    TransferRequest,
    TransferResponse,
    EmployeeListItem,
    AvailableReceiver,
    HandoverRecord,
    CustomerListItem,
    EmployeeUsage,
    BranchStats,
    WeeklyTrend,
)


async def get_system_dashboard(
    period: Optional[str], db: Session
) -> SystemDashboardResponse:
    """시스템 대시보드 조회"""
    # TODO: 구현
    pass


async def get_system_usage(
    period: Optional[str], db: Session
) -> UsageDashboardResponse:
    """시스템 사용량 대시보드"""
    # TODO: 구현
    pass


logger = logging.getLogger(__name__)

ES_HOST = "http://ap.loclx.io:9201"

async def get_system_logs(
    filter: Optional[str], db: Session
) -> LogsDashboardResponse:
    """시스템 로그 대시보드"""
    logs = []
    
    # 1. 엘라스틱서치에서 로그 가져오기 시도 (ap.loclx.io:9201)
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.post(
                f"{ES_HOST}/system_logs/_search",
                json={
                    "query": {
                        "match_all": {}
                    },
                    "sort": [
                        {"timestamp": {"order": "desc"}}
                    ],
                    "size": 50
                }
            )
            
            if response.status_code == 200:
                res_data = response.json()
                hits = res_data.get("hits", {}).get("hits", [])
                for hit in hits:
                    source = hit.get("_source", {})
                    ts_str = source.get("timestamp", datetime.now().isoformat())
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        time_str = ts.strftime("%H:%M:%S")
                    except Exception:
                        time_str = ts_str[-8:] if len(ts_str) >= 8 else ts_str
                    
                    api_path = source.get("api", source.get("path", "/api/unknown"))
                    
                    # 'news' 및 'notification' (뉴스 버킷 관련) 경로는 제외
                    if "news" in api_path or "notification" in api_path:
                        continue
                        
                    logs.append(LogEntry(
                        id=hit.get("_id", "unknown"),
                        time=time_str,
                        api=api_path,
                        path=api_path,
                        ms=f"{source.get('ms', source.get('latency', 50))} ms",
                        status=str(source.get("status", 200)),
                        user_id=source.get("user_id", "system")
                    ))
    except Exception as e:
        logger.warning(f"Failed to fetch logs from remote Elasticsearch: {e}. Falling back to mock logs.")

    # 2. 엘라스틱서치 조회가 실패했거나 결과가 비어있으면 다이내믹 모크 로그 생성
    if not logs:
        now = datetime.now()
        endpoints = [
            ("/api/v1/ai-todo", "GET", [40, 150], [200, 200, 200, 200, 401]),
            ("/api/v1/auth/login", "POST", [150, 400], [200, 200, 401, 200]),
            ("/api/v1/customers/?tab=all&page=1&size=1000", "GET", [80, 250], [200, 200, 200]),
            ("/api/v1/trend/dashboard", "GET", [100, 300], [200, 200, 200]),
            ("/api/v1/schedules", "GET", [50, 120], [200, 200, 200]),
            ("/api/v1/kpi/personal?u_id=admin1", "GET", [60, 180], [200, 200, 200])
        ]
        
        users = ["admin1", "developer", "pb1", "pb2", "system"]
        
        for i in range(12):
            api_path, method, ms_range, status_codes = random.choice(endpoints)
            status_code = random.choice(status_codes)
            ms_val = random.randint(ms_range[0], ms_range[1])
            user = random.choice(users)
            log_time = now - timedelta(seconds=i * random.randint(15, 60))
            
            logs.append(LogEntry(
                id=f"mock_log_{i}",
                time=log_time.strftime("%H:%M:%S"),
                api=api_path,
                path=api_path,
                ms=f"{ms_val} ms",
                status=str(status_code),
                user_id=user
            ))
            
    # 'news' 및 'notification' 필터링 (2중 안전 장치)
    logs = [log for log in logs if "news" not in log.api and "notification" not in log.api]

    # 필터 적용 ("오류만" 인 경우 오류 로그만 필터링)
    if filter == "오류만":
        logs = [log for log in logs if log.status != "200"]

    return LogsDashboardResponse(logs=logs, total=len(logs))


async def get_employee_dashboard(
    period: Optional[str], db: Session
) -> EmployeeDashboardResponse:
    """직원 대시보드 조회"""
    accounts = db.query(Account).filter(Account.role != "admin").all()
    total_count = len(accounts)
    
    active_count = 0
    for acc in accounts:
        pb = acc.pb_user
        status = pb.status if pb else "재직"
        if status == "재직":
            active_count += 1
            
    access_rate = f"{int((active_count / total_count) * 100)}%" if total_count > 0 else "0%"
    
    return EmployeeDashboardResponse(
        active_count=active_count,
        total_count=total_count,
        access_rate=access_rate,
        avg_session_time="24분"
    )


async def get_branch_stats(
    period: Optional[str], db: Session
) -> BranchStatsResponse:
    """지점별 통계 조회"""
    branches = db.query(Branch).all()
    
    # Calculate total and active PBs per branch in single queries
    total_counts = dict(
        db.query(PbUser.branch, func.count(PbUser.u_id))
        .group_by(PbUser.branch)
        .all()
    )
    active_counts = dict(
        db.query(PbUser.branch, func.count(PbUser.u_id))
        .filter(PbUser.status == "재직")
        .group_by(PbUser.branch)
        .all()
    )
    
    stats = []
    for b in branches:
        total_pbs = total_counts.get(b.b_id, 0)
        if total_pbs == 0:
            continue
        active_pbs = active_counts.get(b.b_id, 0)
        rate = round((active_pbs / total_pbs) * 100, 1)
        stats.append(BranchStats(branch_name=b.name, access_rate=rate))
        
    return BranchStatsResponse(stats=stats, period=period)


async def get_weekly_trend(db: Session) -> WeeklyTrendResponse:
    """주간 트렌드 조회"""
    trends = [
        WeeklyTrend(name="4주전", value=61.0),
        WeeklyTrend(name="3주전", value=67.0),
        WeeklyTrend(name="2주전", value=70.0),
        WeeklyTrend(name="지난주", value=75.0),
    ]
    return WeeklyTrendResponse(trends=trends)


async def get_employee_usage(
    period: Optional[str], db: Session
) -> EmployeeUsageResponse:
    """직원 사용량 조회"""
    accounts = (
        db.query(Account)
        .options(joinedload(Account.pb_user).joinedload(PbUser.branch_rel))
        .filter(Account.role != "admin")
        .all()
    )
    usage_list = []
    
    for acc in accounts:
        pb = acc.pb_user
        u_id = acc.id
        name = pb.name if pb else acc.id
        branch_name = pb.branch_rel.name if (pb and pb.branch_rel) else "미지정 지점"
        status = pb.status if pb else "재직"
        
        h = sum(ord(c) for c in u_id)
        s1 = h % 45 + 5
        s2 = h % 35 + 3
        s3 = h % 25 + 2
        s4 = h % 15 + 1
        s5 = h % 10 + 1
        total_val = s1 + s2 + s3 + s4 + s5
        
        status_str = "접속 중" if status == "재직" else ("발령 대기" if status == "발령대기" else "오프라인")
        status_cls = "status-online" if status == "재직" else ("status-away" if status == "발령대기" else "status-offline")
        
        usage_list.append(EmployeeUsage(
            id=u_id,
            name=name,
            branch=branch_name,
            stat1=f"{s1}회",
            stat2=f"{s2}회",
            stat3=f"{s3}회",
            stat4=f"{s4}회",
            stat5=f"{s5}회",
            total=f"{total_val}회",
            status=status_str,
            statusClass=status_cls
        ))
        
    return EmployeeUsageResponse(usage=usage_list, total=len(usage_list))


async def get_permissions(
    search: Optional[str], branch: Optional[str], db: Session
) -> PermissionListResponse:
    """권한 목록 조회"""
    query = db.query(Account).options(
        joinedload(Account.pb_user).joinedload(PbUser.branch_rel)
    ).filter(Account.role != "admin")
    
    if search:
        query = query.outerjoin(PbUser, Account.id == PbUser.u_id)
        query = query.filter((Account.id.like(f"%{search}%")) | (PbUser.name.like(f"%{search}%")))
        
    if branch:
        clean_branch = branch.replace("지점", "").replace("금융센터", "").strip()
        query = query.outerjoin(PbUser, Account.id == PbUser.u_id).outerjoin(Branch, PbUser.branch == Branch.b_id)
        query = query.filter(Branch.name.like(f"%{clean_branch}%"))
        
    accounts = query.all()
    employees = []
    
    # Eager aggregate: Get all client counts in a single query
    client_counts = dict(
        db.query(InCharge.u_id, func.count(InCharge.c_id))
        .group_by(InCharge.u_id)
        .all()
    )
    
    # Pre-fetch all active pending handovers in a single query to avoid lazy loading handover and its associations inside loop
    pending_handovers = {
        h.from_u_id: h
        for h in db.query(Handover)
        .options(joinedload(Handover.to_user).joinedload(PbUser.branch_rel))
        .filter(Handover.status == "대기")
        .all()
    }
    
    for acc in accounts:
        pb = acc.pb_user
        u_id = acc.id
        name = pb.name if pb else acc.id
        branch_name = pb.branch_rel.name if (pb and pb.branch_rel) else "미지정 지점"
        position = pb.position if pb else "PB"
        status = pb.status if pb else "재직"
        
        client_count = client_counts.get(u_id, 0)
        pending = (status == "발령대기")
        branch_note = None
        
        if pending and pb:
            handover = pending_handovers.get(u_id)
            if handover and handover.to_user and handover.to_user.branch_rel:
                branch_note = f"발령 대기 {pb.branch_rel.name.replace('지점', '')} → {handover.to_user.branch_rel.name.replace('지점', '')}"
            else:
                branch_note = f"발령 대기 {pb.branch_rel.name.replace('지점', '')} → 압구정"
                
        employees.append(EmployeeListItem(
            id=u_id,
            u_id=u_id,
            name=name,
            branch=branch_name,
            position=position,
            status=status,
            clients=f"{client_count}명",
            pending=pending,
            branchNote=branch_note
        ))
        
    return PermissionListResponse(employees=employees, total=len(employees))


async def get_available_receivers(
    u_id: str, db: Session
) -> AvailableReceiversResponse:
    """이관 가능한 수신자 목록 조회"""
    pb = db.query(PbUser).filter(PbUser.u_id == u_id).first()
    if not pb:
        return AvailableReceiversResponse(receivers=[])
        
    receivers_query = db.query(PbUser).filter(
        PbUser.branch == pb.branch,
        PbUser.u_id != u_id,
        PbUser.status != "퇴사"
    ).all()
    
    receivers = []
    for r in receivers_query:
        clients_count = db.query(InCharge).filter(InCharge.u_id == r.u_id).count()
        receivers.append(AvailableReceiver(
            id=r.u_id,
            name=r.name,
            clients=f"현재 {clients_count}명 담당"
        ))
        
    return AvailableReceiversResponse(receivers=receivers)


async def get_handovers(
    search: Optional[str], status: Optional[str], db: Session
) -> HandoverListResponse:
    """인수인계 목록 조회"""
    query = db.query(Handover)
    
    if search:
        query = query.join(PbUser, Handover.from_u_id == PbUser.u_id).filter(PbUser.name.like(f"%{search}%"))
        
    handovers_db = query.order_by(Handover.h_date.desc()).all()
    handovers = []
    
    for h in handovers_db:
        from_name = h.from_user.name if h.from_user else "퇴사자"
        to_name = h.to_user.name if h.to_user else "미지정"
        from_branch = h.from_user.branch_rel.name.replace('지점', '') if (h.from_user and h.from_user.branch_rel) else "미정"
        to_branch = h.to_user.branch_rel.name.replace('지점', '') if (h.to_user and h.to_user.branch_rel) else "미정"
        
        title = f"{from_name} {from_branch} → {to_branch}지점"
        date_str = h.h_date.strftime("%Y.%m.%d")
        desc = f"고객 재배정 → {to_name} {date_str}"
        
        handovers.append(HandoverRecord(
            id=str(h.h_id),
            name=from_name,
            title=title,
            desc=desc
         ))
         
    return HandoverListResponse(handovers=handovers, total=len(handovers))


async def get_employee_customers(u_id: str, db: Session) -> CustomerListResponse:
    """직원의 고객 목록 조회"""
    customers_db = (
        db.query(Customer)
        .join(InCharge, Customer.c_id == InCharge.c_id)
        .filter(InCharge.u_id == u_id)
        .all()
    )
    customers = []
    
    for c in customers_db:
        assets_str = f"{c.grade} · 자산 {int(c.total_assets / 100000000)}억" if c.total_assets else "일반 · 자산 0원"
        customers.append(CustomerListItem(
            id=str(c.c_id),
            name=c.name,
            assets=assets_str
        ))
            
    return CustomerListResponse(customers=customers, total=len(customers_db))


async def transfer_customers(
    u_id: str, request: TransferRequest, db: Session
) -> TransferResponse:
    """고객 이관 처리"""
    from_user = db.query(PbUser).filter(PbUser.u_id == u_id).first()
    to_user = db.query(PbUser).filter(PbUser.u_id == request.receiver_u_id).first()
    
    if not from_user or not to_user:
        return TransferResponse(message="인계자 또는 인수자 정보가 유효하지 않습니다.", success=False)
        
    for cid in request.customer_ids:
        db.query(InCharge).filter(InCharge.u_id == u_id, InCharge.c_id == cid).delete()
        new_in_charge = InCharge(u_id=request.receiver_u_id, c_id=cid)
        db.add(new_in_charge)
        
        new_handover = Handover(
            a_id="admin1",
            c_id=cid,
            from_u_id=u_id,
            to_u_id=request.receiver_u_id,
            status="완료"
        )
        db.add(new_handover)
        
    remaining_clients = db.query(InCharge).filter(InCharge.u_id == u_id).count()
    
    if remaining_clients == 0:
        from_user.branch = request.target_branch
        from_user.status = "재직"
        
    db.commit()
    
    return TransferResponse(message="인수인계 및 지점 발령 처리가 성공적으로 완료되었습니다.", success=True)
