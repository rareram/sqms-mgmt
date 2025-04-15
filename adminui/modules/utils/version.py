import requests
import streamlit as st
from packaging import version
import re

def get_latest_version(repo_url):
    """다양한 소스에서 최신 버전 정보를 가져옵니다.
    
    다음 형식을 지원합니다.
    - GitHub 릴리즈: https://github.com/username/repo
    - GitHub 태그: https://github.com/username/repo/tags
    - GitLab 태그: https://gitlab.com/username/repo/-/tags

    Args:
        repo_url (str): 저장소 URL

    Returns:
        dict: 최신 버전 정보 또는 None
    """
    # GitHub 릴리즈
    if "github.com" in repo_url and "/tags" not in repo_url:
        return check_github_release(repo_url)
    
    # GitHub 태그
    elif "github.com" in repo_url and "/tags" in repo_url:
        return check_github_tags(repo_url)
    
    # GitLab 태그
    elif "gitlab.com" in repo_url and "/tags" in repo_url:
        return check_gitlab_tags(repo_url)
    
    # 지원하지 않는 형식
    else:
        return None

def check_github_release(repo_url):
    """GitHub 저장소에서 최신 릴리스 버전을 확인합니다.

    Args:
        repo_url (str): GitHub 저장소 URL (예: 'username/repo' 또는 'https://githbu.com/username/repo')

    Returns:
        dict: 최신 릴리스 정보 (버전, URL, 날짜)
        None: 릴리스 정보를 가져오지 못한 경우
    """
    try:
        # GitHub 저장소 이름 추출
        if "github.com/" in repo_url:
            # 전체 URL에서 사용자/저장소 부분 추출
            parts = repo_url.split("github.com/")
            repo_path = parts[1].strip("/")
            # 추가 경로가 있는 경우 제거
            if "/" in repo_path:
                repo_path = "/".join(repo_path.split("/")[:2])
        else:
            # 이미 username/repo 형식인 경우
            repo_path = repo_url
        
        # GitHub API URL 생성
        api_url = f"https://api.github.com/repos/{repo_path}/releases/latest"
        
        # API 요청
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        
        # 릴리스 정보 추출
        release_info = response.json()
        
        return {
            "version": release_info["tag_name"].lstrip("v"),
            "url": release_info["html_url"],
            "published_at": release_info["published_at"],
            "name": release_info["name"],
            "body": release_info["body"],
            "source": "github_release"
        }
    except Exception as e:
        st.error(f"GitHub 릴리즈 조회 실패: {e}")
        return None

def check_github_tags(repo_url):
    """GitHub 저장소의 태그 목록에서 최신 버전을 확인합니다.
    
    Args:
        repo_url (str): GitHub 태그 URL (예: 'https://github.com/username/repo/tags')
    
    Returns:
        dict: 최신 태그 정보
        None: 태그 정보를 가져오지 못한 경우
    """
    try:
        # GitHub 저장소 이름 추출
        parts = repo_url.split("github.com/")
        if len(parts) < 2:
            return None
        
        repo_path = parts[1].strip("/")
        # /tags 제거
        if "/tags" in repo_path:
            repo_path = repo_path.replace("/tags", "")
        
        # GitHub API URL 생성
        api_url = f"https://api.github.com/repos/{repo_path}/tags"

        # API 요청
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()

        # 태그 목록 추출
        tags = response.json()

        if not tags:
            return None
        
        # 버전 번호를 기준으로 태그 정렬
        valid_tags = []
        for tag in tags:
            tag_name = tag["name"].lstrip("v")
            try:
                # 유효한 버전 형식인지 확인
                parsed_version = version.parse(tag_name)
                valid_tags.append((parsed_version, tag))
            except Exception:
                continue
        
        if not valid_tags:
            # 버전 형식이 아닌 경우 첫 번째 태그 반환
            latest_tag = tags[0]
        else:
            # 버전 번호 기준 정렬
            valid_tags.sort(reverse=True)
            latest_tag = valid_tags[0][1]
        
        tag_url = f"https://github.com/{repo_path}/releases/tag/{latest_tag['name']}"

        return {
            "version": latest_tag["name"].lstrip("v"),
            "url": tag_url,
            "commit": latest_tag.get("commit", {}).get("sha", ""),
            "source": "github_tag"
        }
    except Exception as e:
        st.error(f"GitHub 태그 조회 실패: {e}")
        return None

