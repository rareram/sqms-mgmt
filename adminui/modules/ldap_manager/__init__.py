import streamlit as st
import ldap
import os
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
from modules.utils.version import show_version_info, save_repo_url, load_repo_url, get_latest_version, compare_versions

# 모듈 ID와 버전 정보
MODULE_ID = "ldap_manager"
VERSION = "v0.1.5"
DEFAULT_REPO_URL = "https://github.com/openldap/openldap/tags"

# 폰트 설정 함수
def set_matplotlib_korean_font():
    """matplotlib에 한글 폰트 설정"""
    # 프로젝트 내 폰트 디렉토리 경로
    font_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "../../assets/fonts"
    
    # 시스템에 설치된 폰트 중 한글 폰트 찾기
    system_fonts = [f.name for f in fm.fontManager.ttflist if any(keyword in f.name.lower() for keyword in ['malgun', 'nanum', 'gulim', 'batang', 'gothic'])]
    
    # 프로젝트 내 폰트 디렉토리 검사
    if font_dir.exists():
        # 프로젝트 내 폰트 등록
        font_files = list(font_dir.glob('*.ttf')) + list(font_dir.glob('*.otf'))
        for font_file in font_files:
            fm.fontManager.addfont(str(font_file))
            
    # 폰트 설정 시도
    if font_dir.exists() and len(list(font_dir.glob('*.ttf'))) > 0:
        # 프로젝트 내 첫 번째 폰트 사용
        font_path = next(font_dir.glob('*.ttf'))
        plt.rcParams['font.family'] = fm.FontProperties(fname=str(font_path)).get_name()
    elif system_fonts:
        # 시스템 한글 폰트 사용
        plt.rcParams['font.family'] = system_fonts[0]
    else:
        # 폰트를 찾을 수 없는 경우 대체 방법
        plt.rcParams['font.sans-serif'] = ['Arial', 'Tahoma', 'DejaVu Sans', 'Noto Sans', 'Verdana']
        plt.rcParams['axes.unicode_minus'] = False

# 모듈 시작 시 폰트 설정
set_matplotlib_korean_font()

def show_module():
    """LDAP 관리 모듈 메인 화면"""
    st.title("LDAP 관리")

    # 버전 정보 표시
    st.caption(f"모듈 버전: {VERSION}")
    
    # 탭 생성 - 버전 정보 탭 제거
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

# 사원 구분 관련 함수
def get_employee_type_name(employee_id):
    """사번으로 사원 구분 이름 반환"""
    if not employee_id:
        return "미분류"
    
    # 사번 형식 정규화
    emp_id = employee_id.strip().upper()
    
    if emp_id.startswith("K9"):
        return "협력사"
    elif emp_id.startswith("A0") or emp_id.startswith("K1"):
        return "정직원"
    else:
        return "기타"

