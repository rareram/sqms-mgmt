import pandas as pd
import re
import os
import json
from difflib import SequenceMatcher
from datetime import datetime

# 파일 경로 설정
INTEGRATED_DATA = "gitlab_integrated_data.csv"  # 통합된 데이터
USERS_DATA = "gitlab_allusers.csv"              # 사용자 정보
MEMBERLIST_DATA = "gitlab_all_memberlist.csv"   # 프로젝트별 멤버 정보
OUTPUT_FILE = "gitlab_normalized_data.csv"      # 정규화된 출력 파일
MAPPING_FILE = "user_mapping.json"              # 매핑 정보 저장 파일 (재사용 가능)
LOG_FILE = "normalization_log.txt"              # 로그 파일

# 이메일에서 사용자 이름 추출 패턴
EMAIL_PATTERN = re.compile(r'^([^@]+)@')
NAME_EMAIL_PATTERN = re.compile(r'([^<]+)<([^>]+)>')  # "홍길동 <hong@company.com>" 형식

# 유사도 임계값 (0.0 ~ 1.0, 높을수록 더 엄격한 매칭)
SIMILARITY_THRESHOLD = 0.75

# 매핑 캐시
mapping_cache = {}

def setup_logging():
    """로깅 설정"""
    log_file = open(LOG_FILE, "w", encoding="utf-8")
    log_file.write(f"=== 커밋 사용자 정규화 로그 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===\n\n")
    return log_file

def log_message(log_file, message):
    """로그 메시지 기록"""
    print(message)
    if log_file:
        log_file.write(f"{message}\n")
        log_file.flush()

def load_data(log_file):
    """필요한 데이터 파일들을 로드합니다."""
    log_message(log_file, "🔄 데이터 로드 중...")
    
    try:
        integrated_df = pd.read_csv(INTEGRATED_DATA)
        log_message(log_file, f"✅ 통합 데이터 로드 완료: {len(integrated_df)}개 레코드")
    except Exception as e:
        log_message(log_file, f"❌ 통합 데이터 로드 실패: {e}")
        return None, None, None
    
    try:
        users_df = pd.read_csv(USERS_DATA)
        log_message(log_file, f"✅ 사용자 정보 로드 완료: {len(users_df)}명")
    except Exception as e:
        log_message(log_file, f"❌ 사용자 정보 로드 실패: {e}")
        return integrated_df, None, None
    
    try:
        members_df = pd.read_csv(MEMBERLIST_DATA)
        log_message(log_file, f"✅ 멤버 정보 로드 완료: {len(members_df)}개 프로젝트")
    except Exception as e:
        log_message(log_file, f"❌ 멤버 정보 로드 실패: {e}")
        return integrated_df, users_df, None
    
    return integrated_df, users_df, members_df

def load_existing_mapping():
    """기존 매핑 파일이 있으면 로드합니다."""
    if os.path.exists(MAPPING_FILE):
        try:
            with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_mapping(mapping):
    """매핑 정보를 파일로 저장합니다."""
    try:
        with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def extract_name_email(text):
    """'홍길동 <hong@company.com>' 형식에서 이름과 이메일 추출"""
    if not text or not isinstance(text, str):
        return None, None
    
    match = NAME_EMAIL_PATTERN.match(text.strip())
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None

