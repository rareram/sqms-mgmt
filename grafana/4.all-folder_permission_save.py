import requests
import pandas as pd
from typing import List, Dict, Optional
import logging
from datetime import datetime
import base64
import urllib.parse
from dotenv import load_dotenv
import os

# .env 파일에서 환경변수 로드
load_dotenv()

class GrafanaFolderPermissions:
    def __init__(
            self,
            base_url: str,
            api_key: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None,
            verify_ssl: bool = True
    ):
        
        # Initialize Grafana API client with either API key (Enterprise) or username/password (Open Source)
        if not api_key and not (username and password):
            raise ValueError("Either API key or username/password must be provided")
        
        self.base_url = base_url.rstrip('/')
        self.verify_ssl = verify_ssl
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
        else:
            self.session.auth = (username, password)
        
        self.logger = self._setup_logging()

        # Verify connection
        self.verify_connection()
    
    def verify_connection(self):
        # Test the connection and authentication
        try:
            response = self.session.get(f"{self.base_url}/api/org", verify=self.verify_ssl)
            response.raise_for_status()
            org_info = response.json()
            self.logger.info(f"Successfully connected to Grafana organization: {org_info.get('name', 'Unknown')}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to connect to Grafana: {str(e)}")
            raise
    
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('grafana_permissions')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        url = f'{self.base_url}{endpoint}'
        kwargs['verify'] = self.verify_ssl
    
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.logger.error("Authentication failed. Please check your credentials.")
            elif e.response.status_code == 403:
                self.logger.error("Permission denied. Please check your permissions.")
            raise
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise

    def get_folders(self) -> List[Dict]:
        return self._make_request("GET", "/api/folders")
    
    def get_folder_permission(self, folder_uid: str) -> List[Dict]:
        return self._make_request("GET", f"/api/folders/{folder_uid}/permissions")
    
    def get_team_detaild(self, team_id: int) -> Dict:
        return self._make_request("GET", f"/api/teams/{team_id}")
    
    def get_nested_folders(self, parent_uid: Optional[str] = None) -> List[Dict]:
        url = '/api/folders'
        if parent_uid:
            url += f'?parentUid={parent_uid}'
        
        folders = self._make_request("GET", url)

        result = []
        for folder in folders:
            result.append(folder)
            try:
                nested = self.get_nested_folders(folder['uid'])
                result.extend(nested)
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Failed to get nested folders for {folder['title']}: {str(e)}")
        
        return result
    
    def _is_team_permission(self, permission: Dict) -> bool:
        return (
            'teamId' in permission or
            permission.get('permission', '').startswith('Team ') or
            permission.get('role', '').startswith('Team ')
        )
    
    def collect_permissions(self) -> pd.DataFrame:
        self.logger.info("Starting permission collection...")
        permissions_data = []

        try:
            folders = self.get_folders()

            for folder in folders:
                folder_uid = folder['uid']
                folder_title = folder['title']

                try:
                    perms = self.get_folder_permission(folder_uid)
                    team_perm = [p for p in perms if self._is_team_permission(p)]

                    for perm in team_perm:
                        team_id = perm.get('teamId')
                        if team_id:
                            try:
                                team_info = self.get_team_detaild(team_id)
                                team_name = team_info.get('name', 'Unknown')
                            except requests.RequestException:
                                team_name = f'Team {team_id}'
                            
                            permissions_data.append({
                                'folder_uid': folder_uid,
                                'folder_title': folder_title,
                                'team_id': team_id,
                                'team_name': team_name,
                                'permission_level': perm.get('permission', 'Unknown'),
                                'inherit': perm.get('inherit', False),
                                'parent_folder': folder.get('parentUid', '')
                            })
                except requests.RequestException as e:
                    self.logger.error(f"Error getting permissions for folder {folder_title}: {str(e)}")
                    continue
            
        except requests.RequestException as e:
            self.logger.error(f"Error getting folders: {str(e)}")
            raise

        return pd.DataFrame(permissions_data)
    
    def save_to_csv(self, output_file: Optional[str] = None) -> str:
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"grafana_folder_permissions_{timestamp}.csv"
        
        df = self.collect_permissions()
        df.to_csv(output_file, index=False, encoding='utf-8')
        self.logger.info(f"Permissions saved to {output_file}")
        return output_file

def main():
    # Grafana URL 및 사용자 인증정보
    GRAFANA_URL = os.getenv("GRAFANA_190_URL")
    USERNAME = os.getenv("USERNAME")
    PASSWORD = os.getenv("PASSWORD")

    try:
        client = GrafanaFolderPermissions(
            base_url=GRAFANA_URL,
            username=USERNAME,
            password=PASSWORD,
            verify_ssl=False
        )

        client.save_to_csv()
    
    except requests.exception.RequestException as e:
        print(f"Failed to connect to Grafana: {str(e)}")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()