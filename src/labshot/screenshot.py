"""Native screenshot capture engine for Wayland and X11 display servers."""

import os
import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List, Optional, Tuple


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
    def capture_window(self, output_path: Path, terminal_mgr: Optional[Any] = None) -> bool:
        """Capture specifically the terminal window and save as PNG."""
        pass


class SpectacleBackend(ScreenshotBackend):
    """KDE Spectacle screenshot backend (KDE Plasma on Wayland & X11)."""

    def name(self) -> str:
        return "Spectacle (KDE Native Active Window)"

    def is_available(self) -> bool:
        return shutil.which("spectacle") is not None

    def capture_window(self, output_path: Path, terminal_mgr: Optional[Any] = None) -> bool:
        """Capture the active terminal window using Spectacle."""
        cmd = [
            "spectacle",
            "-b",           # Background mode
            "-n",           # No notification
            "-a",           # Active window only
            "-S",           # No drop shadow
            "-o", str(output_path),
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 500
        except Exception:
            return False


class GrimWindowBackend(ScreenshotBackend):
    """Grim backend for Wayland with window geometry bounding box."""

    def name(self) -> str:
        return "Grim (Wayland Window Region)"

    def is_available(self) -> bool:
        return shutil.which("grim") is not None

    def capture_window(self, output_path: Path, terminal_mgr: Optional[Any] = None) -> bool:
        """Capture window region using grim -g."""
        if not terminal_mgr:
            return False

        geom = terminal_mgr.get_window_geometry()
        if not geom:
            return False

        try:
            cmd = ["grim", "-g", geom.to_geometry_str(), str(output_path)]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 500
        except Exception:
            return False


class MaimWindowBackend(ScreenshotBackend):
    """Maim backend for X11 targeting specific Window ID."""

    def name(self) -> str:
        return "Maim (X11 Window ID)"

    def is_available(self) -> bool:
        return shutil.which("maim") is not None and (os.environ.get("DISPLAY") is not None)

    def capture_window(self, output_path: Path, terminal_mgr: Optional[Any] = None) -> bool:
        win_id = terminal_mgr.find_x11_window_id() if terminal_mgr else None
        if not win_id:
            # Fallback to active window via xdotool
            if shutil.which("xdotool"):
                try:
                    res = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True, timeout=1)
                    if res.returncode == 0:
                        win_id = res.stdout.strip()
                except Exception:
                    pass

        if not win_id:
            return False

        try:
            res = subprocess.run(["maim", "-i", str(win_id), str(output_path)], capture_output=True, text=True, timeout=10)
            return res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 500
        except Exception:
            return False


class ImageMagickImportBackend(ScreenshotBackend):
    """ImageMagick `import` backend for X11 targeting specific Window ID."""

    def name(self) -> str:
        return "ImageMagick Import (X11 Window ID)"

    def is_available(self) -> bool:
        return shutil.which("import") is not None and (os.environ.get("DISPLAY") is not None)

    def capture_window(self, output_path: Path, terminal_mgr: Optional[Any] = None) -> bool:
        win_id = terminal_mgr.find_x11_window_id() if terminal_mgr else None
        if not win_id and shutil.which("xdotool"):
            try:
                res = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True, timeout=1)
                if res.returncode == 0:
                    win_id = res.stdout.strip()
            except Exception:
                pass

        # Strictly require a window ID to prevent capturing root desktop
        if not win_id:
            return False

        try:
            res = subprocess.run(
                ["import", "-window", str(win_id), str(output_path)],
                capture_output=True, text=True, timeout=10
            )
            return res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 500
        except Exception:
            return False


class ScrotFocusedBackend(ScreenshotBackend):
    """Scrot backend capturing exclusively the focused active window."""

    def name(self) -> str:
        return "Scrot (X11 Focused Window)"

    def is_available(self) -> bool:
        return shutil.which("scrot") is not None and (os.environ.get("DISPLAY") is not None)

    def capture_window(self, output_path: Path, terminal_mgr: Optional[Any] = None) -> bool:
        try:
            # -u: focused window only, -b: include window border
            res = subprocess.run(
                ["scrot", "-u", "-b", str(output_path)],
                capture_output=True, text=True, timeout=10
            )
            return res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 500
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
            GrimWindowBackend(),
            MaimWindowBackend(),
            ImageMagickImportBackend(),
            ScrotFocusedBackend(),
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

    def capture(
        self,
        output_path: Path,
        delay_seconds: float = 0.08,
        terminal_mgr: Optional[Any] = None,
    ) -> Path:
        """Capture screenshot of the terminal window and save to output_path."""
        if not self.active_backend:
            raise ScreenshotError(
                "No supported screenshot utility found on this system. "
                "Please install spectacle, grim, maim, import (ImageMagick), or scrot."
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

        success = self.active_backend.capture_window(output_path, terminal_mgr=terminal_mgr)
        if not success or not verify_png_file(output_path):
            # Try other available backends as fallback
            for fallback in self.backends:
                if fallback != self.active_backend and fallback.is_available():
                    if fallback.capture_window(output_path, terminal_mgr=terminal_mgr) and verify_png_file(output_path):
                        return output_path

            raise ScreenshotError(
                f"Failed to capture window screenshot to '{output_path}' using {self.active_backend.name()}. "
                "Ensure the terminal window is visible on screen."
            )

        return output_path