def filter_employees_by_type(employees, employee_type):
    """직원 목록을 사원 구분에 따라 필터링"""
    if employee_type == "전체":
        return employees
    
    filtered = []
    for emp in employees:
        emp_id = emp.get("employee_id", "")
        emp_type = get_employee_type_name(emp_id)
        
        if emp_type == employee_type:
            filtered.append(emp)
    
    return filtered

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
    
    # 사원 구분 필터 추가
    employee_type = st.radio("사원 구분", ["전체", "정직원", "협력사", "기타"], horizontal=True)
    
    # OU(조직 단위) 필터 추가
    st.write("OU(조직 단위) 필터:")
    show_inactive_only = st.checkbox("비활성화된 계정만 표시", value=True)
    search_ou = st.text_input("특정 OU 검색 (선택사항, 예: ou=퇴사자,dc=example,dc=com)", "")
    
    # 퇴사자 조회 버튼
    if st.button("퇴사자 조회"):
        with st.spinner("퇴사자 정보를 조회 중입니다..."):
            exited_users = get_exited_users(start_date, end_date, inactive_only=show_inactive_only, search_ou=search_ou)
            
            if not exited_users:
                st.info("조회된 퇴사자가 없습니다.")
            else:
                # 사원 구분별 필터링
                if employee_type != "전체":
                    exited_users = filter_employees_by_type(exited_users, employee_type)
                
                if not exited_users:
                    st.info(f"조회된 {employee_type} 퇴사자가 없습니다.")
                else:
                    st.write(f"총 {len(exited_users)}명의 {employee_type if employee_type != '전체' else ''} 퇴사자가 조회되었습니다.")
                    
                    # 사원 유형 정보 추가
                    for user in exited_users:
                        user["사원구분"] = get_employee_type_name(user.get("employee_id", ""))
                    
                    # 퇴사자 목록 표시
                    df = pd.DataFrame(exited_users)
                    st.dataframe(df)

                    # CSV 다운로드 버튼 (UTF-8 BOM 추가)
                    csv = '\ufeff' + df.to_csv(index=False)
                    st.download_button(
                        label="퇴사자 목록 CSV 다운로드",
                        data=csv,
                        file_name=f"퇴사자_목록_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                    
                    # 안내 메시지 추가
                    st.info("다운로드한 CSV 파일을 GitLab, Redmine, Grafana 관리 모듈에서 사용하여 서비스 권한을 확인할 수 있습니다.")

def show_user_search():
    """사용자 검색 화면"""
    st.subheader("사용자 검색")
    
    # LDAP 연결이 가능한지 확인
    if not check_ldap_connection():
        st.error("LDAP 연결에 실패했습니다. LDAP 설정을 확인해주세요.")
        return
    
    # 검색 조건
    search_term = st.text_input("검색어 (이름, 사번, 이메일 등)")
    
    # 사원 구분 필터 추가
    employee_type = st.radio("사원 구분으로 필터링", ["전체", "정직원", "협력사", "기타"], horizontal=True)
    
    # 계정 상태 필터
    account_status = st.radio("계정 상태", ["전체", "활성", "비활성"], horizontal=True)
    
    # 검색 버튼
    if st.button("검색") and search_term:
        with st.spinner("사용자를 검색 중입니다..."):
            users = search_users(search_term, account_status)
            
            if not users:
                st.info("검색 결과가 없습니다.")
            else:
                # 사원 구분별 필터링
                if employee_type != "전체":
                    users = filter_employees_by_type(users, employee_type)
                
                if not users:
                    st.info(f"검색된 {employee_type} 사용자가 없습니다.")
                else:
                    st.write(f"총 {len(users)}명의 사용자가 검색되었습니다.")
                    
                    # 사원 유형 정보 추가
                    for user in users:
                        user["사원구분"] = get_employee_type_name(user.get("employee_id", ""))
                    
                    # 사용자 목록 표시
                    df = pd.DataFrame(users)
                    st.dataframe(df)

                    # CSV 다운로드 버튼
                    csv = '\ufeff' + df.to_csv(index=False)
                    st.download_button(
                        label="사용자 목록 CSV 다운로드",
                        data=csv,
                        file_name=f"사용자_검색_{search_term}.csv",
                        mime="text/csv"
                    )
                    
                    # 안내 메시지 추가
                    st.info("다운로드한 CSV 파일을 GitLab, Redmine, Grafana 관리 모듈에서 사용하여 서비스 권한을 확인할 수 있습니다.")

def show_ldap_settings():
    """LDAP 설정 화면"""
    st.subheader("LDAP 설정")
    
    # 현재 설정된 LDAP 정보 불러오기
    ldap_server = os.environ.get("LDAP_SERVER", "")
    ldap_base_dn = os.environ.get("LDAP_BASE_DN", "")
    ldap_user_dn = os.environ.get("LDAP_USER_DN", "")
    ldap_password = os.environ.get("LDAP_PASSWORD", "")
    ldap_type = os.environ.get("LDAP_TYPE", "openldap")

    # LDAP 설정 입력 폼
    with st.form("ldap_settings_form"):
        # LDAP 타입 선택
        new_ldap_type = st.selectbox("LDAP 타입", 
                                  options=["openldap", "activedirectory"],
                                  index=0 if ldap_type.lower() == "openldap" else 1,
                                  help="사용 중인 LDAP 시스템 유형")
        
        new_ldap_server = st.text_input("LDAP 서버 주소", value=ldap_server)
        new_ldap_base_dn = st.text_input("기본 DN", value=ldap_base_dn)
        new_ldap_user_dn = st.text_input("관리자 DN", value=ldap_user_dn)
        new_ldap_password = st.text_input("비밀번호", value=ldap_password, type="password")
        
        # 도움말 추가
        if new_ldap_type == "activedirectory":
            st.info("Active Directory 사용 시 관리자 DN은 'username@domain.com' 형식을 사용합니다.")
        else:
            st.info("OpenLDAP 사용 시 관리자 DN은 'cn=admin,dc=example,dc=com' 형식을 사용합니다.")
        
        # 저장 버튼
        submit_button = st.form_submit_button("설정 저장")
        
        if submit_button:
            # .env 파일 업데이트
            update_env_file({
                "LDAP_SERVER": new_ldap_server,
                "LDAP_BASE_DN": new_ldap_base_dn,
                "LDAP_USER_DN": new_ldap_user_dn,
                "LDAP_PASSWORD": new_ldap_password,
                "LDAP_TYPE": new_ldap_type
            })
            
            st.success("LDAP 설정이 저장되었습니다.")
    
    # LDAP 연결 테스트 버튼
    if st.button("연결 테스트"):
        if check_ldap_connection():
            st.success("LDAP 연결에 성공했습니다.")
        else:
            st.error("LDAP 연결에 실패했습니다. 설정을 확인해주세요.")
    
    # LDAP 서버 정보 섹션
    st.subheader("LDAP 서버 정보")
    
    # LDAP 타입에 따른 안내 메시지
    ldap_type = os.environ.get("LDAP_TYPE", "openldap").lower()
    if ldap_type == "activedirectory":
        st.info("Active Directory는 버전 정보를 직접 조회하기 어렵습니다. 서버 관리자에게 문의하세요.")
    
    # LDAP 서버 버전 확인 버튼 (OpenLDAP에만 표시)
    if ldap_type.lower() == "openldap":
        if st.button("LDAP 서버 버전 확인"):
            with st.spinner("LDAP 서버 버전을 확인 중입니다..."):
                ldap_version_info = get_ldap_version()
                
                if ldap_version_info:
                    st.success("LDAP 서버 연결 성공")
                    st.write(f"버전: {ldap_version_info.get('version', '알 수 없음')}")
                    if 'vendor' in ldap_version_info:
                        st.write(f"공급 업체: {ldap_version_info['vendor']}")
                else:
                    st.error("LDAP 서버 연결 실패")
                    st.info("LDAP 설정을 확인해주세요.")
    
    # 모듈 저장소 및 버전 정보
    with st.expander("모듈 버전 정보", expanded=False):
        # 저장된 저장소 URL 로드 또는 기본값 사용
        repo_url = load_repo_url(MODULE_ID) or DEFAULT_REPO_URL
        
        # 저장소 URL 설정 폼
        with st.form("repo_url_form"):
            new_repo_url = st.text_input("저장소 URL", value=repo_url, help="GitHub 릴리즈/태그 또는 GitLab 태그 URL")
            submit = st.form_submit_button("저장")
            
            if submit and new_repo_url:
                if save_repo_url(MODULE_ID, new_repo_url):
                    st.success("저장소 URL이 저장되었습니다.")
                    repo_url = new_repo_url
        
        # 모듈 최신 버전 확인
        if st.button("모듈 최신 버전 확인"):
            with st.spinner("최신 버전 확인 중..."):
                latest_release = get_latest_version(repo_url)
                
                if latest_release:
                    latest_version = latest_release["version"]
                    version_status = compare_versions(VERSION, latest_version)
                    
                    if version_status == -1:
                        st.warning(f"새 버전의 모듈이 있습니다: {latest_version}")
                        st.markdown(f"[{repo_url.split('/')[-2] if '/tags' in repo_url else '저장소'}에서 업데이트 확인]({latest_release['url']})")
                        
                        # 릴리스 노트 표시 (GitHub 릴리스인 경우)
                        if latest_release.get("source") == "github_release" and "body" in latest_release:
                            with st.expander("릴리스 노트"):
                                st.markdown(f"## {latest_release['name']}")
                                st.markdown(latest_release['body'])
                    
                    elif version_status == 0:
                        st.success(f"최신 모듈 버전을 사용 중입니다: {latest_version}")
                    elif version_status == 1:
                        st.info(f"개발 버전의 모듈을 사용 중입니다. 최신 안정 버전: {latest_version}")
                    else:
                        st.error("버전 비교 실패: 잘못된 버전 형식입니다.")
                else:
                    st.error(f"저장소에서 최신 버전 정보를 가져오지 못했습니다: {repo_url}")

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

def get_ldap_version():
    """LDAP 서버 버전 정보 조회 (OpenLDAP 전용)"""
    try:
        ldap_server = os.environ.get("LDAP_SERVER")
        ldap_user_dn = os.environ.get("LDAP_USER_DN")
        ldap_password = os.environ.get("LDAP_PASSWORD")
        
        if not all([ldap_server, ldap_user_dn, ldap_password]):
            return None
        
        # LDAP 연결
        conn = ldap.initialize(ldap_server)
        conn.simple_bind_s(ldap_user_dn, ldap_password)
        
        # 루트 DSE 조회
        result = conn.search_s("", ldap.SCOPE_BASE, "(objectClass=*)", ["*", "+"])
        conn.unbind_s()
        
        if result:
            dn, attrs = result[0]
            version_info = {}
            
            # 버전 정보 추출
            if b'vendorVersion' in attrs:
                version_info['version'] = attrs[b'vendorVersion'][0].decode('utf-8')
            if b'vendorName' in attrs:
                version_info['vendor'] = attrs[b'vendorName'][0].decode('utf-8')
            elif b'vendor' in attrs:
                version_info['vendor'] = attrs[b'vendor'][0].decode('utf-8')
            
            return version_info
        
        return None
    except Exception as e:
        st.error(f"LDAP 버전 조회 실패: {e}")
        return None

def get_exited_users(start_date, end_date, inactive_only=True, search_ou=""):
    """퇴사자 목록 조회
    LDAP에서 비활성화된 계정 또는 퇴사일이 시작일과 종료일 사이인 사용자 목록 반환
    
    Args:
        start_date (datetime.date): 시작일
        end_date (datetime.date): 종료일
        inactive_only (bool): 비활성화된 계정만 조회할지 여부
        search_ou (str): 특정 OU에서만 검색할 경우 지정
    
    Returns:
        list: 퇴사자 목록 (dict 형태)
    """
    # LDAP 타입에 따라 다른 함수 호출
    ldap_type = os.environ.get("LDAP_TYPE", "openldap").lower()
    
    if ldap_type == "activedirectory":
        return get_exited_users_ad(start_date, end_date, inactive_only, search_ou)
    else:
        return get_exited_users_openldap(start_date, end_date, inactive_only, search_ou)

def get_exited_users_openldap(start_date, end_date, inactive_only=True, search_ou=""):
    """OpenLDAP 방식의 퇴사자 목록 조회"""
    try:
        ldap_server = os.environ.get("LDAP_SERVER")
        ldap_base_dn = os.environ.get("LDAP_BASE_DN")
        ldap_user_dn = os.environ.get("LDAP_USER_DN")
        ldap_password = os.environ.get("LDAP_PASSWORD")
        
        conn = ldap.initialize(ldap_server)
        conn.simple_bind_s(ldap_user_dn, ldap_password)
        
        # 검색 베이스 DN 설정
        base_dn = search_ou if search_ou else ldap_base_dn
        
        # LDAP 필터 구성
        date_filter = f"(&(exitDate>={start_date.strftime('%Y%m%d')})(exitDate<={end_date.strftime('%Y%m%d')}))"
        status_filter = "(objectClass=person)"
        
        if inactive_only:
            # OpenLDAP에서 비활성화 속성이 있다면 추가 (예: shadowExpire)
            status_filter = "(&(objectClass=person)(shadowExpire=*))"
        
        ldap_filter = f"(&{status_filter}{date_filter})"
        
        # LDAP 검색 속성
        attrs = ["uid", "cn", "mail", "employeeNumber", "exitDate", "department", "shadowExpire"]
        
        # LDAP 검색
        result = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, ldap_filter, attrs)
        conn.unbind_s()
        
        # 검색 결과 처리
        exited_users = []
        
        for dn, entry in result:
            user = {
                "uid": entry.get("uid", [b""])[0].decode("utf-8") if "uid" in entry else "",
                "name": entry.get("cn", [b""])[0].decode("utf-8") if "cn" in entry else "",
                "email": entry.get("mail", [b""])[0].decode("utf-8") if "mail" in entry else "",
                "employee_id": entry.get("employeeNumber", [b""])[0].decode("utf-8") if "employeeNumber" in entry else "",
                "exit_date": entry.get("exitDate", [b""])[0].decode("utf-8") if "exitDate" in entry else "",
                "department": entry.get("department", [b""])[0].decode("utf-8") if "department" in entry else "",
                "account_status": "비활성" if "shadowExpire" in entry else "활성"
            }
            exited_users.append(user)
        
        return exited_users
    except Exception as e:
        st.error(f"퇴사자 조회 실패: {e}")
        return []

