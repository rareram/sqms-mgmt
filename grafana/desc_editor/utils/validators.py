import re
from typing import Optional

def validate_grafana_url(url: str) -> bool:
    """Grafana URL 유효성 검사"""
    if not url:
        return False
    
    # 기본 URL 패턴 검사
    url_pattern = r'^https?://[\w\-\.]+(?::\d+)?(?:/.*)?$'
    return bool(re.match(url_pattern, url))

def validate_api_token(token: str) -> bool:
    """API 토큰 유효성 검사"""
    if not token:
        return False
    
    # Grafana API 토큰은 일반적으로 영숫자와 특수문자로 구성
    # 최소 10자 이상
    return len(token) >= 10

def validate_panel_id(panel_id: any) -> bool:
    """패널 ID 유효성 검사"""
    if panel_id is None:
        return False
    
    try:
        int(panel_id)
        return True
    except (ValueError, TypeError):
        return False

def validate_dashboard_uid(uid: str) -> bool:
    """대시보드 UID 유효성 검사"""
    if not uid:
        return False
    
    # UID는 영숫자와 하이픈, 언더스코어로 구성
    # 일반적으로 8-12자 길이
    uid_pattern = r'^[a-zA-Z0-9_-]{8,12}$'
    return bool(re.match(uid_pattern, uid))

def sanitize_description(description: str) -> str:
    """Description 텍스트 정리"""
    if not description:
        return ""
    
    # 기본 HTML 태그 제거 (보안상 이유)
    description = re.sub(r'<script[^>]*>.*?</script>', '', description, flags=re.DOTALL | re.IGNORECASE)
    description = re.sub(r'<style[^>]*>.*?</style>', '', description, flags=re.DOTALL | re.IGNORECASE)
    
    # 앞뒤 공백 제거
    description = description.strip()
    
    # 연속된 공백 정리
    description = re.sub(r'\s+', ' ', description)
    
    return description

def validate_description_length(description: str, max_length: int = 1000) -> bool:
    """Description 길이 유효성 검사"""
    if not description:
        return True
    
    return len(description) <= max_length
