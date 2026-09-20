<!-- Extrait d'`AGENTS.md` par #737. Ces règles ne changent pas de nature en
changeant de fichier : elles restent des instructions, et un renvoi
« AGENTS.md §3f » continue de les désigner — `AGENTS.md` en garde la ligne
d'index. Ce qui change, c'est qu'un lot qui ne touche pas ce domaine n'a plus à
les charger, ni à les faire grossir. -->

# §3f — Portail qualité

### 3f. Quality gate

- **Hard fail**: IncompleteRead over threshold, invalid or missing groupe/gouvernement
  file, broken structure (#212), §4's orphan `succede_a.fichier` (#700), §4b's unmapped
  published AN group sheet (#686), §5b's
  unmapped published slug (#525), §7's 80 MiB blob (#580). **Soft**: low interventions, low coverage, network signals, partial identifier
  coverage in `amendements[]` (§3c), index freshness (§3d), couverture ministérielle,
  empty `textes[]` (§5, mirroring groupes §4).
- **Partial `uid` coverage is soft on purpose** — mixed profiles were expected during the
  remediation window, and failing the gate would have blocked the very runs meant to fix
  them (#447, cause #450). Two versions of one amendment cohabiting means the entry is
  counted twice and the published denominators are wrong.
  → `docs/decisions/cache-amendements-existence-nest-pas-conformite.md`
- **The `uid` measurement follows the amendments, not the record**: it covers every
  profile that *publishes* `amendements[]`, whatever its `chambre`. The "AN candidates"
  counters and the "empty everywhere" signal keep the narrower population, the one
  amendments are *expected* from. **Name the population of every figure.**
  → `docs/decisions/cache-amendements-existence-nest-pas-conformite.md`
- **Frozen legislatures are never re-fetched** — 14/15/16 are closed dossiers, their index
  is committed under `raw_data/amendements_an_figes/`. §3d distinguishes "never built"
  from "present but stale beyond N days" from "frozen".
  → `docs/decisions/amendements-legislatures-figees.md`
