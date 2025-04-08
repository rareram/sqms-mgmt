import streamlit as st
import os
import json
from dotenv import load_dotenv
import importlib
from pathlib import Path
import time

VERSION = "v0.1.3 - 250408"

def load_config():
    """설정 파일 로드"""
    config_file = "config.json"
    default_config = {
        "app_name": "IT 관리 시스템",
        "logo_path": "assets/logo.png",
        "theme": "light",
        "wide_layout": False,
        "modules": []
    }
    
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            loaded_config = json.load(f)
            # 기본값 설정
            for key, value in default_config.items():
                if key not in loaded_config:
                    loaded_config[key] = value
            return loaded_config
    
    # 설정 파일이 없는 경우 기본 설정 저장
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(default_config, f, ensure_ascii=False, indent=4)
    
    return default_config

# 설정 로드
config = load_config()

# 페이지 설정 - wide_layout 적용
st.set_page_config(
    page_title=config.get("app_name"),
    page_icon="🔧",
    layout="wide" if config.get("wide_layout", False) else "centered",
    initial_sidebar_state="expanded"
)

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

    /* 모듈 카드 스타일 */
    .module-card {
        position: relative;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: #858585;
        transition: all 0.3s ease;
        overflow: hidden;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .module-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .module-card h3 {
        margin-top: 0;
        color: #333;
        font-weight: 600;
    }
    
    .module-card p {
        color: #666;
        margin-bottom: 15px;
    }
    
    .module-card .version {
        font-size: 0.8em;
        color: #888;
        margin-top: 10px;
    }
    
    .gear-icon {
        position: absolute;
        bottom: -25px;
        right: -25px;
        font-size: 100px;
        color: rgba(180, 180, 180, 0.1);
        transform: rotate(30deg);
        z-index: 0;
    }
    
    .module-content {
        position: relative;
        z-index: 1;
    }
    </style>
    """, unsafe_allow_html=True)

# 진행 표시줄 유틸리티 함수
def show_progress_bar(message="처리 중입니다...", steps=10, sleep_time=0.1):
    """그라데이션 진행 표시줄 표시"""
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

# 앱 정보 관리 클래스
class AppConfig:
    def __init__(self):
        self.config_file = "config.json"
        self.config = config  # 전역에서 이미 로드한 설정 사용
        
        if "version" not in self.config:
            self.config["version"] = VERSION
            self.save_config()
    
    def save_config(self, updated_config=None):
        """설정 파일 저장"""
        if updated_config:
            self.config = updated_config
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)
            
        # 전역 설정도 업데이트
        global config
        config = self.config
    
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
                            # 모듈 버전 정보 로드
                            try:
                                module = importlib.import_module(f"modules.{module_info['id']}")
                                if hasattr(module, 'VERSION'):
                                    module_info["version"] = module.VERSION
                            except (ImportError, AttributeError):
                                pass
                            available_modules.append(module_info)
        
        # 활성화된 모듈 찾기
        active_modules = []
        for module in self.config.get("modules", []):
            for available in available_modules:
                if module["id"] == available["id"] and module.get("enabled", True):
                    active_modules.append(available)
                    break
        
        return active_modules, available_modules
    
    def add_module(self, module_id):
        """모듈 활성화"""
        # 이미 활성화된 모듈이 있는지 확인
        for module in self.config.get("modules", []):
            if module["id"] == module_id:
                module["enabled"] = True
                self.save_config()
                return
        
        # 새로운 모듈 추가
        if "modules" not in self.config:
            self.config["modules"] = []
            
        self.config["modules"].append({"id": module_id, "enabled": True})
        self.save_config()
    
    def remove_module(self, module_id):
        """모듈 비활성화"""
        for module in self.config.get("modules", []):
            if module["id"] == module_id:
                module["enabled"] = False
                self.save_config()
                return
    
    def update_app_info(self, app_name=None, logo_path=None, theme=None, wide_layout=None):
        """앱 정보 업데이트"""
        if app_name:
            self.config["app_name"] = app_name
        if logo_path:
            self.config["logo_path"] = logo_path
        if theme:
            self.config["theme"] = theme
        if wide_layout is not None:
            self.config["wide_layout"] = wide_layout
        
        self.save_config()

# 메인 대시보드 표시
def show_dashboard(app_config):
    """메인 대시보드 표시"""
    st.title(config.get("app_name") + " 대시보드")
    
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
            module_version = module_info.get("version", "N/A")

            st.markdown(f"""
            <div class="module-card">
                <div class="gear-icon">⚙️</div>
                <div class="module-content">
                    <h3>{module_info["name"]}</h3>
                    <p>{module_info["description"]}</p>
                    <div class="version">버전: {module_version}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# 설정 페이지 표시
def show_settings(app_config):
    """설정 페이지 표시"""
    st.title("설정")
    
    # 탭 생성
    tab1, tab2 = st.tabs(["앱 설정", "모듈 관리"])
    
    # 앱 설정 탭
    with tab1:
        st.subheader("앱 정보 설정")
        
        with st.form(key="app_setting_form"):
            # 앱 이름 설정
            app_name = st.text_input("앱 이름", config.get("app_name"))
        
            # 로고 설정
            logo_path = st.text_input("로고 경로", config.get("logo_path"))
        
            # 테마 설정
            theme = st.selectbox("테마", ["light", "dark"], 
                            index=0 if config.get("theme", "light") == "light" else 1)
        
            # 레이아웃 설정
            wide_layout = st.checkbox("넓은 레이아웃 사용", config.get("wide_layout", False))

            submit_button = st.form_submit_button("설정 저장")

            if submit_button:
                app_config.update_app_info(app_name, logo_path, theme, wide_layout)
                st.success("설정이 저장되었습니다. 변경사항을 적용하려면 앱을 다시 시작하세요.")
        
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
                    module_version = module.get("version", "N/A")
                    st.write(f"{module['name']} - {module['description']} (버전: {module_version})")
                with col2:
                    if st.button("비활성화", key=f"disable_{module['id']}"):
                        app_config.remove_module(module['id'])
                        st.success(f"{module['name']} 모듈이 비활성화되었습니다.")
                        st.rerun()
        else:
            st.info("활성화된 모듈이 없습니다.")
        
        # 사용 가능한 모듈 중 활성화되지 않은 모듈
        active_ids = [m["id"] for m in active_modules]
        inactive_modules = []
        
        # 비활성화된 모듈과 아직 추가되지 않은 모듈을 모두 검사
        for module in available_modules:
            if module["id"] not in active_ids:
                inactive_modules.append(module)
            else:
                # 모듈 ID가 있지만 비활성화된 경우
                for config_module in config.get("modules", []):
                    if config_module["id"] == module["id"] and not config_module.get("enabled", True):
                        inactive_modules.append(module)
        
        if inactive_modules:
            st.write("사용 가능한 모듈")
            for module in inactive_modules:
                col1, col2 = st.columns([3, 1])
                with col1:
                    module_version = module.get("version", "N/A")
                    st.write(f"{module['name']} - {module['description']} (버전: {module_version})")
                with col2:
                    if st.button("활성화", key=f"enable_{module['id']}"):
                        app_config.add_module(module['id'])
                        st.success(f"{module['name']} 모듈이 활성화되었습니다.")
                        st.rerun()

# 환경변수 업데이트 함수
def update_env_file(new_values):
    """환경 변수 파일 업데이트"""
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
        logo_path = config.get("logo_path")
        if logo_path and os.path.exists(logo_path):
            st.image(logo_path, width=100)
        
        st.title(config.get("app_name"))

        # 버전 정보 표시
        st.markdown(f'<p class="version-text">버전: {VERSION}</p>', unsafe_allow_html=True)
        
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
            st.session_state.selected_module = "설정"
            st.rerun()
        
        # 세션 상태에서 선택된 모듈 가져오기
        if "selected_module" in st.session_state:
            selected_module = st.session_state.selected_module
    
    # 선택된 모듈에 따라 콘텐츠 표시
    if selected_module == "메인 대시보드" or selected_module == "설정":
        # 세션 상태 업데이트
        st.session_state.selected_module = selected_module
        
        # 해당 화면 표시
        if selected_module == "메인 대시보드":
            show_dashboard(app_config)
        else:
            show_settings(app_config)
    else:
        # 활성화된 모듈 중에서 해당 모듈 찾기
        for module_info in active_modules:
            if module_info["name"] == selected_module:
                module = load_module(module_info["id"])
                if module and hasattr(module, "show_module"):
                    # 세션 상태 업데이트
                    st.session_state.selected_module = selected_module
                    module.show_module()
                break

if __name__ == "__main__":
    main()