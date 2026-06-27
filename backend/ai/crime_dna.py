import logging
import json
from typing import List, Optional

import numpy as np

logger = logging.getLogger("kaveri.crime_dna")


def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def _tfidf_encode(query: str, corpus: List[str]) -> tuple:
    """TF-IDF fallback encoder. Returns (query_vec, corpus_vecs)."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words="english",
            ngram_range=(1, 2),
        )
        all_texts = [query] + corpus
        matrix = vectorizer.fit_transform(all_texts).toarray()
        query_vec = matrix[0]
        corpus_vecs = matrix[1:]
        return query_vec, corpus_vecs
    except Exception as e:
        logger.warning(f"TF-IDF encoding failed: {e}")
        return None, None


def _sentence_transformer_encode(query: str, corpus: List[str]) -> tuple:
    """sentence-transformers encoder — preferred when available."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        all_texts = [query] + corpus
        embeddings = model.encode(all_texts)
        query_vec = embeddings[0]
        corpus_vecs = embeddings[1:]
        return query_vec, corpus_vecs
    except ImportError:
        return None, None
    except Exception as e:
        logger.warning(f"sentence-transformers encoding failed: {e}")
        return None, None


def find_similar_cases(
    brief_facts: str,
    top_k: int = 5,
    embeddings_data: Optional[list] = None,
) -> List[dict]:
    """
    Find similar past cases using cosine similarity on BriefFacts embeddings.

    Args:
        brief_facts: Text description of the new/query crime case.
        top_k: Number of top similar cases to return.
        embeddings_data: Pre-loaded embeddings from app_state.embeddings or FileStore.
                         Each item: {CrimeNo, BriefFacts, district, embedding: [float]}

    Returns:
        List of {CrimeNo, similarity_score, BriefFacts, district}
    """
    if not brief_facts or not brief_facts.strip():
        logger.warning("find_similar_cases: empty brief_facts provided")
        return []

    # Load embeddings from app_state if not provided
    if embeddings_data is None:
        try:
            from app import app_state
            embeddings_data = app_state.embeddings
        except Exception:
            embeddings_data = None

    if not embeddings_data:
        logger.warning("No embeddings data available — returning empty results")
        return []

    # Extract pre-computed embedding vectors if available
    pre_computed = [
        item for item in embeddings_data
        if "embedding" in item and item["embedding"]
    ]

    if pre_computed:
        # Use pre-computed embeddings (from seed_embeddings.py / FileStore)
        corpus_facts = [item["BriefFacts"] for item in pre_computed]

        # Encode query using same method that produced corpus embeddings
        query_vec, _ = _sentence_transformer_encode(brief_facts, corpus_facts[:1])

        if query_vec is None:
            # Fallback to TF-IDF
            query_vec, corpus_vecs = _tfidf_encode(
                brief_facts,
                corpus_facts,
            )
            if query_vec is None:
                return []
        else:
            # Encode query alone, compare against stored embeddings
            corpus_vecs = np.array([item["embedding"] for item in pre_computed])

        similarities = []
        for i, item in enumerate(pre_computed):
            if corpus_vecs is not None and len(corpus_vecs) > i:
                sim = _cosine_similarity(
                    np.array(query_vec), np.array(corpus_vecs[i])
                )
                similarities.append((sim, item))

    else:
        # No pre-computed embeddings — encode everything from BriefFacts text
        corpus_facts = [item.get("BriefFacts", "") for item in embeddings_data]

        # Try sentence-transformers first
        query_vec, corpus_vecs = _sentence_transformer_encode(brief_facts, corpus_facts)

        if query_vec is None:
            # Fallback: TF-IDF
            query_vec, corpus_vecs = _tfidf_encode(brief_facts, corpus_facts)

        if query_vec is None or corpus_vecs is None:
            logger.error("All encoding methods failed")
            return []

        similarities = [
            (_cosine_similarity(np.array(query_vec), np.array(corpus_vecs[i])), item)
            for i, item in enumerate(embeddings_data)
        ]

    # Sort by similarity descending
    similarities.sort(key=lambda x: x[0], reverse=True)

    results = []
    for sim_score, item in similarities[:top_k]:
        results.append({
            "CrimeNo": item.get("CrimeNo", "UNKNOWN"),
            "similarity_score": round(sim_score, 4),
            "BriefFacts": item.get("BriefFacts", ""),
            "district": item.get("district", item.get("DistrictID", "N/A")),
        })

    return results


def load_embeddings_from_filestore() -> Optional[list]:
    """Load embeddings JSON from Catalyst FileStore."""
    try:
        import zcatalyst_sdk
        app = zcatalyst_sdk.initialize()
        filestore = app.filestore()
        folder = filestore.folder("crime_embeddings")
        file_obj = folder.file("embeddings.json")
        content = file_obj.download()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        data = json.loads(content)
        logger.info(f"Loaded {len(data)} embeddings from FileStore")
        return data
    except Exception as e:
        logger.warning(f"Could not load embeddings from FileStore: {e}")
        return None
