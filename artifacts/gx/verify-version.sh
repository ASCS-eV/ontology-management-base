#!/usr/bin/env bash
# Verify that GX upstream provenance matches the submodule checkout
# Usage: ./verify-version.sh
#
# Exit code 0 = synchronized
# Exit code 1 = out of sync

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SUBMODULE_DIR="$ROOT_DIR/submodules/service-characteristics"
VERSION_FILE="$SCRIPT_DIR/VERSION"
UPSTREAM_COMMIT_FILE="$SCRIPT_DIR/UPSTREAM_COMMIT"
UPSTREAM_REF_FILE="$SCRIPT_DIR/UPSTREAM_REF"

if [ ! -d "$SUBMODULE_DIR" ]; then
    echo "⚠️  Warning: Submodule not initialized"
    echo "Run: git submodule update --init --recursive"
    exit 1
fi

if [ ! -f "$VERSION_FILE" ]; then
    echo "❌ Error: VERSION file not found at $VERSION_FILE"
    exit 1
fi

if [ ! -f "$UPSTREAM_COMMIT_FILE" ]; then
    echo "❌ Error: UPSTREAM_COMMIT file not found at $UPSTREAM_COMMIT_FILE"
    echo "Run: make generate gx"
    exit 1
fi

cd "$SUBMODULE_DIR"
SUBMODULE_REF=$(git describe --tags --always --dirty 2>/dev/null || git rev-parse --short HEAD)
SUBMODULE_COMMIT=$(git rev-parse HEAD)
SUBMODULE_SHORT_COMMIT=$(git rev-parse --short HEAD)

VERSION_FILE_CONTENT=$(tr -d '[:space:]' < "$VERSION_FILE")
RECORDED_UPSTREAM_COMMIT=$(tr -d '[:space:]' < "$UPSTREAM_COMMIT_FILE")
if [ -f "$UPSTREAM_REF_FILE" ]; then
    RECORDED_UPSTREAM_REF=$(tr -d '\r' < "$UPSTREAM_REF_FILE")
else
    RECORDED_UPSTREAM_REF="(not recorded)"
fi

echo "Gaia-X label:          $VERSION_FILE_CONTENT"
echo "Recorded upstream ref: $RECORDED_UPSTREAM_REF"
echo "Recorded commit:       $RECORDED_UPSTREAM_COMMIT"
echo "Submodule ref:         $SUBMODULE_REF"
echo "Submodule commit:      $SUBMODULE_COMMIT"
echo ""

if [ "$RECORDED_UPSTREAM_COMMIT" = "$SUBMODULE_COMMIT" ]; then
    echo "✓ Upstream metadata matches the checked-out submodule."
    echo ""
    echo "The VERSION file is a Gaia-X release label for OMB docs."
    echo "The recorded commit is the source of truth for submodule synchronization."
    exit 0
else
    echo "❌ Upstream sync mismatch!"
    echo ""
    echo "Recorded commit:  $RECORDED_UPSTREAM_COMMIT"
    echo "Submodule commit: $SUBMODULE_COMMIT"
    echo ""
    echo "To update, run:"
    echo "  make generate gx"
    echo ""
    echo "Current submodule short SHA: $SUBMODULE_SHORT_COMMIT"
    exit 1
fi
