# 파이썬에서 앱을 시작하게 하는 파일
import os, sys, subprocess

# 현재 디렉토리를 기준으로 상대 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
script = os.path.join(current_dir, "app", "main.py")
subprocess.run([sys.executable, "-m", "streamlit", "run", script, "--server.port=8502"], check=True)
