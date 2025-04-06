# IT 관리 시스템 설치 및 배포 가이드

이 문서는 IT 관리 시스템의 설치 및 배포 방법을 안내합니다.

## 로컬 개발 환경 설정

### 필수 요구사항
- Python 3.8 이상
- pip (Python 패키지 관리자)
- git

### 설치 단계

1. 저장소 클론
```bash
git clone https://github.com/your-username/it-management-system.git
cd it-management-system
```

2. 가상 환경 생성 및 활성화
```bash
# Linux/macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 실제 환경에 맞게 값을 수정합니다.
```bash
# Linux/macOS
cp .env.example .env

# Windows
copy .env.example .env
```

5. 애플리케이션 실행
```bash
# Linux/macOS
chmod +x run.sh
./run.sh

# Windows
run.bat
```

## 서버 배포 방법

### Docker를 사용한 배포

1. Docker 설치 (Ubuntu)
```bash
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker
```

2. Dockerfile 생성
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.address=0.0.0.0"]
```

3. Docker 이미지 빌드
```bash
docker build -t it-management-system .
```

4. Docker 컨테이너 실행
```bash
docker run -d -p 8501:8501 --env-file .env --name it-management-app it-management-system
```

### 리눅스 서버에 직접 배포

1. 서버에 필요한 패키지 설치
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv libldap2-dev libsasl2-dev
```

2. 애플리케이션 코드 다운로드
```bash
git clone https://github.com/your-username/it-management-system.git
cd it-management-system
```

3. 가상 환경 설정
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. 환경 변수 설정
`.env` 파일을 생성하고 필요한 환경 변수를 설정합니다.

5. Systemd 서비스 파일 생성
```bash
sudo nano /etc/systemd/system/it-management.service
```

다음 내용을 추가합니다:
```
[Unit]
Description=IT Management System
After=network.target

[Service]
User=your-username
WorkingDirectory=/path/to/it-management-system
ExecStart=/path/to/it-management-system/venv/bin/streamlit run main.py --server.address=0.0.0.0
Restart=always
Environment=PATH=/path/to/it-management-system/venv/bin

[Install]
WantedBy=multi-user.target
```

6. 서비스 시작
```bash
sudo systemctl daemon-reload
sudo systemctl start it-management
sudo systemctl enable it-management
```

7. 서비스 상태 확인
```bash
sudo systemctl status it-management
```

## Nginx를 사용한 프록시 설정 (선택 사항)

1. Nginx 설치
```bash
sudo apt-get install nginx
```

2. Nginx 설정 파일 생성
```bash
sudo nano /etc/nginx/sites-available/it-management
```

다음 내용을 추가합니다:
```
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

3. 사이트 활성화 및 Nginx 재시작
```bash
sudo ln -s /etc/nginx/sites-available/it-management /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

4. SSL 인증서 설정 (권장)
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 문제 해결

### 일반적인 문제

1. `ModuleNotFoundError`: 필요한 Python 패키지가 설치되지 않았습니다.
   ```
   pip install -r requirements.txt
   ```

2. LDAP 연결 오류: LDAP 서버 설정이 올바르지 않거나 필요한 라이브러리가 설치되지 않았습니다.
   ```
   sudo apt-get install libldap2-dev libsasl2-dev
   pip install python-ldap
   ```

3. 권한 오류: 환경 변수 설정이 올바르지 않거나 API 키가 잘못되었습니다.
   `.env` 파일의 설정을 확인하세요.

### 로그 확인 방법

- Streamlit 로그: 터미널에서 직접 확인
- Systemd 서비스 로그: `sudo journalctl -u it-management`
- Nginx 로그: `sudo cat /var/log/nginx/error.log`

## 업데이트 방법

1. 코드 업데이트
```bash
git pull origin main
```

2. 패키지 업데이트
```bash
pip install -r requirements.txt
```

3. 서비스 재시작 (시스템 서비스로 실행 중인 경우)
```bash
sudo systemctl restart it-management
```