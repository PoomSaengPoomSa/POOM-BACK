from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, admin, schedule, customer, trend, ai_todo, kpi

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 POOM API 서버가 시작되었습니다.")
    yield
    logger.info("👋 POOM API 서버가 종료됩니다.")


app = FastAPI(
    title="POOM API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정
origins = [
    "http://localhost:5173",
    "http://localhost:5174",  # 이거 추가
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(schedule.router, prefix="/api/v1", tags=["Schedule"])
app.include_router(customer.router, prefix="/api/v1/customers", tags=["Customer"])
app.include_router(trend.router, prefix="/api/v1/trend", tags=["Trend"])
app.include_router(ai_todo.router, prefix="/api/v1/ai-todo", tags=["AI Todo"])
app.include_router(kpi.router, prefix="/api/v1/kpi", tags=["KPI"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