def build_mapping_table(users_df, members_df, integrated_df, log_file):
    """사용자 이름, 이메일, 사용자명에 대한 매핑 테이블을 구축합니다."""
    log_message(log_file, "📊 사용자 매핑 테이블 구축 중...")
    
    # 기존 매핑 로드
    mapping = load_existing_mapping()
    if mapping:
        log_message(log_file, f"✅ 기존 매핑 파일에서 {len(mapping)}개 항목 로드됨")
    
    # 1. GitLab 사용자 정보에서 이름-이메일 매핑
    gitlab_mappings = 0
    
    if users_df is not None:
        for _, user in users_df.iterrows():
            name = user.get('name', '')
            email = user.get('email', '')
            username = user.get('username', '')
            
            if name and email:
                name_key = name.lower()
                # 이름 -> 사용자 정보 매핑
                if name_key not in mapping:
                    mapping[name_key] = {
                        'name': name,
                        'email': email,
                        'username': username,
                        'source': 'gitlab_user'
                    }
                    gitlab_mappings += 1
                
                # 이메일 ID -> 사용자 정보 매핑
                email_id = EMAIL_PATTERN.match(email)
                if email_id:
                    email_key = email_id.group(1).lower()
                    if email_key not in mapping:
                        mapping[email_key] = {
                            'name': name,
                            'email': email,
                            'username': username,
                            'source': 'gitlab_user'
                        }
                        gitlab_mappings += 1
                
                # 이메일 전체 -> 사용자 정보 매핑
                email_key = email.lower()
                if email_key not in mapping:
                    mapping[email_key] = {
                        'name': name,
                        'email': email,
                        'username': username,
                        'source': 'gitlab_user'
                    }
                    gitlab_mappings += 1
        
        log_message(log_file, f"✅ GitLab 사용자 정보에서 {gitlab_mappings}개 매핑 항목 추가")
    
    # 2. 프로젝트별 멤버 정보에서 추가 매핑
    project_members = {}
    member_mappings = 0
    
    if members_df is not None:
        member_cols = []
        for col in members_df.columns:
            if col.startswith('maintainer') or col.startswith('developer') or col == 'owner':
                member_cols.append(col)
        
        # 프로젝트별로 모든 멤버 수집
        for _, row in members_df.iterrows():
            project_id = row.get('project_id')
            if project_id:
                members = []
                for col in member_cols:
                    member_name = row.get(col)
                    if member_name and isinstance(member_name, str) and member_name.strip():
                        member_name = member_name.strip()
                        members.append(member_name)
                        
                        # 이미 매핑에 없는 멤버는 이름만 추가
                        member_key = member_name.lower()
                        if member_key not in mapping:
                            mapping[member_key] = {
                                'name': member_name,
                                'email': '',  # 이메일 미상
                                'username': '',
                                'source': 'project_member'
                            }
                            member_mappings += 1
                
                project_members[project_id] = list(set(members))  # 중복 제거
        
        log_message(log_file, f"✅ {len(project_members)}개 프로젝트의 멤버 정보 수집")
        log_message(log_file, f"✅ 프로젝트 멤버에서 {member_mappings}개 매핑 항목 추가")
    
    # 3. 통합 데이터에서 커밋 사용자 수집 및 분석
    commit_users = set()
    commit_mappings = 0
    
    if integrated_df is not None:
        commit_cols = [col for col in integrated_df.columns if col.startswith('commit_user')]
        for _, row in integrated_df.iterrows():
            for col in commit_cols:
                commit_user = row.get(col)
                if commit_user and isinstance(commit_user, str) and commit_user.strip():
                    commit_user = commit_user.strip()
                    commit_users.add(commit_user)
                    
                    # "홍길동 <hong@company.com>" 형식 처리
                    name, email = extract_name_email(commit_user)
                    if name and email:
                        name_key = name.lower()
                        email_key = email.lower()
                        
                        # 이메일 기반 매핑 추가
                        if email_key not in mapping:
                            mapping[email_key] = {
                                'name': name,
                                'email': email,
                                'username': '',
                                'source': 'commit_user_email'
                            }
                            commit_mappings += 1
                        
                        # 이름 기반 매핑 추가
                        if name_key not in mapping:
                            mapping[name_key] = {
                                'name': name,
                                'email': email,
                                'username': '',
                                'source': 'commit_user_name'
                            }
                            commit_mappings += 1
                        
                        # 커밋 사용자 전체 문자열 매핑
                        commit_key = commit_user.lower()
                        if commit_key not in mapping:
                            mapping[commit_key] = {
                                'name': name,
                                'email': email,
                                'username': '',
                                'source': 'commit_user_full'
                            }
                            commit_mappings += 1
                    else:
                        # 이메일 형식인지 확인
                        if '@' in commit_user:
                            email_key = commit_user.lower()
                            if email_key not in mapping:
                                # 이메일에서 사용자 이름 추출 시도
                                email_id = EMAIL_PATTERN.match(commit_user)
                                extracted_name = email_id.group(1) if email_id else ''
                                
                                mapping[email_key] = {
                                    'name': extracted_name,
                                    'email': commit_user,
                                    'username': '',
                                    'source': 'commit_email'
                                }
                                commit_mappings += 1
                        else:
                            # 이름으로 간주
                            name_key = commit_user.lower()
                            if name_key not in mapping:
                                mapping[name_key] = {
                                    'name': commit_user,
                                    'email': '',
                                    'username': '',
                                    'source': 'commit_name'
                                }
                                commit_mappings += 1
        
        log_message(log_file, f"✅ 통합 데이터에서 {len(commit_users)}명의 고유 커밋 사용자 발견")
        log_message(log_file, f"✅ 커밋 사용자에서 {commit_mappings}개 매핑 항목 추가")
    
    # 4. 매핑 테이블 저장
    total_mappings = len(mapping)
    if save_mapping(mapping):
        log_message(log_file, f"✅ 총 {total_mappings}개 매핑 항목이 {MAPPING_FILE}에 저장됨")
    else:
        log_message(log_file, f"⚠️ 매핑 파일 저장 실패")
    
    # 매핑 테이블 반환
    return mapping, project_members, commit_users

