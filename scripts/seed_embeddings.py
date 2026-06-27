"""
Seed script: Generate Crime DNA embeddings from BriefFacts using sentence-transformers.
Run locally (GPU/CPU). Uploads embeddings.json to Catalyst FileStore.
~20 minutes for 10,000+ records.
"""
import os
import sys
import json
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_embeddings")

try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers not available — using TF-IDF fallback")
    SBERT_AVAILABLE = False

try:
    import zcatalyst_sdk as catalyst
    app = catalyst.initialize()
    ds = app.datastore()
    fs = app.filestore()
    CATALYST_AVAILABLE = True
except Exception:
    logger.warning("Catalyst SDK unavailable — saving to local embeddings.json")
    ds = None
    fs = None
    CATALYST_AVAILABLE = False


def get_fir_records():
    if not CATALYST_AVAILABLE:
        logger.info("Using sample FIR records (no DataStore)")
        return [
            {"CrimeNo": f"SAMPLE_{i:05d}", "BriefFacts": f"Sample crime brief facts for case {i}",
             "DistrictID": "BEU", "CrimeSubHeadID": i % 10 + 1}
            for i in range(100)
        ]
    table = ds.table("CaseMaster")
    result = table.get_by_page_token({"page_size": 10000})
    records = result.get("data", [])
    logger.info(f"Loaded {len(records)} FIR records from DataStore")
    return records


def generate_embeddings_sbert(texts):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("Generating embeddings with sentence-transformers...")
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True)
    return embeddings.tolist()


def generate_embeddings_tfidf(texts):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD
    logger.info("Generating TF-IDF embeddings (fallback)...")
    vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
    tfidf = vectorizer.fit_transform(texts)
    svd = TruncatedSVD(n_components=128)
    embeddings = svd.fit_transform(tfidf)
    return embeddings.tolist()


def main():
    records = get_fir_records()
    texts = [r.get("BriefFacts", "") for r in records]
    crime_nos = [r.get("CrimeNo", f"UNK_{i}") for i, r in enumerate(records)]
    district_ids = [r.get("DistrictID", "UNK") for r in records]

    if SBERT_AVAILABLE:
        embeddings = generate_embeddings_sbert(texts)
    else:
        embeddings = generate_embeddings_tfidf(texts)

    output = {
        "model": "all-MiniLM-L6-v2" if SBERT_AVAILABLE else "tfidf-svd-128",
        "dim": len(embeddings[0]) if embeddings else 128,
        "records": [
            {"CrimeNo": crime_nos[i], "DistrictID": district_ids[i], "embedding": emb}
            for i, emb in enumerate(embeddings)
        ]
    }

    output_path = os.path.join(os.path.dirname(__file__), "embeddings.json")
    with open(output_path, "w") as f:
        json.dump(output, f)
    logger.info(f"Saved {len(embeddings)} embeddings to {output_path}")

    if CATALYST_AVAILABLE and fs:
        logger.info("Uploading embeddings.json to Catalyst FileStore...")
        try:
            folder = fs.folder("kaveri-models")
            with open(output_path, "rb") as f:
                folder.upload_file("embeddings.json", f)
            logger.info("Upload complete")
        except Exception as e:
            logger.error(f"FileStore upload failed: {e}")
    else:
        logger.info("Embeddings saved locally (no FileStore upload)")

    logger.info(f"=== Embedding seed complete: {len(embeddings)} records ===")


if __name__ == "__main__":
    main()
