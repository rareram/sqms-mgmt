# Grafana 대시보드 Export/Import 스크립트

## 파일 구성
- `export_all_dashboards.py`: 모든 대시보드를 JSON으로 추출
- `import_dashboard.py`: JSON 파일을 Grafana에 업로드
- `README.md`: 사용법 안내

## 설정 방법

### 1. 필요한 패키지 설치
```bash
pip install requests
```

### 2. Grafana API 토큰 생성
1. Grafana 웹 UI에 Admin 권한으로 로그인
2. `Administration > Users and access > Service accounts` 메뉴 이동
3. `Create service account` 클릭
4. 이름 입력 (예: "Dashboard Manager")
5. Role을 `Admin`으로 설정
6. `Create` 후 `Add service account token` 클릭
7. 생성된 토큰 복사

### 3. 스크립트 설정 수정
각 스크립트 파일의 상단 설정 부분을 수정:

```python
# export_all_dashboards.py와 import_dashboard.py 모두 수정
GRAFANA_URL = "http://your-grafana-url:3000"  # 실제 Grafana URL
GRAFANA_TOKEN = "your-admin-api-token-here"   # 위에서 생성한 토큰
```

## 사용법

### 1. 모든 대시보드 추출
```bash
python3 export_all_dashboards.py
```

**출력 결과:**
- `grafana_export_YYYYMMDD_HHMMSS/` 디렉토리 생성
- `folders/` 하위에 폴더별로 JSON 파일 저장
- 파일명 형식: `{UID}_{제목}_v{버전}.json`

### 2. 개별 대시보드 업로드
```bash
# 기본 업로드 (백업 생성)
python3 import_dashboard.py path/to/dashboard.json

# 백업 없이 업로드
python3 import_dashboard.py path/to/dashboard.json --no-backup
```

## 테스트 시나리오

### UID 보존 및 Revision 확인
1. 대시보드 추출
2. JSON에서 패널 Description 수정
3. 업로드 후 UID와 버전 변화 확인

**예시 테스트:**
```bash
# 1. 전체 추출
python3 export_all_dashboards.py

# 2. 특정 대시보드 JSON 편집
# 예: panels[0].description 수정

# 3. 업로드 및 확인
python3 import_dashboard.py grafana_export_*/folders/General/db695651-d5b0-4640-a000-b61fec2833bf_New_dashboard_v5.json
```

## 주요 확인 포인트

### ✅ UID 보존 확인
업로드 시 다음과 같이 출력됩니다:
```
   - UID 보존: True ✅
```

### ✅ Revision 추적  
버전 변화를 다음과 같이 확인할 수 있습니다:
```
   - 새 버전: 6
   - 원본 버전: 5
   - 버전 변화: 5 → 6
```

### ✅ Description 구조
패널별 Description은 다음 구조로 저장됩니다:
```json
"panels": [
  {
    "id": 1,
    "description": "여기에 설명 입력",
    ...
  }
]
```

## 중요 사항

- **UID는 절대 변경되면 안됨** (알람 연동 때문)
- 업로드 시 자동으로 백업 생성됨
- 버전(revision)은 자동으로 증가함
- Description 편집 후 업로드하면 패널별 도움말 추가 가능

## 파일 위치
스크립트는 `~/Desktop/`에 저장되었습니다:
- `~/Desktop/export_all_dashboards.py`
- `~/Desktop/import_dashboard.py` 
- `~/Desktop/README.md`
