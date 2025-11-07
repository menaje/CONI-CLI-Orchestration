# Neural-CONI 작업계획서 - Phase 2
## 통합 및 배포 계획

**작성일:** 2025-11-07
**버전:** 1.0
**상태:** Phase 1 완료, Phase 2 준비

---

# 📋 Executive Summary

## Phase 1 완료 현황

✅ **완료된 작업:**
- Neural-CONI 기획서 작성 (46KB, 1,437 라인)
- 핵심 Python 엔진 구현 (2,944 라인)
  - embedding_engine.py
  - attention.py
  - neural_task.py
  - validator.py
  - weight_manager.py
- DB 스키마 템플릿 4개
- 통합 테스트 스크립트

## Phase 2 목표

🎯 **목표:** Neural-CONI를 실제 운영 환경에 배포하고 성능 검증

**기대 효과:**
- 실행 시간: -67%
- 비용: -53%
- 품질: +21%

**기간:** 2주 (Week 5-6)

---

# 📅 Part 1: 전체 로드맵

## Week 5: Agent 행동규범 및 통합

| 일 | 작업 | 산출물 | 우선순위 |
|----|------|--------|---------|
| **Day 1-2** | Neural Orchestrator 작성 | `agents/neural_orchestrator.md` | 🔴 High |
| **Day 2-3** | Neural Planner 작성 | `agents/neural_planner.md` | 🔴 High |
| **Day 3-4** | Neural Executor 수정 | `agents/neural_executor.md` | 🟡 Medium |
| **Day 4-5** | DB 초기화 스크립트 | `scripts/init_neural_db.py` | 🔴 High |

## Week 6: 테스트 및 배포

| 일 | 작업 | 산출물 | 우선순위 |
|----|------|--------|---------|
| **Day 1-2** | 실제 Run 테스트 | 테스트 리포트 | 🔴 High |
| **Day 2-3** | 성능 비교 분석 | 벤치마크 리포트 | 🔴 High |
| **Day 3-4** | 통합 및 배포 | 배포 가이드 | 🟡 Medium |
| **Day 4-5** | 문서화 및 마무리 | 최종 사용자 가이드 | 🟢 Low |

---

# 🎯 Part 2: 상세 작업 명세

## 작업 1: Neural Orchestrator 작성

### 목표
기존 `orchestrator.md`를 Neural-CONI 방식으로 전환

### 핵심 변경사항

**1. DAG 기반 병렬 스케줄링**
```markdown
## Protocol NO-1: Task Dependency Analysis

1. tasks.md에서 dependencies 파싱
2. DAG (Directed Acyclic Graph) 생성
3. 레벨별 그룹화:
   - Level 0: 의존성 없는 Task
   - Level 1: Level 0 완료 후 실행 가능
   - Level 2: Level 1 완료 후 실행 가능
```

**2. 신경망 Forward Pass**
```markdown
## Protocol NO-2: Neural Forward Pass

for each level in DAG:
  # 활성화 계산
  for task in level:
    activation = compute_activation(task, prev_level)
    task.activation = activation

  # 임계값 이상만 실행 (병렬)
  activated_tasks = [t for t in level if t.activation > threshold]

  # 병렬 실행
  python neural_engine/run_parallel.py --tasks activated_tasks
```

**3. Backward Pass (학습)**
```markdown
## Protocol NO-3: Learning Phase

Run 종료 후:
1. 최종 품질 평가
2. 오차 계산: error = target - actual
3. WeightManager.backward_pass() 호출
4. 가중치 자동 업데이트
```

### 산출물
- `agents/neural_orchestrator.md` (약 800 라인)
- 기존 orchestrator.md와 호환 유지

### 예상 소요 시간
**2일**

---

## 작업 2: Neural Planner 작성

### 목표
Task 계획 시 가중치 이력 활용

### 핵심 변경사항

