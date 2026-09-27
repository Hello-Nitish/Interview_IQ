"""
Speech Analytics Engine for InterviewIQ.
Analyzes verbal interview responses for communication delivery, speech cadence,
filler word frequency, stutter disfluencies, lexical diversity (TTR),
chronological STAR structure, active vs. passive voice, and domain terminology.
"""

import re
from typing import Dict, Any, List, Tuple
from utils.domain_vocabulary import DomainVocabularyCorrector


class SpeechAnalyticsEngine:
    """
    Advanced Verbal Communication Diagnostics & NLP Delivery Audit Engine.
    Evaluates acoustic cadence, disfluency density, structural storytelling,
    syntactic variety, and executive presence.
    """

    NON_LEXICAL_FILLERS = [
        r"\bum\b", r"\buh\b", r"\buhm\b", r"\ber\b", r"\bah\b", r"\bhmm\b"
    ]

    LEXICAL_HESITATIONS = [
        r"\blike\b", r"\byou know\b", r"\bbasically\b", r"\bactually\b",
        r"\bliterally\b", r"\bsort of\b", r"\bkind of\b", r"\bhonestly\b",
        r"\bto be honest\b", r"\bI mean\b", r"\bat the end of the day\b",
        r"\bto be precise\b", r"\bas such\b"
    ]

    # Combined filler patterns for legacy parity
    FILLER_PATTERNS = NON_LEXICAL_FILLERS + LEXICAL_HESITATIONS

    STAR_INDICATORS = {
        "Situation": [
            "when i was", "at my previous", "in my project", "during my internship",
            "the context was", "we were facing", "the challenge occurred", "situation",
            "at the time", "our team was", "the problem was", "initially"
        ],
        "Task": [
            "my responsibility was", "my task was", "i was assigned to", "the goal was",
            "we needed to", "the objective was", "i had to", "responsible for", "the mission was"
        ],
        "Action": [
            "i implemented", "i developed", "i designed", "i analyzed", "i created",
            "i conducted", "i initiated", "i coordinated", "i built", "first, i",
            "then, i", "we deployed", "i used", "i executed", "implemented", "developed",
            "i architected", "i spearheaded", "i negotiated"
        ],
        "Result": [
            "as a result", "the outcome was", "we achieved", "improved by",
            "reduced by", "increased by", "resulting in", "successfully delivered",
            "metrics showed", "the impact was", "consequently", "our roi"
        ]
    }

    # Pre-compiled Regexes for High-Throughput Speech Processing
    _WORD_REGEX = re.compile(r"\b\w+\b")
    _COMPILED_FILLERS = [(p.replace(r"\b", ""), re.compile(p, re.IGNORECASE)) for p in FILLER_PATTERNS]
    _COMPILED_NON_LEXICAL = [(p.replace(r"\b", ""), re.compile(p, re.IGNORECASE)) for p in NON_LEXICAL_FILLERS]
    _COMPILED_LEXICAL = [(p.replace(r"\b", ""), re.compile(p, re.IGNORECASE)) for p in LEXICAL_HESITATIONS]

    # Stutter / Immediate token duplication regex (e.g. "I I", "the the")
    _STUTTER_REGEX = re.compile(r"\b([a-zA-Z]+)\s+\1\b", re.IGNORECASE)

    # Active voice executive action verb pattern
    _ACTIVE_ACTION_REGEX = re.compile(
        r"\b(?:I|we)\s+(?:led|designed|engineered|spearheaded|developed|analyzed|optimized|reduced|increased|delivered|architected|executed|orchestrated|negotiated|launched|built|formulated|automated|improved|achieved)\b",
        re.IGNORECASE
    )

    # Passive voice construction pattern
    _PASSIVE_VOICE_REGEX = re.compile(
        r"\b(?:is|are|was|were|been|being|be)\s+(?:[a-z]+ed|built|done|made|given|taken|seen|written|led|driven)\b",
        re.IGNORECASE
    )

    @classmethod
    def count_filler_words(cls, text: str) -> Dict[str, Any]:
        """
        Identifies, categorizes, and counts filler words and hesitation phrases.
        Separates non-lexical vocalizations ('um', 'uh') from conversational crutches ('basically', 'like').
        """
        if not text:
            return {
                "total_fillers": 0,
                "breakdown": {},
                "filler_density_pct": 0.0,
                "is_clean": True,
                "non_lexical_count": 0,
                "lexical_crutches_count": 0,
                "stutter_count": 0,
                "stutters_detected": []
            }

        text_lower = text.lower()
        words = cls._WORD_REGEX.findall(text_lower)
        total_words = len(words)
        breakdown = {}
        total_fillers = 0

        # Legacy and total filler match
        for clean_term, pattern_regex in cls._COMPILED_FILLERS:
            matches = pattern_regex.findall(text_lower)
            if matches:
                breakdown[clean_term] = len(matches)
                total_fillers += len(matches)

        # Categorized counts
        non_lexical_count = sum(len(rgx.findall(text_lower)) for _, rgx in cls._COMPILED_NON_LEXICAL)
        lexical_count = sum(len(rgx.findall(text_lower)) for _, rgx in cls._COMPILED_LEXICAL)

        # Detect stutters / immediate token repetition
        stutter_matches = cls._STUTTER_REGEX.findall(text)
        stutter_count = len(stutter_matches)

        density = round((total_fillers / total_words) * 100, 1) if total_words > 0 else 0.0
        return {
            "total_fillers": total_fillers,
            "total_words": total_words,
            "breakdown": breakdown,
            "filler_density_pct": density,
            "is_clean": density < 3.0 and stutter_count == 0,
            "non_lexical_count": non_lexical_count,
            "lexical_crutches_count": lexical_count,
            "stutter_count": stutter_count,
            "stutters_detected": stutter_matches
        }

    @classmethod
    def calculate_speaking_rate(cls, text: str, duration_seconds: float) -> Dict[str, Any]:
        """Calculates Words Per Minute (WPM) and pacing category."""
        words = len(cls._WORD_REGEX.findall(text)) if text else 0
        minutes = max(duration_seconds / 60.0, 0.1)
        wpm = round(words / minutes, 1)

        if wpm < 110:
            pacing = "Slow / Hesitant"
            verdict = "Increase speech cadence; avoid prolonged pauses between points."
        elif wpm <= 165:
            pacing = "Optimal Executive Cadence"
            verdict = "Excellent pace; professional, measured, and easy to follow."
        else:
            pacing = "Rushed / Fast"
            verdict = "Slow down slightly to ensure clear articulation and executive presence."

        return {
            "word_count": words,
            "duration_seconds": round(duration_seconds, 1),
            "wpm": wpm,
            "pacing_category": pacing,
            "guidance": verdict
        }

    @classmethod
    def calculate_lexical_diversity(cls, text: str) -> Dict[str, Any]:
        """
        Computes Type-Token Ratio (TTR) and vocabulary richness index.
        Evaluates lexical variety and detects circular repetitive phrasing.
        """
        if not text:
            return {"ttr": 0.0, "unique_words": 0, "total_words": 0, "verdict": "Empty response"}

        words = [w.lower() for w in cls._WORD_REGEX.findall(text)]
        total = len(words)
        if total == 0:
            return {"ttr": 0.0, "unique_words": 0, "total_words": 0, "verdict": "Empty response"}

        unique = len(set(words))
        ttr = round(unique / total, 3)

        if ttr >= 0.72:
            verdict = "High Vocabulary Richness — Diverse and articulate phrasing"
        elif ttr >= 0.58:
            verdict = "Moderate Vocabulary Breadth — Standard professional delivery"
        else:
            verdict = "Repetitive Phrasing — High word reuse; expand vocabulary variety"

        return {
            "ttr": ttr,
            "unique_words": unique,
            "total_words": total,
            "verdict": verdict
        }

    @classmethod
    def evaluate_star_compliance(cls, text: str) -> Dict[str, Any]:
        """
        Evaluates whether candidate structured verbal answer with STAR method.
        Upgraded to also check chronological narrative flow (Situation -> Task -> Action -> Result).
        """
        if not text:
            return {
                "star_score": 0,
                "components_present": [],
                "missing_components": ["Situation", "Task", "Action", "Result"],
                "is_well_structured": False,
                "chronological_flow": False
            }

        text_lower = text.lower()
        components_found = {}
        first_occurrence_idx = {}
        missing = []

        for component, indicators in cls.STAR_INDICATORS.items():
            earliest_pos = 999999
            for ind in indicators:
                pos = text_lower.find(ind)
                if pos != -1 and pos < earliest_pos:
                    earliest_pos = pos

            if earliest_pos < 999999:
                components_found[component] = True
                first_occurrence_idx[component] = earliest_pos
            else:
                components_found[component] = False
                missing.append(component)

        present_keys = [k for k, v in components_found.items() if v]
        base_score = len(present_keys) * 25

        # Check chronological flow: Situation before Action, Action before Result
        sit_pos = first_occurrence_idx.get("Situation", -1)
        act_pos = first_occurrence_idx.get("Action", -1)
        res_pos = first_occurrence_idx.get("Result", -1)

        chronological_flow = True
        if sit_pos != -1 and act_pos != -1 and sit_pos > act_pos:
            chronological_flow = False
        if act_pos != -1 and res_pos != -1 and act_pos > res_pos:
            chronological_flow = False

        # Award structure bonus if flow is authentically chronological
        final_score = base_score
        if not chronological_flow and base_score > 50:
            final_score = max(50, base_score - 10)

        return {
            "star_score": final_score,
            "components_present": present_keys,
            "missing_components": missing,
            "is_well_structured": final_score >= 75,
            "chronological_flow": chronological_flow,
            "component_positions": first_occurrence_idx
        }

    @classmethod
    def evaluate_syntactic_style(cls, text: str) -> Dict[str, Any]:
        """
        Evaluates active vs. passive voice and sentence structure health.
        Detects run-on sentences and syntactic fragmentation.
        """
        if not text:
            return {
                "active_verb_count": 0,
                "passive_verb_count": 0,
                "active_voice_ratio": 1.0,
                "run_on_sentence_count": 0,
                "fragment_count": 0,
                "voice_verdict": "Balanced"
            }

        active_matches = cls._ACTIVE_ACTION_REGEX.findall(text)
        passive_matches = cls._PASSIVE_VOICE_REGEX.findall(text)

        active_count = len(active_matches)
        passive_count = len(passive_matches)
        total_voice = active_count + passive_count

        active_ratio = round(active_count / max(total_voice, 1), 2) if total_voice > 0 else 0.85

        # Split sentences by terminal punctuation
        raw_sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        run_ons = 0
        fragments = 0

        for sent in raw_sentences:
            word_count = len(cls._WORD_REGEX.findall(sent))
            if word_count > 38:
                run_ons += 1
            elif word_count < 4:
                fragments += 1

        if active_ratio >= 0.70:
            voice_verdict = "Dominantly Active & Impact-Driven (Executive Style)"
        elif active_ratio >= 0.40:
            voice_verdict = "Balanced Active/Passive Expression"
        else:
            voice_verdict = "Excessively Passive — Reframe using direct first-person ownership ('I executed...')"

        return {
            "active_verb_count": active_count,
            "passive_verb_count": passive_count,
            "active_voice_ratio": active_ratio,
            "run_on_sentence_count": run_ons,
            "fragment_count": fragments,
            "sentence_count": len(raw_sentences),
            "voice_verdict": voice_verdict
        }

    @classmethod
    def analyze_verbal_response(cls, text: str, duration_seconds: float = 45.0) -> Dict[str, Any]:
        """
        Produces comprehensive verbal communication diagnostic audit.
        Combines filler words, stutters, cadence, lexical diversity,
        chronological STAR structure, active voice, and domain terminology.
        """
        fillers = cls.count_filler_words(text)
        pacing = cls.calculate_speaking_rate(text, duration_seconds)
        star = cls.evaluate_star_compliance(text)
        diversity = cls.calculate_lexical_diversity(text)
        syntax = cls.evaluate_syntactic_style(text)
        domain_data = DomainVocabularyCorrector.correct_transcription(text)

        # Composite delivery score calculation (0 - 100)
        # Weights: 30% STAR, 20% Pacing, 20% Low Fillers/Stutters, 15% Lexical Breadth, 15% Active Voice
        filler_score = max(0, 100 - (fillers["filler_density_pct"] * 10) - (fillers["stutter_count"] * 5))
        pacing_score = 100 if "Optimal" in pacing["pacing_category"] else 70
        star_score = star["star_score"]
        diversity_score = min(100, int(diversity["ttr"] * 125)) if diversity["total_words"] >= 10 else 75
        active_score = int(syntax["active_voice_ratio"] * 100)

        composite = round(
            (0.30 * star_score) +
            (0.20 * pacing_score) +
            (0.20 * filler_score) +
            (0.15 * diversity_score) +
            (0.15 * active_score),
            1
        )

        # Cap composite within bounds
        composite = max(10.0, min(100.0, composite))

        return {
            "composite_delivery_score": composite,
            "executive_presence_level": "Strong" if composite >= 75 else ("Developing" if composite >= 50 else "Needs Coaching"),
            "filler_analysis": fillers,
            "cadence_analysis": pacing,
            "star_compliance": star,
            "lexical_diversity": diversity,
            "syntactic_style": syntax,
            "domain_fluency": {
                "terms_found": domain_data["domain_terms_found"],
                "density_pct": domain_data["domain_density_pct"],
                "corrections": domain_data["corrections_applied"]
            }
        }
