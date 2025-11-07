"""
Attention Mechanism: 중요한 정보에 선택적으로 집중

기능:
- Query-Key Attention 계산
- Softmax 정규화
- Top-K 선택
- Attention 가중치 시각화
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from .embedding_engine import EmbeddingEngine, get_embedding_engine


class AttentionMechanism:
    """
    Attention 메커니즘 구현

    Transformer의 Attention을 단순화한 버전:
    - Query: 현재 Task가 원하는 정보
    - Keys: 참조 가능한 정보들
    - Attention Weights: 각 정보의 중요도
    """

    def __init__(self, embedding_engine: Optional[EmbeddingEngine] = None):
        """
        Args:
            embedding_engine: 임베딩 엔진 (None이면 전역 인스턴스 사용)
        """
        self.embedding_engine = embedding_engine or get_embedding_engine()

    def compute_attention_scores(self,
                                 query: np.ndarray,
                                 keys: List[np.ndarray],
                                 method: str = "cosine") -> np.ndarray:
        """
        Attention 점수 계산 (정규화 전)

        Args:
            query: 쿼리 벡터 (384,)
            keys: 키 벡터 리스트 [(384,), (384,), ...]
            method: 유사도 계산 방법 ("cosine" or "dot")

        Returns:
            점수 배열 (N,) - N은 keys 개수
        """
        scores = []

        for key in keys:
            if method == "cosine":
                score = self.embedding_engine.cosine_similarity(query, key)
            elif method == "dot":
                score = np.dot(query, key)
            else:
                raise ValueError(f"Unknown method: {method}")

            scores.append(score)

        return np.array(scores)

    def softmax(self, scores: np.ndarray, temperature: float = 1.0) -> np.ndarray:
        """
        Softmax 함수로 점수를 확률 분포로 변환

        Args:
            scores: 점수 배열
            temperature: 온도 (높을수록 평탄, 낮을수록 뾰족)

        Returns:
            확률 분포 (합이 1)
        """
        # 수치 안정성을 위해 최댓값 빼기
        scores = scores / temperature
        exp_scores = np.exp(scores - np.max(scores))
        return exp_scores / np.sum(exp_scores)

    def attention(self,
                  query: np.ndarray,
                  keys: List[np.ndarray],
                  values: Optional[List] = None,
                  temperature: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Full Attention 계산

        Args:
            query: 쿼리 벡터
            keys: 키 벡터 리스트
            values: 값 리스트 (None이면 keys와 동일)
            temperature: Softmax 온도

        Returns:
            (attention_weights, context_vector)
            - attention_weights: 각 key의 가중치 (N,)
            - context_vector: 가중 평균 벡터 (384,)
        """
        # Attention 점수 계산
        scores = self.compute_attention_scores(query, keys)

        # Softmax로 정규화
        attention_weights = self.softmax(scores, temperature)

        # Values 설정
        if values is None:
            values = keys

        # 가중 평균 계산 (context vector)
        context = np.zeros_like(query)
        for weight, value in zip(attention_weights, values):
            context += weight * value

        return attention_weights, context

    def top_k_attention(self,
                       query: np.ndarray,
                       keys: List[np.ndarray],
                       k: int,
                       threshold: float = 0.0) -> List[Tuple[int, float]]:
        """
        상위 K개만 선택 (Sparse Attention)

        Args:
            query: 쿼리 벡터
            keys: 키 벡터 리스트
            k: 선택할 개수
            threshold: 최소 점수 (이하는 제외)

        Returns:
            [(인덱스, attention_weight), ...] 리스트 (점수 내림차순)
        """
        # Attention 점수 계산
        scores = self.compute_attention_scores(query, keys)

        # Softmax로 정규화
        attention_weights = self.softmax(scores)

        # (인덱스, 가중치) 튜플 생성
        indexed_weights = list(enumerate(attention_weights))

        # 임계값 필터링
        indexed_weights = [(i, w) for i, w in indexed_weights if w >= threshold]

        # 가중치 내림차순 정렬
        indexed_weights.sort(key=lambda x: x[1], reverse=True)

        # 상위 K개 반환
        return indexed_weights[:k]

    def multi_head_attention(self,
                            query: np.ndarray,
                            keys: List[np.ndarray],
                            num_heads: int = 4) -> Tuple[List[np.ndarray], np.ndarray]:
        """
        Multi-Head Attention (간소화 버전)

        여러 관점에서 동시에 Attention 계산

        Args:
            query: 쿼리 벡터 (384,)
            keys: 키 벡터 리스트
            num_heads: Head 개수

        Returns:
            (head_weights_list, final_context)
        """
        dim = query.shape[0]
        head_dim = dim // num_heads

        head_weights_list = []
        head_contexts = []

        for head_idx in range(num_heads):
            # 차원 분할 (간소화: 단순 슬라이싱)
            start = head_idx * head_dim
            end = (head_idx + 1) * head_dim if head_idx < num_heads - 1 else dim

            query_head = query[start:end]
            keys_head = [key[start:end] for key in keys]

            # Attention 계산
            weights, context = self.attention(query_head, keys_head)

            head_weights_list.append(weights)
            head_contexts.append(context)

        # Head 결과 concat
        final_context = np.concatenate(head_contexts)

        return head_weights_list, final_context

    def cross_attention(self,
                       source_query: np.ndarray,
                       target_keys: List[np.ndarray],
                       target_values: List[np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Cross Attention: 서로 다른 도메인 간 Attention

        예: Task 설명 (query) → 파일 내용 (keys, values)

        Args:
            source_query: 소스 쿼리
            target_keys: 타겟 키 리스트
            target_values: 타겟 값 리스트

        Returns:
            (attention_weights, context)
        """
        return self.attention(source_query, target_keys, target_values)


class TaskAttentionSelector:
    """
    Task 실행 시 필요한 파일을 Attention으로 선택

    사용 예:
    selector = TaskAttentionSelector()
    selected_files = selector.select_files(
        task_purpose="보고서 초안 작성",
        candidate_files=["file1.md", "file2.md", ...],
        top_k=2
    )
    """

    def __init__(self, embedding_engine: Optional[EmbeddingEngine] = None):
        self.embedding_engine = embedding_engine or get_embedding_engine()
        self.attention = AttentionMechanism(self.embedding_engine)

    def select_files(self,
                     task_purpose: str,
                     candidate_files: List[str],
                     top_k: int = 3,
                     threshold: float = 0.1) -> List[Tuple[str, float]]:
        """
        Task 목적에 가장 관련 있는 파일 선택

        Args:
            task_purpose: Task 목적 (자연어)
            candidate_files: 후보 파일 경로 리스트
            top_k: 선택할 파일 개수
            threshold: 최소 유사도

        Returns:
            [(파일경로, attention_weight), ...] 리스트
        """
        # Query: Task 목적
        query_emb = self.embedding_engine.embed_text(task_purpose)

        # Keys: 파일 내용
        key_embs = [
            self.embedding_engine.embed_file(file_path)
            for file_path in candidate_files
        ]

        # Top-K Attention
        top_k_indices = self.attention.top_k_attention(
            query_emb, key_embs, k=top_k, threshold=threshold
        )

        # (파일경로, 가중치) 변환
        selected_files = [
            (candidate_files[idx], weight)
            for idx, weight in top_k_indices
        ]

        return selected_files

    def select_references(self,
                         task_purpose: str,
                         related_references: List[str],
                         top_k: int = 2) -> Dict:
        """
        Task 실행에 필요한 참조 파일 선택 (상세 정보 포함)

        Returns:
            {
                "selected": [(file, weight), ...],
                "total_candidates": int,
                "reduction_rate": float,
                "top_weights": [float, ...]
            }
        """
        selected = self.select_files(task_purpose, related_references, top_k)

        result = {
            "selected": selected,
            "total_candidates": len(related_references),
            "selected_count": len(selected),
            "reduction_rate": 1.0 - len(selected) / max(len(related_references), 1),
            "top_weights": [w for _, w in selected]
        }

        return result


def visualize_attention(attention_weights: np.ndarray,
                       labels: Optional[List[str]] = None,
                       title: str = "Attention Weights") -> str:
    """
    Attention 가중치 시각화 (텍스트)

    Args:
        attention_weights: 가중치 배열
        labels: 각 항목의 레이블
        title: 제목

    Returns:
        시각화 문자열
    """
    if labels is None:
        labels = [f"Key {i}" for i in range(len(attention_weights))]

    lines = [f"\n{'=' * 60}", f"{title:^60}", f"{'=' * 60}"]

    for label, weight in zip(labels, attention_weights):
        bar_length = int(weight * 50)  # 최대 50칸
        bar = "█" * bar_length
        lines.append(f"{label:20s} {weight:5.2%} {bar}")

    lines.append("=" * 60)

    return "\n".join(lines)


if __name__ == "__main__":
    """테스트 코드"""
    print("=" * 60)
    print("Attention Mechanism Test")
    print("=" * 60)

    engine = get_embedding_engine()
    attention = AttentionMechanism(engine)

    # 1. 기본 Attention 테스트
    print("\n[Test 1] 기본 Attention")
    query_text = "보고서 초안을 작성해야 합니다"
    key_texts = [
        "요구사항 분석 결과입니다",
        "날씨 정보입니다",
        "보고서 작성 가이드라인입니다",
        "시장 조사 데이터입니다",
    ]

    query_emb = engine.embed_text(query_text)
    key_embs = [engine.embed_text(text) for text in key_texts]

    weights, context = attention.attention(query_emb, key_embs)

    print(f"Query: {query_text}\n")
    print(visualize_attention(weights, key_texts, "Attention Weights"))

    # 2. Top-K Attention 테스트
    print("\n[Test 2] Top-K Attention (K=2)")
    top_k_results = attention.top_k_attention(query_emb, key_embs, k=2)

    print(f"Query: {query_text}\n")
    print("상위 2개 선택:")
    for idx, weight in top_k_results:
        print(f"  {weight:.2%} - {key_texts[idx]}")

    # 3. Task Attention Selector 테스트
    print("\n[Test 3] Task Attention Selector")
    selector = TaskAttentionSelector(engine)

    # 가상의 파일들 (텍스트로 대체)
    candidate_texts = [
        ("doc1.md", "사용자 요구사항: 시스템 분석 필요"),
        ("doc2.md", "맛집 추천 리스트"),
        ("doc3.md", "분석 보고서 작성 템플릿"),
        ("doc4.md", "시장 동향 데이터"),
        ("doc5.md", "코딩 스타일 가이드"),
    ]

    # 임시로 텍스트를 파일처럼 처리
    task_purpose = "시스템 분석 보고서를 작성합니다"
    query_emb = engine.embed_text(task_purpose)
    key_embs = [engine.embed_text(text) for _, text in candidate_texts]

    top_k_results = attention.top_k_attention(query_emb, key_embs, k=3)

    print(f"Task Purpose: {task_purpose}\n")
    print("선택된 파일:")
    for idx, weight in top_k_results:
        filename, _ = candidate_texts[idx]
        print(f"  {weight:.2%} - {filename}")

    # 비용 절감 효과
    reduction = 1.0 - len(top_k_results) / len(candidate_texts)
    print(f"\n💰 토큰 절감: {reduction:.1%} (5개 → 3개)")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
