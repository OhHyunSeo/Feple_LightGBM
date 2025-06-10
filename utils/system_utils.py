# -*- coding: utf-8 -*-
"""
system_utils.py
- 시스템 관련 공통 유틸리티
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any

class SystemUtils:
    """시스템 관련 유틸리티 클래스"""
    
    @staticmethod
    def is_windows() -> bool:
        """Windows 운영체제인지 확인합니다."""
        return os.name == 'nt'
    
    @staticmethod
    def is_linux() -> bool:
        """Linux 운영체제인지 확인합니다."""
        return platform.system().lower() == 'linux'
    
    @staticmethod
    def is_macos() -> bool:
        """macOS 운영체제인지 확인합니다."""
        return platform.system().lower() == 'darwin'
    
    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """
        시스템 정보를 반환합니다.
        
        Returns:
            시스템 정보 딕셔너리
        """
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': sys.version,
            'python_executable': sys.executable,
            'working_directory': os.getcwd()
        }
    
    @staticmethod
    def setup_environment_variables(env_vars: Dict[str, str]) -> Dict[str, str]:
        """
        환경 변수를 설정합니다.
        
        Args:
            env_vars: 설정할 환경 변수 딕셔너리
            
        Returns:
            업데이트된 환경 변수
        """
        env = os.environ.copy()
        env.update(env_vars)
        return env
    
    @staticmethod
    def setup_utf8_environment() -> Dict[str, str]:
        """
        UTF-8 환경을 설정합니다 (Windows 호환).
        
        Returns:
            UTF-8 환경 변수
        """
        env = os.environ.copy()
        env.update({
            'PYTHONIOENCODING': 'utf-8',
            'PYTHONLEGACYWINDOWSSTDIO': '1'
        })
        return env
    
    @staticmethod
    def set_windows_utf8_codepage() -> bool:
        """
        Windows에서 UTF-8 코드페이지를 설정합니다.
        
        Returns:
            설정 성공 여부
        """
        if not SystemUtils.is_windows():
            return True
        
        try:
            subprocess.run(['chcp', '65001'], 
                         shell=True, 
                         capture_output=True, 
                         check=False)
            return True
        except Exception:
            return False
    
    @staticmethod
    def run_command(command: Union[str, List[str]], 
                   working_dir: Optional[Union[str, Path]] = None,
                   env: Optional[Dict[str, str]] = None,
                   timeout: Optional[int] = None,
                   capture_output: bool = True,
                   encoding: str = 'utf-8',
                   shell: bool = False) -> Tuple[bool, str, str]:
        """
        시스템 명령을 실행합니다.
        
        Args:
            command: 실행할 명령
            working_dir: 작업 디렉토리
            env: 환경 변수
            timeout: 타임아웃 (초)
            capture_output: 출력 캡처 여부
            encoding: 인코딩
            shell: 셸 사용 여부
            
        Returns:
            (성공 여부, stdout, stderr)
        """
        try:
            if isinstance(command, str) and not shell:
                command = command.split()
            
            if env is None:
                env = SystemUtils.setup_utf8_environment()
            
            result = subprocess.run(
                command,
                cwd=working_dir,
                env=env,
                timeout=timeout,
                capture_output=capture_output,
                text=True,
                encoding=encoding,
                errors='ignore',
                shell=shell
            )
            
            success = result.returncode == 0
            stdout = result.stdout if result.stdout else ""
            stderr = result.stderr if result.stderr else ""
            
            return success, stdout, stderr
            
        except subprocess.TimeoutExpired:
            return False, "", f"명령 실행 시간 초과 ({timeout}초)"
        except FileNotFoundError:
            return False, "", f"명령을 찾을 수 없습니다: {command}"
        except Exception as e:
            return False, "", f"명령 실행 오류: {str(e)}"
    
    @staticmethod
    def run_python_script(script_path: Union[str, Path],
                         args: Optional[List[str]] = None,
                         working_dir: Optional[Union[str, Path]] = None,
                         timeout: Optional[int] = None) -> Tuple[bool, str, str]:
        """
        Python 스크립트를 실행합니다.
        
        Args:
            script_path: 스크립트 경로
            args: 스크립트 인자
            working_dir: 작업 디렉토리
            timeout: 타임아웃 (초)
            
        Returns:
            (성공 여부, stdout, stderr)
        """
        command = [sys.executable, str(script_path)]
        if args:
            command.extend(args)
        
        return SystemUtils.run_command(
            command=command,
            working_dir=working_dir,
            timeout=timeout
        )
    
    @staticmethod
    def check_python_requirements(requirements: List[str]) -> Tuple[bool, List[str]]:
        """
        Python 패키지 요구사항을 확인합니다.
        
        Args:
            requirements: 필요한 패키지 리스트
            
        Returns:
            (모든 요구사항 충족 여부, 누락된 패키지 리스트)
        """
        missing_packages = []
        
        for package in requirements:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        return len(missing_packages) == 0, missing_packages
    
    @staticmethod
    def get_available_memory_gb() -> float:
        """
        사용 가능한 메모리를 GB 단위로 반환합니다.
        
        Returns:
            사용 가능한 메모리 (GB)
        """
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.available / (1024 ** 3)  # GB 변환
        except ImportError:
            return 0.0
    
    @staticmethod
    def get_cpu_count() -> int:
        """
        CPU 코어 수를 반환합니다.
        
        Returns:
            CPU 코어 수
        """
        return os.cpu_count() or 1
    
    @staticmethod
    def get_disk_usage(path: Union[str, Path]) -> Dict[str, float]:
        """
        디스크 사용량을 반환합니다.
        
        Args:
            path: 확인할 경로
            
        Returns:
            디스크 사용량 정보 (GB 단위)
        """
        try:
            import shutil
            total, used, free = shutil.disk_usage(str(path))
            
            return {
                'total': total / (1024 ** 3),
                'used': used / (1024 ** 3),
                'free': free / (1024 ** 3),
                'usage_percent': (used / total) * 100
            }
        except Exception:
            return {'total': 0.0, 'used': 0.0, 'free': 0.0, 'usage_percent': 0.0}
    
    @staticmethod
    def kill_process_by_name(process_name: str) -> bool:
        """
        프로세스 이름으로 프로세스를 종료합니다.
        
        Args:
            process_name: 프로세스 이름
            
        Returns:
            종료 성공 여부
        """
        try:
            if SystemUtils.is_windows():
                command = f"taskkill /f /im {process_name}"
            else:
                command = f"pkill -f {process_name}"
            
            success, _, _ = SystemUtils.run_command(command, shell=True)
            return success
        except Exception:
            return False
    
    @staticmethod
    def find_processes_by_name(process_name: str) -> List[Dict[str, Any]]:
        """
        프로세스 이름으로 실행 중인 프로세스를 찾습니다.
        
        Args:
            process_name: 프로세스 이름
            
        Returns:
            프로세스 정보 리스트
        """
        try:
            import psutil
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if process_name.lower() in proc.info['name'].lower():
                        processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return processes
        except ImportError:
            return []
    
    @staticmethod
    def create_shortcut(target_path: Union[str, Path], 
                       shortcut_path: Union[str, Path],
                       description: str = "") -> bool:
        """
        바로가기를 생성합니다 (Windows only).
        
        Args:
            target_path: 대상 파일 경로
            shortcut_path: 바로가기 파일 경로
            description: 설명
            
        Returns:
            생성 성공 여부
        """
        if not SystemUtils.is_windows():
            return False
        
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = str(target_path)
            shortcut.Description = description
            shortcut.save()
            return True
        except ImportError:
            return False
        except Exception:
            return False
    
    @staticmethod
    def open_file_explorer(path: Union[str, Path]) -> bool:
        """
        파일 탐색기를 엽니다.
        
        Args:
            path: 열 경로
            
        Returns:
            열기 성공 여부
        """
        try:
            path = Path(path).resolve()
            
            if SystemUtils.is_windows():
                os.startfile(str(path))
            elif SystemUtils.is_macos():
                subprocess.run(['open', str(path)])
            else:  # Linux
                subprocess.run(['xdg-open', str(path)])
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_file_associations(extension: str) -> Optional[str]:
        """
        파일 확장자에 연결된 프로그램을 반환합니다.
        
        Args:
            extension: 파일 확장자 (.txt, .json 등)
            
        Returns:
            연결된 프로그램 경로 또는 None
        """
        try:
            if SystemUtils.is_windows():
                import winreg
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, extension) as key:
                    file_type = winreg.QueryValue(key, "")
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, 
                                  f"{file_type}\\shell\\open\\command") as key:
                    command = winreg.QueryValue(key, "")
                    return command.split('"')[1] if '"' in command else command.split()[0]
            else:
                # Linux/Mac에서는 xdg-mime 사용
                success, stdout, _ = SystemUtils.run_command(
                    ['xdg-mime', 'query', 'default', f'application/{extension[1:]}']
                )
                return stdout.strip() if success else None
        except Exception:
            return None
    
    @staticmethod
    def restart_application(script_path: Union[str, Path], 
                          args: Optional[List[str]] = None) -> bool:
        """
        애플리케이션을 재시작합니다.
        
        Args:
            script_path: 스크립트 경로
            args: 스크립트 인자
            
        Returns:
            재시작 성공 여부
        """
        try:
            command = [sys.executable, str(script_path)]
            if args:
                command.extend(args)
            
            # 새 프로세스로 실행
            subprocess.Popen(command, 
                           env=SystemUtils.setup_utf8_environment(),
                           cwd=os.getcwd())
            
            # 현재 프로세스 종료
            sys.exit(0)
            
        except Exception:
            return False
    
    @staticmethod
    def check_network_connectivity(host: str = "8.8.8.8", timeout: int = 3) -> bool:
        """
        네트워크 연결 상태를 확인합니다.
        
        Args:
            host: 확인할 호스트
            timeout: 타임아웃 (초)
            
        Returns:
            연결 가능 여부
        """
        try:
            import socket
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, 53))
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_environment_summary() -> Dict[str, Any]:
        """
        환경 요약 정보를 반환합니다.
        
        Returns:
            환경 요약 딕셔너리
        """
        system_info = SystemUtils.get_system_info()
        
        summary = {
            'system': {
                'platform': system_info['system'],
                'release': system_info['release'],
                'python_version': system_info['python_version'].split()[0]
            },
            'resources': {
                'cpu_cores': SystemUtils.get_cpu_count(),
                'available_memory_gb': SystemUtils.get_available_memory_gb()
            },
            'network': {
                'connectivity': SystemUtils.check_network_connectivity()
            }
        }
        
        # 디스크 사용량 추가
        try:
            disk_info = SystemUtils.get_disk_usage(os.getcwd())
            summary['disk'] = {
                'free_gb': disk_info['free'],
                'usage_percent': disk_info['usage_percent']
            }
        except Exception:
            summary['disk'] = {'free_gb': 0.0, 'usage_percent': 0.0}
        
        return summary 