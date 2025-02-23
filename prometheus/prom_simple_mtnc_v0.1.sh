#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 환경 변수로 경로 설정 (기본값 제공)
PROM_BASE="${PROM_BASE:-/opt/monitoring/prometheus}"
PROM_BACKUP="$PROM_BASE/backup"
PROM_TSDB="$PROM_BASE/tsdb"
PROM_CONFIG="$PROM_BASE/prometheus.yml"
PROM_TARGETS="$PROM_BASE/target"
PROM_RULES="$PROM_BASE/rules"
LOG_FILE="/var/log/prometheus-migration.log"

# 전역 변수
SELECTED_VERSION=""

# 로그 함수 (파일 및 콘솔 출력)
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}
log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}
log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# root 권한 체크
check_root() {
    if [ "$(id -u)" != "0" ]; then
        log_error "이 스크립트는 root 권한으로 실행해야 합니다."
        exit 1
    fi
}

# 권한 설정 헬퍼 함수
set_prometheus_permissions() {
    local target="$1"
    chown -R prometheus:prometheus "$target" && chmod -R 750 "$target"
    if [ $? -ne 0 ]; then
        log_error "권한 설정 실패: $target"
        return 1
    fi
    return 0
}

# 서비스 재시작 헬퍼 함수
restart_service() {
    systemctl daemon-reload || { log_error "systemd 데몬 리로드 실패"; return 1; }
    systemctl restart prometheus || { log_error "서비스 재시작 실패"; return 1; }
    verify_prometheus_start || { log_error "서비스 상태 확인 실패"; return 1; }
    return 0
}

# TSDB 활성 상태 확인 (생략된 기존 로직 유지, 필요 시 추가)
is_active_tsdb() {
    local tsdb_path="$1"
    local wal_dir=$(find_wal_directory "$tsdb_path")
    [ -n "$wal_dir" ] && return 0
    return 1
}

# TSDB 데이터 디렉토리 찾기 (기존 로직 유지)
find_tsdb_data() {
    local base_path="$1"
    local max_depth=2
    local found_dirs=()
    find "$base_path" -maxdepth $max_depth -type d -name "wal" -exec dirname {} \; 2>/dev/null | while read dir; do
        found_dirs+=("$dir")
    done
    [ ${#found_dirs[@]} -eq 0 ] && return 1
    echo "${found_dirs[0]}"
    return 0
}

# WAL 디렉토리 찾기 (기존 로직 유지)
find_wal_directory() {
    local base_path="$1"
    find "$base_path" -maxdepth 3 -type d -name "wal" 2>/dev/null | head -n 1
}

# WAL 상태 체크 (무결성 검증 추가)
check_wal_status() {
    local tsdb_path="$1"
    local binary_path="$2"
    local wal_path=$(find_wal_directory "$tsdb_path")
    
    if [ -z "$wal_path" ]; then
        log_warn "WAL 디렉토리 없음: $tsdb_path"
        return 1
    fi
    
    # WAL 무결성 체크
    "$binary_path" --storage.tsdb.path="$tsdb_path" --check 2>/dev/null
    if [ $? -ne 0 ]; then
        log_error "WAL 손상 감지: $tsdb_path"
        return 1
    fi
    log_info "WAL 상태 정상: $wal_path"
    return 0
}

# OS 타입 감지 (기존 로직 유지)
detect_os_type() {
    . /etc/os-release 2>/dev/null && echo "${ID%%-*}" || echo "unknown"
}

# 패키지 제거 (기존 로직 유지)
remove_package() {
    local os_type=$(detect_os_type)
    case "$os_type" in
        debian|ubuntu) apt remove --purge -y prometheus ;;
        redhat|centos) dnf remove -y prometheus ;;
        *) log_error "지원하지 않는 OS"; return 1 ;;
    esac
}

# 서비스 파일 위치 확인 (기존 로직 유지)
get_service_file_path() {
    local service_path="/etc/systemd/system/prometheus.service"
    [ -f "/usr/lib/systemd/system/prometheus.service" ] && service_path="/usr/lib/systemd/system/prometheus.service"
    echo "$service_path"
}

# 패키지 설치 여부 확인 (기존 로직 유지)
is_package_installed() {
    local os_type=$(detect_os_type)
    case "$os_type" in
        debian|ubuntu) dpkg-query -W -f='${Status}' prometheus 2>/dev/null | grep -q "install ok installed" && [ -f "/usr/lib/systemd/system/prometheus.service" ] ;;
        redhat|centos) rpm -q prometheus >/dev/null && [ -f "/usr/lib/systemd/system/prometheus.service" ] ;;
        *) return 1 ;;
    esac
}

