import requests
import json
import os
from datetime import datetime
import time
from pathlib import Path
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

# 설정 - .env 파일에서 불러오기
GRAFANA_URL = os.getenv("GRAFANA_URL")
GRAFANA_TOKEN = os.getenv("GRAFANA_TOKEN")

# 출력 디렉토리 설정
EXPORT_DIR = f"grafana_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def setup_session():
    """HTTP 세션 설정"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {GRAFANA_TOKEN}",
        "Content-Type": "application/json"
    })
    session.verify = False  # SSL 인증서 검증 비활성화 (개발 환경에서만 사용)
    return session

def get_all_dashboards(session):
    """모든 대시보드 목록 조회 - Pagination 지원"""
    print("📋 대시보드 목록을 조회하는 중...")
    
    all_dashboards = []
    page = 1
    page_size = 100  # 페이지당 항목 수
    
    while True:
        url = f"{GRAFANA_URL}/api/search"
        params = {
            "type": "dash-db",
            "limit": page_size,
            "page": page
        }
        
        try:
            print(f"   페이지 {page} 조회 중... (URL: {url}?{requests.compat.urlencode(params)})")
            response = session.get(url, params=params)
            response.raise_for_status()

            # 응답 헤더 확인
            for header, value in response.headers.items():
                if any(keyword in header.lower() for keyword in ['total', 'count', 'page', 'limit']):
                    print(f"   응답 헤더: {header} = {value}")
            
            dashboards = response.json()
            
            if not dashboards:
                print(f"    페이지 {page}: 빈 응답 - 종료")
                break
            
            all_dashboards.extend(dashboards)
            print(f"   페이지 {page}: {len(dashboards)}개 발견 (누적: {len(all_dashboards)}개)")
            
            # 페이지 크기보다 적게 반환되면 마지막 페이지
            if len(dashboards) < page_size:
                print(f"   페이지 {page}: 반환된 항목이 {len(dashboards)}개로 페이지 크기({page_size})보다 적음 - 마지막 페이지")
                break
                
            page += 1
            # 무한 루프 방지
            if page > 50:  # 최대 5000개 대시보드
                print("   ⚠️  최대 페이지 수 도달 - 강제 종료")
                break

            time.sleep(0.2)  # API 제한 방지
            
        except Exception as e:
            print(f"❌ 페이지 {page} 조회 실패: {e}")
            break
    
    # 방법 2: offset 방식으로 재시도 (30개로 제한된 경우)
    if len(all_dashboards) == 30:
        print("\n🔍 방법 2: offset 방식으로 재시도")
        all_dashboards = []
        offset = 0
        limit = 100
        
        while True:
            url = f"{GRAFANA_URL}/api/search"
            params = {
                "type": "dash-db",
                "limit": limit,
                "from": offset  # offset 방식
            }
            
            try:
                print(f"   오프셋 {offset} 조회 중...")
                response = session.get(url, params=params)
                response.raise_for_status()
                
                dashboards = response.json()
                
                if not dashboards:
                    break
                
                all_dashboards.extend(dashboards)
                print(f"   오프셋 {offset}: {len(dashboards)}개 발견 (누적: {len(all_dashboards)}개)")
                
                if len(dashboards) < limit:
                    break
                    
                offset += limit
                
                if offset > 5000:  # 무한 루프 방지
                    break
                    
                time.sleep(0.2)
                
            except Exception as e:
                print(f"❌ 오프셋 {offset} 조회 실패: {e}")
                break
    
    # 방법 3: 대용량 limit로 단일 요청 (마지막 수단)
    if len(all_dashboards) <= 30:
        print("\n🔍 방법 3: 대용량 단일 요청")
        url = f"{GRAFANA_URL}/api/search"
        params = {
            "type": "dash-db",
            "limit": 10000  # 매우 큰 값
        }
        
        try:
            response = session.get(url, params=params)
            response.raise_for_status()
            
            dashboards = response.json()
            
            if len(dashboards) > len(all_dashboards):
                all_dashboards = dashboards
                print(f"   단일 요청: {len(dashboards)}개 발견")
            
        except Exception as e:
            print(f"❌ 단일 요청 실패: {e}")
    
    print(f"✅ 총 {len(all_dashboards)}개의 대시보드를 발견했습니다.")
    return all_dashboards

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
    
    # 환경변수 확인
    if not GRAFANA_URL or not GRAFANA_TOKEN:
        print("❌ 환경변수 설정을 확인해주세요!")
        print("  .env 파일에 다음 변수들을 설정하세요:")
        print("  GRAFANA_URL=http://your-grafana-server:3000")
        print("  GRAFANA_TOKEN=your-admin-api-token")
        return
    
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
        print(f"  - GRAFANA_TOKEN: {'설정됨' if GRAFANA_TOKEN else '미설정'}")
        return
    
    # 폴더 정보 조회
    folder_map = get_folder_info(session)
    
    # 대시보드 목록 조회 (Pagination 적용)
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
    main()