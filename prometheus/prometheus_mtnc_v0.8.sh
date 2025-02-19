#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 경로 정의
PROM_BASE="/opt/monitoring/prometheus"
PROM_BACKUP="$PROM_BASE/backup"
PROM_TSDB="$PROM_BASE/tsdb"
PROM_CONFIG="$PROM_BASE/prometheus.yml"
PROM_TARGETS="$PROM_BASE/target"
PROM_RULES="$PROM_BASE/rules"

# 전역 변수
SELECTED_VERSION=""

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

# root 권한 체크
check_root() {
    if [ "$(id -u)" != "0" ]; then
        echo "이 스크립트는 root 권한으로 실행해야 합니다."
        exit 1
    fi
}

# 권한 설정 헬퍼 함수
set_prometheus_permissions() {
    local target="$1"
    chown -R prometheus:prometheus "$target"
    if [ $? -ne 0 ]; then
        log_error "권한 설정 실패: $target"
        return 1
    fi
    return 0
}

# 작업 확인 함수
confirm_action() {
    local message="$1"
    local confirm
    read -p "$message 계속 진행하시겠습니까? (y/N): " confirm
    if [[ "$confirm" != "y" ]]; then
        log_info "작업이 취소되었습니다."
        return 1
    fi
    return 0
}

# TSDB 활성 상태 확인
is_active_tsdb() {
    local tsdb_path="$1"
    local wal_dir=$(find_wal_directory "$tsdb_path")
    
    if [ -n "$wal_dir" ]; then
        # WAL 파일의 최근 수정 시간 확인
        local newest_wal=$(find "$wal_dir" -type f -name "[0-9]*" -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1)
        if [ -n "$newest_wal" ]; then
            local mod_time=$(echo "$newest_wal" | cut -d' ' -f1 | cut -d'.' -f1)
            local current_time=$(date +%s)
            local age=$((current_time - mod_time))
            
            # 1시간 이내에 수정된 WAL 파일이 있다면 활성 상태로 간주
            if [ "$age" -lt 3600 ]; then
                return 0
            fi
        fi
    fi
    return 1
}

# TSDB 데이터 디렉토리 찾기 (재귀적, 다중)
find_tsdb_data() {
    local base_path="$1"
    local max_depth=2
    local found_dirs=()
    local active_dir=""
    
    # TSDB 디렉토리 확인 함수 (snapshots 폴더는 제외)
    is_tsdb_dir() {
        local dir="$1"
        if [ "$(basename "$dir")" = "snapshots" ]; then
            return 1
        fi
        if [ -d "$dir/chunks_head" ] || [ -d "$dir/wal" ]; then
            return 0
        fi
        if [ -n "$(find "$dir" -maxdepth 1 -type f -name '*.json' -o -name '*.meta' 2>/dev/null)" ]; then
            return 0
        fi
        return 1
    }
    
    while IFS= read -r dir; do
        if is_tsdb_dir "$dir"; then
            found_dirs+=("$dir")
            if is_active_tsdb "$dir"; then
                active_dir="$dir"
            fi
        fi
    done < <(find "$base_path" -maxdepth $max_depth -type d 2>/dev/null)
    
    if [ ${#found_dirs[@]} -eq 0 ]; then
        return 1
    fi
    
    if [ ${#found_dirs[@]} -eq 1 ]; then
        echo "${found_dirs[0]}"
        return 0
    fi
    
    if [ -n "$active_dir" ]; then
        echo "$active_dir"
        return 0
    fi
    
    echo "여러 TSDB 디렉토리가 발견되었습니다:"
    for i in "${!found_dirs[@]}"; do
        echo "$((i+1))) ${found_dirs[$i]}"
    done
    
    while true; do
        read -p "사용할 TSDB 디렉토리 번호를 선택하세요: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#found_dirs[@]} ]; then
            echo "${found_dirs[$((choice-1))]}"
            return 0
        fi
        log_error "잘못된 선택입니다. 다시 선택해주세요."
    done
}

# WAL 디렉토리 찾기 (재귀적)
find_wal_directory() {
    local base_path="$1"
    local max_depth=3  # 최대 탐색 깊이 증가 (metric2/wal 등의 구조 고려)
    
    # WAL 디렉토리 찾기
    local wal_dir=$(find "$base_path" -maxdepth $max_depth -type d -name "wal" 2>/dev/null | head -n 1)
    
    if [ -n "$wal_dir" ]; then
        echo "$wal_dir"
        return 0
    fi
    
    return 1
}

# TSDB 상태 체크 (통합)
check_tsdb_status() {
    local base_path="$1"
    local binary_path="$2"
    
    # TSDB 데이터 디렉토리 찾기
    local tsdb_data_dir=$(find_tsdb_data "$base_path")
    if [ -z "$tsdb_data_dir" ]; then
        log_error "TSDB 데이터를 찾을 수 없습니다: $base_path"
        return 1
    fi
    
    # WAL 디렉토리 찾기
    local wal_dir=$(find_wal_directory "$base_path")
    if [ -z "$wal_dir" ]; then
        log_warn "WAL 디렉토리를 찾을 수 없습니다: $base_path"
        return 1
    fi
    
    log_info "TSDB 구조 확인:"
    log_info "- 데이터 경로: $tsdb_data_dir"
    log_info "- WAL 경로: $wal_dir"
    
    # WAL 상태 확인
    check_wal_status "$base_path" "$binary_path"
    return $?
}

# WAL 상태 체크 (수동 검증)
check_wal_status() {
    local tsdb_path="$1"
    
    # TSDB 경로가 존재하는지 확인
    if [ ! -d "$tsdb_path" ]; then
        log_error "TSDB 경로가 존재하지 않습니다: $tsdb_path"
        return 1
    fi

    # WAL 디렉토리 찾기 (재귀적)
    local wal_path
    wal_path=$(find_wal_directory "$tsdb_path")
    if [ -z "$wal_path" ]; then
        log_warn "WAL 디렉토리를 찾을 수 없습니다: $tsdb_path 하위에서 검색"
        return 1
    fi

    log_info "WAL 상태 확인 중... ($wal_path)"
    
    # WAL 디렉토리 내에 숫자로 시작하는 비어있지 않은 파일들이 존재하는지 확인
    local valid_files
    valid_files=$(find "$wal_path" -type f -name "[0-9]*" ! -empty)
    if [ -z "$valid_files" ]; then
        log_error "WAL 상태: 손상됨 - 유효한 WAL 파일이 존재하지 않음"
        return 1
    fi

    # 최신 수정 시간을 기준으로 WAL 파일이 너무 오래되지 않았는지 확인 (예: 1일 이내)
    local current_time
    current_time=$(date +%s)
    local threshold=86400  # 임계값: 86400초 (1일)
    local newest_mod=0
    local file
    for file in $valid_files; do
        local mod_time
        mod_time=$(stat -c %Y "$file")
        if [ "$mod_time" -gt "$newest_mod" ]; then
            newest_mod=$mod_time
        fi
    done

    local age=$(( current_time - newest_mod ))
    if [ "$age" -gt "$threshold" ]; then
        log_warn "WAL 상태: 경고 - 가장 최근 WAL 파일의 수정 시각이 ${age}초 전입니다 (임계값: ${threshold}초)"
    else
        log_info "WAL 상태: 정상 - 유효한 WAL 파일이 존재하며, 가장 최근 수정 시각은 ${age}초 전입니다"
    fi

    return 0
}

# OS 타입 감지
detect_os_type() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case "$ID" in
            debian|ubuntu)
                echo "debian"
                ;;
            rhel|centos|rocky|fedora|almalinux)
                echo "redhat"
                ;;
            *)
                echo "unknown"
                ;;
        esac
    else
        echo "unknown"
    fi
}

