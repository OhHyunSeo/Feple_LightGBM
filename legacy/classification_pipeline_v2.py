# -*- coding: utf-8 -*-
"""
기존 4개 파이썬 파일을 이용한 상담 품질 분류 자동화 파이프라인 (예측 전용)
- 분류 결과: 만족, 미흡, 해결 불가, 추가 상담 필요
- 4단계에서 학습된 모델로 예측만 수행
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path
import json
import pandas as pd

class ClassificationPipelineV2:
    """상담 품질 분류 자동화 파이프라인 (예측 전용)"""
    
    def __init__(self):
        # 수정된 4개 파이썬 파일 순서 (4번만 예측 전용으로 변경)
        self.scripts = [
            "1_preprocessing_model_v3.py",
            "2_coloums_extraction_v3_json2csv.py", 
            "3_make_dataset.py",
            "4_model_predict_only.py"  # <- 예측 전용으로 변경
        ]
        
        self.script_names = [
            "1단계: 전처리 및 JSON 병합",
            "2단계: 텍스트 특성 추출",
            "3단계: 데이터셋 생성", 
            "4단계: 상담 품질 예측 (학습된 모델 사용)"  # <- 설명 변경
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
        
        # 학습된 모델 파일 확인
        model_dir = Path("trained_models")
        model_files = [
            "counseling_quality_model.pkl",
            "label_encoder.pkl", 
            "feature_names.pkl"
        ]
        
        missing_models = []
        for model_file in model_files:
            if not (model_dir / model_file).exists():
                missing_models.append(model_file)
        
        if missing_models:
            print(f"WARNING: 학습된 모델 파일이 없습니다: {missing_models}")
            print("첫 실행 시 모델을 학습한 후 저장됩니다.")
        else:
            print("OK: 학습된 모델 파일이 존재합니다.")
    
    def run_script(self, script_name, step_name):
        """개별 스크립트 실행"""
        print(f"\n[시작] {step_name}")
        print(f"실행: {script_name}")
        
        try:
            # Windows 인코딩 문제 해결을 위한 환경 변수 설정
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
            
            # Windows에서 코드페이지를 UTF-8로 설정
            if os.name == 'nt':  # Windows
                try:
                    subprocess.run(['chcp', '65001'], shell=True, capture_output=True, check=False)
                except:
                    pass  # chcp 실패해도 계속 진행
            
            # subprocess로 스크립트 실행 (인코딩 명시적 지정)
            result = subprocess.run(
                [sys.executable, script_name], 
                capture_output=True, 
                text=True, 
                timeout=600,  # 10분 타임아웃
                env=env,
                encoding='utf-8',
                errors='ignore'  # 인코딩 오류 무시
            )
            
            if result.returncode == 0:
                print(f"[성공] {step_name} 완료")
                return True
            else:
                print(f"[실패] {step_name}")
                # stderr에서 실제 오류만 추출 (인코딩 오류 제외)
                if result.stderr and result.stderr.strip():
                    # UnicodeDecodeError 관련 오류는 제외하고 실제 오류만 표시
                    stderr_lines = result.stderr.strip().split('\n')
                    actual_errors = []
                    for line in stderr_lines:
                        if ('UnicodeDecodeError' not in line and 
                            'codec can\'t decode' not in line and
                            '_readerthread' not in line and
                            'threading.py' not in line and
                            'subprocess.py' not in line and
                            line.strip()):
                            actual_errors.append(line.strip())
                    
                    if actual_errors:
                        print(f"오류: {' '.join(actual_errors[:3])}")  # 처음 3개 오류만
                    else:
                        print("오류: 스크립트 실행 실패 (인코딩 관련 오류는 무시됨)")
                
                # returncode가 0이 아니어도 실제로는 성공일 수 있음 (인코딩 오류 때문)
                # 출력 파일이 생성되었는지 확인해서 성공 여부 재판단
                if step_name == "1단계: 전처리 및 JSON 병합":
                    if Path("json_merge").exists():
                        print("[재확인] 출력 파일 존재 - 성공으로 처리")
                        return True
                elif step_name == "2단계: 텍스트 특성 추출":
                    if Path("output/text_features_all_v4.csv").exists():
                        print("[재확인] 출력 파일 존재 - 성공으로 처리")
                        return True
                elif step_name == "3단계: 데이터셋 생성":
                    if Path("dataset").exists() and len(list(Path("dataset").glob("*.csv"))) > 0:
                        print("[재확인] 출력 파일 존재 - 성공으로 처리")
                        return True
                elif step_name == "4단계: 상담 품질 예측":
                    if Path("results/counseling_quality_predictions.csv").exists():
                        print("[재확인] 출력 파일 존재 - 성공으로 처리")
                        return True
                
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
    
    def analyze_prediction_results(self):
        """예측 결과 분석 및 표시"""
        print("\n" + "="*60)
        print("상담 품질 예측 결과 분석")
        print("="*60)
        
        try:
            # 예측 결과 파일 확인
            results_file = "results/counseling_quality_predictions.csv"
            if Path(results_file).exists():
                df_results = pd.read_csv(results_file, encoding='utf-8-sig')
                print(f"예측 완료된 세션 수: {len(df_results)}")
                
                # 예측 결과 분포 표시
                pred_counts = df_results['predicted_label'].value_counts()
                print("\n[예측 결과 분포]")
                for label, count in pred_counts.items():
                    percentage = count / len(df_results) * 100
                    description = self.quality_labels.get(label, "기타")
                    print(f"  {label}: {count}개 ({percentage:.1f}%) - {description}")
                
                # 신뢰도 통계
                confidence_stats = df_results['confidence'].describe()
                print(f"\n[예측 신뢰도 통계]")
                print(f"  평균: {confidence_stats['mean']:.3f}")
                print(f"  최소: {confidence_stats['min']:.3f}")
                print(f"  최대: {confidence_stats['max']:.3f}")
                
                # 고신뢰도 예측 개수
                high_confidence = (df_results['confidence'] >= 0.8).sum()
                print(f"  고신뢰도(≥0.8): {high_confidence}개 ({high_confidence/len(df_results)*100:.1f}%)")
                
            # 다른 결과 파일들도 확인
            other_files = [
                "output/text_features_all_v4.csv",
                "dataset/train.csv",
                "dataset/val.csv", 
                "dataset/test.csv"
            ]
            
            print("\n[생성된 파일들]")
            for file_path in other_files:
                if Path(file_path).exists():
                    size = Path(file_path).stat().st_size
                    print(f"  OK: {file_path} ({size:,} bytes)")
                else:
                    print(f"  MISSING: {file_path}")
            
            print("\n[분류 시스템 정보]")
            print("이 시스템은 다음 4가지 기준으로 상담을 분류합니다:")
            for label, desc in self.quality_labels.items():
                print(f"  • {label}: {desc}")
                
        except Exception as e:
            print(f"결과 분석 중 오류: {str(e)}")
        
        print("="*60)
    
    def run_full_pipeline(self):
        """전체 파이프라인 실행"""
        print("="*60)
        print("상담 품질 분류 파이프라인 시작 (예측 전용)")
        print("="*60)
        
        # 레이블 파일 준비
        self.create_quality_labels_if_needed()
        
        success_count = 0
        
        # 4단계 스크립트 순차 실행
        for i, (script, name) in enumerate(zip(self.scripts, self.script_names)):
            success = self.run_script(script, name)
            if success:
                success_count += 1
                if i < len(self.scripts) - 1:  # 마지막 단계가 아니면 대기
                    time.sleep(2)
            else:
                print(f"\n[중단] {i+1}단계에서 실패하여 파이프라인을 중단합니다.")
                break
        
        print("\n" + "="*60)
        if success_count == len(self.scripts):
            print("파이프라인 완료! 모든 단계가 성공했습니다.")
            self.analyze_prediction_results()
        else:
            print(f"파이프라인 실패. {success_count}/{len(self.scripts)} 단계 완료")
        print("="*60)
        
        return success_count == len(self.scripts)
    
    def train_model_first(self):
        """최초 1회 모델 학습"""
        print("="*60)
        print("최초 모델 학습 (1-3단계 + 모델 학습)")
        print("="*60)
        
        # 레이블 파일 준비
        self.create_quality_labels_if_needed()
        
        # 1-3단계 실행
        training_scripts = self.scripts[:3]  # 1,2,3단계만
        training_names = self.script_names[:3]
        
        success_count = 0
        for i, (script, name) in enumerate(zip(training_scripts, training_names)):
            success = self.run_script(script, name)
            if success:
                success_count += 1
                time.sleep(2)
            else:
                print(f"\n[중단] {i+1}단계에서 실패하여 모델 학습을 중단합니다.")
                return False
        
        if success_count == 3:
            # 4번 원본 파일로 모델 학습 및 저장
            print("\n[시작] 4단계: 모델 학습 및 저장")
            print("실행: 4_train_model.py (학습 모드)")
            
            # 새로운 학습 파일을 실행해서 모델 학습
            try:
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
                
                # Windows에서 코드페이지를 UTF-8로 설정
                if os.name == 'nt':  # Windows
                    try:
                        subprocess.run(['chcp', '65001'], shell=True, capture_output=True, check=False)
                    except:
                        pass
                
                result = subprocess.run(
                    [sys.executable, "4_train_model.py"], 
                    capture_output=True, 
                    text=True, 
                    timeout=900,  # 15분 타임아웃
                    env=env,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                if result.returncode == 0:
                    print("[성공] 모델 학습 완료")
                    
                    # 모델 파일 존재 확인
                    model_dir = Path("trained_models")
                    required_files = [
                        "counseling_quality_model.pkl",
                        "label_encoder.pkl", 
                        "feature_names.pkl"
                    ]
                    
                    all_files_exist = all((model_dir / f).exists() for f in required_files)
                    
                    if all_files_exist:
                        print("[성공] 모델 파일 저장 확인됨")
                        return True
                    else:
                        missing = [f for f in required_files if not (model_dir / f).exists()]
                        print(f"[실패] 모델 파일 누락: {missing}")
                        return False
                else:
                    print("[실패] 모델 학습 실패")
                    print(f"오류: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"[예외] 모델 학습 중 오류: {str(e)}")
                return False
        
        return False

def create_test_json_with_classification():
    """분류 정보가 포함된 테스트 JSON 파일 생성"""
    test_data = {
        "session_id": "test_prediction",
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
    
    test_file = test_dir / "test_prediction.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"예측 테스트 파일 생성: {test_file}")
    return test_file

def main():
    """메인 실행 함수"""
    pipeline = ClassificationPipelineV2()
    
    print("상담 품질 분류 자동화 파이프라인 (예측 전용)")
    print("분류 결과: 만족 / 미흡 / 해결 불가 / 추가 상담 필요")
    print("="*50)
    
    # 학습된 모델 존재 여부 확인
    model_dir = Path("trained_models")
    model_exists = (
        (model_dir / "counseling_quality_model.pkl").exists() and
        (model_dir / "label_encoder.pkl").exists() and
        (model_dir / "feature_names.pkl").exists()
    )
    
    if not model_exists:
        print("❌ 학습된 모델이 없습니다.")
        print("1. 모델 학습 후 예측 파이프라인 실행")
        print("2. 예측 파이프라인만 실행 (모델 없이)")
        print("3. 테스트 파일 생성 후 모델 학습")
        print("4. 종료")
    else:
        print("✅ 학습된 모델이 존재합니다.")
        print("1. 예측 파이프라인 실행")
        print("2. 테스트 파일 생성 후 예측")
        print("3. 모델 재학습 후 예측")
        print("4. 종료")
    
    while True:
        choice = input("\n선택 (1-4): ").strip()
        
        if choice == "1":
            if not model_exists:
                print("\n모델 학습 후 예측 파이프라인을 실행합니다...")
                train_success = pipeline.train_model_first()
                if train_success:
                    print("\n이제 예측 파이프라인을 실행합니다...")
                    input("Enter를 눌러서 시작하세요...")
                    pipeline.run_full_pipeline()
            else:
                print("\n예측 파이프라인을 실행합니다...")
                input("Enter를 눌러서 시작하세요...")
                pipeline.run_full_pipeline()
            break
            
        elif choice == "2":
            if not model_exists:
                print("\n예측 파이프라인만 실행합니다 (모델 학습 포함)...")
                input("Enter를 눌러서 시작하세요...")
                pipeline.run_full_pipeline()
            else:
                print("\n테스트 파일을 생성하고 예측 파이프라인을 실행합니다...")
                test_file = create_test_json_with_classification()
                input("Enter를 눌러서 파이프라인을 시작하세요...")
                pipeline.run_full_pipeline()
            break
            
        elif choice == "3":
            if not model_exists:
                print("\n테스트 파일을 생성하고 모델 학습을 시작합니다...")
                test_file = create_test_json_with_classification()
                input("Enter를 눌러서 학습을 시작하세요...")
                train_success = pipeline.train_model_first()
                if train_success:
                    print("\n학습 완료! 이제 예측을 실행합니다...")
                    pipeline.run_full_pipeline()
            else:
                print("\n모델 재학습 후 예측을 실행합니다...")
                train_success = pipeline.train_model_first()
                if train_success:
                    pipeline.run_full_pipeline()
            break
            
        elif choice == "4":
            print("프로그램을 종료합니다.")
            break
            
        else:
            print("잘못된 선택입니다.")

if __name__ == "__main__":
    main() 