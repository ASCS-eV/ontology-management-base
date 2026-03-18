#!/usr/bin/env bash
# Update GX artifacts from the service-characteristics submodule
# Usage: ./update-from-submodule.sh [git-ref]
#
# If git-ref is provided, checks it out in the submodule first.
# Then rebuilds the GX artifacts using the service-characteristics build pipeline
# and copies the generated outputs into this folder.

set -euo pipefail

# Prevent MSYS / Git Bash from converting "/" CLI arguments to Windows paths.
# Without this, --enum-iri-separator "/" becomes "C:/Program Files/PortableGit/"
# which corrupts all enum IRIs in the generated OWL ontology.
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL="*"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SUBMODULE_DIR="$ROOT_DIR/submodules/service-characteristics"
ARTIFACTS_DIR="$SCRIPT_DIR"
VERSION_FILE="$ARTIFACTS_DIR/VERSION"
UPSTREAM_COMMIT_FILE="$ARTIFACTS_DIR/UPSTREAM_COMMIT"
UPSTREAM_REF_FILE="$ARTIFACTS_DIR/UPSTREAM_REF"

if [ $# -gt 1 ]; then
    echo "Usage: $0 [git-ref]"
    exit 1
fi

if [ ! -d "$SUBMODULE_DIR" ]; then
    echo "Error: Submodule not found at $SUBMODULE_DIR"
    echo "Run: git submodule update --init --recursive"
    exit 1
fi

cd "$SUBMODULE_DIR"

# Optionally check out a specific ref
if [ $# -eq 1 ] && [ -n "$1" ]; then
    TARGET_REF="$1"
    echo "Checking out $TARGET_REF..."
    git fetch --tags origin
    git checkout "$TARGET_REF"
else
    echo "Using current submodule checkout: $(git rev-parse --short HEAD)"
fi

for cmd in gen-owl gen-shacl gen-jsonld-context rdfpipe; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Error: Required command '$cmd' not found in PATH."
        echo "Run this script via 'make generate gx' or ensure the OMB virtualenv tools are available."
        exit 1
    fi
done

# Log file for generator warnings/trace output.
# merge_schemas.sh uses set -ex which produces verbose trace output on stderr;
# when invoked through deep process chains (PowerShell → make → sh → bash → bash)
# the stderr/stdout pipe buffers can deadlock on Windows. Redirecting stderr to a
# log file avoids the deadlock while still capturing diagnostics.
GX_LOG="$ARTIFACTS_DIR/.generate-gx.log"
: > "$GX_LOG"

echo "Generating artifacts from service-characteristics..."
echo "  Generating SHACL shapes..."
bash ./merge_schemas.sh shacl 2>>"$GX_LOG"
echo "  Generating OWL ontology..."
bash ./merge_schemas.sh owl 2>>"$GX_LOG"
echo "  Generating JSON-LD context..."
gen-jsonld-context linkml/gaia-x.yaml --no-mergeimports > context.jsonld 2>>"$GX_LOG"

# Normalize Turtle output: rdfpipe on Windows inserts literal \r escapes inside
# triple-quoted strings ("""...\r\n...""") that don't appear on Linux/macOS.
# Strip them for deterministic cross-platform output.
for f in shapes.shacl.ttl ontology.owl.ttl; do
    if [ -f "$f" ]; then
        sed -i 's/\\r$//' "$f"
    fi
done

echo "Copying artifacts from submodule..."
cp -v "$SUBMODULE_DIR/ontology.owl.ttl" "$ARTIFACTS_DIR/gx.owl.ttl"
cp -v "$SUBMODULE_DIR/shapes.shacl.ttl" "$ARTIFACTS_DIR/gx.shacl.ttl"
cp -v "$SUBMODULE_DIR/context.jsonld" "$ARTIFACTS_DIR/gx.context.jsonld"

UPSTREAM_COMMIT=$(git rev-parse HEAD)
UPSTREAM_REF=$(git describe --tags --always --dirty 2>/dev/null || git rev-parse --short HEAD)
echo "Recording upstream provenance..."
printf '%s\n' "$UPSTREAM_COMMIT" > "$UPSTREAM_COMMIT_FILE"
printf '%s\n' "$UPSTREAM_REF" > "$UPSTREAM_REF_FILE"

VERSION_TAG=$(git describe --tags --exact-match 2>/dev/null || true)
if [ -n "$VERSION_TAG" ]; then
    VERSION_NUMBER="${VERSION_TAG#v}"
    VERSION_NUMBER="${VERSION_NUMBER%%-*}"
    echo "Updating VERSION file..."
    echo "$VERSION_NUMBER" > "$VERSION_FILE"
else
    CURRENT_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE" 2>/dev/null || true)"
    if [ -n "$CURRENT_VERSION" ]; then
        echo "Leaving VERSION unchanged at $CURRENT_VERSION (current checkout is not an exact tag)."
    else
        echo "VERSION file not updated because the current checkout is not an exact tag."
    fi
fi

echo ""
echo "✓ GX artifacts updated from $(git rev-parse --short HEAD)"
echo ""
echo "Next steps:"
echo "  1. Regenerate documentation:"
echo "     python3 -m src.tools.utils.registry_updater"
echo "     python3 -m src.tools.utils.properties_updater"
echo ""
echo "  2. Review artifacts/gx/VERSION and provenance metadata if needed"
echo ""
echo "  3. Commit the changes:"
echo "     git add artifacts/gx/ submodules/service-characteristics"
echo "     git commit -m 'chore(gx): refresh Gaia-X artifacts'"
