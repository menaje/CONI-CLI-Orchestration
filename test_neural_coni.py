#!/usr/bin/env python3
"""
Neural-CONI 통합 테스트 스크립트

모든 컴포넌트가 정상 작동하는지 검증
"""

import sys
import os

# neural_engine 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_section(title):
    """섹션 구분선 출력"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_embedding_engine():
    """임베딩 엔진 테스트"""
    print_section("Test 1: Embedding Engine")

    try:
        from neural_engine.embedding_engine import EmbeddingEngine

        engine = EmbeddingEngine()

        # 기본 임베딩
        text = "사용자 요구사항을 분석합니다"
        emb = engine.embed_text(text)

        print(f"✓ 임베딩 생성 성공: shape={emb.shape}")
        assert emb.shape[0] == 384, "임베딩 차원 오류"

        # 유사도 계산
        text2 = "요구사항 분석을 수행합니다"
        emb2 = engine.embed_text(text2)
        similarity = engine.cosine_similarity(emb, emb2)

        print(f"✓ 유사도 계산 성공: {similarity:.4f}")
        assert 0 <= similarity <= 1, "유사도 범위 오류"

        print("✅ Embedding Engine 테스트 통과\n")
        return True

    except Exception as e:
        print(f"❌ Embedding Engine 테스트 실패: {e}\n")
        return False


def test_attention():
    """Attention 메커니즘 테스트"""
    print_section("Test 2: Attention Mechanism")

    try:
        from neural_engine.embedding_engine import get_embedding_engine
        from neural_engine.attention import AttentionMechanism

        engine = get_embedding_engine()
        attention = AttentionMechanism(engine)

        # 테스트 데이터
        query_text = "보고서 초안을 작성합니다"
        key_texts = [
            "요구사항 분석 결과",
            "날씨 정보",
            "보고서 작성 가이드라인",
        ]

        query_emb = engine.embed_text(query_text)
        key_embs = [engine.embed_text(text) for text in key_texts]

        # Attention 계산
        weights, context = attention.attention(query_emb, key_embs)

        print(f"✓ Attention 계산 성공")
        print(f"  가중치 합: {weights.sum():.4f}")
        assert abs(weights.sum() - 1.0) < 0.01, "Softmax 합 오류"

        # Top-K 선택
        top_k = attention.top_k_attention(query_emb, key_embs, k=2)
        print(f"✓ Top-K 선택 성공: {len(top_k)}개")

        print("✅ Attention Mechanism 테스트 통과\n")
        return True

    except Exception as e:
        print(f"❌ Attention Mechanism 테스트 실패: {e}\n")
        return False


def test_neural_task():
    """Neural Task 테스트"""
    print_section("Test 3: Neural Task")

    try:
        from neural_engine.neural_task import NeuralTask, NeuralTaskLayer

        # Task 생성
        task1 = NeuralTask(
            task_id="tsk-01",
            run_id="test-run",
            sub_stage_id="sub-01",
            task_name="분석",
            task_reason="테스트",
            task_purpose="테스트 수행",
            threshold=0.6
        )

        print(f"✓ Neural Task 생성 성공: {task1.task_id}")

        # 활성화 계산
        task1.update_activation([])  # 입력층
        print(f"✓ 활성화 계산 성공: {task1.activation_level:.2f}")
        assert task1.should_execute(), "활성화 임계값 오류"

        # 레이어 테스트
        tasks = [task1]
        layer = NeuralTaskLayer(tasks, level=0)
        layer.compute_layer_activation()

        stats = layer.get_layer_stats()
        print(f"✓ 레이어 통계: {stats['activated']}/{stats['total_tasks']}")

        print("✅ Neural Task 테스트 통과\n")
        return True

    except Exception as e:
        print(f"❌ Neural Task 테스트 실패: {e}\n")
        return False


def test_validator():
    """Validator 테스트"""
    print_section("Test 4: Validator")

    try:
        from neural_engine.validator import NeuralValidator

        validator = NeuralValidator()

        # 좋은 결과물
        good_output = """
# 분석 결과

사용자 요구사항은 다음과 같습니다:
1. 성능 개선
2. UI 개선
3. 보안 강화

