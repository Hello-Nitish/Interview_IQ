"""
Advanced Unit Tests for SpeechAnalyticsEngine and GoogleLocalSpeechEngine.
Verifies disfluency categorization, stutter detection, TTR lexical diversity,
chronological STAR sequence, active/passive voice, and acoustic signal inspection.
"""

import unittest
import io
import wave
import numpy as np

from utils.speech_analytics import SpeechAnalyticsEngine
from utils.speech_engine import GoogleLocalSpeechEngine


class TestSpeechAnalyticsAdvanced(unittest.TestCase):

    def test_stutter_and_categorized_fillers(self):
        """Verify stutters (token repetition) and non-lexical vs lexical fillers."""
        # "I I" is a stutter; "um" is non-lexical; "basically" is lexical crutch
        sample = "Um, I I basically wanted to, uh, explain the architecture."
        result = SpeechAnalyticsEngine.count_filler_words(sample)

        self.assertGreaterEqual(result["stutter_count"], 1)
        self.assertIn("I", [s.strip() for s in result["stutters_detected"]])
        self.assertGreaterEqual(result["non_lexical_count"], 2)  # "um", "uh"
        self.assertGreaterEqual(result["lexical_crutches_count"], 1)  # "basically"
        self.assertFalse(result["is_clean"])

    def test_lexical_diversity_ttr(self):
        """Verify Type-Token Ratio distinguishes rich from circular phrasing."""
        diverse_text = (
            "Our cross-functional agile engineering team spearheaded a scalable microservices "
            "architecture to drastically minimize transaction latency and optimize user conversion."
        )
        repetitive_text = (
            "The thing was a thing and the thing was the thing and the thing was a thing."
        )

        diverse_res = SpeechAnalyticsEngine.calculate_lexical_diversity(diverse_text)
        repetitive_res = SpeechAnalyticsEngine.calculate_lexical_diversity(repetitive_text)

        self.assertGreater(diverse_res["ttr"], 0.70)
        self.assertIn("High Vocabulary Richness", diverse_res["verdict"])

        self.assertLess(repetitive_res["ttr"], 0.55)
        self.assertIn("Repetitive Phrasing", repetitive_res["verdict"])

    def test_chronological_star_flow(self):
        """Verify chronological narrative progression (S -> T -> A -> R)."""
        chronological_text = (
            "When I was at my previous firm, our team was facing high customer churn. "
            "My responsibility was to uncover the core drop-off friction points. "
            "I developed an automated anomaly detection pipeline and implemented self-healing workflows. "
            "As a result, we achieved an eighteen percent reduction in churn."
        )
        scrambled_text = (
            "As a result, we achieved an eighteen percent reduction in churn. "
            "When I was at my previous firm, our team was facing high customer churn. "
            "I developed an automated anomaly detection pipeline."
        )

        chrono_res = SpeechAnalyticsEngine.evaluate_star_compliance(chronological_text)
        self.assertTrue(chrono_res["chronological_flow"])
        self.assertEqual(chrono_res["star_score"], 100)

        scrambled_res = SpeechAnalyticsEngine.evaluate_star_compliance(scrambled_text)
        self.assertFalse(scrambled_res["chronological_flow"])
        # Penalty applied for out-of-order sequence
        self.assertLess(scrambled_res["star_score"], 75)

    def test_active_vs_passive_voice(self):
        """Verify active executive voice detection vs passive expression."""
        active_text = (
            "I led the transformation initiative. I designed the cloud migration roadmap. "
            "I optimized our operational expenditure by thirty percent."
        )
        passive_text = (
            "The plan was implemented by the committee. Reports were written and changes were made."
        )

        active_res = SpeechAnalyticsEngine.evaluate_syntactic_style(active_text)
        passive_res = SpeechAnalyticsEngine.evaluate_syntactic_style(passive_text)

        self.assertGreater(active_res["active_voice_ratio"], 0.70)
        self.assertIn("Dominantly Active", active_res["voice_verdict"])

        self.assertLess(passive_res["active_voice_ratio"], 0.35)
        self.assertIn("Excessively Passive", passive_res["voice_verdict"])

    def test_comprehensive_verbal_analysis(self):
        """Verify composite diagnostic output contains all diagnostic pillars."""
        verbal_response = (
            "During my internship at Bain, we were facing delayed client reporting. "
            "My goal was to optimize the analytics workflow. "
            "I engineered a Python ETL pipeline and automated the MECE issue trees. "
            "As a result, delivery turnaround was improved by forty percent."
        )
        # 38 words in 18 seconds = ~127 WPM (Optimal Cadence)
        analysis = SpeechAnalyticsEngine.analyze_verbal_response(verbal_response, duration_seconds=18.0)

        self.assertIn("composite_delivery_score", analysis)
        self.assertGreaterEqual(analysis["composite_delivery_score"], 75.0)
        self.assertEqual(analysis["executive_presence_level"], "Strong")
        self.assertIn("lexical_diversity", analysis)
        self.assertIn("syntactic_style", analysis)
        self.assertIn("domain_fluency", analysis)
        self.assertIn("MECE", analysis["domain_fluency"]["terms_found"])

    def test_audio_quality_assessment(self):
        """Verify acoustic signal assessment on generated test audio."""
        # Synthesize 1-second 16-bit 16kHz sine wave audio
        sample_rate = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        # 440Hz tone with healthy amplitude
        audio_data = (np.sin(2 * np.pi * 440 * t) * 16000).astype(np.int16)

        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        wav_bytes = buf.getvalue()
        quality = GoogleLocalSpeechEngine.assess_audio_quality(wav_bytes)

        self.assertTrue(quality["valid"])
        self.assertAlmostEqual(quality["duration_seconds"], 1.0, delta=0.1)
        self.assertFalse(quality["is_silent"])
        self.assertFalse(quality["is_clipped"])
        self.assertEqual(quality["sample_rate"], 16000)

    def test_silent_audio_guard(self):
        """Verify silence detection when audio amplitude is zero."""
        sample_rate = 16000
        duration = 0.8
        silent_data = np.zeros(int(sample_rate * duration), dtype=np.int16)

        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(silent_data.tobytes())

        silent_bytes = buf.getvalue()
        quality = GoogleLocalSpeechEngine.assess_audio_quality(silent_bytes)

        self.assertTrue(quality["valid"])
        self.assertTrue(quality["is_silent"])


if __name__ == "__main__":
    unittest.main()
