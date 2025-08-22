import streamlit as st
import json
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import ipaddress
import re
from collections import defaultdict, Counter
from modules.utils.version import show_version_info, save_repo_url, load_repo_url

# 시각화용 추가 imports
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import networkx as nx
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

# 모듈 ID와 버전 정보
MODULE_ID = "prometheus_manager"
VERSION = "v0.1.0"
DEFAULT_REPO_URL = "https://github.com/prometheus/prometheus/tags"

def show_module():
    """Prometheus 관리 모듈 메인 화면"""
    st.title("Prometheus 관리")

    # 버전 정보 표시
    st.caption(f"모듈 버전: {VERSION}")
    
    # 탭 생성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 호스트 관리", 
        "⚙️ 설정 제너레이터", 
        "🚀 서버 배포", 
        "🔍 설정 검증",
        "🔧 Prometheus 설정"
    ])
    
    # 호스트 관리 탭
    with tab1:
        show_host_management()
    
    # 설정 제너레이터 탭
    with tab2:
        show_config_generator()
    
    # 서버 배포 탭
    with tab3:
        show_server_deployment()
    
    # 설정 검증 탭
    with tab4:
        show_config_validator()
    
    # Prometheus 설정 탭
    with tab5:
        show_prometheus_settings()

def show_host_management():
    """호스트 관리 화면"""
    st.subheader("호스트 관리")
    
    # 설정 경로 확인
    config_path = os.environ.get("PROMETHEUS_CONFIG_PATH", "")
    
    if not config_path:
        st.error("PROMETHEUS_CONFIG_PATH 환경변수가 설정되지 않았습니다. Prometheus 설정 탭에서 경로를 설정해주세요.")
        return
    
    if not os.path.exists(config_path):
        st.error(f"설정 경로가 존재하지 않습니다: {config_path}")
        return
    
    # 설정 파일 스캔 버튼
    if st.button("설정 파일 스캔", type="primary"):
        with st.spinner("설정 파일을 스캔하는 중입니다..."):
            hosts_data, scan_stats = scan_prometheus_configs(config_path)
            
            if hosts_data:
                # 세션 상태에 저장
                st.session_state.prometheus_hosts = hosts_data
                st.session_state.prometheus_scan_stats = scan_stats
                st.success(f"총 {len(hosts_data)}개의 호스트를 발견했습니다.")
            else:
                st.warning("스캔된 호스트가 없습니다.")
    
    # 스캔 결과 표시
    if hasattr(st.session_state, 'prometheus_hosts'):
        show_host_dashboard()
    else:
        st.info("'설정 파일 스캔' 버튼을 클릭하여 호스트 정보를 불러와주세요.")

def scan_prometheus_configs(config_path):
    """설정 파일들을 스캔하여 호스트 정보 추출"""
    hosts_data = []
    scan_stats = {
        'total_files': 0,
        'parsed_files': 0,
        'total_configs': 0,
        'folders': set(),
        'exporters': set(),
        'services': set(),
        'groups': set(),
        'errors': []
    }
    
    try:
        config_path = Path(config_path)
        
        # JSON 파일들을 재귀적으로 찾기
        for json_file in config_path.rglob("*.json"):
            scan_stats['total_files'] += 1
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 파일 경로에서 메타데이터 추출
                relative_path = json_file.relative_to(config_path)
                path_parts = relative_path.parts
                
                exporter = path_parts[0] if len(path_parts) > 0 else "unknown"
                service_platform = path_parts[1] if len(path_parts) > 1 else "unknown"
                
                scan_stats['folders'].add(str(relative_path.parent))
                scan_stats['exporters'].add(exporter)
                
                # 배열 형태의 설정 처리
                if isinstance(config_data, list):
                    configs = config_data
                else:
                    configs = [config_data]
                
                for config in configs:
                    if 'targets' in config and 'labels' in config:
                        scan_stats['total_configs'] += 1
                        
                        labels = config['labels']
                        targets = config['targets']
                        
                        # 라벨 값들 수집
                        scan_stats['services'].add(labels.get('service', 'unknown'))
                        scan_stats['groups'].add(labels.get('group', 'unknown'))
                        
                        # 각 타겟에 대해 호스트 정보 생성
                        for target in targets:
                            host_info = {
                                'file_path': str(json_file),
                                'relative_path': str(relative_path),
                                'exporter': exporter,
                                'service_platform': service_platform,
                                'target': target,
                                'labels': labels.copy()
                            }
                            
                            # IP와 포트 분리
                            if ':' in target:
                                ip, port = target.rsplit(':', 1)
                                host_info['ip'] = ip
                                host_info['port'] = port
                            else:
                                host_info['ip'] = target
                                host_info['port'] = 'N/A'
                            
                            hosts_data.append(host_info)
                
                scan_stats['parsed_files'] += 1
                
            except json.JSONDecodeError as e:
                scan_stats['errors'].append(f"JSON 파싱 오류 - {json_file}: {str(e)}")
            except Exception as e:
                scan_stats['errors'].append(f"파일 처리 오류 - {json_file}: {str(e)}")
    
    except Exception as e:
        scan_stats['errors'].append(f"경로 스캔 오류: {str(e)}")
    
    # set을 list로 변환
    for key in ['folders', 'exporters', 'services', 'groups']:
        scan_stats[key] = sorted(list(scan_stats[key]))
    
    return hosts_data, scan_stats

def show_host_dashboard():
    """호스트 대시보드 표시"""
    hosts_data = st.session_state.prometheus_hosts
    scan_stats = st.session_state.prometheus_scan_stats
    
    # 스캔 통계 표시
    st.subheader("📊 스캔 통계")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 호스트", len(hosts_data))
    with col2:
        st.metric("처리된 파일", f"{scan_stats['parsed_files']}/{scan_stats['total_files']}")
    with col3:
        st.metric("Exporter 종류", len(scan_stats['exporters']))
    with col4:
        st.metric("서비스 종류", len(scan_stats['services']))
    
    # 에러가 있으면 표시
    if scan_stats['errors']:
        with st.expander(f"⚠️ 처리 오류 ({len(scan_stats['errors'])}개)", expanded=False):
            for error in scan_stats['errors']:
                st.error(error)
    
    # 필터링 옵션
    st.subheader("🔍 필터링")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_exporter = st.selectbox("Exporter", ["전체"] + scan_stats['exporters'])
    with col2:
        selected_service = st.selectbox("서비스", ["전체"] + scan_stats['services'])
    with col3:
        selected_group = st.selectbox("그룹", ["전체"] + scan_stats['groups'])
    
    # 검색어
    search_term = st.text_input("검색 (IP, purpose, gid 등)", "")
    
    # 필터링 적용
    filtered_hosts = filter_hosts(hosts_data, selected_exporter, selected_service, selected_group, search_term)
    
    st.write(f"**필터링 결과: {len(filtered_hosts)}개 호스트**")
    
    if filtered_hosts:
        # 데이터프레임 생성
        df = create_hosts_dataframe(filtered_hosts)
        
        # 데이터프레임 표시
        st.dataframe(df, use_container_width=True)
        
        # CSV 다운로드
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 CSV 다운로드",
            data=csv,
            file_name=f"prometheus_hosts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # 상세 분석
        show_detailed_analysis(filtered_hosts)
        
        # 그래프 시각화
        st.write("---")
        show_network_visualization(filtered_hosts)
    else:
        st.info("필터 조건에 맞는 호스트가 없습니다.")

def filter_hosts(hosts_data, exporter, service, group, search_term):
    """호스트 데이터 필터링"""
    filtered = hosts_data
    
    if exporter != "전체":
        filtered = [h for h in filtered if h['exporter'] == exporter]
    
    if service != "전체":
        filtered = [h for h in filtered if h['labels'].get('service') == service]
    
    if group != "전체":
        filtered = [h for h in filtered if h['labels'].get('group') == group]
    
    if search_term:
        search_lower = search_term.lower()
        filtered = [h for h in filtered if 
                   search_lower in h.get('ip', '').lower() or
                   search_lower in h['labels'].get('purpose', '').lower() or
                   search_lower in h['labels'].get('gid', '').lower() or
                   search_lower in str(h['labels']).lower()]
    
    return filtered

