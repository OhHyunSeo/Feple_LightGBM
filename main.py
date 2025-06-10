#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py
Feple LightGBM v2.0 - 상담 품질 분류 자동화 시스템
메인 실행 파일

사용법:
    python main.py                    # 통합 파이프라인 실행
    python main.py --mode monitoring # 모니터링 모드 실행
    python main.py --help            # 도움말 보기
"""

import sys
import argparse
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.pipeline_manager import PipelineManager
from core.config import VERSION, PROJECT_NAME


def parse_arguments():
    """명령줄 인수를 파싱합니다."""
    parser = argparse.ArgumentParser(
        description=f'{PROJECT_NAME} v{VERSION} - 상담 품질 분류 자동화 시스템',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py                     # 기본 통합 파이프라인 실행
  python main.py --mode unified      # 통합 모드로 실행
  python main.py --mode monitoring  # 모니터링 모드로 실행
  python main.py --mode traditional # 전통적인 단계별 실행

지원되는 모드:
  unified     - 통합 파이프라인 (기본값)
  traditional - 단계별 파이프라인
  monitoring  - 파일 모니터링 모드
        """
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['unified', 'traditional', 'monitoring'],
        default='unified',
        help='실행 모드 선택 (기본값: unified)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'{PROJECT_NAME} v{VERSION}'
    )
    
    return parser.parse_args()


def main():
    """메인 실행 함수"""
    print(f"🚀 {PROJECT_NAME} v{VERSION}")
    print("=" * 60)
    
    try:
        # 명령줄 인수 파싱
        args = parse_arguments()
        
        # 파이프라인 매니저 초기화
        manager = PipelineManager(mode=args.mode)
        
        # 파이프라인 실행
        success = manager.run()
        
        if success:
            print("✅ 프로그램이 성공적으로 완료되었습니다!")
            sys.exit(0)
        else:
            print("❌ 프로그램 실행 중 오류가 발생했습니다.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 프로그램이 중단되었습니다.")
        sys.exit(130)
    except Exception as e:
        print(f"❌ 예상치 못한 오류가 발생했습니다: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 