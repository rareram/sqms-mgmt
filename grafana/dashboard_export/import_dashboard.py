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
            "original_version": original_version,
            "url": result.get("url"),
            "status": result.get("status"),
            "uid_preserved": result.get("uid") == uid
        }
        
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_data = e.response.json()
            error_detail = error_data.get("message", str(e))
        except:
            error_detail = str(e)
        
        print(f"❌ 업로드 실패: {error_detail}")
        
        return {
            "success": False,
            "error": error_detail,
            "status_code": e.response.status_code if hasattr(e, 'response') else None
        }
    
    except Exception as e:
        print(f"❌ 업로드 실패: {e}")
        
        return {
            "success": False,
            "error": str(e)
        }
    
def import_single_dashboard(session, json_file_path, create_backup=True):
    """단일 대시보드 import"""
    print(f"\n🚀 대시보드 import 시작: {json_file_path}")
    
    # JSON 파일 읽기
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            dashboard_json = json.load(f)
    except Exception as e:
        print(f"❌ JSON 파일 읽기 실패: {e}")
        return False
    
    # JSON 유효성 검사
    if not validate_dashboard_json(dashboard_json):
        return False
    
    # UID 추출
    if "dashboard" in dashboard_json:
        uid = dashboard_json["dashboard"]["uid"]
    else:
        uid = dashboard_json["uid"]
    
    # 기존 대시보드 백업
    backup_info = None
    if create_backup:
        backup_info = backup_existing_dashboard(session, uid)
    
    # 업로드 실행
    upload_result = upload_dashboard(session, dashboard_json)
    
    if upload_result["success"]:
        # 요약 출력
        print(f"\n📊 Import 요약:")
        print(f"   - UID 보존: {'✅' if upload_result['uid_preserved'] else '❌'}")
        print(f"   - 버전 변화: {backup_info['original_version'] if backup_info else 'N/A'} → {upload_result['version']}")
        if backup_info:
            print(f"   - 백업 위치: {backup_info['backup_path']}")
        
        return True
    else:
        print(f"\n❌ Import 실패: {upload_result['error']}")
        return False

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="Grafana 대시보드 업로드 스크립트")
    parser.add_argument("json_file", help="업로드할 JSON 파일 경로")
    parser.add_argument("--no-backup", action="store_true", help="백업 생성 안함")
    
    args = parser.parse_args()
    
    print("🚀 Grafana 대시보드 업로드를 시작합니다...")
    
    # 환경변수 확인
    if not GRAFANA_URL or not GRAFANA_TOKEN:
        print("❌ 환경변수 설정을 확인해주세요!")
        print("  .env 파일에 다음 변수들을 설정하세요:")
        print("  GRAFANA_URL=http://your-grafana-server:3000")
        print("  GRAFANA_TOKEN=your-admin-api-token")
        return
    
    # 파일 존재 확인
    if not Path(args.json_file).exists():
        print(f"❌ 파일을 찾을 수 없습니다: {args.json_file}")
        return
    
    # HTTP 세션 설정
    session = setup_session()
    
    # 연결 테스트
    try:
        response = session.get(f"{GRAFANA_URL}/api/org")
        response.raise_for_status()
        print("✅ Grafana 연결 확인 완료")
    except Exception as e:
        print(f"❌ Grafana 연결 실패: {e}")
        print("설정을 확인해주세요:")
        print(f"  - GRAFANA_URL: {GRAFANA_URL}")
        print(f"  - GRAFANA_TOKEN: {'설정됨' if GRAFANA_TOKEN else '미설정'}")
        return
    
    # 대시보드 import
    success = import_single_dashboard(
        session, 
        args.json_file, 
        create_backup=not args.no_backup
    )
    
    if success:
        print(f"\n🎉 대시보드 업로드가 완료되었습니다!")
    else:
        print(f"\n❌ 대시보드 업로드에 실패했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main()