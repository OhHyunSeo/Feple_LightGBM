# -*- coding: utf-8 -*-
"""
4_model_predict_only.py
- 이미 학습된 모델을 불러와서 예측만 수행
- 상담 품질 분류: 만족, 미흡, 해결 불가, 추가 상담 필요
"""

import pandas as pd
import numpy as np
import pickle
import os
from pathlib import Path
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import lightgbm as lgb

def load_trained_model(model_path="trained_models"):
    """학습된 모델과 인코더를 불러오기"""
    model_dir = Path(model_path)
    
    try:
        # 모델 파일들 확인
        model_file = model_dir / "counseling_quality_model.pkl"
        encoder_file = model_dir / "label_encoder.pkl"
        feature_names_file = model_dir / "feature_names.pkl"
        categorical_encoders_file = model_dir / "categorical_encoders.pkl"
        
        if not all([model_file.exists(), encoder_file.exists(), feature_names_file.exists()]):
            print("❌ 학습된 모델 파일이 없습니다. 먼저 모델을 학습해주세요.")
            return None, None, None, None
        
        # 모델과 인코더 로드
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
        
        with open(encoder_file, 'rb') as f:
            label_encoder = pickle.load(f)
        
        with open(feature_names_file, 'rb') as f:
            feature_names = pickle.load(f)
        
        # 범주형 인코더 로드 (있는 경우)
        categorical_encoders = {}
        if categorical_encoders_file.exists():
            with open(categorical_encoders_file, 'rb') as f:
                categorical_encoders = pickle.load(f)
        
        print(f"✅ 학습된 모델 로드 완료")
        print(f"   - 분류 클래스: {label_encoder.classes_}")
        print(f"   - 특성 개수: {len(feature_names)}")
        print(f"   - 범주형 인코더: {len(categorical_encoders)}개")
        
        return model, label_encoder, feature_names, categorical_encoders
        
    except Exception as e:
        print(f"❌ 모델 로드 실패: {str(e)}")
        return None, None, None, None

