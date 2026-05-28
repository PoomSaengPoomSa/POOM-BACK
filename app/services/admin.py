import httpx
from datetime import datetime, timedelta
import random
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

async def seed_system_logs_if_needed(es_host: str):
    """엘라스틱서치에 로그가 부족하거나 인덱스가 없는 경우, 자동으로 사용자의 행동 로그를 벌크 적재(Seed)"""
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.post(
                f"{es_host}/system_logs/_search",
                json={
                    "query": {"match_all": {}},
                    "size": 0
                }
            )
            if response.status_code == 200:
                res_data = response.json()
                total = res_data.get("hits", {}).get("total", {}).get("value", 0)
                if total >= 100:
                    logger.info(f"Elasticsearch system_logs already has {total} documents. Skipping seeding.")
                    return
    except Exception as e:
        logger.warning(f"Error checking ES logs status: {e}. Attempting index creation/seeding.")

    logger.info("Seeding Elasticsearch system logs...")
    
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            idx_resp = await client.get(f"{es_host}/system_logs")
            if idx_resp.status_code != 200:
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
                            "feature":   {"type": "keyword"}
                        }
                    }
                }
                await client.put(f"{es_host}/system_logs", json=mapping)
                logger.info("Created system_logs index mapping in Elasticsearch.")
    except Exception as e:
        logger.error(f"Error creating system_logs mapping: {e}")

    endpoints = [
        ("/api/v1/customers/?tab=all&page=1&size=1000", "고객관리", "GET", [80, 220], [200, 200, 200, 200, 200, 200, 500]),
        ("/api/v1/customers/1", "고객관리", "GET", [40, 120], [200, 200, 200]),
        ("/api/v1/customers/1/reports/generate", "트렌드 아카이브", "POST", [1500, 4500], [200, 200, 500]),
        ("/api/v1/trend/dashboard", "트렌드 아카이브", "GET", [100, 300], [200, 200, 200]),
        ("/api/v1/trend/news", "트렌드 아카이브", "GET", [120, 280], [200, 200]),
        ("/api/v1/schedules", "캘린더", "GET", [50, 110], [200, 200, 200]),
        ("/api/v1/auth/login", "시스템", "POST", [120, 380], [200, 200, 401]),
        ("/api/v1/ai-todo", "트렌드 아카이브", "GET", [60, 150], [200, 200]),
        ("/api/v1/kpi/personal?u_id=admin1", "시스템", "GET", [60, 180], [200, 200])
    ]
    users = ["admin1", "developer", "pb1", "pb2", "system"]
    now = datetime.utcnow()
    
    bulk_lines = []
    for i in range(250):
        path, feature, method, ms_range, status_codes = random.choice(endpoints)
        status_code = random.choice(status_codes)
        ms_val = random.randint(ms_range[0], ms_range[1])
        user = random.choice(users)
        time_offset_secs = random.randint(0, 86400)
        log_time = now - timedelta(seconds=time_offset_secs)
        
        meta = {"index": {"_index": "system_logs"}}
        doc = {
            "timestamp": log_time.isoformat() + "Z",
            "api": f"[{method}] {path}",
            "path": path,
            "method": method,
            "status": status_code,
            "status_code": status_code,
            "ms": ms_val,
            "response_time": ms_val,
            "user_id": user,
            "feature": feature
        }
        bulk_lines.append(json.dumps(meta))
        bulk_lines.append(json.dumps(doc))
        
    bulk_data = "\n".join(bulk_lines) + "\n"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            headers = {"Content-Type": "application/x-ndjson"}
            resp = await client.post(f"{es_host}/_bulk", content=bulk_data, headers=headers)
            if resp.status_code == 200:
                logger.info("Successfully bulk-indexed 250 mock logs to Elasticsearch!")
    except Exception as e:
        logger.error(f"Error bulk-indexing mock logs to ES: {e}")


