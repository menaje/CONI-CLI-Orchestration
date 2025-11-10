# Execution History Database

모든 Task 실행 이력을 추적

## 스키마

| run_id | task_type | activation | confidence | executed | quality_score | execution_time | token_used | cost |
|--------|-----------|-----------|-----------|----------|---------------|----------------|------------|------|
| run-001 | analyze   | 0.95      | 0.88      | true     | 0.82          | 45s            | 8,500      | $0.26 |
| run-001 | research  | 0.42      | 0.65      | false    | -             | -              | 0          | $0.00 |
| run-001 | draft     | 0.87      | 0.91      | true     | 0.79          | 120s           | 15,000     | $0.45 |
| run-002 | analyze   | 0.93      | 0.90      | true     | 0.85          | 42s            | 7,200      | $0.22 |

## 필드 설명

- **run_id**: Run 고유 ID
- **task_type**: Task 유형 (analyze, draft, research 등)
- **activation**: 활성화 값
- **confidence**: 신뢰도
- **executed**: 실행 여부
- **quality_score**: 품질 점수
- **execution_time**: 실행 시간
- **token_used**: 사용 토큰
- **cost**: 비용 (USD)

## 분석 용도

### 1. Task 유형별 성능

```sql
SELECT task_type,
       AVG(quality_score) as avg_quality,
       AVG(execution_time) as avg_time,
       SUM(cost) as total_cost
FROM execution_history
WHERE executed = true
GROUP BY task_type
ORDER BY avg_quality DESC
```

### 2. 학습 곡선

```sql
SELECT run_id,
       AVG(quality_score) as avg_quality
FROM execution_history
WHERE executed = true
GROUP BY run_id
ORDER BY run_id
```

### 3. 비용 절감 효과

```sql
SELECT
    COUNT(*) as total_tasks,
    SUM(CASE WHEN executed THEN 1 ELSE 0 END) as executed_tasks,
    SUM(CASE WHEN NOT executed THEN 1 ELSE 0 END) as skipped_tasks,
    SUM(cost) as total_cost
FROM execution_history
```

## 기대 패턴

- **품질**: Run이 증가할수록 품질 상승
- **활성화율**: 점진적으로 감소 (불필요한 Task Skip)
- **비용**: 점진적으로 감소 (Attention + Skip)
