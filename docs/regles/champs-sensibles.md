<!-- Extrait d'`AGENTS.md` par #737. Ces règles ne changent pas de nature en
changeant de fichier : elles restent des instructions, et un renvoi
« AGENTS.md §5 » continue de les désigner — `AGENTS.md` en garde la ligne
d'index. Ce qui change, c'est qu'un lot qui ne touche pas ce domaine n'a plus à
les charger, ni à les faire grossir. -->

# §5 — Champs institutionnels sensibles

## 5. Sensitive institutional fields (validation constraints)

- `mandats[].position_dans_hemicycle`: requires `source_url` (rule 6).
- `mandats[].suspendu_pour_fonction_gouvernementale`: never confuse with completed mandate.
- `votes[].type_vote == "motion_censure"` requires `texte_lie_id` **or a declared `texte_lie_non_resolu.motif`** (#639); 49.3 → `sort = "adopte_sans_vote_49_3"`, no position (rule 4).
  A censure motion is a **procedural fact**, never a position on the text — and its link is not
  sourceable: `objet.referenceLegislative` and `demandeur.referenceLegislative` are null on **0 of
  18 311** raw AN scrutins (legs 14-17), and an article 49-2 motion has no text to link at all.
  Hence the repo's own `*_non_resolu` pattern — null key **plus** the declaration, never an invented
  key and never silence. A mute motion is still a schema error.
- **`type_scrutin` and `type_vote` come from `typeVote.codeTypeVote`, one source field, no inference
  (#639).** `SPO`→`public_ordinaire`, `SPS`→`solennel`, `SAT`→`tribune`, `MOC`→`motion_censure`
  (+`vote_texte`/`motion_censure` on `type_vote`). An unknown or absent code stays `null` — never
  filed under `SPO`, which is 97,5 % of published scrutins (rule 5). `SSG` (Congress) is absent from the table
  on purpose: those scrutins are dropped upstream on their uid. `vote_texte` stays **coarse** — `SPO`
  covers article, amendment and whole-text ballots alike, so it does NOT constitute the "votes on the
  whole text" universe the published methodology claims.
- **A scrutins cache that carries no qualification is refused, not re-read (#639)** — disk cache **and**
  committed frozen index (`raw_data/scrutins_an_figes/`), whose three legislatures now carry it
  (rebuilt 31/08/2026: 1 354 / 4 417 / 4 105 scrutins, 4 / 5 / 34 censure motions). Same rule as the amendments
  cache: existence is not conformity. Accepting a stale one would have published 43 of the 66 censure motions as
  `vote_texte`. **Carrying it to the index is a third thing**: the raw vote acquires it only through
  `backfill_vote_qualification` (#639, above).
  → `docs/decisions/qualification-scrutins-et-cle-dossier-639.md`
- `votes[].numero_scrutin` restarts at 1 in each legislature: never a key on its own.
  Dedupe by AN `uid` **at index level** (`raw_data/scrutins_an_figes/`, where the AN
  `uid` exists); key group cohesion by `(legislature, numero)` — see
  `docs/decisions/votes-multi-legislature.md`. A profile's `votes[]` carries no
  `uid`: its key is `(legislature, numero_scrutin)`, and 22,5 % of collected votes have no
  `legislature` at all. Resolve it with `src/scrutins_legislature.py` — labelled-twin join
  first, legislature calendar second, loud failure third; never a default (rule 5). Audit
  the corpus with `src/audit_legislature_votes.py` before relying on the key
  (`docs/decisions/resolution-legislature-votes.md`).
- `amendements[].sort == "irrecevable"` requires `base_juridique_irrecevabilite` (`"art. 40"` or `"art. 45"`).
  Since `#431` both fields live in the shared index: the invariant followed them, into
  `validate_amendements_index()` — checked once per amendment, not once per signatory.
  What `validate_profil()` can no longer check alone is that a referenced `amendement_id`
  exists: it does so **only if** `amendements_index=` is passed, and skips it otherwise —
  never declares it valid by default.
- `amendements[].type_deposant`: never aggregate adoption rates across depositor types (rule, Section 6).
- Amendements cache (`.cache/amendements_an/<leg>/`): **a directory that exists is not
  evidence of what it holds.** Presence checks must also check the key format — a frozen
  cache written before the `uid` correction is skipped by `build_amendements_index.py` and
  refused by `_read_cached_amendements_acteur` at once, losing the whole legislature in
  silence. And the shard directory is published by a single `os.replace` from a temp dir,
  never filled in place: a half-written directory reads as "this member has no amendments"
  instead of "index unavailable". That atomicity is what makes the single-shard format
  check legitimate — do not fill in place.
  See `docs/decisions/cache-amendements-existence-nest-pas-conformite.md`.
- **A disk cache prevents a re-download, never a re-parse.** Any shared index read
  once per candidate must be memoised in-process — third occurrence of the same
  cost at the same spot (#392 amendements, #403 scrutins, #467 AN acteurs/organes:
  2 255 re-reads of one index for 24 members, 59 % of wall time). Key the memo on the
  index **path**, never on a logical name: tests patch the cache dir per case, and a
  global memo leaks one test's index into the next (the trap that reverted #377).
  See `docs/decisions/budget-execution-pleine-echelle-467.md`.
- An amendment with no AN `uid` gets **no invented key**: `amendement_id: null` plus its full
  record under `amendement_non_resolu`. That is the normal shape for European Parliament
  amendments, which ParlTrack ships without an AN uid.
- **Never re-materialise the flat form.** `joindre()` is a generator and `get()` returns the
  shared object itself, never a copy — expanding index × mapping cost a ~21 × factor and an
  OOM in `#377`. Locked by `tests/test_amendements_index.py`.
Edge-case history: the amendments and votes entries of `docs/technical_decisions.md`
(the index is chronological, newest first).
