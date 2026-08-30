"""Dynamic Question List Widget showing only actual/needed questions."""

from typing import List, Optional, Set
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static


class QuestionListItem(Static):
    """A single row representing a lab question in the left list."""

    def __init__(self, q_num: int, is_done: bool, is_current: bool, command: str = ""):
        self.q_num = q_num
        self.is_done = is_done
        self.is_current = is_current
        self.command = command
        super().__init__(self._build_text(), classes=self._build_classes())

    def _build_classes(self) -> str:
        classes = ["q-item"]
        if self.is_current:
            classes.append("q-item-active")
        elif self.is_done:
            classes.append("q-item-done")
        return " ".join(classes)

    def _build_text(self) -> str:
        if self.is_current:
            icon = "▶"
            status_text = "current"
        elif self.is_done:
            icon = "✓"
            status_text = self.command[:14] if self.command else "done"
        else:
            icon = "○"
            status_text = "pending"
        return f"{icon} Q{self.q_num:<2} {status_text}"


class QuestionList(Widget):
    """Dynamic vertical list displaying only needed questions."""

    class Selected(Message):
        """Emitted when a question is selected."""
        def __init__(self, q_num: int) -> None:
            self.q_num = q_num
            super().__init__()

    current_q: reactive[int] = reactive(1)
    completed_qs: reactive[Set[int]] = reactive(set)

    def __init__(self, current_q: int = 1, completed_qs: Optional[Set[int]] = None, q_records: Optional[List[dict]] = None):
        super().__init__()
        self.current_q = current_q
        self.completed_qs = completed_qs or set()
        self.q_records = q_records or []

    def compose(self) -> ComposeResult:
        yield Label("Questions", classes="panel-title")
        with VerticalScroll(id="question-list-scroll"):
            # Only render questions that exist or is active (no fixed 15 count!)
            max_q = max(self.current_q, max(self.completed_qs, default=1))
            for i in range(1, max_q + 1):
                cmd = self._get_cmd_for_q(i)
                yield QuestionListItem(
                    q_num=i,
                    is_done=(i in self.completed_qs),
                    is_current=(i == self.current_q),
                    command=cmd,
                )

    def _get_cmd_for_q(self, q_num: int) -> str:
        for r in self.q_records:
            if r.get("number") == q_num:
                return r.get("command", "")
        return ""

    def update_state(
        self,
        current_q: int,
        completed_qs: Set[int],
        q_records: Optional[List[dict]] = None,
    ) -> None:
        """Dynamically refresh question list items."""
        self.current_q = current_q
        self.completed_qs = completed_qs
        if q_records is not None:
            self.q_records = q_records

        scroll = self.query_one("#question-list-scroll", VerticalScroll)
        scroll.remove_children()

        # Dynamic range: exactly completed questions + current active question
        max_q = max(self.current_q, max(self.completed_qs, default=1))
        for i in range(1, max_q + 1):
            cmd = self._get_cmd_for_q(i)
            item = QuestionListItem(
                q_num=i,
                is_done=(i in self.completed_qs),
                is_current=(i == self.current_q),
                command=cmd,
            )
            scroll.mount(item)
