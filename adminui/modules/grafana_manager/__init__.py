import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import os
from datetime import datetime
import time
import urllib.parse
import base64
import urllib3
from modules.utils.version import show_version_info, save_repo_url, load_repo_url

# SSL 경고 억제 (개발용)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_ssl_verify():
    """SSL 검증 설정 반환"""
    return os.environ.get("SSL_VERIFY", "true").lower() != "false"

# 모듈 ID와 버전 정보
MODULE_ID = "grafana_manager"
VERSION = "v0.2.2"
DEFAULT_REPO_URL = "https://github.com/grafana/grafana/tags"

def show_module():
    """Grafana 관리 모듈 메인 화면"""
    st.title("Grafana 관리")

    # 버전 정보 표시
    st.caption(f"모듈 버전: {VERSION}")
    
    # 탭 생성
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["팀 관리", "폴더 권한 관리", "Description 편집기", "Grafana 설정", "버전 정보"])
    
    # 팀 관리 탭
    with tab1:
        show_team_management()
    
    # 폴더 권한 관리 탭
    with tab2:
        show_folder_permission_management()
    
    # Description 편집기 탭
    with tab3:
        show_desc_editor()
    
    # Grafana 설정 탭
    with tab4:
        show_grafana_settings()
    
    # 버전 정보 탭
    with tab5:
        show_version_tab()

