# Neural-CONI Task Memory 통합 기획서

## 📋 문서 정보

- **프로젝트명**: Neural-CONI Task Memory Integration
- **부제**: Git Diff Vector Memory 기술을 Task 실행에 적용
- **버전**: 1.0
- **작성일**: 2025-01-07
- **작성자**: Neural-CONI Team
- **관련 문서**: Git_Diff_Vector_Memory_기획서.md

---

## 1. Executive Summary

### 1.1 핵심 아이디어

**Git Commit을 벡터로 저장하는 기술을 Task 실행에 적용하여, Neural-CONI를 자가 학습 시스템으로 진화시킨다.**

```
Git Diff Memory:
Commit → Problem + Solution (diff) → Vector DB
  → 코드 차원의 학습 ✓

Task Memory (NEW!):
Task → Purpose + Output → Vector DB
  → 업무 차원의 학습 ✓

통합:
코드 + 업무 = 완전한 경험 자산 시스템 🎯
```

### 1.2 Why This Matters

**현재 상황:**
```python
# Git Diff Memory
개발자의 코드 수정 경험 → 재활용 가능 ✓

# Neural-CONI
Task 실행 경험 → 사라짐 ✗
  → 매번 처음부터
  → 과거 성공 패턴 활용 불가
```

**개선 후:**
```python
# 통합 시스템
코드 수정 + Task 실행 → 모두 학습
  → 프로젝트 전체 경험 축적
  → 사용할수록 똑똑해짐
  → 팀 집단 지성 구현
```

### 1.3 핵심 가치

| 구분 | 현재 | 개선 후 | 효과 |
|------|------|---------|------|
| **Task 생성** | 수동 (2시간) | 자동 (10분) | **92% 감소** |
| **Task 실패율** | 20% | 5% | **75% 감소** |
| **새 프로젝트** | 2주 | 1주 | **50% 단축** |
| **재사용률** | 10% | 60% | **6배 증가** |

---

## 2. 문제 정의

### 2.1 현재 Neural-CONI의 한계

#### 문제 1: Task 경험의 휘발성

```python
# Run 1
Task: "사용자 행동 분석 보고서 작성"
  → Attention으로 파일 선택
  → 실행 (1시간)
  → 품질 0.85 (성공!)
  → DB 저장: quality_score만

# Run 2 (1주 후, 유사 Task)
Task: "고객 행동 패턴 분석 리포트"
  → 또 처음부터!
  → Attention 재계산
  → 과거 경험 활용 불가
  → 또 1시간
```

**문제:** Task를 어떻게 성공했는지 저장 안 됨!

#### 문제 2: Task 생성의 수동성

```python
# 현재
PM: "사용자 분석 프로젝트"
  → Task 20개 수동 작성
  → 2시간 소요
  → 과거 유사 프로젝트 참고 불가

# 원하는 것
PM: "사용자 분석 프로젝트"
  → 시스템: "과거 10개 유사 프로젝트 분석 완료"
  → 시스템: "Task 18개 자동 생성 (성공률 85% 패턴)"
  → PM: 리뷰만 (10분)
```

#### 문제 3: 실패 예측 불가

```python
# 현재
Task: "대용량 데이터 처리"
  → 실행 (3시간)
  → 메모리 부족 실패!
  → 과거 5번 같은 실수 했는데 모름

# 원하는 것
Task: "대용량 데이터 처리"
  → 시스템: "⚠️ 경고: 과거 5번 유사 Task 메모리 부족"
  → 시스템: "추천: 배치 크기 감소"
  → 설정 조정
  → 성공! (1시간)
```

#### 문제 4: 프로젝트 간 지식 단절

```python
# 프로젝트 A (6개월 전)
"인증 시스템 구현" → 성공 (2주)

# 프로젝트 B (현재)
"로그인 기능 개발" (유사!)
  → 프로젝트 A 경험 활용 불가
  → 또 2주...
```

### 2.2 Git Diff Memory와의 비교

| 구분 | Git Diff Memory | Neural-CONI (현재) |
|------|-----------------|-------------------|
| **저장 대상** | Commit (코드 변경) | Task 품질 점수만 |
| **내용** | Problem + Solution | 점수 숫자만 |
| **재사용** | 유사 문제 검색 가능 | 불가능 |
| **학습** | 코드 차원 ✓ | 학습 없음 ✗ |
| **프로젝트 독립성** | 가능 | 같은 프로젝트만 |

**통찰:** Git Diff Memory 방식을 Task에 적용하면?
→ **Task 차원의 학습 시스템 완성!**

---

## 3. 해결 방안

### 3.1 Task Execution Memory (핵심!)

**개념:** Task 실행을 Git Commit처럼 저장

```python
# Git Commit 방식
Before: 버그 있는 코드
After:  수정된 코드 (diff)
  → Vector DB 저장
  → 유사 버그 검색 가능

# Task 방식 (NEW!)
Before: Task Purpose (목적)
After:  Task Output (결과물)
  → Vector DB 저장
  → 유사 Task 검색 가능!
```

#### 구현 설계

