from typing import Optional, List
from sqlalchemy.orm import Session
import httpx
import logging
from datetime import datetime, timedelta, date
from app.models.trend import (
    EconomicIndicatorHistory,
    EconomicIndicatorPrediction,
    EconomicIndicatorContribution,
    TrendLlmReport,
)
from app.schemas.trend import (
    TrendDashboardResponse,
    NewsListResponse,
    NewsDetailResponse,
    IndicatorLatestResponse,
    IndicatorHistoryResponse,
    IndicatorPredictionResponse,
    IndicatorContributionResponse,
    ReportCreateRequest,
    ReportCreateResponse,
    ReportStatusResponse,
    ReportLatestResponse,
    IndicatorBulkRequest,
    IndicatorBulkResponse,
    MessageResponse,
)

logger = logging.getLogger(__name__)
from app.config import get_settings
settings = get_settings()
ES_HOST = settings.ES_HOST

import os
import time

AI_NEWS_CACHE = {
    "economy": {"summary": "", "updated_at": 0.0},
    "politics": {"summary": "", "updated_at": 0.0},
    "itScience": {"summary": "", "updated_at": 0.0}
}
CACHE_EXPIRE_SECONDS = 3600  # 1 hour

async def fetch_ai_news_summary(category: str, articles: list) -> str:
    """최신 기사 제목들을 바탕으로 OpenAI를 사용하여 2줄 요약 생성"""
    if not articles:
        return "- 최신 기사가 아직 수집되지 않았습니다."
        
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY is not configured. Returning fallback msg.")
        return "- OpenAI API 키가 설정되지 않아 실시간 AI 요약을 생성할 수 없습니다."
        
    titles_str = "\n".join([f"- {a['title']}" for a in articles])
    
    prompt = f"""
다음은 최신 {category} 뉴스 기사들의 제목 목록입니다:
{titles_str}

이 기사들의 주요 맥락과 트렌드를 요약하여 핵심적인 '2줄 브리핑 요약'을 작성해주세요.
반드시 아래 규칙을 지켜주세요:
1. 글머리 기호(-)를 사용하여 정확히 2개의 요약 문장으로 마크다운 리스트 형태로만 출력하세요.
2. 각 요약문은 전문적이고 깔끔한 한국어 종결어미(~함, ~임 또는 ~했습니다 등 격식있게)로 끝맺으세요.
3. 단순 기사의 나열이 아닌, 전체 기사를 아우르는 핵심 요약 브리핑으로 작성하세요.
4. 추가적인 멘트나 부가 설명 없이 오직 2줄의 마크다운 리스트 결과만 리턴하세요.
"""
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a professional news analyst. You must provide exactly 2-line summarized briefing in markdown bullet format based on user inputs."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 300
                }
            )
            if resp.status_code == 200:
                result = resp.json()
                summary = result["choices"][0]["message"]["content"].strip()
                return summary
            else:
                logger.warning(f"Failed to get AI summary from OpenAI: {resp.status_code} - {resp.text}")
                return "- 실시간 AI 요약 브리핑을 생성하는 도중 오류가 발생했습니다."
    except Exception as e:
        logger.warning(f"Exception while generating AI news summary: {e}")
        return "- 실시간 AI 요약 브리핑을 준비 중입니다."