def show_team_management():
    """팀 관리 화면"""
    st.subheader("팀 관리")
    
    # Grafana 연결 확인
    if not check_grafana_connection():
        st.error("Grafana 연결에 실패했습니다. Grafana 설정을 확인해주세요.")
        return
    
    # 팀 목록 불러오기
    if st.button("팀 목록 갱신"):
        with st.spinner("팀 목록을 불러오는 중입니다..."):
            teams = get_all_teams()
            
            if teams:
                # 세션 상태에 저장
                st.session_state.grafana_teams = teams
                st.success(f"총 {len(teams)}개의 팀을 불러왔습니다.")
            else:
                st.error("팀 목록을 불러오는데 실패했습니다.")
    
    # 팀 목록 표시
    if hasattr(st.session_state, 'grafana_teams'):
        teams = st.session_state.grafana_teams
        
        # 검색 필터
        search_term = st.text_input("팀 검색 (이름, 이메일)")
        
        # 필터링
        if search_term:
            filtered_teams = [team for team in teams if 
                             search_term.lower() in team["name"].lower() or 
                             (team.get("email") and search_term.lower() in team["email"].lower())]
        else:
            filtered_teams = teams
        
        # 팀 목록 표시
        st.write(f"총 {len(filtered_teams)}개의 팀이 있습니다.")
        
        # 데이터프레임 생성
        df = pd.DataFrame([{
            "ID": team["id"],
            "이름": team["name"],
            "이메일": team.get("email", ""),
            "멤버 수": team.get("memberCount", 0)
        } for team in filtered_teams])
        
        # 데이터프레임 표시
        st.dataframe(df)
        
        # 선택한 팀의 상세 정보 표시
        st.subheader("팀 상세 정보")
        team_id = st.number_input("팀 ID", min_value=1, value=1)
        
        if st.button("상세 정보 조회"):
            with st.spinner("팀 정보를 불러오는 중입니다..."):
                team_details = get_team_details(team_id)
                
                if team_details:
                    # 팀 정보 표시
                    st.write("### 기본 정보")
                    st.json({
                        "ID": team_details["id"],
                        "이름": team_details["name"],
                        "이메일": team_details.get("email", ""),
                        "생성자": team_details.get("orgId", "")
                    })
                    
                    # 팀 멤버 정보 불러오기
                    members = get_team_members(team_id)
                    
                    if members:
                        st.write("### 멤버 정보")
                        
                        # 멤버 데이터프레임 생성
                        members_df = pd.DataFrame([{
                            "ID": member["userId"],
                            "이메일": member.get("email", ""),
                            "로그인": member.get("login", ""),
                            "권한": "관리자" if member.get("permission", 0) == 4 else "멤버"
                        } for member in members])
                        
                        # 멤버 데이터프레임 표시
                        st.dataframe(members_df)
                        
                        # CSV 다운로드 버튼
                        csv = members_df.to_csv(index=False)
                        st.download_button(
                            label="멤버 목록 CSV 다운로드",
                            data=csv,
                            file_name=f"grafana_team_{team_id}_members.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("팀 멤버 정보를 불러오는데 실패했습니다.")
                else:
                    st.error("팀 정보를 불러오는데 실패했습니다.")
        
        # 팀 정보 편집 기능
        st.subheader("팀 정보 편집")
        
        # 편집할 팀 선택
        selected_team_id = st.selectbox("편집할 팀 선택", 
                                     options=[team["id"] for team in filtered_teams],
                                     format_func=lambda x: next((team["name"] for team in filtered_teams if team["id"] == x), ""))
        
        # 선택한 팀 정보 가져오기
        selected_team = next((team for team in filtered_teams if team["id"] == selected_team_id), None)
        
        if selected_team:
            # 팀 정보 편집 폼
            with st.form("edit_team_form"):
                new_team_name = st.text_input("팀 이름", value=selected_team["name"])
                new_team_email = st.text_input("팀 이메일", value=selected_team.get("email", ""))
                
                # 저장 버튼
                submit_button = st.form_submit_button("변경사항 저장")
                
                if submit_button:
                    # 팀 정보 업데이트
                    update_result = update_team_info(selected_team_id, {
                        "name": new_team_name,
                        "email": new_team_email
                    })
                    
                    if update_result:
                        st.success("팀 정보가 업데이트되었습니다.")
                        
                        # 세션 상태의 팀 정보 업데이트
                        for i, team in enumerate(st.session_state.grafana_teams):
                            if team["id"] == selected_team_id:
                                st.session_state.grafana_teams[i]["name"] = new_team_name
                                st.session_state.grafana_teams[i]["email"] = new_team_email
                                break
                    else:
                        st.error("팀 정보 업데이트에 실패했습니다.")
        
        # CSV 다운로드 버튼
        csv = df.to_csv(index=False)
        st.download_button(
            label="팀 목록 CSV 다운로드",
            data=csv,
            file_name="grafana_teams.csv",
            mime="text/csv"
        )
    else:
        st.info("'팀 목록 갱신' 버튼을 클릭하여 팀 목록을 불러와주세요.")

def show_folder_permission_management():
    """폴더 권한 관리 화면"""
    st.subheader("폴더 권한 관리")
    
    # Grafana 연결 확인
    if not check_grafana_connection():
        st.error("Grafana 연결에 실패했습니다. Grafana 설정을 확인해주세요.")
        return
    
    # 폴더 목록 불러오기
    if st.button("폴더 목록 갱신"):
        with st.spinner("폴더 목록을 불러오는 중입니다..."):
            folders = get_all_folders()
            
            if folders:
                # 세션 상태에 저장
                st.session_state.grafana_folders = folders
                st.success(f"총 {len(folders)}개의 폴더를 불러왔습니다.")
            else:
                st.error("폴더 목록을 불러오는데 실패했습니다.")
    
    # 폴더 목록 표시
    if hasattr(st.session_state, 'grafana_folders'):
        folders = st.session_state.grafana_folders
        
        # 검색 필터
        search_term = st.text_input("폴더 검색 (이름)")
        
        # 필터링
        if search_term:
            filtered_folders = [folder for folder in folders if 
                               search_term.lower() in folder["title"].lower()]
        else:
            filtered_folders = folders
        
        # 폴더 목록 표시
        st.write(f"총 {len(filtered_folders)}개의 폴더가 있습니다.")
        
        # 데이터프레임 생성
        df = pd.DataFrame([{
            "ID": folder["id"],
            "UID": folder["uid"],
            "제목": folder["title"],
            "URL": folder.get("url", ""),
            "생성일": folder.get("created", "")
        } for folder in filtered_folders])
        
        # 데이터프레임 표시
        st.dataframe(df)
        
        # 폴더 권한 관리
        st.subheader("폴더 권한 관리")
        
        # 폴더 선택
        selected_folder_uid = st.selectbox("폴더 선택", 
                                       options=[folder["uid"] for folder in filtered_folders],
                                       format_func=lambda x: next((folder["title"] for folder in filtered_folders if folder["uid"] == x), ""))
        
        if st.button("권한 조회"):
            with st.spinner("폴더 권한을 불러오는 중입니다..."):
                permissions = get_folder_permissions(selected_folder_uid)
                
                if permissions:
                    # 세션 상태에 저장
                    st.session_state.folder_permissions = permissions
                    st.success(f"폴더 권한을 불러왔습니다.")
                else:
                    st.error("폴더 권한을 불러오는데 실패했습니다.")
        
        # 폴더 권한 표시
        if hasattr(st.session_state, 'folder_permissions'):
            permissions = st.session_state.folder_permissions
            
            # 권한 유형별로 필터링 (userId가 있으면 user, teamId가 있으면 team)
            team_permissions = [p for p in permissions if p.get("teamId", 0) > 0]
            user_permissions = [p for p in permissions if p.get("userId", 0) > 0]
            
            # 팀 권한 표시
            if team_permissions:
                st.write("### 팀 권한")
                
                # 팀 권한 데이터프레임 생성
                team_df = pd.DataFrame([{
                    "팀 ID": p.get("teamId", 0),
                    "팀 이름": p.get("team", ""),
                    "권한": get_permission_name(p.get("permission", 0))
                } for p in team_permissions])
                
                # 팀 이름이 비어있는 경우에만 API 조회
                for i, row in team_df.iterrows():
                    if not row["팀 이름"] or row["팀 이름"].strip() == "":
                        team_id = row["팀 ID"]
                        if team_id > 0:
                            team_details = get_team_details(team_id)
                            if team_details:
                                team_df.at[i, "팀 이름"] = team_details.get("name", f"팀 ID {team_id}")
                            else:
                                team_df.at[i, "팀 이름"] = f"팀 ID {team_id}"
                
                # 열 순서 조정
                team_df = team_df[["팀 이름", "팀 ID", "권한"]]
                
                # 팀 권한 데이터프레임 표시
                st.dataframe(team_df)
            else:
                st.info("팀 권한이 없습니다.")
            
            # 사용자 권한 표시
            if user_permissions:
                st.write("### 사용자 권한")
                
                # 사용자 권한 데이터프레임 생성
                user_df = pd.DataFrame([{
                    "사용자 ID": p.get("userId", 0),
                    "사용자 로그인": p.get("userLogin", ""),
                    "사용자 이메일": p.get("userEmail", ""),
                    "권한": get_permission_name(p.get("permission", 0))
                } for p in user_permissions])
                
                # 사용자 권한 데이터프레임 표시
                st.dataframe(user_df)
            else:
                st.info("사용자 권한이 없습니다.")
            
            # CSV 다운로드 버튼
            if team_permissions:
                team_csv = team_df.to_csv(index=False)
                st.download_button(
                    label="팀 권한 CSV 다운로드",
                    data=team_csv,
                    file_name=f"grafana_folder_{selected_folder_uid}_team_permissions.csv",
                    mime="text/csv"
                )
        
        # 모든 폴더 권한 내보내기
        st.subheader("모든 폴더 권한 내보내기")
        
        if st.button("모든 폴더 권한 조회"):
            with st.spinner("모든 폴더의 권한을 조회 중입니다..."):
                all_permissions = collect_all_folder_permissions(filtered_folders)
                
                if all_permissions:
                    # CSV 다운로드 버튼
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    csv = all_permissions.to_csv(index=False)
                    st.download_button(
                        label="모든 폴더 권한 CSV 다운로드",
                        data=csv,
                        file_name=f"grafana_all_folder_permissions_{timestamp}.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("폴더 권한 조회에 실패했습니다.")
        
        # CSV 다운로드 버튼
        csv = df.to_csv(index=False)
        st.download_button(
            label="폴더 목록 CSV 다운로드",
            data=csv,
            file_name="grafana_folders.csv",
            mime="text/csv"
        )
    else:
        st.info("'폴더 목록 갱신' 버튼을 클릭하여 폴더 목록을 불러와주세요.")

def show_grafana_settings():
    """Grafana 설정 화면"""
    st.subheader("Grafana 설정")
    
    # 현재 설정된 Grafana 정보 불러오기
    grafana_url = os.environ.get("GRAFANA_URL", "")
    grafana_token = os.environ.get("GRAFANA_API_TOKEN", "")
    
    # Grafana 설정 입력 폼
    with st.form("grafana_settings_form"):
        new_grafana_url = st.text_input("Grafana 서버 주소", value=grafana_url)
        new_grafana_token = st.text_input("API 토큰", value=grafana_token, type="password")

        st.info("API 토큰은 Grafana 웹의 [Administration > User and access > Service accounts] 메뉴에서 생성할 수 있습니다. .")
        
        # 저장 버튼
        submit_button = st.form_submit_button("설정 저장")
        
        if submit_button:
            # .env 파일 업데이트
            update_env_file({
                "GRAFANA_URL": new_grafana_url,
                "GRAFANA_API_TOKEN": new_grafana_token
            })
            
            st.success("Grafana 설정이 저장되었습니다.")
    
    # Grafana 연결 테스트 버튼
    if st.button("연결 테스트"):
        if check_grafana_connection():
            st.success("Grafana 연결에 성공했습니다.")
        else:
            st.error("Grafana 연결에 실패했습니다. 설정을 확인해주세요.")

def check_grafana_connection():
    """Grafana 연결 테스트"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_token = os.environ.get("GRAFANA_API_TOKEN")
        
        if not all([grafana_url, grafana_token]):
            return False
        
        headers = {"Authorization": f"Bearer {grafana_token}"}
        url = f"{grafana_url}/api/org"
        
        response = requests.get(url, headers=headers, verify=get_ssl_verify())
        response.raise_for_status()
        
        return True
    except Exception as e:
        st.error(f"Grafana 연결 실패: {e}")
        return False

def get_all_teams():
    """Grafana 팀 목록 조회"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_token = os.environ.get("GRAFANA_API_TOKEN")
        
        if not all([grafana_url, grafana_token]):
            return []
        
        headers = {"Authorization": f"Bearer {grafana_token}"}
        url = f"{grafana_url}/api/teams/search?perpage=1000"
        
        response = requests.get(url, headers=headers, verify=get_ssl_verify())
        response.raise_for_status()
        
        return response.json()["teams"]
    except Exception as e:
        st.error(f"팀 목록 조회 실패: {e}")
        return []

def get_team_details(team_id):
    """팀 상세 정보 조회"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_token = os.environ.get("GRAFANA_API_TOKEN")
        
        if not all([grafana_url, grafana_token]):
            return None
        
        headers = {"Authorization": f"Bearer {grafana_token}"}
        url = f"{grafana_url}/api/teams/{team_id}"
        
        response = requests.get(url, headers=headers, verify=get_ssl_verify())
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"팀 상세 정보 조회 실패: {e}")
        return None

def get_team_members(team_id):
    """팀 멤버 목록 조회"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_token = os.environ.get("GRAFANA_API_TOKEN")
        
        if not all([grafana_url, grafana_token]):
            return []
        
        headers = {"Authorization": f"Bearer {grafana_token}"}
        url = f"{grafana_url}/api/teams/{team_id}/members"
        
        response = requests.get(url, headers=headers, verify=get_ssl_verify())
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"팀 멤버 조회 실패: {e}")
        return []

def update_team_info(team_id, team_info):
    """팀 정보 업데이트"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_token = os.environ.get("GRAFANA_API_TOKEN")
        
        if not all([grafana_url, grafana_token]):
            return False
        
        headers = {"Authorization": f"Bearer {grafana_token}"}
        url = f"{grafana_url}/api/teams/{team_id}"
        
        response = requests.put(url, headers=headers, json=team_info, verify=get_ssl_verify())
        response.raise_for_status()
        
        return True
    except Exception as e:
        st.error(f"팀 정보 업데이트 실패: {e}")
        return False

def get_all_folders():
    """Grafana 폴더 목록 조회"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_token = os.environ.get("GRAFANA_API_TOKEN")
        
        if not all([grafana_url, grafana_token]):
            return []
        
        headers = {"Authorization": f"Bearer {grafana_token}"}
        
        # 폴더 API 호출
        url = f"{grafana_url}/api/folders"
        
        response = requests.get(url, headers=headers, verify=get_ssl_verify())
        response.raise_for_status()
        
        folders = response.json()
        
        # 응답이 리스트가 아닌 경우 처리
        if isinstance(folders, dict):
            if 'folders' in folders:
                folders = folders['folders']
            else:
                folders = []
        
        # 폴더 정보 정규화
        normalized_folders = []
        for folder in folders:
            normalized_folder = {
                "id": folder.get("id", 0),
                "uid": folder.get("uid", ""),
                "title": folder.get("title", ""),
                "url": f"/dashboards/f/{folder.get('uid', '')}/{folder.get('title', '').replace(' ', '-')}" if folder.get('uid') else "",
                "created": folder.get("created", ""),
                "updated": folder.get("updated", ""),
                "parentUid": folder.get("parentUid", "")
            }
            normalized_folders.append(normalized_folder)
        
        # General 폴더 추가 (항상 첫 번째)
        normalized_folders.insert(0, {"id": 0, "uid": "", "title": "General", "url": "/dashboards", "created": "", "updated": "", "parentUid": ""})
        
        return normalized_folders
    except Exception as e:
        st.error(f"폴더 목록 조회 실패: {e}")
        return []

def get_nested_folders(parent_uid=None):
    """중첩된 폴더 목록 조회"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_token = os.environ.get("GRAFANA_API_TOKEN")
        
        if not all([grafana_url, grafana_token]):
            return []
        
        headers = {"Authorization": f"Bearer {grafana_token}"}
        
        # URL 구성
        url = f"{grafana_url}/api/folders"
        params = {}
        if parent_uid:
            params['parentUid'] = parent_uid
        
        response = requests.get(url, headers=headers, params=params, verify=get_ssl_verify())
        response.raise_for_status()
        
        folders = response.json()
        
        # 응답이 리스트가 아닌 경우 처리
        if isinstance(folders, dict):
            if 'folders' in folders:
                folders = folders['folders']
            else:
                folders = []
        
        # 재귀적으로 하위 폴더 조회
        result = []
        
        for folder in folders:
            result.append(folder)
            try:
                nested = get_nested_folders(folder["uid"])
                result.extend(nested)
            except Exception:
                pass
        
        return result
    except Exception as e:
        st.error(f"중첩 폴더 조회 실패: {e}")
        return []

def get_folder_permissions(folder_uid):
    """폴더 권한 조회"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_token = os.environ.get("GRAFANA_API_TOKEN")
        
        if not all([grafana_url, grafana_token]):
            return []
        
        headers = {"Authorization": f"Bearer {grafana_token}"}
        url = f"{grafana_url}/api/folders/{folder_uid}/permissions"
        
        response = requests.get(url, headers=headers, verify=get_ssl_verify())
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"폴더 권한 조회 실패: {e}")
        return []

