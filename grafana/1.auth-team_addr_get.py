import requests
from requests.auth import HTTPBasicAuth
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
    print("API Response:", response.json())
else:
    print(f"Error: {response.status_code}, {response.text}")
