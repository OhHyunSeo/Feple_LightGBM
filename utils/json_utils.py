# -*- coding: utf-8 -*-
"""
json_utils.py
- JSON 처리 관련 공통 유틸리티
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from collections import defaultdict

class JSONUtils:
    """JSON 처리 관련 유틸리티 클래스"""
    
    @staticmethod
    def load_json(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[Any]:
        """
        JSON 파일을 로드합니다.
        
        Args:
            file_path: JSON 파일 경로
            encoding: 파일 인코딩
            
        Returns:
            JSON 데이터 또는 None (실패시)
        """
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"❌ JSON 로드 실패 {file_path}: {e}")
            return None
    
    @staticmethod
    def save_json(data: Any, file_path: Union[str, Path], encoding: str = 'utf-8', 
                  indent: int = 2, ensure_ascii: bool = False) -> bool:
        """
        데이터를 JSON 파일로 저장합니다.
        
        Args:
            data: 저장할 데이터
            file_path: 저장할 파일 경로
            encoding: 파일 인코딩
            indent: 들여쓰기 크기
            ensure_ascii: ASCII 문자만 사용할지 여부
            
        Returns:
            저장 성공 여부
        """
        file_path = Path(file_path)
        
        try:
            # 디렉토리 생성
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
            return True
        except (OSError, TypeError) as e:
            print(f"❌ JSON 저장 실패 {file_path}: {e}")
            return False
    
    @staticmethod
    def normalize_json_data(data: Any) -> Any:
        """
        JSON 데이터를 정규화합니다 (리스트인 경우 첫 번째 요소 반환).
        
        Args:
            data: JSON 데이터
            
        Returns:
            정규화된 데이터
        """
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return data
    
    @staticmethod
    def extract_field(data: Dict[str, Any], field_name: str, default: Any = None) -> Any:
        """
        JSON 데이터에서 특정 필드를 안전하게 추출합니다.
        
        Args:
            data: JSON 데이터
            field_name: 필드명
            default: 기본값
            
        Returns:
            필드 값 또는 기본값
        """
        if not isinstance(data, dict):
            return default
        return data.get(field_name, default)
    
    @staticmethod
    def merge_instructions_data(files: List[Union[str, Path]], 
                               tuning_type: str) -> List[Dict[str, Any]]:
        """
        여러 JSON 파일의 instructions 데이터를 병합합니다.
        
        Args:
            files: JSON 파일 경로 리스트
            tuning_type: 튜닝 타입 (분류, 요약, 질의응답)
            
        Returns:
            병합된 데이터 리스트
        """
        merged_data = []
        content_groups = {}
        
        for file_path in files:
            data = JSONUtils.load_json(file_path)
            if not data:
                continue
            
            # 데이터 정규화
            data = JSONUtils.normalize_json_data(data)
            
            # consulting_content 기준으로 그룹화
            content = JSONUtils.extract_field(data, 'consulting_content', '')
            
            if content not in content_groups:
                # 기본 메타데이터 저장 (instructions, input 제외)
                base_data = {k: v for k, v in data.items() 
                           if k not in ('instructions', 'input')}
                content_groups[content] = {
                    'base': base_data,
                    'data': []
                }
            
            # instructions 데이터 병합
            instructions = JSONUtils.extract_field(data, 'instructions', [])
            if instructions:
                instruction_data = JSONUtils.extract_field(instructions[0], 'data', [])
                content_groups[content]['data'].extend(instruction_data)
        
        # 최종 객체 생성
        for content, info in content_groups.items():
            obj = info['base'].copy()
            obj['consulting_content'] = content
            obj['instructions'] = [{
                'tuning_type': tuning_type,
                'data': info['data']
            }]
            merged_data.append(obj)
        
        return merged_data
    
    @staticmethod
    def remove_input_fields_recursive(obj: Any) -> None:
        """
        JSON 객체에서 'input' 필드를 재귀적으로 제거합니다.
        
        Args:
            obj: JSON 객체
        """
        if isinstance(obj, dict):
            obj.pop('input', None)
            for value in obj.values():
                JSONUtils.remove_input_fields_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                JSONUtils.remove_input_fields_recursive(item)
    
    @staticmethod
    def group_files_by_session(files: List[Union[str, Path]], 
                             extract_session_func) -> Dict[str, List[Path]]:
        """
        파일들을 세션별로 그룹화합니다.
        
        Args:
            files: 파일 경로 리스트
            extract_session_func: 세션 ID 추출 함수
            
        Returns:
            세션별 파일 그룹
        """
        sessions = defaultdict(list)
        
        for file_path in files:
            file_path = Path(file_path)
            session_id = extract_session_func(file_path.name)
            sessions[session_id].append(file_path)
        
        return dict(sessions)
    
    @staticmethod
    def validate_json_structure(data: Dict[str, Any], 
                              required_fields: List[str]) -> tuple[bool, List[str]]:
        """
        JSON 데이터 구조를 검증합니다.
        
        Args:
            data: 검증할 JSON 데이터
            required_fields: 필수 필드 리스트
            
        Returns:
            (검증 성공 여부, 누락된 필드 리스트)
        """
        if not isinstance(data, dict):
            return False, ['데이터가 딕셔너리 형태가 아닙니다']
        
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        return len(missing_fields) == 0, missing_fields
    
    @staticmethod
    def extract_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        JSON 데이터에서 메타데이터를 추출합니다.
        
        Args:
            data: JSON 데이터
            
        Returns:
            메타데이터 딕셔너리
        """
        metadata_fields = [
            'session_id', 'source', 'source_id', 'consulting_category',
            'consulting_time', 'consulting_turns', 'consulting_length',
            'customer_id', 'counselor_id', 'start_time', 'end_time', 'category'
        ]
        
        metadata = {}
        for field in metadata_fields:
            if field in data:
                metadata[field] = data[field]
        
        return metadata
    
    @staticmethod
    def clean_json_data(data: Dict[str, Any], 
                       fields_to_remove: List[str] = None) -> Dict[str, Any]:
        """
        JSON 데이터를 정리합니다 (불필요한 필드 제거).
        
        Args:
            data: 원본 JSON 데이터
            fields_to_remove: 제거할 필드 리스트
            
        Returns:
            정리된 JSON 데이터
        """
        if fields_to_remove is None:
            fields_to_remove = ['input']
        
        cleaned_data = {}
        for key, value in data.items():
            if key not in fields_to_remove:
                if isinstance(value, dict):
                    cleaned_data[key] = JSONUtils.clean_json_data(value, fields_to_remove)
                elif isinstance(value, list):
                    cleaned_data[key] = [
                        JSONUtils.clean_json_data(item, fields_to_remove) 
                        if isinstance(item, dict) else item 
                        for item in value
                    ]
                else:
                    cleaned_data[key] = value
        
        return cleaned_data
    
    @staticmethod
    def merge_json_files(file_paths: List[Union[str, Path]], 
                        output_path: Union[str, Path],
                        merge_key: str = 'data') -> bool:
        """
        여러 JSON 파일을 하나로 병합합니다.
        
        Args:
            file_paths: 병합할 JSON 파일 경로 리스트
            output_path: 출력 파일 경로
            merge_key: 병합할 키
            
        Returns:
            병합 성공 여부
        """
        merged_data = {merge_key: []}
        
        for file_path in file_paths:
            data = JSONUtils.load_json(file_path)
            if data:
                if isinstance(data, list):
                    merged_data[merge_key].extend(data)
                elif isinstance(data, dict):
                    if merge_key in data:
                        if isinstance(data[merge_key], list):
                            merged_data[merge_key].extend(data[merge_key])
                        else:
                            merged_data[merge_key].append(data[merge_key])
                    else:
                        merged_data[merge_key].append(data)
        
        return JSONUtils.save_json(merged_data, output_path)
    
    @staticmethod
    def pretty_print_json(data: Any, indent: int = 2) -> str:
        """
        JSON 데이터를 보기 좋게 포맷팅합니다.
        
        Args:
            data: JSON 데이터
            indent: 들여쓰기 크기
            
        Returns:
            포맷팅된 JSON 문자열
        """
        try:
            return json.dumps(data, ensure_ascii=False, indent=indent)
        except (TypeError, ValueError):
            return str(data) 