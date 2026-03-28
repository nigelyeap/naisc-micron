"""
Central entry point -- starts the FastAPI backend and React frontend together.

Usage:
    python run.py            # starts both backend + frontend
    python run.py --backend  # backend only
    python run.py --frontend # frontend only
"""

import os
import sys
import time
import subprocess
import argparse

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")


def start_backend():
    """Launch the FastAPI/uvicorn backend as a subprocess."""
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app:app",
         "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=PROJECT_ROOT,
    )


def start_frontend():
    """Launch the Vite dev server."""
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    return subprocess.Popen(
        [npm, "run", "dev"],
        cwd=FRONTEND_DIR,
    )


def main():
    parser = argparse.ArgumentParser(description="Smart Log Parser -- Launcher")
    parser.add_argument("--backend",  action="store_true", help="Start backend only")
    parser.add_argument("--frontend", action="store_true", help="Start frontend only")
    args = parser.parse_args()

    run_backend  = not args.frontend or args.backend
    run_frontend = not args.backend  or args.frontend
    if not args.backend and not args.frontend:
        run_backend = run_frontend = True

    procs = []

    try:
        if run_backend:
            print("[SLP] Starting backend  → http://localhost:8000")
            procs.append(start_backend())

        if run_frontend:
            if run_backend:
                time.sleep(2)
            print("[SLP] Starting frontend → http://localhost:5173")
            procs.append(start_frontend())

        print("[SLP] All services running. Press Ctrl+C to stop.\n")

        while True:
            for p in procs:
                ret = p.poll()
                if ret is not None:
                    print(f"\n[SLP] A process exited with code {ret}")
                    raise SystemExit(ret)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[SLP] Shutting down...")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            p.wait(timeout=5)
        print("[SLP] Stopped.")


if __name__ == "__main__":
    main()
