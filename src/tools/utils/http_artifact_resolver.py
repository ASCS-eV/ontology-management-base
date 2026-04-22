#!/usr/bin/env python3
"""
HTTP-based artifact resolution for pip-only OMB installations.

When OMB is installed via ``pip install`` (without the full repository clone),
the local ``artifacts/``, ``imports/``, and ``tests/`` directories are absent.
This module fetches ontology artifacts from the published GitHub Pages site and
raw GitHub content, caching them locally so the existing catalog-driven
validation pipeline works unchanged.

DESIGN:
=======
1. Fetch ``docs/registry.json`` from GitHub Pages — contains all domain→IRI→files
2. Fetch the 3 XML catalogs (artifacts, imports, tests) from raw GitHub
3. For each needed domain, fetch OWL/SHACL/context files from w3id.org or GH Pages
4. Store everything in a cache directory that mirrors the repository structure
5. ``RegistryResolver`` uses the cache dir as ``root_dir``

CACHE STRUCTURE:
================
::

    ~/.cache/omb/{version}/
    ├── artifacts/
    │   ├── catalog-v001.xml
    │   └── {domain}/
    │       ├── {domain}.owl.ttl
    │       ├── {domain}.shacl.ttl
    │       └── {domain}.context.jsonld
    ├── imports/
    │   ├── catalog-v001.xml
    │   └── {module}/
    │       ├── {module}.owl.ttl
    │       └── {module}.context.jsonld
    ├── tests/
    │   └── catalog-v001.xml
    └── docs/
        └── registry.json

USAGE:
======
::

    from src.tools.utils.http_artifact_resolver import HttpArtifactResolver

    resolver = HttpArtifactResolver()
    cache_dir = resolver.ensure_cache()  # fetch everything needed
    # Then use: RegistryResolver(root_dir=cache_dir)

    # Or fetch only domains needed for specific IRIs:
    cache_dir = resolver.ensure_cache_for_iris(iris_set)
"""

import json
import os
import platform
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.tools.core.logging import get_logger

logger = get_logger(__name__)

# GitHub Pages base URL for published ontology artifacts.
GH_PAGES_BASE = "https://ascs-ev.github.io/ontology-management-base"

# Raw GitHub content for files not published to Pages (catalogs, imports).
RAW_GITHUB_BASE = (
    "https://raw.githubusercontent.com/ASCS-eV/ontology-management-base/main"
)

# Registry JSON URL (published via GH Pages docs workflow).
REGISTRY_URL = f"{GH_PAGES_BASE}/registry.json"

# W3ID artifact file names served by GitHub Pages.
W3ID_ARTIFACTS = {
    "ontology": "ontology.ttl",
    "shapes": "shapes.ttl",
    "context": "context.jsonld",
}

# Default HTTP timeout in seconds.
HTTP_TIMEOUT = 30

# Cache TTL: re-validate after this many seconds (24 hours).
CACHE_TTL_SECONDS = 86400


def _get_default_cache_dir() -> Path:
    """Return platform-appropriate cache directory for OMB artifacts."""
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "omb"


