"""Calculate dbt test coverage metrics."""

from __future__ import annotations

from dataclasses import dataclass

from src.dbt.changes import ChangedModel
from src.dbt.manifest import DbtManifest


@dataclass
class ModelCoverage:
    model_name: str
    model_id: str
    test_count: int
    is_tested: bool


@dataclass
class CoverageReport:
    total_models: int
    tested_models: int
    untested_models: int
    coverage_pct: float
    changed_models_without_tests: list[str]  # names of changed models missing tests
    model_details: list[ModelCoverage]

    @property
    def has_gaps(self) -> bool:
        return len(self.changed_models_without_tests) > 0


def calculate_coverage(
    manifest: DbtManifest, changed_models: list[ChangedModel]
) -> CoverageReport:
    """Calculate test coverage for the entire project and flag untested changed models."""
    models = manifest.models
    model_details: list[ModelCoverage] = []
    tested_count = 0

    for model_id, model in models.items():
        tests = manifest.get_tests_for_model(model_id)
        is_tested = len(tests) > 0
        if is_tested:
            tested_count += 1

        model_details.append(ModelCoverage(
            model_name=model.name,
            model_id=model_id,
            test_count=len(tests),
            is_tested=is_tested,
        ))

    total = len(models)
    coverage_pct = (tested_count / total * 100) if total > 0 else 0.0

    # Identify changed models without tests
    changed_without_tests: list[str] = []
    for change in changed_models:
        if change.change_type == "deleted":
            continue
        tests = manifest.get_tests_for_model(change.node.unique_id)
        if not tests:
            changed_without_tests.append(change.node.name)

    return CoverageReport(
        total_models=total,
        tested_models=tested_count,
        untested_models=total - tested_count,
        coverage_pct=round(coverage_pct, 1),
        changed_models_without_tests=changed_without_tests,
        model_details=model_details,
    )
