# LightGBM 기반 상담 결과 예측 시스템

## 📋 프로젝트 개요

이 프로젝트는 **Callytics 모델과 연동**되어 상담 콜센터 데이터를 실시간으로 분석하고 상담 결과를 자동 분류하는 **API 기반 머신러닝 시스템**입니다. 

Callytics에서 전송된 JSON 형태의 상담 데이터를 4단계 파이프라인을 통해 처리하여 LightGBM 모델로 예측 결과를 생성하고, 다시 Callytics로 결과를 전송하는 완전 자동화된 시스템입니다.

### 🎯 주요 기능

- **🔗 Callytics 연동**: RESTful API를 통한 실시간 데이터 연동
- **⚡ 4단계 자동 파이프라인**: 전처리 → 특성추출 → 데이터셋생성 → 예측
- **🧠 LightGBM 예측 모델**: 클래스 불균형 처리가 적용된 고성능 분류 모델
- **📊 감정 분석**: BERT 기반 다중 감정 분석 (5점 척도)
- **💾 데이터베이스 저장**: PostgreSQL 기반 결과 저장 및 이력 관리
- **🚀 비동기 처리**: 대용량 데이터 백그라운드 처리 지원
- **📈 실시간 모니터링**: API 상태 및 처리 현황 실시간 확인

### 📊 예측 결과 분류

| 분류 | 설명 | 예시 상황 |
|-----|-----|----------|
| **해결 불가** | 상담으로 해결되지 않은 케이스 | 시스템 장애, 정책 제한 등 |
| **만족** | 고객이 만족한 상담 결과 | 문제 해결 완료, 정보 제공 완료 |
| **미흡** | 상담이 부족하거나 미흡한 경우 | 불완전한 답변, 고객 불만족 |
| **추가 상담 필요** | 후속 상담이 필요한 케이스 | 복잡한 문제, 추가 조치 필요 |

## 🚀 시작하기

### 전제 조건

- Python 3.8 이상
- 충분한 메모리 (최소 8GB RAM 권장)
- GPU 지원 환경 (CUDA 호환)
- PostgreSQL 또는 MySQL 데이터베이스
- Redis (캐싱용, 선택사항)

### 필요한 라이브러리 설치

```bash
# 기본 머신러닝 라이브러리
pip install lightgbm
pip install transformers torch
pip install konlpy
pip install pandas numpy scikit-learn
pip install tqdm

# API 및 웹 프레임워크
pip install fastapi uvicorn
pip install sqlalchemy psycopg2-binary  # PostgreSQL용
pip install redis  # 캐싱용 (선택사항)

# 기타 유틸리티
pip install python-multipart
pip install celery  # 비동기 작업 처리용
pip install pydantic
```

## 📁 프로젝트 구조

```
LightGBM/
├── core/                          # 핵심 모델 로직
│   ├── 1_preprocessing_model_v3.py     # 1단계: 원본 데이터 전처리 및 병합
│   ├── 2_coloums_extraction_v3_json2csv.py  # 2단계: 텍스트 특성 추출
│   ├── 3_make_dataset.py               # 3단계: 학습용 데이터셋 생성
│   └── 4_simple_model_v2.py           # 4단계: LightGBM 모델 학습 및 평가
├── api/                           # API 레이어
│   ├── main.py                    # FastAPI 메인 애플리케이션
│   ├── routers/                   # API 라우터
│   │   ├── data_ingestion.py      # 데이터 수집 API
│   │   ├── processing.py          # 데이터 처리 API
│   │   └── prediction.py          # 예측 결과 API
│   └── models/                    # Pydantic 모델
│       ├── request_models.py      # 요청 모델
│       └── response_models.py     # 응답 모델
├── database/                      # 데이터베이스 관련
│   ├── models.py                  # SQLAlchemy 모델
│   └── connection.py              # DB 연결 설정
├── services/                      # 비즈니스 로직
│   ├── data_pipeline.py           # 전체 파이프라인 서비스
│   ├── preprocessing_service.py   # 전처리 서비스
│   └── prediction_service.py      # 예측 서비스
├── utils/                         # 유틸리티 함수
│   ├── config.py                  # 설정 관리
│   └── helpers.py                 # 헬퍼 함수
├── docker-compose.yml             # Docker 컨테이너 설정
├── Dockerfile                     # Docker 이미지 빌드
├── requirements.txt               # 의존성 관리
└── README.md                      # 프로젝트 설명서
```

