"""Configuration settings and defaults for labshot."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any


@dataclass
class TerminalTheme:
    """Terminal theme configuration optimized for high readability in reports."""
    name: str = "labshot-high-contrast"
    background: str = "#1e1e2e"
    foreground: str = "#cdd6f4"
    black: str = "#45475a"
    red: str = "#f38ba8"
    green: str = "#a6e3a1"
    yellow: str = "#f9e2af"
    blue: str = "#89b4fa"
    magenta: str = "#f5c2e7"
    cyan: str = "#94e2d5"
    white: str = "#bac2de"


@dataclass
class TerminalConfig:
    """Terminal window dimensions, typography and behavior."""
    columns: int = 110
    lines: int = 32
    font_family: str = "monospace"
    font_size: float = 13.0
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
    post_command_delay: float = 0.12  # Wait for GPU/compositor render buffer
    terminal_config: TerminalConfig = field(default_factory=TerminalConfig)


DEFAULT_CONFIG = LabConfig()
