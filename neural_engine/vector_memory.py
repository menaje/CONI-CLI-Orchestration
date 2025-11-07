"""
Vector Memory: 벡터 DB 기반 장기 기억 시스템

기능:
- 파일 임베딩 캐싱 및 검색
- 실행 컨텍스트 저장 및 유사 경험 검색
- 파일-작업 연관성 학습
- 파일 공동 출현 패턴 학습
- Run 종료 시 학습 데이터 자동 저장

Supabase pgvector 사용
"""

import hashlib
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

from .embedding_engine import UnifiedEmbeddingEngine, get_embedding_engine
from .supabase_client import SupabaseDB


class VectorMemory:
    """
    Vector Memory: Neural-CONI의 장기 기억 시스템

    Supabase pgvector를 사용하여:
    - 파일 임베딩 영구 저장
    - 과거 실행 컨텍스트 저장
    - 학습 패턴 축적 (Run 간 지식 전이)
    """

    def __init__(self, db: Optional[SupabaseDB] = None,
                 embedding_engine: Optional[UnifiedEmbeddingEngine] = None):
        """
        Args:
            db: Supabase DB 클라이언트 (None이면 자동 생성)
            embedding_engine: 임베딩 엔진 (None이면 전역 인스턴스 사용)
        """
        self.db = db or SupabaseDB()
        self.embedding_engine = embedding_engine or get_embedding_engine()

    # ==================== File Embeddings ====================

    def store_file_embedding(self, file_path: str, force_update: bool = False) -> Dict:
        """
        파일 임베딩 저장 (변경 감지 포함)

        Args:
            file_path: 파일 경로
            force_update: 강제 업데이트 (기본: False)

        Returns:
            저장된 임베딩 정보
        """
        # 파일 읽기
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 콘텐츠 해시 계산 (변경 감지)
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        # 기존 임베딩 확인
        existing = self.db.client.table("file_embeddings") \
            .select("id,content_hash") \
            .eq("file_path", file_path) \
            .execute()

        if existing.data and not force_update:
            if existing.data[0]["content_hash"] == content_hash:
                print(f"[VectorMemory] Cache hit: {file_path}")
                return existing.data[0]

        # 임베딩 계산
        embedding = self.embedding_engine.embed_text(content)

        # 파일 메타데이터
        file_stats = os.stat(file_path)
        file_type = os.path.splitext(file_path)[1].lstrip('.')
        line_count = content.count('\n') + 1

        # 데이터 준비
        data = {
            "file_path": file_path,
            "content_hash": content_hash,
            "embedding": embedding.tolist(),
            "file_type": file_type,
            "file_size": file_stats.st_size,
            "line_count": line_count,
            "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
        }

        # Upsert (insert or update)
        result = self.db.client.table("file_embeddings") \
            .upsert(data, on_conflict="file_path") \
            .execute()

        print(f"[VectorMemory] Stored embedding: {file_path} ({len(embedding)} dims)")
        return result.data[0] if result.data else data

    def get_file_embedding(self, file_path: str) -> Optional[np.ndarray]:
        """
        파일 임베딩 조회

        Args:
            file_path: 파일 경로

        Returns:
            임베딩 벡터 또는 None
        """
        result = self.db.client.table("file_embeddings") \
            .select("embedding") \
            .eq("file_path", file_path) \
            .execute()

        if result.data:
            return np.array(result.data[0]["embedding"])
        return None

    def search_similar_files(self, query_text: str,
                            match_threshold: float = 0.5,
                            match_count: int = 10) -> List[Dict]:
        """
        유사한 파일 검색

        Args:
            query_text: 검색 쿼리 (자연어)
            match_threshold: 최소 유사도 (0~1)
            match_count: 반환할 개수

        Returns:
            [{file_path, similarity, usage_count, ...}, ...]
        """
        # 쿼리 임베딩
        query_emb = self.embedding_engine.embed_text(query_text)

        # pgvector 함수 호출
        result = self.db.client.rpc("match_files", {
            "query_embedding": query_emb.tolist(),
            "match_threshold": match_threshold,
            "match_count": match_count
        }).execute()

        return result.data

    def update_file_usage(self, file_path: str, attention_weight: float):
        """
        파일 사용 통계 업데이트

        Args:
            file_path: 파일 경로
            attention_weight: Attention 가중치
        """
        # 현재 통계 조회
        existing = self.db.client.table("file_embeddings") \
            .select("usage_count,avg_attention_weight,last_used_at") \
            .eq("file_path", file_path) \
            .execute()

        if not existing.data:
            return

        current = existing.data[0]
        usage_count = current.get("usage_count", 0) + 1

        # Moving average for attention weight
        current_avg = current.get("avg_attention_weight", 0.0)
        new_avg = (current_avg * (usage_count - 1) + attention_weight) / usage_count

        # 업데이트
        self.db.client.table("file_embeddings") \
            .update({
                "usage_count": usage_count,
                "avg_attention_weight": new_avg,
                "last_used_at": datetime.now().isoformat()
            }) \
            .eq("file_path", file_path) \
            .execute()

    # ==================== Execution Contexts ====================

    def save_execution_context(self,
                               run_id: str,
                               task_id: str,
                               user_request: str,
                               quality_score: float,
                               success: bool,
                               selected_files: List[Tuple[str, float]],
                               execution_time: float = 0.0,
                               tokens_used: int = 0,
                               task_category: Optional[str] = None,
                               error_message: Optional[str] = None) -> int:
        """
        실행 컨텍스트 저장 (학습의 핵심!)

        Args:
            run_id: Run ID
            task_id: Task ID
            user_request: 사용자 요청 (자연어)
            quality_score: 품질 점수 (0~1)
            success: 성공 여부
            selected_files: [(file_path, attention_weight), ...]
            execution_time: 실행 시간 (초)
            tokens_used: 사용된 토큰 수
            task_category: 작업 카테고리 (자동 분류)
            error_message: 에러 메시지 (실패 시)

        Returns:
            context_id
        """
        # 요청 임베딩
        request_emb = self.embedding_engine.embed_text(user_request)

        # 자동 카테고리 분류
        if task_category is None:
            task_category = self._classify_task(user_request)

        # Execution context 저장
        context_data = {
            "run_id": run_id,
            "task_id": task_id,
            "user_request": user_request,
            "request_embedding": request_emb.tolist(),
            "task_category": task_category,
            "quality_score": quality_score,
            "execution_time": execution_time,
            "tokens_used": tokens_used,
            "success": success,
            "error_message": error_message
        }

        result = self.db.client.table("execution_contexts") \
            .insert(context_data) \
            .execute()

        context_id = result.data[0]["id"]

        # 선택된 파일들 저장
        if selected_files:
            self._save_selected_files(context_id, selected_files, quality_score)

            # 파일 사용 통계 업데이트
            for file_path, attention_weight in selected_files:
                self.update_file_usage(file_path, attention_weight)

            # 메타 학습 업데이트
            if success:
                self._update_file_task_affinity(selected_files, task_category,
                                                quality_score, success)
                self._update_co_occurrence(selected_files, quality_score)

        print(f"[VectorMemory] Saved execution context: {context_id} "
              f"(quality={quality_score:.2f}, files={len(selected_files)})")

        return context_id

    def search_similar_contexts(self,
                                query_text: str,
                                success_only: bool = True,
                                min_quality: float = 0.7,
                                match_count: int = 20) -> List[Dict]:
        """
        유사한 과거 실행 컨텍스트 검색

        Args:
            query_text: 현재 요청 (자연어)
            success_only: 성공한 것만
            min_quality: 최소 품질
            match_count: 반환할 개수

        Returns:
            [{context_id, run_id, user_request, similarity, quality_score, ...}, ...]
        """
        # 쿼리 임베딩
        query_emb = self.embedding_engine.embed_text(query_text)

        # pgvector 함수 호출
        result = self.db.client.rpc("match_contexts", {
            "query_embedding": query_emb.tolist(),
            "success_only": success_only,
            "min_quality": min_quality,
            "match_count": match_count
        }).execute()

        return result.data

    def get_selected_files_from_context(self, context_id: int) -> List[Dict]:
        """
        특정 컨텍스트에서 선택된 파일들 조회

        Args:
            context_id: Execution context ID

        Returns:
            [{file_path, attention_weight, was_useful, ...}, ...]
        """
        result = self.db.client.table("selected_files") \
            .select("*") \
            .eq("context_id", context_id) \
            .order("attention_rank") \
            .execute()

        return result.data

    # ==================== Learning & Recommendations ====================

    def get_learned_recommendations(self,
                                   query_text: str,
                                   success_only: bool = True,
                                   min_quality: float = 0.7,
                                   min_usefulness: float = 0.5,
                                   limit_count: int = 10) -> List[Dict]:
        """
        학습된 패턴 기반 파일 추천 (핵심 함수!)

        과거 유사한 요청에서 유용했던 파일들을 추천

        Args:
            query_text: 현재 요청 (자연어)
            success_only: 성공한 것만
            min_quality: 최소 품질
            min_usefulness: 최소 유용성
            limit_count: 반환할 개수

        Returns:
            [{file_path, recommendation_score, avg_attention_weight,
              avg_usefulness_score, times_selected, ...}, ...]
        """
        # 쿼리 임베딩
        query_emb = self.embedding_engine.embed_text(query_text)

        # pgvector 함수 호출 (핵심 학습 쿼리!)
        result = self.db.client.rpc("get_learned_file_recommendations", {
            "query_embedding": query_emb.tolist(),
            "success_only": success_only,
            "min_quality": min_quality,
            "min_usefulness": min_usefulness,
            "limit_count": limit_count
        }).execute()

        return result.data

    def get_category_recommendations(self,
                                    task_category: str,
                                    min_confidence: float = 0.3,
                                    limit_count: int = 10) -> List[Dict]:
        """
        작업 카테고리 기반 파일 추천

        Args:
            task_category: 작업 카테고리
            min_confidence: 최소 신뢰도
            limit_count: 반환할 개수

        Returns:
            [{file_path, learned_importance, avg_quality, ...}, ...]
        """
        result = self.db.client.rpc("recommend_files_for_category", {
            "category": task_category,
            "min_confidence": min_confidence,
            "limit_count": limit_count
        }).execute()

        return result.data

    def get_co_occurring_files(self,
                              target_file: str,
                              min_correlation: float = 0.3,
                              limit_count: int = 5) -> List[Dict]:
        """
        함께 사용되는 파일 조회

        Args:
            target_file: 대상 파일
            min_correlation: 최소 상관도
            limit_count: 반환할 개수

        Returns:
            [{related_file, co_occurrence_count, avg_quality_when_together, ...}, ...]
        """
        result = self.db.client.rpc("get_co_occurring_files", {
            "target_file": target_file,
            "min_correlation": min_correlation,
            "limit_count": limit_count
        }).execute()

        return result.data

    # ==================== Private Helper Methods ====================

    def _save_selected_files(self, context_id: int,
                            selected_files: List[Tuple[str, float]],
                            quality_score: float):
        """선택된 파일들 저장 (내부 메서드)"""
        data = []
        for rank, (file_path, attention_weight) in enumerate(selected_files, 1):
            # 유용성 판단: 품질이 높으면 유용했다고 판단
            was_useful = quality_score >= 0.7
            usefulness_score = quality_score * attention_weight

            data.append({
                "context_id": context_id,
                "file_path": file_path,
                "attention_weight": attention_weight,
                "attention_rank": rank,
                "was_useful": was_useful,
                "usefulness_score": usefulness_score
            })

        if data:
            self.db.client.table("selected_files").insert(data).execute()

    def _update_file_task_affinity(self, selected_files: List[Tuple[str, float]],
                                   task_category: str,
                                   quality_score: float,
                                   success: bool):
        """파일-작업 연관성 업데이트 (메타 학습)"""
        for file_path, attention_weight in selected_files:
            # 기존 데이터 조회
            existing = self.db.client.table("file_task_affinity") \
                .select("*") \
                .eq("file_path", file_path) \
                .eq("task_category", task_category) \
                .execute()

            if existing.data:
                # 업데이트
                current = existing.data[0]
                new_success_count = current["success_count"] + (1 if success else 0)
                new_failure_count = current["failure_count"] + (0 if success else 1)
                new_total = current["total_uses"] + 1

                # Moving averages
                new_avg_quality = (current["avg_quality"] * current["total_uses"] + quality_score) / new_total
                new_avg_attention = (current["avg_attention_weight"] * current["total_uses"] + attention_weight) / new_total

                # Learned importance (성공률 + 품질 + Attention)
                success_rate = new_success_count / new_total
                learned_importance = 0.4 * success_rate + 0.3 * new_avg_quality + 0.3 * new_avg_attention

                # Confidence (샘플 수 기반)
                confidence = min(1.0, new_total / 10.0)  # 10번 이상이면 완전 신뢰

                self.db.client.table("file_task_affinity") \
                    .update({
                        "success_count": new_success_count,
                        "failure_count": new_failure_count,
                        "total_uses": new_total,
                        "avg_quality": new_avg_quality,
                        "avg_attention_weight": new_avg_attention,
                        "learned_importance": learned_importance,
                        "confidence": confidence,
                        "last_updated": datetime.now().isoformat()
                    }) \
                    .eq("file_path", file_path) \
                    .eq("task_category", task_category) \
                    .execute()
            else:
                # 새로 생성
                learned_importance = 0.4 * (1 if success else 0) + 0.3 * quality_score + 0.3 * attention_weight
                confidence = 0.1  # 첫 샘플

                self.db.client.table("file_task_affinity") \
                    .insert({
                        "file_path": file_path,
                        "task_category": task_category,
                        "success_count": 1 if success else 0,
                        "failure_count": 0 if success else 1,
                        "total_uses": 1,
                        "avg_quality": quality_score,
                        "avg_attention_weight": attention_weight,
                        "learned_importance": learned_importance,
                        "confidence": confidence
                    }) \
                    .execute()

    def _update_co_occurrence(self, selected_files: List[Tuple[str, float]],
                             quality_score: float):
        """파일 공동 출현 업데이트"""
        file_paths = [f for f, _ in selected_files]

        # 모든 쌍에 대해 업데이트
        for i in range(len(file_paths)):
            for j in range(i + 1, len(file_paths)):
                file_a, file_b = sorted([file_paths[i], file_paths[j]])

                # 기존 데이터 조회
                existing = self.db.client.table("file_co_occurrence") \
                    .select("*") \
                    .eq("file_a", file_a) \
                    .eq("file_b", file_b) \
                    .execute()

                if existing.data:
                    # 업데이트
                    current = existing.data[0]
                    new_count = current["co_occurrence_count"] + 1
                    new_avg_quality = (current["avg_quality_when_together"] * current["co_occurrence_count"] + quality_score) / new_count

                    # Correlation strength (출현 빈도 + 품질)
                    correlation_strength = min(1.0, (new_count / 5.0) * new_avg_quality)

                    self.db.client.table("file_co_occurrence") \
                        .update({
                            "co_occurrence_count": new_count,
                            "avg_quality_when_together": new_avg_quality,
                            "correlation_strength": correlation_strength,
                            "last_occurred": datetime.now().isoformat()
                        }) \
                        .eq("file_a", file_a) \
                        .eq("file_b", file_b) \
                        .execute()
                else:
                    # 새로 생성
                    correlation_strength = 0.2 * quality_score  # 첫 샘플

                    self.db.client.table("file_co_occurrence") \
                        .insert({
                            "file_a": file_a,
                            "file_b": file_b,
                            "co_occurrence_count": 1,
                            "avg_quality_when_together": quality_score,
                            "correlation_strength": correlation_strength
                        }) \
                        .execute()

    def _classify_task(self, user_request: str) -> str:
        """
        사용자 요청을 자동 분류

        Args:
            user_request: 사용자 요청 (자연어)

        Returns:
            카테고리 (bug_fix, feature, refactor, test, docs, etc)
        """
        request_lower = user_request.lower()

        # 키워드 기반 간단한 분류
        if any(word in request_lower for word in ['bug', 'fix', 'error', '버그', '수정', '오류']):
            return "bug_fix"
        elif any(word in request_lower for word in ['feature', 'add', 'implement', '기능', '추가', '구현']):
            return "feature"
        elif any(word in request_lower for word in ['refactor', 'clean', 'improve', '리팩토링', '개선']):
            return "refactor"
        elif any(word in request_lower for word in ['test', 'testing', '테스트']):
            return "test"
        elif any(word in request_lower for word in ['doc', 'documentation', '문서']):
            return "docs"
        elif any(word in request_lower for word in ['analyze', 'understand', '분석', '이해']):
            return "analysis"
        else:
            return "general"


