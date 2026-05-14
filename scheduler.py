import logging
import subprocess
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from elasticsearch import Elasticsearch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

ES_HOST = "http://localhost:9200"
ES_INDEX = "sbs_news"


def reset_index():
    logger.info("ES 인덱스 초기화 시작...")
    es = Elasticsearch(hosts=[ES_HOST])
    try:
        es.indices.delete(index=ES_INDEX, ignore_unavailable=True)
        logger.info(f"인덱스 삭제 완료: {ES_INDEX}")
    except Exception as e:
        logger.error(f"인덱스 삭제 실패: {e}")


def collect():
    logger.info("뉴스 수집 시작...")
    result = subprocess.run(
        [sys.executable, "sbs_rss.py"],
        capture_output=True,
        text=True
    )
    if result.stdout:
        logger.info(result.stdout.strip())
    if result.stderr:
        logger.warning(result.stderr.strip())
    logger.info("뉴스 수집 완료")


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(collect, "interval", minutes=30, id="news_collect")
    scheduler.add_job(
        lambda: (reset_index(), collect()),
        "cron",
        hour=6,
        minute=0,
        id="daily_reset"
    )

    logger.info("스케줄러 시작 (수집: 30분 간격, 초기화: 매일 06:00)")
    collect()

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("스케줄러 종료")