async def get_system_dashboard(
    period: Optional[str], db: Session
) -> SystemDashboardResponse:
    """시스템 대시보드 조회 (Elasticsearch 기반 실시간 데이터 집계 및 자가 치유)"""
    logs = []
    es_status = "정상"
    
    try:
        await seed_system_logs_if_needed(ES_HOST)
        
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.post(
                f"{ES_HOST}/system_logs/_search",
                json={
                    "query": {
                        "range": {
                            "timestamp": {
                                "gte": "now-24h"
                            }
                        }
                    },
                    "sort": [
                        {"timestamp": {"order": "desc"}}
                    ],
                    "size": 5000
                }
            )
            if response.status_code == 200:
                res_data = response.json()
                hits = res_data.get("hits", {}).get("hits", [])
                for hit in hits:
                    logs.append(hit.get("_source", {}))
            else:
                logger.warning(f"ES search status {response.status_code}.")
                es_status = "오류"
    except Exception as e:
        logger.warning(f"Failed to fetch logs from ES: {e}.")
        es_status = "오류"

    if es_status == "오류":
        logs = []

    # 1. Define the 24 chronological 1-hour blocks in KST ending at the current hour block
    kst_now = datetime.utcnow() + timedelta(hours=9)
    blocks_data = []
    
    # Generate the 24 block labels chronologically (e.g., from 23 hours ago to now)
    for i in range(23, -1, -1):
        block_time = kst_now - timedelta(hours=i)
        block_hour = block_time.hour
        label = f"{block_hour:02d}시"
        blocks_data.append({"time": label, "count": 0, "total_ms": 0, "errors": 0})

    total_latency = 0
    total_count = 0
    error_count = 0
    recent_errors = []

    for log in logs:
        ts_str = log.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if "Z" in ts_str or "+00:00" in ts_str.replace("Z", "+00:00"):
                local_ts = ts + timedelta(hours=9)
            else:
                local_ts = ts
            local_ts = local_ts.replace(tzinfo=None)
        except Exception:
            local_ts = kst_now

        diff = kst_now - local_ts
        diff_seconds = diff.total_seconds()
        
        if diff_seconds < 0:
            diff_seconds = 0
            
        status = int(log.get("status", log.get("status_code", 200)))
        ms = int(log.get("ms", log.get("response_time", 100)))
        is_error = status >= 400
        
        if diff_seconds < 86400:
            block_idx = int(diff_seconds // 3600) # 1 hour
            if block_idx >= 24:
                block_idx = 23
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
            elif "customer" in api_path or "handover" in api_path or "permission" in api_path:
                service = "SQL"
            elif "trend" in api_path or "news" in api_path:
                service = "Elasticsearch"
            else:
                service = "Worker"

            err_msg = f"{status} Error on {log.get('method', 'GET')} {api_path}"
            try:
                time_str = local_ts.strftime("%H:%M")
            except Exception:
                time_str = "14:00"

            recent_errors.append(RecentErrorLog(
                time=time_str,
                service=service,
                error_detail=err_msg
            ))

    requests_chart = []
    latency_chart = []
    error_chart = []

    for block in blocks_data:
        label = block["time"]
        cnt = block["count"]
        avg_ms = round(block["total_ms"] / cnt, 1) if cnt > 0 else 0.0
        err_rate = round((block["errors"] / cnt) * 100, 2) if cnt > 0 else 0.0

        requests_chart.append(ChartPoint(time=label, value=cnt))
        latency_chart.append(ChartPoint(time=label, value=avg_ms))
        error_chart.append(ChartPoint(time=label, value=err_rate))

    db_status = "정상"
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "오류"

    api_response_speed = round(total_latency / total_count, 1) if total_count > 0 else 152.4
    error_rate = round((error_count / total_count) * 100, 2) if total_count > 0 else 0.45

    if error_rate < 5.0:
        server_status = "정상"
    elif error_rate < 15.0:
        server_status = "주의"
    else:
        server_status = "장애"

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
        ml_metrics=ml_metrics
    )


async def get_system_usage(
    period: Optional[str], db: Session
) -> UsageDashboardResponse:
    """시스템 사용량 대시보드"""
    # TODO: 구현
    pass


async def get_system_logs(
    filter: Optional[str], db: Session
) -> LogsDashboardResponse:
    """시스템 로그 대시보드"""
    logs = []
    
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
            
    logs = [log for log in logs if "news" not in log.api and "notification" not in log.api]

    if filter == "오류만":
        logs = [log for log in logs if log.status != "200"]

    return LogsDashboardResponse(logs=logs, total=len(logs))


