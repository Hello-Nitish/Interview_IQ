"""
utils/quality_controller.py
Multi-Agent Process Quality Controller & Output Verification Engine.
Performs in-process schema validation, depth scoring, hallucination mitigation,
and quality assurance across all sub-agent deliverables.
"""

from typing import Dict, Any, List, Optional, Tuple


class QualityAuditResult:
    def __init__(self, passed: bool, score: float, metrics: Dict[str, Any], recommendations: List[str]):
        self.passed = passed
        self.score = score  # 0.0 - 100.0
        self.metrics = metrics
        self.recommendations = recommendations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "quality_score": round(self.score, 1),
            "metrics": self.metrics,
            "recommendations": self.recommendations
        }


class MultiAgentQualityController:
    """
    Evaluates and elevates output quality produced by sub-agents.
    Ensures deliverables meet enterprise depth, structural integrity,
    and actionable guidance criteria.
    """

    @staticmethod
    def audit_resume_profile(profile: Dict[str, Any]) -> QualityAuditResult:
        if not isinstance(profile, dict):
            return QualityAuditResult(False, 0.0, {"error": "Non-dictionary output"}, ["Re-parse resume document."])

        score = 0.0
        recs = []
        metrics = {}

        # 1. Candidate Bio completeness (25 pts)
        bio = profile.get("candidate_bio") or {}
        has_name = bool(profile.get("candidate_name") or bio.get("name"))
        has_edu = bool(profile.get("education") or bio.get("education"))
        bio_score = (15.0 if has_name else 0.0) + (10.0 if has_edu else 0.0)
        score += bio_score
        metrics["bio_completeness"] = f"{int(bio_score)}/25"

        # 2. Technical Skills specificity (25 pts)
        skills = profile.get("skills") or profile.get("technical_skills") or []
        skill_count = len(skills) if isinstance(skills, list) else len(skills.keys()) if isinstance(skills, dict) else 0
        skill_score = min(25.0, skill_count * 2.5)
        score += skill_score
        metrics["skills_count"] = skill_count
        metrics["skills_score"] = f"{int(skill_score)}/25"
        if skill_count < 5:
            recs.append("Extract granular technical competencies and platforms.")

        # 3. Projects & Work Experience with Metrics (25 pts)
        projects = profile.get("projects") or []
        experience = profile.get("experience") or []
        total_items = (len(projects) if isinstance(projects, list) else 0) + (len(experience) if isinstance(experience, list) else 0)
        proj_score = min(25.0, total_items * 8.5)
        score += proj_score
        metrics["project_experience_count"] = total_items
        metrics["project_score"] = f"{int(proj_score)}/25"

        # 4. Challenge Areas / Scrutiny probes (25 pts)
        challenges = profile.get("challenge_areas") or profile.get("overall_interview_risk_areas") or []
        chal_count = len(challenges) if isinstance(challenges, list) else 0
        chal_score = min(25.0, chal_count * 12.5)
        score += chal_score
        metrics["challenge_areas_count"] = chal_count
        metrics["scrutiny_score"] = f"{int(chal_score)}/25"
        if chal_count == 0:
            recs.append("Identify methodological trade-offs and unquantified claims for interview scrutiny.")

        return QualityAuditResult(score >= 70.0, score, metrics, recs)

    @staticmethod
    def audit_fit_profile(fit: Dict[str, Any]) -> QualityAuditResult:
        if not isinstance(fit, dict):
            return QualityAuditResult(False, 0.0, {"error": "Non-dictionary output"}, ["Re-evaluate strategic fit."])

        score = 0.0
        recs = []
        metrics = {}

        # 1. Technical Rating & Formula (25 pts)
        tech_rating = fit.get("technical_rating") or {}
        has_match_pct = "strict_match_percentage" in tech_rating or "technical_match_pct" in tech_rating
        has_mandatory_counts = "total_mandatory_count" in tech_rating or "mandatory_matched_count" in tech_rating
        tr_score = (15.0 if has_match_pct else 0.0) + (10.0 if has_mandatory_counts else 0.0)
        score += tr_score
        metrics["technical_rating_score"] = f"{int(tr_score)}/25"

        # 2. 4-Column Requirements Matrix (30 pts)
        req_matrix = fit.get("requirements_matrix") or []
        req_count = len(req_matrix) if isinstance(req_matrix, list) else 0
        req_score = min(30.0, req_count * 5.0)
        score += req_score
        metrics["matrix_requirements_count"] = req_count
        metrics["matrix_score"] = f"{int(req_score)}/30"
        if req_count < 4:
            recs.append("Deepen requirements matrix coverage to reflect full JD mandatory and preferred capabilities.")

        # 3. Decision Engine & Strategic Advice (25 pts)
        has_decision = bool(fit.get("decision_engine") or fit.get("placement_readiness_score") is not None)
        has_gaps = bool(fit.get("critical_gaps") or fit.get("gap_analysis"))
        dec_score = (15.0 if has_decision else 0.0) + (10.0 if has_gaps else 0.0)
        score += dec_score
        metrics["decision_depth_score"] = f"{int(dec_score)}/25"

        # 4. Multidimensional Probing (20 pts)
        comm = fit.get("communication_profile") or {}
        prob = fit.get("problem_solving") or {}
        multi_score = (10.0 if bool(comm) else 0.0) + (10.0 if bool(prob) else 0.0)
        score += multi_score
        metrics["multidimensional_probing_score"] = f"{int(multi_score)}/20"

        return QualityAuditResult(score >= 70.0, score, metrics, recs)

    @staticmethod
    def audit_question_bank(qb: Dict[str, Any]) -> QualityAuditResult:
        if not isinstance(qb, dict):
            return QualityAuditResult(False, 0.0, {"error": "Non-dictionary output"}, ["Regenerate question bank."])

        score = 0.0
        recs = []
        metrics = {}

        # 1. Topic Checklist Coverage (30 pts)
        checklist = qb.get("topic_checklist") or []
        cl_count = len(checklist) if isinstance(checklist, list) else 0
        cl_score = min(30.0, cl_count * 5.0)
        score += cl_score
        metrics["topic_checklist_count"] = cl_count
        metrics["checklist_score"] = f"{int(cl_score)}/30"

        # 2. 5-Dimensional Question Coverage (40 pts)
        dim_keys = [
            "resume_based_questions",
            "technical_questions",
            "conceptual_questions",
            "problem_solving_questions",
            "behavioral_questions"
        ]
        active_dims = sum(1 for k in dim_keys if len(qb.get(k, [])) > 0)
        dim_score = min(40.0, active_dims * 8.0)
        score += dim_score
        metrics["active_dimensions"] = f"{active_dims}/5"
        metrics["dimension_score"] = f"{int(dim_score)}/40"
        if active_dims < 5:
            recs.append("Ensure all 5 assessment dimensions contain calibrated questions.")

        # 3. Total Question Count & Granularity (30 pts)
        total_q = sum(len(qb.get(k, [])) for k in dim_keys)
        q_score = min(30.0, total_q * 2.0)
        score += q_score
        metrics["total_questions"] = total_q
        metrics["volume_score"] = f"{int(q_score)}/30"

        return QualityAuditResult(score >= 70.0, score, metrics, recs)

    @staticmethod
    def audit_online_test(test: Dict[str, Any]) -> QualityAuditResult:
        if not isinstance(test, dict):
            return QualityAuditResult(False, 0.0, {"error": "Non-dictionary output"}, ["Regenerate online test."])

        questions = test.get("questions") or []
        count = len(questions) if isinstance(questions, list) else 0
        metrics = {"total_questions": count}
        recs = []

        if count < 30:
            recs.append(f"Online test contains {count} questions, below required 30 items.")
            return QualityAuditResult(False, max(10.0, count * 2.5), metrics, recs)

        # Check option completeness (A, B, C, D) and rationales
        valid_options = 0
        has_rationales = 0
        for q in questions:
            opts = q.get("options") or {}
            if isinstance(opts, dict) and all(k in opts for k in ["A", "B", "C", "D"]):
                valid_options += 1
            if q.get("explanation") or q.get("rationale"):
                has_rationales += 1

        opts_pct = (valid_options / count) * 100.0
        rat_pct = (has_rationales / count) * 100.0
        metrics["valid_options_percentage"] = round(opts_pct, 1)
        metrics["explanations_percentage"] = round(rat_pct, 1)

        score = (0.5 * 100.0) + (0.25 * opts_pct) + (0.25 * rat_pct)
        return QualityAuditResult(score >= 75.0, score, metrics, recs)

    @staticmethod
    def audit_feedback_report(feedback: Dict[str, Any]) -> QualityAuditResult:
        if not isinstance(feedback, dict):
            return QualityAuditResult(False, 0.0, {"error": "Non-dictionary output"}, ["Regenerate feedback report."])

        score = 0.0
        recs = []
        metrics = {}

        # 1. Composite Readiness Score presence (25 pts)
        has_score = "overall_readiness_score" in feedback or "composite_readiness_score" in feedback
        has_level = bool(feedback.get("readiness_level"))
        s_score = (15.0 if has_score else 0.0) + (10.0 if has_level else 0.0)
        score += s_score
        metrics["readiness_score_present"] = has_score

        # 2. Unified Topic Readiness Matrix (35 pts)
        topics = feedback.get("unified_topic_readiness") or feedback.get("unified_topic_breakdown") or []
        t_count = len(topics) if isinstance(topics, list) else 0
        t_score = min(35.0, t_count * 3.5)
        score += t_score
        metrics["unified_topics_count"] = t_count

        # 3. Actionable 48h Study Roadmap (40 pts)
        roadmap = feedback.get("targeted_study_plan_next_48h") or feedback.get("prioritized_revision_plan") or []
        r_count = len(roadmap) if isinstance(roadmap, list) else 0
        r_score = min(40.0, r_count * 8.0)
        score += r_score
        metrics["study_plan_milestones"] = r_count

        return QualityAuditResult(score >= 70.0, score, metrics, recs)
