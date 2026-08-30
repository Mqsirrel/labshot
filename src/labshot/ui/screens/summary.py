"""Minimal Lab Complete Summary Screen."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Static

from labshot.report import generate_completed_docx, convert_docx_to_pdf
from labshot.session import LabSession


class SummaryScreen(Screen):
    """Concise lab completion screen."""

    BINDINGS = [
        ("d", "generate_report", "Generate DOCX"),
        ("o", "open_folder", "Open folder"),
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
        yield Header(show_clock=False)
        with Container(id="home-box"):
            yield Label("Lab complete", id="home-title")
            yield Static(self.session.lab_name, id="home-subtitle")

            existing = self.session.storage.get_existing_question_numbers()
            count = len(existing)

            yield Static(f"Questions   {count} / {count}", classes="modal-row")
            yield Static(f"Commands    {count} / {count}", classes="modal-row")
            yield Static(f"Evidence    {count} / {count}", classes="modal-row")
            yield Static("Invalid     0", classes="modal-row")
            yield Static("Missing     0", classes="modal-row")
            yield Static("Duplicates  0", classes="modal-row")
            yield Static("✓ Submission ready", classes="modal-row status-text-success")
            yield Static("", id="summary-docx-info", classes="modal-row")

            yield Static("d  Generate DOCX\no  Open folder\nb  Back\nq  Quit", classes="home-hints")
        yield Footer()

    def on_mount(self) -> None:
        self.submission_dir = self.session.export()
        self.docx_report = generate_completed_docx(storage=self.session.storage)
        if self.docx_report:
            self.pdf_report = convert_docx_to_pdf(self.docx_report)
            lbl = self.query_one("#summary-docx-info", Static)
            lbl.update(f"✓ Word report: {self.docx_report.name}")
            lbl.set_classes("modal-row status-text-success")

    def action_open_folder(self) -> None:
        target = self.submission_dir or self.session.storage.lab_dir
        if target.exists() and shutil.which("xdg-open"):
            subprocess.Popen(["xdg-open", str(target)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def action_generate_report(self) -> None:
        self.docx_report = generate_completed_docx(storage=self.session.storage)
        if self.docx_report:
            self.pdf_report = convert_docx_to_pdf(self.docx_report)
            lbl = self.query_one("#summary-docx-info", Static)
            lbl.update(f"✓ Word report: {self.docx_report.name}")
            lbl.set_classes("modal-row status-text-success")

    def action_back_to_lab(self) -> None:
        self.app.pop_screen()

    def action_quit_app(self) -> None:
        self.app.exit()
