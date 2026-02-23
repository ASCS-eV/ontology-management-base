#!/usr/bin/env python3
"""
Catalog-driven resolution for ontology and SHACL file paths.

The RegistryResolver loads XML catalogs to resolve:
- Ontology domains to their OWL file paths (artifacts/catalog-v001.xml)
- SHACL shapes for a given domain (artifacts/catalog-v001.xml)
- Base ontologies for inference (imports/catalog-v001.xml)
- Test data and fixtures (tests/catalog-v001.xml)
- DID documents for linked data validation (via register_did_documents)

docs/registry.json is still loaded for metadata, but runtime path resolution
is driven by the catalogs for consistency.

EXTERNAL REGISTRATION:
=====================
For cross-repository validation, external artifacts and DID documents can be
registered at runtime:

    # Register external artifact directories
    resolver.register_artifact_directory(Path("../other-repo/artifacts"))

    # Register fixture mappings (from discover_data_hierarchy)
    resolver.register_fixture_mappings(iri_to_file_map)

Usage:
    from src.tools.utils import RegistryResolver

    resolver = RegistryResolver()
    owl_path = resolver.get_ontology_path("general")
    shacl_paths = resolver.get_shacl_paths("general")

    # Discover required schemas based on RDF types
    rdf_types = {"https://example.org/ontology/MyClass"}
    ontology_paths, shacl_paths = resolver.discover_required_schemas(rdf_types)

    # Resolve DID document to local file
    fixture_path = resolver.resolve_fixture_iri("did:web:example.com:entity:123")

See also:
    - artifacts/catalog-v001.xml
    - imports/catalog-v001.xml
    - tests/catalog-v001.xml
    - src.tools.validators.shacl: Main consumer of this utility
"""

import json
import warnings
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Prefix for temporary domains created by --data-paths mode.
TEMP_DOMAIN_PREFIX = "custom-path-"


