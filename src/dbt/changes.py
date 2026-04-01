"""Detect changed dbt models from git diff."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from src.dbt.manifest import DbtManifest, DbtNode


@dataclass
class ChangedModel:
    node: DbtNode
    change_type: str  # added, modified, deleted


def get_changed_files(base_ref: str = "origin/main") -> list[tuple[str, str]]:
    """Get list of changed files from git diff.

    Returns list of (status, file_path) tuples.
    Status: A=added, M=modified, D=deleted, R=renamed.
    """
    try:
        # Fetch the base ref to ensure we can diff against it
        subprocess.run(
            ["git", "fetch", "origin", base_ref.replace("origin/", "")],
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            ["git", "diff", "--name-status", "--diff-filter=AMDR", base_ref, "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        # Fallback: diff against the previous commit
        result = subprocess.run(
            ["git", "diff", "--name-status", "--diff-filter=AMDR", "HEAD~1", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )

    changed = []
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0][0]  # First char (R100 → R)
        file_path = parts[-1]  # Last element (handles renames: old → new)
        changed.append((status, file_path))

    return changed


def detect_changed_models(
    manifest: DbtManifest, base_ref: str = "origin/main"
) -> list[ChangedModel]:
    """Map changed SQL files to dbt model nodes."""
    changed_files = get_changed_files(base_ref)
    changed_models: list[ChangedModel] = []

    # Filter to SQL and YAML files in the dbt project
    dbt_extensions = {".sql", ".yml", ".yaml"}

    for status, file_path in changed_files:
        if not any(file_path.endswith(ext) for ext in dbt_extensions):
            continue

        # Try to match this file to a model in the manifest
        if file_path.endswith(".sql"):
            model = manifest.get_model_by_file(file_path)
            if model:
                change_type = {
                    "A": "added",
                    "M": "modified",
                    "D": "deleted",
                    "R": "modified",
                }.get(status, "modified")
                changed_models.append(ChangedModel(node=model, change_type=change_type))

    return changed_models
