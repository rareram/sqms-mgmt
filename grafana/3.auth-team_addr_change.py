import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from dotenv import load_dotenv
import os

# .env 파일에서 환경변수 로드
load_dotenv()

# Grafana API 정보
GRAFANA_URL = os.getenv("GRAFANA_190_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# CSV 파일명
input_file = "grafana_teamlist.csv"
df = pd.read_csv(input_file)

updated_data = []

# update data
for index, row in df.iterrows():
    team_name = row['team']
    new_team = row['new_team']
    new_email = row['new_email']

    if new_team or new_email:
        endpoint = f"/api/teams/{row['id']}"
        url = f"{GRAFANA_URL}{endpoint}"

        update_data = {}

        # Update data
        for index, row in df.iterrows():
            team_name = row['team']
            new_team = row['new_team'] if pd.notna(row['new_team']) else None
            new_email = row['new_email'] if pd.notna(row['new_email']) else None

            if new_team or new_email:
                endpoint = f"/api/teams/{row['id']}"
                url = f"{GRAFANA_URL}{endpoint}"

                update_data = {}
                if new_team:
                    update_data['name'] = new_team
                if new_email:
                    update_data['email'] = new_email

                # Ensure there are no NaN values when sending the request
                if update_data:
                    response = requests.put(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), json=update_data)

                    if response.status_code == 200:
                        print(f"Team '{team_name}' updated successfully!")
                    else:
                        print(f"Failed to update team: '{team_name}': {response.status_code}, {response.text}")
                else:
                    print(f"No valid data to update for team: '{team_name}'.")
            else:
                print(f"No update needed for team '{team_name}'.")
            
            updated_data.append({
                "id": row['id'],
                "team": team_name,
                "email": row['email'],
                "avatarUrl": row['avatarUrl'],
                "new_team": "",   # 비워두기
                "new_email": ""   # 비워두기
            })
        
        # Save the new DataFrame
        updated_df = pd.DataFrame(updated_data)

        # CSV overwrite
        updated_df.to_csv(input_file, index=False)
        print(f"CSV file '{input_file}' updated successfully!")