def collect_all_folder_permissions(folders):
    """모든 폴더의 권한 정보 수집"""
    try:
        permissions_data = []
        
        for folder in folders:
            folder_uid = folder["uid"]
            folder_title = folder["title"]
            
            # 폴더 권한 조회
            perms = get_folder_permissions(folder_uid)
            
            # 팀 권한만 필터링 (teamId가 있는 것)
            team_perms = [p for p in perms if p.get("teamId", 0) > 0]
            
            for perm in team_perms:
                team_id = perm.get("teamId")
                
                if team_id:
                    # 팀 정보 조회 (API 응답에 이미 있는 경우 우선 사용)
                    team_name = perm.get("team", "")
                    if not team_name:
                        team_info = get_team_details(team_id)
                        team_name = team_info.get("name", f"Team {team_id}") if team_info else f"Team {team_id}"
                    
                    permissions_data.append({
                        "folder_uid": folder_uid,
                        "folder_title": folder_title,
                        "team_id": team_id,
                        "team_name": team_name,
                        "permission": get_permission_name(perm.get("permission", 0)),
                        "parent_folder": folder.get("parentUid", "")
                    })
            
            time.sleep(0.2)  # API 요청 제한 방지
        
        # 데이터프레임 생성
        if permissions_data:
            return pd.DataFrame(permissions_data)
        else:
            return None
    except Exception as e:
        st.error(f"폴더 권한 수집 실패: {e}")
        return None