```python
class TaskExecutionMemory:
    """
    Task 실행을 벡터로 저장 및 검색

    Git Diff Memory의 Task 버전
    """

    def save_task_execution(self,
                           task: NeuralTask,
                           execution_result: Dict):
        """
        Task 실행 저장

        저장 내용:
        - Purpose (목적): "분석 보고서 작성"
        - Output (결과): "## 분석 결과\n1. ..."
        - Context:
          - 선택된 파일들 (Attention)
          - 사용한 Weights
          - 실행 시간, 토큰 수
        - Quality: 0.85
        - Success: True
        """

        # 1. Purpose 임베딩 (Before)
        purpose_emb = self.embedding.embed_text(task.task_purpose)

        # 2. Output 임베딩 (After)
        output_emb = self.embedding.embed_text(execution_result['output'])

        # 3. Task Diff 생성
        diff = {
            "before": {
                "purpose": task.task_purpose,
                "selected_files": task.selected_files,
                "activation": task.activation_level,
                "threshold": task.threshold
            },
            "after": {
                "output": execution_result['output'],
                "quality": task.quality_score,
                "files_used": execution_result['files_used'],
                "tokens_used": task.token_used,
                "execution_time": task.execution_time
            },
            "improvement": task.quality_score - task.threshold
        }

        # 4. 자동 분류 (LLM)
        analysis = self.llm.analyze_task(
            task.task_purpose,
            execution_result['output']
        )
        # Output: {
        #   "category": "analysis",
        #   "difficulty": 0.7,
        #   "tags": ["data-analysis", "report", "visualization"]
        # }

        # 5. Vector DB 저장
        self.db.table("task_executions").insert({
            "task_id": task.task_id,
            "run_id": task.run_id,
            "project_id": self._get_project_id(),

            # Purpose (Before)
            "task_purpose": task.task_purpose,
            "purpose_embedding": purpose_emb.tolist(),

            # Output (After)
            "output_content": execution_result['output'],
            "output_embedding": output_emb.tolist(),

            # Context
            "selected_files": task.selected_files,
            "attention_weights": task.attention_weights,
            "weights_used": self._extract_weights(task),

            # Result
            "quality_score": task.quality_score,
            "execution_time": task.execution_time,
            "tokens_used": task.token_used,
            "success": task.quality_score >= 0.7,

            # Metadata
            "task_category": analysis['category'],
            "difficulty_level": analysis['difficulty'],
            "tags": analysis['tags'],

            # Diff
            "diff_json": diff
        }).execute()

        print(f"✓ Task Memory saved: {task.task_id} (Q={task.quality_score:.2f})")

    def search_similar_tasks(self,
                            task_purpose: str,
                            project_id: str = None,
                            min_quality: float = 0.7,
                            top_k: int = 5) -> List[Dict]:
        """
        유사한 과거 Task 검색

        Args:
            task_purpose: 현재 Task 목적
            project_id: 특정 프로젝트만 (None이면 모든 프로젝트)
            min_quality: 최소 품질 (낮은 품질 제외)
            top_k: 결과 개수

        Returns:
            유사한 과거 Task 리스트 (유사도 순)
        """
        # 1. Purpose 임베딩
        purpose_emb = self.embedding.embed_text(task_purpose)

        # 2. Vector DB 검색
        results = self.db.rpc("search_similar_tasks", {
            "query_embedding": purpose_emb.tolist(),
            "project_filter": project_id,
            "min_quality": min_quality,
            "match_count": top_k
        }).execute()

        return results.data

    def execute_with_memory(self, task: NeuralTask) -> Dict:
        """
        메모리를 활용한 Task 실행

        과거 유사 Task 검색 → 경험 활용 → 실행
        """
        # 1. 유사한 과거 Task 검색
        similar = self.search_similar_tasks(
            task.task_purpose,
            min_quality=0.7,
            top_k=3
        )

        if similar:
            best = similar[0]

            print(f"\n💡 유사 Task 발견!")
            print(f"   과거: {best['task_purpose']}")
            print(f"   유사도: {best['similarity']:.0%}")
            print(f"   품질: {best['quality_score']:.0%}")
            print(f"   사용 파일: {best['selected_files'][:3]}")

            # 2. Attention에 Memory boost 적용
            memory_boost = self._calculate_memory_boost(best, task)
            task.attention_weights = self._combine_attention(
                current_attention=self._compute_attention(task),
                memory_boost=memory_boost,
                weight=0.3  # 30% memory, 70% current
            )

            # 3. 추천 파일 추가
            for file in best['selected_files']:
                if file not in task.selected_files:
                    task.related_references.append(file)

        # 4. 실행
        result = self._execute_task(task)

        # 5. 저장 (학습!)
        self.save_task_execution(task, result)

        return result
```

#### DB 스키마

```sql
-- Task Executions
CREATE TABLE task_executions (
  id SERIAL PRIMARY KEY,

  -- Task 정보
  task_id VARCHAR(10) NOT NULL,
  run_id VARCHAR(10) NOT NULL,
  project_id VARCHAR(100),

  -- Purpose (Before)
  task_purpose TEXT NOT NULL,
  purpose_embedding VECTOR(768),

  -- Output (After)
  output_content TEXT,
  output_embedding VECTOR(768),

  -- Context
  selected_files JSONB,
  attention_weights JSONB,
  weights_used JSONB,

  -- Result
  quality_score FLOAT,
  execution_time FLOAT,
  tokens_used INT,
  success BOOLEAN,

  -- Metadata
  task_category VARCHAR(50),  -- analysis, coding, writing, etc
  difficulty_level FLOAT,     -- 0~1 (자동 추정)
  tags JSONB,                 -- ["data-analysis", "report"]

  -- Diff
  diff_json JSONB,

  executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW 인덱스 (고속 벡터 검색)
CREATE INDEX idx_task_purpose_vector
  ON task_executions USING hnsw (purpose_embedding vector_cosine_ops);

CREATE INDEX idx_task_output_vector
  ON task_executions USING hnsw (output_embedding vector_cosine_ops);

-- 일반 인덱스
CREATE INDEX idx_task_project ON task_executions(project_id);
CREATE INDEX idx_task_category ON task_executions(task_category);
CREATE INDEX idx_task_quality ON task_executions(quality_score DESC);
CREATE INDEX idx_task_success ON task_executions(success);

-- 검색 함수
CREATE OR REPLACE FUNCTION search_similar_tasks(
  query_embedding VECTOR(768),
  project_filter VARCHAR(100) DEFAULT NULL,
  min_quality FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  task_id VARCHAR(10),
  task_purpose TEXT,
  output_content TEXT,
  similarity FLOAT,
  quality_score FLOAT,
  selected_files JSONB,
  attention_weights JSONB
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    task_id,
    task_purpose,
    output_content,
    1 - (purpose_embedding <=> query_embedding) AS similarity,
    quality_score,
    selected_files,
    attention_weights
  FROM task_executions
  WHERE
    (project_filter IS NULL OR project_id = project_filter)
    AND quality_score >= min_quality
    AND success = true
  ORDER BY purpose_embedding <=> query_embedding
  LIMIT match_count;
$$;
```

---

### 3.2 Task Auto-Generation

**혁신:** 과거 패턴 학습 → 자동 Task 생성

