"""Terminal emulator management, configuration generation, and window activation."""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple

from labshot.config import LabConfig, TerminalConfig, DEFAULT_CONFIG


class TerminalManager:
    """Detects, configures, and launches real GUI terminal emulators."""

    def __init__(self, config: LabConfig = DEFAULT_CONFIG, preferred_term: Optional[str] = None):
        self.config = config
        self.preferred_term = preferred_term
        self.selected_term = self._detect_terminal(preferred_term)
        self.temp_dir: Optional[str] = None
        self.process: Optional[subprocess.Popen] = None
        self.window_title: str = "labshot — CS345 Terminal"

    def _detect_terminal(self, preferred: Optional[str] = None) -> str:
        """Detect the best available terminal emulator on the system."""
        candidates = ["alacritty", "konsole", "gnome-terminal", "xfce4-terminal", "xterm", "kitty", "foot"]
        if preferred:
            candidates.insert(0, preferred)

        for name in candidates:
            if shutil.which(name):
                return name

        raise RuntimeError(
            "No supported GUI terminal emulator found (e.g. alacritty, konsole, gnome-terminal, xterm). "
            "Please install alacritty or konsole."
        )

    def generate_alacritty_config(self, target_path: Path) -> None:
        """Generate a clean, high-contrast Alacritty TOML config styled after user's Konsole profile."""
        tcfg = self.config.terminal_config
        theme = tcfg.theme

        content = f"""[window]
dimensions = {{ columns = {tcfg.columns}, lines = {tcfg.lines} }}
padding = {{ x = {tcfg.padding_x}, y = {tcfg.padding_y} }}
decorations = "Full"
opacity = 1.0

[font]
size = {tcfg.font_size}
normal = {{ family = "{tcfg.font_family}", style = "Regular" }}
bold = {{ family = "{tcfg.font_family}", style = "Bold" }}

[colors.primary]
background = "{theme.background}"
foreground = "{theme.foreground}"

[colors.normal]
black = "{theme.black}"
red = "{theme.red}"
green = "{theme.green}"
yellow = "{theme.yellow}"
blue = "{theme.blue}"
magenta = "{theme.magenta}"
cyan = "{theme.cyan}"
white = "{theme.white}"

[colors.bright]
black = "{theme.bright_black}"
red = "{theme.bright_red}"
green = "{theme.bright_green}"
yellow = "{theme.bright_yellow}"
blue = "{theme.bright_blue}"
magenta = "{theme.bright_magenta}"
cyan = "{theme.bright_cyan}"
white = "{theme.bright_white}"

[cursor]
style = {{ shape = "Block", blinking = "Off" }}
"""
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

    def launch(
        self,
        worker_script_path: Path,
        sock_path: Path,
        fifo_path: Path,
        lab_name: str,
    ) -> subprocess.Popen:
        """Launch the GUI terminal window running the worker process."""
        self.window_title = f"labshot — CS345 — {lab_name}"
        self.temp_dir = tempfile.mkdtemp(prefix="labshot_term_")

        env = os.environ.copy()
        env["LABSHOT_SOCK"] = str(sock_path)
        env["LABSHOT_FIFO"] = str(fifo_path)
        env["LABSHOT_TITLE"] = self.window_title
        env["LABSHOT_PS1"] = self.config.prompt_template

        python_exec = shutil.which("python3") or "python3"

        if self.selected_term == "alacritty":
            cfg_path = Path(self.temp_dir) / "alacritty.toml"
            self.generate_alacritty_config(cfg_path)
            cmd = [
                "alacritty",
                "--config-file", str(cfg_path),
                "-T", self.window_title,
                "-e", python_exec, str(worker_script_path), str(sock_path), str(fifo_path),
            ]
        elif self.selected_term == "konsole":
            cmd = [
                "konsole",
                "--separate",
                "--hide-menubar",
                "-p", f"TerminalColumns={self.config.terminal_config.columns}",
                "-p", f"TerminalRows={self.config.terminal_config.lines}",
                "-e", python_exec, str(worker_script_path), str(sock_path), str(fifo_path),
            ]
        elif self.selected_term == "gnome-terminal":
            cmd = [
                "gnome-terminal",
                "--title", self.window_title,
                "--", python_exec, str(worker_script_path), str(sock_path), str(fifo_path),
            ]
        elif self.selected_term == "xterm":
            cmd = [
                "xterm",
                "-title", self.window_title,
                "-geometry", f"{self.config.terminal_config.columns}x{self.config.terminal_config.lines}",
                "-e", python_exec, str(worker_script_path), str(sock_path), str(fifo_path),
            ]
        else:
            cmd = [
                self.selected_term,
                "-e", python_exec, str(worker_script_path), str(sock_path), str(fifo_path),
            ]

        self.process = subprocess.Popen(
            cmd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return self.process

    def activate_window(self) -> None:
        """Activate/raise the terminal window using compositor or window manager methods."""
        if shutil.which("qdbus6"):
            kwin_js = f"""
            var windows = workspace.stackingOrder;
            for (var i = 0; i < windows.length; i++) {{
                var w = windows[i];
                if (w.caption.indexOf("labshot") !== -1 || w.caption.indexOf("CS345") !== -1) {{
                    workspace.activeWindow = w;
                    break;
                }}
            }}
            """
            script_file = Path(self.temp_dir) / "focus.js" if self.temp_dir else Path("/tmp/labshot_focus.js")
            try:
                with open(script_file, "w", encoding="utf-8") as f:
                    f.write(kwin_js)
                subprocess.run(
                    ["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.loadDeclarativeScript", str(script_file), "labshot_focus"],
                    capture_output=True, text=True, timeout=2
                )
                subprocess.run(["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.start"], capture_output=True, timeout=2)
                time.sleep(0.04)
                subprocess.run(["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.unloadScript", "labshot_focus"], capture_output=True, timeout=2)
                return
            except Exception:
                pass

        if shutil.which("xdotool"):
            try:
                subprocess.run(["xdotool", "search", "--name", "labshot", "windowactivate"], capture_output=True, timeout=2)
            except Exception:
                pass
        elif shutil.which("wmctrl"):
            try:
                subprocess.run(["wmctrl", "-a", "labshot"], capture_output=True, timeout=2)
            except Exception:
                pass

    def cleanup(self) -> None:
        """Terminate the terminal process and remove temporary files."""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass
