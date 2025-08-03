#!/usr/bin/env python3
"""
Node Exporter Full (1860) 대시보드의 모든 패널 정보를 상세 분석하는 스크립트
"""

import requests
import json
import urllib3
from typing import Dict, List, Any, Optional
from datetime import datetime
from utils.config import config

# SSL 경고 억제
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NodeExporterAnalyzer:
    """Node Exporter Full 대시보드 분석기"""
    
    def __init__(self):
        self.base_url = config.grafana_url
        self.headers = config.headers
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.verify = config.ssl_verify
        self.session.timeout = 30
        
        # 대시보드 UID
        self.dashboard_uid = "rYdddlPWk"
        
        if not config.ssl_verify:
            print("⚠️  WARNING: SSL 검증이 비활성화되었습니다.")
    
    def get_dashboard_detail(self) -> Optional[Dict]:
        """대시보드 상세 정보 조회"""
        try:
            url = f"{self.base_url}/api/dashboards/uid/{self.dashboard_uid}"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"대시보드 조회 실패: {e}")
            return None
    
    def extract_panel_info(self, panel: Dict) -> Dict:
        """패널 정보 상세 추출"""
        panel_info = {
            'id': panel.get('id'),
            'title': panel.get('title', '제목 없음'),
            'type': panel.get('type', 'unknown'),
            'description': panel.get('description', ''),
            'has_description': bool(panel.get('description', '').strip()),
            'gridPos': panel.get('gridPos', {}),
            'datasource': self._extract_datasource_info(panel),
            'targets': self._extract_targets_info(panel),
            'fieldConfig': self._extract_field_config(panel),
            'thresholds': self._extract_thresholds(panel),
            'alert': self._extract_alert_info(panel),
            'options': panel.get('options', {}),
            'transformations': panel.get('transformations', []),
            'transparent': panel.get('transparent', False),
            'links': panel.get('links', [])
        }
        
        return panel_info
    
    def _extract_datasource_info(self, panel: Dict) -> Dict:
        """데이터소스 정보 추출"""
        datasource_info = {
            'type': 'unknown',
            'uid': '',
            'name': ''
        }
        
        try:
            # 패널 레벨의 datasource
            datasource = panel.get('datasource')
            if isinstance(datasource, dict):
                datasource_info.update({
                    'type': datasource.get('type', 'unknown'),
                    'uid': datasource.get('uid', ''),
                    'name': datasource.get('name', '')
                })
            elif isinstance(datasource, str):
                datasource_info['name'] = datasource
            
            # targets에서 datasource 정보 보완
            targets = panel.get('targets', [])
            if targets and isinstance(targets[0], dict):
                target_ds = targets[0].get('datasource')
                if isinstance(target_ds, dict):
                    if not datasource_info['type'] or datasource_info['type'] == 'unknown':
                        datasource_info.update({
                            'type': target_ds.get('type', 'unknown'),
                            'uid': target_ds.get('uid', ''),
                            'name': target_ds.get('name', '')
                        })
        except Exception as e:
            print(f"데이터소스 정보 추출 오류: {e}")
        
        return datasource_info
    
    def _extract_targets_info(self, panel: Dict) -> List[Dict]:
        """Query/Expression 정보 추출"""
        targets = panel.get('targets', [])
        targets_info = []
        
        for target in targets:
            if isinstance(target, dict):
                target_info = {
                    'expr': target.get('expr', ''),
                    'legendFormat': target.get('legendFormat', ''),
                    'refId': target.get('refId', ''),
                    'interval': target.get('interval', ''),
                    'format': target.get('format', ''),
                    'instant': target.get('instant', False),
                    'hide': target.get('hide', False),
                    'exemplar': target.get('exemplar', False),
                    'datasource': target.get('datasource', {})
                }
                targets_info.append(target_info)
        
        return targets_info
    
    def _extract_field_config(self, panel: Dict) -> Dict:
        """Field Config 정보 추출"""
        field_config = panel.get('fieldConfig', {})
        
        return {
            'defaults': field_config.get('defaults', {}),
            'overrides': field_config.get('overrides', [])
        }
    
    def _extract_thresholds(self, panel: Dict) -> Dict:
        """Threshold 설정 추출"""
        try:
            field_config = panel.get('fieldConfig', {})
            defaults = field_config.get('defaults', {})
            thresholds = defaults.get('thresholds', {})
            
            threshold_info = {
                'mode': thresholds.get('mode', ''),
                'steps': thresholds.get('steps', [])
            }
            
            # Custom threshold 설정 확인
            custom = defaults.get('custom', {})
            if 'thresholdsStyle' in custom:
                threshold_info['thresholdsStyle'] = custom['thresholdsStyle']
            
            return threshold_info
        except Exception:
            return {}
    
    def _extract_alert_info(self, panel: Dict) -> Dict:
        """Alert 설정 정보 추출"""
        alert_info = {
            'has_alert': False,
            'alert_config': {}
        }
        
        try:
            alert = panel.get('alert')
            if alert:
                alert_info['has_alert'] = True
                alert_info['alert_config'] = {
                    'name': alert.get('name', ''),
                    'message': alert.get('message', ''),
                    'frequency': alert.get('frequency', ''),
                    'conditions': alert.get('conditions', []),
                    'executionErrorState': alert.get('executionErrorState', ''),
                    'noDataState': alert.get('noDataState', ''),
                    'for': alert.get('for', '')
                }
        except Exception:
            pass
        
        return alert_info
    
    def get_all_panels(self, dashboard_data: Dict) -> List[Dict]:
        """대시보드의 모든 패널 추출 (중첩 패널 포함)"""
        panels = []
        
        def extract_panels_recursive(panel_list: List[Dict], parent_id: Optional[int] = None):
            for panel in panel_list:
                if panel.get('type') == 'row':
                    # Row 패널의 경우 collapsed 상태 확인
                    panels.append(self.extract_panel_info(panel))
                    
                    # Row 내부의 패널들 처리
                    if panel.get('collapsed', False) and 'panels' in panel:
                        extract_panels_recursive(panel['panels'], panel.get('id'))
                elif panel.get('type') in ['graph', 'stat', 'table', 'singlestat', 'text', 
                                         'heatmap', 'gauge', 'bargauge', 'timeseries', 
                                         'barchart', 'histogram', 'piechart', 'logs']:
                    panels.append(self.extract_panel_info(panel))
                
                # 중첩된 패널들 처리
                if 'panels' in panel and panel.get('type') != 'row':
                    extract_panels_recursive(panel['panels'], panel.get('id'))
        
        dashboard_panels = dashboard_data.get('dashboard', {}).get('panels', [])
        extract_panels_recursive(dashboard_panels)
        
        return panels
    
    def analyze_dashboard(self) -> Dict:
        """대시보드 전체 분석"""
        print(f"Node Exporter Full 대시보드 (UID: {self.dashboard_uid}) 분석 시작...")
        
        # 대시보드 데이터 조회
        dashboard_data = self.get_dashboard_detail()
        if not dashboard_data:
            return {}
        
        dashboard = dashboard_data.get('dashboard', {})
        
        # 기본 정보
        analysis_result = {
            'dashboard_info': {
                'uid': dashboard.get('uid'),
                'title': dashboard.get('title'),
                'id': dashboard.get('id'),
                'version': dashboard.get('version'),
                'tags': dashboard.get('tags', []),
                'description': dashboard.get('description', ''),
                'created': dashboard.get('created'),
                'updated': dashboard.get('updated'),
                'createdBy': dashboard.get('createdBy', {}),
                'updatedBy': dashboard.get('updatedBy', {}),
                'time': dashboard.get('time', {}),
                'timepicker': dashboard.get('timepicker', {}),
                'timezone': dashboard.get('timezone', ''),
                'refresh': dashboard.get('refresh', ''),
                'schemaVersion': dashboard.get('schemaVersion'),
                'style': dashboard.get('style', ''),
                'editable': dashboard.get('editable', True)
            },
            'analysis_timestamp': datetime.now().isoformat(),
            'panels': [],
            'statistics': {
                'total_panels': 0,
                'panels_with_description': 0,
                'panels_without_description': 0,
                'panel_types': {},
                'datasource_types': {},
                'panels_with_alerts': 0,
                'panels_with_thresholds': 0
            }
        }
        
        # 패널 분석
        panels = self.get_all_panels(dashboard_data)
        analysis_result['panels'] = panels
        
        # 통계 계산
        stats = analysis_result['statistics']
        stats['total_panels'] = len(panels)
        
        for panel in panels:
            # Description 통계
            if panel['has_description']:
                stats['panels_with_description'] += 1
            else:
                stats['panels_without_description'] += 1
            
            # 패널 타입 통계
            panel_type = panel['type']
            stats['panel_types'][panel_type] = stats['panel_types'].get(panel_type, 0) + 1
            
            # 데이터소스 타입 통계
            ds_type = panel['datasource']['type']
            stats['datasource_types'][ds_type] = stats['datasource_types'].get(ds_type, 0) + 1
            
            # Alert 통계
            if panel['alert']['has_alert']:
                stats['panels_with_alerts'] += 1
            
            # Threshold 통계
            if panel['thresholds'].get('steps'):
                stats['panels_with_thresholds'] += 1
        
        print(f"✅ 분석 완료: {stats['total_panels']}개 패널 분석됨")
        print(f"   - Description 있음: {stats['panels_with_description']}개")
        print(f"   - Description 없음: {stats['panels_without_description']}개")
        print(f"   - Alert 설정: {stats['panels_with_alerts']}개")
        print(f"   - Threshold 설정: {stats['panels_with_thresholds']}개")
        
        return analysis_result
    
    def save_analysis_result(self, analysis_result: Dict, filename: str = None) -> str:
        """분석 결과를 JSON 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"node_exporter_full_analysis_{timestamp}.json"
        
        file_path = f"/Users/paul/sandbox/sqms-mgmt/grafana/desc_editor/{filename}"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 분석 결과 저장됨: {file_path}")
            return file_path
        except Exception as e:
            print(f"❌ 파일 저장 실패: {e}")
            return ""

def main():
    """메인 실행 함수"""
    try:
        # 설정 검증
        if not config.validate():
            return
        
        # 분석기 초기화
        analyzer = NodeExporterAnalyzer()
        
        # 분석 실행
        result = analyzer.analyze_dashboard()
        if not result:
            print("❌ 분석 실패")
            return
        
        # 결과 저장
        saved_file = analyzer.save_analysis_result(result)
        
        if saved_file:
            print(f"\n📊 Node Exporter Full 대시보드 분석 완료!")
            print(f"📁 저장된 파일: {saved_file}")
            
            # 간단한 요약 출력
            stats = result['statistics']
            print(f"\n📈 분석 요약:")
            print(f"   총 패널 수: {stats['total_panels']}")
            print(f"   Description 있음: {stats['panels_with_description']}")
            print(f"   Description 없음: {stats['panels_without_description']}")
            print(f"   패널 타입: {list(stats['panel_types'].keys())}")
            print(f"   데이터소스: {list(stats['datasource_types'].keys())}")
    
    except Exception as e:
        print(f"❌ 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()