"""
Backend test configuration.

Ensures backend application package
has priority during backend tests.
"""

from pathlib import Path
import sys


BACKEND_PATH = (
    Path(__file__)
    .resolve()
    .parents[1]
)


if str(BACKEND_PATH) in sys.path:
    sys.path.remove(
        str(BACKEND_PATH)
    )

sys.path.insert(
    0,
    str(BACKEND_PATH),
)