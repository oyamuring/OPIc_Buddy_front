# 파이썬에서 앱을 시작하게 하는 파일
import os, sys, subprocess
repo = r"C:\PythonEnvs\huggingface\OPIc_Buddy"
script = os.path.join(repo, "app", "main.py")
subprocess.run([sys.executable, "-m", "streamlit", "run", script, "--server.port=8501"], check=True)
