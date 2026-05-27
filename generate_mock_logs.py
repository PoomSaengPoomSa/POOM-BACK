"""
시스템 로그 가상 데이터 생성 → Elasticsearch 적재
인덱스: system_logs (뉴스: sbs_news 와 분리)
"""

from elasticsearch import Elasticsearch, helpers
from datetime import datetime, timedelta
import random
import uuid

ES_HOST = "http://elasticsearch:9200"
ES_INDEX = "system_logs"

INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "log_id":        {"type": "keyword"},
            "timestamp":     {"type": "date"},
            "endpoint":      {"type": "keyword"},
            "method":        {"type": "keyword"},
            "status_code":   {"type": "integer"},
            "response_time": {"type": "integer"},   # ms
            "feature":       {"type": "keyword"},   # 트렌드 아카이브, 고객관리 등
            "user_id":       {"type": "keyword"},
            "error_message": {"type": "text"},
        }
    }
}

ENDPOINTS = [
    ("/api/ai/chat/completions",          "트렌드 아카이브", [200, 200, 200, 500]),
    ("/api/archive/economic-indicators",  "트렌드 아카이브", [200, 200]),
    ("/api/archive/news",                 "뉴스 버킷",       [200, 200]),
    ("/api/report/generate",              "트렌드 아카이브", [200, 200, 200]),
    ("/api/market/rates",                 "고객관리",        [200, 200]),
    ("/api/calendar/events",              "캘린더",          [200, 200, 200, 500]),
    ("/api/customer/list",                "고객관리",        [200]),
    ("/api/customer/detail",              "고객관리",        [200, 200, 500]),
]

RESPONSE_TIMES = {
    200: lambda: random.randint(50, 1500),
    500: lambda: random.randint(3000, 6000),
}


def generate_logs(count: int = 500) -> list[dict]:
    """가상 로그 데이터 생성"""
    docs = []
    now = datetime.utcnow()

    for _ in range(count):
        endpoint, feature, status_pool = random.choice(ENDPOINTS)
        status_code = random.choice(status_pool)
        response_time = RESPONSE_TIMES[status_code]()
        timestamp = now - timedelta(
            days=random.randint(0, 6),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        log_id = str(uuid.uuid4())
        docs.append({
            "_index": ES_INDEX,
            "_id": log_id,
            "_source": {
                "log_id":        log_id,
                "timestamp":     timestamp.isoformat(),
                "endpoint":      endpoint,
                "method":        "POST" if "chat" in endpoint or "report" in endpoint else "GET",
                "status_code":   status_code,
                "response_time": response_time,
                "feature":       feature,
                "user_id":       f"user_{random.randint(1, 20):03d}",
                "error_message": "Internal Server Error" if status_code == 500 else None,
            }
        })

    return docs


def ensure_index(es: Elasticsearch) -> None:
    try:
        es.indices.get(index=ES_INDEX)
        print(f"인덱스 존재: {ES_INDEX}")
    except Exception:
        es.indices.create(index=ES_INDEX, body=INDEX_MAPPING)
        print(f"인덱스 생성: {ES_INDEX}")


def main():
    es = Elasticsearch(hosts=[ES_HOST])

    try:
        es.ping()
        print(f"ES 연결 성공: {ES_HOST}")
    except Exception as e:
        print(f"ES 연결 실패: {e}")
        return

    ensure_index(es)

    print("가상 로그 데이터 생성 중...")
    docs = generate_logs(count=500)

    success, errors = helpers.bulk(es, docs, raise_on_error=False, stats_only=False)
    print(f"적재 완료 → 성공: {success}, 실패: {len(errors) if isinstance(errors, list) else 0}")


if __name__ == "__main__":
    main()
