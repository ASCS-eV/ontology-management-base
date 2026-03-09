"""Canonicalize Turtle files for deterministic LinkML generator output.

rdflib's Turtle serializer assigns random blank-node identifiers on every run,
making ``gen-owl`` and ``gen-shacl`` output non-deterministic even for identical
input schemas.  This module re-serializes Turtle files through
``rdflib.compare.to_canonical_graph`` which uses graph isomorphism to assign
stable blank-node labels, then rebinds only the original prefixes.

The JSON-LD context generator is already deterministic when invoked with
``--no-metadata`` (which strips the ``generation_date`` timestamp), so no
post-processing is needed for ``.context.jsonld`` files.

Usage
-----
    python -m hooks.normalize_linkml_output <file.ttl> [<file.ttl> ...]

Each *file* is normalized **in-place**.
"""

from __future__ import annotations

import sys
from pathlib import Path

from rdflib import Graph
from rdflib.compare import to_canonical_graph


def normalize_turtle(path: Path) -> None:
    """Canonicalize blank nodes and re-serialize a Turtle file deterministically."""
    g = Graph()
    g.parse(path, format="turtle")
    orig_prefixes = dict(g.namespaces())

    cg = to_canonical_graph(g)

    out = Graph()
    for prefix, ns in orig_prefixes.items():
        out.bind(prefix, ns, override=True)
    for s, p, o in cg:
        out.add((s, p, o))

    result = out.serialize(format="turtle")
    path.write_text(result, encoding="utf-8", newline="\n")


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.ttl> [<file.ttl> ...]", file=sys.stderr)
        sys.exit(1)

    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"WARNING: {path} not found, skipping", file=sys.stderr)
            continue

        if not path.name.endswith(".ttl"):
            print(f"WARNING: not a Turtle file {path}, skipping", file=sys.stderr)
            continue

        normalize_turtle(path)


if __name__ == "__main__":
    main()
