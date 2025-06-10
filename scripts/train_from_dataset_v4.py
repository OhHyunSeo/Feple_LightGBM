# -*- coding: utf-8 -*-
"""
dataset_v4 폴더의 파일들로 모델 학습 및 저장
"""

import os
import pandas as pd
import numpy as np
import pickle
import lightgbm as lgb
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from sklearn.utils.class_weight import compute_class_weight
from lightgbm import LGBMClassifier, early_stopping, log_evaluation

def main():
    print("="*60)
    print("dataset_v4로 상담 품질 분류 모델 학습")
    print("="*60)
    
    # 1) 데이터 로드
    print("\n[1단계] dataset_v4 데이터 로드 중...")
    try:
        train = pd.read_csv('dataset_v4/train.csv', encoding='utf-8-sig')
        val   = pd.read_csv('dataset_v4/val.csv',   encoding='utf-8-sig')
        test  = pd.read_csv('dataset_v4/test.csv',  encoding='utf-8-sig')
        print(f"✅ 데이터 로드 완료")
        print(f"   Train: {train.shape}, Val: {val.shape}, Test: {test.shape}")
        print(f"   컬럼 수: {len(train.columns)}")
    except FileNotFoundError as e:
        print(f"❌ 데이터 파일을 찾을 수 없습니다: {e}")
        return False
    
    # 2) 레이블 확인 및 인코딩
    print("\n[2단계] 레이블 확인 및 인코딩 중...")
    
    # result_label 컬럼 확인
    if 'result_label' not in train.columns:
        print("❌ result_label 컬럼이 없습니다.")
        print(f"   사용 가능한 컬럼: {list(train.columns)}")
        return False
    
    # 레이블 분포 확인
    print(f"   레이블 분포: {train['result_label'].value_counts().to_dict()}")
    
    # 레이블 인코딩
    all_targets = pd.concat([
        train['result_label'],
        val['result_label'],
        test['result_label']
    ]).astype(str)
    
    label_encoder = LabelEncoder().fit(all_targets)
    
    # 각 데이터셋에 적용
    for df in [train, val, test]:
        df['label_id'] = label_encoder.transform(df['result_label'].astype(str))
    
    print(f"✅ 레이블 클래스: {list(label_encoder.classes_)}")
    print(f"   클래스 개수: {len(label_encoder.classes_)}")
    
    # 3) 특성 선택 및 타입 처리
    print("\n[3단계] 학습용 특성 선택 및 데이터 타입 처리 중...")
    
    # 제외할 컬럼들 정의
    exclude_cols = [
        'session_id', 'result_label', 'label_id',
        'top_nouns', 'consulting_content', 'asr_segments',
        'Unnamed: 32'  # 혹시 있을 수 있는 unnamed 컬럼
    ]
    
    # Object 타입 컬럼들 처리를 위한 인코더 저장소
    categorical_encoders = {}
    
    # 전체 컬럼 타입 확인 및 처리
    for col in train.columns:
        if col not in exclude_cols:
            # NaN이 많은 컬럼 제외
            nan_ratio = train[col].isna().mean()
            if nan_ratio > 0.5:  # 50% 이상 NaN인 컬럼 제외
                exclude_cols.append(col)
                print(f"   제외 (NaN {nan_ratio:.1%}): {col}")
                continue
            
            # Object 타입 컬럼 처리
            if train[col].dtype == 'object':
                print(f"   인코딩 처리: {col} (object 타입)")
                
                # 모든 데이터셋의 해당 컬럼을 합쳐서 인코더 학습
                all_values = pd.concat([
                    train[col].fillna('missing'),
                    val[col].fillna('missing'),
                    test[col].fillna('missing')
                ]).astype(str)
                
                # LabelEncoder 생성 및 학습
                encoder = LabelEncoder()
                encoder.fit(all_values)
                categorical_encoders[col] = encoder
                
                # 각 데이터셋에 적용
                for df in [train, val, test]:
                    df[col] = encoder.transform(df[col].fillna('missing').astype(str))
    
    # 실제 사용할 특성들 선택
    feature_cols = [c for c in train.columns if c not in exclude_cols]
    
    print(f"✅ 사용할 특성 개수: {len(feature_cols)}")
    print(f"   주요 특성: {feature_cols[:10]}...")
    print(f"   인코딩된 범주형 특성: {len(categorical_encoders)}개")
    
    # 4) 학습/검증/테스트 데이터 준비
    print("\n[4단계] 학습용 데이터 준비 중...")
    
    X_train, y_train = train[feature_cols].copy(), train['label_id']
    X_val, y_val = val[feature_cols].copy(), val['label_id']
    X_test, y_test = test[feature_cols].copy(), test['label_id']
    
    # NaN 값 처리 (0으로 채우기)
    for X in [X_train, X_val, X_test]:
        X.fillna(0, inplace=True)
    
    # 데이터 타입 강제 변환 (모든 컬럼을 numeric으로)
    for col in feature_cols:
        for X in [X_train, X_val, X_test]:
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
    
    print(f"✅ 특성 행렬 크기: Train {X_train.shape}, Val {X_val.shape}, Test {X_test.shape}")
    print(f"   레이블 분포 (Train): {dict(pd.Series(y_train).value_counts().sort_index())}")
    print(f"   데이터 타입 확인: {X_train.dtypes.value_counts().to_dict()}")
    
    # 5) 클래스 가중치 계산 (불균형 데이터 대응)
    print("\n[5단계] 클래스 가중치 계산 중...")
    
    classes = np.unique(y_train)
    weights = compute_class_weight('balanced', classes=classes, y=y_train)
    class_weight = dict(zip(classes, weights))
    
    print(f"✅ 클래스 가중치: {class_weight}")
    
    # 6) LightGBM 모델 학습
    print("\n[6단계] LightGBM 모델 학습 중...")
    
    model = LGBMClassifier(
        objective='multiclass',
        num_class=len(label_encoder.classes_),
        n_estimators=200,
        learning_rate=0.05,
        max_depth=6,
        num_leaves=31,
        class_weight=class_weight,
        random_state=42,
        verbosity=-1
    )
    
    # 학습 실행
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        eval_metric='multi_logloss',
        callbacks=[
            early_stopping(stopping_rounds=20, verbose=True),
            log_evaluation(period=20)
        ]
    )
    
    print("✅ 모델 학습 완료")
    
    # 7) 모델 평가
    print("\n[7단계] 모델 성능 평가 중...")
    
    # 검증 세트 평가
    y_pred_val = model.predict(X_val)
    val_accuracy = accuracy_score(y_val, y_pred_val)
    
    print(f"\n--- 검증 세트 성능 ---")
    print(f"정확도: {val_accuracy:.4f}")
    print("\n분류 리포트:")
    print(classification_report(y_val, y_pred_val, target_names=label_encoder.classes_))
    
    # 테스트 세트 평가
    y_pred_test = model.predict(X_test)
    test_accuracy = accuracy_score(y_test, y_pred_test)
    
    print(f"\n--- 테스트 세트 성능 ---")
    print(f"정확도: {test_accuracy:.4f}")
    print("\n분류 리포트:")
    print(classification_report(y_test, y_pred_test, target_names=label_encoder.classes_))
    
    # 8) 모델 및 관련 객체 저장
    print("\n[8단계] 모델 및 메타데이터 저장 중...")
    
    # 저장 폴더 생성
    os.makedirs('trained_models', exist_ok=True)
    
    # 모델 저장
    model_path = 'trained_models/counseling_quality_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"✅ 모델 저장: {model_path}")
    
    # 레이블 인코더 저장
    encoder_path = 'trained_models/label_encoder.pkl'
    with open(encoder_path, 'wb') as f:
        pickle.dump(label_encoder, f)
    print(f"✅ 레이블 인코더 저장: {encoder_path}")
    
    # 특성 이름 저장
    features_path = 'trained_models/feature_names.pkl'
    with open(features_path, 'wb') as f:
        pickle.dump(feature_cols, f)
    print(f"✅ 특성 이름 저장: {features_path}")
    
    # 범주형 인코더 저장
    categorical_path = 'trained_models/categorical_encoders.pkl'
    with open(categorical_path, 'wb') as f:
        pickle.dump(categorical_encoders, f)
    print(f"✅ 범주형 인코더 저장: {categorical_path}")
    
    # 성능 결과 저장
    results = {
        'validation_accuracy': val_accuracy,
        'test_accuracy': test_accuracy,
        'feature_count': len(feature_cols),
        'class_count': len(label_encoder.classes_),
        'classes': list(label_encoder.classes_),
        'feature_names': feature_cols,
        'categorical_features': list(categorical_encoders.keys())
    }
    
    results_path = 'results/model_training_results.json'
    os.makedirs('results', exist_ok=True)
    import json
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ 학습 결과 저장: {results_path}")
    
    print("\n" + "="*60)
    print("🎉 모델 학습 및 저장 완료!")
    print("="*60)
    print(f"✅ 검증 정확도: {val_accuracy:.3f}")
    print(f"✅ 테스트 정확도: {test_accuracy:.3f}")
    print(f"✅ 분류 클래스: {label_encoder.classes_}")
    print(f"✅ 저장된 파일들:")
    print(f"   - 모델: {model_path}")  
    print(f"   - 인코더: {encoder_path}")
    print(f"   - 특성: {features_path}")
    print(f"   - 범주형 인코더: {categorical_path}")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1) 