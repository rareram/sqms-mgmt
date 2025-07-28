import streamlit as st
import pandas as pd
from modules.dashboard_manager import DashboardManager
from modules.ai_generator import AIGenerator
from utils.config import config

# 페이지 설정
st.set_page_config(
    page_title="Grafana Dashboard Description Editor",
    page_icon="📊",
    layout="wide"
)

# 세션 상태 초기화
if 'dashboard_manager' not in st.session_state:
    st.session_state.dashboard_manager = DashboardManager()

if 'ai_generator' not in st.session_state:
    st.session_state.ai_generator = AIGenerator()

if 'generated_descriptions' not in st.session_state:
    st.session_state.generated_descriptions = {}

if 'selected_folder' not in st.session_state:
    st.session_state.selected_folder = None

if 'selected_dashboard' not in st.session_state:
    st.session_state.selected_dashboard = None

if 'folder_structure' not in st.session_state:
    st.session_state.folder_structure = None

def main():
    st.title("📊 Grafana Dashboard Description Editor")
    st.markdown("---")
    
    # 연결 테스트
    if not test_grafana_connection():
        st.error("Grafana 연결에 실패했습니다. 설정을 확인해주세요.")
        st.stop()
    
    # 사이드바 - 폴더 및 대시보드 선택
    with st.sidebar:
        st.header("📁 폴더 & 대시보드 선택")
        
        # 폴더 구조 로드
        if st.button("🔄 폴더 구조 새로고침"):
            st.session_state.folder_structure = None
            st.rerun()
        
        load_folder_structure()
        
        if st.session_state.folder_structure:
            display_folder_selection()
    
    # 메인 컨텐츠
    if st.session_state.selected_dashboard:
        display_dashboard_editor()
    else:
        display_welcome()

def test_grafana_connection():
    """Grafana 연결 테스트"""
    try:
        if not config.validate():
            return False
        return st.session_state.dashboard_manager.client.test_connection()
    except Exception as e:
        st.error(f"설정 오류: {e}")
        return False

def load_folder_structure():
    """폴더 구조 로드"""
    if st.session_state.folder_structure is None:
        with st.spinner("폴더 구조를 불러오는 중..."):
            st.session_state.folder_structure = st.session_state.dashboard_manager.get_folder_structure()
def display_folder_selection():
    """폴더 및 대시보드 선택 UI"""
    folder_structure = st.session_state.folder_structure
    
    # 폴더 선택
    folder_names = list(folder_structure.keys())
    selected_folder_name = st.selectbox(
        "📁 폴더 선택",
        folder_names,
        index=folder_names.index(st.session_state.selected_folder) if st.session_state.selected_folder in folder_names else 0
    )
    
    if selected_folder_name != st.session_state.selected_folder:
        st.session_state.selected_folder = selected_folder_name
        st.session_state.selected_dashboard = None
        st.rerun()
    
    # 대시보드 선택
    if st.session_state.selected_folder:
        dashboards = folder_structure[st.session_state.selected_folder]['dashboards']
        
        if not dashboards:
            st.info("선택된 폴더에 대시보드가 없습니다.")
            return
        
        dashboard_options = {f"{dash['title']} ({dash['uid']})": dash['uid'] for dash in dashboards}
        selected_dashboard_display = st.selectbox(
            "📊 대시보드 선택",
            list(dashboard_options.keys()),
            index=None
        )
        
        if selected_dashboard_display:
            selected_dashboard_uid = dashboard_options[selected_dashboard_display]
            if selected_dashboard_uid != st.session_state.selected_dashboard:
                st.session_state.selected_dashboard = selected_dashboard_uid
                st.rerun()

def display_welcome():
    """환영 화면"""
    st.header("환영합니다! 👋")
    st.markdown("""
    ### 📋 사용 방법
    1. **왼쪽 사이드바**에서 폴더를 선택하세요
    2. **대시보드**를 선택하세요
    3. **패널별 Description**을 편집하세요
    4. **저장**하여 변경사항을 적용하세요
    
    ### ✨ 주요 기능
    - 📁 폴더 구조별 대시보드 조회
    - 📊 패널 타입별 시각적 구분
    - 📝 Description 일괄 편집
    - 🔍 패널 검색 및 필터링
    - 📜 변경 이력 조회
    """)
def display_dashboard_editor():
    """대시보드 편집기 UI"""
    dashboard_uid = st.session_state.selected_dashboard
    
    # 대시보드 요약 정보
    with st.spinner("대시보드 정보를 불러오는 중..."):
        summary = st.session_state.dashboard_manager.get_dashboard_summary(dashboard_uid)
    
    if not summary:
        st.error("대시보드 정보를 불러올 수 없습니다.")
        return
    
    # 대시보드 정보 표시
    st.header(f"📊 {summary['title']}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 패널", summary['total_panels'])
    with col2:
        st.metric("Description 있음", summary['panels_with_description'])
    with col3:
        st.metric("Description 없음", summary['panels_without_description'])
    with col4:
        st.metric("커버리지", f"{summary['description_coverage']}")
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["📝 패널 편집", "📊 대시보드 정보", "📜 변경 이력"])
    
    with tab1:
        display_panel_editor(dashboard_uid)
    
    with tab2:
        display_dashboard_info(summary)
    
    with tab3:
        display_version_history(summary['id'])
