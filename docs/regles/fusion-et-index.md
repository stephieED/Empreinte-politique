<!-- Extrait d'`AGENTS.md` par #737. Ces règles ne changent pas de nature en
changeant de fichier : elles restent des instructions, et un renvoi
« AGENTS.md §3a » continue de les désigner — `AGENTS.md` en garde la ligne
d'index. Ce qui change, c'est qu'un lot qui ne touche pas ce domaine n'a plus à
les charger, ni à les faire grossir. -->

# §3a — Fichiers, index, fusion

### 3a. Files, indexes, merge

- **A profile is merged; an aggregate is recomposed — and that difference decides where a
  retraction has to be applied (#890).** `merge_pivot_profile` is additive: `sources[]` is
  unioned by `type`, so a type a fresh collection no longer returns is **never** dropped —
  which is why the Regards Citoyens marker survived on 475 profiles eighteen days after
  `retrait-senat-528` §3 announced it would disappear on its own. Group, lineage,
  government and party sheets work the other way: `group_profile` assigns
  `profil_groupe["sources"]`, rebuilt from the member profiles on every run, and
  `lignee_profile._union_sources` unions the **sheets**, not a previous version of itself.
  `--merge-existing` does not weaken this — it recovers **members** missing from a live
  roster, never a `sources[]` entry. Measured on 13/09/2026, regenerating the 29 sheets a
  run produces: **2 001 marked occurrences over 23 sheets → 1 over 1**, the only survivor
  being the entry of a profile that legitimately keeps its marker. **So a retraction is
  applied to the profiles and to the raw layer, and the aggregates follow by construction**
  — purging them by hand would write, one run early, what the pipeline writes anyway.
  → `docs/decisions/retrait-marqueur-regards-citoyens-deputes-890.md`

- **A closed legislature's amendments are already stored, deduplicated and inverted — the
  raw slices only recopy them (#691).** `raw_data/profiles/` weighs 9.7 GiB, 89 % of it
  amendment slices, and no single field is large: `co_signataires` is **79.5 %** of a
  slice's weight because an amendment with 74 cosignatories is written into **75 files**,
  each carrying all 75 identifiers — 5 625 identifiers for information worth 75, at the
  **median**. `raw_data/amendements_an_figes/` already holds the 624 180 amendments of the
  three closed legislatures in **38 MB** gzipped, **plus** an `index_par_acteur.json.gz`
  that returns `{uid, role_signataire}` — precisely the shape pivots consume since #431.
  Reconstruction is a join, and it is **exact**: 120 profiles, 568 771 amendments, zero
  field-level discrepancy, with only two derived fields (`role_signataire` from the actor
  index, `legislature` from the filename). Two rules follow. **Normalise the XML nils**:
  the archive keeps `{"@xsi:nil": "true"}` where collection writes `null` — 8 entries out
  of 624 180, rare enough to go unseen and real enough to break §2 rule 5. **Never route
  the pivot through a rebuilt slice**: `mapping_pivot()` goes from archive to final shape
  directly, because rebuilding a duplicated list to deduplicate it three lines later pays
  in compute what was just saved on disk. And nothing is deleted before the consumers are
  settled — seven read that field, one of them (`merge_profile`) being a **guard**, not a
  source: the committed slice is what protects against an empty collection, and collection
  reads a CI cache that is not versioned. **Both of those worries turned out backwards
  (#691 lot 2).** Order is not an obstacle: `audit_diff_profils` records a list as an
  **integer**, so a loss is a drop in count, never a change of sequence. And the merge guard
  is *strengthened*, not weakened — today `old` is whatever a previous run managed to
  collect, hostage to an unversioned CI cache, whereas a derived `old` is the committed
  archive, the whole truth of a closed legislature (**854 slices out of 854 covered**,
  measured). What must hold instead: **the manifest has to say `derivee`, and silence stays
  a failure** — reaching for the archive "in case the file is missing" would read a *lost*
  slice as a derived one and republish a truncated profile, the exact distinction
  `PartitionIllisible` carries since #580. The actor comes from the manifest, never a join;
  the announced `nombre` is a check, never a source (#576, #579).
  → `docs/decisions/reconstruction-tranches-depuis-archive-691.md`,
    `docs/decisions/tranches-derivees-lecteur-691.md`
- **Build `pivot_data/scrutins.json` before any pivot pass, and merge it additively.**
  Resolving a ballot's `legislature` is a corpus-wide join, never per-profile.
  → `docs/decisions/normalisation-votes.md`
- **Build `pivot_data/amendements/<legislature>.json` after the pivot pass, once, and
  merge it additively** — with `build_amendements_index_pivot.py`, not
  `build_amendements_index.py` (the raw AN index). `amendement_id` is `an:<uid AN>` and
  the legislature is read **inside** the uid, never derived from the date. Co-signatures
  live in a companion file and are **never deleted**: no consumer reads them, a
  co-signature network is analysis material (#324).
  → `docs/decisions/normalisation-amendements.md`
- **A `texte_vise` is the AN document's uid, never its label (#639).** Each index file
  carries an optional `textes` table (`texte_vise` → `{dossier_id, titre}`), filled
  uid-to-uid from `document.dossierRef` — never by matching a label, not even an exact
  one. A texte with no resolved dossier has **no entry**, and the count is printed.
  **The published index does not heal on its own (#696)**: the additive merge lets a
  populated label win, so the remedy is the named backfill
  `amendements_index.backfill_texte_vise`, run between the merge and `resoudre_textes`,
  reading the sourced uid from `raw_data/amendements_an_figes/<legislature>/`. Its
  criterion is the AN uid **grammar** (`textes_vises_figes.est_uid_texte`), and it is
  wired on **both** call paths: CI never goes through `build_amendements_index_pivot.py`.
  → `docs/decisions/dossier-des-amendements-639.md`,
  `docs/decisions/report-texte-vise-source-696.md`
- **Both shared indexes must be in the workflow's `git add`** — and since #715 so must
  `raw_data/correspondance_acteurs_an.json`, which the run now extends. They are the only
  cross-file dependencies inside `pivot_data/`; an uncommitted index leaves every mapping
  pointing at nothing, silently, and an uncommitted correspondence table rewrites its
  derived entries every run, so the slug freeze it exists for never happens.
- **Individual profiles are written compact, everything else `indent=2`** (`src/json_io.py`).
  Never read a profile line by line — the format carries no meaning.
  → `docs/decisions/profils-json-compact.md`
- **A tool that walks the corpus reads it by projection, and never keeps a document
  (#628).** 623 Mo of JSON on disk is ~2,6 Gio of Python objects (measured inflation:
  × 4,2), and the machine has 4 Gio free with the swap full — an accumulating loop is
  `exit 137`, not a slowdown. Read one profile, reduce it to the blocks your measures
  actually open (declare them in a whitelist), release it. **A ceiling that is not in a
  test is a ceiling nobody re-checks**: measure `ru_maxrss` in a subprocess over fixtures
  and derive the ceiling from the on-disk weight of the blocks you must not keep — never
  from what you observed. Three accumulations remain, named and measured in the decision.
  → `docs/decisions/audit-599-projection-blocs-lus-628.md`
- **Read raw profiles through `src/profil_brut.py`, never `json.load` directly (#580)** —
  a raw profile is a socle plus one amendment slice per legislature, and a broken
  partition must raise `PartitionIllisible`, never return an empty list.
  → `docs/decisions/partition-profils-legislature-580.md`
- **The biggest versioned file is a watched guard-rail with a written course of action
  (#580).** `src/garde_fou_blobs.py` is **§7 of `check_quality_gate.py`**: warn at
  50 MiB, **fail the commit at 80 MiB**. Neither "raise the threshold" nor "delete data"
  is an available remedy.
  → `docs/decisions/partition-profils-legislature-580.md#garde-fou-blob-580`
- **Additive merge (`merge_profile.py`): regeneration never removes collected data.**
  `votes`/`mandats`/`interventions` additive, old entry wins; `amendements`/
  `textes_portes` new entry wins, keyed on `amendement_id` / `dossier_id`, or on the
  `amendement_non_resolu` record — keying on the mapping alone collapses every unresolved
  entry into one. Scalars take the new value only if populated, and **never regress to
  `null`**.
  → `docs/decisions/collecte-vide-necrase-jamais.md`
- **The additive merge protects BOTH stages, and a removal must be applied to both
  (#729, #730).** `merge_pivot_profile` is additive exactly as the raw merge is: the
  previously published entry wins. So a correction that **adds** a field travels through a
  named backfill at the raw stage, but a correction that **removes** an entry has to run
  on `raw_data/profiles/` **and** `pivot_data/profiles/`, or it lands nowhere. Measured on
  run `33872886135`: after purging 185 duplicates from the raw profiles,
  `alexandra-martin` carried **54 mandates raw and 65 in the pivot**, and the loss check
  blocked nothing because nothing had been lost. At the pivot stage the actor ref no
  longer comes from the profile — it is not there — but from the slug ↔ AN actor table
  (#525). `purge_mandats_dupliques.py` and `reprise_mandats_gouvernementaux.py` both take
  `--profiles-dir`.
  → `docs/decisions/purge-doublons-herites-729.md`
- **A removal recomposes the DERIVED fields in the same breath, or the committed corpus
  publishes a derivation of entries it no longer holds (#839).** §4 says a derived field is
  recomputed after every step that moves it; a removal moves two at once —
  `tags_thematiques`, which derives entirely from `interventions[]` (#710), and
  `meta.licence_donnees`, recomposed from `sources[]` **and** intervention URLs (#530).
  Waiting for the next run leaves the layer `web/` reads incoherent for an hour or a day:
  `marine-le-pen` would publish 470 tags drawn from 246 entries that had left. Recomposed
  in the purge, she publishes **152** — exactly what her blank collection had returned that
  morning, which is what verified the cleanup by a second path.
  → `docs/decisions/nettoyage-sediment-839.md`
- **A field added to the schema never reaches an already-collected entry on its own —
  and the fix is a named backfill, never a looser merge (#492, #639, #641, #696, #710,
  #718, #980).** On a list, "old entry wins" and the key does not contain the new field, so the
  regenerated entry is discarded every run. On a scalar, "never regress to `null`"
  restores the very value the publication filter refuses — so **a publication filter runs
  on the COMPOSED block, after the merge, never on what the normaliser produced**. A
  backfill is strictly monotone: it fills only what is absent, it names its fields, and
  **it never touches the merge key** — widening the key to carry the new field is #668's
  defect. Each occurrence passed the whole suite: the test that was missing covered the
  **transition**, not the steps. #710 breaks one property of the family — it **removes** a
  value instead of filling one, so the loss is declared with `allow_declared_losses`.
  → `docs/decisions/qualification-perdue-a-la-fusion-639.md`,
  `docs/decisions/filtre-publication-apres-fusion-641.md`,
  `docs/decisions/creneau-de-seance-nest-pas-un-sujet-710.md`,
  `docs/decisions/categorie-source-des-mandats-718.md`,
  `docs/decisions/sujet-europeen-sans-boutons-a-la-fusion-980.md`
- **A merge key written `a or b` changes identity the day `a` fills in (#668).** #540 was
  a *sticky* key absorbing distinct entries; this is its mirror — the same dossier keyed
  on the fallback before the run and on `source_url` after, published twice (940 entries
  for 472 collected dossiers, 468 duplicates, 22 profiles, live). **An identifier, never a
  URL** (`dossier_id`, the raw stage's own `dossiers_legislatifs[].id`), and the residual
  `or` is neutralised by a **reprise**, not by the key: `clean_stale_textes_portes` drops
  an entry with no identifier only when an identified twin carries the same fallback.
  Dropping the `or` outright would collapse un-identified entries onto one `None` key
  (#432). **Before adding an `a or b` key, measure how much of the published corpus sits
  on each branch** — and a reprise nobody calls cleans nothing: this one was dead code for
  a whole remediation.
- **A fallback key containing a title is hostage to that title (#901).** European
  `textes_portes` have no `dossier_id`, so they all sat on the `(titre, date_min,
  legislature)` fallback; #938 cleaned the titles and 311 texts were published twice
  (Philippot 502 for 252). A European text is now keyed on its **`doceo` document**, read
  from `source_url` **without its scheme** (625 `http://`, 56 `https://`). **Not on
  `reference_dossier`**: it names a procedure, and several texts live in one — an opinion
  and the rapporteur's dossier share it. **When a change rewrites a field that sits in a
  fallback key, count the entries on that fallback first**: every one of them will come
  back as new.
  → `docs/decisions/doublons-textes-europeens-cle-doceo-901.md`
  → `docs/decisions/cle-fusion-textes-portes-668.md`
- **An empty collection never overwrites a non-empty one (#465)** — per field, not per
  profile, even under `--no-merge`. Lifted only by `--autoriser-collecte-vide`, and the
  preservation is always printed. "Zero observed" is not "collection failed" (§2 rule 5).
  → `docs/decisions/collecte-vide-necrase-jamais.md`
