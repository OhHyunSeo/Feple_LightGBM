# -*- coding: utf-8 -*-
"""
4. 상담 품질 분류 모델 학습 (LightGBM)
로컬 환경용으로 수정됨
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
from tqdm import tqdm

def main():
    print("="*60)
    print("상담 품질 분류 모델 학습 시작")
    print("="*60)
    
    # 1) 데이터 로드
    print("\n[1단계] 데이터 로드 중...")
    try:
        train = pd.read_csv('dataset/train.csv', encoding='utf-8-sig')
        val   = pd.read_csv('dataset/val.csv',   encoding='utf-8-sig')
        test  = pd.read_csv('dataset/test.csv',  encoding='utf-8-sig')
        print(f"✅ 데이터 로드 완료")
        print(f"   Train: {train.shape}, Val: {val.shape}, Test: {test.shape}")
    except FileNotFoundError as e:
        print(f"❌ 데이터 파일을 찾을 수 없습니다: {e}")
        print("   먼저 1-3단계를 실행해주세요.")
        return False
    
    # 2) 레이블 인코딩
    print("\n[2단계] 레이블 인코딩 중...")
    
    # 모든 데이터의 레이블 수집
    all_targets = pd.concat([
        train['result_label'],
        val['result_label'],
        test['result_label']
    ]).astype(str)
    
    # 레이블 인코더 생성 및 학습
    label_encoder = LabelEncoder().fit(all_targets)
    
    # 각 데이터셋에 적용
    for df in [train, val, test]:
        df['label_id'] = label_encoder.transform(df['result_label'].astype(str))
    
    print(f"✅ 레이블 클래스: {list(label_encoder.classes_)}")
    print(f"   클래스 개수: {len(label_encoder.classes_)}")
    
    # 3) 범주형 특성 인코딩
    print("\n[3단계] 범주형 특성 인코딩 중...")
    
    categorical_cols = []
    encoders = {}
    
    # 존재하는 범주형 컬럼만 인코딩
    potential_cats = ['sent_label', 'mid_category', 'content_category', 'rec_place']
    for col in potential_cats:
        if col in train.columns:
            categorical_cols.append(col)
            
            # 전체 데이터의 고유값으로 인코더 학습
            all_vals = pd.concat([train[col], val[col], test[col]]).astype(str)
            encoder = LabelEncoder().fit(all_vals)
            encoders[col] = encoder
            
            # 각 데이터셋에 적용
            for df in [train, val, test]:
                df[f'{col}_id'] = encoder.transform(df[col].astype(str))
    
    print(f"✅ 인코딩된 범주형 컬럼: {categorical_cols}")
    
    # 4) 특성 선택
    print("\n[4단계] 학습용 특성 선택 중...")
    
    # 제외할 컬럼들 정의
    exclude_cols = (
        ['session_id', 'result_label', 'label_id'] +
        categorical_cols +  # 원본 범주형 컬럼들
        ['top_nouns']  # 리스트 형태 컬럼
    )
    
    # 텍스트 컬럼이 있다면 제외 (선택사항)
    text_cols = ['consulting_content', 'asr_segments']
    for col in text_cols:
        if col in train.columns:
            exclude_cols.append(col)
    
    # 실제 사용할 특성들 선택
    feature_cols = [c for c in train.columns if c not in exclude_cols]
    
    print(f"✅ 사용할 특성 개수: {len(feature_cols)}")
    print(f"   주요 특성: {feature_cols[:10]}...")
    
    # 5) 학습/검증/테스트 데이터 준비
    print("\n[5단계] 학습용 데이터 준비 중...")
    
    X_train, y_train = train[feature_cols], train['label_id']
    X_val, y_val = val[feature_cols], val['label_id']
    X_test, y_test = test[feature_cols], test['label_id']
    
    # NaN 값 처리 (0으로 채우기)
    for X in [X_train, X_val, X_test]:
        X.fillna(0, inplace=True)
    
    print(f"✅ 특성 행렬 크기: Train {X_train.shape}, Val {X_val.shape}, Test {X_test.shape}")
    print(f"   레이블 분포 (Train): {dict(pd.Series(y_train).value_counts().sort_index())}")
    
    # 6) 클래스 가중치 계산 (불균형 데이터 대응)
    print("\n[6단계] 클래스 가중치 계산 중...")
    
    classes = np.unique(y_train)
    weights = compute_class_weight('balanced', classes=classes, y=y_train)
    class_weight = dict(zip(classes, weights))
    
    print(f"✅ 클래스 가중치: {class_weight}")
    
    # 7) LightGBM 모델 학습
    print("\n[7단계] LightGBM 모델 학습 중...")
    
    model = LGBMClassifier(
        objective='multiclass',
        num_class=len(label_encoder.classes_),
        n_estimators=200,
        learning_rate=0.05,
        max_depth=6,
        num_leaves=31,
        class_weight=class_weight,
        random_state=42,
        verbosity=-1  # 로그 최소화
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
    
    # 8) 모델 평가
    print("\n[8단계] 모델 성능 평가 중...")
    
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
    
    # 9) 모델 및 관련 객체 저장
    print("\n[9단계] 모델 및 메타데이터 저장 중...")
    
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
    
    # 범주형 인코더들 저장
    if encoders:
        cat_encoders_path = 'trained_models/categorical_encoders.pkl'
        with open(cat_encoders_path, 'wb') as f:
            pickle.dump(encoders, f)
        print(f"✅ 범주형 인코더 저장: {cat_encoders_path}")
    
    # 성능 결과 저장
    results = {
        'validation_accuracy': val_accuracy,
        'test_accuracy': test_accuracy,
        'feature_count': len(feature_cols),
        'class_count': len(label_encoder.classes_),
        'classes': list(label_encoder.classes_)
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
    print(f"✅ 저장된 파일들:")
    print(f"   - 모델: {model_path}")
    print(f"   - 인코더: {encoder_path}")
    print(f"   - 특성: {features_path}")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)

