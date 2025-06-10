# -*- coding: utf-8 -*-
"""
기존 파이프라인 자동화 실행기
"""

import subprocess
import sys
from pathlib import Path

def install_watchdog():
    """watchdog 패키지가 없으면 설치"""
    try:
        import watchdog
    except ImportError:
        print("📦 watchdog 패키지 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "watchdog"])
        print("✅ watchdog 설치 완료")

def create_test_json():
    """테스트용 JSON 파일 생성"""
    import json
    
    test_data = {
        "session_id": "test_automation",
        "consulting_content": """상담사: 안녕하세요, 상담원 김영희입니다. 어떤 도움이 필요하신가요?
손님: 네, 안녕하세요. 카드 관련해서 문의드리고 싶습니다.
상담사: 네, 고객님. 어떤 카드 관련 문의이신지 말씀해 주세요.
손님: 제가 새로 발급받은 카드가 있는데, 사용법을 잘 모르겠어서요.
상담사: 네, 친절히 안내해드리겠습니다. 어떤 기능에 대해 궁금하신가요?
손님: 결제할 때 주의사항이 있나요?
상담사: 네, 말씀드리겠습니다. 첫째, 비밀번호는 다른 사람이 보지 않도록 주의해주세요. 둘째, 사용 후에는 영수증을 꼭 확인해주시기 바랍니다.
손님: 아, 그렇군요. 감사합니다.
상담사: 네, 도움이 되셨다면 다행입니다. 추가 문의사항이 있으시면 언제든지 연락주세요.
손님: 네, 감사합니다.""",
        "instructions": [
            {
                "task_category": "상담 주제",
                "output": "카드 사용법 문의"
            },
            {
                "task_category": "상담 내용",
                "output": "일반 문의 상담"
            }
        ]
    }
    
    # data/classification 폴더에 테스트 파일 생성
    test_dir = Path("data/classification")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = test_dir / "test_automation.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 테스트 파일 생성: {test_file}")
    return test_file

def main():
    """메인 실행 함수"""
    print("🚀 기존 파이프라인 자동화 시스템")
    print("="*50)
    
    # watchdog 패키지 확인 및 설치
    install_watchdog()
    
    print("\n다음 중 선택하세요:")
    print("1. 테스트 실행 (샘플 JSON으로 테스트)")
    print("2. 실시간 모니터링 시작")
    print("3. 특정 폴더 일괄 처리")
    print("4. 종료")
    
    while True:
        choice = input("\n선택 (1-4): ").strip()
        
        if choice == "1":
            # 테스트 실행
            print("\n🧪 테스트 실행 중...")
            test_file = create_test_json()
            
            print("파이프라인 실행 중...")
            subprocess.run([sys.executable, "pipeline_automation.py", str(test_file.parent)])
            break
            
        elif choice == "2":
            # 실시간 모니터링
            print("\n👁️ 실시간 모니터링 모드")
            print("data 폴더에 JSON 파일을 넣으면 자동으로 처리됩니다.")
            subprocess.run([sys.executable, "pipeline_automation.py"])
            break
            
        elif choice == "3":
            # 폴더 일괄 처리
            folder_path = input("처리할 폴더 경로를 입력하세요: ").strip()
            subprocess.run([sys.executable, "pipeline_automation.py", folder_path])
            break
            
        elif choice == "4":
            print("👋 프로그램을 종료합니다.")
            break
            
        else:
            print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main() 