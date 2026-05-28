import httpx
from datetime import datetime, timedelta
import logging
import json
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
    ChartPoint,
    RecentErrorLog,
    MLPerformanceMetrics,
    RecentActivityLog,
)

logger = logging.getLogger(__name__)

from app.config import get_settings
settings = get_settings()
ES_HOST = settings.ES_HOST


# ────────────────────────────────────────────────
# 인덱스 매핑만 보장 (seed 데이터 없음)
# ────────────────────────────────────────────────

async def ensure_system_logs_index(es_host: str):
    """system_logs 인덱스 매핑이 없으면 생성 (데이터 적재 X)"""
    try:
        async with httpx.AsyncClient(timeout=3.0, headers={"bypass-tunnel-reminder": "true"}, http2=False) as client:
            idx_resp = await client.get(f"{es_host}/system_logs")
            if idx_resp.status_code == 200:
                return  # 이미 존재
            mapping = {
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "api":       {"type": "keyword"},
                        "path":      {"type": "keyword"},
                        "method":    {"type": "keyword"},
                        "status":    {"type": "integer"},
                        "ms":        {"type": "integer"},
                        "user_id":   {"type": "keyword"},
                    }
                }
            }
            resp = await client.put(f"{es_host}/system_logs", json=mapping)
            if resp.status_code in (200, 201):
                logger.info("system_logs 인덱스 매핑 생성 완료.")
            else:
                logger.warning(f"system_logs 매핑 생성 실패: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.warning(f"system_logs 인덱스 확인 실패: {e!r}")


async def ensure_employee_logs_index(es_host: str):
    """employee_logs 인덱스 매핑이 없으면 생성 (데이터 적재 X)"""
    try:
        async with httpx.AsyncClient(timeout=3.0, headers={"bypass-tunnel-reminder": "true"}, http2=False) as client:
            idx_resp = await client.get(f"{es_host}/employee_logs")
            if idx_resp.status_code == 200:
                return  # 이미 존재
            mapping = {
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "user_id":   {"type": "keyword"},
                        "name":      {"type": "keyword"},
                        "branch":    {"type": "keyword"},
                        "feature":   {"type": "keyword"},
                    }
                }
            }
            resp = await client.put(f"{es_host}/employee_logs", json=mapping)
            if resp.status_code in (200, 201):
                logger.info("employee_logs 인덱스 매핑 생성 완료.")
            else:
                logger.warning(f"employee_logs 매핑 생성 실패: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.warning(f"employee_logs 인덱스 확인 실패: {e!r}")


# ────────────────────────────────────────────────
# 시스템 대시보드
# ────────────────────────────────────────────────

async def get_system_dashboard(
    period: Optional[str], db: Session
) -> SystemDashboardResponse:
    """시스템 대시보드 - 실시간 ES 로그 집계"""

    # 인덱스 매핑 보장 (seed X)
    await ensure_system_logs_index(ES_HOST)

    logs = []
    es_status = "정상"

    try:
        async with httpx.AsyncClient(timeout=3.0, headers={"bypass-tunnel-reminder": "true"}, http2=False) as client:
            response = await client.post(
                f"{ES_HOST}/system_logs/_search",
                json={
                    "query": {"range": {"timestamp": {"gte": "now-24h"}}},
                    "sort": [{"timestamp": {"order": "desc"}}],
                    "size": 5000,
                }
            )
            if response.status_code == 200:
                hits = response.json().get("hits", {}).get("hits", [])
                logs = [hit["_source"] for hit in hits]
            else:
                logger.warning(f"ES system_logs 조회 실패: {response.status_code}")
                es_status = "오류"
    except Exception as e:
        logger.warning(f"ES system_logs 연결 실패: {e!r}")
        es_status = "오류"

    # 24시간 블록 집계
    kst_now = datetime.utcnow() + timedelta(hours=9)
    blocks_data = []
    for i in range(23, -1, -1):
        block_time = kst_now - timedelta(hours=i)
        blocks_data.append({"time": f"{block_time.hour:02d}시", "count": 0, "total_ms": 0, "errors": 0})

    total_latency = 0
    total_count = 0
    error_count = 0
    recent_errors = []

    for log in logs:
        ts_str = log.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            local_ts = (ts + timedelta(hours=9)).replace(tzinfo=None)
        except Exception:
            local_ts = kst_now

        diff_seconds = max((kst_now - local_ts).total_seconds(), 0)
        status = int(log.get("status", 200))
        ms = int(log.get("ms", 100))
        is_error = status >= 400

        if diff_seconds < 86400:
            block_idx = min(int(diff_seconds // 3600), 23)
            target_idx = 23 - block_idx
            blocks_data[target_idx]["count"] += 1
            blocks_data[target_idx]["total_ms"] += ms
            if is_error:
                blocks_data[target_idx]["errors"] += 1
                error_count += 1
            total_latency += ms
            total_count += 1

        if is_error and len(recent_errors) < 5:
            api_path = log.get("path", log.get("api", ""))
            if "ai" in api_path or "completions" in api_path:
                service = "AI Service"
            elif "auth" in api_path or "login" in api_path:
                service = "API Gateway"
            elif "customer" in api_path:
                service = "SQL"
            elif "trend" in api_path or "news" in api_path:
                service = "Elasticsearch"
            else:
                service = "Worker"
            recent_errors.append(RecentErrorLog(
                time=local_ts.strftime("%H:%M"),
                service=service,
                error_detail=f"{status} Error on {log.get('method','GET')} {api_path}"
            ))

    requests_chart, latency_chart, error_chart = [], [], []
    for block in blocks_data:
        cnt = block["count"]
        avg_ms = round(block["total_ms"] / cnt, 1) if cnt > 0 else 0.0
        err_rate = round((block["errors"] / cnt) * 100, 2) if cnt > 0 else 0.0
        requests_chart.append(ChartPoint(time=block["time"], value=cnt))
        latency_chart.append(ChartPoint(time=block["time"], value=avg_ms))
        error_chart.append(ChartPoint(time=block["time"], value=err_rate))

    db_status = "정상"
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "오류"

    api_response_speed = round(total_latency / total_count, 1) if total_count > 0 else 0.0
    error_rate = round((error_count / total_count) * 100, 2) if total_count > 0 else 0.0
    server_status = "정상" if error_rate < 5.0 else ("주의" if error_rate < 15.0 else "장애")

    ml_metrics = [
        MLPerformanceMetrics(
            name="기준 금리",
            metric1_name="정확도", metric1_val="83.33%",
            metric2_name="F1 score", metric2_val="0.45",
            metric3_name="recall", metric3_val="0.45",
            metric4_name="precision", metric4_val="0.45"
        ),
        MLPerformanceMetrics(
            name="금값 변화율",
            metric1_name="정확도", metric1_val="56.06%",
            metric2_name="F1 score", metric2_val="0.54",
            metric3_name="recall", metric3_val="0.55",
            metric4_name="precision", metric4_val="0.55"
        ),
        MLPerformanceMetrics(
            name="부동산지수",
            metric1_name="MSE", metric1_val="0.0064",
            metric2_name="MAE", metric2_val="0.0594%",
            metric3_name="MAPE", metric3_val="0.0450%",
            metric4_name="adj-R squared", metric4_val="62.21%"
        )
    ]

    return SystemDashboardResponse(
        period=period,
        server_status=server_status,
        api_response_speed=api_response_speed,
        api_response_speed_change=-5.0,
        error_rate=error_rate,
        error_rate_change=0.2,
        db_status=db_status,
        es_status=es_status,
        ai_status="정상",
        requests_chart=requests_chart,
        latency_chart=latency_chart,
        error_chart=error_chart,
        recent_errors=recent_errors,
        ml_metrics=ml_metrics,
    )


# ────────────────────────────────────────────────
# 시스템 로그 대시보드
# ────────────────────────────────────────────────

async def get_system_logs(
    filter: Optional[str], db: Session
) -> LogsDashboardResponse:
    """시스템 로그 대시보드 - 실시간 ES 데이터"""
    logs = []

    try:
        async with httpx.AsyncClient(timeout=3.0, headers={"bypass-tunnel-reminder": "true"}, http2=False) as client:

            response = await client.post(
                f"{ES_HOST}/system_logs/_search",
                json={
                    "query": {"match_all": {}},
                    "sort": [{"timestamp": {"order": "desc"}}],
                    "size": 50,
                }
            )
            if response.status_code == 200:
                hits = response.json().get("hits", {}).get("hits", [])
                for hit in hits:
                    source = hit.get("_source", {})
                    ts_str = source.get("timestamp", datetime.now().isoformat())
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        local_ts = ts + timedelta(hours=9)
                        time_str = local_ts.strftime("%H:%M:%S")
                    except Exception:
                        time_str = ts_str[-8:] if len(ts_str) >= 8 else ts_str

                    api_path = source.get("api", source.get("path", "/api/unknown"))
                    if "news" in api_path or "notification" in api_path:
                        continue

                    logs.append(LogEntry(
                        id=hit.get("_id", "unknown"),
                        time=time_str,
                        api=api_path,
                        path=api_path,
                        ms=f"{source.get('ms', 0)} ms",
                        status=str(source.get("status", 200)),
                        user_id=source.get("user_id", "system"),
                    ))
            else:
                logger.warning(f"ES system_logs 조회 실패: {response.status_code}")
    except Exception as e:
        logger.warning(f"ES system_logs 연결 실패: {e!r}")

    if filter == "오류만":
        logs = [log for log in logs if log.status != "200"]

    return LogsDashboardResponse(logs=logs, total=len(logs))


# ────────────────────────────────────────────────
# 직원 대시보드
# ────────────────────────────────────────────────

async def get_employee_dashboard(
    period: Optional[str], db: Session
) -> EmployeeDashboardResponse:
    total_pb = db.query(PbUser).filter(PbUser.status != "퇴사").count()
    active_pb = db.query(PbUser).filter(PbUser.status == "재직").count()

    es_status = "정상"
    try:
        async with httpx.AsyncClient(timeout=3.0, headers={"bypass-tunnel-reminder": "true"}, http2=False) as client:

            response = await client.get(f"{ES_HOST}/")
            if response.status_code != 200:
                es_status = "오류"
    except Exception:
        es_status = "오류"

    return EmployeeDashboardResponse(
        active_count=active_pb,
        total_count=total_pb,
        access_rate=f"{int((active_pb / total_pb) * 100)}%" if total_pb > 0 else "0%",
        avg_session_time="24분",
        total_employees=total_pb,
        total_employees_change="▲ 5(전월 대비)",
        active_employees=active_pb,
        active_employees_sub="실시간",
        todo_approved_month=120,
        todo_approved_month_total=150,
        todo_approved_today=20,
        todo_approved_today_total=25,
        es_status=es_status,
    )


async def get_branch_stats(period: Optional[str], db: Session) -> BranchStatsResponse:
    stats = [
        BranchStats(branch_name="WM영업1팀", access_rate=80.0),
        BranchStats(branch_name="WM영업2팀", access_rate=72.0),
        BranchStats(branch_name="리테일PB팀", access_rate=68.0),
    ]
    return BranchStatsResponse(stats=stats, period=period)


async def get_weekly_trend(db: Session) -> WeeklyTrendResponse:
    trends = [
        WeeklyTrend(name="4주전", value=61.0),
        WeeklyTrend(name="3주전", value=67.0),
        WeeklyTrend(name="2주전", value=70.0),
        WeeklyTrend(name="지난주", value=75.0),
    ]
    return WeeklyTrendResponse(trends=trends)


async def get_employee_usage(period: Optional[str], db: Session) -> EmployeeUsageResponse:
    """직원 현황 + 실시간 최근 활동 로그 (employee_logs 기반)"""

    # 인덱스 매핑 보장 (seed X)
    await ensure_employee_logs_index(ES_HOST)

    # 직원 현황은 DB에서
    pbs = db.query(PbUser).options(joinedload(PbUser.branch_rel)).filter(PbUser.status != "퇴사").all()
    usage_list = []
    for idx, pb in enumerate(pbs):
        branch_name = pb.branch_rel.name if pb.branch_rel else "미지정 지점"
        status_str = "접속 중" if pb.status == "재직" else ("발령 대기" if pb.status == "발령대기" else "오프라인")
        status_cls = "status-online" if pb.status == "재직" else ("status-away" if pb.status == "발령대기" else "status-offline")
        usage_list.append(EmployeeUsage(
            id=f"100{idx+100:03d}",
            name=pb.name,
            branch=branch_name,
            email=pb.email if pb.email else "—",
            status=status_str,
            statusClass=status_cls,
        ))

    # 최근 활동 로그는 ES에서
    recent_activities = []
    es_status = "정상"
    try:
        async with httpx.AsyncClient(timeout=3.0, headers={"bypass-tunnel-reminder": "true"}, http2=False) as client:
            response = await client.post(
                f"{ES_HOST}/employee_logs/_search",
                json={
                    "query": {"range": {"timestamp": {"gte": "now-24h"}}},
                    "sort": [{"timestamp": {"order": "desc"}}],
                    "size": 15,
                }
            )
            if response.status_code == 200:
                hits = response.json().get("hits", {}).get("hits", [])
                for hit in hits:
                    source = hit.get("_source", {})
                    ts_str = source.get("timestamp", "")
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        local_ts = ts + timedelta(hours=9)
                        time_str = local_ts.strftime("%H:%M")
                    except Exception:
                        time_str = "--:--"

                    recent_activities.append(RecentActivityLog(
                        time=time_str,
                        name=source.get("name", source.get("user_id", "unknown")),
                        branch=source.get("branch", "미지정 지점"),
                        feature=source.get("feature", ""),
                    ))
            else:
                logger.warning(f"ES employee_logs 조회 실패: {response.status_code}")
                es_status = "오류"
    except Exception as e:
        logger.warning(f"ES employee_logs 연결 실패: {e!r}")
        es_status = "오류"

    return EmployeeUsageResponse(
        usage=usage_list,
        total=len(usage_list),
        recent_activities=recent_activities,
        es_status=es_status,
    )


async def get_system_usage(period: Optional[str], db: Session) -> UsageDashboardResponse:
    pass


# ────────────────────────────────────────────────
# 권한 / 인수인계 / 고객이관 (변경 없음)
# ────────────────────────────────────────────────

async def get_permissions(search: Optional[str], branch: Optional[str], db: Session) -> PermissionListResponse:
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
    client_counts = dict(db.query(InCharge.u_id, func.count(InCharge.c_id)).group_by(InCharge.u_id).all())
    pending_handovers = {
        h.from_u_id: h
        for h in db.query(Handover)
        .options(joinedload(Handover.to_user).joinedload(PbUser.branch_rel))
        .filter(Handover.status == "대기")
        .all()
    }

    employees = []
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
                branch_note = f"발령 대기 {pb.branch_rel.name.replace('지점','')} → {handover.to_user.branch_rel.name.replace('지점','')}"
            else:
                branch_note = f"발령 대기 {pb.branch_rel.name.replace('지점','')} → 압구정"

        employees.append(EmployeeListItem(
            id=u_id, u_id=u_id, name=name, branch=branch_name,
            position=position, status=status, clients=f"{client_count}명",
            pending=pending, branchNote=branch_note,
        ))

    return PermissionListResponse(employees=employees, total=len(employees))


async def get_available_receivers(u_id: str, db: Session) -> AvailableReceiversResponse:
    pb = db.query(PbUser).filter(PbUser.u_id == u_id).first()
    if not pb:
        return AvailableReceiversResponse(receivers=[])

    receivers_query = db.query(PbUser).filter(
        PbUser.branch == pb.branch, PbUser.u_id != u_id, PbUser.status != "퇴사"
    ).all()

    receivers = []
    for r in receivers_query:
        clients_count = db.query(InCharge).filter(InCharge.u_id == r.u_id).count()
        receivers.append(AvailableReceiver(id=r.u_id, name=r.name, clients=f"현재 {clients_count}명 담당"))

    return AvailableReceiversResponse(receivers=receivers)


async def get_handovers(search: Optional[str], status: Optional[str], db: Session) -> HandoverListResponse:
    query = db.query(Handover)
    if search:
        query = query.join(PbUser, Handover.from_u_id == PbUser.u_id).filter(PbUser.name.like(f"%{search}%"))

    handovers_db = query.order_by(Handover.h_date.desc()).all()
    handovers = []
    for h in handovers_db:
        from_name = h.from_user.name if h.from_user else "퇴사자"
        to_name = h.to_user.name if h.to_user else "미지정"
        from_branch = h.from_user.branch_rel.name.replace('지점','') if (h.from_user and h.from_user.branch_rel) else "미정"
        to_branch = h.to_user.branch_rel.name.replace('지점','') if (h.to_user and h.to_user.branch_rel) else "미정"
        handovers.append(HandoverRecord(
            id=str(h.h_id),
            name=from_name,
            title=f"{from_name} {from_branch} → {to_branch}지점",
            desc=f"고객 재배정 → {to_name} {h.h_date.strftime('%Y.%m.%d')}",
        ))

    return HandoverListResponse(handovers=handovers, total=len(handovers))


async def get_employee_customers(u_id: str, db: Session) -> CustomerListResponse:
    customers_db = (
        db.query(Customer)
        .join(InCharge, Customer.c_id == InCharge.c_id)
        .filter(InCharge.u_id == u_id)
        .all()
    )
    customers = [
        CustomerListItem(
            id=str(c.c_id),
            name=c.name,
            assets=f"{c.grade} · 자산 {int(c.total_assets / 100000000)}억" if c.total_assets else "일반 · 자산 0원",
        )
        for c in customers_db
    ]
    return CustomerListResponse(customers=customers, total=len(customers_db))


async def transfer_customers(u_id: str, request: TransferRequest, db: Session) -> TransferResponse:
    from_user = db.query(PbUser).filter(PbUser.u_id == u_id).first()
    to_user = db.query(PbUser).filter(PbUser.u_id == request.receiver_u_id).first()

    if not from_user or not to_user:
        return TransferResponse(message="인계자 또는 인수자 정보가 유효하지 않습니다.", success=False)

    for cid in request.customer_ids:
        db.query(InCharge).filter(InCharge.u_id == u_id, InCharge.c_id == cid).delete()
        db.add(InCharge(u_id=request.receiver_u_id, c_id=cid))
        db.add(Handover(a_id="admin1", c_id=cid, from_u_id=u_id, to_u_id=request.receiver_u_id, status="완료"))

    if db.query(InCharge).filter(InCharge.u_id == u_id).count() == 0:
        from_user.branch = request.target_branch
        from_user.status = "재직"

    db.commit()
    return TransferResponse(message="인수인계 및 지점 발령 처리가 성공적으로 완료되었습니다.", success=True)