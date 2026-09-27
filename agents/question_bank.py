import json
from agents.base_agent import BaseAgent

class QuestionBankAgent(BaseAgent):
    def __init__(self, api_key: str = None):
        system_instruction = (
            "You are a principal technical interviewer and corporate assessment designer. "
            "Your mission is to construct an exhaustive, role-tailored question bank based on a complete "
            "JD Topic Checklist. Every single requirement from the JD must be rigorously tested — "
            "not just candidate weak spots. "
            "Classify topics as Gap (JD requires, resume lacks), Claimed (resume asserts, test depth), "
            "or Untested (foundational concept candidate must know). Output strictly valid JSON."
        )
        super().__init__(name="QuestionBank", role="Exhaustive JD-Coverage Question Bank Generator", system_instruction=system_instruction, api_key=api_key)

    def extract_topic_checklist(self, jd_profile: dict, resume_profile: dict = None, fit_profile: dict = None, prioritized_topics: list = None) -> list:
        """
        Builds an exhaustive topic checklist from all sections of the JD profile,
        then classifies each topic against the resume and fit-gap analysis as Gap, Claimed, or Untested.
        """
        if fit_profile is None and resume_profile is not None and ("requirements_matrix" in resume_profile or "critical_gaps" in resume_profile):
            fit_profile = resume_profile
            resume_profile = {}

        jd_profile = jd_profile or {}
        resume_profile = resume_profile or {}
        fit_profile = fit_profile or {}
        prioritized_topics = prioritized_topics or []

        checklist = []
        seen = set()

        def add_topic(name: str, category: str):
            clean_name = str(name).strip()
            if not clean_name:
                return
            key = clean_name.lower()
            if key in seen:
                return
            seen.add(key)
            checklist.append({"topic": clean_name, "category": category})

        # 1. Mandatory Skills
        for item in jd_profile.get("mandatory_skills", []):
            req = item.get("requirement", "") if isinstance(item, dict) else str(item)
            add_topic(req, "Mandatory Capability")

        # 2. Preferred Skills
        for item in jd_profile.get("preferred_skills", []):
            req = item.get("requirement", "") if isinstance(item, dict) else str(item)
            add_topic(req, "Preferred Qualification")

        # 3. Required Technical Skills
        for item in jd_profile.get("required_technical_skills", []):
            skill = item.get("skill", "") if isinstance(item, dict) else str(item)
            add_topic(skill, "Technical Skill")

        # 4. Required Tools & Platforms / Frameworks
        for tool in jd_profile.get("required_tools_and_platforms", []) + jd_profile.get("required_tools_and_frameworks", []):
            add_topic(tool, "Tool / Platform")

        # 5. Domain Knowledge & Competencies
        for dom in jd_profile.get("domain_knowledge", []) + jd_profile.get("required_domain_competencies", []):
            add_topic(dom, "Domain Knowledge")

        # 6. Soft Skills
        for soft in jd_profile.get("soft_skills", []):
            add_topic(soft, "Professional Competency")

        # Fallback if JD extraction was sparse
        if not checklist:
            checklist = [
                {"topic": "Core Analytical Thinking", "category": "Technical Skill"},
                {"topic": "Domain Business Understanding", "category": "Domain Knowledge"},
                {"topic": "Data & Numerical Literacy", "category": "Tool / Platform"},
                {"topic": "Structured Executive Communication", "category": "Professional Competency"}
            ]

        # Gather known gaps and claimed areas for classification
        gap_keywords = set()
        for g in fit_profile.get("critical_gaps", []):
            name = g.get("skill_or_area", "") if isinstance(g, dict) else str(g)
            gap_keywords.add(name.lower())
        for row in fit_profile.get("requirements_matrix", []):
            if "missing" in str(row.get("status", "")).lower() or "gap" in str(row.get("status", "")).lower():
                gap_keywords.add(str(row.get("requirement", "")).lower())

        claimed_keywords = set()
        for m in fit_profile.get("strong_matches", []):
            name = m.get("skill_or_area", "") if isinstance(m, dict) else str(m)
            claimed_keywords.add(name.lower())
        for row in fit_profile.get("requirements_matrix", []):
            if "matched" in str(row.get("status", "")).lower():
                claimed_keywords.add(str(row.get("requirement", "")).lower())
        for s in resume_profile.get("technical_skills", []):
            claimed_keywords.add(str(s).lower())
        for p in resume_profile.get("projects", []):
            p_name = p.get("title", "") if isinstance(p, dict) else str(p)
            claimed_keywords.add(p_name.lower())

        # Classify each topic and assign weights
        for item in checklist:
            t_lower = item["topic"].lower()
            is_gap = any(gk in t_lower or t_lower in gk for gk in gap_keywords if gk)
            is_claimed = any(ck in t_lower or t_lower in ck for ck in claimed_keywords if ck)

            if is_gap:
                classification = "Gap"
            elif is_claimed:
                classification = "Claimed"
            else:
                classification = "Untested"

            item["classification"] = classification
            item["topic_name"] = item["topic"]
            item["status"] = classification

            is_prio = any(pt.lower() in t_lower or t_lower in pt.lower() for pt in prioritized_topics if pt)
            if is_prio:
                item["weight"] = 2.5
            elif classification == "Gap":
                item["weight"] = 2.0
            elif classification == "Untested":
                item["weight"] = 1.5
            else:
                item["weight"] = 1.0

        return checklist

    def generate_questions(self, resume_profile: dict, jd_profile: dict, fit_profile: dict, prioritized_topics: list = None) -> dict:
        topic_checklist = self.extract_topic_checklist(jd_profile, resume_profile, fit_profile, prioritized_topics=prioritized_topics)
        
        prioritization_instruction = ""
        if prioritized_topics:
            prioritization_instruction = (
                f"\nIMPORTANT - CLOSED-LOOP RE-WEIGHTING ACTIVE:\n"
                f"The candidate recently completed an assessment that flagged the following topics as critical deficits:\n"
                f"{json.dumps(prioritized_topics, indent=2)}\n"
                f"You MUST generate deeper, advanced drill-down questions specifically targeting these weak topics.\n"
            )

        prompt = f'''
Construct an exhaustive, role-tailored interview preparation question bank that covers the COMPLETE JD Topic Checklist.

TOPIC CHECKLIST (All {len(topic_checklist)} topics must be covered):
{json.dumps(topic_checklist, indent=2)}
{prioritization_instruction}
RESUME PROFILE:
{json.dumps(resume_profile, indent=2)}

FIT / GAP SUMMARY:
{json.dumps(fit_profile, indent=2)}

REQUIREMENTS:
1. EVERY topic on the checklist MUST be covered by at least one question.
2. Tag EVERY question with the specific JD topic or topics it covers (`topics_covered`: ["Topic Name"]).
3. Balance across the 5 dimensions:
   - `resume_based_questions`: Probe claimed skills, project architecture, and trade-offs.
   - `technical_questions`: Role-specific technical mastery and implementation.
   - `conceptual_questions`: Underlying principles, models, and analytical frameworks.
   - `problem_solving_questions`: Complex business or engineering scenarios.
   - `behavioral_questions`: STAR situational questions testing competencies.
4. Output a `coverage_summary` confirming that all {len(topic_checklist)} JD topics are covered.

Return a JSON object with this exact structure:
{{
  "topic_checklist": [
    {{
      "topic": "Topic Name",
      "category": "Category",
      "classification": "Gap | Claimed | Untested",
      "questions_count": 2
    }}
  ],
  "coverage_summary": {{
    "total_jd_topics": {len(topic_checklist)},
    "covered_topics_count": {len(topic_checklist)},
    "all_jd_topics_covered": true,
    "uncovered_topics": []
  }},
  "resume_based_questions": [
    {{
      "question": "Detailed probe on project or claimed experience",
      "topics_covered": ["Specific Topic Name"],
      "target_claim": "Referenced project/role",
      "priority": "High | Medium",
      "guidance": "Key points candidate must address to defend claim"
    }}
  ],
  "technical_questions": [
    {{
      "question": "Technical problem or engineering query",
      "topics_covered": ["Specific Topic Name"],
      "priority": "High | Medium",
      "ideal_answer_framework": "Core technical principles and optimal approach"
    }}
  ],
  "conceptual_questions": [
    {{
      "question": "Conceptual theory, paradigm, or trade-off evaluation",
      "topics_covered": ["Specific Topic Name"],
      "priority": "High | Medium",
      "core_concept": "Key theoretical foundation"
    }}
  ],
  "problem_solving_questions": [
    {{
      "scenario": "Hypothetical business crisis or operational challenge",
      "topics_covered": ["Specific Topic Name"],
      "priority": "High | Medium",
      "evaluation_criteria": "How to structure the solution and mitigate risk"
    }}
  ],
  "behavioral_questions": [
    {{
      "question": "STAR situational inquiry",
      "topics_covered": ["Specific Topic Name"],
      "competency": "Leadership / Adaptability / Conflict Resolution",
      "priority": "High | Medium"
    }}
  ]
}}
'''
        try:
            result = self.run_json(prompt)
            return self._ensure_checklist_integrity(result, topic_checklist)
        except Exception as e:
            return self._generate_failsafe_question_bank(topic_checklist, jd_profile, resume_profile, str(e))

    def _ensure_checklist_integrity(self, result: dict, source_checklist: list) -> dict:
        """
        Validates that all topics from source_checklist are represented.
        Tallies question counts per topic and injects any missing topics.
        """
        all_questions = []
        for cat in ["resume_based_questions", "technical_questions", "conceptual_questions", "problem_solving_questions", "behavioral_questions"]:
            all_questions.extend(result.get(cat, []))

        # Count questions per topic
        topic_counts = {}
        for q in all_questions:
            for t in q.get("topics_covered", []):
                topic_counts[t.lower()] = topic_counts.get(t.lower(), 0) + 1

        updated_checklist = []
        uncovered = []
        for item in source_checklist:
            t_name = item["topic"]
            count = topic_counts.get(t_name.lower(), 0)
            if count == 0:
                uncovered.append(t_name)
                count = 1
                fallback_q = {
                    "question": f"Walk us through your working knowledge and practical application of {t_name}.",
                    "topics_covered": [t_name],
                    "priority": "High" if item["classification"] == "Gap" else "Medium",
                    "ideal_answer_framework": f"Define {t_name}, discuss business/technical context, and provide a concrete implementation example."
                }
                result.setdefault("technical_questions", []).append(fallback_q)

            updated_checklist.append({
                "topic": t_name,
                "topic_name": t_name,
                "category": item.get("category", "Technical Skill"),
                "classification": item.get("classification", "Untested"),
                "status": item.get("classification", "Untested"),
                "weight": item.get("weight", 1.0),
                "questions_count": count,
                "question_count": count
            })

        tot_q = (
            len(result.get("technical_questions", []))
            + len(result.get("resume_based_questions", []))
            + len(result.get("problem_solving_questions", []))
            + len(result.get("behavioral_questions", []))
            + len(result.get("gap_mitigation_questions", []))
            + len(result.get("conceptual_questions", []))
        )

        result["topic_checklist"] = updated_checklist
        result["coverage_summary"] = {
            "total_jd_topics": len(source_checklist),
            "covered_topics": len(source_checklist),
            "covered_topics_count": len(source_checklist),
            "coverage_percentage": 100.0,
            "total_questions": tot_q,
            "all_jd_topics_covered": True,
            "uncovered_topics": []
        }
        return result

    def _generate_failsafe_question_bank(self, topic_checklist = None, jd_profile = None, resume_profile = None, fit_profile = None, error_reason: str = "") -> dict:
        """Failsafe generator that creates a structured question bank guaranteeing 100% topic coverage."""
        # Flexible argument handling: find the list among arguments
        actual_checklist = None
        for arg in [topic_checklist, jd_profile, resume_profile, fit_profile]:
            if isinstance(arg, list):
                actual_checklist = arg
                break

        if actual_checklist is None:
            actual_checklist = self.extract_topic_checklist(
                jd_profile if isinstance(jd_profile, dict) else {},
                resume_profile if isinstance(resume_profile, dict) else {},
                fit_profile if isinstance(fit_profile, dict) else {}
            )
        topic_checklist = actual_checklist

        resume_qs = []
        tech_qs = []
        concept_qs = []
        ps_qs = []
        behav_qs = []

        checklist_summary = []
        for idx, item in enumerate(topic_checklist):
            if isinstance(item, str):
                topic = item
                cat = "Technical Capability"
                cls = "Untested"
                weight = 1.5
            elif isinstance(item, dict):
                topic = item.get("topic") or item.get("topic_name", f"Topic {idx+1}")
                cat = item.get("category", "Technical Capability")
                cls = item.get("classification") or item.get("status", "Untested")
                weight = item.get("weight", 2.0 if cls == "Gap" else (1.5 if cls == "Untested" else 1.0))
            else:
                topic = str(item)
                cat = "Technical Capability"
                cls = "Untested"
                weight = 1.5

            if cls == "Claimed":
                resume_qs.append({
                    "question": f"In your past projects, how specifically did you apply {topic}? What were the performance trade-offs?",
                    "topics_covered": [topic],
                    "topic_tag": topic,
                    "target_claim": f"Claimed experience in {topic}",
                    "priority": "High",
                    "guidance": "Defend methodology, quantify results, and address edge cases."
                })
            elif cls == "Gap":
                tech_qs.append({
                    "question": f"The role mandates deep familiarity with {topic}. How would you execute an end-to-end task leveraging this competency?",
                    "topics_covered": [topic],
                    "topic_tag": topic,
                    "priority": "High",
                    "skill_tested": topic,
                    "ideal_answer_framework": f"Explain key mechanics of {topic}, standard industry workflows, and mitigation of common pitfalls."
                })
            else: # Untested
                concept_qs.append({
                    "question": f"What are the foundational principles of {topic}, and how does it interface with broader system or business goals?",
                    "topics_covered": [topic],
                    "topic_tag": topic,
                    "priority": "Medium",
                    "skill_tested": topic,
                    "core_concept": f"Conceptual foundation and architectural role of {topic}",
                    "ideal_answer_framework": f"Define {topic}, its role in system design, and practical implications."
                })

            if idx % 3 == 0:
                ps_qs.append({
                    "scenario": f"Suppose a critical failure or bottleneck arises in relation to {topic}. How would you systematically diagnose and resolve it?",
                    "topics_covered": [topic],
                    "topic_tag": topic,
                    "priority": "High",
                    "evaluation_criteria": "Structured root-cause diagnosis, stakeholder communication, and post-mortem review."
                })
            elif idx % 4 == 0:
                behav_qs.append({
                    "question": f"Describe a time you had to deliver high-quality outcomes involving {topic} under aggressive deadlines.",
                    "topics_covered": [topic],
                    "topic_tag": topic,
                    "competency": "Execution under Pressure",
                    "priority": "Medium"
                })

            checklist_summary.append({
                "topic": topic,
                "topic_name": topic,
                "category": cat,
                "classification": cls,
                "status": cls,
                "weight": weight,
                "questions_count": 1 + (1 if idx % 3 == 0 or idx % 4 == 0 else 0)
            })

        total_q = len(resume_qs) + len(tech_qs) + len(concept_qs) + len(ps_qs) + len(behav_qs)

        return {
            "topic_checklist": checklist_summary,
            "coverage_summary": {
                "total_jd_topics": len(topic_checklist),
                "covered_topics": len(topic_checklist),
                "covered_topics_count": len(topic_checklist),
                "coverage_percentage": 100.0,
                "total_questions": total_q,
                "all_jd_topics_covered": True,
                "uncovered_topics": []
            },
            "resume_based_questions": resume_qs,
            "technical_questions": tech_qs + concept_qs,
            "conceptual_questions": concept_qs,
            "problem_solving_questions": ps_qs,
            "behavioral_questions": behav_qs,
            "is_failsafe": True,
            "failsafe_reason": error_reason
        }