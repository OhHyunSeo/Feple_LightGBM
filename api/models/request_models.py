"""
API 요청 모델 정의
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime


class CallyticsDataRequest(BaseModel):
    """Callytics에서 받는 JSON 데이터 요청 모델"""
    
    session_id: Optional[str] = Field(
        None, 
        description="세션 고유 ID (없으면 자동 생성)"
    )
    
    data: Dict[str, Any] = Field(
        ..., 
        description="Callytics에서 전송하는 상담 데이터 JSON",
        example={
            "session_id": "40001",
            "consulting_content": "상담사: 안녕하세요, 광진구청입니다...\n고객: 네, 안녕하세요...",
            "instructions": [
                {
                    "tuning_type": "분류",
                    "data": [
                        {
                            "task_category": "상담 결과",
                            "output": "만족"
                        }
                    ]
                }
            ]
        }
    )
    
    processing_mode: Literal["realtime", "background"] = Field(
        "background",
        description="처리 모드 - realtime: 즉시 처리, background: 백그라운드 처리"
    )
    
    priority: Optional[int] = Field(
        1,
        ge=1,
        le=5,
        description="처리 우선순위 (1=낮음, 5=높음)"
    )
    
    callback_url: Optional[str] = Field(
        None,
        description="처리 완료 시 결과를 전송할 콜백 URL"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="추가 메타데이터"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "40001",
                "data": {
                    "session_id": "40001",
                    "consulting_content": "상담사: 안녕하세요...\n고객: 네...",
                    "instructions": [
                        {
                            "tuning_type": "분류",
                            "data": [
                                {
                                    "task_category": "상담 결과",
                                    "output": "만족"
                                }
                            ]
                        }
                    ]
                },
                "processing_mode": "realtime",
                "priority": 3,
                "callback_url": "https://callytics.example.com/webhook/lightgbm-result"
            }
        }


class BatchProcessRequest(BaseModel):
    """배치 처리 요청 모델"""
    
    requests: List[CallyticsDataRequest] = Field(
        ...,
        description="처리할 여러 세션 데이터 목록"
    )
    
    batch_id: Optional[str] = Field(
        None,
        description="배치 작업 ID (없으면 자동 생성)"
    )
    
    max_concurrent: Optional[int] = Field(
        5,
        ge=1,
        le=20,
        description="최대 동시 처리 세션 수"
    )


class ModelRetrainRequest(BaseModel):
    """모델 재학습 요청 모델"""
    
    training_data_source: Literal["database", "file", "api"] = Field(
        "database",
        description="학습 데이터 소스"
    )
    
    data_path: Optional[str] = Field(
        None,
        description="파일 경로 (training_data_source가 'file'인 경우)"
    )
    
    hyperparameters: Optional[Dict[str, Any]] = Field(
        None,
        description="사용자 정의 하이퍼파라미터"
    )
    
    validation_split: Optional[float] = Field(
        0.2,
        ge=0.1,
        le=0.4,
        description="검증 데이터 비율"
    )


class DataExportRequest(BaseModel):
    """데이터 내보내기 요청 모델"""
    
    session_ids: List[str] = Field(
        ...,
        description="내보낼 세션 ID 목록"
    )
    
    export_format: Literal["json", "csv", "parquet"] = Field(
        "json",
        description="내보내기 형식"
    )
    
    include_features: bool = Field(
        True,
        description="추출된 특성 포함 여부"
    )
    
    include_raw_data: bool = Field(
        False,
        description="원본 데이터 포함 여부"
    )
    
    destination: Literal["file", "url", "email"] = Field(
        "file",
        description="내보내기 대상"
    )
    
    destination_config: Optional[Dict[str, Any]] = Field(
        None,
        description="대상별 설정 (URL, 이메일 주소 등)"
    )


class HealthCheckRequest(BaseModel):
    """헬스체크 요청 모델"""
    
    check_database: bool = Field(
        True,
        description="데이터베이스 연결 확인"
    )
    
    check_model: bool = Field(
        True,
        description="모델 로딩 상태 확인"
    )
    
    check_external_apis: bool = Field(
        False,
        description="외부 API 연결 확인"
    ) 