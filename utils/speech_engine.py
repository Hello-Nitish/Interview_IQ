"""
Google Local NLP Speech Processing Engine for InterviewIQ.
Implements free local speech-to-text (STT) via Google's endpoint with
acoustic pre-processing, noise calibration, multi-hypothesis domain rescoring,
and natural cadence text-to-speech (TTS) synthesis.
"""

import io
import math
import os
import wave
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

from utils.domain_vocabulary import DomainVocabularyCorrector


class GoogleLocalSpeechEngine:
    """
    Enhanced Google Local NLP Speech Processing Engine.
    Provides robust acoustic inspection, dynamic ambient noise calibration,
    multi-hypothesis confidence rescoring via DomainVocabularyCorrector,
    and prosody-aware browser TTS generation.
    """

    SUPPORTED_LANGUAGES = {
        "en-US": "English (United States)",
        "en-IN": "English (India)",
        "en-GB": "English (United Kingdom)",
        "en-AU": "English (Australia)"
    }

    @classmethod
    def assess_audio_quality(cls, audio_bytes: bytes) -> Dict[str, Any]:
        """
        Inspects raw audio bytes (WAV/PCM) to evaluate signal health,
        duration, RMS amplitude, silence ratio, and potential clipping.
        Uses pure Python standard library and NumPy (zero C-dependencies).
        """
        if not audio_bytes or len(audio_bytes) < 44:
            return {
                "valid": False,
                "error": "Empty or incomplete audio header",
                "duration_seconds": 0.0,
                "rms_amplitude": 0.0,
                "is_silent": True,
                "is_clipped": False,
                "sample_rate": 0,
                "channels": 0
            }

        try:
            with wave.open(io.BytesIO(audio_bytes), 'rb') as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                sample_rate = wav_file.getframerate()
                num_frames = wav_file.getnframes()
                duration = round(num_frames / float(sample_rate), 2) if sample_rate > 0 else 0.0

                raw_data = wav_file.readframes(num_frames)
                if not raw_data:
                    return {
                        "valid": False,
                        "error": "No frame data found",
                        "duration_seconds": 0.0,
                        "rms_amplitude": 0.0,
                        "is_silent": True,
                        "is_clipped": False,
                        "sample_rate": sample_rate,
                        "channels": channels
                    }

                # Convert to numpy array according to bit depth
                if sample_width == 2:  # 16-bit PCM
                    dtype = np.int16
                    max_possible = 32767.0
                elif sample_width == 1:  # 8-bit PCM
                    dtype = np.uint8
                    max_possible = 128.0
                elif sample_width == 4:  # 32-bit PCM
                    dtype = np.int32
                    max_possible = 2147483647.0
                else:
                    dtype = np.int16
                    max_possible = 32767.0

                audio_samples = np.frombuffer(raw_data, dtype=dtype)
                if audio_samples.size == 0:
                    return {
                        "valid": True,
                        "duration_seconds": duration,
                        "rms_amplitude": 0.0,
                        "is_silent": True,
                        "is_clipped": False,
                        "sample_rate": sample_rate,
                        "channels": channels
                    }

                # Calculate RMS amplitude
                rms = float(np.sqrt(np.mean(audio_samples.astype(np.float64) ** 2)))
                peak = float(np.max(np.abs(audio_samples)))

                # Detect silence: RMS < 0.5% of max possible dynamic range
                is_silent = (rms / max_possible) < 0.005
                # Detect clipping: Peak amplitude >= 99% of max dynamic range
                is_clipped = (peak / max_possible) >= 0.99

                # Normalized SNR estimate in dB
                snr_db = round(20 * math.log10(max(rms, 1.0) / max(1.0, max_possible * 0.001)), 1)

                return {
                    "valid": True,
                    "duration_seconds": duration,
                    "rms_amplitude": round(rms, 2),
                    "peak_amplitude": round(peak, 2),
                    "snr_db": snr_db,
                    "is_silent": is_silent,
                    "is_clipped": is_clipped,
                    "sample_rate": sample_rate,
                    "channels": channels
                }
        except Exception as e:
            # Fallback for non-standard or raw formats
            return {
                "valid": True,
                "byte_size": len(audio_bytes),
                "duration_seconds": round(len(audio_bytes) / 32000.0, 2),
                "rms_amplitude": 500.0,
                "is_silent": len(audio_bytes) < 1000,
                "is_clipped": False,
                "sample_rate": 16000,
                "channels": 1,
                "warning": f"Audio format parsing note: {str(e)}"
            }

    @classmethod
    def transcribe_audio_bytes(cls, audio_bytes: bytes, language: str = "en-US", rescore_domain: bool = True) -> Dict[str, Any]:
        """
        Transcribes audio bytes using Google Local Speech Recognition endpoint.
        Upgrades include:
          1. Acoustic signal inspection & silence guard.
          2. Dynamic ambient noise calibration.
          3. Multi-hypothesis candidate extraction and confidence evaluation (`show_all=True`).
          4. Domain phonetic post-correction for specialized business & tech terms.
          5. Support for localized English accents (e.g., 'en-IN', 'en-US', 'en-GB').
        """
        if not audio_bytes:
            return {
                "success": False,
                "transcript": "",
                "error": "No audio data provided",
                "engine": "Google Local NLP (SpeechRecognition)"
            }

        # Step 1: Assess audio signal health
        quality = cls.assess_audio_quality(audio_bytes)
        if quality.get("is_silent") and quality.get("duration_seconds", 0) > 0.5:
            return {
                "success": False,
                "transcript": "",
                "error": "Audio appears silent or microphone gain is too low. Please speak closer to the mic.",
                "audio_quality": quality,
                "engine": "Google Local NLP (SpeechRecognition)"
            }

        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()

            # Dynamic Energy & Noise Tuning
            recognizer.dynamic_energy_threshold = True
            recognizer.energy_threshold = 300
            recognizer.pause_threshold = 0.8

            with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
                # Calibrate for ambient room noise if audio is sufficiently long
                if quality.get("duration_seconds", 1.0) >= 0.5:
                    recognizer.adjust_for_ambient_noise(source, duration=min(0.3, quality.get("duration_seconds", 1.0) / 2.0))
                audio_data = recognizer.record(source)

                # Query Google Speech endpoint with full alternative hypothesis tree
                try:
                    raw_result = recognizer.recognize_google(audio_data, language=language, show_all=True)
                except Exception:
                    # Fallback to standard recognition call
                    raw_result = recognizer.recognize_google(audio_data, language=language)

                # Parse multi-hypothesis candidates
                candidates: List[Dict[str, Any]] = []
                best_transcript = ""
                confidence = 0.85  # Default baseline confidence when Google returns flat string

                if isinstance(raw_result, dict) and "alternative" in raw_result:
                    alternatives = raw_result["alternative"]
                    for alt in alternatives:
                        trans = alt.get("transcript", "").strip()
                        conf = float(alt.get("confidence", 0.85))
                        if trans:
                            candidates.append({"transcript": trans, "confidence": conf})

                    if candidates:
                        # Multi-hypothesis rescoring: combine confidence with domain lexicon relevance
                        scored_candidates = []
                        for c in candidates:
                            c_text = c["transcript"]
                            c_conf = c["confidence"]
                            domain_density = DomainVocabularyCorrector.calculate_domain_density(c_text)
                            # Composite rank: ASR confidence + boost for domain term recognition
                            composite_rank = c_conf + (min(domain_density, 30.0) / 100.0)
                            scored_candidates.append((composite_rank, c_text, c_conf))

                        scored_candidates.sort(key=lambda x: x[0], reverse=True)
                        best_transcript = scored_candidates[0][1]
                        confidence = scored_candidates[0][2]
                elif isinstance(raw_result, str):
                    best_transcript = raw_result.strip()
                elif isinstance(raw_result, list) and raw_result:
                    best_transcript = str(raw_result[0]).strip()

                if not best_transcript:
                    return {
                        "success": False,
                        "transcript": "",
                        "error": "No intelligible speech detected. Please articulate clearly.",
                        "audio_quality": quality,
                        "engine": "Google Local NLP (SpeechRecognition)"
                    }

                # Step 4: Apply Domain Phonetic Correction
                corrections_applied = []
                domain_terms = []
                domain_density = 0.0

                if rescore_domain:
                    domain_result = DomainVocabularyCorrector.correct_transcription(best_transcript)
                    final_transcript = domain_result["corrected"]
                    corrections_applied = domain_result["corrections_applied"]
                    domain_terms = domain_result["domain_terms_found"]
                    domain_density = domain_result["domain_density_pct"]
                else:
                    final_transcript = best_transcript

                return {
                    "success": True,
                    "transcript": final_transcript,
                    "raw_transcript": best_transcript,
                    "confidence": round(confidence, 3),
                    "alternatives_count": len(candidates),
                    "corrections_applied": corrections_applied,
                    "domain_terms_found": domain_terms,
                    "domain_density_pct": domain_density,
                    "language": language,
                    "audio_quality": quality,
                    "engine": "Google Local NLP (SpeechRecognition + DomainCorrector)"
                }

        except Exception as e:
            error_msg = str(e)
            if "UnknownValueError" in type(e).__name__:
                error_msg = "Could not understand audio. Please check mic input and background noise."
            elif "RequestError" in type(e).__name__:
                error_msg = "Google Speech Recognition service is unreachable. Check network connectivity."

            return {
                "success": False,
                "transcript": "",
                "error": error_msg,
                "audio_quality": quality,
                "engine": "Google Local NLP (SpeechRecognition)"
            }

    @classmethod
    def generate_browser_speech_html(
        cls,
        text_to_speak: str,
        auto_play: bool = True,
        language: str = "en-US",
        rate: float = 0.95,
        pitch: float = 1.0
    ) -> str:
        """
        Generates lightweight HTML5 JavaScript using the browser's native Web Speech API
        (window.speechSynthesis) with Google English voices.
        Includes prosody rate calibration (0.95x for executive clarity), pitch tuning,
        and locale voice binding (en-US, en-IN, en-GB).
        """
        # Escape quotes and normalize whitespace
        escaped_text = text_to_speak.replace('"', '\\"').replace("\n", " ").replace("\r", "")
        auto_call = "speakText();" if auto_play else ""

        # Map language tag to label
        lang_label = cls.SUPPORTED_LANGUAGES.get(language, "English")

        return f"""
        <div style='display:inline-flex; align-items:center; gap:8px;'>
          <button onclick="speakText()" style="
            background: #2563EB;
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            padding: 7px 15px;
            font-size: 0.85rem;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25);
            transition: all 0.2s ease;
          ">
            🔊 Listen to Interviewer ({lang_label})
          </button>
        </div>
        <script>
          function speakText() {{
            if ('speechSynthesis' in window) {{
              window.speechSynthesis.cancel();
              const utterance = new SpeechSynthesisUtterance("{escaped_text}");
              utterance.rate = {rate};
              utterance.pitch = {pitch};
              utterance.lang = "{language}";
              
              // Select preferred Google or localized natural system voice
              const voices = window.speechSynthesis.getVoices();
              const targetLang = "{language}".toLowerCase();
              let selectedVoice = voices.find(v => v.lang.toLowerCase() === targetLang && v.name.includes("Google"));
              if (!selectedVoice) {{
                selectedVoice = voices.find(v => v.lang.toLowerCase().startsWith("{language[:2]}") && v.name.includes("Google"));
              }}
              if (!selectedVoice) {{
                selectedVoice = voices.find(v => v.lang.toLowerCase() === targetLang);
              }}
              if (selectedVoice) {{
                utterance.voice = selectedVoice;
              }}
              
              window.speechSynthesis.speak(utterance);
            }}
          }}
          {auto_call}
        </script>
        """
