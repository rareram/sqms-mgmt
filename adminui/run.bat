@echo off
REM 가상 환경 활성화 (이미 생성되어 있다고 가정)
call venv\Scripts\activate

REM 필요한 디렉토리 생성
if not exist assets mkdir assets
if not exist modules\ldap_manager mkdir modules\ldap_manager
if not exist modules\gitlab_manager mkdir modules\gitlab_manager
if not exist modules\redmine_manager mkdir modules\redmine_manager
if not exist modules\grafana_manager mkdir modules\grafana_manager

REM 애플리케이션 실행
streamlit run main.py