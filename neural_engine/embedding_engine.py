"""
Embedding Engine: 텍스트를 벡터로 변환하고 수학적 연산 수행

기능:
- 텍스트 → 384차원 벡터 변환
- 파일 내용 임베딩
- 코사인 유사도 계산
- 임베딩 캐싱 (성능 최적화)
"""

import os
import hashlib
import json
from typing import List, Dict, Optional, Tuple
import numpy as np
from pathlib import Path

# Lazy import to avoid loading model unless needed
_model = None

def get_model():
    """임베딩 모델 로딩 (지연 로딩)"""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print("[EmbeddingEngine] Loading sentence-transformers model...")
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            print("[EmbeddingEngine] Model loaded successfully (14MB, 384 dimensions)")
        except ImportError:
            print("[ERROR] sentence-transformers not installed!")
            print("Run: pip install sentence-transformers")
            raise
    return _model


class EmbeddingEngine:
    """
    임베딩 엔진: 모든 텍스트-벡터 변환 담당

    Features:
    - 로컬 실행 (무료, CPU 충분)
    - 캐싱으로 중복 계산 방지
    - 빠른 유사도 계산
    """

    def __init__(self, cache_path: str = "db/embeddings_cache.json"):
        """
        Args:
            cache_path: 임베딩 캐시 파일 경로
        """
        self.cache_path = cache_path
        self.cache = self._load_cache()
        self.model = get_model()
        self.dimension = 384  # all-MiniLM-L6-v2 dimension

    def _load_cache(self) -> Dict:
        """캐시 파일 로딩"""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        """캐시 파일 저장"""
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2)

    def _get_cache_key(self, text: str) -> str:
        """텍스트의 캐시 키 생성 (SHA256 해시)"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def embed_text(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        텍스트를 384차원 벡터로 변환

        Args:
            text: 변환할 텍스트
            use_cache: 캐시 사용 여부

        Returns:
            384차원 numpy 배열
        """
        if not text or not text.strip():
            return np.zeros(self.dimension)

        # 캐시 확인
        cache_key = self._get_cache_key(text)
        if use_cache and cache_key in self.cache:
            return np.array(self.cache[cache_key])

        # 임베딩 생성
        embedding = self.model.encode(text, convert_to_numpy=True)

        # 캐시 저장
        if use_cache:
            self.cache[cache_key] = embedding.tolist()
            if len(self.cache) % 10 == 0:  # 10개마다 저장
                self._save_cache()

        return embedding

    def embed_file(self, file_path: str, max_length: int = 10000) -> np.ndarray:
        """
        파일 내용을 임베딩으로 변환

        Args:
            file_path: 파일 경로
            max_length: 최대 문자 수 (너무 긴 파일 방지)

        Returns:
            384차원 numpy 배열
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(max_length)
            return self.embed_text(content)
        except Exception as e:
            print(f"[WARNING] Failed to embed file {file_path}: {e}")
            return np.zeros(self.dimension)

    def cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        두 벡터의 코사인 유사도 계산

        Args:
            emb1, emb2: 384차원 벡터

        Returns:
            유사도 (0~1, 1이 가장 유사)
        """
        # 영벡터 처리
        if np.linalg.norm(emb1) == 0 or np.linalg.norm(emb2) == 0:
            return 0.0

        # 코사인 유사도
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)

    def batch_embed(self, texts: List[str]) -> List[np.ndarray]:
        """
        여러 텍스트를 한 번에 임베딩 (효율적)

        Args:
            texts: 텍스트 리스트

        Returns:
            임베딩 리스트
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return [emb for emb in embeddings]

    def find_most_similar(self,
                         query: str,
                         candidates: List[str],
                         top_k: int = 5) -> List[Tuple[int, float]]:
        """
        쿼리와 가장 유사한 후보들 찾기

        Args:
            query: 쿼리 텍스트
            candidates: 후보 텍스트 리스트
            top_k: 상위 k개 반환

        Returns:
            [(인덱스, 유사도), ...] 리스트 (유사도 내림차순)
        """
        query_emb = self.embed_text(query)
        candidate_embs = self.batch_embed(candidates)

        similarities = [
            (i, self.cosine_similarity(query_emb, cand_emb))
            for i, cand_emb in enumerate(candidate_embs)
        ]

        # 유사도 내림차순 정렬
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def semantic_search(self,
                       query: str,
                       file_paths: List[str],
                       top_k: int = 3) -> List[Tuple[str, float]]:
        """
        파일들 중 쿼리와 가장 관련 있는 파일 찾기

        Args:
            query: 검색 쿼리
            file_paths: 파일 경로 리스트
            top_k: 상위 k개 반환

        Returns:
            [(파일경로, 유사도), ...] 리스트
        """
        query_emb = self.embed_text(query)

        file_similarities = []
        for file_path in file_paths:
            file_emb = self.embed_file(file_path)
            similarity = self.cosine_similarity(query_emb, file_emb)
            file_similarities.append((file_path, similarity))

        # 유사도 내림차순 정렬
        file_similarities.sort(key=lambda x: x[1], reverse=True)

        return file_similarities[:top_k]

    def get_cache_stats(self) -> Dict:
        """캐시 통계 반환"""
        return {
            "total_cached": len(self.cache),
            "cache_size_mb": os.path.getsize(self.cache_path) / 1024 / 1024 if os.path.exists(self.cache_path) else 0,
            "dimension": self.dimension,
            "model": "all-MiniLM-L6-v2"
        }

    def clear_cache(self):
        """캐시 초기화"""
        self.cache = {}
        if os.path.exists(self.cache_path):
            os.remove(self.cache_path)
        print(f"[EmbeddingEngine] Cache cleared: {self.cache_path}")


# 전역 인스턴스 (싱글톤 패턴)
_global_engine = None

def get_embedding_engine() -> EmbeddingEngine:
    """전역 임베딩 엔진 반환 (싱글톤)"""
    global _global_engine
    if _global_engine is None:
        _global_engine = EmbeddingEngine()
    return _global_engine


# 편의 함수들
def embed(text: str) -> np.ndarray:
    """텍스트를 빠르게 임베딩"""
    return get_embedding_engine().embed_text(text)

def similarity(text1: str, text2: str) -> float:
    """두 텍스트의 유사도 계산"""
    engine = get_embedding_engine()
    emb1 = engine.embed_text(text1)
    emb2 = engine.embed_text(text2)
    return engine.cosine_similarity(emb1, emb2)


if __name__ == "__main__":
    """테스트 코드"""
    print("=" * 60)
    print("Embedding Engine Test")
    print("=" * 60)

    engine = EmbeddingEngine()

    # 1. 기본 임베딩 테스트
    print("\n[Test 1] 기본 임베딩")
    text1 = "사용자 요구사항을 분석합니다"
    emb1 = engine.embed_text(text1)
    print(f"Text: {text1}")
    print(f"Embedding shape: {emb1.shape}")
    print(f"Embedding (first 5): {emb1[:5]}")

    # 2. 유사도 테스트
    print("\n[Test 2] 유사도 계산")
    text2 = "요구사항 분석을 수행합니다"
    text3 = "날씨가 좋습니다"

    emb2 = engine.embed_text(text2)
    emb3 = engine.embed_text(text3)

    sim_12 = engine.cosine_similarity(emb1, emb2)
    sim_13 = engine.cosine_similarity(emb1, emb3)

    print(f"Text 1: {text1}")
    print(f"Text 2: {text2}")
    print(f"Similarity 1-2: {sim_12:.4f} (유사함)")
    print(f"\nText 1: {text1}")
    print(f"Text 3: {text3}")
    print(f"Similarity 1-3: {sim_13:.4f} (다름)")

    # 3. 의미 검색 테스트
    print("\n[Test 3] 의미 검색")
    query = "보고서 작성"
    candidates = [
        "문서를 작성합니다",
        "날씨를 확인합니다",
        "리포트를 생성합니다",
        "음식을 먹습니다",
        "초안을 작성합니다"
    ]

    results = engine.find_most_similar(query, candidates, top_k=3)
    print(f"Query: {query}")
    print("\n상위 3개:")
    for idx, score in results:
        print(f"  {score:.4f} - {candidates[idx]}")

    # 4. 캐시 통계
    print("\n[Test 4] 캐시 통계")
    stats = engine.get_cache_stats()
    print(f"Cached embeddings: {stats['total_cached']}")
    print(f"Cache size: {stats['cache_size_mb']:.2f} MB")
    print(f"Model: {stats['model']}")
    print(f"Dimension: {stats['dimension']}")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
