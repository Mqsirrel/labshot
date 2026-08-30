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
        # Check environment variable LABSHOT_TERM as fallback preference
        env_pref = os.environ.get("LABSHOT_TERM")
        pref = preferred_term or env_pref
        self.preferred_term = pref
        self.selected_term = self._detect_terminal(pref)
        self.temp_dir: Optional[str] = None
        self.process: Optional[subprocess.Popen] = None
        self.session_token: str = uuid.uuid4().hex[:8]
        self.window_title: str = f"labshot — CS345 Terminal [{self.session_token}]"
        self.cached_window_id: Optional[str] = None

    def _detect_terminal(self, preferred: Optional[str] = None) -> str:
        """Detect the best available terminal emulator on the system."""
        candidates = ["alacritty", "konsole", "gnome-terminal", "xfce4-terminal", "xterm", "kitty", "foot"]
        if preferred:
            candidates.insert(0, preferred.lower())

        for name in candidates:
            if shutil.which(name):
                return name

        raise RuntimeError(
            "No supported GUI terminal emulator found (e.g. alacritty, konsole, gnome-terminal, xterm). "
            "Please install alacritty or konsole."
        )

    def generate_alacritty_config(self, target_path: Path) -> None:
        """Generate a clean, high-contrast Alacritty TOML config styled after Tokyo Night Modern."""
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
        env["LABSHOT_COLS"] = str(self.config.terminal_config.columns)
        env["LABSHOT_ROWS"] = str(self.config.terminal_config.lines)

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
                "--hide-tabbar",
                "--qwindowtitle", self.window_title,
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
        """Multi-tiered window activation ensuring the terminal window is raised and focused."""
        token = self.session_token
        target_pid = self.process.pid if self.process else 0

        # Tier 1: KDE Plasma 6 KWin Declarative Scripting via qdbus6
        if shutil.which("qdbus6") and (os.environ.get("KDE_FULL_SESSION") or os.environ.get("XDG_CURRENT_DESKTOP") == "KDE"):
            script_name = f"labshot_focus_{token}"
            script_body = f"""
            var clients = workspace.stackingOrder;
            for (var i = 0; i < clients.length; i++) {{
                var w = clients[i];
                if ((w.pid && w.pid === {target_pid}) || (w.caption && w.caption.indexOf("{token}") !== -1)) {{
                    workspace.activeWindow = w;
                    break;
                }}
            }}
            """
            try:
                with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as tf:
                    tf.write(script_body)
                    temp_script_path = tf.name

                res = subprocess.run(
                    ["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.loadDeclarativeScript", temp_script_path, script_name],
                    capture_output=True, text=True, timeout=2
                )
                if res.returncode == 0:
                    subprocess.run(
                        ["qdbus6", "org.kde.KWin", f"/{script_name}", "org.kde.kwin.Scripting.start"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2
                    )
                    subprocess.run(
                        ["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.unloadScript", script_name],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2
                    )
                    try:
                        os.unlink(temp_script_path)
                    except Exception:
                        pass
                    return True
                try:
                    os.unlink(temp_script_path)
                except Exception:
                    pass
            except Exception:
                pass

        # Tier 2: Hyprland IPC
        if shutil.which("hyprctl") and os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
            try:
                res = subprocess.run(
                    ["hyprctl", "dispatch", "focuswindow", f"title:{token}"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1
                )
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        # Tier 3: Sway IPC
        if shutil.which("swaymsg") and os.environ.get("SWAYSOCK"):
            try:
                res = subprocess.run(
                    ["swaymsg", f'[title="{token}"]', "focus"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1
                )
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        # Tier 4: X11 xdotool
        if shutil.which("xdotool") and os.environ.get("DISPLAY"):
            try:
                res = subprocess.run(
                    ["xdotool", "search", "--name", token, "windowactivate", "--sync"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1
                )
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        # Tier 5: X11 wmctrl
        if shutil.which("wmctrl") and os.environ.get("DISPLAY"):
            try:
                res = subprocess.run(
                    ["wmctrl", "-a", token],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1
                )
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        return False

    def find_x11_window_id(self) -> Optional[str]:
        """Find the X11 Window ID corresponding to the terminal window."""
        if self.cached_window_id:
            return self.cached_window_id

        token = self.session_token
        if shutil.which("xdotool"):
            try:
                res = subprocess.run(["xdotool", "search", "--name", token], capture_output=True, text=True, timeout=2)
                if res.returncode == 0 and res.stdout.strip():
                    wid = res.stdout.strip().splitlines()[0]
                    self.cached_window_id = wid
                    return wid
            except Exception:
                pass

        if shutil.which("wmctrl"):
            try:
                res = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=2)
                if res.returncode == 0:
                    for line in res.stdout.splitlines():
                        if token in line:
                            wid = line.split()[0]
                            self.cached_window_id = wid
                            return wid
            except Exception:
                pass

        return None

    def get_window_geometry(self) -> Optional[WindowGeometry]:
        """Query the exact geometry (X, Y, Width, Height) of the terminal window."""
        token = self.session_token

        # Try Hyprland JSON
        if shutil.which("hyprctl"):
            try:
                res = subprocess.run(["hyprctl", "activewindow", "-j"], capture_output=True, text=True, timeout=1)
                if res.returncode == 0:
                    data = json.loads(res.stdout)
                    at = data.get("at", [0, 0])
                    size = data.get("size", [0, 0])
                    if size[0] > 0 and size[1] > 0:
                        return WindowGeometry(x=at[0], y=at[1], width=size[0], height=size[1])
            except Exception:
                pass

        # Try Sway JSON
        if shutil.which("swaymsg"):
            try:
                res = subprocess.run(["swaymsg", "-t", "get_tree"], capture_output=True, text=True, timeout=1)
                if res.returncode == 0:
                    tree = json.loads(res.stdout)
                    def find_focused(node):
                        if node.get("focused"):
                            r = node.get("rect", {})
                            return WindowGeometry(x=r.get("x", 0), y=r.get("y", 0), width=r.get("width", 0), height=r.get("height", 0))
                        for child in node.get("nodes", []) + node.get("floating_nodes", []):
                            found = find_focused(child)
                            if found:
                                return found
                        return None
                    geom = find_focused(tree)
                    if geom:
                        return geom
            except Exception:
                pass

        # Try X11 xwininfo
        x11_id = self.find_x11_window_id()
        if x11_id and shutil.which("xwininfo"):
            try:
                res = subprocess.run(["xwininfo", "-id", str(x11_id)], capture_output=True, text=True, timeout=2)
                if res.returncode == 0:
                    lines = res.stdout.splitlines()
                    x, y, w, h = 0, 0, 0, 0
                    for line in lines:
                        if "Absolute upper-left X:" in line:
                            x = int(line.split()[-1])
                        elif "Absolute upper-left Y:" in line:
                            y = int(line.split()[-1])
                        elif "Width:" in line:
                            w = int(line.split()[-1])
                        elif "Height:" in line:
                            h = int(line.split()[-1])
                    if w > 0 and h > 0:
                        return WindowGeometry(x=x, y=y, width=w, height=h)
            except Exception:
                pass

        return None

    def close(self) -> None:
        """Close the terminal process and clean up temporary directory."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1.5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass
            self.temp_dir = None

    cleanup = close
