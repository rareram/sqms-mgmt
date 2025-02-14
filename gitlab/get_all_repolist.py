import requests
import csv

GITLAB_HOST = "http://<GITLAB_HOST>" 
TOKEN = "<YOUR_ACCESS_TOKEN>" 
HEADERS = {"PRIVATE-TOKEN": TOKEN}
OUTPUT_FILE = "gitlab_repolist.csv" 

def get_all_projects():
    projects = []
    page = 1

    while True:
        url = f"{GITLAB_HOST}/api/v4/projects?per_page=100&page={page}" 
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break
        data = response.json()
        if not data:
            break  # 마지막 페이지 도달

        projects.extend(data)
        page += 1  # 다음 페이지 요청

    return projects

# 프로젝트 데이터 가져오기
projects = get_projects()

# CSV 저장
with open(OUTPUT_FILE, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["id", "group", "project", "repository", "description, "url", "created_at", "last_update"])

    for project in projects:
        writer.writerow([
            project["id"],
            project["namespace"]["name"],
            project["name"],
            project["path_with_namespace"],
            project.get("description", ""),
            project["web_url"],
            project["created_at"],
            project["last_activity_at"]
        ])

print(f"총 {len(projects)}개의 프로젝트를 {OUTPUT_FILE}에 저장 완료했습니다.")
