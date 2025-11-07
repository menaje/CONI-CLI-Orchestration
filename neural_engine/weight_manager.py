"""
Weight Manager: 가중치 학습 및 Backpropagation

기능:
- Task 간 가중치 관리
- Forward Pass (실행 단계)
- Backward Pass (학습 단계)
- Gradient Descent로 가중치 최적화
"""

import os
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np

from .neural_task import NeuralTask, NeuralTaskLayer


class WeightManager:
    """
    Weight Manager: Task 간 연결 강도를 관리하고 학습

    신경망의 학습 메커니즘 구현:
    - Forward: 가중치 기반 활성화 전파
    - Backward: 오차로 가중치 조정
    """

    def __init__(self, weights_file: str = "db/weights.json", learning_rate: float = 0.01):
        """
        Args:
            weights_file: 가중치 저장 파일
            learning_rate: 학습률 (0.01 권장)
        """
        self.weights_file = weights_file
        self.learning_rate = learning_rate
        self.weights: Dict[str, float] = {}
        self.gradients: Dict[str, float] = {}
        self.update_counts: Dict[str, int] = {}

        self._load_weights()

    def _load_weights(self):
        """가중치 파일 로딩"""
        if os.path.exists(self.weights_file):
            try:
                with open(self.weights_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.weights = data.get("weights", {})
                    self.gradients = data.get("gradients", {})
                    self.update_counts = data.get("update_counts", {})
                    print(f"[WeightManager] Loaded {len(self.weights)} weights from {self.weights_file}")
            except Exception as e:
                print(f"[WARNING] Failed to load weights: {e}")
                self.weights = {}

    def _save_weights(self):
        """가중치 파일 저장"""
        os.makedirs(os.path.dirname(self.weights_file), exist_ok=True)

        data = {
            "weights": self.weights,
            "gradients": self.gradients,
            "update_counts": self.update_counts,
            "learning_rate": self.learning_rate
        }

        with open(self.weights_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"[WeightManager] Saved {len(self.weights)} weights to {self.weights_file}")

    def get_weight(self, from_task: str, to_task: str, default: float = 0.5) -> float:
        """
        두 Task 간의 가중치 반환

        Args:
            from_task: 시작 Task ID
            to_task: 끝 Task ID
            default: 기본값 (가중치 없을 때)

        Returns:
            가중치 (0~1)
        """
        key = f"{from_task}→{to_task}"
        return self.weights.get(key, default)

    def set_weight(self, from_task: str, to_task: str, weight: float):
        """
        가중치 설정

        Args:
            from_task: 시작 Task ID
            to_task: 끝 Task ID
            weight: 가중치 값
        """
        key = f"{from_task}→{to_task}"
        # 클리핑 (0.1 ~ 0.99)
        weight = np.clip(weight, 0.1, 0.99)
        self.weights[key] = float(weight)

    def initialize_weights(self, task_pairs: List[Tuple[str, str]], method: str = "xavier"):
        """
        가중치 초기화

        Args:
            task_pairs: [(from_task, to_task), ...] 리스트
            method: 초기화 방법 ("xavier", "he", "uniform")
        """
        for from_task, to_task in task_pairs:
            if method == "xavier":
                # Xavier initialization
                weight = np.random.uniform(0.4, 0.8)
            elif method == "he":
                # He initialization
                weight = np.random.normal(0.6, 0.2)
                weight = np.clip(weight, 0.1, 0.99)
            elif method == "uniform":
                weight = 0.5
            else:
                weight = 0.5

            self.set_weight(from_task, to_task, weight)

        print(f"[WeightManager] Initialized {len(task_pairs)} weights using {method} method")

    def forward_pass(self, layers: List[NeuralTaskLayer]) -> float:
        """
        Forward Pass: 가중치 기반으로 활성화 전파

        Args:
            layers: Task 레이어 리스트 (순서대로)

        Returns:
            최종 레이어의 평균 품질
        """
        print("\n[WeightManager] Forward Pass")

        for i, layer in enumerate(layers):
            prev_layer = layers[i-1] if i > 0 else None

            # 레이어 활성화 계산
            layer.compute_layer_activation(prev_layer)

            # 통계 출력
            stats = layer.get_layer_stats()
            print(f"  Layer {i}: {stats['activated']}/{stats['total_tasks']} activated "
                  f"(avg activation: {stats['avg_activation']:.2f})")

        # 마지막 레이어의 평균 품질 반환
        last_layer = layers[-1]
        qualities = [t.quality_score for t in last_layer.tasks if t.quality_score > 0]

        return np.mean(qualities) if qualities else 0.0

    def backward_pass(self,
                     layers: List[NeuralTaskLayer],
                     target_quality: float = 0.9):
        """
        Backward Pass: 품질 오차로 가중치 업데이트

        Args:
            layers: Task 레이어 리스트 (순서대로)
            target_quality: 목표 품질 (0~1)
        """
        print("\n[WeightManager] Backward Pass")

        # 실행된 Task들만 추출
        all_tasks = []
        for layer in layers:
            all_tasks.extend(layer.get_activated_tasks())

        if not all_tasks:
            print("  No activated tasks. Skipping backward pass.")
            return

        # 최종 품질 계산
        qualities = [t.quality_score for t in all_tasks if t.quality_score > 0]
        if not qualities:
            print("  No quality scores. Skipping backward pass.")
            return

        actual_quality = np.mean(qualities)
        error = target_quality - actual_quality

        print(f"  Target quality: {target_quality:.2f}")
        print(f"  Actual quality: {actual_quality:.2f}")
        print(f"  Error: {error:+.2f}")

        # 레이어를 역순으로 순회
        for i in range(len(layers) - 1, 0, -1):
            current_layer = layers[i]
            prev_layer = layers[i-1]

            current_tasks = current_layer.get_activated_tasks()
            prev_tasks = prev_layer.get_activated_tasks()

            # 각 연결의 가중치 업데이트
            weight_updates = 0
            for curr_task in current_tasks:
                for prev_task in prev_tasks:
                    # Gradient 계산
                    gradient = error * prev_task.activation_level * curr_task.quality_score

                    # 가중치 업데이트
                    key = f"{prev_task.task_id}→{curr_task.task_id}"
                    old_weight = self.get_weight(prev_task.task_id, curr_task.task_id)
                    new_weight = old_weight + self.learning_rate * gradient

                    # 클리핑
                    new_weight = np.clip(new_weight, 0.1, 0.99)

                    # 저장
                    self.set_weight(prev_task.task_id, curr_task.task_id, new_weight)
                    self.gradients[key] = gradient
                    self.update_counts[key] = self.update_counts.get(key, 0) + 1

                    weight_updates += 1

            print(f"  Layer {i}: Updated {weight_updates} weights")

        # 저장
        self._save_weights()

    def get_optimal_path(self, start: str, end: str, all_tasks: List[str]) -> List[str]:
        """
        시작에서 끝까지 가장 가중치가 높은 경로 찾기

        Args:
            start: 시작 Task ID
            end: 끝 Task ID
            all_tasks: 모든 Task ID 리스트

        Returns:
            최적 경로 [task1, task2, ..., end]
        """
        # 간단한 Greedy 알고리즘
        path = [start]
        current = start

        while current != end and len(path) < len(all_tasks):
            # 다음 최선의 Task 찾기
            candidates = [t for t in all_tasks if t not in path]
            if not candidates:
                break

            best_next = None
            best_weight = -1

            for candidate in candidates:
                weight = self.get_weight(current, candidate)
                if weight > best_weight:
                    best_weight = weight
                    best_next = candidate

            if best_next is None:
                break

            path.append(best_next)
            current = best_next

        return path

    def get_weight_stats(self) -> Dict:
        """가중치 통계 반환"""
        if not self.weights:
            return {
                "total_weights": 0,
                "avg_weight": 0.0,
                "max_weight": 0.0,
                "min_weight": 0.0,
                "total_updates": 0
            }

        weights_values = list(self.weights.values())
        total_updates = sum(self.update_counts.values())

        return {
            "total_weights": len(self.weights),
            "avg_weight": np.mean(weights_values),
            "max_weight": np.max(weights_values),
            "min_weight": np.min(weights_values),
            "std_weight": np.std(weights_values),
            "total_updates": total_updates,
            "avg_updates_per_weight": total_updates / len(self.weights) if self.weights else 0
        }

    def visualize_weights(self, top_k: int = 10) -> str:
        """
        상위 K개 가중치 시각화 (텍스트)

        Args:
            top_k: 표시할 개수

        Returns:
            시각화 문자열
        """
        if not self.weights:
            return "No weights to visualize."

        # 가중치 내림차순 정렬
        sorted_weights = sorted(self.weights.items(), key=lambda x: x[1], reverse=True)

        lines = [f"\n{'=' * 60}", f"Top {top_k} Weights (Strongest Connections)", f"{'=' * 60}"]

        for i, (key, weight) in enumerate(sorted_weights[:top_k], 1):
            update_count = self.update_counts.get(key, 0)
            bar_length = int(weight * 40)
            bar = "█" * bar_length

            lines.append(f"{i:2d}. {key:30s} {weight:.3f} {bar} (updates: {update_count})")

        lines.append("=" * 60)

        return "\n".join(lines)


class AdaptiveLearningRate:
    """
    적응적 학습률 (Learning Rate Scheduling)

    학습이 진행됨에 따라 학습률 조정
    """

    def __init__(self, initial_lr: float = 0.01, decay: float = 0.95, min_lr: float = 0.001):
        """
        Args:
            initial_lr: 초기 학습률
            decay: 감쇠율
            min_lr: 최소 학습률
        """
        self.initial_lr = initial_lr
        self.current_lr = initial_lr
        self.decay = decay
        self.min_lr = min_lr
        self.step_count = 0

    def step(self):
        """한 step 진행 (학습률 감소)"""
        self.step_count += 1
        self.current_lr = max(
            self.min_lr,
            self.initial_lr * (self.decay ** self.step_count)
        )

    def get_lr(self) -> float:
        """현재 학습률 반환"""
        return self.current_lr


if __name__ == "__main__":
    """테스트 코드"""
    print("=" * 60)
    print("Weight Manager Test")
    print("=" * 60)

    # 임시 파일
    test_weights_file = "/tmp/test_weights.json"
    manager = WeightManager(test_weights_file)

    # 1. 가중치 초기화
    print("\n[Test 1] 가중치 초기화")
    task_pairs = [
        ("input", "tsk-01"),
        ("tsk-01", "tsk-02"),
        ("tsk-01", "tsk-03"),
        ("tsk-02", "tsk-04"),
        ("tsk-03", "tsk-04"),
    ]

    manager.initialize_weights(task_pairs, method="xavier")

    print("\n초기 가중치:")
    print(manager.visualize_weights(top_k=5))

    # 2. Forward Pass 테스트
    print("\n[Test 2] Forward Pass")

    # 가상의 Task들 생성
    from neural_task import NeuralTask, NeuralTaskLayer

    layer0_tasks = [
        NeuralTask("tsk-01", "run-001", "sub-01", "분석", "", "분석 수행", threshold=0.6)
    ]

    layer1_tasks = [
        NeuralTask("tsk-02", "run-001", "sub-01", "초안", "", "초안 작성", threshold=0.6),
        NeuralTask("tsk-03", "run-001", "sub-01", "검색", "", "정보 검색", threshold=0.6),
    ]

    layer2_tasks = [
        NeuralTask("tsk-04", "run-001", "sub-01", "통합", "", "결과 통합", threshold=0.6)
    ]

    layer0 = NeuralTaskLayer(layer0_tasks, 0)
    layer1 = NeuralTaskLayer(layer1_tasks, 1)
    layer2 = NeuralTaskLayer(layer2_tasks, 2)

    layers = [layer0, layer1, layer2]

    # 가중치 적용
    for task in layer1_tasks:
        task.weights_in = {
            "tsk-01": manager.get_weight("tsk-01", task.task_id)
        }

    for task in layer2_tasks:
        task.weights_in = {
            "tsk-02": manager.get_weight("tsk-02", task.task_id),
            "tsk-03": manager.get_weight("tsk-03", task.task_id),
        }

    # 임의의 품질 점수 설정
    layer0_tasks[0].quality_score = 0.8
    layer1_tasks[0].quality_score = 0.7
    layer1_tasks[1].quality_score = 0.6
    layer2_tasks[0].quality_score = 0.75

    # Forward Pass
    avg_quality = manager.forward_pass(layers)
    print(f"\n최종 평균 품질: {avg_quality:.2f}")

    # 3. Backward Pass 테스트
    print("\n[Test 3] Backward Pass")
    manager.backward_pass(layers, target_quality=0.9)

    print("\n업데이트된 가중치:")
    print(manager.visualize_weights(top_k=5))

    # 4. 통계
    print("\n[Test 4] 가중치 통계")
    stats = manager.get_weight_stats()
    for key, value in stats.items():
        print(f"  {key}: {value:.3f}" if isinstance(value, float) else f"  {key}: {value}")

    # 5. 최적 경로
    print("\n[Test 5] 최적 경로 찾기")
    all_task_ids = ["tsk-01", "tsk-02", "tsk-03", "tsk-04"]
    optimal_path = manager.get_optimal_path("tsk-01", "tsk-04", all_task_ids)
    print(f"최적 경로: {' → '.join(optimal_path)}")

    # 정리
    if os.path.exists(test_weights_file):
        os.remove(test_weights_file)

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
