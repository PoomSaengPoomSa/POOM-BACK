"""
SBS 뉴스 클러스터링 기반 중요도 랭킹
- 임베딩: title + summary + content[:500]
- 모델: jhgan/ko-sroberta-multitask
- 클러스터링: HDBSCAN (K 지정 불필요)
- 후처리: 클러스터 간 병합 → 노이즈 재분류
- 결과: ES에 cluster_id, cluster_size, cluster_rank 업데이트
"""

import numpy as np
from collections import defaultdict
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer
import hdbscan

ES_HOST = "http://localhost:9200"
ES_INDEX = "sbs_news"
EMBED_MODEL = "jhgan/ko-sroberta-multitask"

MERGE_THRESHOLD = 0.85
NOISE_ASSIGN_THRESHOLD = 0.75


def fetch_docs(es: Elasticsearch) -> list[dict]:
    resp = es.search(
        index=ES_INDEX,
        body={
            "_source": ["doc_id", "title", "summary", "content", "category", "url", "published_at"],
            "size": 1000,
            "query": {"match_all": {}}
        }
    )
    docs = []
    for hit in resp["hits"]["hits"]:
        src = hit["_source"]
        docs.append({
            "es_id": hit["_id"],
            "doc_id": src.get("doc_id", ""),
            "title": src.get("title", ""),
            "summary": src.get("summary", ""),
            "content": src.get("content", ""),
            "category": src.get("category", ""),
            "url": src.get("url", ""),
            "published_at": src.get("published_at", ""),
        })
    return docs


def build_text(doc: dict) -> str:
    title = doc["title"].strip()
    summary = doc["summary"].strip()
    content = doc["content"].strip()[:500]
    return f"{title} {summary} {content}"


def embed_docs(docs: list[dict]) -> np.ndarray:
    model = SentenceTransformer(EMBED_MODEL)
    texts = [build_text(d) for d in docs]
    print(f"임베딩 중... ({len(texts)}건)")
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
    return embeddings


