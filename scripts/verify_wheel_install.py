"""Prove that OMB's built wheel is a standalone validator.

This script is the executable acceptance test for OMB's packaging: it builds (or
accepts) the wheel, installs it into a throwaway virtual environment that has no
connection to this source tree, and then runs the installed ``onto-validate``
console script against a built-in domain from a working directory *outside* the
repository. Success proves that a plain ``pip install ontology-management-base``
yields a working validator whose built-in ontology data resolves from inside the
installed package (``site-packages/omb/data``) — no source checkout required.

Run it directly::

    python scripts/verify_wheel_install.py            # builds a fresh wheel, then proves it
    python scripts/verify_wheel_install.py --wheel dist/ontology_management_base-*.whl
    python scripts/verify_wheel_install.py --keep     # leave the temp venv for inspection

Exit code 0 means the proof passed; any non-zero exit means it failed (suitable
for gating in CI). Building the wheel and installing its dependencies require
network access to PyPI unless an index/cache is preconfigured.
"""

from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# A built-in domain + check that reads only packaged data (no user artifacts).
PROOF_RUN = "check-artifact-coherence"
PROOF_DOMAIN = "manifest"


def _run(
    cmd: list[str], *, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess, forcing UTF-8 I/O so the validator's emoji output cannot
    crash on a cp1252 (Windows) console. Output is captured and decoded leniently."""
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_script(venv_dir: Path, name: str) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / f"{name}.exe"
    return venv_dir / "bin" / name


def _fail(message: str, proc: subprocess.CompletedProcess[str] | None = None) -> None:
    print(f"FAIL: {message}")
    if proc is not None:
        tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-25:])
        print("----- subprocess output (tail) -----")
        print(tail)
        print("------------------------------------")
    sys.exit(1)


def build_wheel(build_dir: Path) -> Path:
    """Build the wheel into ``build_dir`` and return its path."""
    print(f"[1/5] Building wheel into {build_dir} ...")
    proc = _run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            str(REPO_ROOT),
            "--no-deps",
            "-w",
            str(build_dir),
        ]
    )
    if proc.returncode != 0:
        _fail("wheel build failed", proc)
    wheels = sorted(build_dir.glob("ontology_management_base-*.whl"))
    if not wheels:
        _fail(f"no wheel produced in {build_dir}", proc)
    print(f"      built {wheels[-1].name}")
    return wheels[-1]


def make_isolated_venv(venv_dir: Path) -> Path:
    print(f"[2/5] Creating isolated venv at {venv_dir} ...")
    proc = _run([sys.executable, "-m", "venv", str(venv_dir)])
    if proc.returncode != 0:
        _fail("venv creation failed", proc)
    vpy = _venv_python(venv_dir)
    _run([str(vpy), "-m", "pip", "install", "--upgrade", "pip", "--quiet"])
    return vpy


def install_wheel(vpy: Path, wheel: Path) -> None:
    print(f"[3/5] Installing {wheel.name} into the isolated venv ...")
    proc = _run([str(vpy), "-m", "pip", "install", str(wheel)])
    if proc.returncode != 0:
        _fail("wheel install failed", proc)


def assert_packaged_data(vpy: Path) -> None:
    """In the isolated venv: import omb, prove the built-in data resolves from
    inside site-packages, and prove the optional publish stack was not pulled in."""
    print("[4/5] Checking that built-in data resolves from the installed package ...")
    probe = (
        "import sys\n"
        "from omb.core.paths import builtin_data_root\n"
        "root = builtin_data_root()\n"
        "assert 'site-packages' in str(root), f'seam not under site-packages: {root}'\n"
        "assert (root / 'imports').is_dir(), 'packaged imports/ missing'\n"
        "assert (root / 'artifacts' / 'manifest').is_dir(), 'packaged artifacts/manifest missing'\n"
        "assert (root / 'docs' / 'registry.json').is_file(), 'packaged docs/registry.json missing'\n"
        "try:\n"
        "    import keycloak  # noqa: F401\n"
        "    sys.exit('publish stack (keycloak) leaked into the lean install')\n"
        "except ModuleNotFoundError:\n"
        "    pass\n"
        "print(root)\n"
    )
    # Run with -P so the current directory is never prepended to sys.path: this
    # guarantees we import the *installed* omb from site-packages, not a source
    # ``omb/`` directory that Python would otherwise find first when this script
    # happens to run from an OMB checkout (which would make the seam resolve to the
    # repo root and defeat the whole proof).
    proc = _run([str(vpy), "-P", "-c", probe])
    if proc.returncode != 0:
        _fail("packaged-data check failed", proc)
    print(f"      built-in data root: {proc.stdout.strip()}")


def run_validation_outside_repo(venv_dir: Path) -> None:
    """Run the installed console script from a cwd outside the repository."""
    print(
        f"[5/5] Running 'onto-validate --run {PROOF_RUN} --domain {PROOF_DOMAIN}' "
        "from outside the repo ..."
    )
    onto = _venv_script(venv_dir, "onto-validate")
    if not onto.exists():
        _fail(f"console script not found: {onto}")
    with tempfile.TemporaryDirectory(prefix="omb-outside-") as outside:
        proc = _run(
            [str(onto), "--run", PROOF_RUN, "--domain", PROOF_DOMAIN],
            cwd=Path(outside),
        )
    if proc.returncode != 0:
        _fail(f"onto-validate exited {proc.returncode}", proc)
    print("      onto-validate exited 0")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--wheel",
        type=str,
        default=None,
        help="Path (or glob) to a prebuilt wheel. If omitted, a fresh wheel is built.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the temporary workspace (venv + build dir) for inspection.",
    )
    args = parser.parse_args()

    workspace = Path(tempfile.mkdtemp(prefix="omb-w1d-"))
    try:
        if args.wheel:
            matches = sorted(glob.glob(args.wheel))
            if not matches:
                _fail(f"no wheel matched --wheel {args.wheel!r}")
            wheel = Path(matches[-1]).resolve()
            print(f"[1/5] Using prebuilt wheel {wheel.name}")
        else:
            wheel = build_wheel(workspace / "build")

        venv_dir = workspace / "venv"
        vpy = make_isolated_venv(venv_dir)
        install_wheel(vpy, wheel)
        assert_packaged_data(vpy)
        run_validation_outside_repo(venv_dir)
    finally:
        if args.keep:
            print(f"\nWorkspace kept at: {workspace}")
        else:
            _rmtree(workspace)

    print(
        "\nPASS: the installed wheel is a standalone validator (no source checkout needed)."
    )
    return 0


def _rmtree(path: Path) -> None:
    import shutil

    shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
