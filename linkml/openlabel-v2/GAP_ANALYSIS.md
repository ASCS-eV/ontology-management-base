# OpenLabel v2 — Known Limitations

Functional differences between the LinkML-generated v2 artifacts and the
handcrafted v1 artifacts that affect validation behaviour. Cosmetic
differences (label formatting, metadata annotations, OWL type precision)
are intentional improvements and not listed here.

---

## L1. Conditional constraints modeled but not yet in SHACL output

v1 SHACL uses 16 `sh:sparql` rules enforcing: *"if boolean flag is absent
or false, the corresponding value must not be present"*. All 16 flag↔value
pairs are now modeled as LinkML `rules:` with `value_presence` /
`equals_string` postconditions on the `Odd` and `Behaviour` classes.

**Schema status:** ✅ All 16 rules defined in `openlabel-v2.yaml`.

**SHACL status:** ❌ `gen-shacl` silently ignores `rules:` blocks
([linkml/linkml#2464](https://github.com/linkml/linkml/issues/2464)).
When that upstream issue ships, SHACL constraints will be generated
automatically — no schema changes needed.

**Impact:** Data with a value but no corresponding flag=true will pass v2
SHACL validation but would fail v1. The constraints *are* enforceable via
`linkml-validate` (JSON Schema path).

---

## Cosmetic differences (intentional, not limitations)

These are deliberate improvements or generator-default behaviors:

- **No `@en` language tags** — gen-owl emits plain literals; upstream
  enhancement needed for `in_language` support.
- **No `sh:name`/`sh:message`** — gen-shacl uses default pyshacl messages;
  no schema mapping exists for these SHACL-specific annotations.
- **`sh:class` instead of `sh:node`** — functionally equivalent; `sh:class`
  is arguably more correct (checks `rdf:type` rather than shape conformance).
