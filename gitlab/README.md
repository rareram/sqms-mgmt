#  commit 유저 네이밍 매핑

- 기본기능: 매핑 룰 파일을 읽어서 커밋 사용자 정보를 변환
- 초기 템플릿 생성시 아래 명령어로 모든 고유한 커밋 사용자 목록을 추출하여 템플릿 생성
`$ python user_mappping_rule.py --create-template` 
- 템플릿 파일을 commit_user_mapping.csv 로 복사 또는 이름 변경
- 매핑 룰 적용 `$ python simple_commit_user_mapper.py`
- 적용 완료되면 `gitlab_mapped_data.csv` 파일이 생성됨

## commit 유저네임 정규화 vb 코드

- 이메일 주소만 있는 경우 (예: user@example.com)
- sksdu_ID 만 있는 경우 (예: sksdu_1234)
- 도메인\사용자 형식 (예: COMPANY\sksdu_3243)
- 한글 이름만 있는 경우 (예: 홍길동)
- 영문 이름만 있는 경우 (예: John Doe)
- 기타 알 수 없는 형식 (기본 형식은 '홍길동(hong_id)')