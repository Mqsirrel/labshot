"""Minimal Keyboard Shortcuts help modal."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Label, Static


class HelpModal(ModalScreen):
    """Modal displaying full keyboard shortcut reference."""

    BINDINGS = [
        ("escape", "close_modal", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="modal-box"):
            yield Label("Keyboard Shortcuts", classes="modal-title")
            yield Static("Enter   Run command and capture screenshot", classes="modal-row")
            yield Static("; <cmd> Run setup / cd without screenshot", classes="modal-row")
            yield Static("N       Next question", classes="modal-row")
            yield Static("B       Previous question", classes="modal-row")
            yield Static("R       Retry current screenshot", classes="modal-row")
            yield Static("P       Preview evidence image", classes="modal-row")
            yield Static("S       Session status", classes="modal-row")
            yield Static("D       Finish lab & generate report", classes="modal-row")
            yield Static("Q       Quit", classes="modal-row")
            yield Static("Esc Close", classes="modal-actions")

    def action_close_modal(self) -> None:
        self.dismiss()
