#!/usr/bin/env python3
"""
전체 대시보드 검색 스크립트
"Node Exporter Full" 관련 대시보드를 모든 폴더에서 찾기
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
    
    return session

def search_all_dashboards(session, base_url):
    """모든 대시보드 검색"""
    print("=" * 80)
    print("전체 대시보드 검색")
    print("=" * 80)
    
    try:
        # 모든 대시보드 검색 (폴더 제한 없음)
        params = {'type': 'dash-db'}
        
        response = session.get(f"{base_url}/api/search", params=params)
        print(f"Dashboard Search API - Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"대시보드 검색 실패: {response.text}")
            return []
        
        dashboards = response.json()
        print(f"총 {len(dashboards)}개의 대시보드를 찾았습니다:")
        
        # 폴더별로 그룹화
        folder_groups = {}
        for dashboard in dashboards:
            folder_id = dashboard.get('folderId', 0)
            folder_title = dashboard.get('folderTitle', 'General' if folder_id == 0 else f'Folder {folder_id}')
            
            if folder_title not in folder_groups:
                folder_groups[folder_title] = []
            folder_groups[folder_title].append(dashboard)
        
        # 폴더별 대시보드 출력
        node_exporter_dashboards = []
        for folder_title, folder_dashboards in folder_groups.items():
            print(f"\n📁 {folder_title} ({len(folder_dashboards)}개 대시보드):")
            
            for dashboard in folder_dashboards:
                title = dashboard.get('title', 'Unknown')
                uid = dashboard.get('uid', 'No UID')
                
                print(f"  - {title} (UID: {uid})")
                
                # Node Exporter 관련 대시보드 찾기
                if "node exporter" in title.lower() or "1860" in title:
                    node_exporter_dashboards.append(dashboard)
                    print(f"    ✅ Node Exporter 관련 대시보드 발견!")
        
        if node_exporter_dashboards:
            print(f"\n" + "=" * 80)
            print(f"Node Exporter 관련 대시보드 상세 정보")
            print("=" * 80)
            
            for dashboard in node_exporter_dashboards:
                print(f"\n대시보드: {dashboard['title']}")
                print(f"  UID: {dashboard['uid']}")
                print(f"  폴더: {dashboard.get('folderTitle', 'General')}")
                print(f"  폴더 ID: {dashboard.get('folderId', 0)}")
                print(f"  URI: {dashboard.get('uri', 'N/A')}")
                print(f"  URL: {dashboard.get('url', 'N/A')}")
                
                # 상세 정보 조회
                try:
                    detail_response = session.get(f"{base_url}/api/dashboards/uid/{dashboard['uid']}")
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        dashboard_info = detail_data.get('dashboard', {})
                        
                        print(f"  Description: {dashboard_info.get('description', 'No description')}")
                        print(f"  Tags: {dashboard_info.get('tags', [])}")
                        print(f"  Version: {dashboard_info.get('version', 'Unknown')}")
                        
                        panels = dashboard_info.get('panels', [])
                        print(f"  Panels: {len(panels)}개")
                    else:
                        print(f"  상세 정보 조회 실패: {detail_response.status_code}")
                except Exception as e:
                    print(f"  상세 정보 조회 오류: {e}")
        
        return node_exporter_dashboards
        
    except Exception as e:
        print(f"대시보드 검색 실패: {e}")
        return []

def search_by_query(session, base_url, query):
    """쿼리로 대시보드 검색"""
    print(f"\n" + "=" * 80)
    print(f"쿼리 '{query}'로 대시보드 검색")
    print("=" * 80)
    
    try:
        params = {
            'type': 'dash-db',
            'query': query
        }
        
        response = session.get(f"{base_url}/api/search", params=params)
        print(f"Query Search API - Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"쿼리 검색 실패: {response.text}")
            return []
        
        dashboards = response.json()
        print(f"'{query}' 쿼리로 {len(dashboards)}개의 대시보드를 찾았습니다:")
        
        for dashboard in dashboards:
            title = dashboard.get('title', 'Unknown')
            uid = dashboard.get('uid', 'No UID')
            folder_title = dashboard.get('folderTitle', 'General')
            
            print(f"  - {title} (UID: {uid}, 폴더: {folder_title})")
        
        return dashboards
        
    except Exception as e:
        print(f"쿼리 검색 실패: {e}")
        return []

def main():
    """메인 함수"""
    try:
        # 설정 로드
        print("전체 대시보드 검색 시작...")
        config = load_config()
        
        # 세션 생성
        session = create_session(config)
        
        # 1. 모든 대시보드 검색
        node_exporter_dashboards = search_all_dashboards(session, config['url'])
        
        # 2. 쿼리로 검색
        print(f"\n" + "=" * 80)
        print("다양한 쿼리로 Node Exporter 대시보드 검색")
        print("=" * 80)
        
        queries = ["node exporter", "Node Exporter", "1860", "node", "exporter"]
        
        all_found = []
        for query in queries:
            found = search_by_query(session, config['url'], query)
            all_found.extend(found)
        
        # 중복 제거
        unique_dashboards = {}
        for dashboard in all_found:
            uid = dashboard.get('uid')
            if uid and uid not in unique_dashboards:
                unique_dashboards[uid] = dashboard
        
        if unique_dashboards:
            print(f"\n" + "=" * 80)
            print(f"최종 결과: {len(unique_dashboards)}개의 고유한 관련 대시보드")
            print("=" * 80)
            
            for dashboard in unique_dashboards.values():
                title = dashboard.get('title', 'Unknown')
                uid = dashboard.get('uid', 'No UID')
                folder_title = dashboard.get('folderTitle', 'General')
                
                print(f"✅ {title}")
                print(f"   UID: {uid}")
                print(f"   폴더: {folder_title}")
                print()
        
        print("검색 완료!")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()