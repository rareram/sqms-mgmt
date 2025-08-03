#!/usr/bin/env python3

import json
import sys
import os

# 현재 경로를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.grafana_client import GrafanaClient
from utils.config import config

def get_first_15_panels():
    """첫 번째 15개 패널의 정보를 가져옵니다."""
    
    # 설정 로드
    client = GrafanaClient()
    
    try:
        # Node Exporter Full 대시보드 정보 가져오기
        dashboard_uid = "rYdddlPWk"
        dashboard = client.get_dashboard_by_uid(dashboard_uid)
        
        if not dashboard:
            print("대시보드를 찾을 수 없습니다.")
            return
        
        # 패널 정보 추출
        panels = dashboard.get('dashboard', {}).get('panels', [])
        
        # Row 패널 제외하고 실제 시각화 패널만 필터링
        visualization_panels = []
        for panel in panels:
            if panel.get('type') != 'row':
                visualization_panels.append(panel)
        
        # 패널을 gridPos.y로 정렬 (위에서부터 순서대로)
        visualization_panels.sort(key=lambda p: (p.get('gridPos', {}).get('y', 0), p.get('gridPos', {}).get('x', 0)))
        
        # 첫 번째 15개 패널 정보 추출
        first_15_panels = []
        for i, panel in enumerate(visualization_panels[:15]):
            panel_info = {
                'order': i + 1,
                'id': panel.get('id'),
                'title': panel.get('title'),
                'type': panel.get('type'),
                'has_description': bool(panel.get('description')),
                'current_description': panel.get('description', ''),
                'gridPos': panel.get('gridPos', {}),
                'query_count': len(panel.get('targets', [])) if panel.get('targets') else 0
            }
            first_15_panels.append(panel_info)
        
        # 결과 출력
        print("=== Node Exporter Full 대시보드 첫 번째 15개 패널 ===\n")
        
        for panel in first_15_panels:
            print(f"{panel['order']}. 패널 ID: {panel['id']}")
            print(f"   제목: {panel['title']}")
            print(f"   타입: {panel['type']}")
            print(f"   Description 존재: {'예' if panel['has_description'] else '아니오'}")
            if panel['has_description']:
                print(f"   현재 Description: \"{panel['current_description']}\"")
            else:
                print(f"   현재 Description: (없음)")
            print(f"   위치: y={panel['gridPos'].get('y', 0)}, x={panel['gridPos'].get('x', 0)}")
            print(f"   쿼리 수: {panel['query_count']}")
            print()
        
        # 영어 Description이 있는 패널들 분석
        english_descriptions = []
        for panel in first_15_panels:
            if panel['has_description'] and panel['current_description']:
                # 영어 description 여부 확인 (간단한 휴리스틱)
                desc = panel['current_description']
                if any(word in desc.lower() for word in ['cpu', 'memory', 'disk', 'network', 'system', 'load', 'usage', 'basic', 'info']):
                    english_descriptions.append({
                        'order': panel['order'],
                        'title': panel['title'],
                        'description': desc
                    })
        
        print("\n=== 영어로 된 Description을 가진 패널들 ===")
        if english_descriptions:
            for panel in english_descriptions:
                print(f"{panel['order']}. {panel['title']}: \"{panel['description']}\"")
        else:
            print("영어 Description을 가진 패널이 없습니다.")
        
        # 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"first_15_panels_analysis_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'dashboard_uid': dashboard_uid,
                'dashboard_title': dashboard.get('dashboard', {}).get('title', ''),
                'analysis_date': timestamp,
                'first_15_panels': first_15_panels,
                'english_descriptions': english_descriptions
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n분석 결과가 {filename}에 저장되었습니다.")
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    from datetime import datetime
    get_first_15_panels()