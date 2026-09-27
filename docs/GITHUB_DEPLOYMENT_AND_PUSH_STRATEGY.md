# GitHub Deployment and Push Strategy Guide
**Project:** InterviewIQ — Multi-Agent Digital Transformation Placement Intelligence Platform  
**Target Repository:** `https://github.com/Hello-Nitish/Interview_IQ.git`  
**Target Hosting:** Streamlit Community Cloud (`https://interview-iq.streamlit.app`) / Docker / Hugging Face Spaces  
**Authors:** Nitish & Jeevana (Engineering Pair Programming with Antigravity AI)  
**Classification:** Enterprise Engineering Architecture & Knowledge Transfer (KT) Manual  
**Last Updated:** 2026-09-28  

---

## Executive Summary

This document serves as the authoritative, definitive guide detailing how the engineering team planned, diagnosed, sanitized, and successfully executed pushing the entire **InterviewIQ** codebase to GitHub and deploying it to **Streamlit Community Cloud**.

During the transition from local development to cloud production, several critical hurdles were encountered and systematically overcome:
1. **GitHub Push Protection Blocks:** Remote rejection triggered by historical API key strings in documentation commit history.
2. **Git DAG Commit Remediation:** Purging secret references from git commit objects without losing uncommitted progress.
3. **GitHub Actions CI Pipeline Failures:** Broken bytecode compilation on deleted pruned modules and environment variable pollution breaking Streamlit UI state assertions.
4. **Streamlit Community Cloud Entrypoint Resolution:** Native discovery requirements (`streamlit_app.py`) and DNS subdomain RFC compliance.
5. **Production Security Hardening:** Ephemeral session-only key lifecycle, complete `.dockerignore` sanitization, and non-root Linux container execution.

This guide provides end-to-end documentation of every diagnosis, plan, and execution step, serving as an indelible Knowledge Transfer (KT) artifact for future AI agents and human developers.

---

## 1. Challenge 1: GitHub Push Protection & Secret Remediation

### 1.1 The Incident & Root Cause Analysis
Upon attempting to push commits to the remote GitHub repository (`git push origin main`), the GitHub remote server rejected the push with the following security policy violation:

```text
remote: - GITHUB PUSH PROTECTION
remote: —————————————————————————————————————————
remote: Resolve the following violations before pushing again
remote:
remote: - Push cannot contain secrets
remote:
remote: —— GCP API Key Bound to a Service Account ————————————
remote: locations:
remote:   - commit: 169fb47b534f6baf9d128e3aba25a934a0e289df
remote:     path: docs/PROJECT_LOG.md:35
remote:
remote: (?) To push, remove secret from commit(s) or follow this URL to allow the secret.
remote: https://github.com/Hello-Nitish/Interview_IQ/security/secret-scanning/unblock-secret/...
```

#### Why Standard Fixes Failed
1. **Editing the file locally and making a new commit:**  
   Git is a Directed Acyclic Graph (DAG) of immutable snapshots. A subsequent commit (`git commit -m "Remove secret"`) merely creates a child commit where the file is edited; the parent commit (`169fb47b...`) still exists in the local git repository history and packfiles. When pushing, Git sends the entire unpushed commit chain. GitHub's Secret Scanner inspects **every commit in the push bundle**, detecting the secret in the parent commit and blocking the push again.
2. **Using `git revert`:**  
   `git revert` creates an inverse patch commit on top of HEAD. It does NOT rewrite history or delete the parent commit object containing the secret.

### 1.2 Multi-Agent Planning & Strategy
To eliminate the secret from git history while guaranteeing zero data loss, the team planned a 4-phase soft-reset strategy:

```
[Local Git History with Secret]
9503e49 (Initial Commit - Clean)
  └── 169fb47 (Commit containing secret in PROJECT_LOG.md:35)
        └── ... (Multiple subsequent commits)
              └── HEAD (Current working state)

                       │
                       │ git reset --soft 9503e49
                       ▼

[Detached Working Tree (Staged)]
Working directory and index preserved intact.
Commits 169fb47... deleted from DAG.

                       │
                       │ Redact lines 35, 127, 235 in PROJECT_LOG.md
                       │ Scan entire tree with regex for GCP/Gemini keys
                       ▼

[Clean Pristine Commit Created]
9503e49 (Initial Commit)
  └── 8f5cf89 (Pristine Single Clean Commit - Zero Secrets)
                       │
                       │ git push origin main
                       ▼
[Remote Push: SUCCESSFUL]
```

### 1.3 Step-by-Step Execution Record

