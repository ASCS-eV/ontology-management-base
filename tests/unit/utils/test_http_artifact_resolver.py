"""Tests for HTTP artifact resolution (src.tools.utils.http_artifact_resolver)."""

import json
import textwrap
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from src.tools.utils.http_artifact_resolver import (
    ALLOWED_HOSTS,
    STALE_BUILD_TIMEOUT_SECONDS,
    HttpArtifactResolver,
    _get_default_cache_dir,
    _safe_cache_path,
    _validate_response_host,
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
        cache_dir = tmp_path / "fresh"
        cache_dir.mkdir()
        (cache_dir / ".cache-timestamp").write_text(str(time.time()))
        assert resolver.is_cache_valid(cache_dir)

    def test_is_cache_valid_false_when_stale(self, resolver, tmp_path):
        """Cache is invalid when marker is older than TTL."""
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
    """Tests for RegistryResolver HTTP bootstrap via _bootstrap_from_http()."""

    def test_enable_http_false_default_no_http_calls(self, tmp_path):
        """Default enable_http=False does not trigger HTTP fetching."""
        from src.tools.utils.registry_resolver import RegistryResolver

        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            resolver = RegistryResolver(tmp_path)
            mock_get.assert_not_called()
            assert resolver.is_http_bootstrapped is False

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
            assert resolver.is_http_bootstrapped is True

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
            assert resolver.is_http_bootstrapped is False


# ---------------------------------------------------------------------------
# Host Allowlist Validation (SSRF prevention)
# ---------------------------------------------------------------------------


class TestValidateResponseHost:
    """Tests for _validate_response_host SSRF prevention."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://ascs-ev.github.io/ontology-management-base/registry.json",
            "https://raw.githubusercontent.com/ASCS-eV/ontology-management-base/main/x",
            "https://w3id.org/ascs-ev/envited-x/hdmap/v6/ontology.ttl",
        ],
    )
    def test_allowed_hosts_pass(self, url):
        """Trusted hosts do not raise."""
        _validate_response_host(url)  # should not raise

    @pytest.mark.parametrize(
        "url",
        [
            "https://evil.example.com/payload",
            "http://169.254.169.254/latest/meta-data/",
            "https://internal-service.company.com/secret",
        ],
    )
    def test_untrusted_hosts_raise(self, url):
        """Untrusted hosts raise URLError."""
        with pytest.raises(URLError, match="untrusted host"):
            _validate_response_host(url)

    def test_allowed_hosts_constant_has_expected_entries(self):
        """ALLOWED_HOSTS includes the three expected domains."""
        assert "ascs-ev.github.io" in ALLOWED_HOSTS
        assert "raw.githubusercontent.com" in ALLOWED_HOSTS
        assert "w3id.org" in ALLOWED_HOSTS

    @pytest.mark.parametrize(
        "url",
        [
            "file:///tmp/test",
            "not-a-url",
            "",
        ],
    )
    def test_missing_host_raises(self, url):
        """URLs without a hostname are rejected (fail-closed)."""
        with pytest.raises(URLError, match="missing host"):
            _validate_response_host(url)


# ---------------------------------------------------------------------------
# W3ID Content-Negotiation Fallback
# ---------------------------------------------------------------------------


class TestW3idConnegFallback:
    """Tests for fetch_domain_artifacts w3id.org content-negotiation path."""

    def test_falls_back_to_w3id_when_gh_pages_fails(self, tmp_path):
        """When GH Pages returns 404, w3id.org content-negotiation is tried."""
        from urllib.error import HTTPError

        resolver = HttpArtifactResolver(cache_dir=tmp_path)

        domain_info = {
            "iri": "https://w3id.org/ascs-ev/envited-x/hdmap/v6",
            "namespace": "ascs-ev",
        }

        gh_pages_404 = HTTPError(
            url="https://ascs-ev.github.io/...",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )

        call_count = {"gh_pages": 0, "conneg": 0}

        def mock_http_get(url, timeout=30, accept=None):
            if accept:
                call_count["conneg"] += 1
                return b"# turtle content"
            else:
                call_count["gh_pages"] += 1
                raise gh_pages_404

        with patch(
            "src.tools.utils.http_artifact_resolver._http_get",
            side_effect=mock_http_get,
        ):
            result = resolver.fetch_domain_artifacts("hdmap", domain_info, tmp_path)

        assert result is True
        # GH Pages was tried (and failed) for all 3 artifacts
        assert call_count["gh_pages"] == 3
        # w3id.org conneg was tried as fallback for all 3
        assert call_count["conneg"] == 3


# ---------------------------------------------------------------------------
# clear_cache Safety
# ---------------------------------------------------------------------------


class TestClearCacheSafety:
    """Tests for clear_cache path validation."""

    def test_clear_cache_no_version_removes_cache_base(self, tmp_path):
        """clear_cache(None) removes the entire cache_base directory."""
        cache_base = tmp_path / "omb"
        cache_base.mkdir()
        (cache_base / "v0.1.4").mkdir()
        (cache_base / "v0.1.4" / "marker.txt").write_text("x")

        resolver = HttpArtifactResolver(cache_dir=cache_base)
        resolver.clear_cache()

        assert not cache_base.exists()

    def test_clear_cache_with_version_only_removes_version(self, tmp_path):
        """clear_cache('v0.1.4') only removes that version subdir."""
        cache_base = tmp_path / "omb"
        (cache_base / "v0.1.4").mkdir(parents=True)
        (cache_base / "v0.1.5").mkdir(parents=True)

        resolver = HttpArtifactResolver(cache_dir=cache_base)
        resolver.clear_cache("v0.1.4")

        assert not (cache_base / "v0.1.4").exists()
        assert (cache_base / "v0.1.5").exists()

    def test_clear_cache_rejects_path_traversal(self, tmp_path):
        """clear_cache rejects version strings that escape cache_base."""
        cache_base = tmp_path / "omb"
        cache_base.mkdir()

        resolver = HttpArtifactResolver(cache_dir=cache_base)
        with pytest.raises(ValueError, match="not under cache base"):
            resolver.clear_cache("../../etc")


# ---------------------------------------------------------------------------
# Path Traversal Prevention (_safe_cache_path)
# ---------------------------------------------------------------------------


class TestSafeCachePath:
    """Tests for _safe_cache_path path traversal prevention."""

    def test_normal_relative_path_allowed(self, tmp_path):
        """Normal relative path resolves within cache."""
        result = _safe_cache_path(tmp_path, "imports", "rdf/rdf.owl.ttl")
        assert result.is_relative_to(tmp_path.resolve())
        assert result == (tmp_path / "imports" / "rdf" / "rdf.owl.ttl").resolve()

    def test_nested_path_allowed(self, tmp_path):
        """Multi-level nesting stays within cache."""
        result = _safe_cache_path(tmp_path, "artifacts", "hdmap", "hdmap.owl.ttl")
        assert result.is_relative_to(tmp_path.resolve())

    def test_benign_dotdot_within_cache_allowed(self, tmp_path):
        """Path with .. that stays within cache is allowed."""
        result = _safe_cache_path(tmp_path, "artifacts", "a", "..", "b", "file.ttl")
        assert result.is_relative_to(tmp_path.resolve())
        assert result == (tmp_path / "artifacts" / "b" / "file.ttl").resolve()

    def test_dotdot_traversal_rejected(self, tmp_path):
        """../../etc/passwd is rejected."""
        with pytest.raises(ValueError, match="Path traversal blocked"):
            _safe_cache_path(tmp_path, "imports", "../../etc/passwd")

    def test_deep_dotdot_traversal_rejected(self, tmp_path):
        """Deep traversal like ../../../ is rejected."""
        with pytest.raises(ValueError, match="Path traversal blocked"):
            _safe_cache_path(tmp_path, "imports", "../../../etc/shadow")

    def test_absolute_path_rejected(self, tmp_path):
        """Absolute paths are rejected (resolved outside cache)."""
        with pytest.raises(ValueError, match="Path traversal blocked"):
            _safe_cache_path(tmp_path, "/etc/passwd")

    def test_backslash_traversal_rejected(self, tmp_path):
        """Backslash-based traversal is rejected."""
        with pytest.raises(ValueError, match="Path traversal blocked"):
            _safe_cache_path(tmp_path, "imports", "..\\..\\etc\\passwd")

    def test_dot_prefixed_traversal_rejected(self, tmp_path):
        """./../../ traversal is rejected."""
        with pytest.raises(ValueError, match="Path traversal blocked"):
            _safe_cache_path(tmp_path, "artifacts", "./../../escape")

    def test_cache_dir_itself_allowed(self, tmp_path):
        """Resolving to cache_dir itself is fine (no escape)."""
        result = _safe_cache_path(tmp_path, "artifacts", "..")
        assert result == tmp_path.resolve()


class TestPathTraversalInCatalogs:
    """Integration tests: traversal in catalog entries is skipped gracefully."""

    MALICIOUS_IMPORTS_CATALOG = textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
          <uri name="http://evil.example.com/" uri="../../etc/passwd"/>
          <uri name="http://www.w3.org/2000/01/rdf-schema#" uri="rdfs/rdfs.owl.ttl"/>
        </catalog>
    """)

    MALICIOUS_ARTIFACTS_CATALOG = textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
          <uri name="http://evil.example.com/" uri="../../../etc/shadow"/>
          <uri name="https://w3id.org/gaia-x/development#" uri="gx/gx.owl.ttl"/>
        </catalog>
    """)

    def test_fetch_import_files_skips_traversal_entry(self, tmp_path):
        """Malicious catalog uri with traversal is skipped; safe entries fetched."""
        cache_dir = tmp_path / "cache"
        imports_dir = cache_dir / "imports"
        imports_dir.mkdir(parents=True)
        (imports_dir / "catalog-v001.xml").write_text(self.MALICIOUS_IMPORTS_CATALOG)

        resolver = HttpArtifactResolver(cache_dir=tmp_path)
        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            mock_get.return_value = b"@prefix rdfs: <...> ."
            count = resolver.fetch_import_files(cache_dir)

        # Only the safe rdfs entry should be fetched; ../../etc/passwd skipped
        assert count == 1
        assert (imports_dir / "rdfs" / "rdfs.owl.ttl").exists()
        assert not (tmp_path / "etc" / "passwd").exists()

    def test_fetch_artifacts_from_catalog_skips_traversal_entry(self, tmp_path):
        """Malicious artifact catalog uri with traversal is skipped."""
        cache_dir = tmp_path / "cache"
        artifacts_dir = cache_dir / "artifacts"
        artifacts_dir.mkdir(parents=True)
        (artifacts_dir / "catalog-v001.xml").write_text(
            self.MALICIOUS_ARTIFACTS_CATALOG
        )

        resolver = HttpArtifactResolver(cache_dir=tmp_path)
        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            mock_get.return_value = b"@prefix gx: <...> ."
            count = resolver.fetch_artifacts_from_catalog(cache_dir)

        # Only gx entry fetched; ../../../etc/shadow skipped
        assert count == 1
        assert (artifacts_dir / "gx" / "gx.owl.ttl").exists()
        assert not (tmp_path / "etc" / "shadow").exists()

    def test_fetch_domain_artifacts_rejects_traversal_domain(self, tmp_path):
        """Domain name with traversal raises ValueError."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True)
        resolver = HttpArtifactResolver(cache_dir=tmp_path)
        info = {"iri": "https://w3id.org/ascs-ev/envited-x/hdmap/v6"}

        with pytest.raises(ValueError, match="Path traversal blocked"):
            resolver.fetch_domain_artifacts("../../escape", info, cache_dir)

    def test_fetch_catalog_rejects_traversal_path(self, tmp_path):
        """Catalog relative path with traversal raises ValueError."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True)
        resolver = HttpArtifactResolver(cache_dir=tmp_path)

        with pytest.raises(ValueError, match="Path traversal blocked"):
            resolver.fetch_catalog("../../etc/passwd", cache_dir)


# ---------------------------------------------------------------------------
# TOCTOU Sentinel (Build Marker)
# ---------------------------------------------------------------------------


class TestBuildSentinel:
    """Tests for .cache-building sentinel in ensure_cache / is_cache_valid."""

    def test_building_marker_makes_cache_invalid(self, tmp_path):
        """is_cache_valid returns False when .cache-building exists."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / ".cache-timestamp").write_text(str(time.time()))
        (cache_dir / ".cache-building").write_text(str(time.time()))

        resolver = HttpArtifactResolver(cache_dir=tmp_path)
        assert not resolver.is_cache_valid(cache_dir)

    def test_stale_building_marker_cleaned_up(self, tmp_path):
        """Stale .cache-building marker (>10 min) is removed."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        stale_time = time.time() - STALE_BUILD_TIMEOUT_SECONDS - 60
        (cache_dir / ".cache-building").write_text(str(stale_time))
        # No .cache-timestamp → still invalid, but marker should be cleaned up

        resolver = HttpArtifactResolver(cache_dir=tmp_path)
        assert not resolver.is_cache_valid(cache_dir)
        assert not (cache_dir / ".cache-building").exists()

    def test_corrupt_building_marker_cleaned_up(self, tmp_path):
        """Corrupt .cache-building marker is removed and cache is invalid."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / ".cache-building").write_text("not-a-number")
        (cache_dir / ".cache-timestamp").write_text(str(time.time()))

        resolver = HttpArtifactResolver(cache_dir=tmp_path)
        assert not resolver.is_cache_valid(cache_dir)
        assert not (cache_dir / ".cache-building").exists()

    def test_ensure_cache_cleans_marker_on_success(self, tmp_path):
        """ensure_cache removes .cache-building after successful build."""
        resolver = HttpArtifactResolver(cache_dir=tmp_path)

        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            mock_get.return_value = json.dumps(SAMPLE_REGISTRY).encode()
            with patch.object(resolver, "fetch_all_catalogs"):
                with patch.object(
                    resolver, "fetch_domain_artifacts", return_value=True
                ):
                    with patch.object(resolver, "fetch_import_files"):
                        with patch.object(resolver, "fetch_artifacts_from_catalog"):
                            cache_dir = resolver.ensure_cache(force=True)

        assert not (cache_dir / ".cache-building").exists()
        assert (cache_dir / ".cache-timestamp").exists()

    def test_ensure_cache_cleans_marker_on_failure(self, tmp_path):
        """ensure_cache removes .cache-building even when build fails."""
        resolver = HttpArtifactResolver(cache_dir=tmp_path)

        with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
            mock_get.return_value = json.dumps(SAMPLE_REGISTRY).encode()
            with patch.object(
                resolver, "fetch_all_catalogs", side_effect=RuntimeError("boom")
            ):
                with pytest.raises(RuntimeError, match="boom"):
                    resolver.ensure_cache(force=True)

        # The versioned cache dir is created, but marker must be cleaned up
        version_dir = tmp_path / SAMPLE_REGISTRY["latestRelease"]
        assert not (version_dir / ".cache-building").exists()


