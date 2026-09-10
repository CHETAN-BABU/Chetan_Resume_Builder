#!/usr/bin/env python3
"""Start the local dashboard; no Node.js or API key is needed."""
import argparse
import importlib.util
import sys
import json
import urllib.request
import urllib.error
import threading
import webbrowser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args()
    if not 1024<=args.port<=65535: parser.error('Choose a port from 1024 to 65535')
    if importlib.util.find_spec('uvicorn') is None:
        raise SystemExit('Install dependencies first: python3 -m pip install -r requirements.txt')
    import uvicorn
    from dashboard.app import create_app
    url=f'http://127.0.0.1:{args.port}'
    try:
        with urllib.request.urlopen(url+'/api/health',timeout=1) as response:
            running=json.load(response)
        if running.get('app')=='chetan-career-workspace' and running.get('root')==str(ROOT):
            print(f'Dashboard already running: {url}',flush=True)
            if not args.no_browser: webbrowser.open(url)
            return
    except (OSError, ValueError):
        pass
    print(f'Chetan Career Workspace: {url}',flush=True)
    if not args.no_browser:
        timer=threading.Timer(1.2,lambda:webbrowser.open(url)); timer.daemon=True; timer.start()
    uvicorn.run(create_app(),host='127.0.0.1',port=args.port,log_level='info')
if __name__=='__main__':main()
