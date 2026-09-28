import unittest
import os
import sys

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from streamlit.testing.v1 import AppTest

class TestRigorousUATStreamlitApp(unittest.TestCase):
    """
    Rigorous Streamlit AppTest UAT Suite.
    Directly mounts and simulates frontend/app.py through the Streamlit engine,
    validating widget stability, zero exceptions, reactive state updates, and export actions.
    """

    def setUp(self):
        self.app_path = os.path.abspath(os.path.join(project_root, "frontend", "app.py"))

    def test_uat_page_01_onboarding_initial_render(self):
        """Validates Step 1 Onboarding page initial render and sidebar widgets."""
        at = AppTest.from_file(self.app_path, default_timeout=60)
        at.run()

        # Must have zero runtime exceptions
        self.assertEqual(len(at.exception), 0, f"AppTest encountered exceptions: {at.exception}")

        # Verify sidebar navigation buttons exist
        button_labels = [b.label for b in at.button]
        self.assertTrue(any("Candidate Onboarding" in lbl for lbl in button_labels))
        self.assertTrue(any("Prep Curriculum" in lbl for lbl in button_labels))

        # If environment pre-loaded an API key, clear it to verify gatekeeper render
        if not any("Validate & Activate Key" in lbl for lbl in button_labels):
            at.session_state["custom_api_key"] = ""
            at.session_state.orchestrator.set_api_key(None)
            at.run()
            button_labels = [b.label for b in at.button]

        # Verify gatekeeper activates when no API key is present
        self.assertTrue(any("Validate & Activate Key" in lbl for lbl in button_labels), f"Expected gatekeeper in {button_labels}")

        # Now simulate authenticated state with active API key
        at.session_state["custom_api_key"] = "AIzaSyTestKeyForStreamlitUAT"
        at.session_state.orchestrator.set_api_key("AIzaSyTestKeyForStreamlitUAT")
        at.run()

        # Verify dual onboarding execution mode buttons and demo triggers exist
        auth_button_labels = [b.label for b in at.button]
        self.assertTrue(any("Strategic Fit & Question Bank Alone" in lbl for lbl in auth_button_labels), f"Expected strategic alone button in {auth_button_labels}")
        self.assertTrue(any("Complete Analysis" in lbl for lbl in auth_button_labels), f"Expected complete analysis button in {auth_button_labels}")
        self.assertTrue(any("Load Demo" in lbl for lbl in auth_button_labels), f"Expected demo buttons in {auth_button_labels}")

    def test_uat_page_02_strategic_fit_report_render(self):
        """Validates Step 2 Strategic Fit Report UI and download elements."""
        at = AppTest.from_file(self.app_path, default_timeout=60)
        at.run()

        # Seed realistic fit data into session state
        orch = at.session_state.orchestrator
        orch.state["candidate_name"] = "Aarav Sharma"
        orch.state["round_number"] = 1
        orch.state["jd_data"] = {"role_title": "Associate Product Manager", "company_name": "GlobalTech"}
        orch.state["fit_data"] = {
            "placement_readiness_score": 78.0,
            "decision_engine": {"final_decision": "DIRECT SHORTLIST", "governing_rule_triggered": "Score >= 75%"},
            "technical_rating": {"technical_match_pct": 82.0},
            "experience_scoring": {"awarded_points": 8.0},
            "requirements_matrix": [
                {"requirement": "Product Roadmapping", "category": "Mandatory", "evidence_or_gap": "Present", "status": "Matched"},
                {"requirement": "SQL Analytics", "category": "Mandatory", "evidence_or_gap": "Missing", "status": "Critical Gap"}
            ]
        }
        at.session_state["current_page"] = "02_fit_report"
        at.run()

        self.assertEqual(len(at.exception), 0, f"Exceptions on Step 2: {at.exception}")
        # Verify download fit report and dossier buttons exist
        dl_labels = [str(d.label) for d in at.download_button]
        self.assertTrue(any("Fit Report" in lbl for lbl in dl_labels), f"Expected Fit Report in {dl_labels}")
        self.assertTrue(any("Dossier" in lbl for lbl in dl_labels), f"Expected Dossier in {dl_labels}")

    def test_uat_page_03_question_bank_dual_exports(self):
        """Validates Step 3 Targeted Question Bank and dual .MD & .TXT export buttons."""
        at = AppTest.from_file(self.app_path, default_timeout=60)
        at.run()

        orch = at.session_state.orchestrator
        orch.state["candidate_name"] = "Aarav Sharma"
        orch.state["jd_data"] = {"role_title": "Associate Product Manager", "company_name": "GlobalTech"}
        orch.state["question_bank"] = {
            "round_number": 1,
            "topic_checklist": [{"topic_name": "Product Roadmapping", "category": "Mandatory", "status": "Matched", "weight": 1.0}],
            "technical_questions": [{"question": "Explain database indexing.", "topic_tag": "SQL", "competency": "Data"}],
            "scenario_questions": [{"question": "How do you manage sprint scope creep?", "topic_tag": "Agile"}],
            "behavioral_questions": [{"question": "Describe a conflict resolution.", "topic_tag": "Leadership"}],
            "resume_based_questions": [{"question": "Detail your fintech internship.", "topic_tag": "Fintech"}],
            "gap_mitigation_questions": [{"question": "How will you master SQL?", "topic_tag": "Databases"}]
        }
        at.session_state["current_page"] = "03_question_bank"
        at.run()

        self.assertEqual(len(at.exception), 0, f"Exceptions on Step 3: {at.exception}")
        dl_labels = [str(d.label) for d in at.download_button]
        self.assertTrue(any(".MD" in lbl for lbl in dl_labels), "Expected .MD export button")
        self.assertTrue(any(".TXT" in lbl for lbl in dl_labels), "Expected .TXT export button")

    def test_uat_page_04_unseeded_direct_render(self):
        """Validates Step 4 unseeded direct mount renders prompt with zero exceptions (bug regression test)."""
        at = AppTest.from_file(self.app_path, default_timeout=60)
        at.run()
        at.session_state["current_page"] = "04_online_test"
        at.run()
        self.assertEqual(len(at.exception), 0, f"Exceptions on unseeded Step 4: {at.exception}")

    def test_uat_page_03_proceed_to_step4_transition(self):
        """Validates Step 3 proceed button synthesizes test data if missing and navigates to Step 4."""
        at = AppTest.from_file(self.app_path, default_timeout=60)
        at.run()

        orch = at.session_state.orchestrator
        orch.state["candidate_name"] = "Aarav Sharma"
        orch.state["jd_data"] = {"role_title": "APM", "company_name": "GlobalTech"}
        checklist = [{"topic_name": "SQL", "category": "Mandatory", "status": "Matched", "weight": 1.0}]
        orch.state["question_bank"] = {
            "round_number": 1,
            "topic_checklist": checklist,
            "technical_questions": [],
            "scenario_questions": [],
            "behavioral_questions": [],
            "resume_based_questions": [],
            "gap_mitigation_questions": []
        }
        orch.online_test_agent.generate_test = lambda **kwargs: orch.online_test_agent._generate_failsafe_test(checklist, "APM")
        at.session_state["current_page"] = "03_question_bank"
        at.run()

        proceed_btn = [b for b in at.button if b.key == "proceed_step4_btn"][0]
        proceed_btn.click().run()

        self.assertEqual(at.session_state["current_page"], "04_online_test")
        self.assertEqual(len(at.exception), 0, f"Exceptions during Step 3->4 proceed: {at.exception}")

    def test_uat_page_04_online_test_and_voice_bridge(self):
        """Validates Step 4 Online Test UI and submit button."""
        at = AppTest.from_file(self.app_path, default_timeout=60)
        at.run()

        orch = at.session_state.orchestrator
        orch.state["candidate_name"] = "Aarav Sharma"
        orch.state["round_number"] = 1
        orch.state["jd_data"] = {"role_title": "APM", "company_name": "GlobalTech"}
        checklist = [{"topic_name": "Roadmapping", "category": "Mandatory", "status": "Matched", "weight": 1.0}]
        orch.state["online_test"] = orch.online_test_agent._generate_failsafe_test(checklist, "APM")
        at.session_state["current_page"] = "04_online_test"
        at.run()

        self.assertEqual(len(at.exception), 0, f"Exceptions on Step 4: {at.exception}")
        btn_labels = [str(b.label) for b in at.button]
        self.assertTrue(any("Submit Exam" in lbl for lbl in btn_labels), f"Expected Submit Exam in {btn_labels}")

    def test_uat_page_04_exam_submission_and_step5_transition(self):
        """Validates submitting 30-MCQ exam, scoring persistence, and transitioning to Step 5."""
        at = AppTest.from_file(self.app_path, default_timeout=60)
        at.run()

        orch = at.session_state.orchestrator
        orch.state["candidate_name"] = "Aarav Sharma"
        orch.state["round_number"] = 1
        orch.state["jd_data"] = {"role_title": "APM", "company_name": "GlobalTech"}
        orch.state["fit_data"] = {
            "placement_readiness_score": 78.0,
            "decision_engine": {"final_decision": "DIRECT SHORTLIST"},
            "requirements_matrix": []
        }
        checklist = [{"topic_name": "SQL", "category": "Mandatory", "status": "Matched", "weight": 1.0}]
        orch.state["online_test"] = orch.online_test_agent._generate_failsafe_test(checklist, "APM")
        orch.feedback_agent.generate_unified_feedback = lambda fit, res, qb: orch.feedback_agent._generate_failsafe_unified_feedback(fit, res)
        at.session_state["current_page"] = "04_online_test"
        at.run()

        submit_btn = [b for b in at.button if "Submit Exam" in (b.label or "")][0]
        submit_btn.click().run()

        self.assertEqual(len(at.exception), 0, f"Exceptions after exam submission: {at.exception}")
        self.assertTrue("test_results" in orch.state)

        # Transition to Step 5
        view_feedback_btn = [b for b in at.button if b.key == "view_unified_feedback_btn"][0]
        view_feedback_btn.click().run()

        self.assertEqual(at.session_state["current_page"], "05_results")
        self.assertEqual(len(at.exception), 0, f"Exceptions navigating to Step 5: {at.exception}")

    def test_uat_page_05_unified_diagnostics(self):
        """Validates Step 5 Unified Diagnostics and Dossier PDF export."""
        at = AppTest.from_file(self.app_path, default_timeout=60)
        at.run()

        orch = at.session_state.orchestrator
        orch.state["candidate_name"] = "Aarav Sharma"
        orch.state["fit_data"] = {"placement_readiness_score": 75.0, "decision_engine": {"final_decision": "DIRECT SHORTLIST"}}
        orch.state["test_results"] = {"score": 22, "total_questions": 30, "percentage": 73.3}
        orch.state["feedback"] = {
            "headline_verdict": "Candidate scored 73.3% across examination.",
            "overall_readiness_score": 75.0,
            "readiness_level": "High Competence",
            "top_strengths": ["Structured problem solving"],
            "unified_topic_readiness": [],
            "targeted_study_plan_next_48h": []
        }
        at.session_state["current_page"] = "05_results"
        at.run()

        self.assertEqual(len(at.exception), 0, f"Exceptions on Step 5: {at.exception}")
        dl_labels = [str(d.label) for d in at.download_button]
        self.assertTrue(any("Full Dossier" in lbl or "Dossier" in lbl for lbl in dl_labels), f"Expected Dossier in {dl_labels}")

    def test_uat_page_05_to_step6_and_shortcuts(self):
        """Validates transitioning from Step 5 to Step 6, and Day 6/7 drill shortcuts."""
        at = AppTest.from_file(self.app_path, default_timeout=60)
        at.run()

        orch = at.session_state.orchestrator
        orch.state["candidate_name"] = "Aarav Sharma"
        orch.state["fit_data"] = {"placement_readiness_score": 75.0, "decision_engine": {"final_decision": "DIRECT SHORTLIST"}}
        orch.state["test_results"] = {"score": 22, "total_questions": 30, "percentage": 73.3}
        orch.state["feedback"] = {
            "headline_verdict": "Scored 73.3%",
            "overall_readiness_score": 75.0,
            "readiness_level": "High Competence",
            "top_strengths": ["Problem solving"],
            "unified_topic_readiness": [],
            "targeted_study_plan_next_48h": []
        }
        at.session_state["current_page"] = "05_results"
        at.run()

        orch.curriculum_agent.run_json = lambda prompt: None
        # Step 5 to Step 6
        to6_btn = [b for b in at.button if b.key == "step5_to_step6_btn"][0]
        to6_btn.click().run()
        self.assertEqual(at.session_state["current_page"], "06_curriculum")

        # Day 6 shortcut to Step 3
        d6_btn = [b for b in at.button if b.key == "curriculum_day6_drill_btn"][0]
        d6_btn.click().run()
        self.assertEqual(at.session_state["current_page"], "03_question_bank")

        # Return to Step 6 and test Day 7 shortcut to Step 4
        at.session_state["current_page"] = "06_curriculum"
        at.run()
        d7_btn = [b for b in at.button if b.key == "curriculum_day7_drill_btn"][0]
        d7_btn.click().run()
        self.assertEqual(at.session_state["current_page"], "04_online_test")

    def test_uat_page_06_prep_curriculum(self):
        """Validates Step 6 7-Day Prep Curriculum media & status filters and zero exceptions."""
        at = AppTest.from_file(self.app_path, default_timeout=60)
        at.run()

        # Mock LLM generation to return failsafe curriculum instantly
        at.session_state.orchestrator.curriculum_agent.run_json = lambda prompt: None
        at.session_state["current_page"] = "06_curriculum"
        at.run()

        self.assertEqual(len(at.exception), 0, f"Exceptions on Step 6: {at.exception}")
        sb_options = [opt for sb in at.selectbox for opt in sb.options]
        self.assertTrue(any("All Assets" in str(opt) for opt in sb_options), f"Expected All Assets in {sb_options}")

    def test_uat_viewport_mode_switcher_toggle(self):
        """Validates Viewport Mode switcher widget existence and toggling across all 4 modes."""
        at = AppTest.from_file(self.app_path, default_timeout=60)
        at.run()
        self.assertEqual(len(at.exception), 0, f"Exceptions on mount: {at.exception}")

        # Verify default session state
        self.assertEqual(at.session_state["view_mode"], "🖥️ Auto (Responsive)")

        # Locate viewport selector
        view_sbs = [sb for sb in at.selectbox if sb.key == "viewport_mode_selector"]
        self.assertTrue(len(view_sbs) > 0, "Viewport mode selectbox not found in sidebar")
        sb = view_sbs[0]

        # 1. Switch to Mobile View (390px)
        sb.select("📱 Mobile View (390px)").run()
        self.assertEqual(len(at.exception), 0, f"Exceptions on Mobile switch: {at.exception}")
        self.assertEqual(at.session_state["view_mode"], "📱 Mobile View (390px)")

        # 2. Switch to Tablet View (820px)
        sb.select("📟 Tablet View (820px)").run()
        self.assertEqual(len(at.exception), 0, f"Exceptions on Tablet switch: {at.exception}")
        self.assertEqual(at.session_state["view_mode"], "📟 Tablet View (820px)")

        # 3. Switch to Desktop (Wide)
        sb.select("💻 Desktop (Wide)").run()
        self.assertEqual(len(at.exception), 0, f"Exceptions on Desktop switch: {at.exception}")
        self.assertEqual(at.session_state["view_mode"], "💻 Desktop (Wide)")

        # 4. Switch back to Auto
        sb.select("🖥️ Auto (Responsive)").run()
        self.assertEqual(len(at.exception), 0, f"Exceptions on Auto switch: {at.exception}")
        self.assertEqual(at.session_state["view_mode"], "🖥️ Auto (Responsive)")

    def test_uat_mobile_layout_stacking_invariants(self):
        """Validates that under Mobile View mode, all Page 1 widgets and buttons execute cleanly."""
        at = AppTest.from_file(self.app_path, default_timeout=60)
        at.run()

        # Set mobile view mode
        at.session_state["view_mode"] = "📱 Mobile View (390px)"
        at.run()
        self.assertEqual(len(at.exception), 0, f"Exceptions in unauthenticated mobile mode: {at.exception}")

        # Set key to verify authenticated mobile onboarding layout
        at.session_state["custom_api_key"] = "AIzaSyFakeKeyForUATTest"
        at.run()
        self.assertEqual(len(at.exception), 0, f"Exceptions in authenticated mobile mode: {at.exception}")

        btn_labels = [str(b.label) for b in at.button]
        self.assertTrue(any("Load Demo" in lbl for lbl in btn_labels), f"Expected Load Demo buttons in mobile view: {btn_labels}")

    def test_uat_step4_iframe_height_contracts(self):
        """Verifies that voice recorder and exam timer iframe contracts in frontend/app.py use responsive heights."""
        with open(self.app_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Voice recorder height must be 280 for mobile responsiveness
        self.assertIn("st.iframe(vr_html, height=280)", code)
        self.assertIn("components.html(vr_html, height=280)", code)

        # Exam timer height must be 140 for mobile clock wrap
        self.assertIn("st.iframe(tf_html, height=140)", code)
        self.assertIn("components.html(tf_html, height=140)", code)


if __name__ == "__main__":
    unittest.main()

