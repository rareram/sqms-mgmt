import streamlit as st
import requests
import pandas as pd
import json
import os
from datetime import datetime
import time
from io import StringIO
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
from modules.utils import version

# 모듈 ID와 버전 정보
MODULE_ID = "gitlab_manager"
VERSION = "v0.2.0"
DEFAULT_REPO_URL = "https://gitlab.com/rluna-gitlab/gitlab-ce/-/tags"

def show_module():
    """GitLab 관리 모듈 메인 화면"""
    st.title("GitLab 관리")

    # 버전 정보 표시
    st.caption(f"모듈 버전: {VERSION}")
    
    # 탭 생성
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["저장소 관리", "저장소 용량", "미사용 저장소", "사용자 관리", "GitLab 설정"])
    
    # 저장소 관리 탭
    with tab1:
        show_repository_management()
    
    # 저장소 용량 탭
    with tab2:
        show_repository_storage()

    # 미사용 저장소 탭
    with tab3:
        show_unused_repositories()
    
    # 사용자 관리 탭
    with tab4:
        show_user_management()
    
    # GitLab 설정 탭
    with tab5:
        show_gitlab_settings()

# 폰트 설정 함수
def set_matplotlib_korean_font():
    """matplotlib에 한글 폰트 설정"""
    # 프로젝트 내 폰트 디렉토리 경로
    font_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "../../config"
    
    # 시스템에 설치된 폰트 중 한글 폰트 찾기
    system_fonts = [f.name for f in fm.fontManager.ttflist if any(keyword in f.name.lower() for keyword in ['malgun', 'nanum', 'gulim', 'batang', 'gothic'])]
    
    # 프로젝트 내 폰트 디렉토리 검사
    if font_dir.exists():
        # 프로젝트 내 폰트 등록
        font_files = list(font_dir.glob('*.ttf')) + list(font_dir.glob('*.otf'))
        for font_file in font_files:
            fm.fontManager.addfont(str(font_file))
            
    # 폰트 설정 시도
    if font_dir.exists() and len(list(font_dir.glob('*.ttf'))) > 0:
        # 프로젝트 내 첫 번째 폰트 사용
        font_path = next(font_dir.glob('*.ttf'))
        plt.rcParams['font.family'] = fm.FontProperties(fname=str(font_path)).get_name()
    elif system_fonts:
        # 시스템 한글 폰트 사용
        plt.rcParams['font.family'] = system_fonts[0]
    else:
        # 폰트를 찾을 수 없는 경우 대체 방법
        plt.rcParams['font.sans-serif'] = ['Arial', 'Tahoma', 'DejaVu Sans', 'Noto Sans', 'Verdana']
        plt.rcParams['axes.unicode_minus'] = False

# 모듈 시작 시 폰트 설정
set_matplotlib_korean_font()

def show_repository_statistics(repo_id):
    """저장소 통계 정보 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return None
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        url = f"{gitlab_host}/api/v4/projects/{repo_id}/statistics"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"저장소 통계 정보 조회 실패: {e}")
        return None

def get_all_repositories_storage():
    """모든 GitLab 저장소 용량 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return []
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        projects = []
        page = 1
        
        while True:
            url = f"{gitlab_host}/api/v4/projects?per_page=100&page={page}&statistics=true"
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            if not data:
                break

            # 저장소 정보 및 통계 정보 저장
            for project in data:
                # 필수 필드 확인
                if all(key in project for key in ["id", "name", "namespace", "statistics"]):
                    # 네임스페이스 확인 및 보정
                    if not isinstance(project["namespace"], dict) or "name" not in project["namespace"]:
                        project["namespace"] = {"name": "Unknown"}
                    
                    # 필요한 필드만 유지하여 메모리 절약
                    clean_project = {
                        "id": project["id"],
                        "name": project["name"],
                        "namespace": {"name": project["namespace"]["name"]},
                        "web_url": project["web_url"],
                        "created_at": project.get("created_at", ""),
                        "last_activity_at": project.get("last_activity_at", ""),
                        # "statistics": project["statistics"]
                        "statistics": {
                            "repository_size": project["statistics"].get("repository_size", 0),
                            "lfs_objects_size": project["statistics"].get("lfs_objects_size", 0),
                            "job_artifacts_size": project["statistics"].get("job_artifacts_size", 0),
                            "packages_size": project["statistics"].get("packages_size", 0),
                            "storage_size": project["statistics"].get("storage_size", 0)
                        }
                    }
                    projects.append(project)

            page += 1
            time.sleep(0.5)  # API 요청 제한 방지
        
        return projects
    except Exception as e:
        st.error(f"저장소 용량 조회 실패: {e}")
        return []
    
def format_size(size_bytes):
    """바이트 단위의 크기를 읽기 쉬운 형식으로 변환"""
    if size_bytes == 0:
        return "0 B"
    
    # 단위 정의
    size_units = ("B", "KB", "MB", "GB", "TB")

    # 적절한 단위 선택
    i = 0
    while size_bytes >= 1024 and i < len(size_units) - 1:
        size_bytes /= 1024
        i += 1

    # 소수점 이하 2자리까지 표시
    return f"{size_bytes:.2f} {size_units[i]}"

