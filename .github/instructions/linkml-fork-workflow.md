# LinkML Fork Maintenance & Upstream PR Workflow

Authoritative guide for maintaining the **ASCS-eV LinkML fork** that OMB depends on,
rebasing feature branches, quality-checking them against upstream, re-integrating them,
and updating the OMB pin. Read this before touching `submodules/linkml`, the
`feat/envited-x-pipeline` branch, or any generator-flag behavior.

## 1. Why this exists

OMB generates its OWL / SHACL / JSON-LD-context / JSON-Schema artifacts with the LinkML
generators (`gen-owl`, `gen-shacl`, `gen-jsonld-context`, `gen-json-schema`). Several
generator features OMB relies on are **not yet in upstream LinkML** — they live on a
fork and are being upstreamed one PR at a time.

The hard part: upstream `linkml/linkml` `main` moves constantly, and our features get
merged into it **step by step**. So the fork must be re-synced periodically, each feature
branch must be re-rebased down to a **single clean commit**, quality-checked so the
upstream PR stays reviewable, and the integration branch must be rebuilt so OMB keeps
working.

## 2. Repository & branch topology

| Ref                                                            | What it is                                                                                                                                |
| -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `upstream` = `github.com/linkml/linkml`                        | The real LinkML. **Monorepo**: package in `packages/linkml/`, tests in top-level `tests/linkml/`. Advances constantly.                    |
| `origin` = `github.com/ASCS-eV/linkml`                         | Our fork. Holds `main`, per-PR feature branches, and the integration branch.                                                              |
| `main` (fork)                                                  | Mirror of upstream `main`. Re-synced (force-pushed) during each maintenance cycle.                                                        |
| Per-PR feature branches (`upstream/feat/*`, `feat/*`, `fix/*`) | **One branch per upstream PR, ideally one commit.** Each is submitted to `linkml/linkml`. Rebased onto fresh upstream `main` every cycle. |
| **`feat/envited-x-pipeline`** (integration branch)             | Cherry-picks **all** unmerged feature commits on top of a recent upstream `main`. **This is what OMB consumes.**                          |

Branch ↔ upstream-PR mapping is discoverable at any time:

```bash
git ls-remote --heads https://github.com/ASCS-eV/linkml.git
gh pr list --repo linkml/linkml --author <maintainer> --state open \
    --json number,title,headRefName,baseRefName,url
```

## 3. How OMB consumes the fork

Two coupled references — **keep them consistent**:

1. **Submodule pin** — the `submodules/linkml` gitlink SHA. Source of truth for the
   version actually used. Should point at the current `feat/envited-x-pipeline` head.
2. **`pyproject.toml` `[dev]`** — for standalone/CI installs without the submodule:
   ```
   linkml @ git+https://github.com/ASCS-eV/linkml.git@feat/envited-x-pipeline#subdirectory=packages/linkml
   ```
   Note the `#subdirectory=packages/linkml` (monorepo). The branch name is pinned, so a
   branch move only requires bumping the submodule gitlink — unless you pin a SHA here.

The generator **flags** OMB depends on (see `Makefile` `_generate_default`) map to fork
features/PRs. If a feature branch's CLI flag name or behavior changes during a rebase,
`make generate` breaks. Cross-check the flag set after every cycle:

- `gen-owl`: `--deterministic --normalize-prefixes --xsd-anyuri-as-iri --default-language --ontology-uri-suffix`
- `gen-shacl`: `--deterministic --normalize-prefixes --default-language --message-template`
- `gen-jsonld-context`: `--deterministic --normalize-prefixes --exclude-external-imports --xsd-anyuri-as-iri`

## 4. The maintenance cycle

Trigger: upstream `main` advanced, one of our PRs merged, or a maintainer asks to
"rebase & check" a feature branch. Steps:

### 4.0 Init & remotes (submodule is often uninitialized)

```bash
git submodule update --init submodules/linkml
cd submodules/linkml
git remote get-url upstream 2>/dev/null || git remote add upstream https://github.com/linkml/linkml.git
git fetch upstream --prune
git fetch origin --prune
```

> If you run git inside an **uninitialized** submodule directory, git silently operates
> on the parent OMB repo (wrong branches/remotes). Always init first and verify
> `git remote -v` shows `linkml`.

### 4.1 Re-sync fork `main` to upstream `main`

```bash
git checkout main
git reset --hard upstream/main
git push --force-with-lease origin main
```

### 4.2 Rebase each feature branch down to a single commit

For a branch that carries **already-merged dependency commits** plus its own feature
commit, replay only the feature commit onto fresh `main` with `git rebase --onto`:

```bash
git checkout <feature-branch>
# Replay only commits AFTER <last-dependency-commit> onto upstream/main:
git rebase --onto upstream/main <last-dependency-commit-sha> <feature-branch>
```

`git rebase --onto NEWBASE UPSTREAM BRANCH` replays commits in `(UPSTREAM, BRANCH]` onto
`NEWBASE`. This drops everything up to and including `UPSTREAM` (the merged dependency),
leaving the single feature commit. Resolve conflicts (the target generator file and its
test are the usual spots), then continue.

If a branch has no merged deps but multiple WIP commits, squash to one:
`git rebase -i upstream/main` and `squash`/`fixup` down to a single commit.

### 4.3 Quality-check the rebased feature branch

The goal is that the **upstream PR is still correct, minimal, and reviewable**:

