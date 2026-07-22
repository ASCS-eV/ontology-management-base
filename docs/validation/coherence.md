# Target Class Coherence

The coherence validator checks that SHACL target classes exist in the OWL ontology.

## Recommended Usage

```bash
python3 -m omb.validators.validation_suite --run check-artifact-coherence --domain hdmap
```

## Direct Module Usage

```bash
python3 -m omb.validators.coherence_validator hdmap
```

## Behavior

- Loads the domain OWL and SHACL files from catalogs
- Includes base classes from `imports/`
- Fails if SHACL files are missing

