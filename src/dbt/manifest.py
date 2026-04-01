"""Parse dbt manifest.json into structured data."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DbtNode:
    unique_id: str
    name: str
    resource_type: str  # model, test, source, seed, snapshot, etc.
    package_name: str
    file_path: str  # original_file_path in manifest
    depends_on: list[str] = field(default_factory=list)
    description: str = ""
    materialized: str = ""
    schema_name: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class DbtManifest:
    nodes: dict[str, DbtNode]
    sources: dict[str, DbtNode]
    parent_map: dict[str, list[str]]  # node → its parents (upstream)
    child_map: dict[str, list[str]]  # node → its children (downstream)

    @property
    def models(self) -> dict[str, DbtNode]:
        return {k: v for k, v in self.nodes.items() if v.resource_type == "model"}

    @property
    def tests(self) -> dict[str, DbtNode]:
        return {k: v for k, v in self.nodes.items() if v.resource_type == "test"}

    def get_model_by_file(self, file_path: str) -> DbtNode | None:
        """Find a model node by its file path (relative to project root)."""
        for node in self.models.values():
            if node.file_path == file_path or file_path.endswith(node.file_path):
                return node
        return None

    def get_downstream(self, node_id: str, depth: int = -1) -> set[str]:
        """Get all downstream node IDs (recursive). depth=-1 means unlimited."""
        visited: set[str] = set()
        queue = [(node_id, 0)]

        while queue:
            current, current_depth = queue.pop(0)
            if current in visited:
                continue
            if current != node_id:
                visited.add(current)
            if depth != -1 and current_depth >= depth:
                continue
            for child in self.child_map.get(current, []):
                if child not in visited:
                    queue.append((child, current_depth + 1))

        return visited

    def get_tests_for_model(self, model_id: str) -> list[DbtNode]:
        """Get all test nodes that depend on a given model."""
        tests = []
        for child_id in self.child_map.get(model_id, []):
            node = self.nodes.get(child_id)
            if node and node.resource_type == "test":
                tests.append(node)
        return tests


def parse_manifest(manifest_path: str | Path) -> DbtManifest:
    """Parse a dbt manifest.json file into a DbtManifest."""
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"manifest.json not found at {path}")

    with open(path) as f:
        raw = json.load(f)

    nodes: dict[str, DbtNode] = {}
    sources: dict[str, DbtNode] = {}

    # Parse nodes (models, tests, seeds, snapshots, etc.)
    for unique_id, node_data in raw.get("nodes", {}).items():
        config = node_data.get("config", {})
        depends_on_nodes = node_data.get("depends_on", {}).get("nodes", [])

        node = DbtNode(
            unique_id=unique_id,
            name=node_data.get("name", ""),
            resource_type=node_data.get("resource_type", ""),
            package_name=node_data.get("package_name", ""),
            file_path=node_data.get("original_file_path", ""),
            depends_on=depends_on_nodes,
            description=node_data.get("description", ""),
            materialized=config.get("materialized", ""),
            schema_name=node_data.get("schema", ""),
            tags=node_data.get("tags", []),
        )
        nodes[unique_id] = node

    # Parse sources
    for unique_id, source_data in raw.get("sources", {}).items():
        source = DbtNode(
            unique_id=unique_id,
            name=source_data.get("name", ""),
            resource_type="source",
            package_name=source_data.get("package_name", ""),
            file_path=source_data.get("original_file_path", source_data.get("path", "")),
            description=source_data.get("description", ""),
            schema_name=source_data.get("schema", ""),
        )
        sources[unique_id] = source

    # Build parent and child maps
    parent_map: dict[str, list[str]] = raw.get("parent_map", {})
    child_map: dict[str, list[str]] = raw.get("child_map", {})

    # If maps not in manifest (older dbt versions), build from depends_on
    if not child_map:
        child_map = {}
        for unique_id, node in nodes.items():
            for parent_id in node.depends_on:
                child_map.setdefault(parent_id, []).append(unique_id)

    return DbtManifest(
        nodes=nodes,
        sources=sources,
        parent_map=parent_map,
        child_map=child_map,
    )
