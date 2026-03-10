"""
Shared test fixtures for all test_and_evals modules.

Provides a pre-configured async FastAPI test client with authentication
and API-key checks bypassed, so tests can focus on the behavior under test
without spinning up real databases or token infrastructure.

Also registers the ``LogCapturePlugin`` which automatically writes per-test-file
log files (with a timestamp in the filename) into the corresponding
``tests/logs/`` directory after each pytest session.  Old logs are **never**
deleted — each run creates a new file.

Naming convention:
    test_{name}.py  →  tests/logs/test_output_{name}_YYYYMMDD_HHMMSS.log

Each model-specific LLM test file already contains the model in its
filename (e.g. ``test_prompt_injection_gpt4o_mini.py``), so the log
names are naturally distinct — no env-var detection needed.
"""

from __future__ import annotations

import asyncio
import os
import platform
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
import httpx

# ---------------------------------------------------------------------------
# Event-loop fixture (session-scoped so the app is created once)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for all async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Fake user returned by the mocked `get_current_user` dependency
# ---------------------------------------------------------------------------
FAKE_USER = {
    "user_id": "test-user-001",
    "role": "admin",
    "email": "test@example.com",
}


# ---------------------------------------------------------------------------
# Application-level fixture — patches auth before importing the app
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def test_app():
    """
    Yield the FastAPI ``app`` with authentication and API-key resolution
    stubbed out.

    * ``get_current_user`` → always returns ``FAKE_USER``
    * ``resolve_api_key``  → always returns a dummy key (patched at call sites)
    * ``validate_thread_ownership`` → no-op (patched at call sites)
    * ``db.connect / db.close`` → no-op (avoids real SQLite)
    * ``mcp_manager.initialize / cleanup`` → no-op
    """
    with (
        # Patch at the *import location* inside routes.generation — these are
        # plain function calls, NOT FastAPI dependencies.
        patch(
            "routes.generation.resolve_api_key",
            new=AsyncMock(return_value="sk-fake-key"),
        ),
        patch(
            "routes.generation.validate_thread_ownership",
            new=AsyncMock(return_value=None),
        ),
        # Lifespan-related services — prevent real DB/MCP connections
        patch("services.database.db.connect", new_callable=AsyncMock),
        patch("services.database.db.close", new_callable=AsyncMock),
        patch("services.mcp_client.mcp_manager.initialize", new_callable=AsyncMock),
        patch("services.mcp_client.mcp_manager.cleanup", new_callable=AsyncMock),
    ):
        # Import app *inside* the patch context so dependency overrides take effect
        from main import app

        # Disable the rate limiter so tests aren't throttled by slowapi
        from rate_limit import limiter

        limiter.enabled = False

        # Override the FastAPI dependency for get_current_user (this one IS a Depends())
        from services.auth_service import get_current_user

        async def fake_get_current_user():
            return FAKE_USER

        app.dependency_overrides[get_current_user] = fake_get_current_user

        yield app

        app.dependency_overrides.clear()
        limiter.enabled = True


@pytest_asyncio.fixture()
async def client(test_app):
    """
    Async HTTP client bound to the test application.

    Uses ``httpx.AsyncClient`` with ``ASGITransport`` so requests never
    hit the network — ideal for unit / integration tests.
    """
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as ac:
        yield ac


# ===========================================================================
# Log-capture plugin — writes per-file test logs with timestamps
# ===========================================================================


@dataclass
class _TestResult:
    """Stores the outcome of one test item."""

    nodeid: str
    outcome: str  # "passed", "failed", "skipped", "error"
    duration: float = 0.0
    longrepr: str = ""


@dataclass
class _FileResults:
    """Aggregated results for a single test file."""

    results: list[_TestResult] = field(default_factory=list)
    collect_errors: list[str] = field(default_factory=list)
    duration: float = 0.0


