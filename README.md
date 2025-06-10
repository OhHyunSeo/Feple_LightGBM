# 🚀 Feple LightGBM v2.0

> **상담 품질 분류 자동화 시스템**  
> LightGBM 기반 고성능 텍스트 분류 및 예측 플랫폼

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![LightGBM](https://img.shields.io/badge/LightGBM-3.0+-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)

---

## 📋 목차

- [📖 개요](#-개요)
- [✨ 주요 기능](#-주요-기능)
- [🛠 설치 방법](#-설치-방법)
- [🚀 빠른 시작](#-빠른-시작)
- [📁 프로젝트 구조](#-프로젝트-구조)
- [⚙️ 사용법](#️-사용법)
- [🐳 Docker 사용](#-docker-사용)
- [📊 결과 확인](#-결과-확인)
- [🤝 기여하기](#-기여하기)

---

## 📖 개요

**Feple LightGBM v2.0**은 상담 데이터의 품질을 자동으로 분류하고 예측하는 머신러닝 시스템입니다. 한국어 자연어 처리 기술과 LightGBM 알고리즘을 결합하여 높은 정확도와 빠른 처리 속도를 제공합니다.

### 🎯 주요 대상
- 콜센터 품질 관리자
- 데이터 분석가
- 머신러닝 엔지니어
- 자동화 시스템 운영자

---

## ✨ 주요 기능

### 🔄 **통합 파이프라인**
- **원클릭 실행**: 전처리부터 예측까지 한 번에
- **자동화된 워크플로우**: 수동 개입 최소화
- **실시간 로깅**: 전 과정 추적 및 모니터링

### 🤖 **머신러닝 엔진**
- **LightGBM**: 고성능 그래디언트 부스팅
- **한국어 특화**: KoNLPy, soynlp 기반 전처리
- **다중 분류**: 분류, 요약, Q&A 동시 처리

### 📊 **스마트 분석**
- **특성 추출**: TF-IDF, 임베딩 기반
- **성능 최적화**: 자동 하이퍼파라미터 튜닝
- **결과 시각화**: 상세한 분석 리포트

### 🔍 **모니터링**
- **파일 감시**: 실시간 데이터 입력 감지
- **자동 처리**: 신규 파일 자동 분석
- **알림 시스템**: 처리 상태 실시간 알림

---

## 🛠 설치 방법

### 📋 시스템 요구사항
- **Python**: 3.8 이상
- **메모리**: 최소 4GB RAM
- **디스크**: 10GB 여유 공간
- **OS**: Windows, macOS, Linux

### ⚡ 빠른 설치

1. **저장소 클론**
```bash
git clone <repository-url>
cd Feple_LightGBM
```

2. **자동 설정 실행**
```bash
python setup.py
```

### 🔧 수동 설치

1. **의존성 설치**
```bash
pip install -r requirements.txt
```

2. **디렉토리 생성**
```bash
mkdir data output logs results trained_models pipeline_results
```

---

## 🚀 빠른 시작

### 1️⃣ **데이터 준비**
```bash
# JSON 파일을 data 폴더에 배치
cp your_data/*.json ./data/
```

### 2️⃣ **기본 실행**
```bash
python main.py
```

### 3️⃣ **결과 확인**
```bash
ls -la output/     # 처리된 데이터
ls -la results/    # 분석 결과
```

---

## 📁 프로젝트 구조

```
Feple_LightGBM/
├── 📄 main.py                    # 메인 실행 파일
├── 📄 setup.py                   # 프로젝트 설정
├── 📄 requirements.txt           # 의존성 목록
├── 📄 docker-compose.yml         # Docker 구성
│
├── 📂 core/                      # 핵심 모듈
│   ├── pipeline_manager.py       # 파이프라인 관리자
│   └── config.py                 # 설정 파일
│
├── 📂 scripts/                   # 실행 스크립트
│   ├── 1_preprocessing_unified.py
│   ├── 2_extract_and_predict.py
│   ├── 3_make_dataset.py
│   ├── run_pipeline.py
│   └── train_from_dataset_v4.py
│
├── 📂 utils/                     # 유틸리티 함수
│   ├── file_utils.py
│   ├── json_utils.py
│   ├── logger_utils.py
│   └── system_utils.py
│
├── 📂 monitoring/                # 모니터링 시스템
├── 📂 docker/                    # Docker 관련 파일
├── 📂 docs/                      # 문서 파일
├── 📂 legacy/                    # 이전 버전 파일
│
├── 📂 data/                      # 입력 데이터
├── 📂 output/                    # 처리된 데이터
├── 📂 results/                   # 분석 결과
├── 📂 logs/                      # 로그 파일
├── 📂 trained_models/            # 학습된 모델
└── 📂 pipeline_results/          # 파이프라인 결과
```

---

## ⚙️ 사용법

### 🎮 **기본 명령어**

```bash
# 기본 실행
python main.py

# 도움말 보기
python main.py --help

# 버전 확인
python main.py --version
```

### 🎯 **실행 모드**

```bash
# 통합 모드 (기본값)
python main.py --mode unified

# 전통적인 단계별 모드
python main.py --mode traditional

# 모니터링 모드
python main.py --mode monitoring
```

### 📝 **실행 예시**

```bash
# 1. 데이터 준비
echo "상담 데이터를 data/ 폴더에 배치하세요"

# 2. 통합 파이프라인 실행
python main.py

# 3. 결과 확인
python -c "
import json
with open('output/pipeline_report_latest.json') as f:
    report = json.load(f)
    print(f'처리 완료: {report[\"files_processed\"]}개 파일')
"
```

---

## 🐳 Docker 사용

### 🏗️ **빌드 및 실행**

```bash
# 이미지 빌드
docker-compose build

# 일반 실행 (한 번 실행 후 종료)
docker-compose up feple-lightgbm

# 모니터링 모드 (지속적 실행)
docker-compose --profile monitor up feple-lightgbm-monitor

# 개발 모드
docker-compose --profile dev up feple-lightgbm-dev
```

### 🛠️ **Docker 관리**

```bash
# 컨테이너 내부 접속
docker-compose exec feple-lightgbm bash

# 로그 확인
docker-compose logs -f feple-lightgbm

# 정리
docker-compose down
```

---

## 📊 결과 확인

### 📁 **출력 파일**

| 위치 | 설명 | 형식 |
|------|------|------|
| `output/` | 전처리된 데이터 | CSV, JSON |
| `results/` | 분류 결과 | JSON, TXT |
| `logs/` | 실행 로그 | LOG |
| `pipeline_results/` | 파이프라인 보고서 | JSON |

### 📈 **결과 분석**

```bash
# 최신 보고서 확인
cat output/pipeline_summary_latest.txt

# 성능 지표 확인
python -c "
import json
with open('results/classification_results.json') as f:
    results = json.load(f)
    print(f'정확도: {results[\"accuracy\"]:.2%}')
"
```

---

## 🎛️ 고급 설정

### ⚙️ **설정 파일 수정**

`core/config.py`에서 다음 설정을 조정할 수 있습니다:

```python
# 모델 성능 설정
PERFORMANCE = {
    'n_jobs': -1,                    # CPU 코어 수
    'max_depth': 10,                 # 트리 깊이
    'learning_rate': 0.1             # 학습률
}

# 파일 처리 설정
BATCH_SIZE = 1000                    # 배치 크기
MEMORY_LIMIT = '4GB'                 # 메모리 제한
```

### 📋 **커스텀 모델 학습**

```bash
# 새로운 데이터로 모델 재학습
python scripts/train_from_dataset_v4.py

# 특정 데이터셋으로 학습
python scripts/train_from_dataset_v4.py --dataset custom_dataset.csv
```

---

## 🔧 문제 해결

### ❓ **자주 묻는 질문**

**Q: 메모리 부족 오류가 발생합니다**
```bash
# 배치 크기 줄이기
export BATCH_SIZE=500
python main.py
```

**Q: 한글 인코딩 문제가 있습니다**
```bash
# 환경 변수 설정
export PYTHONIOENCODING=utf-8
export LANG=ko_KR.UTF-8
```

**Q: Docker에서 권한 오류가 발생합니다**
```bash
# 권한 설정 (Linux/macOS)
sudo chown -R $USER:$USER ./data ./output
```

### 🐛 **로그 확인**

```bash
# 상세 로그 확인
tail -f logs/pipeline_unified.log

# 에러 로그만 확인
grep ERROR logs/*.log
```

---

## 🚀 성능 최적화

### ⚡ **속도 향상**

1. **병렬 처리 활성화**
```python
# config.py에서 설정
PERFORMANCE['n_jobs'] = -1  # 모든 CPU 코어 사용
```

2. **메모리 최적화**
```python
# 청크 처리 활성화
CHUNK_SIZE = 10000
MEMORY_EFFICIENT = True
```

3. **GPU 가속 (선택사항)**
```bash
pip install lightgbm[gpu]
```

---

## 📈 모니터링 및 알림

### 📊 **실시간 모니터링**

```bash
# 모니터링 대시보드 실행
python monitoring/dashboard.py

# 웹 브라우저에서 확인
open http://localhost:8080
```

### 🔔 **알림 설정**

```python
# config.py에서 알림 설정
NOTIFICATIONS = {
    'email': 'admin@company.com',
    'slack_webhook': 'https://hooks.slack.com/...',
    'telegram_bot_token': 'your_bot_token'
}
```

---

## 🤝 기여하기

### 💡 **기여 방법**

1. Fork 저장소
2. 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시 (`git push origin feature/amazing-feature`)
5. Pull Request 생성

### 📝 **개발 가이드**

```bash
# 개발 환경 설정
pip install -r requirements-dev.txt

# 코드 스타일 검사
black . && flake8 .

# 테스트 실행
pytest tests/
```

```bash
# 지금 바로 시작하기
python setup.py && python main.py
```

**Happy Coding! 🚀** 