- `git diff upstream/main --stat` — the change surface must be **only** the files the
  feature owns (merged-dependency files should have disappeared).
- Install and test the branch:
  ```bash
  pip install -e submodules/linkml/packages/linkml   # or: uv sync inside the submodule
  pytest tests/linkml/test_generators/test_<generator>.py
  ```
- Smoke-test the CLI flag end-to-end (generate against a small schema; if it produces
  RDF, sanity-check with pyshacl where relevant).
- Confirm the feature still behaves as its PR description claims against **current**
  upstream (APIs it relied on may have moved in the 10s–100s of commits since).

### 4.4 Push the updated feature branch (updates the upstream PR)

```bash
git push --force-with-lease origin <feature-branch>
```

### 4.5 Rebuild the integration branch `feat/envited-x-pipeline`

```bash
git checkout -B feat/envited-x-pipeline upstream/main
# Cherry-pick each CLEAN feature branch's single commit, in dependency order.
# DROP any feature whose PR is now MERGED upstream (its content is already in main).
git cherry-pick <sha-of-feature-1> <sha-of-feature-2> ...
```

- Order matters when features touch the same generator; follow the maintainer's
  canonical list (or reproduce the previous integration order minus merged PRs).
- After cherry-picking, re-verify the OMB generator flag set (§3) is intact.
- `git push --force-with-lease origin feat/envited-x-pipeline`.

### 4.6 Update the OMB pin + regenerate + verify

```bash
cd submodules/linkml && git checkout feat/envited-x-pipeline && git pull --ff-only
cd ../.. && git add submodules/linkml            # bumps the gitlink SHA
pip install -e submodules/linkml/packages/linkml # reinstall the moved generators
make generate DOMAIN=<domain>                    # regenerate artifacts
pytest tests/                                     # + validation suite
```

Then follow **Generated Artifacts & Line Endings** (Windows CRLF normalization) before
committing, and prepare `.playground/commit-message.md` + `.playground/pr-description.md`
for the OMB pin bump.

## 5. Conventions & guardrails

- **Signed commits** (`git commit -s -S`); **never** add AI attribution or mention AI
  tools — applies to the fork too.
- Prefer `git push --force-with-lease` (never bare `--force`) on shared fork branches.
- Never bump the OMB pin to a fork commit that isn't reachable from
  `feat/envited-x-pipeline`.
- Keep per-PR branches to a single commit; keep the integration branch a clean
  cherry-pick stack (no merge commits from feature branches).
- When a dependency PR merges upstream, **drop** its commits from both the dependent
  feature branch (via `rebase --onto`) and the integration branch (omit from cherry-pick).

## 6. Worked example — PR #3450 (current task)

**PR:** linkml/linkml#3450 `feat(gen-shacl): add --message-template for sh:message`
**Branch:** `upstream/feat/shaclgen-validation-messages`
**Dependency:** #3449 `--default-language` — **MERGED upstream 2026-06-11**.

State when picked up: branch is **3 ahead / 70 behind** upstream main; the 3 commits are
`cc72304` + `f0834ab` (both #3449) and `45f8f69` (the message-template feature). Because
#3449 is merged, the two #3449 commits must drop:

```bash
cd submodules/linkml
git fetch upstream --prune && git fetch origin --prune
git checkout upstream/feat/shaclgen-validation-messages
# f0834ab = last #3449 commit; replay only the message-template commit onto fresh main:
git rebase --onto upstream/main f0834ab81 upstream/feat/shaclgen-validation-messages
```

Expected result: a **single commit** whose diff vs `upstream/main` touches only
`packages/linkml/src/linkml/generators/shaclgen.py` and
`tests/linkml/test_generators/test_shaclgen.py` (the owlgen.py / language_tags.py /
test_owlgen.py changes belong to #3449 and are now in main).

Quality check:

```bash
git diff upstream/main --stat        # expect only the two shaclgen files
pip install -e packages/linkml
pytest tests/linkml/test_generators/test_shaclgen.py -k message
gen-shacl --message-template '{name} ({class}): {description}' <schema>.yaml
gen-shacl --message-template '{name} ({class}): {description}' --default-language en <schema>.yaml
```

Then push (`--force-with-lease`), rebuild `feat/envited-x-pipeline` (dropping #3449 from
the cherry-pick set), bump the OMB pin, and `make generate` — the SHACL output uses
`--message-template "{name} ({class}): {description} {comments}"` so
`artifacts/<domain>/<domain>.shacl.ttl` should regenerate byte-identically (modulo
intended changes).

## 7. Gotchas

- **Uninitialized submodule** → git commands hit the parent OMB repo. Init first.
- **Monorepo paths**: generators are under `packages/linkml/src/linkml/generators/`,
  tests under top-level `tests/linkml/test_generators/`. Older branches on the pre-monorepo
  layout will conflict heavily on rebase — rebase onto current main brings them to the
  new layout.
- **Merged-dependency detection**: squash-merged deps won't auto-skip by patch-id; use
  `rebase --onto` to drop them deterministically rather than relying on "empty commit"
  skipping.
- **Stale pin ≠ integration head**: verify with
  `gh api repos/ASCS-eV/linkml/compare/<pin>...feat/envited-x-pipeline`.
- **CRLF on Windows** when regenerating artifacts — see the line-endings section in the
  main instructions; normalize before committing.
