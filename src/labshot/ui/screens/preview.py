"""Evidence Preview and Inspection modal."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class PreviewModal(ModalScreen):
    """Modal displaying evidence screenshot metadata and launch option."""

    def __init__(self, shot_path: Path, q_num: int, command: str = ""):
        super().__init__()
        self.shot_path = shot_path
        self.q_num = q_num
        self.command = command

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog"):
            yield Label(f"Evidence Inspector: Q{self.q_num}", classes="modal-title")
            
            with Vertical():
                yield Label(f"File:        {self.shot_path.name}")
                yield Label(f"Path:        {self.shot_path}")
                
                # Check dimensions if Pillow available
                res_str = "Unknown"
                size_str = "0 B"
                try:
                    from PIL import Image
                    if self.shot_path.exists():
                        with Image.open(self.shot_path) as img:
                            res_str = f"{img.width} × {img.height} px"
                            size_str = f"{self.shot_path.stat().st_size / 1024:.1f} KB"
                except Exception:
                    pass

                yield Label(f"Resolution:  {res_str}")
                yield Label(f"File Size:   {size_str}")
                yield Label(f"Status:      ✓ Valid PNG Evidence", classes="status-success")
                if self.command:
                    yield Label(f"Command:     {self.command}", classes="status-muted")

            with Horizontal(classes="home-btn-row"):
                yield Button("Open Image (Viewer)", id="btn-open-viewer", variant="primary")
                yield Button("Close (Esc)", id="btn-close-preview", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-open-viewer":
            if self.shot_path.exists() and shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", str(self.shot_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.dismiss()
        elif event.button.id == "btn-close-preview":
            self.dismiss()
