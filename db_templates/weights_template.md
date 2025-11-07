# Weights Database

가중치 데이터베이스: Task 간 연결 강도를 저장하고 학습

## 스키마

| from_task_type | to_task_type | weight | gradient | learning_rate | success_count | fail_count | last_updated | notes |
|----------------|--------------|--------|----------|---------------|---------------|------------|--------------|-------|
| input          | analyze      | 0.75   | 0.05     | 0.01          | 8             | 2          | run-010      | 안정적 |
| analyze        | draft        | 0.85   | 0.12     | 0.01          | 9             | 1          | run-010      | 강한 연결 |
| analyze        | research     | 0.45   | -0.08    | 0.01          | 5             | 5          | run-008      | 약한 연결 |
| research       | draft        | 0.68   | 0.03     | 0.01          | 7             | 3          | run-010      | 보통 |
| draft          | validate     | 0.92   | 0.03     | 0.01          | 10            | 0          | run-010      | 매우 강함 |
| validate       | refine       | 0.78   | -0.02    | 0.01          | 6             | 4          | run-009      | 개선 필요 |

## 필드 설명

- **from_task_type**: 시작 Task의 유형 (예: "analyze", "draft")
- **to_task_type**: 끝 Task의 유형
- **weight**: 연결 가중치 (0.1 ~ 0.99)
- **gradient**: 마지막 역전파에서 계산된 기울기
- **learning_rate**: 이 연결의 학습률
- **success_count**: 성공 횟수 (품질 기준 충족)
- **fail_count**: 실패 횟수
- **last_updated**: 마지막 업데이트된 Run ID
- **notes**: 메모 (선택사항)

## 사용 방법

1. **초기화**: `WeightManager.initialize_weights()`
2. **조회**: `WeightManager.get_weight(from_task, to_task)`
3. **학습**: `WeightManager.backward_pass()` - 자동 업데이트
4. **저장**: `WeightManager._save_weights()` - 자동 저장

## 가중치 해석

- **0.8 이상**: 매우 강한 연결 (거의 항상 성공)
- **0.6 ~ 0.8**: 강한 연결 (자주 성공)
- **0.4 ~ 0.6**: 보통 연결
- **0.4 미만**: 약한 연결 (개선 필요)