def get_exited_users_ad(start_date, end_date, inactive_only=True, search_ou=""):
    """Active Directory 방식의 퇴사자 목록 조회"""
    try:
        ldap_server = os.environ.get("LDAP_SERVER")
        ldap_base_dn = os.environ.get("LDAP_BASE_DN")
        ldap_user_dn = os.environ.get("LDAP_USER_DN")
        ldap_password = os.environ.get("LDAP_PASSWORD")
        
        conn = ldap.initialize(ldap_server)
        conn.simple_bind_s(ldap_user_dn, ldap_password)
        
        # 검색 베이스 DN 설정
        base_dn = search_ou if search_ou else ldap_base_dn
        
        # Active Directory에 맞는 필터
        # userAccountControl=514 또는 userAccountControl=546은 비활성화된 계정을 의미
        date_filter = ""
        start_date_str = start_date.strftime('%Y%m%d000000.0Z')
        end_date_str = end_date.strftime('%Y%m%d235959.0Z')
        
        if inactive_only:
            # 비활성화된 계정 필터
            status_filter = "(|(userAccountControl=514)(userAccountControl=546))"
        else:
            # 모든 계정 필터
            status_filter = "(objectClass=user)"
        
        # whenChanged 필드로 날짜 필터링
        date_filter = f"(whenChanged>={start_date_str})(whenChanged<={end_date_str})"
        
        # 정직원 및 협력사 모두 포함하는 필터
        employee_filter = "(|(employeeID=A0*)(employeeID=K1*)(employeeID=K9*))"
        
        # 최종 필터
        ldap_filter = f"(&(objectClass=user){status_filter}{date_filter}{employee_filter})"
        
        # LDAP 검색 속성
        attrs = ["sAMAccountName", "displayName", "mail", "employeeID", "whenChanged", "department", "userAccountControl"]
        
        # LDAP 검색
        result = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, ldap_filter, attrs)
        conn.unbind_s()
        
        # 검색 결과 처리
        exited_users = []
        st.text("검색된 사용자 수: " + str(len(result)))
        st.text("LDAP 모듈에서는 계정상태(활성/비활성)와 퇴사일(whenChanged)을 확인할 수 있습니다. 사용자에 할당된 서비스 권한은 직접 확인할 수 없으니 목록을 CSV로 다운로드하여 각 어플리케이션에서 확인하시기 바랍니다.")
        
        for dn, entry in result:
            # 계정 상태 확인
            account_status = "비활성"
            if "userAccountControl" in entry:
                uac = int(entry["userAccountControl"][0])
                if not (uac & 2):  # 비트 2가 비활성화를 의미
                    account_status = "활성"
            
            # 속성이 있는지 확인하고 안전하게 디코딩
            user = {
                "uid": entry.get("sAMAccountName", [b""])[0].decode("utf-8") if "sAMAccountName" in entry else "",
                "name": entry.get("displayName", [b""])[0].decode("utf-8") if "displayName" in entry else "",
                "email": entry.get("mail", [b""])[0].decode("utf-8") if "mail" in entry else "",
                "employee_id": entry.get("employeeID", [b""])[0].decode("utf-8") if "employeeID" in entry else "",
                "exit_date": entry.get("whenChanged", [b""])[0].decode("utf-8") if "whenChanged" in entry else "",
                "department": entry.get("department", [b""])[0].decode("utf-8") if "department" in entry else "",
                "account_status": account_status
            }
            exited_users.append(user)
        
        return exited_users
    except Exception as e:
        st.error(f"퇴사자 조회 실패: {e}")
        st.write(f"예외 상세 정보: {str(e)}")
        return []

