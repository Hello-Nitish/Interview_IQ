import unittest
import os
import sys
import json

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.session_manager import SessionManager
from agents.question_bank import QuestionBankAgent
from agents.online_test_agent import OnlineTestAgent
from agents.feedback_agent import FeedbackAgent
from orchestrator.orchestrator import Orchestrator

class TestInterviewIQFoundation(unittest.TestCase):
    def test_session_lifecycle(self):
        session_id = SessionManager.create_session("TestCandidate")
        self.assertTrue(session_id.startswith("session_"))
        
        state = SessionManager.load_session(session_id)
        self.assertEqual(state["candidate_name"], "TestCandidate")
        
        state["fit_data"] = {"placement_readiness_score": 85}
        SessionManager.save_session(session_id, state)
        
        reloaded = SessionManager.load_session(session_id)
        self.assertEqual(reloaded["fit_data"]["placement_readiness_score"], 85)

class TestQuestionBankAgent(unittest.TestCase):
    def setUp(self):
        self.agent = QuestionBankAgent()
        self.jd_profile = {
            "role_title": "Credit Research Analyst",
            "required_technical_skills": [
                {"skill": "Financial Modeling & DCF", "importance": "Mandatory"},
                {"skill": "Ratio Analysis & Cash Flow", "importance": "Mandatory"}
            ],
            "required_domain_competencies": ["Corporate Credit Rating", "Fixed Income Research"],
            "required_tools_and_frameworks": ["Advanced Excel", "Bloomberg Terminal"]
        }
        self.fit_analysis = {
            "requirements_matrix": [
                {"requirement": "Financial Modeling & DCF", "category": "Mandatory", "status": "Matched"},
                {"requirement": "Ratio Analysis & Cash Flow", "category": "Mandatory", "status": "Critical Gap"},
                {"requirement": "Corporate Credit Rating", "category": "Mandatory", "status": "Critical Gap"}
            ],
            "critical_gaps": [
                {"skill_or_area": "Ratio Analysis & Cash Flow", "strategic_advice": "Focus on cash flow debt coverage"}
            ]
        }
        self.resume_profile = {
            "summary_highlights": ["Pursuing MBA Finance", "B.Com graduate"]
        }

    def test_extract_topic_checklist(self):
        checklist = self.agent.extract_topic_checklist(self.jd_profile, self.fit_analysis)
        self.assertGreater(len(checklist), 0)
        topic_names = [t["topic_name"] for t in checklist]
        self.assertIn("Financial Modeling & DCF", topic_names)
        self.assertIn("Ratio Analysis & Cash Flow", topic_names)
        
        # Verify Gap status for Ratio Analysis
        ratio_topic = next(t for t in checklist if t["topic_name"] == "Ratio Analysis & Cash Flow")
        self.assertEqual(ratio_topic["status"], "Gap")
        self.assertEqual(ratio_topic["weight"], 2.0)

    def test_reweight_prioritized_topics(self):
        prioritized = ["Corporate Credit Rating"]
        checklist = self.agent.extract_topic_checklist(self.jd_profile, self.fit_analysis, prioritized_topics=prioritized)
        prio_topic = next(t for t in checklist if t["topic_name"] == "Corporate Credit Rating")
        self.assertEqual(prio_topic["weight"], 2.5)

    def test_question_bank_generation_and_coverage(self):
        # Using deterministic failsafe generation
        q_bank = self.agent._generate_failsafe_question_bank(
            self.resume_profile, self.jd_profile, self.fit_analysis,
            self.agent.extract_topic_checklist(self.jd_profile, self.fit_analysis)
        )
        cov = q_bank.get("coverage_summary", {})
        self.assertEqual(cov.get("coverage_percentage"), 100.0)
        self.assertEqual(cov.get("covered_topics"), cov.get("total_jd_topics"))
        self.assertGreater(cov.get("total_questions"), 0)

