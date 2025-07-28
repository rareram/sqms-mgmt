
import sys
from dotenv import load_dotenv
from modules.dashboard_manager import DashboardManager

def find_dashboard_by_title(target_title: str):
    """대시보드 제목으로 검색하여 UID와 폴더 정보를 반환합니다."""
    load_dotenv()
    try:
        manager = DashboardManager()
        all_dashboards = manager.client.get_dashboards()
        all_folders = {f['id']: f['title'] for f in manager.client.get_folders()}
        all_folders[0] = 'General' # General 폴더 추가

    except Exception as e:
        print(f"❌ Grafana 연결 또는 데이터 조회 실패: {e}", file=sys.stderr)
        sys.exit(1)

    found_dashboards = []
    for dash in all_dashboards:
        if dash.get('title') == target_title:
            folder_id = dash.get('folderId', 0)
            folder_name = all_folders.get(folder_id, '알 수 없는 폴더')
            found_dashboards.append({
                'uid': dash['uid'],
                'title': dash['title'],
                'folder_name': folder_name
            })

    if not found_dashboards:
        print(f"❌ 제목이 '{target_title}'인 대시보드를 찾을 수 없습니다.", file=sys.stderr)
        sys.exit(1)
    
    if len(found_dashboards) > 1:
        print(f"⚠️ 제목이 '{target_title}'인 대시보드가 여러 개 있습니다. UID를 직접 지정해주세요:", file=sys.stderr)
        for dash in found_dashboards:
            print(f"  - UID: {dash['uid']}, 폴더: {dash['folder_name']}", file=sys.stderr)
        sys.exit(1)

    # 정확히 하나만 찾은 경우, UID를 출력
    print(found_dashboards[0]['uid'])

if __name__ == "__main__":
    TARGET_DASHBOARD_TITLE = "(테스트)_Linux_OS_Detail"
    find_dashboard_by_title(TARGET_DASHBOARD_TITLE)
