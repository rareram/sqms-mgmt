import streamlit as st
import os
import json
from dotenv import load_dotenv
import importlib
import sys
import pkgutil
from pathlib import Path
import time

VERSION = "v0.2.250407"

# 앱 정보 관리 클래스
class AppConfig:
    def __init__(self):
        # 기본 설정 로드
        self.config_file = "config.json"
        self.config = self.load_config()

        if "version" not in self.config:
            self.config["version"] = VERSION
            self.save_config()
    
    def load_config(self):
        """설정 파일 로드"""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # 기본 설정
            default_config = {
                "app_name": "IT 관리 시스템",
                "logo_path": "assets/logo.png",
                "theme": "light",
                "modules": []
            }
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config=None):
        """설정 파일 저장"""
        if config:
            self.config = config
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)
    
    def get_modules(self):
        """활성화된, 사용 가능한 모듈 목록 반환"""
        # 사용 가능한 모든 모듈 검색
        available_modules = []
        modules_dir = Path("modules")
        if modules_dir.exists():
            for module_dir in modules_dir.iterdir():
                if module_dir.is_dir() and (module_dir / "__init__.py").exists():
                    module_info_path = module_dir / "module_info.json"
                    if module_info_path.exists():
                        with open(module_info_path, "r", encoding="utf-8") as f:
                            module_info = json.load(f)
                            available_modules.append(module_info)
        
        # 활성화된 모듈 찾기
        active_modules = []
        for module in self.config["modules"]:
            for available in available_modules:
                if module["id"] == available["id"]:
                    active_modules.append(available)
                    break
        
        return active_modules, available_modules
    
    def add_module(self, module_id):
        """모듈 활성화"""
        # 이미 활성화되어 있는지 확인
        for module in self.config["modules"]:
            if module["id"] == module_id:
                return
        
        # 모듈 정보 로드
        module_info_path = Path(f"modules/{module_id}/module_info.json")
        if module_info_path.exists():
            with open(module_info_path, "r", encoding="utf-8") as f:
                module_info = json.load(f)
                self.config["modules"].append({"id": module_id, "enabled": True})
                self.save_config()
    
    def remove_module(self, module_id):
        """모듈 비활성화"""
        self.config["modules"] = [m for m in self.config["modules"] if m["id"] != module_id]
        self.save_config()
    
    def update_app_info(self, app_name=None, logo_path=None, theme=None):
        """앱 정보 업데이트"""
        if app_name:
            self.config["app_name"] = app_name
        if logo_path:
            self.config["logo_path"] = logo_path
        if theme:
            self.config["theme"] = theme
        self.save_config()

