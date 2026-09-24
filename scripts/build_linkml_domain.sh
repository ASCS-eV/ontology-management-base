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
flags="${repo}/linkml/${domain}/gen-flags.env"
if [ -f "${flags}" ]; then
    # shellcheck disable=SC1090
    . "${flags}"
fi

mkdir -p "${outdir}"

# shellcheck disable=SC2086
# --no-use-native-uris makes gen-owl honour class_uri/slot_uri instead of
# deriving the IRI from the LinkML name. Without it the OWL and the SHACL name
# different IRIs for the same term. artifacts/gx/update-from-submodule.sh has
# always used it; the `just generate` recipe for openlabel-v2 does not.
# --metadata-profile rdfs maps `description` to rdfs:comment (the default
# profile uses skos:definition), which is this repository's ontology convention.
"${run}/gen-owl" --diff-stable --normalize-prefixes --no-use-native-uris \
    --metadata-profile rdfs ${OWL_EXTRA_FLAGS} \
    --no-metadata --default-language en --ontology-uri-suffix "" "${schema}" \
    2>/dev/null | tr -d '\r' | sed -e '${' -e '/^$/d' -e '}' \
    > "${outdir}/${domain}.owl.ttl"

# gen-shacl skips a LinkML rule or class expression (any_of, all_of,
# exactly_one_of, none_of) it cannot translate exactly, and reports a skipped
# rule only at DEBUG level. Keep its log and fail on any skip, so a dropped
# constraint is never silent.
shacl_log="$(mktemp)"
# shellcheck disable=SC2086
"${run}/gen-shacl" --diff-stable --normalize-prefixes --no-metadata \
    --default-language en --non-closed --suffix Shape --no-expand-subproperty-of \
    ${SHACL_EXTRA_FLAGS} --message-template "{name} ({class}): {description}" \
    --log_level DEBUG "${schema}" 2>"${shacl_log}" | tr -d '\r' | sed -e '${' -e '/^$/d' -e '}' \
    > "${outdir}/${domain}.shacl.ttl"
skipped="Skipping unsupported rule pattern|is not translated to SHACL"
if grep -Eq "${skipped}" "${shacl_log}"; then
    echo "[ERR] gen-shacl skipped constraint(s) it cannot translate:" >&2
    grep -E "${skipped}" "${shacl_log}" | sed 's/^/      /' >&2
    rm -f "${shacl_log}"
    exit 1
fi
rm -f "${shacl_log}"

# shellcheck disable=SC2086
"${run}/gen-jsonld-context" --normalize-prefixes --no-metadata \
    --exclude-external-imports ${CONTEXT_EXTRA_FLAGS} "${schema}" \
    2>/dev/null | tr -d '\r' | sed -e '${' -e '/^$/d' -e '}' \
    > "${outdir}/${domain}.context.jsonld"

# A generator that fails after emitting nothing still exits 0 (gen-shacl prints a
# traceback then returns success), and stderr is suppressed above, so an empty
# artifact is the only visible symptom. Fail loudly instead.
for f in "${outdir}/${domain}.owl.ttl" "${outdir}/${domain}.shacl.ttl" \
         "${outdir}/${domain}.context.jsonld"; do
    if [ ! -s "${f}" ]; then
        echo "[ERR] $(basename "${f}") is empty - a generator failed silently." >&2
        echo "      Re-run that generator without 2>/dev/null to see why." >&2
        exit 1
    fi
done

echo "[OK] ${domain} -> ${outdir}"