## 🏗️ 시스템 아키텍처

이 프로젝트는 **Callytics와 연동되는 LightGBM 기반 예측 시스템**으로, 다음과 같은 데이터 플로우를 가집니다:

```
[Callytics 모델] → [LightGBM API] → [4단계 처리 파이프라인] → [예측 결과] → [Callytics로 결과 전송]
                        ↓
                  [데이터베이스 저장]
```

### 📊 데이터 플로우 상세

1. **Callytics → LightGBM**: JSON 형태의 상담 데이터 전송
2. **1단계 전처리**: 세션별 데이터 병합 및 정리  
3. **2단계 특성추출**: 텍스트 분석, 감정 분석, 대화 패턴 분석
4. **3단계 데이터셋**: 예측용 데이터셋 구성
5. **4단계 예측**: LightGBM 모델로 상담 결과 예측
6. **결과 반환**: Callytics로 예측 결과 및 신뢰도 전송

### 🚀 빠른 시작

#### 1. 환경 설정

```bash
# 1. 저장소 클론
git clone <repository-url>
cd LightGBM

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 3. 의존성 설치
pip install -r requirements.txt
```

#### 2. 데이터베이스 설정

```bash
# PostgreSQL 설치 및 설정
createdb counseling_analysis

# 환경변수 설정 (.env 파일 생성)
DATABASE_URL=postgresql://username:password@localhost:5432/counseling_analysis
REDIS_URL=redis://localhost:6379/0
```

#### 3. 모델 파일 준비

LightGBM 모델과 인코더 파일들을 준비해야 합니다:

```bash
# 모델 디렉토리 생성
mkdir -p models/

# 필요한 모델 파일들 (사전 학습된 모델이 있는 경우)
# models/
# ├── lightgbm_model.pkl        # 학습된 LightGBM 모델
# ├── label_encoder.pkl         # 레이블 인코더
# ├── feature_encoders.pkl      # 특성 인코더들
# └── model_metadata.json       # 모델 메타정보
```

#### 4. API 서버 실행

##### 개발 환경에서 실행
```bash
# FastAPI 서버 시작 (개발용)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 백그라운드에서 실행
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
```

##### 프로덕션 환경에서 실행
```bash
# Gunicorn으로 프로덕션 실행 (다중 워커)
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 또는 Docker로 실행
docker-compose up -d
```

#### 5. 서비스 상태 확인

```bash
# API 서버 상태 확인
curl -X GET "http://localhost:8000/health"

# Swagger UI 접속
# 브라우저에서 http://localhost:8000/docs 접속

# API 버전 확인
curl -X GET "http://localhost:8000/api/v1/info"
```

## 🔄 Callytics 연동 API 사용법

### 1. 🔗 데이터 수신 및 처리 (`POST /api/v1/callytics/process-data`)

**목적**: Callytics에서 상담 데이터를 받아 4단계 파이프라인으로 자동 처리

#### 📤 요청 예시
```bash
curl -X POST "http://localhost:8000/api/v1/callytics/process-data" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "session_id": "session_40001",
    "data": {
      "session_id": "session_40001",
      "consulting_content": "상담사: 안녕하세요, 광진구청입니다. 어떤 도움이 필요하신가요?\n고객: 네, 안녕하세요. 복지 서비스 관련해서 문의드리고 싶습니다.",
      "instructions": [
        {
          "tuning_type": "분류",
          "data": [
            {
              "task_category": "상담 주제",
              "output": "복지 서비스"
            },
            {
              "task_category": "상담 내용", 
              "output": "복지 서비스 신청 문의"
            }
          ]
        }
      ]
    },
    "processing_mode": "realtime",
    "callback_url": "https://callytics.example.com/webhook/result"
  }'
```

#### 📥 응답 예시
```json
{
  "session_id": "session_40001",
  "status": "completed",
  "message": "Processing completed",
  "prediction_result": {
    "prediction": "만족",
    "confidence": 0.87,
    "session_id": "session_40001",
    "model_version": "v2.0",
    "features": {
      "sentiment_score": 4.2,
      "speech_count": 8,
      "category": "복지 서비스"
    }
  },
  "processing_time": "2024-01-15T10:30:45"
}
```

