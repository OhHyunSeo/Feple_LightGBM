# -*- coding: utf-8 -*-
"""
1_preprocessing_unified.py
- 통합 data 폴더에서 파일명 기반으로 분류/요약/질의응답 처리
- 파일명 패턴: 분류_세션ID_번호.json, 요약_세션ID_번호.json, 질의응답_세션ID_번호.json
"""

import os
import glob
import json
from collections import defaultdict
from tqdm import tqdm

class UnifiedPreprocessor:
    """통합 전처리기"""
    
    def __init__(self, input_dir="data", output_base="json_merge"):
        self.input_dir = input_dir
        self.output_base = output_base
        
        # 출력 폴더 설정
        self.output_dirs = {
            '분류': f'{output_base}/classification_merge_output',
            '요약': f'{output_base}/summary_merge_output', 
            '질의응답': f'{output_base}/qa_merge_output'
        }
        
        # 출력 폴더 생성
        for out_dir in self.output_dirs.values():
            os.makedirs(out_dir, exist_ok=True)
        
        # 파일명 패턴별 매핑
        self.type_mappings = {
            '분류': ['분류', 'classification', 'class'],
            '요약': ['요약', 'summary', 'sum'],
            '질의응답': ['질의응답', 'qa', 'qna', 'question']
        }
    
    def detect_file_type(self, filename):
        """파일명에서 데이터 타입 감지"""
        filename_lower = filename.lower()
        
        for data_type, keywords in self.type_mappings.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return data_type
        
        return None
    
    def extract_session_id(self, filename):
        """파일명에서 세션 ID 추출"""
        # 파일명 패턴: 분류_세션ID_번호.json 또는 세션ID_분류_번호.json 등
        parts = filename.replace('.json', '').split('_')
        
        # 숫자로만 이루어진 부분을 세션 ID로 간주
        for part in parts:
            if part.isdigit():
                return part
        
        # 숫자가 없으면 파일명 전체에서 숫자 추출
        import re
        numbers = re.findall(r'\d+', filename)
        if numbers:
            return numbers[0]  # 첫 번째 숫자를 세션 ID로 사용
        
        return 'unknown'
    
    def extract_file_number(self, filename):
        """파일명에서 파일 번호 추출 (정렬용)"""
        import re
        numbers = re.findall(r'\d+', filename)
        if len(numbers) >= 2:
            return int(numbers[-1])  # 마지막 숫자를 파일 번호로 사용
        elif len(numbers) == 1:
            return int(numbers[0])
        return 0
    
    def group_files_by_type_and_session(self):
        """파일들을 타입과 세션별로 그룹화"""
        print(f"📁 입력 폴더 스캔: {self.input_dir}")
        
        grouped = {
            '분류': defaultdict(list),
            '요약': defaultdict(list),
            '질의응답': defaultdict(list)
        }
        
        # JSON 파일 스캔
        pattern = os.path.join(self.input_dir, '*.json')
        all_files = glob.glob(pattern)
        
        print(f"📄 발견된 JSON 파일: {len(all_files)}개")
        
        for filepath in all_files:
            filename = os.path.basename(filepath)
            
            # 파일 타입 감지
            file_type = self.detect_file_type(filename)
            if not file_type:
                print(f"⚠️ 타입을 감지할 수 없는 파일: {filename}")
                continue
            
            # 세션 ID 추출
            session_id = self.extract_session_id(filename)
            
            # 그룹에 추가
            grouped[file_type][session_id].append(filepath)
            
            print(f"✅ {file_type} | 세션 {session_id} | {filename}")
        
        # 그룹화 결과 출력
        for data_type, sessions in grouped.items():
            print(f"\n📊 {data_type}: {len(sessions)}개 세션")
            for session_id, files in sessions.items():
                print(f"   세션 {session_id}: {len(files)}개 파일")
        
        return grouped
    
    def process_classification_files(self, session_files):
        """분류 파일들 처리"""
        merged_data = []
        
        for session_id, files in session_files.items():
            if len(files) < 1:
                continue
            
            # 파일 번호 순서대로 정렬
            ordered_files = sorted(files, key=lambda x: self.extract_file_number(os.path.basename(x)))
            
            # consulting_content 기준으로 데이터 병합
            content_groups = {}
            
            for filepath in ordered_files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 리스트인 경우 첫 번째 요소 사용
                    if isinstance(data, list):
                        data = data[0]
                    
                    content = data.get('consulting_content', '')
                    
                    if content not in content_groups:
                        # 기본 메타데이터 저장 (instructions, input 제외)
                        base_data = {k: v for k, v in data.items() 
                                   if k not in ('instructions', 'input')}
                        content_groups[content] = {
                            'base': base_data,
                            'data': []
                        }
                    
                    # instructions 데이터 병합
                    instructions = data.get('instructions', [])
                    if instructions:
                        instruction_data = instructions[0].get('data', [])
                        content_groups[content]['data'].extend(instruction_data)
                
                except Exception as e:
                    print(f"❌ 파일 처리 오류 {filepath}: {e}")
            
            # 최종 객체 생성
            for content, info in content_groups.items():
                obj = info['base'].copy()
                obj['consulting_content'] = content
                obj['instructions'] = [{
                    'tuning_type': '분류',
                    'data': info['data']
                }]
                merged_data.append(obj)
            
            # 세션별 파일 저장
            output = {
                'session_id': session_id,
                '분류': merged_data
            }
            
            output_path = os.path.join(
                self.output_dirs['분류'], 
                f'merged_classification_{session_id}_final.json'
            )
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            
            merged_data.clear()  # 다음 세션을 위해 초기화
    
    def process_summary_files(self, session_files):
        """요약 파일들 처리"""
        for session_id, files in session_files.items():
            if len(files) < 1:
                continue
            
            # 파일 번호 순서대로 정렬
            ordered_files = sorted(files, key=lambda x: self.extract_file_number(os.path.basename(x)))
            
            # consulting_content 기준으로 데이터 병합
            content_groups = {}
            
            for filepath in ordered_files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        data = data[0]
                    
                    content = data.get('consulting_content', '')
                    
                    if content not in content_groups:
                        base_data = {k: v for k, v in data.items() 
                                   if k not in ('instructions', 'input')}
                        content_groups[content] = {
                            'base': base_data,
                            'data': []
                        }
                    
                    instructions = data.get('instructions', [])
                    if instructions:
                        instruction_data = instructions[0].get('data', [])
                        content_groups[content]['data'].extend(instruction_data)
                
                except Exception as e:
                    print(f"❌ 요약 파일 처리 오류 {filepath}: {e}")
            
            # 최종 객체 생성
            merged_data = []
            for content, info in content_groups.items():
                obj = info['base'].copy()
                obj['consulting_content'] = content
                obj['instructions'] = [{
                    'tuning_type': '요약',
                    'data': info['data']
                }]
                merged_data.append(obj)
            
            # 세션별 파일 저장
            output = {
                'session_id': session_id,
                '요약': merged_data
            }
            
            output_path = os.path.join(
                self.output_dirs['요약'], 
                f'merged_summary_{session_id}.json'
            )
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
    
    def process_qa_files(self, session_files):
        """질의응답 파일들 처리"""
        for session_id, files in session_files.items():
            if len(files) < 1:
                continue
            
            # 파일 번호 순서대로 정렬
            ordered_files = sorted(files, key=lambda x: self.extract_file_number(os.path.basename(x)))
            
            # consulting_content 기준으로 데이터 병합
            content_groups = {}
            
            for filepath in ordered_files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        data = data[0]
                    
                    content = data.get('consulting_content', '')
                    
                    if content not in content_groups:
                        base_data = {k: v for k, v in data.items() 
                                   if k not in ('instructions', 'input')}
                        content_groups[content] = {
                            'base': base_data,
                            'data': []
                        }
                    
                    instructions = data.get('instructions', [])
                    if instructions:
                        instruction_data = instructions[0].get('data', [])
                        content_groups[content]['data'].extend(instruction_data)
                
                except Exception as e:
                    print(f"❌ 질의응답 파일 처리 오류 {filepath}: {e}")
            
            # 최종 객체 생성
            merged_data = []
            for content, info in content_groups.items():
                obj = info['base'].copy()
                obj['consulting_content'] = content
                obj['instructions'] = [{
                    'tuning_type': '질의응답',
                    'data': info['data']
                }]
                merged_data.append(obj)
            
            # 세션별 파일 저장
            output = {
                'session_id': session_id,
                '질의응답': merged_data
            }
            
            output_path = os.path.join(
                self.output_dirs['질의응답'], 
                f'merged_qa_{session_id}.json'
            )
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
    
    def remove_input_fields(self):
        """생성된 모든 병합 파일에서 input 필드 제거"""
        def remove_input_recursive(obj):
            if isinstance(obj, dict):
                obj.pop('input', None)
                for value in obj.values():
                    remove_input_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    remove_input_recursive(item)
        
        all_files = []
        for output_dir in self.output_dirs.values():
            all_files.extend(glob.glob(os.path.join(output_dir, '*.json')))
        
        for filepath in tqdm(all_files, desc='Input 필드 제거 중'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                remove_input_recursive(data)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            except Exception as e:
                print(f"❌ Input 제거 오류 {filepath}: {e}")
        
        print(f"✅ {len(all_files)}개 파일에서 input 필드 제거 완료")
    
    def integrate_all_sessions(self):
        """모든 세션의 분류/요약/질의응답 데이터를 통합"""
        integration_dir = f'{self.output_base}/integration_data'
        os.makedirs(integration_dir, exist_ok=True)
        
        # 각 세션별로 통합 파일 생성
        all_sessions = set()
        
        # 모든 출력 폴더에서 세션 ID 수집
        for data_type, output_dir in self.output_dirs.items():
            for filepath in glob.glob(os.path.join(output_dir, '*.json')):
                filename = os.path.basename(filepath)
                session_id = self.extract_session_id(filename)
                if session_id != 'unknown':
                    all_sessions.add(session_id)
        
        print(f"🔗 {len(all_sessions)}개 세션 통합 중...")
        
        for session_id in tqdm(all_sessions, desc='세션 통합'):
            integrated_data = {'session_id': session_id}
            
            # 각 데이터 타입별로 파일 읽기
            for data_type, output_dir in self.output_dirs.items():
                type_files = glob.glob(os.path.join(output_dir, f'*{session_id}*.json'))
                
                if type_files:
                    try:
                        with open(type_files[0], 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # 데이터 타입별 정보 추가
                        if data_type == '분류':
                            integrated_data['분류'] = data.get('분류', [])
                        elif data_type == '요약':
                            integrated_data['요약'] = data.get('요약', [])
                        elif data_type == '질의응답':
                            integrated_data['질의응답'] = data.get('질의응답', [])
                    
                    except Exception as e:
                        print(f"❌ 세션 {session_id} {data_type} 통합 오류: {e}")
            
            # 통합 파일 저장
            output_path = os.path.join(integration_dir, f'final_merged_{session_id}.json')
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(integrated_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 세션 통합 완료 → {integration_dir}")
    
    def run(self):
        """전체 전처리 프로세스 실행"""
        print("="*60)
        print("🔄 통합 데이터 전처리 시작")
        print("="*60)
        
        # 1. 파일 그룹화
        grouped_files = self.group_files_by_type_and_session()
        
        # 2. 각 타입별 처리
        print(f"\n[1단계] 분류 데이터 처리...")
        self.process_classification_files(grouped_files['분류'])
        
        print(f"\n[2단계] 요약 데이터 처리...")
        self.process_summary_files(grouped_files['요약'])
        
        print(f"\n[3단계] 질의응답 데이터 처리...")
        self.process_qa_files(grouped_files['질의응답'])
        
        # 3. Input 필드 제거
        print(f"\n[4단계] Input 필드 제거...")
        self.remove_input_fields()
        
        # 4. 세션 통합
        print(f"\n[5단계] 세션별 데이터 통합...")
        self.integrate_all_sessions()
        
        print("\n" + "="*60)
        print("✅ 통합 전처리 완료!")
        print("="*60)
        print(f"📁 출력 폴더:")
        for data_type, output_dir in self.output_dirs.items():
            print(f"   {data_type}: {output_dir}")
        print(f"   통합: {self.output_base}/integration_data")

def main():
    """메인 실행 함수"""
    print("🚀 통합 폴더 기반 전처리 시스템")
    print("="*50)
    
    # 입력 폴더 확인
    input_dir = "data"
    if not os.path.exists(input_dir):
        print(f"❌ 입력 폴더가 없습니다: {input_dir}")
        print("   data 폴더를 생성하고 JSON 파일들을 넣어주세요.")
        return
    
    # JSON 파일 존재 확인
    json_files = glob.glob(os.path.join(input_dir, '*.json'))
    if not json_files:
        print(f"❌ {input_dir} 폴더에 JSON 파일이 없습니다.")
        return
    
    print(f"✅ {len(json_files)}개 JSON 파일 발견")
    print(f"📂 입력 폴더: {input_dir}")
    print(f"📂 출력 폴더: json_merge/")
    
    # 파일명 패턴 안내
    print(f"\n📝 지원하는 파일명 패턴:")
    print(f"   • 분류: 분류_세션ID_번호.json")
    print(f"   • 요약: 요약_세션ID_번호.json")
    print(f"   • 질의응답: 질의응답_세션ID_번호.json")
    print(f"   (또는 영어: classification, summary, qa)")
    
    # 전처리 실행
    processor = UnifiedPreprocessor(input_dir)
    processor.run()

if __name__ == "__main__":
    main() 