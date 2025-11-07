# Unified Embedding Engine

OpenAI SDK를 사용하여 **Ollama**와 **LM Studio**를 통합한 임베딩 엔진입니다.

## 🎯 핵심 기능

- ✅ **OpenAI SDK 통합**: Ollama/LM Studio를 동일한 인터페이스로 사용
- ✅ **자동 감지**: 실행 중인 provider 자동 선택
- ✅ **배치 처리**: 여러 텍스트를 효율적으로 임베딩
- ✅ **메모리 캐싱**: 중복 계산 방지
- ✅ **무료 & 로컬**: API key 불필요, 완전 로컬 실행

## 📦 설치

### 1. Python 패키지 설치

```bash
pip install -r requirements.txt
```

필수 패키지:
- `openai>=1.0.0` - OpenAI SDK (Ollama/LM Studio 호환)
- `numpy>=1.24.3` - 벡터 연산
- `requests>=2.31.0` - HTTP 요청

### 2. 임베딩 모델 준비

#### Option A: Ollama (추천)

```bash
# Ollama 설치
curl -fsSL https://ollama.com/install.sh | sh

# 임베딩 모델 다운로드 (768-dim, 빠름)
ollama pull nomic-embed-text

# 서버 실행
ollama serve
```

**다른 모델 옵션:**
```bash
# 더 높은 품질 (1024-dim)
ollama pull mxbai-embed-large

# 다국어 지원
ollama pull bge-m3
```

#### Option B: LM Studio