### 2. 📊 처리 상태 확인 (`GET /api/v1/callytics/status/{session_id}`)

**목적**: 특정 세션의 처리 상태 및 결과 조회

```bash
curl -X GET "http://localhost:8000/api/v1/callytics/status/session_40001" \
  -H "X-API-Key: your_api_key_here"
```

**응답 예시**:
```json
{
  "session_id": "session_40001",
  "status": "completed",
  "prediction": "만족",
  "confidence": 0.87,
  "created_at": "2024-01-15T10:30:45Z"
}
```

### 3. 📦 배치 처리 (`POST /api/v1/callytics/batch-process`)

**목적**: 여러 세션을 한 번에 배치 처리

```bash
curl -X POST "http://localhost:8000/api/v1/callytics/batch-process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "requests": [
      {
        "session_id": "session_40001",
        "data": { /* 상담 데이터 1 */ },
        "processing_mode": "background"
      },
      {
        "session_id": "session_40002", 
        "data": { /* 상담 데이터 2 */ },
        "processing_mode": "background"
      }
    ]
  }'
```

### 4. 📋 상세 결과 조회 (`GET /api/v1/callytics/results/{session_id}`)

**목적**: 세션의 상세 처리 결과 및 추출된 특성 조회

```bash
curl -X GET "http://localhost:8000/api/v1/callytics/results/session_40001?include_features=true" \
  -H "X-API-Key: your_api_key_here"
```

**응답 예시**:
```json
{
  "session_id": "session_40001",
  "prediction": "만족",
  "confidence": 0.87,
  "pipeline_steps": {
    "preprocessing": {
      "status": "completed",
      "duration": "0.5s"
    },
    "feature_extraction": {
      "status": "completed", 
      "duration": "2.3s",
      "features_count": 45
    },
    "dataset_creation": {
      "status": "completed",
      "duration": "0.2s"
    },
    "prediction": {
      "status": "completed",
      "duration": "0.1s"
    }
  },
  "extracted_features": {
    "sentiment_scores": {
      "emo_1_star_score": 0.02,
      "emo_2_star_score": 0.05,
      "emo_3_star_score": 0.18,
      "emo_4_star_score": 0.35,
      "emo_5_star_score": 0.40
    },
    "text_analysis": {
      "speech_count": 8,
      "top_nouns": ["복지", "서비스", "신청", "문의"],
      "honorific_ratio": 0.85,
      "positive_word_ratio": 0.12
    },
    "dialogue_patterns": {
      "confirmation_ratio": 0.15,
      "empathy_ratio": 0.08,
      "script_phrase_ratio": 0.25
    }
  }
}
```

## 📚 API 문서

### Swagger UI 접속
API 서버 실행 후 `http://localhost:8000/docs`에서 대화형 API 문서를 확인할 수 있습니다.

### 주요 API 엔드포인트

#### 데이터 관리
- `POST /api/v1/data/upload` - 단일 상담 데이터 업로드
- `POST /api/v1/data/batch-upload` - 다중 상담 데이터 배치 업로드
- `GET /api/v1/data/{session_id}` - 특정 세션 데이터 조회
- `DELETE /api/v1/data/{session_id}` - 세션 데이터 삭제

#### 처리 및 분석
- `POST /api/v1/process/start` - 데이터 처리 파이프라인 시작
- `GET /api/v1/process/status/{task_id}` - 처리 상태 확인
- `POST /api/v1/process/cancel/{task_id}` - 처리 작업 취소

#### 예측 및 결과
- `GET /api/v1/predictions/{session_id}` - 예측 결과 조회
- `POST /api/v1/predictions/batch` - 배치 예측 실행
- `GET /api/v1/predictions/history` - 예측 이력 조회

#### 모델 관리
- `GET /api/v1/models/info` - 현재 모델 정보 조회
- `POST /api/v1/models/retrain` - 모델 재학습 실행
- `GET /api/v1/models/metrics` - 모델 성능 지표 조회

