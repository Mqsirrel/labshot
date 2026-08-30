"""Unified multi-shell (Fish, Zsh, Bash) command and path suggester for Textual."""

import os
import re
from pathlib import Path
from typing import Callable, List, Optional, Set
from textual.suggester import Suggester


def load_user_shell_histories(max_items: int = 500) -> List[str]:
    """Seamlessly load and merge commands from Fish, Zsh, and Bash history files."""
    commands: List[str] = []
    seen: Set[str] = set()

    def add_cmd(raw: str):
        c = raw.strip()
        if c and len(c) >= 2 and c not in seen and not c.startswith("#"):
            seen.add(c)
            commands.append(c)

    # 1. Fish History (~/.local/share/fish/fish_history)
    fish_hist = Path.home() / ".local/share/fish/fish_history"
    if fish_hist.exists():
        try:
            for line in fish_hist.read_text(errors="ignore").splitlines():
                line = line.strip()
                if line.startswith("- cmd:"):
                    add_cmd(line[6:])
        except Exception:
            pass

    # 2. Zsh History (~/.zsh_history, ~/.zhistory)
    for zpath in (Path.home() / ".zsh_history", Path.home() / ".zhistory"):
        if zpath.exists():
            try:
                for line in zpath.read_text(errors="ignore").splitlines():
                    line = line.strip()
                    if ":" in line and ";" in line:
                        parts = line.split(";", 1)
                        if len(parts) == 2:
                            add_cmd(parts[1])
                    else:
                        add_cmd(line)
            except Exception:
                pass

    # 3. Bash History (~/.bash_history)
    bash_hist = Path.home() / ".bash_history"
    if bash_hist.exists():
        try:
            for line in bash_hist.read_text(errors="ignore").splitlines():
                add_cmd(line)
        except Exception:
            pass

    return commands[:max_items]


class FishCommandSuggester(Suggester):
    """Provides inline auto-suggestions merging Fish, Zsh, Bash history and Linux commands."""

    COMMON_COMMANDS: List[str] = [
        # Basic File & Directory
        "ls -la",
        "ls -lh",
        "ls -l",
        "pwd",
        "cd ..",
        "cd ~",
        "cd -",
        "mkdir -p",
        "rm -rf",
        "rm -i",
        "cp -r",
        "cp -i",
        "mv -i",
        "touch",
        "cat /etc/passwd",
        "cat /etc/os-release",
        "head -n 10",
        "tail -n 20",
        "tail -f",
        "grep -rn",
        "find . -name",
        "chmod +x",
        "chmod 755",
        "chmod 644",
        "chown",
        "uname -a",
        "whoami",
        "id",
        "df -h",
        "du -sh *",
        "ps aux",
        "ps -ef",
        "top",
        "htop",
        "free -m",
        "tar -xvf",
        "tar -czvf",
        "; cd ..",
        "; cd ~",
        "; cd /tmp",
        "; cd /var/log",
        "; pwd",
        "; ls -la",
        "; mkdir -p",
        "history",
        "clear",
    ]

    def __init__(
        self,
        get_cwd: Optional[Callable[[], str]] = None,
        history: Optional[List[str]] = None,
        load_system_shells: bool = True,
    ):
        super().__init__(use_cache=False, case_sensitive=False)
        self.get_cwd = get_cwd
        self.history: List[str] = []
        self._seen: Set[str] = set()

        if history:
            for h in history:
                self.add_history(h)

        if load_system_shells:
            for sh_cmd in load_user_shell_histories():
                self.add_history(sh_cmd)

    def add_history(self, command: str) -> None:
        cmd = command.strip()
        if cmd and cmd not in self._seen:
            self._seen.add(cmd)
            self.history.append(cmd)

    async def get_suggestion(self, value: str) -> Optional[str]:
        if not value or len(value.strip()) == 0:
            return None

        val = value.strip()
        val_lower = val.lower()

        # 1. Check path completion when typing paths (e.g. 'cd /', '; cd Doc')
        path_suggestion = self._suggest_path(val)
        if path_suggestion:
            return path_suggestion

        # 2. Check recent shell and session history
        for h in self.history:
            if h.lower().startswith(val_lower) and len(h) > len(val):
                return h

        # 3. Check common standard Linux commands
        for cmd in self.COMMON_COMMANDS:
            if cmd.lower().startswith(val_lower) and len(cmd) > len(val):
                return cmd

        return None

    def _suggest_path(self, val: str) -> Optional[str]:
        """Perform path and filename completion based on current working directory."""
        parts = val.split()
        if not parts:
            return None

        # Check if doing a cd, ls, cat, etc.
        target_token: Optional[str] = None
        if len(parts) >= 2 and parts[0].lower() in ("cd", "ls", "cat", "rm", "cp", "mv", "touch", "nano", "vim"):
            target_token = parts[-1]
        elif len(parts) >= 3 and parts[0] in (";", ">", "~") and parts[1].lower() in ("cd", "ls", "cat"):
            target_token = parts[-1]

        if not target_token:
            return None

        prefix = val[:len(val) - len(target_token)]

        try:
            base_dir = Path(self.get_cwd()).resolve() if self.get_cwd else Path.cwd()
            if target_token.startswith("/"):
                search_dir = Path(target_token).parent
                stub = Path(target_token).name
            elif target_token.startswith("~"):
                expanded = Path(target_token).expanduser()
                search_dir = expanded.parent
                stub = expanded.name
            else:
                search_path = base_dir / target_token
                search_dir = search_path.parent if "/" in target_token else base_dir
                stub = target_token.split("/")[-1]

            if search_dir.exists() and search_dir.is_dir():
                for entry in sorted(os.listdir(search_dir)):
                    if entry.lower().startswith(stub.lower()) and len(entry) > len(stub):
                        full_entry = entry + ("/" if (search_dir / entry).is_dir() else "")
                        if "/" in target_token:
                            dir_prefix = target_token.rsplit("/", 1)[0] + "/"
                            completed_arg = dir_prefix + full_entry
                        else:
                            completed_arg = full_entry
                        return prefix + completed_arg
        except Exception:
            pass

        return None
