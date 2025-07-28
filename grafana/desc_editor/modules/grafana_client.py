import requests
import json
import urllib3
from typing import List, Dict, Optional, Any
from utils.config import config

# SSL 경고 억제 (개발용)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GrafanaClient:
    """Grafana API 클라이언트"""
    
    def __init__(self):
        self.base_url = config.grafana_url
        self.headers = config.headers
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # SSL 검증 설정 (환경 변수로 제어)
        self.session.verify = config.ssl_verify
        
        # 타임아웃 설정
        self.session.timeout = 30
        
        # SSL 검증이 비활성화된 경우 경고 출력
        if not config.ssl_verify:
            print("⚠️  WARNING: SSL 검증이 비활성화되었습니다. 개발용으로만 사용하세요!")
    
    def test_connection(self) -> bool:
        """Grafana 연결 테스트"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            return response.status_code == 200
        except Exception as e:
            print(f"연결 테스트 실패: {e}")
            return False
    
    def get_folders(self) -> List[Dict]:
        """폴더 목록 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/folders")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"폴더 조회 실패: {e}")
            return []
    
    def get_dashboards(self, folder_id: Optional[int] = None) -> List[Dict]:
        """대시보드 목록 조회"""
        try:
            params = {'type': 'dash-db'}
            if folder_id is not None:
                params['folderIds'] = folder_id
            
            response = self.session.get(f"{self.base_url}/api/search", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"대시보드 조회 실패: {e}")
            return []
    
    def get_dashboard_by_uid(self, uid: str) -> Optional[Dict]:
        """UID로 대시보드 상세 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/dashboards/uid/{uid}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"대시보드 상세 조회 실패 (UID: {uid}): {e}")
            return None
    
    def get_dashboard_versions(self, dashboard_id: int) -> List[Dict]:
        """대시보드 버전 히스토리 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/dashboards/id/{dashboard_id}/versions")
            response.raise_for_status()
            result = response.json()
            
            # 응답이 리스트인지 확인
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and 'versions' in result:
                return result['versions']
            else:
                print(f"Unexpected response format: {result}")
                return []
        except Exception as e:
            print(f"대시보드 버전 조회 실패 (ID: {dashboard_id}): {e}")
            return []
    
    def update_dashboard(self, dashboard_data: Dict) -> bool:
        """대시보드 업데이트"""
        try:
            # 대시보드 저장을 위한 데이터 구조 준비
            save_data = {
                'dashboard': dashboard_data['dashboard'],
                'message': 'Description 업데이트',
                'overwrite': True
            }
            
            response = self.session.post(
                f"{self.base_url}/api/dashboards/db",
                json=save_data
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"대시보드 업데이트 실패: {e}")
            return False
    
    def get_panel_types_emoji(self) -> Dict[str, str]:
        """패널 타입별 이모지 매핑"""
        return {
            'graph': '📈',
            'stat': '📊',
            'table': '📋',
            'singlestat': '📊',
            'text': '📝',
            'heatmap': '🔥',
            'gauge': '⏲️',
            'bargauge': '📊',
            'piechart': '🥧',
            'logs': '📜',
            'timeseries': '📈',
            'barchart': '📊',
            'histogram': '📊',
            'news': '📰',
            'dashboard-list': '📋',
            'plugin-list': '🔌',
            'alertlist': '🚨',
            'default': '📊'
        }
    
    def format_panel_info(self, panel: Dict) -> Dict:
        """패널 정보 포맷팅"""
        panel_types = self.get_panel_types_emoji()
        panel_type = panel.get('type', 'unknown')
        
        return {
            'id': panel.get('id'),
            'title': panel.get('title', '제목 없음'),
            'type': panel_type,
            'emoji': panel_types.get(panel_type, panel_types['default']),
            'description': panel.get('description', ''),
            'gridPos': panel.get('gridPos', {}),
            'datasource': self._get_datasource_info(panel),
            'has_description': bool(panel.get('description', '').strip())
        }
    
    def _get_datasource_info(self, panel: Dict) -> str:
        """패널의 데이터소스 정보 추출"""
        try:
            datasource = panel.get('datasource')
            if isinstance(datasource, dict):
                return datasource.get('type', 'unknown')
            elif isinstance(datasource, str):
                return datasource
            else:
                # targets에서 datasource 추출 시도
                targets = panel.get('targets', [])
                if targets and isinstance(targets[0], dict):
                    ds = targets[0].get('datasource')
                    if isinstance(ds, dict):
                        return ds.get('type', 'unknown')
                return 'unknown'
        except Exception:
            return 'unknown'