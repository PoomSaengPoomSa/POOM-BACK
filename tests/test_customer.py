import pytest

def test_get_today_visitor_list_success(client):
    # 1. 처음에는 오늘 자 상담 일정이 없어서 빈 리스트 출력
    response = client.get("/api/v1/customers/?tab=today")
    assert response.status_code == 200
    assert len(response.json()) == 0
    
    # 2. 오늘 자 상담 일정을 DB에 등록
    # 김철수 고객(c_id=1001)에 대해 오늘 상담 일정 생성
    response_create = client.post("/api/v1/schedules", json={
        "category": "상담",
        "content": "김철수 고객과 상담 미팅",
        "startDatetime": "2026-06-05T10:00:00",
        "endDatetime": "2026-06-05T11:00:00",
        "color": "blue",
        "customer_id": 1001
    })
    assert response_create.status_code == 200
    
    # 3. 다시 오늘 방문 목록 호출 시 김철수 고객이 필터링되어 출력되는지 검증
    response_today = client.get("/api/v1/customers/?tab=today")
    assert response_today.status_code == 200
    visitors = response_today.json()
    assert len(visitors) == 1
    assert visitors[0]["name"] == "김철수"
    assert visitors[0]["c_id"] == 1001

def test_get_customer_detail_success(client):
    response = client.get("/api/v1/customers/1001")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "김철수"
    assert data["total_assets"] == 800000000
    assert "예금 비중이 62.5%" in data["llm_insight"]

def test_get_customer_churn_risk_success(client):
    response = client.get("/api/v1/customers/1001/churn-risk")
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == 1001
    assert data["grade"] == "위험"
    assert "거액 자산 출금 징후" in data["reason"]

def test_get_customer_product_match_success(client):
    response = client.get("/api/v1/customers/1001/main_product_match")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # 우리WON플러스예금(pd_id=1)은 보유 상품
    # 글로벌 배당주 ETF(pd_id=2)는 미보유 및 부적합 매칭 데이터 존재
    items = data["items"]
    assert len(items) == 2
    
    prod1 = next(i for i in items if i["product_name"] == "우리WON플러스예금")
    assert prod1["is_owned"] is True
    assert prod1["is_suitable"] == 1
    assert "부합함" in prod1["reason"]
    
    prod2 = next(i for i in items if i["product_name"] == "글로벌 배당주 ETF")
    assert prod2["is_owned"] is False
    assert prod2["is_suitable"] == 0
    assert "변동성 위험" in prod2["reason"]

def test_get_customer_feature_tags(db, client):
    # 김철수 고객(c_id=1001)에 대해 메모 기반 특징 추가 및 해시태그 검증
    # 1. 특징 적재
    from app.models.customer import CustomerInformation
    info = CustomerInformation(
        c_id=1001,
        category="기호",
        contents="아메리카노 선호"
    )
    db.add(info)
    db.commit()
    
    # 2. 특징 조회 API 검증
    response = client.get("/api/v1/customers/1001/feature")
    assert response.status_code == 200
    data = response.json()
    assert len(data["features"]) == 1
    assert data["features"][0]["category"] == "기호"
    assert data["features"][0]["text"] == "아메리카노 선호"

def test_get_customer_visit_statistics(client):
    # 김철수 고객과의 방문 주기 통계 검증
    # 1. 2회 이상의 상담 일정을 과거 시점으로 등록 (마지막 방문일 및 평균 주기 계산을 유도)
    client.post("/api/v1/schedules", json={
        "category": "상담",
        "content": "과거 상담 1",
        "startDatetime": "2026-05-01T10:00:00",
        "endDatetime": "2026-05-01T11:00:00",
        "customer_id": 1001
    })
    client.post("/api/v1/schedules", json={
        "category": "상담",
        "content": "과거 상담 2",
        "startDatetime": "2026-05-21T10:00:00",
        "endDatetime": "2026-05-21T11:00:00",
        "customer_id": 1001
    })
    
    response = client.get("/api/v1/customers/1001/visits-statistics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_visits"] == 2
    # 5월 1일 ~ 5월 21일 간격 = 20일
    assert data["avg_visit_cycle_days"] == 20
    assert data["last_visit_date"] == "2026-05-21"
