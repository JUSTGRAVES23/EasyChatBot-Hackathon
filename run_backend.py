import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = PROJECT_ROOT / "backend"

# Both package roots are intentional:
# - backend/ is the import root for the FastAPI app package (pp.*)
# - project root is the import root for the existing runtime (ackend.*)
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(1, str(PROJECT_ROOT))

from app.main import create_application

application = create_application()
