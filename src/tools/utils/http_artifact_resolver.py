#!/usr/bin/env python3
"""
HTTP Artifact Resolver - Remote ontology artifact fetching and caching.

When OMB is installed via ``pip install`` (without the full repository clone),
the local ``artifacts/``, ``imports/``, and ``tests/`` directories are absent.
This module fetches ontology artifacts from the published GitHub Pages site and
raw GitHub content, caching them locally so the existing catalog-driven
validation pipeline works unchanged.

FEATURE SET:
============
1. HttpArtifactResolver - Fetches and caches OMB ontology artifacts from HTTP
2. _http_get - Unified HTTP GET with optional content-negotiation
3. _validate_response_host - SSRF prevention via host allowlist
4. _safe_cache_path - Path traversal prevention for cache writes
5. _get_default_cache_dir - Platform-appropriate cache directory

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

STANDALONE TESTING:
==================
    python3 -m src.tools.utils.http_artifact_resolver --test

    Options:
      --test         Run self-tests (no network required)
      --clear-cache  Remove all cached artifacts
      --cache-dir    Override default cache directory
      --verbose      Verbose output

DEPENDENCIES:
=============
- urllib: HTTP fetching (stdlib, no external dependencies)
- xml.etree.ElementTree: XML catalog parsing

NOTES:
======
- Uses urllib.request (not ``requests``) for consistency with graph_loader.py
- SSRF prevention via ALLOWED_HOSTS post-redirect validation
- Path traversal prevention via _safe_cache_path on all cache writes
"""

import json
import os
import platform
import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from src.tools.core.logging import get_logger

# NOTE: This module uses urllib.request (not the ``requests`` library) for
# consistency with ``graph_loader.py`` which also uses urllib for HTTPS
# fetching.  Both modules share the same trust boundary and timeout semantics.

logger = get_logger(__name__)

# GitHub Pages base URL for published ontology artifacts.
GH_PAGES_BASE = "https://ascs-ev.github.io/ontology-management-base"

# Raw GitHub content for files not published to Pages (catalogs, imports).
# The ref segment is replaced with the registry's release tag in ensure_cache()
# so that catalogs, imports, and non-registry artifacts (e.g. gx) are fetched
# from the same commit as the published registry — not from 'main' HEAD.
_RAW_GITHUB_REPO = "https://raw.githubusercontent.com/ASCS-eV/ontology-management-base"
RAW_GITHUB_BASE = f"{_RAW_GITHUB_REPO}/main"

# Registry JSON URL (published via GH Pages docs workflow).
REGISTRY_URL = f"{GH_PAGES_BASE}/registry.json"

# W3ID artifact file names served by GitHub Pages.
W3ID_ARTIFACTS = {
    "ontology": ("ontology.ttl", "text/turtle"),
    "shapes": ("shapes.ttl", "text/turtle"),
    "context": ("context.jsonld", "application/ld+json"),
}

# Standard catalog filename used across the repository.
CATALOG_FILENAME = "catalog-v001.xml"

# Default HTTP timeout in seconds.
HTTP_TIMEOUT = 30

# Trusted hosts for HTTP fetching.  Response URLs are validated against this
# set after following redirects to prevent SSRF via malicious redirect targets.
ALLOWED_HOSTS = frozenset(
    {
        "ascs-ev.github.io",
        "raw.githubusercontent.com",
        "w3id.org",
    }
)

# Cache TTL: re-validate after this many seconds (24 hours).
CACHE_TTL_SECONDS = 86400

# Stale build sentinel timeout in seconds (10 minutes).
# If a `.cache-building` marker is older than this, it's treated as stale
# (crashed process) and ignored.
STALE_BUILD_TIMEOUT_SECONDS = 600


