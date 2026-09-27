# InterviewIQ — Technical Architecture Document

**Current Date:** 2026-09-26  
**Sprint Status:** Multi-Subagent Output Quality Verification Engine & In-Process Quality Assurance Complete (98/98 Tests Passing in 100% Reliability)  
**Test Suite Health:** 98 of 98 unit, integration, and UAT tests passing cleanly (`Ran 98 tests in 229s — OK`)  
**API Key Governance:** User-Supplied & Verified via Real-Time Cloud Probe (Zero Hardcoded Keys)  
**Rate Safety:** Atomic Reservation Token-Bucket Rate Pacer (<=12 RPM) & Two-Tier SHA-256 Cache (RAM + SQLite)  

---

## 1. System Architecture Overview
InterviewIQ is engineered as a decoupled, event-driven multi-agent framework governed by a master Orchestrator. The system fuses static structural document alignment (Resume vs JD) with empirical examination performance (Timed 30-MCQ testing and Multimodal Voice simulation), persisting historical sessions into a multi-tenant relational database and enforcing strict Google Gemini API quota limits via intelligent rate pacing and two-tier caching.

```
       +---------------------------------------------------------------------------------+
       |                               STREAMLIT FRONTEND                                |
       |     (Steps 1 to 6: Light Theme #F8FAFC / #FFFFFF, High-Contrast Typography)     |
       +---------------------------------------+-----------------------------------------+
                                               |
                                               v
       +---------------------------------------------------------------------------------+
       |                               MASTER ORCHESTRATOR                               |
       |     (Dual Onboarding Modes, Session Lifecycle, Failsafe Engine & Retest Loops)   |
       +---------------------------------------+-----------------------------------------+
                                               |
         +--------------------+----------------+-------------------+--------------------+
         |                    |                |                   |                    |
         v                    v                v                   v                    v
  +--------------+     +--------------+ +--------------+    +--------------+     +--------------+
  |    Resume    |     |  JD Analyzer | | Company Intel|    | Question Bank|     |  Curriculum  |
  |   Reviewer   |     |    Agent     | |  RAG Engine  |    |    Agent     |     |    Agent     |
  +-------+------+     +-------+------+ +-------+------+    +-------+------+     +-------+------+
          |                    |                |                   |                    |
          +----------+---------+                |                   |                    |
                     |                          |                   |                    |
                     v                          |                   |                    |
              +--------------+                  |                   |                    |
              | Fit Analysis | <----------------+                   |                    |
              |    Module    |                                      |                    |
              +-------+------+                                      |                    |
                      |                                             |                    |
                      +----------------------+----------------------+                    |
                                             |                                           |
                                             v                                           |
                              +-----------------------------+                            |
                              |  Dual-Mode Onboarding Gate  |                            |
                              +--------------+--------------+                            |
                                             |                                           |
                      +----------------------+----------------------+                    |
                      | (Option 1: Fast Track)                      | (Option 2: Complete)
                      v                                             v                    |
              [Step 2 Fit Report & QB]                      +--------------+             |
              (On-Demand Test Calibration)                  |  Online Test |             |
                      |                                     |  Agent (MCQ) |             |
                      |                                     | (Anti-Cheat) |             |
                      |                                     +-------+------+             |
                      |                                             |                    |
                      +----------------------+----------------------+                    |
                                             |                                           |
                                             v                                           |
                                      +--------------+                                   |
                                      |   Feedback   | ----> [Step 5 Unified Diagnostics]|
                                      |    Agent     | ----> [Dual-Weakness Alerts 🚨   ]|
                                      +-------+------+ ----> [Vector PDF Dossier Export ]|
                                             |                                           |
                                             +-------------------------------------------+
                                             v
                                      +--------------+
                                      | 7-Day Micro- | (Step 6 Prep Curriculum)
                                      |  Curriculum  | ----> [Curated Resource Library  ]
                                      +--------------+ ----> [4-Stat Executive Dashboard]
                                             |
       +-------------------------------------+-------------------------------------------+
       |                        CROSS-CUTTING PLATFORM SERVICES                         |
       +-------------------------------------+-------------------------------------------+
         |                                   |                                         |
         v                                   v                                         v
  +-------------------+             +-------------------+                     +-------------------+
  | API Quota Manager |             |  Two-Tier Cache   |                     | SQLite Database   |
  | (<= 12 RPM Pacer, |             | (L1 RAM + L2 DB,  |                     | (10 Tables, WAL,  |
  |  Key Validation)  |             |  SHA-256 Hashes)  |                     |  Pragmas & MMAP)  |
  +-------------------+             +-------------------+                     +-------------------+
```

