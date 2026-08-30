"""Clean Terminal Command Prompt input widget."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Label, Static


class CommandPrompt(Widget):
    """Terminal command input prompt."""

    class Submitted(Message):
        """Emitted when user presses Enter."""
        def __init__(self, command: str, is_setup: bool = False) -> None:
            self.command = command
            self.is_setup = is_setup
            super().__init__()

    def __init__(self, placeholder: str = "mkdir projects, ls -la, cd .."):
        super().__init__(id="prompt-row")
        self.placeholder_text = placeholder

    def compose(self) -> ComposeResult:
        yield Static("$ ", id="prompt-symbol")
        yield Input(
            placeholder=self.placeholder_text,
            id="cmd-input",
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw_val = event.value.strip()
        if not raw_val:
            return

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