def search_users(search_term, account_status="전체"):
    """사용자 검색
    LDAP에서 검색어와 일치하는 사용자 목록 반환
    
    Args:
        search_term (str): 검색어
        account_status (str): 계정 상태 필터 ('전체', '활성', '비활성')
    
    Returns:
        list: 사용자 목록 (dict 형태)
    """
    # LDAP 타입에 따라 다른 함수 호출
    ldap_type = os.environ.get("LDAP_TYPE", "openldap").lower()
    
    if ldap_type == "activedirectory":
        return search_users_ad(search_term, account_status)
    else:
        return search_users_openldap(search_term, account_status)

def search_users_openldap(search_term, account_status="전체"):
    """OpenLDAP 방식의 사용자 검색"""
    try:
        ldap_server = os.environ.get("LDAP_SERVER")
        ldap_base_dn = os.environ.get("LDAP_BASE_DN")
        ldap_user_dn = os.environ.get("LDAP_USER_DN")
        ldap_password = os.environ.get("LDAP_PASSWORD")
        
        conn = ldap.initialize(ldap_server)
        conn.simple_bind_s(ldap_user_dn, ldap_password)
        
        # 계정 상태 필터 구성
        status_filter = ""
        if account_status == "활성":
            status_filter = "(!(shadowExpire=*))"
        elif account_status == "비활성":
            status_filter = "(shadowExpire=*)"
        
        # LDAP 필터: 검색어와 일치하는 사용자
        search_filter = f"(|(cn=*{search_term}*)(uid=*{search_term}*)(mail=*{search_term}*)(employeeNumber=*{search_term}*))"
        
        if status_filter:
            ldap_filter = f"(&(objectClass=person){search_filter}{status_filter})"
        else:
            ldap_filter = f"(&(objectClass=person){search_filter})"
        
        # LDAP 검색 속성
        attrs = ["uid", "cn", "mail", "employeeNumber", "department", "title", "shadowExpire"]
        
        # LDAP 검색
        result = conn.search_s(ldap_base_dn, ldap.SCOPE_SUBTREE, ldap_filter, attrs)
        conn.unbind_s()
        
        # 검색 결과 처리
        users = []
        
        for dn, entry in result:
            # 계정 상태 확인
            account_status_val = "활성"
            if "shadowExpire" in entry:
                account_status_val = "비활성"
                
            user = {
                "uid": entry.get("uid", [b""])[0].decode("utf-8") if "uid" in entry else "",
                "name": entry.get("cn", [b""])[0].decode("utf-8") if "cn" in entry else "",
                "email": entry.get("mail", [b""])[0].decode("utf-8") if "mail" in entry else "",
                "employee_id": entry.get("employeeNumber", [b""])[0].decode("utf-8") if "employeeNumber" in entry else "",
                "department": entry.get("department", [b""])[0].decode("utf-8") if "department" in entry else "",
                "title": entry.get("title", [b""])[0].decode("utf-8") if "title" in entry else "",
                "account_status": account_status_val
            }
            users.append(user)
        
        return users
    except Exception as e:
        st.error(f"사용자 검색 실패: {e}")
        return []

