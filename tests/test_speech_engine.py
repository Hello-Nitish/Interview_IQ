import unittest
import os
import sys

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.speech_analytics import SpeechAnalyticsEngine
from utils.speech_engine import GoogleLocalSpeechEngine
from agents.voice_interview_agent import VoiceInterviewAgent

class TestSpeechAndVoiceEngine(unittest.TestCase):
    def test_filler_word_detection(self):
        text_with_fillers = "Um, basically we decided to, you know, deploy the model, and like, it worked."
        res = SpeechAnalyticsEngine.count_filler_words(text_with_fillers)
        self.assertGreater(res["total_fillers"], 0)
        self.assertIn("um", res["breakdown"])
        self.assertIn("basically", res["breakdown"])
        self.assertIn("like", res["breakdown"])
        self.assertFalse(res["is_clean"])

        clean_text = "We engineered an automated pipeline that processed transactions and reduced latency by fifteen percent."
        clean_res = SpeechAnalyticsEngine.count_filler_words(clean_text)
        self.assertEqual(clean_res["total_fillers"], 0)
        self.assertTrue(clean_res["is_clean"])

    def test_speaking_rate_calculation(self):
        # 30 words in 15 seconds = 120 WPM (Optimal)
        sample = "One two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty twenty-one twenty-two twenty-three twenty-four twenty-five twenty-six twenty-seven twenty-eight twenty-nine thirty"
        rate = SpeechAnalyticsEngine.calculate_speaking_rate(sample, duration_seconds=15.0)
        self.assertGreater(rate["wpm"], 100)
        self.assertIn("Optimal", rate["pacing_category"])

    def test_star_compliance_evaluation(self):
        star_response = (
            "During my internship at NexGen, the challenge was high checkout abandonment. "
            "My task was to identify friction points in the payment funnel. "
            "I conducted user session analyses and implemented a one-click checkout flow. "
            "As a result, conversion improved by fourteen percent across mobile users."
        )
        star = SpeechAnalyticsEngine.evaluate_star_compliance(star_response)
        self.assertEqual(star["star_score"], 100)
        self.assertTrue(star["is_well_structured"])
        self.assertIn("Situation", star["components_present"])
        self.assertIn("Task", star["components_present"])
        self.assertIn("Action", star["components_present"])
        self.assertIn("Result", star["components_present"])

        vague_response = "I really like working on products and teamwork."
        vague_star = SpeechAnalyticsEngine.evaluate_star_compliance(vague_response)
        self.assertLess(vague_star["star_score"], 50)
        self.assertFalse(vague_star["is_well_structured"])

    def test_browser_speech_html_generation(self):
        html = GoogleLocalSpeechEngine.generate_browser_speech_html("Hello candidate, welcome to your assessment.")
        self.assertIn("speechSynthesis", html)
        self.assertIn("SpeechSynthesisUtterance", html)

    def test_voice_agent_failsafe_turn(self):
        agent = VoiceInterviewAgent()
        turn = agent.start_interview({"candidate_name": "Aarav"}, {"role_title": "Product Manager"}, {})
        self.assertIn("interviewer_question", turn)
        self.assertIn("turn_number", turn)

if __name__ == "__main__":
    unittest.main()
