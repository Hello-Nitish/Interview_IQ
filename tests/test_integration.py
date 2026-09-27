import unittest
import os
import sys

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.database import DatabaseManager
from utils.pdf_exporter import PDFDossierExporter
from orchestrator.orchestrator import Orchestrator

class TestEndToEndPersistenceAndExport(unittest.TestCase):
    def test_e2e_session_lifecycle_with_pdf_export(self):
        orch = Orchestrator()
        # Mock feedback agent to return deterministic failsafe feedback instantly
        orch.feedback_agent.generate_unified_feedback = lambda fit, res, qb: orch.feedback_agent._generate_failsafe_unified_feedback(fit, res)
        session_id = orch.session_id

        # Populate realistic state
        orch.state["candidate_name"] = "Aarav Sharma"
        orch.state["round_number"] = 1
        orch.state["jd_data"] = {"role_title": "Associate Product Manager", "company_name": "GlobalTech"}
        orch.state["fit_data"] = {
            "candidate_details": {"name": "Aarav Sharma", "candidate_id": "DM274094", "stage": "MBA Final Year"},
            "technical_rating": {"technical_match_pct": 75.0},
            "experience_scoring": {"awarded_points": 8},
            "placement_readiness_score": 72.0,
            "decision_engine": {
                "final_decision": "SHORTLIST",
                "governing_rule_triggered": "Mandatory match benchmark >= 70%",
                "alternative_role_routing": "Junior Business Analyst"
            },
            "requirements_matrix": [
                {"requirement": "Product Roadmapping", "category": "Mandatory", "evidence_or_gap": "Present: Led agile sprint cycles", "status": "Matched"},
                {"requirement": "SQL & Data Warehousing", "category": "Mandatory", "evidence_or_gap": "Missing: No SQL database experience", "status": "Critical Gap"}
            ]
        }

        topic_checklist = [
            {"topic_name": "Product Roadmapping", "category": "Mandatory", "status": "Matched", "weight": 1.0},
            {"topic_name": "SQL & Data Warehousing", "category": "Mandatory", "status": "Gap", "weight": 2.0}
        ]
        orch.state["question_bank"] = {
            "topic_checklist": topic_checklist,
            "round_number": 1
        }

        # Generate Round 1 test using failsafe deterministic generator
        test_r1 = orch.online_test_agent._generate_failsafe_test(topic_checklist, "Associate Product Manager")
        orch.state["online_test"] = test_r1

        # Submit Round 1 with 18 correct answers (60%)
        answers_r1 = {}
        for idx, q in enumerate(test_r1["questions"]):
            if idx < 18:
                answers_r1[q["question_id"]] = q["correct_option"]
            else:
                answers_r1[q["question_id"]] = "A" if q["correct_option"] != "A" else "B"
        
        results_r1 = orch.submit_online_test(answers_r1)
        self.assertEqual(results_r1["score"], 18)
        self.assertEqual(results_r1["total_questions"], 30)

        # Verify Round 1 persisted in SQLite
        attempts = DatabaseManager.get_test_attempts(session_id)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["round_number"], 1)

        # Simulate Round 2
        orch.state["round_number"] = 2
        orch.state["round"] = 2
        test_r2 = orch.online_test_agent._generate_failsafe_test(topic_checklist, "Associate Product Manager")
        orch.state["online_test"] = test_r2

        # Submit Round 2 with 24 correct answers (80%)
        answers_r2 = {}
        for idx, q in enumerate(test_r2["questions"]):
            if idx < 24:
                answers_r2[q["question_id"]] = q["correct_option"]
            else:
                answers_r2[q["question_id"]] = "B" if q["correct_option"] != "B" else "C"

        results_r2 = orch.submit_online_test(answers_r2)
        self.assertEqual(results_r2["score"], 24)

        # Verify Round 2 persisted in SQLite & progression calculated
        comparison = DatabaseManager.get_round_comparison(session_id)
        self.assertTrue(comparison["has_history"])
        self.assertEqual(comparison["total_rounds"], 2)
        self.assertEqual(comparison["net_improvement_pct"], 20.0)

        # Generate PDF Dossier and verify contents
        pdf_bytes = PDFDossierExporter.generate_dossier_pdf(orch.state)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 2000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_curriculum_end_to_end_flow(self):
        """Validates end-to-end execution of Step 6: 7-Day Micro-Curriculum with database persistence."""
        from agents.micro_curriculum_agent import MicroCurriculumAgent

        user_id = DatabaseManager.get_or_create_user("E2E Curriculum Student")
        session_id = DatabaseManager.create_session(user_id, "E2E Curriculum Student", "Associate Product Manager")

        # 1. 7-Day Micro-Curriculum Generation
        curr_agent = MicroCurriculumAgent()
        plan = curr_agent.generate_curriculum(weak_topics=[{"topic": "SQL", "priority": "High"}])
        self.assertEqual(len(plan["days"]), 7)
        plan_id = DatabaseManager.save_curriculum_plan(session_id, plan)
        self.assertTrue(plan_id.startswith("plan_"))
        DatabaseManager.update_curriculum_progress(plan_id, ["sql_mosh"], days_completed=1)

        # 2. Verification from SQLite
        curr_saved = DatabaseManager.get_curriculum_plan(session_id)
        self.assertIsNotNone(curr_saved)
        self.assertEqual(curr_saved["days_completed"], 1)

if __name__ == "__main__":
    unittest.main()
