from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT_STR = str(PROJECT_ROOT)


def pytest_sessionstart(session) -> None:
    """Keep the repository root authoritative for the top-level `app` package.

    The repository contains both:
        <root>/app
        <root>/backend/app

    Some tests import backend modules before the runtime entrypoint tests.
    Those imports can leave an `app` package from the backend tree in
    sys.modules, which breaks the intentional root-level
    `app.character_theme_system` dependency.

    The application code is not modified; this keeps the pytest process
    deterministic and isolated.
    """
    if PROJECT_ROOT_STR in sys.path:
        sys.path.remove(PROJECT_ROOT_STR)

    sys.path.insert(0, PROJECT_ROOT_STR)

    existing_app = sys.modules.get("app")

    if existing_app is not None:
        app_file = getattr(existing_app, "__file__", "") or ""
        app_path = Path(app_file).resolve() if app_file else None

        try:
            app_is_project_root = (
                app_path is not None
                and PROJECT_ROOT in app_path.parents
                and (PROJECT_ROOT / "app").resolve() in app_path.parents
            )
        except OSError:
            app_is_project_root = False

        if not app_is_project_root:
            modules_to_remove = [
                name
                for name in sys.modules
                if name == "app" or name.startswith("app.")
            ]

            for name in modules_to_remove:
                sys.modules.pop(name, None)