def get_permission_name(permission):
    """권한 코드를 이름으로 변환"""
    if permission == 1:
        return "Viewer"
    elif permission == 2:
        return "Editor"
    elif permission == 4:
        return "Admin"
    else:
        return f"Unknown ({permission})"

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

    # Grafana 버전 정보 표시
    st.subheader("Grafana 서버 정보")
    if st.button("Grafana 서버 버전 확인"):
        with st.spinner("Grafana 서버 버전을 확인 중입니다..."):
            grafana_version = get_grafana_version()

            if grafana_version:
                st.success("Grafana 서버 연결 성공")
                if 'version' in grafana_version:
                    st.write(f"버전: {grafana_version['version']}")
                if 'commit' in grafana_version:
                    st.write(f"커밋: {grafana_version['commit']}")
                if 'db_version' in grafana_version:
                    st.write(f"DB 버전: {grafana_version['db_version']}")
            else:
                st.error("Grafana 서버 연결 실패")
                st.info("Grafana 설정을 확인해주세요.")

def get_grafana_version():
    """Grafana 서버의 버전 정보를 가져옵니다."""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_token = os.environ.get("GRAFANA_API_TOKEN")
        
        if not all([grafana_url, grafana_token]):
            return None
        
        headers = {"Authorization": f"Bearer {grafana_token}"}
        url = f"{grafana_url}/api/health"
        
        response = requests.get(url, headers=headers, timeout=5, verify=get_ssl_verify())
        response.raise_for_status()
        
        health_info = response.json()
        return {
            "version": health_info.get("version", "알 수 없음"),
            "commit": health_info.get("commit", "알 수 없음"),
            "db_version": health_info.get("database", "알 수 없음")
        }
    except Exception as e:
        st.error(f"Grafana 버전 조회 실패: {e}")
        return None