def create_hosts_dataframe(hosts_data):
    """호스트 데이터를 데이터프레임으로 변환"""
    df_data = []
    
    for host in hosts_data:
        labels = host['labels']
        df_data.append({
            'IP': host.get('ip', ''),
            'Port': host.get('port', ''),
            'Target': host.get('target', ''),
            'Service': labels.get('service', ''),
            'Group': labels.get('group', ''),
            'GID': labels.get('gid', ''),
            'Purpose': labels.get('purpose', ''),
            'OS': labels.get('os', ''),
            'Exporter': host.get('exporter', ''),
            'Platform': host.get('service_platform', ''),
            'File Path': host.get('relative_path', '')
        })
    
    return pd.DataFrame(df_data)

def show_detailed_analysis(hosts_data):
    """상세 분석 정보 표시"""
    st.subheader("📈 상세 분석")
    
    # 중복 IP 체크
    ip_counts = Counter([h.get('ip') for h in hosts_data if h.get('ip')])
    duplicate_ips = {ip: count for ip, count in ip_counts.items() if count > 1}
    
    if duplicate_ips:
        st.warning(f"🔴 중복 IP 발견: {len(duplicate_ips)}개")
        with st.expander("중복 IP 상세", expanded=False):
            for ip, count in duplicate_ips.items():
                st.write(f"- {ip}: {count}회 등장")
    else:
        st.success("✅ 중복 IP 없음")
    
    # 포트 분포
    port_counts = Counter([h.get('port') for h in hosts_data if h.get('port') != 'N/A'])
    if port_counts:
        st.write("**포트 분포:**")
        port_df = pd.DataFrame(list(port_counts.items()), columns=['Port', 'Count'])
        st.bar_chart(port_df.set_index('Port'))

def show_network_visualization(hosts_data):
    """네트워크 관계 시각화"""
    st.subheader("🕸️ 네트워크 관계 시각화")
    
    if not hosts_data:
        st.info("시각화할 데이터가 없습니다.")
        return
    
    if not VISUALIZATION_AVAILABLE:
        st.warning("⚠️ 시각화에 필요한 패키지가 설치되지 않았습니다.")
        st.info("다음 명령어로 설치하세요: `pip install matplotlib seaborn networkx`")
        return
    
    # 시각화 타입 선택
    viz_type = st.selectbox(
        "시각화 타입", 
        ["라벨 관계도", "서비스 그룹 매트릭스", "포트 분포", "IP 네트워크 맵"]
    )
    
    if viz_type == "라벨 관계도":
        show_label_relationship_graph(hosts_data)
    elif viz_type == "서비스 그룹 매트릭스":
        show_service_group_matrix(hosts_data)
    elif viz_type == "포트 분포":
        show_port_distribution_chart(hosts_data)
    elif viz_type == "IP 네트워크 맵":
        show_ip_network_map(hosts_data)

def show_label_relationship_graph(hosts_data):
    """라벨 관계 그래프 생성"""
    st.write("### 📊 라벨 간 관계도")
    
    # 라벨 조합 분석
    label_combinations = defaultdict(int)
    service_groups = defaultdict(set)
    group_os = defaultdict(set)
    
    for host in hosts_data:
        labels = host.get('labels', {})
        service = labels.get('service', 'unknown')
        group = labels.get('group', 'unknown')
        os_val = labels.get('os', 'unknown')
        
        # 서비스-그룹 관계
        service_groups[service].add(group)
        # 그룹-OS 관계
        group_os[group].add(os_val)
        
        # 라벨 조합 빈도
        combo = f"{service}|{group}|{os_val}"
        label_combinations[combo] += 1
    
    # 간단한 분포 차트 (Streamlit 기본 차트 사용)
    services = set()
    groups = set()
    os_types = set()
    
    for host in hosts_data:
        labels = host.get('labels', {})
        services.add(labels.get('service', 'unknown'))
        groups.add(labels.get('group', 'unknown'))
        os_types.add(labels.get('os', 'unknown'))
    
    # 서비스별 분포
    st.write("### 📊 서비스별 분포")
    service_counts = defaultdict(int)
    for host in hosts_data:
        service = host.get('labels', {}).get('service', 'unknown')
        service_counts[service] += 1
    
    if service_counts:
        service_df = pd.DataFrame(list(service_counts.items()), columns=['Service', 'Count'])
        service_df = service_df.sort_values('Count', ascending=False)
        st.bar_chart(service_df.set_index('Service'))
    
    # 그룹별 분포  
    st.write("### 📊 그룹별 분포")
    group_counts = defaultdict(int)
    for host in hosts_data:
        group = host.get('labels', {}).get('group', 'unknown')
        group_counts[group] += 1
    
    if group_counts:
        group_df = pd.DataFrame(list(group_counts.items()), columns=['Group', 'Count'])
        group_df = group_df.sort_values('Count', ascending=False)
        st.bar_chart(group_df.set_index('Group'))
    
    # OS별 분포
    st.write("### 📊 OS별 분포")
    os_counts = defaultdict(int)
    for host in hosts_data:
        os_val = host.get('labels', {}).get('os', 'unknown')
        os_counts[os_val] += 1
    
    if os_counts:
        os_df = pd.DataFrame(list(os_counts.items()), columns=['OS', 'Count'])
        os_df = os_df.sort_values('Count', ascending=False)
        st.bar_chart(os_df.set_index('OS'))
    
    # 관계 통계
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("서비스 수", len(services))
    with col2:
        st.metric("그룹 수", len(groups))
    with col3:
        st.metric("OS 종류", len(os_types))

def show_service_group_matrix(hosts_data):
    """서비스-그룹 매트릭스"""
    st.write("### 🔲 서비스-그룹 매트릭스")
    
    # 매트릭스 데이터 생성
    matrix_data = defaultdict(lambda: defaultdict(int))
    
    for host in hosts_data:
        labels = host.get('labels', {})
        service = labels.get('service', 'unknown')
        group = labels.get('group', 'unknown')
        matrix_data[service][group] += 1
    
    # DataFrame으로 변환
    services = list(matrix_data.keys())
    all_groups = set()
    for groups in matrix_data.values():
        all_groups.update(groups.keys())
    all_groups = sorted(list(all_groups))
    
    matrix_df = pd.DataFrame(
        [[matrix_data[service][group] for group in all_groups] for service in services],
        index=services,
        columns=all_groups
    )
    
    # 히트맵 생성
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(matrix_df, annot=True, fmt='d', cmap='YlOrRd', ax=ax)
    plt.title("서비스-그룹별 호스트 수")
    plt.xlabel("그룹")
    plt.ylabel("서비스")
    plt.tight_layout()
    st.pyplot(fig)
    
    # 매트릭스 데이터프레임도 표시
    with st.expander("📊 상세 데이터", expanded=False):
        st.dataframe(matrix_df)

def show_port_distribution_chart(hosts_data):
    """포트 분포 차트"""
    st.write("### 🚪 포트 분포 분석")
    
    port_data = []
    for host in hosts_data:
        labels = host.get('labels', {})
        port = host.get('port', 'N/A')
        service = labels.get('service', 'unknown')
        group = labels.get('group', 'unknown')
        
        if port != 'N/A':
            port_data.append({
                'Port': port,
                'Service': service,
                'Group': group,
                'Count': 1
            })
    
    if not port_data:
        st.info("포트 정보가 없습니다.")
        return
    
    port_df = pd.DataFrame(port_data)
    
    # 포트별 서비스 분포
    port_service_df = port_df.groupby(['Port', 'Service']).size().reset_index(name='Count')
    
    # 선버스트 차트 시뮬레이션 (계층적 바차트)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 포트별 총 개수
    port_counts = port_df.groupby('Port')['Count'].sum().sort_values(ascending=False)
    ax1.bar(range(len(port_counts)), port_counts.values, color='lightblue')
    ax1.set_xticks(range(len(port_counts)))
    ax1.set_xticklabels(port_counts.index, rotation=45)
    ax1.set_title("포트별 호스트 수")
    ax1.set_xlabel("포트")
    ax1.set_ylabel("호스트 수")
    
    # 서비스별 포트 분포
    service_counts = port_df.groupby('Service')['Count'].sum().sort_values(ascending=False)
    colors = plt.cm.Set3(range(len(service_counts)))
    ax2.pie(service_counts.values, labels=service_counts.index, autopct='%1.1f%%', colors=colors)
    ax2.set_title("서비스별 분포")
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # 상세 테이블
    with st.expander("📋 상세 포트 정보", expanded=False):
        summary_df = port_df.groupby(['Port', 'Service', 'Group']).size().reset_index(name='호스트수')
        st.dataframe(summary_df.sort_values('호스트수', ascending=False))

