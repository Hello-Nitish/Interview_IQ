import json
from agents.base_agent import BaseAgent

class FeedbackAgent(BaseAgent):
    def __init__(self, api_key: str = None):
        system_instruction = (
            "You are an executive talent evaluator, placement director, and candidate coach. "
            "Your role is to unify structural Candidate-to-Job Fit/Gap Analysis with empirical Online Test performance "
            "into a single de-duplicated readiness diagnostic. "
            "Explicitly attribute strengths and weaknesses to their origin (Online Test, Fit/Gap Analysis, or Both). "
            "When a deficit appears in BOTH the resume fit and the test performance, flag it as HIGH PRIORITY. "
            "Output strictly valid JSON."
        )
        super().__init__(name="FeedbackAgent", role="Unified Readiness Diagnostic & Closed-Loop Feedback Coach", system_instruction=system_instruction, api_key=api_key)

    def build_unified_topic_readiness(self, fit_profile: dict, test_results: dict, question_bank: dict = None) -> list:
        """
        Merges Fit/Gap deficit data with Online Test performance into a single de-duplicated topic list.
        Flags dual weaknesses as 'Both (High Priority)'.
        """
        fit_profile = fit_profile or {}
        test_results = test_results or {}
        question_bank = question_bank or {}

        # 1. Identify Fit/Gap Weaknesses and Strengths
        fit_gaps = set()
        for g in fit_profile.get("critical_gaps", []):
            name = g.get("skill_or_area", "") if isinstance(g, dict) else str(g)
            if name:
                fit_gaps.add(name.lower().strip())
        for row in fit_profile.get("requirements_matrix", []):
            stat = str(row.get("status", "")).lower()
            if "missing" in stat or "gap" in stat:
                req = str(row.get("requirement", "")).lower().strip()
                if req:
                    fit_gaps.add(req)

        fit_strengths = set()
        for m in fit_profile.get("strong_matches", []):
            name = m.get("skill_or_area", "") if isinstance(m, dict) else str(m)
            if name:
                fit_strengths.add(name.lower().strip())
        for row in fit_profile.get("requirements_matrix", []):
            if "matched" in str(row.get("status", "")).lower():
                req = str(row.get("requirement", "")).lower().strip()
                if req:
                    fit_strengths.add(req)

        # 2. Extract Test Topic Accuracies and Weaknesses
        test_topic_map = {}
        for item in test_results.get("topic_breakdown", []):
            t_name = item.get("topic", "").strip()
            if t_name:
                test_topic_map[t_name.lower()] = item
        # Also support topic_accuracy dictionary
        for t_name, stats in test_results.get("topic_accuracy", {}).items():
            if t_name and t_name.lower() not in test_topic_map:
                pct = stats.get("percentage", 0.0)
                test_topic_map[t_name.lower()] = {
                    "topic": t_name,
                    "accuracy_percentage": pct,
                    "is_weak": pct < 70.0
                }

        # 3. Gather all unique topics from Question Bank, Test Breakdown, and Fit Profile
        all_topics = {}
        for item in question_bank.get("topic_checklist", []):
            t_name = item.get("topic") or item.get("topic_name", "")
            t_name = str(t_name).strip()
            if t_name and t_name.lower() not in all_topics:
                all_topics[t_name.lower()] = {
                    "topic": t_name,
                    "category": item.get("category", "Mandatory")
                }
        for item in test_results.get("topic_breakdown", []):
            t_name = item.get("topic", "").strip()
            if t_name and t_name.lower() not in all_topics:
                all_topics[t_name.lower()] = {
                    "topic": t_name,
                    "category": "Assessed Skill"
                }
        for t_name in test_results.get("topic_accuracy", {}).keys():
            if t_name and t_name.lower() not in all_topics:
                all_topics[t_name.lower()] = {
                    "topic": t_name,
                    "category": "Assessed Skill"
                }
        for row in fit_profile.get("requirements_matrix", []):
            req = str(row.get("requirement", "")).strip()
            if req and req.lower() not in all_topics:
                all_topics[req.lower()] = {
                    "topic": req,
                    "category": row.get("category", "Mandatory")
                }

        unified_list = []
        for t_lower, info in all_topics.items():
            t_name = info["topic"]
            cat = info["category"]

            # Evaluate fit deficit
            is_fit_gap = any(fg in t_lower or t_lower in fg for fg in fit_gaps if fg)
            is_fit_strength = any(fs in t_lower or t_lower in fs for fs in fit_strengths if fs)

            # Evaluate test deficit
            test_data = test_topic_map.get(t_lower)
            if test_data:
                test_acc = test_data.get("accuracy_percentage", 100.0)
                is_test_weak = test_data.get("is_weak", False) or test_acc < 70.0
            else:
                test_acc = None
                is_test_weak = False

            # Attribute Source, Priority, and Readiness
            if is_fit_gap and is_test_weak:
                source = "Both (High Priority)"
                status = "Critical Deficit"
                priority = "High Priority"
                readiness_status = "HIGH PRIORITY"
                evidence = f"Gap in resume requirements analysis and demonstrated low accuracy ({test_acc}% in online test)."
            elif is_test_weak:
                source = "Online Test"
                status = "Empirical Test Gap"
                priority = "Medium Priority"
                readiness_status = "Needs Practice"
                evidence = f"Tested below 70% threshold ({test_acc}%) despite baseline credentials."
            elif is_fit_gap:
                source = "Fit/Gap Analysis"
                status = "Resume Document Gap"
                priority = "Medium Priority"
                readiness_status = "Needs Practice"
                evidence = "Missing explicit coursework, project evidence, or certifications in resume audit."
            elif is_fit_strength and (test_acc is not None and test_acc >= 80.0):
                source = "Both (Validated Strength)"
                status = "Mastered"
                priority = "Low Priority"
                readiness_status = "Mastered"
                evidence = f"Documented credentials confirmed by high empirical score ({test_acc}%)."
            elif test_acc is not None and test_acc >= 80.0:
                source = "Online Test"
                status = "Test Validated"
                priority = "Low Priority"
                readiness_status = "Proficient"
                evidence = f"Demonstrated high problem-solving accuracy ({test_acc}%)."
            elif is_fit_strength:
                source = "Fit/Gap Analysis"
                status = "Claimed Strength"
                priority = "Low Priority"
                readiness_status = "Proficient"
                evidence = "Substantiated with strong resume project and background alignment."
            else:
                source = "Baseline Untested"
                status = "Developing"
                priority = "Low Priority"
                readiness_status = "Developing"
                evidence = "Foundational domain concept requiring structured technical revision."

            unified_list.append({
                "topic": t_name,
                "category": cat,
                "source": source,
                "primary_source": source,
                "status": status,
                "readiness_status": readiness_status,
                "priority": priority,
                "evidence": evidence,
                "evidence_summary": evidence,
                "test_accuracy": f"{test_acc}%" if test_acc is not None else "Not Tested in Exam",
                "is_dual_weakness": (source == "Both (High Priority)")
            })

        # Sort: dual weaknesses first, then medium priority, then validated
        priority_order = {"High Priority": 0, "Medium Priority": 1, "Low Priority": 2}
        unified_list.sort(key=lambda x: priority_order.get(x["priority"], 3))
        return unified_list

    def generate_unified_feedback(self, fit_profile: dict, test_results: dict, question_bank: dict = None) -> dict:
        """
        Folds in Online Test results and Fit/Gap data to produce one combined readiness report
        and extracts prioritized topics to feed back into the next round's question bank.
        """
        unified_topics = self.build_unified_topic_readiness(fit_profile, test_results, question_bank)
        
        # Calculate composite readiness score: 45% structural fit + 55% empirical test
        fit_score = fit_profile.get("placement_readiness_score", 65.0) if fit_profile else 65.0
        test_score = test_results.get("percentage", 70.0) if test_results else 70.0
        overall_readiness_score = round((0.45 * fit_score) + (0.55 * test_score), 1)

        if overall_readiness_score >= 80.0:
            readiness_level = "Placement Ready (Strong Contender)"
        elif overall_readiness_score >= 65.0:
            readiness_level = "Competitive (Targeted Revision Needed)"
        else:
            readiness_level = "Action Required (High Vulnerability in Mandatory Areas)"

        dual_weak_topics = [t["topic"] for t in unified_topics if t.get("is_dual_weakness")]
        other_weak_topics = [t["topic"] for t in unified_topics if t.get("priority") in ["High Priority", "Medium Priority"]]
        prioritized_for_next_round = dual_weak_topics + [t for t in other_weak_topics if t not in dual_weak_topics]

        prompt = f'''
Synthesize an executive candidate readiness diagnostic by combining candidate resume fit data with empirical online test results.

COMPOSITE READINESS SCORE: {overall_readiness_score} / 100 ({readiness_level})
FIT READINESS SCORE: {fit_score} / 100
ONLINE TEST SCORE: {test_results.get("score", 0)}/{test_results.get("total_questions", 30)} ({test_score}%)

UNIFIED TOPIC BREAKDOWN:
{json.dumps(unified_topics[:15], indent=2)}

DUAL-WEAKNESS HIGH PRIORITY TOPICS (Failed in BOTH test and resume gap):
{json.dumps(dual_weak_topics, indent=2)}

Generate:
1. `headline_verdict`: Direct 1-2 sentence executive appraisal of the candidate's hiring standing.
2. `strengths_summary`: 3 bullet points of confirmed strengths validated across fit and test.
3. `prioritized_revision_plan`: 4-5 concrete study milestones for the next 48 hours, prioritizing dual-weakness topics first.
4. `closed_loop_guidance`: Specific advice on how the candidate should prepare for Round 2 re-testing.

Return a JSON object with this exact structure:
{{
  "headline_verdict": "Clear executive assessment...",
  "strengths_summary": [
    "Confirmed strength with recruiter value..."
  ],
  "prioritized_revision_plan": [
    {{
      "topic": "Topic Name",
      "concept_to_revise": "Topic Name",
      "priority": "Critical | High | Medium",
      "source_flag": "Both (High Priority) | Online Test | Fit/Gap Analysis",
      "recommended_action": "Specific exercise or problem to solve",
      "recommended_exercise": "Specific exercise or problem to solve",
      "focus_dimension": "Technical Analysis",
      "time_allocation": "2 Hours"
    }}
  ],
  "closed_loop_guidance": "Clear strategic direction for round 2 practice..."
}}
'''
        try:
            feedback_json = self.run_json(prompt)
            feedback_json["overall_readiness_score"] = overall_readiness_score
            feedback_json["readiness_level"] = readiness_level
            feedback_json["fit_score"] = fit_score
            feedback_json["fit_gap_score"] = fit_score
            feedback_json["test_score"] = test_score
            feedback_json["online_test_score"] = test_score
            feedback_json["unified_topic_breakdown"] = unified_topics
            feedback_json["unified_topic_readiness"] = unified_topics
            feedback_json["prioritized_topics_for_next_round"] = prioritized_for_next_round
            feedback_json["top_strengths"] = feedback_json.get("strengths_summary", [])
            feedback_json["targeted_study_plan_next_48h"] = feedback_json.get("prioritized_revision_plan", [])
            return feedback_json
        except Exception as e:
            return self._generate_failsafe_unified_feedback(
                fit_profile, test_results, unified_topics, overall_readiness_score, readiness_level, prioritized_for_next_round, str(e)
            )

    def _generate_failsafe_unified_feedback(self, fit_profile: dict, test_results: dict, unified_topics: list = None, overall_score: float = None, level: str = None, next_round_topics: list = None, error_reason: str = "") -> dict:
        """Failsafe generator creating complete unified feedback when API limits are encountered."""
        fit_profile = fit_profile or {}
        test_results = test_results or {}

        if unified_topics is None:
            unified_topics = self.build_unified_topic_readiness(fit_profile, test_results)

        fit_score = fit_profile.get("placement_readiness_score", 65.0)
        test_score = test_results.get("percentage", 70.0)

        if overall_score is None:
            overall_score = round((0.45 * fit_score) + (0.55 * test_score), 1)

        if level is None:
            if overall_score >= 80.0:
                level = "Placement Ready (Strong Contender)"
            elif overall_score >= 65.0:
                level = "Competitive (Targeted Revision Needed)"
            else:
                level = "Action Required (High Vulnerability in Mandatory Areas)"

        if next_round_topics is None:
            dual_weak = [t["topic"] for t in unified_topics if t.get("is_dual_weakness")]
            other_weak = [t["topic"] for t in unified_topics if t.get("priority") in ["High Priority", "Medium Priority"]]
            next_round_topics = dual_weak + [t for t in other_weak if t not in dual_weak]

        revision_plan = []
        for item in unified_topics[:5]:
            if item.get("priority") in ["High Priority", "Medium Priority"] or item.get("is_dual_weakness"):
                p_prio = "Critical" if item.get("is_dual_weakness") else "High"
                revision_plan.append({
                    "topic": item["topic"],
                    "concept_to_revise": item["topic"],
                    "priority": p_prio,
                    "source_flag": item.get("source", "Online Test"),
                    "recommended_action": f"Review core conceptual mechanics and solve 3 advanced scenario problems in {item['topic']}.",
                    "recommended_exercise": f"Review core conceptual mechanics and solve 3 advanced scenario problems in {item['topic']}.",
                    "focus_dimension": item.get("category", "Technical Competency"),
                    "time_allocation": "2 Hours" if p_prio == "Critical" else "1 Hour"
                })

        if not revision_plan:
            revision_plan.append({
                "topic": "Systematic Technical Synthesis",
                "concept_to_revise": "Systematic Technical Synthesis",
                "priority": "High",
                "source_flag": "Fit/Gap Analysis",
                "recommended_action": "Synthesize core framework trade-offs and practice explaining them under time pressure.",
                "recommended_exercise": "Synthesize core framework trade-offs and practice explaining them under time pressure.",
                "focus_dimension": "Technical Analysis",
                "time_allocation": "2 Hours"
            })

        strengths = [
            "Demonstrated solid conceptual foundation in core candidate profile domains",
            "Consistent problem-solving methodology observed in baseline examination segments",
            "Good structural alignment with primary job description competencies"
        ]

        return {
            "headline_verdict": f"Empirical Diagnostic Complete: Candidate scored {overall_score}/100 ({level}) across structural fit and advanced testing.",
            "overall_readiness_score": overall_score,
            "readiness_level": level,
            "fit_score": fit_score,
            "fit_gap_score": fit_score,
            "test_score": test_score,
            "online_test_score": test_score,
            "strengths_summary": strengths,
            "top_strengths": strengths,
            "unified_topic_breakdown": unified_topics,
            "unified_topic_readiness": unified_topics,
            "prioritized_revision_plan": revision_plan,
            "targeted_study_plan_next_48h": revision_plan,
            "closed_loop_guidance": "Focus immediate review on dual-weakness topics before re-triggering Round 2 Question Bank generation.",
            "prioritized_topics_for_next_round": next_round_topics,
            "is_failsafe": True,
            "failsafe_reason": error_reason
        }