"""Tests for manifest.json parsing."""

import os
from pathlib import Path

from src.dbt.manifest import parse_manifest

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "manifest.json"


def test_parse_manifest_loads_models():
    manifest = parse_manifest(FIXTURE_PATH)
    assert len(manifest.models) == 7
    model_names = {m.name for m in manifest.models.values()}
    assert "stg_orders" in model_names
    assert "fct_orders" in model_names
    assert "dim_customers" in model_names


def test_parse_manifest_loads_tests():
    manifest = parse_manifest(FIXTURE_PATH)
    assert len(manifest.tests) == 5


def test_parse_manifest_loads_sources():
    manifest = parse_manifest(FIXTURE_PATH)
    assert len(manifest.sources) == 3


def test_get_model_by_file():
    manifest = parse_manifest(FIXTURE_PATH)
    model = manifest.get_model_by_file("models/staging/stg_orders.sql")
    assert model is not None
    assert model.name == "stg_orders"


def test_get_model_by_file_not_found():
    manifest = parse_manifest(FIXTURE_PATH)
    model = manifest.get_model_by_file("models/nonexistent.sql")
    assert model is None


def test_child_map_populated():
    manifest = parse_manifest(FIXTURE_PATH)
    children = manifest.child_map.get("model.jaffle_shop.stg_orders", [])
    assert "model.jaffle_shop.int_order_items" in children


def test_get_downstream():
    manifest = parse_manifest(FIXTURE_PATH)
    # stg_orders → int_order_items → fct_orders → dim_customers, fct_revenue
    downstream = manifest.get_downstream("model.jaffle_shop.stg_orders")
    downstream_names = {manifest.nodes[d].name for d in downstream if d in manifest.nodes}
    assert "int_order_items" in downstream_names
    assert "fct_orders" in downstream_names
    assert "dim_customers" in downstream_names
    assert "fct_revenue" in downstream_names


def test_get_downstream_with_depth():
    manifest = parse_manifest(FIXTURE_PATH)
    # depth=1 from stg_orders should only get int_order_items (+ tests)
    downstream = manifest.get_downstream("model.jaffle_shop.stg_orders", depth=1)
    model_downstream = {d for d in downstream if d.startswith("model.")}
    assert "model.jaffle_shop.int_order_items" in model_downstream
    assert "model.jaffle_shop.fct_orders" not in model_downstream


def test_get_tests_for_model():
    manifest = parse_manifest(FIXTURE_PATH)
    tests = manifest.get_tests_for_model("model.jaffle_shop.stg_customers")
    assert len(tests) == 2
    test_names = {t.name for t in tests}
    assert "not_null_stg_customers_customer_id" in test_names
    assert "unique_stg_customers_customer_id" in test_names


def test_get_tests_for_model_no_tests():
    manifest = parse_manifest(FIXTURE_PATH)
    tests = manifest.get_tests_for_model("model.jaffle_shop.stg_payments")
    assert len(tests) == 0


def test_manifest_not_found():
    try:
        parse_manifest("/nonexistent/manifest.json")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass
