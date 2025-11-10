#!/usr/bin/env python3
"""
Vector Memory 테스트 스크립트

Supabase pgvector 기능 테스트:
- 파일 임베딩 저장/검색
- 실행 컨텍스트 저장/검색
- 학습 기반 추천
- EnhancedAttention 테스트
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from neural_engine.vector_memory import VectorMemory, get_vector_memory
from neural_engine.attention import SmartFileSelector, EnhancedAttention
from neural_engine.embedding_engine import get_embedding_engine


def test_file_embeddings():
    """파일 임베딩 캐싱 테스트"""
    print("\n" + "=" * 60)
    print("Test 1: File Embeddings")
    print("=" * 60)

    vm = get_vector_memory()

    # 테스트 파일들
    test_files = [
        "neural_engine/attention.py",
        "neural_engine/embedding_engine.py",
        "neural_engine/vector_memory.py",
        "neural_engine/weight_manager.py"
    ]

    # 파일 임베딩 저장
    print("\n[1-1] Storing file embeddings...")
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                result = vm.store_file_embedding(file_path)
                print(f"  ✓ {file_path}")
                print(f"    Hash: {result['content_hash'][:16]}...")
                print(f"    Type: {result['file_type']}")
            except Exception as e:
                print(f"  ✗ {file_path}: {e}")

    # 유사 파일 검색
    print("\n[1-2] Searching similar files...")
    queries = [
        "attention mechanism for neural networks",
        "embedding and vector similarity",
        "weight learning and backpropagation"
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = vm.search_similar_files(query, match_count=3)
        for r in results:
            print(f"  {r['similarity']:.3f} - {r['file_path']}")


def test_execution_contexts():
    """실행 컨텍스트 저장/검색 테스트"""
    print("\n" + "=" * 60)
    print("Test 2: Execution Contexts")
    print("=" * 60)

    vm = get_vector_memory()

    # 테스트 실행 컨텍스트들
    test_contexts = [
        {
            "run_id": "test-vec-001",
            "task_id": "tsk-01",
            "user_request": "Implement attention mechanism for file selection",
            "quality_score": 0.85,
            "success": True,
            "selected_files": [
                ("neural_engine/attention.py", 0.9),
                ("neural_engine/embedding_engine.py", 0.7)
            ]
        },
        {
            "run_id": "test-vec-002",
            "task_id": "tsk-02",
            "user_request": "Add vector database for long-term memory",
            "quality_score": 0.90,
            "success": True,
            "selected_files": [
                ("neural_engine/vector_memory.py", 0.95),
                ("db_templates/supabase_schema.sql", 0.8),
                ("neural_engine/supabase_client.py", 0.75)
            ]
        },
        {
            "run_id": "test-vec-003",
            "task_id": "tsk-03",
            "user_request": "Improve weight learning algorithm",
            "quality_score": 0.78,
            "success": True,
            "selected_files": [
                ("neural_engine/weight_manager.py", 0.92),
                ("neural_engine/neural_task.py", 0.7)
            ]
        }
    ]

    # 실행 컨텍스트 저장
    print("\n[2-1] Saving execution contexts...")
    for ctx in test_contexts:
        try:
            context_id = vm.save_execution_context(**ctx)
            print(f"  ✓ Context {context_id}: {ctx['user_request'][:50]}...")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    # 유사 컨텍스트 검색
    print("\n[2-2] Searching similar contexts...")
    search_queries = [
        "How to implement attention for neural networks?",
        "Add database integration for persistent storage",
        "Optimize learning algorithm performance"
    ]

    for query in search_queries:
        print(f"\nQuery: '{query}'")
        results = vm.search_similar_contexts(query, match_count=2)
        for r in results:
            print(f"  {r['similarity']:.3f} (Q={r['quality_score']:.2f}) - {r['user_request'][:50]}...")


def test_learned_recommendations():
    """학습 기반 추천 테스트"""
    print("\n" + "=" * 60)
    print("Test 3: Learned Recommendations")
    print("=" * 60)

    vm = get_vector_memory()

    # 추천 쿼리들
    test_queries = [
        "I need to add attention mechanism features",
        "Integrate database for storing results",
        "Improve the learning algorithm"
    ]

    print("\n[3-1] Getting learned recommendations...")
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            recommendations = vm.get_learned_recommendations(
                query,
                success_only=True,
                min_quality=0.7,
                limit_count=5
            )

            if recommendations:
                for rec in recommendations:
                    print(f"  {rec['recommendation_score']:.3f} - {rec['file_path']}")
                    print(f"    Used {rec['times_selected']}x, "
                          f"Avg attention: {rec['avg_attention_weight']:.2f}, "
                          f"Usefulness: {rec['avg_usefulness_score']:.2f}")
            else:
                print("  (No recommendations yet - need more data)")
        except Exception as e:
            print(f"  ✗ Error: {e}")


def test_enhanced_attention():
    """Enhanced Attention 테스트"""
    print("\n" + "=" * 60)
    print("Test 4: Enhanced Attention with Memory")
    print("=" * 60)

    # SmartFileSelector 생성
    selector = SmartFileSelector(enable_memory=True)

    # 후보 파일들
    candidate_files = [
        "neural_engine/attention.py",
        "neural_engine/embedding_engine.py",
        "neural_engine/vector_memory.py",
        "neural_engine/weight_manager.py",
        "neural_engine/neural_task.py",
        "neural_engine/supabase_client.py"
    ]

    # 필터: 존재하는 파일만
    candidate_files = [f for f in candidate_files if os.path.exists(f)]

    # 테스트 쿼리들
    test_queries = [
        "Implement attention for selecting relevant files",
        "Add vector database integration",
        "Improve weight learning"
    ]

    print("\n[4-1] File selection with memory...")
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            selected = selector.select_files(
                task_purpose=query,
                candidate_files=candidate_files,
                top_k=3
            )

            for file_path, score in selected:
                print(f"  {score:.3f} - {file_path}")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    # 실행 결과 저장 (학습)
    print("\n[4-2] Saving execution result for learning...")
    try:
        selector.save_execution_result(
            run_id="test-vec-004",
            task_id="tsk-04",
            user_request=test_queries[0],
            selected_files=[
                ("neural_engine/attention.py", 0.85),
                ("neural_engine/embedding_engine.py", 0.72)
            ],
            quality_score=0.88,
            success=True,
            execution_time=2.5
        )
        print("  ✓ Execution result saved")
    except Exception as e:
        print(f"  ✗ Error: {e}")


def test_explanation():
    """설명 기능 테스트"""
    print("\n" + "=" * 60)
    print("Test 5: Selection Explanation")
    print("=" * 60)

    vm = get_vector_memory()
    embedding_engine = get_embedding_engine()

    try:
        enhanced = EnhancedAttention(embedding_engine, vm)

        candidate_files = [
            "neural_engine/attention.py",
            "neural_engine/embedding_engine.py",
            "neural_engine/vector_memory.py"
        ]
        candidate_files = [f for f in candidate_files if os.path.exists(f)]

        result = enhanced.select_files_with_explanation(
            "Add attention mechanism features",
            candidate_files,
            top_k=2
        )

        print("\n" + result['explanation'])
    except Exception as e:
        print(f"✗ Error: {e}")


def test_statistics():
    """통계 및 메타 정보 테스트"""
    print("\n" + "=" * 60)
    print("Test 6: Statistics")
    print("=" * 60)

    vm = get_vector_memory()

    # 파일 사용 통계
    print("\n[6-1] File usage statistics...")
    try:
        result = vm.db.client.table("file_embeddings") \
            .select("file_path,usage_count,avg_attention_weight") \
            .order("usage_count", desc=True) \
            .limit(5) \
            .execute()

        if result.data:
            for r in result.data:
                print(f"  {r['file_path']}")
                print(f"    Used: {r['usage_count']}x, Avg attention: {r.get('avg_attention_weight', 0):.3f}")
        else:
            print("  (No data yet)")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # 작업 카테고리별 통계
    print("\n[6-2] Task category statistics...")
    try:
        result = vm.db.client.table("execution_contexts") \
            .select("task_category,quality_score") \
            .execute()

        if result.data:
            categories = {}
            for r in result.data:
                cat = r.get('task_category', 'unknown')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(r.get('quality_score', 0))

            for cat, scores in categories.items():
                avg_quality = sum(scores) / len(scores) if scores else 0
                print(f"  {cat}: {len(scores)} executions, avg quality: {avg_quality:.2f}")
        else:
            print("  (No data yet)")
    except Exception as e:
        print(f"  ✗ Error: {e}")


def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("Neural-CONI Vector Memory Test Suite")
    print("=" * 60)
    print("\nTesting Supabase pgvector integration...")

    try:
        # 연결 테스트
        vm = get_vector_memory()
        print("✓ Vector Memory initialized")

        # 각 테스트 실행
        test_file_embeddings()
        test_execution_contexts()
        test_learned_recommendations()
        test_enhanced_attention()
        test_explanation()
        test_statistics()

        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        print("\nNote: If some tests show '(No data yet)', that's normal for first run.")
        print("Run multiple times to see learning effects.")

    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
