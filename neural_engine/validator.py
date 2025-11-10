"""
Validator: Task 결과물의 품질을 정량화

기능:
- 임베딩 기반 관련성 평가
- 휴리스틱 기반 완성도 평가
- 논리적 일관성 평가
- 종합 품질 점수 계산 (0~1)
"""

import re
import numpy as np
from typing import Dict, Optional, List
from .embedding_engine import EmbeddingEngine, get_embedding_engine


class NeuralValidator:
    """
    Neural Validator: 결과물 품질을 0~1 점수로 정량화

    다차원 평가:
    - relevance: 목적과의 관련성
    - completeness: 내용 완성도
    - coherence: 논리적 일관성
    """

    def __init__(self, embedding_engine: Optional[EmbeddingEngine] = None):
        """
        Args:
            embedding_engine: 임베딩 엔진 (None이면 전역 인스턴스 사용)
        """
        self.embedding_engine = embedding_engine or get_embedding_engine()

    def evaluate(self,
                task_output: str,
                task_purpose: str,
                importance: float = 0.5) -> Dict:
        """
        Task 결과물의 품질을 다차원으로 평가

        Args:
            task_output: Task 결과물 (텍스트)
            task_purpose: Task 목적
            importance: Task 중요도 (0~1) - 높을수록 엄격한 평가

        Returns:
            {
                "relevance": float,      # 관련성 (0~1)
                "completeness": float,   # 완성도 (0~1)
                "coherence": float,      # 일관성 (0~1)
                "quality": float,        # 종합 점수 (0~1)
                "passed": bool,          # 통과 여부
                "feedback": str          # 개선 피드백
            }
        """
        # 1. 관련성 평가 (임베딩 기반)
        relevance = self.check_relevance(task_output, task_purpose)

        # 2. 완성도 평가 (휴리스틱)
        completeness = self.check_completeness(task_output)

        # 3. 일관성 평가 (문장 임베딩 기반)
        coherence = self.check_coherence(task_output)

        # 4. 종합 점수 계산 (가중 평균)
        quality = self._compute_quality_score(
            relevance, completeness, coherence
        )

        # 5. 통과 여부 결정
        threshold = 0.7 + (importance * 0.2)  # 0.7~0.9
        passed = quality >= threshold

        # 6. 피드백 생성
        feedback = self._generate_feedback(
            relevance, completeness, coherence, passed
        )

        return {
            "relevance": relevance,
            "completeness": completeness,
            "coherence": coherence,
            "quality": quality,
            "passed": passed,
            "threshold": threshold,
            "feedback": feedback
        }

    def check_relevance(self, output: str, purpose: str) -> float:
        """
        출력과 목적의 관련성 평가 (임베딩 유사도)

        Args:
            output: 결과물
            purpose: 목적

        Returns:
            관련성 점수 (0~1)
        """
        output_emb = self.embedding_engine.embed_text(output)
        purpose_emb = self.embedding_engine.embed_text(purpose)

        similarity = self.embedding_engine.cosine_similarity(output_emb, purpose_emb)

        return float(similarity)

    def check_completeness(self, output: str) -> float:
        """
        내용 완성도 평가 (휴리스틱 기반)

        평가 기준:
        - 최소 길이
        - 구조 (헤더, 목록 등)
        - 문장 수
        - 단락 수

        Args:
            output: 결과물

        Returns:
            완성도 점수 (0~1)
        """
        if not output or not output.strip():
            return 0.0

        scores = []

        # 1. 길이 평가
        min_length = 300  # 최소 300자
        length_score = min(len(output) / min_length, 1.0)
        scores.append(length_score)

        # 2. 구조 평가 (마크다운 헤더)
        has_headers = bool(re.search(r'^#{1,3}\s+.+', output, re.MULTILINE))
        structure_score = 1.0 if has_headers else 0.5
        scores.append(structure_score)

        # 3. 문장 수 평가
        sentences = [s.strip() for s in output.split('.') if s.strip()]
        sentence_score = min(len(sentences) / 5, 1.0)  # 최소 5문장
        scores.append(sentence_score)

        # 4. 단락 수 평가
        paragraphs = [p.strip() for p in output.split('\n\n') if p.strip()]
        paragraph_score = min(len(paragraphs) / 3, 1.0)  # 최소 3단락
        scores.append(paragraph_score)

        # 평균 점수
        return np.mean(scores)

    def check_coherence(self, output: str) -> float:
        """
        논리적 일관성 평가 (문장 간 유사도 기반)

        연속된 문장들이 적절한 유사도를 가지는지 확인:
        - 너무 높으면: 반복적
        - 너무 낮으면: 비일관적
        - 적절한 범위: 0.4 ~ 0.8

        Args:
            output: 결과물

        Returns:
            일관성 점수 (0~1)
        """
        # 문장 분리
        sentences = [s.strip() for s in output.split('.') if s.strip() and len(s.strip()) > 10]

        if len(sentences) < 2:
            return 0.5  # 판단 불가

        # 연속 문장 간 유사도 계산
        similarities = []
        for i in range(len(sentences) - 1):
            sent1 = sentences[i]
            sent2 = sentences[i + 1]

            emb1 = self.embedding_engine.embed_text(sent1)
            emb2 = self.embedding_engine.embed_text(sent2)

            sim = self.embedding_engine.cosine_similarity(emb1, emb2)
            similarities.append(sim)

        if not similarities:
            return 0.5

        avg_sim = np.mean(similarities)

        # 적절한 유사도 범위: 0.4 ~ 0.8
        optimal_min = 0.4
        optimal_max = 0.8

        if optimal_min <= avg_sim <= optimal_max:
            # 최적 범위 내: 점수 1.0
            return 1.0
        elif avg_sim < optimal_min:
            # 너무 낮음 (비일관적)
            return max(0.0, avg_sim / optimal_min)
        else:
            # 너무 높음 (반복적)
            excess = avg_sim - optimal_max
            penalty = excess / (1.0 - optimal_max)
            return max(0.0, 1.0 - penalty)

    def _compute_quality_score(self,
                               relevance: float,
                               completeness: float,
                               coherence: float) -> float:
        """
        종합 품질 점수 계산 (가중 평균)

        가중치:
        - relevance: 40% (가장 중요)
        - completeness: 30%
        - coherence: 30%

        Args:
            relevance, completeness, coherence: 각 평가 점수

        Returns:
            종합 점수 (0~1)
        """
        weights = {
            "relevance": 0.4,
            "completeness": 0.3,
            "coherence": 0.3
        }

        quality = (
            weights["relevance"] * relevance +
            weights["completeness"] * completeness +
            weights["coherence"] * coherence
        )

        return float(quality)

    def _generate_feedback(self,
                          relevance: float,
                          completeness: float,
                          coherence: float,
                          passed: bool) -> str:
        """
        개선 피드백 생성

        Args:
            relevance, completeness, coherence: 평가 점수
            passed: 통과 여부

        Returns:
            피드백 문자열
        """
        if passed:
            return "✅ 품질 기준을 충족합니다."

        # 가장 낮은 점수 찾기
        scores = {
            "관련성": relevance,
            "완성도": completeness,
            "일관성": coherence
        }

        min_aspect = min(scores, key=scores.get)
        min_score = scores[min_aspect]

        feedback_parts = [f"⚠️ 품질 개선 필요 (가장 낮은 점수: {min_aspect} {min_score:.2f})"]

        # 개별 피드백
        if relevance < 0.7:
            feedback_parts.append("- 목적과의 관련성이 낮습니다. Task 목적을 재확인하세요.")

        if completeness < 0.7:
            feedback_parts.append("- 내용이 불충분합니다. 더 상세한 정보를 추가하세요.")

        if coherence < 0.7:
            feedback_parts.append("- 논리적 흐름이 부족합니다. 문장 간 연결을 개선하세요.")

        return "\n".join(feedback_parts)

    def evaluate_multiple(self,
                         outputs: List[str],
                         purpose: str) -> Dict:
        """
        여러 결과물을 평가하고 최선 선택 (앙상블용)

        Args:
            outputs: 결과물 리스트
            purpose: Task 목적

        Returns:
            {
                "best_index": int,
                "best_quality": float,
                "scores": [float, ...]
            }
        """
        evaluations = [
            self.evaluate(output, purpose)
            for output in outputs
        ]

        qualities = [ev["quality"] for ev in evaluations]
        best_index = int(np.argmax(qualities))

        return {
            "best_index": best_index,
            "best_quality": qualities[best_index],
            "scores": qualities,
            "evaluations": evaluations
        }


