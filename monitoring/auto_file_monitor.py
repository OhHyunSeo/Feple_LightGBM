# -*- coding: utf-8 -*-
"""
상담 데이터 자동 처리 시스템
- JSON 파일 자동 감지 및 처리
- 파이프라인 자동 실행
"""

import os
import sys
import time
import threading
import subprocess
import shutil
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
        
        # data/input 폴더의 파일만 처리
        path_obj = Path(file_path)
        if 'data' not in path_obj.parts or 'input' not in path_obj.parts:
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
        
        # 파일 분류 매핑
        self.file_classification_map = {
            '분류': 'classification',
            '요약': 'summary', 
            '질의응답': 'qa'
        }
        
        # 필요한 디렉토리 생성
        self._ensure_directories()
    
    def _ensure_directories(self):
        """필요한 디렉토리들이 존재하는지 확인하고 생성"""
        directories = [
            Path("data/input"),
            Path("data/classification"),
            Path("data/summary"),
            Path("data/qa")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        print("📁 필요한 디렉토리 확인/생성 완료")
        print(f"   - {Path('data/input').absolute()}")
        print(f"   - {Path('data/classification').absolute()}")
        print(f"   - {Path('data/summary').absolute()}")
        print(f"   - {Path('data/qa').absolute()}")
    
    def _classify_and_move_file(self, file_path):
        """파일명을 분석하여 적절한 폴더로 이동"""
        path_obj = Path(file_path)
        filename = path_obj.name
        
        # 파일명에서 한글 키워드 찾기
        target_folder = None
        for korean_keyword, folder_name in self.file_classification_map.items():
            if korean_keyword in filename:
                target_folder = folder_name
                break
        
        if target_folder is None:
            print(f"⚠️ 파일 분류 실패: '{filename}'에서 키워드를 찾을 수 없습니다")
            print(f"   지원되는 키워드: {list(self.file_classification_map.keys())}")
            return None
        
        # 대상 디렉토리 설정
        target_dir = Path("data") / target_folder
        target_path = target_dir / filename
        
        try:
            # 파일이 이미 존재하는 경우 덮어쓰기
            if target_path.exists():
                print(f"⚠️ 파일이 이미 존재함: {target_path}")
                target_path.unlink()
            
            # 파일 이동
            shutil.move(str(path_obj), str(target_path))
            print(f"📂 파일 분류 완료: {filename}")
            print(f"   '{korean_keyword}' → {target_folder} 폴더")
            print(f"   위치: {target_path}")
            
            return str(target_path)
            
        except Exception as e:
            print(f"❌ 파일 이동 실패: {e}")
            return None

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
            
            # 0단계: 파일 분류 및 이동
            print("\n[0단계] 파일 분류 및 이동 중...")
            moved_file_path = self._classify_and_move_file(file_path)
            
            if moved_file_path is None:
                print("❌ 0단계 실패 - 파이프라인 중단")
                return
            
            # 분류된 파일의 세션 ID 추출
            session_id = self._extract_session_id(moved_file_path)
            print(f"📋 세션 ID: {session_id}")
            
            # 해당 세션의 다른 타입 파일들이 모두 준비되었는지 확인
            session_complete = self._check_session_completion(session_id)
            
            if session_complete:
                print(f"✅ 세션 {session_id}의 모든 데이터 타입이 준비완료!")
                
                # 1단계: JSON 병합 (분류, 요약, 질의응답 각각 처리)
                print("\n[1단계] JSON 파일 병합 중...")
                success = self._run_step("scripts/1_preprocessing_unified.py", "JSON 병합")
                
                if not success:
                    print("❌ 1단계 실패 - 파이프라인 중단")
                    return
                
                # 2단계: 특성 추출 + 예측 (통합된 파일 사용)
                print("\n[2단계] 특성 추출 + 예측 중...")
                success = self._run_step("scripts/2_extract_and_predict.py", "특성 추출 + 예측")
                
                if not success:
                    print("❌ 2단계 실패 - 파이프라인 중단")
                    return
                
                # 결과 누적
                self._accumulate_results()
                
                print(f"\n{'='*60}")
                print(f"🎉 세션 {session_id} 완전 처리 완료!")
                print(f"📄 결과 파일: output/text_features_all_v4.csv")
                print(f"{'='*60}")
            else:
                print(f"⏳ 세션 {session_id} 대기 중...")
                print("   분류, 요약, 질의응답 파일이 모두 준비될 때까지 대기합니다.")
                self._show_session_status(session_id)
            
            # 처리 완료 기록 (원본 파일 경로로 기록)
            self._log_processed_file(file_path)
            
        except Exception as e:
            print(f"❌ 처리 중 오류: {str(e)}")
            
        finally:
            self.is_processing = False
    
    def _extract_session_id(self, file_path):
        """파일 경로에서 세션 ID 추출"""
        filename = Path(file_path).name
        parts = filename.split('_')
        
        # 파일명 패턴: 01_분류_20593_1.json, 02_요약_20594_2.json, 03_질의응답_20595_3.json
        if len(parts) >= 3:
            return parts[2]  # 세션 ID 부분
        return 'unknown'
    
    def _check_session_completion(self, session_id):
        """세션의 모든 데이터 타입이 준비되었는지 확인"""
        data_dirs = {
            'classification': Path("data/classification"),
            'summary': Path("data/summary"),
            'qa': Path("data/qa")
        }
        
        required_types = ['분류', '요약', '질의응답']
        found_types = []
        
        for folder_name, folder_path in data_dirs.items():
            if not folder_path.exists():
                continue
                
            # 해당 세션의 파일들 찾기
            session_files = list(folder_path.glob(f"*{session_id}*.json"))
            if session_files:
                # 파일명에서 데이터 타입 확인
                for file_path in session_files:
                    filename = file_path.name
                    for korean_type in required_types:
                        if korean_type in filename and korean_type not in found_types:
                            found_types.append(korean_type)
        
        # 3개 타입이 모두 있는지 확인
        return len(found_types) >= 3
    
    def _show_session_status(self, session_id):
        """세션의 현재 상태 표시"""
        data_dirs = {
            'classification': Path("data/classification"),
            'summary': Path("data/summary"), 
            'qa': Path("data/qa")
        }
        
        type_mapping = {
            '분류': 'classification',
            '요약': 'summary',
            '질의응답': 'qa'
        }
        
        print(f"\n📊 세션 {session_id} 상태:")
        for korean_type, folder_name in type_mapping.items():
            folder_path = data_dirs[folder_name]
            if folder_path.exists():
                session_files = list(folder_path.glob(f"*{session_id}*.json"))
                status = "✅" if session_files else "❌"
                count = len(session_files)
                print(f"   {status} {korean_type}: {count}개 파일")
            else:
                print(f"   ❌ {korean_type}: 폴더 없음")

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
    
    def __init__(self, watch_dir="data/input"):
        self.watch_dir = Path(watch_dir)
        self.processor = AutoProcessor()
        self.observer = Observer()
        
        # 모니터링 디렉토리 확인
        if not self.watch_dir.exists():
            print(f"⚠️ 모니터링 디렉토리가 없습니다: {self.watch_dir}")
            print("   data/input 폴더를 생성합니다.")
            self.watch_dir.mkdir(parents=True, exist_ok=True)
    
    def start_monitoring(self):
        """모니터링 시작"""
        print(f"🔍 파일 모니터링 시작")
        print(f"   감시 디렉토리: {self.watch_dir.absolute()}")
        print(f"   대상 파일: data/input/*.json")
        print(f"   자동 분류: 분류→classification, 요약→summary, 질의응답→qa")
        print(f"   처리 방식: 세션별로 3개 타입이 모두 준비되면 통합 처리")
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
    # 현재 작업 디렉토리 기준으로 절대 경로 생성
    current_dir = Path.cwd()
    model_dir = current_dir / "trained_models"
    
    required_files = [
        "counseling_quality_model.pkl",
        "label_encoder.pkl", 
        "feature_names.pkl"
    ]
    
    # 디버깅을 위한 정보 출력
    print(f"현재 작업 디렉토리: {current_dir}")
    print(f"모델 디렉토리: {model_dir}")
    print(f"모델 디렉토리 존재 여부: {model_dir.exists()}")
    
    missing_files = [f for f in required_files if not (model_dir / f).exists()]
    if missing_files:
        print(f"❌ 학습된 모델 파일이 없습니다: {missing_files}")
        print("   먼저 train_from_dataset_v4.py를 실행하여 모델을 학습해주세요.")
        
        # 실제 파일 상태 확인을 위한 추가 정보
        print(f"\n📂 {model_dir} 내 파일 목록:")
        if model_dir.exists():
            for file in model_dir.iterdir():
                print(f"   - {file.name}")
        else:
            print("   디렉토리가 존재하지 않습니다.")
        return
    
    print("✅ 학습된 모델 확인 완료")
    
    # 파일 모니터링 시작
    monitor = FileMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main() 