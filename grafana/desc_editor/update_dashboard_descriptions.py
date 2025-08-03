#!/usr/bin/env python3
"""
Grafana 대시보드에 생성된 description들을 업데이트하는 스크립트
"""

import os
import json
import requests
import urllib3
from datetime import datetime
from dotenv import load_dotenv

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 환경변수 로드
load_dotenv()

GRAFANA_URL = os.getenv('GRAFANA_URL')
GRAFANA_TOKEN = os.getenv('GRAFANA_TOKEN')
GRAFANA_ORG_ID = os.getenv('GRAFANA_ORG_ID', '1')
SSL_VERIFY = os.getenv('SSL_VERIFY', 'false').lower() == 'true'

# Node Exporter Full 대시보드 UID
DASHBOARD_UID = "rYdddlPWk"

def setup_session():
    """HTTP 세션 설정"""
    session = requests.Session()
    session.headers.update({
        'Authorization': f'Bearer {GRAFANA_TOKEN}',
        'Content-Type': 'application/json',
        'X-Grafana-Org-Id': GRAFANA_ORG_ID
    })
    session.verify = SSL_VERIFY
    return session

def get_dashboard(session, uid):
    """대시보드 정보 가져오기"""
    url = f"{GRAFANA_URL}/api/dashboards/uid/{uid}"
    print(f"대시보드 조회 중: {url}")
    
    try:
        response = session.get(url)
        response.raise_for_status()
        
        dashboard_data = response.json()
        print(f"대시보드 '{dashboard_data['dashboard']['title']}' 조회 성공")
        return dashboard_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 대시보드 조회 실패: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"응답 상태 코드: {e.response.status_code}")
            print(f"응답 내용: {e.response.text}")
        return None

def save_backup(dashboard_data, filename):
    """대시보드 백업 저장"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
        print(f"✅ 백업 저장 완료: {filename}")
        return True
    except Exception as e:
        print(f"❌ 백업 저장 실패: {e}")
        return False

def load_descriptions(filename):
    """생성된 description들 로드"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Description 파일 로드 완료: {data['total_panels_processed']}개 패널")
        return data['panel_descriptions']
    except Exception as e:
        print(f"❌ Description 파일 로드 실패: {e}")
        return None

def update_panel_descriptions(dashboard, descriptions):
    """패널들의 description 업데이트"""
    updated_count = 0
    skipped_count = 0
    errors = []
    
    def update_panels_recursive(panels):
        nonlocal updated_count, skipped_count
        
        for panel in panels:
            panel_id = str(panel.get('id', ''))
            
            if panel_id in descriptions:
                desc_info = descriptions[panel_id]
                panel['description'] = desc_info['description']
                updated_count += 1
                print(f"✅ 패널 {panel_id} '{desc_info['title']}' description 업데이트")
            else:
                skipped_count += 1
                print(f"⚠️  패널 {panel_id} '{panel.get('title', 'Unknown')}' - description 없음")
            
            # 중첩된 패널 처리 (row 타입 등)
            if 'panels' in panel:
                update_panels_recursive(panel['panels'])
    
    try:
        if 'panels' in dashboard:
            update_panels_recursive(dashboard['panels'])
        
        print(f"\n📊 업데이트 완료:")
        print(f"  - 업데이트된 패널: {updated_count}개")
        print(f"  - 건너뛴 패널: {skipped_count}개")
        
        return updated_count, skipped_count, errors
        
    except Exception as e:
        error_msg = f"패널 업데이트 중 오류: {e}"
        print(f"❌ {error_msg}")
        errors.append(error_msg)
        return updated_count, skipped_count, errors

def update_dashboard(session, dashboard_data):
    """대시보드 업데이트"""
    url = f"{GRAFANA_URL}/api/dashboards/db"
    
    try:
        # 메타데이터 설정
        dashboard_payload = {
            'dashboard': dashboard_data['dashboard'],
            'overwrite': True,
            'message': f'Description 자동 업데이트 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        }
        
        print(f"대시보드 업데이트 중...")
        response = session.post(url, json=dashboard_payload)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ 대시보드 업데이트 성공!")
        print(f"  - UID: {result.get('uid')}")
        print(f"  - URL: {result.get('url')}")
        print(f"  - 버전: {result.get('version')}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 대시보드 업데이트 실패: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"응답 상태 코드: {e.response.status_code}")
            print(f"응답 내용: {e.response.text}")
        return False

def main():
    """메인 실행 함수"""
    print("🚀 Grafana 대시보드 Description 업데이트 시작")
    print("=" * 60)
    
    # 파일 경로 설정
    descriptions_file = "node_exporter_descriptions_20250726_224736.json"
    backup_file = f"dashboard_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # 1. Description 파일 로드
    print("1️⃣ Description 파일 로드 중...")
    descriptions = load_descriptions(descriptions_file)
    if not descriptions:
        return False
    
    # 2. Grafana 세션 설정
    print("\n2️⃣ Grafana 연결 설정 중...")
    session = setup_session()
    
    # 3. 현재 대시보드 조회 및 백업
    print("\n3️⃣ 현재 대시보드 조회 및 백업 중...")
    dashboard_data = get_dashboard(session, DASHBOARD_UID)
    if not dashboard_data:
        return False
    
    # 백업 저장
    if not save_backup(dashboard_data, backup_file):
        return False
    
    # 4. 패널 description 업데이트
    print("\n4️⃣ 패널 description 업데이트 중...")
    updated_count, skipped_count, errors = update_panel_descriptions(
        dashboard_data['dashboard'], descriptions
    )
    
    if errors:
        print("\n❌ 업데이트 중 오류 발생:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    # 5. 대시보드 저장
    print("\n5️⃣ 업데이트된 대시보드 저장 중...")
    if not update_dashboard(session, dashboard_data):
        return False
    
    # 6. 결과 보고
    print("\n" + "=" * 60)
    print("🎉 작업 완료!")
    print(f"  📁 백업 파일: {backup_file}")
    print(f"  📊 업데이트 결과:")
    print(f"    - 성공: {updated_count}개 패널")
    print(f"    - 건너뜀: {skipped_count}개 패널")
    print(f"  🔗 대시보드 URL: {GRAFANA_URL}/d/{DASHBOARD_UID}")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)