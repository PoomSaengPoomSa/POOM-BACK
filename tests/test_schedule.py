import pytest

def test_get_schedules_list(client):
    # 처음에는 아무런 일정도 없는 상태
    response = client.get("/api/v1/schedules")
    assert response.status_code == 200
    assert len(response.json()) == 0

def test_create_schedule_success(client):
    response = client.post("/api/v1/schedules", json={
        "category": "상담",
        "content": "박영희 고객 연금 컨설팅",
        "startDatetime": "2026-06-05T15:00:00",
        "endDatetime": "2026-06-05T16:00:00",
        "color": "green",
        "customer_id": 1001, # seed_data에 김철수 존재
        "memo": "연금 자산 배분 상담"
    })
    assert response.status_code == 200
    
    # 생성 확인
    response_get = client.get("/api/v1/schedules")
    assert response_get.status_code == 200
    schedules = response_get.json()
    assert len(schedules) == 1
    assert schedules[0]["title"] == "박영희 고객 연금 컨설팅"
    assert schedules[0]["customer_name"] == "김철수"

def test_update_schedule_success(client):
    # 1. 일정 등록
    response_create = client.post("/api/v1/schedules", json={
        "category": "상담",
        "content": "수정 전 일정",
        "startDatetime": "2026-06-05T15:00:00",
        "endDatetime": "2026-06-05T16:00:00",
        "color": "green",
        "customer_id": 1001,
        "memo": "메모"
    })
    s_id = response_create.json()["s_id"]
    
    # 2. 일정 수정
    response_update = client.patch(f"/api/v1/users/user1/schedules/{s_id}", json={
        "category": "개인",
        "content": "수정 후 일정",
        "startDatetime": "2026-06-05T16:00:00",
        "endDatetime": "2026-06-05T17:00:00",
        "color": "gray",
        "memo": "수정 완료된 메모"
    })
    assert response_update.status_code == 200
    
    # 3. 변경 사항 확인
    response_get = client.get("/api/v1/schedules")
    schedules = response_get.json()
    matched = next(s for s in schedules if s["s_id"] == s_id)
    assert matched["title"] == "수정 후 일정"
    assert matched["category"] == "개인"

def test_delete_schedule_success(client):
    # 1. 일정 등록
    response_create = client.post("/api/v1/schedules", json={
        "category": "개인",
        "content": "삭제 예정 일정",
        "startDatetime": "2026-06-05T15:00:00",
        "endDatetime": "2026-06-05T16:00:00",
        "color": "blue"
    })
    s_id = response_create.json()["s_id"]
    
    # 2. 일정 삭제
    response_delete = client.delete(f"/api/v1/schedules/{s_id}")
    assert response_delete.status_code in (200, 204, 201)
    
    # 3. 삭제 완료 확인
    response_get = client.get("/api/v1/schedules")
    assert len(response_get.json()) == 0
