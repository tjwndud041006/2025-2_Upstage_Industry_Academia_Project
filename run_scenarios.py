"""
===============================================================================
O조 (스마트스토어 1인 판매자 AI 에이전트) - FIXED 버전
===============================================================================

📋 프로젝트 요구사항 반영:
1. ✅ Agentic Reasoning (판단/비교/선택/오류복구)
2. ✅ Tool 호출 활성화 및 정상 동작
3. ✅ 의미 있는 Multi-turn (오류 복구, 조건부 선택)
4. ✅ BFCL 평가 100% 통과 목표
5. ✅ num_tools_called 메타데이터 추가

도메인: 쇼핑 & 이커머스
Tool 개수: 6개 (최적화)
시나리오: Single 2개, Multi 2개

===============================================================================
"""

import os
import sys
import json
import uuid
import random
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# ============================================================================
# 환경 설정
# ============================================================================

print("="*80)
print("O조 (스마트스토어 1인 판매자 AI 에이전트) - FIXED 버전")
print("="*80)

load_dotenv()
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "YOUR_API_KEY_HERE")

if UPSTAGE_API_KEY == "YOUR_API_KEY_HERE":
    print("\n⚠️  .env 파일에 UPSTAGE_API_KEY를 설정해주세요!")
    print("   (이 파일과 같은 위치에 .env 파일을 만들고 UPSTAGE_API_KEY=\"sk-xxx\" 형식으로 키를 입력하세요.)")
    sys.exit(1)

client = OpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v1"
)