# 애플리케이션 전체에 사용할 CSS 정의
def add_custom_css():
    st.markdown("""
    <style>
    /* 그라데이션 진행 표시줄 스타일 */
    .stProgress > div > div {
        background-image: linear-gradient(to right, #FF7A00, #EA002C);
    }
    
    /* 앱 이름 아래 버전 텍스트 스타일 */
    .version-text {
        font-size: 0.8em;
        color: #888;
        margin-top: -1.5em;
        margin-bottom: 1em;
    }
    
    /* 상단 그라데이션 바 */
    .gradient-header {
        background-image: linear-gradient(to right, #FF7A00, #EA002C);
        height: 5px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 진행 표시줄 유틸리티 함수
def show_progress_bar(message="처리 중입니다...", steps=10, sleep_time=0.1):
    """그라데이션 진행 표시줄 표시
    
    Args:
        message (str): 표시할 메시지
        steps (int): 진행 단계 수
        sleep_time (float): 단계 간 지연 시간(초)
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(steps):
        progress = (i + 1) / steps
        status_text.text(f"{message} ({int(progress * 100)}%)")
        progress_bar.progress(progress)
        time.sleep(sleep_time)
    
    status_text.text(f"{message} 완료!")
    time.sleep(0.5)
    progress_bar.empty()
    status_text.empty()

# 모듈 로더
def load_module(module_id):
    """모듈 동적 로드"""
    try:
        module = importlib.import_module(f"modules.{module_id}")
        return module
    except ImportError as e:
        st.error(f"모듈 로드 실패: {e}")
        return None

# 메인 애플리케이션
def main():
    # 환경변수 로드
    load_dotenv()

    # 커스텀 CSS 추가
    add_custom_css()

    # 그라데이션 헤더 바 추가
    st.markdown('<div class="gradient-header"></div>', unsafe_allow_html=True)
    
    # 앱 설정 로드
    app_config = AppConfig()

    # 사이드바 설정
    with st.sidebar:
        # 로고와 앱 이름 표시
        if os.path.exists(app_config.config["logo_path"]):
            st.image(app_config.config["logo_path"], width=100)
        st.title(app_config.config["app_name"])

        # 버전 정보 표시
        # st.caption(f"버전: {app_config.config.get('version', VERSION)}")
        st.markdown(f'<p class="version-text">버전: {app_config.config.get("version", VERSION)}</p>', unsafe_allow_html=True)
        
        # 활성화된 모듈 목록
        active_modules, _ = app_config.get_modules()
        
        # 모듈 선택 옵션
        if active_modules:
            module_names = ["메인 대시보드"] + [m["name"] for m in active_modules]
            selected_module = st.selectbox("모듈 선택", module_names)
        else:
            selected_module = "메인 대시보드"
            st.info("활성화된 모듈이 없습니다. 설정에서 모듈을 추가해주세요.")
        
        # 설정 버튼
        if st.button("⚙️ 설정"):
            selected_module = "설정"
    
    # 선택된 모듈에 따라 콘텐츠 표시
    if selected_module == "메인 대시보드":
        show_dashboard(app_config)
    elif selected_module == "설정":
        show_settings(app_config)
    else:
        # 활성화된 모듈 중에서 해당 모듈 찾기
        for module_info in active_modules:
            if module_info["name"] == selected_module:
                module = load_module(module_info["id"])
                if module and hasattr(module, "show_module"):
                    module.show_module()
                break

def show_dashboard(app_config):
    """메인 대시보드 표시"""
    st.title("IT 관리 시스템 대시보드")
    
    # 활성화된 모듈 정보 표시
    active_modules, _ = app_config.get_modules()
    
    if not active_modules:
        st.info("활성화된 모듈이 없습니다. 설정에서 모듈을 추가해주세요.")
        return
    
    # 모듈별 요약 정보 표시
    st.subheader("활성화된 모듈")
    
    cols = st.columns(min(3, len(active_modules)))
    for i, module_info in enumerate(active_modules):
        with cols[i % 3]:
            st.card(
                title=module_info["name"],
                text=module_info["description"]
            )

def show_settings(app_config):
    """설정 페이지 표시"""
    st.title("설정")
    
    # 탭 생성
    tab1, tab2 = st.tabs(["앱 설정", "모듈 관리"])
    
    # 앱 설정 탭
    with tab1:
        st.subheader("앱 정보 설정")
        
        # 앱 이름 설정
        app_name = st.text_input("앱 이름", app_config.config["app_name"])
        
        # 로고 설정
        logo_path = st.text_input("로고 경로", app_config.config["logo_path"])
        
        # 테마 설정
        theme = st.selectbox("테마", ["light", "dark"], 
                            index=0 if app_config.config["theme"] == "light" else 1)
        
        # 적용 버튼
        if st.button("설정 저장", key="save_app_settings"):
            app_config.update_app_info(app_name, logo_path, theme)
            st.success("설정이 저장되었습니다.")
            st.rerun()
    
    # 모듈 관리 탭
    with tab2:
        st.subheader("모듈 관리")
        
        # 활성화된, 사용 가능한 모듈 목록
        active_modules, available_modules = app_config.get_modules()
        
        # 활성화된 모듈 목록
        st.write("활성화된 모듈")
        if active_modules:
            for module in active_modules:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{module['name']} - {module['description']}")
                with col2:
                    if st.button("비활성화", key=f"disable_{module['id']}"):
                        app_config.remove_module(module['id'])
                        st.success(f"{module['name']} 모듈이 비활성화되었습니다.")
                        st.rerun()
        else:
            st.info("활성화된 모듈이 없습니다.")
        
        # 사용 가능한 모듈 중 활성화되지 않은 모듈
        inactive_modules = [m for m in available_modules if m["id"] not in [am["id"] for am in active_modules]]
        
        if inactive_modules:
            st.write("사용 가능한 모듈")
            for module in inactive_modules:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{module['name']} - {module['description']}")
                with col2:
                    if st.button("활성화", key=f"enable_{module['id']}"):
                        app_config.add_module(module['id'])
                        st.success(f"{module['name']} 모듈이 활성화되었습니다.")
                        st.rerun()

if __name__ == "__main__":
    main()