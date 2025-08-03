#!/usr/bin/env python3
"""
Node Exporter 패널 Description 자동 생성 스크립트
"""

import json
import datetime

def generate_description(panel_title, panel_type, detailed_info=None):
    """패널 제목과 타입을 기반으로 Description 생성"""
    
    descriptions = {
        'CPU': '리눅스 시스템의 CPU 사용률 추이를 상세히 모니터링합니다. <u>시스템 성능의 핵심지표</u>로 user, system, iowait, idle 등 각 모드별 CPU 시간을 보여줍니다. CPU 사용률이 지속적으로 `80%` 이상이면 응답 속도 저하가 발생할 수 있습니다.<ul><li>조치가이드: 높은 CPU 사용률이 지속되면 프로세스 최적화, 작업 부하 분산 또는 하드웨어 업그레이드를 검토해야 합니다.</li></ul>',
        
        'Memory Stack': '리눅스 시스템의 메모리 사용량을 영역별로 상세히 보여줍니다. <u>메모리 관리의 핵심지표</u>로 실제 사용 메모리, 캐시, 버퍼, Slab 등의 분포를 확인할 수 있습니다. 실제 사용 메모리가 `85%` 이상이면 시스템 성능 저하가 발생할 수 있습니다.<ul><li>조치가이드: 메모리 부족이 지속되면 불필요한 프로세스 정리, 메모리 누수 점검 또는 메모리 증설을 검토해야 합니다.</li></ul>',
        
        'Network Traffic': '리눅스 시스템의 네트워크 인터페이스별 트래픽량을 실시간으로 모니터링합니다. <u>네트워크 성능의 핵심지표</u>로 inbound/outbound 트래픽을 bps 단위로 보여줍니다. 네트워크 대역폭 사용률이 `80%` 이상이면 네트워크 병목이 발생할 수 있습니다.<ul><li>조치가이드: 네트워크 포화 상태가 지속되면 네트워크 대역폭 확장, 로드 밸런싱 또는 트래픽 최적화를 검토해야 합니다.</li></ul>',
        
        'Disk Space Used': '리눅스 시스템의 파일시스템별 디스크 사용량을 모니터링합니다. <u>스토리지 관리의 핵심지표</u>로 각 마운트 포인트별 실제 사용량을 바이트 단위로 보여줍니다. 디스크 사용률이 `85%` 이상이면 시스템 안정성에 위험할 수 있습니다.<ul><li>조치가이드: 디스크 사용률이 높으면 불필요한 파일 정리, 로그 순환 설정 또는 디스크 확장을 검토해야 합니다.</li></ul>',
        
        'Disk IOps': '리눅스 시스템의 디스크 I/O 작업 수를 실시간으로 모니터링합니다. <u>디스크 성능의 핵심지표</u>로 읽기/쓰기 IOPS를 초당 단위로 보여줍니다. IOPS가 디스크 성능 한계의 `80%` 이상이면 I/O 대기시간이 증가할 수 있습니다.<ul><li>조치가이드: 높은 IOPS가 지속되면 디스크 I/O 최적화, SSD 업그레이드 또는 스토리지 분산을 검토해야 합니다.</li></ul>',
        
        'I/O Usage Read / Write': '리눅스 시스템의 디스크 I/O 처리량을 모니터링합니다. <u>스토리지 처리량의 핵심지표</u>로 읽기/쓰기 바이트를 초당 단위로 보여줍니다. I/O 처리량이 디스크 대역폭의 `80%` 이상이면 I/O 병목이 발생할 수 있습니다.<ul><li>조치가이드: I/O 처리량 포화가 지속되면 고성능 스토리지 도입, I/O 패턴 최적화 또는 캐싱 전략을 검토해야 합니다.</li></ul>',
        
        'I/O Utilization': '리눅스 시스템의 디스크 활용률을 모니터링합니다. <u>디스크 활용도의 핵심지표</u>로 디스크가 I/O 작업을 수행하는 시간 비율을 백분율로 보여줍니다. 디스크 활용률이 지속적으로 `90%` 이상이면 심각한 I/O 병목이 발생합니다.<ul><li>조치가이드: 디스크 활용률이 높으면 I/O 작업 최적화, 고성능 디스크 도입 또는 워크로드 분산을 검토해야 합니다.</li></ul>',
        
        'CPU spent seconds in guests (VMs)': '리눅스 호스트에서 가상머신(게스트)을 위해 소비된 CPU 시간을 모니터링합니다. <u>가상화 성능의 핵심지표</u>로 게스트 VM이 사용하는 CPU 비율을 보여줍니다. 게스트 CPU 사용률이 `70%` 이상이면 호스트 성능에 영향을 줄 수 있습니다.<ul><li>조치가이드: 게스트 CPU 사용률이 높으면 VM 리소스 재할당, 워크로드 분산 또는 호스트 리소스 확장을 검토해야 합니다.</li></ul>',
        
        'Memory Active / Inactive': '리눅스 시스템의 메모리 활성/비활성 상태를 모니터링합니다. <u>메모리 효율성의 핵심지표</u>로 활발히 사용되는 메모리와 비활성 메모리의 분포를 보여줍니다. 활성 메모리 비율이 `90%` 이상이면 메모리 압박 상태입니다.<ul><li>조치가이드: 활성 메모리 비율이 높으면 메모리 사용 패턴 분석, 캐시 설정 최적화 또는 메모리 증설을 검토해야 합니다.</li></ul>',
        
        'Memory Committed': '리눅스 시스템의 커밋된 메모리와 커밋 한계를 모니터링합니다. <u>메모리 오버커밋의 핵심지표</u>로 시스템이 할당 약속한 메모리 총량을 보여줍니다. 커밋 비율이 `90%` 이상이면 메모리 오버커밋 위험이 있습니다.<ul><li>조치가이드: 높은 메모리 커밋이 지속되면 오버커밋 설정 조정, 메모리 사용량 최적화 또는 메모리 확장을 검토해야 합니다.</li></ul>',
        
        'Memory Active / Inactive Detail': '리눅스 시스템의 활성/비활성 메모리를 파일/익명 메모리로 상세 분류하여 모니터링합니다. <u>메모리 분류의 핵심지표</u>로 캐시와 실제 프로세스 메모리를 구분합니다. 익명 메모리 비율이 `80%` 이상이면 메모리 압박이 심각합니다.<ul><li>조치가이드: 익명 메모리가 많으면 프로세스 메모리 사용량 최적화, 메모리 누수 점검 또는 메모리 확장을 검토해야 합니다.</li></ul>',
        
        'Memory Writeback and Dirty': '리눅스 시스템의 더티(수정됨) 메모리와 라이트백(디스크 쓰기 대기) 메모리를 모니터링합니다. <u>디스크 쓰기 성능의 핵심지표</u>로 메모리에서 디스크로 쓰이기 대기중인 데이터량을 보여줍니다. 더티 메모리가 `200MB` 이상이면 디스크 I/O 지연이 발생할 수 있습니다.<ul><li>조치가이드: 더티 메모리가 많으면 디스크 I/O 성능 개선, 라이트백 설정 조정 또는 스토리지 성능 향상을 검토해야 합니다.</li></ul>',
        
        'Memory Shared and Mapped': '리눅스 시스템의 공유 메모리와 메모리 맵 파일 사용량을 모니터링합니다. <u>메모리 공유의 핵심지표</u>로 프로세스 간 공유되는 메모리 영역을 보여줍니다. 공유 메모리가 급증하면 시스템 성능에 영향을 줄 수 있습니다.<ul><li>조치가이드: 공유 메모리 사용량이 비정상적으로 높으면 공유 메모리 설정 점검, 메모리 맵 파일 최적화를 검토해야 합니다.</li></ul>',
        
        'Memory Slab': '리눅스 커널의 Slab 메모리(커널 객체 캐시) 사용량을 모니터링합니다. <u>커널 메모리의 핵심지표</u>로 회수 가능/불가능한 커널 메모리를 구분합니다. 회수 불가능한 Slab이 `500MB` 이상이면 커널 메모리 누수 가능성이 있습니다.<ul><li>조치가이드: Slab 메모리가 과도하면 커널 모듈 점검, 시스템 재부팅 또는 커널 메모리 누수 분석을 검토해야 합니다.</li></ul>',
        
        'Memory Vmalloc': '리눅스 커널의 가상 메모리 할당(vmalloc) 영역 사용량을 모니터링합니다. <u>커널 가상메모리의 핵심지표</u>로 커널이 사용하는 가상 메모리 공간을 보여줍니다. vmalloc 사용량이 급증하면 커널 드라이버 문제가 있을 수 있습니다.<ul><li>조치가이드: vmalloc 사용량이 비정상적으로 높으면 커널 드라이버 점검, 시스템 로그 확인 또는 커널 업데이트를 검토해야 합니다.</li></ul>',
        
        'Memory Bounce': '리눅스 시스템의 바운스 메모리(DMA 버퍼) 사용량을 모니터링합니다. <u>DMA 성능의 핵심지표</u>로 하드웨어가 직접 접근할 수 없는 메모리에서 DMA 가능한 영역으로 복사되는 메모리를 보여줍니다. 바운스 메모리가 증가하면 I/O 성능이 저하됩니다.<ul><li>조치가이드: 바운스 메모리가 많으면 하드웨어 호환성 점검, 드라이버 업데이트 또는 메모리 구성 최적화를 검토해야 합니다.</li></ul>',
        
        'Memory Anonymous': '리눅스 시스템의 익명 메모리(프로세스 실행 메모리) 사용량을 모니터링합니다. <u>프로세스 메모리의 핵심지표</u>로 파일과 연결되지 않은 순수 프로세스 메모리를 보여줍니다. 익명 메모리가 급증하면 메모리 누수나 프로세스 이상이 있을 수 있습니다.<ul><li>조치가이드: 익명 메모리가 비정상적으로 증가하면 프로세스 메모리 사용량 분석, 메모리 누수 점검 또는 프로세스 재시작을 검토해야 합니다.</li></ul>',
        
        'Memory Kernel / CPU': '리눅스 커널의 스택 메모리와 CPU별 메모리 사용량을 모니터링합니다. <u>커널 메모리 최적화의 핵심지표</u>로 커널 스택과 CPU별 할당된 메모리를 보여줍니다. 커널 스택 메모리가 급증하면 시스템 안정성에 영향을 줄 수 있습니다.<ul><li>조치가이드: 커널 메모리가 비정상적으로 증가하면 커널 프로세스 점검, 시스템 로그 분석 또는 시스템 재부팅을 검토해야 합니다.</li></ul>',
        
        'Memory HugePages Counter': '리눅스 시스템의 HugePage 개수를 모니터링합니다. <u>메모리 최적화의 핵심지표</u>로 여유, 예약, 잉여 HugePage 수를 보여줍니다. HugePage 부족이 지속되면 고성능 애플리케이션 성능이 저하됩니다.<ul><li>조치가이드: HugePage가 부족하면 HugePage 설정 증가, 메모리 구성 최적화 또는 애플리케이션 메모리 사용 패턴 분석을 검토해야 합니다.</li></ul>',
        
        'Memory HugePages Size': '리눅스 시스템의 HugePage 크기와 총 개수를 모니터링합니다. <u>대용량 메모리 관리의 핵심지표</u>로 HugePage의 구성 정보를 보여줍니다. HugePage 설정이 적절하지 않으면 메모리 효율성이 떨어집니다.<ul><li>조치가이드: HugePage 설정이 부적절하면 HugePage 크기 조정, 총 개수 최적화 또는 애플리케이션 요구사항 재검토를 해야 합니다.</li></ul>',
        
        'Memory DirectMap': '리눅스 커널의 DirectMap 메모리 영역별 사용량을 모니터링합니다. <u>커널 메모리 매핑의 핵심지표</u>로 1GB, 2MB, 4KB 페이지별 매핑 상태를 보여줍니다. DirectMap 구성이 비효율적이면 메모리 성능이 저하됩니다.<ul><li>조치가이드: DirectMap 구성이 비효율적이면 커널 매개변수 조정, HugePage 설정 최적화 또는 메모리 구성 재검토를 해야 합니다.</li></ul>',
        
        'Memory Unevictable and MLocked': '리눅스 시스템의 회수 불가능한 메모리와 잠긴 메모리를 모니터링합니다. <u>메모리 잠금의 핵심지표</u>로 스왑 아웃할 수 없는 메모리 영역을 보여줍니다. 잠긴 메모리가 과도하면 메모리 압박 시 문제가 될 수 있습니다.<ul><li>조치가이드: 잠긴 메모리가 과도하면 메모리 잠금 설정 검토, 애플리케이션 구성 최적화 또는 시스템 리소스 확장을 검토해야 합니다.</li></ul>',
        
        'Memory NFS': '리눅스 시스템의 NFS 불안정 페이지 메모리를 모니터링합니다. <u>NFS 성능의 핵심지표</u>로 NFS 서버로 쓰기 대기 중인 메모리를 보여줍니다. NFS 불안정 메모리가 많으면 네트워크 I/O 지연이 발생할 수 있습니다.<ul><li>조치가이드: NFS 불안정 메모리가 많으면 NFS 네트워크 상태 점검, NFS 설정 최적화 또는 네트워크 성능 개선을 검토해야 합니다.</li></ul>',
        
        'Memory Pages In / Out': '리눅스 시스템의 페이지 입출력 작업을 모니터링합니다. <u>메모리 I/O의 핵심지표</u>로 디스크에서 메모리로, 메모리에서 디스크로의 페이지 이동을 보여줍니다. 페이지 I/O가 높으면 메모리 압박 상태입니다.<ul><li>조치가이드: 페이지 I/O가 높으면 메모리 증설, 스왑 설정 최적화 또는 메모리 사용량 분석을 검토해야 합니다.</li></ul>',
        
        'Memory Pages Swap In / Out': '리눅스 시스템의 스왑 페이지 입출력을 모니터링합니다. <u>스왑 성능의 핵심지표</u>로 스왑 영역과의 페이지 교환 상태를 보여줍니다. 스왑 I/O가 빈번하면 심각한 메모리 부족 상태입니다.<ul><li>조치가이드: 스왑 I/O가 빈번하면 즉시 메모리 증설, 프로세스 메모리 사용량 최적화 또는 불필요한 프로세스 종료를 검토해야 합니다.</li></ul>',
        
        'Memory Page Faults': '리눅스 시스템의 페이지 폴트 발생률을 모니터링합니다. <u>메모리 접근 성능의 핵심지표</u>로 major/minor 페이지 폴트를 구분합니다. major 페이지 폴트가 높으면 디스크 I/O 대기로 인한 성능 저하가 발생합니다.<ul><li>조치가이드: major 페이지 폴트가 높으면 메모리 증설, 스왑 성능 개선 또는 애플리케이션 메모리 사용 패턴 최적화를 검토해야 합니다.</li></ul>',
        
        'OOM Killer': '리눅스 시스템의 OOM(Out Of Memory) Killer 실행 횟수를 모니터링합니다. <u>메모리 부족 대응의 핵심지표</u>로 메모리 부족으로 인한 프로세스 강제 종료 상황을 보여줍니다. OOM Killer가 실행되면 시스템이 심각한 메모리 부족 상태입니다.<ul><li>조치가이드: OOM Killer가 실행되면 즉시 메모리 증설, 메모리 사용량이 많은 프로세스 최적화 또는 시스템 리소스 재분배를 검토해야 합니다.</li></ul>',
        
        'Time Synchronized Drift': '리눅스 시스템의 시간 동기화 드리프트를 모니터링합니다. <u>시간 정확도의 핵심지표</u>로 시스템 시간의 오차와 최대 오차를 보여줍니다. 시간 드리프트가 `1초` 이상이면 시스템 서비스에 영향을 줄 수 있습니다.<ul><li>조치가이드: 시간 드리프트가 크면 NTP 서버 설정 점검, 시간 동기화 서비스 재시작 또는 하드웨어 클럭 문제 확인을 검토해야 합니다.</li></ul>',
        
        'Time PLL Adjust': '리눅스 시스템의 PLL(Phase-Locked Loop) 시간 조정 상수를 모니터링합니다. <u>시간 동기화 안정성의 핵심지표</u>로 시스템 클럭의 안정성을 보여줍니다. PLL 상수가 비정상이면 시간 동기화가 불안정할 수 있습니다.<ul><li>조치가이드: PLL 조정이 비정상이면 시간 동기화 설정 점검, NTP 구성 최적화 또는 하드웨어 클럭 상태 확인을 검토해야 합니다.</li></ul>',
        
        'Time Synchronized Status': '리눅스 시스템의 시간 동기화 상태를 모니터링합니다. <u>시간 동기화 신뢰성의 핵심지표</u>로 동기화 상태와 주파수 조정 비율을 보여줍니다. 동기화 상태가 `0`이 아니면 시간 동기화에 문제가 있습니다.<ul><li>조치가이드: 시간 동기화 상태가 비정상이면 NTP 서비스 상태 점검, 네트워크 연결 확인 또는 시간 서버 변경을 검토해야 합니다.</li></ul>',
        
        'Time Misc': '리눅스 시스템의 기타 시간 관련 설정을 모니터링합니다. <u>시간 시스템 구성의 핵심지표</u>로 틱 간격과 TAI 오프셋을 보여줍니다. 시간 설정이 비정상이면 시스템 동작에 영향을 줄 수 있습니다.<ul><li>조치가이드: 시간 설정이 비정상이면 커널 시간 매개변수 확인, 시스템 시간 구성 점검 또는 시간 관련 서비스 재시작을 검토해야 합니다.</li></ul>',
        
        'Processes Status': '리눅스 시스템의 프로세스 상태를 모니터링합니다. <u>프로세스 관리의 핵심지표</u>로 실행 중이거나 블록된 프로세스 수를 보여줍니다. 블록된 프로세스가 많으면 I/O 대기나 리소스 경합이 발생하고 있습니다.<ul><li>조치가이드: 블록된 프로세스가 많으면 I/O 성능 점검, 리소스 병목 분석 또는 프로세스 우선순위 조정을 검토해야 합니다.</li></ul>',
        
        'Processes  Forks': '리눅스 시스템의 프로세스 포크(생성) 비율을 모니터링합니다. <u>프로세스 생성 활동의 핵심지표</u>로 초당 새로 생성되는 프로세스 수를 보여줍니다. 포크 비율이 급증하면 시스템 부하가 증가합니다.<ul><li>조치가이드: 프로세스 포크가 급증하면 과도한 프로세스 생성 원인 분석, 애플리케이션 최적화 또는 시스템 리소스 확장을 검토해야 합니다.</li></ul>',
        
        'Processes Memory': '리눅스 시스템의 프로세스별 메모리 사용량을 모니터링합니다. <u>프로세스 메모리 효율성의 핵심지표</u>로 가상 메모리와 상주 메모리를 보여줍니다. 프로세스 메모리 사용량이 급증하면 메모리 누수가 있을 수 있습니다.<ul><li>조치가이드: 프로세스 메모리가 비정상적으로 증가하면 메모리 누수 점검, 프로세스 재시작 또는 애플리케이션 최적화를 검토해야 합니다.</li></ul>',
        
        'Process schedule stats Running / Waiting': '리눅스 시스템의 프로세스 스케줄링 통계를 모니터링합니다. <u>CPU 스케줄링의 핵심지표</u>로 프로세스가 실행되거나 대기한 시간을 보여줍니다. 대기 시간이 길면 CPU 경합이나 리소스 부족이 있습니다.<ul><li>조치가이드: 프로세스 대기 시간이 길면 CPU 사용률 분석, 프로세스 우선순위 조정 또는 시스템 리소스 확장을 검토해야 합니다.</li></ul>',
        
        'Context Switches / Interrupts': '리눅스 시스템의 컨텍스트 스위치와 인터럽트 발생률을 모니터링합니다. <u>시스템 효율성의 핵심지표</u>로 프로세스 전환과 하드웨어 인터럽트 빈도를 보여줍니다. 컨텍스트 스위치가 과도하면 시스템 오버헤드가 증가합니다.<ul><li>조치가이드: 컨텍스트 스위치가 과도하면 프로세스 수 최적화, CPU 친화성 설정 또는 시스템 튜닝을 검토해야 합니다.</li></ul>',
        
        'System Load': '리눅스 시스템의 로드 애버리지를 모니터링합니다. <u>시스템 부하의 핵심지표</u>로 1분, 5분, 15분 평균 부하를 보여줍니다. 로드가 CPU 코어 수를 초과하면 시스템이 과부하 상태입니다.<ul><li>조치가이드: 시스템 로드가 높으면 CPU 집약적 작업 분석, 프로세스 최적화 또는 하드웨어 리소스 확장을 검토해야 합니다.</li></ul>',
        
        'CPU Frequency Scaling': '리눅스 시스템의 CPU 주파수 스케일링을 모니터링합니다. <u>CPU 전력 관리의 핵심지표</u>로 현재, 최대, 최소 CPU 주파수를 보여줍니다. CPU 주파수가 낮으면 성능 제한이나 전력 절약 모드일 수 있습니다.<ul><li>조치가이드: CPU 주파수가 예상보다 낮으면 전력 관리 설정 확인, CPU 거버너 조정 또는 온도 관리 점검을 검토해야 합니다.</li></ul>',
        
        'Schedule timeslices executed by each cpu': '리눅스 시스템의 CPU별 스케줄 타임슬라이스 실행 횟수를 모니터링합니다. <u>CPU 스케줄링 균형의 핵심지표</u>로 각 CPU 코어의 작업 분배를 보여줍니다. CPU별 타임슬라이스 차이가 크면 부하 불균형이 있습니다.<ul><li>조치가이드: CPU 부하 불균형이 있으면 프로세스 친화성 설정, 스케줄러 튜닝 또는 워크로드 분산 최적화를 검토해야 합니다.</li></ul>',
        
        'Entropy': '리눅스 시스템의 엔트로피(무작위성) 풀 상태를 모니터링합니다. <u>암호화 보안의 핵심지표</u>로 시스템에서 사용 가능한 무작위 비트 수를 보여줍니다. 엔트로피가 `1000` 미만이면 암호화 작업이 지연될 수 있습니다.<ul><li>조치가이드: 엔트로피가 부족하면 하드웨어 난수 생성기 활성화, rng-tools 설치 또는 엔트로피 소스 추가를 검토해야 합니다.</li></ul>',
        
        'CPU time spent in user and system contexts': '리눅스 시스템의 사용자/시스템 컨텍스트 CPU 시간을 모니터링합니다. <u>프로세스 실행 효율성의 핵심지표</u>로 특정 프로세스의 CPU 사용 패턴을 보여줍니다. 시스템 컨텍스트 시간이 높으면 커널 작업이 많습니다.<ul><li>조치가이드: 시스템 컨텍스트 시간이 높으면 시스템 호출 최적화, I/O 패턴 개선 또는 커널 성능 튜닝을 검토해야 합니다.</li></ul>',
        
        'File Descriptors': '리눅스 시스템의 파일 디스크립터 사용량을 모니터링합니다. <u>파일 시스템 리소스의 핵심지표</u>로 현재 열린 파일과 최대 허용 파일 수를 보여줍니다. 파일 디스크립터 사용률이 `80%` 이상이면 파일 오픈 제한에 근접한 상태입니다.<ul><li>조치가이드: 파일 디스크립터가 부족하면 열린 파일 정리, ulimit 설정 증가 또는 애플리케이션 파일 관리 최적화를 검토해야 합니다.</li></ul>',
        
        'Hardware temperature monitor': '리눅스 시스템의 하드웨어 온도를 모니터링합니다. <u>시스템 안정성의 핵심지표</u>로 CPU, GPU 등의 온도와 임계치를 보여줍니다. 온도가 임계치의 `90%` 이상이면 하드웨어 보호를 위한 성능 제한이 발생합니다.<ul><li>조치가이드: 하드웨어 온도가 높으면 냉각 시스템 점검, 먼지 청소, 팬 교체 또는 열 배출 환경 개선을 검토해야 합니다.</li></ul>',
        
        'Throttle cooling device': '리눅스 시스템의 온도 조절 장치 상태를 모니터링합니다. <u>열 관리의 핵심지표</u>로 현재 조절 레벨과 최대 조절 레벨을 보여줍니다. 조절 레벨이 높으면 열 때문에 성능이 제한되고 있습니다.<ul><li>조치가이드: 조절 레벨이 높으면 냉각 효율성 개선, 작업 부하 분산 또는 하드웨어 환경 최적화를 검토해야 합니다.</li></ul>',
        
        'Power supply': '리눅스 시스템의 전원 공급 장치 상태를 모니터링합니다. <u>전력 안정성의 핵심지표</u>로 전원 공급 장치의 온라인 상태를 보여줍니다. 전원 공급 상태가 `0`이면 전력 공급에 문제가 있습니다.<ul><li>조치가이드: 전원 공급에 문제가 있으면 전원 케이블 점검, UPS 상태 확인 또는 전력 공급 장치 교체를 검토해야 합니다.</li></ul>',
        
        'Systemd Sockets': '리눅스 시스템의 systemd 소켓 연결 수용 비율을 모니터링합니다. <u>서비스 소켓 성능의 핵심지표</u>로 소켓 기반 서비스의 연결 처리량을 보여줍니다. 소켓 연결이 급증하면 서비스 부하가 증가하고 있습니다.<ul><li>조치가이드: 소켓 연결이 급증하면 서비스 성능 최적화, 연결 제한 설정 조정 또는 로드 밸런싱을 검토해야 합니다.</li></ul>',
        
        'Systemd Units State': '리눅스 시스템의 systemd 서비스 유닛 상태를 모니터링합니다. <u>시스템 서비스 관리의 핵심지표</u>로 활성, 비활성, 실패 등 서비스 상태별 개수를 보여줍니다. 실패한 서비스가 있으면 시스템 기능에 문제가 있을 수 있습니다.<ul><li>조치가이드: 실패한 서비스가 있으면 서비스 로그 확인, 의존성 점검, 서비스 재시작 또는 구성 수정을 검토해야 합니다.</li></ul>',
        
        'Disk IOps Discards completed / merged': '리눅스 시스템의 디스크 Discard(TRIM) 작업을 모니터링합니다. <u>SSD 최적화의 핵심지표</u>로 완료되거나 병합된 discard 작업 수를 보여줍니다. Discard 작업이 많으면 SSD 성능 최적화가 활발히 진행되고 있습니다.<ul><li>조치가이드: Discard 작업이 과도하면 TRIM 스케줄 조정, SSD 펌웨어 업데이트 또는 파일시스템 설정 최적화를 검토해야 합니다.</li></ul>',
        
        'Filesystem space available': '리눅스 시스템의 파일시스템별 사용 가능한 공간을 모니터링합니다. <u>스토리지 용량 관리의 핵심지표</u>로 사용 가능, 여유, 전체 공간을 보여줍니다. 사용 가능한 공간이 `15%` 미만이면 디스크 공간 부족 위험이 있습니다.<ul><li>조치가이드: 디스크 공간이 부족하면 불필요한 파일 정리, 로그 로테이션 설정, 디스크 확장 또는 데이터 아카이빙을 검토해야 합니다.</li></ul>',
        
        'File Nodes Free': '리눅스 시스템의 파일시스템별 여유 inode 수를 모니터링합니다. <u>파일 생성 능력의 핵심지표</u>로 생성 가능한 파일/디렉토리 수를 보여줍니다. 여유 inode가 `10%` 미만이면 새 파일 생성이 제한됩니다.<ul><li>조치가이드: inode가 부족하면 불필요한 파일 정리, 작은 파일들 통합, 파일시스템 재구성 또는 inode 수 증가를 검토해야 합니다.</li></ul>',
        
        'File Descriptor': '리눅스 시스템의 전역 파일 디스크립터 사용량을 모니터링합니다. <u>시스템 전체 파일 관리의 핵심지표</u>로 할당된 파일 디스크립터와 최대 허용 수를 보여줍니다. 전역 파일 디스크립터 사용률이 `80%` 이상이면 시스템 전체에 영향을 줍니다.<ul><li>조치가이드: 전역 파일 디스크립터가 부족하면 시스템 전체 파일 제한 증가, 애플리케이션 파일 사용 최적화 또는 시스템 튜닝을 검토해야 합니다.</li></ul>',
        
        'File Nodes Size': '리눅스 시스템의 파일시스템별 총 inode 수를 모니터링합니다. <u>파일시스템 구조의 핵심지표</u>로 파일시스템의 파일 생성 용량을 보여줍니다. inode 구성이 워크로드에 적합하지 않으면 효율성이 떨어집니다.<ul><li>조치가이드: inode 구성이 부적절하면 파일시스템 재구성, inode 비율 조정 또는 파일 사용 패턴 최적화를 검토해야 합니다.</li></ul>',
        
        'Filesystem in ReadOnly / Error': '리눅스 시스템의 파일시스템 읽기 전용 상태와 오류를 모니터링합니다. <u>파일시스템 안정성의 핵심지표</u>로 읽기 전용 마운트와 디바이스 오류를 보여줍니다. 파일시스템이 읽기 전용이거나 오류가 있으면 데이터 쓰기가 불가능합니다.<ul><li>조치가이드: 파일시스템 오류가 있으면 fsck 실행, 하드웨어 상태 점검, 파일시스템 복구 또는 백업에서 복원을 검토해야 합니다.</li></ul>',
        
        'Network Traffic by Packets': '리눅스 시스템의 네트워크 패킷 송수신 비율을 모니터링합니다. <u>네트워크 활동의 핵심지표</u>로 초당 송수신 패킷 수를 보여줍니다. 패킷 수가 급증하면 네트워크 부하가 증가하고 있습니다.<ul><li>조치가이드: 네트워크 패킷이 급증하면 네트워크 트래픽 분석, 대역폭 관리, DDoS 공격 점검 또는 네트워크 최적화를 검토해야 합니다.</li></ul>',
        
        'Network Traffic Errors': '리눅스 시스템의 네트워크 송수신 오류를 모니터링합니다. <u>네트워크 품질의 핵심지표</u>로 네트워크 인터페이스의 오류 발생률을 보여줍니다. 네트워크 오류가 발생하면 연결 품질에 문제가 있습니다.<ul><li>조치가이드: 네트워크 오류가 발생하면 네트워크 케이블 점검, 스위치/라우터 상태 확인, 드라이버 업데이트 또는 하드웨어 교체를 검토해야 합니다.</li></ul>',
        
        'Network Traffic Drop': '리눅스 시스템의 네트워크 패킷 드롭을 모니터링합니다. <u>네트워크 성능의 핵심지표</u>로 송수신 시 버려진 패킷 수를 보여줍니다. 패킷 드롭이 발생하면 네트워크 성능 저하나 버퍼 부족이 있습니다.<ul><li>조치가이드: 패킷 드롭이 발생하면 네트워크 버퍼 크기 조정, 네트워크 드라이버 최적화, 대역폭 제한 해제 또는 하드웨어 성능 개선을 검토해야 합니다.</li></ul>',
        
        'Network Traffic Compressed': '리눅스 시스템의 압축된 네트워크 트래픽을 모니터링합니다. <u>네트워크 효율성의 핵심지표</u>로 압축 기능을 사용하는 네트워크 인터페이스의 패킷을 보여줍니다. 압축 트래픽이 증가하면 대역폭 효율성이 개선됩니다.<ul><li>조치가이드: 압축 트래픽 설정이 필요하면 네트워크 압축 활성화, 압축 알고리즘 최적화 또는 대역폭 관리 개선을 검토해야 합니다.</li></ul>',
        
        'Network Traffic Multicast': '리눅스 시스템의 멀티캐스트 네트워크 트래픽을 모니터링합니다. <u>멀티캐스트 통신의 핵심지표</u>로 멀티캐스트 패킷 수신량을 보여줍니다. 멀티캐스트 트래픽이 예상과 다르면 네트워크 구성에 문제가 있을 수 있습니다.<ul><li>조치가이드: 멀티캐스트 트래픽이 비정상이면 멀티캐스트 라우팅 설정 점검, IGMP 구성 확인 또는 네트워크 스위치 설정 검토를 해야 합니다.</li></ul>',
        
        'Network Traffic Fifo': '리눅스 시스템의 네트워크 FIFO 오류를 모니터링합니다. <u>네트워크 큐 관리의 핵심지표</u>로 송수신 FIFO 큐 오버플로우를 보여줍니다. FIFO 오류가 발생하면 네트워크 처리 능력을 초과한 상태입니다.<ul><li>조치가이드: FIFO 오류가 발생하면 네트워크 큐 크기 증가, 네트워크 인터럽트 최적화 또는 네트워크 처리 성능 개선을 검토해야 합니다.</li></ul>',
        
        'Network Traffic Frame': '리눅스 시스템의 네트워크 프레임 오류를 모니터링합니다. <u>네트워크 물리층의 핵심지표</u>로 잘못된 프레임 수신 수를 보여줍니다. 프레임 오류가 발생하면 물리적 네트워크 연결에 문제가 있습니다.<ul><li>조치가이드: 프레임 오류가 발생하면 네트워크 케이블 교체, 포트 점검, 전기적 간섭 제거 또는 네트워크 하드웨어 진단을 검토해야 합니다.</li></ul>',
        
        'Network Traffic Carrier': '리눅스 시스템의 네트워크 캐리어 오류를 모니터링합니다. <u>네트워크 연결 상태의 핵심지표</u>로 송신 시 캐리어 감지 실패를 보여줍니다. 캐리어 오류가 발생하면 네트워크 연결이 불안정합니다.<ul><li>조치가이드: 캐리어 오류가 발생하면 네트워크 연결 안정성 점검, 네트워크 장비 상태 확인 또는 연결 방식 최적화를 검토해야 합니다.</li></ul>',
        
        'Network Traffic Colls': '리눅스 시스템의 네트워크 충돌(Collision) 발생을 모니터링합니다. <u>네트워크 경합의 핵심지표</u>로 이더넷 충돌 횟수를 보여줍니다. 충돌이 빈번하면 네트워크 경합이 심각한 상태입니다.<ul><li>조치가이드: 네트워크 충돌이 빈번하면 네트워크 토폴로지 개선, 스위치 도입, 네트워크 분할 또는 트래픽 분산을 검토해야 합니다.</li></ul>',
        
        'NF Conntrack': '리눅스 시스템의 netfilter 연결 추적 상태를 모니터링합니다. <u>방화벽 성능의 핵심지표</u>로 현재 추적 중인 연결과 최대 허용 연결 수를 보여줍니다. 연결 추적 사용률이 `80%` 이상이면 방화벽 성능이 저하됩니다.<ul><li>조치가이드: 연결 추적이 포화되면 conntrack 테이블 크기 증가, 연결 타임아웃 조정 또는 불필요한 연결 추적 제거를 검토해야 합니다.</li></ul>',
        
        'ARP Entries': '리눅스 시스템의 ARP 테이블 엔트리 수를 모니터링합니다. <u>네트워크 주소 해석의 핵심지표</u>로 IP-MAC 주소 매핑 테이블 크기를 보여줍니다. ARP 엔트리가 급증하면 네트워크 스캔이나 비정상 활동이 있을 수 있습니다.<ul><li>조치가이드: ARP 엔트리가 급증하면 네트워크 보안 점검, ARP 테이블 크기 조정 또는 네트워크 세그멘테이션을 검토해야 합니다.</li></ul>',
        
        'MTU': '리눅스 시스템의 네트워크 인터페이스 MTU(Maximum Transmission Unit) 크기를 모니터링합니다. <u>네트워크 패킷 크기의 핵심지표</u>로 전송 가능한 최대 패킷 크기를 보여줍니다. MTU 설정이 부적절하면 네트워크 효율성이 떨어집니다.<ul><li>조치가이드: MTU 설정이 부적절하면 네트워크 경로 MTU 분석, 점보 프레임 설정 또는 네트워크 구성 최적화를 검토해야 합니다.</li></ul>',
        
        'Speed': '리눅스 시스템의 네트워크 인터페이스 속도를 모니터링합니다. <u>네트워크 대역폭의 핵심지표</u>로 링크 속도를 보여줍니다. 네트워크 속도가 예상보다 낮으면 하드웨어나 설정 문제가 있을 수 있습니다.<ul><li>조치가이드: 네트워크 속도가 낮으면 케이블 품질 점검, 네트워크 카드 설정 확인, 오토 네고시에이션 조정 또는 하드웨어 업그레이드를 검토해야 합니다.</li></ul>',
        
        'Queue Length': '리눅스 시스템의 네트워크 송신 큐 길이를 모니터링합니다. <u>네트워크 송신 성능의 핵심지표</u>로 송신 대기 중인 패킷 큐 크기를 보여줍니다. 큐 길이가 길면 네트워크 송신 병목이 있습니다.<ul><li>조치가이드: 송신 큐가 길면 네트워크 대역폭 확인, 큐 크기 조정, 송신 알고리즘 최적화 또는 네트워크 성능 개선을 검토해야 합니다.</li></ul>',
        
        'Softnet Packets': '리눅스 시스템의 소프트웨어 네트워크 패킷 처리를 모니터링합니다. <u>네트워크 소프트 인터럽트의 핵심지표</u>로 처리되거나 드롭된 패킷 수를 보여줍니다. 소프트넷 드롭이 발생하면 네트워크 처리 능력 부족입니다.<ul><li>조치가이드: 소프트넷 드롭이 발생하면 네트워크 인터럽트 최적화, CPU 친화성 설정, 네트워크 큐 조정 또는 하드웨어 성능 개선을 검토해야 합니다.</li></ul>',
        
        'Softnet Out of Quota': '리눅스 시스템의 소프트넷 할당량 초과를 모니터링합니다. <u>네트워크 처리 제한의 핵심지표</u>로 처리 시간 제한으로 인한 squeeze 횟수를 보여줍니다. 할당량 초과가 발생하면 네트워크 처리가 지연됩니다.<ul><li>조치가이드: 소프트넷 할당량 초과가 발생하면 net.core.netdev_budget 증가, 네트워크 인터럽트 밸런싱 또는 네트워크 처리 최적화를 검토해야 합니다.</li></ul>',
        
        'Network Operational Status': '리눅스 시스템의 네트워크 인터페이스 운영 상태를 모니터링합니다. <u>네트워크 연결 상태의 핵심지표</u>로 인터페이스의 up/down 상태와 캐리어 상태를 보여줍니다. 네트워크 상태가 `0`이면 연결이 끊어진 상태입니다.<ul><li>조치가이드: 네트워크 상태가 비정상이면 물리적 연결 확인, 네트워크 설정 점검, 드라이버 재시작 또는 하드웨어 교체를 검토해야 합니다.</li></ul>',
        
        'Sockstat TCP': '리눅스 시스템의 TCP 소켓 통계를 모니터링합니다. <u>TCP 연결 관리의 핵심지표</u>로 할당, 사용 중, 메모리 사용량, 고아 소켓, TIME_WAIT 소켓 수를 보여줍니다. TCP 소켓이 과도하면 네트워크 리소스가 부족합니다.<ul><li>조치가이드: TCP 소켓이 과도하면 연결 타임아웃 조정, 소켓 재사용 설정, 애플리케이션 연결 관리 최적화 또는 시스템 제한 증가를 검토해야 합니다.</li></ul>',
        
        'Sockstat UDP': '리눅스 시스템의 UDP 소켓 통계를 모니터링합니다. <u>UDP 통신의 핵심지표</u>로 UDP와 UDPLITE 소켓 사용량과 메모리 사용량을 보여줍니다. UDP 소켓이 급증하면 UDP 기반 서비스 부하가 증가하고 있습니다.<ul><li>조치가이드: UDP 소켓이 급증하면 UDP 애플리케이션 최적화, 소켓 버퍼 크기 조정 또는 UDP 트래픽 분석을 검토해야 합니다.</li></ul>',
        
        'Sockstat FRAG / RAW': '리눅스 시스템의 FRAG(조각화)와 RAW 소켓 통계를 모니터링합니다. <u>특수 소켓의 핵심지표</u>로 조각화된 패킷과 RAW 소켓 사용량을 보여줍니다. FRAG 소켓이 많으면 패킷 조각화가 빈번합니다.<ul><li>조치가이드: FRAG 소켓이 많으면 MTU 크기 최적화, 패킷 크기 조정, 네트워크 구성 점검 또는 애플리케이션 패킷 관리 개선을 검토해야 합니다.</li></ul>',
        
        'Sockstat Memory Size': '리눅스 시스템의 소켓별 메모리 사용량을 모니터링합니다. <u>네트워크 메모리 사용의 핵심지표</u>로 TCP, UDP, FRAG 소켓이 사용하는 메모리를 바이트 단위로 보여줍니다. 소켓 메모리가 과도하면 네트워크 성능이 저하됩니다.<ul><li>조치가이드: 소켓 메모리가 과도하면 소켓 버퍼 크기 조정, 네트워크 메모리 제한 증가 또는 연결 관리 최적화를 검토해야 합니다.</li></ul>',
        
        'Sockstat Used': '리눅스 시스템의 전체 소켓 사용량을 모니터링합니다. <u>시스템 소켓 리소스의 핵심지표</u>로 현재 사용 중인 소켓 총 개수를 보여줍니다. 사용 중인 소켓이 시스템 제한에 근접하면 새 연결이 거부될 수 있습니다.<ul><li>조치가이드: 소켓 사용량이 높으면 시스템 소켓 제한 증가, 불필요한 연결 정리 또는 애플리케이션 연결 풀 최적화를 검토해야 합니다.</li></ul>',
        
        'Netstat IP In / Out Octets': '리눅스 시스템의 IP 계층 옥텟(바이트) 송수신량을 모니터링합니다. <u>IP 트래픽 볼륨의 핵심지표</u>로 네트워크 계층에서의 실제 데이터 전송량을 보여줍니다. IP 트래픽이 급증하면 네트워크 사용량이 증가하고 있습니다.<ul><li>조치가이드: IP 트래픽이 급증하면 트래픽 분석, 대역폭 관리, 네트워크 모니터링 강화 또는 트래픽 최적화를 검토해야 합니다.</li></ul>',
        
        'Netstat IP Forwarding': '리눅스 시스템의 IP 포워딩 통계를 모니터링합니다. <u>라우팅 성능의 핵심지표</u>로 라우터 역할을 하는 시스템의 패킷 전달량을 보여줍니다. IP 포워딩이 증가하면 라우팅 부하가 증가하고 있습니다.<ul><li>조치가이드: IP 포워딩 부하가 높으면 라우팅 테이블 최적화, 하드웨어 오프로딩 활성화 또는 전용 라우터 도입을 검토해야 합니다.</li></ul>',
        
        'ICMP In / Out': '리눅스 시스템의 ICMP 메시지 송수신을 모니터링합니다. <u>네트워크 진단의 핵심지표</u>로 ping, traceroute 등의 ICMP 트래픽을 보여줍니다. ICMP 트래픽이 급증하면 네트워크 진단 활동이나 공격이 있을 수 있습니다.<ul><li>조치가이드: ICMP 트래픽이 급증하면 네트워크 스캔 여부 확인, 보안 정책 점검 또는 ICMP 제한 설정을 검토해야 합니다.</li></ul>',
        
        'ICMP Errors': '리눅스 시스템의 ICMP 오류 발생률을 모니터링합니다. <u>네트워크 연결성의 핵심지표</u>로 ICMP 오류 메시지 수신량을 보여줍니다. ICMP 오류가 발생하면 네트워크 연결이나 라우팅에 문제가 있습니다.<ul><li>조치가이드: ICMP 오류가 발생하면 네트워크 연결 상태 점검, 라우팅 설정 확인, 방화벽 규칙 검토 또는 네트워크 경로 분석을 해야 합니다.</li></ul>',
        
        'UDP In / Out': '리눅스 시스템의 UDP 데이터그램 송수신을 모니터링합니다. <u>UDP 통신 활동의 핵심지표</u>로 송수신되는 UDP 패킷 수를 보여줍니다. UDP 트래픽이 급증하면 UDP 기반 서비스 활동이 증가하고 있습니다.<ul><li>조치가이드: UDP 트래픽이 급증하면 UDP 서비스 상태 점검, DNS 질의량 분석, 스트리밍 서비스 모니터링 또는 UDP 플러딩 공격 여부 확인을 검토해야 합니다.</li></ul>',
        
        'UDP Errors': '리눅스 시스템의 UDP 관련 오류를 모니터링합니다. <u>UDP 통신 품질의 핵심지표</u>로 수신 오류, 포트 없음, 버퍼 오류 등을 보여줍니다. UDP 오류가 발생하면 UDP 서비스나 네트워크에 문제가 있습니다.<ul><li>조치가이드: UDP 오류가 발생하면 UDP 서비스 설정 점검, 포트 바인딩 확인, 버퍼 크기 조정 또는 네트워크 구성 검토를 해야 합니다.</li></ul>',
        
        'TCP In / Out': '리눅스 시스템의 TCP 세그먼트 송수신을 모니터링합니다. <u>TCP 통신 활동의 핵심지표</u>로 송수신되는 TCP 세그먼트 수를 보여줍니다. TCP 트래픽이 급증하면 웹, 데이터베이스 등 TCP 기반 서비스 활동이 증가하고 있습니다.<ul><li>조치가이드: TCP 트래픽이 급증하면 TCP 기반 서비스 상태 점검, 연결 풀 최적화, 로드 밸런싱 검토 또는 DDoS 공격 여부 확인을 해야 합니다.</li></ul>',
        
        'TCP Errors': '리눅스 시스템의 TCP 관련 오류를 종합적으로 모니터링합니다. <u>TCP 통신 안정성의 핵심지표</u>로 리슨 오버플로우, 재전송, 수신 오류 등을 보여줍니다. TCP 오류가 발생하면 네트워크 품질이나 서버 성능에 문제가 있습니다.<ul><li>조치가이드: TCP 오류가 발생하면 네트워크 품질 점검, 서버 성능 최적화, TCP 설정 조정 또는 로드 밸런싱 개선을 검토해야 합니다.</li></ul>',
        
        'TCP Connections': '리눅스 시스템의 TCP 연결 상태를 모니터링합니다. <u>TCP 연결 관리의 핵심지표</u>로 현재 설정된 연결과 최대 연결 수를 보여줍니다. TCP 연결이 최대치에 근접하면 새 연결을 수용할 수 없습니다.<ul><li>조치가이드: TCP 연결이 포화되면 연결 제한 증가, 연결 풀 최적화, 로드 밸런싱 도입 또는 서버 확장을 검토해야 합니다.</li></ul>',
        
        'TCP SynCookie': '리눅스 시스템의 TCP SynCookie 사용 현황을 모니터링합니다. <u>SYN 플러딩 방어의 핵심지표</u>로 SynCookie 전송, 수신, 실패 수를 보여줍니다. SynCookie가 활성화되면 SYN 플러딩 공격이 진행 중일 수 있습니다.<ul><li>조치가이드: SynCookie가 빈번하면 SYN 플러딩 공격 대응, 방화벽 설정 강화, 연결 제한 조정 또는 DDoS 방어 시스템 도입을 검토해야 합니다.</li></ul>',
        
        'TCP Direct Transition': '리눅스 시스템의 TCP 연결 생성 방식을 모니터링합니다. <u>TCP 연결 패턴의 핵심지표</u>로 능동(클라이언트)과 수동(서버) 연결 생성을 보여줍니다. 연결 패턴이 급변하면 트래픽 특성이나 서비스 상태가 변화하고 있습니다.<ul><li>조치가이드: TCP 연결 패턴이 비정상이면 서비스 상태 점검, 클라이언트 동작 분석, 로드 밸런싱 검토 또는 트래픽 패턴 분석을 해야 합니다.</li></ul>',
        
        'Node Exporter Scrape Time': 'Node Exporter의 메트릭 수집 소요 시간을 모니터링합니다. <u>모니터링 성능의 핵심지표</u>로 각 컬렉터별 데이터 수집 시간을 보여줍니다. 수집 시간이 `5초` 이상이면 모니터링 성능에 문제가 있습니다.<ul><li>조치가이드: 수집 시간이 길면 불필요한 컬렉터 비활성화, 수집 간격 조정, 시스템 리소스 확인 또는 Node Exporter 최적화를 검토해야 합니다.</li></ul>',
        
        'Node Exporter Scrape': 'Node Exporter의 메트릭 수집 성공/실패 상태를 모니터링합니다. <u>모니터링 안정성의 핵심지표</u>로 컬렉터별 수집 성공률과 텍스트 파일 스크래핑 오류를 보여줍니다. 수집 실패가 발생하면 모니터링 데이터가 누락됩니다.<ul><li>조치가이드: 수집 실패가 발생하면 Node Exporter 로그 확인, 권한 설정 점검, 컬렉터 구성 검토 또는 시스템 상태 분석을 해야 합니다.</li></ul>'
    }
    
    # 정확한 제목이 없으면 유사한 키워드로 검색
    if panel_title in descriptions:
        return descriptions[panel_title]
    
    # 키워드 기반 매칭
    title_lower = panel_title.lower()
    
    if 'cpu' in title_lower:
        if 'guest' in title_lower or 'vm' in title_lower:
            return descriptions.get('CPU spent seconds in guests (VMs)', f'{panel_title} 메트릭을 모니터링합니다.')
        elif 'frequency' in title_lower:
            return descriptions.get('CPU Frequency Scaling', f'{panel_title} 메트릭을 모니터링합니다.')
        else:
            return descriptions.get('CPU', f'{panel_title} 메트릭을 모니터링합니다.')
    elif 'memory' in title_lower:
        for key in descriptions.keys():
            if key.lower().startswith('memory') and any(word in title_lower for word in key.lower().split()[1:]):
                return descriptions[key]
        return descriptions.get('Memory Stack', f'{panel_title} 메트릭을 모니터링합니다.')
    elif 'network' in title_lower:
        for key in descriptions.keys():
            if 'network' in key.lower() and any(word in title_lower for word in key.lower().split()[1:]):
                return descriptions[key]
        return descriptions.get('Network Traffic', f'{panel_title} 메트릭을 모니터링합니다.')
    elif 'disk' in title_lower or 'io' in title_lower:
        for key in descriptions.keys():
            if ('disk' in key.lower() or 'i/o' in key.lower()) and any(word in title_lower for word in key.lower().split()[1:]):
                return descriptions[key]
        return descriptions.get('Disk IOps', f'{panel_title} 메트릭을 모니터링합니다.')
    elif 'filesystem' in title_lower or 'file' in title_lower:
        for key in descriptions.keys():
            if ('filesystem' in key.lower() or 'file' in key.lower()) and any(word in title_lower for word in key.lower().split()[1:]):
                return descriptions[key]
        return f'{panel_title} 파일시스템 메트릭을 모니터링합니다.'
    elif 'process' in title_lower:
        for key in descriptions.keys():
            if 'process' in key.lower() and any(word in title_lower for word in key.lower().split()[1:]):
                return descriptions[key]
        return f'{panel_title} 프로세스 메트릭을 모니터링합니다.'
    elif 'tcp' in title_lower:
        for key in descriptions.keys():
            if 'tcp' in key.lower() and any(word in title_lower for word in key.lower().split()[1:]):
                return descriptions[key]
        return f'{panel_title} TCP 관련 메트릭을 모니터링합니다.'
    elif 'udp' in title_lower:
        for key in descriptions.keys():
            if 'udp' in key.lower() and any(word in title_lower for word in key.lower().split()[1:]):
                return descriptions[key]
        return f'{panel_title} UDP 관련 메트릭을 모니터링합니다.'
    elif 'time' in title_lower:
        for key in descriptions.keys():
            if 'time' in key.lower() and any(word in title_lower for word in key.lower().split()[1:]):
                return descriptions[key]
        return f'{panel_title} 시간 관련 메트릭을 모니터링합니다.'
    elif 'systemd' in title_lower:
        for key in descriptions.keys():
            if 'systemd' in key.lower() and any(word in title_lower for word in key.lower().split()[1:]):
                return descriptions[key]
        return f'{panel_title} systemd 관련 메트릭을 모니터링합니다.'
    elif 'sockstat' in title_lower:
        for key in descriptions.keys():
            if 'sockstat' in key.lower() and any(word in title_lower for word in key.lower().split()[1:]):
                return descriptions[key]
        return f'{panel_title} 소켓 통계 메트릭을 모니터링합니다.'
    elif 'netstat' in title_lower:
        for key in descriptions.keys():
            if 'netstat' in key.lower() and any(word in title_lower for word in key.lower().split()[1:]):
                return descriptions[key]
        return f'{panel_title} 네트워크 통계 메트릭을 모니터링합니다.'
    elif 'icmp' in title_lower:
        for key in descriptions.keys():
            if 'icmp' in key.lower():
                return descriptions[key]
        return f'{panel_title} ICMP 관련 메트릭을 모니터링합니다.'
    elif 'node exporter' in title_lower:
        for key in descriptions.keys():
            if 'node exporter' in key.lower():
                return descriptions[key]
        return f'{panel_title} Node Exporter 관련 메트릭을 모니터링합니다.'
    
    # 기본 설명
    return f'리눅스 시스템의 {panel_title} 메트릭을 모니터링합니다. <u>시스템 운영의 핵심지표</u>로 해당 항목의 상태와 성능을 실시간으로 추적합니다. 임계값을 벗어나면 시스템 성능이나 안정성에 영향을 줄 수 있습니다.<ul><li>조치가이드: 메트릭 값이 비정상이면 관련 로그 확인, 시스템 상태 점검 또는 전문가의 분석을 통해 적절한 대응 방안을 수립해야 합니다.</li></ul>'

