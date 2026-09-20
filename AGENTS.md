# AGENTS.md - Instructions for AI agents

Non-negotiable rules, schema conventions, validation constraints for every session.

## Where to look, by the question you actually have

This file carries the rules. It does **not** carry the pipeline's detail, the
volumetry, or the history — those live elsewhere, and looking for them here
wastes a session. Sorted by the question, not by the filename:

| Your question | Go to |
| --- | --- |
| « What may I never publish? » | **§2 below** — the eight editorial rules. Nothing overrides them |
| « What rule governs this area? » — merge, CI, pre-commit guards, scope, interventions, quality gate | `docs/regles/`, one file per domain, indexed in §3 |
| « **What governs this file I am about to change?** » | `docs/decisions-par-module.md` — *this module → these decisions*, generated |
| « Why was it decided this way? » | `docs/decisions/<anchor>.md`, one file per decision, indexed newest-first by `docs/technical_decisions.md` |
| « What does the data become? » — outputs, schemas, volumetry | `docs/data-architecture.md` |
| « What does a run do? » — jobs, caches, artifacts, budgets, retry | `docs/workflow-generate-data.md` |
| « What does this provider publish, and what are its traps? » | `docs/sources/<source>.md` — each states its own status in its header |
| « What do I type? » | `docs/commandes.md` |
| « What must I update before finishing? » | **§8 below** |
| « What is this project, and what does it refuse to do? » | `README.md` — front door, editorial line, coverage limits |

**A decision is never edited in place, and neither index is written by hand** —
both are generated (§8).

Two habits this table exists to prevent, both paid for on 15/09/2026: searching
the shared checkout, which can be far behind — take a worktree and read there;
and searching `src/` by hand for a mechanism, when `docs/decisions-par-module.md`
names what governs it.

---

## 1. Product

