import os
import time
import logging
import re
import threading
import warnings
from typing import Dict, Any, Tuple, List, Optional, Set

warnings.simplefilter("ignore", category=FutureWarning)

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPICallError, PermissionDenied, InvalidArgument, ResourceExhausted

logger = logging.getLogger(__name__)

class APIQuotaManager:
    """
    Intelligent Quota & Rate Management Engine for Google Gemini APIs.
    Enforces programmatic Token-Bucket pacing (<=12 RPM), sliding-window rate tracking,
    session telemetry, and real-time credential validation probes.
    Thread-safe implementation for concurrent multi-agent executions.
    """
    MIN_CALL_INTERVAL_SEC: float = 2.0       # Guaranteed <= 12 RPM (safety buffer against 15 RPM ceiling)
    MAX_DAILY_FREE_QUOTA: int = 1500         # Free-tier daily request quota

    PREFERRED_MODELS: List[str] = [
        # Tier 1: Modern Flash (Primary Recommendation - High Throughput, Low Latency)
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-001",
        # Tier 2: Resilient Flash Fallbacks (High Availability Workhorses)
        "gemini-2.5-flash-lite",
        "gemini-flash-lite-latest",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-1.5-flash-8b",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        # Tier 3: Pro & Legacy Reasoning Fallbacks (Deep Analysis)
        "gemini-2.5-pro",
        "gemini-1.5-pro",
        "gemini-pro"
    ]

    _lock: threading.Lock = threading.Lock()
    _last_request_timestamp: float = 0.0
    _session_call_count: int = 0
    _session_cache_hits: int = 0
    _estimated_tokens_consumed: int = 0
    _sliding_window_timestamps: List[float] = []

    @classmethod
    def wait_for_slot(cls) -> float:
        """
        Calculates elapsed time since the last Gemini API call using atomic slot reservation.
        Computes the target time and required sleep under the lock, then sleeps OUTSIDE
        the lock so UI telemetry queries and session meter reads never freeze.
        Returns the duration slept in seconds.
        """
        with cls._lock:
            now = time.time()
            target_time = max(now, cls._last_request_timestamp + cls.MIN_CALL_INTERVAL_SEC)
            sleep_needed = max(0.0, target_time - now)
            cls._last_request_timestamp = target_time

        if sleep_needed > 0:
            logger.debug(f"[APIQuotaManager] Pacing API call: sleeping {sleep_needed:.2f}s to respect <=12 RPM limit.")
            time.sleep(sleep_needed)

        return sleep_needed

    @classmethod
    def record_call(cls, token_count: int = 0):
        """
        Records an outbound API call, updates sliding-window timestamps for RPM monitoring,
        and aggregates estimated tokens.
        """
        with cls._lock:
            now = time.time()
            cls._session_call_count += 1
            cls._estimated_tokens_consumed += max(0, token_count)

            # Update sliding window (calls within the last 60 seconds)
            cls._sliding_window_timestamps.append(now)
            cls._prune_sliding_window_locked(now)

    @classmethod
    def record_cache_hit(cls, saved_tokens: int = 0):
        """
        Records an avoided API call satisfied via the SHA-256 response cache.
        """
        with cls._lock:
            cls._session_cache_hits += 1

    @classmethod
    def _prune_sliding_window_locked(cls, current_time: Optional[float] = None):
        """Internal helper: removes timestamps older than 60 seconds (must be called with _lock)."""
        now = current_time or time.time()
        cls._sliding_window_timestamps = [t for t in cls._sliding_window_timestamps if (now - t) < 60.0]

    @classmethod
    def _prune_sliding_window(cls, current_time: Optional[float] = None):
        """Removes timestamps older than 60 seconds from the sliding window."""
        with cls._lock:
            cls._prune_sliding_window_locked(current_time)

    @classmethod
    def get_current_rpm(cls) -> int:
        """Computes current Requests Per Minute over the trailing 60-second window."""
        cls._prune_sliding_window()
        return len(cls._sliding_window_timestamps)

    @classmethod
    def get_telemetry_stats(cls) -> Dict[str, Any]:
        """
        Returns structured telemetry statistics for frontend display.
        """
        current_rpm = cls.get_current_rpm()
        total_requests_handled = cls._session_call_count + cls._session_cache_hits
        cache_hit_pct = round((cls._session_cache_hits / total_requests_handled) * 100, 1) if total_requests_handled > 0 else 0.0

        # Determine rate health status
        if current_rpm <= 8:
            rate_status = "Optimal"
            status_color = "#10B981" # Green
        elif current_rpm <= 12:
            rate_status = "Active / Paced"
            status_color = "#3B82F6" # Blue
        else:
            rate_status = "Nearing Limit"
            status_color = "#F59E0B" # Amber

        return {
            "session_calls": cls._session_call_count,
            "session_cache_hits": cls._session_cache_hits,
            "total_requests": total_requests_handled,
            "cache_savings_pct": cache_hit_pct,
            "current_rpm": current_rpm,
            "rpm_ceiling": 15,
            "target_rpm": 12,
            "estimated_tokens": cls._estimated_tokens_consumed,
            "daily_limit": cls.MAX_DAILY_FREE_QUOTA,
            "daily_remaining_est": max(0, cls.MAX_DAILY_FREE_QUOTA - cls._session_call_count),
            "rate_status": rate_status,
            "status_color": status_color
        }

    @classmethod
    def reset_session_stats(cls):
        """Resets telemetry counters for testing or fresh sessions."""
        with cls._lock:
            cls._session_call_count = 0
            cls._session_cache_hits = 0
            cls._estimated_tokens_consumed = 0
            cls._sliding_window_timestamps = []
            cls._last_request_timestamp = 0.0

    _ACTIVE_MODEL_NAME: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    @classmethod
    def get_active_model(cls) -> str:
        """Returns the currently active, verified Gemini model name."""
        return cls._ACTIVE_MODEL_NAME

    @classmethod
    def set_active_model(cls, model_name: str):
        """Sets the active model name across APIQuotaManager and GeminiClient."""
        if model_name:
            clean = model_name.replace("models/", "").strip()
            cls._ACTIVE_MODEL_NAME = clean
            try:
                from utils.gemini_client import GeminiClient
                GeminiClient._ACTIVE_MODEL_NAME = clean
            except Exception:
                pass

    @classmethod
    def validate_api_key(cls, api_key: str) -> Tuple[bool, str]:
        """
        Performs a lightweight credential verification probe against Google Gemini.
        Dynamically queries available models to find an active supported model,
        gracefully bypassing 404 retired models while strictly tracking failures
        to eliminate false-positive fallback.
        Returns:
            (True, "Key is active and verified.") or
            (False, "<User-friendly explanation of failure>")
        """
        if not api_key or not isinstance(api_key, str):
            return False, "API Key cannot be empty."

        clean_key = api_key.strip()
        if len(clean_key) < 15:
            return False, "API Key format is invalid (key appears too short)."

        if any(dummy in clean_key.lower() for dummy in ["your_", "placeholder", "actual_gemini", "enter_key"]):
            return False, "Please provide an authentic Google Gemini API Key from Google AI Studio."

        try:
            genai.configure(api_key=clean_key)

            # Step 1: Discover models supported by this specific user key/project
            discovered_models: List[str] = []
            try:
                for m in genai.list_models():
                    methods = getattr(m, "supported_generation_methods", [])
                    if "generateContent" in methods:
                        m_name = getattr(m, "name", "")
                        if m_name.startswith("models/"):
                            m_name = m_name[len("models/"):]
                        if m_name:
                            discovered_models.append(m_name)
            except PermissionDenied:
                return False, "Authentication failed: Invalid API Key. Please check the key in Google AI Studio."
            except InvalidArgument as e:
                err = str(e)
                if "API_KEY_INVALID" in err or "API key not valid" in err:
                    return False, "Authentication failed: Invalid API Key. Please check the key in Google AI Studio."
                return False, f"Invalid API parameter: {err[:140]}"
            except GoogleAPICallError as e:
                err = str(e)
                if getattr(e, "code", 0) in (400, 403) or "API_KEY_INVALID" in err or "not valid" in err.lower():
                    return False, "Authentication failed: Invalid API Key. Please check the key in Google AI Studio."
            except Exception as e:
                err = str(e)
                if "API_KEY_INVALID" in err or "API key not valid" in err or "403" in err:
                    return False, "Authentication failed: Invalid API Key. Please check the key in Google AI Studio."

            # Step 2: Build prioritized candidate list
            active_m = cls.get_active_model()
            ordered_preferred = [active_m] + [m for m in cls.PREFERRED_MODELS if m != active_m]

            candidates_to_try: List[str] = []
            if discovered_models:
                for p in ordered_preferred:
                    if p in discovered_models and p not in candidates_to_try:
                        candidates_to_try.append(p)
                for d in discovered_models:
                    if d not in candidates_to_try:
                        candidates_to_try.append(d)
            else:
                candidates_to_try = list(ordered_preferred)

            # Step 3: Probe candidates with minimal 1-token test probe, tracking failures
            failed_models: Set[str] = set()
            last_err = None

            for cand in candidates_to_try:
                try:
                    test_model = genai.GenerativeModel(cand)
                    response = test_model.generate_content(
                        "Ping",
                        generation_config={"max_output_tokens": 2, "temperature": 0.0}
                    )
                    if response is not None:
                        cls.set_active_model(cand)
                        return True, f"API Key successfully validated with Google Gemini (Active Model: {cand})."
                except ResourceExhausted:
                    # Rate limit 429 confirms key is authentic and validated
                    cls.set_active_model(cand)
                    return True, f"API Key successfully validated (Active Model: {cand}). Rate pacer will manage quota."
                except GoogleAPICallError as e:
                    last_err = e
                    failed_models.add(cand)
                    err_msg = str(e).lower()
                    if getattr(e, "code", 0) in (400, 403) or "api_key_invalid" in err_msg or "not valid" in err_msg:
                        return False, "Authentication failed: Invalid API Key. Please check the key in Google AI Studio."
                    if getattr(e, "code", 0) == 404 or "not found" in err_msg or "not supported" in err_msg:
                        continue
                except Exception as e:
                    last_err = e
                    failed_models.add(cand)
                    err_msg = str(e).lower()
                    if "api_key_invalid" in err_msg or "not valid" in err_msg:
                        return False, "Authentication failed: Invalid API Key. Please check the key in Google AI Studio."
                    if "quota" in err_msg or "429" in err_msg:
                        cls.set_active_model(cand)
                        return True, f"API Key successfully validated (Active Model: {cand})."
                    if "404" in err_msg or "not found" in err_msg or "not supported" in err_msg:
                        continue

            # Step 4: Strict Failure Handling (Eliminate false-positive fallback)
            viable_models = [m for m in discovered_models if m not in failed_models]
            if viable_models:
                preferred_viable = [p for p in ordered_preferred if p in viable_models]
                fallback_top = preferred_viable[0] if preferred_viable else viable_models[0]
                cls.set_active_model(fallback_top)
                return True, f"API Key validated with available models (Active Model: {fallback_top})."

            if last_err:
                return False, f"Validation probe failed across candidate models (attempted: {sorted(list(failed_models)) if failed_models else 'none'}). Last error: {str(last_err)[:140]}"
            return False, "Could not find a supported Gemini model for this API key. Please check your Google AI Studio project."

        except PermissionDenied:
            return False, "Authentication failed: Invalid API Key. Please check the key in Google AI Studio."
        except InvalidArgument as e:
            return False, f"Invalid API parameter or key format: {str(e)}"
        except ResourceExhausted:
            return True, "API Key verified, but current quota is temporarily exhausted (429). Rate pacer will manage requests."
        except Exception as e:
            err = str(e)
            if "API_KEY_INVALID" in err or "API key not valid" in err:
                return False, "Authentication failed: API Key not valid. Please verify at aistudio.google.com."
            return False, f"Validation probe failed: {err[:140]}"