**1. 가중치 기반 Task 순서 결정**
```markdown
## Protocol P-T1: Task Planning with Weights

1. execution_history.md 로딩
2. 유사 Task 유형 검색
3. 성공률 높은 순서로 Task 배치:

   예:
   - "분석 → 초안" 가중치 0.85 (성공 9회)
   - "분석 → 검색" 가중치 0.45 (성공 5회)

   → "초안"을 우선 배치
```

**2. Attention을 고려한 references 설정**
```markdown
## Reference 선택 최적화

related_references를 설정할 때:
1. 후보 파일들의 summary 확인 (catalog 활용)
2. task_purpose와 유사도 계산 (임베딩)
3. 상위 K개만 related_references에 포함

효과:
- 기존: 모든 파일 나열 (10개)
- 개선: 관련 파일만 (3개) → Executor 부담 감소
```

**3. Task 의존성 자동 추론**
```markdown
## Dependency 자동 생성

Task의 purpose를 분석하여 의존성 추론:

예:
- tsk-01: "요구사항 분석"
- tsk-02: "분석 결과를 바탕으로 초안 작성"
           ↑ "분석 결과" 키워드 발견
- tsk-03: "웹에서 정보 검색"

자동 의존성:
- tsk-02 depends on tsk-01 ✅
- tsk-03 depends on [] (독립)
```

### 산출물
- `agents/neural_planner.md` (약 600 라인)
- Task 계획 품질 향상

### 예상 소요 시간
**1.5일**

---

## 작업 3: Neural Executor 수정

### 목표
Attention 메커니즘 통합

### 핵심 변경사항

**1. Attention 기반 입력 선택**
```markdown
## E-UP 수정: Attention Integration

기존:
- related_references의 모든 파일 읽기

개선:
1. TaskAttentionSelector 사용
2. task_purpose와 파일 유사도 계산
3. Top-K만 실제로 읽기

코드:
```python
from neural_engine.attention import TaskAttentionSelector

selector = TaskAttentionSelector()
selected = selector.select_files(
    task_purpose=task_purpose,
    candidate_files=related_references,
    top_k=3
)

# 선택된 파일만 읽기
context = "\n".join([read(f) for f, _ in selected])
```

**효과:**
- 토큰 사용량: -30~50%
- 실행 시간: -10~20% (파일 읽기 감소)
```

**2. 품질 검증 및 재시도**
```markdown
## Quality Validation Loop

Task 실행 후:
1. NeuralValidator로 품질 평가
2. if quality < threshold:
     if retry_count < max_retries:
       재실행 (피드백 포함)
     else:
       실패 처리
3. 품질 기록 → learning_metrics.md
```

### 산출물
- `agents/neural_executor.md` (약 500 라인)
- 기존 executor.md 기반 수정

### 예상 소요 시간
**1일**

---

## 작업 4: DB 초기화 스크립트

### 목표
Neural-CONI DB 자동 생성 및 초기화

### 파일 구조
```
scripts/
├── init_neural_db.py        # 메인 스크립트
├── init_weights.py           # 가중치 초기화
└── migrate_from_coni.py      # 기존 CONI 데이터 마이그레이션
```

### init_neural_db.py 구현

