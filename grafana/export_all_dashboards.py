#!/usr/bin/env python3
"""
Grafana 대시보드 전체 추출 스크립트
- 모든 대시보드를 JSON 형태로 추출
- UID 기반 파일명으로 저장
- 폴더 구조 정보 포함
"""

import requests
import json
import os
from datetime import datetime
import time
from pathlib import Path

# 설정 - 실제 환경에 맞게 수정하세요
GRAFANA_URL = "http://your-grafana-url:3000"  # 예: "http://localhost:3000"
GRAFANA_TOKEN = "your-admin-api-token-here"   # Admin 권한 API 토큰

# 출력 디렉토리 설정
EXPORT_DIR = f"grafana_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def setup_session():
    """HTTP 세션 설정"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {GRAFANA_TOKEN}",
        "Content-Type": "application/json"
    })
    return session

def get_all_dashboards(session):
    """모든 대시보드 목록 조회"""
    print("📋 대시보드 목록을 조회하는 중...")
    
    url = f"{GRAFANA_URL}/api/search"
    params = {
        "type": "dash-db",
        "limit": 5000  # 충분히 큰 수로 설정
    }
    
    try:
        response = session.get(url, params=params)
        response.raise_for_status()
        
        dashboards = response.json()
        print(f"✅ 총 {len(dashboards)}개의 대시보드를 발견했습니다.")
        
        return dashboards
    except Exception as e:
        print(f"❌ 대시보드 목록 조회 실패: {e}")
        return []

def get_folder_info(session):
    """폴더 정보 조회"""
    print("📁 폴더 정보를 조회하는 중...")
    
    url = f"{GRAFANA_URL}/api/folders"
    
    try:
        response = session.get(url)
        response.raise_for_status()
        
        folders = response.json()
        
        # 폴더 ID -> 폴더 정보 매핑
        folder_map = {}
        for folder in folders:
            folder_map[folder["id"]] = folder
        
        print(f"✅ 총 {len(folders)}개의 폴더를 발견했습니다.")
        return folder_map
    except Exception as e:
        print(f"❌ 폴더 정보 조회 실패: {e}")
        return {}

def export_dashboard(session, dashboard_info, folder_map):
    """개별 대시보드 추출"""
    uid = dashboard_info["uid"]
    title = dashboard_info["title"]
    folder_id = dashboard_info.get("folderId", 0)
    
    print(f"📄 대시보드 추출 중: {title} (UID: {uid})")
    
    url = f"{GRAFANA_URL}/api/dashboards/uid/{uid}"
    
    try:
        response = session.get(url)
        response.raise_for_status()
        
        dashboard_data = response.json()
        
        # 메타데이터 추가
        dashboard_data["meta"]["exportInfo"] = {
            "exportedAt": datetime.now().isoformat(),
            "exportedBy": "export_all_dashboards.py",
            "originalFolderId": folder_id,
            "folderInfo": folder_map.get(folder_id, {"title": "General", "uid": ""})
        }
        
        # 파일명 생성 (특수문자 제거)
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')
        
        version = dashboard_data["dashboard"].get("version", 0)
        filename = f"{uid}_{safe_title}_v{version}.json"
        
        # 폴더별 디렉토리 생성
        if folder_id and folder_id in folder_map:
            folder_name = folder_map[folder_id]["title"]
            safe_folder_name = "".join(c for c in folder_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_folder_name = safe_folder_name.replace(' ', '_')
            output_dir = Path(EXPORT_DIR) / "folders" / safe_folder_name
        else:
            output_dir = Path(EXPORT_DIR) / "folders" / "General"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON 파일 저장
        output_path = output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 저장 완료: {output_path}")
        
        return {
            "uid": uid,
            "title": title,
            "version": version,
            "folderId": folder_id,
            "folderTitle": folder_map.get(folder_id, {}).get("title", "General"),
            "filename": filename,
            "path": str(output_path),
            "panels_count": len(dashboard_data["dashboard"].get("panels", [])),
            "has_descriptions": sum(1 for panel in dashboard_data["dashboard"].get("panels", []) 
                                  if panel.get("description", "").strip())
        }
        
    except Exception as e:
        print(f"❌ 대시보드 추출 실패 [{title}]: {e}")
        return None

def create_export_summary(export_results, folder_map):
    """추출 결과 요약 생성"""
    summary = {
        "exportInfo": {
            "exportedAt": datetime.now().isoformat(),
            "totalDashboards": len(export_results),
            "successfulExports": len([r for r in export_results if r is not None]),
            "failedExports": len([r for r in export_results if r is None])
        },
        "folderStructure": folder_map,
        "dashboards": [r for r in export_results if r is not None]
    }
    
    # 요약 통계
    successful_results = [r for r in export_results if r is not None]
    total_panels = sum(r["panels_count"] for r in successful_results)
    total_descriptions = sum(r["has_descriptions"] for r in successful_results)
    
    summary["statistics"] = {
        "totalPanels": total_panels,
        "panelsWithDescription": total_descriptions,
        "panelsWithoutDescription": total_panels - total_descriptions,
        "descriptionCoverage": f"{(total_descriptions/total_panels*100):.1f}%" if total_panels > 0 else "0%"
    }
    
    # 요약 파일 저장
    summary_path = Path(EXPORT_DIR) / "export_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 추출 요약:")
    print(f"   - 총 대시보드: {summary['exportInfo']['totalDashboards']}개")
    print(f"   - 성공: {summary['exportInfo']['successfulExports']}개")
    print(f"   - 실패: {summary['exportInfo']['failedExports']}개")
    print(f"   - 총 패널: {total_panels}개")
    print(f"   - Description 있는 패널: {total_descriptions}개")
    print(f"   - Description 커버리지: {summary['statistics']['descriptionCoverage']}")
    print(f"✅ 요약 정보 저장: {summary_path}")

def main():
    """메인 실행 함수"""
    print("🚀 Grafana 대시보드 전체 추출을 시작합니다...")
    print(f"📂 출력 디렉토리: {EXPORT_DIR}")
    
    # 출력 디렉토리 생성
    Path(EXPORT_DIR).mkdir(exist_ok=True)
    
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
        print(f"  - GRAFANA_TOKEN: {'*' * len(GRAFANA_TOKEN) if GRAFANA_TOKEN else 'None'}")
        return
    
    # 폴더 정보 조회
    folder_map = get_folder_info(session)
    
    # 대시보드 목록 조회
    dashboards = get_all_dashboards(session)
    if not dashboards:
        print("❌ 추출할 대시보드가 없습니다.")
        return
    
    # 각 대시보드 추출
    export_results = []
    for i, dashboard in enumerate(dashboards, 1):
        print(f"\n[{i}/{len(dashboards)}]", end=" ")
        result = export_dashboard(session, dashboard, folder_map)
        export_results.append(result)
        
        # API 제한 방지를 위한 지연
        time.sleep(0.1)
    
    # 추출 결과 요약
    create_export_summary(export_results, folder_map)
    
    print(f"\n🎉 모든 대시보드 추출이 완료되었습니다!")
    print(f"📂 결과 확인: {EXPORT_DIR}/")

if __name__ == "__main__":
    # 설정 확인
    if GRAFANA_URL == "http://your-grafana-url:3000" or GRAFANA_TOKEN == "your-admin-api-token-here":
        print("❌ 설정을 먼저 수정해주세요!")
        print("스크립트 상단의 GRAFANA_URL과 GRAFANA_TOKEN을 설정하세요.")
        exit(1)
    
    main()
