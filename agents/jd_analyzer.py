import json
import re
from typing import Dict, Any, List
from agents.base_agent import BaseAgent

class JDAnalyzerAgent(BaseAgent):
    def __init__(self, api_key: str = None):
        system_instruction = (
            "You are a talent acquisition specialist and corporate hiring manager. "
            "Your job is to dissect Job Descriptions (JDs) to extract true hiring requirements. "
            "Prioritize skills by how likely they will be vigorously tested in real-world interviews. "
            "Output strictly valid JSON."
        )
        super().__init__(name="JDAnalyzer", role="Job Description Dissector and Priority Mapper", system_instruction=system_instruction, api_key=api_key)

    def analyze_jd(self, jd_text: str) -> dict:
        prompt = f'''
Dissect the following Job Description (JD) into structured technical and organizational requirements.

JOB DESCRIPTION:
{jd_text}

Return a JSON object with this exact structure:
{{
  "role_title": "Target role title",
  "company_name": "Company name or Not Specified",
  "experience_level": "Entry / Mid / Senior",
  "mandatory_skills": [
    {{"requirement": "Mandatory capability name", "context": "How it is used on the desk"}}
  ],
  "preferred_skills": [
    {{"requirement": "Preferred qualification or tool", "context": "Why it is value-add"}}
  ],
  "required_technical_skills": [
    {{"skill": "Skill name", "priority": "High | Medium | Low", "context": "Usage context in role"}}
  ],
  "required_tools_and_platforms": ["Tool 1", "Tool 2"],
  "domain_knowledge": ["Domain 1", "Domain 2"],
  "soft_skills": ["Communication", "Problem Solving"],
  "top_interview_priority_areas": [
    "Most heavily weighted concept/skill interviewer will focus on 1",
    "Most heavily weighted concept/skill interviewer will focus on 2",
    "Most heavily weighted concept/skill interviewer will focus on 3"
  ]
}}
'''
        try:
            return self.run_json(prompt)
        except Exception as e:
            return self._generate_failsafe_jd(jd_text, error_reason=str(e))

    def _generate_failsafe_jd(self, jd_text: str = "", error_reason: str = "") -> dict:
        """
        Deterministic failsafe generator creating structured JD intelligence
        when LLM extraction or parsing encounters an exception.
        """
        text = jd_text or ""
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        role_title = "Senior Business / Technical Analyst"
        company_name = "Target Enterprise"

        # Heuristic role extraction
        for line in lines[:5]:
            lower = line.lower()
            if any(term in lower for term in ["analyst", "engineer", "associate", "consultant", "manager", "specialist"]):
                role_title = line.split(":")[-1].strip() if ":" in line else line
                break

        # Heuristic company extraction
        for line in lines[:8]:
            lower = line.lower()
            if "company" in lower or "at " in lower or "about " in lower:
                clean = re.sub(r'(?i)(company|about us|about|at)\s*[:\-]?\s*', '', line).strip()
                if clean and len(clean) < 50:
                    company_name = clean
                    break

        return {
            "role_title": role_title,
            "company_name": company_name,
            "experience_level": "Mid-Level Professional",
            "mandatory_skills": [
                {
                    "requirement": "Quantitative Problem Solving & Data Analysis",
                    "context": "Dissecting business problems into structured numerical models and hypotheses."
                },
                {
                    "requirement": "SQL & Relational Database Ingestion",
                    "context": "Executing performant queries, joins, and aggregates across transactional tables."
                },
                {
                    "requirement": "Financial Modeling & Sensitivity Analysis",
                    "context": "Constructing scenario forecasting, variance tracking, and DCF/P&L impact models."
                },
                {
                    "requirement": "Executive Presentation & Stakeholder Synthesis",
                    "context": "Translating technical analyses into actionable C-level strategic summaries."
                }
            ],
            "preferred_skills": [
                {
                    "requirement": "Python / R Scripting & Automation",
                    "context": "Developing automated data pipelines and ETL transformation scripts."
                },
                {
                    "requirement": "Business Intelligence (Power BI / Tableau)",
                    "context": "Building interactive visual dashboards for cross-departmental telemetry."
                }
            ],
            "required_technical_skills": [
                {
                    "skill": "Financial Modeling & Sensitivity Analysis",
                    "priority": "High",
                    "context": "Constructing multi-scenario projections and stress-testing assumptions."
                },
                {
                    "skill": "SQL & Relational Analytics",
                    "priority": "High",
                    "context": "Designing clean queries to validate source-of-truth data integrity."
                },
                {
                    "skill": "Quantitative Problem Solving",
                    "priority": "High",
                    "context": "Applying first-principles thinking to resolve operational trade-offs."
                },
                {
                    "skill": "Process Automation (Python/Excel)",
                    "priority": "Medium",
                    "context": "Eliminating repetitive reconciliations via reproducible scripting."
                }
            ],
            "required_tools_and_platforms": ["SQL", "Advanced Excel", "Power BI / Tableau", "Git"],
            "domain_knowledge": ["Financial Statement Analysis", "Risk Assessment & Mitigation", "Business Process Optimization"],
            "soft_skills": ["Structured Communication", "Critical Thinking", "Stakeholder Alignment"],
            "top_interview_priority_areas": [
                "Rigorous empirical defense of model assumptions and downside risk scenarios.",
                "Technical query construction, schema optimization, and ledger-grain reconciliation.",
                "Cross-functional communication under ambiguous operational constraints."
            ],
            "is_failsafe": True,
            "failsafe_reason": error_reason
        }