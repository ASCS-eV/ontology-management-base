"""Tests for HTTP artifact resolution (src.tools.utils.http_artifact_resolver)."""

import json
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.tools.utils.http_artifact_resolver import (
    HttpArtifactResolver,
    _get_default_cache_dir,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_REGISTRY = {
    "version": "2.1.0",
    "latestRelease": "v0.1.4",
    "ontologies": {
        "hdmap": {
            "namespace": "ascs-ev",
            "iri": "https://w3id.org/ascs-ev/envited-x/hdmap/v6",
            "latest": "v6",
            "versions": {
                "v6": {
                    "releaseTag": "v0.1.4",
                    "versionInfo": "v6",
                    "versionIri": "https://w3id.org/ascs-ev/envited-x/hdmap/v6",
                    "files": {
                        "ontology": "artifacts/hdmap/hdmap.owl.ttl",
                        "shacl": ["artifacts/hdmap/hdmap.shacl.ttl"],
                        "jsonld": "artifacts/hdmap/hdmap.context.jsonld",
                    },
                }
            },
        },
        "scenario": {
            "namespace": "ascs-ev",
            "iri": "https://w3id.org/ascs-ev/envited-x/scenario/v6",
            "latest": "v6",
            "versions": {
                "v6": {
                    "releaseTag": "v0.1.4",
                    "versionInfo": "v6",
                    "versionIri": "https://w3id.org/ascs-ev/envited-x/scenario/v6",
                    "files": {
                        "ontology": "artifacts/scenario/scenario.owl.ttl",
                        "shacl": ["artifacts/scenario/scenario.shacl.ttl"],
                        "jsonld": "artifacts/scenario/scenario.context.jsonld",
                    },
                }
            },
        },
    },
}

SAMPLE_ARTIFACTS_CATALOG = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
      <uri name="https://w3id.org/ascs-ev/envited-x/hdmap/v6" uri="hdmap/hdmap.owl.ttl"/>
      <uri name="https://w3id.org/ascs-ev/envited-x/hdmap/v6/shapes" uri="hdmap/hdmap.shacl.ttl"/>
      <uri name="https://w3id.org/ascs-ev/envited-x/hdmap/v6/context" uri="hdmap/hdmap.context.jsonld"/>
      <uri name="https://w3id.org/gaia-x/development#" uri="gx/gx.owl.ttl"/>
      <uri name="https://w3id.org/gaia-x/development#shapes" uri="gx/gx.shacl.ttl"/>
    </catalog>
""")

SAMPLE_IMPORTS_CATALOG = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
      <uri name="http://www.w3.org/1999/02/22-rdf-syntax-ns#" uri="rdf/rdf.owl.ttl"/>
      <uri name="http://www.w3.org/2000/01/rdf-schema#" uri="rdfs/rdfs.owl.ttl"/>
    </catalog>
""")


@pytest.fixture
def resolver(tmp_path):
    """Create an HttpArtifactResolver with a temp cache dir."""
    return HttpArtifactResolver(
        cache_dir=tmp_path / "cache",
        registry_url="https://test.example.com/registry.json",
        gh_pages_base="https://test.example.com/pages",
        raw_github_base="https://test.example.com/raw",
    )


# ---------------------------------------------------------------------------
# Registry Tests
# ---------------------------------------------------------------------------


class TestRegistryFetch:
    """Tests for registry discovery."""

    def test_fetch_registry_caches_result(self, resolver):
        """Registry is fetched once and cached in memory."""
        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            mock_get.return_value = json.dumps(SAMPLE_REGISTRY).encode()
            result = resolver.fetch_registry()
            assert result["version"] == "2.1.0"
            assert len(result["ontologies"]) == 2

            # Second call should NOT trigger another HTTP request
            result2 = resolver.fetch_registry()
            assert result2 is result
            mock_get.assert_called_once()

    def test_get_registry_version(self, resolver):
        """get_registry_version returns latestRelease."""
        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            mock_get.return_value = json.dumps(SAMPLE_REGISTRY).encode()
            assert resolver.get_registry_version() == "v0.1.4"

    def test_get_domain_info(self, resolver):
        """get_domain_info returns ontologies dict."""
        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            mock_get.return_value = json.dumps(SAMPLE_REGISTRY).encode()
            info = resolver.get_domain_info()
            assert "hdmap" in info
            assert "scenario" in info
            assert info["hdmap"]["iri"] == "https://w3id.org/ascs-ev/envited-x/hdmap/v6"

    def test_fetch_registry_raises_on_failure(self, resolver):
        """RuntimeError raised when registry fetch fails."""
        from urllib.error import URLError

        with patch(
            "src.tools.utils.http_artifact_resolver._http_get",
            side_effect=URLError("connection refused"),
        ):
            with pytest.raises(RuntimeError, match="Failed to fetch registry"):
                resolver.fetch_registry()


