"""
build_docs_and_docx.py
Convenience entrypoint executing build_docx_files.py to regenerate all Word (.docx) documentation dossiers.
"""
import os
import sys

if __name__ == "__main__":
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from build_docx_files import main
    main()
