"""
Unit Tests for DomainVocabularyCorrector in InterviewIQ.
Verifies phonetic confusion correction, acronym collapse, and domain density scoring.
"""

import unittest
from utils.domain_vocabulary import DomainVocabularyCorrector


class TestDomainVocabularyCorrector(unittest.TestCase):

    def test_consulting_phonetic_corrections(self):
        """Verify consulting and finance terms are accurately repaired."""
        raw = "We used a macy framework to analyze their ebita and piano margins."
        result = DomainVocabularyCorrector.correct_transcription(raw)
        corrected = result["corrected"]

        self.assertIn("MECE", corrected)
        self.assertIn("EBITDA", corrected)
        self.assertIn("P&L", corrected)
        self.assertTrue(len(result["corrections_applied"]) >= 3)
        self.assertTrue(result["domain_density_pct"] > 0)

    def test_tech_and_cloud_corrections(self):
        """Verify technology and data stack terms are accurately repaired."""
        raw = "I wrote sequel queries and deployed models with pi torch on cuber netties."
        result = DomainVocabularyCorrector.correct_transcription(raw)
        corrected = result["corrected"]

        self.assertIn("SQL", corrected)
        self.assertIn("PyTorch", corrected)
        self.assertIn("Kubernetes", corrected)

    def test_spelled_out_acronym_collapse(self):
        """Verify spaced out letters like 'k p i' collapse into 'KPI'."""
        raw = "Our primary k p i was to optimize the c a c and grow our a r r."
        result = DomainVocabularyCorrector.correct_transcription(raw)
        corrected = result["corrected"]

        self.assertIn("KPI", corrected)
        self.assertIn("CAC", corrected)
        self.assertIn("ARR", corrected)

    def test_firm_names_corrections(self):
        """Verify consulting and tech firm names are capitalized and corrected."""
        raw = "I interviewed with mac kinsey and b c g for strategy consulting."
        result = DomainVocabularyCorrector.correct_transcription(raw)
        corrected = result["corrected"]

        self.assertIn("McKinsey", corrected)
        self.assertIn("BCG", corrected)

    def test_domain_density_scoring(self):
        """Verify domain density calculation reflects technical depth."""
        dense_text = "In my agile sprint we tracked OKRs, optimized user story velocity, and improved CAC and LTV."
        light_text = "The quick brown fox jumps over the lazy dog."

        dense_score = DomainVocabularyCorrector.calculate_domain_density(dense_text)
        light_score = DomainVocabularyCorrector.calculate_domain_density(light_text)

        self.assertTrue(dense_score > 10.0)
        self.assertEqual(light_score, 0.0)

    def test_empty_or_whitespace_input(self):
        """Verify graceful handling of empty or blank transcripts."""
        result = DomainVocabularyCorrector.correct_transcription("")
        self.assertEqual(result["corrected"], "")
        self.assertEqual(result["domain_terms_found"], [])
        self.assertEqual(result["domain_density_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
