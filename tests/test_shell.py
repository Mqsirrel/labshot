"""Unit and functional tests for persistent shell execution."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from labshot.config import LabConfig
from labshot.shell import PersistentShellController


class TestPersistentShell(unittest.TestCase):

    def setUp(self):
        self.lab_name = "Shell-Test"
        self.controller = PersistentShellController(lab_name=self.lab_name)

    def tearDown(self):
        self.controller.close()

    def test_persistent_execution_and_directory_tracking(self):
        self.controller.start()
        self.assertTrue(self.controller.is_running)

        # 1. Test pwd
        res1 = self.controller.execute("pwd")
        self.assertEqual(res1.exit_code, 0)
        initial_cwd = res1.cwd_after

        # 2. Test directory change
        test_dir = tempfile.mkdtemp(prefix="labshot_cd_test_")
        res2 = self.controller.execute(f"cd {test_dir}")
        self.assertEqual(res2.exit_code, 0)
        self.assertEqual(res2.cwd_after, test_dir)

        # 3. Test persistence of cd in next command
        res3 = self.controller.execute("pwd")
        self.assertEqual(res3.exit_code, 0)
        self.assertEqual(res3.cwd_after, test_dir)

        # 4. Test error exit code
        res4 = self.controller.execute("ls nonexistent_file_xyz_123")
        self.assertNotEqual(res4.exit_code, 0)

        # 5. Clean up directory
        self.controller.execute(f"cd {initial_cwd}")
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    unittest.main()
