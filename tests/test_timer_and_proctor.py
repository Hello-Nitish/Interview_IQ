import unittest
import os
import sys

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.online_test_agent import OnlineTestAgent

class TestTimerAndProctorEngine(unittest.TestCase):
    def setUp(self):
        self.agent = OnlineTestAgent()
        self.sample_checklist = [
            {"topic_name": "Agile Product Management", "category": "Mandatory", "status": "Matched", "weight": 1.0},
            {"topic_name": "SQL & Relational DB", "category": "Mandatory", "status": "Gap", "weight": 2.0}
        ]
        self.test_data = self.agent._generate_failsafe_test(self.sample_checklist, "Associate Product Manager")

    def test_exam_timer_html_component_exists(self):
        timer_path = os.path.join(project_root, "frontend", "components", "exam_timer.html")
        self.assertTrue(os.path.exists(timer_path), "exam_timer.html must exist")
        with open(timer_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Institutional Proctoring Engine", content)
        self.assertIn("countdown", content)
        self.assertIn("autoSubmit", content)

    def test_shuffle_preserves_question_count_and_options(self):
        original_count = len(self.test_data["questions"])
        shuffled = self.agent.shuffle_test_questions(self.test_data, seed=42)
        self.assertEqual(len(shuffled["questions"]), original_count)

        for q in shuffled["questions"]:
            self.assertIn("question_id", q)
            self.assertIn("options", q)
            self.assertEqual(len(q["options"]), 4)
            self.assertIn(q["correct_option"], ["A", "B", "C", "D"])

    def test_shuffle_maintains_auto_scoring_integrity(self):
        """Verify that perfect answer keys evaluate to 100% even after options are shuffled."""
        # Unshuffled perfect score
        perfect_original = {q["question_id"]: q["correct_option"] for q in self.test_data["questions"]}
        orig_score = self.agent.score_test(self.test_data, perfect_original)
        self.assertEqual(orig_score["percentage"], 100.0)

        # Shuffled perfect score
        shuffled = self.agent.shuffle_test_questions(self.test_data, seed=123)
        perfect_shuffled = {q["question_id"]: q["correct_option"] for q in shuffled["questions"]}
        shuffled_score = self.agent.score_test(shuffled, perfect_shuffled)
        self.assertEqual(shuffled_score["percentage"], 100.0)
        self.assertEqual(shuffled_score["score"], len(shuffled["questions"]))

if __name__ == "__main__":
    unittest.main()
