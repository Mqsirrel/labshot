"""Sleek Evidence Card widget displaying execution state and actions."""

from pathlib import Path
from typing import Dict, Optional
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Label, Static


class EvidenceCard(Widget):
    """Evidence status box showing execution, screenshot capture and validation."""

    class ActionRequested(Message):
        """Emitted when an action button is clicked."""
        def __init__(self, action: str) -> None:
            self.action = action
            super().__init__()

    command_status: reactive[str] = reactive("idle")  # idle, running, success, error
    screenshot_status: reactive[str] = reactive("none")  # none, capturing, success, error
    validation_status: reactive[str] = reactive("none")  # none, success, error

    def __init__(self):
        super().__init__(id="evidence-container")

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("● Status: Ready for command", id="ev-status-line", classes="status-badge status-muted")
            yield Label("Screenshot will be captured automatically on Enter.", id="ev-detail-line", classes="status-muted")

        with Horizontal(id="actions-bar"):
            yield Button("Run Setup (No Snap)", id="btn-run-setup", variant="default", classes="-small")
            yield Button("Retry Shot (R)", id="btn-retry-shot", variant="warning", classes="-small")
            yield Button("Preview (P)", id="btn-preview-shot", variant="primary", classes="-small")
            yield Button("Next Q (N)", id="btn-next-q", variant="success", classes="-small")

    def on_mount(self) -> None:
        self._update_buttons_visibility()

    def set_running(self, command: str) -> None:
        """Update state when command starts executing."""
        self.command_status = "running"
        self.screenshot_status = "none"
        self.validation_status = "none"

        lbl_status = self.query_one("#ev-status-line", Label)
        lbl_status.update("⟳ Executing Linux command in real terminal...")
        lbl_status.set_classes("status-badge status-running")

        lbl_detail = self.query_one("#ev-detail-line", Label)
        lbl_detail.update(f"Running: {command}")
        self._update_buttons_visibility()

    def set_setup_success(self, cwd: str) -> None:
        """Update state when a setup/navigation command completes without taking a screenshot."""
        self.command_status = "success"
        self.screenshot_status = "none"

        lbl_status = self.query_one("#ev-status-line", Label)
        lbl_status.update("✓ Setup command executed (no screenshot taken)")
        lbl_status.set_classes("status-badge status-success")

        lbl_detail = self.query_one("#ev-detail-line", Label)
        lbl_detail.update(f"Current Path: {cwd}")
        self._update_buttons_visibility()

    def set_capturing(self) -> None:
        """Update state when screenshot capture begins."""
        self.command_status = "success"
        self.screenshot_status = "capturing"

        lbl_status = self.query_one("#ev-status-line", Label)
        lbl_status.update("⟳ Capturing terminal window...")
        lbl_status.set_classes("status-badge status-running")
        self._update_buttons_visibility()

    def set_success(self, shot_path: Path, exit_code: int = 0) -> None:
        """Update state when evidence is successfully committed and validated."""
        self.command_status = "success"
        self.screenshot_status = "success"
        self.validation_status = "success"

        lbl_status = self.query_one("#ev-status-line", Label)
        lbl_status.update(f"✓ Evidence Captured & Verified (Exit: {exit_code})")
        lbl_status.set_classes("status-badge status-success")

        lbl_detail = self.query_one("#ev-detail-line", Label)
        lbl_detail.update(f"Saved: {shot_path.name} → Desktop Submission Ready")
        self._update_buttons_visibility(has_evidence=True)

    def set_screenshot_error(self, error_msg: str) -> None:
        """Update state when command ran but screenshot capture failed."""
        self.command_status = "success"
        self.screenshot_status = "error"
        self.validation_status = "none"

        lbl_status = self.query_one("#ev-status-line", Label)
        lbl_status.update("✗ Screenshot capture failed (Command succeeded)")
        lbl_status.set_classes("status-badge status-error")

        lbl_detail = self.query_one("#ev-detail-line", Label)
        lbl_detail.update("Press [R] to retry screenshot without re-running the command.")
        self._update_buttons_visibility()

    def set_command_error(self, error_msg: str) -> None:
        """Update state when command execution fails."""
        self.command_status = "error"
        self.screenshot_status = "none"
        self.validation_status = "none"

        lbl_status = self.query_one("#ev-status-line", Label)
        lbl_status.update(f"✗ Command execution error")
        lbl_status.set_classes("status-badge status-error")

        lbl_detail = self.query_one("#ev-detail-line", Label)
        lbl_detail.update(str(error_msg))
        self._update_buttons_visibility()

    def set_existing_record(self, record: Dict) -> None:
        """Populate evidence box for an already completed question."""
        shot_name = Path(record.get("screenshot", "")).name
        exit_code = record.get("exit_code", 0)

        lbl_status = self.query_one("#ev-status-line", Label)
        lbl_status.update(f"✓ Completed (Exit: {exit_code}) → {shot_name}")
        lbl_status.set_classes("status-badge status-success")

        lbl_detail = self.query_one("#ev-detail-line", Label)
        lbl_detail.update(f"Command: {record.get('command', '')}")
        self._update_buttons_visibility(has_evidence=True)

    def reset_for_new_question(self, q_num: int) -> None:
        """Reset state for a brand new question."""
        self.command_status = "idle"
        self.screenshot_status = "none"
        self.validation_status = "none"

        lbl_status = self.query_one("#ev-status-line", Label)
        lbl_status.update(f"● Question {q_num}: Ready for command")
        lbl_status.set_classes("status-badge status-muted")

        lbl_detail = self.query_one("#ev-detail-line", Label)
        lbl_detail.update("Screenshot will be captured automatically on Enter.")
        self._update_buttons_visibility(has_evidence=False)

    def _update_buttons_visibility(self, has_evidence: bool = False) -> None:
        """Show or hide action buttons based on status."""
        try:
            btn_retry = self.query_one("#btn-retry-shot", Button)
            btn_prev = self.query_one("#btn-preview-shot", Button)
            btn_next = self.query_one("#btn-next-q", Button)

            can_preview = (self.screenshot_status == "success" or has_evidence)
            btn_prev.display = can_preview
            btn_retry.display = (self.screenshot_status == "error" or can_preview)
            btn_next.display = can_preview
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-retry-shot":
            self.post_message(self.ActionRequested("retry"))
        elif event.button.id == "btn-preview-shot":
            self.post_message(self.ActionRequested("preview"))
        elif event.button.id == "btn-next-q":
            self.post_message(self.ActionRequested("next"))
        elif event.button.id == "btn-run-setup":
            self.post_message(self.ActionRequested("setup"))