def main():
    # Read the panel summary file
    input_file = '/Users/paul/sandbox/sqms-mgmt/grafana/desc_editor/node_exporter_panel_summary_20250726_224021.json'
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Generate descriptions for all panels needing description
    all_descriptions = {}
    panels_needing_desc = data['panels_needing_description']
    
    print(f"총 {len(panels_needing_desc)}개 패널에 대한 Description 생성 중...")
    
    for i, panel in enumerate(panels_needing_desc, 1):
        panel_id = panel['id']
        panel_title = panel['title']
        panel_type = panel['type']
        
        # Find detailed panel info
        detailed_panel = None
        for detail in data['detailed_panels']:
            if detail['id'] == panel_id:
                detailed_panel = detail
                break
        
        description = generate_description(panel_title, panel_type, detailed_panel)
        
        all_descriptions[panel_id] = {
            'title': panel_title,
            'type': panel_type,
            'description': description,
            'has_thresholds': detailed_panel['has_thresholds'] if detailed_panel else False,
            'threshold_count': detailed_panel['threshold_count'] if detailed_panel else 0,
            'query_count': detailed_panel['query_count'] if detailed_panel else 0
        }
        
        if i % 10 == 0:
            print(f"{i}/{len(panels_needing_desc)} 완료...")
    
    # Create output structure
    output = {
        'generated_at': datetime.datetime.now().isoformat(),
        'source_file': input_file,
        'total_panels_processed': len(panels_needing_desc),
        'panel_descriptions': all_descriptions
    }
    
    # Save to JSON file
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'/Users/paul/sandbox/sqms-mgmt/grafana/desc_editor/node_exporter_descriptions_{timestamp}.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\nDescription 생성 완료!")
    print(f"출력 파일: {output_file}")
    print(f"처리된 패널 수: {len(panels_needing_desc)}")
    
    return output_file

if __name__ == '__main__':
    main()