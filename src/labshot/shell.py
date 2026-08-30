"""Persistent shell controller communicating with GUI terminal worker process."""

import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from labshot.config import LabConfig, DEFAULT_CONFIG
from labshot.terminal import TerminalManager


@dataclass
class CommandResult:
    """Result of command execution in persistent shell."""
    command: str
    exit_code: int
    cwd_before: str
    cwd_after: str


class PersistentShellController:
    """Spawns and controls a persistent real interactive shell in a GUI terminal."""

    def __init__(
        self,
        lab_name: str,
        config: LabConfig = DEFAULT_CONFIG,
        preferred_term: Optional[str] = None,
    ):
        self.lab_name = lab_name
        self.config = config
        self.temp_dir = tempfile.mkdtemp(prefix="labshot_ctl_")
        self.sock_path = Path(self.temp_dir) / "shell.sock"
        self.fifo_path = Path(self.temp_dir) / "status.fifo"
        self.terminal_mgr = TerminalManager(config=config, preferred_term=preferred_term)
        self.server_socket: Optional[socket.socket] = None
        self.conn: Optional[socket.socket] = None
        self.rfile = None
        self.wfile = None
        self.current_cwd: str = os.getcwd()
        self.is_running: bool = False

    def start(self, timeout: float = 12.0) -> None:
        """Create communication primitives, launch GUI terminal, and wait for handshake."""
        # Create status FIFO
        if self.fifo_path.exists():
            self.fifo_path.unlink()
        os.mkfifo(self.fifo_path)

        # Create UNIX domain server socket
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(str(self.sock_path))
        self.server_socket.listen(1)

        # Locate worker script
        import labshot.worker
        worker_file = Path(labshot.worker.__file__).resolve()

        # Launch the GUI terminal running worker.py
        self.terminal_mgr.launch(
            worker_script_path=worker_file,
            sock_path=self.sock_path,
            fifo_path=self.fifo_path,
            lab_name=self.lab_name,
        )

        self.server_socket.settimeout(timeout)
        try:
            self.conn, _ = self.server_socket.accept()
            self.rfile = self.conn.makefile("r", encoding="utf-8")
            self.wfile = self.conn.makefile("w", encoding="utf-8")

            # Receive ready message
            ready_line = self.rfile.readline()
            ready_data = json.loads(ready_line.strip())
            self.current_cwd = ready_data.get("pwd", os.getcwd())
            self.is_running = True
        except Exception as e:
            self.close()
            raise RuntimeError(
                f"Failed to establish connection with terminal window within {timeout}s: {e}"
            )

    def execute(self, command: str, timeout: Optional[float] = None) -> CommandResult:
        """Execute a command in the persistent shell and wait for completion."""
        if not self.is_running or not self.wfile or not self.rfile:
            raise RuntimeError("Persistent shell is not running.")

        timeout_sec = timeout or self.config.default_timeout_seconds
        cwd_before = self.current_cwd

        # Send run command
        payload = json.dumps({"action": "run", "cmd": command}) + "\n"
        self.wfile.write(payload)
        self.wfile.flush()

        # Wait for completion with timeout
        self.conn.settimeout(timeout_sec)
        try:
            line = self.rfile.readline()
            if not line:
                raise RuntimeError("Connection closed by terminal worker.")

            resp = json.loads(line.strip())
            exit_code = int(resp.get("exit_code", 0))
            cwd_after = resp.get("pwd", cwd_before)
            self.current_cwd = cwd_after

            return CommandResult(
                command=command,
                exit_code=exit_code,
                cwd_before=cwd_before,
                cwd_after=cwd_after,
            )
        except socket.timeout:
            # Handle interactive command timeout or hang
            self.interrupt()
            raise TimeoutError(f"Command '{command}' exceeded timeout of {timeout_sec}s.")

    def interrupt(self) -> None:
        """Send interrupt (Ctrl+C) to the running command in the shell."""
        if self.wfile:
            try:
                self.wfile.write(json.dumps({"action": "interrupt"}) + "\n")
                self.wfile.flush()
            except Exception:
                pass

    def activate_terminal_window(self) -> None:
        """Ensure the terminal window is raised and focused before screenshot."""
        self.terminal_mgr.activate_window()

    def close(self) -> None:
        """Terminate the terminal and close sockets."""
        self.is_running = False
        if self.wfile:
            try:
                self.wfile.write(json.dumps({"action": "exit"}) + "\n")
                self.wfile.flush()
            except Exception:
                pass

        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

        self.terminal_mgr.close()

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass
            self.temp_dir = None
