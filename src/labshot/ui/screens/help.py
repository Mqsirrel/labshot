"""Keyboard shortcuts help overlay."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class HelpModal(ModalScreen):
    """Modal displaying full keyboard shortcut reference."""

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog"):
            yield Label("Keyboard Shortcuts", classes="modal-title")
            with Vertical():
                yield Label("  Enter       Execute Linux command & capture")
                yield Label("  ↑ / ↓       Navigate questions")
                yield Label("  N           Next question")
                yield Label("  B           Previous question")
                yield Label("  R           Retry / Redo current screenshot")
                yield Label("  P           Preview evidence in viewer")
                yield Label("  S           Show lab status overview")
                yield Label("  D           Finish lab & package submission")
                yield Label("  ?           Show this help modal")
                yield Label("  Q           Quit / Exit to Home")

            with Horizontal(classes="home-btn-row"):
                yield Button("Close", id="btn-close-help", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()
