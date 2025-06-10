#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup.py
Feple LightGBM v2.0 설정 및 초기화 스크립트
"""

import os
import sys
import subprocess
from pathlib import Path

def create_directories():
    """필요한 디렉토리들을 생성합니다."""
    directories = [
        'data',
        'output',
        'logs',
        'results', 
        'trained_models',
        'pipeline_results'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ 디렉토리 생성: {directory}/")

def check_python_version():
    """Python 버전을 확인합니다."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        print(f"현재 버전: {sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python 버전 확인: {sys.version}")

def install_requirements():
    """의존성 패키지를 설치합니다."""
    try:
        print("📦 의존성 패키지 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 의존성 패키지 설치 완료")
    except subprocess.CalledProcessError:
        print("❌ 의존성 패키지 설치 실패")
        sys.exit(1)

def main():
    """메인 설정 함수"""
    print("🔧 Feple LightGBM v2.0 설정을 시작합니다...")
    print("=" * 60)
    
    # Python 버전 확인
    check_python_version()
    
    # 디렉토리 생성
    create_directories()
    
    # 의존성 설치
    install_requirements()
    
    print("\n🎉 설정이 완료되었습니다!")
    print("=" * 60)
    print("사용법:")
    print("  python main.py                # 기본 실행")
    print("  python main.py --help         # 도움말")
    print("  docker-compose up             # Docker 실행")
    print("")

if __name__ == "__main__":
    main() 