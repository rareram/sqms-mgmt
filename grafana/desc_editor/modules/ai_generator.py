

import json

class AIGenerator:
    """AI 기반 Grafana 패널 설명 생성기"""

    def __init__(self):
        # 향후 모델 설정 등을 위해 초기화 메서드를 둡니다.
        pass

    def _analyze_panel_data(self, panel_data: dict) -> str:
        """패널 데이터를 분석하여 AI 프롬프트에 사용할 핵심 정보를 추출합니다."""
        
        analysis = []
        
        title = panel_data.get('title', 'N/A')
        analysis.append(f"- 패널 제목: {title}")

        panel_type = panel_data.get('type', 'N/A')
        analysis.append(f"- 패널 타입: {panel_type}")

        datasource = panel_data.get('datasource')
        if datasource:
            if isinstance(datasource, dict):
                analysis.append(f"- 데이터소스: {datasource.get('type', 'N/A')} (UID: {datasource.get('uid')})")
            else:
                analysis.append(f"- 데이터소스: {datasource}")

        if 'targets' in panel_data and panel_data['targets']:
            queries = [q.get('expr', '쿼리 없음') for q in panel_data['targets']]
            analysis.append("- 쿼리:")
            for i, query in enumerate(queries):
                analysis.append(f"  - Query {i+1}: {query}")

        if 'alert' in panel_data and panel_data['alert']:
            alert_conditions = panel_data['alert'].get('conditions', [])
            conditions_str = json.dumps(alert_conditions, ensure_ascii=False, indent=2)
            analysis.append(f"- 알림 조건: {conditions_str}")

        if 'thresholds' in panel_data and panel_data['thresholds']:
            thresholds_str = json.dumps(panel_data['thresholds'], ensure_ascii=False)
            analysis.append(f"- 임계값(Thresholds): {thresholds_str}")
            
        return "\n".join(analysis)

    def generate_description(self, panel_data: dict) -> str:
        """
        패널 데이터를 기반으로 풍선도움말(Description)을 생성합니다.
        실제 LLM API를 호출하는 대신, 규칙 기반으로 샘플과 유사한 설명을 생성합니다.
        """
        if not panel_data or panel_data.get('type') == 'text':
            return ""

        analysis_report = self._analyze_panel_data(panel_data)

        title = panel_data.get('title', '')
        queries = [q.get('expr', '').lower() for q in panel_data.get('targets', [])]
        query_str = " ".join(queries)

        description = ""
        action_guide = ""

        # Specific interpretations for common titles
        if "cpu iowait" in title.lower():
            description = "CPU가 디스크 입출력(I/O) 작업을 기다리는 시간의 비율을 나타냅니다. 이 수치가 높으면 디스크 병목 현상이나 I/O 집약적인 애플리케이션으로 인한 성능 저하를 의심할 수 있습니다."
            action_guide = "<li>조치가이드: I/O 대기 시간이 높으면 디스크 성능 최적화, I/O 부하 분산, 또는 스토리지 시스템 점검을 고려해야 합니다.</li>"
        elif "uptime" in title.lower():
            description = "시스템이 재부팅 없이 연속적으로 작동한 시간을 보여줍니다. 시스템의 안정성과 가용성을 나타내는 지표입니다."
            action_guide = "<li>조치가이드: 예상치 못한 짧은 가동 시간은 시스템 불안정성이나 잦은 재부팅의 원인을 분석해야 함을 의미합니다.</li>"
        elif "disk r/w data" in title.lower():
            description = "디스크의 읽기/쓰기 처리량(데이터 전송률)을 모니터링합니다. 디스크 성능의 핵심 지표로, 데이터베이스나 파일 시스템의 부하를 파악하는 데 중요합니다."
            action_guide = "<li>조치가이드: 과도한 읽기/쓰기 작업은 디스크 병목 현상을 유발할 수 있으므로, 쿼리 최적화, 캐싱 전략 개선, 또는 고성능 디스크로의 교체를 고려해야 합니다.</li>"
        elif "network sockstat" in title.lower():
            description = "네트워크 소켓 통계 정보를 보여줍니다. 현재 시스템의 네트워크 연결 상태, 사용 중인 소켓 수 등을 파악하여 네트워크 관련 문제를 진단하는 데 활용됩니다."
            action_guide = "<li>조치가이드: 비정상적으로 높은 소켓 사용량은 애플리케이션의 연결 누수나 네트워크 공격을 의심할 수 있으므로, 관련 프로세스 및 네트워크 로그를 점검해야 합니다.</li>"
        elif "cpu usage" in title.lower() or "cpu used%" in title.lower():
            description = "시스템의 CPU 사용률을 보여줍니다. CPU는 시스템의 연산 능력을 나타내는 핵심 자원으로, 높은 사용률은 과부하를 의미할 수 있습니다."
            action_guide = "<li>조치가이드: CPU 사용률이 지속적으로 높으면, 프로세스 최적화, 불필요한 서비스 중단, 또는 시스템 리소스 증설을 검토해야 합니다.</li>"
        elif "memory used%" in title.lower() or "total memory" in title.lower():
            description = "메모리(RAM) 사용량 추이를 나타냅니다. 메모리 부족은 디스크 스왑(SWAP)을 유발하여 시스템 전체의 응답 속도를 저하시킬 수 있습니다."
            action_guide = "<li>조치가이드: 사용량이 지속적으로 80% 이상이면 애플리케이션의 메모리 누수 점검 또는 증설을 고려해야 합니다.</li>"
        elif "disk space used%" in title.lower() or "total disk" in title.lower():
            description = "디스크의 사용률을 보여줍니다. 디스크 공간 부족은 시스템 오류나 서비스 중단을 초래할 수 있으므로 지속적인 모니터링이 필요합니다."
            action_guide = "<li>조치가이드: 디스크 사용률이 임계치를 초과하면 불필요한 파일 삭제, 로그 관리, 또는 디스크 증설을 고려해야 합니다.</li>"
        elif "network traffic" in title.lower() or "network bandwidth" in title.lower():
            description = "네트워크 트래픽(In/Out)을 모니터링합니다. 갑작스러운 트래픽 증가는 외부 공격 또는 내부 시스템의 비정상적인 동작을 의미할 수 있습니다."
            action_guide = "<li>조치가이드: 비정상적인 네트워크 트래픽 패턴이 감지되면, 방화벽 로그 및 시스템 접근 로그를 분석하여 원인을 파악해야 합니다.</li>"
        elif "system load" in title.lower():
            description = "시스템의 평균 부하(Load Average)를 나타냅니다. 시스템이 처리해야 할 작업량과 대기 중인 작업의 수를 종합적으로 보여주는 지표입니다."
            action_guide = "<li>조치가이드: 시스템 부하가 CPU 코어 수보다 지속적으로 높으면, 시스템 리소스 부족이나 특정 프로세스의 과부하를 의심하고 원인을 분석해야 합니다.</li>"
        elif "tcp established" in title.lower():
            description = "현재 시스템의 TCP Established 상태 연결 수를 보여줍니다. 활성화된 네트워크 연결의 수를 파악하여 서비스의 가용성 및 네트워크 부하를 모니터링합니다."
            action_guide = "<li>조치가이드: 비정상적으로 높은 Established 연결 수는 서비스 과부하, 연결 누수, 또는 외부 공격을 의미할 수 있으므로, 관련 애플리케이션 및 네트워크 설정을 점검해야 합니다.</li>"
        elif "free inodes" in title.lower():
            description = "파일 시스템의 사용 가능한 Inode 수를 보여줍니다. Inode는 파일 및 디렉터리 메타데이터를 저장하는 구조로, Inode 부족은 디스크 공간이 남아있어도 파일을 생성할 수 없게 만듭니다."
            action_guide = "<li>조치가이드: Inode 부족은 작은 파일이 대량으로 생성되는 경우 발생할 수 있으므로, 불필요한 파일 삭제 또는 파일 시스템 구조 개선을 고려해야 합니다.</li>"
        elif "total ram" in title.lower():
            description = "시스템의 총 물리 메모리(RAM) 용량을 보여줍니다. 시스템의 전체 메모리 자원 규모를 파악하는 데 사용됩니다."
            action_guide = "<li>조치가이드: 이 패널은 주로 정보 제공용이며, 메모리 부족 문제는 'Memory Used%' 패널에서 확인해야 합니다.</li>"
        elif "total filefd" in title.lower():
            description = "시스템에서 현재 열려 있는 파일 디스크립터(File Descriptor)의 총 개수를 보여줍니다. 파일 디스크립터는 프로세스가 파일이나 소켓에 접근할 때 사용하는 식별자입니다."
            action_guide = "<li>조치가이드: 파일 디스크립터 수가 시스템 제한에 근접하면 'Too many open files' 오류가 발생할 수 있으므로, 애플리케이션의 파일 핸들링 로직을 점검하거나 시스템 제한을 늘려야 합니다.</li>"
        elif "disk iops completed" in title.lower():
            description = "디스크의 초당 입출력 작업 수(IOPS)를 보여줍니다. 디스크 성능의 중요한 지표로, 스토리지 시스템의 처리 능력을 파악하는 데 사용됩니다."
            action_guide = "<li>조치가이드: IOPS가 지속적으로 높거나 급증하면 디스크 병목 현상을 의심하고, I/O 집약적인 프로세스를 최적화하거나 스토리지 성능을 개선해야 합니다.</li>"
        elif "time spent doing i/os" in title.lower():
            description = "디스크 입출력(I/O) 작업에 소요된 시간의 비율을 보여줍니다. 이 수치가 높으면 디스크가 I/O 요청을 처리하느라 바쁘다는 의미이며, 디스크 성능 저하의 원인이 될 수 있습니다."
            action_guide = "<li>조치가이드: I/O 소요 시간이 높으면 디스크 병목 현상, 느린 스토리지 응답 시간, 또는 I/O 부하가 높은 애플리케이션을 점검해야 합니다.</li>"
        elif "disk r/w time" in title.lower():
            description = "디스크 읽기/쓰기 작업에 걸리는 평균 시간을 보여줍니다. 이 시간이 길어지면 디스크 응답 속도가 느려져 시스템 전반의 성능에 영향을 미칩니다."
            action_guide = "<li>조치가이드: 디스크 응답 시간이 100ms 이상으로 지속되면 스토리지 시스템의 문제, 디스크 불량, 또는 과도한 I/O 부하를 의심하고 점검해야 합니다.</li>"
        elif "open file descriptor" in title.lower() or "context switches" in title.lower():
            description = "시스템의 열린 파일 디스크립터 수와 컨텍스트 스위치 수를 보여줍니다. 열린 파일 디스크립터는 프로세스가 사용하는 자원 수를, 컨텍스트 스위치는 CPU가 프로세스 간 전환하는 빈도를 나타냅니다."
            action_guide = "<li>조치가이드: 두 지표 모두 비정상적으로 높으면 시스템 자원 부족, 애플리케이션의 비효율적인 자원 사용, 또는 과도한 프로세스 생성/종료를 의심하고 분석해야 합니다.</li>"
        elif "linux server" in title.lower() and "total" in title.lower():
            description = "리눅스 서버의 전반적인 상태를 요약하여 보여줍니다. 시스템의 가용성, 주요 자원 사용량 등을 한눈에 파악할 수 있습니다."
            action_guide = "<li>조치가이드: 이 패널은 개요를 제공하므로, 특정 지표에 이상이 감지되면 관련 상세 패널을 확인하여 원인을 분석해야 합니다.</li>"
        elif "overall total 5m load" in title.lower() or "average cpu used%" in title.lower():
            description = "시스템의 5분 평균 부하(Load Average)와 평균 CPU 사용률을 보여줍니다. 시스템의 전반적인 성능 부하와 CPU 자원 활용도를 파악하는 데 사용됩니다."
            action_guide = "<li>조치가이드: 부하 평균이 CPU 코어 수보다 높거나 CPU 사용률이 지속적으로 높으면, 프로세스 최적화, 불필요한 서비스 중단, 또는 시스템 리소스 증설을 검토해야 합니다.</li>"
        elif "overall total memory" in title.lower() or "average memory used%" in title.lower():
            description = "시스템의 총 메모리 용량과 평균 메모리 사용률을 보여줍니다. 메모리 자원의 전반적인 상태와 활용도를 파악하는 데 사용됩니다."
            action_guide = "<li>조치가이드: 메모리 사용률이 지속적으로 80% 이상이면 애플리케이션의 메모리 누수 점검 또는 증설을 고려해야 합니다.</li>"
        elif "overall total disk" in title.lower() or "average disk used%" in title.lower():
            description = "시스템의 총 디스크 공간과 평균 디스크 사용률을 보여줍니다. 디스크 자원의 전반적인 상태와 활용도를 파악하는 데 사용됩니다."
            action_guide = "<li>조치가이드: 디스크 사용률이 임계치를 초과하면 불필요한 파일 삭제, 로그 관리, 또는 디스크 증설을 고려해야 합니다.</li>"
        elif "internet traffic per hour" in title.lower():
            description = "시간당 인터넷 트래픽(In/Out)을 모니터링합니다. 네트워크 대역폭 사용량과 트래픽 패턴을 파악하여 네트워크 부하 및 이상 징후를 감지하는 데 활용됩니다."
            action_guide = "<li>조치가이드: 비정상적인 트래픽 증가는 외부 공격, 서비스 오용, 또는 네트워크 장비의 문제를 의미할 수 있으므로, 관련 로그 및 네트워크 구성을 점검해야 합니다.</li>"
        elif "cpu cores" in title.lower():
            description = "시스템의 CPU 코어 수를 보여줍니다. 시스템의 병렬 처리 능력을 나타내는 지표입니다."
            action_guide = "<li>조치가이드: 이 패널은 주로 정보 제공용이며, CPU 성능 문제는 'CPU Usage' 또는 'System Load' 패널에서 확인해야 합니다.</li>"
        elif "network bandwidth usage per second" in title.lower():
            description = "초당 네트워크 대역폭 사용량(In/Out)을 모니터링합니다. 실시간 네트워크 트래픽을 파악하여 병목 현상이나 과부하를 감지하는 데 활용됩니다."
            action_guide = "<li>조치가이드: 네트워크 대역폭 사용량이 지속적으로 높으면 네트워크 장비의 성능 한계, 서비스 과부하, 또는 비정상적인 트래픽 발생을 의심하고 점검해야 합니다.</li>"
        else:
            # Fallback for general cases based on query keywords
            if 'cpu' in query_str:
                description = "시스템의 CPU 사용률과 관련된 핵심 지표를 보여줍니다. CPU는 시스템의 연산 능력을 나타내는 핵심 자원으로, 높은 사용률은 과부하를 의미할 수 있습니다."
                action_guide = "<li>조치가이드: CPU 사용률이 지속적으로 높으면, 프로세스 최적화, 불필요한 서비스 중단, 또는 시스템 리소스 증설을 검토해야 합니다.</li>"
            elif 'memory' in query_str:
                description = "메모리(RAM) 사용량 추이를 나타냅니다. 메모리 부족은 디스크 스왑(SWAP)을 유발하여 시스템 전체의 응답 속도를 저하시킬 수 있습니다."
                action_guide = "<li>조치가이드: 사용량이 지속적으로 80% 이상이면 애플리케이션의 메모리 누수 점검 또는 증설을 고려해야 합니다.</li>"
            elif 'disk' in query_str or 'filesystem' in query_str:
                description = "디스크의 사용량 또는 I/O 처리량을 보여줍니다. 디스크 성능은 데이터베이스 및 애플리케이션 응답 시간에 직접적인 영향을 줍니다."
                action_guide = "<li>조치가이드: 디스크 I/O 병목 현상 발생 시, 쿼리 튜닝, 인덱싱 최적화 또는 고성능 디스크로의 교체를 고려해야 합니다.</li>"
            elif 'network' in query_str:
                description = "네트워크 트래픽(In/Out)을 모니터링합니다. 갑작스러운 트래픽 증가는 외부 공격 또는 내부 시스템의 비정상적인 동작을 의미할 수 있습니다."
                action_guide = "<li>조치가이드: 비정상적인 네트워크 트래픽 패턴이 감지되면, 방화벽 로그 및 시스템 접근 로그를 분석하여 원인을 파악해야 합니다.</li>"
            else:
                description = f"이 패널은 '{title}'에 대한 정보를 시각화합니다. {panel_data.get('type', '알 수 없는')} 타입으로, {panel_data.get('datasource', '알 수 없는')} 데이터소스에서 데이터를 가져옵니다."
                action_guide = "<li>조치가이드: 데이터의 추이를 지속적으로 관찰하고, 이상 패턴 발생 시 관련 시스템의 로그 및 상태를 점검해야 합니다.</li>"

        # Add alert condition if present
        if 'alert' in panel_data and panel_data['alert']:
            description += " 설정된 임계값을 초과하면 알림이 발생하도록 구성되어 있습니다."

        final_description = f"{description}<ul>{action_guide}</ul>"

        return final_description

# 사용 예시:
if __name__ == '__main__':
    # 테스트용 샘플 패널 데이터
    sample_panel = {
        "id": 1,
        "title": "CPU Usage",
        "type": "timeseries",
        "datasource": {"type": "prometheus", "uid": "prom-123"},
        "targets": [
            {
                "expr": "100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
            }
        ],
        "alert": {
            "conditions": [
                {
                    "evaluator": {"params": [80, 90], "type": "gt"},
                    "operator": {"type": "and"},
                    "query": {"params": ["A", "5m", "now"]},
                    "reducer": {"params": [], "type": "avg"},
                    "type": "query"
                }
            ]
        }
    }
    
    generator = AIGenerator()
    generated_desc = generator.generate_description(sample_panel)
    
    print("--- 생성된 설명 ---")
    print(generated_desc)
    
    print("\n--- 분석 리포트 (AI 프롬프트용) ---")
    print(generator._analyze_panel_data(sample_panel))

