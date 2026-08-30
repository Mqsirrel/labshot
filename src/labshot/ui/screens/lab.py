"""Main Lab Workspace Screen with real-time evidence lifecycle."""

import asyncio
from pathlib import Path
from typing import Dict, Optional, Set
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Static, Button

from labshot.session import LabSession
from labshot.ui.screens.help import HelpModal
from labshot.ui.screens.preview import PreviewModal
from labshot.ui.screens.status import StatusModal
from labshot.ui.screens.summary import SummaryScreen
from labshot.ui.widgets.command_prompt import CommandPrompt
from labshot.ui.widgets.evidence_card import EvidenceCard
from labshot.ui.widgets.question_list import QuestionList


class LabScreen(Screen):
    """Main two-pane interactive lab screen."""

    BINDINGS = [
        ("r", "action_retry", "Retry"),
        ("n", "action_next", "Next Q"),
        ("b", "action_prev", "Prev Q"),
        ("p", "action_preview", "Preview"),
        ("s", "action_status", "Status"),
        ("d", "action_finish", "Finish"),
        ("?", "action_help", "Help"),
        ("q", "action_quit", "Quit"),
    ]

    def __init__(self, session: LabSession):
        super().__init__()
        self.session = session
        self.active_q: int = session.current_q_num
        self.is_executing: bool = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="lab-layout"):
            # Left pane: Question sequence
            with Vertical(id="left-pane"):
                yield QuestionList(
                    current_q=self.active_q,
                    completed_qs=set(self.session.storage.get_existing_question_numbers()),
                )

            # Right pane: Active Question, Command Input, Evidence Lifecycle
            with Vertical(id="right-pane"):
                with Vertical(id="q-detail-box"):
                    yield Label(f"Question {self.active_q}", id="q-number-heading")
                    yield Label("Enter the Linux command to answer this question and capture evidence.", id="q-text")

                yield CommandPrompt()
                yield EvidenceCard()

        yield Footer()

    def on_mount(self) -> None:
        self.sync_ui_to_current_question()

    def sync_ui_to_current_question(self) -> None:
        """Update headings, evidence card, and question list to active question."""
        completed_set = set(self.session.storage.get_existing_question_numbers())
        self.query_one(QuestionList).update_state(
            current_q=self.active_q,
            completed_qs=completed_set,
        )

        heading = self.query_one("#q-number-heading", Label)
        heading.update(f"Question {self.active_q}")

        ev_card = self.query_one(EvidenceCard)
        meta = self.session.storage.load_metadata()
        q_record = next((q for q in meta.get("questions", []) if q.get("number") == self.active_q), None)

        if q_record:
            ev_card.set_existing_record(q_record)
        else:
            ev_card.reset_for_new_question(self.active_q)

        # Focus prompt
        self.query_one(CommandPrompt).focus_input()

    def on_command_prompt_submitted(self, event: CommandPrompt.Submitted) -> None:
        """Handle command submission asynchronously without blocking UI."""
        if self.is_executing:
            return

        cmd = event.command.strip()
        if not cmd:
            return

        self.is_executing = True
        ev_card = self.query_one(EvidenceCard)
        ev_card.set_running(cmd)

        self.run_worker(self._async_execute_and_capture(cmd), exclusive=True)

    async def _async_execute_and_capture(self, command: str) -> None:
        """Execute command in worker thread, then capture and validate evidence."""
        ev_card = self.query_one(EvidenceCard)
        target_q = self.active_q

        try:
            # 1. Execute command in real PTY shell
            cmd_result = await asyncio.to_thread(self.session.execute_command_only, command)

            # 2. Update UI to capturing state
            ev_card.set_capturing()

            # 3. Capture real terminal window screenshot
            record = await asyncio.to_thread(
                self.session.capture_evidence_only,
                question_number=target_q,
                command=command,
                cmd_result=cmd_result,
            )

            shot_file = self.session.storage.get_screenshot_path(target_q)
            ev_card.set_success(shot_path=shot_file, exit_code=record.exit_code)

            # Advance active question if this was the latest question
            if target_q == self.session.current_q_num - 1:
                self.active_q = self.session.current_q_num

            self.sync_ui_to_current_question()
            self.query_one(CommandPrompt).clear()

        except Exception as ex:
            ev_card.set_screenshot_error(str(ex))
        finally:
            self.is_executing = False

    def action_retry(self) -> None:
        """Retry screenshot capture for current question without re-running shell command."""
        if self.is_executing:
            return

        ev_card = self.query_one(EvidenceCard)
        ev_card.set_capturing()
        self.is_executing = True

        async def _retry():
            try:
                shot_path = await asyncio.to_thread(self.session.retry_screenshot_only, self.active_q)
                ev_card.set_success(shot_path=shot_path)
                self.sync_ui_to_current_question()
            except Exception as ex:
                ev_card.set_screenshot_error(str(ex))
            finally:
                self.is_executing = False

        self.run_worker(_retry(), exclusive=True)

    def action_next(self) -> None:
        self.active_q += 1
        self.sync_ui_to_current_question()

    def action_prev(self) -> None:
        if self.active_q > 1:
            self.active_q -= 1
            self.sync_ui_to_current_question()

    def action_preview(self) -> None:
        shot_path = self.session.storage.get_screenshot_path(self.active_q)
        if shot_path.exists():
            self.app.push_screen(PreviewModal(shot_path=shot_path, q_num=self.active_q))

    def action_status(self) -> None:
        self.app.push_screen(StatusModal(self.session))

    def action_finish(self) -> None:
        self.app.push_screen(SummaryScreen(self.session))

    def action_help(self) -> None:
        self.app.push_screen(HelpModal())

    def action_quit(self) -> None:
        self.session.close()
        self.app.pop_screen()

    def on_evidence_card_action_requested(self, event: EvidenceCard.ActionRequested) -> None:
        if event.action == "retry":
            self.action_retry()
        elif event.action == "preview":
            self.action_preview()
        elif event.action == "next":
            self.action_next()
