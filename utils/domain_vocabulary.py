"""
Domain Vocabulary & Phonetic Correction Engine for InterviewIQ.
Improves Google Local NLP speech recognition accuracy by mapping common
ASR phonetic misrecognitions to canonical MBA, Consulting, Tech, and Product terms.
Operates with zero external API calls and zero cloud cost.
"""

import re
from typing import Dict, Any, List, Set, Tuple


class DomainVocabularyCorrector:
    """
    Curated domain lexicon and phonetic repair engine for business,
    technology, and management consulting speech-to-text transcriptions.
    """

    # 120+ Curated Domain Terms across Core Professional Families
    CANONICAL_DOMAIN_TERMS: Set[str] = {
        # Consulting, Strategy & Frameworks
        "MECE", "SWOT", "PESTLE", "Porter's Five Forces", "80/20 Rule", "Pareto Principle",
        "EBITDA", "P&L", "CAGR", "DCF", "NPV", "IRR", "WACC", "CapEx", "OpEx",
        "Gross Margin", "Net Margin", "Operating Leverage", "Unit Economics",
        "Value Chain", "Root Cause Analysis", "Hypothesis-Driven", "Issue Tree",
        "Market Sizing", "Synergy", "Due Diligence", "Benchmarking", "Competitive Moat",
        "McKinsey", "BCG", "Bain", "Deloitte", "PwC", "EY", "KPMG",

        # Product Management & Agile
        "Agile", "Scrum", "Sprint", "Kanban", "MVP", "PRD", "User Story", "Product Backlog",
        "Retrospective", "Burndown Chart", "North Star Metric", "Product-Market Fit",
        "GTM Strategy", "Customer Journey", "Persona", "Wireframe", "Feature Prioritization",
        "RICE Framework", "MoSCoW", "Roadmap", "OKRs", "A/B Testing", "Cohort Analysis",

        # Technology, Cloud & Engineering
        "SQL", "PostgreSQL", "MySQL", "NoSQL", "MongoDB", "ETL", "Data Pipeline",
        "Data Warehouse", "Snowflake", "BigQuery", "Databricks", "Apache Spark",
        "Kafka", "PyTorch", "TensorFlow", "Scikit-learn", "Machine Learning",
        "Deep Learning", "NLP", "LLM", "Docker", "Kubernetes", "Microservices",
        "API", "REST API", "GraphQL", "AWS", "Azure", "GCP", "CI/CD", "DevOps",
        "Git", "GitHub", "Scalability", "Low Latency", "High Availability",

        # Business Metrics & Commercial Operations
        "KPI", "KPIs", "CAC", "LTV", "LTV/CAC", "ROI", "ARR", "MRR", "Churn Rate",
        "Retention Rate", "NPS", "Conversion Rate", "Funnel Optimization", "ARPU",
        "B2B", "B2C", "D2C", "SaaS", "PaaS", "IaaS", "Fintech", "Healthtech",
        "Edtech", "E-commerce", "Omnichannel", "Marketplace", "Top-Line", "Bottom-Line"
    }

    # Phonetic Misrecognition Mapping: {phonetic_phrase_lower: canonical_replacement}
    PHONETIC_CONFUSION_MAP: Dict[str, str] = {
        # Consulting & Finance Acronyms
        "macy": "MECE",
        "missy": "MECE",
        "macey": "MECE",
        "me c": "MECE",
        "me see": "MECE",
        "m e c e": "MECE",
        "ebita": "EBITDA",
        "ebit dah": "EBITDA",
        "ebit da": "EBITDA",
        "a bit the": "EBITDA",
        "a bit da": "EBITDA",
        "e b i t d a": "EBITDA",
        "piano": "P&L",
        "p and l": "P&L",
        "p and el": "P&L",
        "p n l": "P&L",
        "p&l": "P&L",
        "p and lamb": "P&L",
        "cagger": "CAGR",
        "c a g r": "CAGR",
        "d c f": "DCF",
        "dcf valuation": "DCF valuation",
        "n p v": "NPV",
        "i r r": "IRR",
        "wack": "WACC",
        "w a c c": "WACC",
        "cap ex": "CapEx",
        "capex": "CapEx",
        "op ex": "OpEx",
        "opex": "OpEx",
        "s w o t": "SWOT",
        "swat analysis": "SWOT analysis",
        "p e s t l e": "PESTLE",
        "pest analysis": "PESTLE analysis",
        "porters five forces": "Porter's Five Forces",
        "porter 5 forces": "Porter's Five Forces",
        "80 20 rule": "80/20 Rule",
        "80-20 rule": "80/20 Rule",
        "pareto principle": "Pareto Principle",

        # Tech, Cloud & Data Acronyms
        "sequel": "SQL",
        "c cool": "SQL",
        "sea quel": "SQL",
        "s q l": "SQL",
        "no sequel": "NoSQL",
        "no-sequel": "NoSQL",
        "no s q l": "NoSQL",
        "post grass": "PostgreSQL",
        "post gres": "PostgreSQL",
        "post grace": "PostgreSQL",
        "postgre sql": "PostgreSQL",
        "mongo db": "MongoDB",
        "mango db": "MongoDB",
        "e t l": "ETL",
        "pi torch": "PyTorch",
        "pie torch": "PyTorch",
        "py torch": "PyTorch",
        "tensor flow": "TensorFlow",
        "psy kit learn": "Scikit-learn",
        "sci kit learn": "Scikit-learn",
        "scikit learn": "Scikit-learn",
        "cuber netties": "Kubernetes",
        "koober netees": "Kubernetes",
        "koober netes": "Kubernetes",
        "kubernetis": "Kubernetes",
        "snow flake": "Snowflake",
        "big query": "BigQuery",
        "rest a p i": "REST API",
        "graph q l": "GraphQL",
        "c i c d": "CI/CD",
        "ci cd": "CI/CD",
        "a w s": "AWS",
        "g c p": "GCP",

        # Product, Metrics & Startups
        "k p i": "KPI",
        "k p is": "KPIs",
        "kpis": "KPIs",
        "c a c": "CAC",
        "l t v": "LTV",
        "r o i": "ROI",
        "a r r": "ARR",
        "m r r": "MRR",
        "n p s": "NPS",
        "net promoter score": "NPS",
        "b to b": "B2B",
        "b 2 b": "B2B",
        "b to c": "B2C",
        "b 2 c": "B2C",
        "d to c": "D2C",
        "d 2 c": "D2C",
        "sass": "SaaS",
        "s a a s": "SaaS",
        "pass": "PaaS",
        "p a a s": "PaaS",
        "i a a s": "IaaS",
        "m v p": "MVP",
        "p r d": "PRD",
        "o k r": "OKRs",
        "o k rs": "OKRs",
        "okrs": "OKRs",
        "a b testing": "A/B Testing",
        "a/b test": "A/B Testing",
        "a b test": "A/B Testing",
        "can ban": "Kanban",
        "kan ban": "Kanban",
        "burn down chart": "Burndown Chart",
        "burndown": "Burndown Chart",
        "north star metric": "North Star Metric",
        "product market fit": "Product-Market Fit",

        # Consulting Firms & Employers
        "mac kinsey": "McKinsey",
        "mc kinsey": "McKinsey",
        "b c g": "BCG",
        "boston consulting": "BCG",
        "bane and company": "Bain",
        "bain and company": "Bain",
        "p w c": "PwC",
        "e y": "EY",
        "ernst and young": "EY",
        "k p m g": "KPMG"
    }

    # Known 2, 3, and 4 letter acronyms for whitespace collapse
    VALID_SPELLED_ACRONYMS: Dict[str, str] = {
        "k p i": "KPI",
        "k p is": "KPIs",
        "c a c": "CAC",
        "l t v": "LTV",
        "r o i": "ROI",
        "a r r": "ARR",
        "m r r": "MRR",
        "n p v": "NPV",
        "d c f": "DCF",
        "i r r": "IRR",
        "e t l": "ETL",
        "s q l": "SQL",
        "a w s": "AWS",
        "g c p": "GCP",
        "p r d": "PRD",
        "m v p": "MVP",
        "o k r": "OKR",
        "b c g": "BCG",
        "p w c": "PwC",
        "n p s": "NPS"
    }

    # Pre-compile multi-word substitution patterns sorted by character length descending
    _COMPILED_PATTERNS: List[Tuple[re.Pattern, str]] = []

    @classmethod
    def _init_patterns(cls):
        if cls._COMPILED_PATTERNS:
            return
        # Sort confusion keys by length descending to match longest phrase first
        sorted_phrases = sorted(cls.PHONETIC_CONFUSION_MAP.keys(), key=len, reverse=True)
        for phrase in sorted_phrases:
            replacement = cls.PHONETIC_CONFUSION_MAP[phrase]
            # Whole word boundary matching
            escaped = re.escape(phrase)
            pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
            cls._COMPILED_PATTERNS.append((pattern, replacement))

    @classmethod
    def correct_transcription(cls, text: str) -> Dict[str, Any]:
        """
        Applies domain vocabulary phonetic corrections to an ASR transcript.
        
        Returns:
            Dict containing:
                - original: original input string
                - corrected: post-processed string with canonical casing and terminology
                - corrections_applied: list of correction dictionaries
                - domain_terms_found: list of domain terms identified
                - domain_density_pct: percentage of words representing domain concepts
        """
        if not text or not text.strip():
            return {
                "original": text,
                "corrected": text,
                "corrections_applied": [],
                "domain_terms_found": [],
                "domain_density_pct": 0.0
            }

        cls._init_patterns()
        working_text = text
        corrections_applied: List[Dict[str, str]] = []

        # Step 1: Collapsed spelled-out acronyms ("k p i" -> "KPI")
        for spelled, canonical in cls.VALID_SPELLED_ACRONYMS.items():
            pattern = re.compile(rf"\b{re.escape(spelled)}\b", re.IGNORECASE)
            if pattern.search(working_text):
                working_text = pattern.sub(canonical, working_text)
                corrections_applied.append({"original": spelled, "corrected": canonical, "type": "acronym_collapse"})

        # Step 2: Apply phonetic confusion replacements
        for pattern, replacement in cls._COMPILED_PATTERNS:
            matches = pattern.findall(working_text)
            if matches:
                working_text = pattern.sub(replacement, working_text)
                for m in set(matches):
                    corrections_applied.append({"original": m, "corrected": replacement, "type": "phonetic_repair"})

        # Step 3: Identify all canonical domain terms present
        working_lower = working_text.lower()
        domain_terms_found = []
        for term in cls.CANONICAL_DOMAIN_TERMS:
            term_pattern = rf"\b{re.escape(term.lower())}\b"
            if re.search(term_pattern, working_lower):
                domain_terms_found.append(term)

        # Step 4: Calculate domain vocabulary density percentage
        words = re.findall(r"\b\w+\b", working_text)
        total_words = len(words)
        domain_density = round((len(domain_terms_found) / max(total_words, 1)) * 100, 2)

        return {
            "original": text,
            "corrected": working_text,
            "corrections_applied": corrections_applied,
            "domain_terms_found": domain_terms_found,
            "domain_density_pct": domain_density
        }

    @classmethod
    def calculate_domain_density(cls, text: str) -> float:
        """Convenience method returning domain vocabulary density percentage."""
        result = cls.correct_transcription(text)
        return result["domain_density_pct"]
