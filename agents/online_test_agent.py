import json
import random
from agents.base_agent import BaseAgent

class OnlineTestAgent(BaseAgent):
    def __init__(self, api_key: str = None):
        system_instruction = (
            "You are a psychometrician and senior technical assessment authority. "
            "Your role is to design advanced, scenario-based online multiple choice examinations "
            "that rigorously test real-world problem-solving, algorithmic thinking, and domain decision-making. "
            "Never generate trivial recall questions; every question must feature realistic scenarios, "
            "plausible distractors reflecting common professional misconceptions, and detailed explanatory rationales. "
            "Output strictly valid JSON."
        )
        super().__init__(name="OnlineTestAgent", role="Advanced Technical Examination Administrator", system_instruction=system_instruction, api_key=api_key)

    def generate_test(self, jd_profile: dict, resume_profile: dict, fit_profile: dict, topic_checklist: list, num_questions: int = 30) -> dict:
        """
        Generates a 30+ question advanced multiple choice test customized to the JD and domain,
        strictly aligned with the JD topic checklist weighting.
        """
        jd_profile = jd_profile or {}
        if isinstance(jd_profile, str):
            role_title = jd_profile
        else:
            role_title = jd_profile.get("role_title", "Target Role")

        resume_profile = resume_profile or {}
        fit_profile = fit_profile or {}
        topic_checklist = topic_checklist or []
        num_questions = max(30, num_questions)

        prompt = f'''
Generate a challenging, 30-question advanced multiple choice assessment for the role: "{role_title}".

TOPIC CHECKLIST TO COVER:
{json.dumps(topic_checklist, indent=2)}

JD CONTEXT:
{json.dumps(jd_profile, indent=2)}

CANDIDATE FIT PROFILE:
{json.dumps(fit_profile, indent=2)}

SPECIFICATIONS:
1. Generate EXACTLY {num_questions} multiple-choice questions (IDs 1 to {num_questions}).
2. Difficulty: ADVANCED / SENIOR-READY. Each question must present a concrete situational dilemma, architecture trade-off, calculation, code/query interpretation, or risk decision.
3. Every question MUST be tagged with a specific topic from the TOPIC CHECKLIST (`topic`).
4. Distribute questions across the checklist topics, weighting heavily toward topics classified as "Gap" and "Claimed", while ensuring "Untested" topics are also tested.
5. Provide 4 distinct options: "A", "B", "C", "D".
6. Distractors must be plausible, reflecting real-world engineering or financial mistakes.
7. Include the unambiguous `correct_option` ("A", "B", "C", or "D") and a comprehensive `explanation` (why the correct option is right and why the distractors fail).

Return strict JSON:
{{
  "test_metadata": {{
    "title": "{role_title} Advanced Technical Assessment",
    "total_questions": {num_questions},
    "time_limit_minutes": 45,
    "pass_threshold_percentage": 70.0
  }},
  "questions": [
    {{
      "question_id": 1,
      "topic": "Exact topic from checklist",
      "difficulty": "Advanced",
      "question": "Scenario or technical dilemma...",
      "question_text": "Scenario or technical dilemma...",
      "options": {{
        "A": "Plausible solution or distractor...",
        "B": "Plausible solution or distractor...",
        "C": "Plausible solution or distractor...",
        "D": "Plausible solution or distractor..."
      }},
      "correct_option": "A",
      "explanation": "Detailed engineering or domain rationale..."
    }}
  ]
}}
'''
        try:
            test_json = self.run_json(prompt)
            # Ensure integrity
            qs = test_json.get("questions", [])
            if len(qs) < 30:
                raise ValueError(f"Model generated only {len(qs)} questions; requires at least 30.")
            
            # Normalize and guarantee all required fields across every question
            for idx, q in enumerate(qs):
                q_str = (
                    q.get("question_text") or 
                    q.get("question") or 
                    q.get("prompt") or 
                    q.get("scenario") or 
                    q.get("text") or 
                    ""
                ).strip()
                if not q_str:
                    q_topic_name = q.get("topic") or q.get("topic_name") or "Core Technical Capability"
                    q_str = f"Evaluate the strategic dilemma and operational trade-offs concerning {q_topic_name} under real-world constraints."
                
                q["question_text"] = q_str
                q["question"] = q_str
                
                if "question_id" not in q:
                    q["question_id"] = idx + 1
                if "question_number" not in q:
                    q["question_number"] = idx + 1
                
                # Normalize options dictionary
                opts = q.get("options", {})
                if isinstance(opts, list):
                    opt_dict = {}
                    for o_idx, o_val in enumerate(opts[:4]):
                        opt_dict[chr(65 + o_idx)] = str(o_val)
                    q["options"] = opt_dict
                elif isinstance(opts, dict):
                    for k in ["A", "B", "C", "D"]:
                        if k not in opts:
                            opts[k] = f"Strategic alternative {k}"
                    q["options"] = opts
                else:
                    q["options"] = {
                        "A": "Recommended best-practice approach",
                        "B": "Alternative with operational trade-offs",
                        "C": "Sub-optimal implementation with latency",
                        "D": "Infeasible theoretical solution"
                    }

            test_json["questions"] = qs
            test_json["total_questions"] = len(qs)
            test_json["time_limit_minutes"] = test_json.get("test_metadata", {}).get("time_limit_minutes", 30)
            test_json["passing_score_percentage"] = test_json.get("test_metadata", {}).get("pass_threshold_percentage", 70.0)
            return test_json
        except Exception as e:
            return self._generate_failsafe_test(topic_checklist, jd_profile, num_questions, str(e))

    def shuffle_test_questions(self, test_data: dict, seed: int = None) -> dict:
        """
        Randomizes question sequence and distractor option keys (A, B, C, D)
        while maintaining 100% correct answer mapping for deterministic auto-scoring.
        """
        if not test_data or "questions" not in test_data:
            return test_data

        rng = random.Random(seed) if seed is not None else random.Random()
        questions = list(test_data["questions"])
        rng.shuffle(questions)

        shuffled_questions = []
        for idx, q in enumerate(questions):
            q_copy = dict(q)
            q_copy["original_id"] = q_copy.get("question_id", idx + 1)
            q_copy["question_id"] = idx + 1
            q_copy["question_number"] = idx + 1

            opts = q_copy.get("options", {})
            if isinstance(opts, dict) and len(opts) == 4:
                correct_letter = q_copy.get("correct_option", "A")
                correct_text = str(opts.get(correct_letter, "")).strip()

                opt_items = list(opts.values())
                rng.shuffle(opt_items)

                letters = ["A", "B", "C", "D"]
                new_opts = {}
                new_correct = "A"
                for l_idx, letter in enumerate(letters):
                    val = str(opt_items[l_idx]).strip()
                    new_opts[letter] = val
                    if val == correct_text:
                        new_correct = letter

                q_copy["options"] = new_opts
                q_copy["correct_option"] = new_correct

            shuffled_questions.append(q_copy)

        test_data["questions"] = shuffled_questions
        return test_data

    def score_test(self, test_data: dict, candidate_answers: dict) -> dict:
        """
        Auto-scores the online test immediately upon submission.
        Produces overall score, percentage, itemized question review with explanations,
        and an analytical topic-wise performance breakdown.
        """
        questions = test_data.get("questions", [])
        total_questions = len(questions)
        correct_count = 0
        review_items = []
        topic_stats = {}

        for q in questions:
            raw_id = q.get("question_id")
            q_id = str(raw_id)
            topic = q.get("topic", "General Technical")
            correct_opt = str(q.get("correct_option", "A")).strip().upper()

            user_opt = candidate_answers.get(raw_id)
            if user_opt is None:
                user_opt = candidate_answers.get(q_id)
            if user_opt is None and q_id.isdigit():
                user_opt = candidate_answers.get(int(q_id))
            if user_opt is None:
                user_opt = ""
            user_opt = str(user_opt).strip().upper()

            is_correct = (user_opt == correct_opt)
            if is_correct:
                correct_count += 1

            if topic not in topic_stats:
                topic_stats[topic] = {"total": 0, "correct": 0}
            topic_stats[topic]["total"] += 1
            if is_correct:
                topic_stats[topic]["correct"] += 1

            review_items.append({
                "question_id": q.get("question_id"),
                "question_number": q.get("question_number", len(review_items) + 1),
                "topic": topic,
                "question": q.get("question_text") or q.get("question", ""),
                "question_text": q.get("question_text") or q.get("question", ""),
                "options": q.get("options", {}),
                "selected_option": user_opt if user_opt else "Unanswered",
                "candidate_answer": user_opt if user_opt else "Unanswered",
                "correct_option": correct_opt,
                "is_correct": is_correct,
                "explanation": q.get("explanation", "Review the core domain principles for this concept.")
            })

        percentage = round((correct_count / max(total_questions, 1)) * 100, 1)

        topic_breakdown = []
        topic_accuracy = {}
        weak_topics = []
        for topic, stats in topic_stats.items():
            tot = stats["total"]
            corr = stats["correct"]
            acc = round((corr / max(tot, 1)) * 100, 1)
            is_weak = acc < 70.0
            if is_weak:
                weak_topics.append(topic)
            topic_stats[topic]["percentage"] = acc
            topic_accuracy[topic] = {"correct": corr, "total": tot, "percentage": acc}
            topic_breakdown.append({
                "topic": topic,
                "total_questions": tot,
                "correct_answers": corr,
                "accuracy_percentage": acc,
                "status": "Needs Improvement" if is_weak else ("Mastered" if acc >= 85 else "Competent"),
                "is_weak": is_weak
            })

        # Sort breakdown by accuracy ascending so weakest topics appear first
        topic_breakdown.sort(key=lambda x: x["accuracy_percentage"])

        if percentage >= 80.0:
            verdict = "Placement Ready (Distinction Benchmark)"
        elif percentage >= 65.0:
            verdict = "Competitive Baseline (Targeted Polish Needed)"
        else:
            verdict = "Remediation Required (Critical Knowledge Gaps)"

        return {
            "score": correct_count,
            "total_questions": total_questions,
            "percentage": percentage,
            "verdict": verdict,
            "passed": percentage >= test_data.get("test_metadata", {}).get("pass_threshold_percentage", 70.0),
            "topic_breakdown": topic_breakdown,
            "topic_accuracy": topic_accuracy,
            "weak_topics": weak_topics,
            "review_items": review_items,
            "detailed_results": review_items
        }

    def _generate_failsafe_test(self, topic_checklist: list, jd_profile: dict = None, num_questions: int = 30, error_reason: str = "") -> dict:
        """
        Failsafe generator creating 30 advanced, realistic multiple-choice questions
        distributed across the JD topic checklist.
        """
        if isinstance(jd_profile, str):
            role_title = jd_profile
        elif isinstance(jd_profile, dict):
            role_title = jd_profile.get("role_title", "Senior Business / Technical Analyst")
        else:
            role_title = "Senior Business / Technical Analyst"

        questions = []
        weighted_topics = []
        if topic_checklist:
            for t in topic_checklist:
                t_name = t.get("topic") or t.get("topic_name") or "Domain"
                w = float(t.get("weight", 1.0))
                # Repeat by weight so weak / gap topics (weight 2.0 - 2.5) are sampled much more
                reps = max(1, int(round(w * 2)))
                weighted_topics.extend([t_name] * reps)
        if not weighted_topics:
            weighted_topics = [
                "Financial Statement Analysis", "Risk Assessment & Mitigation",
                "Advanced Excel & Data Modeling", "SQL & Relational Analytics",
                "Valuation & Forecasting", "Product Lifecycle Management"
            ]

        templates = [
            (
                "When evaluating {topic} under sudden market liquidity contraction, which of the following actions maintains operational continuity with minimal solvency drag?",
                "Prioritizing cash preservation via dynamic working capital sweeps and extending non-essential payables within covenant boundaries.",
                "Immediately drawing down 100% of revolving credit lines regardless of undrawn commitment fees.",
                "Liquidating core capital equipment at auction to recognize instantaneous non-operating revenue.",
                "Freezing customer invoicing to prevent bad-debt write-offs on current period balance sheet.",
                "A",
                "Working capital optimization and dynamic cash sweeps protect liquidity without triggering covenant violations or penal interest."
            ),
            (
                "In an enterprise implementation involving {topic}, a data discrepancy of 4.8% is detected between the core operational pipeline and reporting views. What is the most rigorous first step?",
                "Execute reconciliation at the transactional ledger grain to isolate pipeline ingestion drops versus downstream transformations.",
                "Apply an arbitrary 4.8% adjustment coefficient across summary reports to reconcile totals.",
                "Drop the delta records to ensure statistical distributions match historical norms.",
                "Assume the variance is attributable to round-off error and proceed without audit tracing.",
                "A",
                "Audit trail integrity mandates reconciling at the source transaction grain rather than masking variances downstream."
            ),
            (
                "Which architectural or methodological approach to {topic} best balances real-time decision throughput with governance constraints?",
                "Modular service decoupling paired with asynchronous event queues and strict schema validation.",
                "Monolithic synchronous execution with direct unindexed queries to the primary transactional store.",
                "Client-side caching with zero server-side state synchronization or access control.",
                "Batch processing executed exclusively once weekly during non-business hours.",
                "A",
                "Event-driven asynchronous decoupling provides horizontal elasticity while preserving strict schema integrity."
            ),
            (
                "Suppose a stakeholder challenges your analytical model on {topic}, asserting that the sensitivity parameters understate downside risk. How do you defend or adjust the framework?",
                "Run a Monte Carlo simulation isolating tail-risk probabilities (VaR 99%) and document the parameter sensitivity elasticities.",
                "Concede immediately and double all risk parameters without empirical backtesting.",
                "Dismiss the critique on the grounds that baseline scenario averages already reflect normal distributions.",
                "Remove sensitive variables from the presentation slides to avoid contentious discussions.",
                "A",
                "Robust analytical defense requires parametric stress-testing and empirical tail-risk distribution modeling (Monte Carlo)."
            )
        ]

        for i in range(1, num_questions + 1):
            topic = weighted_topics[(i - 1) % len(weighted_topics)]
            q_tmpl, opt_a, opt_b, opt_c, opt_d, correct_opt, expl = templates[(i - 1) % len(templates)]
            
            # Shuffle options slightly across questions for variety
            opts = {"A": opt_a, "B": opt_b, "C": opt_c, "D": opt_d}
            if i % 3 == 1:
                opts = {"A": opt_b, "B": opt_a, "C": opt_c, "D": opt_d}
                correct_opt = "B"
            elif i % 3 == 2:
                opts = {"A": opt_c, "B": opt_d, "C": opt_a, "D": opt_b}
                correct_opt = "C"

            questions.append({
                "question_id": i,
                "topic": topic,
                "difficulty": "Advanced",
                "question": q_tmpl.format(topic=topic),
                "question_text": q_tmpl.format(topic=topic),
                "options": opts,
                "correct_option": correct_opt,
                "explanation": expl
            })

        return {
            "title": f"{role_title} Advanced Technical Assessment",
            "total_questions": num_questions,
            "time_limit_minutes": 45,
            "passing_score_percentage": 70.0,
            "test_metadata": {
                "title": f"{role_title} Advanced Technical Assessment",
                "total_questions": num_questions,
                "time_limit_minutes": 45,
                "pass_threshold_percentage": 70.0
            },
            "questions": questions,
            "is_failsafe": True,
            "failsafe_reason": error_reason
        }