# ---------------------------------------------------------------------------
# Coverage gap: URL builders with missing/non-w3id IRIs
# ---------------------------------------------------------------------------


class TestUrlBuilderEdgeCases:
    """Tests for _build_w3id_url and _build_gh_pages_url edge cases."""

    def test_build_w3id_url_missing_iri_returns_none(self, resolver):
        """_build_w3id_url returns None when IRI is absent."""
        assert resolver._build_w3id_url({}) is None
        assert resolver._build_w3id_url({"iri": ""}) is None

    def test_build_gh_pages_url_missing_iri_returns_none(self, resolver):
        """_build_gh_pages_url returns None when IRI is absent."""
        assert resolver._build_gh_pages_url({}) is None
        assert resolver._build_gh_pages_url({"iri": ""}) is None

    def test_build_gh_pages_url_non_w3id_returns_none(self, resolver):
        """_build_gh_pages_url returns None for non-w3id IRIs."""
        info = {"iri": "https://example.org/ontology/v1"}
        assert resolver._build_gh_pages_url(info) is None


# ---------------------------------------------------------------------------
# Coverage gap: Missing catalogs return 0
# ---------------------------------------------------------------------------


class TestMissingCatalogReturnsZero:
    """Tests for fetch_import_files / fetch_artifacts_from_catalog with no catalog."""

    def test_fetch_import_files_no_catalog_returns_zero(self, resolver, tmp_path):
        """Returns 0 when imports catalog does not exist."""
        cache_dir = tmp_path / "empty"
        cache_dir.mkdir()
        assert resolver.fetch_import_files(cache_dir) == 0

    def test_fetch_artifacts_from_catalog_no_catalog_returns_zero(
        self, resolver, tmp_path
    ):
        """Returns 0 when artifacts catalog does not exist."""
        cache_dir = tmp_path / "empty"
        cache_dir.mkdir()
        assert resolver.fetch_artifacts_from_catalog(cache_dir) == 0


