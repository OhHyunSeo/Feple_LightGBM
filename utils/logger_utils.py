# -*- coding: utf-8 -*-
"""
logger_utils.py
- 로깅 관련 공통 유틸리티
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Union, Dict, Any
from datetime import datetime

class LoggerUtils:
    """로깅 관련 유틸리티 클래스"""
    
    _loggers: Dict[str, logging.Logger] = {}
    
    @classmethod
    def setup_logger(cls, name: str, 
                    log_file: Optional[Union[str, Path]] = None,
                    level: str = 'INFO',
                    format_string: Optional[str] = None,
                    console_output: bool = True,
                    file_output: bool = True,
                    max_file_size: int = 10 * 1024 * 1024,  # 10MB
                    backup_count: int = 5,
                    encoding: str = 'utf-8') -> logging.Logger:
        """
        로거를 설정합니다.
        
        Args:
            name: 로거 이름
            log_file: 로그 파일 경로
            level: 로그 레벨
            format_string: 로그 포맷 문자열
            console_output: 콘솔 출력 여부
            file_output: 파일 출력 여부
            max_file_size: 최대 파일 크기 (바이트)
            backup_count: 백업 파일 개수
            encoding: 파일 인코딩
            
        Returns:
            설정된 로거
        """
        # 이미 설정된 로거가 있으면 반환
        if name in cls._loggers:
            return cls._loggers[name]
        
        # 로거 생성
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # 기존 핸들러 제거 (중복 방지)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 포맷터 설정
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(format_string)
        
        # 콘솔 핸들러 추가
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # 파일 핸들러 추가
        if file_output and log_file:
            log_file = Path(log_file)
            
            # 로그 디렉토리 생성
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 회전 파일 핸들러 사용
            file_handler = logging.handlers.RotatingFileHandler(
                str(log_file),
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding=encoding
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # 로거 캐시에 저장
        cls._loggers[name] = logger
        
        return logger
    
    @classmethod
    def get_logger(cls, name: str) -> Optional[logging.Logger]:
        """
        기존에 설정된 로거를 반환합니다.
        
        Args:
            name: 로거 이름
            
        Returns:
            로거 또는 None
        """
        return cls._loggers.get(name)
    
    @classmethod
    def setup_pipeline_logger(cls, pipeline_name: str, 
                            log_dir: Union[str, Path] = "logs") -> logging.Logger:
        """
        파이프라인용 로거를 설정합니다.
        
        Args:
            pipeline_name: 파이프라인 이름
            log_dir: 로그 디렉토리
            
        Returns:
            파이프라인 로거
        """
        log_dir = Path(log_dir)
        log_file = log_dir / f"{pipeline_name}_{datetime.now().strftime('%Y%m%d')}.log"
        
        return cls.setup_logger(
            name=f"pipeline.{pipeline_name}",
            log_file=log_file,
            level='INFO',
            format_string='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
        )
    
    @classmethod
    def setup_monitoring_logger(cls, log_dir: Union[str, Path] = "logs") -> logging.Logger:
        """
        모니터링용 로거를 설정합니다.
        
        Args:
            log_dir: 로그 디렉토리
            
        Returns:
            모니터링 로거
        """
        log_dir = Path(log_dir)
        log_file = log_dir / "monitoring.log"
        
        return cls.setup_logger(
            name="monitoring",
            log_file=log_file,
            level='INFO',
            format_string='%(asctime)s - %(levelname)s - %(message)s',
            max_file_size=50 * 1024 * 1024,  # 50MB
            backup_count=10
        )
    
    @staticmethod
    def log_function_call(logger: logging.Logger, func_name: str, 
                         args: Optional[Dict[str, Any]] = None,
                         level: str = 'DEBUG') -> None:
        """
        함수 호출을 로깅합니다.
        
        Args:
            logger: 로거
            func_name: 함수명
            args: 함수 인자
            level: 로그 레벨
        """
        log_level = getattr(logging, level.upper())
        
        if args:
            arg_str = ', '.join([f"{k}={v}" for k, v in args.items()])
            logger.log(log_level, f"호출: {func_name}({arg_str})")
        else:
            logger.log(log_level, f"호출: {func_name}()")
    
    @staticmethod
    def log_execution_time(logger: logging.Logger, func_name: str, 
                          execution_time: float, level: str = 'INFO') -> None:
        """
        함수 실행 시간을 로깅합니다.
        
        Args:
            logger: 로거
            func_name: 함수명
            execution_time: 실행 시간 (초)
            level: 로그 레벨
        """
        log_level = getattr(logging, level.upper())
        logger.log(log_level, f"완료: {func_name} (실행시간: {execution_time:.2f}초)")
    
    @staticmethod
    def log_error_with_traceback(logger: logging.Logger, error: Exception, 
                               context: str = "") -> None:
        """
        에러와 트레이스백을 로깅합니다.
        
        Args:
            logger: 로거
            error: 예외 객체
            context: 에러 컨텍스트
        """
        import traceback
        
        error_msg = f"❌ 오류 발생"
        if context:
            error_msg += f" - {context}"
        error_msg += f": {str(error)}"
        
        logger.error(error_msg)
        logger.error(f"트레이스백:\n{traceback.format_exc()}")
    
    @staticmethod
    def log_file_operation(logger: logging.Logger, operation: str, 
                          file_path: Union[str, Path], 
                          success: bool = True, 
                          details: str = "") -> None:
        """
        파일 작업을 로깅합니다.
        
        Args:
            logger: 로거
            operation: 작업 종류 (읽기, 쓰기, 삭제 등)
            file_path: 파일 경로
            success: 성공 여부
            details: 추가 세부사항
        """
        status = "✅" if success else "❌"
        message = f"{status} 파일 {operation}: {file_path}"
        
        if details:
            message += f" - {details}"
        
        if success:
            logger.info(message)
        else:
            logger.error(message)
    
    @staticmethod
    def log_progress(logger: logging.Logger, current: int, total: int, 
                    task_name: str = "진행") -> None:
        """
        진행 상황을 로깅합니다.
        
        Args:
            logger: 로거
            current: 현재 진행량
            total: 전체 작업량
            task_name: 작업명
        """
        if total > 0:
            percentage = (current / total) * 100
            logger.info(f"📊 {task_name}: {current}/{total} ({percentage:.1f}%)")
        else:
            logger.info(f"📊 {task_name}: {current}개 완료")
    
    @staticmethod
    def log_system_info(logger: logging.Logger) -> None:
        """
        시스템 정보를 로깅합니다.
        
        Args:
            logger: 로거
        """
        import platform
        import sys
        
        logger.info("="*60)
        logger.info("🖥️ 시스템 정보")
        logger.info("="*60)
        logger.info(f"운영체제: {platform.system()} {platform.release()}")
        logger.info(f"Python 버전: {sys.version}")
        logger.info(f"작업 디렉토리: {os.getcwd()}")
        logger.info("="*60)
    
    @staticmethod
    def create_performance_logger(name: str, log_dir: Union[str, Path] = "logs") -> logging.Logger:
        """
        성능 측정용 로거를 생성합니다.
        
        Args:
            name: 로거 이름
            log_dir: 로그 디렉토리
            
        Returns:
            성능 로거
        """
        log_dir = Path(log_dir)
        log_file = log_dir / f"performance_{name}_{datetime.now().strftime('%Y%m%d')}.log"
        
        return LoggerUtils.setup_logger(
            name=f"performance.{name}",
            log_file=log_file,
            level='INFO',
            format_string='%(asctime)s - %(message)s'
        )
    
    @staticmethod
    def log_configuration(logger: logging.Logger, config: Dict[str, Any]) -> None:
        """
        설정 정보를 로깅합니다.
        
        Args:
            logger: 로거
            config: 설정 딕셔너리
        """
        logger.info("⚙️ 설정 정보:")
        for key, value in config.items():
            logger.info(f"   {key}: {value}")
    
    @classmethod
    def cleanup_old_logs(cls, log_dir: Union[str, Path], days_to_keep: int = 30) -> None:
        """
        오래된 로그 파일을 정리합니다.
        
        Args:
            log_dir: 로그 디렉토리
            days_to_keep: 보관할 일수
        """
        log_dir = Path(log_dir)
        if not log_dir.exists():
            return
        
        import time
        current_time = time.time()
        cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
        
        deleted_count = 0
        for log_file in log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except OSError:
                    pass
        
        if deleted_count > 0:
            print(f"🗑️ {deleted_count}개의 오래된 로그 파일을 삭제했습니다.")

# 장식자 함수들
def log_execution_time(logger: logging.Logger):
    """함수 실행 시간 로깅 장식자"""
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                LoggerUtils.log_execution_time(logger, func.__name__, execution_time)
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                LoggerUtils.log_error_with_traceback(logger, e, f"{func.__name__} (실행시간: {execution_time:.2f}초)")
                raise
        
        return wrapper
    return decorator

def log_function_calls(logger: logging.Logger, level: str = 'DEBUG'):
    """함수 호출 로깅 장식자"""
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 인자 정보 수집 (보안상 중요하지 않은 정보만)
            arg_info = {}
            if args:
                arg_info['args_count'] = len(args)
            if kwargs:
                # 민감한 정보 제외
                safe_kwargs = {k: v for k, v in kwargs.items() 
                              if not any(sensitive in k.lower() 
                                       for sensitive in ['password', 'token', 'key', 'secret'])}
                arg_info.update(safe_kwargs)
            
            LoggerUtils.log_function_call(logger, func.__name__, arg_info, level)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator 