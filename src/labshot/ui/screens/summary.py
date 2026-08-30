"""Lab Complete summary screen and submission packager."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Label, Static

from labshot.report import generate_completed_docx, convert_docx_to_pdf
from labshot.session import LabSession


class SummaryScreen(Screen):
    """Summary and submission completion screen."""

    BINDINGS = [
        ("o", "open_folder", "Open Folder"),
        ("g", "generate_report", "DOCX Report"),
        ("b", "back_to_lab", "Back"),
        ("q", "quit_app", "Quit"),
    ]

    def __init__(self, session: LabSession):
        super().__init__()
        self.session = session
        self.submission_dir: Optional[Path] = None
        self.docx_report: Optional[Path] = None
        self.pdf_report: Optional[Path] = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="home-container"):
            yield Static("L A B   C O M P L E T E", id="home-title")
            yield Static(f"Lab: {self.session.lab_name}", id="home-subtitle")

            with Vertical(classes="panel"):
                existing = self.session.storage.get_existing_question_numbers()
                count = len(existing)

                yield Label(f"Total Questions Captured: {count}", classes="status-success")
                yield Label(f"Screenshots Saved:        {count} verified PNGs", classes="status-success")
                yield Label(f"Desktop Submission:       {self.session.storage.lab_dir / 'submission'}")
                yield Label("", id="summary-docx-info")

            with Horizontal(classes="home-btn-row"):
                yield Button("Open Folder (O)", id="btn-open-folder", variant="primary")
                yield Button("Word Report (G)", id="btn-gen-report", variant="success")
                yield Button("Back to Lab (B)", id="btn-back-lab", variant="default")
                yield Button("Quit (Q)", id="btn-quit-summary", variant="error")

        yield Footer()

    def on_mount(self) -> None:
        # Export submission package on mount
        self.submission_dir = self.session.export()
        # Optionally populate docx
        self.docx_report = generate_completed_docx(storage=self.session.storage)
        if self.docx_report:
            self.pdf_report = convert_docx_to_pdf(self.docx_report)

        lbl = self.query_one("#summary-docx-info", Label)
        if self.docx_report and self.docx_report.exists():
            lbl.update(f"Word Report:             {self.docx_report.name} (Ready on Desktop)")
            lbl.set_classes("status-success")

    def action_open_folder(self) -> None:
        target = self.submission_dir or self.session.storage.lab_dir
        if target.exists() and shutil.which("xdg-open"):
            subprocess.Popen(["xdg-open", str(target)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def action_generate_report(self) -> None:
        self.docx_report = generate_completed_docx(storage=self.session.storage)
        if self.docx_report:
            self.pdf_report = convert_docx_to_pdf(self.docx_report)
            lbl = self.query_one("#summary-docx-info", Label)
            lbl.update(f"Word Report: {self.docx_report.name} (Updated on Desktop)")
            lbl.set_classes("status-success")

    def action_back_to_lab(self) -> None:
        self.app.pop_screen()

    def action_quit_app(self) -> None:
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-open-folder":
            self.action_open_folder()
        elif event.button.id == "btn-gen-report":
            self.action_generate_report()
        elif event.button.id == "btn-back-lab":
            self.action_back_to_lab()
        elif event.button.id == "btn-quit-summary":
            self.action_quit_app()
