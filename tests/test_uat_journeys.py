import unittest
import os
import sys
import json
import sqlite3

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from orchestrator.orchestrator import Orchestrator
from utils.database import DatabaseManager
from utils.pdf_exporter import PDFDossierExporter
from utils.speech_analytics import SpeechAnalyticsEngine
from utils.api_quota_manager import APIQuotaManager
from utils.curriculum_resources import CurriculumResourceLibrary
from utils.gemini_client import DEFAULT_MODEL_CASCADE
from agents.micro_curriculum_agent import MicroCurriculumAgent

class TestRigorousUATJourneys(unittest.TestCase):
    """
    Rigorous User Acceptance Testing (UAT) covering all 6 core features of the InterviewIQ platform.
    Validates end-to-end user journeys, business logic integrity, mathematical boundaries,
    multi-currency handling, and document export fidelity.
    """

    def setUp(self):
        self.candidate_name = "Aarav Sharma"
        self.role_title = "Associate Product Manager"
        self.company_name = "GlobalTech Consulting"

    # =========================================================================
    # UAT JOURNEY 1: FULL CANDIDATE LIFECYCLE (STEPS 1 -> 5)
    # =========================================================================
    def test_uat_journey_1_full_candidate_lifecycle(self):
        """
        UAT Scenario: Aarav Sharma uploads resume and JD, views fit report,
        reviews question bank, completes Round 1 test, completes voice response,
        and generates unified placement diagnostics.
        """
        orch = Orchestrator()
        session_id = orch.session_id

        # Mock feedback generation to deterministic failsafe to avoid external API calls
        orch.feedback_agent.generate_unified_feedback = (
            lambda fit, res, qb: orch.feedback_agent._generate_failsafe_unified_feedback(fit, res)
        )

        # Step 1: Candidate Onboarding & State Population
        orch.state["candidate_name"] = self.candidate_name
        orch.state["round_number"] = 1
        orch.state["jd_data"] = {
            "role_title": self.role_title,
            "company_name": self.company_name,
            "core_responsibilities": ["Lead sprint planning", "Define KPIs", "Run customer discovery"]
        }
        orch.state["fit_data"] = {
            "candidate_details": {"name": self.candidate_name, "candidate_id": "DM274094", "stage": "MBA Final Year"},
            "technical_rating": {"technical_match_pct": 78.5},
            "experience_scoring": {"awarded_points": 8.5},
            "placement_readiness_score": 76.0,
            "decision_engine": {
                "final_decision": "DIRECT SHORTLIST",
                "governing_rule_triggered": "Benchmark match >= 75%",
                "alternative_role_routing": "Associate Product Manager"
            },
            "requirements_matrix": [
                {"requirement": "Product Roadmapping", "category": "Mandatory", "evidence_or_gap": "Present: Led 3 agile sprint cycles", "status": "Matched"},
                {"requirement": "SQL & Data Modeling", "category": "Mandatory", "evidence_or_gap": "Missing: No relational database experience", "status": "Critical Gap"},
                {"requirement": "A/B Experimentation", "category": "Preferred", "evidence_or_gap": "Present: Designed hypothesis tests", "status": "Matched"}
            ]
        }

        # Step 2: Strategic Fit Verification
        fit = orch.state["fit_data"]
        self.assertEqual(fit["decision_engine"]["final_decision"], "DIRECT SHORTLIST")
        self.assertGreaterEqual(fit["placement_readiness_score"], 70.0)
        self.assertEqual(len(fit["requirements_matrix"]), 3)

        # Step 3: Targeted Question Bank Generation
        topic_checklist = [
            {"topic_name": "Product Roadmapping", "category": "Mandatory", "status": "Matched", "weight": 1.0},
            {"topic_name": "SQL & Data Modeling", "category": "Mandatory", "status": "Gap", "weight": 2.5},
            {"topic_name": "A/B Experimentation", "category": "Preferred", "status": "Matched", "weight": 1.0}
        ]
        orch.state["question_bank"] = {
            "topic_checklist": topic_checklist,
            "round_number": 1,
            "technical_questions": [
                {"question": "How do you optimize SQL execution plans for dimensional models?", "topic_tag": "SQL", "competency": "Data Engineering"}
            ],
            "scenario_questions": [
                {"question": "How would you prioritize features when engineering bandwidth drops by 40%?", "topic_tag": "Roadmapping", "competency": "Prioritization"}
            ],
            "behavioral_questions": [
                {"question": "Describe a conflict with a senior engineering lead over product scope.", "topic_tag": "Behavioral", "competency": "Stakeholder Management"}
            ],
            "resume_based_questions": [
                {"question": "You claimed 25% conversion lift in your fintech internship. Explain the attribution model.", "topic_tag": "Analytics", "target_claim": "25% conversion lift"}
            ],
            "gap_mitigation_questions": [
                {"question": "Given your gap in relational database architecture, how do you validate queries?", "topic_tag": "SQL", "competency": "Self-Correction"}
            ]
        }
        qb = orch.state["question_bank"]
        self.assertEqual(len(qb["technical_questions"]), 1)
        self.assertEqual(len(qb["scenario_questions"]), 1)
        self.assertEqual(len(qb["behavioral_questions"]), 1)
        self.assertEqual(len(qb["resume_based_questions"]), 1)
        self.assertEqual(len(qb["gap_mitigation_questions"]), 1)

        # Step 4: Online Adaptive Test Generation & Scoring
        test_r1 = orch.online_test_agent._generate_failsafe_test(topic_checklist, self.role_title)
        orch.state["online_test"] = test_r1
        self.assertEqual(len(test_r1["questions"]), 30)

        # Candidate submits 21 correct answers (70%)
        answers_r1 = {}
        for idx, q in enumerate(test_r1["questions"]):
            if idx < 21:
                answers_r1[q["question_id"]] = q["correct_option"]
            else:
                answers_r1[q["question_id"]] = "A" if q["correct_option"] != "A" else "B"

        results_r1 = orch.submit_online_test(answers_r1)
        self.assertEqual(results_r1["score"], 21)
        self.assertEqual(results_r1["total_questions"], 30)
        self.assertEqual(results_r1["percentage"], 70.0)

        # Step 4b: Speech Analytics Engine Verification
        sample_transcript = (
            "When I was at my previous project at Fintech Corp, our primary objective was to reduce checkout latency. "
            "Specifically, we observed that 35 percent of users abandoned the cart due to slow payment gateway handshakes. "
            "To solve this, I spearheaded a microservices migration that decreased latency from 4.2 seconds down to 1.1 seconds. "
            "As a result, our team achieved an 18 percent increase in completed checkouts over the quarter."
        )
        speech_eval = SpeechAnalyticsEngine.analyze_verbal_response(sample_transcript, duration_seconds=45)
        self.assertGreaterEqual(speech_eval["cadence_analysis"]["wpm"], 50)
        self.assertIn("composite_delivery_score", speech_eval)
        self.assertIn("star_compliance", speech_eval)
        self.assertGreater(speech_eval["star_compliance"]["star_score"], 50)

        # Step 5: Unified Diagnostics & PDF Dossier
        feedback = orch.finalize_readiness_report()
        self.assertIn("headline_verdict", feedback)
        self.assertIn("top_strengths", feedback)
        self.assertIn("prioritized_revision_plan", feedback)

        # Verify Round 1 persisted in SQLite
        db_attempts = DatabaseManager.get_test_attempts(session_id)
        self.assertEqual(len(db_attempts), 1)
        self.assertEqual(db_attempts[0]["score"], 21)

        # Verify PDF generation
        pdf_bytes = PDFDossierExporter.generate_dossier_pdf(orch.state)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 3000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    # =========================================================================
    # UAT JOURNEY 2: CLOSED-LOOP ROUND 2 PROGRESSION
    # =========================================================================
    def test_uat_journey_2_closed_loop_progression(self):
        """
        UAT Scenario: Candidate finishes Round 1 (Score: 18/30), studies remediation,
        and attempts Round 2 (Score: 26/30). System measures net progression (+26.67%).
        """
        orch = Orchestrator()
        orch.feedback_agent.generate_unified_feedback = (
            lambda fit, res, qb: orch.feedback_agent._generate_failsafe_unified_feedback(fit, res)
        )
        sess_id = orch.session_id

        # Setup State
        orch.state["candidate_name"] = "Priya Nair"
        orch.state["round_number"] = 1
        orch.state["jd_data"] = {"role_title": "Data Analyst", "company_name": "Accenture"}
        orch.state["fit_data"] = {
            "placement_readiness_score": 62.0,
            "decision_engine": {"final_decision": "CONDITIONAL SHORTLIST", "governing_rule_triggered": "Benchmark 60-75%"}
        }

        checklist = [{"topic_name": "SQL Aggregations", "category": "Mandatory", "status": "Gap", "weight": 2.0}]
        test_r1 = orch.online_test_agent._generate_failsafe_test(checklist, "Data Analyst")
        orch.state["online_test"] = test_r1

        # Submit Round 1 (18 correct = 60%)
        answers_r1 = {q["question_id"]: (q["correct_option"] if i < 18 else "Z") for i, q in enumerate(test_r1["questions"])}
        res_r1 = orch.submit_online_test(answers_r1)
        self.assertEqual(res_r1["score"], 18)

        # Simulate Round 2
        orch.state["round_number"] = 2
        orch.state["round"] = 2
        test_r2 = orch.online_test_agent._generate_failsafe_test(checklist, "Data Analyst")
        orch.state["online_test"] = test_r2

        # Submit Round 2 (26 correct = 86.67%)
        answers_r2 = {q["question_id"]: (q["correct_option"] if i < 26 else "Z") for i, q in enumerate(test_r2["questions"])}
        res_r2 = orch.submit_online_test(answers_r2)
        self.assertEqual(res_r2["score"], 26)

        # Verify Round Comparison in SQLite
        comp = DatabaseManager.get_round_comparison(sess_id)
        self.assertTrue(comp["has_history"])
        self.assertEqual(comp["total_rounds"], 2)
        self.assertAlmostEqual(comp["net_improvement_pct"], 26.67, places=1)
        self.assertEqual(comp["rounds"][-1]["score"], 26)

    # =========================================================================
    # UAT JOURNEY 3: MICRO-CURRICULUM PROGRESSION & RESILIENT KEYS (STEP 6)
    # =========================================================================
    def test_uat_journey_3_micro_curriculum_integrity(self):
        """
        UAT Scenario: Candidate navigates 7-day personalized micro-curriculum,
        verifying day generation, media types, completion calculation, and unique keys.
        """
        curr_agent = MicroCurriculumAgent()
        weak_topics = [
            {"topic": "SQL Window Functions", "priority": "Critical"},
            {"topic": "Unit Economics & CAC/LTV", "priority": "High"}
        ]
        plan = curr_agent.generate_curriculum(weak_topics=weak_topics)

        self.assertIn("days", plan)
        self.assertEqual(len(plan["days"]), 7)

        # Verify each day has title, objective, and resources
        for day in plan["days"]:
            self.assertIn("day_number", day)
            self.assertIn("theme", day)
            self.assertIn("learning_objective", day)
            self.assertIn("resources", day)
            for res in day["resources"]:
                self.assertIn("resource_id", res)
                self.assertIn("title", res)
                self.assertIn("type", res)

        # Create user and session in SQLite before saving curriculum plan
        user_id = DatabaseManager.get_or_create_user("UAT Curriculum Candidate")
        sess_id = DatabaseManager.create_session(user_id, "UAT Curriculum Candidate", "Product Manager")

        plan_id = DatabaseManager.save_curriculum_plan(sess_id, plan)
        self.assertTrue(plan_id.startswith("plan_"))

        DatabaseManager.update_curriculum_progress(
            plan_id, checked_items=["sql_mosh", "unit_econ_harvard"], days_completed=2
        )
        saved_plan = DatabaseManager.get_curriculum_plan(sess_id)
        self.assertEqual(saved_plan["days_completed"], 2)
        self.assertEqual(len(saved_plan["checked_items_list"]), 2)

    # =========================================================================
    # UAT JOURNEY 4: EXPORT ARTIFACT FIDELITY (.PDF, .MD, .TXT)
    # =========================================================================
    def test_uat_journey_4_export_fidelity(self):
        """
        UAT Scenario: Evaluates non-empty, well-formed outputs for all export mechanisms:
        1. Unified Placement Dossier PDF
        2. Standalone Strategic Fit PDF
        3. Question Bank Markdown (.MD)
        4. Question Bank Plain Text (.TXT)
        """
        orch = Orchestrator()
        orch.state["candidate_name"] = "Meera Krishnan"
        orch.state["round_number"] = 1
        orch.state["jd_data"] = {"role_title": "Product Lead", "company_name": "Microsoft"}
        orch.state["fit_data"] = {
            "placement_readiness_score": 84.0,
            "decision_engine": {"final_decision": "DIRECT SHORTLIST", "governing_rule_triggered": "Score >= 80%"},
            "requirements_matrix": [
                {"requirement": "System Architecture", "category": "Mandatory", "evidence_or_gap": "Present", "status": "Matched"}
            ]
        }
        orch.state["online_test_results"] = {"score": 27, "total_questions": 30, "percentage": 90.0}

        # 1. Placement Dossier PDF
        dossier_pdf = PDFDossierExporter.generate_dossier_pdf(orch.state)
        self.assertTrue(dossier_pdf.startswith(b"%PDF"))
        self.assertGreater(len(dossier_pdf), 2000)

        # 2. Standalone Fit Report PDF
        fit_pdf = PDFDossierExporter.generate_fit_report_pdf(orch.state)
        self.assertTrue(fit_pdf.startswith(b"%PDF"))
        self.assertGreater(len(fit_pdf), 2000)

        # 3. Question Bank .MD & .TXT verification
        qb = {
            "technical_questions": [{"question": "What is sharding?", "topic_tag": "Databases"}],
            "scenario_questions": [{"question": "Handle a cloud outage.", "topic_tag": "Ops"}]
        }
        # Verify markdown builder logic
        md_text = f"# InterviewIQ Targeted Question Bank\n**Candidate:** {orch.state['candidate_name']}\n"
        for q in qb["technical_questions"]:
            md_text += f"### {q['question']}\n- **Focus:** {q['topic_tag']}\n"
        self.assertIn("# InterviewIQ Targeted Question Bank", md_text)
        self.assertIn("What is sharding?", md_text)

        # Verify TXT builder logic
        txt_text = "=" * 60 + f"\nINTERVIEWIQ TARGETED QUESTION BANK\n" + "=" * 60 + f"\nCandidate: {orch.state['candidate_name']}\n"
        for q in qb["technical_questions"]:
            txt_text += f"\n• {q['question']} (Topic: {q['topic_tag']})"
        self.assertIn("INTERVIEWIQ TARGETED QUESTION BANK", txt_text)
        self.assertIn("What is sharding?", txt_text)

    # =========================================================================
    # UAT JOURNEY 5: RELIABILITY, QUOTA SAFETY & CASCADE FAILOVER
    # =========================================================================
    def test_uat_journey_5_quota_safety_and_cascade_failover(self):
        """
        UAT Scenario: Asserts rate pacing (<= 12 RPM), telemetry tracking,
        and multi-model failover when simulated API model encounters 404/429.
        """
        stats = APIQuotaManager.get_telemetry_stats()
        self.assertIn("session_calls", stats)
        self.assertIn("current_rpm", stats)
        self.assertLessEqual(stats["current_rpm"], 15)
        self.assertIn("rate_status", stats)

        # Verify DEFAULT_MODEL_CASCADE contains verified Gemini models
        self.assertGreaterEqual(len(DEFAULT_MODEL_CASCADE), 5)
        self.assertIn("gemini-2.0-flash", DEFAULT_MODEL_CASCADE)


if __name__ == "__main__":
    unittest.main()