# ---------------------------------------------------------------------------
# Cache Tests
# ---------------------------------------------------------------------------


class TestCacheManagement:
    """Tests for cache freshness and directory management."""

    def test_is_cache_valid_false_when_no_marker(self, resolver, tmp_path):
        """Cache is invalid when no timestamp marker exists."""
        cache_dir = tmp_path / "empty"
        cache_dir.mkdir()
        assert not resolver.is_cache_valid(cache_dir)

    def test_is_cache_valid_true_when_fresh(self, resolver, tmp_path):
        """Cache is valid when marker is recent."""
        import time

        cache_dir = tmp_path / "fresh"
        cache_dir.mkdir()
        (cache_dir / ".cache-timestamp").write_text(str(time.time()))
        assert resolver.is_cache_valid(cache_dir)

    def test_is_cache_valid_false_when_stale(self, resolver, tmp_path):
        """Cache is invalid when marker is older than TTL."""
        import time

        cache_dir = tmp_path / "stale"
        cache_dir.mkdir()
        old_time = time.time() - 100000  # Way past TTL
        (cache_dir / ".cache-timestamp").write_text(str(old_time))
        assert not resolver.is_cache_valid(cache_dir)

    def test_clear_cache_removes_directory(self, resolver, tmp_path):
        """clear_cache removes the cache directory."""
        resolver.cache_base = tmp_path / "cache"
        version_dir = resolver.cache_base / "v0.1.4"
        version_dir.mkdir(parents=True)
        (version_dir / "test.txt").write_text("data")

        resolver.clear_cache("v0.1.4")
        assert not version_dir.exists()


# ---------------------------------------------------------------------------
# Catalog Fetch Tests
# ---------------------------------------------------------------------------


class TestCatalogFetch:
    """Tests for XML catalog fetching."""

    def test_fetch_catalog_saves_to_correct_path(self, resolver, tmp_path):
        """Catalog is saved under the correct relative path."""
        cache_dir = tmp_path / "cache"
        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            mock_get.return_value = SAMPLE_ARTIFACTS_CATALOG.encode()
            path = resolver.fetch_catalog("artifacts/catalog-v001.xml", cache_dir)

            assert path == cache_dir / "artifacts" / "catalog-v001.xml"
            assert path.exists()
            assert "hdmap" in path.read_text()

    def test_fetch_all_catalogs_fetches_three(self, resolver, tmp_path):
        """fetch_all_catalogs requests all 3 catalog files."""
        cache_dir = tmp_path / "cache"
        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            mock_get.return_value = b"<catalog/>"
            resolver.fetch_all_catalogs(cache_dir)
            assert mock_get.call_count == 3


# ---------------------------------------------------------------------------
# Domain Artifact Fetch Tests
# ---------------------------------------------------------------------------