async def get_trend_dashboard(current_user, db: Session) -> TrendDashboardResponse:
    """트렌드 대시보드 조회 (Elasticsearch 우선조회 후 MySQL 폴백)"""
    economy_news = []
    politics_news = []
    it_news = []
    
    # 1. Elasticsearch에서 기사 조회 시도 (카테고리별 최신 5건)
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp_econ = await client.post(
                f"{ES_HOST}/sbs_news/_search",
                json={
                    "query": {"term": {"category": "경제"}},
                    "sort": [{"published_at": {"order": "desc"}}],
                    "size": 5
                }
            )
            resp_pol = await client.post(
                f"{ES_HOST}/sbs_news/_search",
                json={
                    "query": {"term": {"category": "정치"}},
                    "sort": [{"published_at": {"order": "desc"}}],
                    "size": 5
                }
            )
            resp_mug = await client.post(
                f"{ES_HOST}/sbs_news/_search",
                json={
                    "query": {"term": {"category": "머그"}},
                    "sort": [{"published_at": {"order": "desc"}}],
                    "size": 5
                }
            )
            
            if resp_econ.status_code == 200:
                economy_news = [
                    {
                        "id": hit["_id"],
                        "title": hit["_source"].get("title", ""),
                        "publishedAt": (hit["_source"].get("published_at", "")[:10] if hit["_source"].get("published_at", "") else "")
                    }
                    for hit in resp_econ.json().get("hits", {}).get("hits", [])
                ]
            if resp_pol.status_code == 200:
                politics_news = [
                    {
                        "id": hit["_id"],
                        "title": hit["_source"].get("title", ""),
                        "publishedAt": (hit["_source"].get("published_at", "")[:10] if hit["_source"].get("published_at", "") else "")
                    }
                    for hit in resp_pol.json().get("hits", {}).get("hits", [])
                ]
            if resp_mug.status_code == 200:
                it_news = [
                    {
                        "id": hit["_id"],
                        "title": hit["_source"].get("title", ""),
                        "publishedAt": (hit["_source"].get("published_at", "")[:10] if hit["_source"].get("published_at", "") else "")
                    }
                    for hit in resp_mug.json().get("hits", {}).get("hits", [])
                ]
    except Exception as e:
        logger.warning(f"Failed to fetch dashboard news from Elasticsearch: {e}.")

    news_data = {
        "economy": economy_news,
        "politics": politics_news,
        "itScience": it_news,
        "it": it_news,
    }

    # 2. 금값 및 부동산 지표 동적 조회
    from sqlalchemy import text
    
    # A. 금값 데이터 쿼리
    gold_yesterday, gold_today = None, None
    try:
        g_hist_query = text("SELECT value FROM economic_indicator_history WHERE type = 'gold' ORDER BY recorded_at DESC LIMIT 2")
        g_res = db.execute(g_hist_query).fetchall()
        if len(g_res) >= 2:
            gold_today = float(g_res[0][0])
            gold_yesterday = float(g_res[1][0])
    except Exception as e:
        logger.warning(f"Failed to fetch gold history: {e}")
        
    gold_tomorrow = None
    prob_rise_val, prob_fall_val = None, None
    pred_text_gold = None
    try:
        g_pred_query = text("SELECT prob_rise, prob_fall FROM gold_predictions ORDER BY created_at DESC LIMIT 1")
        g_pred_res = db.execute(g_pred_query).fetchone()
        if g_pred_res:
            raw_rise = float(g_pred_res[0])
            raw_fall = float(g_pred_res[1])
            prob_rise_val = round(raw_rise * 100) if raw_rise < 1.0 else round(raw_rise)
            prob_fall_val = round(raw_fall * 100) if raw_fall < 1.0 else round(raw_fall)
            # 100% 보정
            total_prob = prob_rise_val + prob_fall_val
            if total_prob > 0:
                prob_rise_val = round((prob_rise_val / total_prob) * 100)
                prob_fall_val = 100 - prob_rise_val
                
            if prob_rise_val > prob_fall_val:
                pred_text_gold = "상승 가능성 높음"
            elif prob_rise_val < prob_fall_val:
                pred_text_gold = "하락 가능성 높음"
            else:
                pred_text_gold = "상승/하락 가능성 동률"
                
            if gold_today is not None:
                gold_tomorrow = round(gold_today * (1 + (prob_rise_val - prob_fall_val)/1000), 2)
    except Exception as e:
        logger.warning(f"Failed to fetch gold predictions: {e}")
        
    gold_change_rate = None
    gold_dir = "flat"
    if gold_today is not None and gold_yesterday is not None:
        gold_change_rate = round(((gold_today - gold_yesterday) / gold_yesterday) * 100, 1) if gold_yesterday != 0 else 0.0
        gold_dir = "up" if gold_today > gold_yesterday else "down" if gold_today < gold_yesterday else "flat"
    
    gold_data = {
        "yesterday": gold_yesterday,
        "today": gold_today,
        "tomorrow": gold_tomorrow,
        "changeRate": gold_change_rate,
        "changeDirection": gold_dir,
        "probRise": prob_rise_val,
        "probFall": prob_fall_val,
        "predictionText": pred_text_gold
    }

    # B. 부동산 데이터 쿼리
    re_yesterday, re_today = None, None
    try:
        re_hist_query = text("SELECT house_price_idx FROM ml_realestate_preprocessed ORDER BY date_ym DESC LIMIT 2")
        re_res = db.execute(re_hist_query).fetchall()
        if len(re_res) >= 2:
            re_today = float(re_res[0][0])
            re_yesterday = float(re_res[1][0])
    except Exception as e:
        logger.warning(f"Failed to fetch realestate history: {e}")
        
    re_tomorrow = None
    re_change_rate = None
    re_dir = "flat"
    try:
        re_pred_query = text("SELECT predicted_value, predicted_index FROM realestate_predictions ORDER BY created_at DESC LIMIT 1")
        re_pred_res = db.execute(re_pred_query).fetchone()
        if re_pred_res:
            pred_rate = float(re_pred_res[0])
            pred_index = re_pred_res[1]
            
            # 변화율은 예측된 변화율 자체를 그대로 사용
            re_change_rate = round(pred_rate, 2)
            re_dir = "up" if pred_rate > 0 else "down" if pred_rate < 0 else "flat"
            
            # predicted_index 컬럼이 DB에 있으면 이를 그대로 쓰고, 없으면 실시간 역산으로 폴백
            if pred_index is not None:
                re_tomorrow = round(float(pred_index), 2)
            elif re_today is not None:
                re_tomorrow = round(re_today * (1 + pred_rate / 100), 2)
    except Exception as e:
        logger.warning(f"Failed to fetch realestate predictions: {e}")
    
    re_data = {
        "yesterday": re_yesterday,
        "today": re_today,
        "tomorrow": re_tomorrow,
        "changeRate": re_change_rate,
        "changeDirection": re_dir
    }

    # C. 기준금리 데이터 쿼리
    br_last_month, br_this_month = None, None
    try:
        br_hist_query = text("SELECT value FROM economic_indicator_history WHERE type = 'base_rate' ORDER BY recorded_at DESC LIMIT 2")
        br_res = db.execute(br_hist_query).fetchall()
        if len(br_res) >= 2:
            br_this_month = float(br_res[0][0])
            br_last_month = float(br_res[1][0])
    except Exception as e:
        logger.warning(f"Failed to fetch baserate history: {e}")
        
    br_next_month = None
    prob_cut_val, prob_freeze_val, prob_hike_val = None, None, None
    pred_text_br = None
    try:
        br_pred_query = text("SELECT prob_cut, prob_freeze, prob_hike FROM baserate_predictions ORDER BY created_at DESC LIMIT 1")
        br_pred_res = db.execute(br_pred_query).fetchone()
        if br_pred_res:
            raw_cut = float(br_pred_res[0])
            raw_freeze = float(br_pred_res[1])
            raw_hike = float(br_pred_res[2])
            prob_cut_val = round(raw_cut * 100) if raw_cut < 1.0 else round(raw_cut)
            prob_freeze_val = round(raw_freeze * 100) if raw_freeze < 1.0 else round(raw_freeze)
            prob_hike_val = round(raw_hike * 100) if raw_hike < 1.0 else round(raw_hike)
            
            # 100% 보정
            total_prob = prob_cut_val + prob_freeze_val + prob_hike_val
            if total_prob > 0:
                prob_cut_val = round((prob_cut_val / total_prob) * 100)
                prob_freeze_val = round((prob_freeze_val / total_prob) * 100)
                prob_hike_val = 100 - prob_cut_val - prob_freeze_val
                
            max_prob = max(prob_cut_val, prob_freeze_val, prob_hike_val)
            if max_prob == prob_cut_val:
                pred_text_br = "인하 가능성 높음"
                if br_this_month is not None:
                    br_next_month = br_this_month - 0.25
            elif max_prob == prob_freeze_val:
                pred_text_br = "동결 가능성 높음"
                if br_this_month is not None:
                    br_next_month = br_this_month
            else:
                pred_text_br = "인상 가능성 높음"
                if br_this_month is not None:
                    br_next_month = br_this_month + 0.25
    except Exception as e:
        logger.warning(f"Failed to fetch baserate predictions: {e}")
        
    br_change_rate = None
    br_dir = "flat"
    if br_this_month is not None and br_last_month is not None:
        br_change_rate = round(br_this_month - br_last_month, 2)
        br_dir = "up" if br_this_month > br_last_month else "down" if br_this_month < br_last_month else "flat"
    
    br_data = {
        "lastMonth": br_last_month,
        "thisMonth": br_this_month,
        "nextMonth": br_next_month,
        "changeRate": br_change_rate,
        "changeDirection": br_dir,
        "probCut": prob_cut_val,
        "probFreeze": prob_freeze_val,
        "probHike": prob_hike_val,
        "predictionText": pred_text_br
    }

    # D. 실시간 트렌드 지표 조회 (각 지표별 최신 2개의 non-null 값 기반)
    realtime_trends = []
    try:
        # 1. CPI (소비자물가지수)
        cpi_query = text("SELECT kr_cpi, loaded_date FROM ml_gold_raw WHERE kr_cpi IS NOT NULL ORDER BY loaded_date DESC LIMIT 2")
        cpi_res = db.execute(cpi_query).fetchall()
        if len(cpi_res) >= 2:
            cpi_today = float(cpi_res[0][0])
            cpi_yesterday = float(cpi_res[1][0])
            cpi_diff = cpi_today - cpi_yesterday
            cpi_rate = (cpi_diff / cpi_yesterday) * 100 if cpi_yesterday != 0 else 0.0
            realtime_trends.append({
                "name": "CPI",
                "value": f"{cpi_today:.1f}" if cpi_today < 1000 else f"{cpi_today:,.1f}",
                "unit": "",
                "rate": f"{cpi_rate:+.2f}%" if cpi_rate != 0 else "0.00%",
                "direction": "up" if cpi_rate > 0 else "down" if cpi_rate < 0 else "flat"
            })

        # 2. 코스피 200 (KOSPI 200)
        kospi_query = text("SELECT kospi200, loaded_date FROM ml_gold_raw WHERE kospi200 IS NOT NULL ORDER BY loaded_date DESC LIMIT 2")
        kospi_res = db.execute(kospi_query).fetchall()
        if len(kospi_res) >= 2:
            kospi_today = float(kospi_res[0][0])
            kospi_yesterday = float(kospi_res[1][0])
            kospi_diff = kospi_today - kospi_yesterday
            kospi_rate = (kospi_diff / kospi_yesterday) * 100 if kospi_yesterday != 0 else 0.0
            realtime_trends.append({
                "name": "코스피 200",
                "value": f"{kospi_today:,.0f}" if kospi_today >= 1000 else f"{kospi_today:.2f}",
                "unit": "pt",
                "rate": f"{kospi_rate:+.2f}%" if kospi_rate != 0 else "0.00%",
                "direction": "up" if kospi_rate > 0 else "down" if kospi_rate < 0 else "flat"
            })

        # 3. S&P 500
        sp_query = text("SELECT sp500, loaded_date FROM ml_gold_raw WHERE sp500 IS NOT NULL ORDER BY loaded_date DESC LIMIT 2")
        sp_res = db.execute(sp_query).fetchall()
        if len(sp_res) >= 2:
            sp_today = float(sp_res[0][0])
            sp_yesterday = float(sp_res[1][0])
            sp_diff = sp_today - sp_yesterday
            sp_rate = (sp_diff / sp_yesterday) * 100 if sp_yesterday != 0 else 0.0
            realtime_trends.append({
                "name": "S&P 500",
                "value": f"{sp_today:,.0f}" if sp_today >= 1000 else f"{sp_today:.2f}",
                "unit": "pt",
                "rate": f"{sp_rate:+.2f}%" if sp_rate != 0 else "0.00%",
                "direction": "up" if sp_rate > 0 else "down" if sp_rate < 0 else "flat"
            })
    except Exception as e:
        logger.warning(f"Failed to fetch realtime trends from DB: {e}")
        realtime_trends = []



    # E. 뉴스 AI 요약 생성 및 캐싱 연동
    import asyncio
    ai_summaries = {}
    current_time = time.time()
    
    categories_to_fetch = []
    
    for cat_key, articles in [("economy", economy_news), ("politics", politics_news), ("itScience", it_news)]:
        cache_data = AI_NEWS_CACHE[cat_key]
        if not cache_data["summary"] or (current_time - cache_data["updated_at"] > CACHE_EXPIRE_SECONDS):
            cat_name = "경제" if cat_key == "economy" else "정치" if cat_key == "politics" else "IT/과학"
            categories_to_fetch.append((cat_key, cat_name, fetch_ai_news_summary(cat_name, articles)))
        else:
            ai_summaries[cat_key] = cache_data["summary"]
            
    if categories_to_fetch:
        # asyncio.gather를 사용해 모든 OpenAI API 호출을 동시에 실행!
        keys = [item[0] for item in categories_to_fetch]
        coroutines = [item[2] for item in categories_to_fetch]
        
        results = await asyncio.gather(*coroutines)
        
        for cat_key, summary_txt in zip(keys, results):
            cache_data = AI_NEWS_CACHE[cat_key]
            if summary_txt and not summary_txt.startswith("- 실시간 AI 요약 브리핑을 생성하는 도중") and not summary_txt.startswith("- 실시간 AI 요약 브리핑을 준비"):
                AI_NEWS_CACHE[cat_key] = {
                    "summary": summary_txt,
                    "updated_at": current_time
                }
                ai_summaries[cat_key] = summary_txt
            else:
                ai_summaries[cat_key] = cache_data["summary"] if cache_data["summary"] else summary_txt

    return {
        "news": news_data,
        "indicators": {
            "gold": gold_data,
            "realEstate": re_data,
            "interestRate": br_data
        },
        "realtimeTrends": realtime_trends,
        "aiSummaries": ai_summaries
    }