def find_best_match(commit_user, mapping, project_id, project_members, log_file=None):
    """커밋 사용자에 대한 최적의 매칭을 찾습니다."""
    if not commit_user or not isinstance(commit_user, str) or not commit_user.strip():
        return None
    
    commit_user = commit_user.strip()
    
    # 캐시 확인
    if commit_user in mapping_cache:
        return mapping_cache[commit_user]
    
    commit_user_lower = commit_user.lower()
    
    # 1. 정확한 매칭 시도
    if commit_user_lower in mapping:
        mapping_cache[commit_user] = mapping[commit_user_lower]
        return mapping[commit_user_lower]
    
    # 2. 이름과 이메일 추출 시도 (홍길동 <hong@company.com> 형식)
    name, email = extract_name_email(commit_user)
    if name and email:
        email_lower = email.lower()
        if email_lower in mapping:
            mapping_cache[commit_user] = mapping[email_lower]
            return mapping[email_lower]
        
        name_lower = name.lower()
        if name_lower in mapping:
            mapping_cache[commit_user] = mapping[name_lower]
            return mapping[name_lower]
    
    # 3. 이메일 패턴 매칭 시도
    if '@' in commit_user:
        # 이메일 자체로 매칭
        if commit_user_lower in mapping:
            mapping_cache[commit_user] = mapping[commit_user_lower]
            return mapping[commit_user_lower]
        
        # 이메일 ID로 매칭
        email_match = EMAIL_PATTERN.match(commit_user)
        if email_match and email_match.group(1).lower() in mapping:
            email_id = email_match.group(1).lower()
            mapping_cache[commit_user] = mapping[email_id]
            return mapping[email_id]
    
    # 4. 프로젝트 멤버와 유사도 매칭 시도
    if project_id and project_id in project_members:
        members = project_members[project_id]
        best_match = None
        highest_ratio = 0
        
        for member in members:
            ratio = SequenceMatcher(None, commit_user_lower, member.lower()).ratio()
            if ratio > highest_ratio and ratio >= SIMILARITY_THRESHOLD:
                highest_ratio = ratio
                best_match = member
        
        if best_match and best_match.lower() in mapping:
            best_match_lower = best_match.lower()
            mapping_cache[commit_user] = mapping[best_match_lower]
            return mapping[best_match_lower]
    
    # 5. 전체 매핑에서 유사도 매칭 시도
    best_match = None
    highest_ratio = 0
    
    for key in mapping:
        ratio = SequenceMatcher(None, commit_user_lower, key).ratio()
        if ratio > highest_ratio and ratio >= SIMILARITY_THRESHOLD:
            highest_ratio = ratio
            best_match = key
    
    if best_match:
        mapping_cache[commit_user] = mapping[best_match]
        return mapping[best_match]
    
    # 매칭 실패 - 기본 정보 생성
    if '@' in commit_user:
        # 이메일로 간주
        email_id = EMAIL_PATTERN.match(commit_user)
        name = email_id.group(1) if email_id else commit_user.split('@')[0]
        default_info = {
            'name': name,
            'email': commit_user,
            'username': '',
            'source': 'default_email'
        }
    else:
        # 이름으로 간주
        default_info = {
            'name': commit_user,
            'email': '',
            'username': '',
            'source': 'default_name'
        }
    
    mapping_cache[commit_user] = default_info
    return default_info