class TestDomainArtifactFetch:
    """Tests for fetching OWL/SHACL/context files."""

    def test_build_gh_pages_url_ascs_ev(self, resolver):
        """GH Pages URL for ascs-ev namespace."""
        info = {"iri": "https://w3id.org/ascs-ev/envited-x/hdmap/v6"}
        url = resolver._build_gh_pages_url(info)
        assert url == "https://test.example.com/pages/w3id/ascs-ev/envited-x/hdmap/v6"

    def test_build_gh_pages_url_gaiax4plcaad(self, resolver):
        """GH Pages URL for legacy gaia-x4plcaad namespace."""
        info = {"iri": "https://w3id.org/gaia-x4plcaad/ontologies/general/v3"}
        url = resolver._build_gh_pages_url(info)
        assert (
            url
            == "https://test.example.com/pages/w3id/gaia-x4plcaad/ontologies/general/v3"
        )

    def test_build_gh_pages_url_gaiax_development_strips_hash(self, resolver):
        """GH Pages URL strips trailing # from gx development IRI."""
        info = {"iri": "https://w3id.org/gaia-x/development#"}
        url = resolver._build_gh_pages_url(info)
        assert url == "https://test.example.com/pages/w3id/gaia-x/development"

    def test_fetch_domain_artifacts_creates_files(self, resolver, tmp_path):
        """Domain artifacts are downloaded and saved with correct names."""
        cache_dir = tmp_path / "cache"
        info = {"iri": "https://w3id.org/ascs-ev/envited-x/hdmap/v6"}

        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            mock_get.return_value = b"@prefix hdmap: <...> ."
            result = resolver.fetch_domain_artifacts("hdmap", info, cache_dir)

            assert result is True
            assert (cache_dir / "artifacts" / "hdmap" / "hdmap.owl.ttl").exists()
            assert (cache_dir / "artifacts" / "hdmap" / "hdmap.shacl.ttl").exists()
            assert (cache_dir / "artifacts" / "hdmap" / "hdmap.context.jsonld").exists()

    def test_fetch_domain_artifacts_skips_cached(self, resolver, tmp_path):
        """Already-cached files are not re-fetched."""
        cache_dir = tmp_path / "cache"
        domain_dir = cache_dir / "artifacts" / "hdmap"
        domain_dir.mkdir(parents=True)
        (domain_dir / "hdmap.owl.ttl").write_text("cached")
        (domain_dir / "hdmap.shacl.ttl").write_text("cached")
        (domain_dir / "hdmap.context.jsonld").write_text("cached")

        info = {"iri": "https://w3id.org/ascs-ev/envited-x/hdmap/v6"}

        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            result = resolver.fetch_domain_artifacts("hdmap", info, cache_dir)
            assert result is True
            mock_get.assert_not_called()


# ---------------------------------------------------------------------------
# Import Fetch Tests
# ---------------------------------------------------------------------------


class TestImportFetch:
    """Tests for base ontology import fetching."""

    def test_fetch_import_files_from_catalog(self, resolver, tmp_path):
        """Import files are fetched based on catalog entries."""
        cache_dir = tmp_path / "cache"
        imports_dir = cache_dir / "imports"
        imports_dir.mkdir(parents=True)
        (imports_dir / "catalog-v001.xml").write_text(SAMPLE_IMPORTS_CATALOG)

        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            mock_get.return_value = b"@prefix rdf: <...> ."
            count = resolver.fetch_import_files(cache_dir)

            assert count == 2
            assert (imports_dir / "rdf" / "rdf.owl.ttl").exists()
            assert (imports_dir / "rdfs" / "rdfs.owl.ttl").exists()


# ---------------------------------------------------------------------------
# Catalog-Based Artifact Fetch Tests (Gaia-X override)
# ---------------------------------------------------------------------------


class TestCatalogBasedArtifactFetch:
    """Tests for fetching artifacts from catalog (covers gx domain)."""

    def test_fetch_artifacts_from_catalog_fetches_gx(self, resolver, tmp_path):
        """gx domain artifacts are fetched via catalog fallback."""
        cache_dir = tmp_path / "cache"
        artifacts_dir = cache_dir / "artifacts"
        artifacts_dir.mkdir(parents=True)
        (artifacts_dir / "catalog-v001.xml").write_text(SAMPLE_ARTIFACTS_CATALOG)

        # Pre-create hdmap files (already fetched via registry)
        hdmap_dir = artifacts_dir / "hdmap"
        hdmap_dir.mkdir()
        (hdmap_dir / "hdmap.owl.ttl").write_text("cached")
        (hdmap_dir / "hdmap.shacl.ttl").write_text("cached")
        (hdmap_dir / "hdmap.context.jsonld").write_text("cached")

        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            mock_get.return_value = b"@prefix gx: <...> ."
            count = resolver.fetch_artifacts_from_catalog(cache_dir)

            # Only gx files should be fetched (hdmap already cached)
            assert count == 2  # gx.owl.ttl + gx.shacl.ttl
            assert (artifacts_dir / "gx" / "gx.owl.ttl").exists()
            assert (artifacts_dir / "gx" / "gx.shacl.ttl").exists()


# ---------------------------------------------------------------------------
# High-Level API Tests
# ---------------------------------------------------------------------------


