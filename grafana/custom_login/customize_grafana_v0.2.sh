#!/bin/bash

# Grafana 커스터마이징 스크립트
# 작성일: $(date +%Y-%m-%d)

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# sudo 권한 체크
check_sudo() {
    if [[ $EUID -eq 0 ]]; then
        log_info "루트 권한으로 실행 중입니다."
        return 0
    fi
    
    if sudo -n true 2>/dev/null; then
        log_info "sudo 권한이 확인되었습니다."
        return 0
    else
        log_error "이 스크립트는 sudo 권한이 필요합니다."
        log_error "다음 명령어로 실행해주세요: sudo $0"
        exit 1
    fi
}

# Grafana 설치 확인
check_grafana() {
    log_info "Grafana 설치 상태를 확인하는 중..."
    
    if systemctl list-unit-files | grep -q "grafana-server"; then
        log_success "Grafana 서비스가 발견되었습니다."
        return 0
    elif which grafana-server >/dev/null 2>&1; then
        log_success "Grafana가 설치되어 있습니다."
        return 0
    else
        log_error "Grafana가 설치되어 있지 않습니다."
        exit 1
    fi
}

# 파일 존재 확인
check_files() {
    log_info "대상 파일들의 존재를 확인하는 중..."
    
    local grafana_files=(
        "/usr/share/grafana/public/img/fav32.png"
        "/usr/share/grafana/public/img/grafana_icon.svg"
        "/usr/share/grafana/public/img/g8_login_dark.svg"
        "/usr/share/grafana/public/img/g8_login_light.svg"
        "/usr/share/grafana/public/build"
    )
    
    for file in "${grafana_files[@]}"; do
        if [[ ! -e "$file" ]]; then
            log_error "파일/디렉토리를 찾을 수 없습니다: $file"
            exit 1
        fi
    done
    
    log_success "모든 대상 파일이 확인되었습니다."
}

# 커스텀 파일 존재 확인
check_custom_files() {
    log_info "커스텀 파일들의 존재를 확인하는 중..."
    
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local custom_files=(
        "$script_dir/img/fav32.png"
        "$script_dir/img/grafana_icon.svg"
        "$script_dir/img/g8_login_dark.svg"
        "$script_dir/img/g8_login_light.svg"
    )
    
    for file in "${custom_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "커스텀 파일을 찾을 수 없습니다: $file"
            exit 1
        fi
    done
    
    log_success "모든 커스텀 파일이 확인되었습니다."
}

