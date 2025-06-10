# -*- coding: utf-8 -*-
"""
2_extract_and_predict.py
- 특성 추출 + 예측을 한번에 수행
- 결과를 text_features_all_v4.csv에 저장 (예측 결과 포함)
"""

import os
import sys
import glob
import json
import re
import pickle
import subprocess
from collections import Counter
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import lightgbm as lgb

def extract_and_predict():
    """특성 추출과 예측을 연속으로 수행"""
    print("="*60)
    print("특성 추출 + 예측 통합 처리")
    print("="*60)
    
    # 1) 2단계 특성 추출 실행
    print("\n[1단계] 텍스트 특성 추출 중...")
    try:
        # Windows 인코딩 문제 해결을 위한 환경 변수 설정
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
        
        # Windows에서 코드페이지를 UTF-8로 설정
        if os.name == 'nt':  # Windows
            try:
                subprocess.run(['chcp', '65001'], shell=True, capture_output=True, check=False)
            except:
                pass
        
        # 2단계 스크립트 실행
        result = subprocess.run(
            [sys.executable, "2_coloums_extraction_v3_json2csv.py"], 
            capture_output=True, 
            text=True, 
            timeout=600,
            env=env,
            encoding='utf-8',
            errors='ignore'
        )
        
        # 결과 확인
        feature_file = "output/text_features_all_v4.csv"
        if Path(feature_file).exists():
            print("✅ 특성 추출 완료")
        else:
            print("❌ 특성 추출 실패 - 출력 파일이 생성되지 않음")
            return False
            
    except Exception as e:
        print(f"❌ 특성 추출 중 오류: {str(e)}")
        return False
    
    # 2) 학습된 모델 로드
    print("\n[2단계] 학습된 모델 로드 중...")
    try:
        model_dir = Path("trained_models")
        
        # 모델 파일들 로드
        with open(model_dir / "counseling_quality_model.pkl", 'rb') as f:
            model = pickle.load(f)
        
        with open(model_dir / "label_encoder.pkl", 'rb') as f:
            label_encoder = pickle.load(f)
        
        with open(model_dir / "feature_names.pkl", 'rb') as f:
            feature_names = pickle.load(f)
        
        # 범주형 인코더 로드 (있는 경우)
        categorical_encoders = {}
        categorical_file = model_dir / "categorical_encoders.pkl"
        if categorical_file.exists():
            with open(categorical_file, 'rb') as f:
                categorical_encoders = pickle.load(f)
        
        print(f"✅ 모델 로드 완료")
        print(f"   - 분류 클래스: {label_encoder.classes_}")
        print(f"   - 특성 개수: {len(feature_names)}")
        print(f"   - 범주형 인코더: {len(categorical_encoders)}개")
        
    except Exception as e:
        print(f"❌ 모델 로드 실패: {str(e)}")
        return False
    
    # 3) 특성 데이터 로드 및 전처리
    print("\n[3단계] 특성 데이터 전처리 중...")
    try:
        # CSV 파일 로드
        df_features = pd.read_csv(feature_file, encoding='utf-8-sig')
        
        # 중복 제거 및 session_id 타입 통일
        df_features = df_features.drop_duplicates(subset=['session_id'])
        df_features['session_id'] = df_features['session_id'].astype(str)
        
        print(f"   📊 처리할 세션 수: {len(df_features)}")
        
        # 레이블 파일 로드 (있는 경우)
        labels_file = "columns_extraction_all/preprocessing/session_labels.csv"
        df_labels = None
        if Path(labels_file).exists():
            df_labels = pd.read_csv(labels_file, encoding='utf-8-sig', dtype={'session_id': str})
            print(f"   📋 레이블 정보: {len(df_labels)}개 세션")
        
        # 데이터 병합
        if df_labels is not None:
            df = df_features.merge(df_labels, on='session_id', how='left')
        else:
            df = df_features.copy()
            df['result_label'] = None
        
        # 범주형 특성 인코딩
        for col, encoder in categorical_encoders.items():
            if col in df.columns:
                print(f"   🔄 범주형 인코딩: {col}")
                original_values = df[col].fillna('missing').astype(str)
                try:
                    df[col] = encoder.transform(original_values)
                except ValueError:
                    # 새로운 값이 있는 경우 기본값으로 처리
                    print(f"     ⚠️ 새로운 범주 발견, 기본값으로 처리")
                    known_classes = set(encoder.classes_)
                    df[col] = [encoder.transform(['missing'])[0] if val not in known_classes 
                              else encoder.transform([val])[0] for val in original_values]
        
        # 특성 선택 및 정렬
        missing_features = []
        for feature in feature_names:
            if feature not in df.columns:
                missing_features.append(feature)
                df[feature] = 0  # 누락된 특성은 0으로 채움
        
        if missing_features:
            print(f"   ⚠️ 누락된 특성 {len(missing_features)}개를 0으로 채움")
        
        # 예측용 데이터 준비
        X_predict = df[feature_names].copy()
        X_predict.fillna(0, inplace=True)
        
        # 데이터 타입 변환
        for col in feature_names:
            X_predict[col] = pd.to_numeric(X_predict[col], errors='coerce').fillna(0)
        
        print(f"   ✅ 예측 데이터 준비 완료: {X_predict.shape}")
        
    except Exception as e:
        print(f"❌ 데이터 전처리 실패: {str(e)}")
        return False
    
    # 4) 예측 수행
    print("\n[4단계] 상담 품질 예측 중...")
    try:
        # 예측 실행
        y_pred_proba = model.predict_proba(X_predict)
        y_pred = np.argmax(y_pred_proba, axis=1)
        
        # 예측 결과 변환
        predicted_labels = label_encoder.inverse_transform(y_pred)
        confidence_scores = np.max(y_pred_proba, axis=1)
        
        # 예측 결과를 원본 DataFrame에 추가
        df_features['predicted_label'] = predicted_labels
        df_features['confidence'] = confidence_scores
        
        # 실제 레이블도 추가 (있는 경우)
        if df_labels is not None:
            # 실제 레이블 병합
            df_with_actual = df_features.merge(df_labels, on='session_id', how='left')
            df_features['actual_label'] = df_with_actual['result_label']
        
        print(f"✅ 예측 완료")
        
        # 예측 결과 분포
        pred_counts = pd.Series(predicted_labels).value_counts()
        print(f"\n📋 예측 결과 분포:")
        for label, count in pred_counts.items():
            percentage = count / len(predicted_labels) * 100
            print(f"   {label}: {count}개 ({percentage:.1f}%)")
        
        # 신뢰도 통계
        print(f"\n📊 신뢰도 통계:")
        print(f"   평균: {confidence_scores.mean():.3f}")
        print(f"   최소: {confidence_scores.min():.3f}")
        print(f"   최대: {confidence_scores.max():.3f}")
        high_confidence = (confidence_scores >= 0.8).sum()
        print(f"   고신뢰도(≥0.8): {high_confidence}개 ({high_confidence/len(confidence_scores)*100:.1f}%)")
        
    except Exception as e:
        print(f"❌ 예측 실행 실패: {str(e)}")
        return False
    
    # 5) 결과 저장
    print("\n[5단계] 결과 저장 중...")
    try:
        # 출력 디렉토리 생성
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # CSV 파일에 저장 (기존 파일 덮어쓰기)
        output_file = output_dir / "text_features_all_v4.csv"
        df_features.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ 결과 저장 완료: {output_file}")
        print(f"   컬럼 수: {len(df_features.columns)}")
        print(f"   행 수: {len(df_features)}")
        
        # 별도로 예측 결과만 저장
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        prediction_columns = ['session_id', 'predicted_label', 'confidence']
        if 'actual_label' in df_features.columns:
            prediction_columns.append('actual_label')
        
        predictions_df = df_features[prediction_columns]
        predictions_file = results_dir / "counseling_quality_predictions.csv"
        predictions_df.to_csv(predictions_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ 예측 결과 별도 저장: {predictions_file}")
        
        # 미리보기
        print(f"\n🔍 결과 미리보기 (상위 3개):")
        for _, row in df_features.head(3).iterrows():
            actual_info = f" (실제: {row.get('actual_label', 'N/A')})" if 'actual_label' in df_features.columns else ""
            print(f"   세션 {row['session_id']}: {row['predicted_label']} (신뢰도: {row['confidence']:.3f}){actual_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ 결과 저장 실패: {str(e)}")
        return False

def main():
    """메인 실행 함수"""
    print("텍스트 특성 추출 + 상담 품질 예측 통합 시스템")
    print("="*50)
    
    # 학습된 모델 파일 확인
    model_dir = Path("trained_models")
    required_files = [
        "counseling_quality_model.pkl",
        "label_encoder.pkl", 
        "feature_names.pkl"
    ]
    
    missing_files = [f for f in required_files if not (model_dir / f).exists()]
    if missing_files:
        print(f"❌ 학습된 모델 파일이 없습니다: {missing_files}")
        print("   먼저 train_from_dataset_v4.py를 실행하여 모델을 학습해주세요.")
        return False
    
    # 통합 처리 실행
    success = extract_and_predict()
    
    if success:
        print("\n" + "="*60)
        print("🎉 특성 추출 + 예측 완료!")
        print("   📄 output/text_features_all_v4.csv (예측 결과 포함)")
        print("   📄 results/counseling_quality_predictions.csv (예측 전용)")
        print("="*60)
    else:
        print("\n❌ 처리 실패")
    
    return success

if __name__ == "__main__":
    main() 