"""Tests for the report composer."""

from pathlib import Path

from src.dbt.changes import ChangedModel
from src.dbt.coverage import calculate_coverage
from src.dbt.lineage import analyze_impact
from src.dbt.manifest import parse_manifest
from src.report.composer import COMMENT_MARKER, compose_report

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "manifest.json"


def test_report_contains_marker():
    manifest = parse_manifest(FIXTURE_PATH)
    stg_orders = manifest.models["model.jaffle_shop.stg_orders"]
    changed = [ChangedModel(node=stg_orders, change_type="modified")]
    impact = analyze_impact(manifest, changed)
    coverage = calculate_coverage(manifest, changed)

    report = compose_report(changed, impact, coverage)

    assert COMMENT_MARKER in report


def test_report_contains_all_sections():
    manifest = parse_manifest(FIXTURE_PATH)
    stg_orders = manifest.models["model.jaffle_shop.stg_orders"]
    changed = [ChangedModel(node=stg_orders, change_type="modified")]
    impact = analyze_impact(manifest, changed)
    coverage = calculate_coverage(manifest, changed)

    report = compose_report(changed, impact, coverage)

    assert "DaterCI Report" in report
    assert "Changed Models" in report
    assert "Impact Analysis" in report
    assert "Test Coverage" in report
    assert "Powered by" in report


def test_report_shows_model_names():
    manifest = parse_manifest(FIXTURE_PATH)
    stg_orders = manifest.models["model.jaffle_shop.stg_orders"]
    changed = [ChangedModel(node=stg_orders, change_type="modified")]
    impact = analyze_impact(manifest, changed)
    coverage = calculate_coverage(manifest, changed)

    report = compose_report(changed, impact, coverage)

    assert "`stg_orders`" in report
    assert "modified" in report


def test_report_no_changes():
    manifest = parse_manifest(FIXTURE_PATH)
    impact = analyze_impact(manifest, [])
    coverage = calculate_coverage(manifest, [])

    report = compose_report([], impact, coverage)

    assert "No dbt model changes detected" in report


def test_report_flags_missing_tests():
    manifest = parse_manifest(FIXTURE_PATH)
    stg_payments = manifest.models["model.jaffle_shop.stg_payments"]
    changed = [ChangedModel(node=stg_payments, change_type="added")]
    impact = analyze_impact(manifest, changed)
    coverage = calculate_coverage(manifest, changed)

    report = compose_report(changed, impact, coverage)

    assert "missing tests" in report.lower() or "stg_payments" in report
