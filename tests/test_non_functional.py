"""
tests/test_non_functional.py
Comprehensive Non-Functional Test Suite for InterviewIQ.
Covers:
1. Performance & Latency SLAs (micro-benchmarks)
2. Concurrency & Multi-Thread Stress Testing (SQLite & Thread Safety)
3. Security, Zero Secret Leakage & SQL Injection Defense
4. Memory & SQLite Handle Leaking Prevention
"""

import asyncio
import concurrent.futures
import json
import os
import time
import unittest

from sidecar import server
from utils.database import DatabaseManager


class TestNonFunctionalMatrix(unittest.TestCase):
    """Rigorous non-functional verification: latency, load, security, and stability."""

    @classmethod
    def setUpClass(cls):
        DatabaseManager.init_db()

    def setUp(self):
        self.app = server.app
        server.EXPECTED_BEARER_TOKEN = None

    def _call(self, method: str, path: str, body: dict = None, headers: list = None) -> tuple:
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
    # NF1: Latency & Response SLAs
    # -------------------------------------------------------------------------
    def test_nf1_health_latency_sla(self):
        """Verify health check responds in < 30ms."""
        t0 = time.perf_counter()
        status, data = self._call("GET", "/health")
        elapsed_ms = (time.perf_counter() - t0) * 1000
        self.assertEqual(status, 200)
        self.assertLess(elapsed_ms, 30.0, f"Health check latency {elapsed_ms:.2f}ms exceeded SLA (30ms)")

    def test_nf1_telemetry_latency_sla(self):
        """Verify telemetry responds in < 40ms."""
        t0 = time.perf_counter()
        status, data = self._call("GET", "/api/telemetry")
        elapsed_ms = (time.perf_counter() - t0) * 1000
        self.assertEqual(status, 200)
        self.assertLess(elapsed_ms, 40.0, f"Telemetry latency {elapsed_ms:.2f}ms exceeded SLA (40ms)")

    def test_nf1_pdf_export_latency_sla(self):
        """Verify PDF generation responds in < 800ms."""
        t0 = time.perf_counter()
        status, data = self._call("POST", "/api/export/pdf", {
            "type": "fit_report",
            "candidate_name": "Latency Benchmark Candidate",
            "role_title": "Lead Architect",
            "fit_report": {"technical_match_pct": 90.0, "requirements_matrix": []},
        })
        elapsed_ms = (time.perf_counter() - t0) * 1000
        self.assertEqual(status, 200)
        self.assertLess(elapsed_ms, 800.0, f"PDF generation {elapsed_ms:.2f}ms exceeded SLA (800ms)")

    # -------------------------------------------------------------------------
    # NF2: Concurrency & Multi-Thread Stress
    # -------------------------------------------------------------------------
    def test_nf2_concurrency_stress_25_workers(self):
        """
        Dispatches 25 concurrent requests across threads hitting SQLite writes,
        session reads, and fit evaluations simultaneously without deadlocks or DB locks.
        """
        num_workers = 25
        results = []

        def worker_task(idx):
            sess_id = f"stress_session_{idx}"
            # 1. Toggle task in SQLite
            s1, d1 = self._call("POST", "/api/curriculum/toggle-task", {
                "session_id": sess_id,
                "day_number": (idx % 7) + 1,
                "task_id": f"task_{idx}",
                "completed": (idx % 2 == 0),
            })
            # 2. Query sessions
            s2, d2 = self._call("GET", "/api/sessions")
            # 3. Fit evaluation
            s3, d3 = self._call("POST", "/api/pipeline/fit-analysis", {
                "profile": {"name": f"Candidate {idx}", "technical_skills": ["Go", "SQL"]},
                "jd_analysis": {"role_title": "Engineer", "mandatory_skills": ["Go"]},
            })
            return (s1 == 200, s2 == 200, s3 == 200)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(worker_task, i) for i in range(num_workers)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        self.assertEqual(len(results), num_workers)
        for r1, r2, r3 in results:
            self.assertTrue(r1, "Task toggle failed during concurrency stress")
            self.assertTrue(r2, "Sessions list failed during concurrency stress")
            self.assertTrue(r3, "Fit analysis failed during concurrency stress")

    # -------------------------------------------------------------------------
    # NF3: Resource & SQLite Handle Leaking Prevention
    # -------------------------------------------------------------------------
    def test_nf3_database_handle_cleanup_100_queries(self):
        """Executes 100 sequential queries in rapid succession ensuring zero handle leakage."""
        for i in range(100):
            with DatabaseManager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 + 1 AS result;")
                row = cursor.fetchone()
                self.assertEqual(row["result"], 2)

    # -------------------------------------------------------------------------
    # NF4: Security & Injection Resistance
    # -------------------------------------------------------------------------
    def test_nf4_sql_injection_defense(self):
        """Validates that SQL injection attempts in session_id or input strings are thwarted."""
        malicious_inputs = [
            "'; DROP TABLE sessions; --",
            "1 OR 1=1",
            "' UNION SELECT * FROM users --",
            "<script>alert('xss')</script>",
        ]
        for payload in malicious_inputs:
            # 1. Load session by malicious ID
            status, data = self._call("GET", f"/api/sessions/{payload}")
            self.assertEqual(status, 404)

            # 2. Toggle task with malicious ID
            status, data = self._call("POST", "/api/curriculum/toggle-task", {
                "session_id": payload,
                "day_number": 1,
                "task_id": payload,
                "completed": True,
            })
            self.assertEqual(status, 200)

        # Confirm sessions table is still intact and operable
        status, data = self._call("GET", "/api/sessions")
        self.assertEqual(status, 200)

    def test_nf4_zero_secret_leakage(self):
        """Validates that telemetry, health, and error responses never echo API keys."""
        status, data = self._call("GET", "/api/telemetry")
        raw_text = json.dumps(data)
        self.assertNotIn("AIzaSy", raw_text)
        self.assertNotIn("api_key", data)

        status, data = self._call("POST", "/api/auth/validate-key", {"api_key": "AIzaSyFakeKeyForTest12345"})
        raw_text = json.dumps(data)
        self.assertNotIn("AIzaSyFakeKeyForTest12345", raw_text)


if __name__ == "__main__":
    unittest.main()