# Description 편집기 관련 함수들
def show_desc_editor():
    """Description 편집기 화면"""
    st.subheader("📝 Dashboard Description 편집기")
    
    # Grafana 연결 확인
    if not check_grafana_connection():
        st.error("Grafana 연결에 실패했습니다. Grafana 설정을 확인해주세요.")
        return
    
    # 세션 상태 초기화
    if 'desc_editor_folders' not in st.session_state:
        st.session_state.desc_editor_folders = None
    if 'desc_editor_selected_folder' not in st.session_state:
        st.session_state.desc_editor_selected_folder = None
    if 'desc_editor_selected_dashboard' not in st.session_state:
        st.session_state.desc_editor_selected_dashboard = None
    
    # 폴더 구조 로드
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 폴더 새로고침"):
            st.session_state.desc_editor_folders = None
            st.rerun()
    
    if st.session_state.desc_editor_folders is None:
        with st.spinner("폴더 구조를 불러오는 중..."):
            st.session_state.desc_editor_folders = load_dashboard_folders()
    
    if not st.session_state.desc_editor_folders:
        st.error("폴더 목록을 불러올 수 없습니다.")
        return
    
    # 폴더 선택
    folder_options = {folder['title']: folder for folder in st.session_state.desc_editor_folders}
    folder_names = list(folder_options.keys())
    
    # 디버깅: 폴더 목록 표시
    st.write(f"**사용 가능한 폴더 ({len(folder_names)}개):** {', '.join(folder_names)}")
    
    # 이전에 선택한 폴더가 있으면 해당 인덱스를 찾기
    default_index = 0
    if (st.session_state.desc_editor_selected_folder and 
        st.session_state.desc_editor_selected_folder['title'] in folder_names):
        default_index = folder_names.index(st.session_state.desc_editor_selected_folder['title'])
    
    selected_folder_name = st.selectbox(
        "📁 폴더 선택",
        folder_names,
        index=default_index,
        key="desc_editor_folder_select"
    )
    
    if selected_folder_name:
        selected_folder = folder_options[selected_folder_name]
        
        # 폴더가 변경되었는지 확인
        folder_changed = (not st.session_state.desc_editor_selected_folder or 
                         st.session_state.desc_editor_selected_folder.get('id') != selected_folder.get('id'))
        
        if folder_changed:
            st.session_state.desc_editor_selected_folder = selected_folder
            # 폴더가 변경되면 선택된 대시보드 초기화
            st.session_state.desc_editor_selected_dashboard = None
            st.rerun()
        
        # 대시보드 목록 조회
        with st.spinner("대시보드 목록을 불러오는 중..."):
            dashboards = get_dashboards_in_folder(selected_folder.get('id'))
        
        if dashboards:
            # 대시보드 선택
            dashboard_options = {f"{dash['title']} ({dash['uid']})": dash for dash in dashboards}
            dashboard_names = list(dashboard_options.keys())
            
            # 이전에 선택한 대시보드가 있으면 해당 인덱스를 찾기
            dashboard_default_index = 0
            if (st.session_state.desc_editor_selected_dashboard and 
                f"{st.session_state.desc_editor_selected_dashboard['title']} ({st.session_state.desc_editor_selected_dashboard['uid']})" in dashboard_names):
                dashboard_default_index = dashboard_names.index(
                    f"{st.session_state.desc_editor_selected_dashboard['title']} ({st.session_state.desc_editor_selected_dashboard['uid']})"
                )
            
            selected_dashboard_name = st.selectbox(
                "📊 대시보드 선택",
                dashboard_names,
                index=dashboard_default_index,
                key="desc_editor_dashboard_select"
            )
            
            if selected_dashboard_name:
                selected_dashboard = dashboard_options[selected_dashboard_name]
                
                # 대시보드가 변경되었는지 확인
                dashboard_changed = (not st.session_state.desc_editor_selected_dashboard or 
                                   st.session_state.desc_editor_selected_dashboard.get('uid') != selected_dashboard.get('uid'))
                
                if dashboard_changed:
                    st.session_state.desc_editor_selected_dashboard = selected_dashboard
                
                # 대시보드 편집기 표시
                show_dashboard_desc_editor(selected_dashboard)
        else:
            st.info(f"'{selected_folder_name}' 폴더에 대시보드가 없습니다.")

