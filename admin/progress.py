import streamlit as st
import time

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