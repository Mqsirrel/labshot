# labshot 📸⚡

> **Terminal lab evidence capture tool for Linux university labs**

`labshot` is a minimal, keyboard-first terminal tool designed for university coursework (e.g. CS345 Operating Systems / Linux Labs). It lets you answer questions by executing commands in a persistent shell running inside an authentic terminal window (Konsole / Alacritty) and automatically captures pixel-perfect native screenshots of the terminal window after each question.

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

- **Independent Core**: `shell`, `execution`, `screenshot`, `validation`, `storage` are completely decoupled from UI code.
- **TUI & CLI**: Textual TUI is the default interface; direct CLI REPL is available with `labshot --cli`.

---

## 🚀 Quickstart

### Launch the TUI (Default)

```bash
labshot
```

### Launch Classic CLI REPL

```bash
labshot --cli
```

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
| :--- | :--- |
| **`Enter`** | Run command & capture official screenshot for current question |
| **`; <cmd>`** | Run setup / navigation command (e.g. `; cd ..`) without screenshot |
| **`↑` / `↓`** | Navigate questions list |
| **`N`** | Next question |
| **`B`** | Previous question |
| **`R`** | Retry current screenshot (without re-running commands) |
| **`P`** | Preview evidence metadata & open image in viewer |
| **`S`** | Session status overview |
| **`D`** | Finish lab & generate DOCX report |
| **`?`** | Help modal |
| **`Q`** | Quit |

---

## 📂 Desktop Output & Word Report

All screenshots and submission files are saved to your Desktop:

```
~/Desktop/CS345/<Lab-Name>/
├── screenshots/
│   ├── q1.png
│   ├── q2.png
│   └── ...
└── submission/
    ├── q1.png
    ├── q2.png
    └── commands.txt
```

If `CS345_Linux_Lab_Template.docx` is present on Desktop, Labshot automatically fills command answers, embeds screenshots, and exports `<Lab-Name>_Completed.docx` and `<Lab-Name>_Completed.pdf`.

---

## 🛠️ CLI Commands

- `labshot --cli` — Classic direct terminal REPL
- `labshot export [lab]` — Export submission folder
- `labshot report [lab]` — Populate Word and PDF report
- `labshot list [lab]` — List recorded questions and exit codes
- `labshot status [lab]` — Display lab metrics
- `labshot redo <N> [cmd]` — Re-take Question N
- `labshot --version` — Display version information
