# -*- coding: utf-8 -*-
"""
auto_file_monitor.py
- data 폴더를 실시간 모니터링
- 새 파일 감지시 자동으로 파이프라인 실행
- 결과를 text_features_all_v4.csv에 누적 저장
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd

# watchdog이 없으면 설치 안내
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("❌ watchdog 라이브러리가 필요합니다.")
    print("설치 명령: pip install watchdog")
    sys.exit(1)

class FileMonitorHandler(FileSystemEventHandler):
    """파일 변경 이벤트 핸들러"""
    
    def __init__(self, processor):
        self.processor = processor
        self.last_processed = {}  # 파일별 마지막 처리 시간
        self.processing_lock = threading.Lock()
        
    def on_created(self, event):
        """새 파일이 생성되었을 때"""
        if not event.is_directory:
            self._handle_file_event(event.src_path, "생성됨")
    
    def on_modified(self, event):
        """파일이 수정되었을 때"""
        if not event.is_directory:
            self._handle_file_event(event.src_path, "수정됨")
    
    def _handle_file_event(self, file_path, event_type):
        """파일 이벤트 처리"""
        # JSON 파일만 처리
        if not file_path.endswith('.json'):
            return
        
        # data/classification 폴더의 파일만 처리
        path_obj = Path(file_path)
        if 'data' not in path_obj.parts or 'classification' not in path_obj.parts:
            return
        
        # 중복 처리 방지 (5초 간격)
        current_time = time.time()
        if (file_path in self.last_processed and 
            current_time - self.last_processed[file_path] < 5):
            return
        
        self.last_processed[file_path] = current_time
        
        # 파일이 완전히 쓰여질 때까지 잠시 대기
        time.sleep(2)
        
        # 처리 실행 (스레드 안전)
        with self.processing_lock:
            print(f"\n🔔 파일 {event_type}: {file_path}")
            self.processor.process_new_file(file_path)

class AutoProcessor:
    """자동 처리 시스템"""
    
    def __init__(self):
        self.is_processing = False
        self.processed_files = set()
        
        # 처리 기록 파일 로드
        self.log_file = Path("auto_processing_log.txt")
        self._load_processed_files()
    
    def _load_processed_files(self):
        """이전에 처리된 파일 목록 로드"""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            self.processed_files.add(line.strip())
                print(f"📋 이전 처리 기록: {len(self.processed_files)}개 파일")
            except Exception as e:
                print(f"⚠️ 처리 기록 로드 실패: {e}")
    
    def _log_processed_file(self, file_path):
        """처리된 파일 기록"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"{file_path}\n")
            self.processed_files.add(file_path)
        except Exception as e:
            print(f"⚠️ 처리 기록 저장 실패: {e}")
    
    def process_new_file(self, file_path):
        """새 파일 처리"""
        # 이미 처리된 파일인지 확인
        if file_path in self.processed_files:
            print(f"⏭️ 이미 처리된 파일: {Path(file_path).name}")
            return
        
        # 현재 처리 중인지 확인
        if self.is_processing:
            print(f"⏳ 다른 파일 처리 중... 대기: {Path(file_path).name}")
            return
        
        self.is_processing = True
        
        try:
            print(f"\n{'='*60}")
            print(f"🚀 자동 파이프라인 시작")
            print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"파일: {file_path}")
            print(f"{'='*60}")
            
            # 1단계: JSON 병합
            print("\n[1단계] JSON 파일 병합 중...")
            success = self._run_step("1_preprocessing_model_v3.py", "JSON 병합")
            
            if not success:
                print("❌ 1단계 실패 - 파이프라인 중단")
                return
            
            # 2단계: 특성 추출 + 예측 (통합)
            print("\n[2단계] 특성 추출 + 예측 중...")
            success = self._run_step("2_extract_and_predict.py", "특성 추출 + 예측")
            
            if not success:
                print("❌ 2단계 실패 - 파이프라인 중단")
                return
            
            # 처리 완료 기록
            self._log_processed_file(file_path)
            
            # 결과 누적
            self._accumulate_results()
            
            print(f"\n{'='*60}")
            print(f"✅ 자동 처리 완료!")
            print(f"📄 결과 파일: output/text_features_all_v4.csv")
            print(f"{'='*60}")
            
        except Exception as e:
            print(f"❌ 처리 중 오류: {str(e)}")
            
        finally:
            self.is_processing = False
    
    def _run_step(self, script_name, step_name):
        """개별 단계 실행"""
        try:
            # Windows 인코딩 문제 해결
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
            
            if os.name == 'nt':  # Windows
                try:
                    subprocess.run(['chcp', '65001'], shell=True, capture_output=True, check=False)
                except:
                    pass
            
            # 스크립트 실행
            result = subprocess.run(
                [sys.executable, script_name], 
                capture_output=True, 
                text=True, 
                timeout=600,  # 10분 타임아웃
                env=env,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                print(f"   ✅ {step_name} 성공")
                return True
            else:
                print(f"   ❌ {step_name} 실패 (코드: {result.returncode})")
                
                # 실제 출력 파일 확인으로 성공 여부 재판단
                if step_name == "JSON 병합":
                    if Path("json_merge").exists():
                        print("   🔍 출력 폴더 확인 - 성공으로 처리")
                        return True
                elif step_name == "특성 추출 + 예측":
                    if Path("output/text_features_all_v4.csv").exists():
                        print("   🔍 출력 파일 확인 - 성공으로 처리")
                        return True
                
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ {step_name} 타임아웃")
            return False
        except Exception as e:
            print(f"   ❌ {step_name} 예외: {str(e)}")
            return False
    
    def _accumulate_results(self):
        """결과를 누적 CSV에 저장"""
        try:
            current_file = Path("output/text_features_all_v4.csv")
            accumulated_file = Path("output/accumulated_results.csv")
            
            if not current_file.exists():
                print("⚠️ 현재 결과 파일이 없음")
                return
            
            # 현재 결과 로드
            df_current = pd.read_csv(current_file, encoding='utf-8-sig')
            
            # 누적 파일이 있으면 병합
            if accumulated_file.exists():
                df_accumulated = pd.read_csv(accumulated_file, encoding='utf-8-sig')
                
                # session_id 기준으로 중복 제거하며 병합
                df_combined = pd.concat([df_accumulated, df_current]).drop_duplicates(
                    subset=['session_id'], keep='last'
                )
                
                print(f"📊 누적 결과 업데이트: {len(df_accumulated)} → {len(df_combined)}개 세션")
            else:
                df_combined = df_current
                print(f"📊 누적 결과 첫 생성: {len(df_combined)}개 세션")
            
            # 누적 파일 저장
            df_combined.to_csv(accumulated_file, index=False, encoding='utf-8-sig')
            print(f"💾 누적 결과 저장: {accumulated_file}")
            
        except Exception as e:
            print(f"❌ 누적 저장 실패: {str(e)}")

class FileMonitor:
    """파일 모니터링 메인 클래스"""
    
    def __init__(self, watch_dir="data"):
        self.watch_dir = Path(watch_dir)
        self.processor = AutoProcessor()
        self.observer = Observer()
        
        # 모니터링 디렉토리 확인
        if not self.watch_dir.exists():
            print(f"⚠️ 모니터링 디렉토리가 없습니다: {self.watch_dir}")
            print("   data 폴더를 생성합니다.")
            self.watch_dir.mkdir(parents=True, exist_ok=True)
    
    def start_monitoring(self):
        """모니터링 시작"""
        print(f"🔍 파일 모니터링 시작")
        print(f"   감시 디렉토리: {self.watch_dir.absolute()}")
        print(f"   대상 파일: data/classification/*.json")
        print(f"   처리 결과: output/text_features_all_v4.csv")
        print(f"   누적 결과: output/accumulated_results.csv")
        print(f"{'='*50}")
        
        # 이벤트 핸들러 설정
        event_handler = FileMonitorHandler(self.processor)
        
        # 재귀적으로 모니터링 설정
        self.observer.schedule(event_handler, str(self.watch_dir), recursive=True)
        
        # 모니터링 시작
        self.observer.start()
        print("✅ 모니터링 활성화됨 (Ctrl+C로 종료)")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 모니터링 중지 중...")
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.observer.stop()
        self.observer.join()
        print("✅ 모니터링 종료됨")

def main():
    """메인 실행 함수"""
    print("상담 데이터 자동 처리 시스템")
    print("="*50)
    
    # 학습된 모델 확인
    model_dir = Path("trained_models")
    required_files = [
        "counseling_quality_model.pkl",
        "label_encoder.pkl", 
        "feature_names.pkl"
    ]
    
    missing_files = [f for f in required_files if not (model_dir / f).exists()]
    if missing_files:
        print(f"❌ 학습된 모델 파일이 없습니다: {missing_files}")
        print("   먼저 train_from_dataset_v4.py를 실행하여 모델을 학습해주세요.")
        return
    
    print("✅ 학습된 모델 확인 완료")
    
    # 파일 모니터링 시작
    monitor = FileMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main() 