def search_users_ad(search_term, account_status="전체"):
    """Active Directory 방식의 사용자 검색"""
    try:
        ldap_server = os.environ.get("LDAP_SERVER")
        ldap_base_dn = os.environ.get("LDAP_BASE_DN")
        ldap_user_dn = os.environ.get("LDAP_USER_DN")
        ldap_password = os.environ.get("LDAP_PASSWORD")
        
        conn = ldap.initialize(ldap_server)
        conn.simple_bind_s(ldap_user_dn, ldap_password)
        
        # 계정 상태 필터 구성
        status_filter = ""
        if account_status == "활성":
            # 활성 계정: userAccountControl 비트 2가 0
            status_filter = "(!(userAccountControl:1.2.840.113556.1.4.803:=2))"
        elif account_status == "비활성":
            # 비활성 계정: userAccountControl 비트 2가 1
            status_filter = "(userAccountControl:1.2.840.113556.1.4.803:=2)"
        
        # AD 필터 - 정직원과 협력사 모두 포함
        search_filter = f"(|(cn=*{search_term}*)(sAMAccountName=*{search_term}*)(mail=*{search_term}*)(employeeID=*{search_term}*))"
        
        # 최종 필터
        if status_filter:
            ldap_filter = f"(&(objectClass=user){search_filter}{status_filter})"
        else:
            ldap_filter = f"(&(objectClass=user){search_filter})"
        
        # LDAP 검색 속성
        attrs = ["sAMAccountName", "displayName", "mail", "employeeID", "department", "title", "userAccountControl"]
        
        # LDAP 검색
        result = conn.search_s(ldap_base_dn, ldap.SCOPE_SUBTREE, ldap_filter, attrs)
        conn.unbind_s()
        
        # 검색 결과 처리
        users = []
        
        for dn, entry in result:
            # 계정 상태 확인
            account_status_val = "활성"
            if "userAccountControl" in entry:
                uac = int(entry["userAccountControl"][0])
                if uac & 2:  # 비트 2가 비활성화를 의미
                    account_status_val = "비활성"
            
            # 속성이 있는지 확인하고 안전하게 디코딩
            user = {
                "uid": entry.get("sAMAccountName", [b""])[0].decode("utf-8") if "sAMAccountName" in entry else "",
                "name": entry.get("displayName", [b""])[0].decode("utf-8") if "displayName" in entry else "",
                "email": entry.get("mail", [b""])[0].decode("utf-8") if "mail" in entry else "",
                "employee_id": entry.get("employeeID", [b""])[0].decode("utf-8") if "employeeID" in entry else "",
                "department": entry.get("department", [b""])[0].decode("utf-8") if "department" in entry else "",
                "title": entry.get("title", [b""])[0].decode("utf-8") if "title" in entry else "",
                "account_status": account_status_val
            }
            users.append(user)
        
        return users
    except Exception as e:
        st.error(f"사용자 검색 실패: {e}")
        st.write(f"예외 상세 정보: {str(e)}")
        return []