```python
class TaskGenerator:
    """
    과거 성공 패턴 학습 → 새 Task 자동 생성

    Example:
    User: "사용자 행동 분석 보고서"
    → 과거 10개 유사 프로젝트 검색
    → 성공했던 Task 시퀀스 추출
    → Task 자동 생성 (18개)
    → PM은 리뷰만
    """

    def suggest_tasks(self,
                     user_request: str,
                     context: Dict) -> List[NeuralTask]:
        """
        사용자 요청 → 자동 Task 생성

        Args:
            user_request: "사용자 행동 분석 보고서 작성"
            context: {
                "current_phase": "phs-01",
                "current_stage": "stg-01",
                "available_files": [...]
            }

        Returns:
            자동 생성된 Task 리스트
        """
        # 1. 요청 분석 (LLM)
        analysis = self.llm.analyze_request(user_request)
        # Output: {
        #   "main_goal": "user behavior analysis report",
        #   "key_tasks": ["data collection", "analysis", "visualization", "report"],
        #   "estimated_difficulty": 0.7
        # }

        # 2. 유사한 과거 Run 검색
        request_emb = self.embedding.embed_text(analysis['main_goal'])

        similar_runs = self.db.table("task_executions") \
            .select("*") \
            .eq("success", True) \
            .execute()

        # 벡터 유사도 계산하여 Top-K 선택
        similar_runs_filtered = self._filter_by_similarity(
            similar_runs.data,
            request_emb,
            min_similarity=0.7,
            top_k=10
        )

        # 3. Task 패턴 추출
        task_patterns = self._extract_task_patterns(similar_runs_filtered)
        # Output: [
        #   {
        #     "task_name": "데이터 수집",
        #     "purpose_template": "Collect {data_type} from {source}",
        #     "success_rate": 0.9,
        #     "avg_quality": 0.85,
        #     "common_files": ["data_loader.py", "api_client.py"],
        #     "avg_threshold": 0.6
        #   },
        #   ...
        # ]

        # 4. Task 자동 생성
        generated_tasks = []
        for i, pattern in enumerate(task_patterns):
            # LLM으로 템플릿 → 구체적 Task
            concrete_purpose = self.llm.adapt_template(
                template=pattern['purpose_template'],
                user_request=user_request
            )

            task = NeuralTask(
                task_id=f"tsk-{i+1:02d}",
                run_id=context['run_id'],
                sub_stage_id=context['current_substage'],

                task_name=pattern['task_name'],
                task_purpose=concrete_purpose,
                task_reason=f"Based on {pattern['success_rate']:.0%} success pattern",

                threshold=pattern['avg_threshold'],
                related_references=pattern['common_files'],

                # 메타데이터
                confidence=pattern['success_rate'],
                quality_history=[pattern['avg_quality']]
            )

            generated_tasks.append(task)

        # 5. 설명 생성
        explanation = self._generate_explanation(
            generated_tasks,
            similar_runs_filtered,
            analysis
        )

        return {
            "tasks": generated_tasks,
            "explanation": explanation,
            "confidence": np.mean([p['success_rate'] for p in task_patterns]),
            "based_on": len(similar_runs_filtered)
        }

    def _extract_task_patterns(self, similar_runs: List[Dict]) -> List[Dict]:
        """
        유사 Run들에서 공통 Task 패턴 추출

        Example:
        Run 1: [Task A, Task B, Task C] → Quality 0.9
        Run 2: [Task A, Task B, Task D] → Quality 0.8
        Run 3: [Task A, Task C] → Quality 0.6

        → 패턴:
          - Task A: 100% 출현, 평균 품질 0.77
          - Task B: 67% 출현, 평균 품질 0.85
          - Task C: 67% 출현, 평균 품질 0.75

        → Task B가 가장 효과적!
        """
        # Task 출현 빈도 및 품질 통계
        task_stats = {}

        for run in similar_runs:
            task = run['task_purpose']

            if task not in task_stats:
                task_stats[task] = {
                    "count": 0,
                    "qualities": [],
                    "thresholds": [],
                    "files": []
                }

            task_stats[task]["count"] += 1
            task_stats[task]["qualities"].append(run['quality_score'])
            task_stats[task]["thresholds"].append(run.get('threshold', 0.6))
            task_stats[task]["files"].extend(run['selected_files'])

        # 패턴 생성
        patterns = []
        for task, stats in task_stats.items():
            occurrence_rate = stats["count"] / len(similar_runs)

            # 최소 30% 이상 출현한 Task만
            if occurrence_rate >= 0.3:
                patterns.append({
                    "task_name": self._extract_task_name(task),
                    "purpose_template": self._generalize_purpose(task),
                    "success_rate": occurrence_rate,
                    "avg_quality": np.mean(stats["qualities"]),
                    "common_files": self._most_common_files(stats["files"]),
                    "avg_threshold": np.mean(stats["thresholds"])
                })

        # 효과성 순 정렬 (출현율 × 품질)
        patterns.sort(
            key=lambda p: p['success_rate'] * p['avg_quality'],
            reverse=True
        )

        return patterns
```

#### 사용 예시

```python
# PM의 요청
user_request = "고객 행동 패턴 분석 리포트 작성"

# Task 자동 생성
generator = TaskGenerator()
result = generator.suggest_tasks(user_request, context)

print(f"\n📋 자동 생성된 Task: {len(result['tasks'])}개")
print(f"신뢰도: {result['confidence']:.0%}")
print(f"기반 데이터: {result['based_on']}개 과거 프로젝트\n")

print(result['explanation'])
# Output:
# """
# 과거 10개 유사 프로젝트 분석 결과:
#
# 【추천 Task 구조】(성공률 85%)
#
# 1. 데이터 수집 및 전처리 (필수, 100% 출현)
#    - 품질: 0.87 | 임계값: 0.6
#    - 주요 파일: data_loader.py, preprocessor.py
#
# 2. 행동 패턴 분석 (필수, 100% 출현)
#    - 품질: 0.83 | 임계값: 0.65
#    - 주요 파일: analyzer.py, statistics.py
#
# 3. 시각화 생성 (권장, 80% 출현)
#    - 품질: 0.78 | 임계값: 0.6
#    - 주요 파일: visualizer.py, plotter.py
#
# ...
# """

# PM 리뷰
for task in result['tasks']:
    print(f"[{task.task_id}] {task.task_name}")
    print(f"  목적: {task.task_purpose}")
    print(f"  신뢰도: {task.confidence:.0%}\n")

# 조정 후 승인
approved_tasks = pm_review(result['tasks'])
```