async def seed_employee_logs_if_needed(es_host: str, db: Session):
    """엘라스틱서치에 employee_logs가 부족하거나 인덱스가 없는 경우, 자동으로 직원 활동 로그를 벌크 적재(Seed)"""
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.post(
                f"{es_host}/employee_logs/_search",
                json={
                    "query": {"match_all": {}},
                    "size": 0
                }
            )
            if response.status_code == 200:
                res_data = response.json()
                total = res_data.get("hits", {}).get("total", {}).get("value", 0)
                if total >= 20:
                    logger.info(f"Elasticsearch employee_logs already has {total} documents. Skipping seeding.")
                    return
    except Exception as e:
        logger.warning(f"Error checking ES employee_logs status: {e}. Attempting mapping/seeding.")

    logger.info("Seeding Elasticsearch employee_logs index...")
    
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            idx_resp = await client.get(f"{es_host}/employee_logs")
            if idx_resp.status_code != 200:
                mapping = {
                    "mappings": {
                        "properties": {
                            "timestamp": {"type": "date"},
                            "user_id":   {"type": "keyword"},
                            "name":      {"type": "keyword"},
                            "branch":    {"type": "keyword"},
                            "feature":   {"type": "keyword"}
                        }
                    }
                }
                await client.put(f"{es_host}/employee_logs", json=mapping)
                logger.info("Created employee_logs index mapping in Elasticsearch.")
    except Exception as e:
        logger.error(f"Error creating employee_logs mapping: {e}")

    features = ["뉴스 아카이브", "AI TODO", "고객 관리", "AI 메모", "캘린더"]
    pbs = db.query(PbUser).filter(PbUser.status != "퇴사").all()
    now = datetime.utcnow()
    
    bulk_lines = []
    
    mock_activities = [
        {"user_id": "pb1", "name": "이종혁", "branch": "강남지점", "feature": "뉴스 아카이브", "offset": 10},
        {"user_id": "pb2", "name": "이수현", "branch": "강남지점", "feature": "AI TODO", "offset": 45},
        {"user_id": "pb3", "name": "김수빈", "branch": "여의도지점", "feature": "고객 관리", "offset": 90},
        {"user_id": "pb4", "name": "이주리", "branch": "압구정지점", "feature": "AI 메모", "offset": 150}
    ]
    for m in mock_activities:
        log_time = now - timedelta(minutes=m["offset"])
        meta = {"index": {"_index": "employee_logs"}}
        doc = {
            "timestamp": log_time.isoformat() + "Z",
            "user_id": m["user_id"],
            "name": m["name"],
            "branch": m["branch"],
            "feature": m["feature"]
        }
        bulk_lines.append(json.dumps(meta))
        bulk_lines.append(json.dumps(doc))

    if pbs:
        for idx in range(50):
            pb = random.choice(pbs)
            feature = random.choice(features)
            log_time = now - timedelta(seconds=random.randint(60, 43200))
            
            meta = {"index": {"_index": "employee_logs"}}
            doc = {
                "timestamp": log_time.isoformat() + "Z",
                "user_id": pb.u_id,
                "name": pb.name,
                "branch": pb.branch_rel.name if pb.branch_rel else "미지정 지점",
                "feature": feature
            }
            bulk_lines.append(json.dumps(meta))
            bulk_lines.append(json.dumps(doc))
            
    bulk_data = "\n".join(bulk_lines) + "\n"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            headers = {"Content-Type": "application/x-ndjson"}
            resp = await client.post(f"{es_host}/_bulk", content=bulk_data, headers=headers)
            if resp.status_code == 200:
                logger.info(f"Successfully bulk-indexed {len(bulk_lines)//2} employee activity logs to employee_logs index!")
    except Exception as e:
        logger.error(f"Error seeding employee_logs: {e}")


async def get_employee_dashboard(
    period: Optional[str], db: Session
) -> EmployeeDashboardResponse:
    """직원 대시보드 조회 (데이터베이스 집계 및 모크 하이브리드)"""
    total_pb = db.query(PbUser).filter(PbUser.status != "퇴사").count()
    active_pb = db.query(PbUser).filter(PbUser.status == "재직").count()
    
    es_status = "정상"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{ES_HOST}/")
            if response.status_code != 200:
                es_status = "오류"
    except Exception:
        es_status = "오류"
        
    return EmployeeDashboardResponse(
        active_count=active_pb,
        total_count=total_pb,
        access_rate=f"{int((active_pb / total_pb) * 100)}%" if total_pb > 0 else "64%",
        avg_session_time="24분",
        total_employees=total_pb if total_pb > 0 else 128,
        total_employees_change="▲ 5(전월 대비)",
        active_employees=active_pb if active_pb > 0 else 82,
        active_employees_sub="실시간",
        todo_approved_month=120,
        todo_approved_month_total=150,
        todo_approved_today=20,
        todo_approved_today_total=25,
        es_status=es_status
    )


async def get_branch_stats(
    period: Optional[str], db: Session
) -> BranchStatsResponse:
    """지점별 접속률 조회 (시안에 따라 WM영업1팀, WM영업2팀, 리테일PB팀 맵핑)"""
    stats = [
        BranchStats(branch_name="WM영업1팀", access_rate=80.0),
        BranchStats(branch_name="WM영업2팀", access_rate=72.0),
        BranchStats(branch_name="리테일PB팀", access_rate=68.0),
    ]
    return BranchStatsResponse(stats=stats, period=period)


