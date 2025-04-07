import streamlit as st
import requests
import pandas as pd
import json
import os
from datetime import datetime
import time
from io import StringIO
from progress import show_progress_bar

def show_module():
    """GitLab 관리 모듈 메인 화면"""
    st.title("GitLab 관리")
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs(["저장소 관리", "사용자 관리", "미사용 저장소", "GitLab 설정"])
    
    # 저장소 관리 탭
    with tab1:
        show_repository_management()
    
    # 사용자 관리 탭
    with tab2:
        show_user_management()
    
    # 미사용 저장소 탭
    with tab3:
        show_unused_repositories()
    
    # GitLab 설정 탭
    with tab4:
        show_gitlab_settings()

def show_repository_management():
    """저장소 관리 화면"""
    st.subheader("저장소 관리")
    
    # GitLab 연결 확인
    if not check_gitlab_connection():
        st.error("GitLab 연결에 실패했습니다. GitLab 설정을 확인해주세요.")
        return
    
    # 저장소 목록 불러오기
    if st.button("저장소 목록 갱신"):
        # with st.spinner("저장소 목록을 불러오는 중입니다..."):
            # repositories = get_all_repositories()
            
            # if repositories:
                # 세션 상태에 저장
                # st.session_state.repositories = repositories
                # st.success(f"총 {len(repositories)}개의 저장소를 불러왔습니다.")
            # else:
                # st.error("저장소 목록을 불러오는데 실패했습니다.")
        
        show_progress_bar("저장소 목록을 불러오는 중입니다", steps=10)

        repositories = get_all_repositories()

        if repositories:
            st.session_state.repositories = repositories
            st.success(f"총 {len(repositories)}개의 저장소를 불러왔습니다.")
    
    # 저장소 목록 표시
    if hasattr(st.session_state, 'repositories'):
        repositories = st.session_state.repositories
        
        # 검색 필터
        search_term = st.text_input("저장소 검색 (이름, 그룹, 설명)")
        
        # 필터링
        if search_term:
            filtered_repos = [repo for repo in repositories if 
                             search_term.lower() in repo["name"].lower() or 
                             search_term.lower() in repo["namespace"]["name"].lower() or 
                             (repo.get("description") and search_term.lower() in repo["description"].lower())]
        else:
            filtered_repos = repositories
        
        # 정렬 옵션
        sort_option = st.selectbox("정렬 기준", ["최근 활동순", "이름순", "생성일순"])
        
        # 정렬
        if sort_option == "최근 활동순":
            filtered_repos.sort(key=lambda x: x["last_activity_at"], reverse=True)
        elif sort_option == "이름순":
            filtered_repos.sort(key=lambda x: x["name"].lower())
        elif sort_option == "생성일순":
            filtered_repos.sort(key=lambda x: x["created_at"], reverse=True)
        
        # 저장소 목록 표시
        st.write(f"총 {len(filtered_repos)}개의 저장소가 있습니다.")
        
        # 데이터프레임 생성
        df = pd.DataFrame([{
            "ID": repo["id"],
            "그룹": repo["namespace"]["name"],
            "프로젝트": repo["name"],
            "설명": repo.get("description", ""),
            "URL": repo["web_url"],
            "생성일": repo["created_at"],
            "최근 활동": repo["last_activity_at"]
        } for repo in filtered_repos])
        
        # 데이터프레임 표시
        st.dataframe(df)
        
        # 선택한 저장소의 상세 정보 표시
        st.subheader("저장소 상세 정보")
        repo_id = st.number_input("저장소 ID", min_value=1, value=1)
        
        if st.button("상세 정보 조회"):
            with st.spinner("저장소 정보를 불러오는 중입니다..."):
                repo_details = get_repository_details(repo_id)
                
                if repo_details:
                    # 저장소 정보 표시
                    st.write("### 기본 정보")
                    st.json({
                        "ID": repo_details["id"],
                        "이름": repo_details["name"],
                        "그룹": repo_details["namespace"]["name"],
                        "설명": repo_details.get("description", ""),
                        "URL": repo_details["web_url"],
                        "생성일": repo_details["created_at"],
                        "최근 활동": repo_details["last_activity_at"],
                        "가시성": repo_details["visibility"]
                    })
                    
                    # 멤버 정보 불러오기
                    members = get_project_members(repo_id)
                    
                    if members:
                        st.write("### 멤버 정보")
                        
                        # 멤버 데이터프레임 생성
                        members_df = pd.DataFrame([{
                            "ID": member["id"],
                            "이름": member["name"],
                            "사용자명": member["username"],
                            "이메일": member.get("email", ""),
                            "권한": get_access_level_name(member["access_level"]),
                            "추가일": member.get("created_at", "")
                        } for member in members])
                        
                        # 멤버 데이터프레임 표시
                        st.dataframe(members_df)
                        
                        # CSV 다운로드 버튼
                        csv = members_df.to_csv(index=False)
                        st.download_button(
                            label="멤버 목록 CSV 다운로드",
                            data=csv,
                            file_name=f"gitlab_repo_{repo_id}_members.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("저장소 멤버 정보를 불러오는데 실패했습니다.")
                    
                    # 커밋 정보 불러오기
                    commits = get_repository_commits(repo_id)
                    
                    if commits:
                        st.write("### 최근 커밋 정보")
                        
                        # 커밋 데이터프레임 생성
                        commits_df = pd.DataFrame([{
                            "SHA": commit["id"][:8],
                            "작성자": commit["author_name"],
                            "메시지": commit["message"].split("\n")[0][:50],
                            "일시": commit["created_at"]
                        } for commit in commits])
                        
                        # 커밋 데이터프레임 표시
                        st.dataframe(commits_df)
                    else:
                        st.info("저장소 커밋 정보를 불러오는데 실패했습니다.")
                else:
                    st.error("저장소 정보를 불러오는데 실패했습니다.")
        
        # CSV 다운로드 버튼
        csv = df.to_csv(index=False)
        st.download_button(
            label="저장소 목록 CSV 다운로드",
            data=csv,
            file_name="gitlab_repositories.csv",
            mime="text/csv"
        )
    else:
        st.info("'저장소 목록 갱신' 버튼을 클릭하여 저장소 목록을 불러와주세요.")

def show_user_management():
    """사용자 관리 화면"""
    st.subheader("사용자 관리")
    
    # GitLab 연결 확인
    if not check_gitlab_connection():
        st.error("GitLab 연결에 실패했습니다. GitLab 설정을 확인해주세요.")
        return
    
    # 사용자 목록 불러오기
    if st.button("사용자 목록 갱신"):
        with st.spinner("사용자 목록을 불러오는 중입니다..."):
            users = get_all_users()
            
            if users:
                # 세션 상태에 저장
                st.session_state.gitlab_users = users
                st.success(f"총 {len(users)}개의 사용자를 불러왔습니다.")
            else:
                st.error("사용자 목록을 불러오는데 실패했습니다.")
    
    # 사용자 목록 표시
    if hasattr(st.session_state, 'gitlab_users'):
        users = st.session_state.gitlab_users
        
        # 검색 필터
        search_term = st.text_input("사용자 검색 (이름, 사용자명, 이메일)")
        
        # 필터링
        if search_term:
            filtered_users = [user for user in users if 
                             search_term.lower() in user["name"].lower() or 
                             search_term.lower() in user["username"].lower() or 
                             (user.get("email") and search_term.lower() in user["email"].lower())]
        else:
            filtered_users = users
        
        # 사용자 상태 필터
        status_filter = st.selectbox("상태 필터", ["모두", "활성", "차단됨"])
        
        if status_filter == "활성":
            filtered_users = [user for user in filtered_users if user["state"] == "active"]
        elif status_filter == "차단됨":
            filtered_users = [user for user in filtered_users if user["state"] == "blocked"]
        
        # 사용자 목록 표시
        st.write(f"총 {len(filtered_users)}명의 사용자가 있습니다.")
        
        # 데이터프레임 생성
        df = pd.DataFrame([{
            "ID": user["id"],
            "이름": user["name"],
            "사용자명": user["username"],
            "이메일": user.get("email", ""),
            "상태": "활성" if user["state"] == "active" else "차단됨",
            "관리자": "예" if user.get("is_admin", False) else "아니오",
            "마지막 로그인": user.get("last_sign_in_at", "")
        } for user in filtered_users])
        
        # 데이터프레임 표시
        st.dataframe(df)
        
        # 선택한 사용자의 상세 정보 표시
        st.subheader("사용자 상세 정보")
        user_id = st.number_input("사용자 ID", min_value=1, value=1)
        
        if st.button("상세 정보 조회"):
            with st.spinner("사용자 정보를 불러오는 중입니다..."):
                user_details = get_user_details(user_id)
                
                if user_details:
                    # 사용자 정보 표시
                    st.write("### 기본 정보")
                    st.json({
                        "ID": user_details["id"],
                        "이름": user_details["name"],
                        "사용자명": user_details["username"],
                        "이메일": user_details.get("email", ""),
                        "상태": "활성" if user_details["state"] == "active" else "차단됨",
                        "관리자": "예" if user_details.get("is_admin", False) else "아니오",
                        "마지막 로그인": user_details.get("last_sign_in_at", ""),
                        "생성일": user_details["created_at"]
                    })
                    
                    # 사용자 프로젝트 정보 불러오기
                    projects = get_user_projects(user_id)
                    
                    if projects:
                        st.write("### 프로젝트 정보")
                        
                        # 프로젝트 데이터프레임 생성
                        projects_df = pd.DataFrame([{
                            "ID": project["id"],
                            "그룹": project["namespace"]["name"],
                            "프로젝트": project["name"],
                            "접근 레벨": get_access_level_name(project["access_level"]),
                            "URL": project["web_url"]
                        } for project in projects])
                        
                        # 프로젝트 데이터프레임 표시
                        st.dataframe(projects_df)
                        
                        # CSV 다운로드 버튼
                        csv = projects_df.to_csv(index=False)
                        st.download_button(
                            label="프로젝트 목록 CSV 다운로드",
                            data=csv,
                            file_name=f"gitlab_user_{user_id}_projects.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("사용자 프로젝트 정보를 불러오는데 실패했습니다.")
                else:
                    st.error("사용자 정보를 불러오는데 실패했습니다.")
        
        # CSV 다운로드 버튼
        csv = df.to_csv(index=False)
        st.download_button(
            label="사용자 목록 CSV 다운로드",
            data=csv,
            file_name="gitlab_users.csv",
            mime="text/csv"
        )
    else:
        st.info("'사용자 목록 갱신' 버튼을 클릭하여 사용자 목록을 불러와주세요.")

def show_unused_repositories():
    """미사용 저장소 화면"""
    st.subheader("미사용 저장소")
    
    # GitLab 연결 확인
    if not check_gitlab_connection():
        st.error("GitLab 연결에 실패했습니다. GitLab 설정을 확인해주세요.")
        return
    
    # 기간 선택
    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox("비활성 기간", ["3개월", "6개월", "1년", "2년"])
    
    # 저장소 목록 불러오기
    if st.button("미사용 저장소 조회"):
        with st.spinner("저장소 목록을 분석하는 중입니다..."):
            # 기간에 따른 날짜 계산
            if period == "3개월":
                days = 90
            elif period == "6개월":
                days = 180
            elif period == "1년":
                days = 365
            elif period == "2년":
                days = 730
            
            # 미사용 저장소 목록 불러오기
            unused_repos = get_unused_repositories(days)
            
            if unused_repos:
                # 세션 상태에 저장
                st.session_state.unused_repos = unused_repos
                st.success(f"총 {len(unused_repos)}개의 미사용 저장소를 발견했습니다.")
            else:
                st.info("미사용 저장소가 없습니다.")
    
    # 미사용 저장소 목록 표시
    if hasattr(st.session_state, 'unused_repos'):
        unused_repos = st.session_state.unused_repos
        
        # 데이터프레임 생성
        df = pd.DataFrame([{
            "ID": repo["id"],
            "그룹": repo["namespace"]["name"],
            "프로젝트": repo["name"],
            "설명": repo.get("description", ""),
            "URL": repo["web_url"],
            "생성일": repo["created_at"],
            "최근 활동": repo["last_activity_at"],
            "소유자": repo.get("owner_name", "알 수 없음")
        } for repo in unused_repos])
        
        # 데이터프레임 표시
        st.dataframe(df)
        
        # CSV 다운로드 버튼
        csv = df.to_csv(index=False)
        st.download_button(
            label="미사용 저장소 목록 CSV 다운로드",
            data=csv,
            file_name=f"gitlab_unused_repos_{period}.csv",
            mime="text/csv"
        )
    else:
        st.info("'미사용 저장소 조회' 버튼을 클릭하여 미사용 저장소 목록을 불러와주세요.")

def show_gitlab_settings():
    """GitLab 설정 화면"""
    st.subheader("GitLab 설정")
    
    # 현재 설정된 GitLab 정보 불러오기
    gitlab_host = os.environ.get("GITLAB_HOST", "")
    gitlab_token = os.environ.get("GITLAB_TOKEN", "")
    
    # GitLab 설정 입력 폼
    with st.form("gitlab_settings_form"):
        new_gitlab_host = st.text_input("GitLab 서버 주소", value=gitlab_host)
        new_gitlab_token = st.text_input("개인 액세스 토큰", value=gitlab_token, type="password")
        
        # 저장 버튼
        submit_button = st.form_submit_button("설정 저장")
        
        if submit_button:
            # .env 파일 업데이트
            update_env_file({
                "GITLAB_HOST": new_gitlab_host,
                "GITLAB_TOKEN": new_gitlab_token
            })
            
            st.success("GitLab 설정이 저장되었습니다.")
    
    # GitLab 연결 테스트 버튼
    if st.button("연결 테스트"):
        if check_gitlab_connection():
            st.success("GitLab 연결에 성공했습니다.")
        else:
            st.error("GitLab 연결에 실패했습니다. 설정을 확인해주세요.")

def check_gitlab_connection():
    """GitLab 연결 테스트"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return False
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        url = f"{gitlab_host}/api/v4/version"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return True
    except Exception as e:
        st.error(f"GitLab 연결 실패: {e}")
        return False

def get_all_repositories():
    """모든 GitLab 저장소 목록 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return []
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        projects = []
        page = 1
        
        while True:
            url = f"{gitlab_host}/api/v4/projects?per_page=100&page={page}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                break
            
            projects.extend(data)
            page += 1
            time.sleep(0.5)  # API 요청 제한 방지
        
        return projects
    except Exception as e:
        st.error(f"저장소 목록 조회 실패: {e}")
        return []

def get_repository_details(repo_id):
    """저장소 상세 정보 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return None
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        url = f"{gitlab_host}/api/v4/projects/{repo_id}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"저장소 상세 정보 조회 실패: {e}")
        return None

def get_project_members(project_id):
    """프로젝트 멤버 목록 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return []
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        members = []
        page = 1
        
        while True:
            url = f"{gitlab_host}/api/v4/projects/{project_id}/members/all?per_page=100&page={page}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 404:
                return []
            
            response.raise_for_status()
            
            data = response.json()
            if not data:
                break
            
            members.extend(data)
            page += 1
            time.sleep(0.5)  # API 요청 제한 방지
        
        return members
    except Exception as e:
        st.error(f"프로젝트 멤버 조회 실패: {e}")
        return []

def get_repository_commits(repo_id):
    """저장소 커밋 목록 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return []
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        url = f"{gitlab_host}/api/v4/projects/{repo_id}/repository/commits?per_page=20"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            return []
        
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"저장소 커밋 조회 실패: {e}")
        return []

def get_all_users():
    """모든 GitLab 사용자 목록 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return []
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        users = []
        page = 1
        
        while True:
            url = f"{gitlab_host}/api/v4/users?per_page=100&page={page}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                break
            
            users.extend(data)
            page += 1
            time.sleep(0.5)  # API 요청 제한 방지
        
        return users
    except Exception as e:
        st.error(f"사용자 목록 조회 실패: {e}")
        return []

def get_user_details(user_id):
    """사용자 상세 정보 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return None
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        url = f"{gitlab_host}/api/v4/users/{user_id}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"사용자 상세 정보 조회 실패: {e}")
        return None

def get_user_projects(user_id):
    """사용자 프로젝트 목록 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return []
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        url = f"{gitlab_host}/api/v4/users/{user_id}/projects"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"사용자 프로젝트 조회 실패: {e}")
        return []

def get_unused_repositories(days):
    """미사용 저장소 목록 조회"""
    try:
        # 모든 저장소 목록 조회
        repositories = get_all_repositories()
        
        if not repositories:
            return []
        
        # 현재 날짜
        now = datetime.now()
        
        # 미사용 저장소 필터링
        unused_repos = []
        
        for repo in repositories:
            # 마지막 활동 날짜
            last_activity_at = datetime.strptime(repo["last_activity_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
            
            # 미사용 기간 계산
            delta = now - last_activity_at
            
            if delta.days > days:
                # 저장소 소유자 정보 추가
                members = get_project_members(repo["id"])
                
                if members:
                    for member in members:
                        if member["access_level"] == 50:  # Owner
                            repo["owner_name"] = member["name"]
                            break
                
                unused_repos.append(repo)
        
        return unused_repos
    except Exception as e:
        st.error(f"미사용 저장소 조회 실패: {e}")
        return []

def get_access_level_name(access_level):
    """접근 레벨 숫자를 이름으로 변환"""
    if access_level == 10:
        return "Guest"
    elif access_level == 20:
        return "Reporter"
    elif access_level == 30:
        return "Developer"
    elif access_level == 40:
        return "Maintainer"
    elif access_level == 50:
        return "Owner"
    else:
        return f"Unknown ({access_level})"

def update_env_file(new_values):
    """환경 변수 파일 업데이트
    
    Args:
        new_values (dict): 새 환경 변수 값
    """
    # .env 파일 읽기
    env_path = ".env"
    env_vars = {}
    
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env_vars[key] = value
    
    # 새 값으로 업데이트
    env_vars.update(new_values)
    
    # .env 파일 쓰기
    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")