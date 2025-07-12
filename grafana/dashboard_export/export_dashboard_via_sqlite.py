import json
import sqlite3
from pathlib import Path

# 설정
# 다운로드한 Grafana SQLite DB 파일 경로
SQLITE_DB_FILE = "grafana.db"
OUTPUT_DIR = "dashboards_from_db_export"

def export_dashboards_from_sqlite_db():
    """
    Grafana SQLite 데이터베이스 파일에서 직접 대시보드를 추출하여 폴더 구조를 유지합니다.
    """
    print(f"🚀 Grafana SQLite DB 파일에서 대시보드 추출을 시작합니다: {SQLITE_DB_FILE}")

    # 출력 디렉토리 생성
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    if not Path(SQLITE_DB_FILE).is_file():
        print(f"❌ 오류: SQLite DB 파일을 찾을 수 없습니다: {SQLITE_DB_FILE}")
        print("스크립트와 동일한 디렉토리에 grafana.db 파일을 위치시키거나 SQLITE_DB_FILE 변수의 경로를 수정해주세요.")
        return

    try:
        # SQLite DB에 연결
        con = sqlite3.connect(SQLITE_DB_FILE)
        con.row_factory = sqlite3.Row  # 컬럼 이름으로 접근 가능하도록 설정
        cur = con.cursor()

        # 1. 폴더 정보 조회
        cur.execute("SELECT id, title FROM dashboard WHERE is_folder = 1 OR is_folder = 'true'")
        folders = cur.fetchall()
        folder_map = {folder['id']: folder['title'] for folder in folders}
        # 기본 폴더(General) 처리
        folder_map[0] = 'General'

        # 2. 대시보드 데이터 조회
        cur.execute("SELECT data, folder_id FROM dashboard WHERE is_folder = 0 OR is_folder = 'false'")
        dashboards = cur.fetchall()

        con.close()

    except sqlite3.Error as e:
        print(f"❌ SQLite 오류 발생: {e}")
        return

    exported_count = 0
    failed_count = 0

    for dash in dashboards:
        try:
            dashboard_json_str = dash['data']
            dashboard_data = json.loads(dashboard_json_str)

            uid = dashboard_data.get("uid", "no_uid")
            title = dashboard_data.get("title", "no_title")
            folder_id = dash['folder_id']

            # 폴더 이름 찾기
            folder_title = folder_map.get(folder_id, 'Uncategorized')
            safe_folder_title = "".join(c for c in folder_title if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')

            # 파일 이름 정리
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')

            # 폴더 생성 및 파일 경로 설정
            target_folder = Path(OUTPUT_DIR) / safe_folder_title
            target_folder.mkdir(parents=True, exist_ok=True)
            filename = f"{uid}_{safe_title}.json"
            output_path = target_folder / filename

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dashboard_data, f, indent=2, ensure_ascii=False)

            print(f"✅ 추출 완료: {output_path}")
            exported_count += 1

        except json.JSONDecodeError as e:
            print(f"❌ 대시보드 데이터 파싱 실패 (원본: {dash['data'][:100]}...): {e}")
            failed_count += 1
        except Exception as e:
            print(f"❌ 대시보드 추출 중 알 수 없는 오류 발생: {e}")
            failed_count += 1

    print(f"\n🎉 대시보드 추출이 완료되었습니다!")
    print(f"   성공적으로 추출된 대시보드: {exported_count}개")
    print(f"   추출 실패한 대시보드: {failed_count}개")
    print(f"📂 결과 확인: {OUTPUT_DIR}/")


if __name__ == "__main__":
    export_dashboards_from_sqlite_db()
