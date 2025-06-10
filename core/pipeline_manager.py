# -*- coding: utf-8 -*-
"""
pipeline_manager.py
- 통합 파이프라인 관리 시스템
- 모든 파이프라인 작업을 통합 관리
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# 프로젝트 내부 모듈
from config import *
from utils import FileUtils, JSONUtils, LoggerUtils, SystemUtils

class PipelineManager:
    """통합 파이프라인 관리 클래스"""
    
    def __init__(self, mode: str = "unified"):
        """
        파이프라인 매니저 초기화
        
        Args:
            mode: 파이프라인 모드 ('unified', 'traditional', 'monitoring')
        """
        self.mode = mode
        self.logger = LoggerUtils.setup_pipeline_logger(f"pipeline_{mode}")
        self.start_time = time.time()
        
        # 설정 로깅
        LoggerUtils.log_system_info(self.logger)
        LoggerUtils.log_configuration(self.logger, {
            'mode': mode,
            'project_name': PROJECT_NAME,
            'version': VERSION,
            'data_dir': str(DATA_DIR),
            'output_dir': str(OUTPUT_DIR)
        })
        
        # 필요한 디렉토리 생성
        ensure_directories()
        
        # 시스템 환경 설정
        self.env = SystemUtils.setup_utf8_environment()
        if SystemUtils.is_windows():
            SystemUtils.set_windows_utf8_codepage()
    
    def check_prerequisites(self) -> Tuple[bool, List[str]]:
        """
        파이프라인 실행 전 전제조건을 확인합니다.
        
        Returns:
            (모든 조건 충족 여부, 문제점 리스트)
        """
        issues = []
        
        # 1. 필수 스크립트 파일 존재 확인
        required_scripts = [
            PIPELINE_SCRIPTS['preprocessing'],
            PIPELINE_SCRIPTS['preprocessing_unified'],
            PIPELINE_SCRIPTS['feature_extraction'],
            PIPELINE_SCRIPTS['extract_and_predict'],
            PIPELINE_SCRIPTS['prediction']
        ]
        
        for script in required_scripts:
            if not Path(script).exists():
                issues.append(f"필수 스크립트 누락: {script}")
        
        # 2. Python 패키지 요구사항 확인
        required_packages = [
            'pandas', 'numpy', 'sklearn', 'lightgbm', 
            'transformers', 'torch', 'konlpy', 'tqdm'
        ]
        
        all_packages_ok, missing_packages = SystemUtils.check_python_requirements(required_packages)
        if not all_packages_ok:
            issues.append(f"누락된 패키지: {', '.join(missing_packages)}")
        
        # 3. 학습된 모델 파일 확인 (예측 모드인 경우)
        if self.mode in ['unified', 'monitoring']:
            for model_name, model_path in MODEL_FILES.items():
                if not model_path.exists():
                    issues.append(f"모델 파일 누락: {model_path}")
        
        # 4. 시스템 리소스 확인
        available_memory = SystemUtils.get_available_memory_gb()
        if available_memory < 2.0:  # 최소 2GB 메모리 필요
            issues.append(f"메모리 부족: {available_memory:.1f}GB (최소 2GB 필요)")
        
        success = len(issues) == 0
        
        if success:
            self.logger.info("✅ 모든 전제조건이 충족되었습니다.")
        else:
            self.logger.error("❌ 전제조건 확인 실패:")
            for issue in issues:
                self.logger.error(f"   - {issue}")
        
        return success, issues
    
    def run_preprocessing(self, unified: bool = True) -> bool:
        """
        전처리 단계를 실행합니다.
        
        Args:
            unified: 통합 모드 사용 여부
            
        Returns:
            실행 성공 여부
        """
        self.logger.info("="*60)
        self.logger.info("🔄 1단계: 전처리 시작")
        self.logger.info("="*60)
        
        script_name = PIPELINE_SCRIPTS['preprocessing_unified'] if unified else PIPELINE_SCRIPTS['preprocessing']
        
        # 입력 데이터 확인
        if unified:
            json_files = FileUtils.find_files_by_pattern(DATA_DIR, "*.json")
        else:
            # 기존 방식: 하위 폴더별 확인
            class_files = FileUtils.find_files_by_pattern(DATA_DIR / "classification", "*.json")
            summary_files = FileUtils.find_files_by_pattern(DATA_DIR / "summary", "*.json")
            qa_files = FileUtils.find_files_by_pattern(DATA_DIR / "qa", "*.json")
            json_files = class_files + summary_files + qa_files
        
        if not json_files:
            self.logger.error("❌ 처리할 JSON 파일이 없습니다.")
            return False
        
        self.logger.info(f"📄 발견된 JSON 파일: {len(json_files)}개")
        
        # 스크립트 실행
        success, stdout, stderr = SystemUtils.run_python_script(
            script_path=script_name,
            timeout=PERFORMANCE['timeout']['preprocessing']
        )
        
        # 결과 확인
        if success:
            # 출력 폴더 확인으로 성공 여부 판단
            if unified:
                success_indicators = [
                    CLASS_MERGE_DIR.exists(),
                    SUMMARY_MERGE_DIR.exists(),
                    QA_MERGE_DIR.exists()
                ]
            else:
                success_indicators = [CLASS_MERGE_DIR.exists()]
            
            if any(success_indicators):
                self.logger.info("✅ 전처리 완료")
                return True
            else:
                self.logger.error("❌ 전처리 실패 - 출력 폴더가 생성되지 않음")
                return False
        else:
            self.logger.error(f"❌ 전처리 스크립트 실행 실패: {stderr}")
            return False
    
    def run_feature_extraction(self) -> bool:
        """
        특성 추출 단계를 실행합니다.
        
        Returns:
            실행 성공 여부
        """
        self.logger.info("="*60)
        self.logger.info("🔧 2단계: 특성 추출 시작")
        self.logger.info("="*60)
        
        # 스크립트 실행
        success, stdout, stderr = SystemUtils.run_python_script(
            script_path=PIPELINE_SCRIPTS['feature_extraction'],
            timeout=PERFORMANCE['timeout']['feature_extraction']
        )
        
        # 결과 확인
        if success and RESULT_FILES['features'].exists():
            features_size = FileUtils.get_file_size_mb(RESULT_FILES['features'])
            self.logger.info(f"✅ 특성 추출 완료 - 결과 파일: {features_size:.2f}MB")
            return True
        else:
            self.logger.error(f"❌ 특성 추출 실패: {stderr}")
            return False
    
    def run_prediction(self) -> bool:
        """
        예측 단계를 실행합니다.
        
        Returns:
            실행 성공 여부
        """
        self.logger.info("="*60)
        self.logger.info("🤖 4단계: 예측 시작")
        self.logger.info("="*60)
        
        # 특성 파일 존재 확인
        if not RESULT_FILES['features'].exists():
            self.logger.error("❌ 특성 파일이 없습니다. 먼저 특성 추출을 실행해주세요.")
            return False
        
        # 스크립트 실행
        success, stdout, stderr = SystemUtils.run_python_script(
            script_path=PIPELINE_SCRIPTS['prediction'],
            timeout=PERFORMANCE['timeout']['prediction']
        )
        
        # 결과 확인
        if success and RESULT_FILES['predictions'].exists():
            predictions_size = FileUtils.get_file_size_mb(RESULT_FILES['predictions'])
            self.logger.info(f"✅ 예측 완료 - 결과 파일: {predictions_size:.2f}MB")
            return True
        else:
            self.logger.error(f"❌ 예측 실패: {stderr}")
            return False
    
    def run_extract_and_predict(self) -> bool:
        """
        특성 추출과 예측을 통합 실행합니다.
        
        Returns:
            실행 성공 여부
        """
        self.logger.info("="*60)
        self.logger.info("🔧🤖 통합: 특성 추출 + 예측 시작")
        self.logger.info("="*60)
        
        # 스크립트 실행
        success, stdout, stderr = SystemUtils.run_python_script(
            script_path=PIPELINE_SCRIPTS['extract_and_predict'],
            timeout=PERFORMANCE['timeout']['feature_extraction'] + PERFORMANCE['timeout']['prediction']
        )
        
        # 결과 확인
        if success and RESULT_FILES['features'].exists():
            self.logger.info("✅ 통합 처리 완료")
            return True
        else:
            self.logger.error(f"❌ 통합 처리 실패: {stderr}")
            return False
    
    def run_traditional_pipeline(self) -> bool:
        """
        기존 4단계 파이프라인을 실행합니다.
        
        Returns:
            실행 성공 여부
        """
        self.logger.info("🚀 기존 4단계 파이프라인 시작")
        
        # 1단계: 전처리
        if not self.run_preprocessing(unified=False):
            return False
        
        # 2단계: 특성 추출
        if not self.run_feature_extraction():
            return False
        
        # 3단계: 데이터셋 생성 (필요한 경우)
        # 현재는 예측 전용이므로 생략
        
        # 4단계: 예측
        if not self.run_prediction():
            return False
        
        return True
    
    def run_unified_pipeline(self) -> bool:
        """
        통합 파이프라인을 실행합니다.
        
        Returns:
            실행 성공 여부
        """
        self.logger.info("🚀 통합 파이프라인 시작")
        
        # 1단계: 통합 전처리
        if not self.run_preprocessing(unified=True):
            return False
        
        # 2+4단계: 특성 추출 + 예측 통합
        if not self.run_extract_and_predict():
            return False
        
        return True
    
    def generate_report(self) -> Dict[str, Any]:
        """
        파이프라인 실행 결과 보고서를 생성합니다.
        
        Returns:
            실행 결과 보고서
        """
        end_time = time.time()
        execution_time = end_time - self.start_time
        
        report = {
            'pipeline_info': {
                'mode': self.mode,
                'execution_time': execution_time,
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.fromtimestamp(end_time).isoformat()
            },
            'input_data': {},
            'output_data': {},
            'system_info': SystemUtils.get_environment_summary()
        }
        
        # 입력 데이터 정보
        json_files = FileUtils.find_files_by_pattern(DATA_DIR, "*.json")
        report['input_data'] = {
            'total_files': len(json_files),
            'data_size_mb': sum(FileUtils.get_file_size_mb(f) for f in json_files)
        }
        
        # 출력 데이터 정보
        output_files = {}
        for name, path in RESULT_FILES.items():
            if path.exists():
                output_files[name] = {
                    'path': str(path),
                    'size_mb': FileUtils.get_file_size_mb(path),
                    'exists': True
                }
            else:
                output_files[name] = {
                    'path': str(path),
                    'size_mb': 0,
                    'exists': False
                }
        
        report['output_data'] = output_files
        
        # 예측 결과 분석 (가능한 경우)
        if RESULT_FILES['predictions'].exists():
            try:
                import pandas as pd
                df = pd.read_csv(RESULT_FILES['predictions'])
                
                if 'predicted_label' in df.columns:
                    label_counts = df['predicted_label'].value_counts().to_dict()
                    report['prediction_summary'] = {
                        'total_predictions': len(df),
                        'label_distribution': label_counts
                    }
                    
                    if 'confidence' in df.columns:
                        report['prediction_summary']['avg_confidence'] = float(df['confidence'].mean())
                        report['prediction_summary']['high_confidence_count'] = int((df['confidence'] >= 0.8).sum())
            except Exception as e:
                self.logger.warning(f"예측 결과 분석 중 오류: {e}")
        
        return report
    
    def save_report(self, report: Dict[str, Any]) -> bool:
        """
        보고서를 파일로 저장합니다.
        
        Args:
            report: 보고서 데이터
            
        Returns:
            저장 성공 여부
        """
        try:
            # JSON 보고서 저장
            report_file = OUTPUT_DIR / f"pipeline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            JSONUtils.save_json(report, report_file)
            
            # 텍스트 요약 보고서 생성
            summary_lines = [
                f"# 파이프라인 실행 보고서",
                f"",
                f"## 기본 정보",
                f"- 실행 모드: {report['pipeline_info']['mode']}",
                f"- 실행 시간: {report['pipeline_info']['execution_time']:.2f}초",
                f"- 시작 시각: {report['pipeline_info']['start_time']}",
                f"- 종료 시각: {report['pipeline_info']['end_time']}",
                f"",
                f"## 입력 데이터",
                f"- 전체 파일 수: {report['input_data']['total_files']}개",
                f"- 데이터 크기: {report['input_data']['data_size_mb']:.2f}MB",
                f"",
                f"## 출력 데이터"
            ]
            
            for name, info in report['output_data'].items():
                status = "✅" if info['exists'] else "❌"
                summary_lines.append(f"- {name}: {status} ({info['size_mb']:.2f}MB)")
            
            if 'prediction_summary' in report:
                ps = report['prediction_summary']
                summary_lines.extend([
                    f"",
                    f"## 예측 결과",
                    f"- 총 예측 수: {ps['total_predictions']}개",
                    f"- 평균 신뢰도: {ps['avg_confidence']:.3f}",
                    f"- 고신뢰도 예측: {ps['high_confidence_count']}개",
                    f"",
                    f"### 레이블 분포"
                ])
                
                for label, count in ps['label_distribution'].items():
                    percentage = (count / ps['total_predictions']) * 100
                    summary_lines.append(f"- {label}: {count}개 ({percentage:.1f}%)")
            
            # 텍스트 보고서 저장
            summary_file = OUTPUT_DIR / f"pipeline_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(summary_lines))
            
            self.logger.info(f"📋 보고서 저장 완료:")
            self.logger.info(f"   - JSON: {report_file}")
            self.logger.info(f"   - 요약: {summary_file}")
            
            return True
            
        except Exception as e:
            LoggerUtils.log_error_with_traceback(self.logger, e, "보고서 저장")
            return False
    
    def run(self) -> bool:
        """
        파이프라인을 실행합니다.
        
        Returns:
            실행 성공 여부
        """
        self.logger.info(f"🚀 {PROJECT_NAME} v{VERSION} 파이프라인 시작")
        self.logger.info(f"📋 실행 모드: {self.mode}")
        
        # 전제조건 확인
        prerequisites_ok, issues = self.check_prerequisites()
        if not prerequisites_ok:
            return False
        
        # 모드별 파이프라인 실행
        success = False
        
        try:
            if self.mode == "unified":
                success = self.run_unified_pipeline()
            elif self.mode == "traditional":
                success = self.run_traditional_pipeline()
            else:
                self.logger.error(f"❌ 지원하지 않는 모드: {self.mode}")
                return False
            
            # 보고서 생성 및 저장
            report = self.generate_report()
            self.save_report(report)
            
            # 최종 결과 로깅
            if success:
                execution_time = time.time() - self.start_time
                self.logger.info("="*60)
                self.logger.info("🎉 파이프라인 실행 완료!")
                self.logger.info(f"⏰ 총 실행 시간: {execution_time:.2f}초")
                self.logger.info("="*60)
            else:
                self.logger.error("❌ 파이프라인 실행 실패")
            
            return success
            
        except Exception as e:
            LoggerUtils.log_error_with_traceback(self.logger, e, "파이프라인 실행")
            return False

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description=f"{PROJECT_NAME} v{VERSION}")
    parser.add_argument('--mode', 
                      choices=['unified', 'traditional'], 
                      default='unified',
                      help='파이프라인 실행 모드')
    
    args = parser.parse_args()
    
    # 파이프라인 매니저 생성 및 실행
    manager = PipelineManager(mode=args.mode)
    success = manager.run()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 