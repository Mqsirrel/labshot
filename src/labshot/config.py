"""Configuration settings and defaults for labshot."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any


@dataclass
class TerminalTheme:
    """Terminal theme configuration matching user's sleek Konsole / MaterialYou appearance."""
    name: str = "Konsole-MaterialYou"
    background: str = "#0c0e14"       # Deep dark background from Konsole MaterialYou
    foreground: str = "#d2ddf2"       # Ice-blue/white high-contrast text
    # Normal colors
    black: str = "#1e222b"
    red: str = "#e06c75"
    green: str = "#98c379"
    yellow: str = "#e5c07b"
    blue: str = "#61afef"
    magenta: str = "#c678dd"
    cyan: str = "#56b6c2"
    white: str = "#c2c2cb"
    # Bright colors
    bright_black: str = "#454d5a"
    bright_red: str = "#e57c85"
    bright_green: str = "#a3ca86"
    bright_yellow: str = "#ebd18a"
    bright_blue: str = "#71b7f2"
    bright_magenta: str = "#cf8ce2"
    bright_cyan: str = "#68c5cf"
    bright_white: str = "#ffffff"


@dataclass
class TerminalConfig:
    """Terminal window dimensions, typography and behavior."""
    columns: int = 110
    lines: int = 32
    font_family: str = "Hack"
    font_size: float = 12.5
    padding_x: int = 14
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
