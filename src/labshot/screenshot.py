"""Native screenshot capture engine for Wayland and X11 display servers."""

import os
import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple


class ScreenshotError(Exception):
    """Raised when screenshot capture fails."""
    pass


class ScreenshotBackend(ABC):
    """Abstract interface for native desktop screenshot capture backends."""

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def capture_active_window(self, output_path: Path) -> bool:
        pass


class SpectacleBackend(ScreenshotBackend):
    """KDE Spectacle screenshot backend (supports KDE Plasma on Wayland & X11)."""

    def name(self) -> str:
        return "Spectacle (KDE Native)"

    def is_available(self) -> bool:
        return shutil.which("spectacle") is not None

    def capture_active_window(self, output_path: Path) -> bool:
        """Capture the currently active window using Spectacle in background mode."""
        cmd = [
            "spectacle",
            "-b",           # Background mode
            "-n",           # No notification
            "-a",           # Active window
            "-S",           # No drop shadow (clean border)
            "-o", str(output_path),
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0
        except Exception:
            return False


class GrimBackend(ScreenshotBackend):
    """Grim / Slurp backend for generic Wayland compositors (Sway, Hyprland, etc.)."""

    def name(self) -> str:
        return "Grim (Wayland)"

    def is_available(self) -> bool:
        return shutil.which("grim") is not None

    def capture_active_window(self, output_path: Path) -> bool:
        """Capture screen/window using grim."""
        try:
            # If slurp is available and window can be targeted or active
            res = subprocess.run(["grim", str(output_path)], capture_output=True, text=True, timeout=10)
            return res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0
        except Exception:
            return False


class ImageMagickImportBackend(ScreenshotBackend):
    """ImageMagick `import` backend for X11 / XWayland."""

    def name(self) -> str:
        return "ImageMagick Import (X11)"

    def is_available(self) -> bool:
        return shutil.which("import") is not None and (os.environ.get("DISPLAY") is not None)

    def capture_active_window(self, output_path: Path) -> bool:
        """Capture active window using ImageMagick import -window root or active."""
        try:
            res = subprocess.run(
                ["import", "-window", "root", str(output_path)],
                capture_output=True, text=True, timeout=10
            )
            return res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0
        except Exception:
            return False


class ScrotBackend(ScreenshotBackend):
    """Scrot backend for X11."""

    def name(self) -> str:
        return "Scrot (X11)"

    def is_available(self) -> bool:
        return shutil.which("scrot") is not None and (os.environ.get("DISPLAY") is not None)

    def capture_active_window(self, output_path: Path) -> bool:
        try:
            res = subprocess.run(
                ["scrot", "-u", "-b", str(output_path)],
                capture_output=True, text=True, timeout=10
            )
            return res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0
        except Exception:
            return False


def verify_png_file(path: Path) -> bool:
    """Verify that file exists, is non-empty, and has valid PNG magic bytes."""
    if not path.exists() or path.stat().st_size < 100:
        return False
    try:
        with open(path, "rb") as f:
            header = f.read(8)
            return header == b"\x89PNG\r\n\x1a\n"
    except Exception:
        return False


class ScreenshotManager:
    """Detects available screenshot engines and performs verified window captures."""

    def __init__(self, preferred_backend: Optional[str] = None):
        self.backends: List[ScreenshotBackend] = [
            SpectacleBackend(),
            GrimBackend(),
            ImageMagickImportBackend(),
            ScrotBackend(),
        ]
        self.active_backend: Optional[ScreenshotBackend] = None
        self._select_backend(preferred_backend)

    def _select_backend(self, preferred_backend: Optional[str] = None) -> None:
        if preferred_backend:
            for b in self.backends:
                if preferred_backend.lower() in b.name().lower() and b.is_available():
                    self.active_backend = b
                    return

        # Auto-detect first available backend
        for b in self.backends:
            if b.is_available():
                self.active_backend = b
                return

    def get_backend_name(self) -> str:
        return self.active_backend.name() if self.active_backend else "None (No tool found)"

    def capture(self, output_path: Path, delay_seconds: float = 0.08) -> Path:
        """Capture screenshot of the active terminal window and save to output_path."""
        if not self.active_backend:
            raise ScreenshotError(
                "No supported screenshot utility found on this system. "
                "Please install spectacle, grim, import (ImageMagick), or scrot."
            )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists():
            try:
                output_path.unlink()
            except Exception:
                pass

        if delay_seconds > 0:
            time.sleep(delay_seconds)

        success = self.active_backend.capture_active_window(output_path)
        if not success or not verify_png_file(output_path):
            # Try other available backends as fallback
            for fallback in self.backends:
                if fallback != self.active_backend and fallback.is_available():
                    if fallback.capture_active_window(output_path) and verify_png_file(output_path):
                        return output_path

            raise ScreenshotError(
                f"Failed to capture screenshot to '{output_path}' using {self.active_backend.name()}."
            )

        return output_path
