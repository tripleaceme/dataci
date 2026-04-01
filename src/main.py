"""DataCI entry point — orchestrates all modules."""

from __future__ import annotations

import sys

from src.config import Config
from src.dbt.changes import detect_changed_models
from src.dbt.coverage import calculate_coverage
from src.dbt.lineage import analyze_impact
from src.dbt.manifest import parse_manifest
from src.report.composer import compose_report
from src.report.github import get_pull_request, post_or_update_comment


def run(config: Config) -> int:
    """Run the DataCI pipeline. Returns exit code (0=success, 1=failure)."""

    # 1. Parse manifest
    print(f"Parsing manifest: {config.manifest_path}")
    manifest = parse_manifest(config.manifest_path)
    print(f"  Found {len(manifest.models)} models, {len(manifest.tests)} tests")

    # 2. Detect changed models
    print("Detecting changed models...")
    changed_models = detect_changed_models(manifest)
    print(f"  {len(changed_models)} model(s) changed")

    if not changed_models:
        print("No dbt model changes detected. Skipping report.")
        return 0

    # 3. Analyze impact
    print("Analyzing downstream impact...")
    impact = analyze_impact(manifest, changed_models)
    print(f"  {impact.total_downstream} downstream model(s) affected (risk: {impact.overall_risk})")

    # 4. Calculate test coverage
    print("Calculating test coverage...")
    coverage = calculate_coverage(manifest, changed_models)
    print(f"  Coverage: {coverage.coverage_pct}% ({coverage.tested_models}/{coverage.total_models})")
    if coverage.changed_models_without_tests:
        print(f"  Missing tests: {', '.join(coverage.changed_models_without_tests)}")

    # 5. Compose report
    report = compose_report(changed_models, impact, coverage)

    # 6. Post to PR
    if config.pr_number and config.github_token:
        print(f"Posting report to PR #{config.pr_number}...")
        pr = get_pull_request(config.github_token, config.github_repository, config.pr_number)
        post_or_update_comment(pr, report)
    else:
        # Not in a PR context — print to stdout (useful for local testing)
        print("\n" + "=" * 60)
        print(report)
        print("=" * 60)

    # 7. Check failure conditions
    exit_code = 0

    if config.fail_on_missing_tests and coverage.changed_models_without_tests:
        print(f"\nFAILED: {len(coverage.changed_models_without_tests)} changed model(s) have no tests")
        exit_code = 1

    if config.coverage_threshold > 0 and coverage.coverage_pct < config.coverage_threshold:
        print(f"\nFAILED: Test coverage {coverage.coverage_pct}% is below threshold {config.coverage_threshold}%")
        exit_code = 1

    return exit_code


def main() -> None:
    config = Config.from_env()
    exit_code = run(config)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
