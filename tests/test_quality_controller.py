import unittest
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.quality_controller import MultiAgentQualityController, QualityAuditResult

class TestMultiAgentQualityController(unittest.TestCase):
    def setUp(self):
        self.qc = MultiAgentQualityController()

    def test_audit_resume_profile(self):
        # High quality profile
        complete_profile = {
            "candidate_name": "Nitin Sharma",
            "candidate_bio": {"name": "Nitin", "education": "B.Tech"},
            "skills": ["Python", "SQL", "Machine Learning", "FastAPI", "Docker", "AWS"],
            "projects": [
                {"title": "AI Platform", "impact": "Reduced inference latency by 45%"},
                {"title": "Data Pipeline", "metrics": "Processed 10M records daily"}
            ],
            "experience": [{"role": "Senior Engineer", "years": 4}],
            "challenge_areas": [
                {"area": "Distributed consensus scale", "reason": "Unquantified partition tolerance"}
            ]
        }
        res = self.qc.audit_resume_profile(complete_profile)
        self.assertTrue(res.passed)
        self.assertGreaterEqual(res.score, 70.0)
        self.assertIn("bio_completeness", res.metrics)

        # Incomplete profile
        sparse_profile = {"candidate_name": "Anonymous"}
        sparse_res = self.qc.audit_resume_profile(sparse_profile)
        self.assertFalse(sparse_res.passed)
        self.assertLess(sparse_res.score, 70.0)
        self.assertTrue(len(sparse_res.recommendations) > 0)

    def test_audit_fit_profile(self):
        fit_profile = {
            "placement_readiness_score": 82.5,
            "technical_rating": {
                "strict_match_percentage": 75.0,
                "total_mandatory_count": 8,
                "mandatory_matched_count": 6
            },
            "requirements_matrix": [
                {"requirement": "Python", "status": "Matched"},
                {"requirement": "SQL", "status": "Matched"},
                {"requirement": "Cloud Infrastructure", "status": "Matched"},
                {"requirement": "Docker", "status": "Matched"}
            ],
            "critical_gaps": [{"skill_or_area": "Kubernetes"}],
            "communication_profile": {"strengths": "Executive articulation"},
            "problem_solving": {"highlighted_project_name": "AI Pipeline"}
        }
        res = self.qc.audit_fit_profile(fit_profile)
        self.assertTrue(res.passed)
        self.assertGreaterEqual(res.score, 75.0)

    def test_audit_question_bank(self):
        qb = {
            "topic_checklist": [{"topic": f"Topic {i}"} for i in range(6)],
            "resume_based_questions": [{"question": "Q1"}],
            "technical_questions": [{"question": "Q2"}],
            "conceptual_questions": [{"question": "Q3"}],
            "problem_solving_questions": [{"question": "Q4"}],
            "behavioral_questions": [{"question": "Q5"}]
        }
        res = self.qc.audit_question_bank(qb)
        self.assertTrue(res.passed)
        self.assertEqual(res.metrics["active_dimensions"], "5/5")

    def test_audit_online_test(self):
        questions = []
        for i in range(30):
            questions.append({
                "question_id": i + 1,
                "question_text": f"Question {i+1}",
                "options": {"A": "Opt A", "B": "Opt B", "C": "Opt C", "D": "Opt D"},
                "correct_option": "A",
                "explanation": "Valid rationale."
            })
        test_obj = {"questions": questions}
        res = self.qc.audit_online_test(test_obj)
        self.assertTrue(res.passed)
        self.assertEqual(res.metrics["total_questions"], 30)

        # Less than 30 fails quality gate
        res_fail = self.qc.audit_online_test({"questions": questions[:15]})
        self.assertFalse(res_fail.passed)

    def test_audit_feedback_report(self):
        feedback = {
            "overall_readiness_score": 78.5,
            "readiness_level": "Competitive",
            "unified_topic_readiness": [
                {"topic": f"Topic {i}", "priority": "High Priority"} for i in range(8)
            ],
            "targeted_study_plan_next_48h": [
                {"topic": f"Topic {i}", "recommended_action": "Exercise"} for i in range(5)
            ]
        }
        res = self.qc.audit_feedback_report(feedback)
        self.assertTrue(res.passed)
        self.assertGreaterEqual(res.score, 70.0)

if __name__ == "__main__":
    unittest.main()
