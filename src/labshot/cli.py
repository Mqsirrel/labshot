"""Command-Line Interface and direct, zero-wizard student workflow for labshot."""

import argparse
import os
import readline
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from labshot.config import LabConfig, DEFAULT_CONFIG
from labshot.screenshot import ScreenshotError
from labshot.session import LabSession
from labshot.storage import LabStorage


def format_path_for_display(path: Path) -> str:
    """Format path nicely, using ~ for home directory."""
    try:
        home = Path.home()
        rel = path.resolve().relative_to(home.resolve())
        return f"~/{rel}"
    except Exception:
        return str(path)


def resolve_lab_name(args_lab: Optional[str] = None, base_dir: Optional[Path] = None) -> str:
    """Directly resolve lab name without any interactive wizard questionnaires."""
    if args_lab and args_lab.strip():
        return args_lab.strip()

    # Automatically use the most recent existing lab, or default directly
    labs = LabStorage.list_all_labs(base_dir=base_dir)
    if labs:
        return labs[-1]["name"]

    return "Essential Linux Commands"


def print_help() -> None:
    """Print simple, student-friendly command reference."""
    print("\n--- labshot Commands ---")
    print("  <Linux command>   Execute in terminal & capture screenshot")
    print("  :status           Show completed questions")
    print("  :redo <N>         Re-take Question N")
    print("  :done             Finish lab & prepare submission package")
    print("  :help             Show this help message")
    print("  :exit             Save and quit\n")


def print_status(session: LabSession) -> None:
    """Display simple, clean visual status of the lab."""
    existing = session.storage.get_existing_question_numbers()
    print(f"\nLab: {session.lab_name}")
    if not existing:
        print("  No questions captured yet.")
    else:
        for num in existing:
            print(f"  ✓ Q{num}")
    print(f"  → Q{session.current_q_num} current")
    print(f"Screenshots: {len(existing)}\n")


def handle_done(session: LabSession) -> None:
    """Finish the lab session, export submission, and summarize results without prompts."""
    sub_dir = session.export()
    existing = session.storage.get_existing_question_numbers()
    count = len(existing)

    print("\n" + "=" * 50)
    print("  ✓ Lab complete")
    print(f"  {count} questions captured")
    print(f"  {count} screenshots saved")
    print(f"  Folder:")
    print(f"    {format_path_for_display(session.storage.lab_dir)}")
    print(f"  Submission Package:")
    print(f"    {format_path_for_display(sub_dir)}")
    print("=" * 50 + "\n")


