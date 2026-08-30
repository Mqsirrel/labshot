# labshot 📸⚡

> **Terminal Lab Screenshot Recorder & Evidence Workspace for Linux University Coursework**

`labshot` is a keyboard-first Textual TUI and CLI developer tool designed for university students (e.g. CS345 Operating Systems / Linux Labs). It lets you answer lab questions by executing commands in a **persistent Linux shell** running inside a terminal window (Konsole / Alacritty) and automatically captures terminal output as PNG images after every question.

---

## 🏗️ Architecture

```
                 Labshot (`bin/labshot`)
                            │
                     ┌──────┴──────┐
                     │             │
                    TUI           CLI
             (`labshot.ui`)   (`labshot.cli`)
                     │             │
                     └──────┬──────┘
                            │
                      Core Engine
              (`labshot.session`, `storage`,
               `shell`, `screenshot`, `report`)
                            │
               ┌────────────┼────────────┐
               │            │            │
            Shell        Capture      Storage
        (PTY / Bash)  (Spectacle/PNG) (JSON/Files)
               │            │            │
            Konsole     Auto-Trim      Desktop
```

---

## 🚀 Quickstart

### Launch the TUI (Default)

```bash
labshot
```

### Launch Classic Direct CLI REPL

```bash
labshot --cli
```

*(or `labshot -c`)*

---

## ⌨️ TUI Keyboard Shortcuts

| Key | Action |
| :--- | :--- |
| **`Enter`** | Execute Linux command in live terminal & capture evidence |
| **`↑` / `↓`** | Navigate through questions list |
| **`N`** | Next question |
| **`B`** | Previous question |
| **`R`** | Retry / Redo screenshot capture |
| **`P`** | Preview evidence & inspect image resolution in system viewer |
| **`S`** | Show Lab Status overview modal |
| **`D`** | Finish lab & package submission |
| **`?`** | Show keyboard help modal |
| **`Q`** | Quit / Exit to Home |

---

## 📂 Desktop Output & Auto-Fill Word Report

All screenshots and submission packages are automatically organized on your Desktop:

```
~/Desktop/CS345/<Lab-Name>/
├── screenshots/
│   ├── q1.png
│   ├── q2.png
│   └── ...
└── submission/
    ├── q1.png
    ├── q2.png
    ├── ...
    └── commands.txt
```

### Optional DOCX & PDF Auto-Fill:
If `CS345_Linux_Lab_Template.docx` is present on your Desktop, `labshot` automatically:
1. Fills your executed commands into the `$ ` answer box.
2. Embeds the high-resolution PNG screenshots into `(Paste here)`.
3. Exports both `~/Desktop/<Lab-Name>_Completed.docx` and `~/Desktop/<Lab-Name>_Completed.pdf` ready for immediate submission!

---

## 🛠️ CLI Subcommands

- `labshot export [lab]` — Export submission package
- `labshot report [lab]` — Populate Word (.docx) and PDF report
- `labshot list [lab]` — List recorded questions and exit codes
- `labshot status [lab]` — Display lab metrics
- `labshot redo <N> [cmd]` — Re-take Question N
- `labshot --version` — Display version information
