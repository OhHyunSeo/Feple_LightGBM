"""
데이터 처리 파이프라인 서비스
Callytics에서 받은 JSON 데이터를 1-4단계로 처리하는 통합 서비스
"""

import json
import logging
import traceback
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_db_session
from database.models import RawData, ProcessedData, PredictionResult
from services.preprocessing_service import PreprocessingService
from services.feature_extraction_service import FeatureExtractionService
from services.dataset_service import DatasetService
from services.prediction_service import PredictionService
from utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DataPipeline:
    """Callytics → LightGBM 데이터 처리 파이프라인"""
    
    def __init__(self):
        self.preprocessing_service = PreprocessingService()
        self.feature_extraction_service = FeatureExtractionService()
        self.dataset_service = DatasetService()
        self.prediction_service = PredictionService()
    
    async def process_callytics_data(
        self, 
        callytics_json: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Callytics에서 받은 JSON 데이터를 완전히 처리
        
        Args:
            callytics_json: Callytics에서 받은 원본 JSON 데이터
            session_id: 세션 고유 ID
            
        Returns:
            처리 결과 및 예측 결과
        """
        try:
            logger.info(f"Starting pipeline for session {session_id}")
            
            # 1단계: 데이터 전처리 및 병합 (1_preprocessing_model_v3.py 로직)
            preprocessed_data = await self._step1_preprocessing(
                callytics_json, session_id
            )
            
            # 2단계: 특성 추출 (2_coloums_extraction_v3_json2csv.py 로직)
            extracted_features = await self._step2_feature_extraction(
                preprocessed_data, session_id
            )
            
            # 3단계: 데이터셋 생성 (3_make_dataset.py 로직)
            dataset_info = await self._step3_dataset_creation(
                extracted_features, session_id
            )
            
            # 4단계: 모델 예측 및 평가 (4_simple_model_v2.py 로직)
            prediction_result = await self._step4_prediction(
                dataset_info, session_id
            )
            
            # 결과 저장
            await self._save_results(session_id, prediction_result)
            
            logger.info(f"Pipeline completed for session {session_id}")
            
            return {
                "session_id": session_id,
                "status": "completed",
                "prediction": prediction_result,
                "processing_time": datetime.now().isoformat(),
                "pipeline_steps": {
                    "preprocessing": "completed",
                    "feature_extraction": "completed", 
                    "dataset_creation": "completed",
                    "prediction": "completed"
                }
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed for session {session_id}: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                "session_id": session_id,
                "status": "failed",
                "error": str(e),
                "processing_time": datetime.now().isoformat()
            }
    
    async def _step1_preprocessing(
        self, 
        callytics_json: Dict[str, Any], 
        session_id: str
    ) -> Dict[str, Any]:
        """1단계: 데이터 전처리 및 병합"""
        logger.info(f"Step 1: Preprocessing for session {session_id}")
        
        # 기존 1_preprocessing_model_v3.py의 로직을 함수화
        # ZIP 파일 해제 → Callytics JSON 직접 처리로 변경
        return await self.preprocessing_service.process_callytics_json(
            callytics_json, session_id
        )
    
    async def _step2_feature_extraction(
        self, 
        preprocessed_data: Dict[str, Any], 
        session_id: str
    ) -> Dict[str, Any]:
        """2단계: 텍스트 특성 추출"""
        logger.info(f"Step 2: Feature extraction for session {session_id}")
        
        # 기존 2_coloums_extraction_v3_json2csv.py의 로직을 함수화
        return await self.feature_extraction_service.extract_features(
            preprocessed_data, session_id
        )
    
    async def _step3_dataset_creation(
        self, 
        extracted_features: Dict[str, Any], 
        session_id: str
    ) -> Dict[str, Any]:
        """3단계: 학습용 데이터셋 생성"""
        logger.info(f"Step 3: Dataset creation for session {session_id}")
        
        # 기존 3_make_dataset.py의 로직을 함수화
        return await self.dataset_service.create_dataset(
            extracted_features, session_id
        )
    
    async def _step4_prediction(
        self, 
        dataset_info: Dict[str, Any], 
        session_id: str
    ) -> Dict[str, Any]:
        """4단계: LightGBM 모델 예측"""
        logger.info(f"Step 4: Prediction for session {session_id}")
        
        # 기존 4_simple_model_v2.py의 로직을 함수화
        return await self.prediction_service.predict(
            dataset_info, session_id
        )
    
    async def _save_results(
        self, 
        session_id: str, 
        prediction_result: Dict[str, Any]
    ) -> None:
        """처리 결과를 데이터베이스에 저장"""
        try:
            async with get_db_session() as db:
                # PredictionResult 테이블에 저장
                result = PredictionResult(
                    session_id=session_id,
                    prediction=prediction_result.get('prediction'),
                    confidence=prediction_result.get('confidence'),
                    features=json.dumps(prediction_result.get('features', {})),
                    model_version=prediction_result.get('model_version'),
                    created_at=datetime.now()
                )
                db.add(result)
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to save results for {session_id}: {str(e)}")
    
    async def get_processing_status(self, session_id: str) -> Dict[str, Any]:
        """세션의 처리 상태 조회"""
        try:
            async with get_db_session() as db:
                result = db.query(PredictionResult).filter(
                    PredictionResult.session_id == session_id
                ).first()
                
                if result:
                    return {
                        "session_id": session_id,
                        "status": "completed",
                        "prediction": result.prediction,
                        "confidence": result.confidence,
                        "created_at": result.created_at.isoformat()
                    }
                else:
                    return {
                        "session_id": session_id,
                        "status": "not_found"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get status for {session_id}: {str(e)}")
            return {
                "session_id": session_id,
                "status": "error",
                "error": str(e)
            }


# 싱글톤 인스턴스
pipeline = DataPipeline() 