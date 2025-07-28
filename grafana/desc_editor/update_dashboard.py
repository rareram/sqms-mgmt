

import os
import sys
from dotenv import load_dotenv
from modules.dashboard_manager import DashboardManager
from modules.ai_generator import AIGenerator

def update_single_dashboard(dashboard_uid: str):
    """
    지정된 단일 대시보드의 모든 패널에 대해 설명을 자동으로 생성하고 업데이트합니다.
    """
    # .env 파일에서 환경 변수 로드
    load_dotenv()
    if not os.getenv("GRAFANA_URL") or not os.getenv("GRAFANA_TOKEN"):
        print("오류: .env 파일에 GRAFANA_URL와 GRAFANA_TOKEN이 설정되어야 합니다.")
        sys.exit(1)

    # 모듈 초기화
    try:
        dashboard_manager = DashboardManager()
        ai_generator = AIGenerator()
        print("✅ Grafana 서버에 성공적으로 연결되었습니다.")
    except Exception as e:
        print(f"❌ Grafana 연결 실패: {e}")
        sys.exit(1)

    # 지정된 대시보드 처리
    print(f"\n--- [ UID: {dashboard_uid} ] 대시보드 처리 시작 ---")

    try:
        dashboard_data = dashboard_manager.get_dashboard_details(dashboard_uid)
        if not dashboard_data:
            print(f"  └ ❌ UID '{dashboard_uid}'에 해당하는 대시보드를 찾을 수 없습니다.")
            sys.exit(1)

        dashboard_title = dashboard_data.get('dashboard', {}).get('title', 'N/A')
        print(f"  └ 📂 대시보드 '{dashboard_title}'를 찾았습니다.")

        panels = dashboard_data.get('dashboard', {}).get('panels', [])
        eligible_panels = [p for p in panels if p.get('type') not in ['text', 'row']]
        
        if not eligible_panels:
            print("  └ ℹ️ 업데이트할 패널이 없습니다.")
            sys.exit(0)

        print(f"  └ 📊 {len(eligible_panels)}개의 패널을 분석합니다.")
        
        panels_updated_count = 0
        for panel in eligible_panels:
            panel_id = panel.get('id')
            panel_title = panel.get('title', f"ID-{panel_id}")
            
            # AI로 설명 생성
            new_desc = ai_generator.generate_description(panel)
            
            # 기존 설명과 다를 경우에만 업데이트 목록에 추가
            if new_desc and panel.get('description') != new_desc:
                panel['description'] = new_desc
                panels_updated_count += 1
                print(f"    - ✅ 패널 '{panel_title}' 설명 생성/업데이트 완료")

        # 변경사항이 있을 경우에만 대시보드 저장
        if panels_updated_count > 0:
            print(f"\n  └ 💾 {panels_updated_count}개 패널의 변경사항을 Grafana에 저장합니다...")
            
            update_payload = {
                'dashboard': dashboard_data['dashboard'],
                'message': f"AI를 통해 {panels_updated_count}개 패널 설명 자동 업데이트",
                'folderId': dashboard_data.get('dashboard', {}).get('folderId', 0)
            }
            success = dashboard_manager.client.update_dashboard(update_payload)
            
            if success:
                print("  └ ✅ 대시보드 저장 성공!")
            else:
                print("  └ ❌ 대시보드 저장 실패.")
        else:
            print("\n  └ ℹ️ 변경된 내용이 없어 대시보드를 업데이트하지 않았습니다.")

    except Exception as e:
        print(f"  └ ❌ 대시보드 처리 중 오류 발생: {e}")
        sys.exit(1)

    print("\n\n🎉 작업이 완료되었습니다.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python update_dashboard.py <DASHBOARD_UID>")
        sys.exit(1)
    
    target_dashboard_uid = sys.argv[1]
    update_single_dashboard(target_dashboard_uid)

