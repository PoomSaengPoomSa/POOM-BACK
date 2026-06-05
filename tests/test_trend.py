import pytest

def test_get_trend_dashboard_success(client):
    response = client.get("/api/v1/trend/dashboard")
    assert response.status_code == 200
    data = response.json()
    
    # 1. 뉴스 검증 (mock_external_calls에서 모킹된 Elasticsearch 결과 반영)
    assert "news" in data
    assert "economy" in data["news"]
    assert len(data["news"]["economy"]) == 1
    assert data["news"]["economy"][0]["id"] == "news_123"
    assert data["news"]["economy"][0]["title"] == "한국은행 기준금리 연 3.5% 동결 유력 기조"
    
    # 2. 경제지표 및 예측값 검증 (seed_data에서 적재된 DB 데이터 반영)
    assert "indicators" in data
    gold = data["indicators"]["gold"]
    assert gold["today"] == 95.2
    assert gold["yesterday"] == 94.5
    # 상승 예측 검증: prob_rise(0.75) > prob_fall(0.25)
    assert gold["predictionText"] == "상승 가능성 높음"
    
    interest = data["indicators"]["interestRate"]
    assert interest["thisMonth"] == 3.5
    assert interest["probFreeze"] == 85
    assert interest["predictionText"] == "동결 가능성 높음"

    # 3. 실시간 트렌드 검증 (CPI, 코스피200 등)
    assert "realtimeTrends" in data
    cpi = next(item for item in data["realtimeTrends"] if item["name"] == "CPI")
    assert cpi["value"] == "110.2"
    assert cpi["direction"] == "up"

    # 4. AI 요약 브리핑 검증 (OpenAI Mock 연동)
    assert "aiSummaries" in data
    assert "economy" in data["aiSummaries"]
    assert "기준금리" in data["aiSummaries"]["economy"]

def test_get_news_list_success(client):
    response = client.get("/api/v1/trend/news?category=경제&q=금리&page=1&size=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "한국은행 기준금리 연 3.5% 동결 유력 기조"
    assert "pagination" in data
    assert data["pagination"]["totalCount"] == 10

def test_get_news_detail_success(client):
    response = client.get("/api/v1/trend/news/news_123")
    assert response.status_code == 200
    data = response.json()
    assert data["newsId"] == "news_123"
    assert data["title"] == "기준금리 동결에 따른 자산 리밸런싱 방향"
    assert data["source"] == "SBS 뉴스"
