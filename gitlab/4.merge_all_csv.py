import pandas as pd
import os
import csv
import sys

# 파일 경로 설정
REPO_FILE = "gitlab_repolist.csv"
USER_FILE = "gitlab_allusers.csv"
MEMBER_FILE = "gitlab_all_memberlist.csv"
OUTPUT_FILE = "gitlab_integrated_data.csv"

# 최대 그룹 depth 설정
MAX_GROUP_DEPTH = 3  # 최대 3단계 그룹 (그룹이 많으면 조정 가능)

def check_files_exist():
    """필요한 파일들이 존재하는지 확인"""
    missing_files = []
    for file in [REPO_FILE, USER_FILE, MEMBER_FILE]:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 다음 파일들이 존재하지 않습니다: {', '.join(missing_files)}")
        print("📌 먼저 get_all_repolist.py, get_all_userinfo.py, get_all_repo2user.py를 실행해주세요.")
        return False
    return True

def merge_gitlab_data():
    """GitLab 레포지토리, 유저, 멤버 정보를 통합"""
    print("🔄 GitLab 데이터 통합 시작...")
    
    if not check_files_exist():
        return
    
    # 1. 레포지토리 정보 로드
    print("📂 레포지토리 정보 로드 중...")
    try:
        repos_df = pd.read_csv(REPO_FILE)
        print(f"✅ 레포지토리 {len(repos_df)}개 로드 완료")
    except Exception as e:
        print(f"❌ 레포지토리 파일 로드 실패: {e}")
        return
    
    # 2. 사용자 정보 로드 (참조용)
    print("👤 사용자 정보 로드 중...")
    try:
        users_df = pd.read_csv(USER_FILE)
        print(f"✅ 사용자 {len(users_df)}명 로드 완료")
    except Exception as e:
        print(f"❌ 사용자 파일 로드 실패: {e}")
        return
    
    # 3. 멤버 및 커밋 정보 로드
    print("👥 멤버 및 커밋 정보 로드 중...")
    try:
        members_df = pd.read_csv(MEMBER_FILE)
        print(f"✅ 프로젝트 멤버 정보 {len(members_df)}개 로드 완료")
        
        # 필요한 메인테이너 컬럼만 선택 (1-18만 사용)
        maintainer_cols = [f'maintainer{i}' for i in range(1, 26) if f'maintainer{i}' in members_df.columns]
        
        # 유지할 컬럼 리스트
        keep_cols = ['project_id', 'owner'] 
        keep_cols.extend(maintainer_cols[:18])  # 최대 18개까지만 유지
        keep_cols.extend([f'developer{i}' for i in range(1, 21) if f'developer{i}' in members_df.columns])
        keep_cols.extend([f'commit_user{i}' for i in range(1, 21) if f'commit_user{i}' in members_df.columns])
        keep_cols.extend([f'commit_date{i}' for i in range(1, 21) if f'commit_date{i}' in members_df.columns])
        
        # 실제 데이터프레임에 있는 컬럼만 선택
        existing_cols = [col for col in keep_cols if col in members_df.columns]
        members_df = members_df[existing_cols]
        
        # maintainer 컬럼 수 확인
        maintainer_count = sum(1 for col in members_df.columns if col.startswith('maintainer'))
        if maintainer_count > 18:
            excess_maintainers = [f'maintainer{i}' for i in range(19, 26) if f'maintainer{i}' in members_df.columns]
            members_df = members_df.drop(columns=excess_maintainers)
            print(f"📝 메인테이너 컬럼 18개로 제한됨 (초과 컬럼 {len(excess_maintainers)}개 제외)")
        
    except Exception as e:
        print(f"❌ 멤버 파일 로드 실패: {e}")
        return
    
    # 4. 레포지토리 경로 분석 및 그룹/프로젝트 분리
    print("📊 레포지토리 경로 분석 중...")
    try:
        # 새로운 컬럼들 초기화
        for i in range(1, MAX_GROUP_DEPTH + 1):
            repos_df[f'group{i}'] = ""
        
        # project 컬럼 추가 (기존에 있으면 유지)
        if 'project' not in repos_df.columns:
            repos_df['project'] = ""
        
        # 각 레포지토리 경로 분석 및 분할
        for idx, repo_path in enumerate(repos_df['repository']):
            parts = repo_path.split('/')
            
            # 마지막 부분은 항상 프로젝트 이름
            if parts:
                repos_df.at[idx, 'project'] = parts[-1]
            
            # 그룹 부분 채우기 (마지막 부분 제외)
            for i, part in enumerate(parts[:-1], start=1):
                if i <= MAX_GROUP_DEPTH:  # 최대 그룹 depth까지만 처리
                    repos_df.at[idx, f'group{i}'] = part
        
        # 기존 'group' 컬럼이 있다면 제거 (이제 group1, group2, group3로 대체)
        if 'group' in repos_df.columns:
            repos_df = repos_df.drop(columns=['group'])
        
        print(f"✅ 레포지토리 경로 분석 완료")
        
        # 결과 확인 (처음 5개만)
        print("📝 레포지토리 경로 분석 샘플 (처음 5개):")
        sample_cols = ['repository', 'group1', 'group2', 'group3', 'project']
        existing_sample_cols = [col for col in sample_cols if col in repos_df.columns]
        print(repos_df[existing_sample_cols].head(5).to_string())
        
    except Exception as e:
        print(f"❌ 레포지토리 경로 분석 실패: {e}")
        return
    
    # 5. 데이터 병합 - repo_id를 기준으로 병합
    print("🔄 데이터 병합 중...")
    try:
        # repo_id(id)와 project_id를 기준으로 조인
        merged_df = pd.merge(
            repos_df, 
            members_df,
            left_on='id',
            right_on='project_id',
            how='left'
        )
        
        # project_id 컬럼 제거 (중복)
        if 'project_id' in merged_df.columns:
            merged_df = merged_df.drop(columns=['project_id'])
        
        # archive 컬럼 추가 (기본값: False)
        merged_df['archive'] = False
        
        # 최종 컬럼 순서 정의
        final_columns = [
            'id', 
            'group1', 'group2', 'group3', 
            'project', 'repository', 'description', 
            'url', 'created_at', 'last_update', 'archive',
            'owner'
        ]
        
        # maintainer 컬럼 추가 (18개)
        final_columns.extend([f'maintainer{i}' for i in range(1, 19)])
        
        # developer 컬럼 추가 (20개)
        final_columns.extend([f'developer{i}' for i in range(1, 21)])
        
        # commit_user 컬럼 추가 (20개)
        final_columns.extend([f'commit_user{i}' for i in range(1, 21)])
        
        # commit_date 컬럼 추가 (20개)
        final_columns.extend([f'commit_date{i}' for i in range(1, 21)])
        
        # 누락된 컬럼 추가
        for col in final_columns:
            if col not in merged_df.columns:
                merged_df[col] = ""
        
        # NaN 값을 빈 문자열로 대체
        merged_df = merged_df.fillna("")
        
        # 최종 컬럼 순서대로 정렬
        final_df = merged_df[final_columns]
        
        print(f"✅ 데이터 병합 완료: {len(final_df)}개 레코드")
        
        # project 컬럼 값 확인
        projects_filled = (final_df['project'] != "").sum()
        print(f"📊 project 컬럼이 채워진 레코드: {projects_filled}개 / {len(final_df)}개")
        
    except Exception as e:
        print(f"❌ 데이터 병합 실패: {e}")
        print(f"오류 상세: {str(e)}")
        return
    
    # 6. CSV 파일로 저장 (한글 지원 및 Excel 호환성 위해 utf-8-sig 인코딩 사용)
    print("💾 통합 데이터 저장 중...")
    try:
        # 샘플 데이터 출력 (처음 3개 레코드)
        sample_cols = ['id', 'group1', 'group2', 'group3', 'project', 'repository']
        print("📝 저장할 데이터 샘플 (처음 3개 레코드의 일부 컬럼):")
        print(final_df[sample_cols].head(3).to_string())
        
        # CSV 파일로 저장
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"✅ 통합 데이터 저장 완료: {OUTPUT_FILE}")
        
        # 컬럼 정보 출력
        print(f"📋 저장된 컬럼 목록과 순서:")
        for i, col in enumerate(final_columns, 1):
            print(f"   {i:2d}. {col}")
    except Exception as e:
        print(f"❌ 통합 데이터 저장 실패: {e}")
        return
    
    print("🎉 모든 작업이 성공적으로 완료되었습니다!")
    print(f"📁 결과 파일: {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    merge_gitlab_data()
