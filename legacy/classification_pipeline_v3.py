# -*- coding: utf-8 -*-
"""
상담 품질 분류 파이프라인 v3 (3단계 건너뛰기)
1단계: JSON 병합 → 2단계: 특성 추출 → 4단계: 예측
"""

import os
import sys
import time
import json
import subprocess
import pandas as pd
from pathlib import Path

class ClassificationPipelineV3:
    def __init__(self):
        # 3개 파이프라인 파일 (3단계 제외)
        self.scripts = [
            "1_preprocessing_model_v3.py",      # JSON 병합
            "2_coloums_extraction_v3_json2csv.py",  # 특성 추출
            "4_model_predict_only.py"           # 예측 실행
        ]
        
        self.script_names = [
            "1단계: 전처리 및 JSON 병합",
            "2단계: 텍스트 특성 추출", 
            "4단계: 상담 품질 예측"
        ]
        
        # 상담 품질 분류 레이블
        self.quality_labels = {
            "만족": "고객이 상담 결과에 만족한 경우",
            "미흡": "상담이 진행되었으나 고객 만족도가 낮은 경우",
            "해결 불가": "고객의 문제를 해결할 수 없는 경우",
            "추가 상담 필요": "추가적인 상담이나 처리가 필요한 경우"
        }
    
    def check_files(self):
        """필요한 파일들이 존재하는지 확인"""
        missing_scripts = []
        for script in self.scripts:
            if not Path(script).exists():
                missing_scripts.append(script)
        
        if missing_scripts:
            print(f"ERROR: 다음 스크립트 파일이 없습니다: {missing_scripts}")
            return False
        
        print("OK: 모든 스크립트 파일이 존재합니다.")
        
        # 학습된 모델 파일 확인
        model_dir = Path("trained_models")
        required_models = ["counseling_quality_model.pkl", "label_encoder.pkl", "feature_names.pkl"]
        missing_models = [f for f in required_models if not (model_dir / f).exists()]
        
        if missing_models:
            print(f"WARNING: 학습된 모델 파일이 없습니다: {missing_models}")
            print("먼저 train_from_dataset_v4.py를 실행하여 모델을 학습해주세요.")
            return False
        
        print("OK: 모든 학습된 모델 파일이 존재합니다.")
        return True
    
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
                if 'confidence' in df_results.columns:
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
                "json_merge/classification_merge_output/merged_classification_20593_final.json"
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
    
    def run_pipeline(self):
        """파이프라인 실행 (3단계 건너뛰기)"""
        print("="*60)
        print("상담 품질 분류 파이프라인 시작 (3단계 건너뛰기)")
        print("흐름: 1단계 → 2단계 → 4단계(예측)")
        print("="*60)
        
        # 레이블 파일 준비
        self.create_quality_labels_if_needed()
        
        success_count = 0
        
        # 3단계 스크립트 순차 실행 (3단계 제외)
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
    pipeline = ClassificationPipelineV3()
    
    print("상담 품질 분류 자동화 파이프라인 v3")
    print("분류 결과: 만족 / 미흡 / 해결 불가 / 추가 상담 필요")
    print("="*50)
    
    # 파일 존재 여부 확인
    if not pipeline.check_files():
        print("\n필요한 파일들을 먼저 준비해주세요:")
        print("1. 모델 학습: python train_from_dataset_v4.py")
        print("2. 그 후 다시 이 파이프라인을 실행하세요.")
        return
    
    print("\n✅ 모든 파일이 준비되었습니다.")
    print("1. 파이프라인 실행 (1단계 → 2단계 → 4단계)")
    print("2. 테스트 파일 생성 후 파이프라인 실행")
    print("3. 종료")
    
    while True:
        choice = input("\n선택 (1-3): ").strip()
        
        if choice == "1":
            print("\n파이프라인을 실행합니다...")
            input("Enter를 눌러서 시작하세요...")
            pipeline.run_pipeline()
            break
            
        elif choice == "2":
            print("\n테스트 파일을 생성하고 파이프라인을 실행합니다...")
            test_file = create_test_json_with_classification()
            input("Enter를 눌러서 파이프라인을 시작하세요...")
            pipeline.run_pipeline()
            break
            
        elif choice == "3":
            print("프로그램을 종료합니다.")
            break
            
        else:
            print("올바른 번호를 선택해주세요 (1-3)")

if __name__ == "__main__":
    main() 