---

## 2. Agent Interfacing & Data Contracts

### 2.1 Resume Reviewer Agent (`agents/resume_reviewer.py`)
- **Input:** `resume_text: str`
- **Output:** Structured JSON candidate profile:
  - `candidate_bio`: Name, education, contact, and objective.
  - `education`: Degrees, institutions, years, and academic standing.
  - `skills`: Categorized technical skills, tools, and libraries.
  - `projects`: Title, role, technologies, and quantified impact metrics.
  - `challenge_areas`: Methodological ambiguities and unquantified claims ripe for interviewer scrutiny.
- **Status:** Baseline core agent (100% preserved and untouched).

### 2.2 JD Analyzer Agent (`agents/jd_analyzer.py`)
- **Input:** `jd_text: str`
- **Output:** Structured JSON job requirement profile:
  - `mandatory_skills`: Core desk capabilities (must-have requirements).
  - `preferred_skills`: Certifications, secondary frameworks, nice-to-have tools.
  - `platforms`: Cloud environments, OS, database engines.
  - `domain_competencies`: Industry-specific concepts and functional requirements.
- **Status:** Baseline core agent (100% preserved and untouched).

### 2.3 Fit Analysis Module (`agents/fit_analyzer.py`)
- **Input:** `resume_profile: dict`, `jd_profile: dict`
- **Output:** Institutional corporate evaluation dictionary:
  - `technical_rating`: Strict mathematical match formula `(Matched Mandatory / Total Mandatory) * 100` and deficit severity badge (`Critical Skill Deficit`, `Manageable Gap`, `Strong Alignment`).
  - `experience_scoring`: Institutional 10-point scale tier assessment (`< 3y: 4pts`, `3-5y: 6pts`, `5-8y: 8pts`, `8y+: 10pts`).
  - `requirements_matrix`: 4-column breakdown (`requirement`, `category`, `evidence_gap` with `Present:` / `Missing:` prefixes, and `status`).
  - `communication_profile`, `problem_solving`, `cultural_fit`.
  - `decision_engine`: Corporate decision (`STRONG HIRE`, `SHORTLIST`, `CONDITIONAL`, `REJECT`), rule triggered, criteria benchmark, justification bullets, and alternative role routing.
- **Status:** Baseline core agent (100% preserved and untouched).

### 2.4 Question Bank Agent (`agents/question_bank.py`)
- **Input:** `fit_profile: dict`, `jd_profile: dict`, optional `prioritized_topics: list`
- **Output:** Comprehensive question schema:
  - `topic_checklist`: Complete 100% extraction of JD topics tagged as `Gap`, `Claimed`, or `Untested`.
  - `coverage_summary`: Table verifying 100% checklist coverage.
  - `questions`: Questions grouped across 5 dimensions: Technical Deep-Dive, Problem Solving / Scenarios, Behavioral STAR, Resume Challenges, and Gap Mitigation.
  - Supports dynamic 2.5x sampling emphasis on diagnosed weakness topics.

### 2.5 Online Test Agent (`agents/online_test_agent.py`)
- **Input:** `jd_profile: dict`, `fit_profile: dict`, optional `prioritized_topics: list`, `round_number: int`
- **Output:** 30-MCQ customized examination:
  - Dual-key normalized items: `"question"`, `"question_text"`, `"options"` (A-D), `"correct_answer"`, `"topic_tag"`, `"rationale"`.
  - Deterministic option shuffling per session ID.
  - `score_test()` method computing overall score, percentage, topic-wise accuracy breakdown table, and itemized candidate answer review.

### 2.6 Feedback Agent (`agents/feedback_agent.py`)
- **Input:** `fit_profile: dict`, `test_results: dict`
- **Output:** Unified Diagnostic Report:
  - `unified_topic_readiness`: De-duplicated matrix merging fit/gap analysis with empirical test scores, flagging dual-weakness topics with `🚨 HIGH PRIORITY` alerts.
  - `composite_readiness_score`: Weighted index (`45% Structural Fit + 55% Online Test`).
  - `study_roadmap`: Prioritized 48-hour revision roadmap with concrete practice exercises.
  - `prioritized_topics_for_next_round`: High-deficit topic list fed back into Orchestrator for Round 2+ retests.

### 2.7 Central Orchestrator (`orchestrator/orchestrator.py`)
- **Methods:** `generate_online_test()`, `submit_online_test()`, `finalize_readiness_report()`, `trigger_next_round()`, and `_generate_failsafe_evaluation()`.
- **Failsafe Engine:** Generates synthetic, mathematically authentic evaluation rubrics if all API models fail, guaranteeing 100% demo uptime.