# 저장소 용량 관리 함수 추가
def show_repository_storage():
    """저장소 용량 관리 화면"""
    st.subheader("저장소 용량 관리")
    
    # GitLab 연결 확인
    if not check_gitlab_connection():
        st.error("GitLab 연결에 실패했습니다. GitLab 설정을 확인해주세요.")
        return
    
    # 저장소 용량 정보 불러오기
    if st.button("저장소 용량 정보 조회", key="refresh_storage_info"):
        with st.spinner("저장소 용량 정보를 조회 중입니다..."):
            storage_stats = get_all_repositories_storage()
            
            if storage_stats:
                # 세션 상태에 저장
                st.session_state.repo_storage_stats = storage_stats
                st.success(f"총 {len(storage_stats)}개의 저장소 용량 정보를 불러왔습니다.")
            else:
                st.error("저장소 용량 정보를 불러오는데 실패했습니다.")

    # 용량 정보 표시
    if hasattr(st.session_state, 'repo_storage_stats'):
        storage_stats = st.session_state.repo_storage_stats
    
        # 검색 필터
        search_term = st.text_input("저장소 검색 (이름, 그룹)", key="storage_search")
    
        # 필터링
        if search_term:
            filtered_stats = [stat for stat in storage_stats if 
                             search_term.lower() in stat["name"].lower() or 
                             search_term.lower() in stat["namespace"]["name"].lower()]
        else:
            filtered_stats = storage_stats
        
        # 정렬 옵션
        sort_option = st.selectbox("정렬 기준", ["용량 (큰 순)", "용량 (작은 순)", "이름순", "최근 활동순"], key="storage_sort")

        # 정렬
        if sort_option == "용량 (큰 순)":
            filtered_stats.sort(key=lambda x: x["statistics"]["storage_size"], reverse=True)
        elif sort_option == "용량 (작은 순)":
            filtered_stats.sort(key=lambda x: x["statistics"]["storage_size"])
        elif sort_option == "이름순":
            filtered_stats.sort(key=lambda x: x["name"].lower())
        elif sort_option == "최근 활동순":
            filtered_stats.sort(key=lambda x: x["last_activity_at"], reverse=True)
        
        # 전체 용량 계산
        total_size = sum(stat["statistics"]["storage_size"] for stat in filtered_stats)
        repository_count = len(filtered_stats)
        avg_size = total_size / repository_count if repository_count > 0 else 0

        # 용량 통계 요약
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 저장소 수", f"{repository_count}개")
        with col2:
            st.metric("전체 용량", format_size(total_size))
        with col3:
            st.metric("평균 저장소 용량", format_size(avg_size))
        
        # 차트 표시 (상위 10개 저장소)
        st.write("### 상위 저장소 용량 분포")
        top_repos = sorted(filtered_stats, key=lambda x: x["statistics"]["storage_size"], reverse=True)[:10]

        # 차트 데이터 준비
        chart_data = pd.DataFrame({
            "저장소": [f"{repo['namespace']['name']}/{repo['name'][:15]}" for repo in top_repos],
            "용량 (MB)": [round(repo["statistics"]["storage_size"] / (1024 * 1024), 2) for repo in top_repos]
        })

        # 차트 표시
        st.bar_chart(chart_data.set_index("저장소"))

        # 그룹별 용량 집계
        st.write("### 그룹별 저장소 용량")
        group_stats = {}
        for repo in filtered_stats:
            group_name = repo["namespace"]["name"]
            if group_name not in group_stats:
                group_stats[group_name] = {
                    "size": 0,
                    "count": 0
                }
            group_stats[group_name]["size"] += repo["statistics"]["storage_size"]
            group_stats[group_name]["count"] += 1
        
        # 그룹별 데이터프레임 생성
        group_df = pd.DataFrame([{
            "그룹명": group_name,
            "저장소 수": stats["count"],
            "전체 용량": format_size(stats["size"]),
            "용량 (MB)": round(stats["size"] / (1024 * 1024), 2),
            "평균 용량": format_size(stats["size"] / stats["count"]) if stats["count"] > 0 else "0 B"
        } for group_name, stats in group_stats.items()])

        # 용량 기준 정렬
        group_df = group_df.sort_values(by="용량 (MB)", ascending=False)

        # 그룹별 데이터프레임 표시
        st.dataframe(group_df, use_container_width=True)

        # 파이 차트 데이터 (상위 5개 그룹)
        if len(group_df) > 5:
            top_groups = group_df.nlargest(5, "용량 (MB)")

            # 나머지 그룹 합계
            other_size = total_size - sum(group["size"] for group in [stats for group_name, stats in group_stats.items() if group_name in top_groups["그룹명"].values])
            
            # Streamlit에서는 파이 차트를 직접 지원하지 않으므로 matplotlib 사용
            fig, ax = plt.subplots(figsize=(10, 6))
            sizes = list(top_groups["용량 (MB)"]) + ([round(other_size / (1024 * 1024), 2)] if other_size > 0 and len(group_df) > 5 else [])
            labels = list(top_groups["그룹명"]) + (["기타"] if other_size > 0 and len(group_df) > 5 else [])
            # labels = [f"Group {i+1}: {name}" if '\u3131' <= name[0] <= '\u318E' or '\uAC00' <= name[0] <= '\uD7A3' else name for i, name in enumerate(top_groups["그룹명"])]
            
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')  # 원형 파이 차트
            plt.title('그룹별 저장소 용량 분포')
            
            st.pyplot(fig)
        
        # 저장소 목록 데이터프레임 생성
        df = pd.DataFrame([{
            "ID": repo["id"],
            "그룹": repo["namespace"]["name"],
            "저장소": repo["name"],
            "용량": format_size(repo["statistics"]["storage_size"]),
            "저장소 용량 (MB)": round(repo["statistics"]["storage_size"] / (1024 * 1024), 2),
            "저장소용량 (바이트)": repo["statistics"]["storage_size"],
            "LFS 객체 크기": format_size(repo["statistics"].get("lfs_objects_size", 0)),
            "저장소 크기": format_size(repo["statistics"].get("repository_size", 0)),
            "저장소 생성일": repo.get("created_at", ""),
            "최근 활동": repo.get("last_activity_at", "")
        } for repo in filtered_stats])
        
        # 데이터프레임 표시
        st.write("### 저장소 용량 상세 목록")
        st.dataframe(df, use_container_width=True)
        
        # CSV 다운로드 버튼
        csv = '\ufeff' + df.to_csv(index=False)  # UTF-8 BOM 추가
        st.download_button(
            label="저장소 용량 정보 CSV 다운로드",
            data=csv,
            file_name="gitlab_repository_storage.csv",
            mime="text/csv",
            key="download_storage_csv"
        )
        
        # 선택한 저장소의 상세 용량 정보 표시
        st.subheader("저장소 상세 용량 정보")
        repo_id = st.number_input("저장소 ID", min_value=1, value=1, key="storage_repo_id_input")
        
        if st.button("상세 용량 조회", key="fetch_storage_details"):
            with st.spinner("저장소 용량 정보를 불러오는 중입니다..."):
                repo_statistics = show_repository_statistics(repo_id)
                
                if repo_statistics:
                    # 저장소 기본 정보 찾기
                    repo_info = next((repo for repo in filtered_stats if repo["id"] == repo_id), None)
                    
                    if repo_info:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**저장소**: {repo_info['namespace']['name']}/{repo_info['name']}")
                            st.write(f"**생성일**: {repo_info.get('created_at', 'N/A')}")
                        with col2:
                            st.write(f"**URL**: {repo_info.get('web_url', 'N/A')}")
                            st.write(f"**최근 활동**: {repo_info.get('last_activity_at', 'N/A')}")
                    
                    # 용량 정보 표시
                    st.write("### 용량 정보")
                    
                    # 용량 세부 항목 계산
                    storage_size = repo_statistics.get("storage_size", 0)
                    repository_size = repo_statistics.get("repository_size", 0)
                    lfs_objects_size = repo_statistics.get("lfs_objects_size", 0)
                    build_artifacts_size = repo_statistics.get("build_artifacts_size", 0)
                    packages_size = repo_statistics.get("packages_size", 0)
                    wiki_size = repo_statistics.get("wiki_size", 0)
                    
                    # 합계와 일치하지 않을 경우 기타 항목 추가
                    other_size = storage_size - (repository_size + lfs_objects_size + build_artifacts_size + packages_size + wiki_size)
                    other_size = max(0, other_size)  # 음수 방지
                    
                    # 테이블로 표시
                    components_df = pd.DataFrame([
                        {"구성 요소": "Git 저장소", "용량": format_size(repository_size), "비율": f"{100 * repository_size / storage_size:.1f}%" if storage_size > 0 else "0%"},
                        {"구성 요소": "LFS 객체", "용량": format_size(lfs_objects_size), "비율": f"{100 * lfs_objects_size / storage_size:.1f}%" if storage_size > 0 else "0%"},
                        {"구성 요소": "CI/CD 빌드 아티팩트", "용량": format_size(build_artifacts_size), "비율": f"{100 * build_artifacts_size / storage_size:.1f}%" if storage_size > 0 else "0%"},
                        {"구성 요소": "패키지", "용량": format_size(packages_size), "비율": f"{100 * packages_size / storage_size:.1f}%" if storage_size > 0 else "0%"},
                        {"구성 요소": "위키", "용량": format_size(wiki_size), "비율": f"{100 * wiki_size / storage_size:.1f}%" if storage_size > 0 else "0%"},
                        {"구성 요소": "기타", "용량": format_size(other_size), "비율": f"{100 * other_size / storage_size:.1f}%" if storage_size > 0 else "0%"},
                        {"구성 요소": "총합", "용량": format_size(storage_size), "비율": "100%"}
                    ])
                    
                    st.table(components_df)
                    
                    # 원형 차트로 시각화
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sizes = [repository_size, lfs_objects_size, build_artifacts_size, packages_size, wiki_size]
                    if other_size > 0:
                        sizes.append(other_size)
                    
                    labels = ["Git 저장소", "LFS 객체", "CI/CD 빌드 아티팩트", "패키지", "위키"]
                    if other_size > 0:
                        labels.append("기타")
                    
                    # 0인 항목 제외
                    non_zero_sizes = []
                    non_zero_labels = []
                    for i, size in enumerate(sizes):
                        if size > 0:
                            non_zero_sizes.append(size)
                            non_zero_labels.append(labels[i])
                    
                    if non_zero_sizes:
                        ax.pie(non_zero_sizes, labels=non_zero_labels, autopct='%1.1f%%', startangle=90)
                        ax.axis('equal')  # 원형 파이 차트
                        plt.title('저장소 용량 구성')
                        
                        st.pyplot(fig)
                    else:
                        st.info("표시할 용량 정보가 없습니다.")
                    
                    # 저장소 용량 관리 팁
                    with st.expander("저장소 용량 관리 팁"):
                        st.markdown("""
                        ### 저장소 용량 최적화 방법
                        
                        1. **대용량 파일 정리**
                           - `git filter-repo`를 사용하여 대용량 파일 제거
                           - `git lfs`를 사용하여 대용량 파일 관리
                        
                        2. **오래된 빌드 아티팩트 정리**
                           - CI/CD 설정에서 아티팩트 보존 기간 설정
                           - 불필요한 빌드 아티팩트 수동 삭제
                        
                        3. **사용하지 않는 브랜치와 태그 정리**
                           - 오래된 브랜치와 태그 정리
                           - 브랜치 관리 정책 수립
                        
                        4. **LFS 객체 관리**
                           - 불필요한 LFS 객체 정리
                           - LFS 사용 가이드라인 수립
                        
                        5. **불필요한 패키지 정리**
                           - 오래된 패키지 버전 삭제
                           - 패키지 보존 정책 수립
                        """)
                else:
                    st.error("저장소 용량 정보를 불러오는데 실패했습니다.")
    else:
        st.info("'저장소 용량 정보 조회' 버튼을 클릭하여 용량 정보를 불러와주세요.")

