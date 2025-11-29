import os, sys, subprocess

BASE = os.path.dirname(__file__)
PY = sys.executable
REQ = os.path.join(BASE, 'requirements.txt')
APP = os.path.join(BASE, 'app.py')

NEEDED = ['flask', 'exifread', 'waitress']

def ensure_deps():
    try:
        for m in NEEDED:
            __import__(m)
        return
    except Exception:
        pass
    print('[GeoPic] Installing dependencies...')
    subprocess.check_call([PY, '-m', 'pip', 'install', '-r', REQ])

if __name__ == '__main__':
    ensure_deps()
    print('[GeoPic] Starting server at http://127.0.0.1:5000')
    os.execv(PY, [PY, APP])
