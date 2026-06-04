from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict
from datetime import datetime, date


# 대시보드
class DashboardNewsItem(BaseModel):
    id: str
    title: str
    publishedAt: str

class DashboardNews(BaseModel):
    economy: List[DashboardNewsItem]
    politics: List[DashboardNewsItem]
    international: Optional[List[DashboardNewsItem]] = None
    itScience: Optional[List[DashboardNewsItem]] = None
    # 하위 호환성을 위해 기존 'it' 필드도 보너스로 포함하여 클라이언트 오류 방지
    it: Optional[List[DashboardNewsItem]] = None

class DashboardGoldRealEstate(BaseModel):
    yesterday: Optional[float] = None
    today: Optional[float] = None
    tomorrow: Optional[float] = None
    changeRate: Optional[float] = None
    changeDirection: Optional[str] = None  # 'up', 'down', 'flat'
    probRise: Optional[float] = None
    probFall: Optional[float] = None
    predictionText: Optional[str] = None

class DashboardInterestRate(BaseModel):
    lastMonth: Optional[float] = None
    thisMonth: Optional[float] = None
    nextMonth: Optional[float] = None
    changeRate: Optional[float] = None
    changeDirection: Optional[str] = None  # 'up', 'down', 'flat'
    probCut: Optional[float] = None
    probFreeze: Optional[float] = None
    probHike: Optional[float] = None
    predictionText: Optional[str] = None

class DashboardIndicators(BaseModel):
    gold: DashboardGoldRealEstate
    realEstate: DashboardGoldRealEstate
    interestRate: DashboardInterestRate

class RealtimeTrendItem(BaseModel):
    name: str
    value: str
    unit: str
    rate: str
    direction: str

class TrendDashboardResponse(BaseModel):
    news: DashboardNews
    indicators: DashboardIndicators
    realtimeTrends: Optional[List[RealtimeTrendItem]] = None
    aiSummaries: Optional[Dict[str, str]] = None


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


class NewsSearchItem(BaseModel):
    id: str
    title: str
    category: str
    publishedAt: str = Field(alias="publishedAt")
    isBookmarked: bool = Field(False, alias="isBookmarked")
    model_config = ConfigDict(populate_by_name=True)

class PaginationInfo(BaseModel):
    page: int
    size: int
    totalCount: int
    totalPages: int

class NewsListResponse(BaseModel):
    items: List[NewsSearchItem]
    pagination: PaginationInfo


class NewsBulkItem(BaseModel):
    title: str
    category: str
    body: str
    publishedAt: str = Field(alias="publishedAt")
    source: str
    originUrl: str = Field(alias="originUrl")
    tags: Optional[List[str]] = None
    model_config = ConfigDict(populate_by_name=True)

class NewsBulkRequest(BaseModel):
    items: List[NewsBulkItem]

class NewsBulkResponse(BaseModel):
    savedCount: int = Field(alias="savedCount")
    skippedCount: int = Field(alias="skippedCount")
    skippedUrls: Optional[List[str]] = Field(None, alias="skippedUrls")
    model_config = ConfigDict(populate_by_name=True)

class NewsBulkDeleteRequest(BaseModel):
    news_ids: List[str]

class NewsBulkDeleteResponse(BaseModel):
    deletedIds: List[str] = Field(alias="deletedIds")
    notFoundIds: Optional[List[str]] = Field(None, alias="notFoundIds")
    deletedCount: int = Field(alias="deletedCount")
    model_config = ConfigDict(populate_by_name=True)


# 경제지표
class YesterdayValue(BaseModel):
    value: float
    recordedAt: str

class TodayValue(BaseModel):
    value: float
    changeRate: float
    direction: str
    recordedAt: str

class TomorrowPrediction(BaseModel):
    value: Optional[float] = None
    changeRate: Optional[float] = None
    direction: Optional[str] = None
    probRise: Optional[float] = None
    probFall: Optional[float] = None
    probCut: Optional[float] = None
    probFreeze: Optional[float] = None
    probHike: Optional[float] = None
    predictionText: Optional[str] = None

