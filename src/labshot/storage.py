"""Storage management for lab screenshots, command logs, metadata, and submissions."""

import json
import os
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_default_base_dir() -> Path:
    """Return default output directory on Desktop."""
    desktop = Path.home() / "Desktop"
    if desktop.exists():
        return desktop / "CS345"
    return Path.cwd() / "CS345"


def sanitize_folder_name(name: str) -> str:
    """Convert lab name to a safe filesystem directory name (e.g. 'Essential Linux Commands' -> 'Essential-Linux-Commands')."""
    s = re.sub(r"[^\w\s-]", "", name).strip()
    s = re.sub(r"[-\s]+", "-", s)
    return s or "Lab"


@dataclass
class QuestionRecord:
    """Metadata for a single lab question execution."""
    number: int
    command: str
    screenshot: str  # Relative path e.g. "screenshots/q1.png"
    command_file: str  # Relative path e.g. "commands/q1.txt"
    exit_code: int
    timestamp: str
    working_directory_before: str
    working_directory_after: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuestionRecord":
        return cls(
            number=data["number"],
            command=data["command"],
            screenshot=data["screenshot"],
            command_file=data["command_file"],
            exit_code=data.get("exit_code", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            working_directory_before=data.get("working_directory_before", ""),
            working_directory_after=data.get("working_directory_after", ""),
        )


class LabStorage:
    """Manages files, directories, metadata JSON, and export for a lab session."""

    def __init__(self, lab_name: str, base_dir: Optional[Path] = None):
        self.lab_name = lab_name
        self.base_dir = Path(base_dir) if base_dir else get_default_base_dir()
        self.folder_name = sanitize_folder_name(lab_name)
        self.lab_dir = self.base_dir / self.folder_name
        self.screenshots_dir = self.lab_dir / "screenshots"
        self.commands_dir = self.lab_dir / "commands"
        self.metadata_file = self.lab_dir / "lab.json"

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they do not exist."""
        self.lab_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.commands_dir.mkdir(parents=True, exist_ok=True)

    def load_metadata(self) -> Dict[str, Any]:
        """Load lab metadata from lab.json, or initialize if missing."""
        if not self.metadata_file.exists():
            now = datetime.now().isoformat()
            data = {
                "lab": self.lab_name,
                "created_at": now,
                "updated_at": now,
                "questions": [],
            }
            self.save_metadata(data)
            return data

        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # Fallback on corrupted file
            return {
                "lab": self.lab_name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "questions": [],
            }

    def save_metadata(self, data: Dict[str, Any]) -> None:
        """Save lab metadata to lab.json atomically."""
        data["updated_at"] = datetime.now().isoformat()
        temp_file = self.metadata_file.with_suffix(".json.tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        temp_file.replace(self.metadata_file)

    def get_existing_question_numbers(self) -> List[int]:
        """Return list of existing question numbers sorted in ascending order."""
        numbers = set()
        # Scan screenshots directory
        if self.screenshots_dir.exists():
            for p in self.screenshots_dir.glob("q*.png"):
                m = re.match(r"^q(\d+)\.png$", p.name)
                if m:
                    numbers.add(int(m.group(1)))

        # Scan commands directory
        if self.commands_dir.exists():
            for p in self.commands_dir.glob("q*.txt"):
                m = re.match(r"^q(\d+)\.txt$", p.name)
                if m:
                    numbers.add(int(m.group(1)))

        # Check metadata
        meta = self.load_metadata()
        for q in meta.get("questions", []):
            if "number" in q:
                numbers.add(int(q["number"]))

        return sorted(list(numbers))

    def get_next_question_number(self) -> int:
        """Return the next question number to execute based on existing files."""
        existing = self.get_existing_question_numbers()
        if not existing:
            return 1
        return max(existing) + 1

    def get_screenshot_path(self, q_num: int) -> Path:
        """Return path for question screenshot."""
        return self.screenshots_dir / f"q{q_num}.png"

    def get_command_file_path(self, q_num: int) -> Path:
        """Return path for question command text file."""
        return self.commands_dir / f"q{q_num}.txt"

    def record_question(
        self,
        number: int,
        command: str,
        exit_code: int,
        cwd_before: str,
        cwd_after: str,
        timestamp: Optional[str] = None,
    ) -> QuestionRecord:
        """Save command file, update metadata JSON, and return QuestionRecord."""
        ts = timestamp or datetime.now().isoformat()
        cmd_path = self.get_command_file_path(number)
        shot_path = self.get_screenshot_path(number)

        # Write exact command to commands/qN.txt
        with open(cmd_path, "w", encoding="utf-8") as f:
            f.write(command.strip() + "\n")

        rel_shot = f"screenshots/{shot_path.name}"
        rel_cmd = f"commands/{cmd_path.name}"

        record = QuestionRecord(
            number=number,
            command=command,
            screenshot=rel_shot,
            command_file=rel_cmd,
            exit_code=exit_code,
            timestamp=ts,
            working_directory_before=cwd_before,
            working_directory_after=cwd_after,
        )

        meta = self.load_metadata()
        questions = meta.get("questions", [])

        # Update or append
        updated = False
        for i, q in enumerate(questions):
            if q.get("number") == number:
                questions[i] = record.to_dict()
                updated = True
                break

        if not updated:
            questions.append(record.to_dict())

        # Sort questions by number
        questions.sort(key=lambda item: item.get("number", 0))
        meta["questions"] = questions
        self.save_metadata(meta)

        return record

    def export_submission(self, target_dir: Optional[Path] = None) -> Path:
        """Export screenshots and formatted commands to a clean submission directory."""
        dest = target_dir or (self.lab_dir / "submission")
        dest.mkdir(parents=True, exist_ok=True)

        meta = self.load_metadata()
        questions = meta.get("questions", [])

        commands_summary_lines = [
            f"# CS345 Lab Submission: {self.lab_name}",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Total Questions: {len(questions)}",
            "-" * 60,
            "",
        ]

        for q in questions:
            num = q.get("number")
            cmd = q.get("command", "")
            code = q.get("exit_code", 0)
            cwd = q.get("working_directory_after", "")
            shot_file = self.get_screenshot_path(num)

            # Copy screenshot to submission directory
            if shot_file.exists():
                dest_shot = dest / f"q{num}.png"
                shutil.copy2(shot_file, dest_shot)

            commands_summary_lines.append(f"Q{num} > {cmd}")
            commands_summary_lines.append(f"  [Exit Code: {code}] [Dir: {cwd}]")
            commands_summary_lines.append(f"  [Screenshot: q{num}.png]")
            commands_summary_lines.append("")

        summary_file = dest / "commands.txt"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("\n".join(commands_summary_lines) + "\n")

        return dest

    @classmethod
    def list_all_labs(cls, base_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Discover and list all existing labs in the Desktop CS345 directory."""
        root = Path(base_dir) if base_dir else get_default_base_dir()
        if not root.exists():
            return []

        labs = []
        for d in sorted(root.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                meta_file = d / "lab.json"
                lab_name = d.name.replace("-", " ")
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            lab_name = meta.get("lab", lab_name)
                    except Exception:
                        pass

                storage = cls(lab_name=lab_name, base_dir=root)
                nums = storage.get_existing_question_numbers()
                if nums or meta_file.exists():
                    labs.append({
                        "name": lab_name,
                        "folder": d.name,
                        "dir": d,
                        "completed": nums,
                        "count": len(nums),
                        "next": storage.get_next_question_number(),
                    })

        return labs
