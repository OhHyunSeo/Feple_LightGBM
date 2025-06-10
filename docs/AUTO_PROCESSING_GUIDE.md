# 🚀 상담 품질 분류 자동 처리 시스템 가이드

## 📋 **시스템 개요**

이 시스템은 `data` 폴더에 새로운 상담 데이터가 들어오면 자동으로 다음 과정을 수행합니다:

1. **JSON 병합** → 2. **특성 추출** → 3. **품질 예측** → 4. **결과 저장**

## 🔧 **초기 설정**

### 1. 모델 학습 (최초 1회)
```bash
python train_from_dataset_v4.py
```

### 2. 필요 라이브러리 설치
```bash
pip install watchdog pandas numpy scikit-learn lightgbm transformers konlpy
```

## 🎯 **사용 방법**

### 📁 **방법 1: 수동 처리**

새로운 상담 데이터를 `data/classification/` 폴더에 JSON 형태로 추가한 후:

```bash
# 전체 파이프라인 실행 (3단계 건너뛰기)
python classification_pipeline_v3.py

# 또는 특성추출+예측만 실행
python 2_extract_and_predict.py
```

### 🔍 **방법 2: 자동 모니터링**

```bash
# 자동 모니터링 시작 (Ctrl+C로 종료)
python auto_file_monitor.py
```

자동 모니터링이 시작되면:
- `data/classification/` 폴더를 실시간 감시
- 새 JSON 파일 감지시 자동으로 파이프라인 실행
- 결과를 `output/text_features_all_v4.csv`에 누적 저장

## 📂 **파일 구조**

### 입력 데이터 형식
`data/classification/session_id.json`:
```json
{
  "session_id": "unique_session_id",
  "consulting_content": "상담사: 안녕하세요...\n고객: 안녕하세요...",
  "instructions": [
    {
      "task_category": "상담 주제",
      "output": "요금제 변경"
    },
    {
      "task_category": "상담 내용", 
      "output": "일반 문의 상담"
    }
  ]
}
```

### 출력 파일
- **`output/text_features_all_v4.csv`**: 특성 + 예측결과 (메인 결과)
- **`results/counseling_quality_predictions.csv`**: 예측 결과만
- **`output/accumulated_results.csv`**: 누적 결과 (자동 모니터링시)

## 📊 **출력 결과 설명**

### text_features_all_v4.csv 주요 컬럼:
- **session_id**: 세션 ID
- **speech_count**: 발화 수
- **emo_1~5_star_score**: 감정 점수 (1~5점)
- **sent_score**: 감정 종합 점수
- **sent_label**: 감정 레이블 (긍정/중립/부정)
- **predicted_label**: 📍 **예측된 상담 품질** ⭐
- **confidence**: 📍 **예측 신뢰도** ⭐
- **actual_label**: 실제 레이블 (있는 경우)

### 상담 품질 분류:
- **만족**: 고객이 상담 결과에 만족한 경우
- **미흡**: 상담이 진행되었으나 고객 만족도가 낮은 경우  
- **해결 불가**: 고객의 문제를 해결할 수 없는 경우
- **추가 상담 필요**: 추가적인 상담이나 처리가 필요한 경우

## 🔧 **스크립트 설명**

### 핵심 스크립트
- **`train_from_dataset_v4.py`**: 모델 학습 (dataset_v4 사용)
- **`2_extract_and_predict.py`**: 특성추출 + 예측 통합
- **`auto_file_monitor.py`**: 자동 모니터링 시스템
- **`classification_pipeline_v3.py`**: 수동 파이프라인 (3단계 건너뛰기)

### 기존 스크립트 (참고용)
- **`1_preprocessing_model_v3.py`**: JSON 병합
- **`2_coloums_extraction_v3_json2csv.py`**: 특성 추출
- **`4_model_predict_only.py`**: 예측만 수행

## 📈 **성능 정보**

현재 학습된 모델:
- **검증 정확도**: 68.5%
- **테스트 정확도**: 70.0%
- **특성 개수**: 29개
- **분류 클래스**: 4개 (만족, 미흡, 해결불가, 추가상담필요)

## 🚨 **주의사항**

1. **데이터 형식**: JSON 파일은 위 형식을 정확히 따라야 함
2. **세션 ID**: 중복되지 않는 고유한 session_id 사용
3. **한글 인코딩**: UTF-8 인코딩 필수
4. **모델 파일**: `trained_models/` 폴더의 pkl 파일들 필수

## 🔄 **워크플로우**

```
새로운 상담 데이터 (JSON)
         ↓
data/classification/session_id.json
         ↓ (자동 감지 또는 수동 실행)
1단계: JSON 병합 → json_merge/
         ↓
2단계: 특성 추출 → output/text_features_all_v4.csv (임시)
         ↓
3단계: 품질 예측 → predicted_label, confidence 추가
         ↓
최종: output/text_features_all_v4.csv (예측 결과 포함)
```

## 📞 **예제 실행**

### 1. 테스트 데이터 생성
```json
// data/classification/test_example.json
{
  "session_id": "test_001",
  "consulting_content": "상담사: 안녕하세요...\n고객: 요금제 문의드려요..."
}
```

### 2. 수동 처리
```bash
python 2_extract_and_predict.py
```

### 3. 결과 확인
```bash
# CSV 파일에서 새 세션 확인
findstr "test_001" output\text_features_all_v4.csv
```

## 🎯 **활용 팁**

1. **배치 처리**: 여러 파일을 한번에 data/classification에 복사 후 실행
2. **품질 모니터링**: confidence 점수로 예측 신뢰도 확인
3. **결과 분석**: 예측 분포로 전체 상담 품질 트렌드 파악
4. **성능 개선**: 새로운 데이터로 주기적으로 모델 재학습

## ✅ **성공 확인**

시스템이 올바르게 작동하면:
- `output/text_features_all_v4.csv`에 새 세션의 예측 결과가 추가됨
- `predicted_label`과 `confidence` 컬럼에 값이 채워짐
- 콘솔에 예측 결과 분포와 신뢰도 통계가 출력됨

---
🚀 **이제 data 폴더에 새로운 상담 데이터를 추가하면 자동으로 품질 분류가 수행됩니다!** 