# 패키지 제거
remove_package() {
    local os_type=$(detect_os_type)
    case "$os_type" in
        debian)
            apt remove --purge prometheus
            ;;
        redhat)
            dnf remove prometheus
            ;;
        *)
            log_error "지원하지 않는 OS입니다."
            return 1
            ;;
    esac
}

# 서비스 파일 위치 확인
get_service_file_path() {
    local prometheus_services=("/usr/lib/systemd/system/prometheus.service" "/etc/systemd/system/prometheus.service")
    local found_services=()

    # 존재하는 모든 서비스 파일 찾기
    for service_path in "${prometheus_services[@]}"; do
        if [ -f "$service_path" ]; then
            found_services+=("$service_path")
        fi
    done

    # 여러 서비스 파일이 발견된 경우 경고
    if [ ${#found_services[@]} -gt 1 ]; then
        log_warn "여러 개의 Prometheus 서비스 파일이 발견되었습니다. 정상적인 동작을 위해 하나만 존재해야 합니다."
        for service_path in "${found_services[@]}"; do
            log_warn "발견된 서비스 파일: $service_path"
        done
        # 패키지 설치 서비스 파일 우선 반환
        for service_path in "${found_services[@]}"; do
            if [[ "$service_path" == *"/usr/lib/systemd/system/"* ]] || 
               [[ "$service_path" == *"/etc/systemd/system/"* ]]; then
                echo "$service_path"
                return 0
            fi
        done
    fi

    # 하나의 서비스 파일만 있는 경우
    if [ ${#found_services[@]} -eq 1 ]; then
        echo "${found_services[0]}"
        return 0
    fi

    # 서비스 파일이 없는 경우 기본값 반환
    echo "/etc/systemd/system/prometheus.service"
    return 1
}

# 패키지 설치 여부 확인
is_package_installed() {
    local os_type
    os_type=$(detect_os_type)
    case "$os_type" in
        debian)
            # dpkg-query를 통해 패키지 상태 확인
            local pkg_status
            pkg_status=$(dpkg-query -W -f='${Status}' prometheus 2>/dev/null)
            # 패키지가 설치된 상태라도, /usr/lib/systemd/system/prometheus.service가 있으면 패키지 설치로 판단
            if [[ "$pkg_status" == "install ok installed" ]]; then
                if [ -f "/usr/lib/systemd/system/prometheus.service" ]; then
                    return 0
                else
                    # 서비스 파일이 없으면 바이너리로 마이그레이션된 것으로 판단
                    return 1
                fi
            else
                return 1
            fi
            ;;
        redhat)
            # redhat 계열도 비슷하게, 서비스 파일 존재 여부를 추가 체크
            rpm -q prometheus >/dev/null && [ -f "/usr/lib/systemd/system/prometheus.service" ]
            return $?
            ;;
        *)
            return 1
            ;;
    esac
}

# 패키지에서 바이너리로 마이그레이션
migrate_package_to_binary() {
    log_info "패키지 설치에서 바이너리 설치로 마이그레이션을 시작합니다..."
    
    # 패키지 설치 확인
    if ! is_package_installed; then
        log_error "패키지로 설치된 Prometheus가 없습니다."
        return 1
    fi

    # 1. 필요한 디렉토리 구조 생성
    log_info "디렉토리 구조를 생성합니다..."
    mkdir -p "$PROM_BASE"/{backup,tsdb,target,rules}
    set_prometheus_permissions "$PROM_BASE"

    # 2. 설정 파일 복사
    log_info "설정 파일을 복사합니다..."
    if ! cp /etc/prometheus/prometheus.yml* "$PROM_CONFIG"; then
        log_error "prometheus.yml 복사 실패"
        return 1
    fi

    if [ -d "/etc/prometheus/target" ]; then
        if ! cp -r /etc/prometheus/target/* "$PROM_TARGETS/"; then
            log_error "target 디렉토리 복사 실패"
            return 1
        fi
    fi
    
    if [ -d "/etc/prometheus/rules" ]; then
        if ! cp -r /etc/prometheus/rules/* "$PROM_RULES/"; then
            log_error "rules 디렉토리 복사 실패"
            return 1
        fi
    fi

    # 3. TSDB 스냅샷 생성 및 백업
    log_info "TSDB 스냅샷을 생성합니다..."
    if ! backup_tsdb; then
        log_error "TSDB 스냅샷 백업 실패"
        return 1
    fi

    # 4. TSDB 데이터 복사
    log_info "TSDB 데이터를 새 위치로 복사합니다..."
    if ! cp -r /var/lib/prometheus/* "$PROM_TSDB/"; then
        log_error "TSDB 복사 실패"
        return 1
    fi
    set_prometheus_permissions "$PROM_TSDB"

    # 5. 새로운 버전 선택 및 서비스 파일 준비
    if ! select_prometheus_version; then
        log_error "Prometheus 버전 선택 실패"
        return 1
    fi
    
    # 6. 기존 패키지 서비스 파일 처리
    local old_service_file="/usr/lib/systemd/system/prometheus.service"
    if [ ! -f "$old_service_file" ]; then
        log_error "패키지 설치 서비스 파일을 찾을 수 없습니다: $old_service_file"
        return 1
    fi

    # 7. 서비스 중지 및 기존 서비스 파일 이동
    log_info "서비스를 전환합니다..."
    systemctl stop prometheus
    mv "$old_service_file" "${old_service_file}.disabled"
    systemctl daemon-reload
    sleep 2

    # 8. 새 서비스 파일 생성 (바이너리용)
    create_service_file
    
    # 9. 권한 설정
    log_info "권한을 설정합니다..."
    set_prometheus_permissions "$PROM_BASE"

    # 10. 새 서비스 시작 및 검증
    if ! verify_prometheus_start; then
        log_error "새 서비스 시작 실패. 롤백을 시작합니다..."
        mv "${old_service_file}.disabled" "$old_service_file"
        systemctl daemon-reload
        sleep 2
        systemctl start prometheus
        return 1
    fi

    # 11. 정상 작동 확인 후 패키지 제거
    sleep 10
    if curl -s http://localhost:9090/-/healthy >/dev/null; then
        log_info "새 서비스가 정상 작동합니다. 패키지를 제거합니다..."
        # 새로 생성한 바이너리용 서비스 파일을 안전한 이름으로 백업하여,
        # 패키지 제거 시 삭제되지 않도록 함.
        cp /etc/systemd/system/prometheus.service /etc/systemd/system/prometheus-binary.service
        if ! remove_package; then
            log_error "패키지 제거 실패"
            return 1
        fi
        # 패키지 제거 후, 바이너리 서비스 파일 이름을 원래대로 복원합니다.
        mv /etc/systemd/system/prometheus-binary.service /etc/systemd/system/prometheus.service
        systemctl daemon-reload
        sleep 2
        systemctl start prometheus
        log_info "마이그레이션이 성공적으로 완료되었습니다."
        return 0
    else
        log_error "새 서비스가 불안정합니다. 롤백을 시작합니다..."
        systemctl stop prometheus
        mv "${old_service_file}.disabled" "$old_service_file"
        systemctl daemon-reload
        sleep 2
        systemctl start prometheus
        return 1
    fi
}


# 스토리지 상태 체크
check_storage_status() {
    log_info "스토리지 상태 확인:"
    echo
    
    # 헤더 출력
    printf "%-20s %-12s %-13s %-12s %-10s %-15s\n" "파일시스템" "크기" "사용됨" "가용" "사용%" "마운트"
    printf "%-15s %-10s %-10s %-10s %-8s %-15s\n" "------------" "--------" "--------" "--------" "------" "------------"
    
    # 루트 파티션 정보
    df -h / | awk 'NR==2 {printf "%-15s %-10s %-10s %-10s %-8s %-15s\n", $1, $2, $3, $4, $5, $6}'
    
    # /opt/monitoring 파티션 정보
    df -h /opt/monitoring | awk 'NR==2 {printf "%-15s %-10s %-10s %-10s %-8s %-15s\n", $1, $2, $3, $4, $5, $6}'
    
    echo
    
    # 패키지 설치 TSDB 크기 확인
    if [ -d "/var/lib/prometheus" ]; then
        local tsdb_dir=$(find_tsdb_data "/var/lib/prometheus")
        if [ -n "$tsdb_dir" ]; then
            local pkg_tsdb_size=$(du -sh "$tsdb_dir" 2>/dev/null | cut -f1)
            log_info "패키지 설치 TSDB 크기 ($tsdb_dir): $pkg_tsdb_size"
            
            # 패키지 설치 WAL 상태 확인
            if [ -f "/usr/bin/prometheus" ]; then
                check_tsdb_status "/var/lib/prometheus" "/usr/bin/prometheus"
            fi
        else
            log_warn "패키지 설치 TSDB 데이터를 찾을 수 없습니다"
        fi
    fi
    
    # 바이너리 설치 TSDB 크기 확인
    if [ -d "$PROM_TSDB" ]; then
        local tsdb_dir=$(find_tsdb_data "$PROM_TSDB")
        if [ -n "$tsdb_dir" ]; then
            local bin_tsdb_size=$(du -sh "$tsdb_dir" 2>/dev/null | cut -f1)
            log_info "바이너리 설치 TSDB 크기 ($tsdb_dir): $bin_tsdb_size"
            
            # 현재 선택된 버전의 바이너리로 WAL 상태 확인
            if [ -n "$SELECTED_VERSION" ] && [ -f "$PROM_BASE/$SELECTED_VERSION/prometheus" ]; then
                check_tsdb_status "$PROM_TSDB" "$PROM_BASE/$SELECTED_VERSION/prometheus"
            else
                # 설치된 버전들 중에서 찾기
                for dir in "$PROM_BASE"/prometheus-*.linux-amd64/; do
                    if [ -d "$dir" ] && [ -f "$dir/prometheus" ]; then
                        check_tsdb_status "$PROM_TSDB" "$dir/prometheus"
                        break
                    fi
                done
            fi
        else
            log_warn "바이너리 설치 TSDB 데이터를 찾을 수 없습니다"
        fi
    fi
}

# 스냅샷 목록 표시
show_snapshots() {
    log_info "기존 스냅샷 목록:"
    local snapshots=$(ls -t "$PROM_BACKUP"/tsdb-*.tar.gz 2>/dev/null)
    if [ -n "$snapshots" ]; then
        while IFS= read -r snapshot; do
            local size=$(du -h "$snapshot" | cut -f1)
            local date=$(basename "$snapshot" | sed 's/tsdb-\([0-9]\{8\}\).tar.gz/\1/')
            log_info "- $(basename "$snapshot") ($size) - 생성일: $date"
        done <<< "$snapshots"
    else
        log_warn "저장된 스냅샷이 없습니다."
    fi
}

# 현재 실행중인 Prometheus 버전 확인
get_current_version() {
    local version=""
    local install_type=""
    local binary_path=""
    
    if systemctl is-active prometheus >/dev/null 2>&1; then
        # API로 버전 확인 시도
        version=$(curl -s --max-time 3 http://localhost:9090/api/v1/status/buildinfo | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        
        # 설치 타입 확인
        if [ -f "/usr/lib/systemd/system/prometheus.service" ]; then
            install_type="패키지"
            binary_path=$(grep "ExecStart=" "/usr/lib/systemd/system/prometheus.service" | sed 's/ExecStart=//' | awk '{print $1}' | tr -d '\\')
        elif [ -f "/etc/systemd/system/prometheus.service" ]; then
            install_type="바이너리"
            binary_path=$(grep "ExecStart=" "/etc/systemd/system/prometheus.service" | sed 's/ExecStart=//' | awk '{print $1}' | tr -d '\\')
        else
            install_type="알 수 없음"
        fi
        
        # API 실패시 바이너리로 확인
        if [ -z "$version" ] && [ ! -z "$binary_path" ] && [ -x "$binary_path" ]; then
            version=$("$binary_path" --version 2>/dev/null | grep "prometheus" | head -1 | awk '{print $3}')
        fi
    fi
    
    if [ -z "$version" ]; then
        log_warn "현재 실행 중인 Prometheus 버전을 찾을 수 없습니다."
        version="unknown"
        install_type="알 수 없음"
        binary_path="알 수 없음"
    fi
    
    log_info "Prometheus 설치 정보:"
    log_info "- 버전: $version"
    log_info "- 설치 유형: $install_type"
    log_info "- 실행 경로: $binary_path"
    
    # 버전만 조용히 반환
    printf "%s" "$version"
}

# TSDB 스냅샷 백업
backup_tsdb() {
    # 패키지/바이너리 설치 확인 및 스냅샷 경로 설정
    local service_file=$(get_service_file_path)
    local snapshot_base_dir

    if is_package_installed; then
        local tsdb_dir=$(find_tsdb_data "/var/lib/prometheus")
        if [ -z "$tsdb_dir" ]; then
            log_error "패키지 설치 TSDB 데이터를 찾을 수 없습니다"
            return 1
        fi
        snapshot_base_dir="$tsdb_dir"
    else
        # local tsdb_dir=$(find_tsdb_data "$PROM_TSDB")
        # if [ -z "$tsdb_dir" ]; then
            # log_error "바이너리 설치 TSDB 데이터를 찾을 수 없습니다"
            # return 1
        # fi
        # snapshot_base_dir="$tsdb_dir"
        snapshot_base_dir="$PROM_TSDB"
    fi

    # TSDB 크기 확인 및 디스크 공간 체크
    local tsdb_size=$(du -s "$snapshot_base_dir" | cut -f1)
    local opt_free=$(df -k /opt/monitoring | awk 'NR==2 {print $4}')

    if [ $opt_free -lt $((tsdb_size * 2)) ]; then
        log_error "/opt/monitoring 파티션의 여유 공간이 부족합니다."
        log_error "필요: $((tsdb_size * 2))K, 가용: ${opt_free}K"
        return 1
    fi

    # TSDB 크기에 따른 예상 시간 표시
    log_info "TSDB 크기: $((tsdb_size/1024/1024))GB"
    log_info "예상 소요 시간: 대략 $(((tsdb_size/1024/1024) * 5))분"

    log_info "TSDB 데이터 위치: $snapshot_base_dir"

    # Admin API 활성화 여부 확인 및 활성화
    if ! systemctl status prometheus | grep -- "--web.enable-admin-api" >/dev/null; then
        log_info "Admin API가 비활성화 상태입니다. 활성화를 진행합니다..."
        local service_backup="${service_file}.backup_$(date +%Y%m%d_%H%M%S)"
        if ! cp "$service_file" "$service_backup"; then
            log_error "서비스 파일 백업 실패"
            return 1
        fi
        
        sed -i '/^ExecStart=/ s/$/ --web.enable-admin-api/' "$service_file"
        
        systemctl daemon-reload
        sleep 2  # daemon-reload 완료 대기
        
        if ! systemctl restart prometheus; then
            log_error "Admin API 활성화를 위한 Prometheus 서비스 재시작 실패"
            mv "$service_backup" "$service_file"
            systemctl daemon-reload
            sleep 2
            systemctl start prometheus
            return 1
        fi
        
        sleep 5  # 서비스 재시작 대기
        if ! systemctl status prometheus | grep -- "--web.enable-admin-api" >/dev/null; then
            log_error "Admin API 활성화 실패"
            mv "$service_backup" "$service_file"
            systemctl daemon-reload
            sleep 2
            systemctl start prometheus
            return 1
        fi
        
        log_info "Admin API가 성공적으로 활성화되었습니다."
    fi

    local today=$(date +%Y%m%d)
    local backup_file="tsdb-${today}.tar.gz"
    
    log_info "TSDB 스냅샷을 API로 생성한뒤 압축백업 시작합니다..."
    
    # 백업 디렉토리 생성 및 권한 설정
    mkdir -p "$PROM_BACKUP"
    set_prometheus_permissions "$PROM_BACKUP"
    
    # Prometheus API를 통한 스냅샷 생성 (snapshots 디렉토리를 /opt/monitoring으로 변경)
    log_info "스냅샷 생성 중..."
    local snapshot_dir="$snapshot_base_dir/snapshots"
    # local snapshot_dir="$PROM_BACKUP/snapshots"
    mkdir -p "$snapshot_dir"
    set_prometheus_permissions "$snapshot_dir"

    local snapshot_response=$(curl -s -XPOST "http://localhost:9090/api/v1/admin/tsdb/snapshot")
    # local snapshot_response=$(curl -s -XPOST "http://localhost:9090/api/v1/admin/tsdb/snapshot?storage.tsdb.wal-directory=$snapshot_dir")
    if [[ $snapshot_response != *"success"* ]]; then
        log_error "스냅샷 생성 실패"
        return 1
    fi
    
    # 대용량 데이터 처리를 위한 충분한 대기 시간
    local wait_time=$((tsdb_size/1024/1024 + 10))  # GB당 1초 + 10초
    log_info "스냅샷 생성 완료 대기 중... (약 ${wait_time}초)"
    sleep $wait_time
    
    # 최신 스냅샷 찾기
    local latest_snapshot=$(ls -td "$snapshot_dir"/* 2>/dev/null | head -1)
    if [ -z "$latest_snapshot" ]; then
        log_error "생성된 스냅샷을 찾을 수 없습니다 (경로: $snapshot_dir)"
        return 1
    fi
    
    # 스냅샷을 백업 위치로 압축
    log_info "스냅샷을 압축 중... ($PROM_BACKUP/$backup_file)"
    if ! (cd "$snapshot_dir" && tar czf "$PROM_BACKUP/$backup_file" "$(basename "$latest_snapshot")"); then
        log_error "백업 실패"
        return 1
    fi
    
    # 백업 파일 권한 설정
    set_prometheus_permissions "$PROM_BACKUP/$backup_file"
    
    log_info "백업 완료: $PROM_BACKUP/$backup_file"
    rm -rf "$latest_snapshot"
    return 0
}

# 버전 호환성 체크
check_version_compatibility() {
    local current_version="$1"
    local target_version="$2"
    
    # 현재 버전에서 메이저 버전만 추출 (예: "3.1.0" -> "3")
    local current_major=${current_version%%.*}
    # 대상 버전에서 메이저 버전만 추출
    local target_major=${target_version%%.*}
    
    # 3.x -> 2.x 다운그레이드 체크
    if [ "$current_major" = "3" ] && [ "$target_major" = "2" ]; then
        return 1
    fi
    
    # 2.x -> 3.x 업그레이드 체크
    if [ "$current_major" = "2" ] && [ "$target_major" = "3" ]; then
        if [ "$current_version" = "2.55.0" ] || [ "$current_version" = "2.55.1" ]; then
            return 0
        else
            return 1
        fi
    fi
    
    # 같은 메이저 버전 내에서는 항상 호환됨
    if [ "$current_major" = "$target_major" ]; then
        return 0
    fi
    
    return 1
}

# 설치 가능한 버전 선택
select_prometheus_version() {
    local current_version=$(get_current_version)
    current_version=$(get_current_version | tail -n1)
    log_info "현재 실행 중인 버전: $current_version"
    
    local versions=()
    for dir in "$PROM_BASE"/prometheus-*.linux-amd64/; do
        if [ -d "$dir" ]; then
            versions+=($(basename "$dir"))
        fi
    done
    
    if [ ${#versions[@]} -eq 0 ]; then
        log_error "설치된 Prometheus 버전을 찾을 수 없습니다."
        return 1
    fi
    
    echo -e "\n사용 가능한 버전:"
    for i in "${!versions[@]}"; do
        local version_number=$(echo "${versions[$i]}" | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
        check_version_compatibility "$current_version" "$version_number"
        local compatible=$?
        
        if [ $compatible -eq 0 ]; then
            echo "$((i+1))) ${versions[$i]} (호환 가능)"
        else
            echo "$((i+1))) ${versions[$i]} (호환 불가)"
        fi
    done
    
    while true; do
        read -p "선택할 버전 번호를 입력하세요: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#versions[@]} ]; then
            SELECTED_VERSION="${versions[$((choice-1))]}"
            local selected_version_number=$(echo "$SELECTED_VERSION" | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
            
            check_version_compatibility "$current_version" "$selected_version_number"
            local compatible=$?
            
            if [ $compatible -ne 0 ]; then
                if [[ "$current_version" == 3.* ]] && [[ "$selected_version_number" == 2.* ]]; then
                    log_error "3.x 버전에서 2.x 버전으로의 다운그레이드는 지원되지 않습니다."
                elif [[ "$current_version" == 2.* ]] && [[ "$selected_version_number" == 3.* ]]; then
                    log_error "2.x -> 3.x 업그레이드는 2.55.0 또는 2.55.1 버전에서만 가능합니다."
                else
                    log_error "선택한 버전은 현재 버전과 호환되지 않습니다."
                fi
                continue
            fi
            
            log_info "선택된 버전: $SELECTED_VERSION"
            return 0
        fi
        log_error "잘못된 선택입니다. 다시 선택해주세요."
    done
}

# 바이너리 버전 업데이트/롤백
update_binary_version() {
    # log_info "바이너리 버전 업데이트/롤백을 시작합니다..."
    if ! confirm_action "바이너리 버전 업데이트/롤백을 진행합니다."; then
        return 1
    fi
    
    # 바이너리 설치 확인
    if is_package_installed; then
        log_error "현재 패키지로 설치된 Prometheus입니다. 먼저 바이너리로 마이그레이션이 필요합니다."
        return 1
    fi
    
    # 현재 버전 확인
    local current_version=$(get_current_version)
    
    # 1. 스냅샷 생성
    log_info "현재 TSDB의 스냅샷을 생성합니다..."
    if ! backup_tsdb; then
        log_error "TSDB 스냅샷 백업 실패"
        return 1
    fi
    
    # 2. 버전 선택
    if ! select_prometheus_version; then
        log_error "Prometheus 버전 선택 실패"
        return 1
    fi
    
    # 3. 서비스 파일 생성
    local backup_date=$(date +%Y%m%d_%H%M%S)
    local service_file=$(get_service_file_path)
    log_info "기존 서비스 파일을 백업합니다..."
    if [ -f "$service_file" ]; then
        if ! cp "$service_file" "${service_file}.backup_${backup_date}"; then
            log_error "서비스 파일 백업 실패"
            return 1
        fi
    fi
    
    create_service_file
    
    # 4. 서비스 시작 및 검증
    if ! verify_prometheus_start; then
        log_error "버전 변경 실패. 이전 버전으로 롤백합니다..."
        if [ -f "${service_file}.backup_${backup_date}" ]; then
            mv "${service_file}.backup_${backup_date}" "$service_file"
            systemctl daemon-reload
            sleep 2
            systemctl start prometheus
        fi
        return 1
    fi
    
    # 5. 권한 재설정
    set_prometheus_permissions "$PROM_BASE"
    
    log_info "버전 변경이 성공적으로 완료되었습니다."
    get_current_version  # 변경된 버전 정보 표시
    return 0
}

# TSDB 동기화
sync_tsdb() {
    # log_info "TSDB 동기화를 시작합니다..."
    if ! confirm_action "TSDB 동기화를 진행합니다."; then
        return 1
    fi

    if [ ! -d "/var/lib/prometheus" ] || [ ! -d "$PROM_TSDB" ]; then
        log_error "패키지 설치 TSDB(/var/lib/prometheus) 또는 바이너리 설치 TSDB($PROM_TSDB)가 존재하지 않습니다."
        return 1
    fi

    # TSDB 데이터 위치 찾기
    local pkg_tsdb_dir=$(find_tsdb_data "/var/lib/prometheus")
    local bin_tsdb_dir=$(find_tsdb_data "$PROM_TSDB")

    if [ -z "$pkg_tsdb_dir" ] || [ -z "$bin_tsdb_dir" ]; then
        log_error "하나 이상의 TSDB 데이터 위치를 찾을 수 없습니다."
        return 1
    fi

    # 각 TSDB의 상태 확인
    local pkg_wal_status=0
    local bin_wal_status=0

    log_info "패키지 설치 WAL 상태 확인 중..."
    if [ -f "/usr/bin/prometheus" ]; then
        check_tsdb_status "/var/lib/prometheus" "/usr/bin/prometheus" || pkg_wal_status=1
    fi

    log_info "바이너리 설치 WAL 상태 확인 중..."
    for dir in "$PROM_BASE"/prometheus-*.linux-amd64/; do
        if [ -d "$dir" ] && [ -f "$dir/prometheus" ]; then
            check_tsdb_status "$PROM_TSDB" "$dir/prometheus" || bin_wal_status=1
            break
        fi
    done

    # 동기화 방향 결정
    local source_path
    local target_path
    local backup_date=$(date +%Y%m%d_%H%M%S)

    if [ $pkg_wal_status -eq 0 ] && [ $bin_wal_status -eq 1 ]; then
        log_info "패키지 설치 TSDB가 정상입니다. 이 데이터로 동기화를 진행합니다."
        source_path="/var/lib/prometheus"
        target_path="$PROM_TSDB"
    elif [ $pkg_wal_status -eq 1 ] && [ $bin_wal_status -eq 0 ]; then
        log_info "바이너리 설치 TSDB가 정상입니다. 이 데이터로 동기화를 진행합니다."
        source_path="$PROM_TSDB"
        target_path="/var/lib/prometheus"
    else
        # 사용자 선택
        log_info "두 TSDB 모두 정상입니다. 동기화 방향을 선택해주세요:"
        echo "1) 패키지 설치 TSDB -> 바이너리 설치 TSDB"
        echo "2) 바이너리 설치 TSDB -> 패키지 설치 TSDB"
        while true; do
            read -p "선택: " sync_choice
            case $sync_choice in
                1)
                    source_path="/var/lib/prometheus"
                    target_path="$PROM_TSDB"
                    break
                    ;;
                2)
                    source_path="$PROM_TSDB"
                    target_path="/var/lib/prometheus"
                    break
                    ;;
                *)
                    log_error "잘못된 선택입니다."
                    ;;
            esac
        done
    fi

    # 대상 TSDB 백업
    log_info "대상 TSDB를 백업합니다..."
    local backup_file="${target_path}_backup_${backup_date}.tar.gz"
    if ! tar czf "$backup_file" -C "$(dirname "$target_path")" "$(basename "$target_path")"; then
        log_error "TSDB 백업 실패"
        return 1
    fi
    set_prometheus_permissions "$backup_file"
    log_info "백업 완료: $backup_file"

    # Prometheus 서비스 중지
    systemctl stop prometheus

    # TSDB 동기화
    log_info "TSDB 동기화를 진행합니다..."
    rm -rf "${target_path:?}"/*
    if ! cp -r "$source_path"/* "$target_path/"; then
        log_error "TSDB 동기화 실패. 백업에서 복구를 시도합니다..."
        rm -rf "${target_path:?}"/*
        tar xzf "$backup_file" -C "$(dirname "$target_path")"
        set_prometheus_permissions "$target_path"
        systemctl start prometheus
        return 1
    fi

    # 권한 설정
    set_prometheus_permissions "$target_path"

    # 서비스 재시작
    log_info "Prometheus 서비스를 재시작합니다..."
    if ! systemctl start prometheus; then
        log_error "서비스 재시작 실패. 백업에서 복구를 시도합니다..."
        rm -rf "${target_path:?}"/*
        tar xzf "$backup_file" -C "$(dirname "$target_path")"
        set_prometheus_permissions "$target_path"
        systemctl start prometheus
        return 1
    fi

    log_info "TSDB 동기화가 성공적으로 완료되었습니다."
    return 0
}

# 설치 타입 확인
check_installation_type() {
    local prometheus_services=("/usr/lib/systemd/system/prometheus.service" "/etc/systemd/system/prometheus.service")
    local service_exists=false

    for service_path in "${prometheus_services[@]}"; do
        if [ -f "$service_path" ]; then
            service_exists=true
            break
        fi
    done

    if is_package_installed; then
        echo "package"
    elif [ "$service_exists" = true ]; then
        echo "binary"
    else
        echo "unknown"
    fi
}

# 서비스 시작 및 검증
verify_prometheus_start() {
    log_info "Prometheus 서비스를 재시작합니다..."
    systemctl daemon-reload
    sleep 2
    
    if ! systemctl restart prometheus; then
        log_error "Prometheus 서비스 시작 실패"
        return 1
    fi
    
    # 서비스 상태 확인 (최대 30초 대기)
    local max_attempts=6
    local attempt=1
    local success=false
    
    log_info "서비스 상태 확인 중..."
    while [ $attempt -le $max_attempts ]; do
        sleep 5  # 5초 간격으로 체크
        if curl -s http://localhost:9090/-/healthy >/dev/null; then
            success=true
            break
        fi
        log_info "상태 확인 시도 ${attempt}/${max_attempts}..."
        attempt=$((attempt + 1))
    done

    if [ "$success" = true ]; then
        log_info "Prometheus 서비스가 정상적으로 시작되었습니다."
        return 0
    else
        log_error "Prometheus 상태 확인 실패"
        return 1
    fi
}

# 서비스 파일 생성
create_service_file() {
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
    --web.enable-admin-api
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

    log_info "서비스 파일이 생성되었습니다."
    systemctl daemon-reload
}

# 메인 메뉴 표시
show_main_menu() {
    echo
    echo "============================================"
    echo "   Prometheus 관리 스크립트 v0.7 (2025.02.19)"
    echo "   SKSDU-PLProm01 (10.46.234.94) 서버 전용"
    echo "============================================"
    echo "1. 스토리지 상태 확인"
    echo "2. 스냅샷 목록 조회"
    echo "3. 스냅샷 생성"
    echo "4. 패키지에서 바이너리로 마이그레이션"
    echo "5. 바이너리 버전 업데이트/롤백"
    echo "6. TSDB 동기화"
    echo "q. 종료"
    echo "============================================"
    echo -n "메뉴를 선택하세요: "
}

# 메인 실행
main() {
    local choice
    
    # root 권한 체크
    check_root
    
    log_info "Prometheus 관리 스크립트를 시작합니다..."
    
    # 기본 디렉토리 권한 확인 및 설정
    if [ -d "$PROM_BASE" ]; then
        log_info "기본 디렉토리 권한을 확인하고 설정합니다..."
        set_prometheus_permissions "$PROM_BASE"
    fi

    while true; do
        show_main_menu
        read choice
        echo
        
        case $choice in
            1)
                log_info "스토리지 상태를 확인합니다..."
                check_storage_status
                echo
                read -p "Enter를 누르면 메인 메뉴로 돌아갑니다..." input
                ;;
            2)
                log_info "스냅샷 목록을 조회합니다..."
                show_snapshots
                echo
                read -p "Enter를 누르면 메인 메뉴로 돌아갑니다..." input
                ;;
            3)
                if ! systemctl is-active prometheus >/dev/null 2>&1; then
                    log_error "Prometheus 서비스가 실행중이지 않습니다."
                    echo
                    read -p "Enter를 누르면 메인 메뉴로 돌아갑니다..." input
                    continue
                fi
                log_info "스냅샷 생성을 시작합니다..."
                backup_tsdb
                echo
                read -p "Enter를 누르면 메인 메뉴로 돌아갑니다..." input
                ;;
            4)
                local current_version=$(get_current_version)
                if [ -f "/etc/systemd/system/prometheus.service" ]; then
                    log_error "이미 바이너리 설치 환경입니다."
                    echo
                    read -p "Enter를 누르면 메인 메뉴로 돌아갑니다..." input
                    continue
                fi
                migrate_package_to_binary
                echo
                read -p "Enter를 누르면 메인 메뉴로 돌아갑니다..." input
                ;;
            5)
                if [ -f "/usr/lib/systemd/system/prometheus.service" ]; then
                    log_error "현재 패키지 설치 환경입니다. 먼저 바이너리로 마이그레이션이 필요합니다."
                    echo
                    read -p "Enter를 누르면 메인 메뉴로 돌아갑니다..." input
                    continue
                fi
                update_binary_version
                echo
                read -p "Enter를 누르면 메인 메뉴로 돌아갑니다..." input
                ;;
            6)
                log_info "TSDB 동기화를 시작합니다..."
                sync_tsdb
                echo
                read -p "Enter를 누르면 메인 메뉴로 돌아갑니다..." input
                ;;
            q|Q)
                log_info "프로그램을 종료합니다."
                exit 0
                ;;
            *)
                log_error "잘못된 선택입니다."
                sleep 1
                ;;
        esac
    done
}

# 스크립트 실행
main