#!/bin/bash

# Grafana 커스터마이징 스크립트 v0.5
# 작성일: 2025-12-08
#
# 변경사항 v0.5:
# - 해시 파일명이 여러 개일 경우 모두 교체하도록 수정
# - 레거시 경로의 grafana_icon.svg도 교체하도록 기능 추가
# - 스크립트 실행 시 루트 권한을 요구하도록 변경하여 안정성 향상

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 전역 변수
BACKUP_ENABLED=false
LOGIN_TEXT=""

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

# sudo 권한 체크 (v0.5 변경)
check_sudo() {
    if [[ $EUID -ne 0 ]]; then
        log_error "이 스크립트는 루트(root) 권한으로 실행해야 합니다."
        log_error "다음 명령어를 사용해 다시 실행해주세요: sudo $0"
        exit 1
    fi
    log_info "루트 권한으로 실행 확인되었습니다."
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

# 해시가 포함된 파일명 목록 찾기 (v0.5 변경)
find_hashed_files() {
    local base_name="$1"
    local search_dir="$2"
    
    local name_without_ext="${base_name%.*}"
    local extension="${base_name##*.}"
    
    # 패턴으로 모든 파일 찾기
    local found_files=$(find "$search_dir" -name "${name_without_ext}.*.${extension}" 2>/dev/null)
    
    if [[ -n "$found_files" ]]; then
        echo "$found_files"
        return 0
    else
        return 1
    fi
}

# 파일 존재 확인
check_files() {
    log_info "대상 파일들의 존재를 확인하는 중..."
    
    local required_dirs=(
        "/usr/share/grafana/public/img"
        "/usr/share/grafana/public/build"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_error "필수 디렉토리를 찾을 수 없습니다: $dir"
            exit 1
        fi
    done

    local static_img_dir="/usr/share/grafana/public/build/static/img"
    local legacy_img_dir="/usr/share/grafana/public/img"
    local all_found=true

    if [[ ! -f "$legacy_img_dir/fav32.png" ]]; then
        log_error "필수 파일을 찾을 수 없습니다: $legacy_img_dir/fav32.png"
        all_found=false
    fi

    local image_files=("grafana_icon.svg" "g8_login_dark.svg" "g8_login_light.svg")
    for file in "${image_files[@]}"; do
        local hashed_files=$(find_hashed_files "$file" "$static_img_dir")
        local legacy_file="$legacy_img_dir/$file"
        
        if [[ -z "$hashed_files" && ! -f "$legacy_file" ]]; then
            log_warning "교체할 대상 파일을 찾을 수 없습니다: $file"
            all_found=false
        fi
    done

    if ! $all_found; then
        log_error "일부 필수 파일이 없어 스크립트를 계속할 수 없습니다."
        # exit 1 # 경고만 표시하고 계속 진행하도록 주석 처리
    fi

    log_success "대상 파일 확인 완료."
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

# 백업 생성 (v0.5 변경)
create_backup() {
    log_info "백업을 생성하는 중..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="/tmp/grafana_backup_$timestamp"
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local backup_archive="$script_dir/backup/grafana_custom_$(date +%Y%m%d).tar.gz"
    
    mkdir -p "$script_dir/backup"
    mkdir -p "$backup_dir/img"
    mkdir -p "$backup_dir/static_img"
    mkdir -p "$backup_dir/build"
    
    local legacy_img_dir="/usr/share/grafana/public/img"
    local static_img_dir="/usr/share/grafana/public/build/static/img"

    cp "$legacy_img_dir/fav32.png" "$backup_dir/img/" 2>/dev/null || log_warning "fav32.png 백업 실패"
    
    if [[ -f "$legacy_img_dir/grafana_icon.svg" ]]; then
        cp "$legacy_img_dir/grafana_icon.svg" "$backup_dir/img/" 2>/dev/null || log_warning "레거시 grafana_icon.svg 백업 실패"
    fi
    
    local image_files=("grafana_icon.svg" "g8_login_dark.svg" "g8_login_light.svg")
    for file in "${image_files[@]}"; do
        local found_files=$(find_hashed_files "$file" "$static_img_dir")
        if [[ -n "$found_files" ]]; then
            while IFS= read -r line; do
                cp "$line" "$backup_dir/static_img/" 2>/dev/null || log_warning "$(basename "$line") 백업 실패"
            done <<< "$found_files"
        fi
    done
    
    local welcome_files=$(grep -l "Welcome to Grafana" /usr/share/grafana/public/build/*.js 2>/dev/null || true)
    if [[ -n "$welcome_files" ]]; then
        for file in $welcome_files; do
            cp "$file" "$backup_dir/build/" 2>/dev/null || log_warning "$(basename $file) 백업 실패"
        done
    fi
    
    tar -czf "$backup_archive" -C "/tmp" "grafana_backup_$timestamp" 2>/dev/null
    
    if [[ $? -eq 0 ]]; then
        log_success "백업이 생성되었습니다: $backup_archive"
        rm -rf "$backup_dir"
    else
        log_error "백업 생성에 실패했습니다."
        exit 1
    fi
}

# 이미지 파일 교체 (v0.5 변경)
replace_images() {
    log_info "이미지 파일들을 교체하는 중..."
    
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local legacy_img_dir="/usr/share/grafana/public/img"
    local static_img_dir="/usr/share/grafana/public/build/static/img"
    
    # 1. 파비콘 교체
    if cp "$script_dir/img/fav32.png" "$legacy_img_dir/fav32.png"; then
        log_success "fav32.png 교체 완료"
    else
        log_error "fav32.png 교체 실패"; exit 1
    fi
    
    # 2. 레거시 grafana_icon.svg 교체
    local legacy_icon_path="$legacy_img_dir/grafana_icon.svg"
    if [[ -f "$legacy_icon_path" ]]; then
        if cp "$script_dir/img/grafana_icon.svg" "$legacy_icon_path"; then
            log_success "grafana_icon.svg (레거시) 교체 완료"
        else
            log_warning "grafana_icon.svg (레거시) 교체 실패."
        fi
    fi

    # 3. 해시 포함 이미지 파일 교체
    local image_files=("grafana_icon.svg" "g8_login_dark.svg" "g8_login_light.svg")
    
    for file in "${image_files[@]}"; do
        local source_file="$script_dir/img/$file"
        local target_files=$(find_hashed_files "$file" "$static_img_dir")
        
        if [[ -n "$target_files" ]]; then
            while IFS= read -r target_file; do
                if cp "$source_file" "$target_file"; then
                    log_success "$file → $(basename "$target_file") 교체 완료"
                else
                    log_error "$file → $(basename "$target_file") 교체 실패"
                fi
            done <<< "$target_files"
        else
            if [[ "$file" != "grafana_icon.svg" ]]; then
                log_warning "$file 의 해시 포함 대상 파일을 찾지 못했습니다."
            fi
        fi
    done
}


# 로그인 문구 변경
change_login_text() {
    local new_text="$1"
    log_info "로그인 문구를 '$new_text'로 변경하는 중..."
    
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

# 메뉴 및 실행 로직 (기존과 동일)
show_main_menu() {
    clear
    echo "=================================="
    echo "   Grafana 커스터마이징 스크립트 v0.5"
    echo "=================================="
    echo "• 해시 파일명 및 레거시 경로 지원"
    echo "• 루트 권한 실행으로 안정성 강화"
    echo ""
}

show_backup_menu() {
    echo "=================================="
    echo "        1. 백업 설정"
    echo "=================================="
    while true; do
        read -p "기존 파일들을 백업하시겠습니까? (Y/n): " backup_choice
        case ${backup_choice:-Y} in
            [Yy]*) BACKUP_ENABLED=true; log_info "백업을 생성합니다."; break ;;
            [Nn]*) BACKUP_ENABLED=false; log_info "백업을 생성하지 않습니다."; break ;;
            *) log_error "Y 또는 n을 입력해주세요." ;;
        esac
    done
}

show_login_text_menu() {
    echo ""
    echo "=================================="
    echo "        2. 로그인 문구 선택"
    echo "=================================="
    echo "1) Integrated Monitoring"
    echo "2) E2E Observability"
    while true; do
        read -p "로그인 화면에 표시할 문구를 선택하세요 (1-2): " text_choice
        case $text_choice in
            1) LOGIN_TEXT="Integrated Monitoring"; break ;;
            2) LOGIN_TEXT="E2E Observability"; break ;;
            *) log_error "1 또는 2를 입력해주세요." ;;
        esac
    done
    log_info "선택된 문구: $LOGIN_TEXT"
}

show_confirmation() {
    echo ""
    echo "=================================="
    echo "        3. 작업 확인"
    echo "=================================="
    echo "• 백업 생성: $(if $BACKUP_ENABLED; then echo "예"; else echo "아니오"; fi)"
    echo "• 이미지 파일 교체"
    echo "• 로그인 문구 변경: '$LOGIN_TEXT'"
    echo "• Grafana 서비스 재시작"
    echo ""
    while true; do
        read -p "위 작업을 진행하시겠습니까? (Y/n): " confirm
        case ${confirm:-Y} in
            [Yy]*) return 0 ;;
            [Nn]*) log_info "작업이 취소되었습니다."; exit 0 ;;
            *) echo "Y 또는 n을 입력해주세요." ;;
        esac
    done
}

execute_tasks() {
    echo ""
    log_info "작업을 시작합니다..."
    
    if $BACKUP_ENABLED; then create_backup; fi
    replace_images
    change_login_text "$LOGIN_TEXT"
    restart_grafana
    
    echo ""
    echo "=================================="
    echo "        작업 완료"
    echo "=================================="
    log_success "모든 작업이 성공적으로 완료되었습니다!"
    echo "브라우저 캐시를 삭제하고 Grafana 페이지를 새로고침하여 변경사항을 확인하세요."
    echo ""
}

main() {
    show_main_menu
    check_sudo
    check_grafana
    check_files
    check_custom_files
    show_backup_menu
    show_login_text_menu
    show_confirmation
    execute_tasks
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
