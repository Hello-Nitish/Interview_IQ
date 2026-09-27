import unittest
import os
import sys
import tempfile
import sqlite3

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.database import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        # Use a temporary database file for isolation
        self.orig_db_path = DatabaseManager.DB_PATH
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_interviewiq.db")
        DatabaseManager.DB_PATH = self.db_path
        DatabaseManager.init_db(force=True)

    def tearDown(self):
        DatabaseManager.DB_PATH = self.orig_db_path
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_user_creation_and_listing(self):
        user_id = DatabaseManager.get_or_create_user("Aarav Sharma", "aarav@example.com", "Product Management")
        self.assertTrue(user_id.startswith("usr_"))
        
        # Second call with same email should return existing ID
        user_id_2 = DatabaseManager.get_or_create_user("Aarav Sharma", "aarav@example.com")
        self.assertEqual(user_id, user_id_2)

        users = DatabaseManager.list_users()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["full_name"], "Aarav Sharma")

    def test_session_state_persistence(self):
        session_id = "session_test_001"
        sample_state = {
            "session_id": session_id,
            "candidate_name": "Priya Patel",
            "role_title": "Digital Transformation Lead",
            "round_number": 1,
            "fit_data": {
                "technical_rating": {"technical_match_pct": 82.5},
                "experience_scoring": {"awarded_points": 8},
                "decision_engine": {
                    "final_decision": "SHORTLIST",
                    "governing_rule_triggered": "Mandatory match > 80%"
                },
                "requirements_matrix": [
                    {"requirement": "Agile PM", "category": "Mandatory", "status": "Matched"}
                ]
            }
        }

        DatabaseManager.save_session_state(session_id, sample_state)
        reloaded = DatabaseManager.load_session_state(session_id)
        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded["candidate_name"], "Priya Patel")
        self.assertEqual(reloaded["fit_data"]["technical_rating"]["technical_match_pct"], 82.5)

        sessions = DatabaseManager.list_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["candidate_name"], "Priya Patel")

    def test_multi_round_attempts_and_comparison(self):
        session_id = "session_test_rounds"
        initial_state = {"session_id": session_id, "candidate_name": "Rahul Verma", "round_number": 1}
        DatabaseManager.save_session_state(session_id, initial_state)

        # Round 1: 18/30 (60%)
        test_data_r1 = {"questions": [{"id": 1}], "round_number": 1}
        results_r1 = {"score": 18, "total_questions": 30, "percentage": 60.0, "passed": False}
        DatabaseManager.record_test_attempt(session_id, 1, test_data_r1, results_r1)

        # Round 2: 24/30 (80%)
        test_data_r2 = {"questions": [{"id": 1}], "round_number": 2}
        results_r2 = {"score": 24, "total_questions": 30, "percentage": 80.0, "passed": True}
        DatabaseManager.record_test_attempt(session_id, 2, test_data_r2, results_r2)

        attempts = DatabaseManager.get_test_attempts(session_id)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0]["score"], 18)
        self.assertEqual(attempts[1]["score"], 24)

        comparison = DatabaseManager.get_round_comparison(session_id)
        self.assertTrue(comparison["has_history"])
        self.assertEqual(comparison["total_rounds"], 2)
        self.assertEqual(comparison["net_improvement_pct"], 20.0)

    def test_readiness_report_recording(self):
        session_id = "session_test_report"
        state = {"session_id": session_id, "candidate_name": "Sneha Roy"}
        DatabaseManager.save_session_state(session_id, state)

        feedback = {
            "overall_readiness_score": 78.5,
            "readiness_level": "High",
            "unified_topic_readiness": [{"topic": "Cloud", "readiness_status": "HIGH PRIORITY"}],
            "targeted_study_plan_next_48h": [{"step": "Study AWS"}],
            "prioritized_topics_for_next_round": ["Cloud"]
        }
        DatabaseManager.record_readiness_report(session_id, 1, feedback)

        report = DatabaseManager.get_latest_readiness_report(session_id)
        self.assertIsNotNone(report)
        self.assertEqual(report["composite_score"], 78.5)
        self.assertEqual(report["readiness_level"], "High")
        self.assertEqual(len(report["unified_matrix"]), 1)

if __name__ == "__main__":
    unittest.main()