class TestOnlineTestAgent(unittest.TestCase):
    def setUp(self):
        self.agent = OnlineTestAgent()
        self.topic_checklist = [
            {"topic_name": "Financial Modeling & DCF", "category": "Mandatory", "status": "Matched", "weight": 1.0},
            {"topic_name": "Ratio Analysis & Cash Flow", "category": "Mandatory", "status": "Gap", "weight": 2.0},
            {"topic_name": "Corporate Credit Rating", "category": "Mandatory", "status": "Untested", "weight": 1.5}
        ]

    def test_generate_test_structure(self):
        test_data = self.agent._generate_failsafe_test(self.topic_checklist, "Credit Research Analyst")
        questions = test_data.get("questions", [])
        self.assertEqual(len(questions), 30)
        self.assertEqual(test_data.get("total_questions"), 30)
        self.assertEqual(test_data.get("passing_score_percentage"), 70)
        
        # Verify each question has 4 options and a correct option
        for q in questions:
            self.assertIn("question_id", q)
            self.assertIn("question_text", q)
            self.assertIn("options", q)
            self.assertEqual(len(q["options"]), 4)
            self.assertIn(q["correct_option"], ["A", "B", "C", "D"])
            self.assertTrue(len(q.get("explanation", "")) > 0)

    def test_score_test(self):
        test_data = self.agent._generate_failsafe_test(self.topic_checklist, "Credit Research Analyst")
        questions = test_data.get("questions", [])
        
        # All correct answers
        perfect_answers = {q["question_id"]: q["correct_option"] for q in questions}
        result = self.agent.score_test(test_data, perfect_answers)
        self.assertEqual(result["score"], 30)
        self.assertEqual(result["percentage"], 100.0)
        self.assertTrue(result["passed"])
        
        # Half correct
        half_answers = {}
        for idx, q in enumerate(questions):
            if idx < 15:
                half_answers[q["question_id"]] = q["correct_option"]
            else:
                wrong = "B" if q["correct_option"] != "B" else "C"
                half_answers[q["question_id"]] = wrong
        half_result = self.agent.score_test(test_data, half_answers)
        self.assertEqual(half_result["score"], 15)
        self.assertEqual(half_result["percentage"], 50.0)
        self.assertFalse(half_result["passed"])
        self.assertIn("topic_accuracy", half_result)

class TestFeedbackAgent(unittest.TestCase):
    def setUp(self):
        self.agent = FeedbackAgent()
        self.fit_data = {
            "placement_readiness_score": 60,
            "requirements_matrix": [
                {"requirement": "Financial Statement Analysis", "category": "Mandatory", "status": "Matched", "evidence_or_gap": "Strong project"},
                {"requirement": "Credit Stress Testing", "category": "Mandatory", "status": "Critical Gap", "evidence_or_gap": "No evidence"}
            ]
        }
        self.test_results = {
            "score": 18,
            "total_questions": 30,
            "percentage": 60.0,
            "passed": False,
            "topic_accuracy": {
                "Financial Statement Analysis": {"correct": 5, "total": 6, "percentage": 83.3},
                "Credit Stress Testing": {"correct": 1, "total": 5, "percentage": 20.0}
            }
        }

    def test_unified_topic_readiness_and_high_priority_flag(self):
        unified = self.agent.build_unified_topic_readiness(self.fit_data, self.test_results)
        self.assertGreater(len(unified), 0)
        
        # Credit Stress Testing is weak in both fit_data and test_results -> must be flagged HIGH PRIORITY
        stress_topic = next(t for t in unified if "Stress" in t["topic"])
        self.assertEqual(stress_topic["readiness_status"], "HIGH PRIORITY")
        self.assertEqual(stress_topic["primary_source"], "Both (High Priority)")

    def test_failsafe_feedback_synthesis(self):
        fb = self.agent._generate_failsafe_unified_feedback(self.fit_data, self.test_results)
        self.assertIn("overall_readiness_score", fb)
        self.assertIn("readiness_level", fb)
        self.assertIn("prioritized_topics_for_next_round", fb)
        self.assertIn("targeted_study_plan_next_48h", fb)
        self.assertTrue(any("Stress" in t for t in fb["prioritized_topics_for_next_round"]))

class TestClosedLoopOrchestration(unittest.TestCase):
    def test_round_progression(self):
        orch = Orchestrator()
        orch.state["round_number"] = 1
        orch.state["jd_profile"] = {
            "role_title": "Credit Research Analyst",
            "required_technical_skills": [{"skill": "Credit Stress Testing", "importance": "Mandatory"}]
        }
        orch.state["fit_data"] = {
            "placement_readiness_score": 50,
            "requirements_matrix": [
                {"requirement": "Credit Stress Testing", "category": "Mandatory", "status": "Critical Gap"}
            ]
        }
        orch.state["feedback"] = {
            "prioritized_topics_for_next_round": ["Credit Stress Testing"]
        }
        
        # Trigger next round with mocked test generation for deterministic fast execution
        orch.online_test_agent.generate_test = lambda **kwargs: {"test_id": "mock_t2", "questions": []}
        qb = orch.trigger_next_round()
        self.assertEqual(orch.state["round_number"], 2)
        self.assertIsNone(orch.state["test_results"])
        
        # Verify the question bank checklist has re-weighted the topic to 2.5x
        checklist = qb.get("topic_checklist", [])
        stress_topic = next(t for t in checklist if "Credit Stress Testing" in t["topic_name"])
        self.assertEqual(stress_topic["weight"], 2.5)