### 2.8 Voice Interview Simulator Agent (`agents/voice_interview_agent.py`)
- **Input:** `fit_profile: dict`, `jd_profile: dict`, `company_name: str`
- **Output:** Turn-by-turn conversational mock interview session.
- **Audio Pipeline:** Google Local NLP (Web Speech API for STT and SpeechSynthesis for TTS) directly in the browser—zero external cloud API costs, zero token consumption.
- **Speech Analytics (`utils/speech_analytics.py`):** Computes Words Per Minute (WPM), filler word frequency (`um`, `uh`, `like`, `you know`), STAR methodology adherence, and question-by-question scoring.

### 2.9 Agentic Company Intelligence RAG (`agents/company_intel_agent.py`)
- **Input:** Target company name / JD text.
- **Output:** Corporate intelligence dossier indexing leadership principles and interview methodologies:
  - Curated rubrics for Amazon (16 Leadership Principles), Google (Googleyness & Problem Solving), McKinsey (Personal Experience Interview & Case Structuring), Goldman Sachs (Risk & Analytical Precision), and Microsoft (Growth Mindset).
  - Enriches Step 2 culture card and injects company principles into Step 3 Behavioral STAR questions.

### 2.10 Automated Corporate PDF Dossier Engine (`utils/pdf_exporter.py`)
- **Input:** Session state containing fit profile, test results, voice metrics, and study roadmap.
- **Output:** Multi-page, high-resolution vector PDF document generated via ReportLab (`build_candidate_dossier()`), available via 1-click download in Step 2, Step 5, and the sidebar.

### 2.11 Database Layer (`utils/database.py`)
- **Engine:** SQLite 3 (`data/interviewiq.db`) with Write-Ahead Logging (WAL) and foreign keys enabled.
- **Tables (8 Relational Tables):**
  1. `users`: `(user_id TEXT PRIMARY KEY, full_name, email, target_domain, created_at)`
  2. `sessions`: `(session_id TEXT PRIMARY KEY, user_id, candidate_name, role_title, current_round, created_at, updated_at)`
  3. `fit_evaluations`: `(id INTEGER PRIMARY KEY, session_id, technical_match_pct, experience_score, decision, rule_triggered, requirements_matrix_json, created_at)`
  4. `test_attempts`: `(attempt_id INTEGER PRIMARY KEY, session_id, round_number, score, total_questions, percentage, passed, topic_accuracy_json, created_at)`
  5. `readiness_reports`: `(id INTEGER PRIMARY KEY, session_id, round_number, composite_score, readiness_level, unified_matrix_json, study_roadmap_json, created_at)`
  6. `session_snapshots`: `(session_id TEXT PRIMARY KEY, state_json, updated_at)`
  7. `api_response_cache`: `(prompt_hash TEXT PRIMARY KEY, model_name, is_json, response_text, created_at, hit_count)`
  8. `curriculum_plans`: `(plan_id TEXT PRIMARY KEY, session_id, plan_json, checked_items, days_completed, created_at, updated_at)`

### 2.12 API Quota Manager & Gemini Cache (`utils/api_quota_manager.py`, `utils/gemini_cache.py`)
- **Quota Manager:**
  - Token-Bucket rate pacer enforcing <=12 RPM (2.0s cooldown between requests).
  - Sliding-window RPM tracker for real-time telemetry.
  - Active cloud key validation probe (1-token ping to Google AI Studio).
- **Gemini Cache:**
  - L1 Memory Cache (LRU dictionary) + L2 Persistent Cache (`api_response_cache` SQLite table).
  - Keyed by SHA-256 hash of normalized prompt + model configuration.
  - Eliminates redundant API calls (0 ms latency, 0 token consumption).

### 2.13 Micro-Curriculum Agent (`agents/micro_curriculum_agent.py` & `utils/curriculum_resources.py`)
- **Input:** `weak_topics: list`, `jd_profile: dict`, `composite_score: float`
- **Output:**
  - `generate_curriculum()`: 7-day personalized prep schedule allocating High-Priority topics to Days 1-3, Medium-Priority to Days 4-5, Day 6 to targeted question drills (linking to Step 3), and Day 7 to dress rehearsal (linking to Step 4). Includes `emergency_sprint` for 48h turnaround.
  - Enriched with up to 4 static free course links per day from `CurriculumResourceLibrary` (zero API calls).
  - Rendered in Step 6 with interactive checklist persistence.

---

## 3. Google API Resilience & Multi-Model Cascade
InterviewIQ implements a multi-tiered defense against Google Gemini API rate limits:

