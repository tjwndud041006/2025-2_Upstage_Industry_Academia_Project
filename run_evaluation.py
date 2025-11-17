"""
evaluate_smartstore.py - O조 (스마트스토어) 프로젝트 평가 스크립트

Tool 개수: 6개 (최적화)
- get_store_dashboard
- analyze_product_strategy
- get_top_shopping_trend
- post_blog_promotion
- post_cafe_article
- alert_seller
"""

import json
import os
import sys
from typing import Dict, List, Any, Tuple
from datetime import datetime

# ============================================================================
# ⚠️ O조 Tool 정의 (evaluate_final.py 기반으로 수정)
# ============================================================================

# 정의된 Tool (O조 6개)
DEFINED_TOOLS = {
    "get_store_dashboard",
    "analyze_product_strategy",
    "get_top_shopping_trend",
    "post_blog_promotion",
    "post_cafe_article",
    "alert_seller"
}

# 필수 인자 (O조 6개 툴 기준)
TOOL_REQUIRED_ARGS = {
    "get_store_dashboard": [],
    "analyze_product_strategy": ["product_id", "analysis_keyword"],
    "get_top_shopping_trend": ["category_code"],
    "post_blog_promotion": ["title", "content"],
    "post_cafe_article": ["cafe_id", "menu_id", "title", "content"],
    "alert_seller": ["message", "alert_level"]
}

# 타입 정의 (O조 6개 툴 기준 - 모두 string 또는 enum(string))
TOOL_ARG_TYPES = {
    "get_store_dashboard": {
        "low_stock_threshold": "string"
    },
    "analyze_product_strategy": {
        "product_id": "string",
        "analysis_keyword": "string"
    },
    "get_top_shopping_trend": {
        "category_code": "string"
    },
    "post_blog_promotion": {
        "title": "string",
        "content": "string"
    },
    "post_cafe_article": {
        "cafe_id": "string",
        "menu_id": "string",
        "title": "string",
        "content": "string"
    },
    "alert_seller": {
        "message": "string",
        "alert_level": "string"
    }
}

# 제약 조건 (O조 6개 툴 기준)
ARG_CONSTRAINTS = {
    "alert_level": ["info", "warning", "urgent"] # enum
}

# ============================================================================
# (이하 DScover_D조의 evaluate_final.py와 거의 동일한 로직)
# ============================================================================

def _validate_type(value: Any, expected_type: str) -> bool:
    """타입 검증 (O조 툴은 모두 string이므로 단순화)"""
    type_mapping = {
        "string": str,
        "integer": int, # (참고: O조 툴은 integer를 사용하지 않음)
        "boolean": bool # (참고: O조 툴은 boolean을 사용하지 않음)
    }
    expected_python_type = type_mapping.get(expected_type)
    if expected_python_type is None:
        return True
    
    # O조 툴은 모두 string 타입이므로 string인지 확인
    if expected_type == "string":
        return isinstance(value, str)
        
    return isinstance(value, expected_python_type)


def check_hallucinated_calls(tool_calls: List[Dict]) -> Tuple[bool, List[str]]:
    """정의되지 않은 함수 호출 확인"""
    errors = []
    for tool_call in tool_calls:
        # run_smartstore.py의 tool_calls 로그 형식에 맞춤 ('name' 사용)
        tool_name = tool_call.get("name") or tool_call.get("tool_name")
        if tool_name and tool_name not in DEFINED_TOOLS:
            errors.append(f"❌ 정의되지 않은 함수: {tool_name}")
    return len(errors) == 0, errors


