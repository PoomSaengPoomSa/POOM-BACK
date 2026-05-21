from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime, date


# 대시보드
class TrendDashboardResponse(BaseModel):
    headlines: dict  # category -> headline list
    indicators: dict  # latest values


# 뉴스
class NewsItem(BaseModel):
    news_id: int
    title: str
    category: str
    body: Optional[str] = None
    published_at: datetime = Field(alias="publishedAt")
    source: str
    origin_url: Optional[str] = Field(None, alias="originUrl")
    tags: Optional[List[str]] = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class NewsListResponse(BaseModel):
    news: List[NewsItem]
    total: int
    page: int
    size: int


class NewsBulkRequest(BaseModel):
    items: List[NewsItem]


class NewsBulkDeleteRequest(BaseModel):
    news_ids: List[int]


class NewsBulkResponse(BaseModel):
    saved: int
    skipped: int


# 경제지표
class IndicatorLatest(BaseModel):
    type: str
    yesterday: Optional[float] = None
    today: Optional[float] = None
    tomorrow_prediction: Optional[float] = None
    change_rate: Optional[float] = None
    direction: Optional[str] = None  # 'up', 'down', 'flat'


class IndicatorHistoryPoint(BaseModel):
    date: date
    value: float


class IndicatorHistoryResponse(BaseModel):
    type: str
    data: List[IndicatorHistoryPoint]
    min: Optional[float] = None
    max: Optional[float] = None
    avg: Optional[float] = None


class IndicatorPrediction(BaseModel):
    date: date
    predicted_value: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None


class IndicatorPredictionResponse(BaseModel):
    type: str
    predictions: List[IndicatorPrediction]


class ContributionItem(BaseModel):
    variable: str
    weight: float


class ContributionResponse(BaseModel):
    type: str
    contributions: List[ContributionItem]


# LLM 보고서
class ReportCreateRequest(BaseModel):
    model: Optional[str] = "gpt-4"
    language: Optional[str] = "ko"


class ReportCreateResponse(BaseModel):
    report_id: str
    status: str = "pending"


class ReportStatusResponse(BaseModel):
    report_id: str
    status: str  # pending, running, done, failed


class ReportResponse(BaseModel):
    report_id: str
    content: str
    model_name: str
    created_at: datetime
    data_source: Optional[str] = None


# 지표 일괄 등록
class IndicatorBulkItem(BaseModel):
    type: str
    value: float
    recorded_at: datetime = Field(alias="recordedAt")
    source: str
    model_config = ConfigDict(populate_by_name=True)


class IndicatorBulkRequest(BaseModel):
    items: List[IndicatorBulkItem]


class IndicatorBulkResponse(BaseModel):
    saved: int
    skipped: int
