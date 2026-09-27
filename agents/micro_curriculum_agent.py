"""
agents/micro_curriculum_agent.py
Phase 25C: Dynamic 7-Day Personalized Micro-Curriculum Agent with Curated Course Resources.
Transforms diagnosed placement gaps into a structured day-by-day learning journey.
Integrates static curated free resources from YouTube, Coursera (free audit), Mode Analytics, Kaggle, and Cheat Sheets.
"""

import json
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from utils.curriculum_resources import CurriculumResourceLibrary

class MicroCurriculumAgent(BaseAgent):
    """
    Adaptive 7-Day Placement Remediation Curriculum Architect.
    Maps diagnostic weaknesses from the Unified Diagnostic Report into an actionable 7-day study plan.
    Enriches each day with curated free videos, interactive drills, official documentation, and cheat sheets.
    """

    def __init__(self, api_key: Optional[str] = None):
        system_instruction = (
            "You are an expert placement coach, dean of career services, and curriculum architect. "
            "You design compact, achievable day-by-day study schedules that target diagnosed candidate weaknesses "
            "to maximize corporate placement readiness within exactly 7 days. "
            "Assign intensive focus to HIGH PRIORITY topics in Days 1-3. "
            "Use Days 4-5 for medium-priority consolidation and domain depth. "
            "Day 6 is reserved for mixed case analysis and interactive practice. "
            "Day 7 is the full mock assessment dress rehearsal. "
            "Keep daily time commitments realistic (1.5 to 2.5 hours). "
            "Output strictly valid JSON."
        )
        super().__init__(
            name="MicroCurriculumAgent",
            role="Adaptive 7-Day Placement Curriculum Architect",
            system_instruction=system_instruction,
            api_key=api_key
        )

    def generate_curriculum(
        self,
        weak_topics: Optional[List[Dict[str, Any]]] = None,
        jd_profile: Optional[Dict[str, Any]] = None,
        composite_score: float = 65.0,
        round_number: int = 1
    ) -> Dict[str, Any]:
        """
        Synthesizes an authentic 7-day personalized micro-curriculum.
        Extracts high/medium priority topics and binds curated free learning assets to each day.
        """
        jd = jd_profile or {}
        role_title = jd.get("role_title", "Candidate Placement Track")
        company_name = jd.get("company_name", "Corporate Placement Partner")

        # Parse weak topics: separate High Priority from Medium Priority
        high_prio_topics = []
        med_prio_topics = []

        if weak_topics:
            for item in weak_topics:
                if isinstance(item, dict):
                    t_name = item.get("topic", "")
                    prio = str(item.get("priority", "")).lower()
                    if "high" in prio or item.get("is_dual_weakness", False):
                        high_prio_topics.append(t_name)
                    else:
                        med_prio_topics.append(t_name)
                elif isinstance(item, str):
                    high_prio_topics.append(item)

        # Ensure fallback topics if list is sparse
        if not high_prio_topics:
            high_prio_topics = ["SQL & Relational Databases", "Data Visualization & Dashboarding"]
        if not med_prio_topics:
            med_prio_topics = ["Cloud Concepts (AWS)", "Product Strategy & Metrics"]

        prompt = f"""
Role: {role_title} at {company_name}
Candidate Placement Readiness Score: {composite_score:.1f}% (Round {round_number})
High Priority Weak Topics (Days 1-3 focus): {', '.join(high_prio_topics[:4])}
Medium Priority Topics (Days 4-5 focus): {', '.join(med_prio_topics[:4])}

Design an executive 7-day study plan:
- Days 1-3: Deep-dive intensive drills on High Priority deficits.
- Days 4-5: Systemic review of Medium Priority concepts.
- Day 6: Targeted Question Bank Probes & Behavioral STAR Drill (connects to Step 3 Question Bank).
- Day 7: Full Mock Assessment Dress Rehearsal (connects to Step 4 30-MCQ Exam).

Also generate an 'emergency_sprint' (compressed 2-day plan for students interviewing in 48 hours).

Return STRICT valid JSON:
{{
  "plan_title": "7-Day Placement Mastery Plan — {role_title}",
  "target_role": "{role_title}",
  "total_hours_commitment": 14.5,
  "days": [
    {{
      "day_number": 1,
      "theme": "Theme title...",
      "focus_topics": ["Topic 1", "Topic 2"],
      "learning_objective": "Concrete verifiable objective...",
      "time_allocation_hours": 2.5,
      "activities": [
        "Review syntax and core operators (45 mins)",
        "Solve 10 practice problems (60 mins)",
        "Review cheat sheet and test notes (45 mins)"
      ],
      "milestone_checkpoint": "Verifiable outcome (e.g. solve 10 intermediate queries error-free)"
    }}
  ],
  "emergency_sprint": {{
    "day_1": {{
      "theme": "Critical Vulnerability Triage (High Priority Deficits)",
      "time_hours": 3.5,
      "core_actions": ["Action 1", "Action 2", "Action 3"]
    }},
    "day_2": {{
      "theme": "Executive Narrative & Mock Simulation Rehearsal",
      "time_hours": 3.0,
      "core_actions": ["Action 1", "Action 2", "Action 3"]
    }}
  }}
}}
"""
        plan = None
        try:
            res = self.run_json(prompt)
            if isinstance(res, dict) and "days" in res and len(res.get("days", [])) == 7:
                plan = res
        except Exception:
            pass

        # Robust Fallback 7-Day Plan (Deterministic execution)
        if not plan:
            t1 = high_prio_topics[0] if high_prio_topics else "SQL & Relational Databases"
            t2 = high_prio_topics[1] if len(high_prio_topics) > 1 else "Data Manipulation with Python"
            t3 = high_prio_topics[2] if len(high_prio_topics) > 2 else "Statistics & Business Metrics"
            t4 = med_prio_topics[0] if med_prio_topics else "Cloud Architecture Concepts"
            t5 = med_prio_topics[1] if len(med_prio_topics) > 1 else "Strategic Frameworks & Agile"

            plan = {
                "plan_title": f"7-Day Placement Acceleration Plan — {role_title}",
                "target_role": role_title,
                "total_hours_commitment": 14.0,
                "days": [
                    {
                        "day_number": 1,
                        "theme": f"Critical Deficit Deep-Dive: {t1}",
                        "focus_topics": [t1],
                        "learning_objective": f"Eliminate core conceptual ambiguities in {t1} through video immersion and hands-on queries.",
                        "time_allocation_hours": 2.5,
                        "activities": [
                            f"Watch core video tutorial on {t1} (60 mins)",
                            "Complete 10 hands-on practice problems on Mode / LeetCode (60 mins)",
                            "Summarize key definitions and edge cases into an interview flashcard (30 mins)"
                        ],
                        "milestone_checkpoint": f"Complete 10 hands-on exercises in {t1} with zero syntax errors."
                    },
                    {
                        "day_number": 2,
                        "theme": f"High-Priority Focus: {t2}",
                        "focus_topics": [t2],
                        "learning_objective": f"Master practical problem-solving patterns and industry workflows for {t2}.",
                        "time_allocation_hours": 2.0,
                        "activities": [
                            f"Review official documentation and core patterns for {t2} (45 mins)",
                            "Execute interactive coding or design exercises (50 mins)",
                            "Review cheat sheet for quick reference during interviews (25 mins)"
                        ],
                        "milestone_checkpoint": f"Build a clean end-to-end working example demonstrating {t2} capabilities."
                    },
                    {
                        "day_number": 3,
                        "theme": f"Analytical Rigor & Metrics: {t3}",
                        "focus_topics": [t3],
                        "learning_objective": f"Strengthen quantitative decision-making and metric estimation under {t3}.",
                        "time_allocation_hours": 2.0,
                        "activities": [
                            "Review statistical hypothesis testing, p-values, and conversion metrics (45 mins)",
                            "Solve 5 business case sizing and estimation calculations (50 mins)",
                            "Audit resume project bullets to ensure all claims in this domain are quantified (25 mins)"
                        ],
                        "milestone_checkpoint": "Articulate 3 business impact metrics using exact numerical formulas."
                    },
                    {
                        "day_number": 4,
                        "theme": f"Platform & Infrastructure Review: {t4}",
                        "focus_topics": [t4],
                        "learning_objective": f"Bridge theoretical knowledge with enterprise deployment in {t4}.",
                        "time_allocation_hours": 1.5,
                        "activities": [
                            f"Watch cloud architecture overview covering core services (45 mins)",
                            "Review trade-offs between cost, latency, and scalability (30 mins)",
                            "Study service architecture diagrams and cheat sheets (15 mins)"
                        ],
                        "milestone_checkpoint": f"Explain 3 architectural trade-offs in {t4} to an executive interviewer."
                    },
                    {
                        "day_number": 5,
                        "theme": f"Management, Strategy & Methodologies: {t5}",
                        "focus_topics": [t5],
                        "learning_objective": f"Adopt structured business frameworking (MECE, CIRCLES, Agile) for {t5}.",
                        "time_allocation_hours": 2.0,
                        "activities": [
                            "Review McKinsey MECE and Victor Cheng problem breakdown frameworks (45 mins)",
                            "Practice structuring 3 ambiguous business problems into mutually exclusive buckets (45 mins)",
                            "Review Agile/Scrum ceremonies, sprint planning, and backlog grooming (30 mins)"
                        ],
                        "milestone_checkpoint": "Structure an ambiguous operational dilemma into a 3-pillar tree in under 3 minutes."
                    },
                    {
                        "day_number": 6,
                        "theme": "Targeted Question Bank Review & Behavioral STAR Probes",
                        "focus_topics": ["Behavioral STAR", "Technical Probes"],
                        "learning_objective": "Stress-test structured thinking and behavioral STAR storytelling against targeted interview probes.",
                        "time_allocation_hours": 2.0,
                        "activities": [
                            "Review Step 3 Question Bank probes targeting critical and moderate gaps (45 mins)",
                            "Draft 3 behavioral STAR stories mapping to target company leadership principles (45 mins)",
                            "Practice explaining technical trade-offs with structured frameworks (30 mins)"
                        ],
                        "milestone_checkpoint": "Confidently master all Step 3 mandatory and gap-mitigation probes."
                    },
                    {
                        "day_number": 7,
                        "theme": "Full Placement Dress Rehearsal & Multi-Round Verification",
                        "focus_topics": ["Timed Online Test", "Voice Interview Simulation"],
                        "learning_objective": "Validate longitudinal score lift across both empirical testing and live verbal cadence.",
                        "time_allocation_hours": 2.0,
                        "activities": [
                            "Retake Step 4 Timed 30-MCQ Test to verify score improvement on weak topics (45 mins)",
                            "Conduct a 4-turn Live Voice Interview Simulator session with speech analytics (35 mins)",
                            "Download and review updated Corporate Placement PDF Dossier for final revision (40 mins)"
                        ],
                        "milestone_checkpoint": "Demonstrate a verified +10% score lift in Step 5 Unified Diagnostics."
                    }
                ],
                "emergency_sprint": {
                    "day_1": {
                        "theme": "Emergency Day 1: High-Priority Gap Elimination",
                        "time_hours": 3.5,
                        "core_actions": [
                            f"Watch 60-min crash course on {t1} and {t2}.",
                            "Memorize syntax, formulas, and key cheat sheet definitions.",
                            "Draft 3 concrete STAR stories for your most scrutinized resume projects."
                        ]
                    },
                    "day_2": {
                        "theme": "Emergency Day 2: Simulation Dress Rehearsal & Delivery",
                        "time_hours": 3.0,
                        "core_actions": [
                            "Review Step 3 Targeted Question Bank probes to calibrate structured delivery.",
                            "Execute Step 4 Voice Interview to eliminate verbal filler words and lock in pacing.",
                            "Review target company leadership principles and memorize 3 quantitative proof points."
                        ]
                    }
                }
            }

        # Enrich every single day with static curated resources from CurriculumResourceLibrary
        for day in plan.get("days", []):
            topics = day.get("focus_topics", [])
            day_resources = []
            seen_ids = set()
            for t in topics:
                res_list = CurriculumResourceLibrary.get_resources(t)
                for r in res_list:
                    if r["resource_id"] not in seen_ids:
                        seen_ids.add(r["resource_id"])
                        day_resources.append(r)
            day["resources"] = day_resources[:4]  # Maximum 4 curated resources per day

        return plan
