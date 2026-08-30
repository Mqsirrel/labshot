"""Question List Widget for the left pane navigation."""

from typing import List, Optional, Set
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static


class QuestionListItem(Static):
    """A single row representing a lab question in the left list."""

    def __init__(self, q_num: int, is_done: bool, is_current: bool, label_text: str = ""):
        self.q_num = q_num
        self.is_done = is_done
        self.is_current = is_current
        self.label_text = label_text or f"Question {q_num}"
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
            icon = "→"
        elif self.is_done:
            icon = "✓"
        else:
            icon = "○"
        return f"{icon} Q{self.q_num}"


class QuestionList(Widget):
    """Vertical list displaying questions and progress in the lab."""

    class Selected(Message):
        """Emitted when a question is selected."""
        def __init__(self, q_num: int) -> None:
            self.q_num = q_num
            super().__init__()

    current_q: reactive[int] = reactive(1)
    completed_qs: reactive[Set[int]] = reactive(set)

    def __init__(self, current_q: int = 1, completed_qs: Optional[Set[int]] = None, total_display: int = 15):
        super().__init__()
        self.current_q = current_q
        self.completed_qs = completed_qs or set()
        self.total_display = total_display

    def compose(self) -> ComposeResult:
        yield Label("Questions", classes="panel-title")
        with VerticalScroll(id="question-list-scroll"):
            for i in range(1, self.total_display + 1):
                yield QuestionListItem(
                    q_num=i,
                    is_done=(i in self.completed_qs),
                    is_current=(i == self.current_q),
                )

    def update_state(self, current_q: int, completed_qs: Set[int], total_count: Optional[int] = None) -> None:
        """Update question list items reflecting new state."""
        self.current_q = current_q
        self.completed_qs = completed_qs
        if total_count and total_count > self.total_display:
            self.total_display = total_count

        scroll = self.query_one("#question-list-scroll", VerticalScroll)
        scroll.remove_children()

        max_q = max(self.total_display, self.current_q + 2, max(self.completed_qs, default=1) + 1)
        for i in range(1, max_q + 1):
            item = QuestionListItem(
                q_num=i,
                is_done=(i in self.completed_qs),
                is_current=(i == self.current_q),
            )
            scroll.mount(item)
