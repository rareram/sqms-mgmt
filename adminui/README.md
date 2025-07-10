# IT 관리 시스템

사내 IT 시스템(LDAP, GitLab, Redmine, Grafana 등)을 통합적으로 관리하기 위한 Streamlit 기반 모듈형 웹 애플리케이션입니다.

## 주요 기능

- **LDAP 관리**: 퇴사자 관리, 사용자 검색 및 LDAP 설정
- **GitLab 관리**: 저장소 관리, 사용자 관리, 미사용 저장소 조회
- **Redmine 관리**: 프로젝트 관리, 사용자 관리
- **Grafana 관리**: 팀 관리, 폴더 권한 관리

## 시스템 요구사항

- Python 3.10 이상
- LDAP 서버 접근 권한
- GitLab, Redmine, Grafana API 접근 권한

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/rareram/sqms-mgmt.git
cd sqms-mgmt/adminui
```

2. uv 전용 가상 환경 생성 및 활성화
```
uv run main.py
```

3. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 작성합니다:
```
# LDAP 서버 정보
LDAP_SERVER=ldap://your-ldap-server:389
LDAP_BASE_DN=dc=example,dc=com
LDAP_USER_DN=cn=admin,dc=example,dc=com 또는 ldap-id@host.com
LDAP_PASSWORD=your-ldap-password
LDAP_TYPE=activedirectory 또는 openldap

# GitLab 서버 정보
GITLAB_HOST=http://your-gitlab-server
GITLAB_TOKEN=your-gitlab-token

# Redmine 서버 정보
REDMINE_URL=http://your-redmine-server
REDMINE_API_KEY=your-redmine-api-key

# Grafana 서버 정보
GRAFANA_URL=http://your-grafana-server:3000
GRAFANA_USERNAME=admin
GRAFANA_PASSWORD=your-grafana-password
```

4. 의존성 패키지 설치 및 애플리케이션 실행
```bash
uv run streamlit run main.py

# python-ldap 설치 중 오류 발생시 Ubuntu/Debian 계열
sudo apt-get install gcc build-essential
sudo apt-get install libldap2-dev libsasl2-dev python3-dev
# Red hat/CentOS/Rocky Linux 계열
sudo dnf install openldap-devel
# macOS (Homebrew 사용)
brew install openldap
```

## 모듈 구조

- **main.py**: 메인 애플리케이션 진입점
- **modules/**: 각 서비스별 모듈
  - **ldap_manager/**: LDAP 관리 모듈
  - **gitlab_manager/**: GitLab 관리 모듈
  - **redmine_manager/**: Redmine 관리 모듈
  - **grafana_manager/**: Grafana 관리 모듈

## 모듈 추가 방법

1. `modules` 디렉토리에 새 모듈 디렉토리 생성 (예: `new_module`)
2. `__init__.py` 파일 생성 및 `show_module()` 함수 구현
3. `module_info.json` 파일 생성:
```json
{
    "id": "new_module",
    "name": "새 모듈",
    "description": "새 모듈 설명",
    "version": "1.0.0",
    "author": "관리자",
    "dependencies": ["dependency1", "dependency2"]
}
```
4. 앱 설정에서 모듈 활성화

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.