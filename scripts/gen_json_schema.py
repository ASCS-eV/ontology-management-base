#!/usr/bin/env python3
"""Thin wrapper around LinkML's JsonSchemaGenerator that exposes the generator's
``include_null`` setting, which the upstream ``gen-json-schema`` CLI does not yet
surface as a flag.

Why this exists
---------------
LinkML emits optional slots as ``type: ["<t>", "null"]`` by default
(``JsonSchemaGenerator.include_null = True``), so the generated JSON Schema
accepts an explicit JSON ``null`` where the value is absent. For a structural
model that mirrors a normative reference schema which forbids ``null`` (e.g. the
ASAM OpenLABEL JSON Schema), that is an unwanted relaxation. ``--no-include-null``
turns it off, per domain — see linkml/<domain>/jsonschema.genopts.

Output is byte-identical to ``gen-json-schema --indent N`` for the same model
when ``--include-null`` is left at its default; the only difference under
``--no-include-null`` is the removal of ``null`` from optional unions.

This wrapper can be retired once the fork's ``gen-json-schema`` CLI gains a
native ``--include-null/--no-include-null`` option.
"""

from __future__ import annotations

import argparse
import sys

from linkml.generators.jsonschemagen import JsonSchemaGenerator


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("yamlfile", help="LinkML structural model")
    ap.add_argument("--indent", type=int, default=4, help="JSON indent (0 = compact)")
    ap.add_argument(
        "--include-null",
        dest="include_null",
        action="store_true",
        default=True,
        help="include a 'null' type in optional slots (LinkML default)",
    )
    ap.add_argument(
        "--no-include-null",
        dest="include_null",
        action="store_false",
        help="forbid explicit null in optional slots (strict reference parity)",
    )
    # Accepted for command-line parity with gen-json-schema; serialize() is
    # already deterministic (sort_keys=True), so this is a no-op here.
    ap.add_argument("--deterministic", action="store_true")
    args = ap.parse_args(argv)

    gen = JsonSchemaGenerator(
        args.yamlfile, indent=args.indent, include_null=args.include_null
    )
    sys.stdout.write(gen.serialize())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
