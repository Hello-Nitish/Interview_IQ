"""
DirectML Hardware Acceleration Engine.
Integrates Microsoft DirectML (via ONNX Runtime DirectML or torch-directml)
for DirectX 12 hardware acceleration across AMD, Intel, and NVIDIA GPUs/NPUs,
with automatic resilient CPU fallback.
"""

import logging
import platform
import sys
from typing import Any, Dict, List, Optional

logger = logging.getLogger("InterviewIQ.DirectML")


class DirectMLEngine:
    """Manages DirectML hardware detection, execution providers, and inference dispatch."""

    _instance: Optional["DirectMLEngine"] = None

    def __new__(cls) -> "DirectMLEngine":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.platform = platform.system()
        self.device_name = "CPU Fallback"
        self.provider = "CPUExecutionProvider"
        self.directml_available = False
        self.device_count = 0
        self.details: Dict[str, Any] = {}
        self._detect_hardware()

    def _detect_hardware(self) -> None:
        """Probes system for DirectML execution providers in ONNX Runtime or torch-directml."""
        # Check ONNX Runtime DirectML Provider
        try:
            import onnxruntime as ort  # type: ignore

            available_providers = ort.get_available_providers()
            if "DmlExecutionProvider" in available_providers:
                self.directml_available = True
                self.provider = "DmlExecutionProvider"
                self.device_name = "DirectX 12 GPU/NPU (DirectML)"
                self.device_count = 1
                self.details = {
                    "framework": "onnxruntime",
                    "version": getattr(ort, "__version__", "unknown"),
                    "providers": available_providers,
                }
                logger.info("DirectML detected via ONNX Runtime DmlExecutionProvider.")
                return
        except Exception as e:
            logger.debug("ONNX Runtime probe: %s", e)

        # Check torch-directml
        try:
            import torch_directml  # type: ignore

            if torch_directml.is_available():
                self.directml_available = True
                self.provider = "TorchDirectML"
                self.device_count = torch_directml.device_count()
                try:
                    self.device_name = torch_directml.device_name(0)
                except Exception:
                    self.device_name = "DirectX 12 Device"
                self.details = {
                    "framework": "torch-directml",
                    "device_count": self.device_count,
                    "device_name": self.device_name,
                }
                logger.info("DirectML detected via torch-directml (%s).", self.device_name)
                return
        except Exception as e:
            logger.debug("torch-directml probe: %s", e)

        # Fallback to standard CPU
        self.directml_available = False
        self.provider = "CPUExecutionProvider"
        self.device_name = "Host CPU (Hardware Acceleration Ready)"
        self.device_count = 1
        self.details = {
            "platform": self.platform,
            "architecture": platform.machine(),
            "python_version": sys.version.split()[0],
            "note": "Install onnxruntime-directml to activate DirectX 12 GPU acceleration.",
        }
        logger.info("DirectML not active; running in high-performance CPU mode.")

    def is_available(self) -> bool:
        """Returns True if DirectX 12 hardware acceleration via DirectML is active."""
        return self.directml_available

    def get_device_info(self) -> Dict[str, Any]:
        """Returns telemetry dictionary regarding hardware execution provider."""
        return {
            "directml_available": self.directml_available,
            "provider": self.provider,
            "device_name": self.device_name,
            "device_count": self.device_count,
            "platform": self.platform,
            "details": self.details,
        }

    def get_onnx_execution_providers(self) -> List[Any]:
        """Returns priority-ordered list of ONNX Runtime execution providers."""
        if self.directml_available and self.provider == "DmlExecutionProvider":
            return [
                ("DmlExecutionProvider", {"device_id": 0}),
                "CPUExecutionProvider",
            ]
        return ["CPUExecutionProvider"]


def get_directml_engine() -> DirectMLEngine:
    """Singleton getter for DirectMLEngine."""
    return DirectMLEngine()
