---
title: InterviewIQ - AI Placement Coach
emoji: 🎯
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.38.0
app_file: frontend/app.py
pinned: false
license: mit
---

# 🎯 InterviewIQ — AI Placement & Interview Preparation Platform

> *Don't Practice Questions. Experience the Interview.*

[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B.svg)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg)](https://www.python.org/)
[![AI-Model](https://img.shields.io/badge/LLM-Gemini%20Cascade%20(2.5%20Flash)-4285F4.svg)](https://aistudio.google.com/)
[![Tests](https://img.shields.io/badge/Tests-108%2F108%20Passing%20(100%25)-success.svg)](#)
[![UI-Design](https://img.shields.io/badge/Design-Neumorphism%20Soft%20UI-718096.svg)](#)
[![Responsive](https://img.shields.io/badge/Viewport-Desktop%20%7C%20Tablet%20%7C%20Mobile-10B981.svg)](#)

---

## 📖 Executive Summary
**InterviewIQ** is an enterprise-grade, multi-agent AI placement coach engineered for candidates preparing for competitive campus and lateral hiring drives. Developed as a capstone project for the **MBA Digital Transformation (DT)** curriculum by **Nitish & Jeevana**, InterviewIQ addresses the fundamental flaws of static question banks and blind ATS scanners by synthesizing dynamic, multi-dimensional candidate evaluation, simulated device layouts, and closed-loop diagnostic retraining.

---

## 🔄 The 6-Step Preparation Pipeline

1. **Step 1: Resume & Job Description Onboarding with Live 6-Stage Telemetry**
   - Ingests PDF/TXT resumes and job descriptions with automated validation.
   - Real-time `st.status()` stage tracker providing deep transparency across profile ingestion, JD extraction, company intelligence retrieval, fit calculation, question formulation, and 30-MCQ test synthesis.
   - Dynamic Gemini model discovery with Tier 1/2/3 cascade (`gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-1.5-flash` → `gemini-1.5-pro`) and proactive token-bucket rate limiter (<=12 RPM cooldown).

2. **Step 2: Strategic Fit Analysis & Formal Recommendation Engine**
   - 4-column requirements matrix mapping candidate skills to role benchmarks.
   - Multi-tier experience scoring and strict technical capability matching.
   - Target company leadership DNA cards (Amazon, Google, McKinsey, Goldman Sachs, Microsoft).
   - Dual PDF downloads: Standalone 2-3 page **Strategic Fit Report PDF** and complete candidate dossier.

3. **Step 3: Targeted Question Bank with 100% Coverage Checklist**
   - Tailored questions across 5 dimensions: Resume Challenges, Technical Deep-Dives, Scenario Problem Solving, Behavioral STAR Probes, and Gap Defenses.
   - Dual export options: Download full question bank as `.md` or `.txt`.

4. **Step 4: Timed 30-MCQ Online Test & Google Local NLP Voice Interview Simulator**
   - 30-minute timed exam with 30 scenario-based MCQs mapped to role capabilities.
   - Anti-cheating proctoring safeguards: Tab visibility change detection, auto-submission on expiration, and option shuffle invariance.
   - Browser-native Voice Interview Simulator via Web Speech API (zero external cloud speech API cost and zero latency).
   - Real-time speech analytics: WPM pacing, filler word detection (*um, like, actually*), and STAR framework compliance scoring.

5. **Step 5: Longitudinal Diagnostic Matrix, PDF Dossier & Multi-Round Re-Test**
   - Unified readiness matrix linking empirical test performance with structural fit (45% fit / 55% test composite formula).
   - 48-hour prioritized study roadmap highlighting dual-weakness deficit areas.
   - 1-click generation of multi-page publication-quality vector PDF evaluation dossiers via ReportLab.
   - Closed-loop re-testing: Re-weights Round 2+ question banks and exams targeting candidate weakness areas.

6. **Step 6: Dynamic 7-Day Personalized Micro-Curriculum & Curated Resource Library**
   - Automated 7-day daily study schedule allocating high-priority gaps to Days 1–3, medium gaps to Days 4–5, targeted question drills to Day 6, and mock exam dress rehearsal to Day 7.
   - 48-hour emergency sprint plan for imminent interview deadlines.
   - Curated resource library of 100% free learning resources (videos, cheat sheets, interactive courses) with interactive checklist persistence.

---

## 📱 Mobile, Tablet & Desktop Responsive Modes
InterviewIQ provides seamless responsive styling powered by Neumorphic CSS and an interactive Viewport Simulator in the sidebar:
- **🖥️ Desktop Mode (100% / Auto):** Full multi-column dashboard with side-by-side metric decks and wide data tables.
- **📱 Mobile Mode (390px):** Constrained preview simulating mobile devices, stacking columns vertically with full-width action buttons, touch-friendly tap targets ($\ge 44\text{px}$), and responsive typography.
- **💻 Tablet Mode (768px):** Medium-width simulated viewport with clean 2x2 metric wraps and optimized card spacing.
- **Fluid CSS Media Queries:** Automatic responsiveness at native viewport breakpoints (`max-width: 768px` and `769px–1024px`) with inline checkbox protection.

---

## 🏛️ Decoupled Multi-Agent Architecture

InterviewIQ organizes domain intelligence into specialized autonomous agents coordinated by a central Orchestrator:

1. **📄 Resume Reviewer Agent ([agents/resume_reviewer.py](agents/resume_reviewer.py)):** Extracts structured candidate profiles, academic stages, projects, and vulnerable claims with upstream parsing failsafes.
2. **💼 JD Analyzer Agent ([agents/jd_analyzer.py](agents/jd_analyzer.py)):** Isolates technical requirements, seniority benchmarks, and core skills with heuristic fallbacks.
3. **🏢 Company Intelligence RAG Agent ([agents/company_intel_agent.py](agents/company_intel_agent.py)):** Ingests and enriches assessment flows with target corporate culture rubrics.
4. **📊 Strategic Fit Analyzer Engine ([agents/fit_analyzer.py](agents/fit_analyzer.py)):** Computes strict match %, experience scoring, and gap classifications.
5. **📚 Targeted Question Bank Agent ([agents/question_bank.py](agents/question_bank.py)):** Synthesizes categorized interview probes and topic checklists.
6. **📝 Online Test Assessment Agent ([agents/online_test_agent.py](agents/online_test_agent.py)):** Generates and scores 30-question scenario-based exams.
7. **🎙️ Voice Interview Simulator Agent ([agents/voice_interview_agent.py](agents/voice_interview_agent.py)):** Manages vocal mock interviews with speech analytics.
8. **🎯 Unified Diagnostics & Feedback Agent ([agents/feedback_agent.py](agents/feedback_agent.py)):** Assembles composite readiness scores and study roadmaps.
9. **📅 Dynamic Micro-Curriculum Agent ([agents/micro_curriculum_agent.py](agents/micro_curriculum_agent.py)):** Creates 7-day day-by-day learning plans with free learning resources.
10. **⚙️ Central Orchestrator ([orchestrator/orchestrator.py](orchestrator/orchestrator.py)):** Governs multi-round session progression, thread-safe client lifecycle, and closed-loop re-testing.

---

## 🎨 Neumorphic Design System & Visual Tokens

InterviewIQ utilizes an executive Neumorphic (Soft UI) design system ([frontend/styles/neumorphism.css](frontend/styles/neumorphism.css) and [frontend/styles/theme.py](frontend/styles/theme.py)):
- **Tactile Depth:** Subtle dual-shadow geometry on clean slate surfaces (`#F8FAFC`).
- **High Contrast & WCAG AA:** All typography strictly enforces contrast guardrails with WCAG AA compliant text (`#0F172A`, `#B45309`).
- **Pure SVG Icon Library ([frontend/components/icons.py](frontend/components/icons.py)):** Zero external icon fonts or CDN network dependencies.
- **Decoupled UI Kit ([frontend/components/ui_kit.py](frontend/components/ui_kit.py)):** Reusable helper components for badges, metric cards, callouts, and progress bars.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10, 3.11, or 3.12 installed.
- Active Google Gemini API Key.

### Option 1: One-Click Launch (Windows)
```cmd
launch.bat
```

### Option 2: Manual Execution
```bash
# 1. Activate virtual environment
.\.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the Streamlit application
streamlit run frontend/app.py
```

---

## 🧪 Automated Test Suite (108/108 Tests Passing)

Verify end-to-end platform integrity:
```bash
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

All 108 tests pass cleanly with 100% success rate:
- `tests/test_agents.py`: Baseline agent pipeline, formula scoring, and closed-loop retesting (9 tests).
- `tests/test_timer_and_proctor.py`: Exam timer countdown, visibility change anti-cheating, and option shuffle invariance (4 tests).
- `tests/test_pdf_exporter.py`: Full dossier PDF, standalone Strategic Fit Report PDF, and ReportLab vector styling (4 tests).
- `tests/test_speech_engine.py`: Google Local NLP speech analytics, WPM pacing, and filler word detection (5 tests).
- `tests/test_company_intel.py`: Corporate leadership principles retrieval and question enrichment (5 tests).
- `tests/test_database.py`: SQLite schema initialization, multi-round session persistence, and snapshots (5 tests).
- `tests/test_api_quota_and_cache.py`: Token-Bucket rate pacing, two-tier SHA-256 caching, key validation, and model failover (8 tests).
- `tests/test_micro_curriculum_agent.py`: 7-day schedule generation, free curated resource mapping, and checklist tracking (9 tests).
- `tests/test_domain_vocabulary.py`: Phonetic confusion repair, acronym collapse, and domain density scoring (6 tests).
- `tests/test_speech_analytics_advanced.py`: Disfluency categorization, stutter detection, and STAR sequence adherence (7 tests).
- `tests/test_ui_kit.py`: Design tokens, SVG icon library, semantic badges, and progress bar clamping (8 tests).
- `tests/test_integration.py`: End-to-end multi-round lifecycle, PDF dossier generation, and micro-curriculum persistence (2 tests).
- `tests/test_uat_journeys.py`: End-to-end candidate user journeys across all stages (5 tests).
- `tests/test_uat_streamlit_app.py`: Streamlit AppTest headless UI navigation, responsive mode switching, and interactive feature validation (5 tests).
- Additional test modules covering salary bands, quota reservations, and resilient parsers.

---

## 📁 Repository Structure
```text
├── agents/                    # Autonomous multi-agent pipeline
│   ├── base_agent.py
│   ├── company_intel_agent.py
│   ├── feedback_agent.py
│   ├── fit_analyzer.py
│   ├── jd_analyzer.py
│   ├── micro_curriculum_agent.py
│   ├── online_test_agent.py
│   ├── question_bank.py
│   ├── resume_reviewer.py
│   └── voice_interview_agent.py
├── orchestrator/              # Master pipeline orchestrator
│   └── orchestrator.py
├── frontend/                  # Streamlit frontend & design system
│   ├── app.py
│   ├── components/
│   │   ├── exam_timer.html
│   │   ├── icons.py
│   │   └── ui_kit.py
│   └── styles/
│       ├── neumorphism.css
│       └── theme.py
├── utils/                     # Core utility & persistence infrastructure
│   ├── api_quota_manager.py
│   ├── curriculum_resources.py
│   ├── database.py
│   ├── domain_vocabulary.py
│   ├── gemini_cache.py
│   ├── gemini_client.py
│   ├── pdf_exporter.py
│   ├── pdf_parser.py
│   ├── quality_controller.py
│   ├── salary_bands.py
│   ├── session_manager.py
│   └── speech_analytics.py
├── docs/                      # Full documentation suite (.md & .docx)
│   ├── BUSINESS_CASE.md / .docx
│   ├── GITHUB_DEPLOYMENT_AND_PUSH_STRATEGY.md / .docx
│   ├── KT_DOCUMENT.md / .docx
│   ├── MOBILE_AND_TAB_VIEW_GUIDE.md / .docx
│   ├── PROJECT_LOG.md / .docx
│   ├── PROJECT_STATUS.md / .docx
│   └── TECH_ARCHITECTURE.md / .docx
├── data/                      # Local persistence & samples
│   ├── interviewiq.db
│   ├── samples/
│   └── sessions/
├── tests/                     # 108 automated tests across all sub-systems
└── requirements.txt           # Python dependencies
```

---

## 👥 Developer Attribution
- **Developed by your friends Nitish & Jeevana**
- Capstone Project for MBA Digital Transformation (DT) Curriculum
- Powered by Google Gemini Multi-Tier Cascade & Neumorphic Design System

---

## 🎓 Academic Alignment (MBA Digital Transformation)
- **Digitizing Qualitative Talent Assessment:** Converts unstructured recruitment artifacts into rigorous, quantitative fit metrics.
- **Zero Marginal Cost Placement Coaching:** Delivers personalized, conversational, and diagnostic coaching with zero recurring third-party API expense.
- **Continuous Closed-Loop Learning:** Storing longitudinal performance data in SQLite to dynamically focus future rounds on verified candidate weaknesses.
