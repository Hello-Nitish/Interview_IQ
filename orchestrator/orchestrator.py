import os
import logging
import concurrent.futures
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List

logger = logging.getLogger(__name__)

from agents.resume_reviewer import ResumeReviewerAgent
from agents.jd_analyzer import JDAnalyzerAgent
from agents.fit_analyzer import FitAnalyzerAgent
from agents.question_bank import QuestionBankAgent
from agents.online_test_agent import OnlineTestAgent
from agents.feedback_agent import FeedbackAgent
from agents.company_intel_agent import CompanyIntelAgent
from agents.micro_curriculum_agent import MicroCurriculumAgent
from utils.session_manager import SessionManager
from utils.quality_controller import MultiAgentQualityController

class Orchestrator:
    def __init__(self, session_id: Optional[str] = None, api_key: Optional[str] = None, *args, **kwargs):
        self.api_key = api_key
        self.quality_controller = MultiAgentQualityController()
        self.resume_agent = ResumeReviewerAgent(api_key=api_key)
        self.jd_agent = JDAnalyzerAgent(api_key=api_key)
        self.fit_agent = FitAnalyzerAgent(api_key=api_key)
        self.qb_agent = QuestionBankAgent(api_key=api_key)
        self.online_test_agent = OnlineTestAgent(api_key=api_key)
        self.feedback_agent = FeedbackAgent(api_key=api_key)
        self.company_intel_agent = CompanyIntelAgent(api_key=api_key)
        self.curriculum_agent = MicroCurriculumAgent(api_key=api_key)

        if session_id:
            self.session_id = session_id
            self.state = SessionManager.load_session(session_id)
        else:
            self.session_id = SessionManager.create_session()
            self.state = SessionManager.load_session(self.session_id)

    def set_api_key(self, api_key: Optional[str]):
        self.api_key = api_key
        from utils.gemini_client import GeminiClient
        self.resume_agent.client = GeminiClient(api_key=api_key)
        self.jd_agent.client = GeminiClient(api_key=api_key)
        self.fit_agent.client = GeminiClient(api_key=api_key)
        self.qb_agent.client = GeminiClient(api_key=api_key)
        self.online_test_agent.client = GeminiClient(api_key=api_key)
        self.feedback_agent.client = GeminiClient(api_key=api_key)
        self.company_intel_agent.client = GeminiClient(api_key=api_key)
        self.curriculum_agent.client = GeminiClient(api_key=api_key)

    def process_onboarding(
        self, 
        resume_text: str, 
        jd_text: str, 
        stage_callback: Optional[Callable] = None,
        mode: str = "complete"
    ) -> Dict[str, Any]:
        """
        Processes candidate onboarding with high-performance concurrent ingestion
        of resume profile and job description benchmarks.

        Modes:
        - 'strategic_only': Option 1 (Fast Track). Runs Stages 1-5 (Resume, JD, Company Intel,
          Strategic Fit, Question Bank) without generating the 30-MCQ test upfront.
        - 'complete': Option 2 (Full Pipeline). Runs Stages 1-6 including the 30-MCQ Online Test.
        """
        clean_mode = (mode or "complete").strip().lower()
        if clean_mode not in ("strategic_only", "complete"):
            clean_mode = "complete"

        total_stages = 5 if clean_mode == "strategic_only" else 6

        if stage_callback:
            stage_callback(1, total_stages, "Parsing & Ingesting Profile", "Profiling candidate education, experience tiers, and skill inventory...")

        # Concurrently execute resume and JD analysis with zero-crash future handling
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_resume = executor.submit(self.resume_agent.review_resume, resume_text)
            future_jd = executor.submit(self.jd_agent.analyze_jd, jd_text)
            
            # Safe worker thread future resolution: Resume with timeout
            try:
                resume_profile = future_resume.result(timeout=60.0)
                if not isinstance(resume_profile, dict):
                    resume_profile = self.resume_agent._generate_failsafe_resume(resume_text, "Invalid non-dict return")
            except Exception as e:
                logger.warning(f"[Orchestrator] Resume analysis worker error: {e}. Activating failsafe resume generator.")
                resume_profile = self.resume_agent._generate_failsafe_resume(resume_text, error_reason=str(e))

            # Safe worker thread future resolution: JD with timeout
            try:
                jd_profile = future_jd.result(timeout=60.0)
                if not isinstance(jd_profile, dict):
                    jd_profile = self.jd_agent._generate_failsafe_jd(jd_text, "Invalid non-dict return")
            except Exception as e:
                logger.warning(f"[Orchestrator] JD analysis worker error: {e}. Activating failsafe JD generator.")
                jd_profile = self.jd_agent._generate_failsafe_jd(jd_text, error_reason=str(e))

        self.state["resume_data"] = resume_profile
        self.state["candidate_name"] = resume_profile.get("candidate_name", "Candidate")

        if stage_callback:
            stage_callback(2, total_stages, "Analyzing Job Description", "Extracting mandatory requirements, role benchmarks, and core skills...")

        self.state["jd_data"] = jd_profile

        # Retrieve Company Culture Principles & Leadership Intelligence
        company_name = jd_profile.get("company_name", "")
        role_title = jd_profile.get("role_title", "")
        if stage_callback:
            stage_callback(3, total_stages, "Retrieving Company Intelligence", f"Analyzing corporate leadership principles and culture DNA for {company_name or 'target firm'}...")
        try:
            company_intel = self.company_intel_agent.get_company_intelligence(company_name, role_title)
        except Exception as e:
            logger.warning(f"[Orchestrator] Company intel retrieval error: {e}. Activating dynamic fallback.")
            company_intel = self.company_intel_agent._synthesize_dynamic_company_intel(company_name, role_title)
        self.state["company_intel"] = company_intel

        if stage_callback:
            stage_callback(4, total_stages, "Computing Strategic Alignment", "Evaluating technical match %, experience scoring, and critical gaps...")
        try:
            fit_profile = self.fit_agent.analyze_fit(resume_profile, jd_profile)
            if not isinstance(fit_profile, dict):
                fit_profile = self.fit_agent._generate_failsafe_fit(resume_profile, jd_profile, "Invalid non-dict return")
        except Exception as e:
            logger.warning(f"[Orchestrator] Strategic fit analysis error: {e}. Activating failsafe fit generator.")
            fit_profile = self.fit_agent._generate_failsafe_fit(resume_profile, jd_profile, error_reason=str(e))
        self.state["fit_data"] = fit_profile

        if stage_callback:
            stage_callback(5, total_stages, "Generating Tailored Question Bank", "Formulating targeted behavioral, technical, and leadership probes...")
        try:
            question_bank = self.qb_agent.generate_questions(resume_profile, jd_profile, fit_profile)
        except Exception as e:
            logger.warning(f"[Orchestrator] Question bank generation error: {e}. Activating failsafe question bank generator.")
            topic_cl = self.qb_agent.extract_topic_checklist(jd_profile, resume_profile, fit_profile)
            question_bank = self.qb_agent._generate_failsafe_question_bank(
                topic_checklist=topic_cl, jd_profile=jd_profile, resume_profile=resume_profile, fit_profile=fit_profile, error_reason=str(e)
            )
        try:
            question_bank = self.company_intel_agent.enrich_question_bank(question_bank, company_intel)
        except Exception as e:
            logger.warning(f"[Orchestrator] Question bank enrichment warning: {e}. Retaining baseline question bank.")
        self.state["question_bank"] = question_bank
        self.state["round"] = 1
        self.state["round_number"] = 1
        self.state["analysis_mode"] = clean_mode

        online_test = None
        if clean_mode != "strategic_only":
            # Stage 6: Pre-generate or prepare the 30-question Online Test
            if stage_callback:
                stage_callback(6, total_stages, "Calibrating 30-MCQ Online Test", "Synthesizing scenario-based multiple choice assessment...")
            try:
                online_test = self.online_test_agent.generate_test(
                    jd_profile=jd_profile,
                    resume_profile=resume_profile,
                    fit_profile=fit_profile,
                    topic_checklist=question_bank.get("topic_checklist", []),
                    num_questions=30
                )
            except Exception as e:
                logger.warning(f"[Orchestrator] Online test calibration error: {e}. Activating failsafe test generator.")
                online_test = self.online_test_agent._generate_failsafe_test(
                    question_bank.get("topic_checklist", []), jd_profile, num_questions=30, error_reason=str(e)
                )
            self.state["online_test"] = online_test
            self.state["test_results"] = None
            self.state["feedback"] = None
            self.state["feedback_data"] = None
        else:
            # Clean state sanitization for strategic_only mode
            self.state["online_test"] = None
            self.state["test_results"] = None
            self.state["feedback"] = None
            self.state["feedback_data"] = None

        # Execute Multi-Agent Quality Assurance Audit
        quality_telemetry = {
            "resume_audit": self.quality_controller.audit_resume_profile(resume_profile).to_dict(),
            "fit_audit": self.quality_controller.audit_fit_profile(fit_profile).to_dict(),
            "qb_audit": self.quality_controller.audit_question_bank(question_bank).to_dict()
        }
        if online_test:
            quality_telemetry["test_audit"] = self.quality_controller.audit_online_test(online_test).to_dict()

        overall_quality_score = round(
            sum(a["quality_score"] for a in quality_telemetry.values()) / max(len(quality_telemetry), 1),
            1
        )
        quality_telemetry["overall_pipeline_quality"] = overall_quality_score
        self.state["quality_telemetry"] = quality_telemetry

        SessionManager.save_session(self.session_id, self.state)
        return {
            "resume_data": resume_profile,
            "jd_data": jd_profile,
            "fit_data": fit_profile,
            "question_bank": question_bank,
            "online_test": online_test,
            "analysis_mode": clean_mode,
            "quality_telemetry": quality_telemetry
        }

    def generate_online_test(self, num_questions: int = 30) -> dict:
        jd_profile = self.state.get("jd_data") or self.state.get("jd_profile") or {}
        resume_profile = self.state.get("resume_data") or self.state.get("resume_profile") or {}
        fit_profile = self.state.get("fit_data") or self.state.get("fit_profile") or {}
        topic_checklist = self.state.get("question_bank", {}).get("topic_checklist", [])

        try:
            online_test = self.online_test_agent.generate_test(
                jd_profile=jd_profile,
                resume_profile=resume_profile,
                fit_profile=fit_profile,
                topic_checklist=topic_checklist,
                num_questions=num_questions
            )
        except Exception as e:
            logger.warning(f"[Orchestrator] generate_online_test error: {e}. Using failsafe test.")
            online_test = self.online_test_agent._generate_failsafe_test(
                topic_checklist, jd_profile, num_questions=num_questions, error_reason=str(e)
            )
        self.state["online_test"] = online_test
        SessionManager.save_session(self.session_id, self.state)
        return online_test

    def submit_online_test(self, candidate_answers: dict) -> dict:
        online_test = self.state.get("online_test")
        if not online_test:
            online_test = self.generate_online_test(num_questions=30)

        test_results = self.online_test_agent.score_test(online_test, candidate_answers)
        self.state["test_results"] = test_results

        # Record test attempt in SQLite
        try:
            from utils.database import DatabaseManager
            current_round = self.state.get("round_number") or self.state.get("round", 1)
            DatabaseManager.record_test_attempt(
                self.session_id,
                current_round,
                online_test,
                test_results,
                candidate_answers
            )
        except Exception:
            pass

        # Automatically synthesize unified performance feedback
        self.finalize_readiness_report()

        SessionManager.save_session(self.session_id, self.state)
        return test_results

    def finalize_readiness_report(self) -> dict:
        fit_profile = self.state.get("fit_data", {})
        test_results = self.state.get("test_results", {})
        question_bank = self.state.get("question_bank", {})

        feedback = self.feedback_agent.generate_unified_feedback(fit_profile, test_results, question_bank)
        self.state["feedback"] = feedback
        self.state["feedback_data"] = feedback

        # Audit feedback report quality
        fb_audit = self.quality_controller.audit_feedback_report(feedback).to_dict()
        if "quality_telemetry" not in self.state or not isinstance(self.state["quality_telemetry"], dict):
            self.state["quality_telemetry"] = {}
        self.state["quality_telemetry"]["feedback_audit"] = fb_audit

        SessionManager.save_session(self.session_id, self.state)

        # Record readiness report in SQLite
        try:
            from utils.database import DatabaseManager
            current_round = self.state.get("round_number") or self.state.get("round", 1)
            DatabaseManager.record_readiness_report(self.session_id, current_round, feedback)
        except Exception:
            pass

        return feedback

    def trigger_next_round(self) -> dict:
        """
        Closed-Loop Feedback:
        Takes the weak topics identified in the Online Test & Fit/Gap Analysis,
        and feeds them back into QuestionBankAgent to re-weight Round 2 prep.
        """
        feedback = self.state.get("feedback", {})
        prioritized = feedback.get("prioritized_topics_for_next_round", [])
        
        resume_profile = self.state.get("resume_data") or self.state.get("resume_profile") or {}
        jd_profile = self.state.get("jd_data") or self.state.get("jd_profile") or {}
        fit_profile = self.state.get("fit_data") or self.state.get("fit_profile") or {}

        # Re-weight question bank targeting weak areas
        new_qb = self.qb_agent.generate_questions(
            resume_profile=resume_profile,
            jd_profile=jd_profile,
            fit_profile=fit_profile,
            prioritized_topics=prioritized
        )
        if "company_intel" in self.state:
            new_qb = self.company_intel_agent.enrich_question_bank(new_qb, self.state["company_intel"])
        self.state["question_bank"] = new_qb

        current_round = self.state.get("round_number") or self.state.get("round", 1)
        new_round = current_round + 1
        self.state["round"] = new_round
        self.state["round_number"] = new_round

        if isinstance(new_qb, dict):
            new_qb["round_number"] = new_round

        # Generate a fresh 30-question assessment reflecting updated priorities
        new_test = self.online_test_agent.generate_test(
            jd_profile=jd_profile,
            resume_profile=resume_profile,
            fit_profile=fit_profile,
            topic_checklist=new_qb.get("topic_checklist", []),
            num_questions=30
        )
        if isinstance(new_test, dict):
            new_test["round_number"] = new_round
        self.state["online_test"] = new_test
        self.state["test_results"] = None

        SessionManager.save_session(self.session_id, self.state)
        return new_qb

    def generate_curriculum(self, weak_topics: Optional[List[Dict[str, Any]]] = None, composite_score: float = 65.0) -> Dict[str, Any]:
        """
        Synthesizes a 7-day personalized micro-curriculum targeted at diagnosed gaps.
        Persists the plan in SQLite and current session state.
        """
        from utils.database import DatabaseManager

        feedback = self.state.get("feedback") or {}
        if not weak_topics:
            weak_topics = feedback.get("unified_topic_readiness", [])
        if not composite_score or composite_score == 65.0:
            composite_score = float(feedback.get("overall_readiness_score", feedback.get("composite_readiness_score", 65.0)))

        jd_profile = self.state.get("jd_data") or self.state.get("jd_profile") or {}

        plan = self.curriculum_agent.generate_curriculum(
            weak_topics=weak_topics,
            jd_profile=jd_profile,
            composite_score=composite_score
        )
        self.state["curriculum_plan"] = plan

        try:
            plan_id = DatabaseManager.save_curriculum_plan(
                session_id=self.session_id,
                plan_dict=plan
            )
            self.state["curriculum_plan_id"] = plan_id
        except Exception:
            pass

        SessionManager.save_session(self.session_id, self.state)
        return plan

    def toggle_curriculum_asset(self, day_num: int, resource_id: str, checked: bool) -> Dict[str, Any]:
        """
        Toggles completion state of a specific curriculum resource in SQLite and session state.
        Returns the updated progress summary.
        """
        from utils.database import DatabaseManager

        plan = self.state.get("curriculum_plan", {})
        checked_list = self.state.get("checked_resources", [])

        if checked and resource_id not in checked_list:
            checked_list.append(resource_id)
        elif not checked and resource_id in checked_list:
            checked_list.remove(resource_id)

        self.state["checked_resources"] = checked_list

        # Compute progress metrics
        total_resources = sum(len(day.get("resources", [])) for day in plan.get("days", []))
        completed = len(checked_list)
        progress_pct = int((completed / max(1, total_resources)) * 100)
        days_completed = int((completed / max(1, total_resources)) * 7)

        try:
            DatabaseManager.update_curriculum_progress(
                session_id=self.session_id,
                checked_items=checked_list,
                days_completed=days_completed
            )
        except Exception:
            pass

        SessionManager.save_session(self.session_id, self.state)
        return {
            "total_resources": total_resources,
            "completed_resources": completed,
            "progress_percentage": progress_pct,
            "days_completed": days_completed
        }