#### Step 1: Soft-Reset History to Initial Clean Anchor
```powershell
git reset --soft 9503e49
```
*Rationale:* `9503e49` was the known-clean initial commit before any sensitive strings were documented. A `--soft` reset moves the `HEAD` pointer back to `9503e49` while preserving all modified files, added files, and working tree changes in the staging index.

#### Step 2: Redact Historical Keys in Documentation
All sample keys and historical logs in `docs/PROJECT_LOG.md` were scrubbed:
- Line 35: Redacted raw GCP key to `<REDACTED_API_KEY>`
- Line 127: Redacted key reference
- Line 235: Redacted key reference

#### Step 3: Automated Repository-Wide Secret Scan
Before creating the new commit, a full ripgrep / regex scan was executed across all tracked files:
```powershell
# Ripgrep scan for typical Gemini/GCP API key patterns: AIzaSy...
rg -i "AIzaSy[0-9A-Za-z-_]{33}" .
```
Result: **Zero occurrences found across all 114 tracked files**.

#### Step 4: Pristine Commit & Push
```powershell
git commit -m "feat: complete multi-agent interview preparation platform with zero-leak architecture"
git push origin main
```
Result: **Push accepted by GitHub with zero push protection triggers**.

---

## 2. Challenge 2: GitHub Actions CI/CD Pipeline Resolution

### 2.1 The Incident
Immediately after pushing commit `8f5cf89`, the GitHub Actions automated CI workflow failed with red ❌ status badges across both Python 3.10 and Python 3.11 runners:

```text
======================================================================
FAIL: test_uat_page_01_onboarding_initial_render (test_uat_streamlit_app.TestRigorousUATStreamlitApp)
Validates Step 1 Onboarding page initial render and sidebar widgets.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/Interview_IQ/Interview_IQ/tests/test_uat_streamlit_app.py", line 36, in test_uat_page_01_onboarding_initial_render
    self.assertTrue(any("Validate & Activate Key" in lbl for lbl in button_labels))
AssertionError: False is not true
```

And in prior iterations:
```text
py_compile: can't open file 'agents/case_study_agent.py': [Errno 2] No such file or directory
py_compile: can't open file 'agents/compensation_negotiator.py': [Errno 2] No such file or directory
py_compile: can't open file 'agents/cohort_analyzer.py': [Errno 2] No such file or directory
Error: Process completed with exit code 1.
```

### 2.2 Root Cause Diagnosis

#### Root Cause 1: Static `py_compile` on Deleted Modules
In Session #16, the engineering team pruned the platform scope from 9 steps down to 6 streamlined steps, permanently deleting:
- `agents/case_study_agent.py`
- `agents/compensation_negotiator.py`
- `agents/cohort_analyzer.py`

However, `.github/workflows/ci.yml` contained static commands:
```yaml
- name: Bytecode compilation check
  run: |
    python -m py_compile agents/case_study_agent.py
    python -m py_compile agents/compensation_negotiator.py
    python -m py_compile agents/cohort_analyzer.py
```
Because the files were deleted, the Python compiler failed with `Errno 2 (No such file or directory)`.

#### Root Cause 2: CI Runner Environment Key Leaks Breaking Streamlit Gatekeeper
In `.github/workflows/ci.yml`, the environment block had:
```yaml
env:
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY || 'MOCK_KEY_FOR_CI_PIPELINE' }}
```
When `frontend/app.py` starts, its initialization routine checks:
```python
if os.getenv("GEMINI_API_KEY") and not st.session_state.get("api_key_valid"):
    # Automatically validates key and unlocks full platform
    st.session_state["api_key_valid"] = True
```
When `TestRigorousUATStreamlitApp.test_uat_page_01_onboarding_initial_render` mounted `frontend/app.py` headlessly, `frontend/app.py` detected the environment key and **auto-authenticated**, immediately rendering the onboarding forms and hiding the Gatekeeper card containing the `"Validate & Activate Key"` button. The test asserted that the Gatekeeper button was present, resulting in `AssertionError: False is not true`.

### 2.3 Planning & Remediation

#### Fix A: Dynamic Recursive Bytecode Compilation
Replaced static individual file checks with Python's standard `compileall` utility:
```yaml
- name: Bytecode compilation check
  run: |
    python -m compileall -q agents/ frontend/ orchestrator/ utils/ tests/ app.py streamlit_app.py
```
`compileall` traverses all project packages recursively, validating syntax without breaking if individual files are added, renamed, or pruned in future sprints.

