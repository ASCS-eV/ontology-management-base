# Gaia-X Ontology & SHACL Shapes

> 📝 **Catalog Registration:** The SHACL shapes are now registered in the ontology catalog with IRI `https://w3id.org/gaia-x/development#shapes`. This enables automatic discovery and resolution of shapes during validation workflows.

## Overview

This folder contains the **Gaia-X Trust Framework ontology and SHACL shapes** (version 25.11+fix.5).

- The **Gaia-X model** (ontology) defines concepts for the Gaia-X Trust Framework including Participants, Services, Credentials, and Compliance.
- The **SHACL shapes** automatically verify that Gaia-X instances conform to the Trust Framework specifications.
- The core Gaia-X ontologies are integrated as a **Git submodule** to ensure version consistency with upstream.
- The **VERSION file** in this directory tracks the Gaia-X release label used in OMB tooling and documentation.
- The **UPSTREAM_REF** and **UPSTREAM_COMMIT** files record the exact `service-characteristics` checkout used to generate the copied artifacts.

### Current Version: 25.11+fix.5

This version is based on the official **25.11 release** with the following additional fixes:

- **Commit eea7ae71**: Fix double hash fragments in IRIs (fixes enum IRI generation)
- **Commit 32394e25**: fix(linkml): rename httpsschema using LinkML-compatible schema URI
- **Commit 33e9e75c**: fix(ci): use patched LinkML for correct any_of type coercion
- **Commit 74e03101**: fix(linkml): rename waterUsageEffectiveness value slot to avoid collision
- **Commit bfb9c620**: chore: switch to ASCS-eV/linkml.git@main

The `+fix.5` suffix indicates this is a post-release patch on top of 25.11. When the upstream releases a later version that includes these fixes, we will update to the official release tag.

## IRI Notes (Enum Values)

The OWL generator now uses a non-hash enum separator (`/`) to avoid double-hash
fragments in enum IRIs. As a result, enum IRIs are emitted like:

```
https://w3id.org/gaia-x/development#GaiaXTermsAndConditions/<hash>
```

This change causes a large diff in the generated OWL because all enum IRIs are
rewritten. It also introduces percent-encoding for reserved characters in enum
values (for example `%20` for spaces and `%2F` for `/`). This is expected and
keeps IRIs valid.

---

## Capabilities

- Describe Gaia-X Participants, Services, and Credentials in **JSON-LD**.
- Validate instances against Gaia-X Trust Framework requirements.
- Ensure compliance with official Gaia-X specifications.

---

## Contents of this folder

- **`gx.owl.ttl`** – The Gaia-X ontology defining core trust framework concepts.
- **`gx.shacl.ttl`** – SHACL validation shapes for Gaia-X instances.
- **`gx.context.jsonld`** – JSON-LD context for GX terms.
- **`PROPERTIES.md`** – An auto-generated summary of SHACL properties.
- **`VERSION`** – Current Gaia-X release label (e.g., `25.11+fix.5`).
- **`UPSTREAM_REF`** – Human-readable `service-characteristics` ref used for generation.
- **`UPSTREAM_COMMIT`** – Exact `service-characteristics` commit used for generation.
- **`VERSIONING.md`** – Detailed versioning scheme and post-release patch documentation.
- **`README.md`** – This readme file.
- **`update-from-submodule.sh`** – Helper script to rebuild and sync artifacts from the submodule.
- **`verify-version.sh`** – Verify recorded upstream provenance matches the submodule checkout.

---

## Submodule Integration

The core Gaia-X ontologies are maintained in an upstream GitLab repository:

