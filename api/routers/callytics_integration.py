"""
Callytics 통합 API 라우터
Callytics에서 JSON 데이터를 받아 LightGBM 파이프라인으로 처리
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
import uuid
from datetime import datetime

from services.data_pipeline import pipeline
from api.models.request_models import CallyticsDataRequest
from api.models.response_models import ProcessingResponse, StatusResponse
from utils.auth import verify_api_key  # API 키 인증

router = APIRouter(prefix="/api/v1/callytics", tags=["Callytics Integration"])
logger = logging.getLogger(__name__)


@router.post("/process-data", response_model=ProcessingResponse)
async def process_callytics_data(
    request: CallyticsDataRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Callytics에서 받은 JSON 데이터를 처리
    
    이 엔드포인트는 Callytics 모델에서 호출되어:
    1. JSON 데이터를 받아
    2. 1-4단계 파이프라인을 실행하고
    3. 예측 결과를 반환합니다
    """
    try:
        # 세션 ID가 없으면 자동 생성
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"Received data from Callytics for session {session_id}")
        
        # 실시간 처리 vs 백그라운드 처리 선택
        if request.processing_mode == "realtime":
            # 실시간 처리 (빠른 응답 필요)
            result = await pipeline.process_callytics_data(
                request.data, session_id
            )
            
            return ProcessingResponse(
                session_id=session_id,
                status=result["status"],
                message="Processing completed",
                prediction_result=result.get("prediction"),
                processing_time=result.get("processing_time")
            )
            
        else:
            # 백그라운드 처리 (비동기)
            background_tasks.add_task(
                pipeline.process_callytics_data,
                request.data, 
                session_id
            )
            
            return ProcessingResponse(
                session_id=session_id,
                status="processing",
                message="Data received, processing in background",
                processing_time=datetime.now().isoformat()
            )
            
    except Exception as e:
        logger.error(f"Failed to process Callytics data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )


@router.get("/status/{session_id}", response_model=StatusResponse)
async def get_processing_status(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    특정 세션의 처리 상태 및 결과 조회
    Callytics에서 처리 완료 여부를 확인할 때 사용
    """
    try:
        status = await pipeline.get_processing_status(session_id)
        
        return StatusResponse(
            session_id=session_id,
            status=status["status"],
            prediction=status.get("prediction"),
            confidence=status.get("confidence"),
            created_at=status.get("created_at"),
            error=status.get("error")
        )
        
    except Exception as e:
        logger.error(f"Failed to get status for {session_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Status check failed: {str(e)}"
        )


@router.post("/batch-process")
async def batch_process_callytics_data(
    requests: List[CallyticsDataRequest],
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    여러 세션을 배치로 처리
    대량 데이터 처리 시 사용
    """
    try:
        session_ids = []
        
        for request in requests:
            session_id = request.session_id or str(uuid.uuid4())
            session_ids.append(session_id)
            
            # 각 세션을 백그라운드에서 처리
            background_tasks.add_task(
                pipeline.process_callytics_data,
                request.data,
                session_id
            )
        
        return JSONResponse({
            "message": f"Batch processing started for {len(session_ids)} sessions",
            "session_ids": session_ids,
            "status": "processing"
        })
        
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch processing failed: {str(e)}"
        )


@router.get("/results/{session_id}")
async def get_detailed_results(
    session_id: str,
    include_features: bool = False,
    api_key: str = Depends(verify_api_key)
):
    """
    세션의 상세 처리 결과 조회
    - 예측 결과
    - 신뢰도 점수  
    - 추출된 특성들 (옵션)
    - 처리 단계별 정보
    """
    try:
        # 데이터베이스에서 상세 결과 조회
        detailed_result = await pipeline.get_detailed_results(
            session_id, include_features
        )
        
        if not detailed_result:
            raise HTTPException(
                status_code=404,
                detail=f"Results not found for session {session_id}"
            )
            
        return detailed_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get detailed results for {session_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve results: {str(e)}"
        )


@router.post("/webhook/notify")
async def notify_callytics_completion(
    session_id: str,
    callback_url: str,
    api_key: str = Depends(verify_api_key)
):
    """
    처리 완료 시 Callytics로 웹훅 전송
    완료 알림이 필요한 경우 사용
    """
    try:
        # 처리 완료 시 Callytics에 결과 전송하는 로직
        success = await pipeline.send_results_to_callytics(
            session_id, callback_url
        )
        
        if success:
            return {"message": "Notification sent successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send notification"
            )
            
    except Exception as e:
        logger.error(f"Webhook notification failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Webhook failed: {str(e)}"
        ) 