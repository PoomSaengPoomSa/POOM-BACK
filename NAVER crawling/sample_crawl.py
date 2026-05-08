import json
import requests
import re
import html
from bs4 import BeautifulSoup
from datetime import datetime
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv
import os
import ast
from elasticsearch import Elasticsearch

load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

es = Elasticsearch("http://localhost:9200")

def load_categories(path="category.md"):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    start = content.find("{")
    end = content.rfind("}") + 1
    return ast.literal_eval(content[start:end])

NEWS_CATEGORY_KEYWORDS = load_categories()

def preprocess(text):
    text = html.unescape(text)
    text = re.sub(r'[*_#>`~]', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'\[.{1,10} 기자\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_html(text):
    return re.sub(r"<.*?>", "", text)

def parse_date(pub_date_str):
    try:
        return parsedate_to_datetime(pub_date_str).isoformat()
    except:
        return datetime.now().isoformat()

def is_duplicate(url):
    res = es.search(index="news_articles", body={
        "query": {"term": {"url": url}}
    })
    return res["hits"]["total"]["value"] > 0

def get_news(query, display=10):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    params = {"query": query, "display": display, "sort": "date"}
    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    return res.json()

def get_article_body(naver_link):
    try:
        res = requests.get(naver_link, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        body = soup.select_one("#newsct_article")
        if body:
            return preprocess(body.get_text(strip=True))
    except:
        pass
    return None

def crawl_and_index():
    total, skipped, indexed = 0, 0, 0

    for category, keywords in NEWS_CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            print(f"[{category}] '{keyword}' 수집 중...")
            try:
                data = get_news(keyword)
                for item in data.get("items", []):
                    total += 1
                    url = item["originallink"]
                    naver_link = item["link"]

                    if "n.news.naver.com" not in naver_link:
                        skipped += 1
                        continue

                    if is_duplicate(url):
                        skipped += 1
                        continue

                    body = get_article_body(naver_link)
                    if not body:
                        skipped += 1
                        continue

                    doc = {
                        "category": category,
                        "keyword": keyword,
                        "title": preprocess(clean_html(item["title"])),
                        "description": preprocess(clean_html(item["description"])),
                        "body": body,
                        "url": url,
                        "naver_link": naver_link,
                        "pub_date": parse_date(item["pubDate"]),
                        "collected_at": datetime.now().isoformat()
                    }
                    es.index(index="news_articles", document=doc)
                    indexed += 1
                    print(f"  적재: {doc['title'][:30]}")

            except Exception as e:
                print(f"  오류: {e}")

    print(f"\n완료 - 전체: {total}건 / 적재: {indexed}건 / 중복스킵: {skipped}건")

if __name__ == "__main__":
    crawl_and_index()