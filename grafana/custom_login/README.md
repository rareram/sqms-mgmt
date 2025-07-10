# Customize Grafana

### 주요 기능

- sudo 권한 체크: 스크립트 실행 시 즉시 확인
- Grafana 설치 확인: systemctl과 which 명령어로 이중 확인
- 원본이미지 백업: 사용자 선택에 따라 백업 생성
- 로그인 문구 선택: "Integrated Monitoring" 또는 "E2E Observability"
- 안전한 파일 교체: 각 단계별 오류 처리
- 로그 종류 표시: 색상별 로그 메시지
- 서비스 재시작: 설정 변경 후 프로세스 재시작 및 상태 확인

### 폴더 구조

```
script_folder/
├── customize_grafana_v0.1.sh
└── img/
    ├── fav32.png
    ├── grafana_icon.svg
    ├── g8_login_dark.svg
    └── g8_login_light.svg
```

### 주의 사항

- 정식 테마가 개발되기 전까지는 설치할때마다 적용 필요