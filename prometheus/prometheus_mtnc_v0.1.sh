#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}
log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}
log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 현재 실행중인 Prometheus 버전 확인
get_current_version() {
    local version=""
    local process_path=""

    # 1. systemctl로 실행 중인 프로세스의 경로 확인
    if systemctl is-active prometheus >/dev/null 2>&1; then
        process_path=$(systemctl status prometheus | grep "ExecStart" | awk '{print $2}' | head -1)
    fi

    # 2. 서비스 파일에서 경로 확인 (process_path가 비어있는 경우)
    if [ -z "$process_path" ]; then
        if [ -f "/etc/systemd/system/prometheus.service" ]; then
            process_path=$(grep "ExecStart=" "/etc/systemd/system/prometheus.service" | sed 's/ExecStart=//' | awk '{print $1}' | tr -d '\')
        elif [ -f "/lib/systemd/system/prometheus.service" ]; then
            process_path=$(grep "ExecStart=" "/lib/systemd/system/prometheus.service" | sed 's/ExecStart=//' | awk '{print $1}' | tr -d '\')
        fi
    fi

    # 3. process_path에서 버전 확인
    if [ ! -z "$process_path" ] && [ -x "$process_path" ]; then
        version=$("$process_path" --version 2>/dev/null | grep "prometheus" | head -1 | awk '{print $3}')
        if [ ! -z "$version" ]; then
            echo "$version"
            return 0
        fi
    fi

    # 4. 설치된 prometheus 바이너리에서 버전 확인
    if [ -z "$version" ]; then
        # 가장 최신 버전의 prometheus 바이너리 찾기
        local newest_binary=$(ls -dt /opt/monitoring/prometheus/prometheus-*.linux-amd64/prometheus 2>/dev/null | head -1)
        if [ ! -z "$newest_binary" ] && [ -x "$newest_binary" ]; then
            version=$("$newest_binary" --version 2>/dev/null | grep "prometheus" | head -1 | awk '{print $3}')
            if [ ! -z "$version" ]; then
                echo "$version"
                return 0
            fi
        fi
    fi

    # 5. 버전을 찾지 못한 경우
    if [ -z "$version" ]; then
        log_warn "현재 실행 중인 Prometheus 버전을 찾을 수 없습니다."
        echo "unknown"
    fi
}

# 버전 호환성 체크
check_version_compatibility() {
    local current_major=$(echo "$1" | cut -d'.' -f1)
    local target_major=$(echo "$2" | cut -d'.' -f1)
    local current_minor=$(echo "$1" | cut -d'.' -f2)

    if [ "$current_major" == "2" ] && [ "$target_major" == "3" ]; then
        if [ "$current_minor" -lt "55" ]; then
            return 1
        fi
    elif [ "$current_major" == "3" ] && [ "$target_major" == "2" ]; then
        return 1
    fi
    return 0
}

# 설치된 Prometheus 버전 선택
select_prometheus_version() {
    # 직접 디렉토리 목록을 확인하고 배열에 추가
    local versions=()
    for dir in /opt/monitoring/prometheus/prometheus-*.linux-amd64/; do
        if [ -d "$dir" ]; then
            # 디렉토리 이름에서 마지막 슬래시 제거
            dir=${dir%/}
            # 디렉토리 경로에서 기본 이름만 추출
            versions+=($(basename "$dir"))
        fi
    done

    if [ ${#versions[@]} -eq 0 ]; then
        log_error "설치된 Prometheus 버전을 찾을 수 없습니다."
        return 1
    fi

    # 디버깅을 위한 출력
    log_info "발견된 버전들:"
    for version in "${versions[@]}"; do
        log_info "- $version"
    done

    local current_version=$(get_current_version)
    log_info "현재 실행 중인 버전: $current_version"

    echo -e "\n사용 가능한 버전:"
    for i in "${!versions[@]}"; do
        local version_number=$(echo "${versions[$i]}" | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
        if check_version_compatibility "$current_version" "$version_number"; then
            echo "$((i+1))) ${versions[$i]} (호환 가능)"
        else
            echo "$((i+1))) ${versions[$i]} (호환 불가)"
        fi
    done

    while true; do
        read -p "선택할 버전 번호를 입력하세요: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#versions[@]} ]; then
            local selected_version=${versions[$((choice-1))]}
            local selected_version_number=$(echo "$selected_version" | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')

            if ! check_version_compatibility "$current_version" "$selected_version_number"; then
                log_error "선택한 버전은 현재 버전과 호환되지 않습니다."
                log_error "2.x -> 3.x 업그레이드는 2.55.x 이상에서만 가능합니다."
                log_error "3.x -> 2.x 다운그레이드는 지원되지 않습니다."
            continue
            fi

            SELECTED_VERSION="$selected_version"
            log_info "선택된 버전: $SELECTED_VERSION"
            return 0
        fi
        log_error "잘못된 선택입니다. 다시 선택해주세요."
    done
}

# 현재 Prometheus 설치 상태 확인
check_prometheus_installation() {
    if [ -f "/lib/systemd/system/prometheus.service" ]; then
        INSTALL_TYPE="package"
        log_info "패키지로 설치된 Prometheus가 발견되었습니다."
        return 0
    elif [ -f "/etc/systemd/system/prometheus.service" ]; then
        INSTALL_TYPE="binary"
        log_info "바이너리로 설치된 Prometheus가 발견되었습니다."
        return 0
    else
        log_error "Prometheus 서비스 파일을 찾을 수 없습니다."
        return 1
    fi
}

# 데이터 마이그레이션
migrate_data() {
    read -p "데이터를 마이그레이션 하시겠습니까? (y/n): " answer
    if [ "$answer" != "y" ]; then
        log_warn "데이터 마이그레이션을 건너뜁니다."
        return 0
    fi

    # 데이터 디렉토리 생성
    mkdir -p /opt/monitoring/prometheus/data

    if [ "$INSTALL_TYPE" == "package" ]; then
        log_info "TSDB 데이터 복사 중..."
        cp -r /var/lib/prometheus/* /opt/monitoring/prometheus/data/

        log_info "설정 파일 복사 중..."
        cp -r /etc/prometheus/* /opt/monitoring/prometheus/${SELECTED_VERSION}/
    fi

    chown -R prometheus:prometheus /opt/monitoring/prometheus/data
    log_info "데이터 마이그레이션 완료"
}

# 서비스 파일 생성
create_service_file() {
    read -p "새로운 서비스 파일을 생성하시겠습니까? (y/n): " answer
    if [ "$answer" != "y" ]; then
        log_warn "서비스 파일 생성을 건너뜁니다."
        return 0
    fi

    cat << EOF > /etc/systemd/system/prometheus.service
[Unit]
Description=Monitoring system and time series database
Documentation=https://prometheus.io/docs/introduction/overview/ man:prometheus(1)
After=network-online.target

[Service]
Restart=on-abnormal
User=prometheus
ExecStart=/opt/monitoring/prometheus/${SELECTED_VERSION}/prometheus \\
  --config.file=/opt/monitoring/prometheus/${SELECTED_VERSION}/prometheus.yml \\
  --storage.tsdb.path=/opt/monitoring/prometheus/data
ExecReload=/bin/kill -HUP \$MAINPID
TimeoutStopSec=20s
SendSIGKILL=no

# systemd hardening-options
AmbientCapabilities=
CapabilityBoundingSet=
DeviceAllow=/dev/null rw
DevicePolicy=strict
LimitMEMLOCK=0
LockPersonality=true
MemoryDenyWriteExecute=true
NoNewPrivileges=true
PrivateDevices=true
PrivateTmp=true
PrivateUsers=true
ProtectControlGroups=true
ProtectHome=true
ProtectKernelModules=true
ProtectKernelTunables=true
ProtectSystem=full
RemoveIPC=true
RestrictNamespaces=true
RestrictRealtime=true
SystemCallArchitectures=native

[Install]
WantedBy=multi-user.target
EOF

    log_info "서비스 파일이 생성되었습니다."
    systemctl daemon-reload
}

# 메인 실행
main() {
    log_info "Prometheus 업그레이드 스크립트를 시작합니다..."

    # 현재 설치 상태 확인
    check_prometheus_installation || exit 1

    # 버전 선택
    select_prometheus_version || exit 1

    # 데이터 마이그레이션
    migrate_data

    # 서비스 파일 생성
    create_service_file

    log_info "모든 작업이 완료되었습니다."
    log_info "다음 명령어로 서비스를 시작할 수 있습니다:"
    echo "systemctl start prometheus"
}

# 스크립트 실행
main
