O조 (스마트스토어 1인 판매자 AI 에이전트) 프로젝트

이 프로젝트는 'DScover_D조'의 파일 구조를 기반으로 O조의 '스마트스토어 AI 에이전트' 시나리오를 실행하고 평가합니다.

🚀 실행 방법

1. 환경 설정

필요한 Python 라이브러리를 설치합니다. (run_smartstore.py가 requirements.txt를 생성해 줍니다.)

# (run_smartstore.py가 requirements.txt를 생성)
pip install -r requirements.txt


2. API 키 설정

이 디렉토리에 .env 파일을 생성하고, Upstage API 키를 입력합니다. (제공된 .env.example 파일 참고)

.env 파일 내용:

UPSTAGE_API_KEY="YOUR_API_KEY_HERE"


3. 시나리오 생성 (run)

run_smartstore.py를 실행하여 4개의 시나리오(Single 2, Multi 2)를 생성합니다.
이 스크립트는 scenarios_single_smartstore.json과 scenarios_multi_smartstore.json을 읽어 Solar Pro 2 API를 호출하고, 그 결과를 data/smartstore_final.jsonl 파일로 저장합니다.

python run_smartstore.py


입력: scenarios_single_smartstore.json, scenarios_multi_smartstore.json

출력: data/smartstore_final.jsonl

4. 시나리오 평가 (evaluate)

evaluate_smartstore.py를 실행하여 run 단계에서 생성된 .jsonl 파일을 평가합니다.
이 스크립트는 O조의 6개 툴 스키마를 기준으로 BFCL 평가(함수명, 인자, Hallucination)를 수행합니다.

python evaluate_smartstore.py --input data/smartstore_final.jsonl --output artifacts/smartstore_report.json


입력: data/smartstore_final.jsonl

출력 (리포트): artifacts/smartstore_report.json

출력 (콘솔): 평가 결과 요약 (성공/실패, 항목별 통과율)