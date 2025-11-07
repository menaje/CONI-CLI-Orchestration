#!/usr/bin/env python3
"""
Embedding Engine Test Script

Ollama/LM Studio 임베딩 엔진 테스트

사용법:
  python scripts/test_embedding.py [provider]

  provider: ollama (기본값) | lmstudio | auto
"""

import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neural_engine.embedding_engine import UnifiedEmbeddingEngine


def test_embedding(provider: str = "auto"):
    """임베딩 엔진 테스트"""

    print("=" * 70)
    print(f"  Embedding Engine Test - Provider: {provider}")
    print("=" * 70)

    # 엔진 초기화
    print("\n[1] 엔진 초기화...")
    try:
        if provider == "auto":
            engine = UnifiedEmbeddingEngine(auto_detect=True)
        else:
            engine = UnifiedEmbeddingEngine(provider=provider, auto_detect=False)
        print(f"    ✅ {engine.provider} 엔진 로딩 성공")
    except Exception as e:
        print(f"    ❌ 엔진 초기화 실패: {e}")
        print("\n💡 해결 방법:")
        print("  Ollama: ollama serve")
        print("  Ollama 모델: ollama pull nomic-embed-text")
        print("  LM Studio: LM Studio 앱 실행 → nomic-embed-text 모델 로드")
        return False

    # 기본 임베딩 테스트
    print("\n[2] 기본 임베딩 테스트...")
    text = "사용자 인증 요구사항을 분석합니다"
    try:
        emb = engine.embed_text(text)
        print(f"    ✅ 임베딩 생성 성공")
        print(f"    - 텍스트: {text}")
        print(f"    - Shape: {emb.shape}")
        print(f"    - 첫 5개 값: {emb[:5]}")
    except Exception as e:
        print(f"    ❌ 임베딩 생성 실패: {e}")
        return False

    # 유사도 테스트
    print("\n[3] 유사도 계산 테스트...")
    text1 = "사용자 인증 시스템 구현"
    text2 = "로그인 기능 개발"
    text3 = "날씨 정보 확인"

    try:
        emb1 = engine.embed_text(text1)
        emb2 = engine.embed_text(text2)
        emb3 = engine.embed_text(text3)

        sim_12 = engine.cosine_similarity(emb1, emb2)
        sim_13 = engine.cosine_similarity(emb1, emb3)

        print(f"    ✅ 유사도 계산 성공")
        print(f"    - '{text1}' ↔ '{text2}': {sim_12:.4f} (높음)")
        print(f"    - '{text1}' ↔ '{text3}': {sim_13:.4f} (낮음)")

        if sim_12 > sim_13:
            print("    ✅ 유사도 판별 정확")
        else:
            print("    ⚠️  유사도 판별 이상")
    except Exception as e:
        print(f"    ❌ 유사도 계산 실패: {e}")
        return False

    # 배치 임베딩 테스트
    print("\n[4] 배치 임베딩 테스트...")
    texts = [
        "요구사항 문서 작성",
        "설계 문서 작성",
        "코드 리뷰 수행"
    ]

    try:
        batch_embs = engine.embed_batch(texts)
        print(f"    ✅ 배치 임베딩 성공")
        print(f"    - 입력: {len(texts)}개 텍스트")
        print(f"    - 출력: {len(batch_embs)}개 임베딩")
    except Exception as e:
        print(f"    ❌ 배치 임베딩 실패: {e}")
        return False

    # 의미 검색 테스트
    print("\n[5] 의미 검색 테스트...")
    query = "보안 설정"
    candidates = [
        "사용자 인증 구현",
        "보안 정책 수립",
        "날씨 API 연동",
        "암호화 알고리즘 적용",
        "UI 디자인"
    ]

    try:
        results = engine.find_most_similar(query, candidates, top_k=3)
        print(f"    ✅ 의미 검색 성공")
        print(f"    - 쿼리: '{query}'")
        print(f"    - Top 3:")
        for idx, score in results:
            print(f"      {score:.4f} - {candidates[idx]}")
    except Exception as e:
        print(f"    ❌ 의미 검색 실패: {e}")
        return False

    # 캐시 통계
    print("\n[6] 캐시 통계...")
    stats = engine.get_cache_stats()
    print(f"    Provider: {stats['provider']}")
    print(f"    Model: {stats['model']}")
    print(f"    Base URL: {stats['base_url']}")
    print(f"    Dimension: {stats['dimension']}")
    print(f"    Cached: {stats['total_cached']} embeddings")
    print(f"    Cache Size: {stats['cache_size_mb']:.2f} MB")

    print("\n" + "=" * 70)
    print("  ✅ 모든 테스트 통과!")
    print("=" * 70)

    return True


if __name__ == "__main__":
    provider = sys.argv[1] if len(sys.argv) > 1 else "auto"

    if provider not in ["auto", "ollama", "lmstudio"]:
        print(f"❌ Unknown provider: {provider}")
        print("Usage: python scripts/test_embedding.py [auto|ollama|lmstudio]")
        sys.exit(1)

    success = test_embedding(provider)

    if not success:
        print("\n❌ 테스트 실패")
        print("\n💡 문제 해결:")
        print("1. Ollama 사용:")
        print("   - ollama serve")
        print("   - ollama pull nomic-embed-text")
        print("")
        print("2. LM Studio 사용:")
        print("   - LM Studio 앱 실행")
        print("   - Models → Download → 'nomic-embed-text' 검색 → 다운로드")
        print("   - Local Server → nomic-embed-text 모델 로드 → Start Server")
        sys.exit(1)

    sys.exit(0)
