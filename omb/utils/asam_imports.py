#!/usr/bin/env python3
"""
Derive ``imports/<vocabulary>/`` from the pinned ``asam-openx-standards`` submodule.

The ASAM standards submodule is the source of truth for ASAM deliverables: it pins the
normative XML schemas, records their provenance, and generates the OWL/SHACL pair from the
open UML model (see ``submodules/asam-openx-standards/pipeline/README.md``). What lives under
``imports/`` is a *derived copy*, present for two reasons the submodule cannot serve:

1. **Catalog resolution.** ``imports/catalog-v001.xml`` maps an ontology IRI to a local file so
   validation resolves offline. The catalog generator computes paths relative to ``imports/``
   and cannot point outside it, so a copy inside the directory is what makes the ASAM
   namespaces resolvable at all.
2. **Availability without the submodule.** A consumer installing this repository as a package,
   or a checkout without ``--recurse-submodules``, still gets the vocabularies.

Because it is derived, it must never be edited: the only supported way to change it is to
change the submodule and re-run this module. ``--check`` compares the copy byte-for-byte
against the submodule and is wired into CI and the test suite, so a hand edit or a submodule
bump that was not followed by a sync fails rather than drifting quietly.

Usage
-----
::

    just asam-imports                  # sync imports/ from the submodule
    just asam-imports-check            # verify in sync; non-zero if not
    just test-asam-imports             # run integration tests

After a sync, regenerate the catalog so the new files are registered::

    just registry-update

Line endings
------------
The XML schemas are copied as raw bytes, CRLF and all. ASAM's ``schema/README.md`` in the
submodule publishes the SHA-256 of the deliverables *as shipped*, and rewriting line endings
would invalidate every one of those checksums - the copy would no longer be the thing ASAM
published. ``.gitattributes`` marks ``imports/*/schema/**`` as not text and the
``mixed-line-ending`` hook excludes it, so neither Git nor pre-commit rewrites them.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from omb.core.constants import ASAM_STANDARDS_ROOT, ASAM_SUBMODULE_HINT
from omb.core.logging import get_logger

logger = get_logger(__name__)

#: What each derived import directory is built from. The key is the directory under
#: ``imports/``; it also names the OWL/SHACL files inside it, because
#: ``file_collector.collect_ontology_bundles`` discovers a bundle only when the ontology is
#: named after its directory - ``imports/opendrive/opendrive.owl.ttl``.
ASAM_IMPORTS: Dict[str, Dict[str, str]] = {
    "opendrive": {
        "standard": "asam-opendrive",
        "title": "ASAM OpenDRIVE®",
    },
    "openscenario": {
        "standard": "asam-openscenario-xml",
        "title": "ASAM OpenSCENARIO® XML",
    },
}

#: Sub-directory holding the copied normative schemas, inside each import directory.
SCHEMA_SUBDIR = "schema"


def submodule_root(root_dir: Path) -> Path:
    return root_dir / ASAM_STANDARDS_ROOT


def source_files(root_dir: Path, vocabulary: str) -> List[Tuple[Path, Path]]:
    """Return (source, destination) pairs for one derived import directory.

    Raises:
        FileNotFoundError: if the submodule is not initialised, or a standard in
            ``ASAM_IMPORTS`` has no generated artifacts. Both are actionable, so neither is
            silently skipped: a partial sync would look like a successful one.
    """
    spec = ASAM_IMPORTS[vocabulary]
    standard = submodule_root(root_dir) / spec["standard"]
    if not standard.is_dir():
        raise FileNotFoundError(f"{standard} not found. {ASAM_SUBMODULE_HINT}")

    destination = root_dir / "imports" / vocabulary
    pairs: List[Tuple[Path, Path]] = []

    for suffix in ("owl.ttl", "shacl.ttl"):
        source = standard / "generated" / f"{vocabulary}.{suffix}"
        if not source.exists():
            raise FileNotFoundError(
                f"{source} does not exist, so imports/{vocabulary} cannot be derived. "
                "Generate it in the submodule first: see pipeline/README.md there."
            )
        pairs.append((source, destination / source.name))

    schemas = sorted((standard / SCHEMA_SUBDIR).glob("*.xsd"))
    if not schemas:
        raise FileNotFoundError(
            f"no .xsd files under {standard / SCHEMA_SUBDIR}, so the normative schema for "
            f"{vocabulary} cannot be derived"
        )
    for source in schemas:
        pairs.append((source, destination / SCHEMA_SUBDIR / source.name))

    return pairs


def sync(root_dir: Path) -> List[Path]:
    """Copy every derived file from the submodule, returning the paths written."""
    written: List[Path] = []
    for vocabulary in sorted(ASAM_IMPORTS):
        for source, destination in source_files(root_dir, vocabulary):
            destination.parent.mkdir(parents=True, exist_ok=True)
            # copyfile, not copy2: the content is what is derived, not the source's mtime.
            # Bytes are preserved exactly - see "Line endings" in the module docstring.
            shutil.copyfile(source, destination)
            written.append(destination)
    return written


def check(root_dir: Path) -> List[str]:
    """Return a description of every way the derived copy differs from the submodule.

    An empty list means in sync. Reported rather than raised, so one run lists every
    difference instead of only the first.
    """
    differences: List[str] = []
    for vocabulary in sorted(ASAM_IMPORTS):
        expected = source_files(root_dir, vocabulary)
        for source, destination in expected:
            if not destination.exists():
                differences.append(
                    f"missing: {destination.relative_to(root_dir).as_posix()}"
                )
            elif not filecmp.cmp(source, destination, shallow=False):
                differences.append(
                    f"differs from the submodule: {destination.relative_to(root_dir).as_posix()}"
                )

        # A file the submodule no longer provides is drift in the other direction: it would go
        # on being catalogued and validated against long after its source was removed.
        expected_paths = {destination for _, destination in expected}
        directory = root_dir / "imports" / vocabulary
        for path in sorted(directory.rglob("*")):
            if path.is_dir() or path.name == "README.md":
                continue
            if path not in expected_paths:
                differences.append(
                    f"not derived from the submodule: {path.relative_to(root_dir).as_posix()}"
                )

    return differences


def _run_tests() -> bool:
    """Self-tests over a synthetic submodule layout, so no real submodule is needed."""
    import tempfile

    passed = failed = 0

    def expect(condition: bool, description: str) -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            sys.stderr.write(f"FAIL: {description}\n")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for vocabulary, spec in ASAM_IMPORTS.items():
            standard = submodule_root(root) / spec["standard"]
            (standard / "generated").mkdir(parents=True)
            (standard / SCHEMA_SUBDIR).mkdir(parents=True)
            (standard / "generated" / f"{vocabulary}.owl.ttl").write_text("# owl\n")
            (standard / "generated" / f"{vocabulary}.shacl.ttl").write_text("# shacl\n")
            # CRLF on purpose: the check must compare bytes, so a copy that normalised line
            # endings has to be reported as differing.
            (standard / SCHEMA_SUBDIR / "Test.xsd").write_bytes(b"<xsd:schema/>\r\n")

        expect(check(root), "an unsynced tree reports differences")
        written = sync(root)
        expect(
            len(written) == 3 * len(ASAM_IMPORTS), f"sync wrote {len(written)} files"
        )
        expect(check(root) == [], f"a synced tree is clean, got {check(root)}")

        schema = root / "imports" / "opendrive" / SCHEMA_SUBDIR / "Test.xsd"
        expect(
            schema.read_bytes() == b"<xsd:schema/>\r\n", "CRLF bytes survive the copy"
        )
        schema.write_bytes(b"<xsd:schema/>\n")
        expect(
            any("differs" in d for d in check(root)),
            "normalising line endings is reported as a difference",
        )
        sync(root)

        stray = root / "imports" / "opendrive" / "stray.ttl"
        stray.write_text("# not from the submodule\n")
        expect(
            any("not derived" in d for d in check(root)),
            "a file with no counterpart in the submodule is reported",
        )
        stray.unlink()

        (root / "imports" / "opendrive" / "README.md").write_text("# hand written\n")
        expect(check(root) == [], "README.md is exempt, being written by hand")

        shutil.rmtree(submodule_root(root))
        try:
            check(root)
            expect(False, "an uninitialised submodule raises")
        except FileNotFoundError as error:
            expect("submodule" in str(error), f"the error names the fix, got {error}")

    print(f"{passed} passed, {failed} failed")
    return failed == 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the derived copy matches the submodule; do not write",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="repository root directory (default: current directory)",
    )
    parser.add_argument("--test", action="store_true", help="run module self-tests")
    args = parser.parse_args()

    if args.test:
        return 0 if _run_tests() else 1

    root_dir = args.root.resolve()

    try:
        if args.check:
            differences = check(root_dir)
            if differences:
                for difference in differences:
                    sys.stderr.write(f"  {difference}\n")
                sys.stderr.write(
                    f"\n{len(differences)} difference(s) between imports/ and the ASAM "
                    "standards submodule. Run 'just asam-imports' to derive "
                    "them again, then 'just registry-update'.\n"
                )
                return 1
            print("imports/ matches the ASAM standards submodule")
            return 0

        written = sync(root_dir)
        for path in written:
            print(f"  {path.relative_to(root_dir).as_posix()}")
        print(
            f"\n{len(written)} file(s) derived from the ASAM standards submodule. "
            "Run 'just registry-update' to register them in imports/catalog-v001.xml."
        )
        return 0
    except FileNotFoundError as error:
        sys.stderr.write(f"{error}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