def _safe_cache_path(cache_dir: Path, *segments: str) -> Path:
    """Resolve a path within cache_dir, rejecting traversal attempts.

    All cache-write operations must call this **before** any ``mkdir()`` to
    prevent directory creation outside the cache boundary.

    Args:
        cache_dir: Root cache directory (must already exist or be the target
                   for creation).
        *segments: Path segments to join (e.g., ``"imports"``, ``"rdf/rdf.owl.ttl"``).

    Returns:
        Resolved absolute path guaranteed to be under *cache_dir*.

    Raises:
        ValueError: If the resolved path escapes *cache_dir*.
    """
    dest = (cache_dir.resolve() / Path(*segments)).resolve()
    if not dest.is_relative_to(cache_dir.resolve()):
        raise ValueError(
            f"Path traversal blocked: {'/'.join(segments)} "
            f"resolves outside cache {cache_dir}"
        )
    return dest


def _get_default_cache_dir() -> Path:
    """Return platform-appropriate cache directory for OMB artifacts."""
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "omb"


def _validate_response_host(response_url: str) -> None:
    """Validate that the response URL host is in the trusted allowlist.

    Prevents SSRF via attacker-controlled redirect targets.  Fails closed:
    missing or unrecognised hosts are rejected.

    Raises:
        URLError: If the response host is not in ALLOWED_HOSTS.
    """
    host = urlparse(response_url).hostname
    if not host:
        raise URLError(f"Invalid response URL (missing host): {response_url}")
    if host not in ALLOWED_HOSTS:
        raise URLError(
            f"Response redirected to untrusted host: {host} (URL: {response_url})"
        )


def _http_get(
    url: str, timeout: int = HTTP_TIMEOUT, accept: str | None = None
) -> bytes:
    """Fetch URL content with a simple GET request.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        accept: Optional Accept header for content-negotiation

    Returns:
        Response body as bytes

    Raises:
        URLError: On network failure or untrusted redirect
        HTTPError: On non-2xx response
    """
    headers: dict[str, str] = {"User-Agent": "ontology-management-base"}
    if accept:
        headers["Accept"] = accept
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        _validate_response_host(response.url)
        return response.read()


