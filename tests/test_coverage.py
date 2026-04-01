"""Tests for test coverage calculation."""

from pathlib import Path

from src.dbt.changes import ChangedModel
from src.dbt.coverage import calculate_coverage
from src.dbt.manifest import parse_manifest

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "manifest.json"


def test_coverage_overall():
    manifest = parse_manifest(FIXTURE_PATH)
    coverage = calculate_coverage(manifest, [])

    assert coverage.total_models == 7
    # stg_customers (2 tests), stg_orders (1 test), fct_orders (1 test), dim_customers (1 test) = 4 tested
    assert coverage.tested_models == 4
    assert coverage.untested_models == 3  # stg_payments, int_order_items, fct_revenue
    assert 50 < coverage.coverage_pct < 60  # 4/7 ≈ 57.1%


def test_coverage_flags_changed_models_without_tests():
    manifest = parse_manifest(FIXTURE_PATH)
    stg_payments = manifest.models["model.jaffle_shop.stg_payments"]
    changed = [ChangedModel(node=stg_payments, change_type="modified")]

    coverage = calculate_coverage(manifest, changed)

    assert coverage.has_gaps
    assert "stg_payments" in coverage.changed_models_without_tests


def test_coverage_no_gap_for_tested_model():
    manifest = parse_manifest(FIXTURE_PATH)
    stg_customers = manifest.models["model.jaffle_shop.stg_customers"]
    changed = [ChangedModel(node=stg_customers, change_type="modified")]

    coverage = calculate_coverage(manifest, changed)

    assert not coverage.has_gaps
    assert "stg_customers" not in coverage.changed_models_without_tests


def test_coverage_ignores_deleted_models():
    manifest = parse_manifest(FIXTURE_PATH)
    fct_revenue = manifest.models["model.jaffle_shop.fct_revenue"]
    changed = [ChangedModel(node=fct_revenue, change_type="deleted")]

    coverage = calculate_coverage(manifest, changed)

    # Deleted models should not be flagged as missing tests
    assert not coverage.has_gaps
