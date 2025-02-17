import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from dotenv import load_dotenv
import os

# .env 파일에서 환경변수 로드
load_dotenv()

# Grafana URL 및 사용자 인증정보
GRAFANA_URL = os.getenv("GRAFANA_190_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# API 엔드포인트
endpoint = "/api/teams/search"
url = f"{GRAFANA_URL}{endpoint}"

# API Request
response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))

if response.status_code == 200:
    teams_data = response.json()
    teams = teams_data.get("teams", [])

    data = []
    for team in teams:
        data.append({
            "id": team.get("id", ""),
            "team": team.get("name", ""),
            "email": team.get("email", ""),
            "avatarUrl": team.get("avatarUrl", ""),
            "new_team": "",
            "new_email": ""
        })
    
    df = pd.DataFrame(data)

    # CSV 저장
    output_file = "grafana_teamlist.csv"
    df.to_csv(output_file, index=False)

    print(f"CSV file '{output_file}' created successfully!")

else:
    print(f"Error: {response.status_code}, {response.text}")