# ---------------------------------------------------------------------------
# Coverage gap: Both fetch strategies fail
# ---------------------------------------------------------------------------


class TestBothStrategiesFail:
    """Tests for fetch_domain_artifacts when all sources fail."""

    def test_returns_false_when_all_sources_fail(self, tmp_path):
        """fetch_domain_artifacts returns False when nothing can be fetched."""
        from urllib.error import HTTPError

        resolver = HttpArtifactResolver(cache_dir=tmp_path)
        domain_info = {"iri": "https://w3id.org/ascs-ev/envited-x/hdmap/v6"}

        error = HTTPError(
            url="https://example.com",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )

        def mock_http_get(url, timeout=30, accept=None):
            raise error

        with patch(
            "src.tools.utils.http_artifact_resolver._http_get",
            side_effect=mock_http_get,
        ):
            result = resolver.fetch_domain_artifacts("hdmap", domain_info, tmp_path)

        assert result is False


# ---------------------------------------------------------------------------
# Coverage gap: Corrupt .cache-timestamp
# ---------------------------------------------------------------------------


class TestCorruptCacheTimestamp:
    """Tests for is_cache_valid with corrupt timestamp file."""

    def test_corrupt_timestamp_returns_false(self, resolver, tmp_path):
        """is_cache_valid returns False when timestamp is corrupt."""
        cache_dir = tmp_path / "corrupt"
        cache_dir.mkdir()
        (cache_dir / ".cache-timestamp").write_text("not-a-number")
        assert not resolver.is_cache_valid(cache_dir)

    def test_is_cache_valid_no_arg_registry_fails_returns_false(self, tmp_path):
        """is_cache_valid(None) returns False when registry fetch fails."""
        resolver = HttpArtifactResolver(
            cache_dir=tmp_path,
            registry_url="https://test.example.com/registry.json",
        )
        with patch(
            "src.tools.utils.http_artifact_resolver._http_get",
            side_effect=URLError("fail"),
        ):
            assert not resolver.is_cache_valid()


