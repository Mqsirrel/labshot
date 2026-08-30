"""Command-Line Interface and interactive REPL for labshot."""

import argparse
import os
import readline
import sys
from pathlib import Path
from typing import Optional

from labshot.config import LabConfig, DEFAULT_CONFIG
from labshot.session import LabSession
from labshot.storage import LabStorage


def print_banner(lab_name: str, session: Optional[LabSession] = None) -> None:
    """Display student-friendly banner."""
    print("=" * 60)
    print("  CS345 Lab Screenshot Recorder")
    print(f"  Lab: {lab_name}")
    if session:
        status = session.get_status()
        print(f"  Terminal: {status['terminal']} | Screenshot: {status['screenshot_backend']}")
        if status['total_completed'] > 0:
            print(f"  Resumed session (Completed questions: {status['completed_questions']})")
    print("=" * 60)
    print("Type lab commands to execute & capture. Internal commands: :help, :status, :list, :redo <N>, :exit\n")


def print_help() -> None:
    """Print internal commands help."""
    print("\n--- labshot Help ---")
    print("  <any Linux command>   Execute in persistent shell and capture screenshot")
    print("  :status               Display current lab status and working directory")
    print("  :list                 List all recorded questions, exit codes, and files")
    print("  :redo <N>             Re-execute Question N and overwrite its screenshot/command")
    print("  :export               Export submission/ package with PNGs and commands.txt")
    print("  :help                 Show this help message")
    print("  :exit / :quit         Save and exit the session\n")


def run_repl(session: LabSession) -> None:
    """Main interactive REPL loop."""
    print_banner(session.lab_name, session)

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

                if cmd in ("exit", "quit", "q"):
                    print("Exiting labshot. All screenshots and metadata saved.")
                    break

                elif cmd == "help":
                    print_help()
                    continue

                elif cmd == "status":
                    status = session.get_status()
                    print("\n--- Session Status ---")
                    print(f"  Lab:               {status['lab']}")
                    print(f"  Lab Directory:     {status['lab_dir']}")
                    print(f"  Next Question:     Q{status['next_question']}")
                    print(f"  Total Questions:   {status['total_completed']}")
                    print(f"  Working Directory: {status['current_cwd']}")
                    print(f"  Terminal:          {status['terminal']}")
                    print(f"  Screenshot Engine: {status['screenshot_backend']}\n")
                    continue

                elif cmd == "list":
                    questions = session.list_questions()
                    print("\n--- Recorded Questions ---")
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

                elif cmd == "export":
                    dest = session.export()
                    print(f"Submission exported successfully to: {dest}")
                    continue

                else:
                    print(f"Unknown internal command ':{cmd}'. Type :help for commands.")
                    continue

            # Execute real Linux command
            target_q = redo_target if redo_target is not None else session.current_q_num
            redo_target = None  # Reset redo target

            record = session.execute_question(raw_input, question_number=target_q)
            print(f"Captured → {record.screenshot}")

        except KeyboardInterrupt:
            print("\n(Press :exit or Ctrl+D to quit labshot)")
            redo_target = None
            continue
        except EOFError:
            print("\nExiting labshot. All screenshots and metadata saved.")
            break
        except Exception as e:
            print(f"Error: {e}")
            redo_target = None


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="labshot",
        description="Real Terminal Lab Screenshot Recorder for Linux university labs.",
    )
    parser.add_argument(
        "--lab",
        "-l",
        type=str,
        default="Essential Linux Commands",
        help="Name of the university lab (e.g. 'Essential Linux Commands')",
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
    export_parser.add_argument("--lab", "-l", type=str, default=None, help="Lab name to export")
    export_parser.add_argument("--out", "-o", type=str, default=None, help="Output destination folder")

    # Subcommand: list
    list_parser = subparsers.add_parser("list", help="List recorded questions for a lab")
    list_parser.add_argument("--lab", "-l", type=str, default=None, help="Lab name")

    # Subcommand: status
    status_parser = subparsers.add_parser("status", help="Show status of a lab session")
    status_parser.add_argument("--lab", "-l", type=str, default=None, help="Lab name")

    # Subcommand: redo
    redo_parser = subparsers.add_parser("redo", help="Re-take a specific question")
    redo_parser.add_argument("question_number", type=int, help="Question number to redo (e.g. 3)")
    redo_parser.add_argument("command", nargs="*", default=[], help="Optional command to execute directly")
    redo_parser.add_argument("--lab", "-l", type=str, default=None, help="Lab name")

    args = parser.parse_args()

    # Determine lab name
    lab_name = getattr(args, "lab", None) or "Essential Linux Commands"

    if args.subcommand == "export":
        storage = LabStorage(lab_name=lab_name)
        out_dir = Path(args.out) if args.out else None
        dest = storage.export_submission(target_dir=out_dir)
        print(f"Exported submission for '{lab_name}' to: {dest}")
        sys.exit(0)

    if args.subcommand == "list":
        storage = LabStorage(lab_name=lab_name)
        meta = storage.load_metadata()
        questions = meta.get("questions", [])
        print(f"\n--- Recorded Questions for {lab_name} ---")
        if not questions:
            print("  No questions recorded yet.\n")
        else:
            for q in questions:
                print(f"  Q{q['number']:<2} | Exit: {q['exit_code']} | Cmd: {q['command']:<25} | Shot: {q['screenshot']}")
            print()
        sys.exit(0)

    if args.subcommand == "status":
        storage = LabStorage(lab_name=lab_name)
        existing = storage.get_existing_question_numbers()
        print(f"\n--- Lab Status: {lab_name} ---")
        print(f"  Directory:           {storage.lab_dir}")
        print(f"  Completed Questions: {existing}")
        print(f"  Next Question:       Q{storage.get_next_question_number()}\n")
        sys.exit(0)

    # Launch interactive session
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
                print(f"Redo Q{q_num} completed: Captured → {rec.screenshot}")
                session.close()
                sys.exit(0)
            else:
                # Enter REPL with redo target preset
                print(f"Starting session to redo Question {q_num}...")

        run_repl(session)

    except KeyboardInterrupt:
        print("\nSession interrupted.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