---

### 3.3 Failure Prediction

**목표:** Task 실행 전 실패 가능성 예측 및 회피

```python
class FailurePredictor:
    """
    과거 실패 패턴 학습 → 위험 예측
    """

    def predict_failure_risk(self, task: NeuralTask) -> Dict:
        """
        Task 실패 위험도 예측

        Returns:
            {
                "risk_level": "HIGH" | "MEDIUM" | "LOW",
                "risk_score": 0.85,
                "similar_failures": 5,
                "failure_patterns": [...],
                "recommendations": [...]
            }
        """
        # 1. Task 특성 추출
        purpose_emb = self.embedding.embed_text(task.task_purpose)

        # 2. 유사한 과거 실패 Task 검색
        failed_tasks = self.db.table("task_executions") \
            .select("*") \
            .eq("success", False) \
            .execute()

        # 3. 유사도 계산
        risks = []
        for failed in failed_tasks.data:
            similarity = cosine_similarity(
                purpose_emb,
                np.array(failed['purpose_embedding'])
            )

            if similarity > 0.75:  # 매우 유사
                risks.append({
                    "past_task": failed['task_purpose'],
                    "similarity": similarity,
                    "quality_score": failed['quality_score'],
                    "failure_reason": failed.get('error_message', 'Unknown'),
                    "execution_time": failed['execution_time'],
                    "selected_files": failed['selected_files']
                })

        # 4. 위험도 판단
        if not risks:
            return {
                "risk_level": "LOW",
                "risk_score": 0.1,
                "similar_failures": 0
            }

        avg_similarity = np.mean([r['similarity'] for r in risks])
        risk_score = avg_similarity * (len(risks) / 10)  # 정규화

        # 5. 실패 패턴 분석
        failure_patterns = self._analyze_failure_patterns(risks)

        # 6. 추천 생성
        recommendations = self._generate_recommendations(
            failure_patterns,
            task
        )

        return {
            "risk_level": self._classify_risk(risk_score),
            "risk_score": risk_score,
            "similar_failures": len(risks),
            "failure_patterns": failure_patterns,
            "recommendations": recommendations,
            "top_risks": risks[:3]  # 가장 유사한 3개
        }

    def _analyze_failure_patterns(self, risks: List[Dict]) -> List[Dict]:
        """실패 패턴 분류"""
        patterns = {}

        for risk in risks:
            reason = risk['failure_reason']

            # 패턴 분류
            if "파일" in reason or "file" in reason.lower():
                category = "missing_file"
            elif "메모리" in reason or "memory" in reason.lower():
                category = "memory_issue"
            elif "timeout" in reason.lower() or "시간" in reason:
                category = "timeout"
            elif "권한" in reason or "permission" in reason.lower():
                category = "permission_error"
            else:
                category = "other"

            if category not in patterns:
                patterns[category] = {
                    "category": category,
                    "count": 0,
                    "examples": []
                }

            patterns[category]["count"] += 1
            patterns[category]["examples"].append(reason)

        # 빈도순 정렬
        return sorted(
            patterns.values(),
            key=lambda p: p['count'],
            reverse=True
        )

    def _generate_recommendations(self,
                                 patterns: List[Dict],
                                 task: NeuralTask) -> List[str]:
        """패턴 기반 추천 생성"""
        recommendations = []

        for pattern in patterns:
            if pattern['category'] == 'missing_file':
                recommendations.append(
                    f"⚠️ 파일 누락 위험 ({pattern['count']}회)\n"
                    f"   → 추천: {', '.join(task.related_references[:3])} 파일 존재 확인"
                )

            elif pattern['category'] == 'memory_issue':
                recommendations.append(
                    f"⚠️ 메모리 부족 위험 ({pattern['count']}회)\n"
                    f"   → 추천: 배치 크기 감소 또는 청크 처리"
                )

            elif pattern['category'] == 'timeout':
                recommendations.append(
                    f"⚠️ 타임아웃 위험 ({pattern['count']}회)\n"
                    f"   → 추천: 실행 시간 제한 증가 또는 작업 분할"
                )

            elif pattern['category'] == 'permission_error':
                recommendations.append(
                    f"⚠️ 권한 오류 위험 ({pattern['count']}회)\n"
                    f"   → 추천: 파일/디렉토리 권한 확인"
                )

        return recommendations

    def _classify_risk(self, risk_score: float) -> str:
        """위험도 분류"""
        if risk_score >= 0.7:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
```

#### 사용 예시

```python
# Task 실행 전 체크
def safe_execute_task(task: NeuralTask):
    predictor = FailurePredictor()
    risk = predictor.predict_failure_risk(task)

    print(f"\n🔍 Task 위험도 분석: {task.task_name}")
    print(f"   위험 수준: {risk['risk_level']}")
    print(f"   위험 점수: {risk['risk_score']:.0%}")
    print(f"   유사 실패: {risk['similar_failures']}건\n")

    if risk['risk_level'] in ['HIGH', 'MEDIUM']:
        print("⚠️ 경고 사항:")
        for rec in risk['recommendations']:
            print(f"   {rec}\n")

        # 사용자 확인
        if risk['risk_level'] == 'HIGH':
            response = input("계속 진행하시겠습니까? (y/n): ")
            if response.lower() != 'y':
                print("Task 건너뜀")
                return skip_task(task)

    # 실행
    return execute_task(task)
```

---

### 3.4 Task Order Optimization

**목표:** 최적 Task 실행 순서 학습

