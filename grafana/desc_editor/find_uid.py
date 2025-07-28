
import sys
from dotenv import load_dotenv
from modules.dashboard_manager import DashboardManager

def find_dashboard_uid(target_folder_path: list, target_dashboard_title: str):
    load_dotenv()
    try:
        dashboard_manager = DashboardManager()
        all_folders = dashboard_manager.client.get_folders()
    except Exception as e:
        print(f"❌ Grafana 연결 또는 폴더 목록 조회 실패: {e}", file=sys.stderr)
        sys.exit(1)

    # 1. 대상 폴더 ID 찾기
    target_folder_id = 0  # General 폴더로 시작
    current_folders = [f for f in all_folders if f.get('folderId') is None or f.get('folderId') == 0]
    
    # 경로의 각 단계별로 폴더를 찾아 들어감
    # 참고: Grafana API는 기본적으로 평평한 폴더 구조만 제공하므로, 
    # 폴더 제목을 기준으로 경로를 추적합니다.
    # 이 로직은 폴더 이름이 경로 내에서 고유하다고 가정합니다.
    folder_found = False
    for folder_name in target_folder_path:
        folder_found = False
        for folder in all_folders:
            if folder.get('title') == folder_name:
                target_folder_id = folder['id']
                folder_found = True
                break
        if not folder_found:
            print(f"❌ 경로에서 폴더 '{folder_name}'를 찾을 수 없습니다.", file=sys.stderr)
            sys.exit(1)

    # 2. 해당 폴더 내에서 대시보드 검색
    try:
        all_dashboards = dashboard_manager.client.get_dashboards()
        target_dashboard = None
        for dash in all_dashboards:
            # 폴더 ID와 대시보드 제목이 모두 일치하는 경우
            if dash.get('folderId') == target_folder_id and dash.get('title') == target_dashboard_title:
                target_dashboard = dash
                break
        
        if target_dashboard:
            print(target_dashboard['uid']) # 성공 시 UID만 출력
        else:
            print(f"❌ 폴더 내에서 대시보드 '{target_dashboard_title}'를 찾을 수 없습니다.", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"❌ 대시보드 검색 실패: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # 사용자로부터 입력받은 경로와 제목
    # 경로: '0.Admin' > '삭제예정' > 'IT서비스품질관리팀(테스트)'
    # Grafana API는 중첩 폴더를 직접 지원하지 않으므로, 마지막 폴더 이름으로 검색
    TARGET_FOLDER_NAME = "IT서비스품질관리팀(테스트)"
    TARGET_DASHBOARD_TITLE = "(테스트)Linux_OS_Detail"
    
    # 실제 폴더 구조를 탐색하는 로직이 필요하지만, 여기서는 평탄화된 구조에서 이름으로 검색
    # find_dashboard_uid 함수는 단일 폴더 이름만 처리하도록 수정
    load_dotenv()
    try:
        dashboard_manager = DashboardManager()
        all_folders = dashboard_manager.client.get_folders()
        all_dashboards = dashboard_manager.client.get_dashboards()

        target_folder_id = None
        for folder in all_folders:
            if folder.get('title') == TARGET_FOLDER_NAME:
                target_folder_id = folder['id']
                break

        if target_folder_id is None:
            print(f"❌ 폴더 '{TARGET_FOLDER_NAME}'를 찾을 수 없습니다.", file=sys.stderr)
            sys.exit(1)

        target_dashboard = None
        for dash in all_dashboards:
            if dash.get('folderId') == target_folder_id and dash.get('title') == TARGET_DASHBOARD_TITLE:
                target_dashboard = dash
                break
        
        if target_dashboard:
            print(target_dashboard['uid']) # 최종 UID 출력
        else:
            print(f"❌ 폴더 '{TARGET_FOLDER_NAME}' 내에서 대시보드 '{TARGET_DASHBOARD_TITLE}'를 찾을 수 없습니다.", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"❌ UID 검색 중 오류 발생: {e}", file=sys.stderr)
        sys.exit(1)
