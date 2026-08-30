"""Theme constants, semantic color palette and CSS stylesheets for Labshot TUI."""

APP_CSS = """
/* =============================================================================
   Labshot TUI — Modern, Restrained Developer Terminal Style
   ============================================================================= */

Screen {
    background: #1a1b26;
    color: #c0caf5;
}

/* Header & Footer */
Header {
    background: #16161e;
    color: #7aa2f7;
    height: 1;
    dock: top;
}

Footer {
    background: #16161e;
    color: #a9b1d6;
    height: 1;
    dock: bottom;
}

/* Common Container Styles */
.panel {
    background: #1f2335;
    border: solid #3b4261;
    padding: 1 2;
    margin: 0 1;
}

.panel-title {
    color: #7aa2f7;
    text-style: bold;
    margin-bottom: 1;
}

/* Home Screen */
#home-container {
    align: center middle;
    width: 78;
    height: auto;
    max-height: 90%;
    border: heavy #7aa2f7;
    background: #1f2335;
    padding: 1 3;
}

#home-title {
    text-align: center;
    color: #7aa2f7;
    text-style: bold;
    margin-bottom: 1;
}

#home-subtitle {
    text-align: center;
    color: #565f89;
    margin-bottom: 1;
}

#labs-list-view {
    height: auto;
    max-height: 10;
    border: round #3b4261;
    margin-bottom: 1;
    background: #16161e;
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
    width: 32;
    height: 100%;
    border-right: solid #3b4261;
    background: #16161e;
    padding: 1;
}

#right-pane {
    width: 1fr;
    height: 100%;
    padding: 1 2;
    background: #1a1b26;
}

/* Question List */
#question-list-scroll {
    height: 1fr;
}

.q-item {
    padding: 0 1;
    margin: 0;
    color: #a9b1d6;
}

.q-item-active {
    color: #73daca;
    text-style: bold;
    background: #24283b;
}

.q-item-done {
    color: #9ece6a;
}

/* Right Pane - Question Detail Box */
#q-detail-box {
    background: #1f2335;
    border: round #414868;
    padding: 1 2;
    margin-bottom: 1;
    height: auto;
    min-height: 5;
}

#q-number-heading {
    color: #7dcfff;
    text-style: bold;
}

#q-text {
    color: #c0caf5;
    margin-top: 1;
}

/* Command Prompt Input Area */
#prompt-box {
    background: #16161e;
    border: round #7aa2f7;
    padding: 1;
    margin-bottom: 1;
    height: auto;
}

#prompt-label {
    color: #e0af68;
    text-style: bold;
}

#cmd-input {
    background: #1f2335;
    color: #c0caf5;
    border: none;
    padding: 0 1;
    margin-top: 1;
}

#cmd-input:focus {
    border: none;
    background: #24283b;
}

/* Evidence Card Box */
#evidence-box {
    background: #1f2335;
    border: round #3b4261;
    padding: 1 2;
    height: auto;
    min-height: 6;
}

.status-line {
    margin: 0 0;
}

.status-success {
    color: #9ece6a;
    text-style: bold;
}

.status-running {
    color: #e0af68;
    text-style: bold;
}

.status-error {
    color: #f7768e;
    text-style: bold;
}

.status-muted {
    color: #565f89;
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
    width: 60;
    height: auto;
    border: heavy #7aa2f7;
    background: #1f2335;
    padding: 1 2;
}

.modal-title {
    text-align: center;
    color: #7aa2f7;
    text-style: bold;
    margin-bottom: 1;
}

/* Button Variants */
Button.-primary {
    background: #7aa2f7;
    color: #15161e;
}

Button.-success {
    background: #9ece6a;
    color: #15161e;
}

Button.-error {
    background: #f7768e;
    color: #15161e;
}
"""