def evaluate_single_tool_call(tool_call: Dict) -> Dict:
    """단일 툴 호출 평가"""
    # run_smartstore.py의 tool_calls 로그 형식에 맞춤
    tool_name = tool_call.get("name") or tool_call.get("tool_name", "unknown")
    arguments = tool_call.get("arguments", {})
    
    result = {
        "tool_name": tool_name,
        "correct_function_name": False,
        "valid_arguments": False,
        "errors": []
    }
    
    # 1. Function Name
    if tool_name not in DEFINED_TOOLS:
        result["errors"].append(f"정의되지 않은 함수: {tool_name}")
        return result
    
    result["correct_function_name"] = True
    
    # 2. Arguments
    required_args = TOOL_REQUIRED_ARGS.get(tool_name, [])
    missing_args = [arg for arg in required_args if arg not in arguments]
    
    if missing_args:
        result["errors"].append(f"필수 인자 누락: {missing_args}")
        # 필수 인자 누락은 심각한 오류이므로 여기서 반환
        return result
    
    # 타입 확인
    arg_types = TOOL_ARG_TYPES.get(tool_name, {})
    type_errors = False
    for arg_name, arg_value in arguments.items():
        if arg_name in arg_types:
            expected_type = arg_types[arg_name]
            if not _validate_type(arg_value, expected_type):
                result["errors"].append(f"'{arg_name}' 타입 오류 (기대: {expected_type}, 실제: {type(arg_value).__name__})")
                type_errors = True
    
    # 제약 조건 (Enum 등)
    constraint_errors = False
    for arg_name, arg_value in arguments.items():
        if arg_name in ARG_CONSTRAINTS:
            constraint = ARG_CONSTRAINTS[arg_name]
            
            if isinstance(constraint, list): # Enum
                if arg_value not in constraint:
                    result["errors"].append(f"'{arg_name}' 허용되지 않는 값: {arg_value} (기대: {constraint})")
                    constraint_errors = True
    
    if not result["errors"] and not type_errors and not constraint_errors:
        result["valid_arguments"] = True
    
    return result


def evaluate_scenario(scenario: Dict) -> Dict:
    """단일 시나리오(entry) 평가"""
    scenario_id = scenario.get("id", "unknown")
    # run_smartstore.py가 생성한 최상위 tool_calls 로그 사용
    tool_calls = scenario.get("tool_calls", [])
    metadata = scenario.get("metadata", {})
    
    result = {
        "scenario_id": scenario_id,
        "scenario_type": metadata.get("scenario_type", "unknown"),
        "correct_function_name": False,
        "valid_arguments": False,
        "no_hallucinated_calls": False,
        "pass": False,
        "errors": [],
        "total_tool_calls": len(tool_calls),
        "tool_results": [],
    }
    
    if len(tool_calls) == 0:
        # 오류 복구 시나리오(2.2)의 1턴처럼 툴 호출이 없는 턴이 있을 수 있으나,
        # 전체 시나리오에서 툴 호출이 0개인 경우만 오류로 처리.
        # (run_smartstore.py가 생성한 tool_calls는 전체 턴의 툴 호출 목록임)
        # 
        # 단, O조 시나리오는 툴 호출이 0개인 경우가 없으므로 이 로직은 유지.
        # (시나리오 2.1은 1턴 1개, 2턴 1개. 시나리오 2.2는 1턴 1개, 2턴 1개)
        # -> 재확인: DScover_D조의 `evaluate_final.py`는 `scenario.get("tool_calls")`를 봅니다.
        # O조의 `run_smartstore.py`는 `tool_calls`에 *전체 턴*의 툴 호출을 누적합니다.
        # 따라서 `len(tool_calls) == 0`인 경우는 없습니다.
        pass

    # 3. No Hallucinated
    no_halluc, halluc_errors = check_hallucinated_calls(tool_calls)
    result["no_hallucinated_calls"] = no_halluc
    if halluc_errors:
        result["errors"].extend(halluc_errors)
        # Hallucination은 심각한 오류이므로 여기서 평가 중단
        return result
    
    # 각 Tool 평가
    all_func_correct = True
    all_args_valid = True
    
    for idx, tool_call in enumerate(tool_calls):
        tool_result = evaluate_single_tool_call(tool_call)
        tool_result["call_index"] = idx
        result["tool_results"].append(tool_result)
        
        if not tool_result["correct_function_name"]:
            all_func_correct = False
        
        if not tool_result["valid_arguments"]:
            all_args_valid = False
        
        if tool_result["errors"]:
            result["errors"].extend([f"[호출 {idx+1} ({tool_result['tool_name']})] {err}" for err in tool_result["errors"]])

    result["correct_function_name"] = all_func_correct
    result["valid_arguments"] = all_args_valid
    result["pass"] = (
        result["correct_function_name"] and
        result["valid_arguments"] and
        result["no_hallucinated_calls"]
    )
    
    return result