- **Upstream Source:** [Gaia-X Service Characteristics](https://gitlab.com/gaia-x/technical-committee/service-characteristics-working-group/service-characteristics)
- **Current Gaia-X Label:** `25.11+fix.5`
- **Submodule Location:** `submodules/service-characteristics`

> **Note:** The `gx/` directory contains copies of the ontology and shapes for local examples and validation. The actual submodule is located at `submodules/service-characteristics`.

---

## How to Initialize the Submodule

If you haven't already initialized the Gaia-X submodule, run:

```bash
git submodule update --init --recursive
```

To inspect the current submodule checkout:

```bash
cd submodules/service-characteristics
git status
git describe --tags --always --dirty
```

---

## How to Run SHACL Validation Tests

See the root guide for the canonical commands and explanations:  
[Running Tests Locally](../../README.md#validation)

Example command for this folder:

```bash
python3 -m src.tools.validators.validation_suite \
  --run check-data-conformance \
  --domain gx
```

---

## Updating to a New Gaia-X Version

### Automated update (recommended)

From the ontology-management-base root, run:

```bash
make generate gx
# OR
make generate gx GX_REF=25.12
```

This command invokes `artifacts/gx/update-from-submodule.sh`, which will:

1. Check out the specified submodule ref (if provided)
2. Rebuild GX artifacts using the `service-characteristics` build commands
3. Copy artifacts (OWL, SHACL, context) from the submodule to `artifacts/gx/`
4. Record the exact upstream ref and commit used to generate the copied artifacts
5. Update `VERSION` automatically only when the submodule is on an exact tag
6. Show next steps for documentation regeneration

You can still run the helper script directly if needed:

```bash
cd artifacts/gx
./update-from-submodule.sh 25.12
./update-from-submodule.sh
```

### Manual update

When a new version of Gaia-X is released:

1. Navigate to the submodule:

   ```bash
   cd submodules/service-characteristics
   ```

2. Check out the new version tag:

   ```bash
   git checkout <new-tag>  # e.g., git checkout 25.12
   ```

3. Rebuild the upstream artifacts:

   ```bash
   bash ./merge_schemas.sh shacl
   bash ./merge_schemas.sh owl
   gen-jsonld-context linkml/gaia-x.yaml --no-mergeimports > context.jsonld
   ```

4. Copy the updated artifacts to `artifacts/gx/`:

   ```bash
   cd ../..
   cp submodules/service-characteristics/ontology.owl.ttl artifacts/gx/gx.owl.ttl
   cp submodules/service-characteristics/shapes.shacl.ttl artifacts/gx/gx.shacl.ttl
   cp submodules/service-characteristics/context.jsonld artifacts/gx/gx.context.jsonld
   ```

5. **Update the VERSION file** to match the new Gaia-X release label:

   ```bash
   echo "25.12" > artifacts/gx/VERSION
   ```

6. Record the exact upstream provenance:

   ```bash
   git -C submodules/service-characteristics describe --tags --always --dirty > artifacts/gx/UPSTREAM_REF
   git -C submodules/service-characteristics rev-parse HEAD > artifacts/gx/UPSTREAM_COMMIT
   ```

7. Regenerate documentation and commit:

   ```bash
   python3 -m src.tools.utils.registry_updater
   python3 -m src.tools.utils.properties_updater
   git add artifacts/gx/ submodules/service-characteristics
   git commit -m "chore(gx): upgrade Gaia-X to 25.12"
   ```

### Verify version sync

To check if the recorded upstream provenance matches the submodule checkout:

```bash
cd artifacts/gx
./verify-version.sh
```

!!! warning "VERSION and provenance metadata matter"
The `VERSION` file is used as the Gaia-X release label in OMB documentation, while `UPSTREAM_COMMIT` is the source of truth for submodule synchronization. Keep both up to date when refreshing `artifacts/gx/`.

---

## See Also

- [Ontology Domains](../../docs/ontologies/catalog.md) – Browse all available ontologies
- [Validation Tools](../../docs/validation/tools.md) – Complete validation tool reference
- [Architecture](../../docs/discovery/catalogs.md) – Technical details about the ontology structure
- [Gaia-X Trust Framework](https://gaia-x.eu/) – Official Gaia-X website
