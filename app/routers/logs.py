"""
시스템 로그 조회 API
GET /api/logs              - 최근 로그 목록 (페이지네이션)
GET /api/logs/stats        - 대시보드 통계 (토큰, API 호출 수, 응답시간, 오류율)
GET /api/logs/feature      - 기능별 사용 횟수
"""

from fastapi import APIRouter, Query
from elasticsearch import Elasticsearch
import os

router = APIRouter(prefix="", tags=["logs"])

from app.config import get_settings
settings = get_settings()
ES_HOST = os.getenv("ES_HOST", settings.ES_HOST)
ES_INDEX = "system_logs"


def get_es():
    return Elasticsearch(hosts=[ES_HOST])


# ── 최근 로그 목록 ─────────────────────────────────────────────────────────────

@router.get("")
def get_logs(
    size: int = Query(20, ge=1, le=100),
    status: str = Query(None, description="200 or 500"),
):
    es = get_es()

    query = {"match_all": {}}
    if status:
        query = {"term": {"status_code": int(status)}}

    resp = es.search(
        index=ES_INDEX,
        body={
            "query": query,
            "sort": [{"timestamp": {"order": "desc"}}],
            "size": size,
            "_source": ["timestamp", "endpoint", "response_time", "status_code", "feature"],
        }
    )

    return {
        "total": resp["hits"]["total"]["value"],
        "logs": [hit["_source"] for hit in resp["hits"]["hits"]],
    }


# ── 대시보드 통계 ──────────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats():
    es = get_es()

    resp = es.search(
        index=ES_INDEX,
        body={
            "size": 0,
            "aggs": {
                "total_calls": {"value_count": {"field": "log_id"}},
                "avg_response_time": {"avg": {"field": "response_time"}},
                "error_count": {
                    "filter": {"term": {"status_code": 500}}
                },
            }
        }
    )

    aggs = resp["aggregations"]
    total = aggs["total_calls"]["value"]
    error_count = aggs["error_count"]["doc_count"]

    return {
        "total_api_calls": total,
        "avg_response_time_ms": round(aggs["avg_response_time"]["value"] or 0, 1),
        "error_rate": round((error_count / total * 100) if total else 0, 1),
        "error_count": error_count,
    }


# ── 기능별 사용 횟수 ───────────────────────────────────────────────────────────

@router.get("/feature")
def get_feature_stats():
    es = get_es()

    resp = es.search(
        index=ES_INDEX,
        body={
            "size": 0,
            "aggs": {
                "by_feature": {
                    "terms": {"field": "feature", "size": 10}
                }
            }
        }
    )

    buckets = resp["aggregations"]["by_feature"]["buckets"]
    return {
        "features": [
            {"feature": b["key"], "count": b["doc_count"]}
            for b in buckets
        ]
    }
