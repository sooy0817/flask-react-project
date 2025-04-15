import subprocess
import os


os.environ["PATH"] += os.pathsep + r"C:\Program Files\wkhtmltopdf\bin"
# 현재 run_all.py의 위치 기준
base_dir = os.path.abspath(os.path.dirname(__file__))

# 가상환경의 python 경로 (Windows 기준)
venv_python = os.path.join(base_dir, "..", "venv", "Scripts", "python.exe")

# 크롤링 스크립트 리스트
scripts = [
    "hana.py",
    "shjoongang.py",
    "suhyup.py",
    "woori.py",
    "kb.py",
]

# 실행
for script in scripts:
    script_path = os.path.join(base_dir, script)
    print(f"📦📦📦 실행 중: {script}")
    try:
        subprocess.run([venv_python, script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"오류 발생: {script} 실패 → {e}")