def normalize_commit_users():
    """커밋 사용자 정보를 정규화합니다."""
    # 로그 파일 설정
    log_file = setup_logging()
    log_message(log_file, "🚀 커밋 사용자 정규화 시작...")
    
    # 1. 데이터 로드
    integrated_df, users_df, members_df = load_data(log_file)
    if integrated_df is None:
        log_message(log_file, "❌ 필수 데이터 로드 실패, 종료합니다.")
        if log_file:
            log_file.close()
        return
    
    # 2. 매핑 테이블 구축
    mapping, project_members, commit_users = build_mapping_table(users_df, members_df, integrated_df, log_file)
    
    # 3. 정규화 작업
    log_message(log_file, "🔄 커밋 사용자 정규화 중...")
    
    # 커밋 사용자 컬럼과 날짜 컬럼 리스트
    commit_user_cols = [col for col in integrated_df.columns if col.startswith('commit_user')]
    
    # 정규화된 이름과 이메일 컬럼 추가
    for i, col in enumerate(commit_user_cols, 1):
        integrated_df[f'normalized_name{i}'] = ""
        integrated_df[f'normalized_email{i}'] = ""
        integrated_df[f'normalized_username{i}'] = ""
    
    # 매칭 통계
    match_stats = {
        'total': 0,
        'matched': 0,
        'unmatched': 0,
        'sources': {}
    }
    
    # 각 행을 처리
    for idx, row in integrated_df.iterrows():
        project_id = row.get('id')
        
        for i, col in enumerate(commit_user_cols, 1):
            commit_user = row.get(col)
            
            if commit_user and isinstance(commit_user, str) and commit_user.strip():
                match_stats['total'] += 1
                
                match = find_best_match(commit_user, mapping, project_id, project_members, log_file)
                
                if match:
                    integrated_df.at[idx, f'normalized_name{i}'] = match['name']
                    integrated_df.at[idx, f'normalized_email{i}'] = match['email']
                    integrated_df.at[idx, f'normalized_username{i}'] = match.get('username', '')
                    
                    match_stats['matched'] += 1
                    
                    # 매칭 소스 통계
                    source = match.get('source', 'unknown')
                    if source not in match_stats['sources']:
                        match_stats['sources'][source] = 0
                    match_stats['sources'][source] += 1
                else:
                    match_stats['unmatched'] += 1
    
    # 4. 매칭 통계 출력
    match_percentage = (match_stats['matched'] / match_stats['total'] * 100) if match_stats['total'] > 0 else 0
    
    log_message(log_file, f"\n📊 매칭 통계:")
    log_message(log_file, f"  - 총 커밋 사용자: {match_stats['total']}명")
    log_message(log_file, f"  - 매칭 성공: {match_stats['matched']}명 ({match_percentage:.2f}%)")
    log_message(log_file, f"  - 매칭 실패: {match_stats['unmatched']}명 ({100-match_percentage:.2f}%)")
    
    if match_stats['sources']:
        log_message(log_file, f"\n📊 매칭 소스 분포:")
        for source, count in sorted(match_stats['sources'].items(), key=lambda x: x[1], reverse=True):
            source_percentage = (count / match_stats['matched'] * 100) if match_stats['matched'] > 0 else 0
            log_message(log_file, f"  - {source}: {count}명 ({source_percentage:.2f}%)")
    
    # 5. 결과 저장
    try:
        # NaN 값을 빈 문자열로 대체
        integrated_df = integrated_df.fillna("")
        
        # CSV 저장
        integrated_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        log_message(log_file, f"\n✅ 정규화된 데이터 저장 완료: {OUTPUT_FILE}")
        
        # 샘플 출력
        log_message(log_file, "\n📝 정규화 예시 (처음 5개):")
        sample_cols = ['id', 'project', 'commit_user1', 'normalized_name1', 'normalized_email1']
        sample_data = integrated_df[sample_cols].head(5).to_string()
        log_message(log_file, sample_data)
        
    except Exception as e:
        log_message(log_file, f"❌ 파일 저장 실패: {e}")
    
    log_message(log_file, "\n🎉 작업이 완료되었습니다!")
    log_message(log_file, f"📋 자세한 로그는 {LOG_FILE} 파일을 참조하세요.")
    
    # 로그 파일 닫기
    if log_file:
        log_file.close()

if __name__ == "__main__":
    normalize_commit_users()