os.makedirs("outputs", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("artifacts", exist_ok=True)

print("✅ 환경 설정 완료\n")


# ============================================================================
# Mock 함수 정의 (O조 6개 툴)
# ============================================================================

# --------------------------
# Tool 1: 스토어 대시보드 요약
# --------------------------
def get_store_dashboard(low_stock_threshold: str = "10") -> Dict[str, Any]:
    """
    일일 스토어 현황 요약 (신규주문, Q&A 개수, 재고부족)
    """
    try:
        threshold = int(low_stock_threshold)
    except ValueError:
        threshold = 10
        
    # Mock Data
    return {
        "new_orders": 5,
        "pending_qa_count": 2,
        "low_stock_products": [
            {"name": "A상품", "stock": 7}
        ],
        "analyzed_threshold": threshold
    }

# --------------------------
# Tool 2: 상품 전략 분석 (오류 복구 시나리오 포함)
# --------------------------
def analyze_product_strategy(product_id: str, analysis_keyword: str) -> Dict[str, Any]:
    """
    상품 재고(커머스)+키워드 트렌드(쇼핑인사이트) 동시 분석
    *** 시나리오 2.2 (오류 복구)를 위한 로직 포함 ***
    """
    # 시나리오 2.2: '울트라 웜 부츠' 키워드가 들어오면 의도적으로 오류 반환
    if "울트라 웜 부츠" in analysis_keyword:
        return {
            "product_id": product_id,
            "stock_level": 200, # 재고는 확인됨
            "keyword_trend": None,
            "error": f"No data found for '{analysis_keyword}'" # 트렌드 데이터 없음
        }
    
    # Mock Data (정상 케이스)
    mock_db = {
        "P123": {"stock_level": 7, "trend": 45.5, "keyword": "캠핑 의자"},
        "P456": {"stock_level": 150, "trend": -10.2, "keyword": "게이밍 의자"},
        "P789": {"stock_level": 200, "trend": 15.0, "keyword": "겨울 부츠"}
    }
    
    data = mock_db.get(product_id, {"stock_level": 50, "trend": 5.0, "keyword": analysis_keyword})
    
    return {
        "product_id": product_id,
        "stock_level": data["stock_level"],
        "keyword_trend": {
            "keyword": data["keyword"],
            "trend_change_percent": data["trend"]
        }
    }

# --------------------------
# Tool 3: 쇼핑 1위 트렌드 조회
# --------------------------
def get_top_shopping_trend(category_code: str) -> Dict[str, Any]:
    """
    카테고리 1위 트렌드 키워드 조회 (Mock)
    """
    # Mock Data
    return {
        "rank": 1,
        "keyword": "경량 패딩",
        "trend_score": 95.8,
        "change_percent": 45.5,
        "category_analyzed": category_code
    }

# --------------------------
# Tool 4: 블로그 포스팅
# --------------------------
def post_blog_promotion(title: str, content: str) -> Dict[str, Any]:
    """
    Solar가 생성한 글을 네이버 블로그에 포스팅 (Mock)
    """
    return {
        "status": "success",
        "post_url": f"https://blog.naver.com/my_id/{random.randint(1000, 9999)}",
        "title_length": len(title),
        "content_length": len(content)
    }

# --------------------------
# Tool 5: 카페 포스팅
# --------------------------
def post_cafe_article(cafe_id: str, menu_id: str, title: str, content: str) -> Dict[str, Any]:
    """
    Solar가 생성한 글을 네이버 카페에 포스팅 (Mock)
    """
    return {
        "status": "success",
        "article_url": f"https://cafe.naver.com/{cafe_id}/{random.randint(100, 999)}",
        "cafe_id": cafe_id,
        "menu_id": menu_id
    }

# --------------------------
# Tool 6: 판매자에게 알림 전송
# --------------------------
def alert_seller(message: str, alert_level: str) -> Dict[str, Any]:
    """
    판매자에게 카톡으로 긴급 알림 전송 (Mock)
    """
    return {
        "status": "success",
        "message_id": f"KA-{random.randint(10000, 99999)}",
        "sent_message": message,
        "level": alert_level
    }

# Tool 매핑
TOOL_FUNCTIONS = {
    "get_store_dashboard": get_store_dashboard,
    "analyze_product_strategy": analyze_product_strategy,
    "get_top_shopping_trend": get_top_shopping_trend,
    "post_blog_promotion": post_blog_promotion,
    "post_cafe_article": post_cafe_article,
    "alert_seller": alert_seller
}

# ============================================================================
# Tool JSON 스키마 정의 (O조 6개 툴)
# ============================================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_store_dashboard",
            "description": "일일 스토어 현황 요약 (신규주문, Q&A 개수, 재고부족)을 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "low_stock_threshold": {
                        "type": "string", 
                        "description": "재고 부족으로 간주할 기준 숫자(문자열 형태)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_product_strategy",
            "description": "특정 상품의 재고와 키워드 트렌드를 동시에 분석합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "분석할 상품의 고유 ID (예: P123)"},
                    "analysis_keyword": {"type": "string", "description": "분석에 사용할 연관 키워드 (예: '캠핑 의자')"}
                },
                "required": ["product_id", "analysis_keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_shopping_trend",
            "description": "특정 카테고리의 현재 쇼핑 트렌드 1위 키워드를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category_code": {"type": "string", "description": "네이버 쇼핑 카테고리 코드 (예: '50000000'은 '패션/잡화')"}
                },
                "required": ["category_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "post_blog_promotion",
            "description": "AI(Solar)가 생성한 제목과 본문을 네이버 블로그에 포스팅합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "포스팅할 블로그 글의 제목"},
                    "content": {"type": "string", "description": "포스팅할 블로그 글의 본문 (HTML 또는 텍스트)"}
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "post_cafe_article",
            "description": "AI(Solar)가 생성한 글을 네이버 카페에 포스팅합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cafe_id": {"type": "string", "description": "네이버 카페 고유 ID"},
                    "menu_id": {"type": "string", "description": "카페 내 게시판(메뉴) ID"},
                    "title": {"type": "string", "description": "게시글 제목"},
                    "content": {"type": "string", "description": "게시글 본문"}
                },
                "required": ["cafe_id", "menu_id", "title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "alert_seller",
            "description": "판매자에게 긴급 알림을 전송합니다(카톡).",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "전송할 알림 메시지 내용"},
                    "alert_level": {
                        "type": "string", 
                        "description": "알림 수준 (info: 정보, warning: 경고, urgent: 긴급)",
                        "enum": ["info", "warning", "urgent"]
                    }
                },
                "required": ["message", "alert_level"]
            }
        }
    }
]

# ============================================================================
# API 호출 및 Tool 실행
# ============================================================================

def call_solar_api(messages: List[Dict], tools_spec: List[Dict]) -> Dict[str, Any]:
    """Solar Pro 2 API 호출"""
    try:
        response = client.chat.completions.create(
            model="solar-pro",
            messages=messages,
            tools=tools_spec,
            tool_choice="auto",  # Tool 자동 선택 활성화
            temperature=0.7
        )
        return {
            "success": True,
            "message": response.choices[0].message
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def execute_tool_call(tool_call) -> Dict[str, Any]:
    """Tool 호출 실행 및 결과 반환"""
    func_name = tool_call.function.name
    func_args = json.loads(tool_call.function.arguments)
    
    if func_name in TOOL_FUNCTIONS:
        result = TOOL_FUNCTIONS[func_name](**func_args)
    else:
        result = {"error": f"Unknown function: {func_name}"}
    
    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "name": func_name,
        "content": json.dumps(result, ensure_ascii=False)
    }


# ============================================================================
# 시나리오 실행 함수들
# ============================================================================

