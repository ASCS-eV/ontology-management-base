"""Canonicalize LinkML generator output for deterministic committed artifacts.

rdflib's Turtle serializer assigns random blank-node identifiers on every run,
making ``gen-owl`` and ``gen-shacl`` output non-deterministic even for identical
input schemas.  This module re-serializes Turtle files through
``rdflib.compare.to_canonical_graph`` which uses graph isomorphism to assign
stable blank-node labels, then rebinds only the original prefixes.

The LinkML JSON-LD context generator can still emit a trailing blank line at
EOF, which then causes ``pretty-format-json`` to rewrite the generated artifact
during ``make lint``. JSON-LD output is therefore normalised to a single LF
terminator with stable indentation too.

Usage
-----
    python -m hooks.normalize_linkml_output <file.ttl> [<file.ttl> ...]

Each *file* is normalized **in-place**.
"""

from __future__ import annotations

import json
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


def normalize_json_document(path: Path) -> None:
    """Rewrite JSON/JSON-LD with stable indentation and one trailing newline."""
    data = json.loads(path.read_text(encoding="utf-8"))
    result = json.dumps(data, indent=3, ensure_ascii=False) + "\n"
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

        if path.name.endswith(".ttl"):
            normalize_turtle(path)
        elif path.suffix.lower() in {".json", ".jsonld"}:
            normalize_json_document(path)
        else:
            print(
                f"WARNING: unsupported file type for normalization {path}, skipping",
                file=sys.stderr,
            )
            continue


if __name__ == "__main__":
    main()
