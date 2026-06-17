# ⚙️ POOM-BACK

> **POOM** — PB(Private Banker) 업무 지원 AI Assistant 플랫폼의 백엔드 서버

---

## 📌 개요

POOM 플랫폼의 FastAPI 기반 백엔드 레포지토리입니다.
PB의 상담 전·중·후 업무를 지원하는 REST API를 제공하며,
고객 관리, 메모 처리, 경제지표 예측 데이터 서빙을 담당합니다.

---

## 🗂 프로젝트 구조
POOM-BACK/

├── app/                # FastAPI 애플리케이션 (라우터, 서비스, 모델)

├── data/               # 경제지표 수집 데이터 및 전처리 스크립트

├── sql/                # DB 스키마 및 초기화 쿼리

├── utils/              # 공통 유틸리티

├── img/                # 참고 이미지

├── .github/workflows/  # GitHub Actions CI/CD

├── Dockerfile

├── requirements.txt

└── plan.md

---

## ⚙️ 기술 스택

| 분류 | 기술 |
|---|---|
| **Framework** | FastAPI, Uvicorn, Starlette |
| **Database** | MySQL (SQLAlchemy, PyMySQL) |
| **검색** | Elasticsearch |
| **인증** | JWT (python-jose), bcrypt, passlib |
| **데이터 수집** | yfinance, requests, aiohttp, beautifulsoup4 |
| **데이터 처리** | pandas, numpy |
| **스토리지** | AWS S3 (boto3) |
| **인프라** | Docker (멀티스테이지 빌드), GitHub Actions |

---

## 📡 경제지표 데이터 수집

`plan.md` 기반으로 아래 3가지 경제지표를 수집·예측합니다.

| 예측 지표 | 방식 | 주기 |
|---|---|---|
| 금값 | 다음날 변화율 회귀 예측 | 일별 |
| 매매가격지수 | 다음달 변화율 회귀 예측 | 월별 |
| 기준금리 | 다음달 금리 회귀 예측 | 월별 |

**수집 출처**

| 데이터 | API |
|---|---|
| 금값, S&P500, KOSPI200, VIX, DXY, WTI | yfinance, FRED |
| 원/달러 환율, CPI, M2, 실업률, GDP | FRED |
| 한국 기준금리, 주택담보대출 금리, CPI | 한국은행 ECOS |
| 매매가격지수, 거래량, 매수우위지수 | 한국부동산원 |

---

## 🚀 실행 방법

### 로컬

```bash
pip install -r requirements.txt
cp .env.example .env  # 환경변수 설정
uvicorn app.main:app --reload
```


---
## 🔗 연관 레포지토리

| 레포 | 역할 |
|---|---|
| [POOM-FRONT](https://github.com/PoomSaengPoomSa/POOM-FRONT) | React 프론트엔드 |
| [POOM-AI](https://github.com/PoomSaengPoomSa/POOM-AI) | LangGraph 멀티 에이전트 |
| [POOM-AIRFLOW](https://github.com/PoomSaengPoomSa/POOM-AIRFLOW) | MLOps 데이터 파이프라인 |
| [POOM-MLFLOW](https://github.com/PoomSaengPoomSa/POOM-MLFLOW) | 모델 실험 관리 |
| [POOM-ELK](https://github.com/PoomSaengPoomSa/POOM-ELK) | 로그 모니터링 |

---

> 우리FISA AI 엔지니어링 1팀 | POOM 프로젝트