#### 시스템 상태
- `GET /health` - 시스템 헬스체크
- `GET /api/v1/stats` - 시스템 통계 정보
- `GET /api/v1/logs/{level}` - 로그 조회

## 📈 모델 성능

모델은 다음과 같은 평가 지표를 제공합니다:

- **정확도 (Accuracy)**
- **정밀도 (Precision)**  
- **재현율 (Recall)**
- **F1-Score**
- **클래스별 상세 성능 리포트**

## ⚙️ 주요 설정 옵션

### LightGBM 하이퍼파라미터
```python
model = LGBMClassifier(
    objective='multiclass',
    num_class=4,  # 상담 결과 4개 클래스
    n_estimators=200,
    learning_rate=0.05,
    class_weight='balanced',  # 클래스 불균형 처리
    random_state=42
)
```

### 감정 분석 모델
- **사용 모델**: `nlptown/bert-base-multilingual-uncased-sentiment`
- **점수 범위**: 1-5점 (부정~긍정)
- **배치 처리**: GPU 환경에서 효율적 처리

## 🔧 커스터마이징

### 1. 새로운 API 엔드포인트 추가
`api/routers/` 디렉토리에 새로운 라우터를 추가하고 `api/main.py`에 등록하세요.

### 2. 새로운 특성 추가
`services/preprocessing_service.py`에서 특성 추출 로직을 수정하여 새로운 특성을 추가할 수 있습니다.

### 3. 모델 변경
`services/prediction_service.py`에서 LightGBM 외에 다른 모델을 사용할 수 있습니다.

### 4. 데이터베이스 스키마 변경
`database/models.py`에서 SQLAlchemy 모델을 수정하고 마이그레이션을 실행하세요.

## 📋 데이터 요구사항 및 형식

### 📤 Callytics에서 전송해야 하는 데이터 형식

#### 필수 필드
```json
{
  "session_id": "session_40001",                    // 세션 고유 ID (필수)
  "consulting_content": "상담사: ...\n고객: ...",    // 상담 대화 내용 (필수)
  "instructions": [                                  // 분류 정보 (선택)
    {
      "tuning_type": "분류",
      "data": [
        {
          "task_category": "상담 주제",
          "output": "복지 서비스"
        },
        {
          "task_category": "상담 내용",
          "output": "복지 서비스 신청 문의" 
        },
        {
          "task_category": "상담 결과",              // 학습 시에만 필요
          "output": "만족"
        }
      ]
    }
  ]
}
```

#### 상담 내용 형식 예시
```
상담사: 안녕하세요, 광진구청입니다. 어떤 도움이 필요하신가요?
고객: 네, 안녕하세요. 복지 서비스 관련해서 문의드리고 싶습니다.
상담사: 네, 어떤 복지 서비스에 대해 궁금하신가요?
고객: 기초생활수급자 신청을 하고 싶은데 어떻게 해야 하나요?
상담사: 기초생활수급자 신청은 주민센터에서 가능합니다. 필요한 서류를 안내해 드릴게요.
고객: 네, 감사합니다. 서류 목록 좀 알려주세요.
상담사: 신분증, 가족관계증명서, 소득증명서가 필요합니다.
고객: 알겠습니다. 감사합니다!
```

### 📥 LightGBM에서 생성하는 결과 형식

#### 기본 예측 결과
```json
{
  "session_id": "session_40001",
  "prediction": "만족",                    // 예측된 상담 결과
  "confidence": 0.87,                     // 예측 신뢰도 (0-1)
  "model_version": "v2.0",               // 사용된 모델 버전
  "processing_time": "2024-01-15T10:30:45Z"
}
```

