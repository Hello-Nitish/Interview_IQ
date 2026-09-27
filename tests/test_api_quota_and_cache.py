import unittest
import os
import sys
import time

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.api_quota_manager import APIQuotaManager
from utils.gemini_cache import GeminiCache
from utils.gemini_client import sanitize_and_budget_prompt, GeminiClient
from utils.database import DatabaseManager

class TestAPIQuotaAndCache(unittest.TestCase):
    def setUp(self):
        APIQuotaManager.reset_session_stats()
        GeminiCache.clear()

    def test_token_bucket_rate_pacing(self):
        # First call establishes baseline
        APIQuotaManager._last_request_timestamp = time.time()
        
        # Second call immediately after should be paced by ~2.0s
        start = time.time()
        slept = APIQuotaManager.wait_for_slot()
        elapsed = time.time() - start

        self.assertGreaterEqual(slept, 1.8)
        self.assertGreaterEqual(elapsed, 1.8)

    def test_sliding_window_rpm_and_telemetry(self):
        APIQuotaManager.reset_session_stats()
        
        # Record 4 calls
        APIQuotaManager.record_call(token_count=150)
        APIQuotaManager.record_call(token_count=200)
        APIQuotaManager.record_call(token_count=250)
        APIQuotaManager.record_cache_hit(saved_tokens=300)

        rpm = APIQuotaManager.get_current_rpm()
        self.assertEqual(rpm, 3)

        stats = APIQuotaManager.get_telemetry_stats()
        self.assertEqual(stats["session_calls"], 3)
        self.assertEqual(stats["session_cache_hits"], 1)
        self.assertEqual(stats["total_requests"], 4)
        self.assertEqual(stats["cache_savings_pct"], 25.0)
        self.assertEqual(stats["estimated_tokens"], 600)
        self.assertIn("Optimal", stats["rate_status"])

    def test_sha256_two_tier_cache(self):
        model = "gemini-1.5-flash"
        instruction = "You are an analytical evaluator."
        prompt = "Evaluate the candidate's proficiency in Enterprise Cloud Systems."
        is_json = True

        cache_key = GeminiCache.compute_hash(model, instruction, prompt, is_json)
        self.assertIsInstance(cache_key, str)
        self.assertEqual(len(cache_key), 64) # SHA-256 is 64 hex chars

        # Initial lookup must miss
        self.assertIsNone(GeminiCache.get(cache_key))

        # Store response
        sample_response = '{"rating": 92, "verdict": "Strong Alignment"}'
        GeminiCache.put(cache_key, model, is_json, sample_response)

        # L1 RAM cache hit
        cached_result = GeminiCache.get(cache_key)
        self.assertEqual(cached_result, sample_response)

        # Check L2 SQLite persistence directly
        db_val = DatabaseManager.get_api_cache_entry(cache_key)
        self.assertEqual(db_val, sample_response)

        # Evict L1 RAM to force an L2 database hit
        GeminiCache._l1_cache.clear()
        l2_promoted_result = GeminiCache.get(cache_key)
        self.assertEqual(l2_promoted_result, sample_response)
        # Verify it was promoted back to L1
        self.assertIn(cache_key, GeminiCache._l1_cache)

    def test_token_budgeting_preprocessor(self):
        # Short text should remain unchanged
        short_prompt = "Short prompt under token budget."
        self.assertEqual(sanitize_and_budget_prompt(short_prompt, max_chars=1000), short_prompt)

        # Massive 30,000 character prompt should be safely budgeted to 24,000
        massive_prompt = "Header Line: Start of Evaluation Prompt.\n" + ("x" * 30000) + "\nTail Line: End of Schema."
        budgeted = sanitize_and_budget_prompt(massive_prompt, max_chars=24000)
        self.assertLessEqual(len(budgeted), 24100)
        self.assertIn("Header Line: Start of Evaluation Prompt.", budgeted)
        self.assertIn("Tail Line: End of Schema.", budgeted)
        self.assertIn("Middle text budgeted to respect Gemini TPM limits", budgeted)

    def test_key_validation_edge_cases(self):
        # Empty key
        is_ok, msg = APIQuotaManager.validate_api_key("")
        self.assertFalse(is_ok)
        self.assertIn("empty", msg.lower())

        # Incomplete/short key
        is_ok, msg = APIQuotaManager.validate_api_key("12345")
        self.assertFalse(is_ok)
        self.assertIn("too short", msg.lower())

        # Placeholder string
        is_ok, msg = APIQuotaManager.validate_api_key("your_actual_gemini_api_key")
        self.assertFalse(is_ok)
        self.assertIn("authentic", msg.lower())

    def test_active_model_tracking(self):
        """Verify get_active_model and set_active_model update global state."""
        APIQuotaManager.set_active_model("gemini-2.0-flash")
        self.assertEqual(APIQuotaManager.get_active_model(), "gemini-2.0-flash")
        self.assertEqual(GeminiClient._ACTIVE_MODEL_NAME, "gemini-2.0-flash")

        APIQuotaManager.set_active_model("models/gemini-1.5-flash-latest")
        self.assertEqual(APIQuotaManager.get_active_model(), "gemini-1.5-flash-latest")
        self.assertEqual(GeminiClient._ACTIVE_MODEL_NAME, "gemini-1.5-flash-latest")

    def test_validate_api_key_404_fallback(self):
        """Verify validate_api_key gracefully handles 404 on older models and succeeds with available model."""
        from unittest.mock import patch, MagicMock
        from google.api_core.exceptions import GoogleAPICallError

        # Mock list_models returning models list
        mock_model_1 = MagicMock()
        mock_model_1.name = "models/gemini-1.5-flash"
        mock_model_1.supported_generation_methods = ["generateContent"]

        mock_model_2 = MagicMock()
        mock_model_2.name = "models/gemini-2.0-flash"
        mock_model_2.supported_generation_methods = ["generateContent"]

        with patch("google.generativeai.list_models", return_value=[mock_model_1, mock_model_2]):
            with patch("google.generativeai.GenerativeModel") as mock_gm:
                # First model (gemini-2.0-flash) succeeds
                instance = MagicMock()
                resp = MagicMock()
                resp.text = "Pong"
                instance.generate_content.return_value = resp
                mock_gm.return_value = instance

                is_ok, msg = APIQuotaManager.validate_api_key("AIzaSyFakeKeyForTesting123456789")
                self.assertTrue(is_ok)
                self.assertIn("gemini-2.0-flash", msg)

    def test_validate_api_key_when_model_throws_404(self):
        """Verify that if candidate 1 throws 404, probe catches it and falls back to candidate 2."""
        from unittest.mock import patch, MagicMock
        from google.api_core.exceptions import GoogleAPICallError

        call_count = 0
        def fake_generate_content(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call throws 404 (models/gemini-2.0-flash or gemini-1.5-flash not found)
                err = GoogleAPICallError("models/gemini-2.0-flash is not found for API version v1beta")
                err.code = 404
                raise err
            # Second call succeeds
            resp = MagicMock()
            resp.text = "Pong"
            return resp

        with patch("google.generativeai.list_models", side_effect=Exception("ListModels not supported")):
            with patch("google.generativeai.GenerativeModel") as mock_gm:
                instance = MagicMock()
                instance.generate_content.side_effect = fake_generate_content
                mock_gm.return_value = instance

                is_ok, msg = APIQuotaManager.validate_api_key("AIzaSyFakeKeyForTesting123456789")
                self.assertTrue(is_ok)
                self.assertGreaterEqual(call_count, 2)


if __name__ == "__main__":
    unittest.main()
