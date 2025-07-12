from typing import List, Dict, Optional, Tuple
from modules.grafana_client import GrafanaClient
from datetime import datetime
import streamlit as st

class DashboardManager:
    """대시보드 관리 클래스"""
    
    def __init__(self):
        self.client = GrafanaClient()
    
    def get_folder_structure(self) -> Dict:
        """폴더 구조와 대시보드 정보 조회"""
        folders = self.client.get_folders()
        
        # 기본 폴더 (General) 추가
        folder_structure = {
            'General': {
                'id': 0,
                'title': 'General',
                'dashboards': []
            }
        }
        
        # 폴더별 구조 생성
        for folder in folders:
            folder_structure[folder['title']] = {
                'id': folder['id'],
                'title': folder['title'],
                'dashboards': []
            }
        
        # 전체 대시보드 조회
        all_dashboards = self.client.get_dashboards()
        
        # 대시보드를 폴더별로 분류
        for dashboard in all_dashboards:
            folder_id = dashboard.get('folderId', 0)
            
            # 해당 폴더 찾기
            target_folder = None
            for folder_name, folder_info in folder_structure.items():
                if folder_info['id'] == folder_id:
                    target_folder = folder_name
                    break
            
            # 폴더를 찾으면 대시보드 추가
            if target_folder:
                folder_structure[target_folder]['dashboards'].append(dashboard)
        
        return folder_structure
    
    def get_dashboard_details(self, dashboard_uid: str) -> Optional[Dict]:
        """대시보드 상세 정보 조회"""
        return self.client.get_dashboard_by_uid(dashboard_uid)
    
    def get_dashboard_panels(self, dashboard_uid: str) -> List[Dict]:
        """대시보드 패널 목록 조회"""
        dashboard_data = self.get_dashboard_details(dashboard_uid)
        if not dashboard_data:
            return []
        
        panels = dashboard_data.get('dashboard', {}).get('panels', [])
        formatted_panels = []
        
        for panel in panels:
            # 행(row) 패널은 제외
            if panel.get('type') == 'row':
                continue
                
            formatted_panel = self.client.format_panel_info(panel)
            formatted_panels.append(formatted_panel)
        
        return formatted_panels
    def get_dashboard_versions(self, dashboard_id: int) -> List[Dict]:
        """대시보드 버전 히스토리 조회"""
        try:
            versions = self.client.get_dashboard_versions(dashboard_id)
            
            # versions가 리스트가 아닌 경우 처리
            if not isinstance(versions, list):
                print(f"Unexpected versions format: {type(versions)}")
                return []
            
            # 최신 5개 버전만 반환
            formatted_versions = []
            for version in versions[:5]:
                formatted_version = {
                    'version': version.get('version', 'unknown'),
                    'created': self._format_datetime(version.get('created', '')),
                    'created_by': version.get('createdBy', 'unknown'),
                    'message': version.get('message', '변경사항 없음')
                }
                formatted_versions.append(formatted_version)
            
            return formatted_versions
        except Exception as e:
            print(f"버전 히스토리 조회 실패: {e}")
            return []
    
    def update_panel_description(self, dashboard_uid: str, panel_id: int, description: str) -> bool:
        """패널 Description 업데이트"""
        dashboard_data = self.get_dashboard_details(dashboard_uid)
        if not dashboard_data:
            return False
        
        # 패널 찾기 및 description 업데이트
        panels = dashboard_data['dashboard']['panels']
        panel_found = False
        
        for panel in panels:
            if panel.get('id') == panel_id:
                panel['description'] = description
                panel_found = True
                break
        
        if not panel_found:
            return False
        
        # 대시보드 업데이트
        return self.client.update_dashboard(dashboard_data)
    
    def _format_datetime(self, datetime_str: str) -> str:
        """날짜시간 포맷팅"""
        try:
            if not datetime_str:
                return 'N/A'
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return datetime_str if datetime_str else 'N/A'
    def get_dashboard_summary(self, dashboard_uid: str) -> Dict:
        """대시보드 요약 정보"""
        try:
            dashboard_data = self.get_dashboard_details(dashboard_uid)
            if not dashboard_data:
                return {}
            
            dashboard = dashboard_data['dashboard']
            panels = self.get_dashboard_panels(dashboard_uid)
            
            # 패널 통계
            total_panels = len(panels)
            panels_with_description = sum(1 for p in panels if p['has_description'])
            panels_without_description = total_panels - panels_with_description
            
            # 패널 타입별 통계
            panel_types = {}
            for panel in panels:
                panel_type = panel['type']
                panel_types[panel_type] = panel_types.get(panel_type, 0) + 1
            
            return {
                'title': dashboard.get('title', '제목 없음'),
                'uid': dashboard.get('uid', 'unknown'),
                'id': dashboard.get('id', 0),
                'tags': dashboard.get('tags', []),
                'created': self._format_datetime(dashboard.get('created', '')),
                'updated': self._format_datetime(dashboard.get('updated', '')),
                'total_panels': total_panels,
                'panels_with_description': panels_with_description,
                'panels_without_description': panels_without_description,
                'panel_types': panel_types,
                'description_coverage': round((panels_with_description / total_panels * 100) if total_panels > 0 else 0, 1)
            }
        except Exception as e:
            print(f"대시보드 요약 정보 조회 실패: {e}")
            return {}
    
    def search_panels(self, dashboard_uid: str, search_term: str = '', 
                     filter_type: str = 'all', filter_description: str = 'all') -> List[Dict]:
        """패널 검색 및 필터링"""
        try:
            panels = self.get_dashboard_panels(dashboard_uid)
            
            filtered_panels = []
            for panel in panels:
                # 검색어 필터
                if search_term:
                    if search_term.lower() not in panel['title'].lower():
                        continue
                
                # 패널 타입 필터
                if filter_type != 'all' and panel['type'] != filter_type:
                    continue
                
                # Description 유무 필터
                if filter_description == 'with_description' and not panel['has_description']:
                    continue
                elif filter_description == 'without_description' and panel['has_description']:
                    continue
                
                filtered_panels.append(panel)
            
            return filtered_panels
        except Exception as e:
            print(f"패널 검색 실패: {e}")
            return []