# 패키지에서 바이너리로 마이그레이션
migrate_package_to_binary() {
    log_info "패키지에서 바이너리 설치로 마이그레이션 시작..."

    # 패키지 설치 확인
    if ! is_package_installed; then
        log_error "패키지로 설치된 Prometheus가 없습니다."
        return 1
    fi

    # 디스크 공간 체크
    local tsdb_size=$(du -s /var/lib/prometheus | cut -f1)
    local opt_free=$(df -k /opt/monitoring | awk 'NR==2 {print $4}')
    if [ "$opt_free" -lt "$((tsdb_size * 2))" ]; then
        log_error "디스크 공간 부족 (필요: $((tsdb_size * 2))K, 가용: $opt_free K)"
        return 1
    fi

    # 디렉토리 생성
    mkdir -p "$PROM_BASE"/{backup,tsdb,target,rules}
    set_prometheus_permissions "$PROM_BASE" || return 1

    # 설정 파일 백업
    mkdir -p "$PROM_BASE/backup/config"
    cp -r /etc/prometheus/* "$PROM_BASE/backup/config/" || { log_error "설정 백업 실패"; return 1; }
    
    # 설정 파일 복사
    cp -r /etc/prometheus/*.yml "$PROM_BASE/" || { log_error "설정 복사 실패"; return 1; }
    [ -d "/etc/prometheus/target" ] && cp -r /etc/prometheus/target/* "$PROM_TARGETS/" || true
    [ -d "/etc/prometheus/rules" ] && cp -r /etc/prometheus/rules/* "$PROM_RULES/" || true

    # 스냅샷 백업
    if ! backup_tsdb; then
        log_error "TSDB 스냅샷 백업 실패"
        rollback_migration
        return 1
    fi

    # TSDB 복사
    systemctl stop prometheus
    cp -r /var/lib/prometheus/* "$PROM_TSDB/" || { log_error "TSDB 복사 실패"; rollback_migration; return 1; }
    set_prometheus_permissions "$PROM_TSDB" || return 1

    # 버전 선택
    if ! select_prometheus_version; then
        log_error "버전 선택 실패"
        rollback_migration
        return 1
    fi

    # 서비스 전환
    local old_service="/usr/lib/systemd/system/prometheus.service"
    mv "$old_service" "${old_service}.disabled" || { log_error "서비스 파일 이동 실패"; rollback_migration; return 1; }
    create_service_file || { log_error "서비스 파일 생성 실패"; rollback_migration; return 1; }
    
    if ! restart_service; then
        log_error "서비스 시작 실패"
        rollback_migration
        return 1
    fi

    # 패키지 제거
    remove_package || log_warn "패키지 제거 실패 (무시됨)"
    log_info "마이그레이션 완료!"
    return 0
}

# 롤백 함수
rollback_migration() {
    log_info "마이그레이션 롤백 시작..."
    mv "/usr/lib/systemd/system/prometheus.service.disabled" "/usr/lib/systemd/system/prometheus.service" 2>/dev/null
    rm -rf "$PROM_TSDB"/* 2>/dev/null
    cp -r "$PROM_BASE/backup/config/"* /etc/prometheus/ 2>/dev/null
    systemctl daemon-reload
    systemctl start prometheus
}

# 스토리지 상태 체크 (기존 로직 유지, 간소화)
check_storage_status() {
    log_info "스토리지 상태 확인:"
    df -h / /opt/monitoring
}

# TSDB 스냅샷 백업
backup_tsdb() {
    local tsdb_dir="/var/lib/prometheus"
    if ! is_package_installed; then
        tsdb_dir="$PROM_TSDB"
    fi

    local tsdb_size=$(du -s "$tsdb_dir" | cut -f1)
    local opt_free=$(df -k /opt/monitoring | awk 'NR==2 {print $4}')
    if [ "$opt_free" -lt "$((tsdb_size * 2))" ]; then
        log_error "디스크 공간 부족"
        return 1
    fi

    # Admin API 활성화
    local service_file=$(get_service_file_path)
    if ! grep -q "--web.enable-admin-api" "$service_file"; then
        sed -i '/^ExecStart=/ s/$/ --web.enable-admin-api/' "$service_file"
        restart_service || { log_error "Admin API 활성화 실패"; return 1; }
    fi

    local backup_file="$PROM_BACKUP/tsdb-$(date +%Y%m%d).tar.gz"
    mkdir -p "$PROM_BACKUP" && set_prometheus_permissions "$PROM_BACKUP"
    
    curl -s -XPOST "http://localhost:9090/api/v1/admin/tsdb/snapshot" | grep -q "success" || { log_error "스냅샷 생성 실패"; return 1; }
    sleep $((tsdb_size/1024/1024 + 10))
    
    local snapshot_dir="$tsdb_dir/snapshots"
    local latest_snapshot=$(ls -td "$snapshot_dir"/* | head -1)
    [ -z "$latest_snapshot" ] && { log_error "스냅샷 찾기 실패"; return 1; }
    
    tar czf "$backup_file" -C "$snapshot_dir" "$(basename "$latest_snapshot")" || { log_error "백업 실패"; return 1; }
    set_prometheus_permissions "$backup_file"
    rm -rf "$latest_snapshot"
    log_info "백업 완료: $backup_file"
    return 0
}

# 버전 선택 (최신 버전 다운로드 추가)
select_prometheus_version() {
    local current_version=$(get_current_version | tail -n1)
    log_info "현재 버전: $current_version"
    
    local versions=()
    for dir in "$PROM_BASE"/prometheus-*.linux-amd64/; do
        [ -d "$dir" ] && versions+=($(basename "$dir"))
    done
    
    echo "사용 가능한 버전:"
    for i in "${!versions[@]}"; do
        echo "$((i+1))) ${versions[$i]}"
    done
    echo "n) 최신 버전 다운로드"
    
    while true; do
        read -p "선택 (번호 또는 n): " choice
        if [[ "$choice" == "n" ]]; then
            download_latest_version || continue
            return 0
        elif [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -le ${#versions[@]} ]; then
            SELECTED_VERSION="${versions[$((choice-1))]}"
            log_info "선택된 버전: $SELECTED_VERSION"
            return 0
        fi
        log_error "잘못된 선택"
    done
}

# 최신 버전 다운로드
download_latest_version() {
    local latest=$(curl -s https://api.github.com/repos/prometheus/prometheus/releases/latest | grep "tag_name" | cut -d'"' -f4 | sed 's/v//')
    local url="https://github.com/prometheus/prometheus/releases/download/v${latest}/prometheus-${latest}.linux-amd64.tar.gz"
    log_info "최신 버전 다운로드: $latest"
    
    wget -q "$url" -O /tmp/prometheus.tar.gz || { log_error "다운로드 실패"; return 1; }
    tar xzf /tmp/prometheus.tar.gz -C "$PROM_BASE" || { log_error "압축 해제 실패"; return 1; }
    rm /tmp/prometheus.tar.gz
    SELECTED_VERSION="prometheus-${latest}.linux-amd64"
    set_prometheus_permissions "$PROM_BASE/$SELECTED_VERSION"
    log_info "다운로드 완료: $SELECTED_VERSION"
    return 0
}

# 서비스 시작 검증
verify_prometheus_start() {
    local attempt=1 max_attempts=6
    while [ $attempt -le $max_attempts ]; do
        sleep 5
        curl -s --connect-timeout 5 --max-time 10 http://localhost:9090/-/healthy >/dev/null && { log_info "서비스 정상 시작"; return 0; }
        log_info "시도 $attempt/$max_attempts..."
        attempt=$((attempt + 1))
    done
    log_error "서비스 시작 실패"
    return 1
}

# 서비스 파일 생성 (로그 디렉토리 권한 포함)
create_service_file() {
    local log_dir="/var/log/prometheus"
    mkdir -p "$log_dir"
    set_prometheus_permissions "$log_dir" || { log_error "로그 디렉토리 권한 설정 실패"; return 1; }
    
    cat << EOF > /etc/systemd/system/prometheus.service
[Unit]
Description=Prometheus Monitoring System
Documentation=https://prometheus.io/docs/introduction/overview/
After=network-online.target

[Service]
User=prometheus
ExecStart=/opt/monitoring/prometheus/${SELECTED_VERSION}/prometheus \\
    --config.file=/opt/monitoring/prometheus/prometheus.yml \\
    --storage.tsdb.path=/opt/monitoring/prometheus/tsdb \\
    --storage.tsdb.retention.time=90d \\
    --web.console.templates=/opt/monitoring/prometheus/consoles \\
    --web.console.libraries=/opt/monitoring/prometheus/console_libraries \\
    --web.listen-address=0.0.0.0:9090 \\
    --web.enable-admin-api \\
    --query.log-file=/var/log/prometheus/query.log
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
    [ $? -ne 0 ] && { log_error "서비스 파일 생성 실패"; return 1; }
    systemctl daemon-reload || { log_error "systemd 데몬 리로드 실패"; return 1; }
    log_info "서비스 파일 생성 완료"
    return 0
}

# 현재 버전 확인 (기존 로직 유지)
get_current_version() {
    local version=$(curl -s --max-time 3 http://localhost:9090/api/v1/status/buildinfo | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    [ -z "$version" ] && version="unknown"
    log_info "현재 버전: $version"
    echo "$version"
}

# 메인 메뉴 및 실행 (간소화)
main() {
    check_root
    log_info "Prometheus 관리 스크립트 시작..."
    mkdir -p "$(dirname "$LOG_FILE")" && touch "$LOG_FILE" && set_prometheus_permissions "$(dirname "$LOG_FILE")"
    
    while true; do
        echo -e "\n1. 스토리지 상태 확인\n2. 스냅샷 생성\n3. 패키지 -> 바이너리 마이그레이션\nq. 종료"
        read -p "선택: " choice
        case $choice in
            1) check_storage_status ;;
            2) backup_tsdb ;;
            3) migrate_package_to_binary ;;
            q|Q) log_info "종료"; exit 0 ;;
            *) log_error "잘못된 선택" ;;
        esac
        log_info "작업 완료. 3초 후 메뉴로..."
        sleep 3
    done
}

# 스크립트 실행
main