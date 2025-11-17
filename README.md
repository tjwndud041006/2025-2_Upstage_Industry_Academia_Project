# 네이버 스마트스토어 운영 Agentic 시나리오 설계

**Upstage 산업 협력 프로젝트 - DScover D조**

---

## 🧑‍💻 Team DScover (D조)

| 이름 |
| :--- |
| 서주영 |
| 이수빈 |
| 이지원 |
| 김진성 |


---

## 1. 프로젝트 개요

본 프로젝트는 네이버 스마트스토어를 운영하는 **1인 소규모 셀러**들이 겪는 운영상의 병목 현상을 해결하기 위해 설계되었습니다. CS 응대, 마케팅, 재고 관리에 이르는 복잡한 업무를 자연어 명령을 통해 자동화하는 **AI Agent 시나리오 데이터셋**을 구축하는 것을 목표로 합니다.

## 2. 핵심 Agentic Reasoning 설계

단순한 툴 호출이 아닌, 툴과 툴 사이의 결과를 바탕으로 AI가 스스로 판단하고, 작업을 연계하며, 오류를 복구하는 3가지 핵심 '에이전트적 사고' 로직을 구현했습니다.

### 2.1. 순차적 툴 연계 (Agentic Chain)

1.  **인지:** `analyze_product_strategy` 툴로 상품 재고와 트렌드 데이터를 분석합니다.
2.  **판단/가공:** AI가 분석 결과(예: 재고 7개)를 "위험" 상태로 인지하고, 요약 리포트 메시지를 스스로 생성합니다.
3.  **연계 실행:** 생성된 메시지를 `alert_seller` 툴의 인자로 사용해 판매자에게 카톡 알림을 전송합니다.

### 2.2. 조건부 선택 (Conditional Selection)

1.  **인지/생성:** `get_top_shopping_trend`로 트렌드 키워드를 확보하고, AI가 홍보용 콘텐츠를 스스로 생성합니다.
2.  **판단:** AI가 사용자에게 "1. 블로그"와 "2. 카페" 중 발행할 채널을 묻습니다.
3.  **조건부 행동:** 사용자 선택(예: '2. 카페')에 따라 `post_cafe_article` 툴을 조건부로 호출합니다.

### 2.3. 오류 복구 (Error Recovery)

1.  **오류 감지:** `analyze_product_strategy` 툴이 "데이터 없음(No data found)" 오류를 반환합니다.
2.  **원인 분석/대안 제시:** AI가 오류를 인지하고 "키워드 데이터가 없습니다"라고 원인을 분석한 뒤, 사용자에게 "다른 연관 키워드를 알려달라"고 대안을 제시합니다.
3.  **재실행:** 사용자가 새 키워드를 제공하면, 툴을 새로운 인자로 다시 호출하여 작업을 성공적으로 복구합니다.

---

## 3. 정의된 Tool 및 활용 API

프로젝트 시나리오를 위해 네이버 커머스, 쇼핑인사이트, 카카오톡, 네이버 소셜 API를 기반으로 총 6개의 툴을 정의했습니다.

| Tool 이름 | 설명 | 통합 API |
| :--- | :--- | :--- |
| `get_store_dashboard` | 일일 스토어 현황 요약 (신규주문, Q&A, 재고부족) | 네이버 커머스 API |
| `analyze_product_strategy` | 상품 재고와 키워드 트렌드 동시 분석 | 커머스 API + 쇼핑인사이트 API |
| `get_top_shopping_trend` | 카테고리 1위 트렌드 키워드 조회 | 네이버 쇼핑인사이트 API |
| `post_blog_promotion` | AI가 생성한 글을 네이버 블로그에 포스팅 | 네이버 블로그 API |
| `post_cafe_article` | AI가 생성한 글을 네이버 카페에 포스팅 | 네이버 카페 API |
| `alert_seller` | 판매자에게 카톡으로 긴급 알림 전송 | 카카오톡 메시지 API |

---

## 4. 시나리오 데이터셋 (JSON)

본 리포지토리에는 4개의 핵심 시나리오를 정의한 JSON 데이터셋이 포함되어 있습니다.

### 4.1. Single-Turn

1.  **DScover_D조_Single_1.json (시나리오 1-1)**
    * **Task:** 전략 분석 및 즉시 리포트
    * **로직:** `analyze_product_strategy` → `alert_seller` (순차적 툴 연계)
2.  **DScover_D조_Single_2.json (시나리오 1-2)**
    * **Task:** 주력 상품 전략 비교 분석
    * **로직:** `analyze_product_strategy` (A상품)과 `analyze_product_strategy` (B상품) (병렬 Tool 호출)

### 4.2. Multi-Turn

3.  **DScover_D조_Multi_1.json (시나리오 2-1)**
    * **Task:** 마케팅 자동화 (조건부 선택)
    * **로직:** `get_top_shopping_trend` → (AI 글 생성 및 채널 선택) → `post_cafe_article` (조건부 선택)
4.  **DScover_D조_Multi_2.json (시나리오 2-2)**
    * **Task:** 트렌드 분석 실패 (오류 복구)
    * **로직:** `analyze_product_strategy` (실패) → (AI 대안 제시) → `analyze_product_strategy` (성공) (오류 복구)

---

## 5. 평가 결과

* 제출된 4개의 시나리오 모두 **BFCL(Berkeley Function-Calling Leaderboard) 정량 평가 기준을 100% 통과**했습니다.
* Correct Function Name (4/4), Valid Arguments (4/4), No Hallucinated Calls (4/4) 항목을 모두 만족하여, AI가 정의된 툴을 일관되게 정확히 호출함을 확인했습니다.2.  **DScover_D조_Single_2.json (시나리오 1-2)**
    * [cite_start]**Task:** 주력 상품 전략 비교 분석 [cite: 66]
    * [cite_start]**로직:** `analyze_product_strategy` (A상품)과 `analyze_product_strategy` (B상품) (병렬 Tool 호출) [cite: 68]

### 4.2. Multi-Turn

3.  **DScover_D조_Multi_1.json (시나리오 2-1)**
    * [cite_start]**Task:** 마케팅 자동화 (조건부 선택) [cite: 73]
    * [cite_start]**로직:** `get_top_shopping_trend` → (AI 글 생성 및 채널 선택) → `post_cafe_article` (조건부 선택) [cite: 77, 84]
4.  **DScover_D조_Multi_2.json (시나리오 2-2)**
    * [cite_start]**Task:** 트렌드 분석 실패 (오류 복구) [cite: 87]
    * [cite_start]**로직:** `analyze_product_strategy` (실패) → (AI 대안 제시) → `analyze_product_strategy` (성공) (오류 복구) [cite: 90, 98]

---

## 5. 평가 결과

* [cite_start]제출된 4개의 시나리오 모두 **BFCL(Berkeley Function-Calling Leaderboard) 정량 평가 기준을 100% 통과**했습니다[cite: 105].
* [cite_start]Correct Function Name (4/4), Valid Arguments (4/4), No Hallucinated Calls (4/4) 항목을 모두 만족하여, AI가 정의된 툴을 일관되게 정확히 호출함을 확인했습니다[cite: 106, 107].
