import pytest

def test_get_personal_kpi_success(client):
    response = client.get("/api/v1/kpi/personal?u_id=user1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "홍길동"
    assert data["customer_count"] == 12
    assert data["customer_goal"] == 20
    # 달성도 계산: 12 / 20 * 100 = 60.0%
    assert data["customer_rate"] == 60.0
    # 전월비 성장률 계산: (12 - 10) / 10 * 100 = 20.0%
    assert data["customer_delta"] == 20.0
    
    assert data["aum"] == 42 # 42억
    assert data["aum_goal"] == 50 # 50억
    assert data["non_interest"] == 450 # 450만
    assert data["non_interest_goal"] == 600

def test_get_personal_kpi_invalid_uid(client):
    response = client.get("/api/v1/kpi/personal?u_id=invalid_user")
    assert response.status_code == 400
    assert response.json()["detail"] == "유효하지 않은 u_id"

def test_get_branch_kpi_success(client):
    response = client.get("/api/v1/kpi/branch?u_id=user1")
    assert response.status_code == 200
    data = response.json()
    assert data["branch_name"] == "종로금융센터"
    assert data["customer_count"] == 98
    assert data["customer_goal"] == 150
    # 전월비 성장률 계산: (98 - 90) / 90 * 100 = 8.9%
    assert data["customer_delta"] == 8.9
    assert data["aum"] == 480 # 480억
    assert data["non_interest"] == 7200 # 7200만

def test_get_seasonal_products_success(client):
    response = client.get("/api/v1/kpi/seasonal-products")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    assert len(data["products"]) == 2
    product_names = [p["name"] for p in data["products"]]
    assert "우리WON플러스예금" in product_names
    assert "글로벌 배당주 ETF" in product_names

def test_get_seasonal_product_detail_success(client):
    # product_id=1은 우리WON플러스예금
    response = client.get("/api/v1/kpi/seasonal-products/1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "우리WON플러스예금"
    assert data["issuer"] == "우리은행"
    assert data["expected_return"] == 3.5
    # 홍길동 PB의 담당 고객(1001 김철수)이 적합 상품 매칭되어 있음
    assert data["matched_customer_count"] == 1
    assert len(data["suitable_customers"]) == 1
    assert data["suitable_customers"][0]["name"] == "김철수"
    assert data["suitable_customers"][0]["tendency"] == "안정추구형"

def test_get_seasonal_product_detail_invalid_id(client):
    response = client.get("/api/v1/kpi/seasonal-products/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "존재하지 않는 상품"
