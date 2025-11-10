# Neural Tasks Database

Neural Task 실행 정보를 저장

## 스키마

| task_id | run_id | activation | confidence | threshold | executed | quality_score | execution_time | token_used | selected_files | output_path |
|---------|--------|-----------|-----------|-----------|----------|---------------|----------------|------------|----------------|-------------|
| tsk-01  | run-001 | 0.95     | 0.88      | 0.6       | true     | 0.82          | 45s            | 8,500      | ["data/doc1.md"] | workspace/task1.md |
| tsk-02  | run-001 | 0.45     | 0.62      | 0.6       | false    | -             | -              | 0          | -              | -           |
| tsk-03  | run-001 | 0.87     | 0.91      | 0.6       | true     | 0.89          | 120s           | 15,000     | ["data/doc2.md", "data/doc3.md"] | workspace/task3.md |

## 필드 설명

- **task_id**: Task 고유 ID
- **run_id**: 소속 Run ID
- **activation**: 활성화 값 (0~1)
- **confidence**: 결과 신뢰도 (0~1)
- **threshold**: 실행 임계값 (기본 0.6)
- **executed**: 실제로 실행되었는지 여부
- **quality_score**: 결과물 품질 점수 (0~1)
- **execution_time**: 실행 시간 (초)
- **token_used**: 사용한 LLM 토큰 수
- **selected_files**: Attention으로 선택된 파일들 (JSON 배열)
- **output_path**: 결과 파일 경로

## 활성화 메커니즘

```python
activation = sigmoid(weighted_sum)

if activation >= threshold:
    execute_task()  # 실행
else:
    skip_task()     # Skip (비용 절감!)
```

## 통계

- **Activation Rate**: executed / total
- **Avg Quality**: mean(quality_score where executed=true)
- **Token Savings**: sum(token_used where executed=false)
