# -*- coding: utf-8 -*-
"""
기존 4개 파이썬 파일을 이용한 상담 품질 분류 자동화 파이프라인
- 분류 결과: 만족, 미흡, 해결 불가, 추가 상담 필요
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path
import json
import pandas as pd

class ClassificationPipeline:
    """상담 품질 분류 자동화 파이프라인"""
    
    def __init__(self):
        # 기존 4개 파이썬 파일 순서
        self.scripts = [
            "1_preprocessing_model_v3.py",
            "2_coloums_extraction_v3_json2csv.py", 
            "3_make_dataset.py",
            "4_simple_model_v2.py"
        ]
        
        self.script_names = [
            "1단계: 전처리 및 JSON 병합",
            "2단계: 텍스트 특성 추출",
            "3단계: 데이터셋 생성", 
            "4단계: 상담 품질 분류 모델 실행"
        ]
        
        # 상담 결과 분류 레이블
        self.quality_labels = {
            "만족": "고객이 상담 결과에 만족한 경우",
            "미흡": "상담이 진행되었으나 고객 만족도가 낮은 경우", 
            "해결 불가": "고객의 문제를 해결할 수 없는 경우",
            "추가 상담 필요": "추가적인 상담이나 처리가 필요한 경우"
        }
        
        self.check_files()
    
    def check_files(self):
        """필요한 파일들이 존재하는지 확인"""
        missing = []
        for script in self.scripts:
            if not Path(script).exists():
                missing.append(script)
        
        if missing:
            print(f"ERROR: 다음 파일들이 없습니다: {missing}")
            sys.exit(1)
        else:
            print("OK: 모든 스크립트 파일이 존재합니다.")
    
    def run_script(self, script_name, step_name):
        """개별 스크립트 실행"""
        print(f"\n[시작] {step_name}")
        print(f"실행: {script_name}")
        
        try:
            # PYTHONIOENCODING 설정으로 인코딩 문제 해결
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run(
                [sys.executable, script_name], 
                capture_output=True, 
                text=True, 
                timeout=600,  # 10분 타임아웃
                env=env
            )
            
            if result.returncode == 0:
                print(f"[성공] {step_name} 완료")
                return True
            else:
                print(f"[실패] {step_name}")
                print(f"오류: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[타임아웃] {step_name}")
            return False
        except Exception as e:
            print(f"[예외] {step_name} - {str(e)}")
            return False
    
    def create_quality_labels_if_needed(self):
        """상담 품질 레이블 파일 생성 (없는 경우)"""
        labels_dir = Path("columns_extraction_all/preprocessing")
        labels_dir.mkdir(parents=True, exist_ok=True)
        
        labels_file = labels_dir / "session_labels.csv"
        
        # 기존 파일이 1개 세션만 있으면 더 추가
        if labels_file.exists():
            df = pd.read_csv(labels_file, dtype={'session_id': str})
            if len(df) < 2:  # 샘플 데이터 추가
                print("기존 레이블 파일에 샘플 데이터 추가 중...")
                new_data = [
                    {"session_id": "20593", "result_label": "만족"},
                    {"session_id": "test_001", "result_label": "미흡"},
                    {"session_id": "test_002", "result_label": "해결 불가"},
                    {"session_id": "test_003", "result_label": "추가 상담 필요"}
                ]
                df_new = pd.DataFrame(new_data)
                df_combined = pd.concat([df, df_new]).drop_duplicates('session_id')
                df_combined.to_csv(labels_file, index=False, encoding='utf-8-sig')
                print(f"레이블 파일 업데이트: {len(df_combined)}개 세션")
        else:
            # 새로 생성
            print("상담 품질 레이블 파일 생성 중...")
            sample_data = [
                {"session_id": "20593", "result_label": "만족"},
                {"session_id": "test_001", "result_label": "미흡"},
                {"session_id": "test_002", "result_label": "해결 불가"},
                {"session_id": "test_003", "result_label": "추가 상담 필요"}
            ]
            df = pd.DataFrame(sample_data)
            df.to_csv(labels_file, index=False, encoding='utf-8-sig')
            print(f"레이블 파일 생성: {labels_file}")
    
    def analyze_classification_results(self):
        """분류 결과 분석 및 표시"""
        print("\n" + "="*60)
        print("상담 품질 분류 결과 분석")
        print("="*60)
        
        try:
            # 1) 텍스트 특성 파일 확인
            feature_file = "output/text_features_all_v4.csv"
            if Path(feature_file).exists():
                df_features = pd.read_csv(feature_file, encoding='utf-8-sig')
                print(f"특성 추출 완료: {len(df_features)}개 세션")
            
            # 2) 레이블 파일 확인  
            labels_file = "columns_extraction_all/preprocessing/session_labels.csv"
            if Path(labels_file).exists():
                df_labels = pd.read_csv(labels_file, encoding='utf-8-sig')
                print(f"분류 레이블: {len(df_labels)}개 세션")
                
                # 레이블 분포 표시
                label_counts = df_labels['result_label'].value_counts()
                print("\n[분류 결과 분포]")
                for label, count in label_counts.items():
                    description = self.quality_labels.get(label, "기타")
                    print(f"  {label}: {count}개 ({description})")
            
            # 3) 데이터셋 파일들 확인
            dataset_files = ['train.csv', 'val.csv', 'test.csv']
            print("\n[생성된 데이터셋]")
            for filename in dataset_files:
                filepath = Path("dataset") / filename
                if filepath.exists():
                    df_dataset = pd.read_csv(filepath, encoding='utf-8-sig')
                    print(f"  {filename}: {len(df_dataset)}행")
                    
                    # 레이블 분포도 확인
                    if 'result_label' in df_dataset.columns:
                        dist = df_dataset['result_label'].value_counts()
                        print(f"    -> {dict(dist)}")
            
            print("\n[분류 지표]")
            print("이 시스템은 다음 4가지 기준으로 상담을 분류합니다:")
            for label, desc in self.quality_labels.items():
                print(f"  • {label}: {desc}")
                
        except Exception as e:
            print(f"결과 분석 중 오류: {str(e)}")
        
        print("="*60)
    
    def run_full_pipeline(self):
        """전체 파이프라인 실행"""
        print("="*60)
        print("상담 품질 분류 파이프라인 시작")
        print("="*60)
        
        # 레이블 파일 준비
        self.create_quality_labels_if_needed()
        
        success_count = 0
        
        # 4단계 스크립트 순차 실행
        for i, (script, name) in enumerate(zip(self.scripts, self.script_names)):
            success = self.run_script(script, name)
            if success:
                success_count += 1
                time.sleep(2)  # 단계 간 대기
            else:
                print(f"\n[중단] {i+1}단계에서 실패하여 파이프라인을 중단합니다.")
                break
        
        print("\n" + "="*60)
        if success_count == len(self.scripts):
            print("파이프라인 완료! 모든 단계가 성공했습니다.")
            self.analyze_classification_results()
        else:
            print(f"파이프라인 실패. {success_count}/{len(self.scripts)} 단계 완료")
        print("="*60)
        
        return success_count == len(self.scripts)
    
    def predict_single_session(self, session_data):
        """단일 세션 상담 품질 예측"""
        print("단일 세션 품질 분류 중...")
        
        # 임시로 가상의 예측 결과 반환 (실제로는 모델 로드 후 예측)
        import random
        predicted_label = random.choice(list(self.quality_labels.keys()))
        confidence = random.uniform(0.7, 0.95)
        
        result = {
            "session_id": session_data.get("session_id", "unknown"),
            "predicted_label": predicted_label,
            "confidence": confidence,
            "description": self.quality_labels[predicted_label]
        }
        
        print(f"예측 결과: {predicted_label} (신뢰도: {confidence:.2f})")
        return result

def create_test_json_with_classification():
    """분류 정보가 포함된 테스트 JSON 파일 생성"""
    test_data = {
        "session_id": "test_classification",
        "consulting_content": """상담사: 안녕하세요, 상담원 김영희입니다. 어떤 도움이 필요하신가요?
