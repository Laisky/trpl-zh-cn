"""Offline behavioral contracts for the eight dependency-updated chapter examples."""
import os
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(os.environ.get("BOOK_ROOT", Path(__file__).resolve().parents[1]))
CARGO = os.environ.get("CARGO", "cargo")
NAMES = [
    "listing-02-02", "listing-02-03", "listing-02-04", "listing-02-05",
    "listing-02-06", "no-listing-03-convert-string-to-number",
    "no-listing-04-looping", "no-listing-05-quitting",
]
BASE = ROOT / "listings/ch02-guessing-game-tutorial"
TARGET = Path(os.environ.get("TEST_BUILD_DIR", ROOT / "target/guessing-regressions"))


class GuessingExampleTests(unittest.TestCase):
    """GuessingExampleTests preserves each teaching stage's intended behavior."""
    @classmethod
    def setUpClass(cls):
        """setUpClass builds each example offline, retaining the intentional compiler error."""
        cls.builds = {}
        for name in NAMES:
            env = dict(os.environ, CARGO_TARGET_DIR=str(TARGET / name))
            result = subprocess.run(
                [CARGO, "build", "--locked", "--offline"],
                cwd=BASE / name, env=env, capture_output=True, text=True, timeout=90)
            cls.builds[name] = result
            if name != "listing-02-04" and result.returncode:
                raise AssertionError(name + "\n" + result.stderr)

    def run_example(self, name, value):
        """run_example supplies bounded input to the real compiled executable."""
        return subprocess.run([str(TARGET / name / "debug/guessing_game")],
                              input=value, capture_output=True, text=True, timeout=5)

    def test_compile_failure_is_the_documented_type_mismatch(self):
        """test_compile_failure_is_the_documented_type_mismatch prevents fixing teaching code."""
        result = self.builds["listing-02-04"]
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("E0308", result.stderr)
        self.assertIn("mismatched types", result.stderr)
        self.assertIn("guess.cmp", result.stderr)

    def test_intro_echo_and_secret_range(self):
        """test_intro_echo_and_secret_range checks the two early runnable examples."""
        for name in ["listing-02-02", "listing-02-03"]:
            with self.subTest(name=name):
                result = self.run_example(name, "42\n")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("You guessed: 42", result.stdout)
                if name == "listing-02-03":
                    number = int(re.search(r"secret number is: (\d+)", result.stdout)[1])
                    self.assertTrue(1 <= number <= 100)

    def test_parsed_one_shot_compares_and_rejects_invalid_input(self):
        """test_parsed_one_shot_compares_and_rejects_invalid_input preserves the parse lesson."""
        name = "no-listing-03-convert-string-to-number"
        for value, message in [("0\n", "Too small!"), ("101\n", "Too big!")]:
            result = self.run_example(name, value)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(message, result.stdout)
        result = self.run_example(name, "invalid\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Please type a number!", result.stderr)

    def test_intermediate_loop_keeps_running_after_a_win(self):
        """test_intermediate_loop_keeps_running_after_a_win preserves its missing-break lesson."""
        values = "".join(str(n) + "\n" for n in range(1, 101)) + "invalid\n"
        result = self.run_example("no-listing-04-looping", values)
        self.assertIn("You win!", result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Please type a number!", result.stderr)

    def test_quitting_stage_exits_on_a_win(self):
        """test_quitting_stage_exits_on_a_win verifies the newly introduced break."""
        values = "".join(str(n) + "\n" for n in range(1, 101))
        result = self.run_example("no-listing-05-quitting", values)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("You win!", result.stdout)

    def test_final_games_skip_invalid_guesses_then_exit(self):
        """test_final_games_skip_invalid_guesses_then_exit preserves error recovery."""
        values = "invalid\n0\n101\n" + "".join(str(n) + "\n" for n in range(1, 101))
        for name in ["listing-02-05", "listing-02-06"]:
            with self.subTest(name=name):
                result = self.run_example(name, values)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Too small!", result.stdout)
                self.assertIn("Too big!", result.stdout)
                self.assertIn("You win!", result.stdout)
                self.assertNotIn("You guessed: invalid", result.stdout)


if __name__ == "__main__":
    unittest.main()
