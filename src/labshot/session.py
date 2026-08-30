"""Lab recording session orchestrator managing questions, commands, screenshots, and metadata."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from labshot.config import LabConfig, DEFAULT_CONFIG
from labshot.screenshot import ScreenshotManager
from labshot.shell import PersistentShellController, CommandResult
from labshot.storage import LabStorage, QuestionRecord


class LabSession:
    """Orchestrates the persistent shell, screenshot captures, and storage for a lab."""

    def __init__(
        self,
        lab_name: str,
        config: LabConfig = DEFAULT_CONFIG,
        preferred_term: Optional[str] = None,
        preferred_screenshot: Optional[str] = None,
    ):
        self.lab_name = lab_name
        self.config = config
        self.storage = LabStorage(lab_name=lab_name, base_dir=config.base_dir)
        self.screenshot_mgr = ScreenshotManager(preferred_backend=preferred_screenshot)
        self.shell = PersistentShellController(
            lab_name=lab_name,
            config=config,
            preferred_term=preferred_term,
        )
        self.current_q_num: int = 1
        self._is_active: bool = False

    def start(self) -> None:
        """Start the terminal window and shell, and determine the next question number."""
        self.shell.start()
        self._is_active = True
        self.current_q_num = self.storage.get_next_question_number()

    def is_active(self) -> bool:
        return self._is_active and self.shell.is_running

    def get_status(self) -> Dict[str, Any]:
        """Return current session status."""
        existing = self.storage.get_existing_question_numbers()
        meta = self.storage.load_metadata()
        return {
            "lab": self.lab_name,
            "lab_dir": str(self.storage.lab_dir),
            "next_question": self.current_q_num,
            "completed_questions": existing,
            "total_completed": len(existing),
            "current_cwd": self.shell.current_cwd,
            "terminal": self.shell.terminal_mgr.selected_term,
            "screenshot_backend": self.screenshot_mgr.get_backend_name(),
        }

    def list_questions(self) -> List[Dict[str, Any]]:
        """Return list of all recorded questions."""
        meta = self.storage.load_metadata()
        return meta.get("questions", [])

    def execute_command_only(self, command: str) -> CommandResult:
        """Execute a command in the persistent shell without capturing screenshot."""
        if not self.is_active():
            raise RuntimeError("Lab session is not active. Call start() first.")
        self.shell.activate_terminal_window()
        return self.shell.execute(command)

    def capture_evidence_only(
        self,
        question_number: int,
        command: str,
        cmd_result: CommandResult,
    ) -> QuestionRecord:
        """Capture screenshot and commit evidence for an already executed command."""
        shot_path = self.storage.get_screenshot_path(question_number)
        self.shell.activate_terminal_window()

        self.screenshot_mgr.capture(
            output_path=shot_path,
            delay_seconds=self.config.post_command_delay,
            terminal_mgr=self.shell.terminal_mgr,
        )

        record = self.storage.record_question(
            number=question_number,
            command=command,
            exit_code=cmd_result.exit_code,
            cwd_before=cmd_result.cwd_before,
            cwd_after=cmd_result.cwd_after,
        )

        if question_number >= self.current_q_num:
            self.current_q_num = question_number + 1

        return record

    def retry_screenshot_only(self, question_number: int) -> Path:
        """Re-capture screenshot for an existing question without re-running shell commands."""
        shot_path = self.storage.get_screenshot_path(question_number)
        self.shell.activate_terminal_window()

        self.screenshot_mgr.capture(
            output_path=shot_path,
            delay_seconds=self.config.post_command_delay,
            terminal_mgr=self.shell.terminal_mgr,
        )
        return shot_path

    def execute_question(self, command: str, question_number: Optional[int] = None) -> QuestionRecord:
        """Execute a lab question command, capture screenshot, and save metadata."""
        if not self.is_active():
            raise RuntimeError("Lab session is not active. Call start() first.")

        q_num = question_number if question_number is not None else self.current_q_num
        cmd_result = self.execute_command_only(command)
        return self.capture_evidence_only(question_number=q_num, command=command, cmd_result=cmd_result)

    def redo_question(self, question_number: int, command: str) -> QuestionRecord:
        """Re-take a previous question with a new command and replace evidence."""
        return self.execute_question(command=command, question_number=question_number)

    def export(self, target_dir: Optional[Path] = None) -> Path:
        """Export lab submission folder."""
        return self.storage.export_submission(target_dir=target_dir)

    def close(self) -> None:
        """Shut down the session and terminal."""
        self._is_active = False
        self.shell.close()