def predict_counseling_quality():
    """상담 품질 예측 실행"""
    print("="*60)
    print("상담 품질 분류 예측 시작")
    print("="*60)
    
    # 1) 학습된 모델 로드
    model, label_encoder, feature_names, categorical_encoders = load_trained_model()
    if model is None:
        print("모델을 로드할 수 없어서 예측을 중단합니다.")
        return False
    
    # 2) 새로운 데이터 로드 (특성 추출된 데이터)
    try:
        feature_file = "output/text_features_all_v4.csv"
        if not Path(feature_file).exists():
            print(f"❌ 특성 파일이 없습니다: {feature_file}")
            return False
        
        df_features = pd.read_csv(feature_file, encoding='utf-8-sig')
        
        # 중복 행 제거
        df_features = df_features.drop_duplicates(subset=['session_id'])
        
        # session_id를 문자열로 통일
        df_features['session_id'] = df_features['session_id'].astype(str)
        
        print(f"📊 예측할 세션 수: {len(df_features)}")
        
        # 3) 레이블 파일 로드 (있는 경우)
        labels_file = "columns_extraction_all/preprocessing/session_labels.csv"
        df_labels = None
        if Path(labels_file).exists():
            df_labels = pd.read_csv(labels_file, encoding='utf-8-sig', dtype={'session_id': str})
            print(f"📋 레이블 정보: {len(df_labels)}개 세션")
        
        # 4) 데이터 병합 (레이블이 있는 경우)
        if df_labels is not None:
            df = df_features.merge(df_labels, on='session_id', how='left')
        else:
            df = df_features.copy()
            df['result_label'] = None
        
        # 5) 범주형 특성 인코딩 (학습시와 동일하게)
        for col, encoder in categorical_encoders.items():
            if col in df.columns:
                print(f"   범주형 인코딩: {col}")
                # 모르는 값은 'missing'으로 처리
                original_values = df[col].fillna('missing').astype(str)
                try:
                    df[col] = encoder.transform(original_values)
                except ValueError as e:
                    # 새로운 값이 있는 경우 기본값으로 처리
                    print(f"   새로운 범주 발견 ({col}), 기본값으로 처리")
                    known_classes = set(encoder.classes_)
                    df[col] = [encoder.transform(['missing'])[0] if val not in known_classes else encoder.transform([val])[0] 
                              for val in original_values]
        
        # 6) 특성 선택 및 순서 맞춤
        print(f"\n🔧 특성 데이터 준비 중...")
        
        # 학습 시 사용한 특성들만 선택
        missing_features = []
        available_features = []
        
        for feature in feature_names:
            if feature in df.columns:
                available_features.append(feature)
            else:
                missing_features.append(feature)
                # 누락된 특성은 0으로 채움
                df[feature] = 0
                available_features.append(feature)
        
        if missing_features:
            print(f"   ⚠️ 누락된 특성 {len(missing_features)}개를 0으로 채움: {missing_features[:5]}...")
        
        # 특성 데이터 준비 (학습시와 동일한 순서)
        X_predict = df[feature_names].copy()
        
        # NaN 처리
        X_predict.fillna(0, inplace=True)
        
        # 데이터 타입 변환 (학습시와 동일)
        for col in feature_names:
            X_predict[col] = pd.to_numeric(X_predict[col], errors='coerce').fillna(0)
        
        print(f"   ✅ 예측 데이터 준비 완료: {X_predict.shape}")
        print(f"   데이터 타입: {X_predict.dtypes.value_counts().to_dict()}")
        
        # 7) 예측 수행
        print("\n🔮 상담 품질 예측 중...")
        y_pred_proba = model.predict_proba(X_predict)
        y_pred = np.argmax(y_pred_proba, axis=1)
        
        # 8) 결과 정리
        predicted_labels = label_encoder.inverse_transform(y_pred)
        max_probabilities = np.max(y_pred_proba, axis=1)
        
        # 9) 결과를 DataFrame으로 정리
        results_df = df[['session_id']].copy()
        results_df['predicted_label'] = predicted_labels
        results_df['confidence'] = max_probabilities
        
        # 실제 레이블 추가 (있는 경우)
        if 'result_label' in df.columns:
            results_df['actual_label'] = df['result_label']
        
        # 실제 레이블이 있는 경우 정확도 계산
        if df_labels is not None and 'result_label' in df.columns:
            mask = df['result_label'].notna()
            if mask.sum() > 0:
                y_true = label_encoder.transform(df.loc[mask, 'result_label'])
                y_pred_labeled = y_pred[mask]
                
                accuracy = accuracy_score(y_true, y_pred_labeled)
                print(f"\n📈 예측 정확도: {accuracy:.4f}")
                
                # 분류 리포트 (클래스가 1개 이상일 때만)
                unique_classes = len(np.unique(y_true))
                if unique_classes > 1:
                    print("\n📊 분류 성능 보고서:")
                    print(classification_report(y_true, y_pred_labeled, 
                                              target_names=label_encoder.classes_))
                else:
                    print(f"\n📊 분류 결과: 모든 샘플이 동일한 클래스로 예측됨")
                    predicted_class = label_encoder.inverse_transform([y_pred_labeled[0]])[0]
                    print(f"   예측된 클래스: {predicted_class}")
        
        # 10) 예측 결과 분포
        pred_counts = pd.Series(predicted_labels).value_counts()
        print(f"\n📋 예측 결과 분포:")
        for label, count in pred_counts.items():
            percentage = count / len(predicted_labels) * 100
            print(f"   {label}: {count}개 ({percentage:.1f}%)")
        
        # 11) 결과 저장
        output_dir = Path("results")
        output_dir.mkdir(exist_ok=True)
        
        results_file = output_dir / "counseling_quality_predictions.csv"
        results_df.to_csv(results_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 예측 결과 저장: {results_file}")
        
        # 12) 상위 결과 미리보기
        print(f"\n🔍 예측 결과 미리보기 (상위 5개):")
        preview_df = results_df.head()
        for _, row in preview_df.iterrows():
            actual_info = f" (실제: {row.get('actual_label', 'N/A')})" if 'actual_label' in row else ""
            print(f"   세션 {row['session_id']}: {row['predicted_label']} (신뢰도: {row['confidence']:.3f}){actual_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ 예측 실행 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_trained_models():
    """학습된 모델 파일들이 존재하는지 확인"""
    model_dir = Path("trained_models")
    required_files = [
        "counseling_quality_model.pkl",
        "label_encoder.pkl", 
        "feature_names.pkl"
    ]
    
    all_exist = all((model_dir / f).exists() for f in required_files)
    return all_exist

def main():
    """메인 실행 함수"""
    print("상담 품질 분류 모델 (예측 전용)")
    print("="*50)
    
    # 학습된 모델이 있는지 확인
    if not check_trained_models():
        print("❌ 학습된 모델이 없습니다.")
        print("   먼저 train_from_dataset_v4.py를 실행하여 모델을 학습해주세요.")
        return False
    else:
        print("✅ 학습된 모델이 존재합니다.")
        return predict_counseling_quality()

if __name__ == "__main__":
    main() 