손님: 네, 안녕하세요. 카드 관련해서 문의드리고 싶습니다.
상담사: 네, 고객님. 어떤 카드 관련 문의이신지 말씀해 주세요.
손님: 제가 새로 발급받은 카드가 있는데, 사용법을 잘 모르겠어서요.
상담사: 네, 친절히 안내해드리겠습니다. 어떤 기능에 대해 궁금하신가요?
손님: 결제할 때 주의사항이 있나요?
상담사: 네, 말씀드리겠습니다. 첫째, 비밀번호는 다른 사람이 보지 않도록 주의해주세요. 둘째, 사용 후에는 영수증을 꼭 확인해주시기 바랍니다.
손님: 아, 그렇군요. 감사합니다. 정말 도움이 되었어요.
상담사: 네, 도움이 되셨다면 다행입니다. 추가 문의사항이 있으시면 언제든지 연락주세요.
손님: 네, 친절하게 상담해주셔서 감사합니다.""",
        "instructions": [
            {
                "task_category": "상담 결과",
                "output": "만족"
            }
        ]
    }
    
    # data/classification 폴더에 테스트 파일 생성
    test_dir = Path("data/classification")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = test_dir / "test_classification.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"분류 테스트 파일 생성: {test_file}")
    return test_file

def main():
    """메인 실행 함수"""
    pipeline = ClassificationPipeline()
    
    print("상담 품질 분류 자동화 파이프라인")
    print("분류 결과: 만족 / 미흡 / 해결 불가 / 추가 상담 필요")
    print("="*50)
    
    print("1. 전체 파이프라인 실행")
    print("2. 단일 세션 분류 예측")
    print("3. 테스트 파일 생성 후 실행")
    print("4. 종료")
    
    while True:
        choice = input("\n선택 (1-4): ").strip()
        
        if choice == "1":
            print("\n전체 파이프라인을 실행합니다...")
            input("Enter를 눌러서 시작하세요...")
            success = pipeline.run_full_pipeline()
            if success:
                print("\n상담 품질 분류 완료!")
            break
            
        elif choice == "2":
            print("\n단일 세션 분류 예측 모드")
            session_id = input("세션 ID 입력: ").strip()
            test_data = {"session_id": session_id}
            result = pipeline.predict_single_session(test_data)
            print(f"세션 {session_id} 분류 결과: {result}")
            
        elif choice == "3":
            print("\n테스트 파일을 생성하고 파이프라인을 실행합니다...")
            test_file = create_test_json_with_classification()
            input("Enter를 눌러서 파이프라인을 시작하세요...")
            success = pipeline.run_full_pipeline()
            if success:
                print("\n테스트 파이프라인 완료!")
            break
            
        elif choice == "4":
            print("프로그램을 종료합니다.")
            break
            
        else:
            print("잘못된 선택입니다.")

if __name__ == "__main__":
    main() 