async def get_news_list(
    category: Optional[str],
    q: Optional[str],
    page: int,
    size: int,
    from_date: Optional[str],
    to_date: Optional[str],
    sort: Optional[str],
    current_user,
    db: Session,
) -> NewsListResponse:
    """뉴스 목록 조회 (Elasticsearch)"""
    try:
        if not from_date:
            kst_now = datetime.utcnow() + timedelta(hours=9)
            from_date = kst_now.strftime("%Y-%m-%d")

        if from_date and len(from_date) == 10:
            try:
                dt = datetime.strptime(from_date, "%Y-%m-%d")
                utc_dt = dt - timedelta(hours=9)
                from_date = utc_dt.strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                pass

        if to_date and len(to_date) == 10:
            try:
                dt = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
                utc_dt = dt - timedelta(hours=9)
                to_date = utc_dt.strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                pass

        es_query = {"bool": {"must": []}}
        
        if q:
            es_query["bool"]["must"].append({
                "multi_match": {
                    "query": q,
                    "fields": ["title", "content", "summary"]
                }
            })
        else:
            es_query["bool"]["must"].append({"match_all": {}})
            
        es_filters = []
        if category and category != "전체":
            cat_map = {
                "경제": "경제",
                "정치": "정치",
                "사회": "머그",
                "IT/과학": "머그",
                "economy": "경제",
                "politics": "정치",
                "it": "머그",
                "itScience": "머그"
            }
            mapped_cat = cat_map.get(category, category)
            es_filters.append({"term": {"category": mapped_cat}})
            
        date_filter = {}
        if from_date:
            date_filter["gte"] = from_date
        if to_date:
            date_filter["lte"] = to_date
        if date_filter:
            es_filters.append({"range": {"published_at": date_filter}})

        if es_filters:
            es_query["bool"]["filter"] = es_filters
            
        es_sort = [{"published_at": {"order": "asc" if sort == "oldest" else "desc"}}]
            
        es_payload = {
            "query": es_query,
            "sort": es_sort,
            "from": (page - 1) * size,
            "size": size
        }
        
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.post(
                f"{ES_HOST}/sbs_news/_search",
                json=es_payload
            )
            
            if response.status_code == 200:
                res_data = response.json()
                hits_info = res_data.get("hits", {})
                hits_list = hits_info.get("hits", [])
                
                total_info = hits_info.get("total", 0)
                total_count = total_info.get("value", 0) if isinstance(total_info, dict) else int(total_info)
                    
                search_items = []
                for hit in hits_list:
                    source = hit.get("_source", {})
                    cat = source.get("category", "일반")
                    if cat in ["머그", "사회"]:
                        cat = "사회"
                    pub_at_str = source.get("published_at", "")
                    if pub_at_str:
                        pub_at_str = pub_at_str.split("T")[0] if "T" in pub_at_str else pub_at_str[:10]
                    else:
                        pub_at_str = date.today().strftime("%Y-%m-%d")
                        
                    search_items.append({
                        "id": hit.get("_id", ""),
                        "title": source.get("title", ""),
                        "category": cat,
                        "publishedAt": pub_at_str,
                        "isBookmarked": False
                    })
                    
                total_pages = max(1, (total_count + size - 1) // size)
                return NewsListResponse(
                    items=search_items,
                    pagination={
                        "page": page,
                        "size": size,
                        "totalCount": total_count,
                        "totalPages": total_pages
                    }
                )
    except Exception as e:
        logger.error(f"Failed to fetch news list from Elasticsearch: {e}")

    return NewsListResponse(
        items=[],
        pagination={
            "page": page,
            "size": size,
            "totalCount": 0,
            "totalPages": 1
        }
    )


async def get_news_detail(
    news_id: str, current_user, db: Session
) -> NewsDetailResponse:
    """뉴스 상세 조회 (Elasticsearch)"""
    from fastapi import HTTPException
    
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.get(f"{ES_HOST}/sbs_news/_doc/{news_id}")
            if response.status_code == 200:
                hit = response.json()
                source = hit.get("_source", {})
                
                pub_at = source.get("published_at", "")
                if pub_at and not pub_at.endswith("Z") and "+" not in pub_at:
                    pub_at = pub_at + "Z"
                    
                tags = source.get("tags", [])
                if isinstance(tags, str):
                    tags = tags.split(",") if tags else []
                    
                cat = source.get("category", "일반")
                if cat in ["머그", "사회"]:
                    cat = "사회"
                    
                return NewsDetailResponse(
                    newsId=news_id,
                    title=source.get("title", ""),
                    body=source.get("content", source.get("summary", "")),
                    category=cat,
                    source=source.get("author", "SBS 뉴스"),
                    originUrl=source.get("url", ""),
                    tags=tags,
                    publishedAt=pub_at or datetime.utcnow().isoformat() + "Z",
                    createdAt=source.get("indexed_at", datetime.utcnow().isoformat() + "Z")
                )
    except Exception as e:
        logger.error(f"Failed to fetch news detail from Elasticsearch: {e}")
        
    raise HTTPException(status_code=404, detail="요청하신 뉴스를 찾을 수 없습니다.")


async def get_indicator_latest(
    type: str, current_user, db: Session
) -> IndicatorLatestResponse:
    """지표 최신값 조회"""
    from fastapi import HTTPException
    
    if type not in ["gold", "real_estate", "base_rate"]:
        raise HTTPException(status_code=400, detail="허용되지 않는 type 값")
    
    label_map = {
        "gold": ("금값", "Gold Price"),
        "real_estate": ("부동산", "Real Estate Index"),
        "base_rate": ("금리", "Base Rate")
    }
    label_ko, label_en = label_map[type]
    
    from sqlalchemy import text
    
    today_val = 0.0
    yesterday_val = 0.0
    today_rec_at = ""
    yesterday_rec_at = ""
    
    if type == "real_estate":
        try:
            re_hist_query = text("SELECT house_price_idx, date_ym FROM ml_realestate_preprocessed ORDER BY date_ym DESC LIMIT 2")
            re_res = db.execute(re_hist_query).fetchall()
            if len(re_res) >= 2:
                today_val = float(re_res[0][0])
                yesterday_val = float(re_res[1][0])
                ym_today = str(re_res[0][1])
                ym_yesterday = str(re_res[1][1])
                today_rec_at = f"{ym_today[:4]}-{ym_today[4:6]}-01T00:00:00Z"
                yesterday_rec_at = f"{ym_yesterday[:4]}-{ym_yesterday[4:6]}-01T00:00:00Z"
            else:
                raise HTTPException(status_code=404, detail="해당 지표 데이터 없음")
        except Exception as e:
            logger.warning(f"Failed to fetch realestate history in get_indicator_latest: {e}")
            raise HTTPException(status_code=404, detail="해당 지표 데이터 없음")
    else:
        history = db.query(EconomicIndicatorHistory).filter(
            EconomicIndicatorHistory.type == type
        ).order_by(EconomicIndicatorHistory.recorded_at.desc()).limit(2).all()
        
        if len(history) < 2:
            raise HTTPException(status_code=404, detail="해당 지표 데이터 없음")
            
        today_row = history[0]
        yesterday_row = history[1]
        
        today_val = float(today_row.value)
        yesterday_val = float(yesterday_row.value)
        
        today_rec_at = today_row.recorded_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        yesterday_rec_at = yesterday_row.recorded_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    if type == "base_rate":
        today_change = round(today_val - yesterday_val, 2)
    else:
        today_change = round(((today_val - yesterday_val) / yesterday_val) * 100, 1) if yesterday_val != 0 else 0.0
            
    if today_val > yesterday_val:
        today_dir = "up"
    elif today_val < yesterday_val:
        today_dir = "down"
    else:
        today_dir = "flat"
        
    tomorrow_val = None
    tomorrow_change = None
    tomorrow_dir = "flat"
    prob_rise_val, prob_fall_val = None, None
    prob_cut_val, prob_freeze_val, prob_hike_val = None, None, None
    pred_text = None
    
    if type == "gold":
        try:
            g_pred_query = text("SELECT prob_rise, prob_fall FROM gold_predictions ORDER BY created_at DESC LIMIT 1")
            g_pred_res = db.execute(g_pred_query).fetchone()
            if g_pred_res:
                raw_rise = float(g_pred_res[0])
                raw_fall = float(g_pred_res[1])
                prob_rise_val = round(raw_rise * 100) if raw_rise < 1.0 else round(raw_rise)
                prob_fall_val = round(raw_fall * 100) if raw_fall < 1.0 else round(raw_fall)
                total_prob = prob_rise_val + prob_fall_val
                if total_prob > 0:
                    prob_rise_val = round((prob_rise_val / total_prob) * 100)
                    prob_fall_val = 100 - prob_rise_val
                
                pred_text = "상승 가능성 높음" if prob_rise_val > prob_fall_val else ("하락 가능성 높음" if prob_rise_val < prob_fall_val else "상승/하락 가능성 동률")
                tomorrow_val = round(today_val * (1 + (prob_rise_val - prob_fall_val)/1000), 2)
                tomorrow_change = round(((tomorrow_val - today_val) / today_val) * 100, 1) if today_val != 0 else 0.0
                tomorrow_dir = "up" if tomorrow_val > today_val else "down" if tomorrow_val < today_val else "flat"
        except Exception as e:
            logger.warning(f"Failed to fetch gold predictions in latest: {e}")
            
    elif type == "base_rate":
        try:
            br_pred_query = text("SELECT prob_cut, prob_freeze, prob_hike FROM baserate_predictions ORDER BY created_at DESC LIMIT 1")
            br_pred_res = db.execute(br_pred_query).fetchone()
            if br_pred_res:
                raw_cut = float(br_pred_res[0])
                raw_freeze = float(br_pred_res[1])
                raw_hike = float(br_pred_res[2])
                prob_cut_val = round(raw_cut * 100) if raw_cut < 1.0 else round(raw_cut)
                prob_freeze_val = round(raw_freeze * 100) if raw_freeze < 1.0 else round(raw_freeze)
                prob_hike_val = round(raw_hike * 100) if raw_hike < 1.0 else round(raw_hike)
                total_prob = prob_cut_val + prob_freeze_val + prob_hike_val
                if total_prob > 0:
                    prob_cut_val = round((prob_cut_val / total_prob) * 100)
                    prob_freeze_val = round((prob_freeze_val / total_prob) * 100)
                    prob_hike_val = 100 - prob_cut_val - prob_freeze_val
                
                max_prob = max(prob_cut_val, prob_freeze_val, prob_hike_val)
                if max_prob == prob_cut_val:
                    tomorrow_val = today_val - 0.25
                    pred_text = "인하 가능성 높음"
                elif max_prob == prob_freeze_val:
                    tomorrow_val = today_val
                    pred_text = "동결 가능성 높음"
                else:
                    tomorrow_val = today_val + 0.25
                    pred_text = "인상 가능성 높음"
                    
                tomorrow_change = round(tomorrow_val - today_val, 2)
                tomorrow_dir = "up" if tomorrow_val > today_val else "down" if tomorrow_val < today_val else "flat"
        except Exception as e:
            logger.warning(f"Failed to fetch baserate predictions in latest: {e}")
            
    elif type == "real_estate":
        try:
            re_pred_query = text("SELECT predicted_value, predicted_index FROM realestate_predictions ORDER BY created_at DESC LIMIT 1")
            re_pred_res = db.execute(re_pred_query).fetchone()
            if re_pred_res:
                pred_rate = float(re_pred_res[0])
                pred_index = re_pred_res[1]
                
                if pred_index is not None:
                    tomorrow_val = round(float(pred_index), 2)
                else:
                    tomorrow_val = round(today_val * (1 + pred_rate / 100), 2)
                    
                tomorrow_change = round(pred_rate, 2)
                tomorrow_dir = "up" if pred_rate > 0 else "down" if pred_rate < 0 else "flat"
        except Exception as e:
            logger.warning(f"Failed to fetch realestate predictions in latest: {e}")
            
    return {
        "type": type,
        "labelKo": label_ko,
        "labelEn": label_en,
        "yesterday": {
            "value": yesterday_val,
            "recordedAt": yesterday_rec_at
        },
        "today": {
            "value": today_val,
            "changeRate": today_change,
            "direction": today_dir,
            "recordedAt": today_rec_at
        },
        "tomorrow": {
            "value": tomorrow_val,
            "changeRate": tomorrow_change,
            "direction": tomorrow_dir,
            "probRise": prob_rise_val,
            "probFall": prob_fall_val,
            "probCut": prob_cut_val,
            "probFreeze": prob_freeze_val,
            "probHike": prob_hike_val,
            "predictionText": pred_text
        }
    }


async def get_indicator_history(
    type: str,
    from_date: Optional[str],
    to_date: Optional[str],
    granularity: Optional[str],
    current_user,
    db: Session,
) -> IndicatorHistoryResponse:
    """지표 이력 조회"""
    from fastapi import HTTPException
    import datetime
    
    if type not in ["gold", "real_estate", "base_rate"]:
        raise HTTPException(status_code=400, detail="허용되지 않는 type 값")
        
    if not from_date or not to_date:
        raise HTTPException(status_code=400, detail="from / to 누락, 날짜 형식 오류, 허용되지 않는 granularity")
        
    try:
        from_dt = datetime.datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="from / to 누락, 날짜 형식 오류, 허용되지 않는 granularity")
        
    if granularity is None:
        granularity = "daily"
    if granularity not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="from / to 누락, 날짜 형식 오류, 허용되지 않는 granularity")
        
    if type == "real_estate":
        from sqlalchemy import text
        try:
            re_hist_query = text("SELECT date_ym, house_price_idx FROM ml_realestate_preprocessed ORDER BY date_ym DESC LIMIT 12")
            re_res = db.execute(re_hist_query).fetchall()
            
            if not re_res:
                raise HTTPException(status_code=404, detail="해당 지표 데이터 없음")
                
            re_res_sorted = sorted(re_res, key=lambda x: x[0])
            
            series = []
            for row in re_res_sorted:
                ym_str = str(row[0])
                formatted_date = f"{ym_str[:4]}-{ym_str[4:6]}-01"
                series.append({
                    "date": formatted_date,
                    "value": float(row[1])
                })
                
            vals = [s["value"] for s in series]
            
            return {
                "type": type,
                "granularity": granularity or "monthly",
                "source": "ECOS",
                "series": series,
                "stats": {
                    "min": round(min(vals), 2),
                    "max": round(max(vals), 2),
                    "avg": round(sum(vals) / len(vals), 2)
                }
            }
        except Exception as e:
            logger.warning(f"Failed to fetch realestate history in get_indicator_history: {e}")
            raise HTTPException(status_code=404, detail="해당 지표 데이터 없음")

    to_dt_end = to_dt + datetime.timedelta(days=1)
    
    history_rows = db.query(EconomicIndicatorHistory).filter(
        EconomicIndicatorHistory.type == type,
        EconomicIndicatorHistory.recorded_at >= from_dt,
        EconomicIndicatorHistory.recorded_at < to_dt_end
    ).order_by(EconomicIndicatorHistory.recorded_at.asc()).all()
    
    if not history_rows:
        raise HTTPException(status_code=404, detail="해당 지표 데이터 없음")
        
    sources = set()
    for row in history_rows:
        if row.source:
            sources.add(row.source)
    source_str = "·".join(sorted(list(sources))) if sources else "ECOS·FRED"
    
    series = []
    
    if granularity == "daily":
        for row in history_rows:
            series.append({
                "date": row.recorded_at.strftime("%Y-%m-%d"),
                "value": float(row.value)
            })
    elif granularity == "weekly":
        weekly_groups = {}
        for row in history_rows:
            row_date = row.recorded_at.date()
            monday = row_date - datetime.timedelta(days=row_date.weekday())
            monday_str = monday.strftime("%Y-%m-%d")
            if monday_str not in weekly_groups:
                weekly_groups[monday_str] = []
            weekly_groups[monday_str].append(float(row.value))
            
        for d_str, vals in sorted(weekly_groups.items()):
            series.append({
                "date": d_str,
                "value": round(sum(vals) / len(vals), 2)
            })
    elif granularity == "monthly":
        monthly_groups = {}
        for row in history_rows:
            month_str = row.recorded_at.strftime("%Y-%m-01")
            if month_str not in monthly_groups:
                monthly_groups[month_str] = []
            monthly_groups[month_str].append(float(row.value))
            
        for d_str, vals in sorted(monthly_groups.items()):
            series.append({
                "date": d_str,
                "value": round(sum(vals) / len(vals), 2)
            })
            
    if not series:
        raise HTTPException(status_code=404, detail="해당 지표 데이터 없음")
        
    vals = [s["value"] for s in series]
    
    return {
        "type": type,
        "granularity": granularity,
        "source": source_str,
        "series": series,
        "stats": {
            "min": round(min(vals), 2),
            "max": round(max(vals), 2),
            "avg": round(sum(vals) / len(vals), 2)
        }
    }


