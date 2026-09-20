<!-- Extrait d'`AGENTS.md` par #737. Ces règles ne changent pas de nature en
changeant de fichier : elles restent des instructions, et un renvoi
« AGENTS.md §3b » continue de les désigner — `AGENTS.md` en garde la ligne
d'index. Ce qui change, c'est qu'un lot qui ne touche pas ce domaine n'a plus à
les charger, ni à les faire grossir. -->

# §3b — CI : jobs, caches, artefacts

### 3b. CI: jobs, caches, artifacts

- **A test run reduces the matrix and nothing else — and it never commits (#792).** Two
  consecutive runs cost 1 h 13 and 1 h 15 to surface a one-line defect; there was no rung
  between a unit test (half a second) and a full run. The `test_slugs` field, **first in the
  form**, shrinks the `extract-an` matrix, caps the roster at 8 members on 1 shard when no
  cap was asked for, and **disarms the commit**. One field for three effects, deliberately:
  two independent checkboxes would allow "reduced scope AND commit", i.e. publishing a
  corpus known to be partial — the only one of the three that cannot be undone. **What the
  mode must never change is the workflow itself**: same jobs, same order, same code, and the
  four pre-commit guards still run, since exercising them is the point. A test mode that
  diverged from the real one would prove nothing about what it was built to prove, and that
  failure is unrecoverable — you cannot learn afterwards what it did not exercise. It
  replaces no test: #788 was a half-second unit test, and this mode exists for what no test
  can see, orchestration. **And it is not a short loop: measured, a test run costs 51 min
  against 1 h 15** — `merge-and-pivot` is half of it and cannot shrink, since it redoes both
  pivot passes, the aggregates and the four guards over the **whole corpus**, which is
  exactly what the run exists to exercise. The gain is a third, not three quarters, and it
  lands on the half that fails early. A requested slug outside the scope is **named**
  (`TEST_SLUG_INTROUVABLE`) and an empty scope fails at the matrix job
  (`TEST_PERIMETRE_VIDE`), never an hour later — otherwise "you mistyped it" reads as
  "nothing to collect" (#510, #771).
  → `docs/decisions/run-de-test-perimetre-reduit-792.md`,
    `docs/decisions/cout-reel-du-run-de-test-792.md`
- **An artifact that was published and did not arrive is a failure, not an absent source
  (#786).** Run `34241352524` is **green and collected nobody**: its four extraction
  downloads left within the same second and all took a **403 "secondary rate limit"** on
  `ListArtifacts`, which `download-artifact` declares *non-retryable*. The four steps carry
  `continue-on-error: true` — correctly, since a source that produced nothing must not block
  the others — so the merge saw empty directories and wrote **0 profiles** where the previous
  run, same code, wrote **636**. The 40 AN and 8 roster artifacts were published and
  unexpired. **No existing guard could see it**: they all measure collection *after* the
  merge, and with no raw profile there is no loss to report (#460) and nothing
  collected-not-published to flag (#511). Hence `src/verifier_transport_artifacts.py`,
  between the downloads and the merge — the only point of the run holding **both** terms, the
  run's artifact **inventory** and the **disk**. Three outcomes, and they must stay named
  apart: nothing published → silence (#412 §2.1's fallback holds), published and arrived →
  nothing to say, published and missing → **failure**, retried through `gh run download` and
  then blocking. The retry deliberately takes the **other path** (`gh` goes through the repo
  REST API where the action queries `results-receiver`, the one that returned the 403), and
  flattens what `gh` files per sub-directory. Two asymmetries hold: `parltrack-dumps` is
  retried but never blocking (declared fallback, gate §5), and an **unreadable inventory does
  not fail** — "I cannot check" is not "there is nothing" (§2 rule 5), which is why
  `inventaire()` returns `None` and never an empty list. The token comes from `github.token`,
  never `secrets.GITHUB_TOKEN`: this job gets **one** identity under `secrets.`, the deploy
  key that pushes (#508).
  → `docs/decisions/transport-artifacts-panne-ou-absence-786.md`
- **No test may read `pivot_data/` or `raw_data/profiles/`, write anywhere under
  `pivot_data/`/`raw_data/`, or hit the network (#473).** Acceptance tests use frozen
  fixtures; `tests/conftest.py` cuts `requests.Session.send` and fails loudly, naming the
  URL. **Loopback stays open** — the criterion is leaving the machine, not speaking HTTP.
  Watch CLI/function **defaults** pointing into the repo. Test-only deps go in
  `requirements-dev.txt`.
  → `docs/decisions/ci-tests-pytest.md`
- **No test opens a `.json` of `raw_data/` without declaring it — and a guard must cut
  `builtins.open`, `io.open` **and** `Path.open`, because none of the three catches the
  other two (#791).** `Path.open()` calls `io.open`; `builtins.open` is a different
  reference to the same function, so patching one leaves the other intact. Measured on the
  full suite, 10/09/2026: of the 144 tests opening a watched repo file, **40** reached one
  through `builtins.open` and **105** through `pathlib` (one test both ways) — the #721
  cache guard had the same hole
  from the day it was written, and one test was walking through it. What a run rewrites
  (`candidats.json`, `correspondance_acteurs_an.json`, `resolutions_candidats.json`) is
  read from a frozen fixture under `tests/fixtures/`. What is a **committed configuration**
  whose validity is itself the subject of a test — `groupes_reels.json`,
  `gouvernements_reels.json`, `candidats.json` — is declared file by file with
  `pytestmark = pytest.mark.lit_reference_committee("<path>")`, and the guard **accepts the
  declaration only if the path is in the `sparse-checkout` of `tests.yml`**: what CI does
  not download, a test reads only locally, on whatever a run left there. Clear module memos
  at **both** ends of the fixture (#767): a memo left full serves a neighbour's table
  without reopening a file, so the guard never sees it.
  → `docs/decisions/lectures-du-depot-dans-les-tests-791.md`
- **A cache key is a freshness policy only until someone adds `restore-keys` (#749).** The
  amendements index went **18 days** without a single rebuild: #249 made the weekly key the
  *only* staleness mechanism (§3d's 7-day threshold is documented as aligned on it),
  #250/#251 rebuild only when the cache is absent or corrupt, #253 **explicitly rejected**
  an unconditional re-download — and #424 then added a `restore-keys` prefix, for the good
  reason of avoiding a cold cache at the week boundary. Together, the cache is never absent,
  so the rebuild never happens. **No module was wrong; the defect lived between two
  decisions**, and the soft warning built for exactly this case rang every run with no
  reader. `outputs.cache-hit` is `'true'` on an **exact** primary-key match only, never on a
  `restore-keys` restore — that is the "new ISO week" signal, and it now arms
  `--reconstruire-actives`, which purges the **non-frozen** legislatures alone (283 Mo, not
  1,22 Gio: re-materialising a frozen index costs the RSS of
  `oom-reconstruction-amendements-figees`). **When a job's log names the loop's intention
  rather than what happened, a dead job reads as a working one**: « Construction de
  l'index… 642 acteurs » was printed for a 0,28 s step that downloaded nothing.
  → `docs/decisions/fraicheur-index-amendements-749.md`
- **A test reading the developer's `.cache/` passes for the wrong reason, and CI never
  sees it (#721).** The eleven cache constants are `Path(".cache") / …` — **relative to
  the cwd**, i.e. the repo root locally. CI's sparse checkout does not materialise
  `.cache/`, so the read fails and the fallback applies; on a machine that has collected,
  it **succeeds**. `tests/conftest.py` filters `builtins.open` and refuses any path under
  the repo's `.cache`, naming the file (patron of #473). **Redirecting the constants was
  tried and rejected**: it breaks the tests that already isolate via
  `monkeypatch.chdir(tmp_path)` and write to a *relative* `.cache` — an absolute constant
  strips their isolation. The property everything rests on — **the constants stay
  relative** — is tested, with a witness counter. `.cache` is listed in
  `_NOMMES_POUR_ETRE_REFUSES` of `tests/test_ci_perimetre_sparse_checkout.py`: it is named
  to be **refused**, never read, and it must stay out of the sparse-checkout or the guard
  becomes a lie.
  → `docs/decisions/cache-du-poste-hors-des-tests-721.md`
- **A test reading a file outside `tests.yml`'s sparse-checkout passes locally and fails
  in CI** — #434, then #518 twice. Whitelisting the file is half of it; the other half is
  `tests/test_ci_perimetre_sparse_checkout.py`, which fails **locally** on an uncovered
  path literal and checks the reverse too. **A top-level file counts as much as a
  directory.** When it slips through anyway (three times now: #434, #520, `CLAUDE.md` on
  30/08/2026), the `pytest_runtest_makereport` hook of `tests/conftest.py` names the cause
  in the CI log — it diagnoses, it does not prevent, and it stays silent on any other
  failure. It is locked by `tests/test_hook_diagnostic_sparse_checkout.py`, which drives
  it without failing anything: **a diagnostic that goes mute without saying so is worse
  than none.** The block itself is parsed in **one** place, `tests/_outils_ci.py` — a
  conftest cannot import a test module, so the shared parser lives beside it, unparsed by
  pytest and imported by path.
  → `docs/decisions/point-de-sauvegarde-dans-les-profils-518.md`,
  `docs/decisions/hook-diagnostic-sparse-checkout.md`
- **The launch form is two disjoint axes plus the cache (#578).** `existing_profiles`
  decides what happens to profiles already written (`overwrite` alone raises
  `--no-merge`); `add_uncovered_members` decides whether members with no profile get one;
  `cold_start` says nothing about how profiles are written; `roster_limit` is a cap and
  commands no refresh policy. Commit only if `check_quality_gate.py` exits 0. **Run
  `python3 scripts/rendu_formulaire.py` before touching a label** — reading the YAML hides
  exactly the defect #578 fixed.
  → `docs/decisions/ci-cd.md`, `docs/decisions/deux-axes-formulaire-578.md`
- **The push identity decides whether any workflow sees the data commit — and today none
  does (#508, #685).** A `GITHUB_TOKEN` push emits **no `push` event**; only a deploy-key
  push does. #508 wired `ssh-key: ${{ secrets.DATA_PUSH_SSH_KEY }}` into `merge-and-pivot`,
  but the three manual gestures its §7 names — deploy key, secret, ruleset — were **never
  performed** (measured 01/09/2026: zero deploy keys, no such secret, no
  `required_status_checks`), so the push still goes out under the token and **0 of the 15
  data commits since `tests.yml` exists carry a test run**, the 11 since #508 included. Its
  **loud** rejection cannot fire either: it speaks only on a `GH013`, which needs the
  required check that was never restored — two omissions covering each other, which is why
  fifteen commits went unnoticed. `merge-and-pivot` now **measures the remote it actually
  pushed to** and says so in an annotation and in the job summary, non-blocking; the
  guarantee returns only with #508 §7, never by editing this line.
  → `docs/decisions/push-donnees-cle-de-deploiement-508.md`,
  `docs/decisions/identite-du-push-et-declenchement-des-tests-685.md`
- **A job never writes a cache key for a directory it does not fill.** Three times:
  #412 §2.3 → #424 → #505. A job carrying a `--skip-*` flag uses `actions/cache/restore`;
  a key whose **content** depends on an input carries that input; two jobs sharing a key
  share the exact same `path:`; an index is cached only once **complete**. Locked by
  `tests/test_ci_cache_producteur_ecrivain.py`.
  → `docs/decisions/cache-mode-interventions-505.md`
- **Never raise `timeout-minutes` without `--budget-interventions-secondes`, or the
  reverse (#498).** A shard killed by `timeout-minutes` writes **no profile at all**; an
  exhausted budget writes the partial profile and declares the truncation in
  `meta.warnings[]` (§2.5). Guarded by `tests/test_ci_budget_interventions.py`.
  → `docs/decisions/budget-collecte-interventions.md`
- **Every collection path must declare what it does with interventions (#501).** A new
  invocation of `generate_all_profiles.py` goes into `tests/test_ci_interventions_par_job.py`
  with its mode, and a job that ignores the input is named in the input's description.
  → `docs/decisions/interventions-senat-501.md`
- **One artifact = one job's contribution (#450).** An extraction job publishes only the
  profiles it actually wrote — never `raw_data/profiles/`, which its `actions/checkout`
  also filled with the committed baseline. Guarded by
  `tests/test_ci_publication_profils.py`.
  → `docs/decisions/publication-scopee-artifacts.md`
- **One roster per run (#518).** `raw_data/roster_candidats.json` is built once and
  shipped as an artifact; a consumer regenerates it **only if the artifact is missing**.
  `fetch_full_roster` retries timeout/`ConnectionError`/5xx and **never** `SSLError`
  (subclass of `ConnectionError` — order matters) or 4xx. Blocking anomalies are
  `::error::` annotations via `src/gha.py`, **stdout only**, single-line.
  → `docs/decisions/roster-unique-par-run-518.md`
- **Retrying under a ceiling set too low does not buy back the ceiling (#518, second
  incident).** A production timeout sits **outside** the endpoint's response distribution;
  `_ROSTER_TIMEOUT` is split `(connect, read)` with **connect unchanged** — #516's
  deterministic `SSLError` verdict rides on it. The run's **raw** roster ships in the same
  artifact, or a group sheet diverges from the collected corpus with no step failing.
  → `docs/decisions/plafond-roster-et-commit-518.md`
- **A source outage costs the roster branch, never the commit (#524).** The exception —
  not the key — reaches the `::error::` annotation; the roster steps tolerate codes **1
  and 2 in the shell** and the pivot step is gated on `hashFiles(...)`, on the **file**,
  not on a step's success; "every group suspended" returns `EXIT_ROSTER_INDISPONIBLE = 2`,
  tolerated by all **three** callers. **Never `continue-on-error: true`** there: it would
  swallow code 1 and commit a stale sheet with nothing blocking.
  → `docs/decisions/cloisonnement-branche-roster-524.md`
- **`retry-generate-data.yml` is coupled to `generate-data.yml`, and nothing in either
  file says so.** The API does not expose a run's inputs, so the retry **rebuilds them
  from the logs** and re-dispatches with `-f`. Two silent failure modes: a `-f` with no
  matching input (422 on the day a retry is needed), and an output written under one name
  and read under another (the retry restarts on the defaults, no error, no trace). Locked
  by `tests/test_ci_inputs_workflow.py`. Read `docs/workflow-generate-data.md` §7 before
  touching either workflow's inputs.
  → `docs/decisions/retry-inputs-appariement-prefixe.md`