def cluster_docs(embeddings: np.ndarray) -> np.ndarray:
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=2,
        min_samples=1,
        metric="euclidean"
    )
    return clusterer.fit_predict(embeddings)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = a.flatten()
    b = b.flatten()
    denom = float(np.linalg.norm(a)) * float(np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def compute_centers(cluster_map: dict, embeddings: np.ndarray) -> dict:
    return {
        cid: embeddings[idxs].mean(axis=0)
        for cid, idxs in cluster_map.items()
        if cid != -1
    }


def merge_clusters(labels: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
    labels = labels.copy()

    cluster_map = defaultdict(list)
    for idx, label in enumerate(labels):
        cluster_map[int(label)].append(idx)

    valid_ids = [cid for cid in cluster_map if cid != -1]
    centers = compute_centers(cluster_map, embeddings)

    merged = True
    while merged:
        merged = False
        valid_ids = sorted([cid for cid in set(labels) if cid != -1])

        pairs = []
        for i in range(len(valid_ids)):
            for j in range(i + 1, len(valid_ids)):
                a, b = valid_ids[i], valid_ids[j]
                if a not in centers or b not in centers:
                    continue
                sim = cosine_similarity(centers[a], centers[b])
                if sim >= MERGE_THRESHOLD:
                    pairs.append((sim, a, b))

        if not pairs:
            break

        pairs.sort(reverse=True)
        _, keep, drop = pairs[0]

        for idx in range(len(labels)):
            if labels[idx] == drop:
                labels[idx] = keep

        cluster_map[keep].extend(cluster_map.pop(drop, []))
        centers[keep] = embeddings[cluster_map[keep]].mean(axis=0)
        if drop in centers:
            del centers[drop]

        merged = True
        print(f"  클러스터 병합: {drop} → {keep} (유사도: {_:.3f})")

    return labels


def assign_noise(labels: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
    labels = labels.copy()

    cluster_map = defaultdict(list)
    for idx, label in enumerate(labels):
        cluster_map[int(label)].append(idx)

    centers = compute_centers(cluster_map, embeddings)
    if not centers:
        return labels

    noise_indices = [idx for idx, label in enumerate(labels) if label == -1]
    assigned = 0

    for idx in noise_indices:
        vec = embeddings[idx]
        best_cid = max(centers.keys(), key=lambda cid: cosine_similarity(vec, centers[cid]))
        best_sim = cosine_similarity(vec, centers[best_cid])
        if best_sim >= NOISE_ASSIGN_THRESHOLD:
            labels[idx] = best_cid
            cluster_map[best_cid].append(idx)
            centers[best_cid] = embeddings[cluster_map[best_cid]].mean(axis=0)
            assigned += 1

    print(f"  노이즈 재분류: {assigned}/{len(noise_indices)}건 편입")
    return labels


def analyze_clusters(docs: list[dict], labels: np.ndarray, embeddings: np.ndarray) -> list[dict]:
    cluster_map = defaultdict(list)
    for idx, label in enumerate(labels):
        cluster_map[int(label)].append(idx)

    valid_clusters = {k: v for k, v in cluster_map.items() if k != -1}
    sorted_clusters = sorted(valid_clusters.items(), key=lambda x: len(x[1]), reverse=True)
    cluster_rank = {cid: rank + 1 for rank, (cid, _) in enumerate(sorted_clusters)}
    noise_rank = len(valid_clusters) + 1

    cluster_centers = {
        cid: embeddings[idxs].mean(axis=0)
        for cid, idxs in valid_clusters.items()
    }

    results = []
    for idx, doc in enumerate(docs):
        label = int(labels[idx])
        if label == -1:
            results.append({
                **doc,
                "cluster_id": -1,
                "cluster_size": 1,
                "cluster_rank": noise_rank,
                "is_representative": False,
            })
        else:
            cluster_size = len(cluster_map[label])
            rank = cluster_rank[label]
            center = cluster_centers[label]
            idxs_in_cluster = cluster_map[label]
            dists = [np.linalg.norm(embeddings[i] - center) for i in idxs_in_cluster]
            rep_idx = idxs_in_cluster[int(np.argmin(dists))]
            results.append({
                **doc,
                "cluster_id": label,
                "cluster_size": cluster_size,
                "cluster_rank": rank,
                "is_representative": (idx == rep_idx),
            })

    return results


def update_es(es: Elasticsearch, results: list[dict]) -> None:
    actions = [
        {
            "_op_type": "update",
            "_index": ES_INDEX,
            "_id": r["es_id"],
            "doc": {
                "cluster_id": r["cluster_id"],
                "cluster_size": r["cluster_size"],
                "cluster_rank": r["cluster_rank"],
                "is_representative": r["is_representative"],
            }
        }
        for r in results
    ]
    success, failed = helpers.bulk(es, actions, raise_on_error=False, stats_only=False)
    print(f"ES 업데이트 완료 → 성공: {success}, 실패: {len(failed) if isinstance(failed, list) else 0}")


def print_ranking(results: list[dict]) -> None:
    reps = [r for r in results if r["is_representative"]]
    reps_sorted = sorted(reps, key=lambda x: x["cluster_rank"])

    print("\n" + "=" * 70)
    print("클러스터 기반 중요도 랭킹 (대표 기사)")
    print("=" * 70)
    for r in reps_sorted:
        print(f"[{r['cluster_rank']}위] 기사 수: {r['cluster_size']}건 | 카테고리: {r['category']}")
        print(f"  제목: {r['title']}")
        print()

    noise_count = sum(1 for r in results if r["cluster_id"] == -1)
    print(f"노이즈(단독 기사): {noise_count}건")


def main():
    es = Elasticsearch(hosts=[ES_HOST])

    print("ES에서 문서 조회 중...")
    docs = fetch_docs(es)
    print(f"조회 완료: {len(docs)}건")

    embeddings = embed_docs(docs)

    print("클러스터링 중...")
    labels = cluster_docs(embeddings)

    unique_labels = set(labels)
    noise_count = sum(1 for l in labels if l == -1)
    print(f"클러스터 수: {len(unique_labels) - (1 if -1 in unique_labels else 0)}, 노이즈: {noise_count}건")

    print("클러스터 병합 중...")
    labels = merge_clusters(labels, embeddings)

    print("노이즈 재분류 중...")
    labels = assign_noise(labels, embeddings)

    unique_labels = set(labels)
    noise_count = sum(1 for l in labels if l == -1)
    print(f"후처리 후 → 클러스터 수: {len(unique_labels) - (1 if -1 in unique_labels else 0)}, 노이즈: {noise_count}건")

    results = analyze_clusters(docs, labels, embeddings)

    print_ranking(results)
    update_es(es, results)


if __name__ == "__main__":
    main()