from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.trend import (
    TrendDashboardResponse,
    NewsListResponse,
    NewsDetailResponse,
    NewsBulkRequest,
    NewsBulkResponse,
    NewsBulkDeleteRequest,
    IndicatorLatestResponse,
    IndicatorHistoryResponse,
    IndicatorPredictionResponse,
    IndicatorContributionResponse,
    ReportCreateRequest,
    ReportCreateResponse,
    ReportStatusResponse,
    ReportLatestResponse,
    IndicatorBulkRequest,
    IndicatorBulkResponse,
    MessageResponse,
)
from app.services import trend as trend_service

router = APIRouter(tags=["Trend"])


@router.get("/dashboard", response_model=TrendDashboardResponse)
async def get_trend_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """트렌드 대시보드 조회"""
    return await trend_service.get_trend_dashboard(current_user, db)


@router.get("/news", response_model=NewsListResponse)
async def get_news_list(
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """뉴스 목록 조회"""
    return await trend_service.get_news_list(
        category, q, page, size, from_date, to_date, sort, current_user, db
    )


@router.get("/news/{news_id}", response_model=NewsDetailResponse)
async def get_news_detail(
    news_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """뉴스 상세 조회"""
    return await trend_service.get_news_detail(news_id, current_user, db)


@router.post("/news/bulk", response_model=NewsBulkResponse)
async def bulk_create_news(
    request: NewsBulkRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """뉴스 일괄 등록"""
    return await trend_service.bulk_create_news(request, current_user, db)


@router.delete("/news/bulk", response_model=MessageResponse)
async def bulk_delete_news(
    request: NewsBulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """뉴스 일괄 삭제"""
    return await trend_service.bulk_delete_news(request, current_user, db)


@router.get("/indicators/{type}/latest", response_model=IndicatorLatestResponse)
async def get_indicator_latest(
    type: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """지표 최신값 조회"""
    return await trend_service.get_indicator_latest(type, current_user, db)


@router.get("/indicators/{type}/history", response_model=IndicatorHistoryResponse)
async def get_indicator_history(
    type: str,
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    granularity: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """지표 이력 조회"""
    return await trend_service.get_indicator_history(
        type, from_date, to_date, granularity, current_user, db
    )


@router.get(
    "/indicators/{type}/prediction", response_model=IndicatorPredictionResponse
)
async def get_indicator_prediction(
    type: str,
    horizon: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """지표 예측 조회"""
    return await trend_service.get_indicator_prediction(
        type, horizon, current_user, db
    )


@router.get(
    "/indicators/{type}/contribution", response_model=IndicatorContributionResponse
)
async def get_indicator_contribution(
    type: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """지표 기여도 조회"""
    return await trend_service.get_indicator_contribution(type, current_user, db)


@router.post(
    "/indicators/{type}/report",
    response_model=ReportCreateResponse,
    status_code=202,
)
async def create_indicator_report(
    type: str,
    request: ReportCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """지표 리포트 생성 요청"""
    return await trend_service.create_indicator_report(
        type, request, current_user, db
    )


@router.get(
    "/indicators/{type}/report/{report_id}/status",
    response_model=ReportStatusResponse,
)
async def get_report_status(
    type: str,
    report_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """리포트 생성 상태 조회"""
    return await trend_service.get_report_status(
        type, report_id, current_user, db
    )


@router.get(
    "/indicators/{type}/report/latest", response_model=ReportLatestResponse
)
async def get_latest_report(
    type: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """최신 리포트 조회"""
    return await trend_service.get_latest_report(type, current_user, db)


@router.post("/indicators/bulk", response_model=IndicatorBulkResponse)
async def bulk_create_indicators(
    request: IndicatorBulkRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """지표 일괄 등록"""
    return await trend_service.bulk_create_indicators(request, current_user, db)
