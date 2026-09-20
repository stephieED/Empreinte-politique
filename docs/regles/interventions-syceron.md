<!-- Extrait d'`AGENTS.md` par #737. Ces règles ne changent pas de nature en
changeant de fichier : elles restent des instructions, et un renvoi
« AGENTS.md §3e » continue de les désigner — `AGENTS.md` en garde la ligne
d'index. Ce qui change, c'est qu'un lot qui ne touche pas ce domaine n'a plus à
les charger, ni à les faire grossir. -->

# §3e — Interventions (Syceron)

### 3e. Interventions (Syceron)

- **Syceron publishes the speaker id BARE (#510)** — prefix it with `PA`, which is not an
  inference: the same `<paragraphe>` carries `id_acteur="PA<id>"`. When `id_acteur`
  **contradicts** the prefixing, the source itself refuses the attribution and so do we:
  keeping the first would fabricate a speech (§2 rule 2).
  → `docs/decisions/syceron-acteur-ref-nu-510.md`
- **Measure only on verbatim reductions of the archive.** The two invented fixtures are
  **deleted**, not deprecated — keeping them under test kept the cause armed. What
  separates a subject from a procedural heading is **structural**, not lexical (the
  point's `code_grammaire`); `sujet` is `None` otherwise (§2 rule 5), never a procedural
  title, which would then feed `tags_thematiques` (§2 rule 8).
  → `docs/decisions/syceron-archives-verifiees-parseur-510.md`
- **`TITRE_TEXTE_DISCUSSION` is not homogeneous, and a séance slot is not a subject
  (#710).** It titles the ORDER-OF-BUSINESS item, and the Assembly inscribes there a text
  as well as a recurring **slot** (« Questions au gouvernement »). The discriminant stays
  structural: an item under which the source files points of the **question grammar**
  (`QG_1_1`/`QOSD_1_1`/`QPM_1_1`) is a slot — the source itself publishes the subject one
  level down (`_creneaux_de_questions`, a pass that must run **before** the paragraph
  walk: those points are XML siblings coming after it). **Never a label list**: the source
  publishes several typographic variants of the same slot, and a lexical filter misses
  most of them (#672, #639). What the criterion does NOT settle is counted, not guessed:
  an item that is a séance moment with no finer grammar under it keeps its subject,
  because the source carries no structural mark for it. An absent or unknown
  `code_grammaire` never becomes procedural by default: the criterion is positive on both
  sides.
  → `docs/decisions/creneau-de-seance-nest-pas-un-sujet-710.md`
- **A cached Syceron index is a cached PARSE, and existence is not conformity (#719).**
  `.cache/syceron_an/<leg>/index_par_acteur` is the output of `parse_syceron`, not an
  archive set aside; its cache key says when, in which mode and over which archives it
  was written (#550), **never with which parser**. A field added to the parser therefore
  never reaches a restored index, and nothing said so — #505/#510 refuse an index built
  on an absent archive or resolving no actor, #550 one written during an outage, neither
  one written by a stale parser. `_syceron_index_qualifie` now reads an unqualified
  directory **as absent**: the test is on the **key**, never its value
  (`sujet_code_grammaire` is legitimately `None`); **one shard is read, the smallest**
  (one entry settles it, and #628 forbids loading a multi-MiB shard for that); the
  refusal is a `continue`, so a stale full index never masks a conforming reduced one
  (#657); and the verdict is memoised **by absolute path** (#377) and **forgotten on
  publication** — without that, the index just written would be refused and every actor
  would re-walk the archive. Retirement condition: the day the cache key carries a
  fingerprint of the **code**. Until then every new parser field must join
  `SYCERON_CHAMP_QUALIFICATION` or go unnoticed.
  → `docs/decisions/conformite-index-syceron-719.md`
- **An index that resolves zero actors is never cached nor returned silently.** #505's
  guard only covered "no readable file", and that gap is how #510 survived (§2.5).
  Unresolved ids are **counted, not warned** per entry; the tripwires are
  `forme_inattendue` and "not one indexed entry carries a subject", both at **0**.
  → `docs/decisions/syceron-actif-510.md`
- **Syceron is live and the NosDéputés fallback is gone (#510).** The flag is **removed**,
  not lowered — a defective mode behind a switch keeps the defect armed;
  `--activer-interventions-syceron` is still declared and **loudly refused**, because
  `unrecognized arguments` would read as "Syceron collection is off". **A source that
  replaces the primary one is what made #510 invisible.** An empty Syceron collection now
  stays empty and says so, under a label that is a **prefix** of the old one so published
  warnings stay recognisable.
  → `docs/decisions/syceron-actif-510.md`
- **The interventions index is sharded per actor**, published by one `os.replace` (patron
  #392/#403). Both flat legacy indexes are **deleted** on publication and never re-read.
  The per-legislature lock is **reentrant**, and the memo of built-but-unpublished indexes
  is keyed on the cache **path** (the #377 trap).
  → `docs/decisions/syceron-actif-510.md`
- **A group aggregate is a consumer nobody greps for (#657).** `--skip-interventions` was
  hard-wired into the roster job on the written ground that "no group aggregate consumes
  interventions". It was **false**: `tags_thematiques` derives entirely from
  `interventions[]`, and each group sheet's `tags_thematiques_agreges` from that — so
  every sheet's "thematic footprint" was **one person's**. The derivation crosses two
  stages, and nobody re-reads `normalize_profil` when deciding what an extraction job
  collects. **Before declaring a list unconsumed, grep the derivations, not the
  aggregates.** The roster now collects **theme only** (`--interventions-theme-seul`):
  debates without verbatim, official questions not at all (they carry no theme). **Two
  index forms, two directories** — the reduced run reads the full index and drops the
  heavy fields; the full run never reads the reduced one. A **declared candidate is never
  reduced**: additive merge keeps the *older* entry, so a reduced entry would freeze his
  full form forever.
  → `docs/decisions/collecte-interventions-reduite-au-theme-657.md`
- **An INTEGER `intervention_id` is NosDéputés-era sediment, and nothing else (#839).**
  Syceron renders `syceron_…`, official questions `question_…`, the European Parliament
  `europarl_…`: no live source renders an integer. #529 changed the source and therefore
  the merge key, and the additive merge kept both — so **492 of the 511 integer entries
  are the same speech published twice**, on 5 declared candidates. Removal is
  `src/purge_interventions_heritees.py`, prudent as #387 (an entry goes only when its
  Syceron twin is present in the same profile, same day, text contained or equal) and run
  **on both layers**, a raw-only removal never reaching the pivot (#729). The 19 without a
  twin stay published. Corollary for the witness protocol: **a blank collection runs in
  two passes**, the second with `--enrich-parltrack` — without it the whole European side
  is missing and the diff accuses the code of losing it.
  → `docs/decisions/sediment-nosdeputes-839.md`
- **`PA0` and NEGATIVE actor ids carry `id_mandat="-1"`: the source attaches the words to no
  mandate (#839).** Measured over 200 XVIe comptes rendus, 118 033 paragraphs: 1 834 `PA0`
  and 11 negative ids, **100 % of them with `id_mandat="-1"`**, and every `PA0` with an
  **empty `code_parole`** — those are the interjections thrown from the benches, not floor
  speeches. A negative id is an actor outside the AN referential, typically a senator
  speaking at the Congrès: the Assembly publishes the name and states there is no AN
  mandate behind it. **Never attribute either to a profile.** The name is published, but
  reading it as an attribution adds a link the source refuses — the same defect as #510's
  contradicted `id_acteur`. This is what settled the 19 inherited interventions without a
  Syceron twin: they leave.
  → `docs/decisions/residus-source-retiree-839.md`
- **What is not measured says so** — per-candidate cost and RSS of the sharded index are
  bounded by construction, not by measurement, and the #429 and #500 balances are
  un-remeasured. Naming them is the rule: §2.5 applies to our own work too.
  → `docs/decisions/syceron-actif-510.md`