class IndicatorLatest(BaseModel):
    type: str
    labelKo: str
    labelEn: str
    yesterday: YesterdayValue
    today: TodayValue
    tomorrow: TomorrowPrediction


class IndicatorHistorySeriesPoint(BaseModel):
    date: str
    value: float

class IndicatorHistoryStats(BaseModel):
    min: float
    max: float
    avg: float

class IndicatorHistoryResponse(BaseModel):
    type: str
    granularity: str
    source: str
    series: List[IndicatorHistorySeriesPoint]
    stats: IndicatorHistoryStats


class MlflowInfo(BaseModel):
    run_id: Optional[str] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    stage: Optional[str] = None


class IndicatorPredictionItem(BaseModel):
    date: str
    value: Optional[float] = None
    lower: Optional[float] = None
    upper: Optional[float] = None


class IndicatorPredictionResponse(BaseModel):
    type: str
    horizon: int
    predictions: List[IndicatorPredictionItem]
    mlflow: MlflowInfo
    generatedAt: str
    source: Optional[str] = None


class ContributionItem(BaseModel):
    feature: str
    label: str
    ratio: float


class ContributionResponse(BaseModel):
    type: str
    contributions: List[ContributionItem]
    mlflow: MlflowInfo
    generatedAt: str


# LLM 보고서
class ReportCreateRequest(BaseModel):
    model: Optional[str] = "gpt-4"
    language: Optional[str] = "ko"


class ReportCreateResponse(BaseModel):
    reportId: str = Field(alias="reportId")
    status: str = "pending"
    estimatedSeconds: Optional[int] = Field(30, alias="estimatedSeconds")
    model_config = ConfigDict(populate_by_name=True)


class ReportStatusResponse(BaseModel):
    reportId: str = Field(alias="reportId")
    status: str  # pending, running, done, failed
    progress: Optional[int] = None
    failedReason: Optional[str] = Field(None, alias="failedReason")
    completedAt: Optional[str] = Field(None, alias="completedAt")
    model_config = ConfigDict(populate_by_name=True)



class DataSourcePeriod(BaseModel):
    from_date: str = Field(alias="from")
    to_date: str = Field(alias="to")
    model_config = ConfigDict(populate_by_name=True)


class ReportResponse(BaseModel):
    reportId: str = Field(alias="reportId")
    type: str
    content: str
    summary: str
    language: str
    modelName: str = Field(alias="modelName")
    dataSources: List[str] = Field(alias="dataSources")
    dataSourcePeriod: DataSourcePeriod = Field(alias="dataSourcePeriod")
    generatedAt: str = Field(alias="generatedAt")
    model_config = ConfigDict(populate_by_name=True)


# 지표 일괄 등록
class IndicatorBulkItem(BaseModel):
    type: str
    value: float
    recorded_at: datetime = Field(alias="recordedAt")
    source: str
    model_config = ConfigDict(populate_by_name=True)


class IndicatorBulkRequest(BaseModel):
    items: List[IndicatorBulkItem]


class IndicatorBulkError(BaseModel):
    index: int
    reason: str


class IndicatorBulkResponse(BaseModel):
    savedCount: int = Field(alias="savedCount")
    skippedCount: int = Field(alias="skippedCount")
    failedCount: int = Field(alias="failedCount")
    errors: Optional[List[IndicatorBulkError]] = None
    model_config = ConfigDict(populate_by_name=True)


# Aliases & Wrappers for trend router compatibility
class NewsDetailResponse(BaseModel):
    newsId: str = Field(alias="newsId")
    title: str
    body: str
    category: str
    source: str
    originUrl: Optional[str] = Field(None, alias="originUrl")
    tags: List[str]
    publishedAt: str = Field(alias="publishedAt")
    createdAt: str = Field(alias="createdAt")
    model_config = ConfigDict(populate_by_name=True)

IndicatorLatestResponse = IndicatorLatest
IndicatorContributionResponse = ContributionResponse
ReportLatestResponse = ReportResponse


class MessageResponse(BaseModel):
    message: str
