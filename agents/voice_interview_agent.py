import json
from agents.base_agent import BaseAgent
from utils.speech_analytics import SpeechAnalyticsEngine

class VoiceInterviewAgent(BaseAgent):
    """
    Adaptive Conversational Voice Interviewer Agent.
    Conducts multi-turn conversational mock interviews with live verbal interaction,
    STAR methodology compliance evaluation, adaptive probing, and speech delivery analytics.
    """

    def __init__(self, api_key: str = None):
        system_instruction = (
            "You are an executive hiring director and talent acquisition leader conducting a rigorous, "
            "competency-grounded job interview. "
            "You ask challenging, conversational scenario questions based on the candidate's resume and job description. "
            "When the candidate gives vague, high-level answers, you probe deeply for specifics, trade-offs, metrics, and STAR details. "
            "You evaluate both the substantive domain content and verbal executive presence. "
            "Output strictly valid JSON."
        )
        super().__init__(name="VoiceInterviewAgent", role="Adaptive Conversational Voice Interviewer", system_instruction=system_instruction, api_key=api_key)

    def start_interview(self, resume_profile: dict, jd_profile: dict, fit_profile: dict) -> dict:
        """Formulates the opening interview turn based on candidate bio and challenge areas."""
        cand_name = resume_profile.get("candidate_name", "Candidate")
        role_title = jd_profile.get("role_title", "Target Role")
        challenges = resume_profile.get("challenge_areas", [])
        top_challenge = "methodological depth"
        if challenges:
            first_c = challenges[0]
            if isinstance(first_c, dict):
                top_challenge = first_c.get("area") or first_c.get("challenge") or str(first_c)
            elif isinstance(first_c, str):
                top_challenge = first_c.strip() or "methodological depth"

        prompt = f"""
Candidate: {cand_name}
Target Role: {role_title}
Key Scrutiny Area: {top_challenge}

Generate an authentic, welcoming yet probing opening interview question.
Ask the candidate to introduce their background, highlight their core capability for {role_title},
and specifically address their experience with {top_challenge}.

Return strict JSON:
{{
  "turn_number": 1,
  "interviewer_question": "Welcoming greeting and initial scenario question...",
  "target_dimension": "Core Background & Strategic Fit",
  "expected_elements": ["STAR context", "Specific project metric", "Clear role alignment"]
}}
"""
        try:
            return self.run_json(prompt)
        except Exception:
            return {
                "turn_number": 1,
                "interviewer_question": f"Welcome {cand_name}. To begin our assessment for the {role_title} position, could you walk me through your academic and project background, and explain how your specific hands-on experiences prepare you to handle real-world operational challenges?",
                "target_dimension": "Core Background & Strategic Fit",
                "expected_elements": ["STAR context", "Specific project metric", "Clear role alignment"]
            }

    def process_turn(self, conversation_history: list, candidate_answer: str, resume_profile: dict, jd_profile: dict, duration_seconds: float = 45.0) -> dict:
        """
        Evaluates a candidate's verbal response and generates an adaptive follow-up question.
        Includes Google Local NLP speech analytics (fillers, WPM, STAR compliance).
        """
        cand_name = resume_profile.get("candidate_name", "Candidate")
        role_title = jd_profile.get("role_title", "Target Role")
        
        # 1. Execute Speech & Communication Analytics
        comm_audit = SpeechAnalyticsEngine.analyze_verbal_response(candidate_answer, duration_seconds=duration_seconds)

        # 2. Evaluate Domain Substantive Depth via LLM
        prompt = f"""
Candidate: {cand_name}
Target Role: {role_title}
Recent Dialogue History:
{json.dumps(conversation_history[-3:], indent=2)}

Candidate Verbal Response:
"{candidate_answer}"

Speech & Delivery Metrics:
- Delivery Score: {comm_audit.get("composite_delivery_score", 0)}/100 ({comm_audit.get("executive_presence_level", "Developing")})
- Pacing: {comm_audit.get("cadence_analysis", {}).get("wpm", 0)} WPM ({comm_audit.get("cadence_analysis", {}).get("pacing_category", "Optimal")})
- Fillers / Disfluencies: {comm_audit.get("filler_analysis", {}).get("total_fillers", 0)} fillers, {comm_audit.get("filler_analysis", {}).get("stutter_count", 0)} stutters
- STAR Chronological Flow: {comm_audit.get("star_compliance", {}).get("chronological_flow", True)}
- Active Voice: {comm_audit.get("syntactic_style", {}).get("voice_verdict", "Balanced")}
- Domain Terminology: {comm_audit.get("domain_fluency", {}).get("terms_found", [])}

Evaluate the candidate's answer for:
1. Substantive domain correctness and depth.
2. Concrete evidence and metrics provided (vs generic assertions).
3. Verbal delivery, active voice, and executive presence based on the speech metrics above.
4. Generate a direct, sharp follow-up probing question that digs into any unquantified claim or trade-off in their answer.
5. If this is turn 4 or later, you may conclude the interview.

Return strict JSON:
{{
  "turn_evaluation": {{
    "substantive_rating": "Strong" | "Moderate" | "Weak",
    "strengths_observed": "What candidate answered well...",
    "gaps_or_vulnerabilities": "Where candidate was vague or missed nuance...",
    "coaching_tip": "Specific tactical improvement tip..."
  }},
  "is_concluded": false,
  "next_question": "Sharp follow-up probing question...",
  "target_dimension": "Technical Depth / Trade-Off Analysis"
}}
"""
        try:
            res = self.run_json(prompt)
            res["communication_audit"] = comm_audit
            return res
        except Exception:
            # Deterministic presentation fallback
            return {
                "turn_evaluation": {
                    "substantive_rating": "Moderate" if len(candidate_answer) > 80 else "Weak",
                    "strengths_observed": "Addressed the broad scenario and maintained conversational tone.",
                    "gaps_or_vulnerabilities": "Could provide more specific quantitative metrics and concrete trade-off rationale.",
                    "coaching_tip": "Structure your answer using the STAR method: explicitly state the Task, your individual Action, and the measurable Result."
                },
                "is_concluded": len(conversation_history) >= 4,
                "next_question": f"That provides helpful context. Let's dig deeper: when you executed that solution, what was the primary architectural or operational trade-off you had to make, and what metrics did you use to validate success?",
                "target_dimension": "Trade-off & Impact Quantification",
                "communication_audit": comm_audit
            }
