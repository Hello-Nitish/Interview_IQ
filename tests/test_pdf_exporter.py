import unittest
import os
import sys

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.pdf_exporter import PDFDossierExporter

class TestPDFDossierExporter(unittest.TestCase):
    def test_generate_pdf_from_full_session(self):
        sample_state = {
            "session_id": "session_sample_123",
            "candidate_name": "Rohan Deshmukh",
            "round_number": 1,
            "jd_data": {"role_title": "Product Manager — FinTech"},
            "fit_data": {
                "technical_rating": {"technical_match_pct": 77.5},
                "experience_scoring": {"awarded_points": 8},
                "placement_readiness_score": 75.0,
                "decision_engine": {
                    "final_decision": "SHORTLIST",
                    "governing_rule_triggered": "Mandatory technical skills meet 75% threshold",
                    "alternative_role_routing": "Associate Product Manager"
                },
                "requirements_matrix": [
                    {
                        "requirement": "Financial API Architecture",
                        "category": "Mandatory",
                        "evidence_or_gap": "Present: Implemented REST APIs in FinTech project",
                        "status": "Matched"
                    },
                    {
                        "requirement": "Risk Modeling",
                        "category": "Mandatory",
                        "evidence_or_gap": "Missing: No quantitative risk modeling cited",
                        "status": "Critical Gap"
                    }
                ]
            },
            "test_results": {
                "score": 23,
                "total_questions": 30,
                "percentage": 76.7,
                "passed": True,
                "topic_accuracy": {
                    "Financial API Architecture": {"correct": 5, "total": 6, "percentage": 83.3},
                    "Risk Modeling": {"correct": 2, "total": 6, "percentage": 33.3}
                }
            },
            "feedback": {
                "overall_readiness_score": 77.0,
                "readiness_level": "High",
                "unified_topic_readiness": [
                    {
                        "topic": "Risk Modeling",
                        "readiness_status": "HIGH PRIORITY",
                        "primary_source": "Both (High Priority)",
                        "recommendation": "Complete quantitative credit risk case study."
                    }
                ],
                "targeted_study_plan_next_48h": [
                    {
                        "timeframe": "Hours 0-12",
                        "action_item": "Deep-dive into credit scoring formulas",
                        "practice_exercise": "Calculate Basel III capital adequacy ratio"
                    }
                ]
            }
        }

        pdf_bytes = PDFDossierExporter.generate_dossier_pdf(sample_state)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        # Check PDF Magic Header
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_generate_pdf_minimal_state(self):
        minimal_state = {"session_id": "session_empty_999"}
        pdf_bytes = PDFDossierExporter.generate_dossier_pdf(minimal_state)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_generate_fit_report_pdf_from_full_state(self):
        fit_data = {
            "candidate_details": {"name": "Aarav Sharma", "candidate_id": "DM982104", "target_role": "VP Product"},
            "technical_rating": {"technical_match_pct": 82.5},
            "experience_scoring": {"awarded_points": 9},
            "company_culture_fit": {"cultural_fit_score": 88.0},
            "placement_readiness_score": 84.0,
            "decision_engine": {
                "final_decision": "STRONG HIRE",
                "governing_rule_triggered": "Exceeds all tier 1 institutional benchmarks",
                "alternative_role_routing": "Director of Product"
            },
            "requirements_matrix": [
                {
                    "requirement": "Enterprise Cloud Architecture",
                    "category": "Mandatory",
                    "evidence_or_gap": "Direct experience running AWS/GCP at scale",
                    "status": "Matched"
                }
            ],
            "strategic_narrative": "Exceptional executive presence and robust technical grounding.",
            "critical_gaps": ["Deepen knowledge in financial risk quantification."]
        }
        pdf_bytes = PDFDossierExporter.generate_fit_report_pdf(
            fit_data=fit_data,
            candidate_name="Aarav Sharma",
            role_title="VP Product",
            company_name="Microsoft"
        )
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_generate_fit_report_pdf_minimal_state(self):
        pdf_bytes = PDFDossierExporter.generate_fit_report_pdf(fit_data={})
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

if __name__ == "__main__":
    unittest.main()