def load_scenarios(input_path: str) -> List[Dict]:
    """JSONL 파일 로드"""
    scenarios = []
    
    if not os.path.exists(input_path):
        print(f"❌ 평가할 입력 파일이 없습니다: {input_path}")
        return scenarios

    if input_path.endswith(".jsonl"):
        with open(input_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        scenarios.append(json.loads(line))
                    except json.JSONDecodeError:
                        print(f"⚠️ {input_path} 파일의 {line_num}번째 줄 JSON 파싱 오류. 건너뜁니다.")
    else:
        # (DScover_D조와 달리 .json 리스트는 지원하지 않음. .jsonl만 사용)
        print(f"⚠️ .jsonl 파일만 지원합니다. ({input_path})")
    
    return scenarios


def print_summary(results: List[Dict]):
    """평가 결과 요약 출력"""
    total = len(results)
    if total == 0:
        print("\n" + "="*80)
        print("📊 평가 결과: 0개 항목 (평가할 데이터 없음)")
        print("="*80)
        return

    passed = sum(1 for r in results if r["pass"])
    
    print("\n" + "="*80)
    print(f"📊 BFCL 평가 결과 (O조: 스마트스토어)")
    print("="*80)
    
    print(f"\n총 시나리오: {total}개")
    print(f"✅ 통과: {passed}개 ({passed/total*100:.1f}%)")
    print(f"❌ 실패: {total - passed}개")
    
    if total > 0:
        print(f"\n📋 BFCL 평가 항목:")
        correct_name = sum(1 for r in results if r["correct_function_name"])
        valid_args = sum(1 for r in results if r["valid_arguments"])
        no_halluc = sum(1 for r in results if r["no_hallucinated_calls"])
        
        print(f"  1️⃣  Correct Function Name: {correct_name}/{total} ({correct_name/total*100:.1f}%)")
        print(f"  2️⃣  Valid Arguments: {valid_args}/{total} ({valid_args/total*100:.1f}%)")
        print(f"  3️⃣  No Hallucinated Calls: {no_halluc}/{total} ({no_halluc/total*100:.1f}%)")
    
    # 타입별
    single_results = [r for r in results if r["scenario_type"] == "single-turn"]
    multi_results = [r for r in results if r["scenario_type"] == "multi-turn"]
    
    if single_results:
        single_passed = sum(1 for r in single_results if r["pass"])
        print(f"\n🔹 Single: {single_passed}/{len(single_results)} 통과 ({single_passed/len(single_results)*100:.1f}%)")
    
    if multi_results:
        multi_passed = sum(1 for r in multi_results if r["pass"])
        print(f"🔹 Multi: {multi_passed}/{len(multi_results)} 통과 ({multi_passed/len(multi_results)*100:.1f}%)")
    
    # 실패 상세
    failed = [r for r in results if not r["pass"]]
    if failed:
        print(f"\n❌ 실패 시나리오:")
        for r in failed:
            print(f"\n  [{r['scenario_id']}]")
            for error in r["errors"][:2]: # 최대 2개 오류만 출력
                print(f"    - {error}")
    
    print("\n" + "="*80)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="O조 (스마트스토어) 프로젝트 평가 스크립트")
    parser.add_argument("--input", required=True, help="입력 .jsonl 파일 (예: data/smartstore_final.jsonl)")
    parser.add_argument("--output", default="artifacts/smartstore_report.json", help="평가 결과 .json 리포트 파일")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"❌ 파일 없음: {args.input}")
        sys.exit(1)
    
    print("="*80)
    print("O조 (스마트스토어) - BFCL 평가")
    print("="*80)
    print(f"\n📂 입력: {args.input}")
    
    scenarios = load_scenarios(args.input)
    if not scenarios:
        return # 로드 실패 시 종료

    print(f"✅ {len(scenarios)}개 시나리오 로드")
    
    print("\n🔍 평가 중...")
    results = [evaluate_scenario(s) for s in scenarios]
    
    print_summary(results)
    
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 결과 저장: {args.output}")


if __name__ == "__main__":
    main()