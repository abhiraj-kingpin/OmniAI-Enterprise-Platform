"""Lightweight knowledge graph: Claude extracts (entity, relation, entity)
triples from a collection's chunks, networkx stores/dedupes them.

Not Neo4j — there's no graph database running locally. networkx is an
in-memory graph library; this demonstrates the entity-relation extraction
and traversal pattern at prototype scale, not production graph storage.
"""

import json

import anthropic
import networkx as nx

from app.modules.rag.schemas import GraphEdge, GraphNode, GraphResponse
from app.modules.rag.store import Collection

MAX_CHUNKS_FOR_EXTRACTION = 15
MAX_CHARS_PER_BATCH = 6000

_TRIPLE_SCHEMA = {
    "type": "object",
    "properties": {
        "triples": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "relation": {"type": "string"},
                    "object": {"type": "string"},
                },
                "required": ["subject", "relation", "object"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["triples"],
    "additionalProperties": False,
}


async def _extract_triples(text: str) -> list[dict[str, str]]:
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-5",
        max_tokens=2048,
        system=(
            "Extract factual (subject, relation, object) triples from the "
            "text. Use short, canonical entity names (merge obvious aliases). "
            "Keep relations as short verb phrases. Return only clearly "
            "stated facts, not speculation."
        ),
        messages=[{"role": "user", "content": text}],
        output_config={"format": {"type": "json_schema", "schema": _TRIPLE_SCHEMA}},
    )
    text_block = next(b for b in response.content if b.type == "text")
    return json.loads(text_block.text)["triples"]


async def build_graph(collection: Collection, collection_name: str) -> GraphResponse:
    chunks = collection.chunks[:MAX_CHUNKS_FOR_EXTRACTION]

    batches: list[str] = []
    current, current_len = [], 0
    for chunk in chunks:
        current.append(chunk.text)
        current_len += len(chunk.text)
        if current_len >= MAX_CHARS_PER_BATCH:
            batches.append("\n\n".join(current))
            current, current_len = [], 0
    if current:
        batches.append("\n\n".join(current))

    graph = nx.DiGraph()
    for batch in batches:
        for triple in await _extract_triples(batch):
            subj, rel, obj = triple["subject"], triple["relation"], triple["object"]
            graph.add_node(subj)
            graph.add_node(obj)
            graph.add_edge(subj, obj, relation=rel)

    nodes = [GraphNode(id=n, label=n) for n in graph.nodes]
    edges = [
        GraphEdge(source=u, target=v, relation=data.get("relation", ""))
        for u, v, data in graph.edges(data=True)
    ]
    return GraphResponse(collection=collection_name, nodes=nodes, edges=edges)