async def get_indicator_prediction(
    type: str, horizon: Optional[int], current_user, db: Session
) -> IndicatorPredictionResponse:
    """지표 예측 조회"""
    from fastapi import HTTPException
    import datetime
    
    if type not in ["gold", "real_estate", "base_rate"]:
        raise HTTPException(status_code=400, detail="허용되지 않는 type 값")
        
    from sqlalchemy import text
    
    h_val = horizon if horizon is not None else 7
    predictions_list = []
    db_run_id = None
    
    if type == "real_estate":
        try:
            re_ym_query = text("SELECT date_ym FROM ml_realestate_preprocessed ORDER BY date_ym DESC LIMIT 1")
            re_ym_res = db.execute(re_ym_query).fetchone()
            
            next_month_str = ""
            if re_ym_res:
                ym_str = str(re_ym_res[0])
                year = int(ym_str[:4])
                month = int(ym_str[4:6])
                if month == 12:
                    next_year = year + 1
                    next_month = 1
                else:
                    next_year = year
                    next_month = month + 1
                next_month_str = f"{next_year}-{next_month:02d}-01"
            else:
                next_month_str = (datetime.datetime.utcnow() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
                
            re_pred_query = text("SELECT run_id, predicted_index FROM realestate_predictions ORDER BY created_at DESC LIMIT 1")
            re_pred_res = db.execute(re_pred_query).fetchone()
            
            if re_pred_res:
                db_run_id = re_pred_res[0]
                pred_index = re_pred_res[1]
                predictions_list = [
                    {
                        "date": next_month_str,
                        "value": float(pred_index) if pred_index is not None else None,
                        "lower": None,
                        "upper": None
                    }
                ]
            else:
                raise HTTPException(status_code=404, detail="해당 지표 데이터 없음")
        except Exception as e:
            logger.warning(f"Failed to fetch realestate predictions in get_indicator_prediction: {e}")
            raise HTTPException(status_code=404, detail="해당 지표 데이터 없음")
    else:
        preds = db.query(EconomicIndicatorPrediction).filter(
            EconomicIndicatorPrediction.type == type
        ).order_by(EconomicIndicatorPrediction.predicted_date.asc()).limit(h_val).all()
        
        predictions_list = [
            {
                "date": p.predicted_date.strftime("%Y-%m-%d"),
                "value": float(p.predicted_value),
                "lower": float(p.confidence_lower) if p.confidence_lower is not None else None,
                "upper": float(p.confidence_upper) if p.confidence_upper is not None else None
            }
            for p in preds
        ]
        
        try:
            pred_tbl = "gold_predictions" if type == "gold" else "baserate_predictions"
            run_id_query = text(f"SELECT run_id FROM {pred_tbl} ORDER BY created_at DESC LIMIT 1")
            run_id_res = db.execute(run_id_query).fetchone()
            if run_id_res:
                db_run_id = run_id_res[0]
        except Exception:
            pass
        
    mlflow_map = {
        "gold": {
            "run_id": db_run_id if db_run_id else None,
            "model_name": "gold_price_predictor",
            "model_version": "12",
            "stage": "Production",
            "source": "ECOS, FRED"
        },
        "real_estate": {
            "run_id": db_run_id if db_run_id else None,
            "model_name": "realestate_index_predictor",
            "model_version": "8",
            "stage": "Production",
            "source": "ECOS"
        },
        "base_rate": {
            "run_id": db_run_id if db_run_id else None,
            "model_name": "baserate_policy_predictor",
            "model_version": "15",
            "stage": "Production",
            "source": "ECOS"
        }
    }
    
    m_info = mlflow_map[type]
    
    return {
        "type": type,
        "horizon": h_val,
        "predictions": predictions_list,
        "mlflow": {
            "run_id": m_info["run_id"],
            "model_name": m_info["model_name"],
            "model_version": m_info["model_version"],
            "stage": m_info["stage"]
        },
        "generatedAt": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": m_info["source"]
    }


async def get_indicator_contribution(
    type: str, current_user, db: Session
) -> IndicatorContributionResponse:
    """지표 기여도 조회"""
    from fastapi import HTTPException
    import datetime
    
    if type not in ["gold", "real_estate", "base_rate"]:
        raise HTTPException(status_code=400, detail="허용되지 않는 type 값")
        
    from sqlalchemy import text
    db_run_id = None
    try:
        pred_tbl = "gold_predictions" if type == "gold" else ("baserate_predictions" if type == "base_rate" else "realestate_predictions")
        run_id_query = text(f"SELECT run_id FROM {pred_tbl} ORDER BY created_at DESC LIMIT 1")
        run_id_res = db.execute(run_id_query).fetchone()
        if run_id_res:
            db_run_id = run_id_res[0]
    except Exception:
        pass

    contribs = db.query(EconomicIndicatorContribution).filter(
        EconomicIndicatorContribution.type == type
    ).order_by(EconomicIndicatorContribution.weight.desc()).all()
    
    feature_map = {
        "kr_usd_exchange": ("kr_usd_exchange", "원/달러 환율"),
        "wti_oil": ("wti_oil", "WTI 유가"),
        "dxy_proxy": ("dxy_proxy", "달러 인덱스 (DXY)"),
        "vix": ("vix", "VIX 지수"),
        "kospi200": ("kospi200", "코스피 200"),
        "sp500": ("sp500", "S&P 500"),
        "kr_cpi": ("kr_cpi", "소비자물가지수 (CPI)"),
        "kr_base_rate": ("kr_base_rate", "기준금리"),
        "kr_unemployment": ("kr_unemployment", "실업률"),
        "kr_gdp": ("kr_gdp", "GDP"),
        "kr_m2": ("kr_m2", "통화량 (M2)"),
        "us_fed_rate": ("us_fed_rate", "미국 기준금리"),
        "house_price_idx": ("house_price_idx", "매매가격지수"),
        "kr_mortgage_rate": ("kr_mortgage_rate", "주택담보대출금리"),
        "apt_trade_count": ("apt_trade_count", "아파트 거래량"),
        "buyer_dominance": ("buyer_dominance", "매수우위지수")
    }
    
    contributions_list = [
        {
            "feature": feature_map.get(c.variable, (c.variable.lower().replace(" ", "_"), c.variable))[0],
            "label": feature_map.get(c.variable, (c.variable.lower().replace(" ", "_"), c.variable))[1],
            "ratio": int(round(float(c.weight) * 100))
        }
        for c in contribs
    ]
        
    mlflow_map = {
        "gold": {
            "run_id": db_run_id if db_run_id else None,
            "model_name": "gold_price_predictor",
            "model_version": "12",
            "stage": "Production"
        },
        "real_estate": {
            "run_id": db_run_id if db_run_id else None,
            "model_name": "realestate_index_predictor",
            "model_version": "8",
            "stage": "Production"
        },
        "base_rate": {
            "run_id": db_run_id if db_run_id else None,
            "model_name": "baserate_policy_predictor",
            "model_version": "15",
            "stage": "Production"
        }
    }
    
    return {
        "type": type,
        "contributions": contributions_list,
        "mlflow": mlflow_map[type],
        "generatedAt": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }


async def create_indicator_report(
    type: str, request: ReportCreateRequest, current_user, db: Session
) -> ReportCreateResponse:
    """지표 리포트 생성 요청"""
    from fastapi import HTTPException
    import random
    
    if type not in ["gold", "real_estate", "base_rate"]:
        raise HTTPException(status_code=400, detail="허용되지 않는 type 값")
        
    report_id = random.randint(100000, 999999)
    return {
        "reportId": report_id,
        "status": "pending",
        "estimatedSeconds": 30
    }


async def get_report_status(
    type: str, report_id: int, current_user, db: Session
) -> ReportStatusResponse:
    """리포트 생성 상태 조회"""
    import datetime
    
    return {
        "reportId": report_id,
        "status": "done",
        "progress": 100,
        "failedReason": None,
        "completedAt": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }


async def get_latest_report(
    type: str, current_user, db: Session
) -> ReportLatestResponse:
    """최신 리포트 조회"""
    from fastapi import HTTPException
    import re
    
    if type not in ["gold", "real_estate", "base_rate"]:
        raise HTTPException(status_code=400, detail="허용되지 않는 type 값")
        
    report = db.query(TrendLlmReport).filter(
        TrendLlmReport.type == type
    ).order_by(TrendLlmReport.created_at.desc()).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="해당 지표 보고서 없음")
        
    # 지능형 요약 추출 파서: 큰 숫자 1,2,3... 대분류 단락 기준 각 문단별 핵심 1~2개 문장 추출
    def clean_markdown(t: str) -> str:
        return t.replace("**", "").replace("__", "").replace("*", "").replace("_", "").strip()

    def parse_sentences(t: str) -> list:
        sents = re.split(r'(?<=[.!?])\s+', t.strip())
        return [s.strip() for s in sents if len(s.strip()) >= 10]

    content = report.content
    section_headers = list(re.finditer(r'^##\s+(\d+)\.\s*(.*)', content, re.MULTILINE))
    
    if not section_headers:
        # 대분류 헤더가 없으면 기본 방식 폴백
        clean_text = clean_markdown(content)
        summary = clean_text[:800].strip() + (" . . . 더보기" if len(clean_text) > 800 else "")
    else:
        sections = []
        for i in range(len(section_headers)):
            start = section_headers[i].end()
            end = section_headers[i+1].start() if i+1 < len(section_headers) else len(content)
            sec_num = section_headers[i].group(1)
            sec_title = clean_markdown(section_headers[i].group(2))
            sec_body = content[start:end]
            sections.append((sec_num, sec_title, sec_body))
            
        summary_parts = []
        for num, title, body in sections:
            lines = body.splitlines()
            sentences_in_section = []
            
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    continue
                if line_str.startswith("#"):
                    continue
                
                if line_str.startswith("-") or line_str.startswith("*"):
                    match_desc = re.match(r"^[-*]\s*\*\*([^*]+)\*\*:\s*(.*)", line_str)
                    if match_desc:
                        key = clean_markdown(match_desc.group(1))
                        val = clean_markdown(match_desc.group(2))
                        if len(val) >= 15:
                            combined = f"{key}: {val}" if not key.lower().strip() in ["평균 shap 기여도", "shap 기여도"] else val
                            sentences_in_section.extend(parse_sentences(combined))
                        continue
                    clean_list_item = re.sub(r"^[-*]\s*", "", line_str)
                    sentences_in_section.extend(parse_sentences(clean_markdown(clean_list_item)))
                    continue
                    
                sentences_in_section.extend(parse_sentences(clean_markdown(line_str)))
                
            selected_sentences = sentences_in_section[:2]
            fixed_sentences = []
            for s in selected_sentences:
                if s and not s.endswith((".", "?", "!")):
                    fixed_sentences.append(s + ".")
                else:
                    fixed_sentences.append(s)
                    
            if fixed_sentences:
                sec_summary = " ".join(fixed_sentences)
                summary_parts.append(f"{num}. {title}: {sec_summary}")
                
        summary = "\n".join(summary_parts)
    
    earliest = db.query(EconomicIndicatorHistory).filter(
        EconomicIndicatorHistory.type == type
    ).order_by(EconomicIndicatorHistory.recorded_at.asc()).first()
    
    latest = db.query(EconomicIndicatorHistory).filter(
        EconomicIndicatorHistory.type == type
    ).order_by(EconomicIndicatorHistory.recorded_at.desc()).first()
    
    from_date = earliest.recorded_at.strftime("%Y-%m-%d") if earliest else "2026-04-25"
    to_date = latest.recorded_at.strftime("%Y-%m-%d") if latest else "2026-05-25"
    
    # Safely handle potential None created_at values
    gen_time_str = report.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if report.created_at else datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return {
        "reportId": report.report_id,
        "type": report.type,
        "content": report.content,
        "summary": report.summary,
        "language": "ko",
        "dataSourcePeriod": {
            "from": from_date,
            "to": to_date
        },
        "generatedAt": gen_time_str
    }


async def bulk_create_indicators(
    request: IndicatorBulkRequest, current_user, db: Session
) -> IndicatorBulkResponse:
    """지표 일괄 등록"""
    saved_count = 0
    skipped_count = 0
    failed_count = 0
    errors_list = []
    
    for idx, item in enumerate(request.items):
        if item.type not in ["gold", "real_estate", "base_rate"]:
            failed_count += 1
            errors_list.append({"index": idx, "reason": "invalid type"})
            continue
            
        existing = db.query(EconomicIndicatorHistory).filter(
            EconomicIndicatorHistory.type == item.type,
            EconomicIndicatorHistory.recorded_at == item.recorded_at
        ).first()
        
        if existing:
            skipped_count += 1
            continue
            
        try:
            db.add(EconomicIndicatorHistory(
                type=item.type,
                value=item.value,
                recorded_at=item.recorded_at,
                source=item.source
            ))
            saved_count += 1
        except Exception as e:
            failed_count += 1
            errors_list.append({"index": idx, "reason": str(e)})
            
    db.commit()
    
    return {
        "savedCount": saved_count,
        "skippedCount": skipped_count,
        "failedCount": failed_count,
        "errors": errors_list if errors_list else None
    }