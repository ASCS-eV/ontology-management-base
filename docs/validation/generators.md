# Generating contexts and property documentation

The installed commands accept a caller-owned artifact directory and an output
directory. An artifact directory contains one folder per ontology domain:

```text
my-artifacts/
└── demo/
    ├── demo.owl.ttl
    └── demo.shacl.ttl
```

## JSON-LD contexts

```bash
onto-generate-context --domain demo --artifacts ./my-artifacts --output ./contexts
onto-generate-context --all --artifacts ./my-artifacts --output ./contexts
```

The output is `contexts/demo/demo.context.jsonld`. `--dry-run` generates the
context without writing files, and `--exclude DOMAIN ...` skips selected domains
with `--all`. Repeating generation with identical inputs leaves context files
unchanged.

`--test-roundtrip demo --instance ./instance.json --output ./contexts` compares
the RDF produced with the selected context against the original instance.
Instances should use locally resolvable or inline contexts for offline checks.

## Property documentation

```bash
onto-generate-docs --artifacts ./my-artifacts --output ./reference
```

The command creates:

- `reference/artifacts/demo/PROPERTIES.md`: class and property reference.
- `reference/docs/ontologies/catalog.md`: ontology catalog.
- `reference/docs/ontologies/properties.md`: domain overview.
- `reference/docs/ontologies/properties/demo.md`: domain documentation page.
- `reference/docs/artifacts/demo/<version>/`: copies of the source artifacts and
  property reference used by the generated links and Markdown snippets.
- `reference/docs/registry.json`: current input-domain metadata.

No pre-existing registry or documentation template is required. The current
version comes from the domain's `VERSION` file, then `owl:versionInfo`, or
`vunknown` if neither is available. The pages use the repository's MkDocs snippet
syntax, with `reference/docs` as the documentation root.

When `catalog.md` already exists, generation replaces only the table between
`<!-- START_REGISTRY_TABLE -->` and `<!-- END_REGISTRY_TABLE -->`. Surrounding
text and comments are preserved. An existing page without these markers is an
error.

## Defaults and failures

Without `--artifacts`, both commands read the bundled ontology artifacts.
Installed commands default to `./generated-contexts` and `./generated-docs` for
output, and reject output inside the installed package. Supplying `--artifacts`
also selects these caller-directory defaults when running from source.

In a source checkout, omitting both path flags preserves the contributor
workflow: contexts update `artifacts/`, and documentation updates `artifacts/`
and `docs/` using the existing release registry. The context generator preserves
the source pipeline's LinkML exclusions, including the externally maintained
`gx` context. Caller-provided artifact roots do not inherit those source-domain
exclusions.

Successful generation and unchanged context output return exit code `0`.
Missing or invalid input, no eligible domains, parsing errors, and write errors
return `1`. Invalid command-line syntax returns `2`. A failed run can leave
outputs from earlier domains; failure never reports them as an unchanged run.
Both entry points configure UTF-8 console output, including installed scripts.
