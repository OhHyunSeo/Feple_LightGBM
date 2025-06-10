# 코드 마이그레이션 가이드

## 📋 현재 문제점 및 해결 방안

### 🚨 기존 코드의 주요 문제점

#### 1. **Google Colab 특화 코드**
```python
# ❌ 제거해야 할 코드들
from google.colab import drive
drive.mount('/content/drive')

!pip install lightgbm
!pip install transformers torch
```

**해결방안**: 
- `requirements.txt`로 의존성 관리
- 환경변수 기반 설정으로 변경

#### 2. **하드코딩된 경로**
```python
# ❌ 문제가 있는 코드
INPUT_DIR  = 'data_v3/classification'
OUTPUT_DIR = 'json_merge_all/classification_merge_output_v3'
CLASS_DIR = '/content/drive/MyDrive/Gwangjin_gu/preprocessing_call/json_merge_all/classification_merge_output_v3'
```

**해결방안**:
```python
# ✅ 수정된 코드
from utils.config import get_settings
settings = get_settings()

INPUT_DIR = settings.data_input_dir
OUTPUT_DIR = settings.data_output_dir
```

#### 3. **파일 기반 처리 → API/DB 기반 처리**
```python
# ❌ 기존 방식
with zipfile.ZipFile(zip_path, 'r') as z:
    # ZIP 파일 처리...

# ❌ CSV 파일 저장
df.to_csv('dataset/train.csv', index=False)
```

**해결방안**:
```python
# ✅ 새로운 방식 - 데이터베이스 기반
async def save_to_database(data: Dict[str, Any], session_id: str):
    async with get_db_session() as db:
        record = ProcessedData(
            session_id=session_id,
            data=json.dumps(data),
            created_at=datetime.now()
        )
        db.add(record)
        await db.commit()
```

## 🔄 파일별 마이그레이션 상세 가이드

### 1️⃣ `1_preprocessing_model_v3.py` → `services/preprocessing_service.py`

#### 기존 코드 문제점:
- ZIP 파일 압축 해제 로직
- 파일 시스템 직접 접근
- 동기적 처리

#### 수정 사항:

```python
# ❌ 기존 코드
def extract_zip_files():
    with zipfile.ZipFile(zip_path, 'r') as z:
        for info in tqdm(entries, desc='Unzipping files'):
            # 파일 압축 해제...

# ✅ 수정된 코드  
class PreprocessingService:
    async def process_callytics_json(
        self, 
        callytics_json: Dict[str, Any], 
        session_id: str
    ) -> Dict[str, Any]:
        """
        Callytics JSON을 직접 처리 (ZIP 파일 없음)
        """
        try:
            # JSON 데이터 검증
            validated_data = self._validate_json_structure(callytics_json)
            
            # 세션별 데이터 병합 (기존 로직 활용)
            merged_data = self._merge_session_data(validated_data)
            
            # 데이터베이스에 저장
            await self._save_preprocessed_data(session_id, merged_data)
            
            return merged_data
            
        except Exception as e:
            logger.error(f"Preprocessing failed for {session_id}: {str(e)}")
            raise
```

### 2️⃣ `2_coloums_extraction_v3_json2csv.py` → `services/feature_extraction_service.py`

#### 수정 사항:

```python
# ❌ 기존 코드 - GPU 설정이 전역적
device = 0 if torch.cuda.is_available() else -1
sentiment = pipeline('sentiment-analysis', device=device)

# ✅ 수정된 코드 - 서비스 클래스 내부로 이동
class FeatureExtractionService:
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        self.sentiment_pipeline = self._init_sentiment_pipeline()
        self.okt = Okt()
    
    def _init_sentiment_pipeline(self):
        """감정 분석 파이프라인 초기화"""
        return pipeline(
            'sentiment-analysis',
            model='nlptown/bert-base-multilingual-uncased-sentiment',
            device=self.device
        )
    
    async def extract_features(
        self, 
        preprocessed_data: Dict[str, Any], 
        session_id: str
    ) -> Dict[str, Any]:
        """
        전처리된 데이터에서 특성 추출
        """
        # 기존 extract_text_features 로직을 비동기로 변환
        features = await self._extract_text_features_async(preprocessed_data)
        
        # 데이터베이스에 저장
        await self._save_features(session_id, features)
        
        return features
```

### 3️⃣ `3_make_dataset.py` → `services/dataset_service.py`

#### 수정 사항:

