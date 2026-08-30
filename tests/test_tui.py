"""Unit and headless pilot tests for Labshot Textual TUI presentation layer."""

import tempfile
import unittest
from pathlib import Path

from labshot.config import LabConfig
from labshot.ui.app import LabshotApp
from labshot.ui.screens.home import HomeScreen
from labshot.ui.suggester import FishCommandSuggester, load_user_shell_histories
from labshot.ui.widgets.command_prompt import CommandPrompt
from labshot.ui.widgets.evidence_card import EvidenceCard
from labshot.ui.widgets.question_list import QuestionList, QuestionListItem


class TestTUIWidgetsAndScreens(unittest.IsolatedAsyncioTestCase):
    """Test suite for TUI components and decoupled state management."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.config = LabConfig(base_dir=self.base_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_app_instantiation_and_css(self):
        app = LabshotApp(lab_name="TUI Unit Test", config=self.config)
        self.assertEqual(app.initial_lab_name, "TUI Unit Test")
        self.assertTrue(len(app.CSS) > 100)

    def test_question_list_item_text(self):
        item_done = QuestionListItem(q_num=1, is_done=True, is_current=False, command="pwd")
        self.assertIn("✓", item_done._build_text())
        self.assertIn("pwd", item_done._build_text())

        item_active = QuestionListItem(q_num=2, is_done=False, is_current=True)
        self.assertIn("▶", item_active._build_text())

    def test_command_prompt_widget(self):
        prompt = CommandPrompt(placeholder="Test prompt")
        self.assertEqual(prompt.placeholder_text, "Test prompt")

    async def test_fish_suggester_completion(self):
        suggester = FishCommandSuggester(history=["mkdir my_special_lab"], load_system_shells=False)
        
        # Test common command completion
        res_ls = await suggester.get_suggestion("ls")
        self.assertEqual(res_ls, "ls -la")

        res_cd = await suggester.get_suggestion("cd")
        self.assertEqual(res_cd, "cd ..")

        # Test setup command completion
        res_setup = await suggester.get_suggestion("; c")
        self.assertEqual(res_setup, "; cd ..")

        # Test history priority
        res_hist = await suggester.get_suggestion("mkdir my_")
        self.assertEqual(res_hist, "mkdir my_special_lab")

    def test_load_user_shell_histories(self):
        hist = load_user_shell_histories(max_items=50)
        self.assertIsInstance(hist, list)

    async def test_app_home_screen_pilot(self):
        app = LabshotApp(config=self.config)
        async with app.run_test() as pilot:
            await pilot.pause()
            self.assertTrue(isinstance(app.screen, HomeScreen))
            # Verify widgets exist on mounted screen
            self.assertIsNotNone(app.screen.query_one("#home-title"))
            self.assertIsNotNone(app.screen.query_one("#btn-new"))
            self.assertIsNotNone(app.screen.query_one("#btn-resume"))

    async def test_evidence_card_mounted_lifecycle(self):
        app = LabshotApp(config=self.config)
        async with app.run_test() as pilot:
            ev = EvidenceCard()
            await app.screen.mount(ev)
            
            ev.set_running("pwd")
            self.assertEqual(ev.command_status, "running")

            ev.set_setup_success(cwd="~/Desktop")
            self.assertEqual(ev.command_status, "success")
            self.assertEqual(ev.screenshot_status, "none")

            ev.set_capturing()
            self.assertEqual(ev.screenshot_status, "capturing")

            fake_path = self.base_dir / "q1.png"
            ev.set_success(fake_path, exit_code=0)
            self.assertEqual(ev.command_status, "success")
            self.assertEqual(ev.screenshot_status, "success")
            self.assertEqual(ev.validation_status, "success")


if __name__ == "__main__":
    unittest.main()
