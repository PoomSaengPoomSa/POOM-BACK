import pytest
from datetime import date, datetime

def test_get_notifications_list_and_count(client):
    # 1. 처음에는 알림이 생성되지 않은 상태. count 호출 시 자동 생성이 트리거됨.
    # 김철수 고객(c_id=1001)이 오늘 생일이므로 '안부 연락' 알림이 생성되고,
    # 배우자 영희의 생일/결혼기념일로 '안부 연락' 알림 2개 추가,
    # 5일 뒤 만기 도래 정기예금으로 '만기 알림' 1개가 자동 생성되어 총 4개가 되어야 함.
    # (참고: ChurnLevel 위험 등급은 오늘 날짜로 seed되어 Churn Level '위험' 경고 알림까지 생성되어 총 5개)
    response_count = client.get("/api/v1/notifications/today-count")
    assert response_count.status_code == 200
    data_count = response_count.json()
    assert data_count["today_count"] >= 4  # (생일, 지인생일, 지인결혼기념일, 예금만기, 이탈위험 경고 등)
    
    # 2. 알림 목록 조회 검증
    response_list = client.get("/api/v1/notifications?tab=today")
    assert response_list.status_code == 200
    notifications = response_list.json()
    assert len(notifications) >= 4
    
    # 알림 카테고리별 정상 분류 검증
    categories = [n["type"] for n in notifications]
    assert "안부 연락" in categories
    assert "만기 알림" in categories
    assert "이탈 위험" in categories
    
    # 세부 텍스트 확인
    birthday_alert = next(n for n in notifications if "생일 축하" in n["content"] and "김철수" in n["content"])
    assert birthday_alert["category"] == "indigo" # indigo가 안부 연락 카테고리 색상
    
    maturity_alert = next(n for n in notifications if "만기" in n["content"] and "WON플러스예금" in n["content"])
    assert maturity_alert["category"] == "blue" # blue가 만기 알림 색상

def test_get_visitor_briefing_on_demand_success(client):
    # 1. 오늘 상담 일정이 등록되지 않았을 때는 브리핑 null 반환
    response_before = client.get("/api/v1/notifications/briefing/1001")
    assert response_before.status_code == 200
    assert response_before.json() is None
    
    # 2. 오늘 김철수(1001) 고객과의 상담 일정 생성
    client.post("/api/v1/schedules", json={
        "category": "상담",
        "content": "김철수 고객 자산상담",
        "startDatetime": f"{date.today().strftime('%Y-%m-%d')}T10:00:00",
        "endDatetime": f"{date.today().strftime('%Y-%m-%d')}T11:00:00",
        "customer_id": 1001
    })
    
    # 3. 브리핑 조회 시 실시간 온디맨드 생성기 작동 검증 (mock OpenAI client가 작동)
    response_after = client.get("/api/v1/notifications/briefing/1001")
    assert response_after.status_code == 200
    briefing = response_after.json()
    assert briefing is not None
    assert briefing["isBriefing"] is True
    assert briefing["category"] == "green" # green이 방문 예정 브리핑 색상
    
    # LLM이 포맷에 맞춰 출력한 보고서 내용인지 확인
    expanded_text = "".join(briefing["expandedContent"])
    assert "[Quick Summary]" in expanded_text
    assert "[고객 정보 & Preference]" in expanded_text
    assert "☕ 따뜻한 아메리카노" in expanded_text
    assert "[자산 현황 & 최근 거래 내역]" in expanded_text
    assert "[핵심 특이사항]" in expanded_text
    assert "이전 상담 히스토리 요약:" in expanded_text

def test_generate_briefing_llm_fallback(mocker, client):
    # OpenAI API 호출 시 의도적으로 예외(에러)를 발생시킴
    from tests.conftest import MockChatCompletions
    mocker.patch.object(MockChatCompletions, "create", side_effect=Exception("OpenAI Rate Limit Exceeded"))
    
    # 1. 오늘 김철수(1001) 고객과의 상담 일정 생성
    client.post("/api/v1/schedules", json={
        "category": "상담",
        "content": "김철수 고객 자산상담",
        "startDatetime": f"{date.today().strftime('%Y-%m-%d')}T10:00:00",
        "endDatetime": f"{date.today().strftime('%Y-%m-%d')}T11:00:00",
        "customer_id": 1001
    })
    
    # 2. 브리핑 생성 요청 -> Heuristic Fallback 모드가 실행되는지 검증
    # (에러가 전파되지 않고, conftest.py 또는 visit_brief_generator.py의 예외 처리 로직에 의해 룰 기반 생성 텍스트가 정상 전달되어야 함)
    response = client.get("/api/v1/notifications/briefing/1001")
    assert response.status_code == 200
    briefing = response.json()
    assert briefing is not None
    
    # Fallback 템플릿에 들어있는 기본 시그니처 텍스트 검증
    expanded_text = "".join(briefing["expandedContent"])
    assert "[Quick Summary]" in expanded_text
    assert "Heuristic Fallback" in expanded_text or "최근 총 자산 변동성이 확인된" in expanded_text
