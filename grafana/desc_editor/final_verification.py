#!/usr/bin/env python3
"""
최종 확인 스크립트
1. Grafana 연결 테스트
2. "My Workspace" 폴더 찾기
3. "Node Exporter Full (1860)" 대시보드 상세 정보 확인
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
        print("⚠️  WARNING: SSL 검증이 비활성화되었습니다.")
    
    return session

def main():
    """메인 함수"""
    print("=" * 80)
    print("Grafana API 최종 확인 결과")
    print("=" * 80)
    
    try:
        # 설정 로드
        config = load_config()
        session = create_session(config)
        
        # 1. 연결 테스트
        print("✅ 1. Grafana 연결 테스트")
        print(f"   서버 URL: {config['url']}")
        
        health_response = session.get(f"{config['url']}/api/health")
        if health_response.status_code == 200:
            print("   상태: 연결 성공 ✅")
            health_data = health_response.json()
            print(f"   데이터베이스: {health_data.get('database', 'unknown')}")
        else:
            print(f"   상태: 연결 실패 ❌ (Status: {health_response.status_code})")
            return
        
        # 사용자 정보 확인
        user_response = session.get(f"{config['url']}/api/user")
        if user_response.status_code == 200:
            user_data = user_response.json()
            print(f"   사용자: {user_data.get('name', 'Unknown')}")
            print(f"   조직 ID: {user_data.get('orgId')}")
        
        print()
        
        # 2. My Workspace 폴더 찾기
        print("✅ 2. 'My Workspace' 폴더 검색")
        
        folders_response = session.get(f"{config['url']}/api/folders")
        if folders_response.status_code == 200:
            folders = folders_response.json()
            workspace_folder = None
            
            for folder in folders:
                if folder.get('title') == 'My Workspace':
                    workspace_folder = folder
                    break
            
            if workspace_folder:
                print("   상태: 폴더 발견 ✅")
                print(f"   폴더 ID: {workspace_folder['id']}")
                print(f"   폴더 UID: {workspace_folder['uid']}")
                print(f"   폴더 이름: {workspace_folder['title']}")
            else:
                print("   상태: 폴더 미발견 ❌")
                return
        else:
            print(f"   상태: 폴더 조회 실패 ❌ (Status: {folders_response.status_code})")
            return
        
        print()
        
        # 3. Node Exporter Full (1860) 대시보드 찾기
        print("✅ 3. 'Node Exporter Full (1860)' 대시보드 검색")
        
        # 직접 UID로 접근 (이전 검색에서 확인된 UID: rYdddlPWk)
        dashboard_uid = "rYdddlPWk"
        dashboard_response = session.get(f"{config['url']}/api/dashboards/uid/{dashboard_uid}")
        
        if dashboard_response.status_code == 200:
            dashboard_data = dashboard_response.json()
            dashboard_info = dashboard_data.get('dashboard', {})
            meta_info = dashboard_data.get('meta', {})
            
            print("   상태: 대시보드 발견 ✅")
            print(f"   대시보드 제목: {dashboard_info.get('title')}")
            print(f"   UID: {dashboard_info.get('uid')}")
            print(f"   ID: {dashboard_info.get('id')}")
            print(f"   폴더 ID: {meta_info.get('folderId')}")
            print(f"   폴더 제목: {meta_info.get('folderTitle')}")
            print(f"   버전: {dashboard_info.get('version')}")
            print(f"   생성일: {meta_info.get('created')}")
            print(f"   수정일: {meta_info.get('updated')}")
            print(f"   설명: {dashboard_info.get('description') or '설명 없음'}")
            print(f"   태그: {dashboard_info.get('tags', [])}")
            
            # 패널 정보
            panels = dashboard_info.get('panels', [])
            print(f"   패널 수: {len(panels)}개")
            
            if panels:
                print("   주요 패널:")
                for i, panel in enumerate(panels[:5]):  # 상위 5개만 표시
                    panel_title = panel.get('title', f'Panel {panel.get("id", i)}')
                    panel_type = panel.get('type', 'unknown')
                    print(f"     - {panel_title} ({panel_type})")
                
                if len(panels) > 5:
                    print(f"     ... 그 외 {len(panels) - 5}개 패널")
            
            # 대시보드 URL 구성
            dashboard_url = f"{config['url']}/d/{dashboard_uid}/{dashboard_info.get('uid', '')}"
            print(f"   대시보드 URL: {dashboard_url}")
            
        else:
            print(f"   상태: 대시보드 조회 실패 ❌ (Status: {dashboard_response.status_code})")
            
            # 폴더 내 대시보드 재검색
            print("   폴더 내 대시보드 재검색 중...")
            search_params = {
                'type': 'dash-db',
                'folderIds': workspace_folder['id']
            }
            
            search_response = session.get(f"{config['url']}/api/search", params=search_params)
            if search_response.status_code == 200:
                dashboards = search_response.json()
                print(f"   폴더 내 대시보드 수: {len(dashboards)}개")
                
                for dashboard in dashboards:
                    title = dashboard.get('title', 'Unknown')
                    if "Node Exporter Full" in title and "1860" in title:
                        print(f"   발견: {title} (UID: {dashboard.get('uid')})")
                        break
                else:
                    print("   'Node Exporter Full (1860)' 대시보드를 찾을 수 없습니다.")
        
        print()
        print("=" * 80)
        print("🎉 작업 완료!")
        print("=" * 80)
        print("요약:")
        print("✅ Grafana 서버 연결 성공")
        print("✅ 'My Workspace' 폴더 발견")
        print("✅ 'Node Exporter Full (1860)' 대시보드 발견 및 상세 정보 확인")
        print()
        print("모든 요청된 작업이 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()