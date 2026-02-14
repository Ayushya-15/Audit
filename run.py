#!/usr/bin/env python3
"""RiskShield local runner — starts backend and frontend without Docker."""

import os
import sys
import subprocess
import shutil
import signal
import time

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
VENV_DIR = os.path.join(ROOT_DIR, "venv")

processes = []


def _run(cmd, cwd=None, check=True):
    """Run a command and stream output."""
    print(f"  → {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=check)


def setup_backend():
    """Create virtualenv (if needed) and install Python dependencies."""
    pip = os.path.join(VENV_DIR, "bin", "pip") if os.name != "nt" else os.path.join(VENV_DIR, "Scripts", "pip.exe")

    if not os.path.isdir(VENV_DIR):
        print("\n[1/4] Creating virtual environment …")
        _run([sys.executable, "-m", "venv", VENV_DIR])
    else:
        print("\n[1/4] Virtual environment already exists.")

    print("\n[2/4] Installing Python dependencies …")
    _run([pip, "install", "-r", os.path.join(BACKEND_DIR, "requirements.txt")])


def setup_frontend():
    """Install Node.js dependencies for the frontend."""
    npm = shutil.which("npm")
    if npm is None:
        print("\n⚠  npm not found — skipping frontend setup.")
        print("   Install Node.js 18+ to enable the frontend.")
        return False
    print("\n[3/4] Installing frontend dependencies …")
    _run([npm, "install"], cwd=FRONTEND_DIR)
    return True


def start_services(frontend_ready):
    """Start backend (uvicorn) and optionally frontend (vite dev)."""
    uvicorn = os.path.join(VENV_DIR, "bin", "uvicorn") if os.name != "nt" else os.path.join(VENV_DIR, "Scripts", "uvicorn.exe")

    print("\n[4/4] Starting services …")
    print("  Backend  → http://localhost:8000")
    backend_proc = subprocess.Popen(
        [uvicorn, "app.main:app", "--reload", "--port", "8000"],
        cwd=BACKEND_DIR,
    )
    processes.append(backend_proc)

    if frontend_ready:
        npm = shutil.which("npm")
        print("  Frontend → http://localhost:5173")
        frontend_proc = subprocess.Popen(
            [npm, "run", "dev"],
            cwd=FRONTEND_DIR,
        )
        processes.append(frontend_proc)

    print("\nRiskShield is running! Press Ctrl+C to stop.\n")


def cleanup(*_args):
    """Terminate child processes on exit."""
    for proc in processes:
        proc.terminate()
    for proc in processes:
        proc.wait()
    sys.exit(0)


def main():
    print("=" * 50)
    print("  RiskShield — Local Python Runner")
    print("=" * 50)

    setup_backend()
    frontend_ready = setup_frontend()

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    start_services(frontend_ready)

    # Keep the script alive until interrupted
    try:
        while True:
            time.sleep(1)
            # Exit if any child process dies
            for proc in processes:
                if proc.poll() is not None:
                    print("A child process exited.")
                    cleanup()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
