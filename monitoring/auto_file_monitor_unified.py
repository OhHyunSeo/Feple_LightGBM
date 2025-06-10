# -*- coding: utf-8 -*-
"""
auto_file_monitor_unified.py
- 통합 data 폴더 모니터링 및 자동 처리
- 파일명 기반으로 분류/요약/질의응답 구분
"""

import os
import time
import json
import subprocess
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import pandas as pd

class UnifiedFileMonitor(FileSystemEventHandler):
    """통합 파일 모니터링 핸들러"""
    
    def __init__(self, monitor_dir="data", output_dir="output"):
        self.monitor_dir = monitor_dir
        self.output_dir = output_dir
        self.processed_files = set()
        self.results_file = os.path.join(output_dir, "accumulated_results.csv")
        
        # 출력 폴더 생성
        os.makedirs(output_dir, exist_ok=True)
        
        # 로깅 설정
        self.setup_logging()
        
        # 지원하는 파일 타입
        self.file_type_keywords = {
            '분류': ['분류', 'classification', 'class'],
            '요약': ['요약', 'summary', 'sum'],
            '질의응답': ['질의응답', 'qa', 'qna', 'question']
        }
        
        self.logger.info("="*60)
        self.logger.info("🔄 통합 파일 모니터링 시스템 시작")
        self.logger.info(f"📁 모니터링 폴더: {monitor_dir}")
        self.logger.info(f"📁 출력 폴더: {output_dir}")
        self.logger.info("="*60)
    
    def setup_logging(self):
        """로깅 설정"""
        log_file = os.path.join(self.output_dir, "monitoring.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def detect_file_type(self, filename):
        """파일명에서 데이터 타입 감지"""
        filename_lower = filename.lower()
        
        for data_type, keywords in self.file_type_keywords.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return data_type
        
        return None
    
    def extract_session_id(self, filename):
        """파일명에서 세션 ID 추출"""
        import re
        numbers = re.findall(r'\d+', filename)
        if numbers:
            return numbers[0]  # 첫 번째 숫자를 세션 ID로 사용
        return 'unknown'
    
    def on_created(self, event):
        """새 파일 생성 이벤트 처리"""
        if event.is_directory:
            return
            
        file_path = event.src_path
        filename = os.path.basename(file_path)
        
        # JSON 파일만 처리
        if not filename.endswith('.json'):
            return
        
        # 이미 처리된 파일 체크
        if file_path in self.processed_files:
            return
        
        # 파일 타입 감지
        file_type = self.detect_file_type(filename)
        if not file_type:
            self.logger.warning(f"⚠️ 알 수 없는 파일 타입: {filename}")
            return
        
        session_id = self.extract_session_id(filename)
        
        self.logger.info(f"🆕 새 파일 감지: {filename}")
        self.logger.info(f"   타입: {file_type}")
        self.logger.info(f"   세션 ID: {session_id}")
        
        # 파일이 완전히 생성될 때까지 대기
        self.wait_for_file_complete(file_path)
        
        # 처리 시작
        self.process_new_file(file_path, file_type, session_id)
    
    def wait_for_file_complete(self, file_path, timeout=30):
        """파일이 완전히 생성될 때까지 대기"""
        start_time = time.time()
        last_size = 0
        
        while time.time() - start_time < timeout:
            try:
                current_size = os.path.getsize(file_path)
                if current_size == last_size and current_size > 0:
                    time.sleep(1)  # 1초 더 대기
                    if os.path.getsize(file_path) == current_size:
                        break
                last_size = current_size
                time.sleep(0.5)
            except OSError:
                time.sleep(0.5)
                continue
    
    def process_new_file(self, file_path, file_type, session_id):
        """새 파일 처리"""
        try:
            self.logger.info(f"🔄 파일 처리 시작: {os.path.basename(file_path)}")
            
            # 1단계: 전처리 (통합 스크립트 사용)
            self.logger.info("   [1단계] 전처리 실행...")
            preprocess_result = self.run_preprocessing()
            
            if not preprocess_result:
                self.logger.error("❌ 전처리 실패")
                return
            
            # 2단계: 특징 추출 및 예측
            self.logger.info("   [2단계] 특징 추출 및 예측...")
            prediction_result = self.run_feature_extraction_and_prediction()
            
            if not prediction_result:
                self.logger.error("❌ 특징 추출 및 예측 실패")
                return
            
            # 결과 누적
            self.accumulate_results(file_path, file_type, session_id)
            
            # 처리 완료 표시
            self.processed_files.add(file_path)
            
            self.logger.info(f"✅ 파일 처리 완료: {os.path.basename(file_path)}")
        
        except Exception as e:
            self.logger.error(f"❌ 파일 처리 중 오류: {e}")
    
    def run_preprocessing(self):
        """통합 전처리 실행"""
        try:
            # UTF-8 환경 설정
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
            
            # 통합 전처리 스크립트 실행
            cmd = [
                'chcp', '65001', '&&',
                'python', 
                '1_preprocessing_unified.py'
            ]
            
            result = subprocess.run(
                ' '.join(cmd),
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                env=env,
                cwd=os.getcwd()
            )
            
            # 성공 여부 확인 (출력 폴더 존재 확인)
            success_indicators = [
                os.path.exists('json_merge/classification_merge_output'),
                os.path.exists('json_merge/summary_merge_output'),
                os.path.exists('json_merge/qa_merge_output')
            ]
            
            if any(success_indicators):
                self.logger.info("   ✅ 전처리 완료")
                return True
            else:
                self.logger.error("   ❌ 전처리 실패 - 출력 폴더 없음")
                if result.stderr:
                    # 실제 오류만 출력 (인코딩 오류는 무시)
                    stderr_lines = result.stderr.split('\n')
                    real_errors = [line for line in stderr_lines 
                                 if line.strip() and 
                                 'UnicodeDecodeError' not in line and
                                 'cp949' not in line]
                    if real_errors:
                        self.logger.error(f"   오류: {'; '.join(real_errors[:3])}")
                return False
                
        except Exception as e:
            self.logger.error(f"   전처리 실행 오류: {e}")
            return False
    
    def run_feature_extraction_and_prediction(self):
        """특징 추출 및 예측 실행"""
        try:
            # UTF-8 환경 설정
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
            
            # 특징 추출 및 예측 스크립트 실행
            cmd = [
                'chcp', '65001', '&&',
                'python', 
                '2_extract_and_predict.py'
            ]
            
            result = subprocess.run(
                ' '.join(cmd),
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                env=env,
                cwd=os.getcwd()
            )
            
            # 성공 여부 확인 (결과 파일 존재 확인)
            result_file = 'output/text_features_all_v4.csv'
            if os.path.exists(result_file):
                self.logger.info("   ✅ 특징 추출 및 예측 완료")
                return True
            else:
                self.logger.error("   ❌ 특징 추출 및 예측 실패 - 결과 파일 없음")
                if result.stderr:
                    stderr_lines = result.stderr.split('\n')
                    real_errors = [line for line in stderr_lines 
                                 if line.strip() and 
                                 'UnicodeDecodeError' not in line and
                                 'cp949' not in line]
                    if real_errors:
                        self.logger.error(f"   오류: {'; '.join(real_errors[:3])}")
                return False
                
        except Exception as e:
            self.logger.error(f"   특징 추출 및 예측 실행 오류: {e}")
            return False
    
    def accumulate_results(self, file_path, file_type, session_id):
        """결과를 누적 파일에 저장"""
        try:
            # 최신 결과 파일 읽기
            result_file = 'output/text_features_all_v4.csv'
            if not os.path.exists(result_file):
                self.logger.warning("   결과 파일이 없습니다.")
                return
            
            # 새로운 결과 로드
            new_results = pd.read_csv(result_file, encoding='utf-8')
            
            # 메타데이터 추가
            new_results['processed_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_results['source_file'] = os.path.basename(file_path)
            new_results['data_type'] = file_type
            
            # 누적 파일에 추가
            if os.path.exists(self.results_file):
                # 기존 결과와 합치기
                existing_results = pd.read_csv(self.results_file, encoding='utf-8')
                combined_results = pd.concat([existing_results, new_results], ignore_index=True)
            else:
                combined_results = new_results
            
            # 중복 제거 (session_id 기준)
            combined_results = combined_results.drop_duplicates(subset=['session_id'], keep='last')
            
            # 저장
            combined_results.to_csv(self.results_file, index=False, encoding='utf-8')
            
            self.logger.info(f"   📈 누적 결과 저장: {len(combined_results)}개 세션")
            
            # 예측 결과 요약
            if 'predicted_label' in new_results.columns:
                prediction_summary = new_results['predicted_label'].value_counts()
                self.logger.info(f"   📊 새 예측 결과:")
                for label, count in prediction_summary.items():
                    self.logger.info(f"      {label}: {count}개")
            
        except Exception as e:
            self.logger.error(f"   결과 누적 오류: {e}")
    
    def generate_summary_report(self):
        """요약 리포트 생성"""
        if not os.path.exists(self.results_file):
            return
        
        try:
            df = pd.read_csv(self.results_file, encoding='utf-8')
            
            report = f"""
📊 통합 처리 결과 요약 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
{'='*60}

📈 전체 통계:
  • 총 처리된 세션: {len(df)}개
  • 처리된 데이터 타입: {df['data_type'].nunique() if 'data_type' in df.columns else 'N/A'}개

"""
            
            if 'predicted_label' in df.columns:
                label_counts = df['predicted_label'].value_counts()
                report += "🎯 예측 결과 분포:\n"
                for label, count in label_counts.items():
                    percentage = (count / len(df)) * 100
                    report += f"  • {label}: {count}개 ({percentage:.1f}%)\n"
                
                if 'confidence' in df.columns:
                    avg_confidence = df['confidence'].mean() * 100  # 백분율로 변환
                    high_confidence = (df['confidence'] >= 0.8).sum()
                    report += f"\n🔍 신뢰도 분석:\n"
                    report += f"  • 평균 신뢰도: {avg_confidence:.1f}%\n"
                    report += f"  • 고신뢰도 예측 (≥80%): {high_confidence}개 ({(high_confidence/len(df)*100):.1f}%)\n"
            
            if 'data_type' in df.columns:
                type_counts = df['data_type'].value_counts()
                report += f"\n📋 데이터 타입별 분포:\n"
                for data_type, count in type_counts.items():
                    report += f"  • {data_type}: {count}개\n"
            
            # 리포트 저장
            report_file = os.path.join(self.output_dir, "summary_report.txt")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            # 로그에도 출력
            self.logger.info(report)
            
        except Exception as e:
            self.logger.error(f"리포트 생성 오류: {e}")
    
    def scan_existing_files(self):
        """기존 파일들 스캔 및 처리"""
        self.logger.info("🔍 기존 파일 스캔 중...")
        
        if not os.path.exists(self.monitor_dir):
            self.logger.warning(f"모니터링 폴더가 없습니다: {self.monitor_dir}")
            return
        
        existing_files = []
        for file_path in Path(self.monitor_dir).glob('*.json'):
            filename = file_path.name
            file_type = self.detect_file_type(filename)
            
            if file_type:
                existing_files.append((str(file_path), file_type, self.extract_session_id(filename)))
        
        if existing_files:
            self.logger.info(f"📄 {len(existing_files)}개 기존 파일 발견")
            
            for file_path, file_type, session_id in existing_files:
                self.logger.info(f"   {file_type} | 세션 {session_id} | {os.path.basename(file_path)}")
            
            # 사용자 확인
            while True:
                try:
                    response = input(f"\n기존 파일들을 처리하시겠습니까? (y/n): ").lower()
                    if response in ['y', 'yes', 'ㅛ']:
                        for file_path, file_type, session_id in existing_files:
                            self.process_new_file(file_path, file_type, session_id)
                        break
                    elif response in ['n', 'no', 'ㅜ']:
                        self.logger.info("기존 파일 처리를 건너뜁니다.")
                        break
                    else:
                        print("y 또는 n을 입력해주세요.")
                except KeyboardInterrupt:
                    self.logger.info("사용자가 취소했습니다.")
                    break
        else:
            self.logger.info("기존 파일이 없습니다.")

def main():
    """메인 실행 함수"""
    print("🚀 통합 폴더 기반 자동 처리 시스템")
    print("="*50)
    
    # 모니터링 설정
    monitor_dir = "data"
    output_dir = "output"
    
    # 폴더 생성
    os.makedirs(monitor_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # 파일 모니터 생성
    event_handler = UnifiedFileMonitor(monitor_dir, output_dir)
    
    # 기존 파일 스캔
    event_handler.scan_existing_files()
    
    # 실시간 모니터링 시작
    observer = Observer()
    observer.schedule(event_handler, monitor_dir, recursive=False)
    observer.start()
    
    print(f"\n👀 실시간 모니터링 시작...")
    print(f"📁 모니터링 폴더: {monitor_dir}")
    print(f"📁 결과 폴더: {output_dir}")
    print(f"\n📝 지원하는 파일명 패턴:")
    print(f"   • 분류: 분류_세션ID_번호.json")
    print(f"   • 요약: 요약_세션ID_번호.json") 
    print(f"   • 질의응답: 질의응답_세션ID_번호.json")
    print(f"   (또는 영어: classification, summary, qa)")
    print(f"\n⚡ 새 JSON 파일을 {monitor_dir} 폴더에 추가하면 자동으로 처리됩니다!")
    print(f"🛑 종료하려면 Ctrl+C를 누르세요.")
    
    try:
        while True:
            time.sleep(60)  # 1분마다 요약 리포트 업데이트
            event_handler.generate_summary_report()
    
    except KeyboardInterrupt:
        observer.stop()
        print(f"\n🛑 모니터링 종료")
        event_handler.generate_summary_report()
    
    observer.join()

if __name__ == "__main__":
    main() 