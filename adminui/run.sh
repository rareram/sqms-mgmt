#!/bin/bash

# 가상 환경 활성화 (이미 생성되어 있다고 가정)
# source venv/bin/activate

# 필요한 디렉토리 생성
mkdir -p assets
mkdir -p modules/ldap_manager
mkdir -p modules/gitlab_manager
mkdir -p modules/redmine_manager
mkdir -p modules/grafana_manager

# 애플리케이션 실행
uv run streamlit run main.py&