class TestDualModeOnboarding(unittest.TestCase):
    """
    Validates dual-mode candidate onboarding:
    1. 'strategic_only': Fast-track (5 stages), skips 30-MCQ online test calibration.
    2. 'complete': Full-pipeline (6 stages), calibrates 30-MCQ online test.
    """

    def setUp(self):
        self.orch = Orchestrator()
        # Mock sub-agents with deterministic mocks for instant offline execution
        self.orch.resume_agent.review_resume = lambda text: {
            "candidate_name": "Aarav Sharma",
            "skills": ["Financial Modeling", "Excel"],
            "education": [{"degree": "MBA"}]
        }
        self.orch.jd_agent.analyze_jd = lambda text: {
            "role_title": "Investment Banking Analyst",
            "company_name": "Goldman Sachs",
            "required_technical_skills": [{"skill": "DCF", "importance": "Mandatory"}]
        }
        self.orch.company_intel_agent.get_company_intelligence = lambda c, r: {
            "company_name": c,
            "core_values": ["Client Service", "Excellence"]
        }
        self.orch.fit_agent.analyze_fit = lambda res, jd: {
            "placement_readiness_score": 75.0,
            "technical_rating": {"technical_match_pct": 80.0},
            "requirements_matrix": [{"requirement": "DCF", "status": "Matched"}]
        }
        self.orch.qb_agent.generate_questions = lambda res, jd, fit: {
            "round_number": 1,
            "topic_checklist": [{"topic_name": "DCF", "category": "Mandatory", "status": "Matched", "weight": 1.0}],
            "technical_questions": [{"question": "What is DCF?"}]
        }
        self.orch.company_intel_agent.enrich_question_bank = lambda qb, intel: qb
        self.orch.online_test_agent.generate_test = lambda **kwargs: {
            "test_id": "test_mock_123",
            "questions": [{"question_id": 1, "question": "What is WACC?", "correct_option": "A"}]
        }

    def test_process_onboarding_strategic_only(self):
        """Validates Option 1: 5 stages executed, online_test is None, state sanitized."""
        stages_recorded = []
        def stage_cb(stage_num, total_stages, name, detail):
            stages_recorded.append((stage_num, total_stages, name))

        result = self.orch.process_onboarding(
            "Resume text here",
            "JD text here",
            stage_callback=stage_cb,
            mode="strategic_only"
        )

        self.assertEqual(len(stages_recorded), 5)
        self.assertTrue(all(total == 5 for _, total, _ in stages_recorded))
        self.assertIsNone(result["online_test"])
        self.assertEqual(result["analysis_mode"], "strategic_only")
        self.assertIsNone(self.orch.state.get("online_test"))
        self.assertIsNone(self.orch.state.get("test_results"))
        self.assertIsNotNone(self.orch.state.get("fit_data"))
        self.assertIsNotNone(self.orch.state.get("question_bank"))

    def test_process_onboarding_complete(self):
        """Validates Option 2: 6 stages executed, online_test is pre-calibrated."""
        stages_recorded = []
        def stage_cb(stage_num, total_stages, name, detail):
            stages_recorded.append((stage_num, total_stages, name))

        result = self.orch.process_onboarding(
            "Resume text here",
            "JD text here",
            stage_callback=stage_cb,
            mode="complete"
        )

        self.assertEqual(len(stages_recorded), 6)
        self.assertTrue(all(total == 6 for _, total, _ in stages_recorded))
        self.assertIsNotNone(result["online_test"])
        self.assertEqual(result["analysis_mode"], "complete")
        self.assertIsNotNone(self.orch.state.get("online_test"))

    def test_process_onboarding_mode_normalization(self):
        """Validates case-insensitivity, whitespace stripping, and fallback for mode."""
        res_upper = self.orch.process_onboarding("R", "J", mode=" STRATEGIC_ONLY ")
        self.assertEqual(res_upper["analysis_mode"], "strategic_only")
        self.assertIsNone(res_upper["online_test"])

        res_invalid = self.orch.process_onboarding("R", "J", mode="unknown_mode")
        self.assertEqual(res_invalid["analysis_mode"], "complete")
        self.assertIsNotNone(res_invalid["online_test"])

if __name__ == "__main__":
    unittest.main()


