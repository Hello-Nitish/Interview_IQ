"""
InterviewIQ Python DirectML Sidecar Microservice.
High-performance local HTTP server exposing agentic evaluation pipelines,
DirectML hardware acceleration, and SQLite persistence to the Wails Go runtime.
"""

import argparse
import base64
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Standard logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("InterviewIQ.Sidecar")

# Starlette / FastAPI imports
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

# Import DirectML modules
from sidecar.directml.engine import get_directml_engine
from sidecar.directml.embeddings import get_embeddings_engine
from sidecar.directml.whisper_stt import get_speech_engine

# Import Agents & Orchestration
from orchestrator.orchestrator import Orchestrator
from agents.resume_reviewer import ResumeReviewerAgent
from agents.jd_analyzer import JDAnalyzerAgent
from agents.fit_analyzer import FitAnalyzerAgent
from agents.question_bank import QuestionBankAgent
from agents.online_test_agent import OnlineTestAgent
from agents.feedback_agent import FeedbackAgent
from agents.micro_curriculum_agent import MicroCurriculumAgent
from agents.company_intel_agent import CompanyIntelAgent

# Import Utilities
from utils.api_quota_manager import APIQuotaManager
from utils.database import DatabaseManager
from utils.pdf_exporter import PDFDossierExporter

# Global token storage
EXPECTED_BEARER_TOKEN: Optional[str] = None
GLOBAL_ORCHESTRATOR = Orchestrator()


def verify_bearer_auth(request: Request) -> Optional[JSONResponse]:
    """Validates authorization bearer header against runtime token."""
    global EXPECTED_BEARER_TOKEN
    if not EXPECTED_BEARER_TOKEN:
        return None  # Dev mode without token restriction

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse({"error": "Unauthorized: Missing Bearer Token"}, status_code=401)

    token = auth_header[7:].strip()
    if token != EXPECTED_BEARER_TOKEN:
        return JSONResponse({"error": "Forbidden: Invalid Bearer Token"}, status_code=403)

    return None


# ----------------------------------------------------------------------
# Route Handlers
# ----------------------------------------------------------------------

async def health_check(request: Request) -> JSONResponse:
    """Public health probe for Go process manager."""
    dml_info = get_directml_engine().get_device_info()
    return JSONResponse({
        "status": "ok",
        "service": "InterviewIQ DirectML Sidecar",
        "version": "1.0.0",
        "directml": dml_info,
        "database_connected": True,
    })


