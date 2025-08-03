#!/usr/bin/env python3
"""
Node Exporter Full 대시보드 패널 분석 결과를 요약하는 스크립트
"""

import json
import os
from datetime import datetime
from typing import Dict, List

def load_analysis_result() -> Dict:
    """최신 분석 결과 파일 로드"""
    current_dir = "/Users/paul/sandbox/sqms-mgmt/grafana/desc_editor"
    
    # node_exporter_full_analysis로 시작하는 파일들 찾기
    analysis_files = [f for f in os.listdir(current_dir) 
                     if f.startswith('node_exporter_full_analysis') and f.endswith('.json')]
    
    if not analysis_files:
        print("❌ 분석 결과 파일을 찾을 수 없습니다.")
        return {}
    
    # 가장 최신 파일 선택
    latest_file = sorted(analysis_files)[-1]
    file_path = os.path.join(current_dir, latest_file)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 파일 로드 실패: {e}")
        return {}

def filter_visualization_panels(panels: List[Dict]) -> List[Dict]:
    """Row 패널을 제외한 시각화 패널만 필터링"""
    visualization_types = [
        'bargauge', 'gauge', 'stat', 'timeseries', 'graph', 'table', 'singlestat',
        'text', 'heatmap', 'barchart', 'histogram', 'piechart', 'logs'
    ]
    
    return [panel for panel in panels if panel['type'] in visualization_types]