# ---------------------------------------------------------------------------
# Coverage gap: ensure_cache_for_iris fallback to full cache
# ---------------------------------------------------------------------------


class TestEnsureCacheForIrisFallback:
    """Tests for ensure_cache_for_iris when no domain matches."""

    def test_no_match_falls_back_to_full_cache(self, resolver, tmp_path):
        """When no IRI matches any registry domain, ensure_cache() is called."""
        resolver.cache_base = tmp_path / "cache"

        iris = {
            "https://unknown.example.org/ontology/Thing",
        }

        with patch.object(resolver, "ensure_cache") as mock_ensure:
            mock_ensure.return_value = tmp_path / "result"
            with patch("src.tools.utils.http_artifact_resolver._http_get") as mock_get:
                mock_get.return_value = json.dumps(SAMPLE_REGISTRY).encode()
                result = resolver.ensure_cache_for_iris(iris)

                # Should fall back to full cache (no domains kwarg)
                mock_ensure.assert_called_once_with()
                assert result == tmp_path / "result"


# ---------------------------------------------------------------------------
# Coverage gap: fetch_all_catalogs re-raises non-test catalog failure
# ---------------------------------------------------------------------------


class TestFetchAllCatalogsErrorHandling:
    """Tests for fetch_all_catalogs error propagation."""

    def test_artifacts_catalog_failure_propagates(self, resolver, tmp_path):
        """Failure to fetch artifacts catalog raises (not swallowed)."""
        from urllib.error import HTTPError

        cache_dir = tmp_path / "cache"
        error = HTTPError(
            url="https://example.com",
            code=500,
            msg="Server Error",
            hdrs={},
            fp=None,
        )

        call_idx = {"n": 0}

        def mock_http_get(url, timeout=30, accept=None):
            call_idx["n"] += 1
            if call_idx["n"] == 1:
                raise error  # First call = artifacts catalog
            return b"<catalog/>"

        with patch(
            "src.tools.utils.http_artifact_resolver._http_get",
            side_effect=mock_http_get,
        ):
            with pytest.raises(HTTPError):
                resolver.fetch_all_catalogs(cache_dir)

    def test_tests_catalog_failure_swallowed(self, resolver, tmp_path):
        """Failure to fetch tests catalog is swallowed (not required)."""
        from urllib.error import HTTPError

        cache_dir = tmp_path / "cache"
        error = HTTPError(
            url="https://example.com",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )

        call_idx = {"n": 0}

        def mock_http_get(url, timeout=30, accept=None):
            call_idx["n"] += 1
            if call_idx["n"] == 3:
                raise error  # Third call = tests catalog
            return b"<catalog/>"

        with patch(
            "src.tools.utils.http_artifact_resolver._http_get",
            side_effect=mock_http_get,
        ):
            resolver.fetch_all_catalogs(cache_dir)  # Should not raise
