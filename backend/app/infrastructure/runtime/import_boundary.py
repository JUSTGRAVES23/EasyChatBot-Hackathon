from __future__ import annotations

from pathlib import Path


class ImportBoundaryError(RuntimeError):
    """Raised when the backend app package resolves outside backend/app."""


def validate_backend_app_import_boundary() -> Path:
    import app

    backend_root = Path(__file__).resolve().parents[3]
    expected_root = backend_root / "app"
    app_file = Path(app.__file__).resolve()

    if not app_file.is_relative_to(expected_root):
        raise ImportBoundaryError(
            "Backend import boundary violated: "
            f"'app' resolved to {app_file}; "
            f"expected a module under {expected_root}."
        )

    return app_file