# 백업 생성
create_backup() {
    log_info "백업을 생성하는 중..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="/tmp/grafana_backup_$timestamp"
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local backup_archive="$script_dir/backup/grafana_custom_$(date +%Y%m%d).tar.gz"
    
    # backup 디렉토리 생성
    mkdir -p "$script_dir/backup"
    mkdir -p "$backup_dir/img"
    mkdir -p "$backup_dir/build"
    
    # 파일 백업
    cp /usr/share/grafana/public/img/fav32.png "$backup_dir/img/" 2>/dev/null || log_warning "fav32.png 백업 실패"
    cp /usr/share/grafana/public/img/grafana_icon.svg "$backup_dir/img/" 2>/dev/null || log_warning "grafana_icon.svg 백업 실패"
    cp /usr/share/grafana/public/img/g8_login_dark.svg "$backup_dir/img/" 2>/dev/null || log_warning "g8_login_dark.svg 백업 실패"
    cp /usr/share/grafana/public/img/g8_login_light.svg "$backup_dir/img/" 2>/dev/null || log_warning "g8_login_light.svg 백업 실패"
    
    # JS 파일에서 Welcome to Grafana 포함된 파일들 백업
    local welcome_files=$(grep -l "Welcome to Grafana" /usr/share/grafana/public/build/*.js 2>/dev/null || true)
    if [[ -n "$welcome_files" ]]; then
        for file in $welcome_files; do
            cp "$file" "$backup_dir/build/" 2>/dev/null || log_warning "$(basename $file) 백업 실패"
        done
    fi
    
    # 압축
    tar -czf "$backup_archive" -C "/tmp" "grafana_backup_$timestamp" 2>/dev/null
    
    if [[ $? -eq 0 ]]; then
        log_success "백업이 생성되었습니다: $backup_archive"
        rm -rf "$backup_dir"
    else
        log_error "백업 생성에 실패했습니다."
        exit 1
    fi
}

# 이미지 파일 교체
replace_images() {
    log_info "이미지 파일들을 교체하는 중..."
    
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local files=(
        "fav32.png"
        "grafana_icon.svg"
        "g8_login_dark.svg"
        "g8_login_light.svg"
    )
    
    for file in "${files[@]}"; do
        if cp "$script_dir/img/$file" "/usr/share/grafana/public/img/$file"; then
            log_success "$file 교체 완료"
        else
            log_error "$file 교체 실패"
            exit 1
        fi
    done
}

# 로그인 문구 변경
change_login_text() {
    local new_text="$1"
    log_info "로그인 문구를 '$new_text'로 변경하는 중..."
    
    # Welcome to Grafana가 포함된 .js 파일 찾기 (*.js.map 제외)
    local js_files=$(find /usr/share/grafana/public/build -name "*.js" -not -name "*.js.map" -exec grep -l "Welcome to Grafana" {} \; 2>/dev/null)
    
    if [[ -z "$js_files" ]]; then
        log_warning "Welcome to Grafana 문구를 찾을 수 없습니다."
        return 1
    fi
    
    local changed_count=0
    for file in $js_files; do
        if sed -i "s/Welcome to Grafana/$new_text/g" "$file" 2>/dev/null; then
            log_success "$(basename $file)에서 문구 변경 완료"
            ((changed_count++))
        else
            log_error "$(basename $file)에서 문구 변경 실패"
        fi
    done
    
    if [[ $changed_count -gt 0 ]]; then
        log_success "총 $changed_count개 파일에서 문구가 변경되었습니다."
    else
        log_error "문구 변경에 실패했습니다."
        exit 1
    fi
}

# Grafana 서비스 재시작
restart_grafana() {
    log_info "Grafana 서비스를 재시작하는 중..."
    
    if systemctl restart grafana-server; then
        log_success "Grafana 서비스가 재시작되었습니다."
        
        # 서비스 상태 확인
        sleep 3
        if systemctl is-active --quiet grafana-server; then
            log_success "Grafana 서비스가 정상적으로 실행 중입니다."
        else
            log_warning "Grafana 서비스 상태를 확인해주세요."
        fi
    else
        log_error "Grafana 서비스 재시작에 실패했습니다."
        exit 1
    fi
}

# 메인 메뉴
show_menu() {
    echo ""
    echo "=============================================="
    echo "        Grafana 커스터마이징 스크립트"
    echo "=============================================="
    echo ""
    echo "이 스크립트는 다음 작업을 수행합니다:"
    echo "• 북마크 아이콘 변경"
    echo "• 심볼마크 변경"
    echo "• 로그인 배경 이미지 변경"
    echo "• 로그인 화면 문구 변경"
    echo "• Grafana 서비스 재시작"
    echo ""
}

# 백업 선택 메뉴
backup_menu() {
    while true; do
        echo ""
        echo "=============================================="
        echo "              백업 생성 여부"
        echo "=============================================="
        echo ""
        echo "기존 파일들을 백업하시겠습니까?"
        echo ""
        echo "1) 예 - 백업 생성 후 진행"
        echo "2) 아니오 - 백업 없이 진행"
        echo ""
        read -p "선택하세요 (1-2): " backup_choice
        
        case $backup_choice in
            1)
                echo ""
                log_info "백업을 생성합니다."
                return 0
                ;;
            2)
                echo ""
                log_info "백업을 생성하지 않고 진행합니다."
                return 1
                ;;
            *)
                echo ""
                log_error "잘못된 선택입니다. 1 또는 2를 입력해주세요."
                ;;
        esac
    done
}

# 로그인 문구 선택 메뉴
login_text_menu() {
    while true; do
        echo ""
        echo "=============================================="
        echo "           로그인 화면 문구 선택"
        echo "=============================================="
        echo ""
        echo "로그인 화면에 표시할 문구를 선택하세요:"
        echo ""
        echo "1) Integrated Monitoring"
        echo "2) E2E Observability"
        echo ""
        read -p "선택하세요 (1-2): " text_choice
        
        case $text_choice in
            1)
                echo "Integrated Monitoring"
                return 0
                ;;
            2)
                echo "E2E Observability"
                return 0
                ;;
            *)
                echo ""
                log_error "잘못된 선택입니다. 1 또는 2를 입력해주세요."
                ;;
        esac
    done
}

# 최종 확인 메뉴
confirm_execution() {
    local backup_choice="$1"
    local login_text="$2"
    
    echo ""
    echo "=============================================="
    echo "              작업 내용 확인"
    echo "=============================================="
    echo ""
    echo "다음 작업을 수행합니다:"
    echo ""
    if [[ $backup_choice -eq 1 ]]; then
        echo "• 기존 파일 백업 생성"
    else
        echo "• 백업 생성하지 않음"
    fi
    echo "• 이미지 파일 교체 (북마크, 심볼마크, 로그인 배경)"
    echo "• 로그인 문구 변경: '$login_text'"
    echo "• Grafana 서비스 재시작"
    echo ""
    
    while true; do
        read -p "위 작업을 진행하시겠습니까? (y/N): " confirm
        
        case $confirm in
            [yY]|[yY][eE][sS])
                return 0
                ;;
            [nN]|[nN][oO]|"")
                log_info "작업이 취소되었습니다."
                exit 0
                ;;
            *)
                echo ""
                log_error "y(예) 또는 n(아니오)을 입력해주세요."
                ;;
        esac
    done
}

# 메인 실행 함수
main() {
    show_menu
    
    # 1. sudo 권한 체크
    check_sudo
    
    # 2. Grafana 설치 확인
    check_grafana
    
    # 3. 파일 존재 확인
    check_files
    check_custom_files
    
    # 4. 백업 여부 선택
    backup_menu
    local backup_choice=$?
    
    # 5. 로그인 문구 선택
    local selected_text=$(login_text_menu)
    
    # 6. 최종 확인
    confirm_execution $backup_choice "$selected_text"
    
    # 7. 작업 실행
    echo ""
    echo "=============================================="
    echo "            커스터마이징 작업 시작"
    echo "=============================================="
    echo ""
    
    # 백업 생성 (선택한 경우)
    if [[ $backup_choice -eq 0 ]]; then
        create_backup
        echo ""
    fi
    
    # 이미지 파일 교체
    replace_images
    echo ""
    
    # 로그인 문구 변경
    change_login_text "$selected_text"
    echo ""
    
    # Grafana 서비스 재시작
    restart_grafana
    
    echo ""
    echo "=============================================="
    echo "              작업 완료"
    echo "=============================================="
    echo ""
    log_success "모든 작업이 성공적으로 완료되었습니다!"
    echo ""
    log_info "브라우저에서 Grafana 페이지를 새로고침하여 변경사항을 확인하세요."
    echo ""
}

# 스크립트 시작점
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi