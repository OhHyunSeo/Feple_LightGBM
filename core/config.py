# -*- coding: utf-8 -*-
"""
config.py
- 프로젝트 전체 설정 중앙화
- 경로, 파라미터, 모델 설정 등 관리
"""

import os
from pathlib import Path

# ==================== 프로젝트 정보 ====================
PROJECT_NAME = "Feple LightGBM"
VERSION = "2.0.0"
DESCRIPTION = "상담 품질 분류 자동화 시스템"

# ==================== 기본 경로 설정 ====================
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
RESULTS_DIR = PROJECT_ROOT / "results"
MODELS_DIR = PROJECT_ROOT / "trained_models"
LOGS_DIR = PROJECT_ROOT / "logs"

# JSON 병합 관련 경로
JSON_MERGE_DIR = PROJECT_ROOT / "json_merge"
CLASS_MERGE_DIR = JSON_MERGE_DIR / "classification_merge_output"
SUMMARY_MERGE_DIR = JSON_MERGE_DIR / "summary_merge_output"
QA_MERGE_DIR = JSON_MERGE_DIR / "qa_merge_output"
INTEGRATION_DIR = JSON_MERGE_DIR / "integration_data"

# 데이터셋 관련 경로
DATASET_DIR = PROJECT_ROOT / "dataset"
DATASET_V4_DIR = PROJECT_ROOT / "dataset_v4"

# 컬럼 추출 관련 경로
COLUMNS_DIR = PROJECT_ROOT / "columns_extraction_all"

# ==================== 데이터 설정 ====================
# 지원하는 파일 타입 및 키워드
FILE_TYPE_MAPPINGS = {
    '분류': ['분류', 'classification', 'class', 'classify'],
    '요약': ['요약', 'summary', 'sum', 'summarize'],
    '질의응답': ['질의응답', 'qa', 'qna', 'question', 'answer']
}

# 상담 품질 분류 레이블
QUALITY_LABELS = {
    "만족": "고객이 상담 결과에 만족한 경우",
    "미흡": "상담이 진행되었으나 고객 만족도가 낮은 경우",
    "해결 불가": "고객의 문제를 해결할 수 없는 경우",
    "추가 상담 필요": "추가적인 상담이나 처리가 필요한 경우"
}

QUALITY_LABEL_MAPPING = {
    0: "만족",
    1: "미흡", 
    2: "해결 불가",
    3: "추가 상담 필요"
}

# ==================== 모델 설정 ====================
# 모델 파일 경로
MODEL_FILES = {
    'classifier': MODELS_DIR / 'counseling_quality_model.pkl',
    'label_encoder': MODELS_DIR / 'label_encoder.pkl',
    'feature_names': MODELS_DIR / 'feature_names.pkl',
    'categorical_encoders': MODELS_DIR / 'categorical_encoders.pkl'
}

# LightGBM 하이퍼파라미터
LIGHTGBM_PARAMS = {
    'objective': 'multiclass',
    'num_class': 4,
    'metric': 'multi_logloss',
    'boosting_type': 'gbdt',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.9,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': -1,
    'random_state': 42,
    'n_estimators': 200,
    'n_jobs': -1
}

# 모델 훈련 설정
TRAIN_CONFIG = {
    'test_size': 0.2,
    'val_size': 0.2,
    'random_state': 42,
    'class_weight': 'balanced'
}

# ==================== 특성 추출 설정 ====================
# 텍스트 처리 설정
TEXT_PROCESSING = {
    'batch_size': 32,
    'max_length': 512,
    'device': -1,  # CPU 사용 (-1), GPU 사용시 0
    'sentiment_model': 'nlptown/bert-base-multilingual-uncased-sentiment'
}

# 형태소 분석 설정
MORPHOLOGY = {
    'analyzer': 'okt',  # 'okt', 'kkma', 'komoran'
    'top_nouns_count': 10
}

# 특성 추출 키워드
FEATURE_KEYWORDS = {
    'polite': ['습니다', '아요', '세요', '요.', '니다'],
    'positive': ['감사', '고맙', '좋', '만족', '훌륭', '완벽'],
    'negative': ['불만', '화나', '짜증', '실망', '최악', '불편'],
    'apology': ['죄송', '미안', '양해'],
    'empathy': ['이해', '공감', '마음'],
    'confirmation': ['맞나요', '맞습니까', '확인'],
    'alternative': ['방법', '대안', '다른'],
    'conflict': ['문제', '갈등', '충돌'],
    'manual': ['메뉴얼', '규정', '정책', '절차']
}

# ==================== 파이프라인 설정 ====================
# 파이프라인 스크립트 순서
PIPELINE_SCRIPTS = {
    'preprocessing': '1_preprocessing_model_v3.py',
    'preprocessing_unified': '1_preprocessing_unified.py',
    'feature_extraction': '2_coloums_extraction_v3_json2csv.py',
    'extract_and_predict': '2_extract_and_predict.py',
    'dataset_creation': '3_make_dataset.py',
    'training': '4_train_model.py',
    'prediction': '4_model_predict_only.py'
}

PIPELINE_NAMES = {
    'preprocessing': '1단계: 전처리 및 JSON 병합',
    'feature_extraction': '2단계: 텍스트 특성 추출',
    'dataset_creation': '3단계: 데이터셋 생성',
    'training': '4단계: 모델 훈련',
    'prediction': '4단계: 상담 품질 예측'
}

# ==================== 모니터링 설정 ====================
# 파일 모니터링 설정
MONITORING = {
    'watch_directory': DATA_DIR,
    'output_directory': OUTPUT_DIR,
    'supported_extensions': ['.json'],
    'check_interval': 1,  # 초
    'file_complete_timeout': 30,  # 초
    'max_retries': 3
}

# 로깅 설정
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_encoding': 'utf-8',
    'console_output': True,
    'file_output': True,
    'log_file': LOGS_DIR / 'system.log',
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# ==================== 웹 API 설정 ====================
# FastAPI 설정
API_CONFIG = {
    'title': PROJECT_NAME,
    'description': DESCRIPTION,
    'version': VERSION,
    'host': '0.0.0.0',
    'port': 8000,
    'workers': 4,
    'reload': False
}

# CORS 설정
CORS_CONFIG = {
    'allow_origins': ["*"],
    'allow_credentials': True,
    'allow_methods': ["*"],
    'allow_headers': ["*"]
}

# ==================== 시스템 설정 ====================
# 인코딩 설정 (Windows 호환)
ENCODING_CONFIG = {
    'default': 'utf-8',
    'environment_vars': {
        'PYTHONIOENCODING': 'utf-8',
        'PYTHONLEGACYWINDOWSSTDIO': '1'
    },
    'windows_codepage': '65001'  # UTF-8
}

# 성능 설정
PERFORMANCE = {
    'multiprocessing': True,
    'max_workers': 4,
    'memory_limit': '4GB',
    'timeout': {
        'preprocessing': 300,    # 5분
        'feature_extraction': 600,  # 10분
        'training': 1800,       # 30분
        'prediction': 120       # 2분
    }
}

# ==================== 결과 파일 설정 ====================
# 결과 파일명
RESULT_FILES = {
    'features': OUTPUT_DIR / 'text_features_all_v4.csv',
    'predictions': RESULTS_DIR / 'counseling_quality_predictions.csv',
    'accumulated': OUTPUT_DIR / 'accumulated_results.csv',
    'summary_report': OUTPUT_DIR / 'summary_report.txt',
    'monitoring_log': OUTPUT_DIR / 'monitoring.log'
}

# 데이터셋 파일명
DATASET_FILES = {
    'train': DATASET_DIR / 'train.csv',
    'validation': DATASET_DIR / 'val.csv',
    'test': DATASET_DIR / 'test.csv'
}

# V4 데이터셋 파일명
DATASET_V4_FILES = {
    'train': DATASET_V4_DIR / 'train.csv',
    'validation': DATASET_V4_DIR / 'val.csv',
    'test': DATASET_V4_DIR / 'test.csv'
}

# ==================== 유틸리티 함수 ====================
def ensure_directories():
    """필요한 디렉토리들을 생성합니다."""
    directories = [
        DATA_DIR, OUTPUT_DIR, RESULTS_DIR, MODELS_DIR, LOGS_DIR,
        JSON_MERGE_DIR, CLASS_MERGE_DIR, SUMMARY_MERGE_DIR, QA_MERGE_DIR,
        INTEGRATION_DIR, DATASET_DIR, DATASET_V4_DIR, COLUMNS_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_environment_config():
    """환경 설정을 반환합니다."""
    env = os.environ.copy()
    env.update(ENCODING_CONFIG['environment_vars'])
    return env

def is_windows():
    """Windows 운영체제인지 확인합니다."""
    return os.name == 'nt'

def get_script_path(script_name):
    """스크립트 이름으로 전체 경로를 반환합니다."""
    if script_name in PIPELINE_SCRIPTS:
        return PROJECT_ROOT / PIPELINE_SCRIPTS[script_name]
    return PROJECT_ROOT / script_name

# ==================== 초기화 ====================
# 프로젝트 시작시 필요한 디렉토리 생성
if __name__ == "__main__":
    print(f"{PROJECT_NAME} v{VERSION} 설정 초기화")
    ensure_directories()
    print("✅ 모든 디렉토리가 생성되었습니다.")
else:
    # 모듈 import시 자동으로 디렉토리 생성
    ensure_directories() 