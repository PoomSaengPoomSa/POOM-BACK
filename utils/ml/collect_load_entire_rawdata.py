import os
import time
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ═══════════════════════════════════════════════════
#  공통 환경 및 날짜 설정
# ═══════════════════════════════════════════════════
today = datetime.today()

# 각 API 포맷에 맞춘 동적 종료일(END DATE)
END_YM = today.strftime('%Y%m')                           # YYYYMM (ECOS, R-ONE 월별)
END_Q = f"{today.year}Q{(today.month - 1) // 3 + 1}"      # YYYYQn (ECOS 분기별)
END_DASH = today.strftime('%Y-%m-%d')                     # YYYY-MM-DD (FRED 일/월별)
# yfinance는 end 속성값의 전날까지 수집하므로 하루 더해줌
END_YF = (today + timedelta(days=1)).strftime('%Y-%m-%d') 

START_YM = '201401'
START_Q = '2014Q1'
START_DASH = '2014-01-01'

# ═══════════════════════════════════════════════════
#  1. 한국은행 ECOS 및 미연준 FRED 데이터 수집
# ═══════════════════════════════════════════════════
def fetch_ecos(api_key, stat_code, item_code, period='M', start='201401', end=END_YM, col_name='value'):
    url = (
        f"https://ecos.bok.or.kr/api/StatisticSearch"
        f"/{api_key}/json/kr/1/10000"
        f"/{stat_code}/{period}/{start}/{end}/{item_code}"
    )
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        print(f"     ⚠ ECOS HTTP {resp.status_code}")
        return pd.DataFrame()

    body = resp.json()
    if 'StatisticSearch' not in body:
        error_msg = body.get('RESULT', {}).get('MESSAGE', '알 수 없는 오류')
        print(f"     ⚠ ECOS API 수집 실패 [{stat_code}-{item_code}]: {error_msg}")
        return pd.DataFrame()

    rows = body['StatisticSearch']['row']
    df = pd.DataFrame(rows)[['TIME', 'DATA_VALUE']].copy()
    
    if period == 'M':
        df['date'] = df['TIME'].str[:4] + '-' + df['TIME'].str[4:6]
    elif period == 'D':
        df['date'] = df['TIME'].str[:4] + '-' + df['TIME'].str[4:6] + '-' + df['TIME'].str[6:8]
    elif period == 'Q':
        quarter_to_month = {'1': '01', '2': '04', '3': '07', '4': '10'}
        df['date'] = df['TIME'].str[:4] + '-' + df['TIME'].str[5].map(quarter_to_month)
        
    df[col_name] = pd.to_numeric(df['DATA_VALUE'], errors='coerce')
    return df[['date', col_name]]

def fetch_fred(api_key, series_id, col_name='value', start=START_DASH, end=END_DASH, frequency='m'):
    params = {
        'series_id': series_id,
        'api_key': api_key,
        'file_type': 'json',
        'observation_start': start,
        'observation_end': end,
        'frequency': frequency,
        'aggregation_method': 'avg' if frequency == 'm' else 'eop',
    }
    resp = requests.get("https://api.stlouisfed.org/fred/series/observations", params=params, timeout=30)
    if resp.status_code != 200:
        print(f"     ⚠ FRED HTTP {resp.status_code}")
        return pd.DataFrame()

    body = resp.json()
    if 'observations' not in body:
        return pd.DataFrame()

    df = pd.DataFrame(body['observations'])[['date', 'value']].copy()
    if frequency == 'm':
        df['date'] = df['date'].str[:7]
        
    df[col_name] = pd.to_numeric(df['value'], errors='coerce')
    df = df.dropna(subset=[col_name])
    return df[['date', col_name]]

