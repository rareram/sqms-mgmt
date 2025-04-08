import streamlit as st
import ldap
import os
from datetime import datetime, timedelta
import pandas as pd

# 모듈 버전 정보
VERSION = "v0.1.0"

def show_module():
    """LDAP 관리 모듈 메인 화면"""
    st.title("LDAP 관리")

    # 버전 정보 표시
    st.caption(f"모듈 버전: {VERSION}")
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["퇴사자 관리", "사용자 검색", "LDAP 설정"])
    
    # 퇴사자 관리 탭
    with tab1:
        show_employee_exit_management()
    
    # 사용자 검색 탭
    with tab2:
        show_user_search()
    
    # LDAP 설정 탭
    with tab3:
        show_ldap_settings()

def show_employee_exit_management():
    """퇴사자 관리 화면"""
    st.subheader("퇴사자 관리")
    
    # LDAP 연결이 가능한지 확인
    if not check_ldap_connection():
        st.error("LDAP 연결에 실패했습니다. LDAP 설정을 확인해주세요.")
        return
    
    # 기간 선택
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("시작일", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("종료일", value=datetime.now())
    
    # 퇴사자 조회 버튼
    if st.button("퇴사자 조회"):
        with st.spinner("퇴사자 정보를 조회 중입니다..."):
            exited_users = get_exited_users(start_date, end_date)
            
            if not exited_users:
                st.info("조회된 퇴사자가 없습니다.")
            else:
                st.write(f"총 {len(exited_users)}명의 퇴사자가 조회되었습니다.")
                
                # 퇴사자 목록 표시
                df = pd.DataFrame(exited_users)
                st.dataframe(df)
                
                # 퇴사자별 서비스 권한 조회
                if st.button("서비스 권한 조회"):
                    with st.spinner("서비스 권한을 조회 중입니다..."):
                        service_permissions = get_service_permissions(exited_users)
                        
                        if not service_permissions:
                            st.info("조회된 서비스 권한이 없습니다.")
                        else:
                            # 서비스별 탭 생성
                            service_tabs = st.tabs(list(service_permissions.keys()))
                            
                            for i, service_name in enumerate(service_permissions.keys()):
                                with service_tabs[i]:
                                    service_df = pd.DataFrame(service_permissions[service_name])
                                    st.dataframe(service_df)
                                    
                                    # CSV 다운로드 버튼
                                    csv = service_df.to_csv(index=False)
                                    st.download_button(
                                        label=f"{service_name} CSV 다운로드",
                                        data=csv,
                                        file_name=f"{service_name}_권한_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
                                        mime="text/csv"
                                    )

def show_user_search():
    """사용자 검색 화면"""
    st.subheader("사용자 검색")
    
    # LDAP 연결이 가능한지 확인
    if not check_ldap_connection():
        st.error("LDAP 연결에 실패했습니다. LDAP 설정을 확인해주세요.")
        return
    
    # 검색 조건
    search_term = st.text_input("검색어 (이름, 사번, 이메일 등)")
    
    # 검색 버튼
    if st.button("검색") and search_term:
        with st.spinner("사용자를 검색 중입니다..."):
            users = search_users(search_term)
            
            if not users:
                st.info("검색 결과가 없습니다.")
            else:
                st.write(f"총 {len(users)}명의 사용자가 검색되었습니다.")
                
                # 사용자 목록 표시
                df = pd.DataFrame(users)
                st.dataframe(df)
                
                # 선택한 사용자의 서비스 권한 조회
                selected_users = st.multiselect("서비스 권한을 조회할 사용자 선택", [user['name'] for user in users])
                
                if selected_users and st.button("서비스 권한 조회", key="search_permissions"):
                    with st.spinner("서비스 권한을 조회 중입니다..."):
                        selected_user_objects = [user for user in users if user['name'] in selected_users]
                        service_permissions = get_service_permissions(selected_user_objects)
                        
                        if not service_permissions:
                            st.info("조회된 서비스 권한이 없습니다.")
                        else:
                            # 서비스별 탭 생성
                            service_tabs = st.tabs(list(service_permissions.keys()))
                            
                            for i, service_name in enumerate(service_permissions.keys()):
                                with service_tabs[i]:
                                    service_df = pd.DataFrame(service_permissions[service_name])
                                    st.dataframe(service_df)

def show_ldap_settings():
    """LDAP 설정 화면"""
    st.subheader("LDAP 설정")
    
    # 현재 설정된 LDAP 정보 불러오기
    ldap_server = os.environ.get("LDAP_SERVER", "")
    ldap_base_dn = os.environ.get("LDAP_BASE_DN", "")
    ldap_user_dn = os.environ.get("LDAP_USER_DN", "")
    ldap_password = os.environ.get("LDAP_PASSWORD", "")
    
    # LDAP 설정 입력 폼
    with st.form("ldap_settings_form"):
        new_ldap_server = st.text_input("LDAP 서버 주소", value=ldap_server)
        new_ldap_base_dn = st.text_input("기본 DN", value=ldap_base_dn)
        new_ldap_user_dn = st.text_input("관리자 DN", value=ldap_user_dn)
        new_ldap_password = st.text_input("비밀번호", value=ldap_password, type="password")
        
        # 저장 버튼
        submit_button = st.form_submit_button("설정 저장")
        
        if submit_button:
            # .env 파일 업데이트
            update_env_file({
                "LDAP_SERVER": new_ldap_server,
                "LDAP_BASE_DN": new_ldap_base_dn,
                "LDAP_USER_DN": new_ldap_user_dn,
                "LDAP_PASSWORD": new_ldap_password
            })
            
            st.success("LDAP 설정이 저장되었습니다.")
    
    # LDAP 연결 테스트 버튼
    if st.button("연결 테스트"):
        if check_ldap_connection():
            st.success("LDAP 연결에 성공했습니다.")
        else:
            st.error("LDAP 연결에 실패했습니다. 설정을 확인해주세요.")

def check_ldap_connection():
    """LDAP 연결 테스트"""
    try:
        ldap_server = os.environ.get("LDAP_SERVER")
        ldap_user_dn = os.environ.get("LDAP_USER_DN")
        ldap_password = os.environ.get("LDAP_PASSWORD")
        
        if not all([ldap_server, ldap_user_dn, ldap_password]):
            return False
        
        conn = ldap.initialize(ldap_server)
        conn.simple_bind_s(ldap_user_dn, ldap_password)
        conn.unbind_s()
        return True
    except Exception as e:
        st.error(f"LDAP 연결 실패: {e}")
        return False

def get_exited_users(start_date, end_date):
    """퇴사자 목록 조회
    LDAP에서 퇴사일이 시작일과 종료일 사이인 사용자 목록 반환
    
    Args:
        start_date (datetime.date): 시작일
        end_date (datetime.date): 종료일
    
    Returns:
        list: 퇴사자 목록 (dict 형태)
    """
    try:
        ldap_server = os.environ.get("LDAP_SERVER")
        ldap_base_dn = os.environ.get("LDAP_BASE_DN")
        ldap_user_dn = os.environ.get("LDAP_USER_DN")
        ldap_password = os.environ.get("LDAP_PASSWORD")
        
        conn = ldap.initialize(ldap_server)
        conn.simple_bind_s(ldap_user_dn, ldap_password)
        
        # LDAP 필터: 퇴사일이 시작일과 종료일 사이인 사용자
        ldap_filter = f"(&(objectClass=person)(exitDate>={start_date.strftime('%Y%m%d')})(exitDate<={end_date.strftime('%Y%m%d')}))"
        
        # LDAP 검색 속성
        attrs = ["uid", "cn", "mail", "employeeNumber", "exitDate", "department"]
        
        # LDAP 검색
        result = conn.search_s(ldap_base_dn, ldap.SCOPE_SUBTREE, ldap_filter, attrs)
        conn.unbind_s()
        
        # 검색 결과 처리
        exited_users = []
        
        for dn, entry in result:
            user = {
                "uid": entry.get("uid", [b""])[0].decode("utf-8"),
                "name": entry.get("cn", [b""])[0].decode("utf-8"),
                "email": entry.get("mail", [b""])[0].decode("utf-8"),
                "employee_id": entry.get("employeeNumber", [b""])[0].decode("utf-8"),
                "exit_date": entry.get("exitDate", [b""])[0].decode("utf-8"),
                "department": entry.get("department", [b""])[0].decode("utf-8")
            }
            exited_users.append(user)
        
        return exited_users
    except Exception as e:
        st.error(f"퇴사자 조회 실패: {e}")
        return []

def search_users(search_term):
    """사용자 검색
    LDAP에서 검색어와 일치하는 사용자 목록 반환
    
    Args:
        search_term (str): 검색어
    
    Returns:
        list: 사용자 목록 (dict 형태)
    """
    try:
        ldap_server = os.environ.get("LDAP_SERVER")
        ldap_base_dn = os.environ.get("LDAP_BASE_DN")
        ldap_user_dn = os.environ.get("LDAP_USER_DN")
        ldap_password = os.environ.get("LDAP_PASSWORD")
        
        conn = ldap.initialize(ldap_server)
        conn.simple_bind_s(ldap_user_dn, ldap_password)
        
        # LDAP 필터: 검색어와 일치하는 사용자
        ldap_filter = f"(&(objectClass=person)(|(cn=*{search_term}*)(uid=*{search_term}*)(mail=*{search_term}*)(employeeNumber=*{search_term}*)))"
        
        # LDAP 검색 속성
        attrs = ["uid", "cn", "mail", "employeeNumber", "department", "title"]
        
        # LDAP 검색
        result = conn.search_s(ldap_base_dn, ldap.SCOPE_SUBTREE, ldap_filter, attrs)
        conn.unbind_s()
        
        # 검색 결과 처리
        users = []
        
        for dn, entry in result:
            user = {
                "uid": entry.get("uid", [b""])[0].decode("utf-8"),
                "name": entry.get("cn", [b""])[0].decode("utf-8"),
                "email": entry.get("mail", [b""])[0].decode("utf-8"),
                "employee_id": entry.get("employeeNumber", [b""])[0].decode("utf-8"),
                "department": entry.get("department", [b""])[0].decode("utf-8"),
                "title": entry.get("title", [b""])[0].decode("utf-8")
            }
            users.append(user)
        
        return users
    except Exception as e:
        st.error(f"사용자 검색 실패: {e}")
        return []

def get_service_permissions(users):
    """사용자의 서비스 권한 조회
    여러 서비스(GitLab, Redmine 등)에서 사용자의 권한 정보 조회
    
    Args:
        users (list): 사용자 목록
    
    Returns:
        dict: 서비스별 권한 정보
    """
    # 결과를 저장할 딕셔너리
    permissions = {
        "GitLab": [],
        "Redmine": [],
        "Grafana": []
    }
    
    # 사용자 ID 목록
    user_ids = [user["uid"] for user in users]
    user_emails = [user["email"] for user in users]
    
    # GitLab 권한 조회 (예시)
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if gitlab_host and gitlab_token:
            # 여기에 GitLab API 호출 코드 구현
            # 실제 구현 시 GitLab API를 사용하여 사용자 권한 정보 조회
            pass
    except Exception as e:
        st.error(f"GitLab 권한 조회 실패: {e}")
    
    # Redmine 권한 조회 (예시)
    try:
        redmine_url = os.environ.get("REDMINE_URL")
        redmine_api_key = os.environ.get("REDMINE_API_KEY")
        
        if redmine_url and redmine_api_key:
            # 여기에 Redmine API 호출 코드 구현
            # 실제 구현 시 Redmine API를 사용하여 사용자 권한 정보 조회
            pass
    except Exception as e:
        st.error(f"Redmine 권한 조회 실패: {e}")
    
    # Grafana 권한 조회 (예시)
    try:
        grafana_url = os.environ.get("GRAFANA_URL")
        grafana_username = os.environ.get("GRAFANA_USERNAME")
        grafana_password = os.environ.get("GRAFANA_PASSWORD")
        
        if grafana_url and grafana_username and grafana_password:
            # 여기에 Grafana API 호출 코드 구현
            # 실제 구현 시 Grafana API를 사용하여 사용자 권한 정보 조회
            pass
    except Exception as e:
        st.error(f"Grafana 권한 조회 실패: {e}")
    
    return permissions

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