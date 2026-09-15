"""Guards for generator data resolution and installed output isolation.

If any of these modules ever reintroduces a hand-rolled ``Path(__file__).parent...``
root computation, this test fails — which is the whole point (see plan 006 / W1b).
"""

import io
import sys

import pytest

import omb.utils.class_page_generator as class_page_generator
import omb.utils.context_generator as context_generator
import omb.utils.properties_updater as properties_updater
import omb.utils.registry_updater as registry_updater
from omb.core.paths import builtin_data_root


def test_generators_resolve_root_through_builtin_data_root_seam():
    root = builtin_data_root()
    assert class_page_generator.ROOT_DIR == root
    assert context_generator.ROOT_DIR == root
    assert properties_updater.ROOT_DIR == root
    assert registry_updater.ROOT_DIR == root


@pytest.mark.parametrize(
    "generator,args,relative_output",
    [
        (context_generator, ["--all"], "generated-contexts/demo/demo.context.jsonld"),
        (properties_updater, [], "generated-docs/docs/ontologies/catalog.md"),
    ],
)
def test_installed_generator_defaults_keep_package_read_only(
    tmp_path, monkeypatch, generator, args, relative_output
):
    data_root = tmp_path / "site-packages/omb/data"
    artifacts = data_root / "artifacts"
    domain = artifacts / "demo"
    domain.mkdir(parents=True)
    (domain / "demo.owl.ttl").write_text(
        "@prefix ex: <https://example.org/> .\n"
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "ex: a owl:Ontology . ex:Thing a owl:Class .\n",
        encoding="utf-8",
    )
    (domain / "demo.shacl.ttl").write_text(
        "@prefix ex: <https://example.org/> .\n"
        "@prefix sh: <http://www.w3.org/ns/shacl#> .\n"
        "ex:Shape a sh:NodeShape; sh:targetClass ex:Thing .\n",
        encoding="utf-8",
    )
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    monkeypatch.setattr(generator, "ROOT_DIR", data_root)
    monkeypatch.setattr(generator, "ARTIFACTS_DIR", artifacts)
    monkeypatch.chdir(consumer)
    before = {p: p.read_bytes() for p in data_root.rglob("*") if p.is_file()}

    assert generator.main(args) == 0
    assert (consumer / relative_output).is_file()
    assert {p: p.read_bytes() for p in data_root.rglob("*") if p.is_file()} == before

    assert generator.main([*args, "--output", str(data_root)]) == 1
    assert {p: p.read_bytes() for p in data_root.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("generator", [context_generator, properties_updater])
def test_generator_main_reconfigures_legacy_streams_before_output(
    generator, monkeypatch, tmp_path
):
    stdout = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="strict")
    stderr = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="strict")
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)
    args = ["--artifacts", str(tmp_path / "不存在")]
    if generator is context_generator:
        args.append("--all")
    assert generator.main(args) == 1
    assert stdout.encoding == stderr.encoding == "utf-8"