async def validate_api_key(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    body = await request.json()
    key = str(body.get("api_key", "")).strip()
    if not key:
        return JSONResponse({"valid": False, "message": "API key cannot be empty"}, status_code=400)

    is_valid, msg = APIQuotaManager.validate_api_key(key)
    if is_valid:
        GLOBAL_ORCHESTRATOR.set_api_key(key)
        active_model = APIQuotaManager.get_active_model()
        return JSONResponse({"valid": True, "message": msg, "active_model": active_model})
    return JSONResponse({"valid": False, "message": msg}, status_code=400)


async def get_telemetry(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    stats = APIQuotaManager.get_telemetry_stats()
    dml_info = get_directml_engine().get_device_info()
    stats["directml"] = dml_info
    return JSONResponse(stats)


async def run_onboarding(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    body = await request.json()
    resume_text = body.get("resume_text", "")
    jd_text = body.get("jd_text", "")

    if not resume_text or not jd_text:
        return JSONResponse({"error": "resume_text and jd_text are required"}, status_code=400)

    api_key = body.get("api_key")
    if api_key:
        GLOBAL_ORCHESTRATOR.set_api_key(api_key)

    GLOBAL_ORCHESTRATOR.ingest_data(resume_text, jd_text)
    profile = GLOBAL_ORCHESTRATOR.run_resume_review()
    jd_analysis = GLOBAL_ORCHESTRATOR.run_jd_analysis()

    # Company Intel analysis if present
    company_name = jd_analysis.get("company_name", "")
    culture_fit = {}
    if company_name:
        company_agent = CompanyIntelAgent(api_key=GLOBAL_ORCHESTRATOR.api_key)
        culture_fit = company_agent.analyze_culture_fit(company_name, profile.get("summary", ""))

    return JSONResponse({
        "status": "success",
        "profile": profile,
        "jd_analysis": jd_analysis,
        "culture_fit": culture_fit,
        "session_id": GLOBAL_ORCHESTRATOR.session_id,
    })


async def run_fit_analysis(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    body = await request.json()
    profile = body.get("profile") or GLOBAL_ORCHESTRATOR.state.get("profile")
    jd_analysis = body.get("jd_analysis") or GLOBAL_ORCHESTRATOR.state.get("jd_analysis")

    if not profile or not jd_analysis:
        return JSONResponse({"error": "profile and jd_analysis are required"}, status_code=400)

    GLOBAL_ORCHESTRATOR.state["profile"] = profile
    GLOBAL_ORCHESTRATOR.state["jd_analysis"] = jd_analysis

    fit_report = GLOBAL_ORCHESTRATOR.run_fit_analysis()
    return JSONResponse({"status": "success", "fit_report": fit_report})


async def run_question_bank(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    body = await request.json()
    jd_analysis = body.get("jd_analysis") or GLOBAL_ORCHESTRATOR.state.get("jd_analysis")
    profile = body.get("profile") or GLOBAL_ORCHESTRATOR.state.get("profile")
    fit_report = body.get("fit_report") or GLOBAL_ORCHESTRATOR.state.get("fit_report")

    if not jd_analysis:
        return JSONResponse({"error": "jd_analysis is required"}, status_code=400)

    GLOBAL_ORCHESTRATOR.state["jd_analysis"] = jd_analysis
    if profile:
        GLOBAL_ORCHESTRATOR.state["profile"] = profile
    if fit_report:
        GLOBAL_ORCHESTRATOR.state["fit_report"] = fit_report

    qb = GLOBAL_ORCHESTRATOR.generate_question_bank()
    return JSONResponse({"status": "success", "question_bank": qb})


async def run_online_test(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    body = await request.json()
    qb = body.get("question_bank") or GLOBAL_ORCHESTRATOR.state.get("question_bank")
    jd_analysis = body.get("jd_analysis") or GLOBAL_ORCHESTRATOR.state.get("jd_analysis")

    if not qb or not jd_analysis:
        return JSONResponse({"error": "question_bank and jd_analysis are required"}, status_code=400)

    agent = OnlineTestAgent(api_key=GLOBAL_ORCHESTRATOR.api_key)
    test_suite = agent.generate_test(
        checklist=qb.get("topic_checklist", []),
        jd_title=jd_analysis.get("role_title", "Candidate"),
        num_questions=30,
    )
    GLOBAL_ORCHESTRATOR.state["online_test"] = test_suite
    return JSONResponse({"status": "success", "online_test": test_suite})


async def score_online_test(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    body = await request.json()
    test_questions = body.get("test_questions")
    if not test_questions and "online_test" in GLOBAL_ORCHESTRATOR.state:
        test_questions = GLOBAL_ORCHESTRATOR.state["online_test"].get("questions", [])

    user_answers = body.get("user_answers", {})
    if not test_questions:
        return JSONResponse({"error": "test_questions required"}, status_code=400)

    agent = OnlineTestAgent(api_key=GLOBAL_ORCHESTRATOR.api_key)
    test_results = agent.score_test(test_questions, user_answers)
    GLOBAL_ORCHESTRATOR.state["test_results"] = test_results
    return JSONResponse({"status": "success", "test_results": test_results})


async def run_feedback(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    body = await request.json()
    fit_report = body.get("fit_report") or GLOBAL_ORCHESTRATOR.state.get("fit_report")
    test_results = body.get("test_results") or GLOBAL_ORCHESTRATOR.state.get("test_results")
    name = body.get("candidate_name") or GLOBAL_ORCHESTRATOR.state.get("profile", {}).get("name", "Candidate")

    if not fit_report:
        return JSONResponse({"error": "fit_report is required"}, status_code=400)

    feedback = GLOBAL_ORCHESTRATOR.run_feedback(candidate_name=name)
    return JSONResponse({"status": "success", "feedback": feedback})


async def run_curriculum(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    body = await request.json()
    feedback = body.get("feedback") or GLOBAL_ORCHESTRATOR.state.get("feedback")
    jd_analysis = body.get("jd_analysis") or GLOBAL_ORCHESTRATOR.state.get("jd_analysis")

    if not feedback or not jd_analysis:
        return JSONResponse({"error": "feedback and jd_analysis are required"}, status_code=400)

    curriculum = GLOBAL_ORCHESTRATOR.generate_micro_curriculum()
    return JSONResponse({"status": "success", "curriculum": curriculum})


async def toggle_curriculum_task(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    body = await request.json()
    sess_id = body.get("session_id") or GLOBAL_ORCHESTRATOR.session_id
    day_num = int(body.get("day_number", 1))
    task_id = str(body.get("task_id", ""))
    completed = bool(body.get("completed", False))

    DatabaseManager.update_curriculum_progress(sess_id, day_num, task_id, completed)
    return JSONResponse({"status": "success", "completed": completed})


async def transcribe_voice(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    body = await request.json()
    audio_b64 = body.get("audio_base64", "")
    if not audio_b64:
        return JSONResponse({"error": "audio_base64 is required"}, status_code=400)

    speech_eng = get_speech_engine()
    res = speech_eng.transcribe_base64(audio_b64)
    return JSONResponse(res)


async def semantic_similarity(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    body = await request.json()
    query = body.get("query", "")
    candidates = body.get("candidates", [])

    embed_eng = get_embeddings_engine()
    ranked = embed_eng.rank_matches(query, candidates)
    return JSONResponse({"status": "success", "matches": ranked})


async def export_pdf(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    body = await request.json()
    doc_type = body.get("type", "fit_report")

    if doc_type == "fit_report":
        fit_report = body.get("fit_report") or GLOBAL_ORCHESTRATOR.state.get("fit_report", {})
        pdf_bytes = PDFDossierExporter.generate_fit_report_pdf(
            fit_data=fit_report,
            candidate_name=body.get("candidate_name", "Candidate"),
            role_title=body.get("role_title", "Target Role"),
        )
    else:
        pdf_bytes = PDFDossierExporter.generate_dossier_pdf(GLOBAL_ORCHESTRATOR.state)

    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    return JSONResponse({
        "status": "success",
        "filename": f"InterviewIQ_{doc_type}.pdf",
        "pdf_base64": b64_pdf,
        "byte_size": len(pdf_bytes),
    })


async def list_sessions(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    sessions = DatabaseManager.list_sessions()
    return JSONResponse({"sessions": sessions})


async def load_session(request: Request) -> JSONResponse:
    auth_err = verify_bearer_auth(request)
    if auth_err:
        return auth_err

    sess_id = request.path_params.get("session_id", "")
    state = DatabaseManager.load_session_state(sess_id)
    if state:
        GLOBAL_ORCHESTRATOR.session_id = sess_id
        GLOBAL_ORCHESTRATOR.state = state
        return JSONResponse({"status": "success", "state": state})
    return JSONResponse({"error": "Session not found"}, status_code=404)


# ----------------------------------------------------------------------
# Application Factory
# ----------------------------------------------------------------------

routes = [
    Route("/health", health_check, methods=["GET"]),
    Route("/api/auth/validate-key", validate_api_key, methods=["POST"]),
    Route("/api/telemetry", get_telemetry, methods=["GET"]),
    Route("/api/pipeline/onboard", run_onboarding, methods=["POST"]),
    Route("/api/pipeline/fit-analysis", run_fit_analysis, methods=["POST"]),
    Route("/api/pipeline/question-bank", run_question_bank, methods=["POST"]),
    Route("/api/pipeline/online-test", run_online_test, methods=["POST"]),
    Route("/api/pipeline/score-test", score_online_test, methods=["POST"]),
    Route("/api/pipeline/feedback", run_feedback, methods=["POST"]),
    Route("/api/pipeline/curriculum", run_curriculum, methods=["POST"]),
    Route("/api/curriculum/toggle-task", toggle_curriculum_task, methods=["POST"]),
    Route("/api/voice/transcribe", transcribe_voice, methods=["POST"]),
    Route("/api/semantic/similarity", semantic_similarity, methods=["POST"]),
    Route("/api/export/pdf", export_pdf, methods=["POST"]),
    Route("/api/sessions", list_sessions, methods=["GET"]),
    Route("/api/sessions/{session_id}", load_session, methods=["GET"]),
]

dist_path = os.path.join(project_root, "frontend", "dist")
if os.path.exists(dist_path):
    routes.append(Mount("/", app=StaticFiles(directory=dist_path, html=True)))

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(debug=False, routes=routes, middleware=middleware)


def run_server(host: str = "127.0.0.1", port: int = 8000, token: Optional[str] = None) -> None:
    """Launches the Uvicorn ASGI server."""
    global EXPECTED_BEARER_TOKEN
    EXPECTED_BEARER_TOKEN = token
    logger.info("Starting InterviewIQ Sidecar on %s:%d (Token Auth: %s)", host, port, bool(token))

    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="InterviewIQ DirectML Sidecar")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--token", default=None, help="Cryptographic bearer token")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port, token=args.token)