#### 상세 결과 (include_features=true)
```json
{
  "session_id": "session_40001",
  "prediction": "만족",
  "confidence": 0.87,
  "extracted_features": {
    "basic_stats": {
      "speech_count": 8,                  // 총 발화 수
      "avg_sentence_length": 15.2,       // 평균 문장 길이
      "total_characters": 245             // 총 문자 수
    },
    "sentiment_analysis": {
      "overall_sentiment": 4.2,          // 전체 감정 점수 (1-5)
      "emo_1_star_score": 0.02,         // 매우 부정
      "emo_2_star_score": 0.05,         // 부정
      "emo_3_star_score": 0.18,         // 중립  
      "emo_4_star_score": 0.35,         // 긍정
      "emo_5_star_score": 0.40,         // 매우 긍정
      "sent_label": "긍정"               // 감정 라벨
    },
    "text_features": {
      "top_nouns": ["복지", "서비스", "신청", "문의"],
      "honorific_ratio": 0.85,          // 경어 사용 비율
      "positive_word_ratio": 0.12,      // 긍정어 비율
      "question_count": 3,              // 질문 수
      "exclamation_count": 1            // 감탄문 수
    },
    "dialogue_patterns": {
      "script_phrase_ratio": 0.25,      // 스크립트 문구 비율
      "confirmation_ratio": 0.15,       // 확인 표현 비율
      "empathy_ratio": 0.08,            // 공감 표현 비율
      "apology_ratio": 0.05,            // 사과 표현 비율
      "solution_offer_count": 2         // 해결책 제시 횟수
    },
    "categories": {
      "mid_category": "복지 서비스",      // 상담 주제
      "content_category": "복지 서비스 신청 문의", // 상담 내용
      "rec_place": "광진구청"            // 상담 장소
    }
  }
}
```

### 🔧 지원하는 데이터 처리 모드

| 모드 | 설명 | 응답 시간 | 사용 시나리오 |
|-----|-----|----------|-------------|
| `realtime` | 실시간 동기 처리 | ~3-5초 | 즉시 결과가 필요한 경우 |
| `background` | 백그라운드 비동기 처리 | 즉시 응답, 별도 조회 | 대량 처리, 배치 작업 |

### ⚠️ 데이터 제한사항

- **세션 ID**: 최대 50자, 영문/숫자/하이픈만 허용
- **상담 내용**: 최대 10,000자
- **동시 처리**: 최대 20개 세션 동시 처리
- **API 요청 크기**: 최대 5MB
- **처리 시간 제한**: 실시간 모드 30초, 백그라운드 모드 10분

## 🐳 Docker 배포

### Docker Compose로 전체 시스템 실행

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/counseling_analysis
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: counseling_analysis
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

```bash
# 전체 시스템 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f app
```

## 🔧 환경 설정

### 환경 변수 설정 (.env)

```bash
# 데이터베이스 설정
DATABASE_URL=postgresql://username:password@localhost:5432/counseling_analysis
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0

# Redis 설정 (캐싱용)
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# 모델 설정
MODEL_PATH=/app/models/
GPU_ENABLED=true
BATCH_SIZE=32

# API 설정
API_WORKERS=4
API_PORT=8000
DEBUG_MODE=false

# 외부 시스템 연동
EXTERNAL_API_ENDPOINT=https://external-system.com/api
EXTERNAL_API_KEY=your_api_key_here
```

## 🚨 운영 고려사항

### 성능 최적화
1. **데이터베이스 인덱싱**: session_id, created_at 컬럼에 인덱스 설정
2. **캐싱 전략**: Redis를 통한 예측 결과 캐싱
3. **비동기 처리**: Celery를 통한 대용량 데이터 백그라운드 처리
4. **로드 밸런싱**: 다중 워커 프로세스 운영

### 모니터링 및 로깅
1. **메트릭 수집**: Prometheus + Grafana 연동
2. **로그 관리**: 구조화된 JSON 로그 형태
3. **에러 추적**: Sentry 연동 권장
4. **헬스체크**: `/health` 엔드포인트 제공

### 보안
1. **API 인증**: JWT 토큰 기반 인증
2. **데이터 암호화**: 민감한 상담 데이터 암호화 저장
3. **네트워크 보안**: HTTPS 통신 및 방화벽 설정
4. **데이터 접근 제어**: 역할 기반 접근 권한 관리

## 🔍 트러블슈팅 및 FAQ

### 🚨 자주 발생하는 문제들

#### 1. **모델 로딩 실패**
```bash
# 에러: ModelNotFoundError
# 해결: 모델 파일 경로 확인
ls -la models/
export MODEL_PATH="/path/to/your/models/"
```

