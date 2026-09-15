#!/usr/bin/env python3
"""Build the React client with whichever local Node runtime is installed."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The runtime that shipped with the original workspace; still used when nothing
# else is installed, so an existing machine keeps working unchanged.
BUNDLED = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies"
MISSING = (
    "Building the dashboard needs Node.js and pnpm. Install Node.js (for example "
    "`brew install node` and `corepack enable pnpm`), or set CAREER_NODE_BIN and "
    "CAREER_PNPM_BIN to their paths, then start the dashboard again."
)


def newest(pattern):
    def key(path):
        name = path.parents[1].name.lstrip("v")
        return [int(p) if p.isdigit() else -1 for p in name.split(".")]

    return sorted(Path.home().glob(pattern), key=key, reverse=True)


def find(env_name, command, extra=()):
    candidates = [os.environ.get(env_name), shutil.which(command)]
    candidates += [str(p) for p in extra]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def node_binary():
    return find(
        "CAREER_NODE_BIN",
        "node",
        [
            "/opt/homebrew/bin/node",
            "/usr/local/bin/node",
            *newest(".nvm/versions/node/*/bin/node"),
            *newest("Library/Application Support/fnm/node-versions/*/installation/bin/node"),
            Path.home() / ".volta/bin/node",
            BUNDLED / "node/bin/node",
        ],
    )


def pnpm_binary():
    return find(
        "CAREER_PNPM_BIN",
        "pnpm",
        [
            Path.home() / "Library/pnpm/pnpm",
            "/opt/homebrew/bin/pnpm",
            "/usr/local/bin/pnpm",
            BUNDLED / "bin/fallback/pnpm",
        ],
    )


def build(force=False):
    frontend = ROOT / "frontend"
    sources = [
        *frontend.glob("src/**/*"),
        frontend / "package.json",
        frontend / "pnpm-lock.yaml",
        frontend / "index.html",
        frontend / "vite.config.ts",
    ]
    output = frontend / "dist/index.html"
    current = output.exists() and all(
        p.stat().st_mtime <= output.stat().st_mtime for p in sources if p.is_file()
    )
    if not force and current:
        return
    node = node_binary()
    if not node:
        if output.exists():
            # Serve the build that is already on disk rather than refusing to start.
            print("WARN: Node.js was not found; serving the existing client build. " + MISSING,
                  file=sys.stderr, flush=True)
            return
        raise SystemExit(MISSING)
    env = {
        **os.environ,
        "PATH": str(Path(node).parent) + os.pathsep + os.environ.get("PATH", ""),
    }
    if not (frontend / "node_modules").exists():
        pnpm = pnpm_binary()
        if not pnpm:
            if output.exists():
                print("WARN: pnpm was not found; serving the existing client build. " + MISSING,
                      file=sys.stderr, flush=True)
                return
            raise SystemExit(MISSING)
        subprocess.run(
            [pnpm, "install", "--frozen-lockfile"], cwd=frontend, env=env, check=True
        )
    subprocess.run(
        [node, str(frontend / "node_modules/typescript/bin/tsc"), "-b"],
        cwd=frontend,
        env=env,
        check=True,
    )
    subprocess.run(
        [node, str(frontend / "node_modules/vite/bin/vite.js"), "build"],
        cwd=frontend,
        env=env,
        check=True,
    )


if __name__ == "__main__":
    build(force=True)