def generate_panel_summary(panels: List[Dict]) -> str:
    """패널 요약 리포트 생성"""
    report_lines = []
    report_lines.append("# Node Exporter Full (1860) 대시보드 패널 분석 리포트")
    report_lines.append(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # 시각화 패널만 필터링
    viz_panels = filter_visualization_panels(panels)
    
    report_lines.append(f"## 📊 전체 요약")
    report_lines.append(f"- 전체 패널 수: {len(panels)}개")
    report_lines.append(f"- 시각화 패널 수: {len(viz_panels)}개")
    report_lines.append(f"- Row 패널 수: {len(panels) - len(viz_panels)}개")
    report_lines.append("")
    
    # Description 통계
    panels_with_desc = [p for p in viz_panels if p['has_description']]
    panels_without_desc = [p for p in viz_panels if not p['has_description']]
    
    report_lines.append(f"## 📝 Description 현황")
    report_lines.append(f"- Description 있음: {len(panels_with_desc)}개 ({len(panels_with_desc)/len(viz_panels)*100:.1f}%)")
    report_lines.append(f"- Description 없음: {len(panels_without_desc)}개 ({len(panels_without_desc)/len(viz_panels)*100:.1f}%)")
    report_lines.append("")
    
    # 패널 타입별 통계
    type_stats = {}
    for panel in viz_panels:
        panel_type = panel['type']
        type_stats[panel_type] = type_stats.get(panel_type, 0) + 1
    
    report_lines.append(f"## 📈 패널 타입별 분포")
    for panel_type, count in sorted(type_stats.items()):
        percentage = count / len(viz_panels) * 100
        report_lines.append(f"- {panel_type}: {count}개 ({percentage:.1f}%)")
    report_lines.append("")
    
    # 상세 패널 정보
    report_lines.append(f"## 📋 상세 패널 정보")
    report_lines.append("")
    
    for i, panel in enumerate(viz_panels, 1):
        report_lines.append(f"### {i}. {panel['title']} (ID: {panel['id']})")
        report_lines.append(f"- **패널 타입**: {panel['type']}")
        report_lines.append(f"- **데이터소스**: {panel['datasource']['type']}")
        report_lines.append(f"- **Description 여부**: {'✅ 있음' if panel['has_description'] else '❌ 없음'}")
        
        if panel['has_description']:
            desc = panel['description'][:100]
            if len(panel['description']) > 100:
                desc += "..."
            report_lines.append(f"- **Description**: {desc}")
        
        # Query 정보
        if panel['targets']:
            report_lines.append(f"- **Query 수**: {len(panel['targets'])}개")
            for j, target in enumerate(panel['targets']):
                if target['expr']:
                    expr = target['expr'][:80]
                    if len(target['expr']) > 80:
                        expr += "..."
                    report_lines.append(f"  - Query {j+1}: `{expr}`")
        
        # Threshold 정보
        if panel['thresholds'].get('steps'):
            threshold_count = len(panel['thresholds']['steps'])
            report_lines.append(f"- **Threshold**: {threshold_count}개 설정됨")
        
        report_lines.append("")
    
    # Description이 없는 패널 목록
    if panels_without_desc:
        report_lines.append(f"## ⚠️  Description이 없는 패널 목록")
        report_lines.append("")
        for panel in panels_without_desc:
            report_lines.append(f"- **{panel['title']}** (ID: {panel['id']}, Type: {panel['type']})")
        report_lines.append("")
    
    return "\n".join(report_lines)

def generate_json_summary(panels: List[Dict]) -> Dict:
    """JSON 형태의 요약 생성"""
    viz_panels = filter_visualization_panels(panels)
    
    summary = {
        "summary": {
            "total_panels": len(panels),
            "visualization_panels": len(viz_panels),
            "row_panels": len(panels) - len(viz_panels),
            "panels_with_description": len([p for p in viz_panels if p['has_description']]),
            "panels_without_description": len([p for p in viz_panels if not p['has_description']]),
            "description_coverage": len([p for p in viz_panels if p['has_description']]) / len(viz_panels) * 100
        },
        "panel_types": {},
        "panels_needing_description": [],
        "detailed_panels": []
    }
    
    # 패널 타입 통계
    for panel in viz_panels:
        panel_type = panel['type']
        summary['panel_types'][panel_type] = summary['panel_types'].get(panel_type, 0) + 1
    
    # Description이 없는 패널들
    for panel in viz_panels:
        if not panel['has_description']:
            summary['panels_needing_description'].append({
                "id": panel['id'],
                "title": panel['title'],
                "type": panel['type']
            })
    
    # 상세 패널 정보 (핵심 정보만)
    for panel in viz_panels:
        panel_summary = {
            "id": panel['id'],
            "title": panel['title'],
            "type": panel['type'],
            "has_description": panel['has_description'],
            "description": panel['description'] if panel['has_description'] else "",
            "datasource_type": panel['datasource']['type'],
            "query_count": len(panel['targets']),
            "queries": [target['expr'] for target in panel['targets'] if target['expr']],
            "has_thresholds": bool(panel['thresholds'].get('steps')),
            "threshold_count": len(panel['thresholds'].get('steps', []))
        }
        summary['detailed_panels'].append(panel_summary)
    
    return summary

def main():
    """메인 실행 함수"""
    print("📊 Node Exporter Full 대시보드 패널 요약 생성 중...")
    
    # 분석 결과 로드
    analysis_data = load_analysis_result()
    if not analysis_data:
        return
    
    panels = analysis_data.get('panels', [])
    if not panels:
        print("❌ 패널 데이터가 없습니다.")
        return
    
    # 마크다운 리포트 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 텍스트 요약 리포트
    text_report = generate_panel_summary(panels)
    text_file = f"/Users/paul/sandbox/sqms-mgmt/grafana/desc_editor/node_exporter_panel_summary_{timestamp}.md"
    
    try:
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_report)
        print(f"✅ 마크다운 리포트 저장됨: {text_file}")
    except Exception as e:
        print(f"❌ 마크다운 리포트 저장 실패: {e}")
    
    # JSON 요약 리포트
    json_summary = generate_json_summary(panels)
    json_file = f"/Users/paul/sandbox/sqms-mgmt/grafana/desc_editor/node_exporter_panel_summary_{timestamp}.json"
    
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_summary, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON 요약 저장됨: {json_file}")
    except Exception as e:
        print(f"❌ JSON 요약 저장 실패: {e}")
    
    # 간단한 통계 출력
    viz_panels = filter_visualization_panels(panels)
    print(f"\n📈 요약 통계:")
    print(f"   시각화 패널: {len(viz_panels)}개")
    print(f"   Description 있음: {len([p for p in viz_panels if p['has_description']])}개")
    print(f"   Description 없음: {len([p for p in viz_panels if not p['has_description']])}개")
    print(f"   Description 커버리지: {len([p for p in viz_panels if p['has_description']])/len(viz_panels)*100:.1f}%")

if __name__ == "__main__":
    main()