import time
from cachetools import TTLCache

# 10분(600초) 동안 활동이 없으면 자동 오프라인 처리
online_users = TTLCache(maxsize=10000, ttl=600)

def mark_user_active(user_id: str):
    if user_id and user_id != "system":
        online_users[user_id] = time.time()

def get_active_users() -> list:
    return list(online_users.keys())
