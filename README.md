# 🏦 POOM-BACK

> **POOM 프로젝트의 백엔드 서버** — 경제지표 예측 모델 API 및 데이터 수집 파이프라인

---

## 📌 프로젝트 개요

금융 AI 상담 서비스 **POOM**의 백엔드 레포지토리입니다.  
FastAPI 기반의 REST API 서버로, 아래 3가지 경제지표를 머신러닝으로 예측하여 제공합니다.

| 예측 지표 | 예측 방식 | 수집 주기 |
|---|---|---|
| 💰 금값 | 다음날 변화율 회귀 예측 | 일별 |
| 🏠 매매가격지수 | 다음달 변화율 회귀 예측 | 월별 |
| 📊 기준금리 | 다음달 금리 회귀 예측 | 월별 |

---

## 🗂 프로젝트 구조
POOM-BACK/

├── app/            # FastAPI 라우터, 서비스, 모델 로직

├── data/           # 수집 데이터 및 전처리 스크립트

├── sql/            # DB 스키마 및 초기화 쿼리

├── utils/          # 공통 유틸리티 함수

├── img/            # 참고 이미지

├── .github/workflows/  # GitHub Actions CI/CD

├── Dockerfile

├── requirements.txt

└── plan.md

---

## ⚙️ 기술 스택

| 분류 | 기술 |
|---|---|
| **Framework** | FastAPI, Uvicorn, Starlette |
| **Database** | MySQL (SQLAlchemy, PyMySQL), Elasticsearch |
| **인증** | JWT (python-jose), bcrypt, passlib |
| **데이터 수집** | yfinance, requests, aiohttp |
| **데이터 처리** | pandas, numpy |
| **인프라** | Docker, GitHub Actions, AWS S3 (boto3) |

---

## 📡 데이터 수집 출처

| 데이터 | API 출처 |
|---|---|
| 금값, S&P500, KOSPI200, VIX, DXY, WTI | yfinance, FRED |
| 원/달러 환율, CPI, M2, 실업률, GDP | FRED |
| 한국 기준금리, 주택담보대출 금리, CPI | 한국은행 ECOS |
| 매매가격지수, 부동산 거래량, 미분양 | 한국부동산원 |


> 우리FISA AI 엔지니어링 1팀 | POOM 프로젝트