def run_single_turn_scenario(scenario: Dict, tools_spec: List[Dict]) -> Dict[str, Any]:
    """Single-turn 시나리오 실행 (수정 버전)"""
    
    scenario_id = scenario["id"]
    user_query = scenario["user_query"]  # ✅ "query" → "user_query" 수정
    
    print(f"\n{'='*70}")
    print(f"[{scenario_id}] {scenario['task_description']}")
    print(f"{'='*70}")
    print(f"Query: {user_query}")
    
    # 간단하고 명확한 시스템 프롬프트 (Tool 호출을 방해하지 않도록)
    system_prompt = """너는 1인 스마트스토어 판매자를 돕는 AI 조수야.
너는 '쇼핑 & 이커머스' 도메인의 전문가이며, 주어진 툴(Tool)을 활용해 판매자의 운영과 마케팅 업무를 자동화해야 해.

[규칙]
1. 사용자의 요청을 분석하고 필요한 Tool을 호출해야 해.
2. Tool 호출 결과를 바탕으로 사용자에게 명확하고 유용한 답변을 제공해야 해.
3. 여러 Tool을 동시에 호출할 수 있어.
4. Tool 호출 전에 사고 과정을 <think> 태그로 작성해.
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    
    conversation_log = [{"role": "user", "content": user_query}]
    tool_calls_log = [] # 평가용 툴 호출 로그
    
    iteration = 0
    max_iterations = 5 # 최대 툴 호출 횟수
    
    while iteration < max_iterations:
        iteration += 1
        
        response = call_solar_api(messages, tools_spec)
        if not response["success"]:
            return {"error": "API 호출 실패", "details": response["error"]}
        
        assistant_message = response["message"]
        conversation_log.append(assistant_message.model_dump()) # 전체 저장
        
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            messages.append(assistant_message)
            
            for tool_call in assistant_message.tool_calls:
                tool_result = execute_tool_call(tool_call)
                messages.append(tool_result)
                conversation_log.append(tool_result)
                # 평가 스크립트가 인식하는 형식으로 tool_calls_log에 저장
                tool_calls_log.append({
                    "name": tool_result["name"],
                    "arguments": json.loads(tool_call.function.arguments) # 파싱된 딕셔너리
                })
        else:
            final_answer = assistant_message.content
            print(f"  💬 답변 완료")
            print(f"  📊 Tool 호출: {len(tool_calls_log)}회\n")
            break
    
    return {
        "id": scenario_id,
        "query": user_query,
        "conversation": conversation_log,
        "tool_calls": tool_calls_log, # 평가 스크립트가 인식하는 tool_calls (실제 실행된 것)
        "metadata": {
            "scenario_type": "single-turn",
            "num_tools_called": len(tool_calls_log),  # ✅ 누락된 필드 추가
            "tools_used": list(set([t["name"] for t in tool_calls_log])),
            **scenario
        }
    }


def run_multi_turn_scenario(scenario: Dict, tools_spec: List[Dict]) -> Dict[str, Any]:
    """Multi-turn 시나리오 실행"""
    
    scenario_id = scenario["id"]
    initial_query = scenario["initial_query"]
    follow_ups = scenario["follow_up_queries"]
    
    print(f"\n{'='*70}")
    print(f"[{scenario_id}] {scenario['task_description']}")
    print(f"{'='*70}")
    
    system_prompt = """너는 1인 스마트스토어 판매자를 돕는 AI 조수(에이전트)야.
너는 '쇼핑 & 이커머스' 도메인의 전문가이며, 주어진 툴(Tool)을 활용해 판매자의 운영과 마케팅 업무를 자동화해야 해.
너는 여러 턴에 걸쳐 대화의 맥락을 기억하고 작업을 수행해야 한다.