def show_ip_network_map(hosts_data):
    """IP 네트워크 맵"""
    st.write("### 🌐 IP 네트워크 맵")
    
    # IP 대역별 분류
    import ipaddress
    network_data = defaultdict(list)
    
    for host in hosts_data:
        ip = host.get('ip')
        if ip and ip != 'N/A':
            try:
                # /24 네트워크로 그룹핑
                network = ipaddress.IPv4Network(f"{ip}/24", strict=False)
                network_addr = str(network.network_address)
                network_data[network_addr].append(host)
            except:
                network_data['기타'].append(host)
    
    if not network_data:
        st.info("유효한 IP 정보가 없습니다.")
        return
    
    # 네트워크별 통계
    st.write("**네트워크 대역별 분포:**")
    
    network_stats = []
    for network, hosts in network_data.items():
        services = set(h.get('labels', {}).get('service', 'unknown') for h in hosts)
        groups = set(h.get('labels', {}).get('group', 'unknown') for h in hosts)
        
        network_stats.append({
            '네트워크': network + '/24' if network != '기타' else network,
            '호스트 수': len(hosts),
            '서비스 종류': len(services),
            '그룹 종류': len(groups),
            '서비스 목록': ', '.join(list(services)[:3]) + ('...' if len(services) > 3 else ''),
            '그룹 목록': ', '.join(list(groups)[:3]) + ('...' if len(groups) > 3 else '')
        })
    
    network_df = pd.DataFrame(network_stats)
    network_df = network_df.sort_values('호스트 수', ascending=False)
    st.dataframe(network_df, use_container_width=True)
    
    # 네트워크 크기 시각화
    fig, ax = plt.subplots(figsize=(12, 6))
    
    networks = network_df['네트워크'].tolist()
    host_counts = network_df['호스트 수'].tolist()
    
    bars = ax.bar(range(len(networks)), host_counts, color='lightgreen')
    ax.set_xticks(range(len(networks)))
    ax.set_xticklabels(networks, rotation=45, ha='right')
    ax.set_title("네트워크 대역별 호스트 분포")
    ax.set_xlabel("네트워크 대역")
    ax.set_ylabel("호스트 수")
    
    # 막대 위에 숫자 표시
    for bar, count in zip(bars, host_counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
               str(count), ha='center', va='bottom')
    
    plt.tight_layout()
    st.pyplot(fig)

def show_config_generator():
    """설정 제너레이터 화면"""
    st.subheader("설정 제너레이터")
    
    # 기존 호스트 데이터에서 라벨 값들 추출
    label_suggestions = get_label_suggestions()
    
    # 입력 폼
    with st.form("config_generator_form"):
        st.write("### 새 호스트 설정 생성")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 타겟 정보
            st.write("**타겟 정보**")
            target_ip = st.text_input("IP 주소", placeholder="192.168.1.100")
            target_port = st.text_input("포트", value="9100", placeholder="9100")
            
            # 서비스 정보 (자동완성 제안)
            service = st.selectbox("서비스", [""] + label_suggestions.get('services', []), 
                                 help="기존 서비스 목록에서 선택하거나 새로 입력")
            if service == "":
                service = st.text_input("새 서비스 이름", placeholder="예: web-server")
            
            group = st.selectbox("그룹", [""] + label_suggestions.get('groups', []),
                               help="기존 그룹 목록에서 선택하거나 새로 입력")
            if group == "":
                group = st.text_input("새 그룹 이름", placeholder="예: production")
        
        with col2:
            st.write("**추가 라벨**")
            gid = st.text_input("GID", placeholder="예: web-001")
            purpose = st.text_input("용도", placeholder="예: 웹 서버")
            os = st.selectbox("운영체제", [""] + label_suggestions.get('os_types', []))
            if os == "":
                os = st.text_input("새 OS", placeholder="예: ubuntu-20.04")
            
            # 커스텀 라벨
            st.write("**커스텀 라벨 (선택사항)**")
            custom_labels = st.text_area("추가 라벨 (JSON 형식)", 
                                       placeholder='{"environment": "prod", "team": "backend"}',
                                       help="JSON 형식으로 추가 라벨을 입력하세요")
        
        # 생성 버튼
        generate_button = st.form_submit_button("설정 생성", type="primary")
        
        if generate_button:
            if not target_ip or not target_port or not service or not group:
                st.error("필수 필드(IP, 포트, 서비스, 그룹)를 모두 입력해주세요.")
            else:
                config = generate_prometheus_config(
                    target_ip, target_port, service, group, gid, purpose, os, custom_labels
                )
                
                if config:
                    show_generated_config(config, target_ip, target_port)
    
    # 설정 템플릿 선택
    st.write("---")
    st.subheader("📋 템플릿 기반 생성")
    
    template_type = st.selectbox("템플릿 선택", [
        "Node Exporter (9100)",
        "MySQL Exporter (9104)", 
        "PostgreSQL Exporter (9187)",
        "Redis Exporter (9121)",
        "Nginx Exporter (9113)",
        "Custom Port"
    ])
    
    if st.button("템플릿으로 생성"):
        template_config = get_config_template(template_type)
        show_generated_config(template_config, "템플릿", template_type)

def show_server_deployment():
    """서버 배포 화면"""
    st.subheader("서버 배포")
    
    # 서버 정보 불러오기
    server1 = os.environ.get("PROMETHEUS_SERVER_1", "")
    server2 = os.environ.get("PROMETHEUS_SERVER_2", "")
    server3 = os.environ.get("PROMETHEUS_SERVER_3", "")
    
    servers = [
        {"name": server1, "id": "server1"},
        {"name": server2, "id": "server2"}, 
        {"name": server3, "id": "server3"}
    ]
    
    # 서버 상태 확인
    st.subheader("🖥️ 서버 현황")
    
    cols = st.columns(3)
    for i, server in enumerate(servers):
        with cols[i]:
            if server["name"]:
                st.info(f"**{server['name']}**\n서버 {i+1}")
                if st.button(f"상태 확인", key=f"check_{server['id']}"):
                    check_server_status(server['name'], server['id'])
            else:
                st.warning(f"**서버 {i+1}**\n설정되지 않음")
    
    st.write("---")
    
    # 배포 옵션
    st.subheader("📤 배포 옵션")
    
    deployment_type = st.radio(
        "배포 방식 선택:",
        ["개별 서버 배포", "전체 서버 일괄 배포", "설정 파일 생성만"],
        help="개별: 선택한 서버에만 배포\n일괄: 모든 서버에 동시 배포\n생성만: 로컬에 파일만 생성"
    )
    
    # 배포할 설정 선택
    if hasattr(st.session_state, 'prometheus_hosts'):
        st.subheader("📁 배포 대상 선택")
        
        # 파일별 그룹화
        hosts_by_file = defaultdict(list)
        for host in st.session_state.prometheus_hosts:
            file_path = host.get('relative_path', 'unknown')
            hosts_by_file[file_path].append(host)
        
        selected_files = []
        
        for file_path, hosts in hosts_by_file.items():
            if st.checkbox(f"📄 {file_path} ({len(hosts)}개 호스트)", key=f"file_{file_path}"):
                selected_files.append(file_path)
        
        if selected_files:
            st.write(f"**선택된 파일:** {len(selected_files)}개")
            
            # 배포 실행
            if deployment_type == "설정 파일 생성만":
                if st.button("📁 로컬 파일 생성", type="primary"):
                    create_deployment_files(selected_files, hosts_by_file)
            else:
                target_servers = []
                
                if deployment_type == "개별 서버 배포":
                    st.write("**배포 대상 서버 선택:**")
                    for server in servers:
                        if server["name"] and st.checkbox(f"{server['name']}", key=f"deploy_{server['id']}"):
                            target_servers.append(server)
                else:
                    target_servers = [s for s in servers if s["name"]]
                
                if target_servers and st.button("🚀 배포 실행", type="primary"):
                    deploy_to_servers(selected_files, hosts_by_file, target_servers)
        
        else:
            st.info("배포할 파일을 선택해주세요.")
    
    else:
        st.info("먼저 '호스트 관리' 탭에서 설정 파일을 스캔해주세요.")
    
    # 배포 히스토리
    st.write("---")
    st.subheader("📜 배포 기록")
    
    if 'deployment_history' not in st.session_state:
        st.session_state.deployment_history = []
    
    if st.session_state.deployment_history:
        history_df = pd.DataFrame(st.session_state.deployment_history)
        st.dataframe(history_df, use_container_width=True)
        
        if st.button("기록 초기화"):
            st.session_state.deployment_history = []
            st.success("배포 기록이 초기화되었습니다.")
    else:
        st.info("배포 기록이 없습니다.")

