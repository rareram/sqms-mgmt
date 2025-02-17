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

# WAL 디렉토리 찾기 (재귀적)
find_wal_directory() {
    local base_path="$1"
    local wal_dir
    wal_dir=$(find "$base_path" -type d -name "wal" 2>/dev/null | head -n 1)
    echo "$wal_dir"
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

# 패키지에서 바이너리로 마이그레이션
migrate_package_to_binary() {
    log_info "패키지 설치에서 바이너리 설치로 마이그레이션을 시작합니다..."
    
    # 패키지 설치 확인
    if [ ! -f "/lib/systemd/system/prometheus.service" ]; then
        log_error "패키지로 설치된 Prometheus가 없습니다."
        return 1
    fi

    # 1. 필요한 디렉토리 구조 생성
    log_info "디렉토리 구조를 생성합니다..."
    mkdir -p "$PROM_BASE"/{backup,tsdb,target,rules}

    # 2. 설정 파일 복사
    log_info "설정 파일을 복사합니다..."
    if ! cp /etc/prometheus/prometheus.yml "$PROM_CONFIG"; then
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

    # 3. TSDB 스냅샷 생성 및 백업 전에 admin API 활성화 확인
    log_info "Admin API 활성화 상태를 확인합니다..."
    if ! systemctl status prometheus | grep -- "--web.enable-admin-api" >/dev/null; then
        log_info "Admin API가 비활성화 상태입니다. 활성화를 진행합니다..."
        
        # 기존 서비스 파일 백업
        local service_backup="/lib/systemd/system/prometheus.service.backup_$(date +%Y%m%d_%H%M%S)"
        cp /lib/systemd/system/prometheus.service "$service_backup"
        
        # ExecStart 라인을 찾아서 --web.enable-admin-api 옵션 추가
        sed -i '/^ExecStart=/ s/$/ --web.enable-admin-api/' /lib/systemd/system/prometheus.service
        
        # 서비스 재시작
        systemctl daemon-reload
        if ! systemctl restart prometheus; then
            log_error "Admin API 활성화를 위한 Prometheus 서비스 재시작 실패"
            mv "$service_backup" /lib/systemd/system/prometheus.service
            systemctl daemon-reload
            systemctl start prometheus
            return 1
        fi
        
        # API 활성화 확인
        sleep 2
        if ! systemctl status prometheus | grep -- "--web.enable-admin-api" >/dev/null; then
            log_error "Admin API 활성화 실패"
            mv "$service_backup" /lib/systemd/system/prometheus.service
            systemctl daemon-reload
            systemctl start prometheus
            return 1
        fi
        
        log_info "Admin API가 성공적으로 활성화되었습니다."
    fi

    # 4. TSDB 스냅샷 생성 및 백업
    log_info "TSDB 스냅샷을 생성합니다..."
    if ! backup_tsdb; then
        log_error "TSDB 스냅샷 백업 실패"
        return 1
    fi

    # 5. TSDB 데이터 복사
    log_info "TSDB 데이터를 새 위치로 복사합니다..."
    if ! cp -r /var/lib/prometheus/* "$PROM_TSDB/"; then
        log_error "TSDB 복사 실패"
        return 1
    fi

    # 6. 새로운 버전 선택 및 서비스 파일 준비
    if ! select_prometheus_version; then
        log_error "Prometheus 버전 선택 실패"
        return 1
    fi
    
    # 7. 기존 서비스 파일 백업
    local backup_date=$(date +%Y%m%d_%H%M%S)
    log_info "기존 서비스 파일을 백업합니다..."
    if ! cp /lib/systemd/system/prometheus.service "/lib/systemd/system/prometheus.service.package_backup_${backup_date}"; then
        log_error "서비스 파일 백업 실패"
        return 1
    fi

    # 8. 새 서비스 파일 생성
    create_service_file

    # 9. 권한 설정
    log_info "권한을 설정합니다..."
    chown -R prometheus:prometheus "$PROM_BASE"

    # 10. 서비스 전환
    log_info "서비스를 전환합니다..."
    systemctl stop prometheus
    mv "/lib/systemd/system/prometheus.service" "/lib/systemd/system/prometheus.service.disabled"
    systemctl daemon-reload

    # 11. 새 서비스 시작 및 검증
    if ! verify_prometheus_start; then
        log_error "새 서비스 시작 실패. 롤백을 시작합니다..."
        # 롤백 프로세스
        mv "/lib/systemd/system/prometheus.service.disabled" "/lib/systemd/system/prometheus.service"
        systemctl daemon-reload
        systemctl start prometheus
        log_error "원래 서비스로 롤백되었습니다."
        return 1
    fi

    # 12. 정상 작동 확인 후 패키지 제거
    log_info "새 서비스가 정상 작동하는지 확인합니다..."
    sleep 10  # 서비스 안정화 대기
    
    if curl -s http://localhost:9090/-/healthy >/dev/null; then
        log_info "새 서비스가 정상 작동합니다. 패키지를 제거합니다..."
        apt remove --purge prometheus
        log_info "마이그레이션이 성공적으로 완료되었습니다."
        log_info "백업된 스냅샷은 $PROM_BACKUP 에서 확인할 수 있습니다."
        return 0
    else
        log_error "새 서비스가 불안정합니다. 롤백을 시작합니다..."
        # 롤백 프로세스
        systemctl stop prometheus
        mv "/lib/systemd/system/prometheus.service.disabled" "/lib/systemd/system/prometheus.service"
        systemctl daemon-reload
        systemctl start prometheus
        log_error "원래 서비스로 롤백되었습니다."
        return 1
    fi
}

# 스토리지 상태 체크
check_storage_status() {
    log_info "스토리지 상태 확인:"
    echo
    
    # 헤더 출력
    printf "%-15s %-10s %-10s %-10s %-8s %-15s\n" "파일시스템" "크기" "사용됨" "가용" "사용%" "마운트"
    printf "%-15s %-10s %-10s %-10s %-8s %-15s\n" "------------" "--------" "--------" "--------" "------" "------------"
    
    # 루트 파티션 정보
    df -h / | awk 'NR==2 {printf "%-15s %-10s %-10s %-10s %-8s %-15s\n", $1, $2, $3, $4, $5, $6}'
    
    # /opt/monitoring 파티션 정보
    df -h /opt/monitoring | awk 'NR==2 {printf "%-15s %-10s %-10s %-10s %-8s %-15s\n", $1, $2, $3, $4, $5, $6}'
    
    echo
    
    # 패키지 설치 TSDB 크기 확인
    if [ -d "/var/lib/prometheus" ]; then
        local pkg_tsdb_size=$(du -sh "/var/lib/prometheus" 2>/dev/null | cut -f1)
        log_info "패키지 설치 TSDB 크기 (/var/lib/prometheus): $pkg_tsdb_size"
        
        # 패키지 설치 WAL 상태 확인
        if [ -f "/usr/bin/prometheus" ]; then
            check_wal_status "/var/lib/prometheus" "/usr/bin/prometheus"
        fi
    fi
    
    # 바이너리 설치 TSDB 크기 확인
    if [ -d "$PROM_TSDB" ]; then
        local bin_tsdb_size=$(du -sh "$PROM_TSDB" 2>/dev/null | cut -f1)
        log_info "바이너리 설치 TSDB 크기 ($PROM_TSDB): $bin_tsdb_size"
        
        # 현재 선택된 버전의 바이너리로 WAL 상태 확인
        if [ -n "$SELECTED_VERSION" ] && [ -f "$PROM_BASE/$SELECTED_VERSION/prometheus" ]; then
            check_wal_status "$PROM_TSDB" "$PROM_BASE/$SELECTED_VERSION/prometheus"
        else
            # 설치된 버전들 중에서 찾기
            for dir in "$PROM_BASE"/prometheus-*.linux-amd64/; do
                if [ -d "$dir" ] && [ -f "$dir/prometheus" ]; then
                    check_wal_status "$PROM_TSDB" "$dir/prometheus"
                    break
                fi
            done
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
        if [ -f "/lib/systemd/system/prometheus.service" ]; then
            install_type="패키지"
            binary_path=$(grep "ExecStart=" "/lib/systemd/system/prometheus.service" | sed 's/ExecStart=//' | awk '{print $1}' | tr -d '\\')
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
    local snapshot_base_dir
    if [ -f "/lib/systemd/system/prometheus.service" ]; then
        snapshot_base_dir="/var/lib/prometheus"
    else
        snapshot_base_dir="$PROM_TSDB"
    fi

    # Admin API 활성화 여부 확인
    if ! systemctl status prometheus | grep -- "--web.enable-admin-api" >/dev/null; then
        log_error "스냅샷 백업을 위한 Prometheus admin API가 활성화되어 있지 않습니다."
        log_error "서비스 파일에 --web.enable-admin-api 옵션을 추가해서 재시작 해주세요."
        return 1
    fi

    local today=$(date +%Y%m%d)
    local backup_file="tsdb-${today}.tar.gz"
    
    log_info "TSDB 스냅샷을 API로 생성한뒤 압축백업 시작합니다..."
    
    # 백업 디렉토리 생성
    mkdir -p "$PROM_BACKUP"
    
    # Prometheus API를 통한 스냅샷 생성
    log_info "스냅샷 생성 중..."
    local snapshot_response=$(curl -s -XPOST http://localhost:9090/api/v1/admin/tsdb/snapshot)
    if [[ $snapshot_response != *"success"* ]]; then
        log_error "스냅샷 생성 실패"
        return 1
    fi
    
    # 스냅샷 생성 대기
    sleep 5  # 스냅샷 생성 완료 대기
    
    # 최신 스냅샷 디렉토리 찾기
    local snapshot_dir="$snapshot_base_dir/snapshots"
    # snapshots 디렉토리 존재 여부 확인
    if [ ! -d "$snapshot_dir" ]; then
        log_error "스냅샷 디렉토리가 존재하지 않습니다: $snapshot_dir"
        return 1
    fi

    local latest_snapshot=$(ls -td "$snapshot_dir"/* 2>/dev/null | head -1)
    if [ -z "$latest_snapshot" ]; then
        log_error "생성된 스냅샷을 찾을 수 없습니다 (경로: $snapshot_dir)"
        return 1
    fi
    
    # 스냅샷을 백업 위치로 복사 및 압축
    log_info "스냅샷을 백업 위치로 복사 및 압축 중... ($PROM_BACKUP/$backup_file)"
    if ! (cd "$snapshot_dir" && tar czf "$PROM_BACKUP/$backup_file" "$(basename "$latest_snapshot")"); then
        log_error "백업 실패"
        return 1
    fi
    
    log_info "백업 완료: $PROM_BACKUP/$backup_file"
    # 원본 스냅샷 정리
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
    log_info "바이너리 버전 업데이트/롤백을 시작합니다..."
    
    # 바이너리 설치 확인
    if [ -f "/lib/systemd/system/prometheus.service" ]; then
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
    log_info "기존 서비스 파일을 백업합니다..."
    if [ -f "/etc/systemd/system/prometheus.service" ]; then
        if ! cp /etc/systemd/system/prometheus.service "/etc/systemd/system/prometheus.service.backup_${backup_date}"; then
            log_error "서비스 파일 백업 실패"
            return 1
        fi
    fi
    
    create_service_file
    
    # 4. 서비스 시작 및 검증
    if ! verify_prometheus_start; then
        log_error "버전 변경 실패. 이전 버전으로 롤백합니다..."
        if [ -f "/etc/systemd/system/prometheus.service.backup_${backup_date}" ]; then
            mv "/etc/systemd/system/prometheus.service.backup_${backup_date}" "/etc/systemd/system/prometheus.service"
            systemctl daemon-reload
            systemctl start prometheus
        fi
        return 1
    fi
    
    log_info "버전 변경이 성공적으로 완료되었습니다."
    get_current_version  # 변경된 버전 정보 표시
    return 0
}

# TSDB 동기화
sync_tsdb() {
    log_info "TSDB 동기화를 시작합니다..."

    # 두 TSDB 경로 존재 확인
    if [ ! -d "/var/lib/prometheus" ] || [ ! -d "$PROM_TSDB" ]; then
        log_error "패키지 설치 TSDB(/var/lib/prometheus) 또는 바이너리 설치 TSDB($PROM_TSDB)가 존재하지 않습니다."
        return 1
    fi

    # 각 TSDB의 WAL 상태 확인
    local pkg_wal_status=0
    local bin_wal_status=0

    log_info "패키지 설치 WAL 상태 확인 중..."
    if [ -f "/usr/bin/prometheus" ]; then
        check_wal_status "/var/lib/prometheus" "/usr/bin/prometheus" || pkg_wal_status=1
    fi

    log_info "바이너리 설치 WAL 상태 확인 중..."
    for dir in "$PROM_BASE"/prometheus-*.linux-amd64/; do
        if [ -d "$dir" ] && [ -f "$dir/prometheus" ]; then
            check_wal_status "$PROM_TSDB" "$dir/prometheus" || bin_wal_status=1
            break
        fi
    done

    # 두 WAL 모두 손상된 경우
    if [ $pkg_wal_status -eq 1 ] && [ $bin_wal_status -eq 1 ]; then
        log_error "두 TSDB의 WAL이 모두 손상되었습니다. 동기화를 진행할 수 없습니다."
        return 1
    fi

    # WAL 상태에 따른 동기화 방향 결정
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
        # 둘 다 정상인 경우, 더 최신 데이터를 가진 쪽을 선택
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
    log_info "백업 완료: $backup_file"

    # Prometheus 서비스 중지
    log_info "Prometheus 서비스를 중지합니다..."
    systemctl stop prometheus

    # TSDB 동기화
    log_info "TSDB 동기화를 진행합니다..."
    rm -rf "${target_path:?}"/*  # 대상 디렉토리 비우기
    if ! cp -r "$source_path"/* "$target_path/"; then
        log_error "TSDB 동기화 실패. 백업에서 복구를 시도합니다..."
        rm -rf "${target_path:?}"/*
        tar xzf "$backup_file" -C "$(dirname "$target_path")"
        systemctl start prometheus
        return 1
    fi

    # 권한 설정
    chown -R prometheus:prometheus "$target_path"

    # 서비스 재시작
    log_info "Prometheus 서비스를 재시작합니다..."
    if ! systemctl start prometheus; then
        log_error "서비스 재시작 실패. 백업에서 복구를 시도합니다..."
        rm -rf "${target_path:?}"/*
        tar xzf "$backup_file" -C "$(dirname "$target_path")"
        systemctl start prometheus
        return 1
    fi

    log_info "TSDB 동기화가 성공적으로 완료되었습니다."
    return 0
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
    
    # 서비스 상태 확인
    sleep 2
    if ! curl -s http://localhost:9090/-/healthy >/dev/null; then
        log_error "Prometheus 상태 확인 실패"
        return 1
    fi
    
    log_info "Prometheus 서비스가 정상적으로 시작되었습니다."
    return 0
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
    echo "     Prometheus 관리 스크립트 v0.6"
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
    
    log_info "Prometheus 관리 스크립트를 시작합니다..."
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
                if [ -f "/lib/systemd/system/prometheus.service" ]; then
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