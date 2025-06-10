# 🐳 Feple LightGBM v2.0 Docker 가이드

상담 품질 분류 자동화 시스템을 Docker 환경에서 실행하기 위한 가이드입니다.

## 📋 목차

- [시스템 요구사항](#시스템-요구사항)
- [빠른 시작](#빠른-시작)
- [상세 사용법](#상세-사용법)
- [개발 환경](#개발-환경)
- [문제 해결](#문제-해결)
- [Docker 명령어 참조](#docker-명령어-참조)

## 🔧 시스템 요구사항

- **Docker**: 20.10 이상
- **Docker Compose**: 1.29 이상
- **메모리**: 최소 4GB RAM 권장
- **디스크**: 최소 10GB 여유 공간

### Docker 설치

#### Windows
1. [Docker Desktop for Windows](https://docs.docker.com/desktop/windows/install/) 다운로드 및 설치
2. WSL 2 백엔드 활성화

#### macOS
1. [Docker Desktop for Mac](https://docs.docker.com/desktop/mac/install/) 다운로드 및 설치

#### Linux (Ubuntu/Debian)
```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 🚀 빠른 시작

### 1. 자동 설정 스크립트 실행

#### Windows
```cmd
docker_run.bat
```

#### Linux/macOS
```bash
chmod +x docker_setup.sh
./docker_setup.sh
```

### 2. 수동 설정

```bash
# 1. 필요한 디렉토리 생성
mkdir -p data output logs results trained_models pipeline_results

# 2. Docker 이미지 빌드
docker-compose build

# 3. 컨테이너 실행
docker-compose up
```

## 📖 상세 사용법

### 기본 실행

```bash
# 포어그라운드 실행 (로그 실시간 확인)
docker-compose up

# 백그라운드 실행
docker-compose up -d

# 특정 서비스만 실행
docker-compose up feple-lightgbm
```

### 데이터 처리 워크플로우

1. **데이터 준비**
   ```bash
   # 입력 데이터를 data 폴더에 복사
   cp your_data/*.json ./data/
   ```

2. **파이프라인 실행**
   ```bash
   # 통합 파이프라인 실행
   docker-compose exec feple-lightgbm python pipeline_manager.py
   
   # 또는 특정 모드로 실행
   docker-compose exec feple-lightgbm python pipeline_manager.py --mode unified
   ```

3. **결과 확인**
   ```bash
   # 결과 파일 확인
   ls -la ./output/
   ls -la ./results/
   ```

### 컨테이너 관리

```bash
# 실행 중인 컨테이너 확인
docker-compose ps

# 컨테이너 내부 접속
docker-compose exec feple-lightgbm bash

# 로그 확인
docker-compose logs -f feple-lightgbm

# 컨테이너 정지
docker-compose stop

# 컨테이너 및 네트워크 제거
docker-compose down

# 볼륨 포함 완전 제거
docker-compose down -v --rmi all
```

## 🛠 개발 환경

개발 환경에서는 소스 코드가 실시간으로 반영되도록 설정되어 있습니다.

```bash
# 개발 환경 실행
docker-compose --profile dev up feple-lightgbm-dev

# 개발 컨테이너에 Bash로 접속
docker-compose --profile dev exec feple-lightgbm-dev bash
```

### 개발 환경 특징

- 소스 코드 실시간 마운트
- 대화형 터미널 접근
- 개발 도구 사용 가능
- 포트 8001로 서비스 노출

## 🗂 폴더 구조

```
Feple_LightGBM/
├── Dockerfile                 # Docker 이미지 정의
├── docker-compose.yml         # Docker Compose 설정
├── .dockerignore              # Docker 빌드 제외 파일
├── docker_setup.sh            # Linux/macOS 설정 스크립트
├── docker_run.bat             # Windows 설정 스크립트
├── requirements.txt           # Python 의존성
├── pipeline_manager.py        # 메인 애플리케이션
├── config.py                  # 설정 파일
├── utils/                     # 유틸리티 모듈
├── data/                      # 입력 데이터 (호스트와 공유)
├── output/                    # 처리된 데이터 (호스트와 공유)
├── logs/                      # 로그 파일 (호스트와 공유)
├── results/                   # 분석 결과 (호스트와 공유)
├── trained_models/            # 학습된 모델 (호스트와 공유)
└── pipeline_results/          # 파이프라인 결과 (호스트와 공유)
```

## 🔍 문제 해결

### 일반적인 문제

#### 1. 메모리 부족 오류
```bash
# Docker Desktop에서 메모리 할당량 증가 (설정 > Resources > Memory)
# 또는 스왑 메모리 증가
```

#### 2. 포트 충돌
```bash
# docker-compose.yml에서 포트 변경
ports:
  - "8080:8000"  # 호스트 포트를 8080으로 변경
```

#### 3. 권한 문제 (Linux/macOS)
```bash
# Docker 그룹에 사용자 추가
sudo usermod -aG docker $USER
newgrp docker
```

#### 4. 한글 인코딩 문제
```bash
# 컨테이너 내부에서 환경 변수 확인
docker-compose exec feple-lightgbm env | grep -i utf
```

### 로그 확인

```bash
# 전체 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs feple-lightgbm

# 실시간 로그 스트림
docker-compose logs -f --tail=100

# 애플리케이션 로그 (컨테이너 내부)
docker-compose exec feple-lightgbm tail -f logs/pipeline_unified.log
```

### 성능 모니터링

```bash
# 컨테이너 리소스 사용량
docker stats

# 특정 컨테이너 리소스 사용량
docker stats feple-lightgbm-app
```

## 📚 Docker 명령어 참조

### 이미지 관리

```bash
# 이미지 목록
docker images

# 이미지 삭제
docker rmi feple_lightgbm_feple-lightgbm

# 사용하지 않는 이미지 정리
docker image prune -a
```

### 컨테이너 관리

```bash
# 모든 컨테이너 목록
docker ps -a

# 컨테이너 삭제
docker rm feple-lightgbm-app

# 모든 중지된 컨테이너 삭제
docker container prune
```

### 볼륨 관리

```bash
# 볼륨 목록
docker volume ls

# 사용하지 않는 볼륨 삭제
docker volume prune
```

### 시스템 정리

```bash
# 모든 미사용 리소스 정리
docker system prune -a --volumes

# 빌드 캐시 정리
docker builder prune -a
```

## 🌐 외부 서버 배포

### 1. 클라우드 배포 (AWS/GCP/Azure)

```bash
# Docker 이미지를 레지스트리에 푸시
docker tag feple_lightgbm_feple-lightgbm:latest your-registry/feple-lightgbm:latest
docker push your-registry/feple-lightgbm:latest

# 원격 서버에서 실행
docker pull your-registry/feple-lightgbm:latest
docker-compose up -d
```

### 2. 도커 허브 사용

```bash
# Docker Hub에 이미지 푸시
docker tag feple_lightgbm_feple-lightgbm:latest username/feple-lightgbm:latest
docker push username/feple-lightgbm:latest
```

### 3. 환경 변수 설정

```bash
# .env 파일 생성
echo "ENVIRONMENT=production" > .env
echo "LOG_LEVEL=INFO" >> .env

# docker-compose.yml에서 env_file 사용
```

## 📞 지원

문제가 발생하거나 추가 도움이 필요한 경우:

1. **로그 확인**: `docker-compose logs -f`
2. **GitHub Issues**: 프로젝트 저장소의 Issues 탭
3. **문서 확인**: README.md 및 관련 가이드 문서

---

**주의사항**: 
- 운영 환경에서는 보안을 위해 적절한 네트워크 설정과 방화벽을 구성하세요.
- 대용량 데이터 처리 시 충분한 메모리와 스토리지를 확보하세요.
- 정기적으로 Docker 이미지와 컨테이너를 업데이트하세요. 