def run_repl(session: LabSession) -> None:
    """Main direct student REPL."""
    if not session.is_active():
        session.start()

    print(f"Lab: {session.lab_name}")
    print(f"Ready.\n")

    redo_target: Optional[int] = None

    while True:
        try:
            if redo_target is not None:
                prompt_str = f"Q{redo_target} (redo) > "
            else:
                prompt_str = f"Q{session.current_q_num} > "

            raw_input = input(prompt_str).strip()

            if not raw_input:
                continue

            # Handle internal commands prefixed with ':'
            if raw_input.startswith(":"):
                parts = raw_input[1:].strip().split()
                cmd = parts[0].lower() if parts else ""

                if cmd in ("done", "finish"):
                    handle_done(session)
                    break

                elif cmd in ("exit", "quit", "q"):
                    print("Exiting labshot. All screenshots and commands saved.")
                    break

                elif cmd == "help":
                    print_help()
                    continue

                elif cmd == "status":
                    print_status(session)
                    continue

                elif cmd == "list":
                    questions = session.list_questions()
                    print(f"\n--- Recorded Questions: {session.lab_name} ---")
                    if not questions:
                        print("  No questions recorded yet.\n")
                    else:
                        for q in questions:
                            print(f"  Q{q['number']:<2} | Exit: {q['exit_code']} | Cmd: {q['command']:<25} | Shot: {q['screenshot']}")
                        print()
                    continue

                elif cmd == "redo":
                    if len(parts) < 2 or not parts[1].isdigit():
                        print("Usage: :redo <question_number>")
                        continue
                    target_q = int(parts[1])
                    if target_q < 1:
                        print("Error: Question number must be >= 1.")
                        continue
                    redo_target = target_q
                    print(f"Next command will re-take Question {redo_target}.")
                    continue

                else:
                    print(f"Unknown command ':{cmd}'. Type :help for commands.")
                    continue

            # Execute real Linux command
            target_q = redo_target if redo_target is not None else session.current_q_num
            is_redo = (redo_target is not None)
            redo_target = None  # Reset redo target

            try:
                record = session.execute_question(raw_input, question_number=target_q)
                shot_name = Path(record.screenshot).name
                if is_redo:
                    print(f"✓ Q{record.number} re-captured → {shot_name}")
                else:
                    print(f"✓ Q{record.number} captured → {shot_name}")
            except ScreenshotError as se:
                print(f"\n✗ Couldn't capture the terminal screenshot.")
                print(f"  Reason: {se}")
                print("  Try:")
                print("    1. Make sure the terminal window is visible and not minimized.")
                print(f"    2. Re-enter your command or run :redo {target_q}\n")
            except Exception as ex:
                print(f"\n✗ Command execution error: {ex}\n")

        except KeyboardInterrupt:
            print("\n(Press :done to finish or :exit to quit)")
            redo_target = None
            continue
        except EOFError:
            print("\nExiting labshot. All screenshots and metadata saved.")
            break


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="labshot",
        description="Real Terminal Lab Screenshot Recorder for Linux university labs.",
    )
    parser.add_argument(
        "lab_name_pos",
        nargs="?",
        default=None,
        help="Optional lab name (e.g. 'Essential Linux Commands')",
    )
    parser.add_argument(
        "--lab",
        "-l",
        type=str,
        default=None,
        help="Name of the university lab",
    )
    parser.add_argument(
        "--term",
        "-t",
        type=str,
        default=None,
        help="Preferred terminal emulator (alacritty, konsole, etc.)",
    )
    parser.add_argument(
        "--screenshot",
        "-s",
        type=str,
        default=None,
        help="Preferred screenshot utility (spectacle, grim, import, scrot)",
    )

    subparsers = parser.add_subparsers(dest="subcommand")

    # Subcommand: export
    export_parser = subparsers.add_parser("export", help="Export screenshots and commands for lab submission")
    export_parser.add_argument("lab", nargs="?", default=None, help="Lab name to export")
    export_parser.add_argument("--out", "-o", type=str, default=None, help="Output destination folder")

    # Subcommand: list
    list_parser = subparsers.add_parser("list", help="List recorded questions for a lab")
    list_parser.add_argument("lab", nargs="?", default=None, help="Lab name")

    # Subcommand: status
    status_parser = subparsers.add_parser("status", help="Show status of a lab session")
    status_parser.add_argument("lab", nargs="?", default=None, help="Lab name")

    # Subcommand: redo
    redo_parser = subparsers.add_parser("redo", help="Re-take a specific question")
    redo_parser.add_argument("question_number", type=int, help="Question number to redo (e.g. 3)")
    redo_parser.add_argument("command", nargs="*", default=[], help="Optional command to execute directly")
    redo_parser.add_argument("--lab", "-l", type=str, default=None, help="Lab name")

    args = parser.parse_args()

    # If subcommand supplied
    if args.subcommand == "export":
        lab_name = resolve_lab_name(args.lab)
        storage = LabStorage(lab_name=lab_name)
        out_dir = Path(args.out) if args.out else None
        dest = storage.export_submission(target_dir=out_dir)
        print(f"Exported submission for '{lab_name}' to: {format_path_for_display(dest)}")
        sys.exit(0)

    if args.subcommand == "list":
        lab_name = resolve_lab_name(args.lab)
        storage = LabStorage(lab_name=lab_name)
        meta = storage.load_metadata()
        questions = meta.get("questions", [])
        print(f"\n--- Recorded Questions: {lab_name} ---")
        if not questions:
            print("  No questions recorded yet.\n")
        else:
            for q in questions:
                print(f"  Q{q['number']:<2} | Exit: {q['exit_code']} | Cmd: {q['command']:<25} | Shot: {q['screenshot']}")
            print()
        sys.exit(0)

    if args.subcommand == "status":
        lab_name = resolve_lab_name(args.lab)
        storage = LabStorage(lab_name=lab_name)
        existing = storage.get_existing_question_numbers()
        print(f"\n--- Lab Status: {lab_name} ---")
        print(f"  Directory:           {format_path_for_display(storage.lab_dir)}")
        print(f"  Completed Questions: {existing}")
        print(f"  Next Question:       Q{storage.get_next_question_number()}\n")
        sys.exit(0)

    # Directly resolve lab name: no wizard, no questions
    specified_name = args.lab or args.lab_name_pos
    lab_name = resolve_lab_name(specified_name)

    session = LabSession(
        lab_name=lab_name,
        preferred_term=args.term,
        preferred_screenshot=args.screenshot,
    )

    try:
        session.start()

        if args.subcommand == "redo":
            q_num = args.question_number
            if args.command:
                cmd_str = " ".join(args.command)
                rec = session.redo_question(question_number=q_num, command=cmd_str)
                print(f"✓ Q{q_num} re-captured → {Path(rec.screenshot).name}")
                session.close()
                sys.exit(0)

        run_repl(session)

    except KeyboardInterrupt:
        print("\nSession interrupted.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