#### 2. **GPU 메모리 부족**
```bash
# 에러: CUDA out of memory
# 해결: 배치 크기 줄이기
export BATCH_SIZE=16  # 기본값 32에서 16으로 감소
export GPU_ENABLED=false  # CPU 모드로 실행
```

#### 3. **데이터베이스 연결 실패**
```bash
# 에러: Connection refused
# 해결: PostgreSQL 서비스 상태 확인
sudo systemctl status postgresql
sudo systemctl start postgresql

# 연결 문자열 확인
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
```

#### 4. **Callytics 연동 인증 실패**
```bash
# 에러: 401 Unauthorized
# 해결: API 키 확인
export CALLYTICS_API_KEY="your_correct_api_key"
```

### 📊 성능 최적화 가이드

#### 1. **대용량 데이터 처리**
```python
# .env 파일 설정
BATCH_SIZE=16                    # GPU 메모리에 맞게 조정
MAX_CONCURRENT_SESSIONS=10       # 동시 처리 세션 수 제한
CACHE_TTL=3600                  # 결과 캐싱 시간 (초)
```

#### 2. **메모리 사용량 최적화**
```bash
# Python 메모리 제한
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=4
ulimit -m 8388608  # 8GB 메모리 제한
```

#### 3. **API 응답 시간 개선**
```python
# gunicorn 설정 최적화
gunicorn api.main:app \
  -w 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --worker-connections 1000 \
  --max-requests 1000 \
  --timeout 30 \
  --keep-alive 2
```

### ❓ 자주 묻는 질문 (FAQ)

#### Q1: Callytics와 연동하려면 어떤 설정이 필요한가요?
**A**: 다음 환경변수들을 설정해야 합니다:
```bash
CALLYTICS_API_ENDPOINT=https://your-callytics-api.com/api
CALLYTICS_API_KEY=your_api_key
LIGHTGBM_WEBHOOK_URL=https://your-lightgbm-api.com/api/v1/callytics/process-data
```

#### Q2: 실시간 처리와 백그라운드 처리의 차이점은?
**A**: 
- **실시간 처리**: 3-5초 내 즉시 결과 반환, 소량 데이터에 적합
- **백그라운드 처리**: 즉시 접수 확인 후 별도 조회, 대량 데이터에 적합

#### Q3: 모델을 새로 학습시키려면?
**A**: 
```bash
# 재학습 API 호출
curl -X POST "http://localhost:8000/api/v1/models/retrain" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "training_data_source": "database",
    "validation_split": 0.2
  }'
```

#### Q4: API 요청 제한이 있나요?
**A**: 
- 요청 크기: 최대 5MB
- 동시 처리: 최대 20개 세션
- 처리 시간: 실시간 30초, 백그라운드 10분
- API 호출 제한: 초당 100회 (설정 가능)

#### Q5: 로그는 어디서 확인할 수 있나요?
**A**:
```bash
# 애플리케이션 로그
tail -f logs/app.log

# API 로그 조회
curl -X GET "http://localhost:8000/api/v1/logs/error" \
  -H "X-API-Key: your_api_key"
```

### 🔧 개발자 가이드

#### 새로운 특성 추가하기
1. `services/feature_extraction_service.py`에서 특성 추출 로직 수정
2. `database/models.py`에서 데이터베이스 스키마 업데이트
3. 마이그레이션 실행: `alembic revision --autogenerate -m "add_new_feature"`

#### 새로운 API 엔드포인트 추가하기
1. `api/routers/`에 새 라우터 파일 생성
2. `api/main.py`에 라우터 등록
3. `api/models/`에 요청/응답 모델 정의

#### 모델 업데이트하기
1. 새 모델을 `models/` 디렉토리에 저장
2. `services/prediction_service.py`에서 모델 로딩 로직 업데이트
3. 모델 버전 관리를 위해 메타데이터 업데이트

### 📞 지원 및 문의

#### 기술 지원
- **버그 리포트**: GitHub Issues 생성
- **기능 요청**: GitHub Discussions 이용
- **긴급 문의**: 시스템 관리자에게 직접 연락

#### 모니터링 대시보드
- **Grafana**: `http://localhost:3000` (성능 지표)
- **Swagger UI**: `http://localhost:8000/docs` (API 문서)
- **로그 뷰어**: `http://localhost:5601` (Kibana, 선택사항)