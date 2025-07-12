import os
from dotenv import load_dotenv
from typing import Optional

class Config:
    """설정 관리 클래스"""
    
    def __init__(self):
        load_dotenv()
    
    @property
    def ssl_verify(self) -> bool:
        """SSL 검증 여부 (개발용 우회 옵션)"""
        # 환경 변수로 SSL 검증 비활성화 가능
        return os.getenv('SSL_VERIFY', 'true').lower() != 'false'
        
    @property
    def grafana_url(self) -> str:
        """Grafana 서버 URL"""
        url = os.getenv('GRAFANA_URL', 'http://localhost:3000')
        return url.rstrip('/')
    
    @property
    def grafana_token(self) -> str:
        """Grafana API 토큰"""
        token = os.getenv('GRAFANA_TOKEN')
        if not token:
            raise ValueError("GRAFANA_TOKEN이 설정되지 않았습니다. .env 파일을 확인하세요.")
        return token
    
    @property
    def grafana_org_id(self) -> Optional[int]:
        """Grafana 조직 ID"""
        org_id = os.getenv('GRAFANA_ORG_ID')
        return int(org_id) if org_id else None
    
    @property
    def headers(self) -> dict:
        """API 요청 헤더"""
        headers = {
            'Authorization': f'Bearer {self.grafana_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.grafana_org_id:
            headers['X-Grafana-Org-Id'] = str(self.grafana_org_id)
            
        return headers
    
    def validate(self) -> bool:
        """설정 유효성 검사"""
        try:
            assert self.grafana_url, "GRAFANA_URL이 설정되지 않았습니다."
            assert self.grafana_token, "GRAFANA_TOKEN이 설정되지 않았습니다."
            return True
        except (AssertionError, ValueError) as e:
            print(f"설정 오류: {e}")
            return False

# 전역 설정 인스턴스
config = Config()
