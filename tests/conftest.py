import os
import sys
from datetime import datetime, date, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock

# POOM-BACK 루트 디렉토리를 파이썬 패스에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. sys.modules에 가짜 openai 주입 (app.main 임포트 시 ModuleNotFoundError 방지)
mock_openai = MagicMock()
sys.modules["openai"] = mock_openai

class MockChatCompletions:
    def create(self, *args, **kwargs):
        class MockMessage:
            content = (
                "[Quick Summary]\n"
                "- 5일 뒤 예금 만기가 예정되어 있으므로 고금리 정기 특판 재가입 권장.\n"
                "- 자금 이탈 위험군으로 등록되어 있어 신중한 세후 수익률 비교 상담 필요.\n\n"
                "[고객 정보 & Preference]\n"
                "- 고객명/등급: 김철수 고객 (안정추구형 성향)\n"
                "- 음료/편의 선호도 (★필독):\n"
                "  ☕ 따뜻한 아메리카노 연하게 선호\n\n"
                "[자산 현황 & 최근 거래 내역]\n"
                "- 총 자산: 800,000,000 원\n"
                "- 보유 상품 상세:\n"
                "  - 우리WON플러스예금 (만기: 2026-06-10)\n\n"
                "[핵심 특이사항]\n"
                "- 이탈 위험도: 위험 (타행 예금 특판 문의 및 거액 자산 출금 징후 포착)\n"
                "- 이전 상담 히스토리 요약:\n"
                "- [2026-05-15] 상담 내용: 만기 금리 우대 조건 유선 문의 | AI 요약: 금리 민감도 높음 | ID: 150"
            )
        class MockChoice:
            message = MockMessage()
        class MockResult:
            choices = [MockChoice()]
        return MockResult()

class MockOpenAIClient:
    def __init__(self, *args, **kwargs):
        self.chat = type("MockChat", (), {"completions": MockChatCompletions()})()

mock_openai.OpenAI = MockOpenAIClient

from app.database import Base, get_db
from app.dependencies import get_current_user
from app.main import app
from app.models.account import Account, PbUser
from app.models.branch import Branch
from app.models.customer import Customer, CustomerInformation, CustomerRelationship
from app.models.customer_account import CustomerAccount, CustomerTransaction
from app.models.product import Product, CustomerProduct, ProductMatching
from app.models.schedule import Schedule
from app.models.ai_todo import AiTodo
from app.models.kpi import Kpi
from app.models.churn_level import ChurnLevel
from app.models.trend import EconomicIndicatorHistory, EconomicIndicatorPrediction
from app.models.ml_raw import MlGoldRaw

# 테스트용 SQLite 인메모리 데이터베이스 생성
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def clean_scratch():
    import glob
    import os
    from pathlib import Path
    
    # Path of scratch
    back_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    scratch_dir = back_dir / "scratch"
    if scratch_dir.exists():
        for f in scratch_dir.glob("last_run_date_*.txt"):
            try:
                os.remove(f)
            except Exception:
                pass
        for f in scratch_dir.glob("generation_*.lock"):
            try:
                os.remove(f)
            except Exception:
                pass
    yield

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # 데이터베이스 스키마 생성
    Base.metadata.create_all(bind=engine)
    yield
    # 데이터베이스 스키마 삭제
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

# 가짜 테스트 유저
class MockUser:
    id = "user1"
    role = "user"
    
    @property
    def pb_user(self):
        # Relationship 모킹용 속성
        class MockPb:
            u_id = "user1"
            name = "홍길동"
            branch = 1
            position = "PB"
            status = "재직"
        return MockPb()

@pytest.fixture(autouse=True)
def override_dependencies(db):
    # get_db 의존성을 테스트용 세션으로 오버라이드
    def _get_db_override():
        try:
            yield db
        finally:
            pass
            
    def _get_current_user_override():
        # DB에서 mock 유저와 연계된 Account 레코드 조회
        user_account = db.query(Account).filter(Account.id == "user1").first()
        if not user_account:
            # 존재하지 않는 경우 가짜 MockUser 객체 리턴
            return MockUser()
        return user_account

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = _get_current_user_override
    
    yield
    
    app.dependency_overrides.clear()

