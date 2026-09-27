import unittest
import os
import sys

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.company_intel_agent import CompanyIntelAgent

class TestCompanyIntelAgent(unittest.TestCase):
    def setUp(self):
        self.agent = CompanyIntelAgent()

    def test_curated_amazon_profile(self):
        intel = self.agent.get_company_intelligence("Amazon")
        self.assertEqual(intel["canonical_name"], "Amazon")
        self.assertIn("16 Amazon Leadership Principles", intel["evaluation_framework"])
        principles = [p["name"] for p in intel["core_principles"]]
        self.assertIn("Customer Obsession", principles)
        self.assertIn("Bias for Action", principles)
        self.assertIn("Dive Deep", principles)
        self.assertGreaterEqual(len(intel["authentic_behavioral_probes"]), 3)
        self.assertIn("Customer Centricity", intel["cultural_radar_weights"])

    def test_curated_google_profile_and_alias(self):
        intel = self.agent.get_company_intelligence("Alphabet Inc / Google Cloud")
        self.assertEqual(intel["canonical_name"], "Google")
        self.assertIn("Googleyness", intel["evaluation_framework"])
        principles = [p["name"] for p in intel["core_principles"]]
        self.assertIn("Googleyness", principles)
        self.assertIn("General Cognitive Ability (GCA)", principles)

    def test_curated_mckinsey_and_consulting_alias(self):
        intel = self.agent.get_company_intelligence("McKinsey & Company")
        self.assertEqual(intel["canonical_name"], "McKinsey & Company")
        self.assertIn("Personal Experience Interview (PEI)", intel["evaluation_framework"])
        principles = [p["name"] for p in intel["core_principles"]]
        self.assertIn("Personal Impact", principles)
        self.assertIn("Hypothesis-Driven Problem Solving", principles)

        # Alias test: BCG
        bcg_intel = self.agent.get_company_intelligence("BCG Strategy Group")
        self.assertEqual(bcg_intel["canonical_name"], "McKinsey & Company")

    def test_curated_finance_and_alias(self):
        intel = self.agent.get_company_intelligence("Goldman Sachs")
        self.assertEqual(intel["canonical_name"], "Goldman Sachs")
        principles = [p["name"] for p in intel["core_principles"]]
        self.assertIn("Downside Risk Consciousness", principles)

        # Alias test: J.P. Morgan
        jpm_intel = self.agent.get_company_intelligence("JPMorgan Chase")
        self.assertEqual(jpm_intel["canonical_name"], "Goldman Sachs")

    def test_dynamic_fallback_for_unindexed_firm(self):
        intel = self.agent.get_company_intelligence("NexGen Digital Solutions Ltd")
        self.assertIn("NexGen", intel["canonical_name"])
        self.assertIn("core_principles", intel)
        self.assertGreater(len(intel["core_principles"]), 0)
        self.assertIn("authentic_behavioral_probes", intel)
        self.assertIn("cultural_radar_weights", intel)

    def test_enrich_question_bank(self):
        mock_qb = {
            "behavioral_questions": [
                {
                    "question": "Tell me about a time you handled conflict.",
                    "topics_covered": ["Conflict Resolution"],
                    "priority": "Medium"
                }
            ]
        }
        amazon_intel = self.agent.get_company_intelligence("Amazon")
        enriched = self.agent.enrich_question_bank(mock_qb, amazon_intel)

        self.assertIn("company_intelligence", enriched)
        self.assertEqual(enriched["company_intelligence"]["company_name"], "Amazon")
        # Ensure authentic probes were prepended
        first_q = enriched["behavioral_questions"][0]["question"]
        self.assertIn("[Amazon •", first_q)
        # Original question should still be present
        all_q_texts = [q["question"] for q in enriched["behavioral_questions"]]
        self.assertIn("Tell me about a time you handled conflict.", all_q_texts)

if __name__ == "__main__":
    unittest.main()
