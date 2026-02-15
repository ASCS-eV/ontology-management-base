#!/usr/bin/env python3
"""
JSON-LD Context Generator - Generates context files from OWL/SHACL artifacts.

This script parses OWL ontologies and SHACL shapes to generate JSON-LD context
files that enable compact JSON-LD instance syntax. It extracts datatype
information from SHACL property constraints and maps them to JSON-LD type
coercion rules.

FEATURE SET:
============
1. generate_context - Generate JSON-LD context from OWL+SHACL for a domain
2. generate_all_contexts - Generate contexts for all domains in artifacts/
3. extract_property_datatypes - Extract datatypes from SHACL shapes
4. test_context_roundtrip - Verify context produces equivalent RDF triples

USAGE:
======
    # Generate context for a specific domain
    python -m src.tools.utils.context_generator --domain manifest

    # Generate contexts for all domains
    python -m src.tools.utils.context_generator --all

    # Test round-trip equivalence
    python -m src.tools.utils.context_generator --test-roundtrip manifest

STANDALONE TESTING:
==================
    python -m src.tools.utils.context_generator --test

DEPENDENCIES:
=============
- rdflib: RDF graph parsing and manipulation

NOTES:
======
- This is a transitional tool bridging to full LinkML adoption
- Context files enable compact JSON-LD syntax without explicit @value/@type
- The generator extracts datatypes from sh:datatype, sh:class, sh:nodeKind
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from rdflib import RDF, Graph, Namespace, URIRef
from rdflib.namespace import OWL, XSD

from src.tools.core.constants import FAST_STORE, Extensions
from src.tools.core.logging import get_logger
from src.tools.utils.file_collector import write_if_changed

logger = get_logger(__name__)

# Constants
ROOT_DIR = Path(__file__).parent.parent.parent.parent.resolve()
ARTIFACTS_DIR = ROOT_DIR / "artifacts"

# Namespaces
SH = Namespace("http://www.w3.org/ns/shacl#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

# XSD datatype mappings for JSON-LD context
XSD_TYPE_MAP = {
    str(XSD.string): None,  # Default, no coercion needed
    str(XSD.integer): "xsd:integer",
    str(XSD.int): "xsd:int",
    str(XSD.float): "xsd:float",
    str(XSD.double): "xsd:double",
    str(XSD.decimal): "xsd:decimal",
    str(XSD.boolean): "xsd:boolean",
    str(XSD.date): "xsd:date",
    str(XSD.dateTime): "xsd:dateTime",
    str(XSD.time): "xsd:time",
    str(XSD.anyURI): "xsd:anyURI",
    str(XSD.nonNegativeInteger): "xsd:nonNegativeInteger",
    str(XSD.positiveInteger): "xsd:positiveInteger",
}


def parse_graph(file_path: Path) -> Optional[Graph]:
    """Parse an RDF file into a graph."""
    if not file_path.exists():
        logger.warning("File not found: %s", file_path)
        return None

    g = Graph(store=FAST_STORE)
    try:
        g.parse(file_path, format="turtle")
        return g
    except Exception as e:
        logger.error("Failed to parse %s: %s", file_path, e)
        return None


def extract_ontology_iri(owl_graph: Graph) -> Optional[str]:
    """Extract the ontology IRI from an OWL graph."""
    for s in owl_graph.subjects(RDF.type, OWL.Ontology):
        return str(s)
    return None


def extract_prefix_from_iri(iri: str) -> str:
    """Extract a short prefix name from an ontology IRI."""
    # Handle trailing slash or hash
    iri = iri.rstrip("/#")
    # Get the last path segment
    parts = iri.split("/")
    # Find the domain part (e.g., 'manifest' from '.../manifest/v5')
    for i, part in enumerate(parts):
        if part.startswith("v") and part[1:].isdigit():
            return parts[i - 1] if i > 0 else part
    return parts[-1]


def extract_property_datatypes(
    shacl_graph: Graph, domain_prefix: str, domain_iri: str
) -> Dict[str, Dict[str, Any]]:
    """
    Extract property definitions and datatypes from SHACL shapes.

    Returns a dict mapping property local names to their context definitions:
    {
        "filePath": {"@id": "manifest:filePath", "@type": "xsd:anyURI"},
        "mimeType": {"@id": "manifest:mimeType"},
        "hasFileMetadata": {"@id": "manifest:hasFileMetadata", "@type": "@id"},
    }
    """
    properties: Dict[str, Dict[str, Any]] = {}

    # Find all property constraints in SHACL shapes
    for shape in shacl_graph.subjects(RDF.type, SH.NodeShape):
        # Get properties defined on this shape
        for prop_node in shacl_graph.objects(shape, SH.property):
            path = shacl_graph.value(prop_node, SH.path)
            if not path:
                continue

            path_str = str(path)

            # Only process properties from this domain
            if not path_str.startswith(domain_iri):
                # Also handle external properties we want to map (skos:note, sh:conformsTo)
                if path_str.startswith(str(SKOS)):
                    local_name = path_str.replace(str(SKOS), "")
                    properties[local_name] = {"@id": f"skos:{local_name}"}
                elif path_str.startswith(str(SH)):
                    local_name = path_str.replace(str(SH), "")
                    if local_name == "conformsTo":
                        properties[local_name] = {
                            "@id": "sh:conformsTo",
                            "@type": "@id",
                            "@container": "@set",
                        }
                continue

            # Extract local name
            local_name = path_str.replace(domain_iri, "").lstrip("/")

            # Determine the type coercion
            datatype = shacl_graph.value(prop_node, SH.datatype)
            node_kind = shacl_graph.value(prop_node, SH.nodeKind)
            node_ref = shacl_graph.value(prop_node, SH.node)
            class_ref = shacl_graph.value(prop_node, SH["class"])

            prop_def: Dict[str, Any] = {"@id": f"{domain_prefix}:{local_name}"}

            if datatype:
                datatype_str = str(datatype)
                if datatype_str in XSD_TYPE_MAP:
                    mapped_type = XSD_TYPE_MAP[datatype_str]
                    if mapped_type:
                        prop_def["@type"] = mapped_type
                else:
                    # Unknown datatype, preserve it
                    prop_def["@type"] = datatype_str

            elif node_kind == SH.IRI or class_ref or node_ref:
                # Object property - reference to another node
                prop_def["@type"] = "@id"

            # Check if it's a list/set property (minCount > 1 or no maxCount with minCount)
            max_count = shacl_graph.value(prop_node, SH.maxCount)
            if max_count is None or int(max_count) > 1:
                # Could be multi-valued, but we only add @container if clearly a list
                # For now, skip container annotation unless we have clear evidence
                pass

            properties[local_name] = prop_def

    return properties


def extract_classes(owl_graph: Graph, domain_iri: str) -> Set[str]:
    """Extract class local names from the OWL ontology."""
    classes = set()
    domain_ns = domain_iri if domain_iri.endswith("/") else domain_iri + "/"

    for cls in owl_graph.subjects(RDF.type, OWL.Class):
        cls_str = str(cls)
        if cls_str.startswith(domain_iri):
            local_name = cls_str.replace(domain_ns, "").replace(domain_iri, "")
            if local_name and not local_name.startswith("http"):
                classes.add(local_name)

    return classes


def extract_named_individuals(owl_graph: Graph, domain_iri: str) -> Dict[str, str]:
    """Extract named individuals (enum values) from the OWL ontology."""
    individuals: Dict[str, str] = {}
    domain_ns = domain_iri if domain_iri.endswith("/") else domain_iri + "/"

    for ind in owl_graph.subjects(RDF.type, OWL.NamedIndividual):
        ind_str = str(ind)
        if ind_str.startswith(domain_iri):
            local_name = ind_str.replace(domain_ns, "").replace(domain_iri, "")
            if local_name and not local_name.startswith("http"):
                individuals[local_name] = ind_str

    return individuals


def generate_context(domain: str) -> Optional[Dict[str, Any]]:
    """
    Generate a JSON-LD context for a domain.

    Args:
        domain: Domain name (e.g., 'manifest', 'hdmap')

    Returns:
        JSON-LD context dictionary, or None if generation fails
    """
    domain_dir = ARTIFACTS_DIR / domain
    owl_path = domain_dir / f"{domain}{Extensions.OWL}"
    shacl_path = domain_dir / f"{domain}{Extensions.SHACL}"

    if not owl_path.exists():
        logger.error("OWL file not found: %s", owl_path)
        return None

    # Handle domains with multiple SHACL files or non-standard naming
    shacl_paths: List[Path] = []
    if shacl_path.exists():
        shacl_paths.append(shacl_path)
    else:
        # Look for any .shacl.ttl files in the domain directory
        shacl_paths = sorted(domain_dir.glob(f"*{Extensions.SHACL}"))
        if not shacl_paths:
            logger.error("No SHACL files found in: %s", domain_dir)
            return None
        logger.info(
            "Using %d SHACL file(s) for domain '%s': %s",
            len(shacl_paths),
            domain,
            [p.name for p in shacl_paths],
        )

    # Parse OWL graph
    owl_graph = parse_graph(owl_path)
    if not owl_graph:
        return None

    # Parse and merge all SHACL graphs
    shacl_graph = Graph(store=FAST_STORE)
    for sp in shacl_paths:
        g = parse_graph(sp)
        if g:
            shacl_graph += g

    if len(shacl_graph) == 0:
        logger.error("Failed to parse any SHACL files for domain '%s'", domain)
        return None

    # Extract ontology IRI
    ontology_iri = extract_ontology_iri(owl_graph)
    if not ontology_iri:
        logger.error("Could not extract ontology IRI from %s", owl_path)
        return None

    logger.info("Processing domain '%s' with IRI: %s", domain, ontology_iri)

    # Determine prefix
    prefix = extract_prefix_from_iri(ontology_iri)

    # Build context
    context: Dict[str, Any] = {
        # JSON-LD 1.1 required for @container features
        "@version": 1.1,
        # Standard prefixes
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "sh": "http://www.w3.org/ns/shacl#",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        # Domain prefix
        prefix: ontology_iri if ontology_iri.endswith("/") else ontology_iri + "/",
    }

    # Add prefixes for imported ontologies (resolved from owl:imports IRIs)
    for imported in owl_graph.objects(URIRef(ontology_iri), OWL.imports):
        imported_str = str(imported)
        imported_prefix = extract_prefix_from_iri(imported_str)
        if imported_prefix and imported_prefix not in context:
            imported_ns = (
                imported_str if imported_str.endswith("/") else imported_str + "/"
            )
            context[imported_prefix] = imported_ns

    # Extract property definitions from SHACL
    properties = extract_property_datatypes(shacl_graph, prefix, ontology_iri)

    # Also check for properties in imported SHACL if owl:imports exists
    # (For now, we focus on the domain's own properties)

    # Add properties to context
    context.update(properties)

    # Extract and add class term mappings for compact @type usage
    # This allows: "@type": "Manifest" instead of "@type": "manifest:Manifest"
    classes = extract_classes(owl_graph, ontology_iri)
    for class_name in sorted(classes):
        # Map bare class names to full IRIs for @type expansion
        context[class_name] = f"{prefix}:{class_name}"

    # Build source_shacl value (single path or list)
    if len(shacl_paths) == 1:
        source_shacl = shacl_paths[0].relative_to(ROOT_DIR).as_posix()
    else:
        source_shacl = [p.relative_to(ROOT_DIR).as_posix() for p in shacl_paths]

    # Build the full context document
    context_doc = {
        "comments": {
            "description": "Auto-generated JSON-LD context for compact instance syntax",
            "generator": "context_generator.py",
            "source_owl": owl_path.relative_to(ROOT_DIR).as_posix(),
            "source_shacl": source_shacl,
            "note": "Transitional artifact - will be replaced by LinkML-generated context",
        },
        "@context": context,
    }

    return context_doc


def write_context(domain: str, context_doc: Dict[str, Any]) -> Optional[Path]:
    """Write context document to file only if content has changed."""
    output_path = ARTIFACTS_DIR / domain / f"{domain}{Extensions.CONTEXT}"
    new_content = json.dumps(context_doc, indent=2, ensure_ascii=False) + "\n"

    if write_if_changed(output_path, new_content):
        logger.info("Written: %s", output_path)
        return output_path
    else:
        logger.debug("Context unchanged: %s", output_path.name)
        return None


def generate_all_contexts(
    exclude: Optional[List[str]] = None,
) -> Dict[str, Optional[Path]]:
    """
    Generate contexts for all domains in artifacts/.

    Args:
        exclude: List of domains to skip (e.g., ['gx'] which has LinkML-generated context)

    Returns:
        Dict mapping domain names to output paths (or None if failed)
    """
    exclude = exclude or ["gx"]  # gx already has LinkML-generated context
    results: Dict[str, Optional[Path]] = {}

    for domain_dir in sorted(ARTIFACTS_DIR.iterdir()):
        if not domain_dir.is_dir():
            continue

        domain = domain_dir.name
        if domain in exclude:
            logger.info("Skipping excluded domain: %s", domain)
            results[domain] = None
            continue

        owl_path = domain_dir / f"{domain}{Extensions.OWL}"
        if not owl_path.exists():
            logger.debug("No OWL file in %s, skipping", domain)
            continue

        context_doc = generate_context(domain)
        if context_doc:
            results[domain] = write_context(domain, context_doc)
        else:
            results[domain] = None

    return results


def test_context_roundtrip(domain: str, instance_path: Path) -> bool:
    """
    Test that a compact instance produces equivalent RDF triples.

    This test:
    1. Loads the original verbose instance
    2. Loads a compact version using the generated context
    3. Compares the resulting RDF graphs for isomorphism

    Args:
        domain: Domain name
        instance_path: Path to a verbose JSON-LD instance

    Returns:
        True if graphs are isomorphic, False otherwise
    """
    from rdflib.compare import isomorphic

    context_path = ARTIFACTS_DIR / domain / f"{domain}{Extensions.CONTEXT}"
    if not context_path.exists():
        logger.error("Context file not found: %s", context_path)
        return False

    if not instance_path.exists():
        logger.error("Instance file not found: %s", instance_path)
        return False

    # Load context
    with open(context_path, "r", encoding="utf-8") as f:
        context_doc = json.load(f)
    context = context_doc.get("@context", {})

    # Load original instance
    with open(instance_path, "r", encoding="utf-8") as f:
        original = json.load(f)

    # Parse original to graph
    g_original = Graph()
    g_original.parse(data=json.dumps(original), format="json-ld")

    # Create compact version by replacing context
    compact = original.copy()
    compact["@context"] = context

    # Parse compact to graph
    g_compact = Graph()
    try:
        g_compact.parse(data=json.dumps(compact), format="json-ld")
    except Exception as e:
        logger.error("Failed to parse compact instance: %s", e)
        return False

    # Compare
    if isomorphic(g_original, g_compact):
        logger.info("✅ Round-trip test PASSED for %s", instance_path.name)
        return True
    else:
        logger.warning("❌ Round-trip test FAILED for %s", instance_path.name)
        logger.debug("Original triples: %d", len(g_original))
        logger.debug("Compact triples: %d", len(g_compact))

        # Show differences
        original_triples = set(g_original)
        compact_triples = set(g_compact)
        missing = original_triples - compact_triples
        extra = compact_triples - original_triples

        if missing:
            logger.debug("Missing triples (in original, not in compact):")
            for t in list(missing)[:5]:
                logger.debug("  %s", t)
        if extra:
            logger.debug("Extra triples (in compact, not in original):")
            for t in list(extra)[:5]:
                logger.debug("  %s", t)

        return False


def _run_tests() -> bool:
    """Run self-tests for the module."""
    print("Running context_generator self-tests...")
    all_passed = True

    # Test 1: Extract prefix from IRI
    try:
        iri1 = "https://w3id.org/ascs-ev/envited-x/manifest/v5"
        assert extract_prefix_from_iri(iri1) == "manifest"

        iri2 = "https://w3id.org/ascs-ev/envited-x/hdmap/v5/"
        assert extract_prefix_from_iri(iri2) == "hdmap"

        print("PASS: extract_prefix_from_iri")
    except AssertionError as e:
        print(f"FAIL: extract_prefix_from_iri - {e}")
        all_passed = False

    # Test 2: Generate context for manifest (if files exist)
    try:
        manifest_owl = ARTIFACTS_DIR / "manifest" / "manifest.owl.ttl"
        if manifest_owl.exists():
            context = generate_context("manifest")
            assert context is not None
            assert "@context" in context
            assert "manifest" in context["@context"]
            print("PASS: generate_context (manifest)")
        else:
            print("SKIP: generate_context (manifest files not found)")
    except AssertionError as e:
        print(f"FAIL: generate_context - {e}")
        all_passed = False

    print()
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests FAILED!")

    return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate JSON-LD context files from OWL/SHACL artifacts"
    )
    parser.add_argument(
        "--domain",
        help="Generate context for a specific domain",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate contexts for all domains",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=["gx"],
        help="Domains to exclude (default: gx)",
    )
    parser.add_argument(
        "--test-roundtrip",
        metavar="DOMAIN",
        help="Test round-trip equivalence for a domain",
    )
    parser.add_argument(
        "--instance",
        type=Path,
        help="Instance file for round-trip test",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run self-tests",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing files",
    )

    args = parser.parse_args()

    if args.test:
        success = _run_tests()
        return 0 if success else 1

    if args.test_roundtrip:
        if not args.instance:
            # Try to find a valid instance
            test_dir = ROOT_DIR / "tests" / "data" / args.test_roundtrip / "valid"
            instances = list(test_dir.glob("*.json"))
            if instances:
                args.instance = instances[0]
            else:
                print(f"No instance file found for {args.test_roundtrip}")
                return 1

        success = test_context_roundtrip(args.test_roundtrip, args.instance)
        return 0 if success else 1

    if args.all:
        results = generate_all_contexts(exclude=args.exclude)
        written_count = sum(1 for p in results.values() if p is not None)
        total_count = len([d for d in results if d not in (args.exclude or [])])
        if written_count > 0:
            print(f"\nUpdated {written_count}/{total_count} context files")
        else:
            print(f"\nAll {total_count} context files unchanged")
        return 0

    if args.domain:
        context_doc = generate_context(args.domain)
        if context_doc:
            if args.dry_run:
                print(json.dumps(context_doc, indent=2))
            else:
                write_context(args.domain, context_doc)
            return 0
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
