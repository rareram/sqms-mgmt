# Grafana Dashboard Description Editor

Grafana 대시보드 패널의 Description을 편집하는 웹 서비스입니다.

## 설치 및 실행

1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 패키지 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 Grafana 정보 입력
```

4. 실행
```bash
streamlit run main.py
```

## 기능

- 폴더 구조별 대시보드 조회
- 패널별 Description 편집
- 변경 이력 조회
- 패널 타입별 시각적 구분
