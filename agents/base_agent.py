import json
import re
from typing import Optional, Any, Dict
from utils.gemini_client import GeminiClient

class BaseAgent:
    def __init__(self, name: str, role: str, system_instruction: str = None, api_key: str = None):
        self.name = name
        self.role = role
        self.system_instruction = system_instruction
        self.client = GeminiClient(api_key=api_key)

    def run_json(self, prompt: str) -> dict:
        """
        Executes an LLM JSON generation prompt with a 6-stage progressive resilience parser:
        Stage 1: Direct JSON parsing
        Stage 2: Regex code-fence extraction (```json ... ```)
        Stage 3: Outermost bracket/brace slicer ({...} or [...])
        Stage 4: Trailing comma sanitizer
        Stage 5: Aggressive control-character & unescaped string repair
        Stage 6: Non-circular terminal ValueError
        """
        raw = self.client.generate_json(prompt, system_instruction=self.system_instruction)
        
        # If client or mock already returned a deserialized dict/list
        if isinstance(raw, (dict, list)):
            return raw

        if not isinstance(raw, str):
            raw = str(raw)

        text = raw.strip()

        # Stage 1: Direct JSON parsing
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass

        # Stage 2: Regex code-fence extraction
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fence_match:
            candidate = fence_match.group(1).strip()
            try:
                return json.loads(candidate)
            except (json.JSONDecodeError, TypeError):
                text = candidate  # Use unwrapped inner text for subsequent stages
        elif text.startswith("```"):
            candidate = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE).strip()
            if candidate.endswith("```"):
                candidate = candidate[:-3].strip()
            try:
                return json.loads(candidate)
            except (json.JSONDecodeError, TypeError):
                text = candidate

        # Stage 3: Outermost bracket slicer (objects {...} or arrays [...])
        start_brace = text.find('{')
        end_brace = text.rfind('}')
        start_bracket = text.find('[')
        end_bracket = text.rfind(']')

        candidate_slices = []
        if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
            candidate_slices.append((start_brace, text[start_brace:end_brace + 1]))
        if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
            candidate_slices.append((start_bracket, text[start_bracket:end_bracket + 1]))

        # Try parsing slices directly (outermost / longest first)
        candidate_slices.sort(key=lambda x: len(x[1]), reverse=True)
        for _, c_text in candidate_slices:
            try:
                return json.loads(c_text)
            except (json.JSONDecodeError, TypeError):
                pass

        # Stage 4 & 5: Sanitizer & control-character repairs across candidate slices
        candidates_to_sanitize = [c_text for _, c_text in candidate_slices] if candidate_slices else [text]
        for c_text in candidates_to_sanitize:
            # Stage 4: Trailing comma sanitizer
            sanitized = re.sub(r",\s*([\]\}])", r"\1", c_text)
            try:
                return json.loads(sanitized)
            except (json.JSONDecodeError, TypeError):
                pass

            # Stage 5: Aggressive control-character & unescaped string repair
            try:
                return json.loads(sanitized, strict=False)
            except (json.JSONDecodeError, TypeError):
                pass

            # Strip single-line comments // ... or /* ... */ if present
            without_comments = re.sub(r"//.*?\n", "\n", sanitized)
            without_comments = re.sub(r"/\*.*?\*/", "", without_comments, flags=re.DOTALL)
            without_comments = re.sub(r",\s*([\]\}])", r"\1", without_comments)
            try:
                return json.loads(without_comments, strict=False)
            except (json.JSONDecodeError, TypeError):
                pass

        # Stage 6: Non-circular terminal ValueError
        preview = (raw[:300] + "...") if len(raw) > 300 else raw
        raise ValueError(
            f"[{self.name}] Failed to parse valid JSON response after all 6 parsing stages. "
            f"Raw output snippet: {preview!r}"
        )

    def run_text(self, prompt: str) -> str:
        return self.client.generate_text(prompt, system_instruction=self.system_instruction)