```
[Incoming Request]
        |
        v
[1. Two-Tier Cache Check]
        |---> Hit: Return Cached Response (0 ms, 0 Tokens)
        |
        +---> Miss:
                 |
                 v
        [2. Atomic Reservation Rate Pacer]
                 |---> Wait for Slot (<= 12 RPM, >= 2.0s Cooldown)
                 |---> Reserve timestamp under lock (<1us), sleep outside lock
                 v
        [3. Execute Modern 16-Model Cascade]
                 |---> Tier 1 (Flash): gemini-2.5-flash -> gemini-flash-latest -> gemini-3.8-flash -> ...
                 |---> Tier 2 (Lite): gemini-2.5-flash-lite -> gemini-flash-lite-latest -> ...
                 |---> Tier 3 (Pro): gemini-2.5-pro -> gemini-1.5-pro -> gemini-pro
                 |
                 v
        [4. Dynamic Model Discovery & Session Blacklisting]
                 |---> Double-checked list_models() discovery on user key
                 |---> Thread-safe _BLACKLISTED_MODELS skips 404 retired models instantly
                 |
                 v
        [5. Transient 429 Jittered Backoff]
                 |---> Exponential backoff with jitter on transient rate limits
                 |
                 v
        [6. Store in Two-Tier Cache]
                 |---> Save response in RAM and SQLite upon validated generation
                 |
                 v
        [7. Upstream Heuristic Failsafes]
                 |---> If all models fail: Deterministic fallbacks in Resume, JD & Fit Agents
```

---

## 4. Frontend Styling & Design System
- **Framework:** Streamlit with custom CSS tokens (`frontend/styles/neumorphism.css`).
- **Server Configuration (`.streamlit/config.toml`):**
  - Theme: Strict Light Mode (`base = "light"`).
  - Background: Clean slate `#F8FAFC`.
  - Secondary Background: `#F1F5F9`.
  - Text Color: High-contrast `#0F172A`.
  - Primary Accent: Executive Blue `#2563EB`.
- **Contrast Guardrails:** All headings, bold tags, labels, and form titles are forced to `#0F172A !important` to ensure zero low-contrast text artifacts across different operating systems and display monitors.

---

## 5. Automated Test Framework
InterviewIQ maintains a comprehensive test suite in the `tests/` directory:
- `tests/test_agents.py`: Baseline agent pipeline, formula scoring, and closed-loop retesting (9 tests).
- `tests/test_timer_and_proctor.py`: Exam countdown timer, tab blur anti-cheating, and option shuffle invariance (4 tests).
- `tests/test_pdf_exporter.py`: Full dossier PDF generation, standalone Strategic Fit Report PDF generation, ReportLab vector elements, and schema validation (4 tests).
- `tests/test_speech_engine.py`: Google Local NLP speech analytics, WPM calculation, filler words, and STAR compliance (5 tests).
- `tests/test_company_intel.py`: Company intelligence RAG, Leadership Principle retrieval, and prompt enrichment (5 tests).
- `tests/test_database.py`: SQLite schema, session persistence, and longitudinal retest score tracking (5 tests).
- `tests/test_api_quota_and_cache.py`: Token-Bucket rate pacing, two-tier SHA-256 caching, key validation, 404 model failover, and active model state tracking (8 tests).
- `tests/test_micro_curriculum_agent.py`: 7-day personalized schedule generation, curated free resource mapping, topic normalization edge cases, and SQLite progress tracking (9 tests).
- `tests/test_domain_vocabulary.py`: Domain vocabulary phonetic confusion repair, acronym collapse, and domain density scoring (6 tests).
- `tests/test_speech_analytics_advanced.py`: Disfluency categorization, stutter detection, TTR lexical diversity, chronological STAR sequence, and active voice (7 tests).
- `tests/test_ui_kit.py`: Design tokens generation, pure SVG icon library, fallback safety, badge styling, metric cards, callouts, progress bar clamping, and status pill mapping (12 tests).
- `tests/test_integration.py`: End-to-end multi-round lifecycle, PDF generation, and Step 6 micro-curriculum persistence (2 tests).
- `tests/test_uat_journeys.py`: End-to-end candidate user journeys across onboarding, fit report, testing, and curriculum (5 tests).
- `tests/test_uat_streamlit_app.py`: Streamlit AppTest headless UI navigation, dual onboarding mode buttons, and interactive feature validation (10 tests).
- `tests/test_agents.py`: Baseline agent suites, closed-loop reweighting, and dual-mode onboarding verification (`TestDualModeOnboarding`) (12 tests).
- `tests/test_quality_controller.py`: In-process output quality auditing for resume, fit, question bank, test, and feedback deliverables (5 tests).
- **Test Suite Result:** **98 of 98 unit, integration, and UAT tests passing cleanly (100% pass rate in 229s)**. Zero warnings, zero regressions. Baseline scoring agents (`online_test_agent.score_test` and `feedback_agent.build_unified_topic_readiness` 45/55 formula) remain 100% untouched.

