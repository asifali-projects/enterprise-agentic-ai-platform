"""Deterministic workflow-definition validation.

The workflow graph is validated before a version is persisted so that
execution never has to reason about malformed input: node ids must be unique,
every declared dependency must resolve to a known node, and the graph must be
acyclic (Kahn topological sort).
"""

from fastapi import HTTPException

from app.schemas.api import Definition


def validate_definition(definition: Definition) -> Definition:
    nodes = definition.nodes
    if not nodes:
        raise HTTPException(422, "Workflow definition must contain at least one node")

    ids = [n.id for n in nodes]
    unique = set(ids)
    if len(unique) != len(nodes):
        raise HTTPException(422, "Workflow node ids must be unique")

    indegree = {n.id: 0 for n in nodes}
    children: dict[str, list[str]] = {n.id: [] for n in nodes}
    for n in nodes:
        for dep in n.depends_on:
            if dep not in unique:
                raise HTTPException(422, f"Unknown dependency: {dep}")
            if dep == n.id:
                raise HTTPException(422, f"Node '{n.id}' cannot depend on itself")
            indegree[n.id] += 1
            children[dep].append(n.id)

    queue = [node_id for node_id, degree in indegree.items() if degree == 0]
    visited = 0
    while queue:
        current = queue.pop()
        visited += 1
        for child in children[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if visited != len(nodes):
        raise HTTPException(422, "Workflow contains a dependency cycle")
    return definition
