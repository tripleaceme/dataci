"""Tests for impact analysis / lineage tracing."""

from pathlib import Path

from src.dbt.changes import ChangedModel
from src.dbt.lineage import ImpactReport, analyze_impact, assess_risk
from src.dbt.manifest import parse_manifest

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "manifest.json"


def test_assess_risk_levels():
    assert assess_risk(0) == "LOW"
    assert assess_risk(2) == "LOW"
    assert assess_risk(5) == "MEDIUM"
    assert assess_risk(15) == "HIGH"


def test_analyze_impact_single_staging_model():
    manifest = parse_manifest(FIXTURE_PATH)
    stg_orders = manifest.models["model.jaffle_shop.stg_orders"]
    changed = [ChangedModel(node=stg_orders, change_type="modified")]

    impact = analyze_impact(manifest, changed)

    assert impact.has_impact
    assert impact.total_downstream >= 3  # int_order_items, fct_orders, dim_customers, fct_revenue
    assert impact.overall_risk in ("MEDIUM", "HIGH")
    assert len(impact.results) == 1
    assert "fct_orders" in impact.results[0].downstream_models


def test_analyze_impact_leaf_model():
    manifest = parse_manifest(FIXTURE_PATH)
    fct_revenue = manifest.models["model.jaffle_shop.fct_revenue"]
    changed = [ChangedModel(node=fct_revenue, change_type="modified")]

    impact = analyze_impact(manifest, changed)

    assert impact.total_downstream == 0
    assert impact.overall_risk == "LOW"


def test_analyze_impact_multiple_models():
    manifest = parse_manifest(FIXTURE_PATH)
    stg_orders = manifest.models["model.jaffle_shop.stg_orders"]
    stg_customers = manifest.models["model.jaffle_shop.stg_customers"]
    changed = [
        ChangedModel(node=stg_orders, change_type="modified"),
        ChangedModel(node=stg_customers, change_type="modified"),
    ]

    impact = analyze_impact(manifest, changed)

    assert len(impact.results) == 2
    assert impact.has_impact


def test_analyze_impact_no_changes():
    manifest = parse_manifest(FIXTURE_PATH)
    impact = analyze_impact(manifest, [])

    assert not impact.has_impact
    assert impact.total_downstream == 0
    assert impact.overall_risk == "LOW"
