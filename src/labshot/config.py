"""Configuration settings and defaults for labshot."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any


@dataclass
class TerminalTheme:
    """Terminal theme configuration matching Tokyo Night (Deep Modern)."""
    name: str = "Tokyo-Night-Modern"
    background: str = "#1a1b26"       # Deep modern Tokyo Night dark background
    foreground: str = "#c0caf5"       # Crisp high-contrast lavender-white text
    # Normal colors
    black: str = "#15161e"
    red: str = "#f7768e"
    green: str = "#9ece6a"
    yellow: str = "#e0af68"
    blue: str = "#7aa2f7"
    magenta: str = "#bb9af7"
    cyan: str = "#7dcfff"
    white: str = "#a9b1d6"
    # Bright colors
    bright_black: str = "#414868"
    bright_red: str = "#ff7a93"
    bright_green: str = "#b9f27c"
    bright_yellow: str = "#ff9e64"
    bright_blue: str = "#7da6ff"
    bright_magenta: str = "#c099ff"
    bright_cyan: str = "#0db9d7"
    bright_white: str = "#c0caf5"


@dataclass
class TerminalConfig:
    """Terminal window dimensions, typography and behavior."""
    columns: int = 110
    lines: int = 32
    font_family: str = "JetBrainsMono Nerd Font"
    font_size: float = 12.5
    padding_x: int = 16
    padding_y: int = 14
    opacity: float = 1.0
    theme: TerminalTheme = field(default_factory=TerminalTheme)


@dataclass
class LabConfig:
    """General configuration for the lab recording session."""
    default_lab_name: str = "Essential Linux Commands"
    base_dir: Path = field(default_factory=lambda: Path.cwd() / "CS345")
    prompt_template: str = r"\u@\h:\w\$ "
    default_timeout_seconds: float = 30.0
    post_command_delay: float = 0.12
    terminal_config: TerminalConfig = field(default_factory=TerminalConfig)


DEFAULT_CONFIG = LabConfig()
