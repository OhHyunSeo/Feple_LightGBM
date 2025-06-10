# -*- coding: utf-8 -*-
"""
기존 4개 파이썬 파일을 이용한 자동화 파이프라인
- data 폴더에 JSON 파일이 들어오면 자동으로 4단계 처리
- 1단계: 1_preprocessing_model_v3.py (전처리)
- 2단계: 2_coloums_extraction_v3_json2csv.py (특성 추출)
- 3단계: 3_make_dataset.py (데이터셋 생성)
- 4단계: 4_simple_model_v2.py (모델 평가)
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataFileHandler(FileSystemEventHandler):
    """data 폴더의 JSON 파일 변경을 감지하는 핸들러"""
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
        
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            logger.info(f"🔍 새 JSON 파일 감지: {event.src_path}")
            # 파일이 완전히 복사될 때까지 잠시 대기
            time.sleep(2)
            self.pipeline.process_new_file(event.src_path)

class PipelineAutomation:
    """기존 4개 파이썬 파일을 이용한 자동화 파이프라인"""
    
    def __init__(self, data_dir="data", output_dir="pipeline_results"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 기존 4개 파이썬 파일
        self.scripts = [
            "1_preprocessing_model_v3.py",
            "2_coloums_extraction_v3_json2csv.py", 
            "3_make_dataset.py",
            "4_simple_model_v2.py"
        ]
        
        # 처리 단계별 설명
        self.script_descriptions = {
            "1_preprocessing_model_v3.py": "📝 1단계: 전처리",
            "2_coloums_extraction_v3_json2csv.py": "🔧 2단계: 텍스트 특성 추출",
            "3_make_dataset.py": "📊 3단계: 데이터셋 생성", 
            "4_simple_model_v2.py": "🤖 4단계: 모델 평가"
        }
        
        # 각 단계별 결과 파일 확인
        self.check_scripts_exist()
    
    def check_scripts_exist(self):
        """필요한 스크립트 파일들이 존재하는지 확인"""
        missing_scripts = []
        for script in self.scripts:
            if not Path(script).exists():
                missing_scripts.append(script)
        
        if missing_scripts:
            logger.error(f"❌ 다음 스크립트 파일들이 없습니다: {missing_scripts}")
            sys.exit(1)
        else:
            logger.info("✅ 모든 필요한 스크립트 파일이 존재합니다.")
    
    def prepare_input_data(self, json_file_path):
        """입력 데이터를 적절한 위치로 복사 및 준비"""
        logger.info(f"📁 입력 데이터 준비: {json_file_path}")
        
        # json_merge/integration_data 디렉토리 생성
        integration_dir = Path("json_merge/integration_data")
        integration_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON 파일을 적절한 위치로 복사
        source_file = Path(json_file_path)
        target_file = integration_dir / source_file.name
        
        shutil.copy2(source_file, target_file)
        logger.info(f"✅ 파일 복사 완료: {target_file}")
        
        return target_file
    
    def run_script(self, script_name, step_num):
        """개별 스크립트 실행"""
        logger.info(f"\n{self.script_descriptions[script_name]} 시작...")
        
        try:
            # 스크립트 실행
            result = subprocess.run([sys.executable, script_name], 
                                    capture_output=True, 
                                    text=True, 
                                    timeout=300)  # 5분 타임아웃
            
            if result.returncode == 0:
                logger.info(f"✅ {step_num}단계 완료: {script_name}")
                if result.stdout:
                    logger.info(f"출력: {result.stdout[-200:]}")  # 마지막 200자만 출력
                return True
            else:
                logger.error(f"❌ {step_num}단계 실패: {script_name}")
                logger.error(f"오류: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ {step_num}단계 타임아웃: {script_name}")
            return False
        except Exception as e:
            logger.error(f"💥 {step_num}단계 예외 발생: {script_name} - {str(e)}")
            return False
    
    def extract_results(self):
        """최종 결과 추출 및 정리"""
        logger.info("📋 최종 결과 추출 중...")
        
        results_summary = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'completed',
            'output_files': []
        }
        
        # 주요 결과 파일들 확인
        result_files = [
            "output/text_features_all_v4.csv",
            "dataset/train.csv",
            "dataset/val.csv", 
            "dataset/test.csv"
        ]
        
        for file_path in result_files:
            if Path(file_path).exists():
                results_summary['output_files'].append(file_path)
                logger.info(f"✅ 결과 파일 생성됨: {file_path}")
        
        # 최종 평가 결과 표시
        self.display_final_results()
        
        return results_summary
    
    def display_final_results(self):
        """최종 평가 결과를 콘솔에 표시"""
        print("\n" + "="*60)
        print("🎉 상담 품질 평가 파이프라인 완료!")
        print("="*60)
        
        # CSV 파일에서 최신 결과 읽기 (4_simple_model_v2.py 결과)
        try:
            import pandas as pd
            
            # 텍스트 특성 파일 확인
            feature_file = "output/text_features_all_v4.csv"
            if Path(feature_file).exists():
                df = pd.read_csv(feature_file, encoding='utf-8-sig')
                print(f"📊 처리된 세션 수: {len(df)}")
                print(f"📁 특성 추출 결과: {feature_file}")
            
            # 데이터셋 파일들 확인
            for dataset_type in ['train', 'val', 'test']:
                dataset_file = f"dataset/{dataset_type}.csv"
                if Path(dataset_file).exists():
                    df_dataset = pd.read_csv(dataset_file, encoding='utf-8-sig')
                    print(f"📈 {dataset_type.upper()} 데이터셋: {len(df_dataset)}행")
            
            print("-"*60)
            print("🤖 4개 지표 평가 모델 준비 완료!")
            print("   - 적극성 (Proactivity)")
            print("   - 친화성 (Friendliness)")  
            print("   - 전문성 (Expertise)")
            print("   - 문제해결력 (Problem Solving)")
            
        except Exception as e:
            logger.warning(f"결과 표시 중 오류: {str(e)}")
        
        print("="*60)
    
    def process_new_file(self, file_path):
        """새로운 JSON 파일 처리"""
        logger.info(f"🚀 파이프라인 시작: {file_path}")
        
        try:
            # 1. 입력 데이터 준비
            prepared_file = self.prepare_input_data(file_path)
            
            # 2. 4단계 스크립트 순차 실행
            all_success = True
            for i, script in enumerate(self.scripts, 1):
                success = self.run_script(script, i)
                if not success:
                    logger.error(f"❌ {i}단계에서 실패. 파이프라인 중단.")
                    all_success = False
                    break
                
                # 각 단계 사이에 잠시 대기
                time.sleep(1)
            
            # 3. 결과 처리
            if all_success:
                results = self.extract_results()
                logger.info("🎉 전체 파이프라인 성공적으로 완료!")
                return results
            else:
                logger.error("❌ 파이프라인 실행 실패")
                return None
                
        except Exception as e:
            logger.error(f"💥 파이프라인 실행 중 오류: {str(e)}")
            return None
    
    def process_batch(self, folder_path):
        """폴더 내 모든 JSON 파일 일괄 처리"""
        json_files = list(Path(folder_path).glob("*.json"))
        
        if not json_files:
            logger.warning(f"📁 {folder_path}에 JSON 파일이 없습니다.")
            return
        
        logger.info(f"📦 일괄 처리 시작: {len(json_files)}개 파일")
        
        successful = 0
        failed = 0
        
        for json_file in json_files:
            logger.info(f"\n{'='*40}")
            logger.info(f"처리 중: {json_file.name}")
            logger.info(f"{'='*40}")
            
            result = self.process_new_file(str(json_file))
            if result:
                successful += 1
            else:
                failed += 1
        
        logger.info(f"\n📊 일괄 처리 완료!")
        logger.info(f"   성공: {successful}개")
        logger.info(f"   실패: {failed}개")
    
    def start_monitoring(self):
        """실시간 모니터링 시작"""
        event_handler = DataFileHandler(self)
        observer = Observer()
        
        # data 폴더의 모든 하위 폴더 모니터링
        folders_to_monitor = ['classification', 'qa', 'summary']
        
        for folder_name in folders_to_monitor:
            folder_path = self.data_dir / folder_name
            folder_path.mkdir(exist_ok=True)
            observer.schedule(event_handler, str(folder_path), recursive=True)
            logger.info(f"👁️ 모니터링 시작: {folder_path}")
        
        observer.start()
        logger.info("🔍 실시간 모니터링 활성화!")
        logger.info("📁 data 폴더에 JSON 파일을 넣으면 자동으로 처리됩니다.")
        logger.info("⏹️ 종료하려면 Ctrl+C를 누르세요.")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("✋ 모니터링 중단")
        
        observer.join()

def main():
    """메인 실행 함수"""
    pipeline = PipelineAutomation()
    
    if len(sys.argv) > 1:
        # 배치 모드: 특정 폴더 처리
        folder_path = sys.argv[1]
        pipeline.process_batch(folder_path)
    else:
        # 대화형 모드
        print("🤖 상담 품질 평가 자동화 파이프라인")
        print("="*50)
        print("1. 실시간 모니터링 시작")
        print("2. 폴더 일괄 처리")
        print("3. 단일 파일 처리")
        print("4. 종료")
        
        while True:
            choice = input("\n선택 (1-4): ").strip()
            
            if choice == "1":
                pipeline.start_monitoring()
                break
            elif choice == "2":
                folder_path = input("처리할 폴더 경로: ").strip()
                pipeline.process_batch(folder_path)
            elif choice == "3":
                file_path = input("처리할 JSON 파일 경로: ").strip()
                pipeline.process_new_file(file_path)
            elif choice == "4":
                print("👋 프로그램을 종료합니다.")
                break
            else:
                print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main() 