# ==================== Global Instance ====================

_global_vector_memory: Optional[VectorMemory] = None


def get_vector_memory() -> VectorMemory:
    """전역 VectorMemory 인스턴스 반환 (싱글톤)"""
    global _global_vector_memory
    if _global_vector_memory is None:
        _global_vector_memory = VectorMemory()
    return _global_vector_memory


if __name__ == "__main__":
    """테스트 코드"""
    print("=" * 60)
    print("Vector Memory Test")
    print("=" * 60)

    vm = VectorMemory()

    # 1. 파일 임베딩 저장 테스트
    print("\n[Test 1] Store file embedding")
    test_file = "neural_engine/attention.py"
    if os.path.exists(test_file):
        result = vm.store_file_embedding(test_file)
        print(f"  Stored: {result['file_path']}")
        print(f"  Hash: {result['content_hash'][:16]}...")

    # 2. 유사 파일 검색 테스트
    print("\n[Test 2] Search similar files")
    results = vm.search_similar_files("attention mechanism implementation", match_count=3)
    for r in results:
        print(f"  {r['file_path']} (similarity: {r['similarity']:.2f})")

    # 3. 실행 컨텍스트 저장 테스트
    print("\n[Test 3] Save execution context")
    context_id = vm.save_execution_context(
        run_id="test-001",
        task_id="tsk-01",
        user_request="Implement attention mechanism for file selection",
        quality_score=0.85,
        success=True,
        selected_files=[
            ("neural_engine/attention.py", 0.9),
            ("neural_engine/embedding_engine.py", 0.7)
        ]
    )
    print(f"  Context ID: {context_id}")

    # 4. 유사 컨텍스트 검색 테스트
    print("\n[Test 4] Search similar contexts")
    contexts = vm.search_similar_contexts(
        "Add new attention feature",
        match_count=3
    )
    for ctx in contexts:
        print(f"  {ctx['user_request'][:50]}... (similarity: {ctx['similarity']:.2f})")

    # 5. 학습된 추천 테스트
    print("\n[Test 5] Get learned recommendations")
    recommendations = vm.get_learned_recommendations(
        "Improve attention mechanism",
        limit_count=5
    )
    for rec in recommendations:
        print(f"  {rec['file_path']} (score: {rec['recommendation_score']:.3f})")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
