"""Unit tests for LabStorage and metadata management."""

import json
import tempfile
import unittest
from pathlib import Path

from labshot.storage import LabStorage, sanitize_folder_name, QuestionRecord


class TestLabStorage(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.lab_name = "Essential Linux Commands"
        self.storage = LabStorage(lab_name=self.lab_name, base_dir=self.base_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sanitize_folder_name(self):
        self.assertEqual(sanitize_folder_name("Essential Linux Commands"), "Essential-Linux-Commands")
        self.assertEqual(sanitize_folder_name("Lab 1: Basic Shell (v2.0)"), "Lab-1-Basic-Shell-v20")
        self.assertEqual(sanitize_folder_name("   Spaces   "), "Spaces")

    def test_directory_creation(self):
        self.assertTrue(self.storage.lab_dir.exists())
        self.assertTrue(self.storage.screenshots_dir.exists())
        self.assertTrue(self.storage.commands_dir.exists())

    def test_record_question_and_metadata(self):
        rec1 = self.storage.record_question(
            number=1,
            command="ls -la",
            exit_code=0,
            cwd_before="/home/student",
            cwd_after="/home/student",
        )
        self.assertEqual(rec1.number, 1)
        self.assertEqual(rec1.command, "ls -la")

        # Check command file
        cmd_file = self.storage.get_command_file_path(1)
        self.assertTrue(cmd_file.exists())
        self.assertEqual(cmd_file.read_text().strip(), "ls -la")

        # Check metadata
        meta = self.storage.load_metadata()
        self.assertEqual(meta["lab"], self.lab_name)
        self.assertEqual(len(meta["questions"]), 1)
        self.assertEqual(meta["questions"][0]["command"], "ls -la")
        self.assertEqual(meta["questions"][0]["exit_code"], 0)

    def test_question_sequencing_and_resume(self):
        self.assertEqual(self.storage.get_next_question_number(), 1)

        self.storage.record_question(1, "pwd", 0, "/home", "/home")
        self.assertEqual(self.storage.get_next_question_number(), 2)

        self.storage.record_question(2, "cd ..", 0, "/home/student", "/home")
        self.assertEqual(self.storage.get_next_question_number(), 3)
        self.assertEqual(self.storage.get_existing_question_numbers(), [1, 2])

    def test_redo_question_updates_existing(self):
        self.storage.record_question(1, "pwd", 0, "/home", "/home")
        self.storage.record_question(2, "ls", 0, "/home", "/home")

        # Redo question 1 with a modified command
        self.storage.record_question(1, "pwd -P", 0, "/home/student", "/home/student")

        meta = self.storage.load_metadata()
        self.assertEqual(len(meta["questions"]), 2)
        self.assertEqual(meta["questions"][0]["number"], 1)
        self.assertEqual(meta["questions"][0]["command"], "pwd -P")

        cmd_file = self.storage.get_command_file_path(1)
        self.assertEqual(cmd_file.read_text().strip(), "pwd -P")

    def test_export_submission(self):
        self.storage.record_question(1, "pwd", 0, "/home", "/home")
        self.storage.record_question(2, "ls -la", 0, "/home", "/home")

        # Create dummy screenshots
        shot1 = self.storage.get_screenshot_path(1)
        shot2 = self.storage.get_screenshot_path(2)
        shot1.write_bytes(b"\x89PNG\r\n\x1a\n" + b"dummy1")
        shot2.write_bytes(b"\x89PNG\r\n\x1a\n" + b"dummy2")

        sub_dir = self.storage.export_submission()
        self.assertTrue(sub_dir.exists())
        self.assertTrue((sub_dir / "q1.png").exists())
        self.assertTrue((sub_dir / "q2.png").exists())
        self.assertTrue((sub_dir / "commands.txt").exists())

        cmd_content = (sub_dir / "commands.txt").read_text()
        self.assertIn("Q1 > pwd", cmd_content)
        self.assertIn("Q2 > ls -la", cmd_content)


if __name__ == "__main__":
    unittest.main()
