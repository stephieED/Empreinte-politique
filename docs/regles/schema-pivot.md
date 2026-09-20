<!-- Extrait d'`AGENTS.md` par #737. Ces règles ne changent pas de nature en
changeant de fichier : elles restent des instructions, et un renvoi
« AGENTS.md §4 » continue de les désigner — `AGENTS.md` en garde la ligne
d'index. Ce qui change, c'est qu'un lot qui ne touche pas ce domaine n'a plus à
les charger, ni à les faire grossir. -->

# §4 — Schéma pivot v1 (`src/schema_pivot.py`)

## 4. Pivot schema v1 (`src/schema_pivot.py`)

| Key | Content |
|---|---|
| `id` | The profile's **slug** — its filename, **no provenance prefix** (#487). `nosdeputes:`/`nossenateurs:` derived from whichever chamber answered the collection, so it *changed value* on an unchanged career (two profiles flipped, in opposite directions, between `25f7bc7` and `01ffa7f`). Provenance stays where it is true: `sources[].type`, `identite.source_url`, `meta.provenance`. Standalone tools with no slug (`mep_profile.py --ep-id`) keep an explicit source id — better that than a slug invented from a collected name. See `docs/decisions/id-pivot-sans-prefixe.md`. |
| `nom`, `chambres`, `chambre`, `parti`, `groupe` | `chambres` (#493) is the **derived list** of chambers the person sat in, values from `KNOWN_CHAMBRES`, ordered by `ORDRE_CHAMBRES` (`AN`, `Senat`, `PE`, `mairie`). `chambre` is `chambres[0]` — never collected, never able to contradict it (`validate_profil` enforces it). Both come from `schema_pivot.deriver_chambres()`, the single factory. See `docs/decisions/chambres-profil-derivees.md` |
| `identite` | Nullable bio block. **`civilite` and the two INSEE PCS levels come from AMO30 and are copied, never inferred (#659)** — `civilite` from `etatCivil.ident.civ` (3 117/3 117 fiches: M. 2 106, Mme 1 011), **never derived from a first name**; `famille_socioprofessionnelle`/`categorie_socioprofessionnelle` from `profession.socProcINSEE` (2 177/3 117, both levels always filled or absent together). Publishing them is legitimate **because the source classifies, not us**: a socio-professional categorisation built by this repo would be an editorial act (§2 rule 1). `null` on the 940 fiches the source does not classify — and **« not classified » is not the family « Sans profession déclarée »** (85 fiches), which is a value of the nomenclature; conflating them is #556's exact contresens. Labels are published **verbatim**, typographic variants included; grouping belongs to whoever aggregates, purely typographic, never semantic. `profession` stays free text (#641). The three keys are optional, like `identifiants` and `provenance_champs`. See `docs/decisions/civilite-et-pcs-insee-659.md` |
| `sources[]` | `{type, url, synchro_le}` |
| `mandats[]` | Elections, committees... + sensitive fields (Section 5). `mandats[].chambre` (#492) is written **only on `mandat_electif`**: `AN`/`Senat`/`PE`/`null`, meaning *the chamber whose dataset returned this mandate*, stamped at collection. Never derived from `source_url` (0 of 214 AN/Senate elective mandates carry one) nor from the profile's `chambre` (additive merge accumulates mandates from both chambers in one profile). `null` + one aggregated warning per profile, never a default. See `docs/decisions/chambre-par-mandat-electif.md`. **A profile publishes ALL its elective mandates (#640)**, one per seat, grouped on AMO30's `(legislature, dateDebut)` — never on the legislature alone, which would weld together two terms separated by an annulled election. `identite.nb_mandats` counts AMO30 *records*, the list counts *seats*: the two are no longer meant to be equal. See `docs/decisions/mandats-electifs-liste-complete-640.md`. **`categorie_source` (#718) names the referential that ESTABLISHED the category** — `an` (AMO30 `codeType`, via `_TYPE_ORGANE_TO_CATEGORIE`) or `europarl`, `KNOWN_CATEGORIE_SOURCES`. **Optional key, and its absence is a meaning**: nobody established it. There is **no `heritee` value** — that would be an accusation the corpus cannot support (#486: 29 of the 511 published `mandat_electif` are entries the source no longer serves), and `None` is refused too because it states an absence as a finding (§2 rule 5, the `interventions[].collecte` arbitration of #657). Crosses the additive merge through `backfill_mandat_categorie_source`, wired at **both** stages — raw and pivot: wiring only the raw one lets the field reach the raw profile and never the layer `web/` reads. Simulated on 468 profiles: 640 of 39 449 categorical mandates unstamped (1,6 %), 467 of 11 775 `commission` (4,0 %), 33 profiles' denominator falling. It marks, it never deletes and never relabels — #729 and #730 carry the wrong categories themselves. See `docs/decisions/categorie-source-des-mandats-718.md`. **`sigle_organe` and `type_organe_source` (#863)** say what the SOURCE publishes about the organ, where `categorie` says how the pivot files it: the acronym as the portal writes it (`GUE/NGL`, `S&D`, `Verts/ALE`) and its classification translated into the closed `KNOWN_TYPES_ORGANE_SOURCE` — which is how the interface recognises a European political group **without reading its label**. Measured: 63 group mandates, **61 with an acronym**. **An organisation id is not an acronym**: when the portal resolves no name (`stephane-le-foll`, `"2953"`), `sigle_organe` is `null` and `sigle_organe_non_resolu` carries the reason (§2 rule 5). An unclassified membership (`AUTRE`) keeps **no** `type_organe_source` — the absence says the source did not classify it. The category itself does **not** move: `_mandat_key` contains it, so re-filing an entry would ADD one instead of correcting it (#668's defect). Crosses the additive merge through `backfill_mandat_organe_source`, wired at **both** stages. See `docs/decisions/sigle-groupe-europeen-863.md` |
| `votes[]` | **Mapping only** (`#432`): `{scrutin_id, position}`. The ballot's metadata (date, text, sort, type_vote…) lives once in `pivot_data/scrutins.json`, not once per voter — 179,8 → 17,9 Mo + 8,1 Mo of shared index, −85,5 %. AN legislatures 14-17 aggregated (`#403`) |
| `textes_portes[]` | Author/reporter/co-reporter + procedural stage. `dossier_id` (#639) is the AN legislative-dossier key (`DLR5L15N37607`), copied verbatim from the raw `dossiers_legislatifs[].id` (472/472) — **same name as a government sheet's `textes[].dossier_id`**, deliberately: two names for one identifier send every cross-reference back to the label. Never rebuilt from a title. See `docs/decisions/qualification-scrutins-et-cle-dossier-639.md`. **`nature_texte` (#689) is the sourced fact and `role` derives from it** — `projet_de_loi` / `proposition_de_loi` / `proposition_de_resolution` / `null`, read from the uid prefix of the deposited document (`PRJL`/`PION`/`PNRE`) by `gouvernement_textes.nature_texte_depose`, the same function the government sheets read (#435/#400). **Never from a libellé**: the XVth-legislature dossiers are titled « Bioéthique », « CETA », « Coopération avec le Luxembourg », and a starts-with-*Projet de loi* filter misses 283 of 304. `auteur` was **split** — a projet de loi carried on behalf of the government is not a personal act (316 of 472 published entries, 282 of `edouard-philippe`'s 283) — into `initiateur_projet_de_loi` / `auteur_proposition_de_loi` / `auteur_proposition_de_resolution`; `auteur` survives, narrowed to the 5 initiator entries whose nature the source does not establish. `validate_profil()` **refuses any contradiction** between the two, exactly as `chambre` cannot contradict `chambres[0]`. The role is derived, never merged; the nature crosses the additive merge through `backfill_dossier_nature` — without it the old raw entry wins and the field never lands (#639, #492, same hole). Gate §5c counts what is still unqualified. See `docs/decisions/qualification-textes-portes-689.md`. **`sort` (#743) is the dossier's OUTCOME, and it is never derived from `stade_procedural`** — `KNOWN_SORTS_TEXTE_PORTE`, the same nine values as a government sheet's `textes[].statut` because it is the same source read by the same function (`gouvernement_textes._determine_statut` on `statutConclusion.fam_code`, **not** `codeActe` — spike #207). The stage is a progression whose missing next rung is a fact of the source at its date: « discussed and not adopted » never becomes « rejected ». A `null` sort always carries `sort_non_resolu.motif` (`sans_decision` — a legitimate state, nothing to fix — / `fam_code_inconnu` / `archives_indisponibles` / `source_sans_sort`, the ParlTrack dossier dump carrying no outcome at all), and the validator refuses both together **and neither** (#747): it used to arm only on a non-null motif, so `sort: null` with no motif — an absence with no declared cause, §2 rule 5 — passed for a month on 49 entries, and hid a second live producer. **A profile whose own collection declares this list discarded (`meta.collecte_ecartee`) must not carry it**: the additive merge preserves such residue indefinitely, because the new list is empty and not incomplete, so no named backfill has a key to land on. `sort_49_3` is deliberately not republished: `adopte_49_3` already carries it. Crosses the raw additive merge through `backfill_sort_texte_porte`; **the pivot needs no backfill**, because `merge_dossier_records` lets the NEW entry win where `merge_lists_by_key` lets the old one — a general rule does not excuse checking that it applies here. See `docs/decisions/sort-des-textes-portes-743.md` |
| `amendements[]` | **Mapping only** (`#431`): `{amendement_id, role_signataire}`. Outcome, inadmissibility, date, `co_signataires`… live once in `pivot_data/amendements/<legislature>.json`, not once per signatory — 1 342,4 → 73,8 Mo of mapping + 130,1 Mo of shared index, −84,8 %. `role_signataire` is the only member-specific field |
| `interventions[]` | Speeches, questions (`type_detail`). An entry carrying `collecte: "theme_seul"` (#657) was collected **without its verbatim**: its heavy fields are **absent, never `null`** — a `"texte": null` would read as a fact about the person, where the fact is about the run (§2 rule 5). `collecte` is a closed value (`KNOWN_COLLECTES_INTERVENTION`); its **absence** is the full form. See `docs/decisions/collecte-interventions-reduite-au-theme-657.md` |
| `tags_thematiques[]` | **Derived**, never merged (#710) — `schema_pivot.deriver_tags_thematiques`, recomputed after the pivot merge like `chambres` and `licence_donnees`; the old union made every published tag immortal. Its values are the lowercased `interventions[].theme_officiel`, `mots_cles` as fallback (#529): **5 669 distinct labels on the 481 published profiles**, not a closed vocabulary — `STABLE_THEMES` and `classify_keywords()` this row used to name **do not exist in the repo**. §2 rule 8 still governs what they are: reading aids, never declared positions. |
| `mandats_anterieurs` | **Candidats déclarés seulement (#860).** Les mandats nationaux antérieurs au **19/06/2002** — début des données de l'Assemblée, que le corpus ne peut pas porter —, reposés depuis la table relue `raw_data/mandats_anterieurs.json` **à chaque écriture du pivot, jamais fusionnés**. Une ligne : `institution` (`KNOWN_INSTITUTIONS_ANTERIEURES` : `assemblee_nationale`, `gouvernement` — **pas** le Sénat, #528), `libelle`, `legislature` (député), `debut`, `fin`, `source_url` **primaire** (Sycomore, décret au JO), `source_fin_url` facultatif. Une `fin` nulle porte **toujours** `fin_non_resolue.motif`. **Relu ≠ non relu** : liste (vide = aucun) si le slug est dans la table, `null` + `mandats_anterieurs_non_resolu: {motif: "non_relu"}` sinon. Absent des profils de roster. See `docs/decisions/mandats-anterieurs-couverture-860.md` |
| `meta` | `schema_version`, `genere_le`, `licence_donnees`, `warnings[]`, `avertissements[]` (#642), `provenance` (`candidat_declare`\|`roster_groupe`, see `docs/decisions/provenance-pivot.md`), `provenance_champs` (#603). **`provenance` says why the profile exists; `provenance_champs` says which source filled which field of `identite`, and when** — optional (absent from the 481 profiles published before the lot), `identite`-only, and an unknown origin is published `{"source": null, "synchro_le": null}`, never omitted. Derived after the merge like `chambres` and `licence_donnees`, never merged. Not to be confused with `couverture` either: that one says *why a business list is empty*, per list, not per field. See `docs/decisions/provenance-par-champ-603.md`. **`meta.avertissements[]` (#642) is the typed twin of `warnings[]`** — one `{message, destinataire}` entry per warning, same order, same strings, enforced by `valider_avertissements()`. `destinataire` is a closed two-value vocabulary (`lecteur`, `interne`, `DESTINATAIRES_AVERTISSEMENT`): the key is **mandatory**, `null` says « nobody declared it », the omission says nothing. There is no third « mixed » value — a warning addressing both is **written twice**. It is declared **at the site that writes it**, via `avertissements.avertissement(message, destinataire)`, never by a table keyed on the message prefix: `votes introuvables` covers a constat *and* a panne (#484 verbatim). Derived like `chambres` and `licence_donnees`, never merged; optional on the 481 profiles published before the lot, with a written retirement condition. See `docs/decisions/destinataire-avertissements-642.md` |

Conventions: French `snake_case`; missing = `null` (never `""` or `0`); closed values in
`frozenset KNOWN_*`, validated by `validate_profil()` — extend the frozenset, never bypass.

### 4a. Group fiches: every count is taken at one published date (#653)

**A group fiche describes a legislature, and none of the 7 published describes
the one in progress. No counter on it may mean "today".** Three did, and all
three measured the members' *later careers* instead of the group:
`effectif.actuel` equalled, exactly, the number of members holding an **open
elective mandate** (38/38, 85/85, 60/60 on `LR`, `REN`, `LFI` — re-elected in
2024, not group members in June 2024), and `nb_membres_actifs` counted their
**present-day** committee.

- **`date_reference` is published in the fiche** — `{date, origine}`, `origine`
  in `ORIGINES_DATE_REFERENCE`. **Derived, never guessed**: the latest
  `fin_dans_groupe` when every membership is closed (`cloture_legislature`,
  `2024-06-09` for the XVIᵉ), the generation date while one is still open
  (`generation`). A dated counter the reader cannot date is a bare counter
  (§2 rule 2).
- **The three counters are named for it**: `effectif.a_la_date_de_reference`,
  `mandats_agreges[].nb_membres_a_la_date_de_reference`,
  `membres[].present_a_la_date_de_reference`. The names are long on purpose —
  a short name that reads "today" is what produced the defect.
- **`periode.actif` is *not* rebased on it.** It describes the *period*, not a
  headcount at an instant; `false` on a closed legislature is exact.
- **Selecting the entry matters as much as the flag.** A duplicate
  `(categorie, label)` must be resolved to the mandate **open at the reference
  date** (`_select_mandat_a_la_date`) before `_select_mandat_entree_unique`'s
  rule applies: that one prefers the `actif` entry, i.e. a re-elected member's
  committee in the **next** legislature. 1 000 of `AN:LFI-16`'s 2 384 entries
  have several candidates; without the preference, its `affaires sociales`
  drops from 9 sitting members to 3.
- **A mandate with no `debut` is open at no date.** `_intervals_overlap` treats
  an absent bound as unbounded, which would make it cover every date (§2 rule 5).
- **`date_reference` is optional, never required.** The 2 frozen `groupe-Senat-*`
  fiches (#516) will not be regenerated and keep the old names; requiring the
  key would hard-fail the quality gate on already-published files. Readers must
  therefore accept both names — `audit_groupe_dataset.CHAMPS_EFFECTIF` does.

- **L'amplitude sur la période porte sa date, ou ne se publie pas (#702).**
  `effectif.min_historique`/`max_historique` sont des objets `{valeur, date}` — un
  minimum sans sa date est un nombre sans fait. Réévalués à chaque `debut_dans_groupe`
  et au **lendemain** de chaque `fin_dans_groupe` (borne de fin inclusive), sur la
  fenêtre `periode.debut` → `periode.fin` (`date_reference.date` en relais tant que la
  période est ouverte), **jamais au-delà**. **Seuil 0** : une seule entrée sans
  `debut_dans_groupe` laisse les deux à `null` avec son motif — ce membre n'est
  comptable à aucune date, et une borne inférieure publiée sous le nom « minimum » est
  un chiffre faux (§2 règle 5). Trois formes lues (`null`, entier nu hérité, objet), une
  seule produite. Le calcul vit dans `build_groupe_profile`, sur la même liste et la
  même fonction de présence que les compteurs de #653.
  **Depuis #809, `membres[]` porte `periodes[]`** : un départ suivi d'un retour n'est
  plus invisible, et `_appartenance_couvre` est exact par construction là où il lisait
  une enveloppe — 48 des 1 604 couples (acteur, groupe) ont plusieurs périodes, le plus
  long trou faisant 1 110 jours. Deux mandats séparés d'**un** jour sont recollés, au-delà
  c'est une absence : 67 trous d'un jour, **0** entre 2 et 30, 48 au-delà de 31, la
  distribution ne laisse aucune zone grise. L'enveloppe reste publiée et reste le repli
  des fiches d'avant ce lot ; la clé n'apparaît que si la source l'a donnée. C'est la
  **seule** entrée dont `validate_profil_groupe` vérifie le contenu, parce que des
  périodes qui contrediraient leurs bornes ne se rattraperaient nulle part en aval.
  → `docs/decisions/periodes-appartenance-809.md`
### 4b. One sheet per group AND per legislature — and `succede_a` is ours, not the AN's (#700)

`groupes_reels.json` carries **12 entries** since #700 (5 AN-XVIe, 5 AN-XVIIe,
2 frozen Senate ones): the filename has said so from the start
(`groupe-AN-REN-16.json`). Two things follow, and they are not of the same kind.

- **`correspondance_sigles_an` produces no sheet.** The five XVIIe groups sat in
  that table, measured and reviewed, since 26/08/2026 — under a note saying « the
  publication is lot 1b », which was **#527**, a lot that switched the roster's
  *source* to AMO30 and published nothing. Only `groupes[]` decides what a run
  writes. A note pointing at a lot that did something else spares everyone from
  checking.
- **`groupe_id` always carries its legislature, and `succede_a` is a non-empty
  list (#815).** Seven ids of eighteen lacked the suffix — `AN:REN`, `AN:SOC`,
  `AN:RN`, `AN:LFI`, `AN:LR`, `AN:EPR`, `AN:DR` — a leftover from when
  `groupes_reels.json` described **one** legislature and the sigle was enough.
  A returning sigle makes the reference ambiguous: declaring `LR` for the XVᵉ
  turns `AN:LR` into two sheets. The list exists because a **merge** has two
  predecessors and a **split** is not a replacement — `AD` leaves `DR` on
  11/09/2024 while `DR` carries on. **The file holds two lists** (`groupes[]`,
  the only one that decides what a run writes, and
  `correspondance_sigles_an.groupes`); fixing one and not the other is
  invisible. The old shape is refused **by name** at both stages, never
  tolerated.
- **`succede_a` is an assertion of this repo, and the schema forbids it a
  `source_url`.** The Assembly opens and closes organs (`PO800508` closed
  09/06/2024, `PO845425` opened 18/07/2024); it never chains them. Exact mirror
  of `position_politique`, which *requires* one: here `etabli_par`
  (`relecture_humaine`, a one-value closed vocabulary) plus `verifie_le` say
  where it comes from, and the published proof is the predecessor's
  `sigles_an`/`organes_an`, verbatim. Optional, like #686 and #653. A succession
  that does not resolve is refused **twice**: in the table (after the loop — at
  entry-scan time the verdict would depend on file order) and at gate §4, hard,
  threshold 0, on a `fichier` naming no published document.
- **`groupe_id` is opaque, and it is no longer `<chambre>:<sigle>`** — `AN:EPR`
  and `AN:DR` carry no suffix, `AN:RN:17`/`AN:SOC:17`/`AN:LFI:17` do. Tenable
  only because nothing in the repo splits it; a test forbids a `split(":")` on
  it. **Before quoting a coverage figure, name the legislature**: the XVIIe
  sheets will carry 305 of 461 members (66,2 %), against 99,1 % on the XVIe,
  because 156 roster members had no slug. **#708 lifts that**: they now enter with a
  fabricated slug, and the coverage rises only once they are collected **and** their
  correspondence reviewed — gate §5b blocks publication until then.

→ `docs/decisions/fiches-groupe-17e-legislature-700.md`
