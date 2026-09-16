"""
Backend test configuration.

Ensures backend application package
has priority during backend tests and
loads repository environment configuration.
"""

from pathlib import Path
import sys

from dotenv import load_dotenv


BACKEND_PATH = (
    Path(__file__)
    .resolve()
    .parents[1]
)

PROJECT_ROOT = BACKEND_PATH.parent
ENV_FILE = PROJECT_ROOT / ".env"


if str(BACKEND_PATH) in sys.path:
    sys.path.remove(
        str(BACKEND_PATH)
    )

sys.path.insert(
    0,
    str(BACKEND_PATH),
)


load_dotenv(
    ENV_FILE,
)