def update_env_file(new_values):
    """환경 변수 파일 업데이트 - 주석과 형식 보존
    
    Args:
        new_values (dict): 새 환경 변수 값
    """
    env_path = ".env"
    env_vars = new_values.copy()  # 업데이트할 값 복사
    
    if os.path.exists(env_path):
        # 원본 파일의 내용과 구조 저장
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        # 수정된 파일 내용 작성
        with open(env_path, "w") as f:
            updated_keys = set()  # 이미 업데이트한 키 추적
            
            for line in lines:
                line = line.rstrip("\n")
                
                # 주석 또는 빈 줄 유지
                if not line or line.startswith("#"):
                    f.write(f"{line}\n")
                    continue
                
                # 키=값 형식의 라인 처리
                try:
                    key, original_value = line.split("=", 1)
                    key = key.strip()
                    
                    # 새 값이 있으면 업데이트
                    if key in new_values:
                        f.write(f"{key}={new_values[key]}\n")
                        updated_keys.add(key)
                    else:
                        # 새 값이 없으면 원래 값 유지
                        f.write(f"{key}={original_value}\n")
                except ValueError:
                    # 형식이 잘못된 줄은 그대로 유지
                    f.write(f"{line}\n")
            
            # 파일에 없는 새 값들 추가
            for key, value in new_values.items():
                if key not in updated_keys:
                    f.write(f"{key}={value}\n")
    else:
        # 파일이 없으면 새로 생성
        with open(env_path, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")