```python
class TaskOrderOptimizer:
    """
    과거 성공 패턴에서 최적 Task 순서 학습

    Example:
    과거 데이터:
    - Run 1: [A→B→C] → Quality 0.6 (실패)
    - Run 2: [A→C→B] → Quality 0.9 (성공!)
    - Run 3: [C→A→B] → Quality 0.5 (실패)

    → 학습: A→C→B 순서가 최적!
    """

    def optimize_order(self, tasks: List[NeuralTask]) -> List[NeuralTask]:
        """
        Task 순서 최적화

        Returns:
            재정렬된 Task 리스트
        """
        # 1. Task 이름 추출
        task_names = [t.task_name for t in tasks]

        # 2. 과거 순서 패턴 검색
        patterns = self._search_order_patterns(task_names)

        if not patterns:
            print("순서 패턴 없음 - 원래 순서 유지")
            return tasks

        # 3. 최고 품질 순서 선택
        best_pattern = max(patterns, key=lambda p: p['avg_quality'])

        print(f"\n💡 최적 순서 발견!")
        print(f"   과거 품질: {best_pattern['avg_quality']:.0%}")
        print(f"   출현: {best_pattern['count']}회")
        print(f"   순서: {' → '.join(best_pattern['order'])}\n")

        # 4. 재정렬
        reordered = self._reorder_tasks(tasks, best_pattern['order'])

        return reordered

    def _search_order_patterns(self, task_names: List[str]) -> List[Dict]:
        """과거 순서 패턴 검색"""
        # DB에서 유사한 Task 조합 검색
        result = self.db.rpc("search_task_sequences", {
            "task_names": task_names
        }).execute()

        return result.data
```

#### DB 스키마 (추가)

```sql
-- Task Order Patterns
CREATE TABLE task_order_patterns (
  id SERIAL PRIMARY KEY,

  -- Task 시퀀스
  task_sequence JSONB NOT NULL,  -- ["Task A", "Task B", "Task C"]
  task_count INT NOT NULL,

  -- 통계
  occurrence_count INT DEFAULT 0,
  avg_quality FLOAT,
  success_rate FLOAT,

  -- 메타데이터
  project_ids JSONB,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_task_sequence ON task_order_patterns USING GIN (task_sequence);
CREATE INDEX idx_task_quality ON task_order_patterns(avg_quality DESC);
```

---

### 3.5 Cross-Project Learning

**목표:** 프로젝트 간 지식 전이

```python
class CrossProjectLearning:
    """
    다른 프로젝트의 경험 활용

    Example:
    프로젝트 A (6개월 전): "사용자 인증 구현"
    프로젝트 B (현재): "로그인 시스템 개발"

    → 유사한 Task! 프로젝트 A 경험 활용
    """

    def recommend_from_other_projects(self,
                                      task: NeuralTask) -> List[Dict]:
        """
        다른 프로젝트의 유사 Task 경험 검색
        """
        # 1. Task 추상화 (LLM)
        abstract_purpose = self.llm.abstract_task(task.task_purpose)
        # Input: "Django 프로젝트에 OAuth2 인증 추가"
        # Output: "authentication system implementation"

        # 2. 추상화된 목적으로 검색
        abstract_emb = self.embedding.embed_text(abstract_purpose)

        # 3. 모든 프로젝트에서 검색
        all_tasks = self.db.table("task_executions") \
            .select("*") \
            .eq("success", True) \
            .execute()

        # 4. 유사도 계산 (같은 프로젝트 제외)
        recommendations = []
        for task_exec in all_tasks.data:
            if task_exec['project_id'] == self._current_project_id():
                continue  # 같은 프로젝트 제외

            similarity = cosine_similarity(
                abstract_emb,
                np.array(task_exec['purpose_embedding'])
            )

            if similarity > 0.7:
                recommendations.append({
                    "project": task_exec['project_id'],
                    "task": task_exec['task_purpose'],
                    "similarity": similarity,
                    "quality": task_exec['quality_score'],
                    "files": task_exec['selected_files'],
                    "approach": task_exec['output_content'][:300],
                    "execution_time": task_exec['execution_time']
                })

        # 5. 종합 점수 순 정렬
        recommendations.sort(
            key=lambda x: x['similarity'] * x['quality'],
            reverse=True
        )

        return recommendations[:5]  # Top 5
```

#### 사용 예시

```python
# 새 프로젝트에서 Task 실행
task = NeuralTask(
    task_name="인증 시스템 구현",
    task_purpose="사용자 로그인 및 권한 관리 시스템 개발"
)

# 다른 프로젝트 경험 검색
cross_learning = CrossProjectLearning()
recommendations = cross_learning.recommend_from_other_projects(task)

if recommendations:
    print("\n🌐 다른 프로젝트 경험 발견!\n")

    for i, rec in enumerate(recommendations, 1):
        print(f"[{i}] 프로젝트: {rec['project']}")
        print(f"    Task: {rec['task']}")
        print(f"    유사도: {rec['similarity']:.0%}")
        print(f"    품질: {rec['quality']:.0%}")
        print(f"    소요 시간: {rec['execution_time']:.1f}초")
        print(f"    접근 방법:")
        print(f"    {rec['approach']}")
        print()

    # 사용자 선택
    choice = input("참고할 경험을 선택하세요 (1-5, 0=건너뛰기): ")

    if choice != '0':
        selected = recommendations[int(choice) - 1]
        # 선택된 경험의 파일 목록을 현재 Task에 추가
        task.related_references.extend(selected['files'])
```

---

## 4. 통합 아키텍처

### 4.1 전체 구조

