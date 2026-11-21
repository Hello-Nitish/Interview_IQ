"""
Unit Tests for InterviewIQ Python DirectML Sidecar.
Validates microservice routing, bearer token security, DirectML hardware detection,
semantic embeddings, and speech analytics engines.
"""

import asyncio
import json
import unittest
from sidecar import server
from sidecar.directml.engine import get_directml_engine
from sidecar.directml.embeddings import get_embeddings_engine
from sidecar.directml.whisper_stt import get_speech_engine


class TestDirectMLSidecar(unittest.TestCase):
    """Test suite for DirectML sidecar microservice and inference engines."""

    def setUp(self):
        self.app = server.app
        # Set a test bearer token
        server.EXPECTED_BEARER_TOKEN = "test-secret-token-xyz-123"

    def tearDown(self):
        server.EXPECTED_BEARER_TOKEN = None

    def _call_asgi(self, method: str, path: str, body: dict = None, headers: list = None) -> tuple:
        """Helper to invoke the ASGI app synchronously."""
        raw_body = json.dumps(body).encode("utf-8") if body else b""
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
        headers_out = {}
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

    def test_health_check_public_endpoint(self):
        """Verify /health is accessible without a bearer token and returns DirectML info."""
        status, data = self._call_asgi("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "InterviewIQ DirectML Sidecar")
        self.assertIn("directml", data)
        self.assertIn("provider", data["directml"])

    def test_bearer_token_authentication_enforcement(self):
        """Verify protected /api/* endpoints reject unauthorized requests."""
        # 1. No token -> 401
        status, data = self._call_asgi("GET", "/api/telemetry")
        self.assertEqual(status, 401)
        self.assertIn("Missing Bearer Token", data.get("error", ""))

        # 2. Invalid token -> 403
        status, data = self._call_asgi(
            "GET",
            "/api/telemetry",
            headers=[("Authorization", "Bearer invalid-token")],
        )
        self.assertEqual(status, 403)
        self.assertIn("Invalid Bearer Token", data.get("error", ""))

        # 3. Valid token -> 200
        status, data = self._call_asgi(
            "GET",
            "/api/telemetry",
            headers=[("Authorization", "Bearer test-secret-token-xyz-123")],
        )
        self.assertEqual(status, 200)
        self.assertIn("session_calls", data)

    def test_root_serves_static_frontend(self):
        """Verify root / endpoint serves the desktop frontend HTML."""
        status, data = self._call_asgi("GET", "/")
        self.assertEqual(status, 200)
        raw_text = data.get("raw", "")
        self.assertIn("InterviewIQ", raw_text)

    def test_directml_engine_hardware_reporting(self):
        """Verify DirectMLEngine returns well-formed hardware telemetry."""
        engine = get_directml_engine()
        info = engine.get_device_info()
        self.assertIn("directml_available", info)
        self.assertIn("provider", info)
        self.assertIn("device_name", info)
        self.assertIn("details", info)

    def test_semantic_embeddings_cosine_similarity(self):
        """Verify DirectML embeddings engine calculates accurate semantic similarities."""
        embeddings = get_embeddings_engine()
        # Identical text should have similarity ~1.0
        sim_identical = embeddings.compute_similarity(
            "Experienced Python and Go backend developer with Kubernetes",
            "Experienced Python and Go backend developer with Kubernetes",
        )
        self.assertGreaterEqual(sim_identical, 0.95)

        # Related text should have higher similarity than unrelated text
        sim_related = embeddings.compute_similarity(
            "Senior Software Engineer specializing in Go microservices and distributed systems",
            "Golang backend engineering with high-throughput API architecture",
        )
        sim_unrelated = embeddings.compute_similarity(
            "Senior Software Engineer specializing in Go microservices and distributed systems",
            "Pastry chef skilled in French bakery and croissant decoration",
        )
        self.assertGreater(sim_related, sim_unrelated)

    def test_whisper_speech_metrics_calculation(self):
        """Verify speech engine accurately computes WPM, filler words, and STAR tags."""
        speech_eng = get_speech_engine()
        sample_transcript = (
            "Well basically in my previous role the situation was that our API latency was over 500ms. "
            "My task was to optimize query performance. I took the action of implementing Redis caching "
            "and indexing Postgres tables. The result was a 65% reduction in response times."
        )
        metrics = speech_eng.analyze_text_speech_metrics(sample_transcript, duration_seconds=18.0)

        self.assertGreater(metrics["word_count"], 30)
        self.assertGreater(metrics["wpm"], 100)
        self.assertGreaterEqual(metrics["filler_count"], 1)  # Detected "basically"
        self.assertIn("basically", metrics["fillers_detected"])

        star = metrics["star_alignment"]
        self.assertTrue(star["has_situation"])
        self.assertTrue(star["has_task"])
        self.assertTrue(star["has_action"])
        self.assertTrue(star["has_result"])
        self.assertEqual(star["score_out_of_4"], 4)


if __name__ == "__main__":
    unittest.main()