def show_repository_management():
    """저장소 관리 화면"""
    st.subheader("저장소 관리")
    
    # GitLab 연결 확인
    if not check_gitlab_connection():
        st.error("GitLab 연결에 실패했습니다. GitLab 설정을 확인해주세요.")
        return
    
    # 저장소 목록 불러오기
    if st.button("저장소 목록 갱신", key="refresh_repo_list"):
        repositories = get_all_repositories()

        if repositories:
            st.session_state.repositories = repositories
            st.success(f"총 {len(repositories)}개의 저장소를 불러왔습니다.")
    
    # 저장소 목록 표시
    if hasattr(st.session_state, 'repositories'):
        repositories = st.session_state.repositories
        
        # 검색 필터
        search_term = st.text_input("저장소 검색 (이름, 그룹, 설명)", key="repo_search")
        
        # 필터링
        if search_term:
            filtered_stats = [repo for repo in repositories if 
                             search_term.lower() in repo["name"].lower() or 
                             search_term.lower() in repo["namespace"]["name"].lower() or 
                             (repo.get("description") and search_term.lower() in repo["description"].lower())]
        else:
            filtered_stats = repositories
        
        # 정렬 옵션
        sort_option = st.selectbox("정렬 기준", ["최근 활동순", "이름순", "생성일순"], key="repo_sort")
        
        # 정렬
        if sort_option == "최근 활동순":
            filtered_stats.sort(key=lambda x: x["last_activity_at"], reverse=True)
        elif sort_option == "이름순":
            filtered_stats.sort(key=lambda x: x["name"].lower())
        elif sort_option == "생성일순":
            filtered_stats.sort(key=lambda x: x["created_at"], reverse=True)
        
        # 저장소 목록 표시
        st.write(f"총 {len(filtered_stats)}개의 저장소가 있습니다.")
        
        try:
            # 데이터프레임 생성
            df = pd.DataFrame([{
                "ID": repo["id"],
                "그룹": repo["namespace"]["name"],
                "프로젝트": repo["name"],
                "설명": repo.get("description", ""),
                "URL": repo["web_url"],
                "생성일": repo["created_at"],
                "최근 활동": repo["last_activity_at"]
            } for repo in filtered_stats])
        
            # 데이터프레임 표시
            st.dataframe(df, key="repo_dataframe")

            # CSV 다운로드 버튼
            csv = '\ufeff' + df.to_csv(index=False)
            st.download_button(
                label="저장소 목록 CSV 다운로드",
                data=csv,
                file_name="gitlab_repositories.csv",
                mime="text/csv",
                key="download_repo_csv"
            )
        except Exception as e:
            st.error(f"저장소 목록 표시 중 오류가 발생했습니다: {str(e)}")
            st.info("저장소 데이터 형식이 예사과 다를 수 있습니다. GitLab API 응답을 확인해주세요.")
        
        # 선택한 저장소의 상세 정보 표시
        st.subheader("저장소 상세 정보")
        repo_id = st.number_input("저장소 ID", min_value=1, value=1, key="repo_id_input")
        
        if st.button("상세 정보 조회", key="fetch_repo_details"):
            with st.spinner("저장소 정보를 불러오는 중입니다..."):
                repo_details = get_repository_details(repo_id)
                
                if repo_details:
                    # 저장소 정보 표시
                    st.write("### 기본 정보")
                    st.json({
                        "ID": repo_details["id"],
                        "이름": repo_details["name"],
                        "그룹": repo_details["namespace"]["name"],
                        "설명": repo_details.get("description", ""),
                        "URL": repo_details["web_url"],
                        "생성일": repo_details["created_at"],
                        "최근 활동": repo_details["last_activity_at"],
                        "가시성": repo_details["visibility"]
                    })
                    
                    # 멤버 정보 불러오기
                    members = get_project_members(repo_id)
                    
                    if members:
                        st.write("### 멤버 정보")
                        
                        # 멤버 데이터프레임 생성
                        members_df = pd.DataFrame([{
                            "ID": member["id"],
                            "이름": member["name"],
                            "사용자명": member["username"],
                            "이메일": member.get("email", ""),
                            "권한": get_access_level_name(member["access_level"]),
                            "추가일": member.get("created_at", "")
                        } for member in members])
                        
                        # 멤버 데이터프레임 표시
                        st.dataframe(members_df, key="members_dataframe")
                        
                        # CSV 다운로드 버튼
                        csv = members_df.to_csv(index=False)
                        st.download_button(
                            label="멤버 목록 CSV 다운로드",
                            data=csv,
                            file_name=f"gitlab_repo_{repo_id}_members.csv",
                            mime="text/csv",
                            key="download_members_csv"
                        )
                    else:
                        st.info("저장소 멤버 정보를 불러오는데 실패했습니다.")
                    
                    # 커밋 정보 불러오기
                    commits = get_repository_commits(repo_id)
                    
                    if commits:
                        st.write("### 최근 커밋 정보")
                        
                        # 커밋 데이터프레임 생성
                        commits_df = pd.DataFrame([{
                            "SHA": commit["id"][:8],
                            "작성자": commit["author_name"],
                            "메시지": commit["message"].split("\n")[0][:50],
                            "일시": commit["created_at"]
                        } for commit in commits])
                        
                        # 커밋 데이터프레임 표시
                        st.dataframe(commits_df, key="commits_dataframe")
                    else:
                        st.info("저장소 커밋 정보를 불러오는데 실패했습니다.")
                else:
                    st.error("저장소 정보를 불러오는데 실패했습니다.")
        
    else:
        st.info("'저장소 목록 갱신' 버튼을 클릭하여 저장소 목록을 불러와주세요.")

