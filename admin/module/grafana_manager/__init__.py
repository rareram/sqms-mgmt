import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import os
from datetime import datetime
import time
import urllib.parse
import base64

def show_module():
    """Grafana 관리 모듈 메인 화면"""
    st.title("Grafana 관리")
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["팀 관리", "폴더 권한 관리", "Grafana 설정"])
    
    # 팀 관리 탭
    with tab1:
        show_team_management()
    
    # 폴더 권한 관리 탭
    with tab2:
        show_folder_permission_management()
    
    # Grafana 설정 탭
    with tab3:
        show_grafana_settings()

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
            "URL": folder["url"],
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
            
            # 권한 유형별로 필터링
            team_permissions = [p for p in permissions if p["type"] == "team"]
            user_permissions = [p for p in permissions if p["type"] == "user"]
            
            # 팀 권한 표시
            if team_permissions:
                st.write("### 팀 권한")
                
                # 팀 권한 데이터프레임 생성
                team_df = pd.DataFrame([{
                    "팀 ID": p["teamId"],
                    "권한": get_permission_name(p["permission"])
                } for p in team_permissions])
                
                # 팀 이름 추가
                for i, row in team_df.iterrows():
                    team_id = row["팀 ID"]
                    team_details = get_team_details(team_id)
                    if team_details:
                        team_df.at[i, "팀 이름"] = team_details["name"]
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
                    "사용자 ID": p["userId"],
                    "권한": get_permission_name(p["permission"])
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
    grafana_username = os.environ.get("GRAFANA_USERNAME", "")
    grafana_password = os.environ.get("GRAFANA_PASSWORD", "")
    
    # Grafana 설정 입력 폼
    with st.form("grafana_settings_form"):
        new_grafana_url = st.text_input("Grafana 서버 주소", value=grafana_url)
        new_grafana_username = st.text_input("사용자명", value=grafana_username)
        new_grafana_password = st.text_input("비밀번호", value=grafana_password, type="password")
        
        # 저장 버튼
        submit_button = st.form_submit_button("설정 저장")
        
        if submit_button:
            # .env 파일 업데이트
            update_env_file({
                "GRAFANA_URL": new_grafana_url,
                "GRAFANA_USERNAME": new_grafana_username,
                "GRAFANA_PASSWORD": new_grafana_password
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
        grafana_username = os.environ.get("GRAFANA_USERNAME")
        grafana_password = os.environ.get("GRAFANA_PASSWORD")
        
        if not all([grafana_url, grafana_username, grafana_password]):
            return False
        
        auth = HTTPBasicAuth(grafana_username, grafana_password)
        url = f"{grafana_url}/api/org"
        
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        return True
    except Exception as e:
        st.error(f"Grafana 연결 실패: {e}")
        return False

def get_all_teams():
    """Grafana 팀 목록 조회"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_username = os.environ.get("GRAFANA_USERNAME")
        grafana_password = os.environ.get("GRAFANA_PASSWORD")
        
        if not all([grafana_url, grafana_username, grafana_password]):
            return []
        
        auth = HTTPBasicAuth(grafana_username, grafana_password)
        url = f"{grafana_url}/api/teams/search?perpage=1000"
        
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        return response.json()["teams"]
    except Exception as e:
        st.error(f"팀 목록 조회 실패: {e}")
        return []

def get_team_details(team_id):
    """팀 상세 정보 조회"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_username = os.environ.get("GRAFANA_USERNAME")
        grafana_password = os.environ.get("GRAFANA_PASSWORD")
        
        if not all([grafana_url, grafana_username, grafana_password]):
            return None
        
        auth = HTTPBasicAuth(grafana_username, grafana_password)
        url = f"{grafana_url}/api/teams/{team_id}"
        
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"팀 상세 정보 조회 실패: {e}")
        return None

def get_team_members(team_id):
    """팀 멤버 목록 조회"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_username = os.environ.get("GRAFANA_USERNAME")
        grafana_password = os.environ.get("GRAFANA_PASSWORD")
        
        if not all([grafana_url, grafana_username, grafana_password]):
            return []
        
        auth = HTTPBasicAuth(grafana_username, grafana_password)
        url = f"{grafana_url}/api/teams/{team_id}/members"
        
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"팀 멤버 조회 실패: {e}")
        return []

def update_team_info(team_id, team_info):
    """팀 정보 업데이트"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_username = os.environ.get("GRAFANA_USERNAME")
        grafana_password = os.environ.get("GRAFANA_PASSWORD")
        
        if not all([grafana_url, grafana_username, grafana_password]):
            return False
        
        auth = HTTPBasicAuth(grafana_username, grafana_password)
        url = f"{grafana_url}/api/teams/{team_id}"
        
        response = requests.put(url, auth=auth, json=team_info)
        response.raise_for_status()
        
        return True
    except Exception as e:
        st.error(f"팀 정보 업데이트 실패: {e}")
        return False

def get_all_folders():
    """Grafana 폴더 목록 조회"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_username = os.environ.get("GRAFANA_USERNAME")
        grafana_password = os.environ.get("GRAFANA_PASSWORD")
        
        if not all([grafana_url, grafana_username, grafana_password]):
            return []
        
        auth = HTTPBasicAuth(grafana_username, grafana_password)
        url = f"{grafana_url}/api/folders"
        
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"폴더 목록 조회 실패: {e}")
        return []

def get_nested_folders(parent_uid=None):
    """중첩된 폴더 목록 조회"""
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_username = os.environ.get("GRAFANA_USERNAME")
        grafana_password = os.environ.get("GRAFANA_PASSWORD")
        
        if not all([grafana_url, grafana_username, grafana_password]):
            return []
        
        auth = HTTPBasicAuth(grafana_username, grafana_password)
        
        # URL 구성
        url = f"{grafana_url}/api/folders"
        if parent_uid:
            url += f"?parentUid={parent_uid}"
        
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        folders = response.json()
        
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
        grafana_username = os.environ.get("GRAFANA_USERNAME")
        grafana_password = os.environ.get("GRAFANA_PASSWORD")
        
        if not all([grafana_url, grafana_username, grafana_password]):
            return []
        
        auth = HTTPBasicAuth(grafana_username, grafana_password)
        url = f"{grafana_url}/api/folders/{folder_uid}/permissions"
        
        response = requests.get(url, auth=auth)
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
            
            # 팀 권한만 필터링
            team_perms = [p for p in perms if p["type"] == "team"]
            
            for perm in team_perms:
                team_id = perm.get("teamId")
                
                if team_id:
                    # 팀 정보 조회
                    team_info = get_team_details(team_id)
                    team_name = team_info.get("name", f"Team {team_id}") if team_info else f"Team {team_id}"
                    
                    permissions_data.append({
                        "folder_uid": folder_uid,
                        "folder_title": folder_title,
                        "team_id": team_id,
                        "team_name": team_name,
                        "permission": get_permission_name(perm["permission"]),
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