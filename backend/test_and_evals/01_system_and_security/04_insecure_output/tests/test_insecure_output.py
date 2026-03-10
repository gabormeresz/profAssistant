"""
Test 1.4 — Insecure Output Handling (OWASP LLM02)
=====================================================

**Objective:** Prove that malicious executable code in LLM-generated output
(whether from hallucination or successful prompt injection) cannot execute
in the client's browser.

**Defense model:**

1. **Backend transport layer** — The backend sends LLM output as JSON string
   values inside SSE ``complete`` events.  JSON encoding automatically escapes
   ``<``, ``>``, ``"``, etc.  The test verifies that XSS payloads survive the
   pipeline as inert string data.

2. **Frontend render layer** — React components render structured data via
   JSX interpolation (``{value}``), which auto-escapes HTML entities.  The
   test statically proves that no ``dangerouslySetInnerHTML`` usage exists
   in the project's source code, making JSX auto-escaping the sole render path.

Together, these two layers form a complete defence-in-depth against OWASP LLM02.

**Strategy:**

- **Part A (Backend Pipeline):** Patch ``run_course_outline_generator`` with a
  mock that returns a ``CourseOutline`` whose string fields are populated with
  XSS payloads from ``xss_payloads.json``.  Send a real HTTP request, read the
  SSE stream, parse the ``complete`` event, and assert the payloads are present
  as plain text (not stripped, not mangled — proving the frontend is expected
  to handle them).

- **Part B (Frontend Static Scan):** Recursively scan ``frontend/src/`` for
  ``dangerouslySetInnerHTML`` and ``v-html`` patterns.  Presence of either
  would create a code path that bypasses React's auto-escaping.

No real LLM calls, API keys, or browser runtime needed.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent
_PAYLOADS_FILE = _HERE / "xss_payloads.json"
_PROJECT_ROOT = _HERE.parents[
    4
]  # tests → 04_insecure_output → 01_system_and_security → test_and_evals → backend → project root
_FRONTEND_SRC = _PROJECT_ROOT / "frontend" / "src"

# ---------------------------------------------------------------------------
# Load payload dataset
# ---------------------------------------------------------------------------


def _load_payloads() -> list[dict]:
    with open(_PAYLOADS_FILE) as f:
        data = json.load(f)
    return data["payloads"]


XSS_PAYLOADS = _load_payloads()


# ---------------------------------------------------------------------------
# Mock generator: builds a CourseOutline with XSS payloads injected
# ---------------------------------------------------------------------------


def _build_poisoned_outline(payload: str) -> dict:
    """
    Return a CourseOutline-shaped dict with *payload* injected into every
    user-visible string field.  The structure mirrors the ``CourseOutline``
    schema shape (required keys and list sizes) so it is accepted by the
    SSE transport layer.  Note: Pydantic validation is bypassed because
    the mock replaces the generator, not the schema validator.
    """
    return {
        "course_title": f"Course: {payload}",
        "classes": [
            {
                "class_number": 1,
                "class_title": f"Class: {payload}",
                "learning_objectives": [
                    f"Objective A: {payload}",
                    f"Objective B: {payload}",
                ],
                "key_topics": [
                    f"Topic 1: {payload}",
                    f"Topic 2: {payload}",
                    f"Topic 3: {payload}",
                ],
                "activities_projects": [
                    f"Activity: {payload}",
                ],
            }
        ],
    }


async def _make_poisoned_generator(payload: str):
    """Async generator that mimics ``run_course_outline_generator``."""
    import uuid

    thread_id = str(uuid.uuid4())
    yield {"type": "thread_id", "thread_id": thread_id}
    yield {"type": "progress", "message_key": "overlay.generatingCourseOutline"}
    yield {"type": "complete", "data": _build_poisoned_outline(payload)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _payload_ids() -> list[str]:
    return [p["id"] for p in XSS_PAYLOADS]


def _payload_by_id(pid: str) -> str:
    return next(p["payload"] for p in XSS_PAYLOADS if p["id"] == pid)


async def _read_sse_complete_event(response) -> dict | None:
    """
    Read the raw SSE stream from an httpx response and return the parsed
    JSON from the first ``event: complete`` frame, or None.
    """
    current_event = ""
    async for line in response.aiter_lines():
        if line.startswith("event: "):
            current_event = line[7:].strip()
        elif line.startswith("data: ") and current_event == "complete":
            return json.loads(line[6:])
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Part A — Backend Pipeline: XSS payloads survive as inert JSON data
# ═══════════════════════════════════════════════════════════════════════════


class TestXSSPayloadTransport:
    """
    Each XSS payload is injected as LLM output via a mocked generator.
    The test asserts the SSE ``complete`` event contains the payload
    verbatim in the JSON — proving the backend does *not* silently strip
    it (the defense responsibility belongs to the frontend renderer).
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload_id", _payload_ids(), ids=_payload_ids())
    async def test_payload_present_in_sse_json(self, client, payload_id):
        """XSS payload {payload_id} is transported as inert JSON string data."""
        payload = _payload_by_id(payload_id)

        async def mock_generator(*args, **kwargs):
            async for event in _make_poisoned_generator(payload):
                yield event

        form = {
            "message": "Generate a course outline",
            "topic": "Security Testing",
            "number_of_classes": "1",
            "language": "English",
        }

        with patch(
            "routes.generation.run_course_outline_generator",
            side_effect=mock_generator,
        ):
            async with client.stream(
                "POST", "/course-outline-generator", data=form
            ) as resp:
                assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
                complete_data = await _read_sse_complete_event(resp)

        assert complete_data is not None, "No 'complete' SSE event received"

        # The payload must appear in every string field it was injected into
        assert (
            payload in complete_data["course_title"]
        ), f"Payload missing from course_title — backend may be stripping HTML"
        assert (
            payload in complete_data["classes"][0]["class_title"]
        ), f"Payload missing from class_title"
        assert any(
            payload in obj for obj in complete_data["classes"][0]["learning_objectives"]
        ), f"Payload missing from learning_objectives"
        assert any(
            payload in t for t in complete_data["classes"][0]["key_topics"]
        ), f"Payload missing from key_topics"
        assert any(
            payload in a for a in complete_data["classes"][0]["activities_projects"]
        ), f"Payload missing from activities_projects"

    @pytest.mark.asyncio
    async def test_json_round_trip_integrity(self, client):
        """
        Verify that an XSS payload containing HTML special characters
        survives the full SSE transport as a valid JSON string and can
        be recovered identically after ``json.loads`` — proving the
        serialization layer preserves payload fidelity without data loss.
        """
        payload = "<script>alert('XSS')</script>"

        async def mock_generator(*args, **kwargs):
            async for event in _make_poisoned_generator(payload):
                yield event

        form = {
            "message": "Generate a course outline",
            "topic": "Security Testing",
            "number_of_classes": "1",
            "language": "English",
        }

        with patch(
            "routes.generation.run_course_outline_generator",
            side_effect=mock_generator,
        ):
            async with client.stream(
                "POST", "/course-outline-generator", data=form
            ) as resp:
                raw_body = ""
                async for line in resp.aiter_lines():
                    raw_body += line + "\n"

        # 1. The complete event must exist in the stream
        assert "complete" in raw_body, "No complete event in SSE stream"

        # 2. Parse the complete event data from the raw stream
        parsed = None
        current_event = ""
        for line in raw_body.split("\n"):
            if line.startswith("event: "):
                current_event = line[7:].strip()
            elif line.startswith("data: ") and current_event == "complete":
                parsed = json.loads(line[6:])
                break

        assert parsed is not None, "Failed to parse complete event JSON"

        # 3. Round-trip integrity: the exact payload is recoverable
        assert parsed["course_title"] == f"Course: {payload}"
        assert parsed["classes"][0]["class_title"] == f"Class: {payload}"