def display_panel_editor(dashboard_uid):
    """패널 편집기 UI"""
    # 검색 및 필터 옵션
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("🔍 패널 제목 검색", "")
    with col2:
        filter_type = st.selectbox("📊 패널 타입 필터", ["all", "graph", "stat", "table", "timeseries", "text"])
    with col3:
        filter_description = st.selectbox("📝 Description 필터", 
                                        ["all", "with_description", "without_description"],
                                        format_func=lambda x: {"all": "전체", "with_description": "있음", "without_description": "없음"}[x])
    
    # 패널 목록 조회
    panels = st.session_state.dashboard_manager.search_panels(
        dashboard_uid, search_term, filter_type, filter_description
    )
    
    if not panels:
        st.info("조건에 맞는 패널이 없습니다.")
        return
    
    st.markdown(f"**{len(panels)}개의 패널이 발견되었습니다.**")
    
    # 패널 편집 폼
    with st.form("panel_editor_form"):
        edited_panels = {}
        
        for i, panel in enumerate(panels):
            st.markdown(f"### {panel['emoji']} {panel['title']}")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**타입:** {panel['type']} | **데이터소스:** {panel['datasource']}")
            with col2:
                if panel['has_description']:
                    st.success("✅ Description 있음")
                else:
                    st.warning("❌ Description 없음")
            
            # Description 편집
            current_desc = panel.get('description', '')
            
            # AI가 생성한 설명이 있으면 사용, 없으면 현재 설명을 사용
            if panel['id'] in st.session_state.generated_descriptions:
                current_desc = st.session_state.generated_descriptions.pop(panel['id'])

            if new_desc != current_desc:
                edited_panels[panel['id']] = new_desc
            
            st.markdown("---")
        
        # 저장 버튼
        if st.form_submit_button("💾 모든 변경사항 저장", type="primary"):
            if edited_panels:
                save_panel_descriptions(dashboard_uid, edited_panels)
            else:
                st.info("변경된 내용이 없습니다.")

    # AI 설명 생성 버튼들을 폼 외부에서 처리
    for i, panel in enumerate(panels):
        if st.button("🤖 AI로 설명 생성", key=f"ai_btn_{panel['id']}"):
            with st.spinner("AI가 설명을 생성하는 중..."):
                panel_details = st.session_state.dashboard_manager.get_panel_details(dashboard_uid, panel['id'])
                if panel_details:
                    generated_desc = st.session_state.ai_generator.generate_description(panel_details)
                    st.session_state.generated_descriptions[panel['id']] = generated_desc
                    st.rerun()
                else:
                    st.error("패널 상세 정보를 가져오는데 실패했습니다.")

    # AI 설명 생성 버튼들을 폼 외부에서 처리
    for i, panel in enumerate(panels):
        if st.button("🤖 AI로 설명 생성", key=f"ai_btn_{panel['id']}"):
            with st.spinner("AI가 설명을 생성하는 중..."):
                panel_details = st.session_state.dashboard_manager.get_panel_details(dashboard_uid, panel['id'])
                if panel_details:
                    generated_desc = st.session_state.ai_generator.generate_description(panel_details)
                    st.session_state.generated_descriptions[panel['id']] = generated_desc
                    st.rerun()
                else:
                    st.error("패널 상세 정보를 가져오는데 실패했습니다.")
def save_panel_descriptions(dashboard_uid, edited_panels):
    """패널 Description 저장"""
    success_count = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (panel_id, description) in enumerate(edited_panels.items()):
        status_text.text(f"패널 {panel_id} 업데이트 중... ({i+1}/{len(edited_panels)})")
        
        if st.session_state.dashboard_manager.update_panel_description(dashboard_uid, panel_id, description):
            success_count += 1
        
        progress_bar.progress((i + 1) / len(edited_panels))
    
    status_text.empty()
    progress_bar.empty()
    
    if success_count == len(edited_panels):
        st.success(f"✅ {success_count}개 패널의 Description이 성공적으로 업데이트되었습니다!")
    else:
        st.warning(f"⚠️ {success_count}/{len(edited_panels)}개 패널만 업데이트되었습니다.")
    
    # 새로고침
    st.rerun()

def display_dashboard_info(summary):
    """대시보드 정보 표시"""
    st.subheader("📊 대시보드 정보")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**제목:** {summary['title']}")
        st.markdown(f"**UID:** {summary['uid']}")
        st.markdown(f"**ID:** {summary['id']}")
    with col2:
        st.markdown(f"**생성일:** {summary['created']}")
        st.markdown(f"**수정일:** {summary['updated']}")
        st.markdown(f"**태그:** {', '.join(summary['tags']) if summary['tags'] else '없음'}")
    
    # 패널 타입별 통계
    st.subheader("📈 패널 타입별 통계")
    if summary['panel_types']:
        df = pd.DataFrame(list(summary['panel_types'].items()), columns=['패널 타입', '개수'])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("패널이 없습니다.")
def display_version_history(dashboard_id):
    """버전 히스토리 표시"""
    st.subheader("📜 변경 이력")
    
    with st.spinner("변경 이력을 불러오는 중..."):
        versions = st.session_state.dashboard_manager.get_dashboard_versions(dashboard_id)
    
    if not versions:
        st.info("변경 이력이 없습니다.")
        return
    
    # 버전 히스토리 테이블
    df = pd.DataFrame(versions)
    df.columns = ['버전', '수정일시', '수정자', '변경사항']
    st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()