def show_config_validator():
    """설정 검증 화면"""
    st.subheader("설정 검증")
    st.write("기존 설정과 격리된 상태에서 새로운 JSON/YAML 설정을 검증합니다.")
    
    # 입력 방식 선택
    input_method = st.radio(
        "입력 방식 선택:",
        ["텍스트 직접 입력", "파일 업로드"],
        horizontal=True
    )
    
    config_data = None
    config_format = None
    
    if input_method == "텍스트 직접 입력":
        # 형식 선택
        config_format = st.selectbox("설정 형식", ["JSON", "YAML"])
        
        # 예시 템플릿 제공
        if st.button("예시 템플릿 로드"):
            if config_format == "JSON":
                example_config = get_example_json_config()
            else:
                example_config = get_example_yaml_config()
            st.session_state.config_input = example_config
        
        # 텍스트 입력
        config_text = st.text_area(
            f"{config_format} 설정 입력:",
            value=st.session_state.get('config_input', ''),
            height=400,
            help=f"검증할 {config_format} 형식의 Prometheus 설정을 입력하세요"
        )
        
        if config_text.strip():
            config_data = config_text
    
    else:
        # 파일 업로드
        uploaded_file = st.file_uploader(
            "설정 파일 업로드", 
            type=['json', 'yml', 'yaml'],
            help="JSON 또는 YAML 형식의 Prometheus 설정 파일을 업로드하세요"
        )
        
        if uploaded_file is not None:
            # 파일 확장자로 형식 판단
            if uploaded_file.name.endswith('.json'):
                config_format = "JSON"
            elif uploaded_file.name.endswith(('.yml', '.yaml')):
                config_format = "YAML"
            
            # 파일 내용 읽기
            try:
                config_data = uploaded_file.read().decode('utf-8')
                st.success(f"파일 '{uploaded_file.name}'이 업로드되었습니다.")
            except Exception as e:
                st.error(f"파일 읽기 실패: {str(e)}")
    
    # 검증 실행
    if config_data and config_format:
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🔍 검증 실행", type="primary"):
                validate_custom_config(config_data, config_format)
        
        with col2:
            if st.button("📚 기존 설정 참조"):
                show_existing_config_reference()
    
    # 검증 도움말
    st.write("---")
    with st.expander("💡 검증 도움말", expanded=False):
        st.write("""
        **검증 항목:**
        - JSON/YAML 구문 검사
        - 필수 필드 확인 (targets, labels)
        - IP 주소 및 포트 형식 검증
        - 라벨 규칙 검사
        - 기존 설정과의 중복 확인
        - 권장사항 제시
        
        **기존 설정 참조:**
        - 현재 사용 중인 라벨 값들
        - 포트 사용 현황
        - IP 대역 분포
        - 서비스/그룹 목록
        """)

def get_example_json_config():
    """예시 JSON 설정 반환"""
    return '''{
  "targets": ["192.168.1.100:9100"],
  "labels": {
    "service": "example-service",
    "group": "production",
    "ip": "192.168.1.100",
    "gid": "app-001",
    "purpose": "웹 서버 모니터링",
    "os": "ubuntu-20.04",
    "environment": "prod",
    "team": "backend"
  }
}'''

def get_example_yaml_config():
    """예시 YAML 설정 반환"""
    return '''targets:
  - "192.168.1.100:9100"
labels:
  service: "example-service"
  group: "production"
  ip: "192.168.1.100"
  gid: "app-001"
  purpose: "웹 서버 모니터링"
  os: "ubuntu-20.04"
  environment: "prod"
  team: "backend"'''

def validate_custom_config(config_data, config_format):
    """커스텀 설정 검증"""
    st.subheader("🔍 검증 결과")
    
    # 1. 구문 검사
    parsed_config = None
    try:
        if config_format == "JSON":
            parsed_config = json.loads(config_data)
            st.success("✅ JSON 구문이 올바릅니다.")
        else:  # YAML
            try:
                import yaml
                parsed_config = yaml.safe_load(config_data)
                st.success("✅ YAML 구문이 올바릅니다.")
            except ImportError:
                st.error("❌ YAML 파싱을 위해 PyYAML 패키지가 필요합니다.")
                return
    except Exception as e:
        st.error(f"❌ {config_format} 구문 오류: {str(e)}")
        return
    
    # 2. 구조 검증
    issues = []
    warnings = []
    suggestions = []
    
    # 단일 객체인지 배열인지 확인
    if isinstance(parsed_config, list):
        configs = parsed_config
        st.info(f"📋 배열 형태의 설정 (항목 수: {len(configs)})")
    else:
        configs = [parsed_config]
        st.info("📄 단일 객체 형태의 설정")
    
    # 각 설정 항목 검증
    for i, config in enumerate(configs):
        st.write(f"**항목 {i+1} 검증:**")
        
        # 필수 필드 검사
        if not config.get('targets'):
            issues.append(f"항목 {i+1}: 'targets' 필드가 누락되었습니다")
        
        if not config.get('labels'):
            warnings.append(f"항목 {i+1}: 'labels' 필드가 누락되었습니다")
        
        # 타겟 검증
        targets = config.get('targets', [])
        for target in targets:
            if not isinstance(target, str):
                issues.append(f"항목 {i+1}: 타겟은 문자열이어야 합니다: {target}")
                continue
                
            if ':' not in target:
                warnings.append(f"항목 {i+1}: 타겟에 포트가 명시되지 않았습니다: {target}")
            else:
                ip, port = target.rsplit(':', 1)
                try:
                    ipaddress.ip_address(ip)
                except ValueError:
                    issues.append(f"항목 {i+1}: 올바르지 않은 IP 주소: {ip}")
                
                if not port.isdigit() or not (1 <= int(port) <= 65535):
                    issues.append(f"항목 {i+1}: 올바르지 않은 포트: {port}")
        
        # 라벨 검증
        labels = config.get('labels', {})
        if labels:
            validate_labels_detailed(labels, i+1, warnings, suggestions)
    
    # 기존 설정과 비교
    if hasattr(st.session_state, 'prometheus_hosts'):
        compare_with_existing_configs(configs, warnings, suggestions)
    
    # 결과 표시
    display_validation_results(issues, warnings, suggestions)
    
    # 최종 설정 미리보기
    st.subheader("📄 검증된 설정 미리보기")
    if config_format == "JSON":
        formatted_config = json.dumps(parsed_config, indent=2, ensure_ascii=False)
        st.code(formatted_config, language="json")
    else:
        st.code(config_data, language="yaml")

def validate_labels_detailed(labels, item_num, warnings, suggestions):
    """라벨 상세 검증"""
    required_labels = ['service', 'group', 'ip']
    recommended_labels = ['gid', 'purpose', 'os']
    
    # 필수 라벨 검사
    for label in required_labels:
        if not labels.get(label):
            warnings.append(f"항목 {item_num}: 필수 라벨 '{label}'이 누락되었습니다")
    
    # 권장 라벨 검사
    missing_recommended = [label for label in recommended_labels if not labels.get(label)]
    if missing_recommended:
        suggestions.append(f"항목 {item_num}: 권장 라벨 추가 고려: {', '.join(missing_recommended)}")
    
    # 라벨 값 검사
    for key, value in labels.items():
        if not value or str(value).strip() == '':
            warnings.append(f"항목 {item_num}: 라벨 '{key}'의 값이 비어있습니다")
        elif str(value) == 'tobe':
            suggestions.append(f"항목 {item_num}: 라벨 '{key}'의 값이 'tobe'입니다. 실제 값으로 변경하세요")

