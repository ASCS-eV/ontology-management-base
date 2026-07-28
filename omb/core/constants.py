#!/usr/bin/env python3
"""
Shared constants for ontology management tools.

FEATURE SET:
============
1. FAST_STORE - Auto-detected RDF store for performance optimization
2. Standard namespace prefixes used across the project
3. File extension constants for consistent pattern matching

USAGE:
======
    from omb.core.constants import FAST_STORE, EXTENSIONS

    # Use FAST_STORE when creating graphs
    graph = Graph(store=FAST_STORE)

STANDALONE TESTING:
==================
    python3 -m omb.core.constants [--test]

DEPENDENCIES:
=============
- oxrdflib (optional): For Oxigraph performance optimization

NOTES:
======
- FAST_STORE is 'oxigraph' if oxrdflib is installed, 'default' otherwise
- Oxigraph provides significantly better performance for large graphs
"""

# Try to import performance optimization
try:
    import oxrdflib  # noqa: F401

    FAST_STORE = "oxigraph"
except ImportError:
    FAST_STORE = "default"


# Standard file extensions
class Extensions:
    """Standard file extensions used in the project."""

    TURTLE = ".ttl"
    JSONLD = {".json", ".jsonld"}
    OWL = ".owl.ttl"
    SHACL = ".shacl.ttl"
    CONTEXT = ".context.jsonld"


# Standard namespace IRIs (for reference)
class Namespaces:
    """Common namespace IRIs used in the project."""

    RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    RDFS = "http://www.w3.org/2000/01/rdf-schema#"
    OWL = "http://www.w3.org/2002/07/owl#"
    XSD = "http://www.w3.org/2001/XMLSchema#"
    SHACL = "http://www.w3.org/ns/shacl#"
    SKOS = "http://www.w3.org/2004/02/skos/core#"


# Normative ASAM XML schemas.
#
# Single source of truth for where the vendored ASAM XSDs live. They used to sit in
# ``imports/OpenDrive/`` and ``imports/OpenScenario/``, which predates the
# ``asam-openx-standards`` submodule; the submodule is now the one place that pins ASAM
# deliverables, records their provenance (version, source URL, retrieval date, checksums)
# and states ASAM's ownership. Paths are repository-relative.
#
# These files are only present when the submodule is initialised:
#   git submodule update --init --recursive submodules/asam-openx-standards
ASAM_STANDARDS_ROOT = "submodules/asam-openx-standards/standards"
ASAM_OPENDRIVE_SCHEMA_DIR = f"{ASAM_STANDARDS_ROOT}/asam-opendrive/schema"
ASAM_OPENSCENARIO_SCHEMA_FILE = (
    f"{ASAM_STANDARDS_ROOT}/asam-openscenario-xml/schema/OpenSCENARIO.xsd"
)

#: Shown when a pinned ASAM schema is missing, so the fix is always in the error.
ASAM_SUBMODULE_HINT = (
    "Pinned ASAM schemas not found. Initialise the standards submodule: "
    "git submodule update --init --recursive submodules/asam-openx-standards"
)


# Validation-related constants
MAX_INFERENCE_ITERATIONS = 10  # Maximum iterations for RDFS inference


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Show core constants")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    args = parser.parse_args()

    if args.test:
        print("Running self-tests...")
        assert FAST_STORE in ("oxigraph", "default")
        assert Extensions.TURTLE == ".ttl"
        assert ".json" in Extensions.JSONLD
        assert Namespaces.RDF.startswith("http://")
        print("All tests passed!")
    else:
        print(f"FAST_STORE: {FAST_STORE}")
        print(f"Extensions.TURTLE: {Extensions.TURTLE}")
        print(f"Extensions.JSONLD: {Extensions.JSONLD}")
        print(f"MAX_INFERENCE_ITERATIONS: {MAX_INFERENCE_ITERATIONS}")