class RegistryResolver:
    """
    Resolves ontology files using XML catalogs.

    Usage:
        resolver = RegistryResolver(root_dir="/path/to/repo")
        owl_path = resolver.get_ontology_path("scenario")
        shacl_paths = resolver.get_shacl_paths("scenario")
        domains = resolver.list_domains()
    """

    def __init__(self, root_dir: Path = None):
        """
        Initialize the registry resolver.

        Args:
            root_dir: Root directory of the repository. Defaults to current directory.
        """
        self.root_dir = Path(root_dir or Path.cwd()).resolve()
        self._registry: Dict = {}
        self._catalog: Dict[str, Dict] = {}  # Full catalog (test-data + fixtures)
        self._fixtures_catalog: Dict[str, str] = {}  # Fixture IRIs only
        self._artifact_domains: Dict[str, Dict[str, object]] = {}
        self._domain_iris: Dict[str, str] = {}
        self._iri_to_domain: Dict[str, str] = {}
        self._imports_catalog_entries: Optional[Dict[str, str]] = None
        self._imports_context_entries: Optional[Dict[str, str]] = None

        self._load_registry()
        self._load_catalog()  # Replaces _load_fixtures_catalog
        self._load_artifacts_catalog()
        self._build_iri_index()

    def _load_registry(self) -> None:
        """Load docs/registry.json."""
        registry_path = self.root_dir / "docs" / "registry.json"
        if not registry_path.exists():
            warnings.warn(f"Registry file not found: {registry_path}")
            return

        try:
            with registry_path.open("r", encoding="utf-8") as f:
                self._registry = json.load(f)
        except Exception as e:
            warnings.warn(f"Could not load registry: {e}")

    def _load_catalog(self) -> None:
        """
        Load unified test catalog for test data discovery and fixture resolution.

        Loads all catalog entries including test-data, fixtures, and other categories.
        """
        catalog_path = self.root_dir / "tests" / "catalog-v001.xml"

        if not catalog_path.exists():
            return

        try:
            tree = ET.parse(catalog_path)
            root = tree.getroot()
            ns = {"cat": "urn:oasis:names:tc:entity:xmlns:xml:catalog"}

            # Parse with namespace first
            for uri_elem in root.findall("cat:uri", ns):
                test_id = uri_elem.get("name")
                path = uri_elem.get("uri")
                domain = uri_elem.get("domain")
                test_type = uri_elem.get("test-type")
                category = uri_elem.get("category")

                if test_id and path:
                    self._catalog[test_id] = {
                        "path": path,
                        "domain": domain,
                        "test_type": test_type,
                        "category": category,
                    }

                    if category == "fixture":
                        self._fixtures_catalog[test_id] = path

            # Try without namespace if nothing found
            if not self._catalog:
                for uri_elem in root.findall("uri"):
                    test_id = uri_elem.get("name")
                    path = uri_elem.get("uri")
                    domain = uri_elem.get("domain")
                    test_type = uri_elem.get("test-type")
                    category = uri_elem.get("category")

                    if test_id and path:
                        self._catalog[test_id] = {
                            "path": path,
                            "domain": domain,
                            "test_type": test_type,
                            "category": category,
                        }

                        if category == "fixture":
                            self._fixtures_catalog[test_id] = path

        except Exception as e:
            warnings.warn(f"Could not parse test catalog: {e}")

    def _normalize_catalog_path(self, base_dir: str, uri: str) -> Path:
        """
        Normalize a catalog URI to a repository-relative path.

        Args:
            base_dir: Base directory for relative paths (e.g., "artifacts", "imports")
            uri: URI attribute from catalog entry

        Returns:
            Repository-relative Path
        """
        uri_path = Path(uri)
        if uri_path.is_absolute():
            return Path(self.to_relative(uri_path))
        if uri_path.parts and uri_path.parts[0] == base_dir:
            return uri_path
        return Path(base_dir) / uri_path

    def _extract_domain_from_artifact_path(self, rel_path: Path) -> Optional[str]:
        """
        Extract domain name from an artifacts catalog path.

        Args:
            rel_path: Repository-relative path to an artifact file

        Returns:
            Domain name or None if not determinable
        """
        parts = rel_path.parts
        if not parts:
            return None
        if parts[0] == "artifacts" and len(parts) > 1:
            return parts[1]
        return parts[0]

    def _load_artifacts_catalog(self) -> None:
        """
        Load artifacts/catalog-v001.xml for ontology and SHACL resolution.

        Populates:
            - _artifact_domains: domain -> files (ontology, shacl, jsonld)
            - _domain_iris: domain -> ontology IRI
        """
        catalog_path = self.root_dir / "artifacts" / "catalog-v001.xml"
        if not catalog_path.exists():
            warnings.warn(f"Artifacts catalog not found: {catalog_path}")
            return

        try:
            tree = ET.parse(catalog_path)
            root = tree.getroot()
        except Exception as e:
            warnings.warn(f"Could not parse artifacts catalog: {e}")
            return

        ns = {"cat": "urn:oasis:names:tc:entity:xmlns:xml:catalog"}
        uri_elems = root.findall("cat:uri", ns)
        if not uri_elems:
            uri_elems = root.findall("uri")

        for uri_elem in uri_elems:
            iri = uri_elem.get("name")
            uri = uri_elem.get("uri")
            if not iri or not uri:
                continue

            rel_path = self._normalize_catalog_path("artifacts", uri)
            domain = self._extract_domain_from_artifact_path(rel_path)
            if not domain:
                continue

            if domain not in self._artifact_domains:
                self._artifact_domains[domain] = {
                    "ontology": None,
                    "shacl": [],
                    "jsonld": None,
                }

            if self._is_context_path(rel_path):
                if self._artifact_domains[domain]["jsonld"] is None:
                    self._artifact_domains[domain]["jsonld"] = rel_path.as_posix()
                continue

            if self._is_shacl_path(rel_path):
                shacl_list = self._artifact_domains[domain]["shacl"]
                shacl_path = rel_path.as_posix()
                if shacl_path not in shacl_list:
                    shacl_list.append(shacl_path)
                continue

            if self._is_ontology_file(rel_path):
                if self._artifact_domains[domain]["ontology"] is None:
                    self._artifact_domains[domain]["ontology"] = rel_path.as_posix()
                if domain not in self._domain_iris:
                    self._domain_iris[domain] = iri

        # Normalize SHACL lists for consistent output
        for info in self._artifact_domains.values():
            info["shacl"] = sorted(set(info["shacl"]))

    def _parse_imports_catalog_entries(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Parse imports/catalog-v001.xml into ontology and context mappings.

        Returns:
            Tuple of:
              - ontology IRI -> repository-relative ontology path
              - context URL -> repository-relative context path
        """
        catalog_path = self.root_dir / "imports" / "catalog-v001.xml"
        if not catalog_path.exists():
            return {}, {}

        try:
            tree = ET.parse(catalog_path)
            root = tree.getroot()
        except Exception as e:
            warnings.warn(f"Could not parse imports catalog: {e}")
            return {}, {}

        ns = {"cat": "urn:oasis:names:tc:entity:xmlns:xml:catalog"}
        uri_elems = root.findall("cat:uri", ns)
        if not uri_elems:
            uri_elems = root.findall("uri")

        ontology_entries: Dict[str, str] = {}
        context_entries: Dict[str, str] = {}

        for uri_elem in uri_elems:
            iri = uri_elem.get("name")
            uri = uri_elem.get("uri")
            if not iri or not uri:
                continue

            rel_path = self._normalize_catalog_path("imports", uri)
            if self._is_context_path(rel_path):
                context_entries[iri] = rel_path.as_posix()
                continue
            if self._is_ontology_file(rel_path):
                ontology_entries[iri] = rel_path.as_posix()

        return ontology_entries, context_entries

    def _load_imports_catalog_entries(self) -> Dict[str, str]:
        """
        Load base ontology entries from imports/catalog-v001.xml.

        Returns:
            Mapping of base ontology IRI to repository-relative path
        """
        ontology_entries, context_entries = self._parse_imports_catalog_entries()
        self._imports_context_entries = context_entries
        return ontology_entries

    def _load_imports_context_entries(self) -> Dict[str, str]:
        """
        Load JSON-LD context entries from imports/catalog-v001.xml.

        Returns:
            Mapping of context URL to repository-relative context file path
        """
        ontology_entries, context_entries = self._parse_imports_catalog_entries()
        self._imports_catalog_entries = ontology_entries
        return context_entries

    @staticmethod
    def _is_context_path(path: Path) -> bool:
        path_str = path.as_posix().lower()
        return path_str.endswith((".context.jsonld", ".context.json"))

    @staticmethod
    def _is_shacl_path(path: Path) -> bool:
        path_str = path.as_posix().lower()
        return ".shacl." in path_str or path_str.endswith(".shacl.ttl")

    @classmethod
    def _is_ontology_file(cls, path: Path) -> bool:
        """
        Check if a catalog entry looks like an ontology file (not context/shapes).

        Args:
            path: Path to check (relative)

        Returns:
            True if path is a likely ontology file
        """
        if cls._is_context_path(path):
            return False
        if cls._is_shacl_path(path):
            return False
        return path.suffix.lower() in {".ttl", ".rdf", ".owl", ".xml", ".nt", ".n3"}

    def _build_iri_index(self) -> None:
        """Build IRI -> domain mapping from artifacts catalog."""
        self._iri_to_domain = {}
        for domain, iri in self._domain_iris.items():
            if iri:
                self._iri_to_domain[iri] = domain
                base_iri = iri.rstrip("/")
                if base_iri != iri:
                    self._iri_to_domain[base_iri] = domain

    # =========================================================================
    # Core Methods (return repo-relative paths as strings)
    # =========================================================================

    def list_domains(self) -> List[str]:
        """
        List all ontology domains available in the artifacts catalog.

        Returns:
            List of domain names sorted alphabetically
        """
        return sorted(self._artifact_domains.keys())

    def get_ontology_path(self, domain: str) -> Optional[str]:
        """
        Get the ontology (.owl.ttl) file path for a domain.

        Args:
            domain: Domain name (e.g., "scenario", "hdmap")

        Returns:
            Repository-relative path to the ontology file, or None if not found
        """
        info = self._artifact_domains.get(domain)
        if not info:
            return None
        return info.get("ontology")

    def get_shacl_paths(self, domain: str) -> List[str]:
        """
        Get all SHACL shapes (.shacl.ttl) file paths for a domain.

        Args:
            domain: Domain name (e.g., "scenario", "survey")

        Returns:
            List of repository-relative paths to SHACL files
        """
        info = self._artifact_domains.get(domain)
        if not info:
            return []
        return list(info.get("shacl") or [])

    def get_context_path(self, domain: str) -> Optional[str]:
        """
        Get the JSON-LD context (.context.jsonld) file path for a domain.

        Args:
            domain: Domain name (e.g., "gx")

        Returns:
            Repository-relative path to the context file, or None if not found
        """
        info = self._artifact_domains.get(domain)
        if not info:
            return None
        return info.get("jsonld")

    def get_iri(self, domain: str) -> Optional[str]:
        """
        Get the IRI for a domain.

        Args:
            domain: Domain name (e.g., "scenario")

        Returns:
            IRI string, or None if not found
        """
        return self._domain_iris.get(domain)

    def get_base_ontology_paths(self) -> List[str]:
        """
        Get paths to base ontologies required for RDFS inference.

        Base ontologies (RDF, RDFS, OWL, SKOS, etc.) are registered in
        the imports/ directory and listed in imports/catalog-v001.xml.

        Returns:
            List of repository-relative paths to base ontology files
        """
        if self._imports_catalog_entries is None:
            self._imports_catalog_entries = self._load_imports_catalog_entries()
        if self._imports_catalog_entries:
            return sorted(set(self._imports_catalog_entries.values()))
        return []

    def get_import_context_mappings(self) -> Dict[str, str]:
        """
        Get import context URL mappings from imports/catalog-v001.xml.

        Returns:
            Dict mapping context URL -> repository-relative context path
        """
        if self._imports_context_entries is None:
            self._imports_context_entries = self._load_imports_context_entries()
        return dict(self._imports_context_entries or {})

    def get_base_ontology_paths_for_iris(self, iris: Set[str]) -> List[str]:
        """
        Get base ontologies filtered by actual IRI usage.

        Args:
            iris: Set of IRIs referenced in the data graph

        Returns:
            List of repository-relative paths to base ontology files
        """
        if self._imports_catalog_entries is None:
            self._imports_catalog_entries = self._load_imports_catalog_entries()
        if not self._imports_catalog_entries:
            return []

        matches: List[str] = []
        for base_iri, path in self._imports_catalog_entries.items():
            if self._iri_matches_base(iris, base_iri):
                matches.append(path)

        return sorted(set(matches))

    @staticmethod
    def _iri_matches_base(iris: Set[str], base_iri: str) -> bool:
        candidates = {base_iri}
        if base_iri.startswith("http://"):
            candidates.add("https://" + base_iri[len("http://") :])
        elif base_iri.startswith("https://"):
            candidates.add("http://" + base_iri[len("https://") :])

        for candidate in candidates:
            base = candidate.rstrip("#/")
            for iri in iris:
                if iri == candidate or iri.startswith(candidate):
                    return True
                if iri.startswith(base + "/") or iri.startswith(base + "#"):
                    return True
        return False

    # =========================================================================
    # Test Catalog Methods
    # =========================================================================

    def get_test_files(
        self, domain: str, test_type: str = None, category: str = "test-data"
    ) -> List[Path]:
        """
        Get test files for a specific domain from the catalog.

        Args:
            domain: Domain name (e.g., "scenario", "manifest")
            test_type: Optional filter: "valid", "invalid", "custom", or None for all
            category: Category filter: "test-data" (default), "fixture", etc.

        Returns:
            List of absolute paths to test files
        """
        test_files = set()

        for test_id, metadata in self._catalog.items():
            if (
                metadata.get("category") == category
                and metadata.get("domain") == domain
            ):
                if test_type is None or metadata.get("test_type") == test_type:
                    file_path = self.root_dir / metadata["path"]
                    if file_path.exists():
                        test_files.add(file_path)

        return sorted(test_files)

    def get_all_cataloged_files(
        self,
        extensions: set = None,
        include_artifacts: bool = True,
        domains: List[str] = None,
    ) -> Dict[str, List[Path]]:
        """
        Get all files from catalogs, grouped by extension.

        This provides a clean API for syntax checking without direct catalog access.
        Collects files from both the tests catalog and artifacts catalog.

        Args:
            extensions: Optional set of extensions to filter (e.g., {".json", ".ttl"}).
                       If None, returns all files.
            include_artifacts: If True (default), also include OWL, SHACL, and context
                              files from the artifacts catalog.
            domains: Optional list of domains to filter. If None, returns files from
                    all domains.

        Returns:
            Dict mapping extension to list of absolute file paths.
            Example: {".json": [Path(...), ...], ".ttl": [Path(...), ...]}
        """
        files_by_ext: Dict[str, List[Path]] = {}
        domains_set = set(domains) if domains else None

        def add_file(file_path: Path) -> None:
            """Helper to add a file to the appropriate extension list."""
            if not file_path.exists():
                return
            ext = file_path.suffix
            if extensions is None or ext in extensions:
                if ext not in files_by_ext:
                    files_by_ext[ext] = []
                files_by_ext[ext].append(file_path)

        # 1. Files from tests catalog
        for metadata in self._catalog.values():
            path_str = metadata.get("path")
            if not path_str:
                continue

            # Filter by domain if specified
            if domains_set:
                entry_domain = metadata.get("domain")
                if entry_domain and entry_domain not in domains_set:
                    continue

            if Path(path_str).is_absolute():
                file_path = Path(path_str)
            else:
                file_path = self.root_dir / path_str

            add_file(file_path)

        # 2. Files from artifacts catalog (OWL, SHACL, context)
        if include_artifacts:
            for domain, paths in self._artifact_domains.items():
                # Filter by domain if specified
                if domains_set and domain not in domains_set:
                    continue

                # OWL ontology
                if paths.get("ontology"):
                    add_file(self.root_dir / paths["ontology"])

                # SHACL shapes
                for shacl in paths.get("shacl", []):
                    add_file(self.root_dir / shacl)

                # JSON-LD context
                if paths.get("context"):
                    add_file(self.root_dir / paths["context"])

        # Sort and deduplicate each list
        for ext in files_by_ext:
            files_by_ext[ext] = sorted(set(files_by_ext[ext]))

        return files_by_ext

    def get_test_domains(self, category: str = "test-data") -> List[str]:
        """
        Get list of all test domains in the catalog.

        Args:
            category: Category filter (default: "test-data")

        Returns:
            Sorted list of domain names
        """
        domains = set()
        for metadata in self._catalog.values():
            if metadata.get("category") == category:
                domain = metadata.get("domain")
                if domain:
                    domains.add(domain)
        return sorted(domains)

    def get_artifact_domains(self) -> List[str]:
        """
        Get list of all artifact domains (from artifacts catalog).

        Returns:
            Sorted list of domain names that have registered artifacts
        """
        return sorted(self._artifact_domains.keys())

    def is_catalog_loaded(self) -> bool:
        """
        Check if catalog is loaded and has entries.

        Returns:
            True if catalog has entries, False otherwise
        """
        return len(self._catalog) > 0

    def add_temporary_test_entries(
        self, domain: str, file_paths: List[Path], test_type: str = "valid"
    ) -> None:
        """
        Add temporary catalog entries for custom file paths.

        Useful for validating arbitrary files using catalog infrastructure.

        Args:
            domain: Temporary domain name to use
            file_paths: List of file paths to add to catalog
            test_type: Test type identifier (default: "valid")
        """
        for i, file_path in enumerate(file_paths):
            file_path = Path(file_path)
            if not file_path.is_absolute():
                file_path = (self.root_dir / file_path).resolve()

            # Create relative path from root
            try:
                rel_path = file_path.relative_to(self.root_dir)
            except ValueError:
                # File is outside repo, use absolute path
                rel_path = file_path

            test_id = f"temporary:{domain}:file{i:03d}"
            self._catalog[test_id] = {
                "path": str(rel_path),
                "domain": domain,
                "test_type": test_type,
                "category": "test-data",
            }

    def create_temporary_domain(self, paths: List[str]) -> Optional[str]:
        """
        Create a temporary domain from file paths for validation.

        Collects JSON-LD files from paths and adds them as temporary catalog entries.

        Args:
            paths: List of file or directory paths

        Returns:
            Temporary domain name, or None if no files found
        """
        import hashlib

        from src.tools.utils.file_collector import collect_jsonld_files

        # Generate unique domain name from paths
        path_hash = hashlib.md5("|".join(sorted(paths)).encode()).hexdigest()[:8]
        temp_domain = f"{TEMP_DOMAIN_PREFIX}{path_hash}"

        # Collect all JSON-LD files from provided paths
        jsonld_files = collect_jsonld_files(paths)

        if not jsonld_files:
            return None

        # Convert to Path objects
        file_paths = [Path(f) for f in jsonld_files]

        # Add temporary entries to catalog
        self.add_temporary_test_entries(temp_domain, file_paths, test_type="valid")

        print(
            f"📋 Created temporary domain '{temp_domain}' with {len(file_paths)} file(s)",
            flush=True,
        )

        return temp_domain

    def register_artifact_directory(self, artifact_dir: Path) -> List[str]:
        """
        Register an external artifact directory with the resolver.

        Scans ``artifact_dir`` for domain subdirectories, each containing
        ``{domain}.owl.ttl``, ``{domain}.shacl.ttl``, and
        ``{domain}.context.jsonld`` files.  Reads ``@vocab`` from context
        files to determine the ontology IRI for each domain.

        This enables consuming repositories to register their own generated
        artifacts so the validation pipeline can discover schemas, inline
        contexts, and resolve types for domains not present in the base
        catalog.

        Args:
            artifact_dir: Absolute path to an artifacts directory.
                          Expected structure: ``artifact_dir/{domain}/{domain}.*``

        Returns:
            List of domain names that were registered.
        """
        import json as _json

        artifact_dir = Path(artifact_dir).resolve()
        registered: List[str] = []

        if not artifact_dir.is_dir():
            return registered

        for child in sorted(artifact_dir.iterdir()):
            if not child.is_dir():
                continue

            domain = child.name
            owl_path = child / f"{domain}.owl.ttl"
            shacl_path = child / f"{domain}.shacl.ttl"
            context_path = child / f"{domain}.context.jsonld"

            # Need at least the ontology file
            if not owl_path.exists():
                continue

            # Determine repo-relative path for the domain
            try:
                rel_base = artifact_dir.relative_to(self.root_dir)
            except ValueError:
                # External directory — store absolute paths
                rel_base = artifact_dir

            owl_rel = (rel_base / domain / f"{domain}.owl.ttl").as_posix()
            shacl_rel = (rel_base / domain / f"{domain}.shacl.ttl").as_posix()
            ctx_rel = (rel_base / domain / f"{domain}.context.jsonld").as_posix()

            # Build artifact domain entry
            info: Dict[str, object] = {
                "ontology": owl_rel,
                "shacl": [shacl_rel] if shacl_path.exists() else [],
                "jsonld": ctx_rel if context_path.exists() else None,
            }
            self._artifact_domains[domain] = info

            # Extract IRI from context @vocab
            if context_path.exists():
                try:
                    with context_path.open("r", encoding="utf-8") as f:
                        ctx_data = _json.load(f)
                    context = ctx_data.get("@context", {})
                    vocab = None
                    if isinstance(context, dict):
                        vocab = context.get("@vocab")
                    elif isinstance(context, list):
                        for entry in context:
                            if isinstance(entry, dict) and "@vocab" in entry:
                                vocab = entry["@vocab"]
                                break
                    if vocab:
                        self._domain_iris[domain] = vocab
                except Exception:
                    pass

            registered.append(domain)

        # Rebuild IRI index with newly registered domains
        if registered:
            self._build_iri_index()

        return registered

    def register_fixture_mappings(self, mappings: Dict[str, Path]) -> int:
        """
        Register pre-computed IRI → file path mappings for fixture resolution.

        This is used by discover_data_hierarchy() to register all discovered
        files as potential fixtures.

        Args:
            mappings: Dictionary mapping IRIs to absolute file paths

        Returns:
            Number of fixtures registered
        """
        count = 0
        for iri, file_path in mappings.items():
            try:
                rel_path = str(file_path.relative_to(self.root_dir))
            except ValueError:
                rel_path = str(file_path)

            self._fixtures_catalog[iri] = rel_path
            count += 1

        return count

    # =========================================================================
    # Bulk Accessors
    # =========================================================================

    def get_all_ontology_paths(self) -> List[str]:
        """
        Get all ontology file paths from the artifacts catalog.

        Returns:
            List of repository-relative paths to all ontology files
        """
        paths = []
        for domain in self.list_domains():
            path = self.get_ontology_path(domain)
            if path:
                paths.append(path)
        return sorted(paths)

    def get_all_shacl_paths(self) -> List[str]:
        """
        Get all SHACL shape file paths from the artifacts catalog.

        Returns:
            List of repository-relative paths to all SHACL files
        """
        paths = []
        for domain in self.list_domains():
            paths.extend(self.get_shacl_paths(domain))
        return sorted(set(paths))

    # =========================================================================
    # IRI Resolution
    # =========================================================================

    def resolve_type_to_domain(self, rdf_type: str) -> Optional[str]:
        """
        Map an RDF type IRI to its domain name.

        Args:
            rdf_type: RDF type IRI (e.g., "https://w3id.org/ascs-ev/envited-x/scenario/v5/Scenario")

        Returns:
            Domain name if found, None otherwise
        """
        # Check exact match first
        if rdf_type in self._iri_to_domain:
            return self._iri_to_domain[rdf_type]

        # Check prefix match
        for iri, domain in self._iri_to_domain.items():
            if rdf_type.startswith(iri.rstrip("/") + "/"):
                return domain
            if rdf_type.startswith(iri.rstrip("#") + "#"):
                return domain

        return None

    def resolve_fixture_iri(self, iri: str) -> Optional[str]:
        """
        Resolve a fixture IRI to its local file path.

        Args:
            iri: Fixture IRI (e.g., "did:web:registry.gaia-x.eu:participant:...")

        Returns:
            Repository-relative path to the fixture file, or None if not found
        """
        return self._fixtures_catalog.get(iri)

    # =========================================================================
    # Path Helpers
    # =========================================================================

    def to_absolute(self, rel_path: str) -> Path:
        """
        Convert a repository-relative path to an absolute path.

        Args:
            rel_path: Repository-relative path string

        Returns:
            Absolute Path object
        """
        return self.root_dir / rel_path

    def to_relative(self, abs_path: Path) -> str:
        """
        Convert an absolute path to a repository-relative string.

        Args:
            abs_path: Absolute Path object

        Returns:
            Repository-relative path string
        """
        try:
            return str(abs_path.relative_to(self.root_dir))
        except ValueError:
            return str(abs_path)

    # =========================================================================
    # Discovery Methods
    # =========================================================================

    def discover_required_schemas(
        self, rdf_types: Set[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Discover required ontology and SHACL files based on RDF types.

        Args:
            rdf_types: Set of rdf:type IRIs found in the data

        Returns:
            Tuple of (ontology_paths, shacl_paths) as repository-relative strings
        """
        ontology_paths = []
        shacl_paths = []
        domains_found = set()

        for rdf_type in rdf_types:
            domain = self.resolve_type_to_domain(rdf_type)
            if domain and domain not in domains_found:
                domains_found.add(domain)

                ont_path = self.get_ontology_path(domain)
                if ont_path:
                    ontology_paths.append(ont_path)

                shacl_paths.extend(self.get_shacl_paths(domain))

        return sorted(set(ontology_paths)), sorted(set(shacl_paths))

    # =========================================================================
    # Info Methods
    # =========================================================================

    def get_registry_info(self) -> Dict:
        """
        Get information about the loaded registry.

        Returns:
            Dictionary with registry statistics and info
        """
        return {
            "root_dir": str(self.root_dir),
            "registry_version": self._registry.get("version"),
            "domains_available": len(self.list_domains()),
            "total_ontologies": len(self.get_all_ontology_paths()),
            "total_shacl_files": len(self.get_all_shacl_paths()),
            "fixture_mappings": len(self._fixtures_catalog),
        }


def print_registry_info(resolver: RegistryResolver) -> None:
    """
    Print registry information to console.

    Args:
        resolver: RegistryResolver instance
    """
    info = resolver.get_registry_info()
    print("Registry Resolver Information:")
    print(f"   Root: {info['root_dir']}")
    print(f"   Version: {info['registry_version']}")
    print(f"   Domains Available: {info['domains_available']}")
    print(f"   Total Ontologies: {info['total_ontologies']}")
    print(f"   Total SHACL Files: {info['total_shacl_files']}")
    print(f"   Fixture Mappings: {info['fixture_mappings']}")

    domains = resolver.list_domains()
    if domains:
        print(f"\nAvailable Domains ({len(domains)}):")
        for domain in domains[:10]:
            ont = resolver.get_ontology_path(domain)
            ont_status = "Y" if ont else "N"
            shacl_count = len(resolver.get_shacl_paths(domain))
            shacl_status = f"{shacl_count}" if shacl_count else "N"
            ctx = resolver.get_context_path(domain)
            ctx_status = "Y" if ctx else "N"
            print(
                f"   {domain}: OWL={ont_status} SHACL={shacl_status} Context={ctx_status}"
            )
        if len(domains) > 10:
            print(f"   ... and {len(domains) - 10} more")


if __name__ == "__main__":
    resolver = RegistryResolver()
    print_registry_info(resolver)

    print("\nTesting discovery for 'scenario' domain:")
    ont = resolver.get_ontology_path("scenario")
    shacl = resolver.get_shacl_paths("scenario")
    print(f"   Ontology: {ont}")
    print(f"   SHACL: {shacl}")
