@echo off
chcp 65001 >nul
:: Feple LightGBM v2.0 Docker 실행 스크립트 (Windows)
:: 상담 품질 분류 자동화 시스템

echo.
echo 🐳 Feple LightGBM Docker 설정을 시작합니다...
echo ==================================================
echo.

:: Docker 설치 확인
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker가 설치되어 있지 않습니다.
    echo Docker를 먼저 설치해주세요: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

:: Docker Compose 설치 확인
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose가 설치되어 있지 않습니다.
    echo Docker Compose를 먼저 설치해주세요: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

echo ✅ Docker 및 Docker Compose가 설치되어 있습니다.
echo.

:: 필요한 디렉토리 생성
echo 📁 필요한 디렉토리를 생성합니다...
if not exist "data" mkdir data
if not exist "output" mkdir output
if not exist "logs" mkdir logs
if not exist "results" mkdir results
if not exist "trained_models" mkdir trained_models
if not exist "pipeline_results" mkdir pipeline_results
echo.

:: Docker 이미지 빌드
echo 🔨 Docker 이미지를 빌드합니다...
docker-compose build

if %errorlevel% equ 0 (
    echo ✅ Docker 이미지 빌드가 완료되었습니다.
) else (
    echo ❌ Docker 이미지 빌드에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo 🎉 Docker 설정이 완료되었습니다!
echo.
echo 사용 방법:
echo ==================================================
echo 1. 프로덕션 환경 실행:
echo    docker-compose up
echo.
echo 2. 백그라운드 실행:
echo    docker-compose up -d
echo.
echo 3. 개발 환경 실행:
echo    docker-compose --profile dev up feple-lightgbm-dev
echo.
echo 4. 컨테이너 내부 접속:
echo    docker-compose exec feple-lightgbm bash
echo.
echo 5. 로그 확인:
echo    docker-compose logs -f feple-lightgbm
echo.
echo 6. 정지 및 정리:
echo    docker-compose down
echo.
echo 7. 데이터 볼륨 포함 완전 정리:
echo    docker-compose down -v
echo.
echo 💡 데이터 파일을 ./data 폴더에 넣고 실행하세요.
echo 💡 결과는 ./output, ./results 폴더에서 확인할 수 있습니다.
echo.

pause 