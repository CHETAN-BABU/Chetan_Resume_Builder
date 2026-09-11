#!/usr/bin/env python3
"""Build the React client with the installed Node runtime and locked dependencies."""
import os
import shutil
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def build(force=False):
    frontend=ROOT/'frontend'
    sources=[*frontend.glob('src/**/*'),frontend/'package.json',frontend/'pnpm-lock.yaml',frontend/'index.html',frontend/'vite.config.ts']
    output=frontend/'dist/index.html'
    if not force and output.exists() and all(p.stat().st_mtime<=output.stat().st_mtime for p in sources if p.is_file()):return
    runtime=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies'
    node=shutil.which('node') or str(runtime/'node/bin/node')
    pnpm=shutil.which('pnpm') or str(runtime/'bin/fallback/pnpm')
    if not Path(node).exists() or not Path(pnpm).exists():raise SystemExit('Building the dashboard needs Node.js and pnpm. Install them or open this workspace in Codex and retry.')
    env={**os.environ,'PATH':str(Path(node).parent)+os.pathsep+os.environ.get('PATH','')}
    if not (frontend/'node_modules').exists():subprocess.run([pnpm,'install','--frozen-lockfile'],cwd=frontend,env=env,check=True)
    subprocess.run([node,str(frontend/'node_modules/typescript/bin/tsc'),'-b'],cwd=frontend,env=env,check=True)
    subprocess.run([node,str(frontend/'node_modules/vite/bin/vite.js'),'build'],cwd=frontend,env=env,check=True)
if __name__=='__main__':build(force=True)
