#!/bin/bash

# Feple LightGBM v2.0 Docker 설정 스크립트
# 상담 품질 분류 자동화 시스템

echo "🐳 Feple LightGBM Docker 설정을 시작합니다..."
echo "=================================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker가 설치되어 있지 않습니다.${NC}"
    echo "Docker를 먼저 설치해주세요: https://docs.docker.com/get-docker/"
    exit 1
fi

# Docker Compose 설치 확인
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose가 설치되어 있지 않습니다.${NC}"
    echo "Docker Compose를 먼저 설치해주세요: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker 및 Docker Compose가 설치되어 있습니다.${NC}"

# 필요한 디렉토리 생성
echo -e "${YELLOW}📁 필요한 디렉토리를 생성합니다...${NC}"
mkdir -p data output logs results trained_models pipeline_results

# Docker 이미지 빌드
echo -e "${YELLOW}🔨 Docker 이미지를 빌드합니다...${NC}"
docker-compose build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker 이미지 빌드가 완료되었습니다.${NC}"
else
    echo -e "${RED}❌ Docker 이미지 빌드에 실패했습니다.${NC}"
    exit 1
fi

# 사용법 안내
echo ""
echo -e "${GREEN}🎉 Docker 설정이 완료되었습니다!${NC}"
echo ""
echo "사용 방법:"
echo "=================================================="
echo "1. 프로덕션 환경 실행:"
echo "   docker-compose up"
echo ""
echo "2. 백그라운드 실행:"
echo "   docker-compose up -d"
echo ""
echo "3. 개발 환경 실행:"
echo "   docker-compose --profile dev up feple-lightgbm-dev"
echo ""
echo "4. 컨테이너 내부 접속:"
echo "   docker-compose exec feple-lightgbm bash"
echo ""
echo "5. 로그 확인:"
echo "   docker-compose logs -f feple-lightgbm"
echo ""
echo "6. 정지 및 정리:"
echo "   docker-compose down"
echo ""
echo "7. 데이터 볼륨 포함 완전 정리:"
echo "   docker-compose down -v"
echo ""
echo -e "${YELLOW}💡 데이터 파일을 ./data 폴더에 넣고 실행하세요.${NC}"
echo -e "${YELLOW}💡 결과는 ./output, ./results 폴더에서 확인할 수 있습니다.${NC}" 