class HttpArtifactResolver:
    """Fetches and caches OMB ontology artifacts from HTTP sources.

    Attributes:
        cache_base: Root cache directory (versioned subdirs created inside)
        gh_pages_base: GitHub Pages base URL
        raw_github_base: Raw GitHub content base URL
        registry_url: URL for docs/registry.json
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
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
        self._registry: dict | None = None

    # =========================================================================
    # Registry Discovery
    # =========================================================================

    def fetch_registry(self) -> dict:
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

    def get_domain_info(self) -> dict[str, dict]:
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

    def _versioned_cache_dir(self, version: str | None = None) -> Path:
        """Get the versioned cache directory.

        Args:
            version: Explicit version string, or auto-detect from registry.

        Returns:
            Path to versioned cache directory.
        """
        if version is None:
            version = self.get_registry_version()
        return self.cache_base / version

    def is_cache_valid(self, cache_dir: Path | None = None) -> bool:
        """Check if the cache is present and not stale.

        Returns False when a ``.cache-building`` sentinel exists (build in
        progress or crashed).  Stale sentinels older than
        ``STALE_BUILD_TIMEOUT_SECONDS`` are cleaned up automatically.

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

        building_marker = cache_dir / ".cache-building"
        if building_marker.exists():
            try:
                ts = float(building_marker.read_text().strip())
                if (time.time() - ts) > STALE_BUILD_TIMEOUT_SECONDS:
                    logger.warning(
                        "Removing stale build marker (>%d s old): %s",
                        STALE_BUILD_TIMEOUT_SECONDS,
                        building_marker,
                    )
                    building_marker.unlink(missing_ok=True)
                else:
                    logger.debug("Cache build in progress: %s", building_marker)
                    return False
            except (ValueError, OSError):
                # Corrupt marker — remove and treat as invalid
                building_marker.unlink(missing_ok=True)
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

    def _pin_raw_github_to_release(self, tag: str) -> None:
        """Pin ``raw_github_base`` to a release tag instead of ``main``.

        Replaces the Git ref segment (last path component) in the raw GitHub
        URL with the given release tag so that catalogs, imports, and
        non-registry artifacts are fetched from a deterministic commit.

        Args:
            tag: Release tag from the registry (e.g., "v0.1.6").
        """
        if not tag or tag == "unknown":
            return

        repo_base, _, current_ref = self.raw_github_base.rpartition("/")
        if not repo_base:
            return

        if current_ref == tag:
            return

        self.raw_github_base = f"{repo_base}/{tag}"
        logger.info(
            "Pinned raw GitHub base to release tag: %s (was: %s)",
            tag,
            current_ref,
        )

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
        dest = _safe_cache_path(cache_dir, catalog_rel_path)
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
            f"artifacts/{CATALOG_FILENAME}",
            f"imports/{CATALOG_FILENAME}",
            f"tests/{CATALOG_FILENAME}",
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
        dest.write_text(json.dumps(registry, indent=2), encoding="utf-8")
        return dest

    # =========================================================================
    # Fetching: Domain Artifacts (via w3id.org / GH Pages)
    # =========================================================================

    def _build_w3id_url(self, domain_info: dict) -> str | None:
        """Build the w3id.org base URL for a domain's artifacts.

        Args:
            domain_info: Domain metadata from registry.json

        Returns:
            Base w3id.org URL, or None if IRI is missing.
        """
        iri = domain_info.get("iri")
        if not iri:
            return None
        return iri.rstrip("#/")

    def _build_gh_pages_url(self, domain_info: dict) -> str | None:
        """Build the GitHub Pages URL for a domain's artifacts.

        GH Pages URL pattern:
        ``{GH_PAGES_BASE}/w3id/{namespace_path}/{version}/``

        Args:
            domain_info: Domain metadata from registry.json

        Returns:
            GH Pages base URL for the domain's w3id artifacts.
        """
        iri = domain_info.get("iri", "")
        if not iri or "w3id.org/" not in iri:
            return None

        path = iri.split("w3id.org/", 1)[1].rstrip("#/")
        return f"{self.gh_pages_base}/w3id/{path}"

    def fetch_domain_artifacts(
        self,
        domain: str,
        domain_info: dict,
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
        domain_dir = _safe_cache_path(cache_dir, "artifacts", domain)
        domain_dir.mkdir(parents=True, exist_ok=True)

        gh_url = self._build_gh_pages_url(domain_info)
        w3id_url = self._build_w3id_url(domain_info)

        # Map of local filename → (GH Pages artifact name, w3id accept header)
        # derived from W3ID_ARTIFACTS constant.
        file_map = {
            f"{domain}.owl.ttl": W3ID_ARTIFACTS["ontology"],
            f"{domain}.shacl.ttl": W3ID_ARTIFACTS["shapes"],
            f"{domain}.context.jsonld": W3ID_ARTIFACTS["context"],
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
                    data = _http_get(conneg_url, self.timeout, accept=accept_header)
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
            Number of files successfully fetched (excluding cache hits)
        """
        catalog_path = cache_dir / "imports" / CATALOG_FILENAME
        if not catalog_path.exists():
            logger.warning("Imports catalog not cached, cannot fetch import files")
            return 0

        tree = ET.parse(catalog_path)  # noqa: S314 — trusted source (raw GitHub)
        root = tree.getroot()
        ns = {"cat": "urn:oasis:names:tc:entity:xmlns:xml:catalog"}
        uri_elems = root.findall("cat:uri", ns)
        if not uri_elems:
            uri_elems = root.findall("uri")

        fetched = 0
        cached = 0
        seen_paths: set[str] = set()

        for elem in uri_elems:
            rel_path = elem.get("uri")
            if not rel_path or rel_path in seen_paths:
                continue
            seen_paths.add(rel_path)

            try:
                dest = _safe_cache_path(cache_dir, "imports", rel_path)
            except ValueError:
                logger.warning("Skipping import with path traversal: %s", rel_path)
                continue
            if dest.exists():
                cached += 1
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

        logger.info("Import files: %d fetched, %d already cached", fetched, cached)
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
            Number of files successfully fetched (excluding cache hits)
        """
        catalog_path = cache_dir / "artifacts" / CATALOG_FILENAME
        if not catalog_path.exists():
            logger.warning("Artifacts catalog not cached, skipping catalog fetch")
            return 0

        tree = ET.parse(catalog_path)  # noqa: S314 — trusted source (raw GitHub)
        root = tree.getroot()
        ns = {"cat": "urn:oasis:names:tc:entity:xmlns:xml:catalog"}
        uri_elems = root.findall("cat:uri", ns)
        if not uri_elems:
            uri_elems = root.findall("uri")

        fetched = 0
        cached = 0
        seen_paths: set[str] = set()

        for elem in uri_elems:
            rel_path = elem.get("uri")
            if not rel_path or rel_path in seen_paths:
                continue
            seen_paths.add(rel_path)

            try:
                dest = _safe_cache_path(cache_dir, "artifacts", rel_path)
            except ValueError:
                logger.warning(
                    "Skipping catalog artifact with path traversal: %s", rel_path
                )
                continue
            if dest.exists():
                cached += 1
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
            logger.info(
                "Catalog artifacts: %d fetched, %d already cached", fetched, cached
            )
        return fetched

    # =========================================================================
    # High-Level API
    # =========================================================================

    def ensure_cache(
        self,
        domains: list[str] | None = None,
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

        # Pin raw GitHub fetches to the release tag so catalogs, imports, and
        # non-registry artifacts (e.g. gx) come from the same commit as the
        # published registry — not from an arbitrary 'main' HEAD.
        self._pin_raw_github_to_release(version)

        if not force and self.is_cache_valid(cache_dir):
            logger.info("Using valid cache at %s", cache_dir)
            return cache_dir

        logger.info("Building artifact cache at %s", cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)

        building_marker = cache_dir / ".cache-building"
        building_marker.write_text(str(time.time()))
        try:
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

            # Step 6: Write cache marker (only on success)
            self._write_cache_marker(cache_dir)
        finally:
            building_marker.unlink(missing_ok=True)

        return cache_dir

    def ensure_cache_for_iris(self, iris: set[str]) -> Path:
        """Ensure artifacts are cached for domains matching the given IRIs.

        Discovers which domains are needed based on the IRI prefixes in the
        data, and fetches only those domains.

        Args:
            iris: Set of RDF type or predicate IRIs from data being validated.

        Returns:
            Path to the versioned cache directory.
        """
        domain_info = self.get_domain_info()
        needed_domains: set[str] = set()

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
            # Non-registry domains (e.g., gx/gaia-x) are only discoverable
            # via the artifacts catalog, not registry.json.  Fall back to a
            # full cache build which includes catalog-based fetching.
            logger.info(
                "No registry-based domain match for %d IRI(s); "
                "fetching all domains (includes catalog-only domains like gx)",
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

    def clear_cache(self, version: str | None = None) -> None:
        """Remove cached artifacts.

        Args:
            version: Specific version to clear. If None, clears entire cache.

        Raises:
            ValueError: If the resolved target is not under cache_base.
        """
        if version:
            target = self.cache_base / version
        else:
            target = self.cache_base

        # Safety: ensure target is under the expected cache hierarchy.
        try:
            target.resolve().relative_to(self.cache_base.resolve())
        except ValueError:
            raise ValueError(
                f"Refusing to delete {target}: not under cache base {self.cache_base}"
            ) from None

        if target.exists():
            shutil.rmtree(target)
            logger.info("Cleared cache: %s", target)


# =========================================================================
# Standalone self-tests
# =========================================================================


def _run_tests() -> bool:
    """Run self-tests for the module.

    Tests core utilities (cache dir, host validation, safe paths, URL builders)
    without making real HTTP requests.
    """
    import tempfile

    print("Running http_artifact_resolver self-tests...")
    all_passed = True

    # Test 1: _get_default_cache_dir returns an omb-suffixed path
    cache_dir = _get_default_cache_dir()
    if cache_dir.name != "omb":
        print(f"FAIL: Expected cache dir name 'omb', got '{cache_dir.name}'")
        all_passed = False
    else:
        print(f"PASS: Default cache dir: {cache_dir}")

    # Test 2: _validate_response_host accepts trusted hosts
    try:
        _validate_response_host("https://ascs-ev.github.io/test")
        print("PASS: Trusted host accepted")
    except URLError:
        print("FAIL: Trusted host rejected")
        all_passed = False

    # Test 3: _validate_response_host rejects untrusted hosts
    try:
        _validate_response_host("https://evil.example.com/payload")
        print("FAIL: Untrusted host accepted")
        all_passed = False
    except URLError:
        print("PASS: Untrusted host rejected")

    # Test 4: _safe_cache_path rejects path traversal
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        try:
            _safe_cache_path(tmp, "imports", "../../etc/passwd")
            print("FAIL: Path traversal not rejected")
            all_passed = False
        except ValueError:
            print("PASS: Path traversal rejected")

        # Test 5: _safe_cache_path allows normal paths
        result = _safe_cache_path(tmp, "artifacts", "hdmap/hdmap.owl.ttl")
        if result.is_relative_to(tmp.resolve()):
            print("PASS: Normal path allowed")
        else:
            print("FAIL: Normal path rejected")
            all_passed = False

    # Test 6: URL builders
    resolver = HttpArtifactResolver(cache_dir=Path(tempfile.mkdtemp()))
    info_ascs = {"iri": "https://w3id.org/ascs-ev/envited-x/hdmap/v6"}
    gh_url = resolver._build_gh_pages_url(info_ascs)
    if gh_url and "w3id/ascs-ev/envited-x/hdmap/v6" in gh_url:
        print("PASS: GH Pages URL built correctly")
    else:
        print(f"FAIL: GH Pages URL: {gh_url}")
        all_passed = False

    w3id_url = resolver._build_w3id_url(info_ascs)
    if w3id_url == "https://w3id.org/ascs-ev/envited-x/hdmap/v6":
        print("PASS: w3id URL built correctly")
    else:
        print(f"FAIL: w3id URL: {w3id_url}")
        all_passed = False

    # Test 7: Missing IRI returns None
    if resolver._build_w3id_url({}) is None:
        print("PASS: Missing IRI returns None")
    else:
        print("FAIL: Missing IRI did not return None")
        all_passed = False

    # Cleanup
    shutil.rmtree(resolver.cache_base, ignore_errors=True)

    print(f"\n{'All tests passed!' if all_passed else 'Some tests FAILED!'}")
    return all_passed


def main():
    """CLI entry point for http_artifact_resolver."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="HTTP-based artifact resolution for OMB"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run self-tests",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear all cached artifacts",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Override cache directory",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if args.test:
        success = _run_tests()
        sys.exit(0 if success else 1)

    resolver = HttpArtifactResolver(cache_dir=args.cache_dir)

    if args.clear_cache:
        resolver.clear_cache()
        print("Cache cleared.")
        sys.exit(0)

    # Default: show cache info
    cache_dir = _get_default_cache_dir()
    print(f"Cache directory: {cache_dir}")
    if cache_dir.exists():
        versions = [d.name for d in cache_dir.iterdir() if d.is_dir()]
        print(f"Cached versions: {versions or '(none)'}")
    else:
        print("No cache present.")


if __name__ == "__main__":
    main()
