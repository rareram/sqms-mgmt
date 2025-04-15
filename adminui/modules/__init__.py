# modules 패키지 초기화 파일
# 모듈 로딩을 위한 기본 패키지 구조를 제공합니다.

"""
project_root/
├── modules/
│   ├── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── version.py
│   ├── gitlab_manager/
│   │   ├── __init__.py
│   │   └── module_info.json
│   ├── redmine_manager/
│   │   ├── __init__.py
│   │   └── module_info.json
│   ├── grafana_manager/
│   │   ├── __init__.py
│   │   └── module_info.json
│   └── ldap_manager/
│       ├── __init__.py
│       └── module_info.json
├── config/
│   └── modules/
│       ├── gitlab_manager.json
│       ├── redmine_manager.json
│       ├── grafana_manager.json
│       └── ldap_manager.json
└── main.py
"""