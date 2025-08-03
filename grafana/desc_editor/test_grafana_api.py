#!/usr/bin/env python3
"""
Grafana API 테스트 스크립트
1. Grafana 연결 테스트
2. "My Workspace" 폴더 찾기
3. 폴더 내의 "Node Exporter Full (1860)" 대시보드 찾기
"""

import requests
import urllib3
import os
from dotenv import load_dotenv
import json

# SSL 경고 억제 (개발용)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_config():
    """환경 변수 로드 및 설정"""
    load_dotenv()
    
    config = {
        'url': os.getenv('GRAFANA_URL', 'http://localhost:3000').rstrip('/'),
        'token': os.getenv('GRAFANA_TOKEN'),
        'org_id': os.getenv('GRAFANA_ORG_ID', '1'),
        'ssl_verify': os.getenv('SSL_VERIFY', 'true').lower() != 'false'
    }
    
    if not config['token']:
        raise ValueError("GRAFANA_TOKEN이 설정되지 않았습니다. .env 파일을 확인하세요.")
    
    return config

def create_session(config):
    """HTTP 세션 생성"""
    session = requests.Session()
    
    # 헤더 설정
    headers = {
        'Authorization': f'Bearer {config["token"]}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Grafana-Org-Id': config['org_id']
    }
    session.headers.update(headers)
    
    # SSL 검증 설정
    session.verify = config['ssl_verify']
    session.timeout = 30
    
    if not config['ssl_verify']:
        print("⚠️  WARNING: SSL 검증이 비활성화되었습니다. 개발용으로만 사용하세요!")
    
    return session