def compare_with_existing_configs(new_configs, warnings, suggestions):
    """기존 설정과 비교"""
    existing_hosts = st.session_state.prometheus_hosts
    
    existing_targets = set()
    existing_ips = set()
    existing_services = set()
    
    for host in existing_hosts:
        target = host.get('target', '')
        existing_targets.add(target)
        
        labels = host.get('labels', {})
        if labels.get('ip'):
            existing_ips.add(labels['ip'])
        if labels.get('service'):
            existing_services.add(labels['service'])
    
    # 새 설정 검사
    for i, config in enumerate(new_configs):
        targets = config.get('targets', [])
        labels = config.get('labels', {})
        
        # 중복 타겟 검사
        for target in targets:
            if target in existing_targets:
                warnings.append(f"항목 {i+1}: 타겟 '{target}'이 기존 설정에 이미 존재합니다")
        
        # IP 중복 검사
        if labels.get('ip') in existing_ips:
            warnings.append(f"항목 {i+1}: IP '{labels.get('ip')}'가 기존 설정에 이미 존재합니다")
        
        # 서비스명 유사성 검사
        service = labels.get('service', '')
        similar_services = [s for s in existing_services if service and service.lower() in s.lower()]
        if similar_services:
            suggestions.append(f"항목 {i+1}: 유사한 서비스명이 존재합니다: {', '.join(similar_services)}")

