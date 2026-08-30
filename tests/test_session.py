"""Unit tests for LabSession."""

import tempfile
import unittest
from pathlib import Path

from labshot.config import LabConfig
from labshot.session import LabSession
from labshot.storage import LabStorage


class TestLabSession(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.config = LabConfig(base_dir=self.base_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_session_initialization(self):
        session = LabSession(lab_name="Process Management", config=self.config)
        self.assertEqual(session.lab_name, "Process Management")
        self.assertEqual(session.storage.folder_name, "Process-Management")
        self.assertFalse(session.is_active())

    def test_status_dict(self):
        session = LabSession(lab_name="File Permissions", config=self.config)
        status = session.get_status()
        self.assertEqual(status["lab"], "File Permissions")
        self.assertEqual(status["next_question"], 1)
        self.assertEqual(status["total_completed"], 0)


if __name__ == "__main__":
    unittest.main()