class LogCapturePlugin:
    """Pytest plugin that writes timestamped per-file log reports.

    Existing logs are **never** deleted — each run appends a new file with a
    ``_YYYYMMDD_HHMMSS`` suffix so every run is preserved.
    """

    def __init__(self) -> None:
        self.file_results: dict[str, _FileResults] = defaultdict(_FileResults)
        self.session_start: float = 0.0
        # Timestamp determined once at session start so all logs share it
        self._timestamp: str = ""

    # -- hooks ---------------------------------------------------------------

    def pytest_sessionstart(self, session: pytest.Session) -> None:
        self.session_start = time.time()
        self._timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def pytest_collectreport(self, report) -> None:
        """Capture collection-level errors (import errors, syntax errors)."""
        if report.failed:
            fspath = str(report.fspath) if report.fspath else "unknown"
            fr = self.file_results[fspath]
            longrepr = str(report.longrepr) if report.longrepr else ""
            fr.collect_errors.append(longrepr)

    def pytest_runtest_logreport(self, report) -> None:
        """Capture the *call* phase of each test (skip setup/teardown noise)."""
        if report.when != "call":
            return

        fspath = report.fspath
        longrepr = ""
        if report.failed and report.longrepr:
            longrepr = str(report.longrepr)

        tr = _TestResult(
            nodeid=report.nodeid,
            outcome=report.outcome,
            duration=report.duration,
            longrepr=longrepr,
        )
        self.file_results[fspath].results.append(tr)
        self.file_results[fspath].duration += report.duration

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        """Write one timestamped log file per test module after the session."""
        wall_time = time.time() - self.session_start
        for fspath, fr in self.file_results.items():
            self._write_log(fspath, fr, wall_time)

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _log_dir_for(test_file: str) -> Path:
        """Return the ``tests/logs/`` directory next to the test file."""
        return Path(test_file).resolve().parent / "logs"

    def _log_name_for(self, test_file: str) -> str:
        """Derive the log filename with a timestamp suffix.

        ``test_X.py`` → ``test_output_X_YYYYMMDD_HHMMSS.log``
        """
        stem = Path(test_file).stem
        name_part = stem[len("test_") :] if stem.startswith("test_") else stem
        return f"test_output_{name_part}_{self._timestamp}.log"

    def _write_log(self, test_file: str, fr: _FileResults, wall_time: float) -> None:
        logs_dir = self._log_dir_for(test_file)
        logs_dir.mkdir(parents=True, exist_ok=True)

        log_path = logs_dir / self._log_name_for(test_file)

        total = len(fr.results) + len(fr.collect_errors)
        passed = sum(1 for r in fr.results if r.outcome == "passed")
        failed = sum(1 for r in fr.results if r.outcome == "failed")
        skipped = sum(1 for r in fr.results if r.outcome == "skipped")
        errors = len(fr.collect_errors)

        lines: list[str] = []
        sep = "=" * 78

        # -- header --
        lines.append(sep)
        lines.append(" test session starts")
        lines.append(sep)
        lines.append(
            f"platform {sys.platform} -- Python {platform.python_version()}, "
            f"pytest-{pytest.__version__}"
        )
        lines.append(f"rootdir: {os.getcwd()}")
        lines.append(f"timestamp: {self._timestamp}")
        lines.append(f"collected {total} items")
        lines.append("")

        # -- per-test results --
        for r in fr.results:
            lines.append(f"{r.nodeid} {r.outcome.upper()}  [{r.duration:.2f}s]")

        # -- failures --
        if any(r.longrepr for r in fr.results):
            lines.append("")
            lines.append(f"{'=' * 30} FAILURES {'=' * 30}")
            for r in fr.results:
                if r.longrepr:
                    lines.append(f"___ {r.nodeid} ___")
                    lines.append(r.longrepr)
                    lines.append("")

        # -- collection errors --
        if fr.collect_errors:
            lines.append("")
            lines.append(f"{'=' * 30} ERRORS {'=' * 30}")
            for err in fr.collect_errors:
                lines.append(err)
                lines.append("")

        # -- summary --
        lines.append("")
        parts = []
        if passed:
            parts.append(f"{passed} passed")
        if failed:
            parts.append(f"{failed} failed")
        if skipped:
            parts.append(f"{skipped} skipped")
        if errors:
            parts.append(f"{errors} error(s)")

        summary = ", ".join(parts) if parts else "no tests ran"
        lines.append(sep)
        lines.append(f" {summary} in {fr.duration:.2f}s (wall {wall_time:.2f}s)")
        lines.append(sep)

        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def pytest_configure(config: pytest.Config) -> None:
    """Register the log-capture plugin globally for all test sections."""
    config.pluginmanager.register(LogCapturePlugin(), "log_capture_global")
