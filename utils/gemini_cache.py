import hashlib
import logging
import threading
from collections import OrderedDict
from typing import Optional
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)

class GeminiCache:
    """
    Two-Tier Deterministic Response Cache for Google Gemini API.
    L1: High-speed in-memory LRU cache (RAM).
    L2: Relational SQLite persistence in data/interviewiq.db.
    Provides instant (0 ms) responses for identical prompts, saving 100% of API tokens.
    Thread-safe implementation.
    """
    MAX_L1_CAPACITY: int = 500
    _lock: threading.Lock = threading.Lock()
    _l1_cache: OrderedDict = OrderedDict()

    @staticmethod
    def compute_hash(model_name: str, system_instruction: Optional[str], prompt: str, is_json: bool) -> str:
        """
        Computes a deterministic SHA-256 compound hash from generation parameters.
        """
        norm_model = (model_name or "").strip().lower()
        norm_inst = (system_instruction or "").strip()
        norm_prompt = (prompt or "").strip()
        raw_key = f"{norm_model}:{int(is_json)}:{norm_inst}:{norm_prompt}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @classmethod
    def get(cls, cache_key: str) -> Optional[str]:
        """
        Retrieves cached response text if present in L1 RAM or L2 SQLite cache.
        Promotes L2 hits into L1 for subsequent instant lookups.
        """
        if not cache_key:
            return None

        # 1. Check L1 Memory Cache
        with cls._lock:
            if cache_key in cls._l1_cache:
                # Move to end to maintain LRU ordering
                cls._l1_cache.move_to_end(cache_key)
                logger.debug(f"[GeminiCache] L1 RAM Hit: {cache_key[:12]}...")
                return cls._l1_cache[cache_key]

        # 2. Check L2 SQLite Cache
        try:
            db_res = DatabaseManager.get_api_cache_entry(cache_key)
            if db_res:
                logger.debug(f"[GeminiCache] L2 SQLite Hit: {cache_key[:12]}... (Promoting to L1)")
                with cls._lock:
                    cls._put_l1(cache_key, db_res)
                return db_res
        except Exception as e:
            logger.warning(f"[GeminiCache] L2 retrieval error: {e}")

        return None

    @classmethod
    def put(cls, cache_key: str, model_name: str, is_json: bool, response_text: str):
        """
        Stores generation response text into both L1 RAM and L2 SQLite cache.
        """
        if not cache_key or not response_text:
            return

        # Write to L1 RAM
        with cls._lock:
            cls._put_l1(cache_key, response_text)

        # Write to L2 SQLite
        try:
            DatabaseManager.save_api_cache_entry(cache_key, model_name, is_json, response_text)
        except Exception as e:
            logger.warning(f"[GeminiCache] L2 persistence error: {e}")

    @classmethod
    def _put_l1(cls, key: str, value: str):
        """Internal helper to write to L1 with LRU capacity enforcement (must be called with _lock)."""
        if key in cls._l1_cache:
            cls._l1_cache.move_to_end(key)
        cls._l1_cache[key] = value
        if len(cls._l1_cache) > cls.MAX_L1_CAPACITY:
            # Pop oldest entry
            cls._l1_cache.popitem(last=False)

    @classmethod
    def clear(cls):
        """Purges both L1 in-memory and L2 SQLite caches."""
        with cls._lock:
            cls._l1_cache.clear()
        try:
            DatabaseManager.clear_api_cache()
        except Exception as e:
            logger.warning(f"[GeminiCache] L2 clear error: {e}")
