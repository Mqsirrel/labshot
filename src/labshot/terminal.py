"""Terminal emulator management, configuration generation, and window activation."""

import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from labshot.config import LabConfig, TerminalConfig, DEFAULT_CONFIG


@dataclass
class WindowGeometry:
    """Window pixel coordinates and dimensions."""
    x: int
    y: int
    width: int
    height: int

    def to_geometry_str(self) -> str:
        """Format as 'X,Y WxH' string for grim / slurp."""
        return f"{self.x},{self.y} {self.width}x{self.height}"


class TerminalManager:
    """Detects, configures, launches, and activates real GUI terminal emulators."""

    def __init__(self, config: LabConfig = DEFAULT_CONFIG, preferred_term: Optional[str] = None):
        self.config = config
        self.preferred_term = preferred_term
        self.selected_term = self._detect_terminal(preferred_term)
        self.temp_dir: Optional[str] = None
        self.process: Optional[subprocess.Popen] = None
        self.session_token: str = uuid.uuid4().hex[:8]
        self.window_title: str = f"labshot — CS345 Terminal [{self.session_token}]"
        self.cached_window_id: Optional[str] = None

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
        self.session_token = uuid.uuid4().hex[:8]
        self.window_title = f"labshot — CS345 — {lab_name} [{self.session_token}]"
        self.temp_dir = tempfile.mkdtemp(prefix="labshot_term_")

        env = os.environ.copy()
        env["LABSHOT_SOCK"] = str(sock_path)
        env["LABSHOT_FIFO"] = str(fifo_path)
        env["LABSHOT_TITLE"] = self.window_title
        env["LABSHOT_TOKEN"] = self.session_token
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

    def activate_window(self) -> bool:
        """Activate/raise the terminal window using multi-tiered compositor and window manager APIs."""
        target_pid = self.process.pid if self.process else -1
        token = self.session_token

        # Tier 1: KDE Plasma 6 & 5 KWin Scripting (Wayland & X11)
        if shutil.which("qdbus6") or shutil.which("qdbus"):
            qdbus_bin = shutil.which("qdbus6") or "qdbus"
            kwin_js = f"""
            var wins = workspace.stackingOrder;
            for (var i = 0; i < wins.length; i++) {{
                var w = wins[i];
                if ((w.pid && w.pid === {target_pid}) || (w.caption && w.caption.indexOf("{token}") !== -1)) {{
                    workspace.activeWindow = w;
                    break;
                }}
            }}
            """
            script_file = Path(self.temp_dir) / "focus.js" if self.temp_dir else Path(f"/tmp/labshot_focus_{token}.js")
            try:
                with open(script_file, "w", encoding="utf-8") as f:
                    f.write(kwin_js)
                subprocess.run(
                    [qdbus_bin, "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.loadDeclarativeScript", str(script_file), f"labshot_focus_{token}"],
                    capture_output=True, text=True, timeout=2
                )
                subprocess.run([qdbus_bin, "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.start"], capture_output=True, timeout=2)
                time.sleep(0.05)
                subprocess.run([qdbus_bin, "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.unloadScript", f"labshot_focus_{token}"], capture_output=True, timeout=2)
                return True
            except Exception:
                pass

        # Tier 2: Hyprland Wayland IPC (hyprctl)
        if shutil.which("hyprctl"):
            try:
                subprocess.run(["hyprctl", "dispatch", "focuswindow", f"title:{token}"], capture_output=True, timeout=1)
                return True
            except Exception:
                pass

        # Tier 3: Sway Wayland IPC (swaymsg)
        if shutil.which("swaymsg"):
            try:
                subprocess.run(["swaymsg", f"[title=\"{token}\"]", "focus"], capture_output=True, timeout=1)
                return True
            except Exception:
                pass

        # Tier 4: X11 / XWayland (xdotool / wmctrl)
        if shutil.which("xdotool"):
            try:
                res = subprocess.run(["xdotool", "search", "--name", token, "windowactivate", "--sync"], capture_output=True, timeout=1)
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        if shutil.which("wmctrl"):
            try:
                res = subprocess.run(["wmctrl", "-a", token], capture_output=True, timeout=1)
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        return False

    def find_x11_window_id(self) -> Optional[str]:
        """Find the X11 Window ID corresponding to our terminal window."""
        token = self.session_token

        if shutil.which("xdotool"):
            try:
                res = subprocess.run(["xdotool", "search", "--name", token], capture_output=True, text=True, timeout=1)
                if res.returncode == 0 and res.stdout.strip():
                    # Return the last window ID found
                    ids = res.stdout.strip().splitlines()
                    if ids:
                        self.cached_window_id = ids[-1].strip()
                        return self.cached_window_id
            except Exception:
                pass

        if shutil.which("wmctrl"):
            try:
                res = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=1)
                if res.returncode == 0:
                    for line in res.stdout.splitlines():
                        if token in line:
                            parts = line.split()
                            if parts:
                                self.cached_window_id = parts[0]
                                return self.cached_window_id
            except Exception:
                pass

        return None

    def get_window_geometry(self) -> Optional[WindowGeometry]:
        """Query compositor IPC to retrieve exact window bounding box."""
        target_pid = self.process.pid if self.process else -1
        token = self.session_token

        # Hyprland
        if shutil.which("hyprctl"):
            try:
                res = subprocess.run(["hyprctl", "activewindow", "-j"], capture_output=True, text=True, timeout=1)
                if res.returncode == 0:
                    data = json.loads(res.stdout)
                    if token in data.get("title", "") or data.get("pid") == target_pid:
                        at = data.get("at", [0, 0])
                        size = data.get("size", [0, 0])
                        return WindowGeometry(x=at[0], y=at[1], width=size[0], height=size[1])
            except Exception:
                pass

        # Sway
        if shutil.which("swaymsg"):
            try:
                res = subprocess.run(["swaymsg", "-t", "get_tree"], capture_output=True, text=True, timeout=1)
                if res.returncode == 0:
                    tree = json.loads(res.stdout)
                    def find_node(node):
                        if token in node.get("name", ""):
                            r = node.get("rect", {})
                            return WindowGeometry(x=r.get("x", 0), y=r.get("y", 0), width=r.get("width", 0), height=r.get("height", 0))
                        for n in node.get("nodes", []) + node.get("floating_nodes", []):
                            found = find_node(n)
                            if found:
                                return found
                        return None
                    geom = find_node(tree)
                    if geom:
                        return geom
            except Exception:
                pass

        return None

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
