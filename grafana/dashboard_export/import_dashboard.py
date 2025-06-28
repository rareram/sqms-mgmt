import requests
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import argparse
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

# 설정 - .env 파일에서 불러오기
GRAFANA_URL = os.getenv("GRAFANA_URL")
GRAFANA_TOKEN = os.getenv("GRAFANA_TOKEN")

def setup_session():
    """HTTP 세션 설정"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {GRAFANA_TOKEN}",
        "Content-Type": "application/json"
    })
    return session

def backup_existing_dashboard(session, uid):
    """기존 대시보드 백업"""
    print(f"💾 기존 대시보드 백업 중 (UID: {uid})...")
    
    url = f"{GRAFANA_URL}/api/dashboards/uid/{uid}"
    
    try:
        response = session.get(url)
        if response.status_code == 404:
            print("ℹ️  기존 대시보드가 없습니다. (새로 생성됨)")
            return None
        
        response.raise_for_status()
        dashboard_data = response.json()
        
        # 백업 파일 생성
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        title = dashboard_data["dashboard"]["title"]
        version = dashboard_data["dashboard"]["version"]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')
        
        backup_filename = f"backup_{uid}_{safe_title}_v{version}_{timestamp}.json"
        backup_path = backup_dir / backup_filename
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 백업 완료: {backup_path}")
        
        return {
            "original_version": version,
            "backup_path": str(backup_path),
            "title": title
        }
        
    except Exception as e:
        print(f"❌ 백업 실패: {e}")
        return None

def validate_dashboard_json(dashboard_json):
    """대시보드 JSON 유효성 검사"""
    required_fields = ["uid", "title", "panels"]
    
    if "dashboard" in dashboard_json:
        dashboard = dashboard_json["dashboard"]
    else:
        dashboard = dashboard_json
    
    missing_fields = [field for field in required_fields if field not in dashboard]
    
    if missing_fields:
        print(f"❌ 필수 필드 누락: {missing_fields}")
        return False
    
    uid = dashboard["uid"]
    title = dashboard["title"]
    panels_count = len(dashboard.get("panels", []))
    
    print(f"📋 대시보드 정보:")
    print(f"   - UID: {uid}")
    print(f"   - 제목: {title}")
    print(f"   - 패널 수: {panels_count}")
    
    # Description 통계
    descriptions_count = sum(1 for panel in dashboard.get("panels", []) 
                           if panel.get("description", "").strip())
    print(f"   - Description 있는 패널: {descriptions_count}")
    
    return True

def upload_dashboard(session, dashboard_json, overwrite=True):
    """대시보드 업로드"""
    
    # JSON 구조 정규화
    if "dashboard" in dashboard_json:
        dashboard = dashboard_json["dashboard"]
        folder_id = dashboard_json.get("meta", {}).get("folderId", 0)
    else:
        dashboard = dashboard_json
        folder_id = 0  # General 폴더
    
    uid = dashboard["uid"]
    title = dashboard["title"]
    original_version = dashboard.get("version", 0)
    
    print(f"📤 대시보드 업로드 중: {title} (UID: {uid})")
    
    # 업로드 데이터 구성
    upload_data = {
        "dashboard": dashboard,
        "folderId": folder_id,
        "overwrite": overwrite,
        "message": f"Updated via import script at {datetime.now().isoformat()}"
    }
    
    # 버전 정보 제거 (Grafana가 자동으로 관리)
    if "version" in upload_data["dashboard"]:
        del upload_data["dashboard"]["version"]
    if "id" in upload_data["dashboard"]:
        del upload_data["dashboard"]["id"]
    
    url = f"{GRAFANA_URL}/api/dashboards/db"
    
    try:
        response = session.post(url, json=upload_data)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"✅ 업로드 성공!")
        print(f"   - 응답 상태: {result.get('status', 'unknown')}")
        print(f"   - 새 버전: {result.get('version', 'unknown')}")
        print(f"   - 원본 버전: {original_version}")
        print(f"   - UID 보존: {result.get('uid') == uid} ({'✅' if result.get('uid') == uid else '❌'})")
        print(f"   - URL: {result.get('url', 'N/A')}")
        
        return {
            "success": True,
            "uid": result.get("uid"),
            "version": result.get("version"),