```
┌─────────────────────────────────────────────────────────┐
│  User Interface (CLI/Web)                               │
│  - Task 생성/관리                                        │
│  - 실행 모니터링                                         │
└─────────────────────────────────────────────────────────┘
                    ↓ ↑
┌─────────────────────────────────────────────────────────┐
│  Neural-CONI Orchestrator                               │
│  - Task 생성 및 스케줄링                                 │
│  - DAG 기반 병렬 실행                                    │
│  - Weights, Attention, Backpropagation                  │
└─────────────────────────────────────────────────────────┘
                    ↓ ↑
┌─────────────────────────────────────────────────────────┐
│  Task Intelligence Layer (NEW!) 🌟                      │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │ TaskExecution    │  │ TaskGenerator    │            │
│  │ Memory           │  │ (자동 생성)      │            │
│  │ (실행 저장/검색) │  └──────────────────┘            │
│  └──────────────────┘                                   │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │ FailurePredictor │  │ OrderOptimizer   │            │
│  │ (실패 예측)      │  │ (순서 최적화)    │            │
│  └──────────────────┘  └──────────────────┘            │
│                                                          │
│  ┌──────────────────┐                                   │
│  │ CrossProject     │                                   │
│  │ Learning         │                                   │
│  │ (지식 전이)      │                                   │
│  └──────────────────┘                                   │
└─────────────────────────────────────────────────────────┘
                    ↓ ↑
┌─────────────────────────────────────────────────────────┐
│  LLM Layer (Ollama/LM Studio)                           │
│  - Task 분석 및 분류                                     │
│  - Task 추상화                                           │
│  - 설명 생성                                             │
└─────────────────────────────────────────────────────────┘
                    ↓ ↑
┌─────────────────────────────────────────────────────────┐
│  Embedding Engine (CodeBERT)                            │
│  - Task purpose 임베딩 (768차원)                        │
│  - Output 임베딩 (768차원)                              │
└─────────────────────────────────────────────────────────┘
                    ↓ ↑
┌─────────────────────────────────────────────────────────┐
│  Unified Vector Memory (Supabase pgvector)              │
│                                                          │
│  ┌────────────────┐  ┌────────────────┐                │
│  │ code_changes   │  │ task_executions│ ← NEW!         │
│  │ (Git Diff)     │  │ (Task Memory)  │                │
│  └────────────────┘  └────────────────┘                │
│                                                          │
│  ┌────────────────┐  ┌────────────────┐                │
│  │ task_order_    │  │ task_          │                │
│  │ patterns       │  │ abstractions   │                │
│  └────────────────┘  └────────────────┘                │
└─────────────────────────────────────────────────────────┘
```

### 4.2 데이터 흐름

```
1. Task 생성 요청
   User: "사용자 행동 분석 보고서"
     ↓
   TaskGenerator: 과거 패턴 검색
     ↓
   자동 생성: Task 18개
     ↓
   PM 승인

2. Task 실행 전
   Task: "데이터 수집 및 전처리"
     ↓
   FailurePredictor: 위험도 체크
     ↓
   TaskExecutionMemory: 유사 Task 검색
     ↓
   Memory boost 적용

3. Task 실행
   Execute with enhanced context
     ↓
   Output 생성
     ↓
   Quality 측정

4. Task 실행 후
   TaskExecutionMemory: 저장
     ↓
   Vector DB: 임베딩 + 메타데이터
     ↓
   Pattern Learning: 패턴 업데이트

5. 다음 Task 실행
   (1단계부터 반복, 점점 똑똑해짐!)
```

---

## 5. 구현 계획

### 5.1 Phase 1: Task Execution Memory (Week 1-2)

**목표:** 핵심 저장/검색 기능

| Task | 설명 | 소요 |
|------|------|------|
| DB 스키마 확장 | task_executions 테이블 추가 | 0.5일 |
| TaskExecutionMemory 구현 | 저장/검색 로직 | 2일 |
| Vector 검색 함수 | search_similar_tasks SQL | 0.5일 |
| Memory-boosted Attention | 과거 경험 통합 | 1일 |
| 테스트 | 단위/통합 테스트 | 1일 |
| 문서화 | 사용 가이드 | 0.5일 |

**마일스톤:**
- ✅ Task 실행이 저장됨
- ✅ 유사 Task 검색 가능
- ✅ Memory로 Attention 개선

### 5.2 Phase 2: Failure Prediction (Week 3)

**목표:** 실패 예측 및 방지

| Task | 설명 | 소요 |
|------|------|------|
| FailurePredictor 구현 | 위험도 분석 로직 | 1.5일 |
| 패턴 분석 | 실패 원인 분류 | 1일 |
| 추천 시스템 | 회피 방법 생성 | 1일 |
| UI 통합 | 경고 표시 | 0.5일 |
| 테스트 | 다양한 실패 시나리오 | 1일 |

**마일스톤:**
- ✅ Task 실행 전 위험도 알림
- ✅ 실패 회피 추천 제공
- ✅ 실패율 감소

### 5.3 Phase 3: Task Auto-Generation (Week 4-5)

**목표:** Task 자동 생성

| Task | 설명 | 소요 |
|------|------|------|
| TaskGenerator 구현 | 패턴 추출 로직 | 2일 |
| LLM 통합 | 요청 분석, 템플릿 적용 | 1일 |
| 신뢰도 계산 | 패턴 기반 신뢰도 | 1일 |
| UI 개선 | Task 리뷰 인터페이스 | 1일 |
| 테스트 | 다양한 요청 유형 | 1일 |
| 문서화 | 생성 가이드 | 0.5일 |

**마일스톤:**
- ✅ 사용자 요청 → 자동 Task 생성
- ✅ PM 리뷰만 필요
- ✅ Task 생성 시간 90% 감소

### 5.4 Phase 4: Advanced Features (Week 6)

**목표:** 순서 최적화 및 지식 전이

| Task | 설명 | 소요 |
|------|------|------|
| OrderOptimizer 구현 | 순서 패턴 학습 | 1.5일 |
| CrossProjectLearning | Task 추상화, 검색 | 2일 |
| 통합 테스트 | 전체 시스템 | 1일 |
| 성능 최적화 | 캐싱, 배치 처리 | 1일 |
| 문서화 | 완전한 가이드 | 0.5일 |

**마일스톤:**
- ✅ 최적 실행 순서 자동 결정
- ✅ 프로젝트 간 지식 재사용
- ✅ 전체 시스템 통합 완료

---

## 6. 사용 시나리오

### 6.1 시나리오 A: 자동 Task 생성

**Before (현재):**
```
PM: "사용자 행동 분석 리포트 작성"
  ↓
수동으로 Task 20개 작성
  - Task 1: 데이터 수집
  - Task 2: 전처리
  - Task 3: ...
  ↓
2시간 소요
```

