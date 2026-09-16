from __future__ import annotations

import importlib
from pathlib import Path


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_backend_app_package_resolves_inside_backend() -> None:
    app = importlib.import_module("app")

    app_file = Path(app.__file__).resolve()
    expected_root = _backend_root() / "app"

    assert app_file.is_relative_to(expected_root), (
        "Backend package boundary violated: "
        f"'app' resolved to {app_file}, "
        f"expected a module under {expected_root}"
    )


def test_academy_activation_resolves_from_backend_app() -> None:
    module = importlib.import_module(
        "app.application.academy.academy_activation"
    )

    module_file = Path(module.__file__).resolve()
    expected_root = _backend_root() / "app"

    assert module_file.is_relative_to(expected_root), (
        "Academy activation resolved outside backend/app: "
        f"{module_file}"
    )