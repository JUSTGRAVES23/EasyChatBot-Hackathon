"""
Deploy the EasyChatBot Cinema Intelligence Agent to Google Agent Runtime.

IMPORTANT DEPLOYMENT DESIGN
---------------------------
The runtime package is intentionally isolated.

The deployment package must contain these import roots at its archive root:

    adk_cinema/
    backend/
    src/
    g5_final_hackathon_demo.py

We deliberately pass RELATIVE paths to Agent Runtime from inside the
runtime package directory. This prevents Windows absolute paths such as:

    C:/AI Folder/EasyChatBot-Hackathon/.agent_runtime_package/...

from leaking into dependencies.tar.gz.

GEMINI DEPLOYMENT ARCHITECTURE
------------------------------
Agent Runtime deployment location:

    europe-west1

Gemini model execution location:

    eu

Google Cloud reserves:

    GOOGLE_CLOUD_PROJECT
    GOOGLE_CLOUD_LOCATION

Therefore neither variable is passed through Agent Runtime env_vars.

The Agent Runtime execution identity supplies the Google Cloud project
context through Application Default Credentials.

The application-specific Gemini location is supplied through:

    EASYCHATBOT_GEMINI_LOCATION=eu

Parallel authentication remains Secret Manager backed.

Workflow:

    1. python .\\build_runtime_package.py
    2. python .\\deploy_agent.py --preflight
    3. python .\\deploy_agent.py --dry-run
    4. python .\\deploy_agent.py

A real deployment is only performed after all local preflight checks pass.
"""

from __future__ import annotations

import argparse
import importlib
import os
import subprocess
from pathlib import Path

import vertexai
from vertexai import agent_engines

from adk_cinema.agent import root_agent


# ============================================================================
# Google Cloud configuration
# ============================================================================

PROJECT_ID = "demoeasyworld-2026"

# Agent Runtime resource location.
LOCATION = "europe-west1"

# Gemini model execution location.
GEMINI_LOCATION = "eu"

STAGING_BUCKET = (
    "gs://demoeasyworld-2026-agent-staging-eu"
)


# ============================================================================
# Local paths
# ============================================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parent
)

RUNTIME_PACKAGE = (
    ROOT.parent
    / "EasyChatBot-AgentRuntime"
)

RUNTIME_REQUIREMENTS = (
    ROOT
    / "adk_cinema"
    / "requirements-runtime.txt"
)


# ============================================================================
# Deployment metadata
# ============================================================================

DISPLAY_NAME = (
    "EasyChatBot Cinema Intelligence Agent"
)

DESCRIPTION = (
    "Hackathon cinema intelligence agent using Google ADK, "
    "Gemini, live Parallel research, learner memory, "
    "and personalisation."
)


# ============================================================================
# Required runtime files
# ============================================================================

REQUIRED_FILES = {
    "adk_cinema/__init__.py",
    "adk_cinema/agent.py",
    "adk_cinema/tools.py",
    "backend/conversation/conversation_request.py",
    "backend/memory/memory_service.py",
    "backend/providers/llm/llm_provider_factory.py",
    "backend/providers/parallel/parallel_client.py",
    "g5_final_hackathon_demo.py",
}


# ============================================================================
# Runtime deployment inputs
# ============================================================================

RELATIVE_DEPLOYMENT_INPUTS = (
    "./adk_cinema",
    "./backend",
    "./src",
    "./g5_final_hackathon_demo.py",
)


# ============================================================================
# Runtime environment
#
# GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION are reserved by
# Google Agent Runtime and MUST NOT be passed through env_vars.
#
# The Gemini model location therefore uses an application-specific
# variable.
# ============================================================================

DEPLOYMENT_ENV_VARS = {
    "EASYCHATBOT_GEMINI_LOCATION": GEMINI_LOCATION,
    "PARALLEL_API_KEY": {
        "secret": "parallel-api-key",
        "version": "latest",
    },
}


# ============================================================================
# Utility
# ============================================================================


