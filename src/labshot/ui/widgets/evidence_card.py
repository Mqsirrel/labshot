"""Compact inline evidence status widget."""

from pathlib import Path
from typing import Dict, Optional
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class EvidenceCard(Widget):
    """Minimal inline status line showing command and evidence state."""

    command_status: reactive[str] = reactive("idle")
    screenshot_status: reactive[str] = reactive("none")
    validation_status: reactive[str] = reactive("none")

    def __init__(self):
        super().__init__(id="evidence-status-line")

    def compose(self) -> ComposeResult:
        yield Static("Ready for command", id="ev-line", classes="status-text-muted")

    def set_running(self, command: str) -> None:
        self.command_status = "running"
        self.screenshot_status = "none"
        self.validation_status = "none"

        line = self.query_one("#ev-line", Static)
        line.update(f"⟳ executing {command}...")
        line.set_classes("status-text-running")

    def set_setup_success(self, cwd: str) -> None:
        self.command_status = "success"
        self.screenshot_status = "none"

        line = self.query_one("#ev-line", Static)
        line.update(f"✓ executed (setup) · path: {cwd}")
        line.set_classes("status-text-success")

    def set_capturing(self) -> None:
        self.command_status = "success"
        self.screenshot_status = "capturing"

        line = self.query_one("#ev-line", Static)
        line.update("✓ executed · ⟳ capturing...")
        line.set_classes("status-text-running")

    def set_success(self, shot_path: Path, exit_code: int = 0) -> None:
        self.command_status = "success"
        self.screenshot_status = "success"
        self.validation_status = "success"

        line = self.query_one("#ev-line", Static)
        line.update(f"✓ executed (exit {exit_code}) · ✓ captured ({shot_path.name}) · ✓ verified")
        line.set_classes("status-text-success")

    def set_screenshot_error(self, error_msg: str) -> None:
        self.command_status = "success"
        self.screenshot_status = "error"
        self.validation_status = "none"

        line = self.query_one("#ev-line", Static)
        line.update("✗ Screenshot failed\nCommand execution succeeded. Evidence was not committed.\nR Retry screenshot · S Skip")
        line.set_classes("status-text-error")

    def set_command_error(self, error_msg: str) -> None:
        self.command_status = "error"
        self.screenshot_status = "none"
        self.validation_status = "none"

        line = self.query_one("#ev-line", Static)
        line.update(f"✗ Command failed: {error_msg}")
        line.set_classes("status-text-error")

    def set_existing_record(self, record: Dict) -> None:
        shot_name = Path(record.get("screenshot", "")).name
        exit_code = record.get("exit_code", 0)

        line = self.query_one("#ev-line", Static)
        line.update(f"✓ executed (exit {exit_code}) · ✓ captured ({shot_name}) · ✓ verified")
        line.set_classes("status-text-success")

    def reset_for_new_question(self, q_num: int) -> None:
        self.command_status = "idle"
        self.screenshot_status = "none"
        self.validation_status = "none"

        line = self.query_one("#ev-line", Static)
        line.update("Ready for command")
        line.set_classes("status-text-muted")
