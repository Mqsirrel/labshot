"""Evidence Card widget displaying execution and screenshot verification state."""

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
    detail_message: reactive[str] = reactive("")

    def __init__(self):
        super().__init__(id="evidence-box")

    def compose(self) -> ComposeResult:
        yield Label("Evidence", classes="panel-title")
        with Vertical(id="evidence-status-container"):
            yield Static("○ Ready for command", id="ev-line-1", classes="status-line status-muted")
            yield Static("○ Screenshot pending", id="ev-line-2", classes="status-line status-muted")
            yield Static("○ Validation pending", id="ev-line-3", classes="status-line status-muted")
        yield Label("", id="ev-detail-label", classes="status-line")

        with Horizontal(id="actions-bar"):
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
        self.detail_message = f"Executing: {command}"

        self.query_one("#ev-line-1", Static).update("⟳ Executing Linux command in real terminal...")
        self.query_one("#ev-line-1", Static).set_classes("status-line status-running")

        self.query_one("#ev-line-2", Static).update("○ Waiting for command completion...")
        self.query_one("#ev-line-2", Static).set_classes("status-line status-muted")

        self.query_one("#ev-line-3", Static).update("○ Validation pending")
        self.query_one("#ev-line-3", Static).set_classes("status-line status-muted")
        self._update_buttons_visibility()

    def set_capturing(self) -> None:
        """Update state when screenshot capture begins."""
        self.command_status = "success"
        self.screenshot_status = "capturing"

        self.query_one("#ev-line-1", Static).update("✓ Command executed successfully")
        self.query_one("#ev-line-1", Static).set_classes("status-line status-success")

        self.query_one("#ev-line-2", Static).update("⟳ Capturing real terminal window...")
        self.query_one("#ev-line-2", Static).set_classes("status-line status-running")
        self._update_buttons_visibility()

    def set_success(self, shot_path: Path, exit_code: int = 0) -> None:
        """Update state when evidence is successfully committed and validated."""
        self.command_status = "success"
        self.screenshot_status = "success"
        self.validation_status = "success"

        self.query_one("#ev-line-1", Static).update(f"✓ Command executed (Exit: {exit_code})")
        self.query_one("#ev-line-1", Static).set_classes("status-line status-success")

        self.query_one("#ev-line-2", Static).update(f"✓ Screenshot captured → {shot_path.name}")
        self.query_one("#ev-line-2", Static).set_classes("status-line status-success")

        self.query_one("#ev-line-3", Static).update(f"✓ Evidence verified and committed")
        self.query_one("#ev-line-3", Static).set_classes("status-line status-success")
        self._update_buttons_visibility()

    def set_screenshot_error(self, error_msg: str) -> None:
        """Update state when command ran but screenshot capture failed."""
        self.command_status = "success"
        self.screenshot_status = "error"
        self.validation_status = "none"

        self.query_one("#ev-line-1", Static).update("✓ Command executed successfully")
        self.query_one("#ev-line-1", Static).set_classes("status-line status-success")

        self.query_one("#ev-line-2", Static).update("✗ Screenshot capture failed")
        self.query_one("#ev-line-2", Static).set_classes("status-line status-error")

        self.query_one("#ev-line-3", Static).update("⚠️ Evidence was NOT committed. Press [R] to retry screenshot.")
        self.query_one("#ev-line-3", Static).set_classes("status-line status-error")
        self._update_buttons_visibility()

    def set_command_error(self, error_msg: str) -> None:
        """Update state when command execution fails."""
        self.command_status = "error"
        self.screenshot_status = "none"
        self.validation_status = "none"

        self.query_one("#ev-line-1", Static).update(f"✗ Command failed: {error_msg}")
        self.query_one("#ev-line-1", Static).set_classes("status-line status-error")
        self._update_buttons_visibility()

    def set_existing_record(self, record: Dict) -> None:
        """Populate evidence box for an already completed question."""
        shot_name = Path(record.get("screenshot", "")).name
        exit_code = record.get("exit_code", 0)

        self.query_one("#ev-line-1", Static).update(f"✓ Command: {record.get('command', '')} (Exit: {exit_code})")
        self.query_one("#ev-line-1", Static).set_classes("status-line status-success")

        self.query_one("#ev-line-2", Static).update(f"✓ Screenshot: {shot_name}")
        self.query_one("#ev-line-2", Static).set_classes("status-line status-success")

        self.query_one("#ev-line-3", Static).update(f"✓ Verified PNG on Desktop")
        self.query_one("#ev-line-3", Static).set_classes("status-line status-success")
        self._update_buttons_visibility(has_evidence=True)

    def reset_for_new_question(self, q_num: int) -> None:
        """Reset state for a brand new question."""
        self.command_status = "idle"
        self.screenshot_status = "none"
        self.validation_status = "none"

        self.query_one("#ev-line-1", Static).update(f"○ Ready to execute Question {q_num}")
        self.query_one("#ev-line-1", Static).set_classes("status-line status-muted")

        self.query_one("#ev-line-2", Static).update("○ Screenshot pending")
        self.query_one("#ev-line-2", Static).set_classes("status-line status-muted")

        self.query_one("#ev-line-3", Static).update("○ Validation pending")
        self.query_one("#ev-line-3", Static).set_classes("status-line status-muted")
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
