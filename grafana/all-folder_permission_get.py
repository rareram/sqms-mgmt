import requests
import pandas as pd
from typing import List, Dict, Optional
import logging
from datetime import datetime
import base64

class GrafanaFolderPermissions:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):

        if not api_key and not (username and password):
            raise ValueError("Either api_key or both username and password must be provided")
            
        self.base_url = base_url.rstrip('/')
        self.headers = {'Content-Type': 'application/json'}
        
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
        else:
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            self.headers['Authorization'] = f'Basic {credentials}'
            
        self.logger = self._setup_logging()

    # configure logging
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('grafana_permissions')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    # Make HTTP request to Grafana API with error handling
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        url = f'{self.base_url}{endpoint}'
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.logger.error("Authentication failed. Please check your credentials.")
            elif e.response.status_code == 403:
                self.logger.error("Permission denied. Please check your user permissions.")
            raise

    # Retrieve all folders from Grafana
    def get_folders(self) -> List[Dict]:
        return self._make_request('GET', '/api/folders')

    # Get permissions for a specific folder
    def get_folder_permissions(self, folder_uid: str) -> List[Dict]:
        return self._make_request('GET', f'/api/folders/{folder_uid}/permissions')

    # Get team details by ID
    def get_team_details(self, team_id: int) -> Dict:
        return self._make_request('GET', f'/api/teams/{team_id}')

    def get_nested_folders(self, parent_uid: Optional[str] = None) -> List[Dict]:
        """
        Recursively get all folders and their nested folders
        
        Args:
            parent_uid: UID of parent folder (None for root level)
        """
        url = '/api/folders'
        if parent_uid:
            url += f'?parentUid={parent_uid}'
        
        folders = self._make_request('GET', url)
        
        result = []
        for folder in folders:
            result.append(folder)
            nested = self.get_nested_folders(folder['uid'])
            result.extend(nested)
        
        return result

    # Collect permissions data for all folders and save to DataFrame
    def collect_permissions(self) -> pd.DataFrame:
        self.logger.info("Starting permission collection...")
        permissions_data = []

        try:
            folders = self.get_nested_folders()
            
            for folder in folders:
                folder_uid = folder['uid']
                folder_title = folder['title']
                
                try:
                    perms = self.get_folder_permissions(folder_uid)
                    team_perms = [p for p in perms if p['type'] == 'team']
                    
                    for perm in team_perms:
                        try:
                            # Get team name (optional)
                            team_info = self.get_team_details(perm['teamId'])
                            team_name = team_info.get('name', 'Unknown')
                        except requests.RequestException:
                            team_name = 'Unknown'
                            
                        permissions_data.append({
                            'folder_uid': folder_uid,
                            'folder_title': folder_title,
                            'team_id': perm['teamId'],
                            'team_name': team_name,
                            'permission_level': perm['permission'],
                            'inherited': perm.get('inherited', False),
                            'parent_folder': folder.get('parentUid', '')
                        })
                        
                except requests.RequestException as e:
                    self.logger.error(f"Error getting permissions for folder {folder_title}: {str(e)}")
                    continue
                
        except requests.RequestException as e:
            self.logger.error(f"Error getting folders: {str(e)}")
            raise

        return pd.DataFrame(permissions_data)

    # Collect permissions and save to CSV file
    def save_to_csv(self, output_file: Optional[str] = None) -> str:
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'grafana_folder_permissions_{timestamp}.csv'
            
        df = self.collect_permissions()
        df.to_csv(output_file, index=False, encoding='utf-8')
        self.logger.info(f"Permissions saved to {output_file}")
        return output_file

def main():
    # Configuration
    GRAFANA_URL = "http://10.250.238.71:3000"
    
    # Enterprise version with API key
    client = GrafanaFolderPermissions(
        base_url=GRAFANA_URL,
        api_key="your-api-key"
    )
    
    # OR OSS version with username/password
    client = GrafanaFolderPermissions(
        base_url=GRAFANA_URL,
        username="admin",
        password="1infosec!@#"
    )
    
    client.save_to_csv()

if __name__ == "__main__":
    main()
