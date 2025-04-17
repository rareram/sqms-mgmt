import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime, timedelta
import time
from modules.utils.version import show_version_info, save_repo_url, load_repo_url

# 모듈 ID와 버전 정보
MODULE_ID = "redmine_manager"
VERSION = "v0.1.1"
DEFAULT_REPO_URL = "https://github.com/redmine/redmine/tags"

def show_module():
    """Redmine 관리 모듈 메인 화면"""
    st.title("Redmine 관리")

    # 버전 정보 표시
    st.caption(f"모듈 버전: {VERSION}")
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs(["프로젝트 관리", "사용자 관리", "Redmine 설정", "버전 정보"])
    
    # 프로젝트 관리 탭
    with tab1:
        show_project_management()
    
    # 사용자 관리 탭
    with tab2:
        show_user_management()
    
    # Redmine 설정 탭
    with tab3:
        show_redmine_settings()

    # 버전 정보 탭
    with tab4:
        show_version_tab()

def show_project_management():
    """프로젝트 관리 화면"""
    st.subheader("프로젝트 관리")
    
    # Redmine 연결 확인
    if not check_redmine_connection():
        st.error("Redmine 연결에 실패했습니다. Redmine 설정을 확인해주세요.")
        return
    
    # 프로젝트 목록 불러오기
    if st.button("프로젝트 목록 갱신"):
        with st.spinner("프로젝트 목록을 불러오는 중입니다..."):
            projects = get_all_projects()
            
            if projects:
                # 세션 상태에 저장
                st.session_state.redmine_projects = projects
                st.success(f"총 {len(projects)}개의 프로젝트를 불러왔습니다.")
            else:
                st.error("프로젝트 목록을 불러오는데 실패했습니다.")
    
    # 프로젝트 목록 표시
    if hasattr(st.session_state, 'redmine_projects'):
        projects = st.session_state.redmine_projects
        
        # 검색 필터
        search_term = st.text_input("프로젝트 검색 (이름, 설명)")
        
        # 필터링
        if search_term:
            filtered_projects = [project for project in projects if 
                             search_term.lower() in project["name"].lower() or 
                             (project.get("description") and search_term.lower() in project["description"].lower())]
        else:
            filtered_projects = projects
        
        # 상태 필터
        status_filter = st.selectbox("상태 필터", ["모두", "활성", "보관됨"])
        
        if status_filter == "활성":
            filtered_projects = [project for project in filtered_projects if project["status"] == 1]
        elif status_filter == "보관됨":
            filtered_projects = [project for project in filtered_projects if project["status"] == 9]
        
        # 프로젝트 목록 표시
        st.write(f"총 {len(filtered_projects)}개의 프로젝트가 있습니다.")
        
        # 데이터프레임 생성
        df = pd.DataFrame([{
            "ID": project["id"],
            "이름": project["name"],
            "식별자": project["identifier"],
            "설명": project.get("description", ""),
            "상태": "활성" if project["status"] == 1 else "보관됨",
            "생성일": project.get("created_on", ""),
            "업데이트": project.get("updated_on", "")
        } for project in filtered_projects])
        
        # 데이터프레임 표시
        st.dataframe(df)
        
        # 선택한 프로젝트의 상세 정보 표시
        st.subheader("프로젝트 상세 정보")
        project_id = st.number_input("프로젝트 ID", min_value=1, value=1)
        
        if st.button("상세 정보 조회"):
            with st.spinner("프로젝트 정보를 불러오는 중입니다..."):
                project_details = get_project_details(project_id)
                
                if project_details:
                    # 프로젝트 정보 표시
                    st.write("### 기본 정보")
                    st.json({
                        "ID": project_details["id"],
                        "이름": project_details["name"],
                        "식별자": project_details["identifier"],
                        "설명": project_details.get("description", ""),
                        "상태": "활성" if project_details["status"] == 1 else "보관됨",
                        "생성일": project_details.get("created_on", ""),
                        "업데이트": project_details.get("updated_on", "")
                    })
                    
                    # 멤버 정보 불러오기
                    memberships = get_project_memberships(project_id)
                    
                    if memberships:
                        st.write("### 멤버 정보")
                        
                        # 멤버 데이터프레임 생성
                        members_df = pd.DataFrame([{
                            "ID": member["id"],
                            "사용자": member.get("user", {}).get("name", "") if "user" in member else "",
                            "역할": ", ".join([role["name"] for role in member.get("roles", [])]),
                            "그룹": member.get("group", {}).get("name", "") if "group" in member else ""
                        } for member in memberships])
                        
                        # 멤버 데이터프레임 표시
                        st.dataframe(members_df)
                        
                        # CSV 다운로드 버튼
                        csv = members_df.to_csv(index=False)
                        st.download_button(
                            label="멤버 목록 CSV 다운로드",
                            data=csv,
                            file_name=f"redmine_project_{project_id}_members.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("프로젝트 멤버 정보를 불러오는데 실패했습니다.")
                    
                    # 이슈 정보 불러오기
                    issues = get_project_issues(project_id)
                    
                    if issues:
                        st.write("### 이슈 정보")
                        
                        # 최근 업데이트된 이슈 찾기
                        latest_issues = sorted(issues, key=lambda x: x.get("updated_on", ""), reverse=True)[:10]
                        
                        # 이슈 데이터프레임 생성
                        issues_df = pd.DataFrame([{
                            "ID": issue["id"],
                            "제목": issue["subject"],
                            "상태": issue.get("status", {}).get("name", ""),
                            "담당자": issue.get("assigned_to", {}).get("name", "") if "assigned_to" in issue else "",
                            "업데이트": issue.get("updated_on", "")
                        } for issue in latest_issues])
                        
                        # 이슈 데이터프레임 표시
                        st.dataframe(issues_df)
                        
                        # 이슈 상태별 통계
                        st.write("### 이슈 상태별 통계")
                        
                        # 상태별 카운트
                        status_counts = {}
                        for issue in issues:
                            status = issue.get("status", {}).get("name", "알 수 없음")
                            status_counts[status] = status_counts.get(status, 0) + 1
                        
                        # 상태별 통계 데이터프레임
                        status_df = pd.DataFrame([{"상태": status, "개수": count} for status, count in status_counts.items()])
                        
                        # 차트 표시
                        st.bar_chart(status_df.set_index("상태"))
                    else:
                        st.info("프로젝트 이슈 정보를 불러오는데 실패했습니다.")
                else:
                    st.error("프로젝트 정보를 불러오는데 실패했습니다.")
        
        # 비활성 프로젝트 조회
        st.subheader("비활성 프로젝트 조회")
        
        col1, col2 = st.columns(2)
        with col1:
            inactive_days = st.number_input("비활성 기간 (일)", min_value=30, value=180, step=30)
        
        if st.button("비활성 프로젝트 조회"):
            with st.spinner("비활성 프로젝트를 조회 중입니다..."):
                inactive_projects = get_inactive_projects(filtered_projects, inactive_days)
                
                if inactive_projects:
                    st.write(f"총 {len(inactive_projects)}개의 비활성 프로젝트가 있습니다.")
                    
                    # 데이터프레임 생성
                    inactive_df = pd.DataFrame([{
                        "ID": project["id"],
                        "이름": project["name"],
                        "식별자": project["identifier"],
                        "설명": project.get("description", ""),
                        "상태": "활성" if project["status"] == 1 else "보관됨",
                        "생성일": project.get("created_on", ""),
                        "업데이트": project.get("updated_on", ""),
                        "마지막 업데이트 (일)": project.get("days_since_update", 0)
                    } for project in inactive_projects])
                    
                    # 데이터프레임 표시
                    st.dataframe(inactive_df)
                    
                    # CSV 다운로드 버튼
                    csv = inactive_df.to_csv(index=False)
                    st.download_button(
                        label="비활성 프로젝트 CSV 다운로드",
                        data=csv,
                        file_name=f"redmine_inactive_projects_{inactive_days}days.csv",
                        mime="text/csv"
                    )
                else:
                    st.info(f"{inactive_days}일 이상 비활성 상태인 프로젝트가 없습니다.")
        
        # CSV 다운로드 버튼
        csv = df.to_csv(index=False)
        st.download_button(
            label="프로젝트 목록 CSV 다운로드",
            data=csv,
            file_name="redmine_projects.csv",
            mime="text/csv"
        )
    else:
        st.info("'프로젝트 목록 갱신' 버튼을 클릭하여 프로젝트 목록을 불러와주세요.")

def show_user_management():
    """사용자 관리 화면"""
    st.subheader("사용자 관리")
    
    # Redmine 연결 확인
    if not check_redmine_connection():
        st.error("Redmine 연결에 실패했습니다. Redmine 설정을 확인해주세요.")
        return
    
    # 사용자 목록 불러오기
    if st.button("사용자 목록 갱신"):
        with st.spinner("사용자 목록을 불러오는 중입니다..."):
            users = get_all_users()
            
            if users:
                # 세션 상태에 저장
                st.session_state.redmine_users = users
                st.success(f"총 {len(users)}명의 사용자를 불러왔습니다.")
            else:
                st.error("사용자 목록을 불러오는데 실패했습니다.")
    
    # 사용자 목록 표시
    if hasattr(st.session_state, 'redmine_users'):
        users = st.session_state.redmine_users
        
        # 검색 필터
        search_term = st.text_input("사용자 검색 (이름, 로그인명)")
        
        # 필터링
        if search_term:
            filtered_users = [user for user in users if 
                             search_term.lower() in user["firstname"].lower() or
                             search_term.lower() in user["lastname"].lower() or
                             search_term.lower() in user["login"].lower()]
        else:
            filtered_users = users
        
        # 상태 필터
        status_filter = st.selectbox("상태 필터", ["모두", "활성", "잠금"])
        
        if status_filter == "활성":
            filtered_users = [user for user in filtered_users if user["status"] == 1]
        elif status_filter == "잠금":
            filtered_users = [user for user in filtered_users if user["status"] == 3]
        
        # 사용자 목록 표시
        st.write(f"총 {len(filtered_users)}명의 사용자가 있습니다.")
        
        # 데이터프레임 생성
        df = pd.DataFrame([{
            "ID": user["id"],
            "이름": f"{user['firstname']} {user['lastname']}",
            "로그인명": user["login"],
            "이메일": user.get("mail", ""),
            "상태": "활성" if user["status"] == 1 else "잠금",
            "관리자": "예" if user.get("admin", False) else "아니오",
            "마지막 로그인": user.get("last_login_on", "")
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
                        "이름": f"{user_details['firstname']} {user_details['lastname']}",
                        "로그인명": user_details["login"],
                        "이메일": user_details.get("mail", ""),
                        "상태": "활성" if user_details["status"] == 1 else "잠금",
                        "관리자": "예" if user_details.get("admin", False) else "아니오",
                        "마지막 로그인": user_details.get("last_login_on", ""),
                        "생성일": user_details.get("created_on", "")
                    })
                    
                    # 사용자 멤버십 정보 불러오기
                    memberships = get_user_memberships(user_id)
                    
                    if memberships:
                        st.write("### 프로젝트 정보")
                        
                        # 프로젝트 데이터프레임 생성
                        projects_df = pd.DataFrame([{
                            "ID": membership["id"],
                            "프로젝트": membership.get("project", {}).get("name", ""),
                            "역할": ", ".join([role["name"] for role in membership.get("roles", [])])
                        } for membership in memberships])
                        
                        # 프로젝트 데이터프레임 표시
                        st.dataframe(projects_df)
                        
                        # CSV 다운로드 버튼
                        csv = projects_df.to_csv(index=False)
                        st.download_button(
                            label="프로젝트 목록 CSV 다운로드",
                            data=csv,
                            file_name=f"redmine_user_{user_id}_projects.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("사용자 멤버십 정보를 불러오는데 실패했습니다.")
                else:
                    st.error("사용자 정보를 불러오는데 실패했습니다.")
        
        # CSV 다운로드 버튼
        csv = df.to_csv(index=False)
        st.download_button(
            label="사용자 목록 CSV 다운로드",
            data=csv,
            file_name="redmine_users.csv",
            mime="text/csv"
        )
    else:
        st.info("'사용자 목록 갱신' 버튼을 클릭하여 사용자 목록을 불러와주세요.")

def show_redmine_settings():
    """Redmine 설정 화면"""
    st.subheader("Redmine 설정")
    
    # 현재 설정된 Redmine 정보 불러오기
    redmine_url = os.environ.get("REDMINE_URL", "")
    redmine_api_key = os.environ.get("REDMINE_API_KEY", "")
    
    # Redmine 설정 입력 폼
    with st.form("redmine_settings_form"):
        new_redmine_url = st.text_input("Redmine 서버 주소", value=redmine_url)
        new_redmine_api_key = st.text_input("API 키", value=redmine_api_key, type="password")
        
        # 저장 버튼
        submit_button = st.form_submit_button("설정 저장")
        
        if submit_button:
            # .env 파일 업데이트
            update_env_file({
                "REDMINE_URL": new_redmine_url,
                "REDMINE_API_KEY": new_redmine_api_key
            })
            
            st.success("Redmine 설정이 저장되었습니다.")
    
    # Redmine 연결 테스트 버튼
    if st.button("연결 테스트"):
        if check_redmine_connection():
            st.success("Redmine 연결에 성공했습니다.")
        else:
            st.error("Redmine 연결에 실패했습니다. 설정을 확인해주세요.")

def check_redmine_connection():
    """Redmine 연결 테스트"""
    try:
        redmine_url = os.environ.get("REDMINE_URL")
        redmine_api_key = os.environ.get("REDMINE_API_KEY")
        
        if not all([redmine_url, redmine_api_key]):
            return False
        
        headers = {"X-Redmine-API-Key": redmine_api_key}
        url = f"{redmine_url}/users/current.json"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return True
    except Exception as e:
        st.error(f"Redmine 연결 실패: {e}")
        return False

def get_all_projects():
    """모든 Redmine 프로젝트 목록 조회"""
    try:
        redmine_url = os.environ.get("REDMINE_URL")
        redmine_api_key = os.environ.get("REDMINE_API_KEY")
        
        if not all([redmine_url, redmine_api_key]):
            return []
        
        headers = {"X-Redmine-API-Key": redmine_api_key}
        projects = []
        offset = 0
        limit = 100
        
        while True:
            url = f"{redmine_url}/projects.json?offset={offset}&limit={limit}&include=trackers,issue_categories"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if not data["projects"]:
                break
            
            projects.extend(data["projects"])
            
            if len(data["projects"]) < limit:
                break
            
            offset += limit
            time.sleep(0.5)  # API 요청 제한 방지
        
        return projects
    except Exception as e:
        st.error(f"프로젝트 목록 조회 실패: {e}")
        return []

def get_project_details(project_id):
    """프로젝트 상세 정보 조회"""
    try:
        redmine_url = os.environ.get("REDMINE_URL")
        redmine_api_key = os.environ.get("REDMINE_API_KEY")
        
        if not all([redmine_url, redmine_api_key]):
            return None
        
        headers = {"X-Redmine-API-Key": redmine_api_key}
        url = f"{redmine_url}/projects/{project_id}.json?include=trackers,issue_categories"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()["project"]
    except Exception as e:
        st.error(f"프로젝트 상세 정보 조회 실패: {e}")
        return None

def get_project_memberships(project_id):
    """프로젝트 멤버십 목록 조회"""
    try:
        redmine_url = os.environ.get("REDMINE_URL")
        redmine_api_key = os.environ.get("REDMINE_API_KEY")
        
        if not all([redmine_url, redmine_api_key]):
            return []
        
        headers = {"X-Redmine-API-Key": redmine_api_key}
        url = f"{redmine_url}/projects/{project_id}/memberships.json"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()["memberships"]
    except Exception as e:
        st.error(f"프로젝트 멤버십 조회 실패: {e}")
        return []

def get_project_issues(project_id):
    """프로젝트 이슈 목록 조회"""
    try:
        redmine_url = os.environ.get("REDMINE_URL")
        redmine_api_key = os.environ.get("REDMINE_API_KEY")
        
        if not all([redmine_url, redmine_api_key]):
            return []
        
        headers = {"X-Redmine-API-Key": redmine_api_key}
        issues = []
        offset = 0
        limit = 100
        
        while True:
            url = f"{redmine_url}/issues.json?project_id={project_id}&offset={offset}&limit={limit}&status_id=*&include=status,priority,assigned_to"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if not data["issues"]:
                break
            
            issues.extend(data["issues"])
            
            if len(data["issues"]) < limit:
                break
            
            offset += limit
            time.sleep(0.5)  # API 요청 제한 방지
        
        return issues
    except Exception as e:
        st.error(f"프로젝트 이슈 조회 실패: {e}")
        return []

def get_all_users():
    """모든 Redmine 사용자 목록 조회"""
    try:
        redmine_url = os.environ.get("REDMINE_URL")
        redmine_api_key = os.environ.get("REDMINE_API_KEY")
        
        if not all([redmine_url, redmine_api_key]):
            return []
        
        headers = {"X-Redmine-API-Key": redmine_api_key}
        users = []
        offset = 0
        limit = 100
        
        while True:
            url = f"{redmine_url}/users.json?offset={offset}&limit={limit}&status=*"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if not data["users"]:
                break
            
            users.extend(data["users"])
            
            if len(data["users"]) < limit:
                break
            
            offset += limit
            time.sleep(0.5)  # API 요청 제한 방지
        
        return users
    except Exception as e:
        st.error(f"사용자 목록 조회 실패: {e}")
        return []

def get_user_details(user_id):
    """사용자 상세 정보 조회"""
    try:
        redmine_url = os.environ.get("REDMINE_URL")
        redmine_api_key = os.environ.get("REDMINE_API_KEY")
        
        if not all([redmine_url, redmine_api_key]):
            return None
        
        headers = {"X-Redmine-API-Key": redmine_api_key}
        url = f"{redmine_url}/users/{user_id}.json?include=memberships,groups"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()["user"]
    except Exception as e:
        st.error(f"사용자 상세 정보 조회 실패: {e}")
        return None

def get_user_memberships(user_id):
    """사용자 멤버십 목록 조회"""
    try:
        # 사용자 상세 정보에서 멤버십 정보 추출
        user_details = get_user_details(user_id)
        
        if user_details and "memberships" in user_details:
            return user_details["memberships"]
        
        return []
    except Exception as e:
        st.error(f"사용자 멤버십 조회 실패: {e}")
        return []

def get_inactive_projects(projects, inactive_days):
    """비활성 프로젝트 목록 조회"""
    try:
        # 현재 날짜
        now = datetime.now()
        
        # 비활성 프로젝트 필터링
        inactive_projects = []
        
        for project in projects:
            # 마지막 업데이트 날짜
            updated_on = datetime.strptime(project["updated_on"], "%Y-%m-%dT%H:%M:%SZ")
            
            # 비활성 기간 계산
            delta = now - updated_on
            
            if delta.days > inactive_days:
                # 비활성 일수 추가
                project["days_since_update"] = delta.days
                inactive_projects.append(project)
        
        # 비활성 일수 기준으로 정렬
        inactive_projects.sort(key=lambda x: x["days_since_update"], reverse=True)
        
        return inactive_projects
    except Exception as e:
        st.error(f"비활성 프로젝트 조회 실패: {e}")
        return []

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

# 버전 정보 탭
def show_version_tab():
    """버전 정보 탭 내용"""
    st.subheader("버전 정보")

    # 저장된 저장소 URL 로드 또는 기본값 사용
    repo_url = load_repo_url(MODULE_ID) or DEFAULT_REPO_URL

    # 저장소 URL 설정 폼
    with st.expander("저장소 URL 설정", expanded=False):
        with st.form("repo_url_form"):
            new_repo_url = st.text_input("저장소 URL", value=repo_url, help="GitHub 릴리즈/태그 또는 GitLab 태그 URL")
            submit = st.form_submit_button("저장")

            if submit and new_repo_url:
                if save_repo_url(MODULE_ID, new_repo_url):
                    st.success("저장소 URL이 저장되었습니다.")
                    repo_url = new_repo_url

    # 버전 정보 표시
    show_version_info(VERSION, repo_url)

    # Redmine 버전 정보 표시
    st.subheader("Redmine 서버 정보")
    if st.button("Redmine 서버 버전 확인"):
        with st.spinner("Redmine 서버 버전을 확인 중입니다..."):
            redmine_version = get_redmine_version()

            if redmine_version:
                st.success("Redmine 서버 연결 성공")
                if 'version' in redmine_version:
                    st.write(f"버전: {redmine_version['version']}")
                else:
                    st.write("버전 정보를 확인 할 수 없습니다.")
            else:
                st.error("Redmine 서버 연결 실패")
                st.info("Redmine 설정을 확인해주세요.")

def get_redmine_version():
    """Redmine 서버의 버전 정보를 가져옵니다."""
    try:
        redmine_url = os.environ.get("REDMINE_URL")
        redmine_api_key = os.environ.get("REDMINE_API_KEY")
        
        if not all([redmine_url, redmine_api_key]):
            return None
        
        headers = {"X-Redmine-API-Key": redmine_api_key}
        
        # Redmine은 버전 정보를 제공하는 별도의 API가 없어 /users/current.json을 사용
        url = f"{redmine_url}/users/current.json"
        
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        # API 버전은 응답 헤더에서 가져올 수 있음
        api_version = response.headers.get("X-Redmine-API", "알 수 없음")
        
        # 추가 정보 수집 시도
        try:
            # 일부 Redmine 인스턴스에서는 /info 경로에서 버전 정보 확인 가능
            info_url = f"{redmine_url}/admin/info"
            info_response = requests.get(info_url, headers=headers, timeout=5)
            
            if info_response.status_code == 200 and "text/html" in info_response.headers.get("Content-Type", ""):
                # HTML 응답에서 버전 추출 시도
                html_content = info_response.text
                import re
                version_match = re.search(r'Redmine\s+version\s+(\d+\.\d+\.\d+)', html_content)
                if version_match:
                    version = version_match.group(1)
                    return {
                        "version": version,
                        "api_version": api_version
                    }
        except:
            pass
            
        return {
            "api_version": api_version,
            "connected": True
        }
    except Exception as e:
        st.error(f"Redmine 버전 조회 실패: {e}")
        return None