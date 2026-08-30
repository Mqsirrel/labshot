"""Main Textual Application for Labshot."""

from typing import Optional
from textual.app import App, ComposeResult
from textual.screen import Screen

from labshot.config import LabConfig, DEFAULT_CONFIG
from labshot.session import LabSession
from labshot.ui.screens.home import HomeScreen
from labshot.ui.screens.lab import LabScreen
from labshot.ui.theme import APP_CSS


class LabshotApp(App):
    """Labshot Keyboard-First TUI Application."""

    TITLE = "Labshot — Linux Lab Evidence Recorder"
    CSS = APP_CSS

    def __init__(
        self,
        lab_name: Optional[str] = None,
        preferred_term: Optional[str] = None,
        preferred_screenshot: Optional[str] = None,
        config: Optional[LabConfig] = None,
    ):
        super().__init__()
        self.initial_lab_name = lab_name
        self.preferred_term = preferred_term
        self.preferred_screenshot = preferred_screenshot
        self.config = config or DEFAULT_CONFIG
        self.current_session: Optional[LabSession] = None

    def on_mount(self) -> None:
        self.push_screen(HomeScreen())
        if self.initial_lab_name:
            self.start_lab_session(self.initial_lab_name)

    def start_lab_session(self, lab_name: str) -> None:
        """Initialize and launch real shell terminal and enter Lab workspace."""
        if self.current_session:
            try:
                self.current_session.close()
            except Exception:
                pass

        self.current_session = LabSession(
            lab_name=lab_name,
            config=self.config,
            preferred_term=self.preferred_term,
            preferred_screenshot=self.preferred_screenshot,
        )
        self.current_session.start()
        self.push_screen(LabScreen(self.current_session))

    def on_unmount(self) -> None:
        if self.current_session:
            try:
                self.current_session.close()
            except Exception:
                pass


def run_tui(
    lab_name: Optional[str] = None,
    preferred_term: Optional[str] = None,
    preferred_screenshot: Optional[str] = None,
) -> None:
    """Entry point to launch the Textual TUI."""
    app = LabshotApp(
        lab_name=lab_name,
        preferred_term=preferred_term,
        preferred_screenshot=preferred_screenshot,
    )
    app.run()
