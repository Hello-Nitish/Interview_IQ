import os
import sys
import runpy

# Ensure repository root is on sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Hugging Face Spaces Entry Point
# Directs Streamlit execution to the main application in frontend/app.py
if __name__ == "__main__":
    target_script = os.path.join(ROOT_DIR, "frontend", "app.py")
    runpy.run_path(target_script, run_name="__main__")
