"""Theme constants, semantic color palette and sleek CSS stylesheets for Labshot TUI."""

APP_CSS = """
/* =============================================================================
   Labshot TUI — Ultra-Clean, Modern Developer Workspace
   ============================================================================= */

Screen {
    background: #181926;
    color: #cad3f5;
}

/* Header & Footer */
Header {
    background: #1e2030;
    color: #8aadf4;
    height: 1;
    dock: top;
}

Footer {
    background: #1e2030;
    color: #a5adcb;
    height: 1;
    dock: bottom;
}

/* Home Screen */
#home-container {
    align: center middle;
    width: 72;
    height: auto;
    max-height: 85%;
    border: round #8aadf4;
    background: #1e2030;
    padding: 1 3;
}

#home-title {
    text-align: center;
    color: #8aadf4;
    text-style: bold;
    margin-bottom: 0;
}

#home-subtitle {
    text-align: center;
    color: #6e738d;
    margin-bottom: 1;
}

#labs-list-view {
    height: auto;
    max-height: 8;
    border: solid #363a4f;
    margin-bottom: 1;
    background: #181926;
}

.home-btn-row {
    layout: horizontal;
    align: center middle;
    height: auto;
    margin-top: 1;
}

.home-btn-row Button {
    margin: 0 1;
}

/* Main Lab Two-Pane Layout */
#lab-layout {
    layout: horizontal;
    height: 1fr;
}

#left-pane {
    width: 28;
    height: 100%;
    border-right: solid #363a4f;
    background: #181926;
    padding: 1;
}

#right-pane {
    width: 1fr;
    height: 100%;
    padding: 1 2;
    background: #1e2030;
}

/* Question List */
#question-list-scroll {
    height: 1fr;
}

.q-item {
    padding: 0 1;
    margin: 0 0 1 0;
    color: #a5adcb;
}

.q-item-active {
    color: #8aadf4;
    text-style: bold;
    background: #24273a;
    border-left: thick #8aadf4;
}

.q-item-done {
    color: #a6da95;
}

/* Right Pane - Question Workspace */
#q-workspace {
    height: 1fr;
}

#q-meta-bar {
    layout: horizontal;
    height: auto;
    margin-bottom: 1;
    align: left middle;
}

#q-badge {
    background: #8aadf4;
    color: #181926;
    text-style: bold;
    padding: 0 1;
    margin-right: 2;
}

#q-pwd-label {
    color: #eed49f;
    text-style: bold;
}

/* Command Prompt Input Area */
#prompt-container {
    background: #181926;
    border: round #8aadf4;
    padding: 1 2;
    margin-bottom: 1;
    height: auto;
}

#prompt-label {
    color: #eed49f;
    text-style: bold;
}

#cmd-input {
    background: #24273a;
    color: #cad3f5;
    border: none;
    padding: 0 1;
    margin-top: 1;
}

#cmd-input:focus {
    border: none;
    background: #282c44;
}

#cmd-tip-label {
    color: #6e738d;
    margin-top: 1;
}

/* Evidence Status Card */
#evidence-container {
    background: #181926;
    border: round #363a4f;
    padding: 1 2;
    height: auto;
    min-height: 4;
}

.status-badge {
    text-style: bold;
}

.status-success {
    color: #a6da95;
}

.status-running {
    color: #eed49f;
}

.status-error {
    color: #ed8796;
}

.status-muted {
    color: #6e738d;
}

/* Action Buttons Bar */
#actions-bar {
    layout: horizontal;
    height: auto;
    margin-top: 1;
    align: left middle;
}

#actions-bar Button {
    margin-right: 1;
}

/* Modals & Dialogs */
ModalScreen {
    align: center middle;
}

.modal-dialog {
    width: 64;
    height: auto;
    border: round #8aadf4;
    background: #1e2030;
    padding: 1 2;
}

.modal-title {
    text-align: center;
    color: #8aadf4;
    text-style: bold;
    margin-bottom: 1;
}

/* Button Variants */
Button.-primary {
    background: #8aadf4;
    color: #181926;
}

Button.-success {
    background: #a6da95;
    color: #181926;
}

Button.-warning {
    background: #eed49f;
    color: #181926;
}

Button.-error {
    background: #ed8796;
    color: #181926;
}
"""