#### Fix B: Decouple CI Environment & Make UAT Test Environment-Agnostic
1. **Removed `GEMINI_API_KEY` from `.github/workflows/ci.yml`**: CI runners start in a pure, unauthenticated state matching a first-time user.
2. **Refactored `test_uat_page_01_onboarding_initial_render` in `tests/test_uat_streamlit_app.py`**:
   The test now deterministically asserts either:
   - If unauthenticated: The Gatekeeper card with `"Validate & Activate Key"` is rendered.
   - If pre-authenticated via environment: The onboarding upload elements are rendered.
   This guarantees that whether tests are executed locally, in Docker, or on GitHub Actions, tests pass with 100% reliability.

### 2.4 CI Verification
Commit `a4cbe46` pushed to GitHub `origin/main`.  
GitHub Actions execution result:
- **Build and test Python 3.10:** ✅ GREEN (101/101 tests passed in 23s)
- **Build and test Python 3.11:** ✅ GREEN (101/101 tests passed in 21s)

---

## 3. Challenge 3: Streamlit Community Cloud Hosting Deployment

### 3.1 The Incident
When connecting GitHub repository `Hello-Nitish/Interview_IQ` to [Streamlit Community Cloud](https://share.streamlit.io), two deployment errors occurred:

1. **Missing Main File Path Error:**
   ```text
   Main file path: streamlit_app.py — This file does not exist
   ```
2. **Subdomain Naming Validation Error:**
   ```text
   A subdomain can only contain a-z, 0-9, and - characters
   ```

### 3.2 Root Cause & Engineering Solutions

#### Solution 1: Root Entrypoint Proxy (`streamlit_app.py`)
Streamlit Community Cloud defaults to looking for a root-level file named `streamlit_app.py` or `app.py`. In InterviewIQ, the main application file is located at `frontend/app.py`.

To support Streamlit Cloud's default repository search path without reorganizing the clean multi-tier directory structure, a proxy entrypoint was engineered at the root:

**File:** `streamlit_app.py`
```python
"""
streamlit_app.py
Root entrypoint for Streamlit Community Cloud deployment.
Delegates execution to frontend/app.py while ensuring root directory is on sys.path.
"""
import os
import sys
import runpy

# Ensure repository root is on sys.path so agents, utils, orchestrator can be imported
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Execute main application frontend
frontend_app = os.path.join(root_dir, "frontend", "app.py")
runpy.run_path(frontend_app, run_name="__main__")
```

**Benefits of this architecture:**
- Zero changes needed to `frontend/app.py` imports or assets.
- Users deploying via Streamlit Community Cloud can leave the default `streamlit_app.py` in the deployment modal.
- Local developers can run either `streamlit run streamlit_app.py` or `streamlit run frontend/app.py` interchangeably.

#### Solution 2: RFC 1035 / RFC 1123 Subdomain Compliance
- In domain name systems (DNS) governed by RFC 1035 and RFC 1123, subdomains **cannot contain underscore characters (`_`)**.
- The repository name `Interview_IQ` contains an underscore. Entering `interview_iq` into Streamlit Cloud's URL field triggered the regex validation failure.
- **Resolution:** Configure the custom subdomain with hyphens or alphanumeric characters:
  - Recommended URL: `https://interview-iq.streamlit.app`
  - Alternative URL: `https://interviewiq.streamlit.app`

---

## 4. Challenge 4: Security Hardening & Zero-Leak Architecture

### 4.1 Ephemeral Session-Only Key Management
To ensure candidate data and API credentials cannot be exposed when hosting publicly:
1. **Removed Local `.env` Writeback:** The *"Remember key in local .env"* checkbox and `write_env_key()` function were eradicated from `frontend/app.py`.
2. **Session Memory Storage Only:** Keys entered in the Gatekeeper are stored exclusively in Streamlit's in-memory `st.session_state["gemini_api_key"]`. When the browser tab is closed or the user session ends, the key is immediately purged from RAM.
3. **No Key Echoing:** API keys are rendered in password masking mode (`type="password"`) and never logged to stdout, logs, or telemetry files.

### 4.2 Docker Container Hardening
The container setup was fortified to prevent accidental inclusion of secrets or candidate data:
1. **Overhauled `.dockerignore`:**
   ```gitignore
   .env
   .env.*
   data/interviewiq.db*
   data/sessions/*.json
   !data/sessions/.gitkeep
   *.log
   __pycache__/
   .git/
   ```
2. **Hardened `Dockerfile`:**
   - Non-root user `appuser` (UID 1000) created and assigned ownership of `/app`.
   - Pre-installed `ffmpeg` for multimodal audio processing.
   - Pinned Python 3.11-slim base image for minimal attack surface.

### 4.3 Developer & Partner Attribution
As requested, an institutional attribution card was added to all views and sidebars in `frontend/app.py` and `frontend/components/ui_kit.py`:
```html
<div class="developer-card">
  Developed by your frd Nitish and Jeevana
</div>
```

---

## 5. Architectural Verification & Quality Gates

The deployment pipeline is guarded by 4 automated quality gates:

```
┌─────────────────────────────────────────────────────────────┐
│                   DEPLOYMENT QUALITY GATES                   │
├─────────────────┬───────────────────────────────────────────┤
│ Gate 1: Compile │ python -m compileall (0 syntax errors)   │
├─────────────────┼───────────────────────────────────────────┤
│ Gate 2: Secrets │ Regex scan for AIzaSy... (0 secrets)      │
├─────────────────┼───────────────────────────────────────────┤
│ Gate 3: Tests   │ 101/101 automated tests pass (100% pass)  │
├─────────────────┼───────────────────────────────────────────┤
│ Gate 4: UAT     │ Headless Streamlit AppTest simulation     │
└─────────────────┴───────────────────────────────────────────┘
```

### 5.1 Test Execution Matrix
```text
Ran 101 tests in 22.518s

OK
- test_agents.py: 16 tests PASSED
- test_api_quota_and_cache.py: 11 tests PASSED
- test_curriculum_agent.py: 6 tests PASSED
- test_database.py: 8 tests PASSED
- test_integration.py: 4 tests PASSED
- test_pdf_exporter.py: 4 tests PASSED
- test_quality_controller.py: 8 tests PASSED
- test_speech_analytics_advanced.py: 7 tests PASSED
- test_uat_journeys.py: 8 tests PASSED
- test_uat_streamlit_app.py: 10 tests PASSED
- test_ui_kit.py: 19 tests PASSED
```

### 5.2 Academic Scoring Integrity Guarantee
The core academic scoring algorithms remain **100% untouched**:
- `OnlineTestAgent.score_test` (Deterministic topic MCQ evaluation)
- `FeedbackAgent.build_unified_topic_readiness` (45% strategic fit / 55% online test composite formula)

---

## 6. Runbook: How to Push & Deploy in the Future

Follow this exact procedure whenever updating code and deploying to GitHub or Streamlit Cloud:

### 6.1 Pre-Flight Check (Run Locally)
```powershell
# 1. Activate Virtual Environment
.\.venv\Scripts\Activate.ps1

# 2. Verify Syntax Compilation
python -m compileall -q agents/ frontend/ orchestrator/ utils/ tests/ app.py streamlit_app.py

# 3. Run Complete Automated Test Suite
python -m unittest discover -s tests -p "test_*.py"

# 4. Verify Zero Secrets in Staging
git status
# Confirm no .env or sensitive files are staged
```

### 6.2 Staging, Committing, and Pushing
```powershell
# 5. Stage modified files
git add agents/ frontend/ orchestrator/ utils/ tests/ docs/ scripts/ streamlit_app.py .github/

# 6. Commit with semantic convention
git commit -m "feat/fix: descriptive summary of changes"

# 7. Push to Remote
git push origin main
```

### 6.3 Verifying Streamlit Community Cloud
1. Open [share.streamlit.io](https://share.streamlit.io).
2. Select your app: `Interview_IQ`.
3. Verify the deployment status displays **"Active"**.
4. Check the "Manage app" logs in the bottom right corner of the Streamlit Cloud dashboard to confirm clean boot without warnings.

---

## 7. Summary of Artifacts Created in this Deployment

| File Path | Purpose |
|:---|:---|
| `streamlit_app.py` | Root proxy entrypoint for Streamlit Community Cloud deployment |
| `.github/workflows/ci.yml` | Hardened GitHub Actions CI with recursive compilation and clean environment |
| `tests/test_uat_streamlit_app.py` | Environment-agnostic headless UI simulation tests |
| `Dockerfile` & `.dockerignore` | Secure, non-root container deployment configuration |
| `docs/GITHUB_DEPLOYMENT_AND_PUSH_STRATEGY.md` | This architectural deployment manual |
| `docs/GITHUB_DEPLOYMENT_AND_PUSH_STRATEGY.docx` | Executive Word version with professional formatting |
| `docs/PROJECT_LOG.md` & `.docx` | Complete audit history including Sessions #24–#27 |
| `docs/PROJECT_STATUS.md` & `.docx` | Real-time platform readiness and milestone tracker |
| `docs/KT_DOCUMENT.md` & `.docx` | Master Knowledge Transfer handbook for developers and AI agents |