def display_validation_results(issues, warnings, suggestions):
    """검증 결과 표시"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("오류", len(issues), delta=f"해결 필요" if issues else "없음")
    with col2:
        st.metric("경고", len(warnings), delta=f"검토 권장" if warnings else "없음")
    with col3:
        st.metric("제안", len(suggestions), delta=f"개선 가능" if suggestions else "완벽")
    
    if issues:
        st.error("❌ **오류 (해결 필요):**")
        for issue in issues:
            st.write(f"- {issue}")
    
    if warnings:
        st.warning("⚠️ **경고 (검토 권장):**")
        for warning in warnings:
            st.write(f"- {warning}")
    
    if suggestions:
        st.info("💡 **제안 (개선 가능):**")
        for suggestion in suggestions:
            st.write(f"- {suggestion}")
    
    if not issues and not warnings and not suggestions:
        st.success("🎉 **완벽한 설정입니다!** 오류, 경고, 개선사항이 없습니다.")

def show_existing_config_reference():
    """기존 설정 참조 정보 표시"""
    st.subheader("📚 기존 설정 참조")
    
    if not hasattr(st.session_state, 'prometheus_hosts'):
        st.warning("기존 설정 데이터가 없습니다. '호스트 관리' 탭에서 먼저 스캔해주세요.")
        return
    
    hosts_data = st.session_state.prometheus_hosts
    
    # 탭으로 정보 분류
    ref_tab1, ref_tab2, ref_tab3, ref_tab4 = st.tabs([
        "라벨 값", "포트 현황", "IP 대역", "서비스/그룹"
    ])
    
    with ref_tab1:
        st.write("**현재 사용 중인 라벨 값들:**")
        label_values = defaultdict(set)
        
        for host in hosts_data:
            labels = host.get('labels', {})
            for key, value in labels.items():
                if value and value != 'tobe':
                    label_values[key].add(str(value))
        
        for label, values in sorted(label_values.items()):
            with st.expander(f"{label} ({len(values)}개)"):
                for value in sorted(values):
                    st.code(f'"{label}": "{value}"')
    
    with ref_tab2:
        st.write("**포트 사용 현황:**")
        ports = []
        for host in hosts_data:
            target = host.get('target', '')
            if ':' in target:
                port = target.split(':')[-1]
                ports.append(port)
        
        port_counts = Counter(ports)
        port_df = pd.DataFrame([
            {"포트": port, "사용 횟수": count, "설명": get_port_description(port)}
            for port, count in port_counts.most_common()
        ])
        st.dataframe(port_df, use_container_width=True)
    
    with ref_tab3:
        st.write("**IP 대역 분포:**")
        ips = []
        for host in hosts_data:
            labels = host.get('labels', {})
            ip = labels.get('ip', '')
            if ip:
                ips.append(ip)
        
        # IP 대역별 그룹화
        subnets = defaultdict(list)
        for ip in ips:
            try:
                ip_obj = ipaddress.ip_address(ip)
                subnet = str(ipaddress.ip_network(f"{ip}/24", strict=False))
                subnets[subnet].append(ip)
            except:
                subnets['기타'].append(ip)
        
        for subnet, subnet_ips in subnets.items():
            with st.expander(f"{subnet} ({len(subnet_ips)}개)"):
                for ip in sorted(subnet_ips):
                    st.write(f"- {ip}")
    
    with ref_tab4:
        st.write("**서비스 및 그룹:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**서비스 목록:**")
            services = set()
            for host in hosts_data:
                labels = host.get('labels', {})
                service = labels.get('service', '')
                if service and service != 'tobe':
                    services.add(service)
            
            for service in sorted(services):
                st.code(f'"service": "{service}"')
        
        with col2:
            st.write("**그룹 목록:**")
            groups = set()
            for host in hosts_data:
                labels = host.get('labels', {})
                group = labels.get('group', '')
                if group and group != 'tobe':
                    groups.add(group)
            
            for group in sorted(groups):
                st.code(f'"group": "{group}"')

def get_port_description(port):
    """포트 설명 반환"""
    port_descriptions = {
        '9100': 'Node Exporter (시스템 메트릭)',
        '9104': 'MySQL Exporter',
        '9187': 'PostgreSQL Exporter', 
        '9121': 'Redis Exporter',
        '9113': 'Nginx Exporter',
        '9090': 'Prometheus Server',
        '3000': 'Grafana',
        '8080': 'HTTP 서비스',
        '443': 'HTTPS',
        '80': 'HTTP'
    }
    return port_descriptions.get(port, '커스텀 포트')

def show_prometheus_settings():
    """Prometheus 설정 화면"""
    st.subheader("Prometheus 설정")
    
    # 현재 설정된 정보 불러오기
    config_path = os.environ.get("PROMETHEUS_CONFIG_PATH", "")
    server1 = os.environ.get("PROMETHEUS_SERVER_1", "")
    server2 = os.environ.get("PROMETHEUS_SERVER_2", "")
    server3 = os.environ.get("PROMETHEUS_SERVER_3", "")
    
    # 설정 입력 폼
    with st.form("prometheus_settings_form"):
        st.write("### 설정 파일 경로")
        new_config_path = st.text_input("Prometheus 설정 파일 경로", value=config_path)
        
        st.write("### 서버 정보")
        new_server1 = st.text_input("서버 1 이름", value=server1)
        new_server2 = st.text_input("서버 2 이름", value=server2) 
        new_server3 = st.text_input("서버 3 이름", value=server3)
        
        # 저장 버튼
        submit_button = st.form_submit_button("설정 저장")
        
        if submit_button:
            # .env 파일 업데이트
            update_env_file({
                "PROMETHEUS_CONFIG_PATH": new_config_path,
                "PROMETHEUS_SERVER_1": new_server1,
                "PROMETHEUS_SERVER_2": new_server2,
                "PROMETHEUS_SERVER_3": new_server3
            })
            
            st.success("Prometheus 설정이 저장되었습니다.")
    
    # 경로 테스트
    if config_path:
        if st.button("경로 테스트"):
            if os.path.exists(config_path):
                st.success(f"✅ 경로가 존재합니다: {config_path}")
                # 하위 폴더 구조 미리보기
                try:
                    path_obj = Path(config_path)
                    json_files = list(path_obj.rglob("*.json"))
                    st.info(f"발견된 JSON 파일: {len(json_files)}개")
                    
                    if json_files:
                        st.write("**샘플 파일들:**")
                        for i, file in enumerate(json_files[:5]):
                            relative_path = file.relative_to(path_obj)
                            st.write(f"- {relative_path}")
                        
                        if len(json_files) > 5:
                            st.write(f"... 외 {len(json_files) - 5}개")
                except Exception as e:
                    st.error(f"폴더 탐색 오류: {e}")
            else:
                st.error(f"❌ 경로가 존재하지 않습니다: {config_path}")
    
    # 버전 정보
    with st.expander("모듈 버전 정보", expanded=False):
        repo_url = load_repo_url(MODULE_ID) or DEFAULT_REPO_URL
        
        with st.form("repo_url_form"):
            new_repo_url = st.text_input("저장소 URL", value=repo_url)
            submit = st.form_submit_button("저장")
            
            if submit and new_repo_url:
                if save_repo_url(MODULE_ID, new_repo_url):
                    st.success("저장소 URL이 저장되었습니다.")
                    repo_url = new_repo_url
        
        show_version_info(VERSION, repo_url)
    
    # JSON 검증 섹션 추가
    st.write("---")
    st.subheader("🔍 설정 검증")
    
    validation_method = st.radio(
        "검증 방법 선택:",
        ["JSON 붙여넣기", "파일 업로드"],
        horizontal=True
    )
    
    json_data = None
    
    if validation_method == "JSON 붙여넣기":
        st.write("**JSON 데이터를 붙여넣어주세요:**")
        json_text = st.text_area(
            "JSON 입력:",
            height=200,
            placeholder='[\n  {\n    "targets": ["192.168.1.100:9100"],\n    "labels": {\n      "service": "web-server",\n      "group": "production"\n    }\n  }\n]'
        )
        
        if json_text.strip():
            try:
                json_data = json.loads(json_text)
                st.success("✅ 유효한 JSON 형식입니다!")
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON 형식 오류: {str(e)}")
                json_data = None
    
    else:  # 파일 업로드
        uploaded_file = st.file_uploader(
            "JSON 파일을 업로드하세요:",
            type=['json'],
            help="prometheus 설정 JSON 파일을 선택해주세요"
        )
        
        if uploaded_file is not None:
            try:
                json_data = json.load(uploaded_file)
                st.success(f"✅ 파일 업로드 성공: {uploaded_file.name}")
            except json.JSONDecodeError as e:
                st.error(f"❌ 파일 읽기 오류: {str(e)}")
                json_data = None
            except Exception as e:
                st.error(f"❌ 파일 처리 오류: {str(e)}")
                json_data = None
    
    # JSON 데이터 분석 및 시각화
    if json_data is not None:
        analyze_uploaded_json(json_data)

def analyze_uploaded_json(json_data):
    """업로드된 JSON 데이터 분석 및 시각화"""
    try:
        st.subheader("📊 JSON 데이터 분석")
        
        # JSON 구조 확인 - 단일 객체인지 배열인지
        if isinstance(json_data, dict):
            if 'targets' in json_data and 'labels' in json_data:
                # 단일 객체
                json_list = [json_data]
            else:
                st.error("❌ 올바른 Prometheus 설정 형식이 아닙니다. 'targets'와 'labels' 필드가 필요합니다.")
                return
        elif isinstance(json_data, list):
            json_list = json_data
        else:
            st.error("❌ JSON 데이터는 객체 또는 배열이어야 합니다.")
            return
        
        # 기본 통계
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 타겟", len(json_list))
        with col2:
            total_hosts = sum(len(item.get('targets', [])) for item in json_list)
            st.metric("호스트 수", total_hosts)
        with col3:
            unique_services = set()
            for item in json_list:
                if 'labels' in item and 'service' in item['labels']:
                    unique_services.add(item['labels']['service'])
            st.metric("서비스 수", len(unique_services))
        
        # 데이터 테이블 표시
        st.subheader("📋 상세 데이터")
        
        table_data = []
        for i, item in enumerate(json_list):
            targets = item.get('targets', [])
            labels = item.get('labels', {})
            
            for target in targets:
                table_data.append({
                    '번호': i + 1,
                    '타겟': target,
                    '서비스': labels.get('service', 'N/A'),
                    '그룹': labels.get('group', 'N/A'),
                    'IP': labels.get('ip', 'N/A'),
                    'GID': labels.get('gid', 'N/A'),
                    'OS': labels.get('os', 'N/A'),
                    '용도': labels.get('purpose', 'N/A')
                })
        
        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
            
            # CSV 다운로드
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 CSV로 다운로드",
                data=csv,
                file_name=f"prometheus_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # 시각화
        if len(json_list) > 1:
            st.subheader("📈 시각화")
            
            # 서비스별 분포
            service_counts = defaultdict(int)
            group_counts = defaultdict(int)
            port_counts = defaultdict(int)
            
            for item in json_list:
                labels = item.get('labels', {})
                targets = item.get('targets', [])
                
                service = labels.get('service', 'unknown')
                group = labels.get('group', 'unknown')
                
                service_counts[service] += len(targets)
                group_counts[group] += len(targets)
                
                for target in targets:
                    if ':' in target:
                        port = target.split(':')[-1]
                        port_counts[port] += 1
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**서비스별 분포:**")
                if service_counts:
                    service_df = pd.DataFrame(list(service_counts.items()), columns=['Service', 'Count'])
                    service_df = service_df.sort_values('Count', ascending=False)
                    st.bar_chart(service_df.set_index('Service'))
            
            with col2:
                st.write("**그룹별 분포:**")
                if group_counts:
                    group_df = pd.DataFrame(list(group_counts.items()), columns=['Group', 'Count'])
                    group_df = group_df.sort_values('Count', ascending=False)
                    st.bar_chart(group_df.set_index('Group'))
            
            if port_counts:
                st.write("**포트별 분포:**")
                port_df = pd.DataFrame(list(port_counts.items()), columns=['Port', 'Count'])
                port_df = port_df.sort_values('Count', ascending=False)
                st.bar_chart(port_df.set_index('Port'))
        
        # 검증 결과
        st.subheader("✅ 검증 결과")
        
        validation_results = validate_json_config(json_list)
        
        if validation_results['errors']:
            st.error("❌ **오류 발견:**")
            for error in validation_results['errors']:
                st.write(f"- {error}")
        
        if validation_results['warnings']:
            st.warning("⚠️ **권장사항:**")
            for warning in validation_results['warnings']:
                st.write(f"- {warning}")
        
        if not validation_results['errors'] and not validation_results['warnings']:
            st.success("🎉 모든 검증을 통과했습니다!")
        
        # 최적화 제안
        if validation_results['suggestions']:
            st.info("💡 **최적화 제안:**")
            for suggestion in validation_results['suggestions']:
                st.write(f"- {suggestion}")
    
    except Exception as e:
        st.error(f"❌ JSON 분석 중 오류가 발생했습니다: {str(e)}")

def validate_json_config(json_list):
    """JSON 설정 검증"""
    errors = []
    warnings = []
    suggestions = []
    
    for i, item in enumerate(json_list):
        item_num = i + 1
        
        # 필수 필드 검사
        if 'targets' not in item:
            errors.append(f"항목 {item_num}: 'targets' 필드가 없습니다")
            continue
        
        if 'labels' not in item:
            warnings.append(f"항목 {item_num}: 'labels' 필드가 없습니다")
        
        # targets 검증
        targets = item.get('targets', [])
        if not targets:
            warnings.append(f"항목 {item_num}: targets가 비어있습니다")
        
        for j, target in enumerate(targets):
            if not isinstance(target, str):
                errors.append(f"항목 {item_num}, 타겟 {j+1}: 문자열이 아닙니다")
                continue
            
            if ':' not in target:
                warnings.append(f"항목 {item_num}, 타겟 {j+1}: 포트가 지정되지 않았습니다 ({target})")
            else:
                ip, port = target.rsplit(':', 1)
                
                # IP 주소 검증
                try:
                    ipaddress.ip_address(ip)
                except ValueError:
                    warnings.append(f"항목 {item_num}, 타겟 {j+1}: 올바르지 않은 IP 주소 ({ip})")
                
                # 포트 검증
                try:
                    port_num = int(port)
                    if port_num < 1 or port_num > 65535:
                        warnings.append(f"항목 {item_num}, 타겟 {j+1}: 올바르지 않은 포트 번호 ({port})")
                except ValueError:
                    warnings.append(f"항목 {item_num}, 타겟 {j+1}: 포트는 숫자여야 합니다 ({port})")
        
        # labels 검증
        labels = item.get('labels', {})
        if labels:
            required_labels = ['service', 'group', 'ip']
            for label in required_labels:
                if label not in labels:
                    warnings.append(f"항목 {item_num}: 권장 라벨 '{label}'이 없습니다")
            
            # 'tobe' 값 체크
            tobe_labels = [k for k, v in labels.items() if v == 'tobe']
            if tobe_labels:
                warnings.append(f"항목 {item_num}: 'tobe' 값을 가진 라벨들 ({', '.join(tobe_labels)})")
        
        # 최적화 제안
        if 'labels' in item and 'service' in item['labels']:
            service = item['labels']['service']
            if len(targets) > 1:
                suggestions.append(f"항목 {item_num}: {service} 서비스의 여러 타겟을 별도 항목으로 분리 고려")
    
    # 중복 타겟 체크
    all_targets = []
    for item in json_list:
        all_targets.extend(item.get('targets', []))
    
    duplicates = [target for target in set(all_targets) if all_targets.count(target) > 1]
    if duplicates:
        warnings.append(f"중복된 타겟들: {', '.join(duplicates)}")
    
    return {
        'errors': errors,
        'warnings': warnings, 
        'suggestions': suggestions
    }

def get_label_suggestions():
    """기존 호스트 데이터에서 라벨 제안값 추출"""
    suggestions = {
        'services': [],
        'groups': [],
        'os_types': [],
        'purposes': [],
        'gids': []
    }
    
    if hasattr(st.session_state, 'prometheus_hosts'):
        hosts_data = st.session_state.prometheus_hosts
        
        for host in hosts_data:
            labels = host.get('labels', {})
            
            service = labels.get('service', '').strip()
            if service and service not in suggestions['services']:
                suggestions['services'].append(service)
            
            group = labels.get('group', '').strip()
            if group and group not in suggestions['groups']:
                suggestions['groups'].append(group)
            
            os_val = labels.get('os', '').strip()
            if os_val and os_val not in suggestions['os_types']:
                suggestions['os_types'].append(os_val)
            
            purpose = labels.get('purpose', '').strip()
            if purpose and purpose not in suggestions['purposes']:
                suggestions['purposes'].append(purpose)
            
            gid = labels.get('gid', '').strip()
            if gid and gid not in suggestions['gids']:
                suggestions['gids'].append(gid)
        
        # 정렬
        for key in suggestions:
            suggestions[key] = sorted(suggestions[key])
    
    return suggestions

def generate_prometheus_config(target_ip, target_port, service, group, gid, purpose, os, custom_labels):
    """Prometheus 설정 JSON 생성"""
    try:
        # 타겟 구성
        target = f"{target_ip}:{target_port}"
        
        # 라벨 구성
        labels = {
            "service": service,
            "group": group,
            "ip": target_ip,
            "gid": gid or "tobe",
            "purpose": purpose or "tobe",
            "os": os or "tobe"
        }
        
        # 커스텀 라벨 추가
        if custom_labels:
            try:
                custom = json.loads(custom_labels)
                labels.update(custom)
            except json.JSONDecodeError:
                st.warning("커스텀 라벨 JSON 형식이 올바르지 않습니다. 기본 라벨만 사용합니다.")
        
        # 설정 객체 생성
        config = {
            "targets": [target],
            "labels": labels
        }
        
        return config
    
    except Exception as e:
        st.error(f"설정 생성 중 오류가 발생했습니다: {str(e)}")
        return None

def get_config_template(template_type):
    """템플릿 기반 설정 생성"""
    templates = {
        "Node Exporter (9100)": {
            "targets": ["192.168.1.100:9100"],
            "labels": {
                "service": "node-exporter",
                "group": "monitoring",
                "ip": "192.168.1.100",
                "gid": "node-001",
                "purpose": "시스템 모니터링",
                "os": "ubuntu-20.04"
            }
        },
        "MySQL Exporter (9104)": {
            "targets": ["192.168.1.101:9104"],
            "labels": {
                "service": "mysql-exporter",
                "group": "database",
                "ip": "192.168.1.101",
                "gid": "db-001",
                "purpose": "MySQL 모니터링",
                "os": "centos-7"
            }
        },
        "PostgreSQL Exporter (9187)": {
            "targets": ["192.168.1.102:9187"],
            "labels": {
                "service": "postgresql-exporter",
                "group": "database",
                "ip": "192.168.1.102",
                "gid": "db-002",
                "purpose": "PostgreSQL 모니터링",
                "os": "ubuntu-20.04"
            }
        },
        "Redis Exporter (9121)": {
            "targets": ["192.168.1.103:9121"],
            "labels": {
                "service": "redis-exporter",
                "group": "cache",
                "ip": "192.168.1.103",
                "gid": "cache-001",
                "purpose": "Redis 모니터링",
                "os": "alpine-3.14"
            }
        },
        "Nginx Exporter (9113)": {
            "targets": ["192.168.1.104:9113"],
            "labels": {
                "service": "nginx-exporter",
                "group": "web",
                "ip": "192.168.1.104",
                "gid": "web-001",
                "purpose": "웹서버 모니터링",
                "os": "debian-10"
            }
        },
        "Custom Port": {
            "targets": ["192.168.1.200:8080"],
            "labels": {
                "service": "custom-service",
                "group": "application",
                "ip": "192.168.1.200",
                "gid": "app-001",
                "purpose": "커스텀 애플리케이션",
                "os": "ubuntu-20.04"
            }
        }
    }
    
    return templates.get(template_type, templates["Node Exporter (9100)"])

def show_generated_config(config, identifier, context=""):
    """생성된 설정 표시"""
    st.success(f"✅ 설정이 생성되었습니다! ({identifier})")
    
    # JSON 미리보기
    st.subheader("📄 생성된 설정")
    config_json = json.dumps(config, indent=2, ensure_ascii=False)
    
    # 코드 블록으로 표시
    st.code(config_json, language="json")
    
    # 복사 가능한 텍스트 영역
    st.subheader("📋 복사용 설정")
    st.text_area("아래 내용을 복사하여 사용하세요:", config_json, height=200)
    
    # 배열 형태로도 표시
    array_config = json.dumps([config], indent=2, ensure_ascii=False)
    with st.expander("배열 형태 설정 (다중 타겟용)", expanded=False):
        st.code(array_config, language="json")
        st.text_area("배열 형태 복사용:", array_config, height=150, key="array_copy")
    
    # 설정 검증
    validate_config(config)
    
    # 저장 권장사항
    st.info("💡 **저장 권장사항**\n"
           f"- 파일 경로: `{get_suggested_file_path(config)}`\n"
           "- 서버별로 다른 폴더에 저장하세요\n"
           "- 파일명은 의미있는 이름으로 지정하세요")

def get_suggested_file_path(config):
    """권장 파일 경로 생성"""
    labels = config.get('labels', {})
    service = labels.get('service', 'unknown')
    group = labels.get('group', 'default')
    
    # exporter 타입 추정
    target = config.get('targets', [''])[0]
    port = target.split(':')[-1] if ':' in target else '9100'
    
    exporter_map = {
        '9100': 'node_exporter',
        '9104': 'mysql_exporter', 
        '9187': 'postgresql_exporter',
        '9121': 'redis_exporter',
        '9113': 'nginx_exporter'
    }
    
    exporter = exporter_map.get(port, 'custom_exporter')
    
    return f"{exporter}/{group}/{service}.json"

def validate_config(config):
    """설정 검증"""
    st.subheader("🔍 설정 검증")
    
    issues = []
    warnings = []
    
    # 필수 필드 검사
    if not config.get('targets'):
        issues.append("타겟이 정의되지 않았습니다")
    
    if not config.get('labels'):
        issues.append("라벨이 정의되지 않았습니다")
    
    # 타겟 형식 검사
    targets = config.get('targets', [])
    for target in targets:
        if ':' not in target:
            warnings.append(f"타겟에 포트가 명시되지 않았습니다: {target}")
        else:
            ip, port = target.rsplit(':', 1)
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                warnings.append(f"올바르지 않은 IP 주소: {ip}")
            
            if not port.isdigit():
                warnings.append(f"올바르지 않은 포트: {port}")
    
    # 라벨 검사
    labels = config.get('labels', {})
    required_labels = ['service', 'group', 'ip']
    
    for label in required_labels:
        if not labels.get(label):
            warnings.append(f"필수 라벨이 누락되었습니다: {label}")
    
    # tobe 값 검사
    tobe_labels = [k for k, v in labels.items() if v == 'tobe']
    if tobe_labels:
        warnings.append(f"'tobe' 값을 가진 라벨들: {', '.join(tobe_labels)}")
    
    # 결과 표시
    if not issues and not warnings:
        st.success("✅ 설정이 올바릅니다!")
    else:
        if issues:
            st.error("❌ 오류:")
            for issue in issues:
                st.write(f"- {issue}")
        
        if warnings:
            st.warning("⚠️ 권장사항:")
            for warning in warnings:
                st.write(f"- {warning}")

def check_server_status(server_name, server_id):
    """실제 서버 상태 확인"""
    if not server_name or server_name.strip() == "":
        st.error("❌ 서버 주소가 설정되지 않았습니다.")
        st.warning("💡 'Prometheus 설정' 탭에서 서버 주소를 설정해주세요.")
        return
    
    st.write("🔄 서버 상태를 확인하는 중...")
    
    # 기본 형식 검증
    if not (server_name.startswith('http://') or server_name.startswith('https://')):
        st.error("❌ 올바른 URL 형식이 아닙니다. (http:// 또는 https://로 시작해야 함)")
        return
    
    try:
        import urllib3
        import requests
        from requests.exceptions import ConnectionError, Timeout, RequestException
        import urllib3.exceptions
        
        # SSL 경고 무시 (내부 서버인 경우)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 헬스체크 엔드포인트들
        health_endpoints = [
            f"{server_name.rstrip('/')}/api/v1/query?query=up",  # Prometheus 메트릭 쿼리
            f"{server_name.rstrip('/')}/metrics",  # Prometheus 자체 메트릭
            f"{server_name.rstrip('/')}/api/v1/status/buildinfo",  # 빌드 정보
            f"{server_name.rstrip('/')}/",  # 루트 페이지
        ]
        
        session = requests.Session()
        session.verify = False  # SSL 검증 비활성화 (내부 서버)
        
        success = False
        error_msg = ""
        
        for i, endpoint in enumerate(health_endpoints):
            try:
                response = session.get(endpoint, timeout=5)
                
                if response.status_code == 200:
                    success = True
                    
                    # 응답 내용에 따른 추가 정보
                    if 'prometheus' in response.text.lower() or 'query' in endpoint:
                        st.success("✅ Prometheus 서버 정상 - API 응답 확인됨")
                        
                        # 간단한 서버 정보 표시
                        if 'buildinfo' in endpoint:
                            try:
                                build_info = response.json()
                                if 'data' in build_info:
                                    st.info(f"📊 버전: {build_info['data'].get('version', 'N/A')}")
                            except:
                                pass
                        break
                    else:
                        st.success("✅ 서버 응답 정상")
                        break
                        
            except (ConnectionError, urllib3.exceptions.NewConnectionError):
                error_msg = f"연결 실패: {server_name}에 연결할 수 없습니다."
            except Timeout:
                error_msg = f"타임아웃: 서버 응답 시간이 너무 깁니다."
            except RequestException as e:
                error_msg = f"요청 오류: {str(e)}"
            except Exception as e:
                error_msg = f"알 수 없는 오류: {str(e)}"
        
        if not success:
            st.error(f"❌ 서버 연결 실패")
            st.warning(f"⚠️ {error_msg}")
            
            # troubleshooting 제안
            with st.expander("🔧 문제 해결 방법", expanded=False):
                st.write("""
                **가능한 원인:**
                - 서버가 실행되지 않음
                - 네트워크 연결 문제  
                - 방화벽 차단
                - 잘못된 URL 또는 포트
                
                **확인 방법:**
                1. 서버가 실행 중인지 확인
                2. URL이 정확한지 확인 (예: http://192.168.1.100:9090)
                3. 네트워크 연결 상태 확인
                4. 방화벽 설정 확인
                """)
        
    except ImportError:
        st.error("❌ requests 라이브러리가 설치되지 않았습니다.")
        st.code("pip install requests", language="bash")
    except Exception as e:
        st.error(f"❌ 서버 상태 확인 중 오류 발생: {str(e)}")

def create_deployment_files(selected_files, hosts_by_file):
    """로컬에 배포용 설정 파일들 생성"""
    try:
        deployment_dir = Path("prometheus_deployment")
        deployment_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        created_files = []
        
        for file_path in selected_files:
            hosts = hosts_by_file[file_path]
            
            # 파일별로 설정 생성
            config_list = []
            for host in hosts:
                config = {
                    "targets": [host.get('target', '')],
                    "labels": host.get('labels', {})
                }
                config_list.append(config)
            
            # 파일 저장
            file_name = f"{Path(file_path).stem}_{timestamp}.json"
            output_path = deployment_dir / file_name
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config_list, f, indent=2, ensure_ascii=False)
            
            created_files.append(str(output_path))
        
        # 배포 기록 추가
        record = {
            "시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "작업": "로컬 파일 생성",
            "대상": "로컬",
            "파일 수": len(created_files),
            "상태": "완료"
        }
        
        if 'deployment_history' not in st.session_state:
            st.session_state.deployment_history = []
        
        st.session_state.deployment_history.append(record)
        
        st.success(f"✅ {len(created_files)}개 파일이 생성되었습니다!")
        st.info(f"📁 저장 경로: `{deployment_dir.absolute()}`")
        
        with st.expander("생성된 파일 목록", expanded=True):
            for file in created_files:
                st.write(f"- {file}")
    
    except Exception as e:
        st.error(f"파일 생성 중 오류가 발생했습니다: {str(e)}")

def deploy_to_servers(selected_files, hosts_by_file, target_servers):
    """서버에 설정 배포 (시뮬레이션)"""
    st.write("🚀 **배포를 시작합니다...**")
    
    # 진행 상황 표시
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_operations = len(selected_files) * len(target_servers)
    current_operation = 0
    
    deployment_results = []
    
    for file_path in selected_files:
        hosts = hosts_by_file[file_path]
        
        # 설정 준비
        config_list = []
        for host in hosts:
            config = {
                "targets": [host.get('target', '')],
                "labels": host.get('labels', {})
            }
            config_list.append(config)
        
        for server in target_servers:
            current_operation += 1
            progress = current_operation / total_operations
            progress_bar.progress(progress)
            
            status_text.text(f"배포 중: {server['name']} - {Path(file_path).name}")
            
            # 실제로는 여기서 서버 배포 작업 수행
            # 현재는 시뮬레이션으로 처리
            import time
            time.sleep(0.5)  # 배포 시간 시뮬레이션
            
            # 랜덤하게 성공/실패 결정 (실제로는 실제 배포 결과)
            import random
            success = random.random() > 0.1  # 90% 성공률
            
            result = {
                "파일": Path(file_path).name,
                "서버": server['name'],
                "호스트 수": len(hosts),
                "상태": "성공" if success else "실패",
                "시간": datetime.now().strftime("%H:%M:%S")
            }
            deployment_results.append(result)
    
    progress_bar.progress(1.0)
    status_text.text("배포 완료!")
    
    # 결과 표시
    st.subheader("📊 배포 결과")
    
    success_count = sum(1 for r in deployment_results if r['상태'] == '성공')
    total_count = len(deployment_results)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 작업", total_count)
    with col2:
        st.metric("성공", success_count, delta=f"{success_count/total_count*100:.1f}%")
    with col3:
        st.metric("실패", total_count - success_count)
    
    # 상세 결과
    results_df = pd.DataFrame(deployment_results)
    st.dataframe(results_df, use_container_width=True)
    
    # 배포 기록 추가
    record = {
        "시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "작업": f"서버 배포 ({len(target_servers)}대)",
        "대상": ", ".join([s['name'] for s in target_servers]),
        "파일 수": len(selected_files),
        "상태": f"{success_count}/{total_count} 성공"
    }
    
    if 'deployment_history' not in st.session_state:
        st.session_state.deployment_history = []
    
    st.session_state.deployment_history.append(record)
    
    if success_count == total_count:
        st.success("🎉 모든 배포가 성공적으로 완료되었습니다!")
    else:
        st.warning(f"⚠️ {total_count - success_count}개 작업이 실패했습니다. 로그를 확인해주세요.")

def update_env_file(new_values):
    """환경 변수 파일 업데이트"""
    env_path = ".env"
    env_vars = new_values.copy()
    
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        with open(env_path, "w") as f:
            updated_keys = set()

            for line in lines:
                line = line.rstrip("\n")

                if not line or line.startswith("#"):
                    f.write(f"{line}\n")
                    continue
                
                try:
                    key, original_value = line.split("=", 1)
                    key = key.strip()

                    if key in new_values:
                        f.write(f"{key}={new_values[key]}\n")
                        updated_keys.add(key)
                    else:
                        f.write(f"{key}={original_value}\n")
                except ValueError:
                    f.write(f"{line}\n")
            
            for key, value in new_values.items():
                if key not in updated_keys:
                    f.write(f"{key}={value}\n")
    else:
        with open(env_path, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")