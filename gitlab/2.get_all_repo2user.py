import requests
import json
import csv
import os
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

GITLAB_HOST = os.getenv("GITLAB_HOST") 
TOKEN = os.getenv("GITLAB_TOKEN") 
HEADERS = {"PRIVATE-TOKEN": TOKEN}
JSON_FILE = "gitlab_all_memberlist.json" 
CSV_FILE = "gitlab_all_memberlist.csv" 

def get_project_members(project_id):
    members = []
    page = 1
    per_page = 100  # GitLab API 최대 100개씩 조회 가능

    while True:
        url = f"{GITLAB_HOST}/api/v4/projects/{project_id}/members/all" 
        params = {"per_page": per_page, "page": page}
        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code == 404:
            print(f"프로젝트 id={project_id}는 삭제됨.")
            return None
        if response.status_code != 200:
            print(f"프로젝트 id={project_id} 조회 실패: {response.status_code}")
            return None

        data = response.json()
        if not data:
            break

        members.extend(data)
        page += 1

    return members

def get_project_owner(members):
    for member in members:
        if member.get("access_level") == 50:
            return member.get("name", "")
    return "" 

def get_commit_authors(project_id):
    url = f"{GITLAB_HOST}/api/v4/projects/{project_id}/repository/commits" 
    params = {"per_page": 20}  # 최근 20개 커밋 조회
    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code != 200:
        print(f"프로젝트 id={project_id} 커밋 조회 실패: {response.status_code}")
        return [], []  # 커밋 내역이 없으면 빈 리스트 반환

    commits = response.json()
    if not commits:
        return [], []

    # (이름, 날짜) 튜플로 저장 후 중복 제거
    unique_authors = list({(commit.get("author_name", ""), commit.get("created_at", "")) for commit in commits})

    # (이름, 날짜) 튜플을 분리하여 리스트로 변환
    authors, dates = zip(*unique_authors) if unique_authors else ([], [])

    return list(authors)[:20], list(dates)[:20]  # 최대 20개 유지

all_members = {}
csv_data = []

for project_id in range(1, 1330):
    members = get_project_members(project_id)

    if members is not None:
        # 프로젝트 생성자의 이름(오너)을 가져옴
        owner = get_project_owner(members)

        # 중복 제거 후 메인테이너 및 디벨로퍼 이름 수집
        maintainer_names = list(set(m.get("name", "") for m in members if m.get("access_level") == 40))[:25]
        developer_names = list(set(m.get("name", "") for m in members if m.get("access_level") == 30))[:20]

        # 커밋자 정보 가져오기
        commit_authors_names, commit_authors_dates = get_commit_authors(project_id)

        # 리스트 크기가 부족할 경우 빈 문자열로 채움
        maintainer_names += [""] * (25 - len(maintainer_names))
        developer_names += [""] * (20 - len(developer_names))
        commit_authors_names += [""] * (20 - len(commit_authors_names))
        commit_authors_dates += [""] * (20 - len(commit_authors_dates))

        # CSV 데이터에 모든 정보 추가
        csv_data.append(
            [project_id, owner] + maintainer_names + developer_names + commit_authors_names + commit_authors_dates
        )

# JSON 파일 저장
with open(JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(all_members, f, ensure_ascii=False, indent=4)

# CSV 파일 저장
with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(
        ["project_id", "owner"] + 
        ["maintainer" + str(i) for i in range(1, 26)] + 
        ["developer" + str(i) for i in range(1, 21)] + 
        ["commit_user" + str(i) for i in range(1, 21)] + 
        ["commit_date" + str(i) for i in range(1, 21)]
    )
    for row in csv_data:
        writer.writerow(row)

print(f"- JSON 저장 완료: {JSON_FILE}")
print(f"- CSV 저장 완료: {CSV_FILE}")
