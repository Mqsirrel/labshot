"""Command Prompt input widget with real-time state indication."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Label


class CommandPrompt(Widget):
    """Terminal-style command prompt input box."""

    class Submitted(Message):
        """Emitted when user presses Enter to execute command."""
        def __init__(self, command: str) -> None:
            self.command = command
            super().__init__()

    def __init__(self, placeholder: str = "e.g. ls -la, pwd, mkdir projects"):
        super().__init__(id="prompt-box")
        self.placeholder_text = placeholder

    def compose(self) -> ComposeResult:
        yield Label("Command", id="prompt-label")
        yield Input(
            placeholder=self.placeholder_text,
            id="cmd-input",
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        if cmd:
            self.post_message(self.Submitted(cmd))

    def set_value(self, text: str) -> None:
        inp = self.query_one("#cmd-input", Input)
        inp.value = text

    def clear(self) -> None:
        inp = self.query_one("#cmd-input", Input)
        inp.value = ""

    def focus_input(self) -> None:
        inp = self.query_one("#cmd-input", Input)
        inp.focus()