def load_dashboard_folders():
    """대시보드 폴더 목록 조회"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_token = os.environ.get("GRAFANA_API_TOKEN")
        
        if not all([grafana_url, grafana_token]):
            return []
        
        headers = {"Authorization": f"Bearer {grafana_token}"}
        
        # 폴더 API 호출
        url = f"{grafana_url}/api/folders"
        
        response = requests.get(url, headers=headers, verify=get_ssl_verify())
        response.raise_for_status()
        
        folders = response.json()
        
        # 응답이 리스트가 아닌 경우 처리
        if isinstance(folders, dict):
            if 'folders' in folders:
                folders = folders['folders']
            else:
                folders = []
        
        # 폴더 정보 정규화
        normalized_folders = []
        for folder in folders:
            normalized_folder = {
                "id": folder.get("id", 0),
                "uid": folder.get("uid", ""),
                "title": folder.get("title", ""),
                "url": f"/dashboards/f/{folder.get('uid', '')}/{folder.get('title', '').replace(' ', '-')}" if folder.get('uid') else "",
                "created": folder.get("created", ""),
                "updated": folder.get("updated", ""),
                "parentUid": folder.get("parentUid", "")
            }
            normalized_folders.append(normalized_folder)
        
        # General 폴더 추가 (항상 첫 번째)
        normalized_folders.insert(0, {"id": 0, "uid": "", "title": "General", "url": "/dashboards", "created": "", "updated": "", "parentUid": ""})
        
        return normalized_folders
    except Exception as e:
        st.error(f"폴더 목록 조회 실패: {e}")
        return []

def get_dashboards_in_folder(folder_id):
    """특정 폴더의 대시보드 목록 조회"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_token = os.environ.get("GRAFANA_API_TOKEN")
        
        if not all([grafana_url, grafana_token]):
            return []
        
        headers = {"Authorization": f"Bearer {grafana_token}"}
        url = f"{grafana_url}/api/search"
        
        # 모든 대시보드 조회
        params = {'type': 'dash-db'}
        
        response = requests.get(url, headers=headers, params=params, verify=get_ssl_verify())
        response.raise_for_status()
        
        all_dashboards = response.json()
        
        # 클라이언트 사이드에서 폴더별 필터링
        folder_dashboards = []
        for dashboard in all_dashboards:
            dashboard_folder_id = dashboard.get('folderId', 0)
            if dashboard_folder_id == folder_id:
                folder_dashboards.append(dashboard)
        
        return folder_dashboards
    except Exception as e:
        st.error(f"대시보드 목록 조회 실패: {e}")
        return []

