#!/usr/bin/env python3
"""一键启动开发环境：后端 + 前端"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

processes: dict[str, subprocess.Popen] = {}
_shutdown_event = threading.Event()


def _monitor_thread(name: str, proc: subprocess.Popen) -> None:
    """后台线程：等待子进程退出，异常退出时通知主线程。"""
    ret = proc.wait()
    if not _shutdown_event.is_set():
        print(f"\n[错误] {name} 异常退出 (code: {ret})", flush=True)
        _shutdown_event.set()


def start_service(name: str, cmd: list[str], cwd: Path, label: str = "") -> subprocess.Popen:
    """启动一个服务子进程，输出直接打印到终端。"""
    display = label or cmd[-1]
    print(f"[启动] {name} -> {display}", flush=True)
    return subprocess.Popen(
        cmd,
        cwd=cwd,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )


def shutdown() -> None:
    """优雅关闭所有服务。"""
    _shutdown_event.set()
    print("\n正在关闭所有服务...", flush=True)
    for name, proc in processes.items():
        if proc.poll() is None:
            print(f"  -> 停止 {name} (PID: {proc.pid})", flush=True)
            proc.terminate()
    for _ in range(30):
        if all(p.poll() is not None for p in processes.values()):
            break
        time.sleep(0.1)
    for name, proc in processes.items():
        if proc.poll() is None:
            proc.kill()
    print("[完成] 所有服务已停止", flush=True)


def main() -> None:
    """启动所有开发服务。"""
    print("=" * 60, flush=True)
    print("  开发环境启动脚本", flush=True)
    print("=" * 60, flush=True)

    if not BACKEND_DIR.exists():
        print(f"[错误] 后端目录不存在: {BACKEND_DIR}", flush=True)
        sys.exit(1)
    if not FRONTEND_DIR.exists():
        print(f"[错误] 前端目录不存在: {FRONTEND_DIR}", flush=True)
        sys.exit(1)

    def _signal_handler(signum: int, _frame) -> None:
        shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    processes["backend"] = start_service(
        "backend",
        [
            "uv",
            "run",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
        BACKEND_DIR,
        label="http://localhost:8000",
    )
    processes["frontend"] = start_service(
        "frontend",
        [npm_cmd, "run", "dev"],
        FRONTEND_DIR,
        label="http://localhost:5173",
    )

    # 为每个进程启动监控线程
    for name, proc in processes.items():
        t = threading.Thread(target=_monitor_thread, args=(name, proc), daemon=True)
        t.start()

    print("-" * 60, flush=True)
    print("  服务已启动：", flush=True)
    print("    - 前端:       http://localhost:5173", flush=True)
    print("    - 后端 API:   http://localhost:8000", flush=True)
    print("    - API 文档:   http://localhost:8000/docs", flush=True)
    print("-" * 60, flush=True)
    print("  按 Ctrl+C 停止所有服务\n", flush=True)

    try:
        # 主线程等待，子进程输出直接打印到终端
        while not _shutdown_event.wait(1):
            pass
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()


if __name__ == "__main__":
    main()