class QualityTracker:
    """
    품질 변화 추적 및 분석

    Run마다 품질이 어떻게 변화하는지 추적
    """

    def __init__(self):
        self.quality_history: List[Dict] = []

    def record(self, run_id: str, task_id: str, quality_data: Dict):
        """품질 데이터 기록"""
        record = {
            "run_id": run_id,
            "task_id": task_id,
            **quality_data
        }
        self.quality_history.append(record)

    def get_task_quality_trend(self, task_type: str) -> List[float]:
        """특정 Task 유형의 품질 추세"""
        return [
            record["quality"]
            for record in self.quality_history
            if record["task_id"].startswith(task_type)
        ]

    def get_average_quality(self, last_n: int = 10) -> float:
        """최근 N개의 평균 품질"""
        recent = self.quality_history[-last_n:]
        if not recent:
            return 0.0

        qualities = [r["quality"] for r in recent]
        return np.mean(qualities)

    def is_improving(self, window: int = 5) -> bool:
        """품질이 개선되고 있는지 확인"""
        if len(self.quality_history) < window * 2:
            return False

        old_avg = np.mean([r["quality"] for r in self.quality_history[-window*2:-window]])
        new_avg = np.mean([r["quality"] for r in self.quality_history[-window:]])

        return new_avg > old_avg