```python
#!/usr/bin/env python3
"""
Neural-CONI DB 초기화 스크립트

사용법:
  python scripts/init_neural_db.py --mode fresh
  python scripts/init_neural_db.py --mode migrate
"""

import os
import json
import argparse
from pathlib import Path

def create_directory_structure():
    """필요한 디렉토리 생성"""
    dirs = [
        "db",
        "runs",
        "outputs"
    ]

    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✓ Created: {dir_path}/")

def initialize_weights_db():
    """가중치 DB 초기화"""
    weights_file = "db/weights.json"

    # 초기 가중치 (휴리스틱 기반)
    initial_weights = {
        "weights": {
            "input→analyze": 0.8,
            "analyze→draft": 0.75,
            "analyze→research": 0.5,
            "research→draft": 0.65,
            "draft→validate": 0.9,
            "validate→refine": 0.7,
            "refine→output": 0.85
        },
        "gradients": {},
        "update_counts": {},
        "learning_rate": 0.01
    }

    with open(weights_file, 'w') as f:
        json.dump(initial_weights, f, indent=2)

    print(f"✓ Initialized: {weights_file}")
    print(f"  Initial weights: {len(initial_weights['weights'])}")

def initialize_metrics_db():
    """메트릭 DB 초기화"""
    files = {
        "db/execution_history.json": [],
        "db/learning_metrics.json": [],
        "db/architecture_performance.json": []
    }

    for file_path, initial_data in files.items():
        with open(file_path, 'w') as f:
            json.dump(initial_data, f, indent=2)
        print(f"✓ Initialized: {file_path}")

def create_readme():
    """DB README 생성"""
    readme_content = """# Neural-CONI Database

이 디렉토리는 Neural-CONI의 학습 데이터를 저장합니다.

## 파일 설명

- `weights.json`: Task 간 가중치
- `execution_history.json`: 실행 이력
- `learning_metrics.json`: 학습 메트릭
- `architecture_performance.json`: 아키텍처 성능

## 초기화

```bash
python scripts/init_neural_db.py --mode fresh
```

## 백업

중요한 학습 데이터이므로 정기적으로 백업하세요:

```bash
cp -r db/ db_backup_$(date +%Y%m%d)/
```
"""

    with open("db/README.md", 'w') as f:
        f.write(readme_content)

    print("✓ Created: db/README.md")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['fresh', 'migrate'],
                       default='fresh',
                       help='fresh: 새로 시작, migrate: 기존 데이터 마이그레이션')
    args = parser.parse_args()

    print("=" * 60)
    print("Neural-CONI DB Initialization")
    print("=" * 60)
    print(f"Mode: {args.mode}\n")

    # 1. 디렉토리 생성
    create_directory_structure()

    # 2. DB 초기화
    initialize_weights_db()
    initialize_metrics_db()

    # 3. README 생성
    create_readme()

    print("\n" + "=" * 60)
    print("✅ Initialization Complete!")
    print("=" * 60)
    print("\n다음 단계:")
    print("  1. pip install -r requirements.txt")
    print("  2. python test_neural_coni.py")
    print("  3. gemini -p '@agents/neural_orchestrator.md ...'")

if __name__ == "__main__":
    main()
```

### 산출물
- `scripts/init_neural_db.py`
- `scripts/init_weights.py`
- `scripts/migrate_from_coni.py`
- `db/README.md`

### 예상 소요 시간
**1일**

---

## 작업 5: 실제 Run 테스트

### 목표
Neural-CONI로 실제 작업 실행 및 검증

### 테스트 시나리오

**시나리오 1: 간단한 보고서 작성 (5 Tasks)**
```
목표: "사용자 요구사항 분석 보고서 작성"

예상 Task 흐름:
1. [tsk-01] 요구사항 파일 읽기
2. [tsk-02] 핵심 요구사항 추출
3. [tsk-03] 분석 수행
4. [tsk-04] 보고서 초안 작성
5. [tsk-05] 최종 문서 생성

기대 결과:
- 실행 시간: < 10분
- 품질 점수: > 0.7
- 비용: < $3
```

**시나리오 2: 복잡한 분석 (18 Tasks)**
```
목표: 사용예제의 run_20250726_intro_gen 재현

기존 CONI 결과:
- Task 수: 18개
- 실행 시간: ~88분 (추정)
- 비용: ~$16

Neural-CONI 목표:
- 실행 Task: 12~14개 (20% 감소)
- 실행 시간: < 30분 (67% 단축)
- 비용: < $8 (50% 절감)
- 품질: > 0.85
```

### 테스트 실행 절차

