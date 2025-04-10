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
    
    # TSDB 크기 확인
    if [ -d "$PROM_TSDB" ]; then
        local tsdb_size=$(du -sh "$PROM_TSDB" 2>/dev/null | cut -f1)
        log_info "현재 TSDB 크기: $tsdb_size"
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

# TSDB 스냅샷 백업
backup_tsdb() {
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
    
    # 최신 스냅샷 디렉토리 찾기
    local snapshot_dir="$PROM_TSDB/snapshots"
    local latest_snapshot=$(ls -td "$snapshot_dir"/* 2>/dev/null | head -1)
    
    if [ -z "$latest_snapshot" ]; then
        log_error "생성된 스냅샷을 찾을 수 없습니다"
        return 1
    fi
    
    # 스냅샷을 백업 위치로 복사 및 압축
    log_info "스냅샷을 백업 위치로 복사 및 압축 중... ($PROM_BACKUP/$backup_file)"
    (cd "$snapshot_dir" && tar czf "$PROM_BACKUP/$backup_file" "$(basename "$latest_snapshot")")
    
    if [ $? -eq 0 ]; then
        log_info "백업 완료: $PROM_BACKUP/$backup_file"
        # 원본 스냅샷 정리
        rm -rf "$latest_snapshot"
        return 0
    else
        log_error "백업 실패"
        return 1
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
    
    echo
    log_info "Prometheus 설치 정보:"
    log_info "- 버전: $version"
    log_info "- 설치 유형: $install_type"
    log_info "- 실행 경로: $binary_path"
    
    echo "$version"  # 기존 호출 코드와의 호환성을 위해 버전만 반환
}

# 버전 호환성 체크
check_version_compatibility() {
    local current_version="$1"
    local target_version="$2"
    
    # 2.x -> 3.x 업그레이드는 2.55.0 또는 2.55.1 버전에서만 가능
    if [[ "$current_version" == 2.* ]] && [[ "$target_version" == 3.* ]]; then
        if [[ "$current_version" == "2.55.0" ]] || [[ "$current_version" == "2.55.1" ]]; then
            return 0
        else
            return 1
        fi
    elif [[ "$current_version" == 3.* ]] && [[ "$target_version" == 2.* ]]; then
        # 3.x -> 2.x 다운그레이드 불가
        return 1
    fi
    return 0  # 같은 메이저 버전 내 업그레이드는 허용
}

# 패키지 설치 여부 확인 및 마이그레이션 준비
prepare_migration() {
    if [ -f "/lib/systemd/system/prometheus.service" ]; then
        log_info "패키지로 설치된 Prometheus가 발견되었습니다. 바이너리 환경으로 마이그레이션을 준비합니다."
        
        # 디렉토리 구조 생성
        mkdir -p "$PROM_TSDB" "$PROM_TARGETS" "$PROM_RULES"
        
        # 설정 파일 복사
        if [ -f "/etc/prometheus/prometheus.yml" ]; then
            cp "/etc/prometheus/prometheus.yml" "$PROM_CONFIG"
            log_info "설정 파일 복사 완료: $PROM_CONFIG"
        fi
        
        # 타겟 파일 복사
        if [ -d "/etc/prometheus/target" ]; then
            shopt -s nullglob
            local target_files=(/etc/prometheus/target/*)
            if [ ${#target_files[@]} -gt 0 ]; then
                cp -r "${target_files[@]}" "$PROM_TARGETS/"
                log_info "타겟 설정 파일 복사 완료: $PROM_TARGETS/"
            else
                log_warn "타겟 디렉토리가 비어있습니다"
            fi
            shopt -u nullglob
        fi
        
        # 룰 파일 복사
        if [ -d "/etc/prometheus/rules" ]; then
            shopt -s nullglob
            local rule_files=(/etc/prometheus/rules/*)
            if [ ${#rule_files[@]} -gt 0 ]; then
                cp -r "${rule_files[@]}" "$PROM_RULES/"
                log_info "룰 파일 복사 완료: $PROM_RULES/"
            else
                log_warn "룰 디렉토리가 비어있습니다"
            fi
            shopt -u nullglob
        fi
        
        # 권한 설정
        chown -R prometheus:prometheus "$PROM_BASE"
        
        return 0
    else
        log_info "이미 바이너리 설치 환경입니다."
        return 0
    fi
}

# 최신 백업에서 TSDB 복원
restore_latest_backup() {
    local latest_backup=$(ls -t "$PROM_BACKUP"/tsdb-*.tar.gz 2>/dev/null | head -1)
    
    if [ -z "$latest_backup" ]; then
        log_error "복원할 백업 파일을 찾을 수 없습니다."
        return 1
    fi
    
    log_info "최신 백업 파일에서 TSDB를 복원합니다: $(basename "$latest_backup")"
    
    # 스냅샷 디렉토리 생성
    mkdir -p "$PROM_TSDB/snapshots"
    
    # 백업 파일 압축 해제
    tar xzf "$latest_backup" -C "$PROM_TSDB/snapshots"
    
    if [ $? -eq 0 ]; then
        log_info "TSDB 복원 완료"
        chown -R prometheus:prometheus "$PROM_TSDB"
        return 0
    else
        log_error "TSDB 복원 실패"
        return 1
    fi
}

# 설치 가능한 버전 선택
select_prometheus_version() {
    local current_version=$(get_current_version)
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
    
    log_info "발견된 버전들:"
    for version in "${versions[@]}"; do
        local version_number=$(echo "$version" | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
        if check_version_compatibility "$current_version" "$version_number"; then
            log_info "- $version (호환 가능)"
        else
            log_info "- $version (호환 불가)"
        fi
    done
    
    # 현재 2.x 버전이고 3.x로 업그레이드하려는 경우 2.55.0 또는 2.55.1 중간 단계 필요
    if [[ "$current_version" == 2.* ]] && [[ "$current_version" != "2.55.0" ]] && [[ "$current_version" != "2.55.1" ]]; then
        log_info "3.x 버전으로 업그레이드하기 위해서는 먼저 2.55.0 또는 2.55.1 버전으로 업그레이드해야 합니다."
        for i in "${!versions[@]}"; do
            if [[ "${versions[$i]}" == *"2.55."[01]* ]]; then
                SELECTED_VERSION="${versions[$i]}"
                log_info "2.55.x 버전을 자동으로 선택했습니다: $SELECTED_VERSION"
                return 0
            fi
        done
        log_error "2.55.0 또는 2.55.1 버전을 찾을 수 없습니다. 먼저 해당 버전을 설치해주세요."
        return 1
    fi
    
    # 버전 선택 메뉴 표시
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
            SELECTED_VERSION="${versions[$((choice-1))]}";
            local selected_version_number=$(echo "$SELECTED_VERSION" | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
            
            if ! check_version_compatibility "$current_version" "$selected_version_number"; then
                log_error "선택한 버전은 현재 버전과 호환되지 않습니다."
                log_error "2.x -> 3.x 업그레이드는 2.55.0 또는 2.55.1 버전에서만 가능합니다."
                log_error "3.x -> 2.x 다운그레이드는 지원되지 않습니다."
                continue
            fi
            
            log_info "선택된 버전: $SELECTED_VERSION"
            return 0
        fi
        log_error "잘못된 선택입니다. 다시 선택해주세요."
    done
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

show_main_menu() {
    echo 
    echo "============================================"
    echo "   SQMS Prometheus 유지관리 스크립트 v0.5"
    echo "============================================"
    echo " 1. 스토리지 상태 확인"
    echo " 2. 스냅샷 목록 조회"
    echo " 3. 스냅샷 생성"
    echo " 4. 버전 업그레이드/롤백 실행"
    echo " q. 종료"
    echo "============================================"
    echo -n "메뉴를 선택하세요... "
}

# 메인 실행
main() {
    local choice

    log_info "SQMS Prometheus 유지관리 스크립트 v0.5를 시작합니다."
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
                log_info "TSDB 스냅샷을 생성합니다..."
                backup_tsdb
                echo
                read -p "Enter를 누르면 메인 메뉴로 돌아갑니다..." input
                ;;
            4)
                log_info "버전 업그레이드/롤백을 실행합니다..."
                run_upgrade
                echo
                read -p "Enter를 누르면 메인 메뉴로 돌아갑니다..." input
                ;;
            q|Q)
                echo "프로그램을 종료합니다."
                exit 0
                ;;
            *)
                log_error "잘못된 선택입니다."
                sleep 1
                ;;
        esac
    done
}

# 업그레이드 실행 함수
run_upgrade() {
    # 스토리지 상태 확인
    check_storage_status
    
    # 현재 버전 확인
    local current_version=$(get_current_version)
    local is_package_install=false
    
    if [ -f "/lib/systemd/system/prometheus.service" ]; then
        is_package_install=true
    fi
    
    # 스냅샷 목록 표시
    show_snapshots
    
    # 패키지에서 바이너리로의 마이그레이션인 경우
    if [ "$is_package_install" = true ]; then
        log_info "패키지 설치에서 바이너리 설치로 마이그레이션을 진행합니다..."
        
        # 백업 여부 확인
        read -p "현재 TSDB의 스냅샷 백업을 진행하시겠습니까? (y/n): " do_backup
        if [ "$do_backup" = "y" ]; then
            backup_tsdb || return 1
        fi
        
        # 마이그레이션 준비
        prepare_migration || return 1
        
        # TSDB 복원
        read -p "백업된 TSDB를 복원하시겠습니까? (y/n): " do_restore
        if [ "$do_restore" = "y" ]; then
            restore_latest_backup || return 1
        fi
    else
        # 3.x 버전 간 업데이트/롤백인 경우
        log_info "바이너리 버전 간 업데이트/롤백을 진행합니다..."
    fi
    
    # 버전 선택
    select_prometheus_version || return 1
    
    # 서비스 파일 생성
    create_service_file
    
    log_info "모든 작업이 완료되었습니다."
    log_info "다음 명령어로 서비스를 시작할 수 있습니다:"
    echo "systemctl start prometheus"
}

# 스크립트 실행
main