class TestEnsureCache:
    """Tests for the high-level ensure_cache API."""

    def test_ensure_cache_skips_when_valid(self, resolver, tmp_path):
        """ensure_cache returns immediately when cache is fresh."""
        import time

        resolver.cache_base = tmp_path / "cache"
        cache_dir = resolver.cache_base / "v0.1.4"
        cache_dir.mkdir(parents=True)
        (cache_dir / ".cache-timestamp").write_text(str(time.time()))

        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            mock_get.return_value = json.dumps(SAMPLE_REGISTRY).encode()
            result = resolver.ensure_cache()
            assert result == cache_dir
            # Only registry fetch should happen (for version), no catalog fetches
            assert mock_get.call_count == 1

    def test_ensure_cache_for_iris_resolves_domains(self, resolver, tmp_path):
        """ensure_cache_for_iris resolves IRIs to needed domains."""
        resolver.cache_base = tmp_path / "cache"

        iris = {
            "https://w3id.org/ascs-ev/envited-x/hdmap/v6/HdMap",
            "https://w3id.org/ascs-ev/envited-x/scenario/v6/Scenario",
        }

        with patch.object(resolver, "ensure_cache") as mock_ensure:
            mock_ensure.return_value = tmp_path / "result"
            with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
                mock_get.return_value = json.dumps(SAMPLE_REGISTRY).encode()
                resolver.ensure_cache_for_iris(iris)

                # Should resolve to hdmap and scenario domains
                call_args = mock_ensure.call_args
                domains = set(
                    call_args.kwargs.get(
                        "domains", call_args.args[0] if call_args.args else []
                    )
                )
                assert "hdmap" in domains
                assert "scenario" in domains


# ---------------------------------------------------------------------------
# Default Cache Dir
# ---------------------------------------------------------------------------


class TestDefaultCacheDir:
    """Tests for platform-appropriate cache directory."""

    def test_default_cache_dir_returns_path(self):
        """Default cache dir is a valid Path."""
        cache_dir = _get_default_cache_dir()
        assert isinstance(cache_dir, Path)
        assert cache_dir.name == "omb"


# ---------------------------------------------------------------------------
# RegistryResolver Integration
# ---------------------------------------------------------------------------


class TestRegistryResolverHttpFallback:
    """Tests for RegistryResolver.enable_http_fallback()."""

    def test_enable_http_false_default_no_http_calls(self, tmp_path):
        """Default enable_http=False does not trigger HTTP fetching."""
        from src.tools.utils.registry_resolver import RegistryResolver

        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            resolver = RegistryResolver(tmp_path)
            mock_get.assert_not_called()
            assert resolver._http_enabled is False

    def test_enable_http_true_triggers_bootstrap_when_no_catalogs(self, tmp_path):
        """enable_http=True triggers HTTP bootstrap when catalogs missing."""
        from src.tools.utils.registry_resolver import RegistryResolver

        with patch(
            "src.tools.utils.http_artifact_resolver.HttpArtifactResolver"
        ) as MockResolver:
            mock_instance = MagicMock()
            mock_instance.ensure_cache.return_value = tmp_path / "cache"
            MockResolver.return_value = mock_instance

            # Create minimal cache dir so RegistryResolver doesn't fail
            (tmp_path / "cache").mkdir()

            resolver = RegistryResolver(tmp_path, enable_http=True)
            mock_instance.ensure_cache.assert_called_once()
            assert resolver._http_enabled is True

    def test_enable_http_true_skips_bootstrap_when_catalogs_exist(self, tmp_path):
        """enable_http=True does NOT bootstrap when local catalogs exist."""
        from src.tools.utils.registry_resolver import RegistryResolver

        # Create catalog files so _has_local_catalogs returns True
        (tmp_path / "artifacts").mkdir()
        (tmp_path / "artifacts" / "catalog-v001.xml").write_text(
            '<?xml version="1.0"?><catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"/>'
        )
        (tmp_path / "imports").mkdir()
        (tmp_path / "imports" / "catalog-v001.xml").write_text(
            '<?xml version="1.0"?><catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"/>'
        )

        with patch(
            "src.tools.utils.http_artifact_resolver.HttpArtifactResolver"
        ) as MockResolver:
            resolver = RegistryResolver(tmp_path, enable_http=True)
            MockResolver.assert_not_called()
            assert resolver._http_enabled is False