```bash
# 1. DB 초기화
python scripts/init_neural_db.py --mode fresh

# 2. 시나리오 1 실행
python run_neural_test.py \
  --scenario simple \
  --user-request "사용자 요구사항 분석 보고서 작성" \
  --output-dir test_results/scenario1

# 3. 결과 분석
python analyze_results.py \
  --result-dir test_results/scenario1 \
  --baseline-dir 사용예제/runs/baseline

# 4. 시나리오 2 실행 (복잡)
python run_neural_test.py \
  --scenario complex \
  --user-request "행동규범 설명 문서 작성" \
  --output-dir test_results/scenario2

# 5. 성능 비교
python compare_performance.py \
  --neural test_results/scenario2 \
  --coni 사용예제/runs/run_20250726_intro_gen
```

### 검증 항목

| 항목 | 측정 방법 | 목표 |
|------|----------|------|
| **실행 시간** | end_time - start_time | < 30분 |
| **비용** | sum(token_used × price) | < $8 |
| **품질** | avg(quality_score) | > 0.85 |
| **Skip 비율** | skipped / total | 20~30% |
| **Attention 효과** | avg(selected / candidates) | < 40% |

### 산출물
- `test_results/scenario1/` - 간단 시나리오 결과
- `test_results/scenario2/` - 복잡 시나리오 결과
- `test_results/test_report.md` - 테스트 리포트
- `test_results/performance_comparison.csv`

### 예상 소요 시간
**2일**

---

## 작업 6: 성능 비교 분석

### 목표
Neural-CONI vs 기존 CONI 정량적 비교

### 분석 스크립트: `analyze_performance.py`

```python
#!/usr/bin/env python3
"""
성능 비교 분석 스크립트

사용법:
  python analyze_performance.py \
    --neural test_results/scenario2 \
    --coni 사용예제/runs/run_20250726_intro_gen
"""

import json
import pandas as pd
import matplotlib.pyplot as plt

def load_metrics(result_dir):
    """메트릭 로딩"""
    with open(f"{result_dir}/learning_metrics.json") as f:
        data = json.load(f)
    return data

def compare_metrics(neural_data, coni_data):
    """메트릭 비교"""
    comparison = {
        "실행 시간": {
            "CONI": coni_data['total_time'],
            "Neural-CONI": neural_data['total_time'],
            "개선율": (coni_data['total_time'] - neural_data['total_time']) / coni_data['total_time']
        },
        "비용": {
            "CONI": coni_data['total_cost'],
            "Neural-CONI": neural_data['total_cost'],
            "개선율": (coni_data['total_cost'] - neural_data['total_cost']) / coni_data['total_cost']
        },
        "품질": {
            "CONI": coni_data['final_quality'],
            "Neural-CONI": neural_data['final_quality'],
            "개선율": (neural_data['final_quality'] - coni_data['final_quality']) / coni_data['final_quality']
        }
    }

    return comparison

def generate_report(comparison):
    """리포트 생성"""
    report = f"""# Neural-CONI vs CONI 성능 비교 리포트

## 실행 결과

| 메트릭 | CONI | Neural-CONI | 개선율 |
|--------|------|-------------|--------|
| 실행 시간 | {comparison['실행 시간']['CONI']:.1f}분 | {comparison['실행 시간']['Neural-CONI']:.1f}분 | **{comparison['실행 시간']['개선율']*100:.1f}%** |
| 비용 | ${comparison['비용']['CONI']:.2f} | ${comparison['비용']['Neural-CONI']:.2f} | **{comparison['비용']['개선율']*100:.1f}%** |
| 품질 | {comparison['품질']['CONI']:.2f} | {comparison['품질']['Neural-CONI']:.2f} | **{comparison['품질']['개선율']*100:.1f}%** |

## 분석

### 속도 개선
- 병렬 실행으로 {comparison['실행 시간']['개선율']*100:.0f}% 단축
- DAG 기반 스케줄링 효과

### 비용 절감
- Attention으로 불필요한 토큰 제거
- Task Skip으로 실행 감소

### 품질 향상
- Validator 피드백 루프
- 가중치 학습 효과

## 결론

✅ Neural-CONI가 모든 메트릭에서 우수한 성능을 보임
"""

    return report

def main():
    # ... 구현
    pass

if __name__ == "__main__":
    main()
```