**Empreinte politique** — "Politics made clear". Factual, sourced political CVs
(mandates, votes, texts, interventions) for 2027 presidential candidates.
`CONTRECHAMP` (`web/`) is the interface design lab. `web/UI_finale` (React 19 + Vite) is
the current production interface, wired to real pivot data (`docs/decisions/web-v3-ui.md`). Earlier design
generations — `v1`-`v7`, including the `v3` editorial reference — are archived under `web/old/`.
`web/UI_finale` navigation: **Candidats** · **Groupes** (real parliamentary groups) ·
**Gouvernement** (real governments) — no Partis tab. Three tabs, but **seven published
pages**: `/a-propos`, `/methodologie`, `/mentions-legales`, `/sources` and `/faq` live outside
the tabs. `/a-propos` says what the site is and who edits it; `/methodologie` says how each
fiche is made, and the manifesto lives on **one** of the two, never both (#1032).
`/sources` (formerly `/couverture`, which redirects to it — #951) says which source brings what, and once, for the whole corpus, what every fiche used to repeat — what the
repository holds and since when (#328).
Positioning, naming, target audience: `docs/decisions/direction-artistique-empreinte.md`.

## 2. Non-negotiable editorial rules

Duplicated in `schema_pivot.py`, `validate_profil()`, and `web/old/v3/methodologie.html`.
Any schema/display change must preserve them:

1. No value judgments, no score, no ranking.
2. Full traceability: every fact must map to a primary source.
3. No individual attendance rate is ever published.
4. A 49.3 procedure is never treated as a vote position (separate procedural fact).
5. Missing data means missing data, never default `0`.
6. `position_dans_hemicycle` always requires a verifiable `source_url` (enforced by `validate_profil()`).
7. Group ratios published only with numerator + denominator + sufficient coverage; otherwise `N/D`.
   **An individual index measured against a group average** — cohesion rate, participation rate —
   is **internal quality control** only, never public (`--rapport-interne`). **Juxtaposing, on one
   sourced ballot, a member's position and their group's majority position is a fact, and is
   publishable** — never counted, never rated, never turned into a frequency: « a voté contre son
   groupe 47 fois » is that same individual index by another route.
8. Thematic tags are reading aids, not declared candidate positions.

## 3. Pipeline

Three files carry what this section deliberately does not. **Why** a rule
exists: one file per decision under `docs/decisions/`, indexed by
`docs/technical_decisions.md`. **What the data becomes** — flow, files, schemas,
volumetry: `docs/data-architecture.md` — what `pivot_data/` publishes, rewritten
from the code on 30/08/2026 (#606). **What a run does** — the jobs, caches,
artifacts, budgets, the launch form, the push, the automatic retry:
`docs/workflow-generate-data.md`. **The rules stay here**, because a rule
behind a link is a rule that gets missed.

Public sources → `raw_data/profiles/<slug>.json` + per-legislature amendment
slices → `pivot_data/profiles/<slug>.pivot.json` → groupes / lignées /
gouvernements → `check_quality_gate.py`, which gates every commit. `raw_data/` is
source-near; `pivot_data/` is the only layer `web/` reads.

**`pivot_data/profiles/` holds three populations, and nothing on disk says so
(#630, #996).** One directory, one naming pattern — a `glob` returns all of
them. `meta.provenance == "candidat_declare"` marks the declared candidates,
the ones `web/` publishes a page for; `roster_groupe` marks the group members
and `roster_gouvernement` the government members AMO30 lists and no group
roster brings in — both collected **to feed the group and government
aggregates**. `group_profile.py` never reads their `identite` block, it
consumes `nom`, `mandats`, `votes`, `interventions`, `amendements`, all lists.
**What differs is the use, not the standard**: an identity **merge** fix covers
the declared candidates only, an identity **quality** fix covers every profile
(#556's HATVP markers were in the roster). Name the population before you quote
a figure — and the tools do it for you: every profile count they print carries
its breakdown, via `src/population_profils.py`. **The counts themselves are not
here**: every run moves them, and this file is read as current.

**Never write `provenance == "roster_groupe"` to mean "a roster member"** —
import `population_profils.PROVENANCES_ROSTER`. That equality, copied into six
modules, published a minister as `candidat_declare` and dropped the
`acteur_ref` their collection depends on, and nothing failed.
→ `docs/decisions/populations-profils-portees-par-les-outils-630.md`,
  `docs/decisions/provenance-roster-gouvernement-996.md`

### The domain rules, and why they are not here

The rules below govern **one area each**. They live in `docs/regles/`, one file
per domain, and are loaded when you touch that domain — not at every session.
`AGENTS.md` keeps the index, so a reference to « AGENTS.md §3a » still resolves.

| Where | What it governs |
| --- | --- |
| [`docs/regles/fusion-et-index.md`](docs/regles/fusion-et-index.md) | **§3a. Files, indexes, merge** — the two shared indexes, additive merge, named backfills, compact profile JSON, projection reads. |
| [`docs/regles/ci.md`](docs/regles/ci.md) | **§3b. CI: jobs, caches, artifacts** — no test reads the live corpus, cache keys, budgets, artifacts, the launch form, the push identity, the retry. |
| [`docs/regles/gardes-avant-commit.md`](docs/regles/gardes-avant-commit.md) | **§3c. The four pre-commit guards** — loss check, referential integrity, collected = published, each list carries what collection returned. |
| [`docs/regles/roster-et-sources.md`](docs/regles/roster-et-sources.md) | **§3d. Scope, sources, rosters** — Senate and NosDéputés out, the slug ↔ AN actor table, AMO30 rosters, group positions, bicameral collection. |
| [`docs/regles/interventions-syceron.md`](docs/regles/interventions-syceron.md) | **§3e. Interventions (Syceron)** — bare actor ids, verbatim reductions, séance slots, index conformity and sharding, theme-only collection. |
| [`docs/regles/portail-qualite.md`](docs/regles/portail-qualite.md) | **§3f. Quality gate** — what hard-fails, what stays soft, and why. |

**A new pipeline rule goes into one of those files, never here.** That is the
whole point: a lot about the merge touches `docs/regles/fusion-et-index.md`, and
`AGENTS.md` does not move.
## 4. Pivot schema v1 (`src/schema_pivot.py`)

**The schema lives in [`docs/regles/schema-pivot.md`](docs/regles/schema-pivot.md)** —
the field-by-field table, the group-fiche counters taken at one published date
(§4a, #653), and one sheet per group *and* per legislature (§4b, #700).

What holds everywhere, and is worth carrying without opening the file:
French `snake_case`; missing is `null`, never `""` or `0`; closed values live in
`frozenset KNOWN_*` and are checked by `validate_profil()` — **extend the
frozenset, never bypass it**. A derived field (`chambres`, `licence_donnees`,
`tags_thematiques`, `meta.avertissements`) is **recomputed after the merge**, never
merged.

## 5. Sensitive institutional fields (validation constraints)

**The constraints live in
[`docs/regles/champs-sensibles.md`](docs/regles/champs-sensibles.md)** — hemicycle
position, censure motions, ballot qualification, amendment inadmissibility, and
the caches whose existence is not conformity.

The one that governs every one of them: **a key we cannot source is never
invented, and never silently dropped** — it is published `null` alongside its
`*_non_resolu` record, which names the reason (§2 rule 5).
## 6. Metrics: public vs internal

| Metric | Status |
|---|---|
| `textes_portes[]` (stage ≥ `examine_commission`) | Public |
| `textes_portes[]` below threshold | Via explicit user toggle — not published by default |
| `textes_portes[]` **European** — any `ue_` stage **except** `ue_phase_preparatoire_parlement` | Public. The threshold is a **rank** in the French list, and no European stage has one: applying it unchanged discarded all 383 European texts. The European nomenclature is flat, so the rule is stated by exclusion — the one stage that means "not yet examined anywhere", the counterpart of `depose`. Arbitrated 14/09/2026; 58 of the 20 442 dossiers carrying a stage are in that case. A stage the source adds later is **not** published until it is placed here (§2 rule 5) |
| `amendements[]` raw counts + `par_type_deposant` | Public |
| Adoption rate across all submitter types | **Never** (misleading) |
| `amendements_agreges` on a group sheet | Public — **distinct amendments**, deduplicated on `amendement_id`. A co-signed amendment is **one** |
| Signatures laid by a group's members | Public, under `amendements_agreges.signatures`, never under the word "amendments" |
| Adoption rate over signatures | **Never** — numerator and denominator are inflated by different co-signatory counts, so the bias has no known direction (§2 rule 7) |
| `votes[]` bill vote (`vote_texte`, latest reading) | Public — **one text, one position**. The fold and the selection live ONLY in `web/UI_finale/src/utils/lecture.js`, beside `isWholeTextVote` (#711); the last reading is chosen by the **date**, over the **whole** scrutins corpus, never over the person's own votes — the rule was published for a year and implemented nowhere. See `docs/decisions/derniere-lecture-retenue-711.md` |
| `votes[]` **European** — one position per dossier | Public — **one text, one position**, the European counterpart of the last reading (#711), which does not apply: the source publishes no reading. The retained ballot is the **last** one on the dossier — latest date, then rank in the sitting — and the fold lives ONLY in `web/UI_finale/src/utils/votesEuropeens.js`. The positions carry no `scrutin_id` by contract (`index-scrutins-europeens-901`) and join `pivot_data/scrutins_europeens.json` by **number + date**. What the fold sets aside is published beside the figure, never left to a subtraction. See `docs/decisions/lecture-europeenne-themes-et-votes-901.md` |
| European **theme** of a text, an amendment or a vote | Public as a reading aid (§2 rule 8) — the EuroVoc domains of the dossier, failing that its OEIL families, never inferred from a title. One object counts under **each** of its themes in a bar chart, so its lines do not add up to the total, while the counters beside them count DISTINCT objects; a sankey splits the object pro rata instead and shows no per-theme count. A dossier the collection has not queried yet is **not** a dossier without theme |
| 49.3 / no-confidence motion | Public, labeled as procedural fact |
| Individual attendance/presence | **Never public** (rule 3) |
| Group `cohesion_votes[]` | Public, with numerator/denominator |
| Individual cohesion/participation **index** vs group average | **Never** — internal only (`--rapport-interne`) |
| A member's position beside their group's majority position, **one sourced ballot at a time** | Public — never counted, never rated |
| `mandats[].notableCount` | Internal only (display ordering) |
| `tags_thematiques[]` — the **titles of the sitting items** spoken under (`theme_officiel`), deduplicated per profile; never a closed list of categories | Public — reading aids, never declared positions (rule 8) |

Full rationale: `web/old/v3/methodologie.html` — do not duplicate prose here.

## 7. Sources and licenses (reuse implications)

| Source | Collected? | License | Constraint |
|---|---|---|---|
| data.assemblee-nationale.fr / questions.assemblee-nationale.fr | **Yes — the main French source** (#529) | Licence Ouverte / Open Licence (Etalab) | Attribution only |
| data.senat.fr | **Yes since #885 — memberships only.** The dataset carries no ballots and no floor records, so §7.2 of #528 stays **declared unmet**, not worked around. Three tables of individual attendance are refused at collection (§2 rule 3) | Licence Ouverte (`fr-lo`) | Attribution only — **no share-alike**, so a profile that gains Senate data does not enter the ODbL clause |
| Parltrack (JSON dumps) | Yes | ODbL v1.0 | **Share-alike** if republished as downloadable dataset |
| European Parliament (data.europarl.europa.eu) | Yes — **every request goes to the open-data portal**; `www.europarl.europa.eu` is only linked, never fetched (#983) | CC BY 4.0 (Bureau decision of 16/12/2024, EUR-Lex C/2025/341, art. 4) | Attribution only |
| NosDeputes.fr / NosSenateurs.fr | **No** since #528/#529 — and **no published field derives from it any more** since #976 and #718 (measured 17/09/2026 — #976 missed 331 mandate entries that carried no source name): not cited on the site | ODbL v1.0 | None while nothing derives from it — attribution and share-alike return with the first field that does |
| Sycomore (www2.assemblee-nationale.fr/sycomore) | **No — cited**: one row per deputy mandate older than AMO30's 19/06/2002 bound, hand-checked, in `raw_data/mandats_anterieurs.json` (#860) | © Assemblée nationale, all rights reserved | **Facts only** (office, dates) with a link to the page; nothing reproduced |
| Journal officiel (Légifrance) | **No — cited**: one decree per government office older than the corpus, same table (#860) | Licence Ouverte 2.0 (Etalab) | Attribution only |
| Répertoire national des élus + Municipales 2026 sortants (data.gouv.fr, `tabular-api`) | **Yes since #922 — local mandates only**, for declared candidates. Queried through the tabular API (~160 filtered requests), never downloaded (76 Mo). Coverage **starts in 2020**: the complete 2014 and 2020 datasets declare no licence, and the Licence Ouverte 2014 ones cover the first round only. An absence before that bound is **declared**, never read as « no local mandate ». The three files of mandates we already collect elsewhere — deputies, senators, MEPs — are refused at read time | Licence Ouverte 2.0 (Etalab) | Attribution only |
| EuroVoc (publications.europa.eu, point SPARQL) | **Yes since #901 — two readings, both in French**: `skos:prefLabel`, to name a concept whose identifier the European Parliament already gave, and since 17/09/2026 the concept's **domain**, read along the thesaurus (concept → microthesaurus → domain), never inferred from a label. Nothing is discovered here and nothing is classified here: the subject of a document is the Parliament's fact, never our reading of its title | CC BY 4.0 | Attribution, and changes must be stated. A code the thesaurus does not return is **never invented**: the document keeps the labels found and declares the others |
| French Wikipedia | Yes — the declared-candidate list only (#753) | CC BY-SA 4.0 | **Facts only** (names, party labels) into `raw_data/candidats.json`, never verbatim prose. It reaches no `sources[]`, so it moves no `meta.licence_donnees` |
| Wikidata | **Yes since #757 — one property, `P4123`** (the AN actor id), to resolve a declared candidate's actor. **Not** for discovering candidates: `P3602` returns 1 person for the 2027 election against 30 declared (#753) | CC0 1.0 | No restriction |

**"No French source is collected from Regards Citoyens any more" does not mean "the
corpus is under Licence Ouverte" (#530).** Share-alike survives on two counts: Parltrack
is a *live* source under ODbL, and the Regards Citoyens marker survived on the profiles
whose data still needed it. That second leg shrank as retractions were written, and was
**measured empty after #976** (16/09/2026) — share-alike now rests on Parltrack alone. **Its
size is a measurement, never a constant: re-measure before relying on it, never read a
published figure as today's corpus** (#886). `merge_pivot_profile` unions `sources[]` by
type, so additive regeneration never drops a marker **and a retraction has to be
written**, at both layers; aggregates recompose instead, and follow on their own.
Attribution stays due while the fields stay published (§2 rule 2) — and stops being due
when they no longer are.
→ `docs/decisions/licence-lot-6-530.md`,
  `docs/decisions/retrait-marqueur-regards-citoyens-deputes-890.md`

`meta.licence_donnees` is therefore a **derived** field, never a constant: `src/licences.py`
holds the four canonical labels and `appliquer_licence_donnees(profil)` recomposes the
string from `sources[]` after every step that changes it (`normalize_profil`,
`normalize_europarl`, `enrich_pivot_with_parltrack`, `merge_pivot_profile`). Same pattern as
`chambres` in #493 — and its retirement condition runs itself: the ODbL clause leaves a
profile the day that profile stops carrying anything from Regards Citoyens.
Never hardcode a licence label elsewhere; import it from `src/licences.py`, and keep
`AGENTS.md` §7, `sources.config.js` and `LegalNoticePage.jsx` saying the same thing.

**The code is AGPL-3.0 since 18/09/2026 (#1032), and it changes nothing here.** `LICENSE`
covers the code only: the editorial texts and the graphic identity are all rights reserved, and
the data keep their sources' licences — a software licence does not reach them. What the AGPL
does add is an obligation on us: the deployed site must correspond to the published code, its
section 13 being the reason `/a-propos` carries the link to the repository.

Site HTML = ODbL "Produced Work" (attribution sufficient). Downloadable raw data → share-alike.
Full details: `docs/decisions/licences.md`, `docs/decisions/licence-lot-6-530.md`.

## 8. End-of-task documentation upkeep

Before finishing a task, update only what actually changed — skip a file if nothing changed for it:

**A source added, removed or changed is never one file.** Four move together, and
each says something the others do not: `docs/sources/<source>.md` (what the
provider publishes, and its traps), `docs/data-architecture.md` (what the data
becomes), `docs/workflow-generate-data.md` (the job that fetches it), `README.md`
(the reader's table, with its licence). `AGENTS.md` §7 carries the licence and
the reuse constraint. Miss one and the source exists in some files and not in
others — measured on #922, where the RNE reached §7, the architecture and the
workflow, but neither `docs/sources/` nor the README.
`tests/test_sources_documentees.py` fails on a source documented in one place and
absent from another.

| File | Update when |
|---|---|
| `AGENTS.md` | **A rule that governs everything** — editorial, reporting, what to ask. A rule that governs **one area** goes to `docs/regles/`, never here (#737). **Never a count that a run or a lot moves** — corpus sizes, profile populations, file inventories: here they are read as current long after they stopped being so. The figure lives in the decision that measured it, or in the tool that prints it. Rare edit; stay terse. |
| `docs/regles/<domaine>.md` | **The rule you are about to add governs one module or one job.** Eight files, one per domain, indexed by `AGENTS.md` §3 — loaded when you touch that domain, not at every session. Keep the instruction, put the measurement and the incident in the decision file. `tests/test_regles_par_domaine_737.py` fails when a file empties, leaves the index, or when a section the repo cites stops being named in `AGENTS.md`. |
| `README.md` | **The front door, one page.** A new setup step, a change to the editorial line or to a coverage limit, a doc that becomes an entry point. Never a command — that is the row below. |
| `docs/commandes.md` | **An option is added or removed, a script is renamed or retired, a command's output moves.** Not when the pipeline changes: the file says what to type, never how the run works. `tests/test_commandes_documentees.py` fails on a script or a long option that no longer exists. |
| `docs/data-architecture.md` | A file under `pivot_data/`/`raw_data/` appears or changes shape, a source is added or removed, a normalisation or aggregation step moves. **The schema changed — say what it now publishes, in the same lot.** A value added to a closed vocabulary (`KNOWN_*`) changes what a fiche can carry, and a field added to a raw block reaches nothing until something versates it: both belong here, not only in `src/schema_pivot.py`. `tests/test_sources_documentees.py` fails on a value of `KNOWN_CATEGORIES`, `KNOWN_CHAMBRES` or `KNOWN_CATEGORIE_SOURCES` that no documentation names. **Every volumetry carries its own measurement date**: a row filed under another row's date reads as true on that day — `lignees/` was once dated 30/08, a day it did not exist. |
| `docs/workflow-generate-data.md` | **The entry point for every job** (§1: what each one does, consumes, produces, and its structuring decisions). **A job added to the workflow gets its block here, in the same lot** — name its entry script and the modules it reads, or the next session greps 4 000 lines of YAML to find them. Update too when what a job does or touches changes, when a form input, cache key or artifact name changes, when a budget is re-measured, or when the retry contract is touched. `tests/test_sources_documentees.py` fails on a job the YAML declares and this file does not name. |
| `docs/extract-roster-groupes.md` | The only extraction job with a page of its own — it has depth a block cannot hold (rollout, regenerating existing profiles, the roster's three exit codes). A new job does **not** get a file: it gets a block in `docs/workflow-generate-data.md` §1. Eight files drift independently; one is reread in a single pass. |
| `docs/sources/` | **External-source references — the only docs that drift with their provider, not with our code.** Update when the provider moves a dataset, a URL pattern or a field, never because our pipeline changed. Each file states its own status in its header (`an-opendata.md`: live, the main French source; `senat-opendata.md` and `parltrack-et-europarl.md`: live; `nosdeputes/`: historical, not queried since #529) — the directory names the category, the header names the status. |
| `docs/decisions-par-module.md` | **Never by hand — it is generated.** Run `python3 scripts/generer_decisions_par_module.py` whenever a decision is added or edited, a `src/` module is added, renamed or removed, or a top-level function/constant a decision names is renamed. `tests/test_decisions_par_module.py` fails when the committed file has drifted, and when a module governed by 5 or more decisions cites none. |
| `docs/decisions/<anchor>.md` | New architectural choice or trade-off. **One decision = one new file**, never an insertion into an existing one. Level-1 `#` title carrying the issue number and the date, then context, decision, alternative rejected. Name it in kebab-case with the issue number (`retrait-senat-528`). |
| `docs/technical_decisions.md` | **Never by hand — it is generated (#840).** The decision file carries its own date and its own `> **En bref** — …` summary; run `python3 scripts/generer_index_decisions.py` and the index follows. It was hand-maintained, and every lot wrote at the same spot — a line inserted at the top — so two parallel branches conflicted systematically: four rebases in one hour on 10/09/2026. `tests/test_index_decisions.py` fails when the committed index has drifted, or when a decision lacks what its line needs. |
| `ROADMAP.md` | **A large piece of work to plan for**, or a known defect that stays open. **Never a small fix — that is a GitHub issue.** It holds what GitHub cannot: the scoping findings that must not be re-litigated, and the known defects a cold-start session has to read. **Never a list of issues**: one was removed on purpose, because a table copying GitHub's state goes stale with every lot shipped, and a wrong table is worse than none. Keep entries to one line; put rationale in `docs/decisions/<anchor>.md` instead. |
| `CLAUDE.md`, `.github/copilot-instructions.md` | **Never — they are symlinks to this file.** One source, several names, so the instructions cannot drift between tools. Adding a tool that expects another name: create the symlink and add it to `ALIAS` in `tests/test_instructions_agents.py`. |
| `requirements.txt` | A new package is imported that isn't already listed. Pin the version actually installed/tested (`==`), don't add unpinned entries. |
| `requirements-dev.txt` | A new **test-only** package is imported. Same pinning rule; it already pulls `requirements.txt` via `-r`. |

Never create a missing file from this list without flagging it first.

## 9. Reporting to the owner

The rationale lives in this file and in `docs/decisions/`. Don't restate it in
chat.

**Length is a rule, not only shape — aim for ten lines.** Formatting buys no
extra room: a forty-line reply, tables and short paragraphs included, still makes
the owner reread everything to find the one thing that needs her decision.
Measured on three consecutive reports, 30/08/2026, each well-formatted and each
too long. Sorting is the agent's work, not hers.

- **One arbitration per reply.** When several points need a decision, raise the
  first and wait. Sequenced replies beat one complete report — she asked for this
  explicitly.
- **The detail lives in the deliverable, not in chat.** The document, the issue,
  the decision file carry the full reasoning; the reply carries the conclusion
  and the question.
- **A table whenever two things compare.** Prose forces a reread to compare two
  lines; a table is scanned. Applies to issue rundowns, before/after
  measurements, options with their costs.
- **No paragraph over four lines.** Break it, or turn it into a table.
- **Every time is given in Paris time.** The GitHub API returns UTC, suffixed
  `Z`; the owner's machine is `Europe/Paris`. Convert before quoting a
  `createdAt`, a job timestamp or a log line — `TZ=Europe/Paris date -d "<iso>"`.
  A duration needs no conversion, an instant does. Quoted raw, a two-hour shift
  turns an ordinary wait into an anomaly, and it was the owner who caught it.
- **Every figure names its population.** "20 members of the two Senate group
  files", never "20 senators". A correct figure on the wrong population is an
  error, not an approximation.
- **Never restate what the previous turn established.** No preamble, no "in
  summary" recap, no list of files read or alternatives discarded.
- **One recommendation, not a survey.** If two options are open, say which one
  and why in a sentence — then let the owner overrule.
- Test/command output: pass/fail counts only, unless something failed.
- Always flag, even briefly: schema/validation changes, anything touching
  Section 2, new warnings or errors introduced.
- **End every reply with what remains.** Never present partial work as done:
  the last lines say what is still open, so nothing silently drops.
- **A PR touching `src/` or `raw_data/*.json` pushed while a data run is going
  says "do not merge"** — first line of the reply and of the PR body. The run
  commits data built from the code it started with; merging under it mixes two
  states.

## 10. A subagent's report is a claim, not a result

Before relaying **any** figure, file path, test name or measurement produced by
a subagent, re-run the check yourself. Say what you verified, and say what you
could not.

This is not precautionary. Three drifts in a single day, 29-30/08/2026:

- an issue cited `test_les_inputs_du_retry_sont_tous_ecrits`; **that test does
  not exist**, and the name was passed on into agent instructions before anyone
  checked;
- a review reported "680 of 1 016 positions"; re-measured, it was **715** — the
  substance held, the figure did not;
- an agent reported a repo state that a second agent had already changed under
  it, and the collision only surfaced because the state was re-read.

A subagent that reports honestly still reports from a corpus that moved, a
grep that missed a case, or an instruction that was wrong. Verification is the
main agent's job, and it is the only place it can happen.

## 11. What to ask the owner, and what to decide alone

**Ask when the answer changes what gets built, and cannot be derived** from the
code, from Section 2, or from a decision already recorded in `docs/decisions/`.
A form's shape, a threshold's fate, a trade-off with a measured cost, deleting
unmerged work, pushing to a public repo: those are hers.

**Show before implementing anything a human will read on screen** — input
labels, published copy, page text. She has asked for this explicitly, and it is
the one case where reviewing draft wording is wanted. Render it as it will
appear (`scripts/rendu_formulaire.py` for workflow inputs), not as source.

**Do not ask her to review your own work.** Sub-issue bodies, commit messages,
agent instructions, which files to touch, how to name a branch: that is the
agent's job. Bad work gets corrected, not pre-approved. A report listing every
draft produced buries the two or three decisions that are genuinely hers —
sorting is the agent's work, not the owner's.

**One "awaiting your decision" section per report, and nothing else pending.**

**Push yes, merge never.** Branch, push and open the PR without asking; the
merge is hers, always.

**A mockup before code, on anything visual** — an artifact, rendered on real
data, and **several forms to compare**, not one. Charting libraries (D3,
ECharts…) may be loaded in a mockup; the constraint "one form, bars only" was
never hers. Explanatory text on a figure is an admission that the form failed.

### Working alongside other sessions

- **One worktree per session.** The main checkout is shared between sessions:
  never `checkout`, `stash`, `clean`, `reset` or `pull` in it. A green suite
  means something only in your own worktree.
- **Write to another session only when she asks.** When she tells you what
  another session is doing, that is information, not a request to relay — a
  message sent on your own initiative arrives twice, and may state a decision
  differently from how she put it.
- **Data needs flow from the interface to the backend.** The session that draws
  a figure states the field it needs; the backend session does not go looking.
- **Warn at about 80 % of the context**, one line at the top of a reply, before
  a compaction happens — the agent estimates, `/context` gives the figure.

### The shape of an arbitration

When something does need deciding, five parts, in this order:

1. **The concrete problem, with the measurement that makes it real.** Not "the
   labels are unclear" but "22 rendered lines for 10 fields".
2. **The question, on one bold line of its own.** This is the part most often
   lost: a question buried in exposition reads as commentary.
3. **Each option with its cost.** A table beyond two options.
4. **"My recommendation", and its reason in one sentence.**
5. **What follows regardless of the choice**, so the decision isn't taken
   under the impression that everything hangs on it.

## References

- `src/schema_pivot.py`, `schema_groupe.py`, `schema_parti.py`, `schema_gouvernement.py`: structure contracts.
- **An audit is a consumer like any other, and nothing warns it that a field
  moved (#726).** Before reading a field, check it is still where the schema puts
  it. Two rules came out of it and hold everywhere: an absence is not a fault
  (§2 rule 5), and **a fixture describing the world as the code imagines it
  cannot reveal that the world moved** — the incident, the fields concerned and
  the reasoning are in the decision.
  → `docs/decisions/audit-champs-deplaces-726.md`
- `src/check_quality_gate.py`: the quality gate, one numbered block per concern —
  the list is the module's `main()` and the run summary, not this line, which
  went stale the day a block was added. The `n/4` denominators printed are
  themselves stale. Hard vs soft fail logic.
  Amendements coverage/freshness are deliberately never hard fails — see
  `docs/decisions/amendements-zero-pas-de-hard-fail.md`.
- `docs/sources/`: external-source references, which drift with their provider and not
  with our code. `an-opendata.md` (AN open-data JSON schemas — live, our main source);
  `senat-opendata.md` (live since #885 — memberships only); `parltrack-et-europarl.md`
  (live — the two European sources, and the dump format that was assumed for the module's
  whole life); `sycomore-et-journal-officiel.md` (cited, not collected);
  `nosdeputes/` (historical, not queried since #529). Status is in each file's header,
  not in the directory name.
- `docs/extract-roster-groupes.md`: the roster-driven job, in depth (the other seven jobs are blocks in `docs/workflow-generate-data.md` §1).
- `docs/commandes.md`: every command the owner may have to type, grouped by
  intention (generate, audit, check before committing, operate, see what the user
  sees). The pipeline-internal executables are left out, and
  the file says so. Locked by `tests/test_commandes_documentees.py`.
- `docs/data-architecture.md`: what the data becomes — the outputs of
  `pivot_data/` (profiles, groupes, lignees, gouvernements, scrutins,
  amendements, commissions_dossiers). `lignees/` est arrivé avec #836 : **une**
  fiche par LIGNÉE de groupe, et c'est la seule collection que l'interface
  publie côté groupes. Tous sont produits et versionnés — `partis/` est sorti
  avec #906, faute de lecteur.
  `commissions_dossiers.json` ne résout que les dossiers **déposés à l'AN** : le
  référentiel est celui de l'AN et le Sénat est hors périmètre (#528) — une
  absence de cause connue, à déclarer et non à combler. Ses volumes et son taux
  de résolution vivent dans `docs/data-architecture.md`, pas ici.
- `docs/workflow-generate-data.md`: what a run does — every job one by one, the
  form, caches, artifacts, budgets, push, automatic retry. **Start here for "what was
  that job again, and why like that".**
- HATVP lobby-register: out of scope, and **there is no file for it** — this
  line named `docs/hatvp_opendata.md`, which never existed. The verdict now
  lives in `docs/decisions/hors-perimetre.md`, with the distinction from
  `identite.uri_hatvp`, the one HATVP datum the pipeline does carry.
- `src/json_io.py`: profile JSON write format (compact vs indented, #433).
- `src/normalize_profil.py`: raw FR profile → pivot adapter (named
  `normalize_nosdeputes.py` until #529).
- `src/licences.py`: canonical licence labels + the derivation of `meta.licence_donnees` (#530).
- `docs/decisions-par-module.md`: the same decisions read the other way round —
  **this module → these decisions**, generated from the symbols each decision
  names. Open it when you are about to change a file under `src/` and want to
  know what governs it. `docs/decisions/table-inversee-decisions-par-module.md`
  holds the criterion and what it misses.
- `docs/technical_decisions.md`: the generated index of every decision file under
  `docs/decisions/`, newest first — the chronological read. Frequent entry points:
  `docs/decisions/direction-artistique-empreinte.md` (positioning, naming, targets),
  `docs/decisions/collecte-vide-necrase-jamais.md` (merge), `docs/decisions/licences.md`,
  `docs/decisions/licence-lot-6-530.md`, `docs/decisions/ci-cd.md`,
  `docs/decisions/ci-tests-pytest.md`, `docs/decisions/web-v3-ui.md`,
  `docs/decisions/hors-perimetre.md`, `docs/decisions/profils-json-compact.md`.
- `docs/archive/`: the pre-split copy of the old single file, frozen at 30/08/2026.
  **Never cite it** — its anchors are prefixed `archive-` on purpose, and
  `tests/test_index_decisions.py` refuses any path pointing into it.
- `ROADMAP.md`: known bugs + unscheduled ideas, kept short (not read
  automatically — consult on request). Rationale for deferred items lives
  in `docs/decisions/hors-perimetre.md`, not duplicated here.
