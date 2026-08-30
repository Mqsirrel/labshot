"""Centralized semantic theme and minimal stylesheet for Labshot TUI.

Target aesthetic: Minimalist developer tool (lazygit / k9s / btop / neovim).
"""

APP_CSS = """
/* Global Screen */
Screen {
    background: #181825;
    color: #cdd6f4;
    align: center middle;
}

/* Header & Footer */
Header {
    background: #11111b;
    color: #89b4fa;
    height: 1;
    dock: top;
}

Footer {
    background: #11111b;
    color: #a6adc8;
    height: 1;
    dock: bottom;
}

/* Home Screen */
#home-box {
    width: 60;
    height: auto;
    max-height: 80%;
    padding: 1 2;
    border: solid #45475a;
    background: #1e1e2e;
}

#home-title {
    text-style: bold;
    color: #89b4fa;
    margin-bottom: 1;
}

#home-subtitle {
    color: #6c7086;
    margin-bottom: 1;
}

#labs-list-view {
    height: auto;
    max-height: 8;
    background: #181825;
    border: solid #313244;
    margin-bottom: 1;
}

.home-hints {
    color: #6c7086;
    margin-top: 1;
}

/* Main Lab Two-Pane Layout */
#lab-layout {
    layout: horizontal;
    height: 1fr;
    width: 100%;
}

#left-pane {
    width: 24;
    height: 100%;
    border-right: solid #313244;
    background: #181825;
    padding: 0 1;
}

#right-pane {
    width: 1fr;
    height: 100%;
    padding: 1 2;
    background: #1e1e2e;
}

/* Left Pane Question List */
#question-list-scroll {
    height: 1fr;
}

.q-item {
    padding: 0 0;
    color: #a6adc8;
    height: 1;
}

.q-item-active {
    color: #89b4fa;
    text-style: bold;
}

.q-item-done {
    color: #a6e3a1;
}

/* Right Pane - Question Workspace */
#q-header-line {
    layout: horizontal;
    height: 1;
    margin-bottom: 1;
}

#q-title-label {
    text-style: bold;
    color: #cdd6f4;
    width: 1fr;
}

#q-progress-label {
    color: #6c7086;
    text-align: right;
    width: 16;
}

#q-pwd-line {
    color: #f9e2af;
    margin-bottom: 1;
}

/* Command Prompt Input */
#prompt-row {
    layout: horizontal;
    height: 3;
    margin-bottom: 1;
    background: #181825;
    border: solid #45475a;
    padding: 0 1;
}

#prompt-symbol {
    width: 3;
    color: #89b4fa;
    text-style: bold;
    padding-top: 1;
}

#cmd-input {
    width: 1fr;
    height: 1;
    background: #181825;
    color: #cdd6f4;
    border: none;
    padding: 0;
    margin-top: 1;
}

#cmd-input:focus {
    border: none;
    background: #181825;
}

/* Evidence Inline Status */
#evidence-status-line {
    height: auto;
    margin-top: 1;
}

.status-text-muted {
    color: #6c7086;
}

.status-text-running {
    color: #f9e2af;
}

.status-text-success {
    color: #a6e3a1;
}

.status-text-error {
    color: #f38ba8;
}

/* Compact Modal Screens */
ModalScreen {
    align: center middle;
}

.modal-box {
    width: 56;
    height: auto;
    border: solid #45475a;
    background: #1e1e2e;
    padding: 1 2;
}

.modal-title {
    text-style: bold;
    color: #89b4fa;
    margin-bottom: 1;
}

.modal-row {
    margin: 0 0;
    color: #cdd6f4;
}

.modal-actions {
    color: #6c7086;
    margin-top: 1;
}
"""
