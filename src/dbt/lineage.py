"""Build dependency graph and trace impact from changed models."""

from __future__ import annotations

from dataclasses import dataclass

from src.dbt.changes import ChangedModel
from src.dbt.manifest import DbtManifest


@dataclass
class ImpactResult:
    changed_model_id: str
    changed_model_name: str
    change_type: str
    downstream_models: list[str]  # names of affected downstream models
    downstream_count: int
    risk_level: str  # LOW, MEDIUM, HIGH


@dataclass
class ImpactReport:
    results: list[ImpactResult]
    total_downstream: int
    overall_risk: str

    @property
    def has_impact(self) -> bool:
        return self.total_downstream > 0


def assess_risk(downstream_count: int) -> str:
    """Determine risk level based on downstream impact count."""
    if downstream_count == 0:
        return "LOW"
    elif downstream_count <= 3:
        return "LOW"
    elif downstream_count <= 10:
        return "MEDIUM"
    else:
        return "HIGH"


def analyze_impact(
    manifest: DbtManifest, changed_models: list[ChangedModel]
) -> ImpactReport:
    """Analyze downstream impact of changed models."""
    results: list[ImpactResult] = []
    all_downstream: set[str] = set()

    for change in changed_models:
        downstream_ids = manifest.get_downstream(change.node.unique_id)
        # Filter to only model nodes (exclude tests, etc.)
        downstream_model_ids = {
            d for d in downstream_ids
            if d in manifest.models
        }
        downstream_names = [
            manifest.nodes[d].name for d in downstream_model_ids
        ]
        all_downstream.update(downstream_model_ids)

        results.append(ImpactResult(
            changed_model_id=change.node.unique_id,
            changed_model_name=change.node.name,
            change_type=change.change_type,
            downstream_models=sorted(downstream_names),
            downstream_count=len(downstream_model_ids),
            risk_level=assess_risk(len(downstream_model_ids)),
        ))

    total = len(all_downstream)
    overall_risk = assess_risk(total)

    return ImpactReport(
        results=results,
        total_downstream=total,
        overall_risk=overall_risk,
    )
