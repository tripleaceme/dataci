"""Compose all module outputs into a single Markdown PR comment."""

from __future__ import annotations

from src.dbt.changes import ChangedModel
from src.dbt.coverage import CoverageReport
from src.dbt.lineage import ImpactReport

COMMENT_MARKER = "<!-- daterci-report -->"

RISK_EMOJI = {
    "LOW": ":white_check_mark:",
    "MEDIUM": ":warning:",
    "HIGH": ":rotating_light:",
}


def compose_report(
    changed_models: list[ChangedModel],
    impact: ImpactReport,
    coverage: CoverageReport,
) -> str:
    """Build the full Markdown report for the PR comment."""
    sections = [
        COMMENT_MARKER,
        "## :bar_chart: DaterCI Report\n",
        _changes_section(changed_models),
        _impact_section(impact),
        _coverage_section(coverage),
        _footer(),
    ]
    return "\n".join(sections)


def _changes_section(changed_models: list[ChangedModel]) -> str:
    if not changed_models:
        return "> No dbt model changes detected in this PR.\n"

    lines = ["### Changed Models\n"]
    lines.append("| Model | Change |")
    lines.append("|-------|--------|")
    for change in changed_models:
        icon = {"added": ":heavy_plus_sign:", "modified": ":pencil2:", "deleted": ":x:"}.get(
            change.change_type, ":pencil2:"
        )
        lines.append(f"| `{change.node.name}` | {icon} {change.change_type} |")
    lines.append("")
    return "\n".join(lines)


def _impact_section(impact: ImpactReport) -> str:
    if not impact.results:
        return ""

    emoji = RISK_EMOJI.get(impact.overall_risk, "")
    lines = [
        "### Impact Analysis\n",
        f"**{impact.total_downstream} downstream model(s)** affected "
        f"| Risk: {emoji} **{impact.overall_risk}**\n",
    ]

    # Show per-model impact if multiple models changed
    if len(impact.results) > 1:
        lines.append("<details>")
        lines.append("<summary>Impact by model</summary>\n")
        for result in impact.results:
            if result.downstream_models:
                lines.append(f"**`{result.changed_model_name}`** ({result.change_type}) "
                             f"→ {result.downstream_count} downstream:")
                for name in result.downstream_models:
                    lines.append(f"  - `{name}`")
                lines.append("")
            else:
                lines.append(f"**`{result.changed_model_name}`** ({result.change_type}) "
                             f"→ no downstream impact\n")
        lines.append("</details>\n")
    elif impact.results[0].downstream_models:
        result = impact.results[0]
        lines.append("<details>")
        lines.append("<summary>Affected models</summary>\n")
        for name in result.downstream_models:
            lines.append(f"- `{name}`")
        lines.append("\n</details>\n")

    return "\n".join(lines)


def _coverage_section(coverage: CoverageReport) -> str:
    lines = ["### Test Coverage\n"]

    # Coverage bar
    filled = int(coverage.coverage_pct / 10)
    bar = ":green_square:" * filled + ":white_large_square:" * (10 - filled)
    lines.append(f"{bar} **{coverage.coverage_pct}%** "
                 f"({coverage.tested_models}/{coverage.total_models} models tested)\n")

    # Flag changed models without tests
    if coverage.changed_models_without_tests:
        lines.append(":warning: **Changed models missing tests:**\n")
        for name in coverage.changed_models_without_tests:
            lines.append(f"- `{name}`")
        lines.append("")

    return "\n".join(lines)


def _footer() -> str:
    return (
        "---\n"
        "*Powered by [DaterCI](https://github.com/marketplace/actions/dataci) "
        "— CI/CD for analytics engineering*"
    )