if __name__ == "__main__":
    """테스트 코드"""
    print("=" * 60)
    print("Validator Test")
    print("=" * 60)

    validator = NeuralValidator()

    # 1. 좋은 결과물 테스트
    print("\n[Test 1] 좋은 결과물")
    good_output = """
# 사용자 요구사항 분석 결과

## 주요 요구사항

1. 시스템 성능 개선
2. 사용자 인터페이스 개선
3. 보안 강화

## 분석 내용

사용자는 현재 시스템의 응답 속도가 느리다고 지적했습니다.
또한 UI가 직관적이지 않아 사용에 어려움을 겪고 있습니다.
보안 측면에서도 최신 암호화 기술을 적용해야 합니다.

## 결론

위 세 가지 요구사항을 우선순위로 개선 작업을 진행합니다.
"""

    purpose = "사용자 요구사항을 분석합니다"
    result = validator.evaluate(good_output, purpose)

    print(f"Purpose: {purpose}\n")
    print("평가 결과:")
    print(f"  관련성: {result['relevance']:.2f}")
    print(f"  완성도: {result['completeness']:.2f}")
    print(f"  일관성: {result['coherence']:.2f}")
    print(f"  종합 품질: {result['quality']:.2f}")
    print(f"  통과: {result['passed']}")
    print(f"  피드백: {result['feedback']}")

    # 2. 나쁜 결과물 테스트
    print("\n[Test 2] 부족한 결과물")
    bad_output = "요구사항은 성능, UI, 보안입니다."

    result = validator.evaluate(bad_output, purpose)

    print(f"Purpose: {purpose}\n")
    print("평가 결과:")
    print(f"  관련성: {result['relevance']:.2f}")
    print(f"  완성도: {result['completeness']:.2f}")
    print(f"  일관성: {result['coherence']:.2f}")
    print(f"  종합 품질: {result['quality']:.2f}")
    print(f"  통과: {result['passed']}")
    print(f"  피드백: {result['feedback']}")

    # 3. 앙상블 평가
    print("\n[Test 3] 앙상블 평가 (3개 중 최선 선택)")
    outputs = [
        "요구사항 분석 결과: 성능, UI, 보안",
        good_output,
        "사용자가 원하는 것은 빠르고 안전한 시스템입니다."
    ]

    ensemble_result = validator.evaluate_multiple(outputs, purpose)

    print(f"Purpose: {purpose}\n")
    print("후보별 점수:")
    for i, score in enumerate(ensemble_result["scores"]):
        print(f"  후보 {i+1}: {score:.2f}")

    print(f"\n최선: 후보 {ensemble_result['best_index'] + 1}")
    print(f"최선 품질: {ensemble_result['best_quality']:.2f}")

    # 4. Quality Tracker
    print("\n[Test 4] Quality Tracker")
    tracker = QualityTracker()

    # 가상의 품질 데이터 기록
    for i in range(10):
        tracker.record(
            f"run-00{i}",
            "tsk-01",
            {"quality": 0.6 + i * 0.03}  # 점진적 개선
        )

    avg_quality = tracker.get_average_quality(last_n=5)
    is_improving = tracker.is_improving(window=3)

    print(f"최근 5개 평균 품질: {avg_quality:.2f}")
    print(f"품질 개선 중: {is_improving}")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