def show_user_management():
    """사용자 관리 화면"""
    st.subheader("사용자 관리")
    
    # GitLab 연결 확인
    if not check_gitlab_connection():
        st.error("GitLab 연결에 실패했습니다. GitLab 설정을 확인해주세요.")
        return
    
    # 사용자 목록 불러오기
    if st.button("사용자 목록 갱신"):
        with st.spinner("사용자 목록을 불러오는 중입니다..."):
            users = get_all_users()
            
            if users:
                # 세션 상태에 저장
                st.session_state.gitlab_users = users
                st.success(f"총 {len(users)}개의 사용자를 불러왔습니다.")
            else:
                st.error("사용자 목록을 불러오는데 실패했습니다.")
    
    # 사용자 목록 표시
    if hasattr(st.session_state, 'gitlab_users'):
        users = st.session_state.gitlab_users
        
        # 검색 필터
        search_term = st.text_input("사용자 검색 (이름, 사용자명, 이메일)")
        
        # 필터링
        if search_term:
            filtered_users = [user for user in users if 
                             search_term.lower() in user["name"].lower() or 
                             search_term.lower() in user["username"].lower() or 
                             (user.get("email") and search_term.lower() in user["email"].lower())]
        else:
            filtered_users = users
        
        # 사용자 상태 필터
        status_filter = st.selectbox("상태 필터", ["모두", "활성", "차단됨"])
        
        if status_filter == "활성":
            filtered_users = [user for user in filtered_users if user["state"] == "active"]
        elif status_filter == "차단됨":
            filtered_users = [user for user in filtered_users if user["state"] == "blocked"]
        
        # 사용자 목록 표시
        st.write(f"총 {len(filtered_users)}명의 사용자가 있습니다.")
        
        # 데이터프레임 생성
        df = pd.DataFrame([{
            "ID": user["id"],
            "이름": user["name"],
            "사용자명": user["username"],
            "이메일": user.get("email", ""),
            "상태": "활성" if user["state"] == "active" else "차단됨",
            "관리자": "예" if user.get("is_admin", False) else "아니오",
            "마지막 로그인": user.get("last_sign_in_at", "")
        } for user in filtered_users])
        
        # 데이터프레임 표시
        st.dataframe(df)
        
        # 선택한 사용자의 상세 정보 표시
        st.subheader("사용자 상세 정보")
        user_id = st.number_input("사용자 ID", min_value=1, value=1, key="user_id_input")
        
        if st.button("상세 정보 조회", key=f"fetch_user_details_{user_id}"):
            with st.spinner("사용자 정보를 불러오는 중입니다..."):
                user_details = get_user_details(user_id)
                
                if user_details:
                    # 사용자 정보 표시
                    st.write("### 기본 정보")
                    st.json({
                        "ID": user_details["id"],
                        "이름": user_details["name"],
                        "사용자명": user_details["username"],
                        "이메일": user_details.get("email", ""),
                        "상태": "활성" if user_details["state"] == "active" else "차단됨",
                        "관리자": "예" if user_details.get("is_admin", False) else "아니오",
                        "마지막 로그인": user_details.get("last_sign_in_at", ""),
                        "생성일": user_details["created_at"]
                    })
                    
                    # 사용자 프로젝트 정보 불러오기
                    projects = get_user_projects(user_id)
                    
                    if projects:
                        st.write("### 프로젝트 정보")
                        
                        # 프로젝트 데이터프레임 생성
                        projects_df = pd.DataFrame([{
                            "ID": project["id"],
                            "그룹": project["namespace"]["name"],
                            "프로젝트": project["name"],
                            "접근 레벨": get_access_level_name(project["access_level"]),
                            "URL": project["web_url"]
                        } for project in projects])
                        
                        # 프로젝트 데이터프레임 표시
                        st.dataframe(projects_df)
                        
                        # CSV 다운로드 버튼
                        csv = projects_df.to_csv(index=False)
                        st.download_button(
                            label="프로젝트 목록 CSV 다운로드",
                            data=csv,
                            file_name=f"gitlab_user_{user_id}_projects.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("사용자 프로젝트 정보를 불러오는데 실패했습니다.")
                else:
                    # st.error("사용자 정보를 불러오는데 실패했습니다.")
                    st.warning(f"ID {user_id}에 해당하는 사용자 정보가 없습니다. 존재하지 않는 ID이거나 퇴사로 인해 삭제된 ID 일 수 있습니다.")
        
        # CSV 다운로드 버튼
        csv = df.to_csv(index=False)
        st.download_button(
            label="사용자 목록 CSV 다운로드",
            data=csv,
            file_name="gitlab_users.csv",
            mime="text/csv"
        )
    else:
        st.info("'사용자 목록 갱신' 버튼을 클릭하여 사용자 목록을 불러와주세요.")

def show_unused_repositories():
    """미사용 저장소 화면"""
    st.subheader("미사용 저장소")
    
    # GitLab 연결 확인
    if not check_gitlab_connection():
        st.error("GitLab 연결에 실패했습니다. GitLab 설정을 확인해주세요.")
        return
    
    # 기간 선택
    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox("비활성 기간", ["3개월", "6개월", "1년", "2년"])
    
    # 저장소 목록 불러오기
    if st.button("미사용 저장소 조회"):
        with st.spinner("저장소 목록을 분석하는 중입니다..."):
            # 기간에 따른 날짜 계산
            if period == "3개월":
                days = 90
            elif period == "6개월":
                days = 180
            elif period == "1년":
                days = 365
            elif period == "2년":
                days = 730
            
            # 미사용 저장소 목록 불러오기
            unused_repos = get_unused_repositories(days)
            
            if unused_repos:
                # 세션 상태에 저장
                st.session_state.unused_repos = unused_repos
                st.success(f"총 {len(unused_repos)}개의 미사용 저장소를 발견했습니다.")
            else:
                st.info("미사용 저장소가 없습니다.")
    
    # 미사용 저장소 목록 표시
    if hasattr(st.session_state, 'unused_repos'):
        unused_repos = st.session_state.unused_repos
        
        # 데이터프레임 생성
        df = pd.DataFrame([{
            "ID": repo["id"],
            "그룹": repo["namespace"]["name"],
            "프로젝트": repo["name"],
            "설명": repo.get("description", ""),
            "URL": repo["web_url"],
            "생성일": repo["created_at"],
            "최근 활동": repo["last_activity_at"],
            "소유자": repo.get("owner_name", "알 수 없음")
        } for repo in unused_repos])
        
        # 데이터프레임 표시
        st.dataframe(df)
        
        # CSV 다운로드 버튼
        csv = df.to_csv(index=False)
        st.download_button(
            label="미사용 저장소 목록 CSV 다운로드",
            data=csv,
            file_name=f"gitlab_unused_repos_{period}.csv",
            mime="text/csv"
        )
    else:
        st.info("'미사용 저장소 조회' 버튼을 클릭하여 미사용 저장소 목록을 불러와주세요.")

def show_gitlab_settings():
    """GitLab 설정 화면"""
    st.subheader("GitLab 설정")
    
    # 현재 설정된 GitLab 정보 불러오기
    gitlab_host = os.environ.get("GITLAB_HOST", "")
    gitlab_token = os.environ.get("GITLAB_TOKEN", "")
    
    # GitLab 설정 입력 폼
    with st.form("gitlab_settings_form"):
        new_gitlab_host = st.text_input("GitLab 서버 주소", value=gitlab_host)
        new_gitlab_token = st.text_input("개인 액세스 토큰", value=gitlab_token, type="password")
        
        # 저장 버튼
        submit_button = st.form_submit_button("설정 저장")
        
        if submit_button:
            # .env 파일 업데이트
            update_env_file({
                "GITLAB_HOST": new_gitlab_host,
                "GITLAB_TOKEN": new_gitlab_token
            })
            
            st.success("GitLab 설정이 저장되었습니다.")
    
    # GitLab 연결 테스트 버튼
    if st.button("연결 테스트"):
        if check_gitlab_connection():
            st.success("GitLab 연결에 성공했습니다.")
        else:
            st.error("GitLab 연결에 실패했습니다. 설정을 확인해주세요.")

    # 버전 정보 섹션
    st.subheader("GitLab 서버 정보")

    # GitLab 서버 버전 확인 버튼
    if st.button("GitLab 서버 버전 확인"):
        with st.spinner("GitLab 서버 버전을 확인 중입니다..."):
            gitlab_version = get_gitlab_version()

            if gitlab_version:
                st.success("GitLab 서버 연결 성공")
                st.write(f"버전: {gitlab_version['version']}")
                if 'revision' in gitlab_version:
                    st.write(f"리비전: {gitlab_version['revision']}")
            else:
                st.error("GitLab 서버 연결 실패")
                st.info("GitLab 설정을 확인해주세요.")
    
    # 모듈 저장소 및 버전 정보
    with st.expander("모듈 버전 정보", expanded=False):
        # 저장된 저장소 URL 로드 또는 기본값 사용
        repo_url = version.load_repo_url(MODULE_ID) or DEFAULT_REPO_URL

        # 저장소 URL 설정 폼
        with st.form("repo_url_form"):
            new_repo_url = st.text_input("저장소 URL", value=repo_url, help="GitHub 릴리즈/태그 또는 GitLab 태그 URL")
            submit = st.form_submit_button("저장")

            if submit and new_repo_url:
                if save_repo_url(MODULE_ID, new_repo_url):
                    st.success("저장소 URL이 저장되었습니다.")
                    repo_url = new_repo_url

        # 모듈 버전 정보 표시
        st.write(f"현재 모듈 버전: {VERSION}")
        
        # 모듈 최신 버전 확인
        if st.button("모듈 최신 버전 확인"):
            with st.spinner("최신 버전 확인 중..."):
                latest_release = get_latest_version(repo_url)
                
                if latest_release:
                    latest_version = latest_release["version"]
                    version_status = compare_versions(VERSION, latest_version)
                    
                    if version_status == -1:
                        st.warning(f"새 버전의 모듈이 있습니다: {latest_version}")
                        st.markdown(f"[{repo_url.split('/')[-2] if '/tags' in repo_url else '저장소'}에서 업데이트 확인]({latest_release['url']})")
                        
                        # 릴리스 노트 표시 (GitHub 릴리스인 경우)
                        if latest_release.get("source") == "github_release" and "body" in latest_release:
                            with st.expander("릴리스 노트"):
                                st.markdown(f"## {latest_release['name']}")
                                st.markdown(latest_release['body'])
                        
                    elif version_status == 0:
                        st.success(f"최신 모듈 버전을 사용 중입니다: {latest_version}")
                    elif version_status == 1:
                        st.info(f"개발 버전의 모듈을 사용 중입니다. 최신 안정 버전: {latest_version}")
                    else:
                        st.error("버전 비교 실패: 잘못된 버전 형식입니다.")
                else:
                    st.error(f"저장소에서 최신 버전 정보를 가져오지 못했습니다: {repo_url}")

def check_gitlab_connection():
    """GitLab 연결 테스트"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return False
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        url = f"{gitlab_host}/api/v4/version"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return True
    except Exception as e:
        st.error(f"GitLab 연결 실패: {e}")
        return False

def get_all_repositories():
    """모든 GitLab 저장소 목록 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return []
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        projects = []
        page = 1
        
        while True:
            url = f"{gitlab_host}/api/v4/projects?per_page=100&page={page}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                break
            
            # 데이터 형식 검증 및 불필요한 필드 제거
            for project in data:
                # 필수 필드 확인
                if all(key in project for key in ["id", "name", "namespace", "web_url", "created_at", "last_activity_at"]):
                    # 네임스페이스 확인 및 보정
                    if not isinstance(project["namespace"], dict) or "name" not in project["namespace"]:
                        project["namespace"] = {"name": "Unknown"}
                    
                    # 필수 필드만 유지하여 메모리 절약
                    clean_project = {
                        "id": project["id"],
                        "name": project["name"],
                        "namespace": {"name": project["namespace"]["name"]},
                        "description": project.get("description", ""),
                        "web_url": project["web_url"],
                        "created_at": project["created_at"],
                        "last_activity_at": project["last_activity_at"]
                    }
                    projects.append(clean_project)
            
            page += 1
            time.sleep(0.5)  # API 요청 제한 방지
        
        return projects
    except Exception as e:
        st.error(f"저장소 목록 조회 실패: {e}")
        return []

def get_repository_details(repo_id):
    """저장소 상세 정보 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return None
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        url = f"{gitlab_host}/api/v4/projects/{repo_id}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"저장소 상세 정보 조회 실패: {e}")
        return None

def get_project_members(project_id):
    """프로젝트 멤버 목록 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return []
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        members = []
        page = 1
        
        while True:
            url = f"{gitlab_host}/api/v4/projects/{project_id}/members/all?per_page=100&page={page}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 404:
                return []
            
            response.raise_for_status()
            
            data = response.json()
            if not data:
                break
            
            members.extend(data)
            page += 1
            time.sleep(0.5)  # API 요청 제한 방지
        
        return members
    except Exception as e:
        st.error(f"프로젝트 멤버 조회 실패: {e}")
        return []

def get_repository_commits(repo_id):
    """저장소 커밋 목록 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return []
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        url = f"{gitlab_host}/api/v4/projects/{repo_id}/repository/commits?per_page=20"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            return []
        
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"저장소 커밋 조회 실패: {e}")
        return []

def get_all_users():
    """모든 GitLab 사용자 목록 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return []
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        users = []
        page = 1
        
        while True:
            url = f"{gitlab_host}/api/v4/users?per_page=100&page={page}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                break
            
            users.extend(data)
            page += 1
            time.sleep(0.5)  # API 요청 제한 방지
        
        return users
    except Exception as e:
        st.error(f"사용자 목록 조회 실패: {e}")
        return []

def get_user_details(user_id):
    """사용자 상세 정보 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return None
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        url = f"{gitlab_host}/api/v4/users/{user_id}"
        
        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            return None

        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"사용자 상세 정보 조회 실패: {e}")
        return None

def get_user_projects(user_id):
    """사용자 프로젝트 목록 조회"""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")
        
        if not all([gitlab_host, gitlab_token]):
            return []
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        url = f"{gitlab_host}/api/v4/users/{user_id}/projects"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"사용자 프로젝트 조회 실패: {e}")
        return []

def get_unused_repositories(days):
    """미사용 저장소 목록 조회"""
    try:
        # 모든 저장소 목록 조회
        repositories = get_all_repositories()
        
        if not repositories:
            return []
        
        # 현재 날짜
        now = datetime.now()
        
        # 미사용 저장소 필터링
        unused_repos = []
        
        for repo in repositories:
            # 마지막 활동 날짜
            last_activity_at = datetime.strptime(repo["last_activity_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
            
            # 미사용 기간 계산
            delta = now - last_activity_at
            
            if delta.days > days:
                # 저장소 소유자 정보 추가
                members = get_project_members(repo["id"])
                
                if members:
                    for member in members:
                        if member["access_level"] == 50:  # Owner
                            repo["owner_name"] = member["name"]
                            break
                
                unused_repos.append(repo)
        
        return unused_repos
    except Exception as e:
        st.error(f"미사용 저장소 조회 실패: {e}")
        return []

def get_access_level_name(access_level):
    """접근 레벨 숫자를 이름으로 변환"""
    if access_level == 10:
        return "Guest"
    elif access_level == 20:
        return "Reporter"
    elif access_level == 30:
        return "Developer"
    elif access_level == 40:
        return "Maintainer"
    elif access_level == 50:
        return "Owner"
    else:
        return f"Unknown ({access_level})"

def update_env_file(new_values):
    """환경 변수 파일 업데이트
    
    Args:
        new_values (dict): 새 환경 변수 값
    """
    # .env 파일 읽기
    env_path = ".env"
    env_vars = {}
    
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env_vars[key] = value
    
    # 새 값으로 업데이트
    env_vars.update(new_values)
    
    # .env 파일 쓰기
    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

def get_gitlab_version():
    """GitLab 서버의 버전 정보를 가져옵니다."""
    try:
        gitlab_host = os.environ.get("GITLAB_HOST")
        gitlab_token = os.environ.get("GITLAB_TOKEN")

        if not all([gitlab_host, gitlab_token]):
            return None
        
        headers = {"PRIVATE-TOKEN": gitlab_token}
        url = f"{gitlab_host}/api/v4/version"

        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        return response.json()
    except Exception as e:
        st.error(f"GitLab 버전 조회 실패: {e}")
        return None