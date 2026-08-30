"""Worker process executing inside the GUI terminal window, managing the live PTY and shell."""

import fcntl
import json
import os
import pty
import select
import shutil
import signal
import socket
import struct
import subprocess
import sys
import termios
import threading
import time
from pathlib import Path


def main():
    if len(sys.argv) >= 3:
        sock_path = sys.argv[1]
        fifo_path = sys.argv[2]
    else:
        sock_path = os.environ.get("LABSHOT_SOCK", "")
        fifo_path = os.environ.get("LABSHOT_FIFO", "")

    if not sock_path or not fifo_path:
        print("Error: Missing socket or FIFO path arguments.", file=sys.stderr)
        sys.exit(1)

    # 1. Connect to controller socket with retry loop
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connected = False
    for _ in range(60):
        try:
            s.connect(sock_path)
            connected = True
            break
        except Exception:
            time.sleep(0.1)

    if not connected:
        print(f"Error: Could not connect to controller socket {sock_path}", file=sys.stderr)
        sys.exit(1)

    rf = s.makefile("r", encoding="utf-8")
    wf = s.makefile("w", encoding="utf-8")

    # 2. Open pseudo-terminal for persistent bash with proper window dimensions
    master_fd, slave_fd = pty.openpty()

    # Query or determine terminal dimensions
    target_cols = int(os.environ.get("LABSHOT_COLS", "110"))
    target_rows = int(os.environ.get("LABSHOT_ROWS", "32"))
    try:
        ts = shutil.get_terminal_size((target_cols, target_rows))
        target_cols, target_rows = ts.columns, ts.lines
    except Exception:
        pass

    winsize = struct.pack("HHHH", target_rows, target_cols, 0, 0)
    try:
        fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)
        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
    except Exception:
        pass

    def preexec():
        os.setsid()
        fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 0)

    title = os.environ.get("LABSHOT_TITLE", f"labshot — CS345 Terminal [{os.environ.get('LABSHOT_TOKEN', '')}]")

    # Explicitly set terminal window title via OSC 0/2 escape sequences
    sys.stdout.write(f"\033]0;{title}\007\033]2;{title}\007")
    sys.stdout.flush()

    env = os.environ.copy()
    # Keep title locked in window caption on every command prompt
    env["PROMPT_COMMAND"] = f'printf "\\033]0;{title}\\007"; echo $? $PWD > {fifo_path}'
    env["PS1"] = os.environ.get("LABSHOT_PS1", r"\u:\w\$ ")
    env["TERM"] = "xterm-256color"
    env["COLUMNS"] = str(target_cols)
    env["LINES"] = str(target_rows)

    bash_proc = subprocess.Popen(
        ["bash", "--noprofile", "--norc", "-i"],
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        preexec_fn=preexec,
        close_fds=True,
        env=env,
    )
    os.close(slave_fd)

    # Forward window resize signals
    def handle_sigwinch(signum, frame):
        try:
            ts = shutil.get_terminal_size((target_cols, target_rows))
            ws = struct.pack("HHHH", ts.lines, ts.columns, 0, 0)
            fcntl.ioctl(master_fd, termios.TIOCSWINSZ, ws)
        except Exception:
            pass

    signal.signal(signal.SIGWINCH, handle_sigwinch)

    # 3. Synchronized PTY buffer forwarder
    running = True

    def forward_terminal_output():
        while running:
            try:
                r, _, _ = select.select([master_fd], [], [], 0.02)
                if r:
                    data = os.read(master_fd, 8192)
                    if not data:
                        break
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
            except Exception:
                break

    forward_thread = threading.Thread(target=forward_terminal_output, daemon=True)
    forward_thread.start()

    # 4. Open FIFO for non-blocking status notifications
    fifo_fd = os.open(fifo_path, os.O_RDWR)
    fifo_file = os.fdopen(fifo_fd, "r")

    # Initial shell prompt trigger & drain
    init_status = fifo_file.readline().strip()
    parts = init_status.split(" ", 1)
    init_pwd = parts[1] if len(parts) > 1 else os.getcwd()

    # Drain initial prompt to terminal
    time.sleep(0.12)
    sys.stdout.buffer.flush()

    wf.write(json.dumps({"status": "ready", "pwd": init_pwd}) + "\n")
    wf.flush()

    # 5. Main command dispatch loop
    while True:
        line = rf.readline()
        if not line:
            break
        try:
            msg = json.loads(line.strip())
        except Exception:
            continue

        action = msg.get("action")
        if action == "exit":
            break

        elif action == "interrupt":
            # Send Ctrl+C (ETX) to PTY
            os.write(master_fd, b"\x03")
            time.sleep(0.05)
            wf.write(json.dumps({"status": "interrupted"}) + "\n")
            wf.flush()

        elif action == "run":
            cmd = msg.get("cmd", "")
            # Clear screen and redraw clean prompt for isolated question capture
            os.write(master_fd, b"")
            time.sleep(0.04)
            # Send command + newline to interactive bash PTY
            os.write(master_fd, (cmd + "\n").encode("utf-8"))

            # Wait for bash completion via FIFO
            status_line = fifo_file.readline().strip()
            status_parts = status_line.split(" ", 1)
            exit_code = int(status_parts[0]) if len(status_parts) > 0 else 0
            pwd = status_parts[1] if len(status_parts) > 1 else ""

            # Ensure all terminal output (including final PS1 prompt) is flushed to GUI
            time.sleep(0.14)
            try:
                sys.stdout.buffer.flush()
                wf.write(json.dumps({"status": "done", "exit_code": exit_code, "pwd": pwd}) + "\n")
                wf.flush()
            except (BrokenPipeError, OSError):
                break

    running = False
    try:
        bash_proc.terminate()
        bash_proc.wait(timeout=1)
    except Exception:
        pass


if __name__ == "__main__":
    main()