def run_command(
    command: list[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a local command and return its completed process."""

    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


# ============================================================================
# Validation: Google configuration
# ============================================================================


def validate_configuration() -> None:
    """Validate static Google Cloud configuration."""

    if not PROJECT_ID.strip():
        raise RuntimeError(
            "PROJECT_ID is empty."
        )

    if not LOCATION.strip():
        raise RuntimeError(
            "Agent Runtime LOCATION is empty."
        )

    if not GEMINI_LOCATION.strip():
        raise RuntimeError(
            "GEMINI_LOCATION is empty."
        )

    if not STAGING_BUCKET.startswith(
        "gs://"
    ):
        raise RuntimeError(
            "STAGING_BUCKET must start with gs://"
        )

    if not DISPLAY_NAME.strip():
        raise RuntimeError(
            "DISPLAY_NAME is empty."
        )

    if (
        DEPLOYMENT_ENV_VARS.get(
            "EASYCHATBOT_GEMINI_LOCATION"
        )
        != GEMINI_LOCATION
    ):
        raise RuntimeError(
            "EASYCHATBOT_GEMINI_LOCATION does not match "
            "GEMINI_LOCATION."
        )

    if "GOOGLE_CLOUD_PROJECT" in DEPLOYMENT_ENV_VARS:
        raise RuntimeError(
            "GOOGLE_CLOUD_PROJECT is reserved and must not "
            "be passed through Agent Runtime env_vars."
        )

    if "GOOGLE_CLOUD_LOCATION" in DEPLOYMENT_ENV_VARS:
        raise RuntimeError(
            "GOOGLE_CLOUD_LOCATION is reserved and must not "
            "be passed through Agent Runtime env_vars."
        )

    if "GEMINI_API_KEY" in DEPLOYMENT_ENV_VARS:
        raise RuntimeError(
            "GEMINI_API_KEY must not be deployed."
        )

    if "PARALLEL_API_KEY" not in DEPLOYMENT_ENV_VARS:
        raise RuntimeError(
            "PARALLEL_API_KEY must be configured."
        )


# ============================================================================
# Validation: runtime requirements
# ============================================================================


def parse_requirement_name(
    line: str,
) -> str:
    """Extract a normalized Python package name."""

    value = line.strip()

    for separator in (
        "==",
        ">=",
        "<=",
        "~=",
        ">",
        "<",
        "!=",
        "[",
    ):
        value = value.split(
            separator,
            1,
        )[0]

    return value.strip().lower()


def read_runtime_requirements() -> list[str]:
    """Read and validate runtime requirements."""

    if not RUNTIME_REQUIREMENTS.exists():
        raise FileNotFoundError(
            "Missing runtime requirements file:\n"
            f"{RUNTIME_REQUIREMENTS}"
        )

    raw = (
        RUNTIME_REQUIREMENTS.read_bytes()
    )

    if raw.startswith(
        b"\xef\xbb\xbf"
    ):
        raise RuntimeError(
            "requirements-runtime.txt contains a UTF-8 BOM."
        )

    if raw.startswith(
        b"\xc3\xaf\xc2\xbb\xc2\xbf"
    ):
        raise RuntimeError(
            "requirements-runtime.txt contains a malformed UTF-8 BOM."
        )

    text = raw.decode(
        "utf-8"
    )

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
        and not line.lstrip().startswith("#")
    ]

    if not lines:
        raise RuntimeError(
            "requirements-runtime.txt is empty."
        )

    names = {
        parse_requirement_name(line)
        for line in lines
    }

    required = {
        "google-adk",
        "google-cloud-aiplatform",
        "google-auth",
        "parallel-web",
        "python-dotenv",
    }

    missing = (
        required
        - names
    )

    if missing:
        raise RuntimeError(
            "Runtime requirements missing:\n"
            + "\n".join(
                f"  - {item}"
                for item in sorted(missing)
            )
        )

    return lines


# ============================================================================
# Validation: installed local versions
# ============================================================================


def validate_local_versions() -> None:
    """
    Validate local serialization/runtime versions.
    """

    import cloudpickle
    import pydantic

    print()
    print(
        "Local serialization versions:"
    )

    print(
        f"  pydantic:    {pydantic.__version__}"
    )

    print(
        f"  cloudpickle: {cloudpickle.__version__}"
    )

    if (
        pydantic.__version__
        != "2.13.4"
    ):
        raise RuntimeError(
            "Unexpected local pydantic version. "
            f"Expected 2.13.4, got "
            f"{pydantic.__version__}"
        )

    if (
        cloudpickle.__version__
        != "3.1.2"
    ):
        raise RuntimeError(
            "Unexpected local cloudpickle version. "
            f"Expected 3.1.2, got "
            f"{cloudpickle.__version__}"
        )


# ============================================================================
# Validation: local imports
# ============================================================================


def validate_local_imports() -> None:
    """Verify required application modules can be imported."""

    modules = [
        "adk_cinema",
        "adk_cinema.agent",
        "adk_cinema.tools",
        "backend",
        "backend.memory.memory_service",
        "backend.providers.llm.llm_provider_factory",
        "backend.providers.parallel.parallel_client",
        "src",
        "src.ai_agents.live_intelligence_agent.handler",
        "src.challenge_engine.generator",
        "src.challenge_engine.gemini_content_generator",
        "src.providers.search_provider.parallel_adapter",
        "g5_final_hackathon_demo",
    ]

    print()
    print(
        "Validating local imports:"
    )

    for module_name in modules:

        importlib.import_module(
            module_name
        )

        print(
            f"  PASS {module_name}"
        )


# ============================================================================
# Validation: runtime package
# ============================================================================


def validate_runtime_package() -> list[Path]:
    """Validate the isolated runtime package."""

    if not RUNTIME_PACKAGE.exists():
        raise FileNotFoundError(
            "Runtime package does not exist:\n"
            f"{RUNTIME_PACKAGE}\n\n"
            "Build it first with:\n"
            "  python .\\build_runtime_package.py"
        )

    if not RUNTIME_PACKAGE.is_dir():
        raise RuntimeError(
            "Runtime package is not a directory: "
            f"{RUNTIME_PACKAGE}"
        )

    files = sorted(
        path
        for path in RUNTIME_PACKAGE.rglob("*")
        if path.is_file()
    )

    if not files:
        raise RuntimeError(
            "Runtime package is empty."
        )

    relative_files = {
        path.relative_to(
            RUNTIME_PACKAGE
        ).as_posix()
        for path in files
    }

    missing = (
        REQUIRED_FILES
        - relative_files
    )

    if missing:
        raise RuntimeError(
            "Required runtime files are missing:\n"
            + "\n".join(
                f"  - {item}"
                for item in sorted(missing)
            )
        )

    return files


# ============================================================================
# Validation: package roots
# ============================================================================


def validate_package_roots() -> None:
    """Ensure all Python import roots are physically present."""

    required_roots = (
        "adk_cinema",
        "backend",
        "src",
    )

    for name in required_roots:

        path = (
            RUNTIME_PACKAGE
            / name
        )

        if not path.is_dir():
            raise RuntimeError(
                "Missing runtime package root:\n"
                f"  {path}"
            )

        init_file = (
            path
            / "__init__.py"
        )

        if (
            name == "adk_cinema"
            and not init_file.exists()
        ):
            raise RuntimeError(
                "adk_cinema is missing __init__.py."
            )


# ============================================================================
# Validation: deployment inputs
# ============================================================================


def validate_relative_deployment_inputs() -> None:
    """
    Validate exact relative inputs handed to Agent Runtime.
    """

    print()
    print(
        "Validating Agent Runtime package inputs:"
    )

    for relative_input in (
        RELATIVE_DEPLOYMENT_INPUTS
    ):

        path = (
            RUNTIME_PACKAGE
            / relative_input.removeprefix(
                "./"
            )
        )

        if not path.exists():
            raise RuntimeError(
                "Deployment input does not exist:\n"
                f"  {relative_input}\n"
                f"  resolved: {path}"
            )

        print(
            f"  PASS {relative_input}"
        )


# ============================================================================
# Validation: forbidden artifacts
# ============================================================================


def validate_forbidden_artifacts(
    files: list[Path],
) -> None:
    """Reject secrets, databases, backups, logs and inspection files."""

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

    forbidden = []

    for path in files:

        name = path.name.lower()

        if any(
            pattern in name
            for pattern in forbidden_patterns
        ):
            forbidden.append(
                path
            )

    if forbidden:

        details = "\n".join(
            f"  - {path.relative_to(RUNTIME_PACKAGE)}"
            for path in forbidden
        )

        raise RuntimeError(
            "Forbidden deployment artifacts detected:\n"
            f"{details}"
        )


# ============================================================================
# Validation: deployment environment
# ============================================================================


def validate_deployment_environment() -> None:
    """
    Validate the environment supplied to Agent Runtime.

    GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION are reserved by
    Agent Runtime and therefore must not be passed through env_vars.

    Gemini uses EASYCHATBOT_GEMINI_LOCATION.

    Parallel uses a Secret Manager-backed API key.

    GEMINI_API_KEY is intentionally not deployed.
    """

    print()
    print(
        "Validating Agent Runtime environment:"
    )

    location = DEPLOYMENT_ENV_VARS.get(
        "EASYCHATBOT_GEMINI_LOCATION"
    )

    if location != GEMINI_LOCATION:
        raise RuntimeError(
            "EASYCHATBOT_GEMINI_LOCATION mismatch.\n"
            f"Expected: {GEMINI_LOCATION}\n"
            f"Actual:   {location}"
        )

    if "GOOGLE_CLOUD_PROJECT" in (
        DEPLOYMENT_ENV_VARS
    ):
        raise RuntimeError(
            "GOOGLE_CLOUD_PROJECT is reserved and must not "
            "be deployed."
        )

    if "GOOGLE_CLOUD_LOCATION" in (
        DEPLOYMENT_ENV_VARS
    ):
        raise RuntimeError(
            "GOOGLE_CLOUD_LOCATION is reserved and must not "
            "be deployed."
        )

    if "GEMINI_API_KEY" in (
        DEPLOYMENT_ENV_VARS
    ):
        raise RuntimeError(
            "GEMINI_API_KEY must not be deployed."
        )

    parallel_config = (
        DEPLOYMENT_ENV_VARS.get(
            "PARALLEL_API_KEY"
        )
    )

    if not isinstance(
        parallel_config,
        dict,
    ):
        raise RuntimeError(
            "PARALLEL_API_KEY must use a Secret Manager mapping."
        )

    if not parallel_config.get(
        "secret"
    ):
        raise RuntimeError(
            "PARALLEL_API_KEY Secret Manager secret is missing."
        )

    if not parallel_config.get(
        "version"
    ):
        raise RuntimeError(
            "PARALLEL_API_KEY Secret Manager version is missing."
        )

    print(
        "  PASS EASYCHATBOT_GEMINI_LOCATION"
    )

    print(
        f"    {location}"
    )

    print(
        "  PASS GOOGLE_CLOUD_PROJECT not injected"
    )

    print(
        "  PASS GOOGLE_CLOUD_LOCATION not injected"
    )

    print(
        "  PASS GEMINI_API_KEY not deployed"
    )

    print(
        "  PASS PARALLEL_API_KEY Secret Manager mapping"
    )


# ============================================================================
# Validation: Google Cloud environment
# ============================================================================


def validate_cloud_environment() -> None:
    """Verify local gcloud project configuration."""

    gcloud = (
        Path(
            os.environ.get(
                "LOCALAPPDATA",
                "",
            )
        )
        / "Google"
        / "Cloud SDK"
        / "google-cloud-sdk"
        / "bin"
        / "gcloud.cmd"
    )

    if not gcloud.exists():

        print()

        print(
            "WARNING: gcloud.cmd not found at expected path."
        )

        print(
            "Continuing because Vertex AI SDK authentication "
            "is already available."
        )

        return

    result = subprocess.run(
        [
            str(gcloud),
            "config",
            "get-value",
            "project",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    configured_project = (
        result.stdout.strip()
    )

    print()

    print(
        f"gcloud configured project: "
        f"{configured_project}"
    )

    if (
        configured_project
        and configured_project
        != PROJECT_ID
    ):
        raise RuntimeError(
            "gcloud project mismatch.\n"
            f"Expected: {PROJECT_ID}\n"
            f"Actual:   {configured_project}"
        )


# ============================================================================
# Deployment plan
# ============================================================================


def print_deployment_plan(
    files: list[Path],
) -> None:
    """Print a deterministic deployment plan."""

    print()
    print("=" * 70)
    print(
        "GOOGLE AGENT RUNTIME DEPLOYMENT PLAN"
    )
    print("=" * 70)

    print(
        f"Project:           {PROJECT_ID}"
    )

    print(
        f"Agent Runtime:     {LOCATION}"
    )

    print(
        f"Gemini location:   {GEMINI_LOCATION}"
    )

    print(
        f"Staging bucket:    {STAGING_BUCKET}"
    )

    print(
        f"Display name:      {DISPLAY_NAME}"
    )

    print()
    print(
        f"Requirements:      {RUNTIME_REQUIREMENTS}"
    )

    print(
        f"Runtime package:   {RUNTIME_PACKAGE}"
    )

    print()
    print(
        "Deployment archive roots:"
    )

    for item in (
        RELATIVE_DEPLOYMENT_INPUTS
    ):
        print(
            f"  - {item}"
        )

    print()
    print(
        f"Deployment files:  {len(files)}"
    )

    print()
    print(
        "Runtime environment:"
    )

    print(
        f"  - EASYCHATBOT_GEMINI_LOCATION = "
        f"{GEMINI_LOCATION}"
    )

    print(
        "  - GOOGLE_CLOUD_PROJECT = "
        "RUNTIME MANAGED"
    )

    print(
        "  - GOOGLE_CLOUD_LOCATION = "
        "RUNTIME MANAGED"
    )

    print(
        "  - GEMINI_API_KEY = NOT DEPLOYED"
    )

    print()
    print(
        "Secret-backed environment variables:"
    )

    print(
        "  - PARALLEL_API_KEY -> "
        "parallel-api-key:latest"
    )

    print()
    print(
        "Agent:"
    )

    print(
        f"  Name:   {root_agent.name}"
    )

    print(
        f"  Model:  {root_agent.model}"
    )

    print(
        f"  Tools:  {len(root_agent.tools)}"
    )

    print()
    print(
        "DEPLOYMENT_PLAN_VALIDATED"
    )

    print("=" * 70)


# ============================================================================
# Complete preflight
# ============================================================================


def run_preflight() -> list[Path]:
    """Run every local check possible before deployment."""

    print()
    print("=" * 70)
    print(
        "AGENT RUNTIME PRE-FLIGHT"
    )
    print("=" * 70)

    validate_configuration()

    requirements = (
        read_runtime_requirements()
    )

    print()
    print(
        "Runtime requirements:"
    )

    for requirement in requirements:
        print(
            f"  - {requirement}"
        )

    validate_local_versions()

    validate_local_imports()

    files = (
        validate_runtime_package()
    )

    validate_package_roots()

    validate_relative_deployment_inputs()

    validate_forbidden_artifacts(
        files
    )

    validate_deployment_environment()

    validate_cloud_environment()

    print_deployment_plan(
        files
    )

    print()
    print("=" * 70)
    print(
        "AGENT_RUNTIME_PREFLIGHT_PASS"
    )
    print("=" * 70)

    return files


# ============================================================================
# Deployment
# ============================================================================


def deploy() -> None:
    """Create the remote Agent Runtime deployment."""

    files = run_preflight()

    print()
    print(
        "Initialising Vertex AI..."
    )

    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET,
    )

    app = agent_engines.AdkApp(
        agent=root_agent,
    )

    print()
    print(
        "Starting Agent Runtime deployment..."
    )

    print()
    print(
        "CRITICAL:"
    )

    print(
        "The following paths are passed as RELATIVE paths"
    )

    print(
        "from the isolated runtime package directory:"
    )

    for item in (
        RELATIVE_DEPLOYMENT_INPUTS
    ):
        print(
            f"  {item}"
        )

    print()

    print(
        "Gemini execution configuration:"
    )

    print(
        f"  EASYCHATBOT_GEMINI_LOCATION = "
        f"{GEMINI_LOCATION}"
    )

    print(
        "  GOOGLE_CLOUD_PROJECT = RUNTIME MANAGED"
    )

    print(
        "  GOOGLE_CLOUD_LOCATION = RUNTIME MANAGED"
    )

    print(
        "  GEMINI_API_KEY = NOT DEPLOYED"
    )

    print()

    original_cwd = Path.cwd()

    try:

        os.chdir(
            RUNTIME_PACKAGE
        )

        print(
            "Agent Runtime packaging working directory:"
        )

        print(
            f"  {Path.cwd()}"
        )

        remote_agent = (
            agent_engines.create(
                agent_engine=app,
                requirements=str(
                    RUNTIME_REQUIREMENTS
                ),
                extra_packages=list(
                    RELATIVE_DEPLOYMENT_INPUTS
                ),
                env_vars=DEPLOYMENT_ENV_VARS,
                display_name=DISPLAY_NAME,
                description=DESCRIPTION,
            )
        )

    finally:

        os.chdir(
            original_cwd
        )

    print()
    print("=" * 70)
    print(
        "AGENT_RUNTIME_DEPLOYMENT_SUCCESS"
    )
    print("=" * 70)

    print()

    print(
        f"Resource: "
        f"{remote_agent.resource_name}"
    )

    print()

    print(
        "The Agent Runtime resource was created successfully."
    )


# ============================================================================
# CLI
# ============================================================================


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(
        description=(
            "Deploy the EasyChatBot Cinema Intelligence "
            "Agent to Google Agent Runtime."
        )
    )

    parser.add_argument(
        "--preflight",
        action="store_true",
        help=(
            "Run complete local validation without creating "
            "a remote resource."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Run validation and print the deployment plan "
            "without creating a remote resource."
        ),
    )

    args = parser.parse_args()

    if (
        args.preflight
        or args.dry_run
    ):

        run_preflight()

        print()

        if args.dry_run:

            print(
                "DRY RUN: no Agent Runtime resource was created."
            )

            print(
                "DEPLOYMENT_DRY_RUN_PASS"
            )

        return

    deploy()


if __name__ == "__main__":
    main()
