"""Configuration from GitHub Action inputs (environment variables)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    manifest_path: str
    github_token: str
    project_dir: str
    fail_on_missing_tests: bool
    coverage_threshold: float

    # GitHub context (set automatically by GitHub Actions runner)
    github_repository: str  # owner/repo
    github_event_name: str  # pull_request, push, etc.
    pr_number: int | None
    github_sha: str

    @classmethod
    def from_env(cls) -> Config:
        pr_number = None
        event_name = os.environ.get("GITHUB_EVENT_NAME", "")

        if event_name == "pull_request":
            # PR number is in GITHUB_REF: refs/pull/<number>/merge
            ref = os.environ.get("GITHUB_REF", "")
            parts = ref.split("/")
            if len(parts) >= 3 and parts[1] == "pull":
                pr_number = int(parts[2])

        return cls(
            manifest_path=os.environ.get("INPUT_MANIFEST_PATH", "target/manifest.json"),
            github_token=os.environ.get("INPUT_GITHUB_TOKEN", ""),
            project_dir=os.environ.get("INPUT_PROJECT_DIR", "."),
            fail_on_missing_tests=os.environ.get("INPUT_FAIL_ON_MISSING_TESTS", "false").lower() == "true",
            coverage_threshold=float(os.environ.get("INPUT_COVERAGE_THRESHOLD", "0")),
            github_repository=os.environ.get("GITHUB_REPOSITORY", ""),
            github_event_name=event_name,
            pr_number=pr_number,
            github_sha=os.environ.get("GITHUB_SHA", ""),
        )