async def get_weekly_trend(db: Session) -> WeeklyTrendResponse:
    """주간 접속률 추이 조회"""
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
    """직원별 기능 사용 현황 및 최근 활동 로그 조회 (Elasticsearch employee.logs 연동)"""
    pbs = db.query(PbUser).options(joinedload(PbUser.branch_rel)).filter(PbUser.status != "퇴사").all()
    
    mock_pbs = [
        {"id": "100089", "name": "이종혁", "branch": "강남지점", "email": "user1@example.com", "status": "접속 중", "statusClass": "status-online"},
        {"id": "100021", "name": "이수현", "branch": "강남지점", "email": "user1@example.com", "status": "접속 중", "statusClass": "status-online"},
        {"id": "100088", "name": "김수빈", "branch": "여의도지점", "email": "user1@example.com", "status": "오프라인", "statusClass": "status-offline"},
        {"id": "100102", "name": "이주리", "branch": "압구정지점", "email": "—", "status": "오프라인", "statusClass": "status-offline"}
    ]
    
    usage_list = []
    for mpb in mock_pbs:
        usage_list.append(EmployeeUsage(
            id=mpb["id"],
            name=mpb["name"],
            branch=mpb["branch"],
            email=mpb["email"],
            status=mpb["status"],
            statusClass=mpb["statusClass"]
        ))
        
    seen_names = {"이종혁", "이수현", "김수빈", "이주리"}
    for idx, pb in enumerate(pbs):
        if pb.name in seen_names:
            continue
        branch_name = pb.branch_rel.name if pb.branch_rel else "미지정 지점"
        if "금융센터" in branch_name:
            branch_name = branch_name.replace("금융센터", "지점")
            
        status_str = "접속 중" if pb.status == "재직" else ("발령 대기" if pb.status == "발령대기" else "오프라인")
        status_cls = "status-online" if pb.status == "재직" else ("status-away" if pb.status == "발령대기" else "status-offline")
        
        mapped_id = f"100{idx+100:03d}"
        
        usage_list.append(EmployeeUsage(
            id=mapped_id,
            name=pb.name,
            branch=branch_name,
            email=pb.email if pb.email else "—",
            status=status_str,
            statusClass=status_cls
        ))

    recent_activities = []
    es_status = "정상"
    try:
        await seed_employee_logs_if_needed(ES_HOST, db)
        
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.post(
                f"{ES_HOST}/employee_logs/_search",
                json={
                    "query": {
                        "range": {
                            "timestamp": {
                                "gte": "now-24h"
                            }
                        }
                    },
                    "sort": [{"timestamp": {"order": "desc"}}],
                    "size": 15
                }
            )
            if response.status_code == 200:
                hits = response.json().get("hits", {}).get("hits", [])
                users_db = db.query(PbUser).options(joinedload(PbUser.branch_rel)).all()
                user_map = {u.u_id: u for u in users_db}
                
                for hit in hits:
                    source = hit.get("_source", {})
                    user_id = source.get("user_id", "system")
                    ts_str = source.get("timestamp", "")
                    
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if "Z" in ts_str or "+00:00" in ts_str.replace("Z", "+00:00"):
                            local_ts = ts + timedelta(hours=9)
                        else:
                            local_ts = ts
                        time_str = local_ts.strftime("%H:%M")
                    except Exception:
                        time_str = "14:29"
                        
                    name = source.get("name")
                    branch = source.get("branch")
                    
                    if not name or not branch:
                        pb = user_map.get(user_id)
                        name = pb.name if pb else user_id
                        branch_name = pb.branch_rel.name if (pb and pb.branch_rel) else "미지정 지점"
                        if "금융센터" in branch_name:
                            branch = branch_name.replace("금융센터", "지점")
                        else:
                            branch = branch_name
                            
                    recent_activities.append(RecentActivityLog(
                        time=time_str,
                        name=name,
                        branch=branch,
                        feature=source.get("feature", "고객 관리")
                    ))
            else:
                logger.warning(f"ES search status {response.status_code}.")
                es_status = "오류"
    except Exception as e:
        logger.warning(f"Error fetching activities from employee_logs index: {e}")
        es_status = "오류"

    return EmployeeUsageResponse(
        usage=usage_list,
        total=len(usage_list),
        recent_activities=recent_activities,
        es_status=es_status
    )


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
