import datetime
import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models.trend import (
    TrendNews,
    EconomicIndicatorHistory,
    EconomicIndicatorPrediction,
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
        db.query(EconomicIndicatorPrediction).delete()
        db.query(EconomicIndicatorHistory).delete()
        db.query(TrendLlmReport).delete()
        db.query(TrendNews).delete()
        db.commit()

        print("초기 고품질 트렌드 & 경제지표 데이터 적재(Seeding)를 시작합니다...")

        # 2. Seed News Data
        news_items = [
            # 경제 뉴스 (economy)
            TrendNews(
                title="코스피 2,700 돌파 — 사상 최고치 3일 연속 경신. 'Sell in May' 격언 유효 여부 주목",
                category="economy",
                body="코스피 지수가 외국인과 기관의 강력한 동반 매수세에 힘입어 종가 기준 2,700선을 돌파했습니다. 3일 연속 최고치 경신으로, 미국 기술주 호조와 국내 반도체 기업들의 턴어라운드 전망이 견인했습니다. 일부 전문가들은 5월 하락장 격언인 'Sell in May'를 우려하고 있으나, 펀더멘털 개선세가 뚜렷하여 추가 상승 여력이 충분하다는 분석이 지배적입니다.",
                published_at=datetime.datetime(2026, 5, 24, 9, 30),
                source="연합인포맥스",
                origin_url="https://news.einfomax.co.kr/news/123",
                tags="코스피,주식시장,금융위원회",
            ),
            TrendNews(
                title="삼성전자 어닝 서프라이즈 — 1분기 영업이익 5.72조 원(+756%), 주가 장중 신고가 경신",
                category="economy",
                body="삼성전자가 1분기 잠정 실적 발표를 통해 매출 71조 원, 영업이익 5.72조 원을 기록했다고 공시했습니다. 이는 시장 전망치를 30% 이상 초과한 수치로, 메모리 반도체 가격 상승과 HBM3E 납품 본격화로 인한 DS 부문 적자 폭 축소가 주요인입니다. 발표 직후 주가는 장중 5% 급등하며 역대 신고가를 돌파했습니다.",
                published_at=datetime.datetime(2026, 5, 23, 10, 15),
                source="매일경제",
                origin_url="https://mk.co.kr/news/456",
                tags="삼성전자,실적발표,반도체",
            ),
            TrendNews(
                title="카카오, 1분기 영업이익 2,114억 원 달성... 전년 대비 66% 성장",
                category="economy",
                body="카카오가 올해 1분기 연결 기준 매출 1조 9,870억 원, 영업이익 2,114억 원을 기록했다고 발표했습니다. 플랫폼 부문의 톡비즈 광고 매출 확대와 더불어 콘텐츠 부문의 뮤직, 미디어 부문 글로벌 성장이 호실적을 견인했습니다. 특히 인건비 및 마케팅비 효율화 등 비용 제어가 유효했다는 평가를 받습니다.",
                published_at=datetime.datetime(2026, 5, 22, 14, 0),
                source="한국경제",
                origin_url="https://hankyung.com/news/789",
                tags="카카오,어닝서프라이즈,빅테크",
            ),
            TrendNews(
                title="HMM 예인선 도착 완료... 지체된 물류 수송 오늘 오전 중 전격 재개 예정",
                category="economy",
                body="HMM의 초대형 컨테이너선이 엔진 문제로 일시 정박했던 해역에 긴급 예인 보트와 정비팀이 도착했습니다. 선사 측은 오늘 오전 중 간단한 부품 교체와 정밀 검사를 마치고 지체된 물류 수송 업무를 전격 재개할 예정이라고 밝혔습니다. 물류 대란 우려가 조기에 해소되면서 해운 업계도 안도하는 분위기입니다.",
                published_at=datetime.datetime(2026, 5, 21, 8, 45),
                source="조선일보",
                origin_url="https://chosun.com/news/101",
                tags="HMM,물류,해운동향",
            ),

            # 정치 뉴스 (politics)
            TrendNews(
                title="부산 북구갑 3자 구도 확정 — 여야 격돌 속 무소속 한동훈 변수 등장",
                category="politics",
                body="다가오는 보궐선거 최대 격전지로 떠오른 부산 북구갑 선거구의 대진표가 3자 구도로 최종 확정되었습니다. 더불어민주당 하정우 후보와 국민의힘 공천 후보의 양강 구도에 무소속으로 출마를 강행한 한동훈 후보가 가세하면서 선거 판세가 안개정국으로 접어들었습니다. 세 후보는 일제히 지역 전통시장 방원을 시작으로 본격적인 득표전에 돌입했습니다.",
                published_at=datetime.datetime(2026, 5, 24, 11, 0),
                source="동아일보",
                origin_url="https://donga.com/news/202",
                tags="부산보궐선거,공천확정,정치지형",
            ),
            TrendNews(
                title="한동훈 \"이번 대결은 민생 중심 대리전\" — 반이재명 구도 전면 내세워 유세",
                category="politics",
                body="무소속 한동훈 후보가 부산 북구 상가 사거리 유세에서 '이번 선거는 야당 대표의 방탄을 막고 오직 서민과 청년의 미래를 돕는 민생 대리전'이라고 외치며 집중 지지를 호소했습니다. 야당 대표와 민주당 후보를 겨냥한 반이재명 구도 프레임을 부각하는 한편, 자신이 여권 쇄신의 중심에 서겠다고 거듭 공언했습니다.",
                published_at=datetime.datetime(2026, 5, 23, 16, 20),
                source="중앙일보",
                origin_url="https://joongang.co.kr/news/303",
                tags="한동훈,보궐선거,정치현안",
            ),
            TrendNews(
                title="국산 최초 전투기 KF-21 '보라매', 방위사업청 전투용 적합 판정 획득",
                category="politics",
                body="방위사업청은 국산 최초 초음속 전투기 KF-21(보라매)이 군의 최종 작전 요구 요건을 완벽히 만족하여 '전투용 적합 판정'을 최종 획득했다고 공식 발표했습니다. 이로써 양산 단계로 신속히 전환될 예정이며, 우리 영공을 수호하는 핵심 전력으로 자리 잡는 동시에 K-방산의 글로벌 방산 수출에도 큰 기폭제가 될 것으로 보입니다.",
                published_at=datetime.datetime(2026, 5, 22, 9, 0),
                source="KBS 뉴스",
                origin_url="https://news.kbs.co.kr/news/505",
                tags="KF-21,방위사업청,방산수출",
            ),

            # IT/과학 뉴스 (it)
            TrendNews(
                title="스탠퍼드 AI 인덱스 2026 — 생성형 AI, 단순 기술 넘어서 '국가 인프라'로 전면 재편",
                category="it",
                body="스탠퍼드 대학교 인간중심AI연구소(HAI)가 발표한 'AI 인덱스 2026' 보고서에 따르면 생성형 AI와 AI 에이전트 기술이 단순 비즈니스 솔루션을 뛰어넘어 전 세계 국가 및 산업의 지배 인프라로 안착하고 있습니다. 보고서는 각국 정부가 자체 주권 AI(Sovereign AI) 확보를 위해 반도체 장비 및 인프라 구축 경쟁에 본격적으로 가세하고 있다고 진단했습니다.",
                published_at=datetime.datetime(2026, 5, 24, 8, 0),
                source="테크엠",
                origin_url="https://techm.kr/news/404",
                tags="스탠퍼드,생성형AI,인프라경쟁",
            ),
            TrendNews(
                title="오픈AI, 마이크로소프트(MS)와의 전용 독점 파트너십 종료 선언... 멀티클라우드 확대",
                category="it",
                body="오픈AI가 마이크로소프트(MS)와 체결해 온 애저(Azure) 기반 전용 클라우드 인프라 독점 파트너십을 완화하고, 아마존(AWS) 및 구글 클라우드와의 대대적인 컴퓨팅 제휴를 체결했다고 발표했습니다. 오픈AI 앤디 재시 임시 협의회원은 안정적인 연산 파워 수급과 AI 트래픽 분산을 위해 멀티클라우드 체제로 가기 위한 전략적 결정이라고 덧붙였습니다.",
                published_at=datetime.datetime(2026, 5, 23, 13, 10),
                source="블로터",
                origin_url="https://bloter.net/news/506",
                tags="오픈AI,MS,멀티클라우드",
            ),
            TrendNews(
                title="카카오, 고도화된 '에이전틱 AI' 신모델 전격 공개 — 톡 채널 내 탐색부터 결제까지 일괄 수행",
                category="it",
                body="카카오가 자사 카카오톡 환경 내에 특화 탑재되는 에이전틱 AI(Agentic AI) 서비스를 발표했습니다. 이 AI 비서는 사용자의 질문과 요구 사항에 반응하여 카카오톡 대화방에서 쇼핑 검색, 매장 예약, 최종 카드 결제 및 배송 추적까지의 모든 단계를 스스로 추론하고 연속 실행할 수 있는 고도의 자율 기능을 탑재해 큰 관심을 끌고 있습니다.",
                published_at=datetime.datetime(2026, 5, 22, 17, 30),
                source="디지털데일리",
                origin_url="https://ddaily.co.kr/news/607",
                tags="카카오톡,에이전틱AI,결제연동",
            ),
        ]
        db.add_all(news_items)
        db.commit()
        print(f"총 {len(news_items)}개의 뉴스 기사 적재 성공!")

        # 3. Seed Economic Indicators History (최근 30일 데이터)
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

        # 4. Seed Economic Indicators Predictions (미래 7일 예측)
        predictions_seed = []

        # Gold: 내일 85.0 및 향후 예측
        gold_pred = [85.0, 85.5, 86.0, 86.2, 86.8, 87.5, 88.0]
        for i, val in enumerate(gold_pred):
            pred_date = today + datetime.timedelta(days=(i + 1))
            predictions_seed.append(
                EconomicIndicatorPrediction(
                    type="gold",
                    predicted_value=Decimal(str(val)),
                    confidence_lower=Decimal(str(val - 1.5)),
                    confidence_upper=Decimal(str(val + 1.5)),
                    predicted_date=pred_date,
                )
            )

        # Real Estate: 내일 100.2 및 향후 예측
        re_pred = [100.2, 100.2, 100.1, 100.1, 100.0, 100.0, 99.9]
        for i, val in enumerate(re_pred):
            pred_date = today + datetime.timedelta(days=(i + 1))
            predictions_seed.append(
                EconomicIndicatorPrediction(
                    type="real_estate",
                    predicted_value=Decimal(str(val)),
                    confidence_lower=Decimal(str(val - 0.2)),
                    confidence_upper=Decimal(str(val + 0.2)),
                    predicted_date=pred_date,
                )
            )

        # Base Rate: 다음달 예측 2.0 및 향후 예측
        br_pred = [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0]
        for i, val in enumerate(br_pred):
            pred_date = today + datetime.timedelta(days=(i + 1))
            predictions_seed.append(
                EconomicIndicatorPrediction(
                    type="base_rate",
                    predicted_value=Decimal(str(val)),
                    confidence_lower=Decimal(str(val - 0.25)),
                    confidence_upper=Decimal(str(val + 0.25)),
                    predicted_date=pred_date,
                )
            )

        db.add_all(predictions_seed)
        db.commit()
        print(f"총 {len(predictions_seed)}개의 지표 예측 데이터 적재 성공!")

        # 5. Seed Contributions (예측 기여도 가중치 - ML 원본 컬럼명 기반)
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

        # 6. Seed LLM Reports
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

        reports = [
            TrendLlmReport(
                type="gold",
                content=gold_report,
                created_at=datetime.datetime.utcnow(),
            ),
            TrendLlmReport(
                type="real_estate",
                content=re_report,
                created_at=datetime.datetime.utcnow(),
            ),
            TrendLlmReport(
                type="base_rate",
                content=br_report,
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
