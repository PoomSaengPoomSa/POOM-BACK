from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, Date, Index
from app.database import Base
import datetime

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

    report_id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