**After (개선):**
```
PM: "사용자 행동 분석 리포트 작성"
  ↓
TaskGenerator 자동 실행
  → 과거 10개 유사 프로젝트 분석
  → Task 18개 자동 생성

출력:
📋 자동 생성된 Task (신뢰도 85%)

[tsk-01] 데이터 수집 및 검증
  목적: 사용자 행동 로그 데이터 수집 및 품질 검증
  신뢰도: 92% (과거 10/10 성공)
  추천 파일: data_loader.py, validator.py

[tsk-02] 데이터 전처리
  목적: 결측치 처리 및 정규화
  신뢰도: 88% (과거 9/10 성공)
  추천 파일: preprocessor.py

...

  ↓
PM 리뷰 (10분)
  - tsk-05 제거
  - tsk-12 목적 수정
  ↓
승인!

절감: 1시간 50분 (92%)
```

### 6.2 시나리오 B: 실패 예측 및 회피

**Before (현재):**
```
Task: "대규모 데이터 시각화 생성"
  ↓
실행 (3시간)
  ↓
메모리 부족으로 실패!
  ↓
설정 조정
  ↓
재실행 (3시간)
  ↓
성공

총: 6시간
```

**After (개선):**
```
Task: "대규모 데이터 시각화 생성"
  ↓
FailurePredictor 실행

출력:
🔍 Task 위험도 분석
   위험 수준: HIGH
   위험 점수: 82%
   유사 실패: 5건

⚠️ 경고 사항:

1. 메모리 부족 위험 (5회)
   → 추천: 청크 단위 처리 또는 해상도 감소

2. 타임아웃 위험 (3회)
   → 추천: 병렬 처리 또는 작업 분할

과거 해결 사례:
- 프로젝트 "customer_analytics":
  청크 크기 1000 → 100으로 변경하여 해결

계속 진행하시겠습니까? (y/n): n

  ↓
설정 조정 (5분)
  - 청크 크기: 100
  - 병렬 처리: 4 workers
  ↓
실행 (1.5시간)
  ↓
성공!

총: 1.5시간 (75% 단축)
실패 없음 ✓
```

### 6.3 시나리오 C: Cross-Project 지식 활용

**Before (현재):**
```
새 프로젝트: "전자상거래 결제 시스템 구축"
  ↓
처음부터 설계
  ↓
시행착오
  ↓
2주 소요
```

**After (개선):**
```
새 프로젝트: "전자상거래 결제 시스템 구축"
  ↓
CrossProjectLearning 검색

출력:
🌐 다른 프로젝트 경험 발견! (3건)

[1] 프로젝트: subscription_platform (6개월 전)
    Task: 구독 결제 시스템 구현
    유사도: 87%
    품질: 92%
    소요: 10일

    접근 방법:
    - Stripe API 통합
    - 결제 재시도 로직 구현
    - Webhook 처리 최적화

[2] 프로젝트: marketplace (1년 전)
    Task: 다중 결제 수단 지원
    유사도: 82%
    품질: 85%

[3] ...

참고할 경험을 선택하세요 (1-3, 0=건너뛰기): 1

  ↓
선택된 경험의 Task 구조 적용
  ↓
TaskGenerator가 자동으로 Task 생성
  - [1]의 Task 시퀀스 참고
  - [1]에서 사용한 파일 목록 추천
  ↓
실행
  ↓
1주 소요!

절감: 1주 (50%)
품질: 이전 프로젝트 수준 유지
```

### 6.4 시나리오 D: 순서 최적화

**Before (현재):**
```
Tasks: [A, B, C, D, E]
  ↓
순서대로 실행
  ↓
품질: 0.65 (실패)
```

**After (개선):**
```
Tasks: [A, B, C, D, E]
  ↓
TaskOrderOptimizer 실행

출력:
💡 최적 순서 발견!

과거 패턴 분석 (12개 유사 Run):
- 순서 [A→B→C→D→E]: 품질 0.65 (4회)
- 순서 [A→C→B→D→E]: 품질 0.88 (5회) ✓
- 순서 [C→A→B→D→E]: 품질 0.52 (3회)

최적 순서: [A→C→B→D→E]
성공률: 92%

재정렬하시겠습니까? (y/n): y

  ↓
재정렬: [A, C, B, D, E]
  ↓
실행
  ↓
품질: 0.86 (성공!)

개선: +32%
```

---

## 7. 기대 효과

### 7.1 정량적 효과

| 지표 | 현재 | Phase 1 | Phase 3 | Phase 4 | 최종 개선 |
|------|------|---------|---------|---------|-----------|
| **Task 생성 시간** | 2시간 | 1.5시간 | 10분 | 10분 | **92%↓** |
| **Task 실패율** | 20% | 12% | 8% | 5% | **75%↓** |
| **새 프로젝트 시작** | 2주 | 1.5주 | 1주 | 1주 | **50%↓** |
| **품질 일관성** | 70% | 78% | 85% | 90% | **29%↑** |
| **재사용률** | 10% | 30% | 50% | 60% | **6배↑** |
| **개발 생산성** | 100% | 130% | 180% | 200% | **2배↑** |

### 7.2 정성적 효과

#### 개발자 경험
- ✅ 과거 성공 패턴 즉시 활용
- ✅ 실패 사전 예방 (스트레스 감소)
- ✅ 반복 작업 자동화
- ✅ 학습 곡선 완화

#### 팀 협업
- ✅ 집단 지성 자동 공유
- ✅ 신입 온보딩 가속
- ✅ 베스트 프랙티스 자동 전파
- ✅ 프로젝트 간 지식 전이

#### 조직 자산
- ✅ 암묵적 지식 명시화
- ✅ 퇴사자 지식 보존
- ✅ 경험 축적 자동화
- ✅ 데이터 기반 의사결정

### 7.3 ROI 분석 (10명 팀 기준)

**투자 비용:**
```
개발: 6주 × 1명 = 약 1,500만원
인프라: Supabase 무료 티어 = 0원
운영: 최소 관리 = 0원
──────────────────────────
총 투자: 1,500만원
```