### 비교 항목

**1. 정량적 비교**
- 실행 시간
- 비용 (USD)
- 품질 점수
- 토큰 사용량
- Task Skip 비율

**2. 정성적 비교**
- 결과물 품질 (사람 평가)
- 사용 편의성
- 안정성

**3. 학습 효과 분석**
- 1회 → 10회 실행 시 품질 변화
- 가중치 수렴 속도
- 비용 절감 추이

### 산출물
- `test_results/performance_report.md`
- `test_results/metrics_comparison.csv`
- `test_results/charts/` (그래프)

### 예상 소요 시간
**1일**

---

## 작업 7: 통합 및 배포

### 목표
기존 CONI 시스템과 Neural-CONI 통합

### 배포 전략: Gradual Rollout

**Phase 2A: Opt-in (선택적 사용)**
```bash
# 사용자가 명시적으로 선택
gemini -p '@agents/neural_orchestrator.md ...'  # Neural-CONI
gemini -p '@agents/orchestrator.md ...'         # 기존 CONI
```

**Phase 2B: A/B Testing**
```bash
# 50% 확률로 Neural-CONI 사용
# 자동으로 성능 비교 및 피드백 수집
```

**Phase 2C: Full Deployment**
```bash
# Neural-CONI를 기본값으로 설정
# 기존 CONI는 fallback으로 유지
```

### 통합 작업

**1. Gemini CLI 설정**
```bash
# .gemini/agents/ 에 추가
cp agents/neural_orchestrator.md .gemini/agents/
cp agents/neural_planner.md .gemini/agents/
cp agents/neural_executor.md .gemini/agents/
```

**2. 호환성 레이어**
```python
# scripts/compatibility_layer.py

def convert_coni_to_neural(coni_tasks):
    """기존 CONI tasks.md → Neural tasks.md 변환"""
    neural_tasks = []
    for task in coni_tasks:
        neural_task = {
            **task,
            "activation": 0.95,  # 기본값
            "threshold": 0.6,
            "dependencies": infer_dependencies(task)
        }
        neural_tasks.append(neural_task)
    return neural_tasks
```

**3. 롤백 메커니즘**
```bash
# 문제 발생 시 즉시 롤백
./scripts/rollback.sh --to-version coni-v1.0
```

### 산출물
- `scripts/deploy.sh` - 배포 스크립트
- `scripts/rollback.sh` - 롤백 스크립트
- `docs/deployment_guide.md` - 배포 가이드

### 예상 소요 시간
**1.5일**

---

## 작업 8: 문서화 및 마무리

### 목표
사용자 가이드 및 개발자 문서 작성

### 문서 구조

```
docs/
├── user_guide.md              # 사용자 가이드
├── developer_guide.md         # 개발자 가이드
├── api_reference.md           # API 레퍼런스
├── troubleshooting.md         # 트러블슈팅
└── migration_guide.md         # 마이그레이션 가이드
```

### user_guide.md 목차

```markdown
# Neural-CONI 사용자 가이드

## 1. 시작하기
- 설치
- 초기 설정
- 첫 Run 실행

## 2. 핵심 개념
- Neural Task란?
- Attention 메커니즘
- 가중치 학습

## 3. 사용법
- 기본 사용
- 고급 설정
- 성능 튜닝

## 4. 모니터링
- 실행 이력 확인
- 학습 진행 상황
- 비용 추적

## 5. FAQ
- 자주 묻는 질문
- 에러 해결
```

### 산출물
- `docs/user_guide.md` (약 50KB)
- `docs/developer_guide.md` (약 40KB)
- `docs/api_reference.md` (약 30KB)
- `docs/troubleshooting.md` (약 20KB)
- `README.md` 업데이트

### 예상 소요 시간
**1.5일**

---

# 📊 Part 3: 일정 및 마일스톤

## Week 5: 통합 준비