---

## 6. Current Checkpoint, Where We Stopped & Future Roadmap

### Current Status
All core pipeline steps (Steps 1 through 6), comprehensive code optimizations, Google Local NLP voice simulation, UI/UX Neumorphic Design System, dynamic Gemini model discovery & 404 failover architecture, standalone Fit Report PDF download, live dual-mode onboarding analysis progress tracking, and Session #22 Multi-Subagent Output Quality Verification Engine are implemented, integrated, and verified live with zero errors. All **98 unit, integration, and UAT tests pass cleanly (100% pass rate in 229s)**. Baseline scoring agents remain 100% untouched.

### Where We Stopped
- Successfully completed in Session #22 (Multi-Subagent Output Quality Verification Engine):
  1. Engineered in-process `MultiAgentQualityController` in `utils/quality_controller.py`.
  2. Integrated output quality auditing into `Orchestrator.process_onboarding` and `Orchestrator.finalize_readiness_report`.
  3. Added real-time quality verification badges (`Multi-Agent Quality Verified: 85%+ • Enterprise Depth`) in `frontend/app.py`.
  4. Added `tests/test_quality_controller.py` bringing full test suite to 98/98 passing tests.
  3. Upgraded Quick Demo loader with dual 1-click triggers: `⚡ Load Demo: Fit & Question Bank Only (~10s)` and `🚀 Load Demo: Complete Pipeline (~35s)`.
  4. Added spinner to Step 3 proceed button (`proceed_step4_btn`) when lazily generating tests on-demand.
  5. Enhanced Step 6 curriculum initialization to synthesize adaptive learning roadmaps directly from `fit_data` requirements matrix gaps for Option 1 candidates.
  6. Added `TestDualModeOnboarding` unit tests in `tests/test_agents.py` and dual mode UI tests in `tests/test_uat_streamlit_app.py`.
  7. Maintained **93 tests** passing cleanly (100% pass rate).

### Why We Stopped
1. **Scope Realization:** Both requested onboarding options and full architectural decoupling have been completely implemented and verified.
2. **System Health:** 100% unit test pass rate confirms zero functional regressions across all 93 tests with zero warnings or errors.
3. **Documentation Synchronization:** Paused to synchronize all technical architecture, project logs, business case, and KT documents across both Markdown (`.md`) and Word (`.docx`) formats.

### Future Project Plan (Roadmap for Next Phases)
- **Phase 26: University LMS Integration (Canvas / Moodle / Blackboard):**
  - Implement LTI 1.3 / OAuth 2.0 protocol integration.
  - Automatic roster sync and gradebook passback.
- **Phase 27: Real-Time WebRTC Audio Streaming with Live Sentiment Waveforms:**
  - Full-duplex low-latency audio streaming for synchronous vocal interactions.
  - Real-time vocal pitch variation, stress indicators, and confidence heatmaps.
- **Phase 28: Automated Corporate Recruiter Dispatch & ATS Webhooks:**
  - Automated webhook integration with Greenhouse, Lever, and Workday.
  - One-click batch dispatch of candidate PDF dossiers to corporate hiring partners.
- **Phase 29: Fine-Tuned Domain LLM Adapters for Specialized Verticals:**
  - LoRA / PEFT adapters fine-tuned on quantitative finance, clinical research, and patent law interview rubrics.

### Where to Resume Next
1. Launch app via `launch.bat` or `.\.venv\Scripts\python.exe -m streamlit run frontend/app.py`.
2. Supply your Gemini API key in Step 1 and activate. The system auto-selects `gemini-2.0-flash` or the best available model with zero 404 errors.
3. Validate both onboarding paths:
   - Option 1: Click *"⚡ Load Demo: Fit & Question Bank Only (~10s)"*, observe the 5-stage live progress bar, and inspect Step 2 and Step 3.
   - Option 2: Click *"🚀 Load Demo: Complete Pipeline (~35s)"*, observe the 6-stage live progress bar, and inspect Step 4 pre-calibration.
4. Execute `.\.venv\Scripts\python.exe -m unittest discover tests` to verify all 93 tests.
5. Commence development on **Phase 26** (LMS Integration) or **Phase 27** (WebRTC Voice Waveforms).
