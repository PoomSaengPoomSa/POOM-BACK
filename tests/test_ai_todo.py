import pytest

def test_get_ai_todos_success(client):
    response = client.get("/api/v1/ai-todo/?u_id=user1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["todos"]) == 2
    
    todo_titles = [t["title"] for t in data["todos"]]
    assert "김철수 고객 예금 만기 재가입 유도" in todo_titles
    assert "홍길동 PB 개인 AUM 증대 전략 검토" in todo_titles

def test_confirm_ai_todo_success(client):
    # 김철수 고객 AI To-Do 승인 (at_id=10)
    response = client.post("/api/v1/ai-todo/confirm", json={
        "u_id": "user1",
        "at_ids": [10],
        "target_date": "2026-06-05"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["confirmed"] == 1
    assert len(data["schedule_ids"]) == 1

def test_confirm_ai_todo_overlap_conflict(client):
    # 1. 먼저 10시 일정 강제 등록 (중복을 유도하기 위해)
    # 10번 AI To-Do는 10시로 등록 예정.
    # 10시~11시 사이에 겹치는 일정을 미리 임의 등록해 둠.
    response_create = client.post("/api/v1/schedules", json={
        "category": "상담",
        "content": "선점된 일반 미팅",
        "startDatetime": "2026-06-05T10:15:00",
        "endDatetime": "2026-06-05T10:45:00",
        "color": "blue",
        "customer_id": 1001,
        "memo": "이미 있는 선점 미팅"
    })
    assert response_create.status_code == 200
    
    # 2. 동일 날짜/시간대에 at_id=10(10:00~11:00) 승인 시도 -> 충돌 에러 발생 검출
    response_confirm = client.post("/api/v1/ai-todo/confirm", json={
        "u_id": "user1",
        "at_ids": [10],
        "target_date": "2026-06-05"
    })
    assert response_confirm.status_code == 400
    assert "이미 겹치는 일정이 존재합니다" in response_confirm.json()["detail"]

def test_unconfirm_ai_todo_success(client):
    # 1. 먼저 승인 실행
    response_confirm = client.post("/api/v1/ai-todo/confirm", json={
        "u_id": "user1",
        "at_ids": [11],
        "target_date": "2026-06-05"
    })
    assert response_confirm.status_code == 200
    
    # 2. 승인 취소 (복원) 실행
    response_unconfirm = client.patch("/api/v1/ai-todo/11/unconfirm")
    assert response_unconfirm.status_code == 200
    assert response_unconfirm.json()["success"] is True

def test_delete_ai_todo_success(client):
    response = client.delete("/api/v1/ai-todo/10")
    assert response.status_code == 200
    assert response.json()["message"] == "추천 일정이 성공적으로 삭제되었습니다."

def test_run_ai_todo_agent_trigger_success(client):
    response = client.post("/api/v1/ai-todo/run?u_id=user1&date=2026-06-05")
    assert response.status_code == 200
    assert "LangGraph AI ToDo 에이전트 백그라운드 구동 시작" in response.json()["message"]
