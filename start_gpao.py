import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PY = sys.executable

def run(*args):
    subprocess.check_call([PY, *args], cwd=BASE_DIR)

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gpao.settings')
    run('manage.py', 'makemigrations', 'core')
    run('manage.py', 'migrate')
    run('manage.py', 'seed_demo')
    run('manage.py', 'runserver', '127.0.0.1:8000')
