
from dotenv import load_dotenv
from modules.grafana_client import GrafanaClient

def list_all_folders():
    load_dotenv()
    try:
        client = GrafanaClient()
        folders = client.get_folders()
        
        if not folders:
            print("폴더를 찾을 수 없습니다.")
            return

        print("--- 사용 가능한 모든 Grafana 폴더 ---")
        for folder in folders:
            print(f"- 제목: {folder.get('title')}, ID: {folder.get('id')}, UID: {folder.get('uid')}")
        print("-------------------------------------")

    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    list_all_folders()
