

import sys
from dotenv import load_dotenv
from modules.dashboard_manager import DashboardManager

def list_all_dashboards_with_folders():
    """접근 가능한 모든 대시보드 목록을 폴더와 함께 출력합니다."""
    load_dotenv()
    try:
        manager = DashboardManager()
        all_dashboards = manager.client.get_dashboards()
        all_folders = {f['id']: f['title'] for f in manager.client.get_folders()}
        all_folders[0] = 'General'  # General 폴더 (ID: 0)

    except Exception as e:
        print(f"❌ Grafana 연결 또는 데이터 조회 실패: {e}", file=sys.stderr)
        sys.exit(1)

    if not all_dashboards:
        print("접근 가능한 대시보드가 하나도 없습니다.", file=sys.stderr)
        sys.exit(1)

    # 폴더 이름과 대시보드 제목으로 정렬하기 위한 리스트 생성
    sorted_list = []
    for dash in all_dashboards:
        folder_id = dash.get('folderId', 0)
        folder_name = all_folders.get(folder_id, '[알 수 없는 폴더]')
        sorted_list.append({
            'folder': folder_name,
            'title': dash.get('title', '[제목 없음]'),
            'uid': dash.get('uid', '[UID 없음]')
        })
    
    # 폴더명, 대시보드 제목 순으로 정렬
    sorted_list.sort(key=lambda x: (x['folder'], x['title']))

    print("--- 접근 가능한 모든 대시보드 목록 ---")
    current_folder = None
    for item in sorted_list:
        if item['folder'] != current_folder:
            print(f"\n📁 폴더: {item['folder']}")
            current_folder = item['folder']
        print(f"  - 제목: {item['title']}")
        print(f"    UID: {item['uid']}")
    print("---------------------------------------")

if __name__ == "__main__":
    list_all_dashboards_with_folders()

