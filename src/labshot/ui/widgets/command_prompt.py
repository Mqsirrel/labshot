"""Command Prompt input widget with Fish-style auto-suggestions and setup command support."""

from typing import Optional
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.suggester import Suggester
from textual.widget import Widget
from textual.widgets import Input, Label


class CommandPrompt(Widget):
    """Terminal-style command prompt input box supporting setup commands and suggestions."""

    class Submitted(Message):
        """Emitted when user executes a command."""
        def __init__(self, command: str, is_setup: bool = False) -> None:
            self.command = command
            self.is_setup = is_setup
            super().__init__()

    def __init__(
        self,
        placeholder: str = "Enter Linux command (e.g. ls -la, pwd, mkdir projects)",
        suggester: Optional[Suggester] = None,
    ):
        super().__init__(id="prompt-container")
        self.placeholder_text = placeholder
        self.suggester = suggester

    def compose(self) -> ComposeResult:
        yield Label("Command", id="prompt-label")
        yield Input(
            placeholder=self.placeholder_text,
            suggester=self.suggester,
            id="cmd-input",
        )
        yield Label("💡 Hint: Fish-like suggestions active (Press Tab/→ to accept). Prefix with ';' for setup without screenshot.", id="cmd-tip-label")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw_val = event.value.strip()
        if not raw_val:
            return

        # Check if setup command prefix is used (e.g. ; cd .., > cd .., ~ pwd)
        if raw_val.startswith(";") or raw_val.startswith(">") or raw_val.startswith("~"):
            clean_cmd = raw_val[1:].strip()
            if clean_cmd:
                self.post_message(self.Submitted(command=clean_cmd, is_setup=True))
        else:
            self.post_message(self.Submitted(command=raw_val, is_setup=False))

    def set_value(self, text: str) -> None:
        inp = self.query_one("#cmd-input", Input)
        inp.value = text

    def clear(self) -> None:
        inp = self.query_one("#cmd-input", Input)
        inp.value = ""

    def focus_input(self) -> None:
        inp = self.query_one("#cmd-input", Input)
        inp.focus()
