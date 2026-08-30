"""Lab Status informational modal."""

from typing import Dict, Any
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from labshot.session import LabSession


class StatusModal(ModalScreen):
    """Informational modal showing session metrics."""

    def __init__(self, session: LabSession):
        super().__init__()
        self.session = session

    def compose(self) -> ComposeResult:
        status = self.session.get_status()
        existing = status.get("completed_questions", [])
        total = len(existing)

        with Container(classes="modal-dialog"):
            yield Label("Lab Status Overview", classes="modal-title")
            with Vertical():
                yield Label(f"Lab:             {status.get('lab')}")
                yield Label(f"Output:          {status.get('lab_dir')}")
                yield Label(f"Completed:       {total} questions")
                yield Label(f"Screenshots:     {total} verified PNGs", classes="status-success")
                yield Label(f"Current Dir:     {status.get('current_cwd')}")
                yield Label(f"Terminal:        {status.get('terminal')}")
                yield Label(f"Backend:         {status.get('screenshot_backend')}")

            with Horizontal(classes="home-btn-row"):
                yield Button("Close (Esc)", id="btn-close-status", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()