def _http_get(url: str, timeout: int = HTTP_TIMEOUT) -> bytes:
    """Fetch URL content with a simple GET request.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Response body as bytes

    Raises:
        URLError: On network failure
        HTTPError: On non-2xx response
    """
    request = Request(url, headers={"User-Agent": "ontology-management-base"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _http_get_with_accept(url: str, accept: str, timeout: int = HTTP_TIMEOUT) -> bytes:
    """Fetch URL with a specific Accept header (content-negotiation).

    Args:
        url: URL to fetch
        accept: Accept header value (e.g., "text/turtle")
        timeout: Request timeout in seconds

    Returns:
        Response body as bytes
    """
    request = Request(
        url,
        headers={
            "User-Agent": "ontology-management-base",
            "Accept": accept,
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read()


class HttpArtifactResolver:
    """Fetches and caches OMB ontology artifacts from HTTP sources.

    Attributes:
        cache_dir: Root cache directory (versioned subdirs created inside)
        gh_pages_base: GitHub Pages base URL
        raw_github_base: Raw GitHub content base URL
        registry_url: URL for docs/registry.json
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        gh_pages_base: str = GH_PAGES_BASE,
        raw_github_base: str = RAW_GITHUB_BASE,
        registry_url: str = REGISTRY_URL,
        timeout: int = HTTP_TIMEOUT,
    ):
        """Initialize the HTTP artifact resolver.

        Args:
            cache_dir: Override default cache directory.
            gh_pages_base: GitHub Pages base URL for w3id artifacts.
            raw_github_base: Raw GitHub content base URL for catalogs/imports.
            registry_url: URL for the domain registry JSON.
            timeout: HTTP request timeout in seconds.
        """
        self.cache_base = cache_dir or _get_default_cache_dir()
        self.gh_pages_base = gh_pages_base.rstrip("/")
        self.raw_github_base = raw_github_base.rstrip("/")
        self.registry_url = registry_url
        self.timeout = timeout
        self._registry: Optional[Dict] = None

    # =========================================================================
    # Registry Discovery
    # =========================================================================

    def fetch_registry(self) -> Dict:
        """Fetch and parse docs/registry.json from GitHub Pages.

        Returns:
            Parsed registry dictionary with domain metadata.

        Raises:
            RuntimeError: If registry cannot be fetched or parsed.
        """
        if self._registry is not None:
            return self._registry

        logger.info("Fetching registry from %s", self.registry_url)
        try:
            data = _http_get(self.registry_url, self.timeout)
            self._registry = json.loads(data.decode("utf-8"))
            logger.info(
                "Registry loaded: version=%s, domains=%d",
                self._registry.get("version", "?"),
                len(self._registry.get("ontologies", {})),
            )
            return self._registry
        except (HTTPError, URLError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"Failed to fetch registry from {self.registry_url}: {e}"
            ) from e

    def get_registry_version(self) -> str:
        """Get the latest release tag from the registry."""
        registry = self.fetch_registry()
        return registry.get("latestRelease", "unknown")

    def get_domain_info(self) -> Dict[str, Dict]:
        """Get domain→metadata mapping from the registry.

        Returns:
            Dict mapping domain name to its registry metadata
            (namespace, iri, latest version, file paths).
        """
        registry = self.fetch_registry()
        return registry.get("ontologies", {})

    # =========================================================================
    # Cache Management
    # =========================================================================

    def _versioned_cache_dir(self, version: Optional[str] = None) -> Path:
        """Get the versioned cache directory.

        Args:
            version: Explicit version string, or auto-detect from registry.

        Returns:
            Path to versioned cache directory.
        """
        if version is None:
            version = self.get_registry_version()
        return self.cache_base / version

    def is_cache_valid(self, cache_dir: Optional[Path] = None) -> bool:
        """Check if the cache is present and not stale.

        Args:
            cache_dir: Explicit cache directory, or auto-detect.

        Returns:
            True if cache exists and is fresh enough to use.
        """
        if cache_dir is None:
            try:
                cache_dir = self._versioned_cache_dir()
            except RuntimeError:
                return False

        marker = cache_dir / ".cache-timestamp"
        if not marker.exists():
            return False

        try:
            ts = float(marker.read_text().strip())
            return (time.time() - ts) < CACHE_TTL_SECONDS
        except (ValueError, OSError):
            return False

    def _write_cache_marker(self, cache_dir: Path) -> None:
        """Write a timestamp marker for cache freshness tracking."""
        marker = cache_dir / ".cache-timestamp"
        marker.write_text(str(time.time()))

    # =========================================================================
    # Fetching: Catalogs
    # =========================================================================

    def fetch_catalog(self, catalog_rel_path: str, cache_dir: Path) -> Path:
        """Fetch an XML catalog from raw GitHub and save to cache.

        Args:
            catalog_rel_path: Repo-relative path (e.g., "artifacts/catalog-v001.xml")
            cache_dir: Cache root directory

        Returns:
            Absolute path to the cached catalog file
        """
        url = f"{self.raw_github_base}/{catalog_rel_path}"
        dest = cache_dir / catalog_rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Fetching catalog: %s", catalog_rel_path)
        try:
            data = _http_get(url, self.timeout)
            dest.write_bytes(data)
            logger.debug("Cached catalog: %s (%d bytes)", dest, len(data))
            return dest
        except (HTTPError, URLError) as e:
            logger.warning("Failed to fetch catalog %s: %s", url, e)
            raise

    def fetch_all_catalogs(self, cache_dir: Path) -> None:
        """Fetch all 3 XML catalogs to the cache directory."""
        for rel_path in [
            "artifacts/catalog-v001.xml",
            "imports/catalog-v001.xml",
            "tests/catalog-v001.xml",
        ]:
            try:
                self.fetch_catalog(rel_path, cache_dir)
            except (HTTPError, URLError):
                if "tests/" in rel_path:
                    logger.info("Tests catalog not required for remote mode")
                else:
                    raise

    # =========================================================================
    # Fetching: Registry JSON
    # =========================================================================

    def fetch_registry_to_cache(self, cache_dir: Path) -> Path:
        """Fetch and cache docs/registry.json."""
        registry = self.fetch_registry()
        dest = cache_dir / "docs" / "registry.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(registry, indent=3), encoding="utf-8")
        return dest

    # =========================================================================
    # Fetching: Domain Artifacts (via w3id.org / GH Pages)
    # =========================================================================

    def _build_w3id_url(self, domain_info: Dict) -> Optional[str]:
        """Build the w3id.org base URL for a domain's artifacts.

        The w3id URL pattern depends on the namespace:
        - ascs-ev: https://w3id.org/ascs-ev/envited-x/{domain}/{version}
        - gaia-x4plcaad: https://w3id.org/gaia-x4plcaad/ontologies/{domain}/{version}
        - gaia-x development: special case (# fragment IRI)

        Args:
            domain_info: Domain metadata from registry.json

        Returns:
            Base w3id.org URL, or None if cannot be determined.
        """
        iri = domain_info.get("iri")
        if not iri:
            return None
        # The IRI itself is the w3id.org URL (minus any trailing # or /)
        return iri.rstrip("#/")

    def _build_gh_pages_url(self, domain_info: Dict) -> Optional[str]:
        """Build the GitHub Pages URL for a domain's artifacts.

        GH Pages URL pattern:
        ``{GH_PAGES_BASE}/w3id/{namespace_path}/{version}/``

        Args:
            domain_info: Domain metadata from registry.json

        Returns:
            GH Pages base URL for the domain's w3id artifacts.
        """
        iri = domain_info.get("iri", "")
        if not iri:
            return None

        # Extract the path after w3id.org/
        if "w3id.org/" in iri:
            path = iri.split("w3id.org/", 1)[1].rstrip("#/")
            return f"{self.gh_pages_base}/w3id/{path}"

        return None

    def fetch_domain_artifacts(
        self,
        domain: str,
        domain_info: Dict,
        cache_dir: Path,
    ) -> bool:
        """Fetch OWL, SHACL, and context files for a domain.

        Tries GitHub Pages first (direct URL), falls back to w3id.org
        content-negotiation.

        Args:
            domain: Domain name (e.g., "hdmap")
            domain_info: Domain metadata from registry.json
            cache_dir: Cache root directory

        Returns:
            True if at least the ontology was fetched successfully
        """
        domain_dir = cache_dir / "artifacts" / domain
        domain_dir.mkdir(parents=True, exist_ok=True)

        gh_url = self._build_gh_pages_url(domain_info)
        w3id_url = self._build_w3id_url(domain_info)

        # Map of local filename → (GH Pages artifact name, w3id accept header)
        file_map = {
            f"{domain}.owl.ttl": ("ontology.ttl", "text/turtle"),
            f"{domain}.shacl.ttl": ("shapes.ttl", "text/turtle"),
            f"{domain}.context.jsonld": ("context.jsonld", "application/ld+json"),
        }

        ontology_fetched = False

        for local_name, (gh_artifact, accept_header) in file_map.items():
            dest = domain_dir / local_name
            if dest.exists():
                logger.debug("Already cached: %s", dest)
                if local_name.endswith(".owl.ttl"):
                    ontology_fetched = True
                continue

            fetched = False

            # Strategy 1: GitHub Pages direct URL
            if gh_url:
                artifact_url = f"{gh_url}/{gh_artifact}"
                try:
                    data = _http_get(artifact_url, self.timeout)
                    dest.write_bytes(data)
                    logger.info("Fetched %s/%s from GH Pages", domain, local_name)
                    fetched = True
                except (HTTPError, URLError) as e:
                    logger.debug("GH Pages fetch failed for %s: %s", artifact_url, e)

            # Strategy 2: w3id.org content-negotiation
            if not fetched and w3id_url:
                # For shapes, use the /shapes path
                if "shacl" in local_name:
                    conneg_url = f"{w3id_url}/shapes"
                else:
                    conneg_url = w3id_url
                try:
                    data = _http_get_with_accept(
                        conneg_url, accept_header, self.timeout
                    )
                    dest.write_bytes(data)
                    logger.info("Fetched %s/%s via w3id.org conneg", domain, local_name)
                    fetched = True
                except (HTTPError, URLError) as e:
                    logger.debug("w3id.org conneg failed for %s: %s", conneg_url, e)

            if not fetched:
                logger.warning(
                    "Could not fetch %s/%s from any source", domain, local_name
                )
            elif local_name.endswith(".owl.ttl"):
                ontology_fetched = True

        return ontology_fetched

    # =========================================================================
    # Fetching: Import Ontologies (from raw GitHub)
    # =========================================================================

    def fetch_import_files(self, cache_dir: Path) -> int:
        """Fetch all base ontology files listed in imports/catalog-v001.xml.

        Reads the cached imports catalog to discover which files are needed,
        then fetches each from raw GitHub.

        Args:
            cache_dir: Cache root directory

        Returns:
            Number of files successfully fetched
        """
        import xml.etree.ElementTree as ET

        catalog_path = cache_dir / "imports" / "catalog-v001.xml"
        if not catalog_path.exists():
            logger.warning("Imports catalog not cached, cannot fetch import files")
            return 0

        tree = ET.parse(catalog_path)
        root = tree.getroot()
        ns = {"cat": "urn:oasis:names:tc:entity:xmlns:xml:catalog"}
        uri_elems = root.findall("cat:uri", ns)
        if not uri_elems:
            uri_elems = root.findall("uri")

        fetched = 0
        seen_paths: Set[str] = set()

        for elem in uri_elems:
            rel_path = elem.get("uri")
            if not rel_path or rel_path in seen_paths:
                continue
            seen_paths.add(rel_path)

            dest = cache_dir / "imports" / rel_path
            if dest.exists():
                fetched += 1
                continue

            url = f"{self.raw_github_base}/imports/{rel_path}"
            dest.parent.mkdir(parents=True, exist_ok=True)

            try:
                data = _http_get(url, self.timeout)
                dest.write_bytes(data)
                logger.debug("Fetched import: %s", rel_path)
                fetched += 1
            except (HTTPError, URLError) as e:
                logger.warning("Failed to fetch import %s: %s", rel_path, e)

        logger.info("Fetched %d import files", fetched)
        return fetched

    def fetch_artifacts_from_catalog(self, cache_dir: Path) -> int:
        """Fetch artifact files referenced in artifacts/catalog-v001.xml.

        This is the fallback for domains NOT in registry.json (e.g., the
        ``gx`` domain with IRI ``https://w3id.org/gaia-x/development#``).
        Parses the cached artifacts catalog and fetches any referenced files
        that are not yet present in the cache.

        Args:
            cache_dir: Cache root directory

        Returns:
            Number of files successfully fetched
        """
        import xml.etree.ElementTree as ET

        catalog_path = cache_dir / "artifacts" / "catalog-v001.xml"
        if not catalog_path.exists():
            logger.warning("Artifacts catalog not cached, skipping catalog fetch")
            return 0

        tree = ET.parse(catalog_path)
        root = tree.getroot()
        ns = {"cat": "urn:oasis:names:tc:entity:xmlns:xml:catalog"}
        uri_elems = root.findall("cat:uri", ns)
        if not uri_elems:
            uri_elems = root.findall("uri")

        fetched = 0
        seen_paths: Set[str] = set()

        for elem in uri_elems:
            rel_path = elem.get("uri")
            if not rel_path or rel_path in seen_paths:
                continue
            seen_paths.add(rel_path)

            dest = cache_dir / "artifacts" / rel_path
            if dest.exists():
                continue

            url = f"{self.raw_github_base}/artifacts/{rel_path}"
            dest.parent.mkdir(parents=True, exist_ok=True)

            try:
                data = _http_get(url, self.timeout)
                dest.write_bytes(data)
                logger.debug("Fetched artifact from catalog: %s", rel_path)
                fetched += 1
            except (HTTPError, URLError) as e:
                logger.warning("Failed to fetch artifact %s: %s", rel_path, e)

        if fetched:
            logger.info("Fetched %d additional artifact files from catalog", fetched)
        return fetched

    # =========================================================================
    # High-Level API
    # =========================================================================

    def ensure_cache(
        self,
        domains: Optional[List[str]] = None,
        force: bool = False,
    ) -> Path:
        """Ensure all required artifacts are cached locally.

        Fetches registry, catalogs, domain artifacts, and import files.
        Returns the cache directory that can be used as ``root_dir`` for
        ``RegistryResolver``.

        Args:
            domains: Optional list of specific domains to fetch.
                     If None, fetches all domains from the registry.
            force: If True, re-fetch even if cache is valid.

        Returns:
            Path to the versioned cache directory (use as root_dir).
        """
        version = self.get_registry_version()
        cache_dir = self._versioned_cache_dir(version)

        if not force and self.is_cache_valid(cache_dir):
            logger.info("Using valid cache at %s", cache_dir)
            return cache_dir

        logger.info("Building artifact cache at %s", cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Fetch registry
        self.fetch_registry_to_cache(cache_dir)

        # Step 2: Fetch catalogs
        self.fetch_all_catalogs(cache_dir)

        # Step 3: Fetch domain artifacts
        domain_info = self.get_domain_info()
        if domains is None:
            domains = list(domain_info.keys())

        fetched_domains = []
        for domain_name in domains:
            info = domain_info.get(domain_name)
            if not info:
                logger.warning("Domain '%s' not found in registry", domain_name)
                continue
            if self.fetch_domain_artifacts(domain_name, info, cache_dir):
                fetched_domains.append(domain_name)

        logger.info(
            "Fetched artifacts for %d/%d domains",
            len(fetched_domains),
            len(domains),
        )

        # Step 4: Fetch import ontologies
        self.fetch_import_files(cache_dir)

        # Step 5: Fetch any remaining artifacts from catalog
        # (covers domains like gx that are in catalog but not registry.json)
        self.fetch_artifacts_from_catalog(cache_dir)

        # Step 6: Write cache marker
        self._write_cache_marker(cache_dir)

        return cache_dir

    def ensure_cache_for_iris(self, iris: Set[str]) -> Path:
        """Ensure artifacts are cached for domains matching the given IRIs.

        Discovers which domains are needed based on the IRI prefixes in the
        data, and fetches only those domains.

        Args:
            iris: Set of RDF type or predicate IRIs from data being validated.

        Returns:
            Path to the versioned cache directory.
        """
        domain_info = self.get_domain_info()
        needed_domains: Set[str] = set()

        for iri in iris:
            for domain_name, info in domain_info.items():
                domain_iri = info.get("iri", "")
                if not domain_iri:
                    continue
                base = domain_iri.rstrip("#/")
                if iri.startswith(base + "/") or iri.startswith(base + "#"):
                    needed_domains.add(domain_name)
                    break

        if not needed_domains:
            logger.warning(
                "No matching domains found for %d IRIs, fetching all",
                len(iris),
            )
            return self.ensure_cache()

        logger.info(
            "Resolved %d IRIs to %d domains: %s",
            len(iris),
            len(needed_domains),
            sorted(needed_domains),
        )
        return self.ensure_cache(domains=list(needed_domains))

    def clear_cache(self, version: Optional[str] = None) -> None:
        """Remove cached artifacts.

        Args:
            version: Specific version to clear. If None, clears entire cache.
        """
        if version:
            target = self.cache_base / version
        else:
            target = self.cache_base

        if target.exists():
            shutil.rmtree(target)
            logger.info("Cleared cache: %s", target)
