# labshot 📸⚡

> **Real Terminal Lab Screenshot Recorder for Linux University Coursework & Lab Submissions**

`labshot` is a one-command Linux CLI tool designed for university students (e.g. CS345 Operating Systems / Linux Labs). It lets you answer lab questions by executing commands in a **real persistent Linux shell** running inside an authentic terminal window (Alacritty / Konsole) and automatically captures **genuine, pixel-perfect native screenshots** of the terminal window after every question.

---

## 🚀 One-Command Simple Workflow

Just run:

```bash
labshot
```

*(or `./bin/labshot`)*

### 1. Interactive Setup

```
Labshot — Linux Lab Evidence Recorder
Lab name: Essential Linux Commands
Lab directory:
  ~/CS345/Essential-Linux-Commands
Starting real terminal session...
Ready.
```

### 2. Enter Commands

```
Q1 > ls -la
✓ Q1 captured → q1.png

Q2 > cd ..
✓ Q2 captured → q2.png

Q3 > mkdir projects
✓ Q3 captured → q3.png

Q4 > pwd
✓ Q4 captured → q4.png
```

### 3. Finish Your Lab

Type `:done` when you're finished:

```
Q5 > :done

==================================================
  ✓ Lab complete
  4 questions captured
  4 screenshots saved
  Folder:
    ~/CS345/Essential-Linux-Commands/
  Submission Package:
    ~/CS345/Essential-Linux-Commands/submission/
==================================================

Open screenshot folder? [y/N]: y
```

---

## ⚡ Useful In-Session Commands

Keep things simple — just a few memorable commands:

| Command | Description |
| :--- | :--- |
| **`<any Linux command>`** | Runs the command in the persistent shell & captures screenshot |
| **`:status`** | Shows visual check-list of captured questions |
| **`:redo <N>`** | Re-takes Question `N` and replaces its evidence |
| **`:done`** | Completes the lab and prepares the submission folder |
| **`:help`** | Displays quick command reference |
| **`:exit`** | Saves and quits |

---

## 🔄 Automatic Resume & Multi-Lab Support

If you run `labshot` again, existing labs are detected automatically:

```
Labshot — Linux Lab Evidence Recorder
Existing lab found:
  Essential Linux Commands (Completed: Q1–Q7)
Resume from Q8? [Y/n]: 
```

Press **Enter** to resume right where you left off — no duplicate questions, no accidental overwrites.

---

## 📁 Automatic Directory Layout

Everything is structured cleanly in `~/CS345/<Lab-Name>/`:

```
CS345/
└── Essential-Linux-Commands/
    ├── screenshots/
    │   ├── q1.png
    │   ├── q2.png
    │   ├── q3.png
    │   └── q4.png
    ├── commands/
    │   ├── q1.txt
    │   ├── q2.txt
    │   ├── q3.txt
    │   └── q4.txt
    ├── submission/
    │   ├── q1.png
    │   ├── q2.png
    │   ├── q3.png
    │   ├── q4.png
    │   └── commands.txt      <-- Formatted summary ready for DOCX
    └── lab.json              <-- Structured metadata with exit codes & PWDs
```

---

## 🚫 100% Real Terminal Screenshots (No Fake Images)

- Every `.png` is an **actual hardware/compositor-rendered screen capture** of the real terminal window.
- **Persistent shell state**: `cd` changes, environment variables, and background processes persist across all questions.
- **Report-ready styling**: Deep dark background matching Konsole `MaterialYou` palette, crisp `Hack` typography, and high contrast for sharp insertion into **Microsoft Word / DOCX** lab reports.
- **Wayland & X11 Native**: Uses KDE **Spectacle** active-window capture with robust multi-tiered window activation.

---

## 🧪 Running Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

---

## 📄 License

MIT License. Built for CS345 Operating Systems and Linux coursework.
