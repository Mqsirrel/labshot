"""Worker process executing inside the GUI terminal window, managing the live PTY and shell."""

import fcntl
import json
import os
import pty
import select
import socket
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

    # 2. Open pseudo-terminal for persistent bash
    master_fd, slave_fd = pty.openpty()

    def preexec():
        os.setsid()
        fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 0)

    env = os.environ.copy()
    env["PROMPT_COMMAND"] = f"echo $? $PWD > {fifo_path}"
    env["PS1"] = r"student@cs345:\w$ "
    env["TERM"] = "xterm-256color"

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

    # 3. Thread: Forward master PTY output directly to GUI terminal stdout
    def forward_terminal_output():
        while True:
            try:
                r, _, _ = select.select([master_fd], [], [], 0.05)
                if r:
                    data = os.read(master_fd, 4096)
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

    # Initial shell prompt trigger
    init_status = fifo_file.readline().strip()
    parts = init_status.split(" ", 1)
    init_pwd = parts[1] if len(parts) > 1 else os.getcwd()

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
            # Send command + newline to interactive bash PTY
            os.write(master_fd, (cmd + "\n").encode("utf-8"))

            # Wait for bash completion via FIFO
            status_line = fifo_file.readline().strip()
            status_parts = status_line.split(" ", 1)
            exit_code = int(status_parts[0]) if len(status_parts) > 0 else 0
            pwd = status_parts[1] if len(status_parts) > 1 else ""

            # Brief pause to allow terminal render engine to display full text buffer
            time.sleep(0.08)

            wf.write(json.dumps({"status": "done", "exit_code": exit_code, "pwd": pwd}) + "\n")
            wf.flush()

    try:
        bash_proc.terminate()
        bash_proc.wait(timeout=1)
    except Exception:
        pass
    s.close()


if __name__ == "__main__":
    main()