```
Day 1-2 ████████████░░░░░░░░ Neural Orchestrator
Day 2-3 ░░░░░░░░░░░░████████░░ Neural Planner
Day 3-4 ░░░░░░░░░░░░░░░░████░░ Neural Executor
Day 4-5 ░░░░░░░░░░░░░░░░░░░░██ DB Scripts
```

**마일스톤 1 (Day 5):**
- [ ] Agent 행동규범 완성
- [ ] DB 초기화 가능
- [ ] 통합 테스트 통과

## Week 6: 테스트 및 배포

```
Day 1-2 ████████████░░░░░░░░ Run 테스트
Day 2-3 ░░░░░░░░░░░░████████░░ 성능 분석
Day 3-4 ░░░░░░░░░░░░░░░░████░░ 통합 배포
Day 4-5 ░░░░░░░░░░░░░░░░░░░░██ 문서화
```

**마일스톤 2 (Day 10):**
- [ ] 실제 Run 성공
- [ ] 성능 목표 달성
- [ ] 배포 완료
- [ ] 문서 완성

---

# 🎯 Part 4: 성공 기준

## 필수 기준 (Must Have)

| 항목 | 목표 | 측정 방법 |
|------|------|----------|
| **실행 성공률** | > 95% | 10회 실행 중 성공 횟수 |
| **실행 시간** | < 30분 | 18-Task Run 기준 |
| **비용 절감** | > 30% | 기존 CONI 대비 |
| **품질** | > 0.8 | Validator 평균 점수 |

## 권장 기준 (Should Have)

| 항목 | 목표 | 측정 방법 |
|------|------|----------|
| **비용 절감** | > 50% | 기존 CONI 대비 |
| **품질** | > 0.85 | Validator 평균 점수 |
| **Task Skip** | 20~30% | skipped / total |
| **학습 효과** | 10회 후 품질 +15% | 품질 추이 |

## 선택 기준 (Nice to Have)

| 항목 | 목표 | 측정 방법 |
|------|------|----------|
| **실행 시간** | < 20분 | 최고 성능 |
| **비용 절감** | > 60% | 최고 효율 |
| **품질** | > 0.9 | 최고 품질 |

---

# ⚠️ Part 5: 위험 관리

## 기술적 위험

| 위험 | 확률 | 영향 | 완화 방안 | 책임자 |
|------|------|------|----------|--------|
| **Agent 행동규범 복잡도** | 중 | 높음 | 단계별 테스트, 롤백 준비 | Dev |
| **성능 목표 미달성** | 중 | 중간 | 하이퍼파라미터 튜닝, A/B 테스트 | QA |
| **기존 CONI와 충돌** | 낮음 | 높음 | 호환성 레이어, Gradual Rollout | Dev |
| **학습 불안정** | 낮음 | 중간 | Learning rate 조정, 클리핑 | Dev |

## 일정 위험

| 위험 | 확률 | 영향 | 완화 방안 |
|------|------|------|----------|
| **Agent 작성 지연** | 중 | 중간 | 우선순위 조정, 병렬 작업 |
| **테스트 실패** | 낮음 | 높음 | 충분한 테스트 시간 확보 |
| **문서화 미완성** | 낮음 | 낮음 | 문서 템플릿 사전 준비 |

---

# 📋 Part 6: 체크리스트

## Week 5 체크리스트

### Day 1-2: Neural Orchestrator
- [ ] DAG 파싱 로직 구현
- [ ] 병렬 실행 메커니즘
- [ ] Forward Pass 프로토콜
- [ ] Backward Pass 프로토콜
- [ ] 에러 처리
- [ ] 단위 테스트

### Day 2-3: Neural Planner
- [ ] 가중치 이력 로딩
- [ ] Task 순서 최적화
- [ ] Dependency 자동 추론
- [ ] Reference 선택 최적화
- [ ] 단위 테스트

### Day 3-4: Neural Executor
- [ ] Attention 통합
- [ ] 품질 검증 루프
- [ ] 재시도 메커니즘
- [ ] 메트릭 기록
- [ ] 단위 테스트

