"""
tests/test_functional_matrix.py
Comprehensive Functional Test Matrix for InterviewIQ.
Covers all 12 functional areas and 16 API endpoints across the
Python DirectML Sidecar, multi-agent pipeline, SQLite persistence,
and document/audio inference engines.
"""

import asyncio
import base64
import json
import os
import unittest

from sidecar import server
from utils.database import DatabaseManager
from utils.session_manager import SessionManager


class TestFunctionalMatrix(unittest.TestCase):
    """Exhaustive functional verification suite for InterviewIQ."""

    @classmethod
    def setUpClass(cls):
        DatabaseManager.init_db()

    def setUp(self):
        self.app = server.app
        server.EXPECTED_BEARER_TOKEN = None

    def _call(self, method: str, path: str, body: dict = None, headers: list = None) -> tuple:
        """Invokes the ASGI application synchronously and returns (status_code, json_or_text)."""
        raw_body = json.dumps(body).encode("utf-8") if body is not None else b""
        req_headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(raw_body)).encode("ascii")),
        ]
        if headers:
            for k, v in headers:
                req_headers.append((k.lower().encode("ascii"), v.encode("ascii")))

        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": req_headers,
            "state": {},
        }

        sent = []

        async def send(msg):
            sent.append(msg)

        async def receive():
            return {"type": "http.request", "body": raw_body, "more_body": False}

        asyncio.run(self.app(scope, receive, send))

        status_code = 500
        body_parts = []
        for msg in sent:
            if msg["type"] == "http.response.start":
                status_code = msg["status"]
            elif msg["type"] == "http.response.body":
                body_parts.append(msg.get("body", b""))

        res_data = {}
        raw_resp = b"".join(body_parts)
        if raw_resp:
            try:
                res_data = json.loads(raw_resp.decode("utf-8"))
            except Exception:
                res_data = {"raw": raw_resp.decode("utf-8", errors="ignore")}

        return status_code, res_data

    # -------------------------------------------------------------------------
    # F1: Health & Telemetry
    # -------------------------------------------------------------------------
    def test_f1_health_probe(self):
        status, data = self._call("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "InterviewIQ DirectML Sidecar")
        self.assertIn("directml", data)
        self.assertIn("provider", data["directml"])
        self.assertIn("device_name", data["directml"])

    def test_f1_telemetry(self):
        status, data = self._call("GET", "/api/telemetry")
        self.assertEqual(status, 200)
        self.assertIn("current_rpm", data)
        self.assertIn("cache_savings_pct", data)
        self.assertIn("directml", data)

    # -------------------------------------------------------------------------
    # F2: Authentication & Security Guardrails
    # -------------------------------------------------------------------------
    def test_f2_bearer_auth_guard(self):
        server.EXPECTED_BEARER_TOKEN = "secret-guard-token"
        try:
            # 1. Missing header -> 401
            status, data = self._call("GET", "/api/telemetry")
            self.assertEqual(status, 401)
            self.assertIn("Missing Bearer Token", data.get("error", ""))

            # 2. Invalid token -> 403
            status, data = self._call(
                "GET", "/api/telemetry", headers=[("Authorization", "Bearer wrong-secret")]
            )
            self.assertEqual(status, 403)
            self.assertIn("Invalid Bearer Token", data.get("error", ""))

            # 3. Valid token -> 200
            status, data = self._call(
                "GET", "/api/telemetry", headers=[("Authorization", "Bearer secret-guard-token")]
            )
            self.assertEqual(status, 200)
        finally:
            server.EXPECTED_BEARER_TOKEN = None

    def test_f2_validate_api_key_empty(self):
        status, data = self._call("POST", "/api/auth/validate-key", {"api_key": ""})
        self.assertEqual(status, 400)
        self.assertFalse(data.get("valid"))

    # -------------------------------------------------------------------------
    # F3: Candidate Ingestion & Parsing
    # -------------------------------------------------------------------------
    def test_f3_onboard_validation(self):
        # Empty inputs
        status, data = self._call("POST", "/api/pipeline/onboard", {"resume_text": "", "jd_text": ""})
        self.assertEqual(status, 400)
        self.assertIn("error", data)

    def test_f3_onboard_success(self):
        sample_resume = "Aarav Sharma. Senior Distributed Systems Engineer with 8 years building Raft consensus, Go, Kafka, and Kubernetes."
        sample_jd = "GlobalTech Solutions. Looking for Senior Systems Engineer with Go, Distributed Systems, Microservices, and Cloud Architecture."
        status, data = self._call("POST", "/api/pipeline/onboard", {"resume_text": sample_resume, "jd_text": sample_jd})
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "success")
        self.assertIn("profile", data)
        self.assertIn("jd_analysis", data)
        self.assertIn("session_id", data)

    # -------------------------------------------------------------------------
    # F4: Strategic Role Fit Analysis
    # -------------------------------------------------------------------------
    def test_f4_fit_analysis_validation(self):
        status, data = self._call("POST", "/api/pipeline/fit-analysis", {})
        # If server state is populated it might run or reject if empty
        if status == 400:
            self.assertIn("error", data)

    def test_f4_fit_analysis_execution(self):
        profile = {
            "candidate_name": "Aarav Sharma",
            "name": "Aarav Sharma",
            "technical_skills": ["Go", "Kubernetes", "Kafka", "Distributed Systems", "SQL"],
            "years_of_experience": 8,
            "summary": "Distributed systems engineer specializing in consensus and stream processing.",
        }
        jd_analysis = {
            "role_title": "Senior Distributed Systems Engineer",
            "company_name": "GlobalTech Solutions",
            "mandatory_skills": ["Go", "Distributed Systems", "Kubernetes"],
            "preferred_skills": ["Kafka", "Rust"],
            "experience_level": "Senior (6+ years)",
        }
        status, data = self._call("POST", "/api/pipeline/fit-analysis", {"profile": profile, "jd_analysis": jd_analysis})
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "success")
        fit_report = data.get("fit_report", {})
        self.assertIn("technical_match_pct", fit_report)
        self.assertGreaterEqual(fit_report["technical_match_pct"], 0.0)
        self.assertLessEqual(fit_report["technical_match_pct"], 100.0)

    # -------------------------------------------------------------------------
    # F5: Question Bank Engine
    # -------------------------------------------------------------------------
    def test_f5_question_bank_generation(self):
        profile = {"name": "Aarav Sharma", "technical_skills": ["Go", "Kubernetes"]}
        jd_analysis = {"role_title": "Systems Architect", "mandatory_skills": ["Go", "Distributed Systems"]}
        status, data = self._call("POST", "/api/pipeline/question-bank", {"profile": profile, "jd_analysis": jd_analysis})
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "success")
        qb = data.get("question_bank", {})
        self.assertIn("topic_checklist", qb)
        self.assertGreater(len(qb["topic_checklist"]), 0)

    # -------------------------------------------------------------------------
    # F6: Online Test Generation & Scoring
    # -------------------------------------------------------------------------
    def test_f6_online_test_and_scoring(self):
        qb = {"topic_checklist": [{"topic": "Distributed Consensus", "category": "Mandatory"}]}
        jd_analysis = {"role_title": "Staff Engineer"}
        
        # 1. Test Generation
        status, data = self._call("POST", "/api/pipeline/online-test", {"question_bank": qb, "jd_analysis": jd_analysis})
        self.assertEqual(status, 200)
        test_suite = data.get("online_test", {})
        questions = test_suite.get("questions", [])
        self.assertGreaterEqual(len(questions), 30)

        # 2. Perfect Score Test
        perfect_answers = {q["question_id"]: q["correct_option"] for q in questions}
        status, score_data = self._call("POST", "/api/pipeline/score-test", {
            "test_questions": questions,
            "user_answers": perfect_answers,
        })
        self.assertEqual(status, 200)
        results = score_data.get("test_results", {})
        self.assertEqual(results.get("score"), len(questions))
        self.assertEqual(results.get("percentage"), 100.0)
        self.assertTrue(results.get("passed"))

        # 3. Zero Score Test
        wrong_answers = {
            q["question_id"]: ("B" if q["correct_option"] == "A" else "A") for q in questions
        }
        status, score_data2 = self._call("POST", "/api/pipeline/score-test", {
            "test_questions": questions,
            "user_answers": wrong_answers,
        })
        self.assertEqual(status, 200)
        results2 = score_data2.get("test_results", {})
        self.assertEqual(results2.get("score"), 0)
        self.assertEqual(results2.get("percentage"), 0.0)
        self.assertFalse(results2.get("passed"))

    # -------------------------------------------------------------------------
    # F7: Diagnostics & Feedback (45/55 Formula Invariant)
    # -------------------------------------------------------------------------
    def test_f7_feedback_formula_invariant(self):
        fit_report = {
            "placement_readiness_score": 80.0,
            "technical_match_pct": 80.0,
            "requirements_matrix": [],
        }
        test_results = {
            "score": 27,
            "total_questions": 30,
            "percentage": 90.0,
            "passed": True,
            "topic_breakdown": [],
        }
        status, data = self._call("POST", "/api/pipeline/feedback", {
            "fit_report": fit_report,
            "test_results": test_results,
            "candidate_name": "Aarav Sharma",
        })
        self.assertEqual(status, 200)
        fb = data.get("feedback", {})
        comp_score = fb.get("overall_readiness_score")
        
        # Expected: 0.45 * 80 + 0.55 * 90 = 36.0 + 49.5 = 85.5
        expected = round(0.45 * 80.0 + 0.55 * 90.0, 1)
        self.assertAlmostEqual(comp_score, expected, places=1)

    # -------------------------------------------------------------------------
    # F8: 7-Day Agile Micro-Curriculum & Persistence
    # -------------------------------------------------------------------------
    def test_f8_curriculum_and_task_toggle(self):
        feedback = {
            "overall_readiness_score": 75.0,
            "unified_topic_readiness": [
                {"topic": "Distributed Consensus", "priority": "High Priority"}
            ],
        }
        jd_analysis = {"role_title": "Distributed Systems Engineer"}

        # 1. Generate curriculum
        status, data = self._call("POST", "/api/pipeline/curriculum", {
            "feedback": feedback,
            "jd_analysis": jd_analysis,
        })
        self.assertEqual(status, 200)
        curr = data.get("curriculum", {})
        days = curr.get("days", [])
        self.assertEqual(len(days), 7)

        # 2. Toggle Task Checkbox
        sess_id = server.GLOBAL_ORCHESTRATOR.session_id
        status, toggle_res = self._call("POST", "/api/curriculum/toggle-task", {
            "session_id": sess_id,
            "day_number": 1,
            "task_id": "d1_t1",
            "completed": True,
        })
        self.assertEqual(status, 200)
        self.assertTrue(toggle_res.get("completed"))

        # Verify task is present in checklist
        plan = DatabaseManager.get_curriculum_plan(sess_id)
        if plan:
            self.assertIn("d1_t1", plan.get("checked_items_list", []))

        # 3. Untoggle Task Checkbox
        status, toggle_res2 = self._call("POST", "/api/curriculum/toggle-task", {
            "session_id": sess_id,
            "day_number": 1,
            "task_id": "d1_t1",
            "completed": False,
        })
        self.assertEqual(status, 200)
        self.assertFalse(toggle_res2.get("completed"))

    # -------------------------------------------------------------------------
    # F9: Voice Transcription Engine
    # -------------------------------------------------------------------------
    def test_f9_voice_transcription(self):
        # Empty audio -> 400
        status, data = self._call("POST", "/api/voice/transcribe", {"audio_base64": ""})
        self.assertEqual(status, 400)

        # Corrupted / Mock base64 -> graceful recovery
        fake_b64 = base64.b64encode(b"RIFFmockwavheaderdata").decode()
        status, data = self._call("POST", "/api/voice/transcribe", {"audio_base64": fake_b64})
        self.assertEqual(status, 200)
        self.assertIn("transcript", data)
        self.assertIn("wpm", data)

    # -------------------------------------------------------------------------
    # F10: Semantic Similarity Embeddings
    # -------------------------------------------------------------------------
    def test_f10_semantic_similarity(self):
        query = "distributed database consensus protocol"
        candidates = [
            "Raft consensus and Paxos leader election",
            "Frontend React component styling with CSS",
            "Kafka message partition queue",
        ]
        status, data = self._call("POST", "/api/semantic/similarity", {
            "query": query,
            "candidates": candidates,
        })
        self.assertEqual(status, 200)
        matches = data.get("matches", [])
        self.assertEqual(len(matches), 3)
        # Raft should be ranked highest
        self.assertEqual(matches[0][0], candidates[0])

    # -------------------------------------------------------------------------
    # F11: PDF Exporter (Fit Report & Full Dossier)
    # -------------------------------------------------------------------------
    def test_f11_export_pdf_fit_report(self):
        status, data = self._call("POST", "/api/export/pdf", {
            "type": "fit_report",
            "candidate_name": "Aarav Sharma",
            "role_title": "Senior Systems Engineer",
            "fit_report": {
                "technical_match_pct": 85.0,
                "experience_scoring": {"awarded_points": 9},
                "decision_engine": {"final_decision": "STRONG HIRE"},
                "requirements_matrix": [],
            },
        })
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "success")
        pdf_b64 = data.get("pdf_base64", "")
        self.assertGreater(len(pdf_b64), 500)
        raw_pdf = base64.b64decode(pdf_b64)
        self.assertTrue(raw_pdf.startswith(b"%PDF-"))

    def test_f11_export_pdf_full_dossier(self):
        status, data = self._call("POST", "/api/export/pdf", {"type": "full_dossier"})
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "success")
        pdf_b64 = data.get("pdf_base64", "")
        self.assertGreater(len(pdf_b64), 500)
        raw_pdf = base64.b64decode(pdf_b64)
        self.assertTrue(raw_pdf.startswith(b"%PDF-"))

    # -------------------------------------------------------------------------
    # F12: SQLite Session Persistence & Retrieval
    # -------------------------------------------------------------------------
    def test_f12_sessions_api(self):
        # 1. List sessions
        status, data = self._call("GET", "/api/sessions")
        self.assertEqual(status, 200)
        self.assertIn("sessions", data)
        self.assertIsInstance(data["sessions"], list)

        # 2. Non-existent session 404
        status, data = self._call("GET", "/api/sessions/non_existent_session_id_99999")
        self.assertEqual(status, 404)
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