@pytest.fixture
def client():
    # 라이프스팬 이벤트를 트리거하지 않도록 설정 가능 (lifespan 모킹용)
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def seed_data(db):
    # 테스트 공통 기초 데이터 적재
    
    # 1. 지점
    branch = Branch(b_id=1, name="종로금융센터", region="서울", b_phone="02-123-4567", address="서울시 종로구")
    db.add(branch)
    db.flush()
    
    # 2. 계정 및 PB 유저
    account = Account(id="user1", password="hashedpassword", role="user")
    db.add(account)
    db.flush()
    
    pb_user = PbUser(
        u_id="user1",
        name="홍길동",
        email="hong@poom.com",
        number="010-1234-5678",
        branch=1,
        status="재직",
        position="PB",
        start_date=date(2020, 1, 1),
        birth_date=date(1980, 1, 1)
    )
    db.add(pb_user)
    db.flush()

    # 3. 고객 정보
    customer = Customer(
        c_id=1001,
        name="김철수",
        number="010-1111-2222",
        birthday=date(1975, 6, 5), # 오늘 생일로 세팅
        job="의사",
        gender="M",
        email="cheolsu@poom.com",
        address="서울시 종로구",
        tendency="안정추구형",
        total_assets=800000000,
        deposit=500000000,
        investment=300000000,
        pension=0,
        loan=100000000,
        net_worth=700000000,
        marital_status=True,
        grade="VIP",
        llm_insight="자산 포트폴리오 진단 결과 예금 비중이 62.5%로 다소 높은 편입니다."
    )
    db.add(customer)
    db.flush()
    
    # 4. 담당 관계 mapping
    from app.models.in_charge import InCharge
    in_charge = InCharge(u_id="user1", c_id=1001)
    db.add(in_charge)
    db.flush()

    # 5. Churn Level (이탈 위험도)
    churn = ChurnLevel(
        c_id=1001,
        grade="위험",
        reason="타행 예금 특판 문의 및 거액 자산 출금 징후 포착",
        explain_reason="자산 유출 위험군 분류",
        created_date=datetime.now()
    )
    db.add(churn)
    db.flush()
    
    # 6. 주력 상품
    product1 = Product(
        pd_id=1,
        name="우리WON플러스예금",
        type="예적금",
        explanation="고금리 정기예금 상품",
        update_date=datetime.now(),
        issuer="우리은행",
        features="우대금리,비과세 혜택",
        target_customer="안정적인 고수익을 원하는 VIP 고객",
        expected_return=3.5,
        return_type="세전",
        season="여름",
        is_main=True
    )
    product2 = Product(
        pd_id=2,
        name="글로벌 배당주 ETF",
        type="투자상품",
        explanation="글로벌 우량 배당주에 분산 투자",
        update_date=datetime.now(),
        issuer="우리자산운용",
        features="주기적 배당,글로벌 분산",
        target_customer="적극적인 배당 수익을 원하는 적극투자형 고객",
        expected_return=6.2,
        return_type="세후",
        season="사계절",
        is_main=True
    )
    db.add_all([product1, product2])
    db.flush()
    
    # 7. 주력 상품 적합도 매칭
    matching1 = ProductMatching(
        c_id=1001,
        pd_id=1,
        is_suitable=True,
        reason="안정추구형 투자성향에 완벽히 부합함",
        created_date=datetime.now()
    )
    matching2 = ProductMatching(
        c_id=1001,
        pd_id=2,
        is_suitable=False,
        reason="보수적 성향에 대비해 높은 주식형 변동성 위험 존재",
        created_date=datetime.now()
    )
    db.add_all([matching1, matching2])
    db.flush()

    # 8. 고객 보유 상품
    cust_product = CustomerProduct(
        cu_id=1,
        c_id=1001,
        pd_id=1,
        opening_date=date(2025, 6, 12),
        expiration_date=date.today() + timedelta(days=5) # 5일 뒤 만기 도래 세팅
    )
    db.add(cust_product)
    db.flush()
    
    # 9. KPI
    kpi_pb = Kpi(
        recorded_date=datetime.now(),
        kpi_type="PB",
        u_id="user1",
        b_id=1,
        current_new_customer=12,
        target_new_customer=20,
        current_aum=4200000000,
        target_aum=5000000000,
        current_non_interest=4500000,
        target_non_interest=6000000,
        aum=0,
        non_interest=0,
        new_customer=0
    )
    kpi_pb_prev = Kpi(
        recorded_date=datetime.now() - timedelta(days=30),
        kpi_type="PB",
        u_id="user1",
        b_id=1,
        current_new_customer=10,
        target_new_customer=20,
        current_aum=4000000000,
        target_aum=5000000000,
        current_non_interest=4000000,
        target_non_interest=6000000,
        aum=0,
        non_interest=0,
        new_customer=0
    )
    kpi_branch = Kpi(
        recorded_date=datetime.now(),
        kpi_type="BRANCH",
        u_id="user1",
        b_id=1,
        current_new_customer=98,
        target_new_customer=150,
        current_aum=48000000000,
        target_aum=55000000000,
        current_non_interest=72000000,
        target_non_interest=90000000,
        aum=0,
        non_interest=0,
        new_customer=0
    )
    kpi_branch_prev = Kpi(
        recorded_date=datetime.now() - timedelta(days=30),
        kpi_type="BRANCH",
        u_id="user1",
        b_id=1,
        current_new_customer=90,
        target_new_customer=150,
        current_aum=46000000000,
        target_aum=55000000000,
        current_non_interest=70000000,
        target_non_interest=90000000,
        aum=0,
        non_interest=0,
        new_customer=0
    )
    db.add_all([kpi_pb, kpi_pb_prev, kpi_branch, kpi_branch_prev])
    db.flush()

    # 10. AI 투두 추천 일정
    ai_todo1 = AiTodo(
        at_id=10,
        title="김철수 고객 예금 만기 재가입 유도",
        memo="5일 내 만기되는 WON플러스예금 자금 타행 이탈 방어",
        category="상담 일정 제안",
        create_date=datetime.now(),
        execution_date=datetime.combine(date.today(), datetime.min.time()) + timedelta(hours=10), # 오늘 오전 10시
        is_checked=False,
        c_id=1001,
        u_id="user1"
    )
    ai_todo2 = AiTodo(
        at_id=11,
        title="홍길동 PB 개인 AUM 증대 전략 검토",
        memo="KPI 지표 개선을 위한 자산관리 포트폴리오 리디자인",
        category="KPI 기반",
        create_date=datetime.now(),
        execution_date=datetime.combine(date.today(), datetime.min.time()) + timedelta(hours=14), # 오늘 오후 2시
        is_checked=False,
        c_id=None,
        u_id="user1"
    )
    db.add_all([ai_todo1, ai_todo2])
    db.flush()

    # 11. 트렌드 지표 역사 & 예측 데이터
    g_hist1 = EconomicIndicatorHistory(type="gold", value=95.2, recorded_at=datetime.now())
    g_hist2 = EconomicIndicatorHistory(type="gold", value=94.5, recorded_at=datetime.now() - timedelta(days=1))
    
    br_hist1 = EconomicIndicatorHistory(type="base_rate", value=3.5, recorded_at=datetime.now())
    br_hist2 = EconomicIndicatorHistory(type="base_rate", value=3.5, recorded_at=datetime.now() - timedelta(days=30))
    
    db.add_all([g_hist1, g_hist2, br_hist1, br_hist2])
    db.flush()
    
    # Raw SQL로 예측 임시 적재 (ML 모델 예측 결과 재현)
    from sqlalchemy import text
    db.execute(text("CREATE TABLE IF NOT EXISTS gold_predictions (prob_rise REAL, prob_fall REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
    db.execute(text("CREATE TABLE IF NOT EXISTS realestate_predictions (predicted_value REAL, predicted_index REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
    db.execute(text("CREATE TABLE IF NOT EXISTS baserate_predictions (prob_cut REAL, prob_freeze REAL, prob_hike REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
    
    db.execute(text("INSERT INTO gold_predictions (prob_rise, prob_fall) VALUES (0.75, 0.25)"))
    db.execute(text("INSERT INTO realestate_predictions (predicted_value, predicted_index) VALUES (1.25, 103.4)"))
    db.execute(text("INSERT INTO baserate_predictions (prob_cut, prob_freeze, prob_hike) VALUES (0.1, 0.85, 0.05)"))
    
    # 12. 실시간 트렌드용 MlGoldRaw
    raw_trend1 = MlGoldRaw(gr_id=1, loaded_date=datetime.now(), kr_cpi=110.2, kospi200=340.5, sp500=5100.2)
    raw_trend2 = MlGoldRaw(gr_id=2, loaded_date=datetime.now() - timedelta(days=1), kr_cpi=109.8, kospi200=338.2, sp500=5050.5)
    db.add_all([raw_trend1, raw_trend2])
    db.flush()
    
    # 13. 오늘 생일 외 기념일 지인 데이터
    rel = CustomerRelationship(
        c_id=1001,
        relationship_="배우자",
        birthday=date.today(), # 오늘 생일인 지인 세팅
        wedding_date=date.today(), # 오늘 결혼기념일 세팅
        is_spouse=True,
        information="배우자 정보"
    )
    db.add(rel)
    db.flush()

    db.commit()

@pytest.fixture(autouse=True)
def mock_external_calls(mocker):
    # 1. httpx.AsyncClient 비동기 외부 호출 모킹 (Elasticsearch 및 OpenAI 통신 차단)
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self._json_data = json_data
            self.status_code = status_code
            self.text = str(json_data)
            
        def json(self):
            return self._json_data
            
        @property
        def ok(self):
            return 200 <= self.status_code < 300

    async def mock_post(url, *args, **kwargs):
        # Elasticsearch 쿼리에 대한 가짜 응답
        if "sbs_news/_search" in url:
            return MockResponse({
                "hits": {
                    "total": {"value": 10},
                    "hits": [
                        {
                            "_id": "news_123",
                            "_source": {
                                "title": "한국은행 기준금리 연 3.5% 동결 유력 기조",
                                "category": "경제",
                                "published_at": "2026-06-05T10:00:00Z"
                            }
                        }
                    ]
                }
            })
        # OpenAI chat/completions API 에 대한 가짜 응답
        elif "api.openai.com/v1/chat/completions" in url:
            return MockResponse({
                "choices": [{
                    "message": {
                        "content": "- 한국은행이 경제 지표 안정을 위해 기준금리를 3.5%로 다시 한번 동결했습니다.\n- 시장 금리 추이에 맞춘 VIP 고객 자산 방어책이 요구됩니다."
                    }
                }]
            })
        return MockResponse({"message": "Not Mocked"}, 404)

    async def mock_get(url, *args, **kwargs):
        if "sbs_news/_doc" in url:
            return MockResponse({
                "_source": {
                    "title": "기준금리 동결에 따른 자산 리밸런싱 방향",
                    "content": "상세 기사 내용 본문입니다. 경제 카테고리 뉴스의 중요성...",
                    "category": "경제",
                    "author": "SBS 뉴스",
                    "url": "https://sbs.co.kr/news_123"
                }
            })
        return MockResponse({"message": "Not Mocked"}, 404)

    mocker.patch("httpx.AsyncClient.post", side_effect=mock_post)
    mocker.patch("httpx.AsyncClient.get", side_effect=mock_get)

    # 2. OpenAI SDK 모킹 (이미 sys.modules["openai"]를 통해 전역 모킹 완료됨)
    pass

    # 3. 백그라운드 Popen 서브프로세스 실행 차단 (AI To-Do 에이전트 및 Customer Feature 에이전트 호출 차단)
    class MockProcess:
        returncode = 0
        def communicate(self, *args, **kwargs):
            return "Mock Subprocess Successful Output", ""
    mocker.patch("subprocess.Popen", return_value=MockProcess())
