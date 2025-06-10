# -*- coding: utf-8 -*-
"""
file_utils.py
- 파일 처리 관련 공통 유틸리티
"""

import os
import re
import glob
import time
from pathlib import Path
from typing import List, Dict, Optional, Union

class FileUtils:
    """파일 처리 관련 유틸리티 클래스"""
    
    @staticmethod
    def detect_file_type(filename: str, type_mappings: Dict[str, List[str]]) -> Optional[str]:
        """
        파일명에서 데이터 타입을 감지합니다.
        
        Args:
            filename: 파일명
            type_mappings: 타입별 키워드 매핑
            
        Returns:
            감지된 파일 타입 또는 None
        """
        filename_lower = filename.lower()
        
        for data_type, keywords in type_mappings.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return data_type
        
        return None
    
    @staticmethod
    def extract_session_id(filename: str) -> str:
        """
        파일명에서 세션 ID를 추출합니다.
        
        Args:
            filename: 파일명
            
        Returns:
            추출된 세션 ID
        """
        # 확장자 제거
        name_without_ext = filename.replace('.json', '')
        parts = name_without_ext.split('_')
        
        # 숫자로만 이루어진 부분을 세션 ID로 간주
        for part in parts:
            if part.isdigit():
                return part
        
        # 정규식으로 숫자 추출
        numbers = re.findall(r'\d+', filename)
        if numbers:
            return numbers[0]  # 첫 번째 숫자를 세션 ID로 사용
        
        return 'unknown'
    
    @staticmethod
    def extract_file_number(filename: str) -> int:
        """
        파일명에서 파일 번호를 추출합니다 (정렬용).
        
        Args:
            filename: 파일명
            
        Returns:
            파일 번호
        """
        numbers = re.findall(r'\d+', filename)
        if len(numbers) >= 2:
            return int(numbers[-1])  # 마지막 숫자를 파일 번호로 사용
        elif len(numbers) == 1:
            return int(numbers[0])
        return 0
    
    @staticmethod
    def wait_for_file_complete(file_path: Union[str, Path], timeout: int = 30) -> bool:
        """
        파일이 완전히 생성될 때까지 대기합니다.
        
        Args:
            file_path: 파일 경로
            timeout: 타임아웃 (초)
            
        Returns:
            파일 생성 완료 여부
        """
        file_path = Path(file_path)
        start_time = time.time()
        last_size = 0
        
        while time.time() - start_time < timeout:
            try:
                if not file_path.exists():
                    time.sleep(0.5)
                    continue
                    
                current_size = file_path.stat().st_size
                if current_size == last_size and current_size > 0:
                    time.sleep(1)  # 1초 더 대기
                    if file_path.stat().st_size == current_size:
                        return True
                last_size = current_size
                time.sleep(0.5)
            except OSError:
                time.sleep(0.5)
                continue
        
        return False
    
    @staticmethod
    def find_files_by_pattern(directory: Union[str, Path], pattern: str) -> List[Path]:
        """
        패턴에 매치되는 파일들을 찾습니다.
        
        Args:
            directory: 검색할 디렉토리
            pattern: 파일 패턴 (glob 형식)
            
        Returns:
            매치된 파일 리스트
        """
        directory = Path(directory)
        if not directory.exists():
            return []
        
        search_pattern = directory / pattern
        return [Path(f) for f in glob.glob(str(search_pattern))]
    
    @staticmethod
    def ensure_directory(directory: Union[str, Path]) -> Path:
        """
        디렉토리가 존재하지 않으면 생성합니다.
        
        Args:
            directory: 디렉토리 경로
            
        Returns:
            생성된 디렉토리 경로
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        return directory
    
    @staticmethod
    def get_file_size_mb(file_path: Union[str, Path]) -> float:
        """
        파일 크기를 MB 단위로 반환합니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파일 크기 (MB)
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return 0.0
        
        size_bytes = file_path.stat().st_size
        return size_bytes / (1024 * 1024)
    
    @staticmethod
    def is_file_accessible(file_path: Union[str, Path]) -> bool:
        """
        파일이 접근 가능한지 확인합니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            접근 가능 여부
        """
        file_path = Path(file_path)
        try:
            return file_path.exists() and os.access(str(file_path), os.R_OK)
        except (OSError, PermissionError):
            return False
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """
        파일명에서 특수문자를 제거하여 안전한 파일명을 만듭니다.
        
        Args:
            filename: 원본 파일명
            
        Returns:
            정리된 파일명
        """
        # 위험한 문자들을 언더스코어로 대체
        cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 연속된 언더스코어를 하나로 통합
        cleaned = re.sub(r'_+', '_', cleaned)
        # 앞뒤 언더스코어 제거
        cleaned = cleaned.strip('_')
        
        return cleaned if cleaned else 'unnamed_file'
    
    @staticmethod
    def backup_file(file_path: Union[str, Path], backup_suffix: str = '.bak') -> Optional[Path]:
        """
        파일을 백업합니다.
        
        Args:
            file_path: 백업할 파일 경로
            backup_suffix: 백업 파일 접미사
            
        Returns:
            백업 파일 경로 또는 None (실패시)
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return None
        
        backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
        
        try:
            import shutil
            shutil.copy2(str(file_path), str(backup_path))
            return backup_path
        except Exception:
            return None
    
    @staticmethod
    def get_directory_size(directory: Union[str, Path]) -> float:
        """
        디렉토리 전체 크기를 MB 단위로 반환합니다.
        
        Args:
            directory: 디렉토리 경로
            
        Returns:
            디렉토리 크기 (MB)
        """
        directory = Path(directory)
        if not directory.exists():
            return 0.0
        
        total_size = 0
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except (OSError, PermissionError):
            pass
        
        return total_size / (1024 * 1024)
    
    @staticmethod
    def count_files_by_extension(directory: Union[str, Path]) -> Dict[str, int]:
        """
        디렉토리의 확장자별 파일 개수를 반환합니다.
        
        Args:
            directory: 디렉토리 경로
            
        Returns:
            확장자별 파일 개수 딕셔너리
        """
        directory = Path(directory)
        if not directory.exists():
            return {}
        
        extension_counts = {}
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    if not ext:
                        ext = 'no_extension'
                    extension_counts[ext] = extension_counts.get(ext, 0) + 1
        except (OSError, PermissionError):
            pass
        
        return extension_counts 