import json
import re
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent

class CompanyIntelAgent(BaseAgent):
    """
    Agentic Corporate Culture Principles & Company Intelligence RAG Engine.
    Grounds candidate evaluation and behavioral interview questions in the specific
    leadership principles, cultural values, and interview rubrics of hiring companies.
    """

    CURATED_PROFILES: Dict[str, Dict[str, Any]] = {
        "amazon": {
            "canonical_name": "Amazon",
            "tier": "Tier 1 Big Tech / Cloud & E-Commerce",
            "culture_motto": "Work Hard. Have Fun. Make History.",
            "evaluation_framework": "16 Amazon Leadership Principles (LP) & Bar Raiser Standard",
            "core_principles": [
                {
                    "name": "Customer Obsession",
                    "description": "Leaders start with the customer and work backwards. They work vigorously to earn and keep customer trust.",
                    "interview_implication": "Every answer must demonstrate how the candidate prioritized long-term customer value over short-term internal metrics."
                },
                {
                    "name": "Ownership",
                    "description": "Leaders are owners. They think long term and don't sacrifice long-term value for short-term results. They never say 'that's not my job'.",
                    "interview_implication": "Probe for proactive initiatives where the candidate solved cross-functional problems outside their explicit domain."
                },
                {
                    "name": "Bias for Action",
                    "description": "Speed matters in business. Many decisions and actions are reversible and do not need extensive study. We value calculated risk taking.",
                    "interview_implication": "Candidate should demonstrate rapid decision-making under incomplete information with two-way door decision frameworks."
                },
                {
                    "name": "Dive Deep",
                    "description": "Leaders operate at all levels, stay connected to the details, audit frequently, and are skeptical when metrics and anecdote differ.",
                    "interview_implication": "Interviewers will probe 3-5 layers deep into candidate project metrics, root causes, and SQL/data architectures."
                },
                {
                    "name": "Deliver Results",
                    "description": "Leaders focus on the key inputs for their business and deliver them with the right quality and in a timely fashion.",
                    "interview_implication": "Expect strict scrutiny of quantified outcomes, revenue lift, latency reduction, or efficiency gains."
                },
                {
                    "name": "Invent and Simplify",
                    "description": "Leaders expect and require innovation and invention from their teams and always find ways to simplify.",
                    "interview_implication": "Candidate must illustrate turning convoluted legacy workflows into elegant, automated architectures."
                }
            ],
            "authentic_behavioral_probes": [
                {
                    "principle": "Customer Obsession",
                    "question": "Tell me about a time when you had to advocate for a customer requirement that conflicted with internal engineering deadlines or executive goals.",
                    "evaluation_rubric": "Did the candidate use data to demonstrate customer pain? Did they refuse to ship a degraded experience?"
                },
                {
                    "principle": "Ownership",
                    "question": "Describe a significant project failure or missed milestone. What was your personal responsibility, and how did you prevent systemic recurrence?",
                    "evaluation_rubric": "Does the candidate own the fault without deflecting to teammates, management, or vendors?"
                },
                {
                    "principle": "Bias for Action",
                    "question": "Give an example of a high-impact decision you made with less than 70% of the data you wanted. What was the calculated downside?",
                    "evaluation_rubric": "Assesses comfort with ambiguity and velocity of calculated experimentation."
                },
                {
                    "principle": "Dive Deep",
                    "question": "Walk me through the most complex technical or business problem you debugged. What metrics did you personally inspect at the granular level?",
                    "evaluation_rubric": "Tests hands-on mastery vs. delegating/hand-waving high-level executive speak."
                }
            ],
            "cultural_radar_weights": {
                "Customer Centricity": 95,
                "Ownership & Accountability": 95,
                "Analytical Rigor (Dive Deep)": 90,
                "Speed & Ambiguity (Bias for Action)": 90,
                "Simplification & Innovation": 85
            }
        },
        "google": {
            "canonical_name": "Google",
            "tier": "Tier 1 Big Tech / AI & Enterprise Systems",
            "culture_motto": "Organize the world's information and make it universally accessible and useful.",
            "evaluation_framework": "Googleyness & General Cognitive Ability (GCA) Rubric",
            "core_principles": [
                {
                    "name": "Googleyness",
                    "description": "Intellectual humility, doing the right thing, thriving in ambiguity, and collaborative team orientation.",
                    "interview_implication": "Candidates must show open-mindedness to dissenting data, admitting mistakes, and putting team cohesion above ego."
                },
                {
                    "name": "General Cognitive Ability (GCA)",
                    "description": "Capacity to learn, adapt, synthesize disparate information, and solve problems with structured first-principles thinking.",
                    "interview_implication": "Probing through hypothetical, open-ended business scenarios with unknown variables."
                },
                {
                    "name": "Role-Related Knowledge (RRK)",
                    "description": "Deep domain understanding and technical expertise applied to scalable systems.",
                    "interview_implication": "Evaluation of whether candidate understands enterprise scale, distributed architectures, and product telemetry."
                },
                {
                    "name": "Emergent Leadership",
                    "description": "Stepping up to lead when required, and seamlessly stepping back to follow when another team member is better equipped.",
                    "interview_implication": "Evidence of consensus-building without relying on positional authority or formal hierarchy."
                }
            ],
            "authentic_behavioral_probes": [
                {
                    "principle": "Googleyness & Intellectual Humility",
                    "question": "Tell me about a situation where you had a strong technical conviction that was proven completely wrong by data or a junior colleague.",
                    "evaluation_rubric": "Did the candidate pivot gracefully, embrace the new truth, and celebrate the collaborator?"
                },
                {
                    "principle": "General Cognitive Ability (GCA)",
                    "question": "If you were tasked with launching Google Workspace for a developing nation's entire public school system with intermittent connectivity, how would you architect the phased rollout?",
                    "evaluation_rubric": "Tests structured MECE scoping, edge-case identification, and empathetic user constraint modeling."
                },
                {
                    "principle": "Emergent Leadership",
                    "question": "Describe a project where cross-functional stakeholders had conflicting incentives and zero formal reporting lines to you. How did you build consensus?",
                    "evaluation_rubric": "Assesses influence without authority, active listening, and common ground discovery."
                }
            ],
            "cultural_radar_weights": {
                "Googleyness & Humility": 95,
                "Structured Problem Solving (GCA)": 95,
                "Scale & System Architecture": 90,
                "Influence Without Authority": 90,
                "Innovation & 10x Thinking": 85
            }
        },
        "mckinsey": {
            "canonical_name": "McKinsey & Company",
            "tier": "Tier 1 Strategy Consulting / MBB",
            "culture_motto": "Help clients make distinctive, lasting, and substantial improvements in their performance.",
            "evaluation_framework": "Personal Experience Interview (PEI) & MECE Hypothesis-Driven Rigor",
            "core_principles": [
                {
                    "name": "Personal Impact",
                    "description": "Ability to persuade, influence senior executives, and shape outcomes in high-stakes environments.",
                    "interview_implication": "Candidate must articulate exact words, psychological levers, and communication strategy used to win over stubborn stakeholders."
                },
                {
                    "name": "Inclusive Leadership",
                    "description": "Guiding teams through adversity, fostering psychological safety, and developing junior talent.",
                    "interview_implication": "Focus on coaching, mentoring, and navigating team crises under intense deadline pressure."
                },
                {
                    "name": "Entrepreneurial Drive",
                    "description": "Relentless tenacity to overcome systemic obstacles, pioneer new initiatives, and deliver against impossible odds.",
                    "interview_implication": "Stories must show overcoming repeated roadblocks without giving up."
                },
                {
                    "name": "Hypothesis-Driven Problem Solving",
                    "description": "Structuring complex, messy corporate problems into Mutually Exclusive, Collectively Exhaustive (MECE) issue trees.",
                    "interview_implication": "Zero tolerance for unstructured brainstorming; every recommendation must be rooted in an 80/20 hypothesis."
                }
            ],
            "authentic_behavioral_probes": [
                {
                    "principle": "Personal Impact (PEI)",
                    "question": "Take me back to a pivotal conversation where an executive client strongly rejected your strategic proposal. How did you change their mind?",
                    "evaluation_rubric": "Interviewer will spend 15 minutes probing sentence by sentence: What did you say? What was their body language? What compromise was reached?"
                },
                {
                    "principle": "Entrepreneurial Drive",
                    "question": "Describe a situation where a critical external resource or funding was revoked midway through a project. How did you pivot to deliver anyway?",
                    "evaluation_rubric": "Tests resilience, resourcefulness, and unwillingness to accept bureaucratic dead-ends."
                },
                {
                    "principle": "Inclusive Leadership",
                    "question": "Tell me about a time when a team member was struggling or underperforming on a high-visibility deliverable. How did you handle it?",
                    "evaluation_rubric": "Assesses empathetic diagnostics vs. punitive escalation."
                }
            ],
            "cultural_radar_weights": {
                "Executive Presence & Personal Impact": 95,
                "Hypothesis-Driven MECE Rigor": 95,
                "Entrepreneurial Drive & Tenacity": 90,
                "Inclusive Team Leadership": 85,
                "Synthesized Communication (Top-Down)": 90
            }
        },
        "goldmansachs": {
            "canonical_name": "Goldman Sachs",
            "tier": "Bulge Bracket Investment Banking & Global Markets",
            "culture_motto": "Our clients' interests always come first.",
            "evaluation_framework": "14 Goldman Sachs Business Principles & Fiduciary Risk Protocol",
            "core_principles": [
                {
                    "name": "Client Interests First",
                    "description": "Our experience shows that if we serve our clients well, our own success will follow.",
                    "interview_implication": "Must demonstrate uncompromising ethics and placing client fiduciary integrity above short-term trading margins."
                },
                {
                    "name": "Excellence & Precision",
                    "description": "Zero tolerance for quantitative inaccuracy, faulty formulas, or sloppy modeling.",
                    "interview_implication": "Every financial metric, DCF assumption, and debt covenant must be defended with rigorous rationale."
                },
                {
                    "name": "Integrity & Compliance",
                    "description": "Dedication to complying fully with the letter and spirit of laws, rules, and ethical principles.",
                    "interview_implication": "Probes on ethical dilemmas and confidentiality protocols."
                },
                {
                    "name": "Downside Risk Consciousness",
                    "description": "Anticipating tail risks, liquidity stress, and macro volatility in every deal.",
                    "interview_implication": "Candidate should always evaluate sensitivity tables, stress testing, and downside protection."
                }
            ],
            "authentic_behavioral_probes": [
                {
                    "principle": "Integrity & Fiduciary Responsibility",
                    "question": "Have you ever identified a flaw in a model or pitch deck that, if corrected, would make the opportunity look less attractive to an investor? What did you do?",
                    "evaluation_rubric": "Does the candidate immediately correct the error transparently, upholding reputational integrity?"
                },
                {
                    "principle": "Excellence Under Extreme Pressure",
                    "question": "Describe a live transaction or audit where you had to reconcile massive contradictory financial data under overnight deal deadlines.",
                    "evaluation_rubric": "Assesses stamina, verification checklists, and mental composure under high stakes."
                }
            ],
            "cultural_radar_weights": {
                "Fiduciary Ethics & Integrity": 95,
                "Quantitative Precision": 95,
                "Downside Risk Modeling": 90,
                "Client Stewardship": 90,
                "Execution Stamina": 85
            }
        },
        "microsoft": {
            "canonical_name": "Microsoft",
            "tier": "Tier 1 Enterprise Tech & Cloud (Azure / Copilot)",
            "culture_motto": "Empower every person and every organization on the planet to achieve more.",
            "evaluation_framework": "Growth Mindset & Customer Empathy Competency Matrix",
            "core_principles": [
                {
                    "name": "Growth Mindset",
                    "description": "Learn-it-alls outperform know-it-alls. Embracing curiosity, learning from failure, and continuous self-reinvention.",
                    "interview_implication": "Candidate should highlight how they learned new technologies or adapted when legacy approaches failed."
                },
                {
                    "name": "Customer Empathy",
                    "description": "Deeply understanding diverse enterprise client needs and constraints.",
                    "interview_implication": "Probing on accessibility, security compliance, and user workflows."
                },
                {
                    "name": "One Microsoft Collaboration",
                    "description": "Breaking down organizational silos to deliver cohesive solutions across products.",
                    "interview_implication": "Evidence of working across organizational boundaries to ship joint capabilities."
                }
            ],
            "authentic_behavioral_probes": [
                {
                    "principle": "Growth Mindset",
                    "question": "Tell me about a time when you ventured outside your expertise to master a completely unfamiliar technology or business domain under tight timelines.",
                    "evaluation_rubric": "Assesses intellectual curiosity and velocity of self-directed upskilling."
                },
                {
                    "principle": "One Microsoft Collaboration",
                    "question": "Describe a project where multiple departments had isolated tools and conflicting priorities. How did you synthesize a unified strategy?",
                    "evaluation_rubric": "Assesses cross-boundary orchestration and enterprise empathy."
                }
            ],
            "cultural_radar_weights": {
                "Growth Mindset (Curiosity)": 95,
                "Customer Empathy": 90,
                "Cross-Boundary Collaboration": 90,
                "Enterprise Scalability": 85,
                "Inclusion & Diversity": 85
            }
        }
    }

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="CompanyIntelAgent",
            role="Corporate Culture Intelligence & Leadership Principles Specialist",
            system_instruction=(
                "You are an executive corporate intelligence director. You identify hiring company leadership "
                "principles, cultural DNA, evaluation rubrics, and authentic behavioral interview patterns. "
                "Output strictly valid JSON."
            ),
            api_key=api_key
        )

    def get_company_intelligence(self, company_name: str, domain_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves company intelligence from curated corporate profiles or dynamically synthesizes
        corporate cultural DNA via LLM grounding for arbitrary hiring firms.
        """
        if not company_name:
            company_name = "Global Enterprise"

        cleaned_key = re.sub(r'[^a-zA-Z0-9]', '', company_name.lower())

        # Check curated profiles
        for key, profile in self.CURATED_PROFILES.items():
            if key in cleaned_key or (len(cleaned_key) >= 4 and cleaned_key in key):
                return profile

        # Check known aliases
        if any(w in cleaned_key for w in ["aws", "amzn"]):
            return self.CURATED_PROFILES["amazon"]
        if any(w in cleaned_key for w in ["alphabet", "goog"]):
            return self.CURATED_PROFILES["google"]
        if any(w in cleaned_key for w in ["bain", "bcg", "kearney", "oliverwyman", "consulting"]):
            return self.CURATED_PROFILES["mckinsey"]
        if any(w in cleaned_key for w in ["jpmorgan", "morganstanley", "barclays", "citi", "bank"]):
            return self.CURATED_PROFILES["goldmansachs"]
        if any(w in cleaned_key for w in ["msft", "azure"]):
            return self.CURATED_PROFILES["microsoft"]

        # If not found in curated dictionary, generate grounded company intelligence
        return self._synthesize_dynamic_company_intel(company_name, domain_context)

    def _synthesize_dynamic_company_intel(self, company_name: str, domain_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates grounded corporate principles for an unindexed firm using LLM,
        with a robust deterministic failsafe for offline/quota scenarios.
        """
        domain = domain_context or "Digital Transformation & Technology"
        prompt = f"""
Analyze the corporate culture, leadership principles, and authentic interview standards for:
COMPANY: {company_name}
INDUSTRY / DOMAIN: {domain}

Return a valid JSON object with:
{{
  "canonical_name": "{company_name}",
  "tier": "Corporate Sector Tier (e.g. Enterprise Technology | Global Financial Services | Strategy Consulting)",
  "culture_motto": "Representative corporate motto or cultural philosophy",
  "evaluation_framework": "Core Interview Evaluation Standard (e.g. Behavioral Competency & Technical Rigor)",
  "core_principles": [
    {{
      "name": "Principle Name",
      "description": "Detailed explanation of this core corporate value",
      "interview_implication": "How interviewers test this specific principle"
    }}
  ],
  "authentic_behavioral_probes": [
    {{
      "principle": "Principle Name",
      "question": "Authentic behavioral STAR interview question testing this principle",
      "evaluation_rubric": "Evaluation standard candidate must satisfy"
    }}
  ],
  "cultural_radar_weights": {{
    "Dimension 1": 90,
    "Dimension 2": 85,
    "Dimension 3": 85,
    "Dimension 4": 80,
    "Dimension 5": 75
  }}
}}
"""
        try:
            res = self.run_json(prompt)
            if res and isinstance(res, dict) and "core_principles" in res:
                return res
        except Exception:
            pass

        # Robust Failsafe
        return {
            "canonical_name": company_name,
            "tier": "Enterprise Digital Transformation Leader",
            "culture_motto": f"Driving Excellence and Innovation at {company_name}",
            "evaluation_framework": f"{company_name} Core Competency & Behavioral Alignment Model",
            "core_principles": [
                {
                    "name": "Strategic Innovation",
                    "description": f"Pioneering pragmatic solutions that modernise business capabilities at {company_name}.",
                    "interview_implication": "Probes candidate ability to transform traditional operations through digital leverage."
                },
                {
                    "name": "Accountability & Execution",
                    "description": "Taking end-to-end ownership of project delivery, timeline governance, and KPI realization.",
                    "interview_implication": "Evaluates candidate resilience and proactive problem-solving when milestones are at risk."
                },
                {
                    "name": "Data-Driven Decision Making",
                    "description": "Grounding strategic recommendations and prioritization in empirical metrics and financial validation.",
                    "interview_implication": "Tests candidate fluency with data models, business cases, and quantitative ROI."
                },
                {
                    "name": "Collaborative Stakeholder Stewardship",
                    "description": "Aligning cross-functional engineering, business, and executive partners toward unified goals.",
                    "interview_implication": "Assesses communication clarity, executive brevity, and conflict negotiation."
                }
            ],
            "authentic_behavioral_probes": [
                {
                    "principle": "Strategic Innovation",
                    "question": f"Describe a project where you identified an inefficient legacy workflow and architected an innovative digital solution. What was the tangible impact?",
                    "evaluation_rubric": "Candidate must quantify efficiency improvement and detail stakeholder adoption strategy."
                },
                {
                    "principle": "Accountability & Execution",
                    "question": f"Tell me about a time when an unforeseen technical bottleneck threatened an enterprise launch date. How did you triage and deliver?",
                    "evaluation_rubric": "Assesses risk mitigation, root-cause diagnostics, and transparent stakeholder communication."
                },
                {
                    "principle": "Collaborative Stakeholder Stewardship",
                    "question": f"Give an example of a situation where you had to convince skeptical business leaders to adopt a major process or technology transformation at {company_name}.",
                    "evaluation_rubric": "Tests empathetic listening, business case persuasion, and consensus building."
                }
            ],
            "cultural_radar_weights": {
                "Strategic Innovation": 90,
                "Execution Accountability": 90,
                "Data-Driven Decisiveness": 85,
                "Cross-Functional Alignment": 85,
                "Customer Stewardship": 80
            }
        }

    def enrich_question_bank(self, question_bank: Dict[str, Any], company_intel: Dict[str, Any]) -> Dict[str, Any]:
        """
        Injects company-specific behavioral probes and leadership principles into the
        Question Bank's behavioral section, elevating role realism.
        """
        if not question_bank or not isinstance(question_bank, dict):
            return question_bank

        intel_probes = company_intel.get("authentic_behavioral_probes", [])
        company_name = company_intel.get("canonical_name", "Target Company")
        
        behavioral_list = question_bank.setdefault("behavioral_questions", [])
        
        # Prepend authentic company probes
        formatted_probes = []
        for probe in intel_probes:
            formatted_probes.append({
                "question": f"[{company_name} • {probe.get('principle')}] {probe.get('question')}",
                "topics_covered": [probe.get("principle", "Leadership Alignment")],
                "competency": f"{company_name} Principle: {probe.get('principle')}",
                "priority": "High",
                "evaluation_criteria": probe.get("evaluation_rubric", "Evaluate STAR rigor and cultural alignment.")
            })

        # Place company probes at the front of behavioral questions
        question_bank["behavioral_questions"] = formatted_probes + behavioral_list
        question_bank["company_intelligence"] = {
            "company_name": company_name,
            "evaluation_framework": company_intel.get("evaluation_framework"),
            "core_principles_tested": [p.get("name") for p in company_intel.get("core_principles", [])]
        }
        return question_bank
