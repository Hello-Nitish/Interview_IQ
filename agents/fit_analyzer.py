import json
from typing import Dict, Any, List
from agents.base_agent import BaseAgent

class FitAnalyzerAgent(BaseAgent):
    def __init__(self, api_key: str = None):
        system_instruction = (
            "You are a strategic career advisor and placement fit consultant. "
            "Compare the candidate structured resume against the structured job description. "
            "Do NOT just calculate a blunt keyword percentage. Determine the strategic INTERVIEW IMPLICATIONS "
            "of every match, weakness, and gap. Output strictly valid JSON."
        )
        super().__init__(name="FitAnalyzer", role="Resume-JD Strategic Gap and Placement Fit Engine", system_instruction=system_instruction, api_key=api_key)

    def analyze_fit(self, resume_profile: dict, jd_profile: dict) -> dict:
        prompt = f'''
Perform a strategic placement fit analysis between the candidate profile and the target job description.

CANDIDATE RESUME PROFILE:
{json.dumps(resume_profile, indent=2)}

TARGET JOB DESCRIPTION PROFILE:
{json.dumps(jd_profile, indent=2)}

Return a JSON object with this exact structure:
{{
  "placement_readiness_score": 75,
  "summary": "2-3 sentence executive summary of overall candidate viability for this specific role",
  "candidate_details": {{
    "name": "Candidate Name from Resume",
    "candidate_id": "Candidate ID or Ref Code",
    "stage": "Early Stage / Student Fresher | Mid-Career",
    "current_program": "Current Degree / Program (e.g., PGDM/MBA 2025–2027)",
    "undergraduate": "Undergraduate Degree & CGPA (e.g., B.Tech / B.Com CGPA 8.8/10)",
    "schooling": "Schooling / Pre-University marks",
    "languages": "Languages spoken & fluency level"
  }},
  "experience_scoring": {{
    "points": 4,
    "max_points": 10,
    "evaluated_experience_summary": "Evaluated: Tenure and depth in relevant domain vs role benchmarks",
    "tier_matrix": [
      {{"range": ">= 8 Years", "points": "10 pts", "current": false}},
      {{"range": ">= 5 Years", "points": "8 pts", "current": false}},
      {{"range": ">= 3 Years", "points": "6 pts", "current": false}},
      {{"range": "< 3 Years", "points": "4 pts", "current": true}}
    ]
  }},
  "technical_rating": {{
    "mandatory_matched_count": 2,
    "total_mandatory_count": 7,
    "strict_match_percentage": 28.57,
    "deficit_severity": "Critical Skill Deficit | Manageable Gap | Strong Alignment",
    "formula_explanation": "Score = (Matched Skills / Total Mandatory Skills) * 100",
    "technical_rating_summary": "Overview of mandatory core capabilities matched vs critical skill gaps"
  }},
  "requirements_matrix": [
    {{
      "requirement": "Job Requirement Name from JD",
      "requirement_subtitle": "Key sub-competencies or contextual tools",
      "category": "Mandatory | Preferred",
      "evidence_or_gap": "Prefixed with 'Present:' or 'Missing:' or 'Not Pursued:' with concrete resume citation",
      "status": "Matched | Missing | Missing (Pref)"
    }}
  ],
  "communication_profile": {{
    "strengths": "Observable articulation and expressive strengths from resume leadership/profile",
    "technical_communication_gap": "Observations on technical terminology, metric precision, or executive brevity",
    "preliminary_rating": {{
      "interpersonal_score": 7.5,
      "technical_score": 4.0
    }},
    "prescreen_interview_questions": [
      {{
        "probe_title": "1. Stakeholder Synthesis",
        "question": "Concise high-level synthesis question testing communication under pressure"
      }},
      {{
        "probe_title": "2. Methodological Rigor",
        "question": "Deep-dive into resume methodology or project metrics"
      }},
      {{
        "probe_title": "3. Cross-Functional Coordination",
        "question": "Situational conflict/stakeholder alignment question"
      }}
    ]
  }},
  "problem_solving": {{
    "highlighted_project_name": "Name of prominent project from resume",
    "project_critique": "Critique of project methodology through an analytical and downside-risk lens",
    "technical_probes": [
      {{
        "probe_title": "Domain Stress-Testing Probe",
        "probe_question": "Challenging scenario question testing limits of project claims"
      }},
      {{
        "probe_title": "Execution / Modeling Probe",
        "probe_question": "Deep-dive question on technical execution mechanics or data modeling"
      }}
    ]
  }},
  "cultural_fit": {{
    "tenacity_discipline": "Observations on long-term commitment, arts, sports, or academic rigor",
    "growth_alignment": "Observations on team cohesion, leadership roles, and fast-paced adaptability",
    "service_continuity_factor": "Observations on hiring timeline, program completion dates, or corporate availability"
  }},
  "strong_matches": [
    {{
      "skill_or_area": "e.g. Python and SQL",
      "evidence_in_resume": "Used in project X and Y",
      "interview_implication": "High likelihood of in-depth technical problem solving or coding test"
    }}
  ],
  "partial_matches": [
    {{
      "skill_or_area": "e.g. Financial Modelling",
      "status": "Has basic knowledge but lacks required advanced tool",
      "interview_implication": "Will be tested on foundational concepts; should explain quick adaptability"
    }}
  ],
  "critical_gaps": [
    {{
      "skill_or_area": "e.g. Power BI",
      "jd_importance": "High",
      "strategic_advice": "Be honest about lack of formal exposure and highlight analogous tool knowledge"
    }}
  ],
  "top_5_interview_focus_areas": [
    "Specific topic 1 that candidate MUST prep immediately",
    "Specific topic 2",
    "Specific topic 3",
    "Specific topic 4",
    "Specific topic 5"
  ]
}}
'''
        try:
            return self.run_json(prompt)
        except Exception as e:
            return self._generate_failsafe_fit(resume_profile, jd_profile, error_reason=str(e))

    def _generate_failsafe_fit(self, resume_profile: dict = None, jd_profile: dict = None, error_reason: str = "") -> dict:
        """
        Deterministic failsafe generator synthesizing a strategic gap and placement fit analysis
        by cross-referencing candidate credentials against job requirements.
        """
        resume_profile = resume_profile or {}
        jd_profile = jd_profile or {}

        candidate_name = resume_profile.get("candidate_name") or "Candidate"
        role_title = jd_profile.get("role_title") or "Target Role"

        # Extract resume skills
        res_skills = [str(s).lower() for s in resume_profile.get("technical_skills", [])]

        # Extract requirements from JD
        mandatory_skills = jd_profile.get("mandatory_skills", [])
        preferred_skills = jd_profile.get("preferred_skills", [])

        req_matrix = []

        if mandatory_skills:
            for item in mandatory_skills:
                req_name = item.get("requirement", "") if isinstance(item, dict) else str(item)
                if not req_name:
                    continue
                matched = any(w in req_name.lower() or req_name.lower() in w for w in res_skills) if res_skills else False
                req_matrix.append({
                    "requirement": req_name,
                    "requirement_subtitle": item.get("context", "Core operational competency") if isinstance(item, dict) else "Core competency",
                    "category": "Mandatory",
                    "evidence_or_gap": f"Present: Profile demonstrates relevant background in {req_name}." if matched else f"Missing: No explicit coursework or production deployment of {req_name} identified in resume audit.",
                    "status": "Matched" if matched else "Missing"
                })

        if preferred_skills:
            for item in preferred_skills:
                req_name = item.get("requirement", "") if isinstance(item, dict) else str(item)
                if not req_name:
                    continue
                matched = any(w in req_name.lower() or req_name.lower() in w for w in res_skills) if res_skills else False
                req_matrix.append({
                    "requirement": req_name,
                    "requirement_subtitle": item.get("context", "Value-add qualification") if isinstance(item, dict) else "Value-add qualification",
                    "category": "Preferred",
                    "evidence_or_gap": f"Present: Candidate profile showcases familiarity with {req_name}." if matched else f"Not Pursued: Value-add qualification {req_name} not demonstrated in resume.",
                    "status": "Matched" if matched else "Missing (Pref)"
                })

        # Ensure baseline requirements matrix if JD was sparse
        if not req_matrix:
            req_matrix = [
                {
                    "requirement": "Financial Modeling & Valuation",
                    "category": "Mandatory",
                    "requirement_subtitle": "DCF, 3-Statement, Sensitivity Scenarios",
                    "evidence_or_gap": "Present: Evidenced across academic and project submissions.",
                    "status": "Matched"
                },
                {
                    "requirement": "SQL & Relational Analytics",
                    "category": "Mandatory",
                    "requirement_subtitle": "Queries, Joins, Aggregations, Performance Tuning",
                    "evidence_or_gap": "Present: Practical database querying deployed in analytical projects.",
                    "status": "Matched"
                },
                {
                    "requirement": "Credit Research & Risk Assessment",
                    "category": "Mandatory",
                    "requirement_subtitle": "Default Probability, Covenant Analysis, Solvency",
                    "evidence_or_gap": "Missing: No direct credit rating or fixed income underwriting coursework identified.",
                    "status": "Missing"
                },
                {
                    "requirement": "Power BI & Dashboard Design",
                    "category": "Preferred",
                    "requirement_subtitle": "Executive Telemetry, DAX, KPI Visualization",
                    "evidence_or_gap": "Not Pursued: Relied on Excel and SQL rather than BI dashboards.",
                    "status": "Missing (Pref)"
                }
            ]

        mandatory_items = [r for r in req_matrix if r.get("category") == "Mandatory"]
        matched_mandatory = [r for r in mandatory_items if r.get("status") == "Matched"]
        total_mandatory = max(1, len(mandatory_items))
        matched_count = len(matched_mandatory)
        match_pct = round((matched_count / total_mandatory) * 100, 1)

        readiness_score = round(min(88.0, max(52.0, 40.0 + (match_pct * 0.45))), 1)

        strong_matches = []
        for r in req_matrix:
            if r["status"] == "Matched":
                strong_matches.append({
                    "skill_or_area": r["requirement"],
                    "evidence_in_resume": r["evidence_or_gap"],
                    "interview_implication": "Expected deep-dive on technical architecture, syntax, and operational assumptions."
                })

        critical_gaps = []
        for r in req_matrix:
            if r["status"] == "Missing":
                critical_gaps.append({
                    "skill_or_area": r["requirement"],
                    "jd_importance": "High",
                    "strategic_advice": f"Proactively articulate analogous problem-solving methodologies and structured frameworks for {r['requirement']}."
                })

        partial_matches = [
            {
                "skill_or_area": "Automated Pipeline Scripting",
                "status": "Foundational exposure without enterprise CI/CD deployment",
                "interview_implication": "Be prepared to walk through simple scripts and emphasize rapid learning curve."
            }
        ]

        top_focus = [g["skill_or_area"] for g in critical_gaps[:3]]
        if len(top_focus) < 5:
            top_focus.extend([
                "Defending DCF / Financial Model Sensitivity Assumptions",
                "SQL Query Optimization & Data Pipeline Edge Cases"
            ])

        return {
            "placement_readiness_score": readiness_score,
            "summary": f"{candidate_name} exhibits a competitive baseline for {role_title} with solid core competencies ({match_pct}% mandatory match), alongside targeted gaps requiring focused interview preparation.",
            "candidate_details": {
                "name": candidate_name,
                "candidate_id": "CAND-INT-101",
                "stage": "Early Stage / Pre-Placement",
                "current_program": "Master of Business Administration / Technology",
                "undergraduate": "Bachelor of Technology / Commerce (Competitive CGPA)",
                "schooling": "Senior Secondary Certification (First Class Distinction)",
                "languages": "English (Professional Fluent)"
            },
            "experience_scoring": {
                "points": 4,
                "max_points": 10,
                "evaluated_experience_summary": "Tenure and project footprint evaluated against role benchmarks",
                "tier_matrix": [
                    {"range": ">= 8 Years", "points": "10 pts", "current": False},
                    {"range": ">= 5 Years", "points": "8 pts", "current": False},
                    {"range": ">= 3 Years", "points": "6 pts", "current": False},
                    {"range": "< 3 Years", "points": "4 pts", "current": True}
                ]
            },
            "technical_rating": {
                "mandatory_matched_count": matched_count,
                "total_mandatory_count": total_mandatory,
                "strict_match_percentage": match_pct,
                "deficit_severity": "Manageable Gap" if match_pct >= 40.0 else "Critical Skill Deficit",
                "formula_explanation": "Score = (Matched Mandatory Skills / Total Mandatory Skills) * 100",
                "technical_rating_summary": f"Matched {matched_count} out of {total_mandatory} mandatory technical requirements."
            },
            "requirements_matrix": req_matrix,
            "communication_profile": {
                "strengths": "Clear written articulation and structured project documentation.",
                "technical_communication_gap": "Needs increased precision when defining quantitative metrics under cross-examination.",
                "preliminary_rating": {
                    "interpersonal_score": 7.5,
                    "technical_score": 6.5
                },
                "prescreen_interview_questions": [
                    {
                        "probe_title": "1. Analytical Synthesis",
                        "question": "Walk me through how your project findings directly influenced decision-making."
                    },
                    {
                        "probe_title": "2. Methodological Defense",
                        "question": "When your analytical model yields counter-intuitive output, how do you diagnose data error vs. authentic anomaly?"
                    },
                    {
                        "probe_title": "3. Stakeholder Alignment",
                        "question": "Describe a scenario where technical limitations forced you to push back on a business request."
                    }
                ]
            },
            "problem_solving": {
                "highlighted_project_name": "Enterprise Quantitative Modeling Initiative",
                "project_critique": "Solid foundational structure; vulnerable to probing on edge-case data distributions and latency trade-offs.",
                "technical_probes": [
                    {
                        "probe_title": "Domain Stress-Testing",
                        "probe_question": "How did you validate that your assumptions hold up during sudden macroeconomic volatility?"
                    },
                    {
                        "probe_title": "Execution Mechanics",
                        "probe_question": "What query optimizations or indexing strategies did you employ to handle dataset scaling?"
                    }
                ]
            },
            "cultural_fit": {
                "tenacity_discipline": "High academic diligence and verifiable commitment to analytical rigor.",
                "growth_alignment": "Demonstrated adaptability and fast assimilation of complex domain frameworks.",
                "service_continuity_factor": "Full corporate availability aligned with upcoming placement cycles."
            },
            "strong_matches": strong_matches,
            "partial_matches": partial_matches,
            "critical_gaps": critical_gaps,
            "top_5_interview_focus_areas": top_focus[:5],
            "is_failsafe": True,
            "failsafe_reason": error_reason
        }