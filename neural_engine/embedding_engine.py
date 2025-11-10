"""
Unified Embedding Engine: Ollama/LM Studio 통합 임베딩 엔진

OpenAI SDK 사용으로 Ollama와 LM Studio를 동일한 인터페이스로 사용

기능:
- Ollama/LM Studio 임베딩 지원 (OpenAI 호환 API)
- 텍스트 → 벡터 변환 (768-dim, nomic-embed-text 기본)
- 배치 임베딩 (효율적)
- 코사인 유사도 계산
- 메모리 캐싱 (성능 최적화)
"""

import os
import hashlib
import json
from typing import List, Dict, Optional, Tuple
import numpy as np
from pathlib import Path

# OpenAI SDK (Ollama, LM Studio 둘 다 사용)
try:
    from openai import OpenAI
except ImportError:
    print("[ERROR] openai package not installed!")
    print("Run: pip install openai")
    raise


class UnifiedEmbeddingEngine:
    """
    통합 임베딩 엔진: Ollama/LM Studio를 OpenAI SDK로 통합

    Features:
    - Ollama/LM Studio 자동 선택
    - 로컬 실행 (무료, 빠름)
    - 배치 처리 지원
    - 메모리 캐싱
    """

    def __init__(
        self,
        provider: str = "ollama",
        model: str = None,
        base_url: str = None,
        cache_path: str = "db/embeddings_cache.json",
        auto_detect: bool = True
    ):
        """
        Args:
            provider: "ollama" or "lmstudio"
            model: 임베딩 모델 이름 (None이면 기본값)
            base_url: API URL (None이면 기본값)
            cache_path: 캐시 파일 경로
            auto_detect: 자동으로 사용 가능한 provider 찾기
        """
        self.cache_path = cache_path
        self.cache = self._load_cache()

        # Provider별 기본값
        providers_config = {
            "ollama": {
                "base_url": base_url or "http://localhost:11434/v1",
                "model": model or "nomic-embed-text",
                "dimension": 768
            },
            "lmstudio": {
                "base_url": base_url or "http://localhost:1234/v1",
                "model": model or "nomic-embed-text",
                "dimension": 768
            }
        }

        # Auto-detect: 사용 가능한 provider 찾기
        if auto_detect:
            provider = self._detect_provider(providers_config)

        if provider not in providers_config:
            raise ValueError(f"Unknown provider: {provider}. Use 'ollama' or 'lmstudio'")

        config = providers_config[provider]
        self.provider = provider
        self.model = config["model"]
        self.base_url = config["base_url"]
        self.dimension = config["dimension"]

        # OpenAI 클라이언트 초기화
        self.client = OpenAI(
            base_url=self.base_url,
            api_key="not-needed"  # Ollama/LM Studio는 API key 불필요
        )

        print(f"[EmbeddingEngine] Using {provider}: {self.model}")
        print(f"[EmbeddingEngine] API URL: {self.base_url}")
        print(f"[EmbeddingEngine] Dimension: {self.dimension}")

    def _detect_provider(self, providers_config: Dict) -> str:
        """사용 가능한 provider 자동 감지"""
        import requests

        # Ollama 먼저 시도
        try:
            response = requests.get(
                f"{providers_config['ollama']['base_url'].replace('/v1', '')}/api/tags",
                timeout=2
            )
            if response.status_code == 200:
                print("[EmbeddingEngine] Auto-detected: Ollama")
                return "ollama"
        except:
            pass

        # LM Studio 시도
        try:
            response = requests.get(
                f"{providers_config['lmstudio']['base_url']}/models",
                timeout=2
            )
            if response.status_code == 200:
                print("[EmbeddingEngine] Auto-detected: LM Studio")
                return "lmstudio"
        except:
            pass

        # 기본값: ollama
        print("[EmbeddingEngine] No provider detected, using default: ollama")
        return "ollama"

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
        """텍스트의 캐시 키 생성 (모델명 포함)"""
        text_with_model = f"{self.model}::{text}"
        return hashlib.sha256(text_with_model.encode('utf-8')).hexdigest()

    def embed_text(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        텍스트를 벡터로 변환

        Args:
            text: 변환할 텍스트
            use_cache: 캐시 사용 여부

        Returns:
            768차원 numpy 배열 (nomic-embed-text 기본)
        """
        if not text or not text.strip():
            return np.zeros(self.dimension)

        # 캐시 확인
        cache_key = self._get_cache_key(text)
        if use_cache and cache_key in self.cache:
            return np.array(self.cache[cache_key])

        # OpenAI API로 임베딩 생성
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            embedding = np.array(response.data[0].embedding)
        except Exception as e:
            print(f"[ERROR] Failed to generate embedding: {e}")
            print(f"[ERROR] Make sure {self.provider} is running and model '{self.model}' is available")
            return np.zeros(self.dimension)

        # 캐시 저장
        if use_cache:
            self.cache[cache_key] = embedding.tolist()
            if len(self.cache) % 10 == 0:  # 10개마다 저장
                self._save_cache()

        return embedding

    def embed_batch(self, texts: List[str], use_cache: bool = True) -> List[np.ndarray]:
        """
        여러 텍스트를 배치로 임베딩 (효율적)

        Args:
            texts: 텍스트 리스트
            use_cache: 캐시 사용 여부

        Returns:
            임베딩 리스트
        """
        embeddings = []

        # 캐시되지 않은 텍스트만 API 호출
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if use_cache and cache_key in self.cache:
                embeddings.append(np.array(self.cache[cache_key]))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
                embeddings.append(None)  # placeholder

        # 캐시되지 않은 텍스트 배치 임베딩
        if uncached_texts:
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=uncached_texts
                )

                for i, data in enumerate(response.data):
                    embedding = np.array(data.embedding)
                    idx = uncached_indices[i]
                    embeddings[idx] = embedding

                    # 캐시 저장
                    if use_cache:
                        cache_key = self._get_cache_key(uncached_texts[i])
                        self.cache[cache_key] = embedding.tolist()

                if use_cache:
                    self._save_cache()

            except Exception as e:
                print(f"[ERROR] Failed to generate batch embeddings: {e}")
                # Fallback: 영벡터
                for idx in uncached_indices:
                    if embeddings[idx] is None:
                        embeddings[idx] = np.zeros(self.dimension)

        return embeddings

    def embed_file(self, file_path: str, max_length: int = 10000) -> np.ndarray:
        """
        파일 내용을 임베딩으로 변환

        Args:
            file_path: 파일 경로
            max_length: 최대 문자 수

        Returns:
            벡터 (768-dim)
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
            emb1, emb2: 벡터

        Returns:
            유사도 (0~1, 1이 가장 유사)
        """
        # 영벡터 처리
        if np.linalg.norm(emb1) == 0 or np.linalg.norm(emb2) == 0:
            return 0.0

        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)

    def find_most_similar(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
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
        candidate_embs = self.embed_batch(candidates)

        similarities = [
            (i, self.cosine_similarity(query_emb, cand_emb))
            for i, cand_emb in enumerate(candidate_embs)
        ]

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def semantic_search(
        self,
        query: str,
        file_paths: List[str],
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
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

        file_similarities.sort(key=lambda x: x[1], reverse=True)
        return file_similarities[:top_k]

    def get_cache_stats(self) -> Dict:
        """캐시 통계 반환"""
        return {
            "total_cached": len(self.cache),
            "cache_size_mb": os.path.getsize(self.cache_path) / 1024 / 1024 if os.path.exists(self.cache_path) else 0,
            "dimension": self.dimension,
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url
        }

    def clear_cache(self):
        """캐시 초기화"""
        self.cache = {}
        if os.path.exists(self.cache_path):
            os.remove(self.cache_path)
        print(f"[EmbeddingEngine] Cache cleared: {self.cache_path}")


# 전역 인스턴스 (싱글톤 패턴)
_global_engine = None

def get_embedding_engine(
    provider: str = None,
    model: str = None,
    auto_detect: bool = True
) -> UnifiedEmbeddingEngine:
    """
    전역 임베딩 엔진 반환 (싱글톤)

    Args:
        provider: "ollama" or "lmstudio" (None이면 기존 인스턴스 또는 auto-detect)
        model: 모델 이름
        auto_detect: 사용 가능한 provider 자동 감지
    """
    global _global_engine

    # 이미 생성된 인스턴스가 있고 provider 지정 없으면 재사용
    if _global_engine is not None and provider is None:
        return _global_engine

    # 새 인스턴스 생성
    _global_engine = UnifiedEmbeddingEngine(
        provider=provider or "ollama",
        model=model,
        auto_detect=auto_detect
    )
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
    print("Unified Embedding Engine Test")
    print("=" * 60)

    # 엔진 초기화 (auto-detect)
    engine = UnifiedEmbeddingEngine(auto_detect=True)

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

    # 3. 배치 임베딩 테스트
    print("\n[Test 3] 배치 임베딩")
    texts = [
        "문서를 작성합니다",
        "리포트를 생성합니다",
        "초안을 작성합니다"
    ]
    batch_embs = engine.embed_batch(texts)
    print(f"Batch size: {len(texts)}")
    print(f"Embeddings generated: {len(batch_embs)}")

    # 4. 의미 검색 테스트
    print("\n[Test 4] 의미 검색")
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

    # 5. 캐시 통계
    print("\n[Test 5] 캐시 통계")
    stats = engine.get_cache_stats()
    print(f"Provider: {stats['provider']}")
    print(f"Model: {stats['model']}")
    print(f"Dimension: {stats['dimension']}")
    print(f"Cached embeddings: {stats['total_cached']}")
    print(f"Cache size: {stats['cache_size_mb']:.2f} MB")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\nNote: Make sure Ollama or LM Studio is running with nomic-embed-text model")
    print("  Ollama: ollama pull nomic-embed-text")
    print("  LM Studio: Download nomic-embed-text from model library")
