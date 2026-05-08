from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

es.indices.create(index="news_articles", mappings={
    "properties": {
        "category":     {"type": "keyword"},
        "keyword":      {"type": "keyword"},
        "title":        {"type": "text"},
        "description":  {"type": "text"},
        "body":         {"type": "text"},
        "url":          {"type": "keyword"},
        "naver_link":   {"type": "keyword"},
        "pub_date":     {"type": "keyword"},
        "collected_at": {"type": "date", "format": "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"}
    }
})
print("인덱스 생성 완료")