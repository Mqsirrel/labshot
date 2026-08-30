"""Comprehensive end-to-end integration and reliability tests for labshot."""

import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from labshot.config import LabConfig
from labshot.screenshot import verify_png_file
from labshot.session import LabSession
from labshot.storage import LabStorage


class TestLabshotIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.lab_name = "Essential Linux Commands"
        self.config = LabConfig(base_dir=self.base_dir, post_command_delay=0.1)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_full_cs345_workflow_and_20_commands(self):
        """Execute CS345 sequence + 20+ diverse commands in a single persistent session."""
        session = LabSession(lab_name=self.lab_name, config=self.config)
        session.start()
        self.assertTrue(session.is_active())

        test_proj_dir = Path(tempfile.mkdtemp(prefix="cs345_test_proj_"))

        commands = [
            # CS345 Core Sequence
            "ls -la",
            f"cd {test_proj_dir}",
            "mkdir projects",
            "pwd",
            "cd projects",
            "touch test.txt",
            "ls -la",
            "cd ..",
            "rmdir projects",
            # Additional Reliability & Edge Case Commands (Total > 20)
            "echo 'Hello CS345 Linux Lab!'",
            "echo $USER",
            "whoami",
            "uname -a",
            "date",
            "seq 1 30",                          # Multi-line output
            "ls /nonexistent_directory_error",   # Error exit code + stderr
            "mkdir -p a/b/c/d",                  # Nested directories (no output)
            "cd a/b/c/d",                        # Deep navigation
            "pwd",                               # Verify deep path
            "touch deep_file.txt",
            "echo 'CS345 deep test' > deep_file.txt",
            "cat deep_file.txt",
            "cd ../../../..",                    # Relative back-navigation
            "pwd",                               # Verify return
            "rm -rf a",                          # Recursive cleanup
            "python3 -c 'import sys; sys.exit(42)'", # Non-zero exit code 42
        ]

        records = []
        for i, cmd in enumerate(commands, start=1):
            rec = session.execute_question(cmd)
            self.assertEqual(rec.number, i)
            self.assertEqual(rec.command, cmd)
            records.append(rec)

            # Verify screenshot existence and PNG header validity
            shot_file = session.storage.get_screenshot_path(i)
            self.assertTrue(shot_file.exists(), f"Missing screenshot for Q{i}")
            self.assertTrue(verify_png_file(shot_file), f"Invalid PNG for Q{i}")
            self.assertGreater(shot_file.stat().st_size, 1000, f"Screenshot too small for Q{i}")

            # Verify command file
            cmd_file = session.storage.get_command_file_path(i)
            self.assertTrue(cmd_file.exists(), f"Missing command file for Q{i}")
            self.assertEqual(cmd_file.read_text().strip(), cmd)

        session.close()

        # Verify metadata
        meta = session.storage.load_metadata()
        self.assertEqual(len(meta["questions"]), len(commands))
        self.assertEqual(meta["questions"][15]["exit_code"], 2)  # ls error code
        self.assertEqual(meta["questions"][25]["exit_code"], 42) # python exit 42

        # Test Session Resume
        session2 = LabSession(lab_name=self.lab_name, config=self.config)
        session2.start()
        self.assertEqual(session2.current_q_num, len(commands) + 1)

        # Run 1 more command in resumed session
        next_rec = session2.execute_question("echo 'Resumed session working!'")
        self.assertEqual(next_rec.number, len(commands) + 1)
        session2.close()

        # Test Redo Question 3
        session3 = LabSession(lab_name=self.lab_name, config=self.config)
        session3.start()
        redo_rec = session3.redo_question(question_number=3, command="echo 'Redone Question 3'")
        self.assertEqual(redo_rec.number, 3)
        self.assertEqual(redo_rec.command, "echo 'Redone Question 3'")

        shot3 = session3.storage.get_screenshot_path(3)
        self.assertTrue(verify_png_file(shot3))
        cmd3 = session3.storage.get_command_file_path(3)
        self.assertEqual(cmd3.read_text().strip(), "echo 'Redone Question 3'")

        # Test Export
        sub_dir = session3.export()
        self.assertTrue(sub_dir.exists())
        self.assertTrue((sub_dir / "q1.png").exists())
        self.assertTrue((sub_dir / "commands.txt").exists())

        session3.close()
        shutil.rmtree(test_proj_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
