# labshot 📸⚡

> **Real Terminal Lab Screenshot Recorder for Linux University Coursework & Lab Submissions**

`labshot` is a Linux CLI tool designed for university students (e.g. CS345 Operating Systems / Linux Labs). It lets you execute lab commands in a **real, persistent PTY-backed Bash shell** running inside an authentic GUI terminal window (such as Alacritty or Konsole) and automatically captures **genuine, pixel-perfect native screenshots** of the terminal window after every question.

---

## 🚫 No Fake Images

`labshot` does **NOT** synthesize fake terminal images using HTML, SVG, Canvas, or Pillow:
- Every `.png` is an **actual hardware/compositor-rendered screen capture** of a real Linux terminal emulator window.
- Captures genuine font rendering, true colors, standard prompts, exit codes, and output formatting.
- Generated screenshots are sized and styled with high contrast and crisp typography, optimized for inserting directly into **Microsoft Word / DOCX** lab submission reports.

---

## 🏗️ Architecture

```
                      +-----------------------------+
                      |   Student CLI Controller    |
                      |   (Q1 > ls -la, :redo, ...) |
                      +--------------+--------------+
                                     |
                          IPC (UNIX Domain Socket)
                                     |
                                     v
                      +-----------------------------+
                      | Real GUI Terminal (Window)  |
                      | (Alacritty / Konsole)       |
                      |                             |
                      |   +-----------------------+ |
                      |   | Worker (PTY Master)   | |
                      |   +-----------+-----------+ |
                      |               |             |
                      |   +-----------v-----------+ |
                      |   | Persistent Bash Shell | |
                      |   | (student@cs345:\w$ )  | |
                      |   +-----------+-----------+ |
                      +---------------+-------------+
                                      |
                      PROMPT_COMMAND Completion FIFO
                                      |
                                      v
                      +-----------------------------+
                      | Native Screenshot Engine    |
                      | (Spectacle / Grim / Scrot)  |
                      +--------------+--------------+
                                     |
                                     v
                 CS345/<Lab-Name>/
                 ├── screenshots/q1.png, q2.png, ...
                 ├── commands/q1.txt, q2.txt, ...
                 └── lab.json
```

---

## ✨ Features

- **Persistent Shell State**: Single bash process throughout the entire lab. Directory changes (`cd ..`, `cd /path`), exported environment variables, and background jobs persist across all questions.
- **Zero Configuration Setup**: Uses 100% Python standard library (`pty`, `termios`, `fcntl`, `socket`, `subprocess`). No heavy external Python dependencies.
- **Wayland & X11 Native**: Built-in support for **KDE Plasma Wayland (Spectacle)**, **wlroots Wayland (Grim/Slurp)**, and **X11 (Scrot/ImageMagick)**.
- **Report-Ready Styling**: High-contrast, clean 110×32 terminal layout, 13pt monospace typography, solid background (zero blur/transparency) for sharp Word/DOCX readability.
- **Non-blocking Completion Detection**: Uses `PROMPT_COMMAND` IPC signaling — no ugly markers or sentinels printed on the terminal screen.
- **Interactive REPL & Special Commands**:
  - `:help`: Show help and command reference.
  - `:status`: Show current directory, completed questions, active terminal & screenshot engine.
  - `:list`: List all recorded questions with exit codes.
  - `:redo <N>`: Re-execute question N and replace its evidence.
  - `:export`: Export submission bundle with `qN.png` and `commands.txt`.
  - `:exit`: Gracefully close session.
- **Session Resume**: Automatically resumes from the next question if you close and re-open `labshot`.

---

## 🚀 Quick Start

### 1. Launch a Lab Session

```bash
./bin/labshot --lab "Essential Linux Commands"
```

Or execute directly with Python:

```bash
python3 -m labshot.cli --lab "Essential Linux Commands"
```

### 2. Answer Lab Questions

```
============================================================
  CS345 Lab Screenshot Recorder
  Lab: Essential Linux Commands
  Terminal: alacritty | Screenshot: Spectacle (KDE Native)
============================================================
Type lab commands to execute & capture. Internal commands: :help, :status, :list, :redo <N>, :exit

Q1 > ls -la
Captured → screenshots/q1.png
Q2 > cd ..
Captured → screenshots/q2.png
Q3 > mkdir projects
Captured → screenshots/q3.png
Q4 > pwd
Captured → screenshots/q4.png
Q5 > cd projects
Captured → screenshots/q5.png
Q6 > touch test.txt
Captured → screenshots/q6.png
Q7 > ls -la
Captured → screenshots/q7.png
```

### 3. Lab Directory Structure

```
CS345/
└── Essential-Linux-Commands/
    ├── screenshots/
    │   ├── q1.png
    │   ├── q2.png
    │   ├── q3.png
    │   ├── q4.png
    │   ├── q5.png
    │   ├── q6.png
    │   └── q7.png
    ├── commands/
    │   ├── q1.txt
    │   ├── q2.txt
    │   ├── q3.txt
    │   ├── q4.txt
    │   ├── q5.txt
    │   ├── q6.txt
    │   └── q7.txt
    └── lab.json
```

---

## 📋 Metadata Format (`lab.json`)

```json
{
  "lab": "Essential Linux Commands",
  "created_at": "2026-08-30T23:31:30.002106",
  "updated_at": "2026-08-30T23:31:40.014153",
  "questions": [
    {
      "number": 1,
      "command": "ls -la",
      "screenshot": "screenshots/q1.png",
      "command_file": "commands/q1.txt",
      "exit_code": 0,
      "timestamp": "2026-08-30T23:31:32.493257",
      "working_directory_before": "/home/student",
      "working_directory_after": "/home/student"
    }
  ]
}
```

---

## 📤 Submission Export

Generate a submission package formatted for your lab assignment report:

```bash
./bin/labshot export --lab "Essential Linux Commands"
```

Creates `CS345/Essential-Linux-Commands/submission/`:
- `q1.png`, `q2.png`, `q3.png` ...
- `commands.txt` (summary of all questions with exit codes and working directories)

---

## 🧪 Testing

Run the automated test suite:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

---

## 📄 License

MIT License. Designed for CS345 Operating Systems and Linux coursework.
