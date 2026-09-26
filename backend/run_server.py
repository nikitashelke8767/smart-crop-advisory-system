"""
Run script for Smart Crop Advisory backend.
Sets up sys.path so both 'backend.x' and bare 'utils', 'services' imports work.
"""
import sys
import os
from pathlib import Path

# Add both the project root AND backend directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # smart-crop-advisory-system/
BACKEND_DIR = Path(__file__).resolve().parent          # backend/

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(BACKEND_DIR)],
    )
