"""Pytest bootstrap.

Ensures the ``app`` package is importable both from the repository root
(``backend/`` on the path) and from the container image where the backend
source is flattened into the working directory.
"""

import pathlib
import sys

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))
