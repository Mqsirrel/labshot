"""Minimal Home Screen for Labshot."""

from typing import List, Dict, Any, Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, Label, ListItem, ListView, Static, Input

from labshot.storage import LabStorage


class NewLabModal(ModalScreen[Optional[str]]):
    """Minimal modal to enter a new lab name."""

    def compose(self) -> ComposeResult:
        with Container(classes="modal-box"):
            yield Label("New lab", classes="modal-title")
            yield Input(placeholder="Lab name (e.g. Essential Linux Commands)", id="new-lab-input")
            yield Static("Enter Confirm · Esc Cancel", classes="modal-actions")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()
        self.dismiss(val or "Essential Linux Commands")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class HomeScreen(Screen):
    """Minimal home screen displaying recent labs and quick key shortcuts."""

    BINDINGS = [
        ("n", "new_lab", "New lab"),
        ("q", "quit_app", "Quit"),
        ("?", "show_help", "Help"),
    ]

    def __init__(self):
        super().__init__()
        self.recent_labs: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Container(id="home-box"):
            yield Static("labshot", id="home-title")
            yield Static("Recent labs", id="home-subtitle")
            yield ListView(id="labs-list-view")
            yield Static("n  New lab\nq  Quit\n↑↓ Select lab · Enter Open", classes="home-hints")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_recent_labs()

    def refresh_recent_labs(self) -> None:
        """Scan and display existing labs from Desktop CS345 folder."""
        self.recent_labs = LabStorage.list_all_labs()
        list_view = self.query_one("#labs-list-view", ListView)
        list_view.clear()

        if not self.recent_labs:
            list_view.append(ListItem(Label("  No recent labs found.")))
        else:
            for lab in self.recent_labs:
                name = lab["name"]
                count = lab["count"]
                # Format: "  Essential Linux Commands     4"
                list_view.append(ListItem(Label(f"  {name:<30} {count} questions")))

    def action_new_lab(self) -> None:
        def on_modal_result(lab_name: Optional[str]) -> None:
            if lab_name:
                self.app.start_lab_session(lab_name)

        self.app.push_screen(NewLabModal(), on_modal_result)

    def action_quit_app(self) -> None:
        self.app.exit()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self.recent_labs):
            chosen = self.recent_labs[idx]["name"]
            self.app.start_lab_session(chosen)