1. [LM Studio](https://lmstudio.ai/) 다운로드 및 설치
2. **Models** 탭 → "nomic-embed-text" 검색 → 다운로드
3. **Local Server** 탭 → nomic-embed-text 모델 로드 → **Start Server**

## 🚀 사용법

### 기본 사용

```python
from neural_engine.embedding_engine import UnifiedEmbeddingEngine

# 엔진 초기화 (자동 감지)
engine = UnifiedEmbeddingEngine(auto_detect=True)

# 텍스트 임베딩
text = "사용자 인증 요구사항을 분석합니다"
embedding = engine.embed_text(text)

print(f"Shape: {embedding.shape}")  # (768,)
print(f"First 5: {embedding[:5]}")
```

### Provider 지정

```python
# Ollama 강제 사용
engine = UnifiedEmbeddingEngine(
    provider="ollama",
    auto_detect=False
)

# LM Studio 강제 사용
engine = UnifiedEmbeddingEngine(
    provider="lmstudio",
    auto_detect=False
)
```

### 배치 임베딩 (효율적)

```python
texts = [
    "요구사항 문서 작성",
    "설계 문서 작성",
    "코드 리뷰 수행"
]

embeddings = engine.embed_batch(texts)
# -> 한 번의 API 호출로 3개 임베딩
```

### 유사도 계산

```python
text1 = "사용자 인증 시스템"
text2 = "로그인 기능"

emb1 = engine.embed_text(text1)
emb2 = engine.embed_text(text2)

similarity = engine.cosine_similarity(emb1, emb2)
print(f"Similarity: {similarity:.4f}")  # 0.8500
```

### 의미 검색

```python
query = "보안 설정"
candidates = [
    "사용자 인증 구현",
    "보안 정책 수립",
    "날씨 API 연동",
    "암호화 알고리즘"
]

results = engine.find_most_similar(query, candidates, top_k=2)

for idx, score in results:
    print(f"{score:.4f} - {candidates[idx]}")
# 0.8823 - 보안 정책 수립
# 0.7654 - 암호화 알고리즘
```

### 편의 함수

```python
from neural_engine.embedding_engine import embed, similarity

# 빠른 임베딩
emb = embed("텍스트")

# 빠른 유사도
sim = similarity("텍스트1", "텍스트2")
```

## 🧪 테스트

```bash
# 자동 감지 테스트
python scripts/test_embedding.py

# Ollama 테스트
python scripts/test_embedding.py ollama

# LM Studio 테스트
python scripts/test_embedding.py lmstudio
```

**예상 출력:**
```
======================================================================
  Embedding Engine Test - Provider: auto
======================================================================

[1] 엔진 초기화...
[EmbeddingEngine] Auto-detected: Ollama
[EmbeddingEngine] Using ollama: nomic-embed-text
[EmbeddingEngine] API URL: http://localhost:11434/v1
[EmbeddingEngine] Dimension: 768
    ✅ ollama 엔진 로딩 성공

[2] 기본 임베딩 테스트...
    ✅ 임베딩 생성 성공
    - 텍스트: 사용자 인증 요구사항을 분석합니다
    - Shape: (768,)

...

======================================================================
  ✅ 모든 테스트 통과!
======================================================================
```

## ⚙️ 설정

### config/neural_config.yaml

```yaml
embedding:
  provider: "auto"  # auto | ollama | lmstudio

  ollama:
    base_url: "http://localhost:11434/v1"
    model: "nomic-embed-text"

  lmstudio:
    base_url: "http://localhost:1234/v1"
    model: "nomic-embed-text"

  cache:
    enabled: true
    path: "db/embeddings_cache.json"
```

## 📊 성능 비교

| 모델 | Provider | 차원 | MTEB Score | 속도 |
|------|----------|------|------------|------|
| all-MiniLM-L6-v2 (기존) | sentence-transformers | 384 | 56.3 | 빠름 |
| **nomic-embed-text** | Ollama/LM Studio | **768** | **62.4** | **빠름** |
| mxbai-embed-large | Ollama/LM Studio | 1024 | 64.7 | 중간 |

## 🔧 문제 해결

### 1. "Failed to generate embedding" 오류

**원인**: Ollama/LM Studio가 실행 중이 아니거나 모델이 로드되지 않음

**해결:**
```bash
# Ollama
ollama serve
ollama pull nomic-embed-text

# LM Studio
# 앱 실행 → Local Server → 모델 로드 → Start Server
```

### 2. "Connection refused" 오류

**원인**: API URL이 올바르지 않음

**해결:**
```python
# Ollama 기본 포트 확인
engine = UnifiedEmbeddingEngine(
    provider="ollama",
    base_url="http://localhost:11434/v1"  # 기본값
)

# LM Studio 기본 포트 확인
engine = UnifiedEmbeddingEngine(
    provider="lmstudio",
    base_url="http://localhost:1234/v1"  # 기본값
)
```

### 3. 느린 임베딩 속도

**원인**: 캐시 미사용 또는 배치 처리 미사용

**해결:**
```python
# 캐시 사용 (기본 활성화)
emb = engine.embed_text(text, use_cache=True)

# 배치 처리 사용
embeddings = engine.embed_batch(texts)  # 개별 호출보다 5-10배 빠름
```

## 📝 API Reference

### UnifiedEmbeddingEngine

#### `__init__(provider, model, base_url, auto_detect)`

- `provider`: "ollama" | "lmstudio"
- `model`: 모델 이름 (기본: "nomic-embed-text")
- `base_url`: API URL (기본: provider별 기본값)
- `auto_detect`: 자동 감지 여부 (기본: True)

#### `embed_text(text, use_cache=True) -> np.ndarray`

텍스트를 768차원 벡터로 변환

#### `embed_batch(texts, use_cache=True) -> List[np.ndarray]`

여러 텍스트를 배치로 임베딩 (효율적)

#### `cosine_similarity(emb1, emb2) -> float`

두 벡터의 코사인 유사도 (0~1)

#### `find_most_similar(query, candidates, top_k) -> List[Tuple[int, float]]`

쿼리와 가장 유사한 후보 찾기

#### `semantic_search(query, file_paths, top_k) -> List[Tuple[str, float]]`

파일 중 가장 관련 있는 파일 찾기

## 🎯 Neural-CONI 통합

Neural Planner와 Executor에서 자동으로 사용됩니다:

```python
# Neural Planner: Task 계획 시 Attention 기반 파일 선택
from neural_engine.embedding_engine import get_embedding_engine

engine = get_embedding_engine()
selected_files = engine.find_most_similar(
    query=task_purpose,
    candidates=all_reference_files,
    top_k=3  # Top-3만 선택 → 70% 토큰 절감
)
```

## 📚 추가 정보

- [Ollama 문서](https://github.com/ollama/ollama)
- [LM Studio 문서](https://lmstudio.ai/docs)
- [nomic-embed-text 모델](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
