#!/usr/bin/env bash
# Generate OWL / SHACL / JSON-LD context for one LinkML domain into a directory.
# The LinkML generators are the only thing that runs here: whatever they cannot
# express is a gap to be named, not something to patch up afterwards.
set -euo pipefail

domain="${1:?usage: build_linkml_domain.sh <domain> <outdir>}"
outdir="${2:?usage: build_linkml_domain.sh <domain> <outdir>}"
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
run="${repo}/.venv/bin"
schema="${repo}/linkml/${domain}/${domain}.yaml"

# Per-domain generator flags; see linkml/<domain>/gen-flags.env.
OWL_EXTRA_FLAGS="--xsd-anyuri-as-iri"
SHACL_EXTRA_FLAGS=""
CONTEXT_EXTRA_FLAGS="--xsd-anyuri-as-iri"
OWL_METADATA_FLAGS="--metadata-profile rdfs"
SHACL_SHAPE_FLAGS="--non-closed --suffix Shape --no-expand-subproperty-of"
SHACL_MESSAGE_TEMPLATE="{name} ({class}): {description}"
flags="${repo}/linkml/${domain}/gen-flags.env"
if [ -f "${flags}" ]; then
    # shellcheck disable=SC1090
    . "${flags}"
fi

destination="${outdir}"
outdir="$(mktemp -d)"

# A generator's diagnostics go to a log, shown only when it fails: the artifacts
# are written from stdout, and a failure must say why instead of ending the
# script without a word (set -o pipefail makes the pipeline report it).
gen_log="$(mktemp)"
trap 'rm -f "${gen_log}"; rm -rf "${outdir}"' EXIT
generator_failed() {
    echo "[ERR] $1 failed for ${domain}:" >&2
    tail -n 25 "${gen_log}" | sed 's/^/      /' >&2
    exit 1
}

# shellcheck disable=SC2086
# --no-use-native-uris makes gen-owl honour class_uri/slot_uri instead of
# deriving the IRI from the LinkML name. Without it the OWL and the SHACL name
# different IRIs for the same term. Every domain, and
# artifacts/gx/update-from-submodule.sh, uses it.
# --metadata-profile rdfs maps `description` to rdfs:comment (the default
# profile uses skos:definition), which is this repository's ontology convention.
if ! "${run}/gen-owl" --diff-stable --normalize-prefixes --no-use-native-uris \
    ${OWL_METADATA_FLAGS} ${OWL_EXTRA_FLAGS} \
    --no-metadata --default-language en --ontology-uri-suffix "" "${schema}" \
    2>"${gen_log}" | tr -d '\r' | sed -e '${' -e '/^$/d' -e '}' \
    > "${outdir}/${domain}.owl.ttl"; then
    generator_failed gen-owl
fi

# gen-shacl skips a LinkML rule or class expression (any_of, all_of,
# exactly_one_of, none_of) it cannot translate exactly, and reports the skip
# only in its log. Keep the log and fail on any skip, so a dropped constraint is
# never silent.
shacl_log="${outdir}/shacl.log"
# shellcheck disable=SC2086
if ! "${run}/gen-shacl" --diff-stable --normalize-prefixes --no-metadata \
    --default-language en ${SHACL_SHAPE_FLAGS} \
    ${SHACL_EXTRA_FLAGS} --message-template "${SHACL_MESSAGE_TEMPLATE}" \
    --log_level DEBUG "${schema}" 2>"${shacl_log}" | tr -d '\r' | sed -e '${' -e '/^$/d' -e '}' \
    > "${outdir}/${domain}.shacl.ttl"; then
    cp "${shacl_log}" "${gen_log}"
    rm -f "${shacl_log}"
    generator_failed gen-shacl
fi
skipped="Skipping unsupported rule pattern|is not translated to SHACL|Rule .*skipped, because"
if grep -Eq "${skipped}" "${shacl_log}"; then
    echo "[ERR] gen-shacl skipped constraint(s) it cannot translate:" >&2
    grep -E "${skipped}" "${shacl_log}" | sed 's/^/      /' >&2
    rm -f "${shacl_log}"
    exit 1
fi
rm -f "${shacl_log}"

# shellcheck disable=SC2086
if ! "${run}/gen-jsonld-context" --normalize-prefixes --no-metadata \
    --exclude-external-imports ${CONTEXT_EXTRA_FLAGS} "${schema}" \
    2>"${gen_log}" | tr -d '\r' | sed -e '${' -e '/^$/d' -e '}' \
    > "${outdir}/${domain}.context.jsonld"; then
    generator_failed gen-jsonld-context
fi

# A generator that fails after emitting nothing can still exit 0 (gen-shacl prints
# a traceback then returns success), so an empty artifact is checked as well.
for f in "${outdir}/${domain}.owl.ttl" "${outdir}/${domain}.shacl.ttl" \
         "${outdir}/${domain}.context.jsonld"; do
    if [ ! -s "${f}" ]; then
        echo "[ERR] $(basename "${f}") is empty - a generator failed silently." >&2
        exit 1
    fi
done

# An IRI that is an unexpanded CURIE (`<sh:conformsTo>`, `<xsd:float>`) matches
# nothing, so a shape using it as a path or datatype silently constrains nothing or
# rejects everything. It appears when a schema's shapes use a prefix the schema does
# not declare (linkml/GAPS.md M10, G13). Read the output and fail on one.
"${run}/python" - "${repo}/scripts" "${outdir}/${domain}.owl.ttl" "${outdir}/${domain}.shacl.ttl" <<'EOF'
import sys
from rdflib import Graph

sys.path.insert(0, sys.argv[1])
from compare_artifacts import unexpanded_iris

found = unexpanded_iris(*(Graph().parse(path, format="turtle") for path in sys.argv[2:]))
if found:
    print("[ERR] unexpanded IRIs - declare their prefixes in the schema:", file=sys.stderr)
    for iri, count in sorted(found.items()):
        print(f"      <{iri}> ({count} use(s))", file=sys.stderr)
    sys.exit(1)
EOF

# Publish only after all three generators and the checks succeed. Normalize JSON
# exactly as pretty-format-json does in CI, without changing generated RDF terms.
"${run}/python" - "${outdir}/${domain}.context.jsonld" <<'EOF'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
path.write_text(json.dumps(json.loads(path.read_text()), indent=3, ensure_ascii=False) + "\n")
EOF
mkdir -p "${destination}"
for suffix in owl.ttl shacl.ttl context.jsonld; do
    cp "${outdir}/${domain}.${suffix}" "${destination}/${domain}.${suffix}"
done
echo "[OK] ${domain} -> ${destination}"