def test_connection(session, base_url):
    """1. Grafana 연결 테스트"""
    print("=" * 60)
    print("1. Grafana 연결 테스트")
    print("=" * 60)
    
    try:
        # Health check
        response = session.get(f"{base_url}/api/health")
        print(f"Health Check - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"Health Status: {json.dumps(health_data, indent=2)}")
        
        # User info (현재 인증된 사용자 정보)
        user_response = session.get(f"{base_url}/api/user")
        print(f"\nUser Info - Status Code: {user_response.status_code}")
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            print(f"Current User: {user_data.get('name', 'Unknown')} ({user_data.get('email', 'No email')})")
            print(f"User ID: {user_data.get('id')}")
            print(f"Organization: {user_data.get('orgId')}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"연결 테스트 실패: {e}")
        return False

def find_workspace_folder(session, base_url):
    """2. "My Workspace" 폴더 찾기"""
    print("\n" + "=" * 60)
    print("2. 'My Workspace' 폴더 찾기")
    print("=" * 60)
    
    try:
        response = session.get(f"{base_url}/api/folders")
        print(f"Folders API - Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"폴더 조회 실패: {response.text}")
            return None
        
        folders = response.json()
        print(f"총 {len(folders)}개의 폴더를 찾았습니다:")
        
        workspace_folder = None
        for folder in folders:
            folder_name = folder.get('title', 'Unknown')
            folder_id = folder.get('id')
            folder_uid = folder.get('uid', 'No UID')
            
            print(f"  - {folder_name} (ID: {folder_id}, UID: {folder_uid})")
            
            if folder_name == "My Workspace":
                workspace_folder = folder
                print(f"    ✅ Found 'My Workspace' folder!")
        
        if workspace_folder:
            print(f"\n'My Workspace' 폴더 정보:")
            print(f"  ID: {workspace_folder['id']}")
            print(f"  UID: {workspace_folder['uid']}")
            print(f"  Title: {workspace_folder['title']}")
            print(f"  URL: {workspace_folder.get('url', 'N/A')}")
            
        return workspace_folder
        
    except Exception as e:
        print(f"폴더 조회 실패: {e}")
        return None

def find_node_exporter_dashboard(session, base_url, folder_id):
    """3. "Node Exporter Full (1860)" 대시보드 찾기"""
    print("\n" + "=" * 60)
    print("3. 'Node Exporter Full (1860)' 대시보드 찾기")
    print("=" * 60)
    
    try:
        # 특정 폴더의 대시보드 검색
        params = {
            'type': 'dash-db',
            'folderIds': folder_id
        }
        
        response = session.get(f"{base_url}/api/search", params=params)
        print(f"Dashboard Search API - Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"대시보드 검색 실패: {response.text}")
            return None
        
        dashboards = response.json()
        print(f"'My Workspace' 폴더에서 {len(dashboards)}개의 대시보드를 찾았습니다:")
        
        node_exporter_dashboard = None
        for dashboard in dashboards:
            title = dashboard.get('title', 'Unknown')
            uid = dashboard.get('uid', 'No UID')
            uri = dashboard.get('uri', 'N/A')
            
            print(f"  - {title} (UID: {uid})")
            
            # "Node Exporter Full" 또는 "1860"이 포함된 대시보드 찾기
            if ("Node Exporter Full" in title and "1860" in title) or title == "Node Exporter Full (1860)":
                node_exporter_dashboard = dashboard
                print(f"    ✅ Found 'Node Exporter Full (1860)' dashboard!")
        
        if node_exporter_dashboard:
            print(f"\n'Node Exporter Full (1860)' 대시보드 정보:")
            print(f"  ID: {node_exporter_dashboard.get('id')}")
            print(f"  UID: {node_exporter_dashboard['uid']}")
            print(f"  Title: {node_exporter_dashboard['title']}")
            print(f"  URI: {node_exporter_dashboard.get('uri')}")
            print(f"  URL: {node_exporter_dashboard.get('url')}")
            print(f"  Folder ID: {node_exporter_dashboard.get('folderId')}")
            
            # 대시보드 상세 정보 조회
            print(f"\n대시보드 상세 정보 조회 중...")
            detail_response = session.get(f"{base_url}/api/dashboards/uid/{node_exporter_dashboard['uid']}")
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                dashboard_info = detail_data.get('dashboard', {})
                
                print(f"  Description: {dashboard_info.get('description', 'No description')}")
                print(f"  Tags: {dashboard_info.get('tags', [])}")
                print(f"  Version: {dashboard_info.get('version', 'Unknown')}")
                print(f"  Created: {detail_data.get('meta', {}).get('created', 'Unknown')}")
                print(f"  Updated: {detail_data.get('meta', {}).get('updated', 'Unknown')}")
                
                panels = dashboard_info.get('panels', [])
                print(f"  Panels: {len(panels)}개의 패널")
                
                # 패널 정보 간략히 출력
                if panels:
                    print(f"  Panel 목록 (상위 5개):")
                    for i, panel in enumerate(panels[:5]):
                        panel_title = panel.get('title', f'Panel {panel.get("id", i)}')
                        panel_type = panel.get('type', 'unknown')
                        print(f"    - {panel_title} ({panel_type})")
                    
                    if len(panels) > 5:
                        print(f"    ... 그 외 {len(panels) - 5}개 패널")
            else:
                print(f"  상세 정보 조회 실패: {detail_response.status_code}")
        
        return node_exporter_dashboard
        
    except Exception as e:
        print(f"대시보드 검색 실패: {e}")
        return None

def main():
    """메인 함수"""
    try:
        # 설정 로드
        print("Grafana API 테스트 시작...")
        config = load_config()
        print(f"Grafana URL: {config['url']}")
        print(f"Organization ID: {config['org_id']}")
        
        # 세션 생성
        session = create_session(config)
        
        # 1. 연결 테스트
        if not test_connection(session, config['url']):
            print("연결 테스트 실패. 프로그램을 종료합니다.")
            return
        
        # 2. My Workspace 폴더 찾기
        workspace_folder = find_workspace_folder(session, config['url'])
        if not workspace_folder:
            print("'My Workspace' 폴더를 찾을 수 없습니다. 프로그램을 종료합니다.")
            return
        
        # 3. Node Exporter Full (1860) 대시보드 찾기
        dashboard = find_node_exporter_dashboard(session, config['url'], workspace_folder['id'])
        if not dashboard:
            print("'Node Exporter Full (1860)' 대시보드를 찾을 수 없습니다.")
        
        print("\n" + "=" * 60)
        print("모든 작업이 완료되었습니다!")
        print("=" * 60)
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()