### Day 4-5: DB Scripts
- [ ] init_neural_db.py
- [ ] init_weights.py
- [ ] migrate_from_coni.py
- [ ] DB README
- [ ] 스크립트 테스트

## Week 6 체크리스트

### Day 1-2: Run 테스트
- [ ] 시나리오 1 (간단) 성공
- [ ] 시나리오 2 (복잡) 성공
- [ ] 10회 반복 테스트
- [ ] 에러 로그 확인
- [ ] 결과 저장

### Day 2-3: 성능 분석
- [ ] 메트릭 수집
- [ ] 비교 리포트 작성
- [ ] 그래프 생성
- [ ] 병목 지점 분석
- [ ] 개선안 도출

### Day 3-4: 통합 배포
- [ ] Gemini CLI 통합
- [ ] 호환성 테스트
- [ ] Rollback 테스트
- [ ] A/B 테스트 설정
- [ ] 배포 스크립트

### Day 4-5: 문서화
- [ ] User Guide
- [ ] Developer Guide
- [ ] API Reference
- [ ] Troubleshooting
- [ ] README 업데이트

---

# 💰 Part 7: 예산 및 리소스

## 개발 리소스

| 역할 | 기간 | 예상 비용 |
|------|------|----------|
| Senior Developer | 2주 | $4,000 |
| QA Engineer | 1주 | $1,500 |
| Tech Writer | 3일 | $900 |
| **총계** | - | **$6,400** |

## 테스트 비용

| 항목 | 예상 비용 |
|------|----------|
| LLM API 호출 (테스트) | $200 |
| 인프라 (AWS/GCP) | $50 |
| **총계** | **$250** |

**Phase 2 총 예산: $6,650**

---

# 📈 Part 8: 예상 ROI

## 투자

| Phase | 비용 |
|-------|------|
| Phase 1 (구현) | $13,000 |
| Phase 2 (배포) | $6,650 |
| **총 투자** | **$19,650** |

## 회수

**월간 사용 시나리오 (100 Runs):**
- 기존 CONI: $1,620/월
- Neural-CONI: $756/월
- **월간 절감: $864**

**ROI 계산:**
- 회수 기간: $19,650 / $864 = **22.7개월 (약 2년)**
- 2년 ROI: 88%
- 3년 ROI: 232%

---

# 🎓 Part 9: 학습 및 개선

## 지속적 개선 계획

### Month 1-3: 안정화
- 버그 수정
- 성능 튜닝
- 사용자 피드백 수집

### Month 4-6: 최적화
- 고급 Attention 기법 (Multi-Head)
- Ensemble 기능 추가
- Adaptive Learning Rate

### Month 7-12: 확장
- Multi-Modal 지원
- AutoML 통합
- Cloud Native 아키텍처

---

# 📚 Part 10: 참고 자료

## 관련 문서

- [Neural-CONI 기획서](Neural-CONI_기획서.md)
- [Neural Engine README](neural_engine/README.md)
- [통합 테스트 스크립트](test_neural_coni.py)

## 외부 레퍼런스

- Attention Is All You Need (Vaswani et al., 2017)
- Neural Architecture Search
- Gradient Descent Optimization

---

# ✅ Part 11: 승인 및 실행

## 승인 체크리스트

- [ ] 기술 검토 완료
- [ ] 예산 승인
- [ ] 일정 확정
- [ ] 리소스 할당
- [ ] 위험 관리 계획 승인

## 실행 준비

**즉시 시작 가능:**
```bash
# 1. 작업 브랜치 생성
git checkout -b feature/neural-coni-phase2

# 2. Day 1 작업 시작
# agents/neural_orchestrator.md 작성 시작
```

---

**문서 정보:**
- 작성일: 2025-11-07
- 버전: 1.0
- 다음 리뷰: Phase 2 시작 전
- 승인 필요: 프로젝트 매니저

**이 작업계획서는 Neural-CONI Phase 2의 완전한 로드맵을 제공합니다.**
