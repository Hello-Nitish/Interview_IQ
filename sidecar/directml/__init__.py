"""
DirectML Hardware Acceleration Package.
Provides DirectX 12 hardware acceleration via ONNX Runtime DirectML / Torch DirectML
with seamless CPU fallback.
"""
from sidecar.directml.engine import DirectMLEngine, get_directml_engine

__all__ = ["DirectMLEngine", "get_directml_engine"]
