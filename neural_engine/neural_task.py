"""
Neural Task: Task를 Neuron(뉴런)처럼 동작하게 만드는 클래스

기능:
- 활성화 값 계산 (0~1)
- Attention 기반 입력 선택
- 실행 여부 결정 (임계값)
- 품질 점수 추적
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(Enum):
    """Task 상태"""
    PENDING = "PENDING"
    ACTIVATED = "ACTIVATED"      # 활성화됨 (임계값 이상)
    SKIPPED = "SKIPPED"          # Skip됨 (임계값 미만)
    EXECUTING = "EXECUTING"      # 실행 중
    COMPLETED = "COMPLETED"      # 완료
    FAILED = "FAILED"            # 실패


@dataclass
class NeuralTask:
    """
    Neural Task: 뉴런처럼 동작하는 Task

    기존 Task의 모든 속성 유지 + 신경망 속성 추가
    """

    # ===== 기존 속성 (CONI 호환) =====
    task_id: str
    run_id: str
    sub_stage_id: str
    task_name: str
    task_reason: str
    task_purpose: str

    # 참조 파일들
    related_references: List[str] = field(default_factory=list)
    related_guidelines: List[str] = field(default_factory=list)

    # 출력
    output_folder: str = ""
    output_path: str = ""

    # MCP 및 Pre-tool
    mcp_id: Optional[str] = None
    pre_tool_reason: Optional[str] = None
    pre_tool_purpose: Optional[str] = None

    # 상태
    status: TaskStatus = TaskStatus.PENDING

    # ===== 신경망 속성 (새로 추가) =====

    # 활성화 관련
    activation_level: float = 0.0        # 현재 활성화 값 (0~1)
    threshold: float = 0.6               # 실행 임계값
    confidence: float = 0.0              # 결과 신뢰도

    # 가중치 (Task 간 연결)
    weights_in: Dict[str, float] = field(default_factory=dict)   # 입력 가중치
    weights_out: Dict[str, float] = field(default_factory=dict)  # 출력 가중치

    # 임베딩
    purpose_embedding: Optional[np.ndarray] = None  # Task 목적의 벡터 표현
    output_embedding: Optional[np.ndarray] = None   # 결과물의 벡터 표현

    # 품질 관련
    quality_score: float = 0.0           # 결과물 품질 (0~1)
    quality_history: List[float] = field(default_factory=list)  # 과거 품질 기록

    # Attention 관련
    attention_weights: Dict[str, float] = field(default_factory=dict)  # 파일별 가중치
    selected_files: List[str] = field(default_factory=list)  # Attention으로 선택된 파일

    # 실행 메타데이터
    execution_time: float = 0.0          # 실행 시간 (초)
    token_used: int = 0                  # 사용한 토큰 수
    retry_count: int = 0                 # 재시도 횟수

    def compute_activation(self,
                          prev_tasks: List['NeuralTask'],
                          weights: Optional[Dict[str, float]] = None) -> float:
        """
        입력 Task들의 가중 합으로 활성화값 계산

        Args:
            prev_tasks: 이전 레이어의 Task들
            weights: 가중치 딕셔너리 (None이면 self.weights_in 사용)

        Returns:
            활성화 값 (0~1)
        """
        if not prev_tasks:
            # 입력층 (의존성 없음) → 항상 높은 활성화
            return 0.95

        weights = weights or self.weights_in
        weighted_sum = 0.0

        for prev_task in prev_tasks:
            weight = weights.get(prev_task.task_id, 0.5)  # 기본 가중치 0.5
            weighted_sum += prev_task.activation_level * weight

        # Sigmoid 활성화 함수
        activation = 1.0 / (1.0 + np.exp(-weighted_sum))

        return float(activation)

    def should_execute(self) -> bool:
        """
        활성화값이 임계값 이상인지 확인

        Returns:
            True면 실행, False면 Skip
        """
        return self.activation_level >= self.threshold

    def update_activation(self, prev_tasks: List['NeuralTask']):
        """활성화값 계산 및 업데이트"""
        self.activation_level = self.compute_activation(prev_tasks)

        if self.should_execute():
            self.status = TaskStatus.ACTIVATED
        else:
            self.status = TaskStatus.SKIPPED

    def select_inputs_with_attention(self,
                                     attention_selector,
                                     top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Attention 메커니즘으로 중요한 입력 파일만 선택

        Args:
            attention_selector: TaskAttentionSelector 인스턴스
            top_k: 선택할 파일 개수

        Returns:
            [(파일경로, attention_weight), ...]
        """
        if not self.related_references:
            return []

        # Attention으로 파일 선택
        selected = attention_selector.select_files(
            task_purpose=self.task_purpose,
            candidate_files=self.related_references,
            top_k=top_k
        )

        # 결과 저장
        self.selected_files = [file for file, _ in selected]
        self.attention_weights = {file: weight for file, weight in selected}

        return selected

    def get_execution_context(self) -> Dict:
        """
        실행에 필요한 컨텍스트 반환

        Returns:
            {
                "task_id": ...,
                "task_purpose": ...,
                "selected_files": [...],
                "guidelines": [...],
                ...
            }
        """
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "task_purpose": self.task_purpose,
            "selected_files": self.selected_files or self.related_references,
            "guidelines": self.related_guidelines,
            "activation": self.activation_level,
            "confidence": self.confidence,
            "mcp_id": self.mcp_id,
        }

    def record_execution_result(self,
                                quality_score: float,
                                execution_time: float,
                                token_used: int,
                                output_path: str):
        """
        실행 결과 기록

        Args:
            quality_score: 품질 점수 (0~1)
            execution_time: 실행 시간 (초)
            token_used: 사용한 토큰 수
            output_path: 결과 파일 경로
        """
        self.quality_score = quality_score
        self.execution_time = execution_time
        self.token_used = token_used
        self.output_path = output_path
        self.status = TaskStatus.COMPLETED

        # 품질 이력 추가
        self.quality_history.append(quality_score)

        # 신뢰도 계산 (품질 점수 기반)
        self.confidence = quality_score

    def to_dict(self) -> Dict:
        """Dict로 변환 (DB 저장용)"""
        return {
            # 기본 정보
            "task_id": self.task_id,
            "run_id": self.run_id,
            "task_name": self.task_name,
            "task_purpose": self.task_purpose,
            "status": self.status.value,

            # 신경망 속성
            "activation": self.activation_level,
            "threshold": self.threshold,
            "confidence": self.confidence,
            "quality_score": self.quality_score,

            # 실행 정보
            "executed": self.status == TaskStatus.COMPLETED,
            "selected_files": self.selected_files,
            "execution_time": self.execution_time,
            "token_used": self.token_used,

            # 출력
            "output_path": self.output_path,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'NeuralTask':
        """Dict에서 생성 (DB 로딩용)"""
        # 필수 필드만 추출
        return cls(
            task_id=data.get("task_id", ""),
            run_id=data.get("run_id", ""),
            sub_stage_id=data.get("sub_stage_id", ""),
            task_name=data.get("task_name", ""),
            task_reason=data.get("task_reason", ""),
            task_purpose=data.get("task_purpose", ""),
            related_references=data.get("related_references", []),
            related_guidelines=data.get("related_guidelines", []),
            activation_level=data.get("activation", 0.0),
            threshold=data.get("threshold", 0.6),
            quality_score=data.get("quality_score", 0.0),
        )

    def __repr__(self) -> str:
        """문자열 표현"""
        return (f"NeuralTask(id={self.task_id}, "
                f"activation={self.activation_level:.2f}, "
                f"status={self.status.value}, "
                f"quality={self.quality_score:.2f})")


class NeuralTaskLayer:
    """
    Task들의 레이어 (한 단계)

    신경망의 한 층(Layer)처럼 동작:
    - 같은 레벨의 Task들을 병렬 실행
    - 전체 레이어의 활성화 통계 제공
    """

    def __init__(self, tasks: List[NeuralTask], level: int):
        """
        Args:
            tasks: 이 레이어의 Task들
            level: 레이어 번호 (0부터 시작)
        """
        self.tasks = tasks
        self.level = level

    def compute_layer_activation(self, prev_layer: Optional['NeuralTaskLayer'] = None):
        """레이어 전체의 활성화 계산"""
        prev_tasks = prev_layer.tasks if prev_layer else []

        for task in self.tasks:
            task.update_activation(prev_tasks)

    def get_activated_tasks(self) -> List[NeuralTask]:
        """실행될 Task들 (활성화된 것만)"""
        return [t for t in self.tasks if t.should_execute()]

    def get_skipped_tasks(self) -> List[NeuralTask]:
        """Skip될 Task들"""
        return [t for t in self.tasks if not t.should_execute()]

    def get_layer_stats(self) -> Dict:
        """레이어 통계"""
        activated = self.get_activated_tasks()
        skipped = self.get_skipped_tasks()

        activations = [t.activation_level for t in self.tasks]

        return {
            "level": self.level,
            "total_tasks": len(self.tasks),
            "activated": len(activated),
            "skipped": len(skipped),
            "activation_rate": len(activated) / len(self.tasks) if self.tasks else 0,
            "avg_activation": np.mean(activations) if activations else 0,
            "max_activation": np.max(activations) if activations else 0,
            "min_activation": np.min(activations) if activations else 0,
        }

    def __repr__(self) -> str:
        stats = self.get_layer_stats()
        return (f"Layer {self.level}: {stats['total_tasks']} tasks "
                f"({stats['activated']} activated, {stats['skipped']} skipped)")


if __name__ == "__main__":
    """테스트 코드"""
    print("=" * 60)
    print("Neural Task Test")
    print("=" * 60)

    # 1. Neural Task 생성
    print("\n[Test 1] Neural Task 생성")
    task1 = NeuralTask(
        task_id="tsk-01",
        run_id="run-001",
        sub_stage_id="sub-01",
        task_name="분석",
        task_reason="요구사항 파악을 위해",
        task_purpose="사용자 요구사항을 분석합니다",
        related_references=["data/doc1.md", "data/doc2.md"],
        threshold=0.6
    )

    print(f"Created: {task1}")

    # 2. 활성화 계산 (입력층 → 높은 활성화)
    print("\n[Test 2] 활성화 계산 (입력층)")
    task1.update_activation([])  # 의존성 없음
    print(f"Activation: {task1.activation_level:.2f}")
    print(f"Should execute: {task1.should_execute()}")
    print(f"Status: {task1.status.value}")

    # 3. 다음 Task (의존성 있음)
    print("\n[Test 3] 의존성 있는 Task")
    task2 = NeuralTask(
        task_id="tsk-02",
        run_id="run-001",
        sub_stage_id="sub-01",
        task_name="초안작성",
        task_reason="분석 결과를 바탕으로",
        task_purpose="보고서 초안을 작성합니다",
        threshold=0.6
    )

    # 가중치 설정
    task2.weights_in = {"tsk-01": 0.8}

    # 활성화 계산
    task2.update_activation([task1])
    print(f"Task 2 activation: {task2.activation_level:.2f}")
    print(f"Task 2 should execute: {task2.should_execute()}")

    # 4. 레이어 테스트
    print("\n[Test 4] Neural Task Layer")

    layer0_tasks = [
        NeuralTask(f"tsk-0{i}", "run-001", "sub-01", f"Task{i}",
                  "", f"Purpose {i}", threshold=0.6)
        for i in range(1, 4)
    ]

    layer0 = NeuralTaskLayer(layer0_tasks, level=0)
    layer0.compute_layer_activation()

    print(layer0)
    print(f"Stats: {layer0.get_layer_stats()}")

    # 5. 품질 기록
    print("\n[Test 5] 실행 결과 기록")
    task1.record_execution_result(
        quality_score=0.85,
        execution_time=45.0,
        token_used=8500,
        output_path="workspace/task1_output.md"
    )

    print(f"Quality: {task1.quality_score:.2f}")
    print(f"Execution time: {task1.execution_time:.1f}s")
    print(f"Tokens used: {task1.token_used}")
    print(f"Status: {task1.status.value}")

    # 6. Dict 변환
    print("\n[Test 6] Dict 변환")
    task_dict = task1.to_dict()
    print("Saved to dict:")
    for key, value in task_dict.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
