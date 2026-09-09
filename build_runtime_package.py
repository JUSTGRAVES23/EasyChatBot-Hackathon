"""Build a minimal isolated package for the cinema Agent Runtime deployment.\n\nThe generated package contains only the Python files required by the\nGoogle ADK cinema agent and its G5 workflow.\n\nThe package root is intentionally structured so that the following\nmodules are importable directly by the remote Agent Runtime:\n\n    adk_cinema\n    backend\n    src\n    g5_final_hackathon_demo\n\nThe generated deployment package is intentionally outside the source\nrepository so the Agent Runtime packaging process cannot accidentally\ninclude the repository .venv, .git metadata, or unrelated artifacts.\n\nNo .env files, databases, logs, backups, inspection artifacts, or\nother repository files are copied into the runtime package.\n"""

from __future__ import annotations

import ast
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent

# Keep the generated deployment artifact outside the source repository.
# This is deliberate: the Agent Runtime SDK archives extra_packages
# exactly as supplied, so the deployment root must not contain .venv,
# .git, or unrelated repository artifacts.
OUT = ROOT.parent / "EasyChatBot-AgentRuntime"


ENTRYPOINTS = [
    ROOT / "adk_cinema",
    ROOT / "g5_final_hackathon_demo.py",
]


def module_to_path(module: str) -> Path | None:
    """Resolve a local absolute Python module to its source path."""

    if not module:
        return None

    parts = module.split(".")

    candidates = [
        ROOT.joinpath(*parts).with_suffix(".py"),
        ROOT.joinpath(*parts, "__init__.py"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return None


def resolve_import(
    current_file: Path,
    module: str,
    level: int,
) -> Path | None:
    """Resolve absolute or relative local imports."""

    current_file = current_file.resolve()

    if level == 0:
        return module_to_path(module)

    try:
        relative_parts = current_file.relative_to(ROOT).parts
    except ValueError:
        return None

    current_parts = relative_parts[:-1]

    if level > len(current_parts) + 1:
        return None

    base_parts = current_parts[: len(current_parts) - level + 1]

    if module:
        full_module = ".".join(
            (*base_parts, module)
        )
    else:
        full_module = ".".join(base_parts)

    return module_to_path(full_module)


def discover_file(
    path: Path,
    discovered: set[Path],
) -> None:
    """Recursively discover local Python imports."""

    path = path.resolve()

    if path in discovered:
        return

    if not path.exists():
        return

    if path.suffix != ".py":
        return

    discovered.add(path)

    try:
        tree = ast.parse(
            path.read_text(
                encoding="utf-8-sig",
            ),
            filename=str(path),
        )
    except SyntaxError as exc:
        raise RuntimeError(
            f"Cannot parse {path}: {exc}"
        ) from exc

    for node in ast.walk(tree):

        # --------------------------------------------------------------
        # Absolute imports
        # --------------------------------------------------------------

        if isinstance(node, ast.Import):

            for alias in node.names:
                target = resolve_import(
                    path,
                    alias.name,
                    0,
                )

                if target:
                    discover_file(
                        target,
                        discovered,
                    )

        # --------------------------------------------------------------
        # from ... import ...
        # --------------------------------------------------------------

        elif isinstance(node, ast.ImportFrom):

            module = node.module or ""

            target = resolve_import(
                path,
                module,
                node.level,
            )

            if target:
                discover_file(
                    target,
                    discovered,
                )

            # Also resolve imported submodules when possible.
            if module:

                for alias in node.names:

                    if alias.name == "*":
                        continue

                    submodule = (
                        f"{module}.{alias.name}"
                    )

                    target = resolve_import(
                        path,
                        submodule,
                        node.level,
                    )

                    if target:
                        discover_file(
                            target,
                            discovered,
                        )


def copy_file(source: Path) -> None:
    """Copy a discovered source file into the isolated package."""

    source = source.resolve()

    relative = source.relative_to(ROOT)

    destination = (
        OUT / relative
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        source,
        destination,
    )


def validate_output_structure() -> None:
    """Validate the resulting package has the expected import roots."""

    required_files = {
        "adk_cinema/__init__.py",
        "adk_cinema/agent.py",
        "adk_cinema/tools.py",
        "g5_final_hackathon_demo.py",
    }

    actual_files = {
        path.relative_to(OUT).as_posix()
        for path in OUT.rglob("*")
        if path.is_file()
    }

    missing = (
        required_files - actual_files
    )

    if missing:
        raise RuntimeError(
            "Runtime package is missing required files:\n"
            + "\n".join(
                f"  - {item}"
                for item in sorted(missing)
            )
        )


def validate_forbidden_artifacts() -> None:
    """Reject secrets, databases, logs, backups, and inspection files."""

    forbidden_patterns = (
        ".env",
        ".db",
        ".sqlite",
        ".sqlite3",
        "backup",
        "inspection",
        ".log",
        ".pkl",
        ".tar",
        ".gz",
    )

    forbidden: list[Path] = []

    for path in OUT.rglob("*"):

        if not path.is_file():
            continue

        name = path.name.lower()

        if any(
            pattern in name
            for pattern in forbidden_patterns
        ):
            forbidden.append(path)

    if forbidden:

        details = "\n".join(
            f"  - {path.relative_to(OUT)}"
            for path in forbidden
        )

        raise RuntimeError(
            "Forbidden deployment artifacts detected:\n"
            f"{details}"
        )


def validate_output_isolation() -> None:
    """Validate that the output package is outside the source repository."""

    try:
        OUT.relative_to(ROOT)
    except ValueError:
        return

    raise RuntimeError(
        "Runtime package output must be outside the source repository:\n"
        f"  ROOT: {ROOT}\n"
        f"  OUT:  {OUT}"
    )


def main() -> None:
    """Build the isolated Agent Runtime package."""

    print()
    print("=" * 70)
    print("BUILDING ISOLATED AGENT RUNTIME PACKAGE")
    print("=" * 70)
    print()

    print("Repository root:")
    print(f"  {ROOT}")

    print()
    print("Output package:")
    print(f"  {OUT}")

    # ------------------------------------------------------------------
    # Validate the isolation boundary before touching the output.
    # ------------------------------------------------------------------

    validate_output_isolation()

    # ------------------------------------------------------------------
    # Clean previous package
    # ------------------------------------------------------------------

    if OUT.exists():

        print()
        print("Removing previous runtime package...")

        shutil.rmtree(OUT)

    OUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ------------------------------------------------------------------
    # Discover local Python dependencies
    # ------------------------------------------------------------------

    discovered: set[Path] = set()

    print()
    print("Discovering local Python dependencies...")

    for entrypoint in ENTRYPOINTS:

        if not entrypoint.exists():
            raise FileNotFoundError(
                f"Missing runtime entrypoint: {entrypoint}"
            )

        if entrypoint.is_dir():

            for path in entrypoint.rglob("*.py"):

                discover_file(
                    path,
                    discovered,
                )

        else:

            discover_file(
                entrypoint,
                discovered,
            )

    # ------------------------------------------------------------------
    # Copy files
    # ------------------------------------------------------------------

    print()
    print("Copying discovered files...")

    for path in sorted(discovered):

        copy_file(path)

    # ------------------------------------------------------------------
    # Validate package
    # ------------------------------------------------------------------

    validate_output_structure()
    validate_forbidden_artifacts()

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    print()
    print("=" * 70)
    print("AGENT_RUNTIME_PACKAGE_BUILD_PASS")
    print("=" * 70)

    print()
    print(
        f"Files included: {len(discovered)}"
    )

    print()
    print("Output:")
    print(f"  {OUT}")

    print()
    print("Top-level runtime modules:")

    top_level_items = sorted(
        path.name
        for path in OUT.iterdir()
    )

    for item in top_level_items:
        print(f"  - {item}")

    print()
    print("Included files:")

    for path in sorted(discovered):

        print(
            "  "
            + path.relative_to(ROOT).as_posix()
        )

    print()
    print(
        "Runtime package structure validated."
    )


if __name__ == "__main__":
    main()