def show_dashboard_desc_editor(dashboard):
    """대시보드 Description 편집기"""
    st.markdown("---")
    st.subheader(f"📊 {dashboard['title']}")
    
    # 대시보드 상세 정보 조회
    dashboard_details = get_dashboard_details(dashboard['uid'])
    
    if not dashboard_details:
        st.error("대시보드 상세 정보를 불러올 수 없습니다.")
        return
    
    dashboard_data = dashboard_details['dashboard']
    panels = dashboard_data.get('panels', [])
    
    if not panels:
        st.info("이 대시보드에는 패널이 없습니다.")
        return
    
    # 패널 통계 표시
    panels_with_desc = sum(1 for panel in panels if panel.get('description', '').strip())
    panels_without_desc = len(panels) - panels_with_desc
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 패널", len(panels))
    with col2:
        st.metric("Description 있음", panels_with_desc)
    with col3:
        st.metric("Description 없음", panels_without_desc)
    with col4:
        coverage = f"{(panels_with_desc/len(panels)*100):.1f}%" if panels else "0%"
        st.metric("커버리지", coverage)
    
    # 패널 필터링 옵션
    st.markdown("### 🔍 패널 필터링")
    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("패널 제목 검색", key="panel_search")
    with col2:
        desc_filter = st.selectbox(
            "Description 필터",
            ["전체", "있음", "없음"],
            key="desc_filter"
        )
    
    # 패널 필터링
    filtered_panels = []
    for panel in panels:
        # 제목 검색 필터
        if search_term and search_term.lower() not in panel.get('title', '').lower():
            continue
        
        # Description 필터
        has_desc = bool(panel.get('description', '').strip())
        if desc_filter == "있음" and not has_desc:
            continue
        elif desc_filter == "없음" and has_desc:
            continue
        
        filtered_panels.append(panel)
    
    st.markdown(f"**{len(filtered_panels)}개의 패널이 발견되었습니다.**")
    
    if not filtered_panels:
        st.info("조건에 맞는 패널이 없습니다.")
        return
    
    # 패널 편집 폼
    with st.form("desc_editor_form"):
        edited_descriptions = {}
        
        for i, panel in enumerate(filtered_panels):
            panel_type = panel.get('type', 'unknown')
            panel_title = panel.get('title', f'패널 {panel.get("id", i)}')
            current_desc = panel.get('description', '')
            
            # 패널 타입별 이모지
            emoji = get_panel_type_emoji(panel_type)
            
            st.markdown(f"### {emoji} {panel_title}")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**타입:** {panel_type} | **ID:** {panel.get('id')}")
            with col2:
                if current_desc.strip():
                    st.success("✅ Description 있음")
                else:
                    st.warning("❌ Description 없음")
            
            # Description 편집
            new_desc = st.text_area(
                "Description",
                value=current_desc,
                height=100,
                key=f"desc_{panel.get('id', i)}"
            )
            
            if new_desc != current_desc:
                edited_descriptions[panel.get('id')] = new_desc
            
            st.markdown("---")
        
        # 저장 버튼
        if st.form_submit_button("💾 모든 변경사항 저장", type="primary"):
            if edited_descriptions:
                save_dashboard_descriptions(dashboard['uid'], dashboard_data, edited_descriptions)
            else:
                st.info("변경된 내용이 없습니다.")