**연간 절감:**
```
Task 생성 시간:
  - 주 2회 × 2시간 → 10분
  - 절감: 1.8시간/주 × 10명 × 50주
  - = 900시간/년 × 5만원 = 4,500만원

실패 복구 시간:
  - 실패율 20% → 5% (75% 감소)
  - 실패당 평균 2시간 손실
  - 주 10 Task × 15% 감소 = 1.5 Task
  - = 3시간/주 × 10명 × 50주
  - = 1,500시간/년 × 5만원 = 7,500만원

새 프로젝트 시작:
  - 분기당 1개 × 1주 절감 × 10명
  - = 4주 × 10명 × 40시간
  - = 1,600시간/년 × 5만원 = 8,000만원
──────────────────────────
총 절감: 2억원/년
```

**ROI:**
```
(2억 - 1,500만) / 1,500만 × 100
= 1,233% (첫 해)

Break-even: 약 1개월
```

---

## 8. 리스크 및 대응

### 8.1 기술적 리스크

| 리스크 | 영향 | 확률 | 대응 방안 |
|--------|------|------|-----------|
| **Task 유사도 정확도** | 높음 | 중간 | 하이브리드 검색 (벡터 + 키워드) |
| **자동 생성 품질** | 높음 | 중간 | PM 리뷰 필수, 신뢰도 표시 |
| **Vector DB 용량** | 중간 | 낮음 | 오래된 데이터 아카이브 |
| **LLM 분석 정확도** | 중간 | 낮음 | 사용자 피드백으로 개선 |

### 8.2 운영 리스크

| 리스크 | 영향 | 확률 | 대응 방안 |
|--------|------|------|-----------|
| **사용자 채택** | 높음 | 중간 | 단계적 도입, 교육 |
| **과도한 의존** | 중간 | 낮음 | 수동 모드 옵션 제공 |
| **데이터 품질** | 중간 | 중간 | 품질 필터링, 주기적 정제 |

---

## 9. 성공 지표 (KPI)

| 지표 | 목표 (3개월) | 측정 방법 |
|------|--------------|-----------|
| **메모리 적중률** | 60% | 유사 Task 발견 비율 |
| **자동 생성 사용률** | 70% | TaskGenerator 사용 비율 |
| **실패 예측 정확도** | 75% | 예측한 실패 실제 발생 비율 |
| **Task 재사용률** | 50% | 과거 패턴 활용 비율 |
| **사용자 만족도** | 4.0/5.0 | 설문 조사 |
| **시간 절감** | 50% | 실제 측정 |

---

## 10. 확장 계획

### 10.1 Phase 2 고급 기능

**1. Task 품질 자동 평가**
```python
# LLM이 Task 결과물 자동 평가
auto_quality = evaluate_task_output(task.output)
  → 사람 개입 최소화
```

**2. Task 자동 분할**
```python
# 큰 Task를 자동으로 작은 Task들로 분할
if task.estimated_time > 2h:
    sub_tasks = split_task(task)
```

**3. 실시간 Task 추천**
```python
# Task 실행 중 다음 Task 미리 추천
while executing(current_task):
    next_tasks = recommend_next(current_task)
```

### 10.2 통합 확장

- **IDE 플러그인** (VSCode)
- **Slack 봇** (Task 상태 알림)
- **대시보드** (학습 현황 시각화)
- **API** (외부 시스템 통합)

---

## 11. 결론

### 11.1 핵심 가치

**Git Diff Vector Memory + Neural-CONI =**
**자가 학습하는 AI 오케스트레이션 시스템**

1. ✅ **코드 차원 학습** (Git Diff Memory)
2. ✅ **업무 차원 학습** (Task Memory) ← NEW!
3. ✅ **통합 경험 자산** (완전한 시스템)

### 11.2 차별화

| 기존 시스템 | Neural-CONI (현재) | 통합 후 |
|------------|-------------------|---------|
| 단순 오케스트레이터 | 신경망 스타일 | **자가 학습 AI** |
| 정적 Task | Weight 학습 | **Task 생성/최적화** |
| 반복 작업 | Attention 선택 | **실패 예방** |
| 프로젝트별 | 경험 축적 | **지식 전이** |

### 11.3 최종 추천

**즉시 시작:**
- Week 1-2: Task Execution Memory ⭐⭐⭐⭐⭐
- Week 3: Failure Prediction ⭐⭐⭐⭐
- Week 4-5: Task Auto-Generation ⭐⭐⭐⭐⭐

**결과:**
- 개발 생산성 2배
- 품질 일관성 향상
- 팀 집단 지성 구현
- 지속적 자가 개선

**이것은 단순한 기능 추가가 아니다.**
**Neural-CONI를 진정한 AI 시스템으로 진화시키는 것이다.** 🚀

---

## 부록

### A. 참고 자료

- **Git Diff Vector Memory 기획서**: `docs/Git_Diff_Vector_Memory_기획서.md`
- **Neural-CONI 기존 문서**: `docs/Neural-CONI 기획서.md`
- **Vector Memory README**: `neural_engine/README_VECTOR_MEMORY.md`

### B. 용어 정의

| 용어 | 설명 |
|------|------|
| **Task Execution Memory** | Task 실행 전후를 벡터로 저장하는 시스템 |
| **Task Auto-Generation** | 과거 패턴 학습으로 Task 자동 생성 |
| **Failure Prediction** | 과거 실패 패턴으로 위험 예측 |
| **Cross-Project Learning** | 프로젝트 간 지식 전이 |
| **Memory Boost** | 과거 경험으로 Attention 강화 |

### C. FAQ

**Q: 기존 Neural-CONI와 호환되나요?**
A: 예. 완전히 하위 호환됩니다.

**Q: Task Memory 없이도 작동하나요?**
A: 예. 메모리가 없으면 기본 방식으로 동작합니다.

**Q: 자동 생성된 Task를 수정할 수 있나요?**
A: 예. PM 리뷰 단계에서 자유롭게 수정 가능합니다.

**Q: 실패 예측이 틀리면?**
A: 예측은 참고사항이며, 최종 결정은 사용자가 합니다.

**Q: 다른 프로젝트 데이터가 섞이나요?**
A: project_id로 격리되며, 원하면 통합 검색도 가능합니다.

---

**문서 버전**: 1.0
**최종 수정**: 2025-01-07
**작성자**: Neural-CONI Team
**승인자**: [TBD]
