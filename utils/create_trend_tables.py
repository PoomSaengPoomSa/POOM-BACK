import datetime
import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models.trend import (
    EconomicIndicatorHistory,
    EconomicIndicatorContribution,
    TrendLlmReport,
)

def seed_data():
    # 1. Create tables
    print("MySQL 데이터베이스에 트렌드 및 경제지표 테이블을 생성 중...")
    Base.metadata.create_all(bind=engine)
    print("테이블 생성 완료!")

    db: Session = SessionLocal()
    try:
        # 다른 테이블은 일절 건드리지 않고 오직 5개의 트렌드 관련 테이블만 청소하여 재설정합니다.
        print("이전 트렌드 & 경제지표 세팅 데이터 초기화 중...")
        db.query(EconomicIndicatorContribution).delete()
        db.query(EconomicIndicatorHistory).delete()
        db.query(TrendLlmReport).delete()
        db.commit()

        print("초기 고품질 트렌드 & 경제지표 데이터 적재(Seeding)를 시작합니다...")

        # 2. Seed Economic Indicators History (최근 30일 데이터)
        today = datetime.datetime.utcnow().date()
        indicators_seed = []

        # Gold: 30일 이력 (80.0 ~ 오늘 95.0)
        gold_values = [
            80.0, 80.5, 81.0, 81.2, 80.8, 81.5, 82.0, 81.8, 82.5, 83.0, 
            82.7, 83.2, 84.0, 84.5, 83.9, 84.8, 85.2, 85.0, 86.0, 87.0, 
            86.5, 87.8, 88.5, 88.0, 89.2, 90.0, 91.5, 92.0, 83.0, 95.0
        ]
        for i, val in enumerate(gold_values):
            rec_date = today - datetime.timedelta(days=(29 - i))
            rec_datetime = datetime.datetime.combine(rec_date, datetime.time(16, 0))
            indicators_seed.append(
                EconomicIndicatorHistory(
                    type="gold",
                    value=Decimal(str(val)),
                    recorded_at=rec_datetime,
                    source="FRED",
                )
            )

        # Real Estate: 30일 이력 (101.5 ~ 오늘 100.3)
        re_values = [
            101.5, 101.4, 101.3, 101.3, 101.2, 101.1, 101.0, 101.0, 100.9, 100.9,
            100.8, 100.8, 100.7, 100.7, 100.6, 100.6, 100.5, 100.5, 100.5, 100.4,
            100.4, 100.4, 100.4, 100.4, 100.4, 100.4, 100.4, 100.4, 100.4, 100.3
        ]
        for i, val in enumerate(re_values):
            rec_date = today - datetime.timedelta(days=(29 - i))
            rec_datetime = datetime.datetime.combine(rec_date, datetime.time(16, 0))
            indicators_seed.append(
                EconomicIndicatorHistory(
                    type="real_estate",
                    value=Decimal(str(val)),
                    recorded_at=rec_datetime,
                    source="ECOS",
                )
            )

        # Base Rate: 12달 및 매월 데이터 (지난달 2.0, 이번달 2.5)
        # 시계열 차트를 위해 매일 2.0 및 2.5를 할당
        for i in range(30):
            rec_date = today - datetime.timedelta(days=(29 - i))
            rec_datetime = datetime.datetime.combine(rec_date, datetime.time(16, 0))
            # 15일 전부터 기준금리가 2.0에서 2.5로 상향 조정된 것으로 처리
            val = 2.5 if i >= 15 else 2.0
            indicators_seed.append(
                EconomicIndicatorHistory(
                    type="base_rate",
                    value=Decimal(str(val)),
                    recorded_at=rec_datetime,
                    source="ECOS",
                )
            )

        db.add_all(indicators_seed)
        db.commit()
        print(f"총 {len(indicators_seed)}개의 지표 이력 데이터 적재 성공!")

        # 3. Seed Contributions (예측 기여도 가중치 - ML 원본 컬럼명 기반)
        contribs = [
            # Gold (ml_gold_raw 기반)
            EconomicIndicatorContribution(type="gold", variable="dxy_proxy", weight=Decimal("0.3200")),
            EconomicIndicatorContribution(type="gold", variable="kr_cpi", weight=Decimal("0.2500")),
            EconomicIndicatorContribution(type="gold", variable="kr_usd_exchange", weight=Decimal("0.2300")),
            EconomicIndicatorContribution(type="gold", variable="wti_oil", weight=Decimal("0.2000")),

            # Real Estate (ml_realestate_raw 기반)
            EconomicIndicatorContribution(type="real_estate", variable="kr_base_rate", weight=Decimal("0.4000")),
            EconomicIndicatorContribution(type="real_estate", variable="kr_cpi", weight=Decimal("0.3000")),
            EconomicIndicatorContribution(type="real_estate", variable="buyer_dominance", weight=Decimal("0.2000")),
            EconomicIndicatorContribution(type="real_estate", variable="kr_mortgage_rate", weight=Decimal("0.1000")),

            # Base Rate (ml_baserate_raw 기반)
            EconomicIndicatorContribution(type="base_rate", variable="us_fed_rate", weight=Decimal("0.3500")),
            EconomicIndicatorContribution(type="base_rate", variable="wti_oil", weight=Decimal("0.2500")),
            EconomicIndicatorContribution(type="base_rate", variable="kr_cpi", weight=Decimal("0.2000")),
            EconomicIndicatorContribution(type="base_rate", variable="kr_usd_exchange", weight=Decimal("0.2000")),
        ]
        db.add_all(contribs)
        db.commit()
        print(f"총 {len(contribs)}개의 지표 예측 기여도 가중치 적재 성공!")

        # 5. Seed LLM Reports
        gold_report = (
            "### [금값 분석 리포트]\n\n"
            "향후 12개월간 금값은 3,890달러 수준으로 완만한 상승이 예상됩니다. 미 연준의 금리 인하 기조와 지정학적 불안이 주요 상승 요인입니다.\n\n"
            "**1. 인플레이션 헷지 수요 지속**\n"
            "글로벌 지정학적 불안 지속으로 리스크 회피를 위한 안전 자산 유입세가 지속되고 있으며, 각국 중앙은행의 실물 금 매수 흐름이 가격 하방 지지선을 강화하고 있습니다.\n\n"
            "**2. 통화정책 완화 기조**\n"
            "미국의 소비자물가지수(CPI)가 하향 안정화되는 신호에 따라 연준의 연내 추가 금리 인하 기대가 달러화 약세 압력을 높여 금 가격의 추가적인 상승 모멘텀을 지지하고 있습니다."
        )
        re_report = (
            "### [부동산 가격지수 분석 리포트]\n\n"
            "서울 아파트 시장의 회복세를 지지할 것으로 보입니다. 거래량은 점진적으로 증가하고 있으며, 매매수급동향도 호전되고 있습니다.\n\n"
            "**1. 매수세의 회복**\n"
            "금리 인하 기조가 본격화되면서 대출 이자 부담이 다소 줄어들자 서울 및 수도권의 정주 여건이 우수한 단지를 중심으로 실수요자의 적극적인 진입이 두드러지고 있습니다.\n\n"
            "**2. 공급 대책의 영향**\n"
            "정부의 도심 주택 공급 확대 대책이 발표되었으나 실제 착공 및 완공 시점까지의 공급 공백기가 존재하므로, 기축 아파트 가격의 일시적인 완만한 우상향 압력이 발생하고 있습니다."
        )
        br_report = (
            "### [기준 금리 분석 리포트]\n\n"
            "한국 기준금리는 2.50%까지 단계적 인하가 전망되며, 물가 안정화 추세에 따라 하반기부터 통화정책 전환 가능성이 제기됩니다.\n\n"
            "**1. 물가상승률(CPI) 하향 안정**\n"
            "최근 3개월간 한국의 소비자물가 지표가 한국은행의 물가 안정 목표치인 2.0%대에 안착하는 경향이 입증되어 통화 긴축을 지속해야 할 객관적 압박이 매우 완화되었습니다.\n\n"
            "**2. 경기 부양 필요성 확대**\n"
            "내수 소비 지표의 침체와 건설 투자 위축이 가속화되면서 경제 전반의 연착륙을 유도하기 위해 한은 금융통화위원회가 하반기 중 기준금리 인하 사이클에 진입할 가능성이 대우 높습니다."
        )

        gold_summary = (
            "### [금값 분석 리포트]\n\n"
            "향후 12개월간 금값은 3,890달러 수준으로 완만한 상승이 예상됩니다.\n\n"
            "**1. 인플레이션 헷지 수요 지속**: 안전 자산 유입이 계속되어 하방 지지선이 견고합니다.\n"
            "**2. 통화정책 완화 기조**: 연준의 추가 금리 인하 기대가 금 가격 상승을 지지합니다."
        )
        re_summary = (
            "### [부동산 가격지수 분석 리포트]\n\n"
            "서울 아파트 시장의 회복세를 지지할 것으로 보입니다.\n\n"
            "**1. 매수세의 회복**: 대출 이자 부담 감소로 실수요자의 진입이 늘어납니다.\n"
            "**2. 공급 대책의 영향**: 도심 주택 공급 확대 대책 발표로 아파트 가격 우상향 압력이 있습니다."
        )
        br_summary = (
            "### [기준금리 전망 리포트]\n\n"
            "한국 기준금리는 2.50%까지 단계적 인하가 전망됩니다.\n\n"
            "**1. 물가상승률(CPI) 하향 안정**: 소비자물가가 2.0%대에 안착하여 인하 압력이 완화되었습니다.\n"
            "**2. 경기 부양 필요성 확대**: 내수 침체 극복을 위해 금통위가 인하 사이클에 진입할 가능성이 높습니다."
        )

        reports = [
            TrendLlmReport(
                type="gold",
                content=gold_report,
                summary=gold_summary,
                created_at=datetime.datetime.utcnow(),
            ),
            TrendLlmReport(
                type="real_estate",
                content=re_report,
                summary=re_summary,
                created_at=datetime.datetime.utcnow(),
            ),
            TrendLlmReport(
                type="base_rate",
                content=br_report,
                summary=br_summary,
                created_at=datetime.datetime.utcnow(),
            ),
        ]
        db.add_all(reports)
        db.commit()
        print(f"총 {len(reports)}개의 LLM 분석 보고서 적재 성공!")
        print("초기 모든 데이터 적재 완료!")

    except Exception as e:
        db.rollback()
        print(f"데이터 적재 중 심각한 에러 발생: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
