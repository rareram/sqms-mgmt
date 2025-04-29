import pandas as pd
import os
import csv
import sys

# 파일 경로 설정
REPO_FILE = "gitlab_repolist.csv"
USER_FILE = "gitlab_allusers.csv"
MEMBER_FILE = "gitlab_all_memberlist.csv"
OUTPUT_FILE = "gitlab_integrated_data.csv"

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
    
    # 2. 사용자 정보 로드 (나중에 사용자 이름 대신 이메일이 필요할 경우 참조용)
    print("👤 사용자 정보 로드 중...")
    try:
        users_df = pd.read_csv(USER_FILE)
        print(f"✅ 사용자 {len(users_df)}명 로드 완료")
        
        # 사용자 정보에서 이름과 이메일 매핑 생성 (필요시 사용)
        user_email_map = dict(zip(users_df['name'], users_df['email']))
    except Exception as e:
        print(f"❌ 사용자 파일 로드 실패: {e}")
        user_email_map = {}
    
    # 3. 멤버 및 커밋 정보 로드
    print("👥 멤버 및 커밋 정보 로드 중...")
    try:
        members_df = pd.read_csv(MEMBER_FILE)
        print(f"✅ 프로젝트 멤버 정보 {len(members_df)}개 로드 완료")
        
        # 필요한 컬럼만 남기기
        member_columns = ['project_id', 'owner']
        member_columns.extend([f'maintainer{i}' for i in range(1, 19)])  # 18명으로 제한
        member_columns.extend([f'developer{i}' for i in range(1, 21)])
        member_columns.extend([f'commit_user{i}' for i in range(1, 21)])
        member_columns.extend([f'commit_date{i}' for i in range(1, 21)])
        
        # 실제 데이터프레임에 있는 컬럼만 선택
        existing_member_columns = [col for col in member_columns if col in members_df.columns]
        members_df = members_df[existing_member_columns]
        
        # maintainer 컬럼이 25개인 경우 18개로 제한
        if 'maintainer19' in members_df.columns:
            members_df = members_df.drop(columns=[f'maintainer{i}' for i in range(19, 26) if f'maintainer{i}' in members_df.columns])
        
    except Exception as e:
        print(f"❌ 멤버 파일 로드 실패: {e}")
        return
    
    # 4. 데이터 병합 - repo_id를 기준으로 병합
    print("🔄 데이터 병합 중...")
    try:
        # repo_id와 project_id를 기준으로 조인
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
            'id', 'group', 'project', 'repository', 'description', 
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
    except Exception as e:
        print(f"❌ 데이터 병합 실패: {e}")
        print(f"오류 상세: {str(e)}")
        return
    
    # 5. CSV 파일로 저장 (한글 지원 및 Excel 호환성 위해 utf-8-sig 인코딩 사용)
    print("💾 통합 데이터 저장 중...")
    try:
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"✅ 통합 데이터 저장 완료: {OUTPUT_FILE}")
        print(f"📊 총 {len(final_df)}개의 레포지토리 정보가 통합되었습니다.")
    except Exception as e:
        print(f"❌ 통합 데이터 저장 실패: {e}")
        return
    
    print("🎉 모든 작업이 성공적으로 완료되었습니다!")
    print(f"📁 결과 파일: {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    merge_gitlab_data()