```python
# ❌ 기존 코드 - CSV 파일 기반
train.to_csv('dataset/train.csv', index=False)
val.to_csv('dataset/val.csv', index=False) 
test.to_csv('dataset/test.csv', index=False)

# ✅ 수정된 코드 - 메모리 기반 처리
class DatasetService:
    async def create_dataset(
        self, 
        extracted_features: Dict[str, Any], 
        session_id: str
    ) -> Dict[str, Any]:
        """
        특성 데이터에서 학습용 데이터셋 생성
        """
        # 기존 레이블 추출 로직 활용
        labels = self._extract_labels(extracted_features)
        
        # 특성과 레이블 병합
        dataset = self._merge_features_and_labels(extracted_features, labels)
        
        # 데이터 분할 (실시간 예측용이므로 분할 필요 없을 수도)
        processed_dataset = self._prepare_for_prediction(dataset)
        
        return processed_dataset
```

### 4️⃣ `4_simple_model_v2.py` → `services/prediction_service.py`

#### 수정 사항:

```python
# ❌ 기존 코드 - CSV 파일 로드
train = pd.read_csv('dataset/train.csv')
val = pd.read_csv('dataset/val.csv')
test = pd.read_csv('dataset/test.csv')

# ✅ 수정된 코드 - 실시간 예측
class PredictionService:
    def __init__(self):
        self.model = self._load_trained_model()
        self.label_encoder = self._load_label_encoder()
    
    async def predict(
        self, 
        dataset_info: Dict[str, Any], 
        session_id: str
    ) -> Dict[str, Any]:
        """
        단일 세션에 대한 실시간 예측
        """
        try:
            # 입력 데이터 준비
            X = self._prepare_features(dataset_info)
            
            # 예측 실행
            prediction_proba = self.model.predict_proba(X)
            prediction = self.model.predict(X)[0]
            confidence = max(prediction_proba[0])
            
            # 결과 후처리
            prediction_label = self.label_encoder.inverse_transform([prediction])[0]
            
            result = {
                "prediction": prediction_label,
                "confidence": float(confidence),
                "session_id": session_id,
                "model_version": "v2.0",
                "features": dataset_info
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed for {session_id}: {str(e)}")
            raise
```

## 🔧 환경 설정 수정사항

### `utils/config.py` 생성
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 데이터베이스 설정
    database_url: str
    
    # 모델 설정
    model_path: str = "/app/models/"
    gpu_enabled: bool = True
    batch_size: int = 32
    
    # API 설정
    api_workers: int = 4
    api_port: int = 8000
    
    # Callytics 연동 설정
    callytics_api_endpoint: str
    callytics_api_key: str
    
    class Config:
        env_file = ".env"

def get_settings():
    return Settings()
```

### `requirements.txt` 작성
```txt
# 기본 ML 라이브러리
lightgbm==4.1.0
transformers==4.35.0
torch==2.1.0
konlpy==0.6.0
pandas==2.1.0
numpy==1.24.0
scikit-learn==1.3.0
tqdm==4.66.0

# API 프레임워크
fastapi==0.104.0
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# 데이터베이스
sqlalchemy==2.0.0
asyncpg==0.29.0  # PostgreSQL
alembic==1.12.0  # DB 마이그레이션

# 캐싱 및 백그라운드 작업
redis==5.0.0
celery==5.3.0

# 기타
python-multipart==0.0.6
python-dotenv==1.0.0
```

## 🚀 마이그레이션 실행 순서

### 1. 프로젝트 구조 생성
```bash
mkdir -p {api,services,database,utils,core}/{routers,models}
```

### 2. 기존 파일들을 `core/` 디렉토리로 이동
```bash
mv *.py core/
```

### 3. 서비스 클래스들 생성
- `services/preprocessing_service.py`
- `services/feature_extraction_service.py`
- `services/dataset_service.py`
- `services/prediction_service.py`

### 4. API 엔드포인트 생성
- `api/routers/callytics_integration.py`
- `api/models/request_models.py`
- `api/models/response_models.py`

### 5. 데이터베이스 설정
- `database/models.py`
- `database/connection.py`

### 6. 설정 및 유틸리티
- `utils/config.py`
- `utils/auth.py`
- `utils/helpers.py`

## ⚠️ 주의사항

1. **GPU 메모리 관리**: 여러 세션 동시 처리 시 GPU 메모리 부족 가능
2. **비동기 처리**: 감정 분석 같은 무거운 작업은 비동기로 처리
3. **에러 핸들링**: 각 단계별 실패 시 롤백 로직 필요
4. **캐싱**: 반복적인 모델 로딩을 피하기 위한 캐싱 전략
5. **로깅**: 디버깅을 위한 상세한 로깅 시스템

이렇게 마이그레이션하면 Callytics → LightGBM의 매끄러운 데이터 플로우가 구축됩니다. 