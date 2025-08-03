#!/usr/bin/env python3
"""
Grafana 대시보드 패널 Description 업데이트 스크립트
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple

# 프로젝트 루트를 Python 경로에 추가
sys.path.append('.')

from modules.grafana_client import GrafanaClient

def load_improved_descriptions() -> Dict[str, str]:
    """개선된 한국어 descriptions 로드"""
    try:
        with open('improved_korean_descriptions.json', 'r', encoding='utf-8') as f:
            descriptions = json.load(f)
        
        print(f"✅ 개선된 설명 {len(descriptions)}개 로드 완료")
        return descriptions
    except Exception as e:
        print(f"❌ 설명 파일 로드 실패: {e}")
        return {}

def update_panel_descriptions(dashboard_data: Dict, descriptions: Dict[str, str]) -> Tuple[Dict, List[Dict]]:
    """패널들의 description 업데이트"""
    panels = dashboard_data.get('dashboard', {}).get('panels', [])
    update_results = []
    
    for panel in panels:
        panel_id = str(panel.get('id'))
        
        if panel_id in descriptions:
            old_description = panel.get('description', '')
            new_description = descriptions[panel_id]
            
            # Description 업데이트
            panel['description'] = new_description
            
            update_results.append({
                'panel_id': panel_id,
                'title': panel.get('title', '제목 없음'),
                'success': True,
                'old_length': len(old_description),
                'new_length': len(new_description),
                'had_description': bool(old_description.strip())
            })
            
            print(f"✅ Panel {panel_id} ({panel.get('title', '제목 없음')}) 업데이트 완료")
        else:
            # 대상 패널이 아닌 경우
            continue
    
    return dashboard_data, update_results

def main():
    """메인 실행 함수"""
    print("🚀 Grafana 대시보드 Description 업데이트 시작")
    print("=" * 60)
    
    # 1. 개선된 descriptions 로드
    descriptions = load_improved_descriptions()
    if not descriptions:
        print("❌ 설명 파일 로드 실패로 종료")
        return False
    
    # 2. Grafana 클라이언트 초기화
    try:
        client = GrafanaClient()
        if not client.test_connection():
            print("❌ Grafana 연결 실패")
            return False
        print("✅ Grafana 연결 성공")
    except Exception as e:
        print(f"❌ Grafana 클라이언트 초기화 실패: {e}")
        return False
    
    # 3. 현재 대시보드 조회
    dashboard_uid = 'rYdddlPWk'
    dashboard_data = client.get_dashboard_by_uid(dashboard_uid)
    
    if not dashboard_data:
        print(f"❌ 대시보드 조회 실패 (UID: {dashboard_uid})")
        return False
    
    print(f"✅ 대시보드 조회 성공: {dashboard_data.get('dashboard', {}).get('title', 'Unknown')}")
    
    # 4. 패널 descriptions 업데이트
    print("\n📝 패널 Description 업데이트 진행...")
    updated_dashboard, update_results = update_panel_descriptions(dashboard_data, descriptions)
    
    # 5. 업데이트 결과 요약
    successful_updates = [r for r in update_results if r['success']]
    print(f"\n📊 업데이트 결과 요약:")
    print(f"   - 성공한 패널: {len(successful_updates)}/{len(descriptions)}개")
    
    if not successful_updates:
        print("❌ 업데이트된 패널이 없습니다.")
        return False
    
    # 6. 대시보드 저장
    print(f"\n💾 대시보드 저장 중...")
    
    try:
        if client.update_dashboard(updated_dashboard):
            print("✅ 대시보드 저장 성공!")
            
            # 7. 상세 결과 보고
            print(f"\n📋 상세 업데이트 결과:")
            print("-" * 60)
            
            for result in successful_updates:
                had_desc_status = "기존 설명 있음" if result['had_description'] else "기존 설명 없음"
                print(f"Panel {result['panel_id']:>3} | {result['title']:<30} | {had_desc_status}")
                print(f"         | 설명 길이: {result['old_length']:>4} → {result['new_length']:>4} 글자")
                print()
            
            # 8. 검증을 위한 재조회
            print("🔍 업데이트 검증 중...")
            verification_dashboard = client.get_dashboard_by_uid(dashboard_uid)
            
            if verification_dashboard:
                verification_results = []
                panels = verification_dashboard.get('dashboard', {}).get('panels', [])
                
                for panel in panels:
                    panel_id = str(panel.get('id'))
                    if panel_id in descriptions:
                        current_desc = panel.get('description', '')
                        expected_desc = descriptions[panel_id]
                        
                        verification_results.append({
                            'panel_id': panel_id,
                            'title': panel.get('title', '제목 없음'),
                            'verified': current_desc == expected_desc,
                            'current_length': len(current_desc),
                            'expected_length': len(expected_desc)
                        })
                
                verified_count = sum(1 for r in verification_results if r['verified'])
                print(f"✅ 검증 완료: {verified_count}/{len(verification_results)}개 패널 정상 업데이트")
                
                # 검증 실패한 패널이 있으면 보고
                failed_verifications = [r for r in verification_results if not r['verified']]
                if failed_verifications:
                    print(f"\n⚠️  검증 실패 패널:")
                    for result in failed_verifications:
                        print(f"   Panel {result['panel_id']}: {result['title']}")
                        print(f"   예상 길이: {result['expected_length']}, 실제 길이: {result['current_length']}")
            
            return True
        else:
            print("❌ 대시보드 저장 실패")
            return False
            
    except Exception as e:
        print(f"❌ 대시보드 저장 중 오류: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 60)
    if success:
        print("🎉 모든 작업이 성공적으로 완료되었습니다!")
    else:
        print("❌ 작업 중 오류가 발생했습니다.")
    
    sys.exit(0 if success else 1)