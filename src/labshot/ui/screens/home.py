"""Home Screen displaying recent labs and quick actions."""

from typing import List, Dict, Any, Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen, ModalScreen
from textual.widgets import Button, Header, Footer, Label, ListItem, ListView, Static, Input

from labshot.storage import LabStorage


class NewLabModal(ModalScreen[Optional[str]]):
    """Modal to enter a new lab name."""

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog"):
            yield Label("Create New Lab", classes="modal-title")
            yield Label("Enter Lab Name (e.g. Essential Linux Commands):", classes="status-muted")
            yield Input(placeholder="Essential Linux Commands", id="new-lab-input")
            with Horizontal(classes="home-btn-row"):
                yield Button("Start Lab", id="btn-create-lab", variant="primary")
                yield Button("Cancel", id="btn-cancel-modal", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-create-lab":
            val = self.query_one("#new-lab-input", Input).value.strip()
            self.dismiss(val or "Essential Linux Commands")
        elif event.button.id == "btn-cancel-modal":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()
        self.dismiss(val or "Essential Linux Commands")


class HomeScreen(Screen):
    """Home Screen with Recent Labs overview and fast keyboard selection."""

    BINDINGS = [
        ("r", "resume_latest", "Resume"),
        ("n", "new_lab", "New Lab"),
        ("q", "quit_app", "Quit"),
        ("?", "show_help", "Help"),
    ]

    def __init__(self):
        super().__init__()
        self.recent_labs: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="home-container"):
            yield Static("L A B S H O T", id="home-title")
            yield Static("Real Linux Terminal Lab Evidence Recorder", id="home-subtitle")

            yield Label("Recent Labs:", classes="panel-title")
            yield ListView(id="labs-list-view")

            with Horizontal(classes="home-btn-row"):
                yield Button("Resume Lab (R)", id="btn-resume", variant="primary")
                yield Button("New Lab (N)", id="btn-new", variant="success")
                yield Button("Quit (Q)", id="btn-quit", variant="error")

        yield Footer()

    def on_mount(self) -> None:
        self.refresh_recent_labs()

    def refresh_recent_labs(self) -> None:
        """Scan and display existing labs from Desktop CS345 folder."""
        self.recent_labs = LabStorage.list_all_labs()
        list_view = self.query_one("#labs-list-view", ListView)
        list_view.clear()

        if not self.recent_labs:
            list_view.append(ListItem(Label("No existing labs found. Press [N] to create a new lab.")))
            btn_resume = self.query_one("#btn-resume", Button)
            btn_resume.disabled = True
        else:
            for lab in self.recent_labs:
                name = lab["name"]
                count = lab["count"]
                item_label = f"  ● {name:<36} ({count} questions)"
                list_view.append(ListItem(Label(item_label)))
            btn_resume = self.query_one("#btn-resume", Button)
            btn_resume.disabled = False

    def action_resume_latest(self) -> None:
        if self.recent_labs:
            latest = self.recent_labs[-1]["name"]
            self.app.start_lab_session(latest)
        else:
            self.action_new_lab()

    def action_new_lab(self) -> None:
        def on_modal_result(lab_name: Optional[str]) -> None:
            if lab_name:
                self.app.start_lab_session(lab_name)

        self.app.push_screen(NewLabModal(), on_modal_result)

    def action_quit_app(self) -> None:
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-resume":
            self.action_resume_latest()
        elif event.button.id == "btn-new":
            self.action_new_lab()
        elif event.button.id == "btn-quit":
            self.action_quit_app()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self.recent_labs):
            chosen = self.recent_labs[idx]["name"]
            self.app.start_lab_session(chosen)
