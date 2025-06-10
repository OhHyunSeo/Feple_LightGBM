# Feple LightGBM v2.0 - 상담 품질 분류 자동화 시스템
# Base Image: Python 3.9 slim
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    cmake \
    build-essential \
    curl \
    wget \
    git \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# UTF-8 환경 설정
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONIOENCODING=utf-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Python 요구사항 복사 및 설치
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 코드 복사
COPY . .

# 필요한 디렉토리 생성
RUN mkdir -p data output logs results trained_models pipeline_results

# 포트 노출 (FastAPI 사용시)
EXPOSE 8000

# 기본 실행 명령어 - 메인 파일 사용
CMD ["python", "main.py"] 