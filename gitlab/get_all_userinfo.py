import requests
import json
import csv
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# GitLab 서버 정보 (환경 변수에서 가져오기)
GITLAB_HOST = os.getenv("GITLAB_HOST")
TOKEN = os.getenv("GITLAB_TOKEN")
HEADERS = {"PRIVATE-TOKEN": TOKEN}

# 저장할 파일명
JSON_FILE = "gitlab_allusers.json"
CSV_FILE = "gitlab_allusers.csv"

def get_all_users():
    """GitLab 전체 유저 목록 가져오기"""
    users = []
    page = 1
    per_page = 100  # 최대 100명씩 가져오기

    while True:
        url = f"{GITLAB_HOST}/api/v4/users"
        params = {"per_page": per_page, "page": page}
        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code != 200:
            print(f"유저 조회 실패: {response.status_code}")
            break

        data = response.json()
        if not data:
            break  # 더 이상 데이터 없음

        users.extend(data)
        page += 1

    return users

def get_user_details(user_id):
    """각 유저의 상세 정보 가져오기"""
    url = f"{GITLAB_HOST}/api/v4/users/{user_id}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"유저 ID {user_id} 정보 조회 실패")
        return None

    return response.json()

# 전체 유저 리스트 가져오기
users = get_all_users()
user_data = []

for user in users:
    user_id = user.get("id")
    user_details = get_user_details(user_id)
    
    if user_details:
        user_data.append({
            "id": user_details.get("id"),
            "username": user_details.get("username"),
            "name": user_details.get("name"),
            "email": user_details.get("email", ""),
            "state": user_details.get("state"),
            "created_at": user_details.get("created_at"),
            "is_admin": user_details.get("is_admin"),
            "last_sign_in_at": user_details.get("last_sign_in_at", ""),
            "two_factor_enabled": user_details.get("two_factor_enabled"),
            "external": user_details.get("external"),
            "bio": user_details.get("bio", "").replace("\n", " "),
            "organization": user_details.get("organization", ""),
        })

# JSON 파일 저장
with open(JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(user_data, f, ensure_ascii=False, indent=4)

# CSV 파일 저장
with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=user_data[0].keys())
    writer.writeheader()
    writer.writerows(user_data)

print(f"✅ JSON 저장 완료: {JSON_FILE}")
print(f"✅ CSV 저장 완료: {CSV_FILE}")