def check_gitlab_tags(repo_url):
    """GitLab 저장소의 태그 목록에서 최신 버전을 확인합니다.
    
    Args:
        repo_url (str): GitLab 태그 URL (예: 'https://gitlab.com/username/repo/-/tags')
    
    Returns:
        dict: 최신 태그 정보
        None: 태그 정보를 가져오지 못한 경우
    """
    try:
        # GitLab 저장소 이름 추출
        parts = repo_url.split("gitlab.com/")
        if len(parts) < 2:
            return None

        repo_path = parts[1].strip("/")
        # /-/tags 제거
        if "/-/tags" in repo_path:
            repo_path = repo_path.replace("/-/tags", "")
        
        # GitLab API URL 생성 (프로젝트 ID 필요)
        # URL 인코딩이 필요함
        encoded_path = repo_path.replace("/", "%2F")
        api_url = f"https://gitlab.com/api/v4/projects/{encoded_path}/repository/tags"

        # API 요청
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()

        # 태그 목록 추출
        tags = response.json()

        if not tags:
            return None
        
        # 버전 번호를 기준으로 태그 정렬
        valid_tags = []
        for tag in tags:
            tag_name = tag["name"].lstrip("v")
            try:
                # 유효한 버전 형식인지 확인
                parsed_version = version.parse(tag_name)
                valid_tags.append((parsed_version, tag))
            except Exception:
                continue
        
        if not valid_tags:
            # 버전 형식이 아닌 경우 첫 번째 태그 반환
            latest_tag = tags[0]
        else:
            # 버전 번호 기준 정렬
            valid_tags.sort(reverse=True)
            latest_tag = valid_tags[0][1]
        
        tag_url = f"https://gitlab.com/{repo_path}/-/tags/{latest_tag['name']}"

        return {
            "version": latest_tag["name"].lstrip("v"),
            "url": tag_url,
            "commit": latest_tag.get("commit", {}.get("id", "")),
            "message": latest_tag.get("messgae", ""),
            "source": "gitlab_tag"
        }
    except Exception as e:
        st.error(f"GitLab 태그 조회 실패: {e}")
        return None

def compare_versions(current_version, latest_version):
    """현재 버전과 최신 버전을 비교합니다.

    Args:
        current_version (str): 현재 버전
        latest_version (str): 최신 버전

    Returns:
        int: -1 (구버전), 0 (최신버전), 1 (개발버전)
    """
    try:
        # 버전 앞의 'v' 제거
        current = current_version.lstrip("v")
        latest = latest_version.lstrip("v")
        
        # 버전 비교
        v_current = version.parse(current)
        v_latest = version.parse(latest)
        
        if v_current < v_latest:
            return -1  # 구버전
        elif v_current > v_latest:
            return 1   # 개발버전
        else:
            return 0   # 동일 버전
    except Exception:
        return None  # 비교 실패

def show_version_info(current_version, repo_url=None):
    """모듈 버전 정보를 표시합니다.

    Args:
        current_version (str): 현재 모듈 버전
        repo_url (str, optional): 저장소 URL

    Returns:
        None
    """
    st.write(f"### 현재 버전: {current_version}")
    
    if repo_url:
        if st.button("최신 버전 확인"):
            with st.spinner("최신 버전 확인 중..."):
                latest_release = get_latest_version(repo_url)
                
                if latest_release:
                    latest_version = latest_release["version"]
                    version_status = compare_versions(current_version, latest_version)
                    
                    if version_status == -1:
                        st.warning(f"새 버전이 있습니다: {latest_version}")
                        st.markdown(f"[{repo_url.split('/')[-2] if '/tags' in repo_url else '저장소'}에서 업데이트 확인]({latest_release['url']})")
                        
                        # 릴리스 노트 표시 (GitHub 릴리스인 경우)
                        if latest_release.get("source") == "github_release" and "body" in latest_release:
                            with st.expander("릴리스 노트"):
                                st.markdown(f"## {latest_release['name']}")
                                st.markdown(latest_release['body'])
                        
                    elif version_status == 0:
                        st.success(f"최신 버전을 사용 중입니다: {latest_version}")
                    elif version_status == 1:
                        st.info(f"개발 버전을 사용 중입니다. 최신 안정 버전: {latest_version}")
                    else:
                        st.error("버전 비교 실패: 잘못된 버전 형식입니다.")
                else:
                    st.error(f"저장소에서 최신 버전 정보를 가져오지 못했습니다: {repo_url}")
    else:
        st.info("저장소 URL이 설정되지 않았습니다. 최신 버전 확인을 위해 저장소 URL 설정이 필요합니다.")

def save_repo_url(module_id, repo_url):
    """모듈의 저장소 URL을 저장합니다.
    
    Args:
        module_id (str): 모듈 ID
        repo_url (str): 저장소 URL
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        import json
        import os
        
        config_dir = os.path.join("config", "modules")
        os.makedirs(config_dir, exist_ok=True)
        
        config_file = os.path.join(config_dir, f"{module_id}.json")
        
        config = {}
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
        
        config["repo_url"] = repo_url
        
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
        
        return True
    except Exception as e:
        st.error(f"저장소 URL 저장 실패: {e}")
        return False

def load_repo_url(module_id):
    """모듈의 저장소 URL을 로드합니다.
    
    Args:
        module_id (str): 모듈 ID
    
    Returns:
        str: 저장소 URL 또는 None
    """
    try:
        import json
        import os
        
        config_file = os.path.join("config", "modules", f"{module_id}.json")
        
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
                return config.get("repo_url")
        
        return None
    except Exception:
        return None