#!/usr/bin/env python3
"""
Grafana 대시보드 업로드 스크립트
- JSON 파일을 Grafana에 업로드
- UID 보존 확인
- 백업 및 버전 관리
"""

import requests
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import argparse

# 설정 - 실제 환경에 맞게 수정하세요
GRAFANA_URL = "http://your-grafana-url:3000"  # 예: "http://localhost:3000"
GRAFANA_TOKEN = "your-admin-api-token-here"   # Admin 권한 API 토큰

def setup_session():
    """HTTP 세션 설정"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {GRAFANA_TOKEN}",
        "Content-Type": "application/json"
    })
    return session