def get_dashboard_details(dashboard_uid):
    """대시보드 상세 정보 조회"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_token = os.environ.get("GRAFANA_API_TOKEN")
        
        if not all([grafana_url, grafana_token]):
            return None
        
        headers = {"Authorization": f"Bearer {grafana_token}"}
        url = f"{grafana_url}/api/dashboards/uid/{dashboard_uid}"
        
        response = requests.get(url, headers=headers, verify=get_ssl_verify())
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"대시보드 상세 조회 실패: {e}")
        return None

def save_dashboard_descriptions(dashboard_uid, dashboard_data, edited_descriptions):
    """패널 Description 저장"""
    try:
        # 패널 descriptions 업데이트
        panels = dashboard_data.get('panels', [])
        updated_count = 0
        
        for panel in panels:
            panel_id = panel.get('id')
            if panel_id in edited_descriptions:
                panel['description'] = edited_descriptions[panel_id]
                updated_count += 1
        
        # 대시보드 저장
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_token = os.environ.get("GRAFANA_API_TOKEN")
        
        if not all([grafana_url, grafana_token]):
            st.error("Grafana 설정이 없습니다.")
            return
        
        headers = {"Authorization": f"Bearer {grafana_token}"}
        
        # 대시보드 저장을 위한 데이터 구조
        save_data = {
            'dashboard': dashboard_data,
            'message': 'Description 업데이트 (adminui)',
            'overwrite': True
        }
        
        url = f"{grafana_url}/api/dashboards/db"
        
        response = requests.post(url, headers=headers, json=save_data, verify=get_ssl_verify())
        response.raise_for_status()
        
        st.success(f"✅ {updated_count}개 패널의 Description이 성공적으로 업데이트되었습니다!")
        
        # 세션 상태 초기화하여 새로고침
        if 'desc_editor_selected_dashboard' in st.session_state:
            del st.session_state.desc_editor_selected_dashboard
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Description 저장 실패: {e}")

def get_panel_type_emoji(panel_type):
    """패널 타입별 이모지 반환"""
    emoji_map = {
        'graph': '📈',
        'stat': '📊',
        'table': '📋',
        'singlestat': '📊',
        'text': '📝',
        'heatmap': '🔥',
        'gauge': '⏲️',
        'bargauge': '📊',
        'piechart': '🥧',
        'logs': '📜',
        'timeseries': '📈',
        'barchart': '📊',
        'histogram': '📊',
        'news': '📰',
        'dashboard-list': '📋',
        'plugin-list': '🔌',
        'alertlist': '🚨'
    }
    return emoji_map.get(panel_type, '📊')