<!-- Extrait d'`AGENTS.md` par #737. Ces règles ne changent pas de nature en
changeant de fichier : elles restent des instructions, et un renvoi
« AGENTS.md §3c » continue de les désigner — `AGENTS.md` en garde la ligne
d'index. Ce qui change, c'est qu'un lot qui ne touche pas ce domaine n'a plus à
les charger, ni à les faire grossir. -->

# §3c — Les quatre gardes d'avant-commit

### 3c. The four pre-commit guards

`merge-and-pivot` runs all four before the commit, each in a separate process. Each
tolerance is **partitioned** — no input disarms another's check.

- **Loss check (#460, extended by #470)**: `audit_diff_profils.py --ref HEAD` over all of
  `pivot_data/`. Three findings abort the commit — a file that **disappeared**, a **drop
  on a stable list**, a **watched scalar going from populated to `null`**; drops on
  `amendements`/`sources`, index counts and scalar value changes are reported only. A run
  may legitimately lose entries — declare it with `allow_declared_losses`, never by
  removing the check. **The published aggregates are watched scalars, not stable lists
  (#649)** — `amendements_agreges` and `comptages.par_statut` block on disappearing or
  going `null`, never on their value falling, and `0` is a measurement while `null` is
  not. **There is no ratio threshold, and adding one is settled**: the *correct* drop of
  `3c8e1f0c` (× 0,03 to × 0,21) is larger than the *defective* one of `a125e9e` (× 0,00
  to × 0,64) on every fiche, so no threshold separates them.
  **A count does not see a swap (#823)**: an entry replaced by another leaves the total
  unchanged. Three fields therefore declare `listes_nommees` — `tags_thematiques` on
  profiles, `tags_thematiques_agreges` on groupes and partis — whose relevé keeps the
  **values**, so vanished entries are **named**, even at equal count and even when the
  count rises. Non-blocking on purpose: a derived field recomputed every run legitimately
  swaps entries; what this adds is an **explanation**, not a second lock. Not generalised:
  5 911 distinct values over 53 183 entries is affordable, millions of `amendements` keys
  are not.
  → `docs/decisions/controle-de-perte-avant-commit.md`,
  `docs/decisions/perimetre-controle-perte.md`,
  `docs/decisions/agregats-publies-controle-perte-649.md`,
  `docs/decisions/controle-perte-nomme-les-echanges-823.md`
- **Referential integrity (#485)**: `audit_integrite_referentielle.py`. Every published
  key resolves in the index it points at, or the commit aborts naming file and key — an
  orphan reference is a vote published with no object, on a groupe a false denominator
  (§2.7). A `null` key **with** its `*_non_resolu` record never blocks. Index entries
  nobody references are non-blocking. **`allow_declared_losses` does not disarm it**, and
  it must never be merged with `allow_broken_references`.
  → `docs/decisions/integrite-referentielle-pivot.md`
- **Collected must equal published (#511)**: `audit_collecte_non_publiee.py`, run
  **after both `--pivot-only` passes** — placement is half the control; run between them,
  every roster member would be a phantom gap. Threshold **0**; a pivot with no raw is
  non-blocking. Tolerance `allow_unpublished_profiles`. `generate_roster_candidats.py`
  refuses to write on a failed fetch, on a configured group returning 0 members, or on an
  empty roster.
  → `docs/decisions/collecte-non-publiee.md`
- **Each published list must carry what collection returned (#545)**:
  `audit_collecte_vs_publie.py`. #511 reasons about profiles, this one about the
  **contents of their lists**. Each published list declares in `RELATIONS` the raw **paths
  whose lengths it sums** — a named source, never a tolerated margin, which keeps the
  threshold at **0** everywhere. Blocking: a deficit, or an unreadable profile. Reported:
  a surplus, and a raw list with no declared relation. Tolerance
  `allow_publication_gaps`.
  **A sum of lengths assumes every collected entry is a distinct entry, and a source
  may deny it (#888).** The European portal publishes the same membership **twice** —
  one classified, one not — and `dedupliquer_appartenances` publishes one (#879); the
  raw keeps both, because the raw says what the source returned. A relation may
  therefore declare a **named reduction** beside its sources: the normalisation's own
  function, **replayed** on the raw by this guard, never reimplemented — a control that
  rewrote the criterion would drift the day the criterion moves. The threshold stays
  **0**: an entry that is nobody's duplicate is still a deficit, and two entries the
  source *both* classifies are never reduced (§2 rule 2). A reduction is added only
  once it is **measured**; without that it is the unattributed margin #545 refuses.
  → `docs/decisions/collecte-vs-publie-545.md`,
  `docs/decisions/reduction-nommee-collecte-vs-publie-888.md`
- **A progress file is not a profile — and `Path.glob` disagrees (#518, third incident).**
  `Path.glob("*.json")` **returns dotfiles**, unlike the `glob` module: every inventory of
  `raw_data/profiles/` skips `name.startswith(".")`, safe by construction since no slug
  starts with a dot. Cause fixed too: **`--no-checkpoint` on every `--pivot-only` pass**.
  → `docs/decisions/point-de-sauvegarde-dans-les-profils-518.md`