각 항목에 대해 상세히 분석했습니다.
"""

        purpose = "사용자 요구사항을 분석합니다"
        result = validator.evaluate(good_output, purpose)

        print(f"✓ 품질 평가 성공")
        print(f"  관련성: {result['relevance']:.2f}")
        print(f"  완성도: {result['completeness']:.2f}")
        print(f"  일관성: {result['coherence']:.2f}")
        print(f"  종합: {result['quality']:.2f}")

        assert 0 <= result['quality'] <= 1, "품질 점수 범위 오류"

        print("✅ Validator 테스트 통과\n")
        return True

    except Exception as e:
        print(f"❌ Validator 테스트 실패: {e}\n")
        return False


def test_weight_manager():
    """Weight Manager 테스트"""
    print_section("Test 5: Weight Manager")

    try:
        from neural_engine.weight_manager import WeightManager
        from neural_engine.neural_task import NeuralTask, NeuralTaskLayer

        # 임시 파일
        test_file = "/tmp/test_weights.json"
        if os.path.exists(test_file):
            os.remove(test_file)

        manager = WeightManager(test_file, learning_rate=0.01)

        # 가중치 초기화
        pairs = [("tsk-01", "tsk-02"), ("tsk-02", "tsk-03")]
        manager.initialize_weights(pairs)

        print(f"✓ 가중치 초기화 성공: {len(manager.weights)}개")

        # Forward Pass 테스트
        task1 = NeuralTask("tsk-01", "test", "sub-01", "T1", "", "Purpose 1")
        task2 = NeuralTask("tsk-02", "test", "sub-01", "T2", "", "Purpose 2")

        task1.quality_score = 0.8
        task2.quality_score = 0.7

        layer1 = NeuralTaskLayer([task1], 0)
        layer2 = NeuralTaskLayer([task2], 1)

        layers = [layer1, layer2]
        manager.forward_pass(layers)

        print(f"✓ Forward Pass 성공")

        # Backward Pass 테스트
        manager.backward_pass(layers, target_quality=0.9)

        print(f"✓ Backward Pass 성공")

        # 통계
        stats = manager.get_weight_stats()
        print(f"  평균 가중치: {stats['avg_weight']:.3f}")

        # 정리
        if os.path.exists(test_file):
            os.remove(test_file)

        print("✅ Weight Manager 테스트 통과\n")
        return True

    except Exception as e:
        print(f"❌ Weight Manager 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """통합 시나리오 테스트"""
    print_section("Test 6: Integration Scenario")

    try:
        from neural_engine.embedding_engine import get_embedding_engine
        from neural_engine.attention import TaskAttentionSelector
        from neural_engine.neural_task import NeuralTask
        from neural_engine.validator import NeuralValidator

        print("시나리오: Task 실행 시뮬레이션")

        # 1. 임베딩 엔진
        engine = get_embedding_engine()
        print("✓ 임베딩 엔진 로드")

        # 2. Attention Selector
        selector = TaskAttentionSelector(engine)

        # 3. Neural Task 생성
        task = NeuralTask(
            task_id="tsk-test",
            run_id="test-run",
            sub_stage_id="sub-01",
            task_name="보고서 작성",
            task_reason="테스트",
            task_purpose="보고서를 작성합니다",
            related_references=["doc1.md", "doc2.md", "doc3.md"]
        )
        print("✓ Neural Task 생성")

        # 4. 활성화 계산
        task.update_activation([])
        print(f"✓ 활성화: {task.activation_level:.2f}")

        # 5. 실행 여부 결정
        if task.should_execute():
            print("✓ Task 실행 결정")

            # 6. 품질 평가 (가상의 출력)
            validator = NeuralValidator()
            output = "테스트 보고서 내용입니다. 요구사항을 분석하고 결과를 정리했습니다."

            result = validator.evaluate(output, task.task_purpose)
            print(f"✓ 품질 평가: {result['quality']:.2f}")

            # 7. 결과 기록
            task.record_execution_result(
                quality_score=result['quality'],
                execution_time=10.0,
                token_used=1000,
                output_path="/tmp/test_output.md"
            )
            print("✓ 결과 기록 완료")

        print("\n✅ Integration 테스트 통과\n")
        return True

    except Exception as e:
        print(f"❌ Integration 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 실행"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "Neural-CONI 통합 테스트" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")

    tests = [
        test_embedding_engine,
        test_attention,
        test_neural_task,
        test_validator,
        test_weight_manager,
        test_integration
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # 결과 요약
    print_section("Test Summary")
    passed = sum(results)
    total = len(results)

    print(f"통과: {passed}/{total}")

    if passed == total:
        print("\n🎉 모든 테스트 통과! Neural-CONI가 정상 작동합니다.")
        return 0
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
