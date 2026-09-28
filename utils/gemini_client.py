import os
import re
import time
import random
import logging
import threading
import warnings
from typing import Optional, List, Set, Dict, Any, Tuple

warnings.simplefilter("ignore", category=FutureWarning)

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPICallError
from dotenv import load_dotenv

from utils.api_quota_manager import APIQuotaManager
from utils.gemini_cache import GeminiCache

logger = logging.getLogger(__name__)

# Explicitly find project root .env and force override cached environment
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path, override=True)

# Standardized Tier 1/2/3 Model Cascade (15 RPM / 1M TPM / 1500 RPD)
DEFAULT_MODEL_CASCADE = [
    # Tier 1 Flash: High-throughput primary generative models
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",

    # Tier 2 Lite: Ultra-lightweight fallback models with independent quota pools
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-1.5-flash-8b",

    # Tier 3 Pro: High-capacity reasoning fallbacks
    "gemini-2.5-pro",
    "gemini-1.5-pro",
    "gemini-pro"
]

def extract_retry_delay(error_text: str, default: float = 15.0) -> float:
    """Extract retry delay in seconds from Gemini API 429 error messages."""
    m = re.search(r"retry in ([\d\.]+)s", error_text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    m = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", error_text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    m = re.search(r"seconds:\s*(\d+)", error_text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return default

def sanitize_and_budget_prompt(prompt: str, max_chars: int = 24000) -> str:
    """
    Guards against 1,000,000 TPM limit overconsumption by budgeting excessive
    boilerplate text while preserving prompt instructions, schemas, and core tokens.
    """
    if not prompt or len(prompt) <= max_chars:
        return prompt
    logger.info(f"[GeminiClient] Budgeting prompt: truncating from {len(prompt)} to {max_chars} characters.")
    head_len = int(max_chars * 0.6)
    tail_len = max_chars - head_len - 120
    truncated = prompt[:head_len] + "\n\n... [Middle text budgeted to respect Gemini TPM limits] ...\n\n" + prompt[-tail_len:]
    return truncated

class GeminiClient:
    _blacklist_lock: threading.Lock = threading.Lock()
    _active_model_lock: threading.Lock = threading.Lock()
    _discovery_lock: threading.Lock = threading.Lock()
    _BLACKLISTED_MODELS: Set[str] = set()
    _ACTIVE_MODEL_NAME: Optional[str] = None
    _DISCOVERED_MODELS: Optional[List[str]] = None

    @classmethod
    def blacklist_model(cls, model_name: str) -> None:
        """
        Thread-safely adds a model to the class-level blacklist.
        Blacklisted models are permanently skipped during cascade failover and dynamic discovery.
        """
        if not model_name:
            return
        clean_name = model_name.replace("models/", "").strip()
        with cls._blacklist_lock:
            cls._BLACKLISTED_MODELS.add(clean_name)
            logger.warning(f"[GeminiClient] Model '{clean_name}' blacklisted across all threads.")
        with cls._active_model_lock:
            if cls._ACTIVE_MODEL_NAME == clean_name:
                cls._ACTIVE_MODEL_NAME = None

    @classmethod
    def is_model_blacklisted(cls, model_name: str) -> bool:
        """Checks if a model is currently blacklisted."""
        if not model_name:
            return False
        clean_name = model_name.replace("models/", "").strip()
        with cls._blacklist_lock:
            return clean_name in cls._BLACKLISTED_MODELS

    @classmethod
    def get_blacklisted_models(cls) -> Set[str]:
        """Returns a snapshot of currently blacklisted models."""
        with cls._blacklist_lock:
            return set(cls._BLACKLISTED_MODELS)

    @classmethod
    def set_active_model(cls, model_name: str) -> None:
        """
        Thread-safely updates the global active model across GeminiClient and APIQuotaManager.
        STRICTLY called ONLY upon validated successful content generation.
        """
        if not model_name:
            return
        clean_name = model_name.replace("models/", "").strip()
        with cls._active_model_lock:
            cls._ACTIVE_MODEL_NAME = clean_name
        try:
            APIQuotaManager.set_active_model(clean_name)
        except Exception as e:
            logger.debug(f"[GeminiClient] APIQuotaManager synchronization bypassed: {e}")

    @classmethod
    def get_active_model(cls) -> Optional[str]:
        """Returns the verified global active model name."""
        with cls._active_model_lock:
            return cls._ACTIVE_MODEL_NAME

    @classmethod
    def reset_model_registry(cls) -> None:
        """Resets active, blacklisted, and discovered models (used in test fixtures and key rotations)."""
        with cls._blacklist_lock:
            cls._BLACKLISTED_MODELS.clear()
        with cls._active_model_lock:
            cls._ACTIVE_MODEL_NAME = None
        with cls._discovery_lock:
            cls._DISCOVERED_MODELS = None

    @classmethod
    def discover_models(cls, api_key: Optional[str] = None, force_refresh: bool = False) -> List[str]:
        """
        Queries Google Gemini API for models supporting generateContent available to this key.
        Prioritizes results according to DEFAULT_MODEL_CASCADE tiers, filters out blacklisted models,
        and caches results with thread safety.
        """
        with cls._discovery_lock:
            if cls._DISCOVERED_MODELS is not None and not force_refresh:
                return [m for m in cls._DISCOVERED_MODELS if not cls.is_model_blacklisted(m)]

        clean_key = (api_key or os.getenv('GEMINI_API_KEY') or "").strip()
        if not clean_key:
            try:
                import streamlit as st
                clean_key = (st.secrets.get('GEMINI_API_KEY') or "").strip()
            except Exception:
                pass

        if not clean_key or any(d in clean_key.lower() for d in ["your_", "placeholder", "actual_gemini", "enter_key"]):
            with cls._discovery_lock:
                return [m for m in DEFAULT_MODEL_CASCADE if not cls.is_model_blacklisted(m)]

        discovered: List[str] = []
        try:
            genai.configure(api_key=clean_key)
            for m in genai.list_models():
                methods = getattr(m, "supported_generation_methods", [])
                if "generateContent" in methods:
                    m_name = getattr(m, "name", "")
                    if m_name.startswith("models/"):
                        m_name = m_name[len("models/"):]
                    if m_name and m_name not in discovered:
                        discovered.append(m_name)
        except Exception as e:
            logger.warning(f"[GeminiClient] Dynamic model discovery failed: {e}. Falling back to default cascade.")
            with cls._discovery_lock:
                cls._DISCOVERED_MODELS = list(DEFAULT_MODEL_CASCADE)
                return [m for m in cls._DISCOVERED_MODELS if not cls.is_model_blacklisted(m)]

        # Prioritize:
        # 1. Models in DEFAULT_MODEL_CASCADE that were discovered (preserving Tier 1 -> 2 -> 3 order)
        # 2. Any additional discovered models supporting generateContent not in DEFAULT_MODEL_CASCADE
        prioritized: List[str] = []
        for default_m in DEFAULT_MODEL_CASCADE:
            if default_m in discovered and default_m not in prioritized:
                prioritized.append(default_m)

        for disc_m in discovered:
            if disc_m not in prioritized:
                prioritized.append(disc_m)

        if not prioritized:
            prioritized = list(DEFAULT_MODEL_CASCADE)

        with cls._discovery_lock:
            cls._DISCOVERED_MODELS = prioritized
            return [m for m in cls._DISCOVERED_MODELS if not cls.is_model_blacklisted(m)]

    def __init__(self, model_name: str = None, api_key: str = None):
        clean_key = (api_key or os.getenv('GEMINI_API_KEY') or "").strip()
        if not clean_key:
            try:
                import streamlit as st
                clean_key = (st.secrets.get('GEMINI_API_KEY') or "").strip()
            except Exception:
                pass

        if clean_key and any(d in clean_key.lower() for d in ["your_", "placeholder", "actual_gemini", "enter_key"]):
            clean_key = ""

        self.api_key = clean_key or None

        # 1. Dynamically discover or retrieve prioritized candidate pool
        discovered: List[str] = []
        if self.api_key:
            try:
                discovered = GeminiClient.discover_models(api_key=self.api_key)
            except Exception as e:
                logger.debug(f"[GeminiClient] Model discovery bypassed in init: {e}")

        base_pool = discovered if discovered else [m for m in DEFAULT_MODEL_CASCADE if not GeminiClient.is_model_blacklisted(m)]
        if not base_pool:
            base_pool = list(DEFAULT_MODEL_CASCADE)

        # 2. Select initial model candidate with exact precedence
        active_mgr = APIQuotaManager.get_active_model() if hasattr(APIQuotaManager, 'get_active_model') else None
        candidate = (
            model_name or 
            os.getenv('GEMINI_MODEL') or 
            GeminiClient.get_active_model() or 
            active_mgr or 
            base_pool[0]
        )
        if candidate:
            candidate = candidate.replace("models/", "").strip()

        # If candidate is blacklisted, disregard it and select top candidate from healthy pool
        if candidate and GeminiClient.is_model_blacklisted(candidate):
            logger.warning(f"[GeminiClient] Requested model '{candidate}' is blacklisted. Selecting next best candidate.")
            candidate = None

        if not candidate:
            candidate = base_pool[0]

        # 3. Assemble instance cascade
        self.model_cascade = [candidate] + [m for m in base_pool if m != candidate]
        self.current_model_index = 0
        self.model_name = self.model_cascade[self.current_model_index]
        self.model = None

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
            except Exception as e:
                logger.warning(f"[GeminiClient] genai configure error: {e}")

    def _get_next_model(self) -> Optional[str]:
        """
        Advances the instance to the next available, non-blacklisted fallback model.
        Decoupled from premature global state mutation.
        Global state is updated ONLY upon validated successful generation.
        """
        while self.current_model_index + 1 < len(self.model_cascade):
            self.current_model_index += 1
            candidate = self.model_cascade[self.current_model_index]

            if GeminiClient.is_model_blacklisted(candidate):
                logger.debug(f"[GeminiClient] Skipping blacklisted candidate: {candidate}")
                continue

            self.model_name = candidate
            if self.api_key:
                try:
                    self.model = genai.GenerativeModel(self.model_name)
                except Exception as e:
                    logger.warning(f"[GeminiClient] Failed to instantiate candidate '{self.model_name}': {e}")
            logger.warning(f"[GeminiClient] Switching instance to candidate fallback model: {self.model_name}")
            return self.model_name

        return None

    def _execute_with_resilience(self, is_json: bool, prompt: str, system_instruction: str = None) -> str:
        """
        Executes generate_content with SHA-256 two-tier caching, token-bucket rate pacing (<=12 RPM),
        token budgeting, dynamic model discovery, automatic 429 backoff / failover, and diagnostic preservation.
        """
        if not self.api_key:
            raise ValueError(
                "Gemini API Key is missing. Please enter and validate your Google Gemini API Key in the onboarding card or sidebar."
            )

        # 1. Check Two-Tier SHA-256 Response Cache
        cache_key = GeminiCache.compute_hash(self.model_name, system_instruction, prompt, is_json)
        cached_res = GeminiCache.get(cache_key)
        if cached_res:
            saved_tokens = (len(prompt) + len(cached_res)) // 4
            APIQuotaManager.record_cache_hit(saved_tokens=saved_tokens)
            logger.info(f"[GeminiClient] Serving from cache ({cache_key[:8]}...): 0ms latency, {saved_tokens} tokens saved.")
            return cached_res

        # 2. Token-Bucket Rate Pacer (<= 12 RPM, >= 2.0s interval)
        slept = APIQuotaManager.wait_for_slot()
        if slept > 0:
            logger.debug(f"[GeminiClient] Rate-pacer paused for {slept:.2f}s before API call.")

        # 3. Input Token Budgeting
        budgeted_prompt = sanitize_and_budget_prompt(prompt)

        generation_config = {
            'temperature': 0.2,
        }
        if is_json:
            generation_config['response_mime_type'] = 'application/json'

        diagnostic_errors: List[Dict[str, Any]] = []
        last_error = None
        max_model_switches = len(self.model_cascade)

        for _ in range(max_model_switches):
            current_model_name = self.model_name

            # Skip if blacklisted by another concurrent thread
            if GeminiClient.is_model_blacklisted(current_model_name):
                next_model = self._get_next_model()
                if not next_model:
                    break
                continue

            model = genai.GenerativeModel(
                model_name=current_model_name,
                system_instruction=system_instruction,
                generation_config=generation_config
            )

            for attempt in range(2):
                try:
                    response = model.generate_content(budgeted_prompt)
                    if response is None:
                        raise RuntimeError(f"Model '{current_model_name}' returned null response.")

                    response_text = response.text
                    if not response_text or not response_text.strip():
                        raise ValueError(f"Model '{current_model_name}' returned empty content or was filtered.")

                    # ==========================================================
                    # STRICT VALIDATION SUCCESS POINT
                    # Synchronize active model globally only after verified generation
                    # ==========================================================
                    self.model_name = current_model_name
                    GeminiClient.set_active_model(current_model_name)

                    # Cache successful result and record API quota telemetry
                    GeminiCache.put(cache_key, current_model_name, is_json, response_text)
                    total_tokens = (len(budgeted_prompt) + len(response_text)) // 4
                    APIQuotaManager.record_call(token_count=total_tokens)
                    return response_text

                except (ResourceExhausted, GoogleAPICallError, Exception) as e:
                    err_msg = str(e)
                    is_quota_error = (
                        isinstance(e, ResourceExhausted) or
                        "429" in err_msg or
                        "ResourceExhausted" in err_msg or
                        "quota" in err_msg.lower() or
                        "rate limit" in err_msg.lower()
                    )
                    is_model_unavailable = (
                        "404" in err_msg or
                        "not found" in err_msg.lower() or
                        "not supported" in err_msg.lower() or
                        "unsupported" in err_msg.lower()
                    )
                    is_transient_error = (
                        "503" in err_msg or "500" in err_msg or "502" in err_msg or "504" in err_msg or
                        "overloaded" in err_msg.lower() or "server error" in err_msg.lower() or
                        "connection" in err_msg.lower() or "timeout" in err_msg.lower() or
                        "remote disconnected" in err_msg.lower() or "try again later" in err_msg.lower()
                    )
                    is_safety_filtered = (
                        "response.parts" in err_msg or
                        "filtered" in err_msg.lower() or
                        "safety" in err_msg.lower()
                    )

                    last_error = e
                    diagnostic_errors.append({
                        "model": current_model_name,
                        "attempt": attempt + 1,
                        "error_type": type(e).__name__,
                        "error_message": err_msg,
                        "is_quota": is_quota_error,
                        "is_unavailable": is_model_unavailable,
                        "is_transient": is_transient_error
                    })

                    # If not a retryable quota, model-availability, or transient error, re-raise immediately
                    if not is_quota_error and not is_model_unavailable and not is_transient_error and not is_safety_filtered:
                        logger.error(f"[GeminiClient] Non-retryable error on model '{current_model_name}': {err_msg}")
                        raise e

                    # Model unavailable (404/unsupported) -> Add to class blacklist and immediately failover
                    if is_model_unavailable:
                        GeminiClient.blacklist_model(current_model_name)
                        logger.warning(
                            f"[GeminiClient] Model '{current_model_name}' is unavailable ({err_msg[:120]}). "
                            f"Blacklisted across threads. Failing over immediately..."
                        )
                        break

                    # Safety filter trigger -> Failover to next candidate in cascade
                    if is_safety_filtered:
                        logger.warning(f"[GeminiClient] Content filtered or empty on '{current_model_name}'. Failing over to next cascade model...")
                        break

                    # Transient server / network error (503 overloaded, 500, timeouts)
                    if is_transient_error:
                        if attempt == 0:
                            wait_t = 1.5 + random.uniform(0.2, 0.8)
                            logger.warning(f"[GeminiClient] Transient error on '{current_model_name}': {err_msg[:100]}. Backing off {wait_t:.1f}s before attempt 2...")
                            time.sleep(wait_t)
                            continue
                        else:
                            logger.warning(f"[GeminiClient] Transient error persisted on '{current_model_name}'. Failing over to next cascade model...")
                            break

                    # 429 Quota Exceeded -> Rate limit backoff calculation
                    delay = extract_retry_delay(err_msg, default=15.0)
                    jitter = random.uniform(0.5, 1.5)
                    total_cooldown = delay + jitter
                    logger.warning(
                        f"[GeminiClient] Model '{current_model_name}' hit quota limit (429). "
                        f"Cooldown: {total_cooldown:.1f}s (delay: {delay:.1f}s, jitter: {jitter:.2f}s). Attempt {attempt + 1}/2."
                    )

                    # If cooldown is brief (<= 8.0s) and on first attempt, sleep and retry once
                    if delay <= 8.0 and attempt == 0:
                        logger.info(f"[GeminiClient] Short quota delay ({delay:.1f}s <= 8.0s). Retrying '{current_model_name}' after {total_cooldown:.1f}s cooldown...")
                        time.sleep(total_cooldown)
                        continue
                    else:
                        # Otherwise, immediately failover to next model in cascade
                        logger.info(
                            f"[GeminiClient] Delay too long ({delay:.1f}s > 8.0s) or retry exhausted for '{current_model_name}'. "
                            f"Failing over to next cascade model..."
                        )
                        break

            # Switch instance to next candidate in cascade
            next_model = self._get_next_model()
            if not next_model:
                break
            logger.info(f"[GeminiClient] Failing over to model '{next_model}'...")

        # Diagnostic Error Preservation on Cascade Exhaustion
        if last_error:
            diag_lines = [
                f"- Model '{d['model']}' (Attempt {d['attempt']}): [{d['error_type']}] {d['error_message'][:150]}"
                for d in diagnostic_errors
            ]
            diag_summary = "\n".join(diag_lines)
            logger.error(
                f"[GeminiClient] All Gemini model fallbacks exhausted ({len(diagnostic_errors)} attempts failed):\n{diag_summary}"
            )
            raise RuntimeError(
                f"Failed to generate content: All Gemini model fallbacks exhausted.\n"
                f"Cascade Diagnostic Trace ({len(diagnostic_errors)} attempts across {len(self.model_cascade)} models):\n{diag_summary}"
            ) from last_error

        raise RuntimeError("Failed to generate content: All Gemini model fallbacks exhausted.")

    def generate_json(self, prompt: str, system_instruction: str = None) -> str:
        return self._execute_with_resilience(is_json=True, prompt=prompt, system_instruction=system_instruction)

    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        return self._execute_with_resilience(is_json=False, prompt=prompt, system_instruction=system_instruction)