[규칙]
1. 사용자의 요청을 분석하고 필요한 Tool을 호출해야 해.
2. 사용자의 선택이나 맥락에 따라 '조건부로' 다른 툴을 선택할 수 있어야 해.
3. 툴 호출이 실패하면(예: API가 error 반환), 그 원인을 사용자에게 설명하고 대안을 제시하여 '오류를 복구'해야 해.
4. Tool 호출 전에 사고 과정을 <think> 태그로 작성해.
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    all_conversation = []
    all_tool_calls = [] # 평가용 전체 툴 호출 로그
    turn_count = 0
    
    queries = [initial_query] + follow_ups
    
    for query_idx, query in enumerate(queries):
        turn_count += 1
        print(f"  [Turn {turn_count}] {query}")
        
        user_message = {"role": "user", "content": query}
        messages.append(user_message)
        all_conversation.append(user_message)
        
        max_iterations = 3 # 툴 호출은 턴당 최대 3번 (재호출 등)
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            response = call_solar_api(messages, tools_spec)
            if not response["success"]:
                error_msg = {"role": "assistant", "content": f"API 호출 오류: {response['error']}"}
                messages.append(error_msg)
                all_conversation.append(error_msg)
                break
            
            assistant_message = response["message"]
            messages.append(assistant_message)
            all_conversation.append(assistant_message.model_dump())
            
            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    tool_result = execute_tool_call(tool_call)
                    messages.append(tool_result)
                    all_conversation.append(tool_result)
                    # 평가 스크립트가 인식하는 형식으로 tool_calls_log에 저장
                    all_tool_calls.append({
                        "name": tool_result["name"],
                        "arguments": json.loads(tool_call.function.arguments) # 파싱된 딕셔너리
                    })
            else:
                print(f"    💬 답변 완료\n")
                break # 툴 호출 없으면 턴 종료
    
    print(f"  📊 총 Tool 호출: {len(all_tool_calls)}회")
    
    return {
        "id": scenario_id,
        "query": initial_query, # 대표 쿼리
        "conversation": all_conversation,
        "tool_calls": all_tool_calls, # 평가 스크립트가 인식하는 tool_calls
        "metadata": {
            "scenario_type": "multi-turn",
            "num_turns": turn_count,
            "tools_used": list(set([t["name"] for t in all_tool_calls])),
            "num_tools_called": len(all_tool_calls),
            **scenario
        }
    }


# ============================================================================
# 메인 - O조 시나리오 4개 실행
# ============================================================================

def main():
    print("\n" + "="*80)
    print("O조 - 스마트스토어 시나리오 4개 실행")
    print("="*80)
    
    # 시나리오 JSON 파일 로드
    try:
        with open("scenarios_single_smartstore.json", "r", encoding="utf-8") as f:
            single_data = json.load(f)
        
        with open("scenarios_multi_smartstore.json", "r", encoding="utf-8") as f:
            multi_data = json.load(f)
    except FileNotFoundError:
        print("❌ 시나리오 정의 파일(scenarios_single_smartstore.json 또는 scenarios_multi_smartstore.json)을 찾을 수 없습니다.")
        return

    single_scenarios = single_data["scenarios"]
    multi_scenarios = multi_data["scenarios"]
    
    print(f"\n✅ 시나리오 로드")
    print(f"   - Single: {len(single_scenarios)}개")
    print(f"   - Multi: {len(multi_scenarios)}개")
    
    all_results = []
    
    # Single-turn
    print("\n" + "="*80)
    print("SINGLE-TURN 실행")
    print("="*80)
    
    for scenario in single_scenarios:
        result = run_single_turn_scenario(scenario, tools)
        all_results.append(result)
        time.sleep(1) # API 속도 제한
    
    # Multi-turn
    print("\n" + "="*80)
    print("MULTI-TURN 실행")
    print("="*80)
    
    for scenario in multi_scenarios:
        result = run_multi_turn_scenario(scenario, tools)
        all_results.append(result)
        time.sleep(1) # API 속도 제한
    
    # 저장
    output_file = "data/smartstore_final.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for result in all_results:
            # evaluate_final.py는 'id'와 'tool_calls'를 최상위에 기대합니다.
            eval_entry = {
                "id": result["id"],
                "query": result["query"],
                "conversation": result["conversation"],
                "tool_calls": result["tool_calls"], # 
                "metadata": result["metadata"]
            }
            f.write(json.dumps(eval_entry, ensure_ascii=False) + "\n")
    
    print("\n" + "="*80)
    print("✅ 완료!")
    print("="*80)
    print(f"\n📁 결과: {output_file}")
    
    # 통계
    single_count = sum(1 for r in all_results if r["metadata"]["scenario_type"] == "single-turn")
    multi_count = sum(1 for r in all_results if r["metadata"]["scenario_type"] == "multi-turn")
    total_tools_called = sum(r["metadata"]["num_tools_called"] for r in all_results)
    avg_tools = total_tools_called / len(all_results) if len(all_results) > 0 else 0
    
    print(f"\n📊 통계:")
    print(f"  - Single 시나리오: {single_count}개")
    print(f"  - Multi 시나리오: {multi_count}개")
    print(f"  - 평균 Tool 호출: {avg_tools:.1f}회")
    print(f"  - 총 Tool 호출: {total_tools_called}회")
    print(f"  - 총 Tool: {len(tools)}개 (O조 최적화)")
    
    print(f"\n🚀 다음 단계:")
    print(f"  1. 터미널에서 'python evaluate_smartstore.py --input {output_file}'을 실행하여 평가하세요.")


if __name__ == "__main__":
    main()