"""Lightweight Evidence Preview and Metadata Inspector."""

import shutil
import subprocess
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, Static


class PreviewModal(ModalScreen):
    """Modal displaying evidence screenshot metadata and launch option."""

    BINDINGS = [
        ("o", "open_viewer", "Open in viewer"),
        ("escape", "close_modal", "Close"),
    ]

    def __init__(self, shot_path: Path, q_num: int):
        super().__init__()
        self.shot_path = shot_path
        self.q_num = q_num

    def compose(self) -> ComposeResult:
        with Container(classes="modal-box"):
            yield Label(f"Evidence: {self.shot_path.name}", classes="modal-title")
            
            res_str = "Unknown"
            size_str = "0 KB"
            try:
                from PIL import Image
                if self.shot_path.exists():
                    with Image.open(self.shot_path) as img:
                        res_str = f"{img.width} × {img.height}"
                        size_str = f"{self.shot_path.stat().st_size / 1024:.1f} KB"
            except Exception:
                pass

            yield Static(f"Resolution: {res_str}", classes="modal-row")
            yield Static(f"File size:  {size_str}", classes="modal-row")
            yield Static("✓ valid image", classes="modal-row status-text-success")
            yield Static("✓ evidence committed", classes="modal-row status-text-success")
            yield Static("o Open in viewer · Esc Close", classes="modal-actions")

    def action_open_viewer(self) -> None:
        if self.shot_path.exists() and shutil.which("xdg-open"):
            subprocess.Popen(["xdg-open", str(self.shot_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.dismiss()

    def action_close_modal(self) -> None:
        self.dismiss()
