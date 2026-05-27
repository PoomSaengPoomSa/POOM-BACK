from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, Date, Index
from app.database import Base
import datetime

class TrendNews(Base):
    """뉴스 아카이브 테이블 모델"""
    __tablename__ = "trend_news"

    news_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # 'economy', 'politics', 'it' 등
    body = Column(Text, nullable=True)
    published_at = Column(DateTime, default=datetime.datetime.utcnow)
    source = Column(String(100), nullable=False)
    origin_url = Column(String(255), nullable=True)
    tags = Column(String(255), nullable=True)  # 쉼표 구분 태그 목록

    __table_args__ = (
        Index('idx_tn_cat_pub', 'category', published_at.desc()),
        Index('idx_tn_pub', published_at.desc()),
        Index('idx_tn_url', 'origin_url'),
    )

class EconomicIndicatorHistory(Base):
    """경제지표 과거 이력 테이블 모델"""
    __tablename__ = "economic_indicator_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)  # 'gold', 'real_estate', 'base_rate' 등
    value = Column(Numeric(15, 4), nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    source = Column(String(100), nullable=True)

    __table_args__ = (
        Index('idx_eih_type_recorded', 'type', recorded_at.desc()),
    )

class EconomicIndicatorPrediction(Base):
    """경제지표 ML 예측 테이블 모델"""
    __tablename__ = "economic_indicator_prediction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)  # 'gold', 'real_estate', 'base_rate' 등
    predicted_value = Column(Numeric(15, 4), nullable=False)
    confidence_lower = Column(Numeric(15, 4), nullable=True)
    confidence_upper = Column(Numeric(15, 4), nullable=True)
    predicted_date = Column(Date, nullable=False)

    __table_args__ = (
        Index('idx_eip_type_date', 'type', predicted_date.asc()),
    )

class EconomicIndicatorContribution(Base):
    """지표 예측 기여도 테이블 모델"""
    __tablename__ = "economic_indicator_contribution"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)
    variable = Column(String(100), nullable=False)  # 변수 이름 (예: 달러 인덱스)
    weight = Column(Numeric(5, 4), nullable=False)  # SHAP 기여도 가중치

class TrendLlmReport(Base):
    """LLM 생성 분석 보고서 테이블 모델"""
    __tablename__ = "trend_llm_report"

    report_id = Column(String(50), primary_key=True)
    type = Column(String(50), nullable=False)
    model_name = Column(String(50), nullable=False, default="gpt-4")
    language = Column(String(10), nullable=False, default="ko")
    content = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="done")  # pending, running, done, failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    data_source = Column(String(255), nullable=True)