# ═══════════════════════════════════════════════════════════════════════════
# Part B — Frontend Static Scan: no dangerouslySetInnerHTML in source
# ═══════════════════════════════════════════════════════════════════════════


class TestFrontendXSSDefense:
    """
    Static analysis of frontend source code to prove that React's built-in
    XSS protection (JSX auto-escaping) is the only render path for LLM data.

    If ``dangerouslySetInnerHTML`` is found in any source file, it means
    there exists a code path that could render raw HTML — breaking the
    defense model.
    """

    # Patterns that bypass React's auto-escaping
    DANGEROUS_PATTERNS = [
        "dangerouslySetInnerHTML",
        "v-html",  # Vue.js equivalent (shouldn't exist, but check)
        "__html",  # Part of dangerouslySetInnerHTML's API shape
        ".innerHTML",  # Direct DOM manipulation
        ".outerHTML",  # Direct DOM manipulation (similar to innerHTML)
        "document.write",  # Direct document injection
        "insertAdjacentHTML",  # DOM API for inserting raw HTML
    ]

    # Files/directories to exclude (third-party, build artifacts)
    EXCLUDE_DIRS = {"node_modules", "dist", "build", ".next", "coverage"}

    def _scan_source_files(self) -> list[tuple[str, int, str, str]]:
        """
        Walk frontend/src/ and return a list of (file, line_num, line, pattern)
        tuples for every dangerous pattern occurrence.
        """
        if not _FRONTEND_SRC.exists():
            pytest.skip(f"Frontend source not found at {_FRONTEND_SRC}")

        findings: list[tuple[str, int, str, str]] = []

        for root, dirs, files in os.walk(_FRONTEND_SRC):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]

            for filename in files:
                if not filename.endswith((".ts", ".tsx", ".js", ".jsx")):
                    continue

                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, _PROJECT_ROOT)

                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern in self.DANGEROUS_PATTERNS:
                            if pattern in line:
                                findings.append(
                                    (rel_path, line_num, line.strip(), pattern)
                                )

        return findings

    def test_no_dangerous_inner_html(self):
        """
        No source file in frontend/src/ uses dangerouslySetInnerHTML.

        This is the critical proof that React's JSX auto-escaping is the
        sole render path for all LLM-generated content, making script
        injection via structured output impossible.
        """
        findings = self._scan_source_files()

        if findings:
            report = "\n".join(
                f"  {f}:{ln} [{pat}]: {line[:120]}" for f, ln, line, pat in findings
            )
            pytest.fail(
                f"Found {len(findings)} dangerous pattern(s) in frontend source:\n{report}\n\n"
                f"Each occurrence creates a potential XSS vector that bypasses "
                f"React's auto-escaping. Remove or replace with a safe alternative."
            )

    def test_no_rehype_raw_plugin(self):
        """
        If react-markdown is used for rendering, the ``rehype-raw`` plugin
        must NOT be installed — it would allow raw HTML passthrough in
        markdown content, defeating React's escaping.
        """
        package_json = _PROJECT_ROOT / "frontend" / "package.json"
        if not package_json.exists():
            pytest.skip("package.json not found")

        with open(package_json) as f:
            pkg = json.load(f)

        all_deps = {}
        all_deps.update(pkg.get("dependencies", {}))
        all_deps.update(pkg.get("devDependencies", {}))

        assert "rehype-raw" not in all_deps, (
            "rehype-raw is installed as a dependency. This plugin allows raw HTML "
            "passthrough in react-markdown, which would create an XSS vector for "
            "LLM-generated content. Remove it or use rehype-sanitize instead."
        )

    def test_react_markdown_no_html_passthrough(self):
        """
        Scan for react-markdown usage with ``rehypePlugins`` containing
        ``rehypeRaw`` — even if rehype-raw isn't in package.json, someone
        might import it from a local file.
        """
        if not _FRONTEND_SRC.exists():
            pytest.skip(f"Frontend source not found at {_FRONTEND_SRC}")

        findings: list[tuple[str, int, str]] = []

        for root, dirs, files in os.walk(_FRONTEND_SRC):
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]

            for filename in files:
                if not filename.endswith((".ts", ".tsx", ".js", ".jsx")):
                    continue

                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, _PROJECT_ROOT)

                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if "rehypeRaw" in line or "rehype-raw" in line:
                            findings.append((rel_path, line_num, line.strip()))

        if findings:
            report = "\n".join(f"  {f}:{ln}: {line[:120]}" for f, ln, line in findings)
            pytest.fail(
                f"Found rehype-raw references in source:\n{report}\n\n"
                f"This enables raw HTML passthrough in react-markdown, "
                f"creating an XSS vector."
            )