# ═══════════════════════════════════════════════════
#  2. R-ONE 부동산 데이터 수집
# ═══════════════════════════════════════════════════
def get_period_list(start, end):
    periods = []
    sy, sm = int(start[:4]), int(start[4:])
    ey, em = int(end[:4]),   int(end[4:])
    y, m = sy, sm
    while (y, m) <= (ey, em):
        periods.append(f"{y}{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return periods

def fetch_reb(api_key, stat_code, item_code, col_name, region_code=None, start=START_YM, end=END_YM):
    print(f"  📥 {col_name} 수집 중...")
    periods = get_period_list(start, end)
    rows_all = []

    for period in periods:
        params = {
            'KEY':              api_key,
            'Type':             'json',
            'pIndex':           '1',
            'pSize':            '1000',
            'STATBL_ID':        stat_code,
            'DTACYCLE_CD':      'MM',
            'WRTTIME_IDTFR_ID': period,
            'ITEM_ID':          item_code,
        }
        if region_code:
            params['REGION_CD'] = region_code

        try:
            resp = requests.get('https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do', params=params, timeout=30)
            body = resp.json()
            if 'SttsApiTblData' in body:
                rows = body['SttsApiTblData'][1].get('row', [])
                if rows:
                    rows_all.extend(rows)
        except Exception as e:
            print(f"     ❌ {period} 오류: {e}")
        time.sleep(0.1)

    if not rows_all:
        print(f"     ⚠️  데이터 없음")
        return pd.DataFrame()

    df = pd.DataFrame(rows_all)
    if 'CLS_ID' in df.columns:
        df = df[df['CLS_ID'] == 500001].copy()
    if 'ITM_ID' in df.columns:
        df = df[df['ITM_ID'] == 100001].copy()

    df = df[['WRTTIME_IDTFR_ID', 'DTA_VAL']].copy()
    df['date'] = df['WRTTIME_IDTFR_ID'].str[:4] + '-' + df['WRTTIME_IDTFR_ID'].str[4:6]
    df[col_name] = pd.to_numeric(df['DTA_VAL'], errors='coerce')

    print(f"     ✅ {len(df)}건 수집 완료")
    return df[['date', col_name]]

# ═══════════════════════════════════════════════════
#  3. yfinance (주가, 금, 달러) 데이터 수집
# ═══════════════════════════════════════════════════
def download_yf_all(tickers: dict, start: str, end: str) -> pd.DataFrame:
    frames = []
    for col_name, ticker in tickers.items():
        print(f"  📥 {ticker:12s} → {col_name}")
        try:
            df = yf.download(ticker, start=start, end=end, interval="1d", auto_adjust=True, progress=False)
            if df.empty:
                print(f"     ⚠️  데이터 없음: {ticker}")
                continue

            if isinstance(df.columns, pd.MultiIndex):
                close = df["Close"].iloc[:, 0]
            else:
                close = df["Close"]

            close.name = col_name
            frames.append(close)
        except Exception as e:
            print(f"     ❌ 오류 ({ticker}): {e}")

    if not frames:
        return pd.DataFrame()

    result = pd.concat(frames, axis=1)
    result.index.name = "date"
    return result

def make_yf_daily(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    d = df.copy()
    if d.index.tz is not None:
        d.index = d.index.tz_localize(None)
    else:
        d.index = pd.to_datetime(d.index)

    d = d.reset_index()
    d["date"] = d["date"].dt.strftime("%Y-%m-%d")
    cols = ["date", "gold", "sp500", "dxy", "kospi200"]
    return d[[c for c in cols if c in d.columns]]

def make_yf_monthly(daily: pd.DataFrame) -> pd.DataFrame:
    if daily.empty: return daily
    m = daily.copy()
    m["date"] = pd.to_datetime(m["date"])
    m = m.set_index("date")

    numeric_cols = m.select_dtypes(include="number").columns.tolist()
    monthly = m[numeric_cols].resample("ME").mean()

    monthly = monthly.reset_index()
    monthly["date"] = monthly["date"].dt.strftime("%Y-%m")
    cols = ["date", "gold", "sp500", "dxy", "kospi200"]
    return monthly[[c for c in cols if c in monthly.columns]]

# ═══════════════════════════════════════════════════
#  데이터 병합 및 저장 헬퍼 함수
# ═══════════════════════════════════════════════════
def merge_and_save(dfs, file_path, desc):
    if not dfs:
        print(f"⚠ {desc} 수집된 데이터가 없어 파일을 생성하지 않습니다.")
        return
        
    merged = dfs[0]
    for df in dfs[1:]:
        merged = pd.merge(merged, df, on='date', how='outer')
        
    merged = merged.sort_values('date').reset_index(drop=True)
    merged.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"✅ {desc} 저장 완료: {file_path} ({len(merged)}건)")

# ═══════════════════════════════════════════════════
#  메인 실행: 데이터 수집
# ═══════════════════════════════════════════════════
def collect_all():
    # 3단계 위로 수정 (POOM-BACK 루트)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    load_dotenv(dotenv_path=os.path.join(base_dir, '.env'))

    ecos_key = os.getenv('ECOS_API_KEY')
    fred_key = os.getenv('FRED_API_KEY')
    reb_key = os.getenv('REB_API_KEY')

    if not all([ecos_key, fred_key, reb_key]):
        print("❌ .env 파일에서 하나 이상의 API_KEY(ECOS, FRED, REB)를 찾을 수 없습니다.")
        return

    save_dir = os.path.join(base_dir, 'data', 'ml')
    os.makedirs(save_dir, exist_ok=True)

    print("=" * 60)
    print(f"  통합 원시 데이터 수집 파이프라인 (종료일 기준: {END_DASH})")
    print("=" * 60)

    # ─────────────────────────────────────────
    # 1. ECOS 데이터
    # ─────────────────────────────────────────
    print("\n[1/4] 🇰🇷 한국은행(ECOS) 데이터 수집 시작...")
    ecos_m_dfs, ecos_d_dfs = [], []
    ecos_indicators = [
        ('722Y001', '0101000', 'kr_base_rate', '한국 기준금리', 'M'),
        ('901Y009', '0', 'kr_cpi', '한국 CPI(소비자물가지수)', 'M'),
        ('121Y006', 'BECBLA0302', 'kr_mortgage_rate', '주택담보대출금리', 'M'),
        ('161Y005', 'BBHS00', 'kr_m2', '한국 M2 통화량', 'M'),
        ('200Y102', '10111', 'kr_gdp', '한국 GDP', 'Q')
    ]
    for stat, item, col, desc, prd in ecos_indicators:
        print(f"  📊 {desc} ({'월별' if prd == 'M' else '분기별'})...")
        req_start = START_YM if prd == 'M' else START_Q
        req_end = END_YM if prd == 'M' else END_Q
        df = fetch_ecos(ecos_key, stat, item, period=prd, start=req_start, end=req_end, col_name=col)
        if not df.empty: ecos_m_dfs.append(df)
        time.sleep(0.3)

    merge_and_save(ecos_m_dfs, os.path.join(save_dir, 'ecos_m.csv'), "ECOS 월별 데이터")

    # ─────────────────────────────────────────
    # 2. FRED 데이터
    # ─────────────────────────────────────────
    print("\n[2/4] 🌐 FRED 데이터 수집 시작...")
    fred_m_dfs, fred_d_dfs = [], []
    fred_m_indicators = [
        ('DEXKOUS', 'kr_usd_exchange', '원/달러 환율'),
        ('VIXCLS', 'vix', 'VIX 변동성 지수'),
        ('DCOILWTICO', 'wti_oil', 'WTI 유가'),
        ('FEDFUNDS', 'us_fed_rate', '미국 연방기금금리'),
        ('LRHUTTTTKRM156S', 'kr_unemployment', '한국 실업률(OECD)'),
    ]
    fred_d_indicators = [
        ('DEXKOUS', 'kr_usd_exchange', '원/달러 환율'),
        ('VIXCLS', 'vix', 'VIX 변동성 지수'),
        ('DTWEXBGS', 'dxy_proxy', '달러 인덱스(FRED Broad)'),
        ('DCOILWTICO', 'wti_oil', 'WTI 유가')
    ]
    for series_id, col, desc in fred_m_indicators:
        print(f"  📊 {desc} (월별)...")
        df = fetch_fred(fred_key, series_id, col_name=col, start=START_DASH, end=END_DASH, frequency='m')
        if not df.empty: fred_m_dfs.append(df)
        time.sleep(0.3)

    for series_id, col, desc in fred_d_indicators:
        print(f"  📊 {desc} (일별)...")
        df = fetch_fred(fred_key, series_id, col_name=col, start=START_DASH, end=END_DASH, frequency='d')
        if not df.empty: fred_d_dfs.append(df)
        time.sleep(0.3)

    merge_and_save(fred_m_dfs, os.path.join(save_dir, 'fred_m.csv'), "FRED 월별 데이터")
    merge_and_save(fred_d_dfs, os.path.join(save_dir, 'fred_d.csv'), "FRED 일별 데이터")

    # ─────────────────────────────────────────
    # 3. R-ONE 부동산 데이터
    # ─────────────────────────────────────────
    print("\n[3/4] 🏢 R-ONE 부동산 데이터 수집 시작...")
    reb_indicators = [
        ('A_2024_00045', '100001', 'house_price_idx', None),
        ('A_2024_00554', '100001', 'apt_trade_count', '500001'),
        ('A_2024_00076', '100001', 'buyer_dominance', None),
    ]
    reb_dfs = []
    for stat_code, item_code, col_name, region_code in reb_indicators:
        df = fetch_reb(reb_key, stat_code, item_code, col_name, region_code, start=START_YM, end=END_YM)
        if not df.empty: reb_dfs.append(df)

    if reb_dfs:
        reb_merged = reb_dfs[0]
        for df in reb_dfs[1:]:
            reb_merged = pd.merge(reb_merged, df, on='date', how='outer')
        reb_merged = reb_merged.sort_values('date').reset_index(drop=True)
        
        reb_cols = ['date', 'house_price_idx', 'apt_trade_count', 'buyer_dominance']
        reb_merged = reb_merged[[c for c in reb_cols if c in reb_merged.columns]]
        
        reb_path = os.path.join(save_dir, 'realestate_m.csv')
        reb_merged.to_csv(reb_path, index=False, encoding='utf-8-sig')
        print(f"✅ R-ONE 부동산 월별 데이터 저장 완료: {reb_path} ({len(reb_merged)}건)")

    # ─────────────────────────────────────────
    # 4. yfinance 데이터
    # ─────────────────────────────────────────
    print("\n[4/4] 📈 yfinance (금융/증시) 데이터 수집 시작...")
    tickers = {"gold": "GC=F", "sp500": "^GSPC", "dxy": "DX-Y.NYB", "kospi200": "^KS200"}
    yf_raw = download_yf_all(tickers, START_DASH, END_YF)
    
    if not yf_raw.empty:
        yf_daily = make_yf_daily(yf_raw)
        yf_daily_path = os.path.join(save_dir, "yfinance_d.csv")
        yf_daily.to_csv(yf_daily_path, index=False, encoding="utf-8-sig")
        print(f"✅ yfinance 일별 데이터 저장 완료: {yf_daily_path} ({len(yf_daily)}건)")

        yf_monthly = make_yf_monthly(yf_daily)
        yf_monthly_path = os.path.join(save_dir, "yfinance_m.csv")
        yf_monthly.to_csv(yf_monthly_path, index=False, encoding="utf-8-sig")
        print(f"✅ yfinance 월별 데이터 저장 완료: {yf_monthly_path} ({len(yf_monthly)}건)")

    print("\n🎉 모든 데이터의 수집 및 통합 병합 처리가 완료되었습니다!")


def concat_rawdata():
    # 3단계 위로 수정 (POOM-BACK 루트)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(current_dir))
    data_dir = os.path.join(base_dir, 'data', 'ml')
    
    print(f"📂 데이터 디렉토리 확인: {data_dir}")

    # 대상 파일 리스트 정의
    monthly_files = [f for f in os.listdir(data_dir) if f.endswith('_m.csv') and not f.startswith('rawdata')]
    daily_files = [f for f in os.listdir(data_dir) if f.endswith('_d.csv') and not f.startswith('rawdata')]

    def merge_logic(file_list, freq, output_filename, monthly_df_for_daily=None):
        if not file_list:
            print(f"⚠ {output_filename} 생성을 위한 대상 파일이 없습니다.")
            return None

        dfs = []
        all_dates = []

        # 데이터 로드 및 날짜 수집
        for f in file_list:
            path = os.path.join(data_dir, f)
            df = pd.read_csv(path)
            df['date'] = pd.to_datetime(df['date'])
            dfs.append(df)
            all_dates.extend(df['date'].tolist())

        # 전체 기간 마스터 생성
        start_date = min(all_dates)
        end_date = max(all_dates)
        
        if freq == 'M': 
            master_date = pd.date_range(start=start_date, end=end_date, freq='MS')
            date_format = '%Y-%m'
        else: 
            master_date = pd.date_range(start=start_date, end=end_date, freq='D')
            date_format = '%Y-%m-%d'

        master_df = pd.DataFrame({'date': master_date})

        # 순차 병합
        for df in dfs:
            master_df = pd.merge(master_df, df, on='date', how='left')

        # 🌟 [요청 사항] 월별 데이터 처리 시, 분기별 데이터(GDP)를 해당 분기의 모든 월에 채움 (ffill) 유지!
        if freq == 'M' and 'kr_gdp' in master_df.columns:
            # 1월(Q1), 4월(Q2), 7월(Q3), 10월(Q4)의 데이터를 이어지는 2달에 복사
            master_df['kr_gdp'] = master_df['kr_gdp'].ffill(limit=2)

        # [기존 로직] 일별 데이터 처리 시, CPI 등 월별 지표를 일별로 매핑
        if freq == 'D' and monthly_df_for_daily is not None:
            # 일별 날짜에서 'YYYY-MM' 형태의 병합 키 추출
            master_df['year_month'] = master_df['date'].dt.strftime('%Y-%m')
            
            # 월별 데이터에서 필요한 컬럼(kr_cpi)만 가져옴
            if 'kr_cpi' in monthly_df_for_daily.columns:
                monthly_subset = monthly_df_for_daily[['date', 'kr_cpi']].copy()
                
                monthly_subset.rename(columns={'date': 'year_month'}, inplace=True)
                
                # 일별 마스터 데이터에 병합
                master_df = pd.merge(master_df, monthly_subset, on='year_month', how='left')
            
            # 병합 후 임시 키 삭제
            master_df.drop(columns=['year_month'], inplace=True)

        # 날짜 포맷팅 변환 (저장용)
        master_df['date'] = master_df['date'].dt.strftime(date_format)
        
        # 저장
        output_path = os.path.join(data_dir, output_filename)
        master_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✅ 통합 완료: {output_filename} ({len(master_df)}건, 기간: {master_df['date'].iloc[0]} ~ {master_df['date'].iloc[-1]})")
        
        return master_df

    # 2. 월별 데이터 통합 우선 수행 (결과물 Dataframe 반환)
    print("\n[진행] 월별 데이터 통합 중...")
    master_m_df = merge_logic(monthly_files, 'M', 'rawdata_m.csv')

    # 3. 일별 데이터 통합 수행 (월별 Dataframe을 인자로 전달하여 CPI 병합)
    print("\n[진행] 일별 데이터 통합 중...")
    merge_logic(daily_files, 'D', 'rawdata_d.csv', monthly_df_for_daily=master_m_df)


def load_and_split_data():
    # 3단계 위로 수정 (POOM-BACK 루트)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(current_dir))
    data_dir = os.path.join(base_dir, 'data', 'ml')
    load_dotenv(dotenv_path=os.path.join(base_dir, '.env'))

    # 파일 읽기
    path_m = os.path.join(data_dir, 'rawdata_m.csv')
    path_d = os.path.join(data_dir, 'rawdata_d.csv')

    if not os.path.exists(path_m) or not os.path.exists(path_d):
        print("❌ 통합 데이터 파일(rawdata_m.csv 또는 rawdata_d.csv)이 존재하지 않습니다.")
        return

    df_m = pd.read_csv(path_m)
    df_d = pd.read_csv(path_d)

    print("📊 데이터 로드 완료. 목적별 분리 시작...")

    # 2. [금값 데이터] - 일별 (Gold) 파생변수 제거 및 이름 변경
    gold_cols = [
        'date', 'gold', 'kr_usd_exchange', 
        'wti_oil', 'dxy_proxy', 'vix', 'kospi200', 'sp500','kr_cpi'
    ]
    gold_data = df_d[[c for c in gold_cols if c in df_d.columns]].copy()
    gold_data.rename(columns={'date': 'loaded_date'}, inplace=True)
    gold_data.to_csv(os.path.join(data_dir, 'gold_data.csv'), index=False, encoding='utf-8-sig')

    # 3. [매매가격지수 데이터] - 월별 (Real Estate) 파생변수 제거 및 이름 변경
    re_cols = [
        'date', 'house_price_idx', 'kr_cpi', 
        'kr_unemployment', 'kr_base_rate', 'kr_mortgage_rate', 
        'kospi200', 'apt_trade_count', 'kr_m2', 'buyer_dominance'
    ]
    realestate_data = df_m[[c for c in re_cols if c in df_m.columns]].copy()
    realestate_data.rename(columns={'date': 'loaded_date'}, inplace=True)
    realestate_data.to_csv(os.path.join(data_dir, 'realestate_data.csv'), index=False, encoding='utf-8-sig')

    # 4. [기준금리 데이터] - 월별 (Base Rate) 파생변수 제거 및 이름 변경
    br_cols = [
        'date', 'kr_base_rate', 'kr_cpi', 'kr_unemployment', 
        'kr_usd_exchange', 'kr_gdp', 'kr_m2', 'us_fed_rate', 'vix', 'wti_oil'
    ]
    baserate_data = df_m[[c for c in br_cols if c in df_m.columns]].copy()
    baserate_data.rename(columns={'date': 'loaded_date'}, inplace=True)
    baserate_data.to_csv(os.path.join(data_dir, 'baserate_data.csv'), index=False, encoding='utf-8-sig')

    print(f"✅ CSV 파일 저장 완료: data/ml/ 내 gold, realestate, baserate_data.csv")

    # 5. MySQL 데이터베이스 적재 (새로운 테이블명 적용)
    upload_to_mysql(
        {
            'ml_gold_raw': gold_data, 
            'ml_realestate_raw': realestate_data, 
            'ml_baserate_raw': baserate_data
        }
    )

def upload_to_mysql(data_dict):
    # .env에서 DB 정보 로드
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_NAME')

    if not all([db_user, db_password, db_host, db_name]):
        print("⚠ DB 연결 정보가 부족하여 데이터베이스 적재를 건너뜁니다.")
        return

    try:
        # SQLAlchemy 엔진 생성 (pymysql 드라이버 사용)
        engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4")

        with engine.begin() as conn:
            for table_name, df in data_dict.items():
                
                # 🌟 [수정 포인트] DB에 넣기 직전, 불완전한 문자열('YYYY-MM')을 완벽한 날짜 객체로 변환
                # '2014-01' -> '2014-01-01 00:00:00' 으로 자동 치환됩니다.
                df['loaded_date'] = pd.to_datetime(df['loaded_date'])
                
                # 1. 기존 테이블이 있다면 삭제
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                
                # 2. 각 테이블 스키마에 맞는 CREATE TABLE DDL 실행
                if table_name == 'ml_gold_raw':
                    create_table_query = f"""
                    CREATE TABLE {table_name} (
                        gr_id INT AUTO_INCREMENT,
                        loaded_date DATETIME NOT NULL,
                        gold DECIMAL(15,2),
                        kr_usd_exchange DECIMAL(15,2),
                        wti_oil DECIMAL(15,2),
                        dxy_proxy DECIMAL(15,2),
                        vix DECIMAL(15,2),
                        kospi200 DECIMAL(15,2),
                        sp500 DECIMAL(15,2),
                        kr_cpi DECIMAL(15,2),
                        PRIMARY KEY (gr_id, loaded_date)
                    )
                    """
                elif table_name == 'ml_baserate_raw':
                    create_table_query = f"""
                    CREATE TABLE {table_name} (
                        br_id INT AUTO_INCREMENT,
                        loaded_date DATETIME NOT NULL,
                        kr_base_rate DECIMAL(15,2),
                        kr_cpi DECIMAL(15,2),
                        kr_unemployment DECIMAL(15,2),
                        kr_usd_exchange DECIMAL(15,2),
                        kr_gdp DECIMAL(15,2),
                        kr_m2 DECIMAL(15,2),
                        us_fed_rate DECIMAL(15,2),
                        vix DECIMAL(15,2),
                        wti_oil DECIMAL(15,2),
                        PRIMARY KEY (br_id, loaded_date)
                    )
                    """
                elif table_name == 'ml_realestate_raw':
                    create_table_query = f"""
                    CREATE TABLE {table_name} (
                        rr_id INT AUTO_INCREMENT,
                        loaded_date DATETIME NOT NULL,
                        house_price_idx DECIMAL(15,2),
                        kr_cpi DECIMAL(15,2),
                        kr_unemployment DECIMAL(15,2),
                        kr_base_rate DECIMAL(15,2),
                        kr_mortgage_rate DECIMAL(15,2),
                        kospi200 DECIMAL(15,2),
                        apt_trade_count DECIMAL(15,2),
                        kr_m2 DECIMAL(15,2),
                        buyer_dominance DECIMAL(15,2),
                        PRIMARY KEY (rr_id, loaded_date)
                    )
                    """
                else:
                    continue # 알 수 없는 테이블명 방어 코드

                conn.execute(text(create_table_query))
                
                # 3. 데이터프레임을 테이블에 삽입 (if_exists='append')
                df.to_sql(name=table_name, con=conn, if_exists='append', index=False)
                
                print(f"🚀 DB 적재 완료: {table_name} ({len(df)} rows)")

        print("\n🎉 모든 데이터 분석 준비 및 DB 적재가 완료되었습니다!")

    except Exception as e:
        print(f"❌ DB 적재 중 오류 발생: {e}")

if __name__ == '__main__':
    #collect_all()
    #concat_rawdata()
    load_and_split_data()