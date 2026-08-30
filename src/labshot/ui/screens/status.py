"""Minimal Lab Status Overview modal."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Label, Static

from labshot.session import LabSession


class StatusModal(ModalScreen):
    """Informational modal showing session metrics."""

    BINDINGS = [
        ("escape", "close_modal", "Close"),
    ]

    def __init__(self, session: LabSession):
        super().__init__()
        self.session = session

    def compose(self) -> ComposeResult:
        status = self.session.get_status()
        existing = status.get("completed_questions", [])
        total = len(existing)

        with Container(classes="modal-box"):
            yield Label(f"Lab Status: {status.get('lab')}", classes="modal-title")
            yield Static(f"Completed:  {total} questions", classes="modal-row")
            yield Static(f"Directory:  {status.get('current_cwd')}", classes="modal-row")
            yield Static(f"Terminal:   {status.get('terminal')}", classes="modal-row")
            yield Static(f"Backend:    {status.get('screenshot_backend')}", classes="modal-row")
            yield Static("Esc Close", classes="modal-actions")

    def action_close_modal(self) -> None:
        self.dismiss()
