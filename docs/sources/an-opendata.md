# National Assembly Open Data (votes, amendments)

> **Status: live — the pipeline's single source.** External reference: it drifts
> with `data.assemblee-nationale.fr`, not with this repository's code. Re-check it
> when the provider moves a dataset, a URL pattern or a field — not when our code
> changes. Sibling: `docs/sources/nosdeputes/` (historical, no longer queried).

This project downloads two large datasets directly from the official National
Assembly Open Data catalog (<http://data.assemblee-nationale.fr>): votes
(roll-call records) and amendments. This page gathers practical references to
maintain/extend this code (`src/candidate_profile.py`) without re-exploring the
catalog every time.

## General URL pattern

```
https://data.assemblee-nationale.fr/static/openData/repository/{legislature}/loi/{dataset}/{file}.zip
```

- `{legislature}`: `13` to `17` (`17` is current).
- `{dataset}`: varies by data family and legislature (see tables below) - do
  not assume temporal stability.
- Catalog pages rendered in JS do not expose `.zip` links via naive HTML fetch.
  The "all X" subpages (for example amendments pages) include links in static
  HTML and are used as the reliable discovery path.

## Votes (roll-call records)

| Legislature | Dataset | File | Size (zip) | Packaging |
|---|---|---|---|---|
| 17 (ongoing) | `scrutins` | `Scrutins.json.zip` | ~26 MB | `json/` tree, one file per scrutin |
| 16 (archived) | `scrutins` | `Scrutins.json.zip` | ~10 MB | `json/` tree, one file per scrutin |
| 15 (archived) | `scrutins` | `Scrutins_XV.json.zip` | ~9 MB | `json/` tree, one file per scrutin |
| 14 (archived) | `scrutins` | `Scrutins_XIV.json.zip` | ~0.7 MB | **monolithic** `Scrutins_XIV.json` (`scrutins.scrutin[]`) |
| 13 | - | no equivalent dataset available | | |

All four are aggregated per profile (`AN_SCRUTINS_LEGISLATURES`); 14/15/16 are
closed and their index is committed under `raw_data/scrutins_an_figes/`.

Three `decompteNominatif` key schemes coexist (exhaustive survey, 2026-08-18) —
a reader accepting only the plural form silently drops legislature 14 in full:

| Positions | Where |
|---|---|
| `pours` / `contres` / `abstentions` / `nonVotants` | legislatures 15, 17, and 4 105 of the 4 106 scrutins of 16 |
| `pour` / `contre` + `abstentions` / `nonVotants` | all of legislature 14 |
| `pour` / `contre` / `abstention` / `nonVotant` | `VTCGR5L16V1` only (Congrès, 2024-03-04) |

Scrutin `uid` (e.g. `VTANR5L17V1000`) is unique across legislatures and is the
deduplication key; `numero` restarts at 1 in each legislature and never
identifies a scrutin on its own. Congrès scrutins (`VTCGR…` prefix) share the
AN number space and are excluded — see `AN_SCRUTIN_UID_PREFIXE`.

See `AN_SCRUTINS_ZIP_NAME` / `_parse_scrutins_zip` / `fetch_votes_officiels` in
`src/candidate_profile.py`, and
`docs/decisions/votes-multi-legislature.md`.

## Amendments

| Legislature | Dataset | File | Approx. size |
|---|---|---|---|
| 17 (ongoing, daily updates) | `amendements_div_legis` | `Amendements.json.zip` | ~283 MB |
| 16 (archived) | `amendements_div_legis` | `Amendements.json.zip` | ~363 MB |
| 15 (archived) | `amendements_legis` | `Amendements_XV.json.zip` | ~618 MB |
| 14 (archived) | `amendements_legis_XIV` | `Amendements_XIV.json.zip` | ~99 MB |
| 13 | - | no equivalent dataset (tested paths return 404) |

The ZIP contains one JSON per amendment (~123k files for legislature 17),
under `json/{dataset}/{text}/AMANR5L{legislature}...json` — except
legislature 14, published via a separate archives page (not the standard
openData path, see `docs/decisions/amendements-legislatures-figees.md`),
whose single JSON entry (`Amendements_XIV.json`) nests all amendments under
a different schema (`textesEtAmendements.texteleg[].amendements.amendement[]`,
see "Legacy schema (legislature 14)" below).
See `AN_AMENDEMENTS_PATH` / `fetch_amendements_officiels` in
`src/candidate_profile.py`.

### Key JSON fields (empirical observations on legislature 17)

- `amendement.signataires.auteur.acteurRef` (`PAxxxxx`): linked against
  `identite.url_an_ou_senat` in raw profiles (which already contains the AN ID)
  via `_extract_acteur_ref()`.
- `.signataires.auteur.typeAuteur`: `Depute`, `Gouvernement`, `Rapporteur`
  (`Commission` seen occasionally).
- `.cycleDeVie.etatDesTraitements.etat.libelle` and `.sousEtat.libelle`:
  non-trivial pair used by `_derive_amendement_sort()` and
  `_AMENDEMENT_SORT_MAP` in `candidate_profile.py`.
- `.texteLegislatifRef`: raw target code, not a human title.
- `.representations.representation.contenu.documentURI`: currently does not
  resolve to a stable public URL in tested cases.

### Legacy schema (legislature 14)

Measured on the legislature 14 archive (843 `texteleg`, 167,420 amendments
total). Root: `{"textesEtAmendements": {"texteleg": [...]}}` — `texteleg` is
a dict instead of a list when there is only one (same quirk as
`cosignataires.acteur` below). Per `texteleg`:

- `refTexteLegislatif`: shared by all its amendments (per-`texteleg`, not
  per-amendement like `.texteLegislatifRef` in the current schema).
- `amendements.amendement[]` (dict instead of list for a single amendment).

Per amendement (differences from the 15/16/17 schema only; `signataires` is
unchanged, see below):

- `identifiant.numero` / `numeroLong` (root, e.g. `"7 (Rect)"`) instead of
  `identification.numeroLong`.
- `dateDepot` (root, e.g. `"2014-02-14"`) instead of `cycleDeVie.dateDepot`.
- `etat` (string, e.g. `"Discuté"`) + `sort.sortEnSeance` (e.g. `"Tombé"`)
  instead of `cycleDeVie.etatDesTraitements.etat/sousEtat.libelle`. Unlike
  the current schema's `(etat, sousEtat)` pair (ambiguous depending on
  context, see `_AMENDEMENT_SORT_MAP`), `sortEnSeance` unambiguously carries
  the outcome — only a case-normalization table is needed
  (`_LEGACY_AMENDEMENT_SORT_EN_SEANCE_MAP` in `candidate_profile.py`);
  irrecevability (`etat` in `"Irrecevable"`/`"Irrecevable 40"`) reuses the
  exact same logic as `_derive_amendement_sort()`.
- `signataires.auteur.acteurRef` / `signataires.cosignataires.acteurRef`:
  identical to the current schema, `_extract_cosignataire_refs()` reused as
  is.

See `_parse_amendement_entry_legacy()` / `_derive_amendement_sort_legacy()`
in `candidate_profile.py` (issue #299); schema detection (root key
`"amendement"` vs `"textesEtAmendements"`) happens in `_parse_amendements_zip()`.

## Archive: "Schemas and legislative data documentation"

<http://data.assemblee-nationale.fr/static/openData/repository/SCHEMAS/Schemas.zip>
(MD5 `67a8dd5b74dea0cc688003b3400c879e`, dated 2016-11-25) contains Sphinx
HTML documentation for the Assembly data model. Useful context, but **outdated**
for current JSON payloads.

Still useful confirmations:

- Historical `typeAuteur` values match `_AMENDEMENT_TYPE_AUTEUR_MAP`.
- Historical `sortEnSeance` values confirm procedural constitutional
  inadmissibility distinctions.

## Actors / mandates / bodies (official identity + mandates)

Two datasets share the same JSON schema, at different scopes:

| Dataset | Path | Size | Scope |
|---|---|---|---|
| `AMO10` (**no longer used**, see below) | `.../17/amo/deputes_actifs_mandats_actifs_organes/AMO10_deputes_actifs_mandats_actifs_organes.json.zip` | ~4.9 MB, daily updates | Deputies with an active mandate in the current legislature only (~577 acteurs) |
| `AMO30` (`AN_ACTEURS_HISTORIQUE_ZIP_URL`, in use) | `.../17/amo/tous_acteurs_mandats_organes_xi_legislature/AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip` | ~13.6 MB, daily updates | All acteurs referenced since the 11th legislature, active or not (3117 acteurs) |

**« Acteur » ne veut pas dire « député », et la borne de 2002 ne vaut que pour les
députés (mesuré le 12/09/2026 sur l'archive en cache).** Deux confusions que le
nom du fichier et la page du portail entretiennent, et qui ont produit une phrase
publiée fausse sur 2 337 entrées de couverture
(`docs/decisions/borne-mandats-acteur-nest-pas-depute.md`) :

| La population | Acteurs |
| --- | ---: |
| ont siégé à l'Assemblée | **2 122** |
| **sénateurs, n'ayant jamais siégé à l'Assemblée** | **905** |
| fonction gouvernementale seulement | 90 |
| **total** | **3 117** |

| Type d'organe | Mandat le plus ancien |
| --- | --- |
| `GROUPESENAT` | **1980-10-02** |
| `SENAT` | 1998-10-01 |
| `COMSENAT`, `DELEGSENAT`, `HCJ`, `CJR` | 2001 |
| **`ASSEMBLEE`** | **2002-06-19** (ouverture de la XIIe) |

Le fichier porte donc **390 mandats sénatoriaux commencés avant le 19/06/2002**
(192 `SENAT`, 123 `COMSENAT`, 75 `GROUPESENAT`) — et **aucun** mandat de député.
La page du portail annonce « l'état civil des députés et anciens députés élus à
partir du début de la XIe législature en juin 1997» : cette couverture porte sur
**les personnes**, pas sur leurs mandats. Vérifié nommément — `segolene-royal`
(députée depuis 1988), `nicolas-dupont-aignan` et `bernard-cazeneuve`
(1997-2002) sont **présents comme acteurs, avec 0 mandat avant 2002**.

Conséquence pour le pipeline : les mandats sénatoriaux que le référentiel publie
sur des profils déjà collectés — **291 entrées sur 33 profils** — sont
aujourd'hui jetés par la normalisation, qui ne lit que les organes de
l'Assemblée. C'est l'objet de #878.

`_build_acteur_identite_index` used `AMO10` until issue #354 (sub-issue 3/6 of
#351): switched to `AMO30` to cover elected officials whose mandate has
ended, invisible in `AMO10`. `AMO30` was already downloaded/cached by
`_build_organe_index` / `_build_acteur_positions_hemicycle_index` (#353) —
reusing it (via the shared `_ensure_acteurs_historique_zip_downloaded`) avoids
an extra network round-trip per profile, on top of covering more legislatures
than the `AMO20_dep_sen_min_tous_mandats_et_organes*` archives considered
initially in the issue (confirmed to exist for legislatures 15/16/17 only,
one file per legislature to combine) — see
`docs/decisions/identite-acteurs-amo30.md` for the full comparison.

Empirically documented structure (identical on both datasets, `AMO30` verified
directly by downloading the 13.6 MB archive and sampling `json/acteur/*.json`
entries for deputies/senators from legislatures 12-17):

- Mixed entity types in one ZIP:
  - `json/acteur/PA{id}.json`
  - `json/organe/PO{id}.json`
  - `json/deport/DPTR5L{leg}PA{id}D{n}.json`
- `acteur.uri_hatvp`: link to HATVP declaration (not yet in current pivot schema).
- `acteur.mandats.mandat[].typeOrgane`: wide set of observed types (`GP`,
  `COMPER`, `PARPOL`, `MISINFO*`, `DELEG`, `BUREAU`, `CMP`, `GOUVERNEMENT`,
  `MINISTERE`, `ASSEMBLEE`, ...).
- `acteur.mandats.mandat[].infosQualite.codeQualite/libQualite`: free-text labels.
- `acteur.mandats.mandat[].legislature`/`dateDebut`/`dateFin`: on `AMO30`, a
  single acteur can have several `ASSEMBLEE` mandates (one per legislature
  they were (re-)elected in) — `_select_mandat_assemblee_courant` picks the
  ongoing one (`dateFin` absent) if any, else the one with the most recent
  `dateDebut`. Not needed on `AMO10` (single active mandate per acteur, by
  construction of that dataset's scope).
- `acteur.etatCivil.ident.{civ,prenom,nom}`: full name (used by
  `_build_acteur_identite_index` to build `nom_complet`). `civ` is filled on
  **all 3 117 fiches** of the historical archive, with two values — `"M."`
  (2 106) and `"Mme"` (1 011); it is the profile's only source of `civilite`
  (#659), never a first-name heuristic.
- `acteur.profession.socProcINSEE.{famSocPro,catSocPro}`: the INSEE
  socio-professional nomenclature (PCS) as the Assembly itself applies it —
  family and category. The block is present on all 3 117 fiches with exactly
  those two keys, and the two levels are **always filled or absent together**:
  2 177 fiches carry a pair of labels, 940 carry the `xsi:nil` marker on both.
  Labels come with typographic variants (`"Professions Intermédiaires"` 107 vs
  `"Professions intermédiaires"` 58), and one category label contains a double
  space. Distinct from `acteur.profession.libelleCourant`, which is free text
  (#641). Measured 31/08/2026.
- `acteur.adresses.adresse[]` (single dict, not a list, when there is only
  one entry — normalize like `mandats.mandat`): each entry has a
  `typeLibelle` (`"Adresse officielle"`, `"Adresse publiée de
  circonscription"`, `"Mèl"`, `"Twitter"`, `"Facebook"`, `"Instagram"`,
  `"Linkedin"`, `"Site internet"`, `"Téléphone"`, `"Télécopie"`, `"Url
  sénateur"` — observed on the full `AMO10` set, 577 acteurs) and a `valElec`
  field for non-postal types. `_build_acteur_identite_index` only extracts
  `Mèl`/`Twitter`/`Facebook`/`Site internet` into `contact`
  (email/twitter/facebook/site_web) — the rest is out of scope for now.
- Circonscription/place hémicycle: on the mandat selected by
  `_select_mandat_assemblee_courant` (`typeOrgane == "ASSEMBLEE"`),
  `election.lieu.{numDepartement,numCirco}` and `mandature.placeHemicycle` —
  extracted by `_build_acteur_identite_index` into
  `numero_departement`/`numero_circo`/`place_hemicycle`. Not yet wired into
  the pivot schema (`identite` block) — see #352/#351 subtask 4.

### `json/organe/*.json` structure (organeRef resolution, #353)

`organe.uid` (ex. `"PO59048"`) is the target of `mandats[].organes.organeRef`.
Confirmed fields on the historical bulk file (`AMO30`): `codeType` (33
distinct values observed on `AMO30`, e.g. `COMPER` committee, `GP` political
group, `GA` friendship group, `MISINFO*` info missions, `GOUVERNEMENT`,
`ORGEXTPARL` extra-parliamentary body, `CMP`, `DELEG`...), `libelle` (full
name, e.g. "Commission des finances, de l'économie générale et du contrôle
budgétaire"), `libelleAbrege` (short name, e.g. "Finances"), `libelleAbrev`
(very short code, e.g. "CION_FIN"), `organeParent` (nullable ref to a parent
organe). `_build_organe_index` (`candidate_profile.py`) indexes
`organeRef -> {sigle: libelleAbrege, nom: libelle, type: codeType}` for all
`codeType` values (no filtering) — a prerequisite for resolving any
`mandats[].organes.organeRef` to a readable name (committees with role,
friendship groups, extra-parliamentary engagements, political group).
`_build_organe_positions_index` is a narrower, pre-existing index limited to
`GP`/`GOUVERNEMENT` for majority/opposition/government qualification (see
`fetch_positions_hemicycle_officielles`) — the two are independent and do not
replace each other.

**`codeType == "GOUVERNEMENT"`: one organe per government, and its members
include people who were never deputies (#996, measured 17/09/2026 on the
17/08 archive).** 17 such organes, from `libelleAbrege` `FILLON 1`
(`viMoDe.dateDebut` 2007-05-17) to `LECORNU II`; nothing before 2007, so
Raffarin and Villepin are simply absent. `libelleAbrege` is what the collection
writes into `mandats[].label` as `"Gouvernement (<libelleAbrege>)"`, and
`viMoDe` carries the period verbatim. Mandates targeting these organes
(`typeOrgane == "GOUVERNEMENT"`) name **311 distinct people**, of whom **124
never held an `ASSEMBLEE` mandate** — Rachida Dati (`PA387829`) is in the zip
like any deputy, with her `etatCivil`. A roster built on `GP` mandates alone
cannot see them, which is why `gouvernement_roster_an.py` reads the organes
directly.

## Legislative files (bulk, multi-legislature in one file)

`.../17/loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip` (~10 MB,
daily updates).

### Deux formats coexistent, et la XIV n'est pas incompatible (2026-09-18)

Relevé le 18/09/2026 sur les quatre archives ingérées :

| Législature | URL | Format |
| --- | --- | --- |
| XIV | `.../14/…/Dossiers_Legislatifs_XIV.json.zip` (2,5 Mo) | **monolithique** — un seul `.json`, 36 Mo décompressés |
| XV | `.../15/…/Dossiers_Legislatifs_XV.json.zip` (15 Mo) | un fichier par objet |
| XVI, XVII | `.../{16,17}/…/Dossiers_Legislatifs.json.zip` | un fichier par objet |
| XII, XIII | — | **404**, revérifié le 18/09/2026 |

Le format monolithique porte les objets dans deux tableaux :
`export.dossiersLegislatifs.dossier[]` (**3 432**) et
`export.textesLegislatifs.document[]` (7 120). **Chaque dossier est sous la clé
`dossierParlementaire`, exactement comme dans le format par fichier** — seul
l'emballage change, pas le contenu, et `parse_dossier_gouvernemental` traite les
3 432 sans une exception.

**Le piège** : l'emballage n'est pas le même pour les deux collections. Un
dossier est `{"dossierParlementaire": {…}}`, un **document est l'objet nu**.

Second piège : le nom de fichier porte l'uid dans le format par fichier, ce qui
permet d'arbitrer les doublons sans rien désérialiser. Le monolithe n'en a pas,
donc l'uid se lit dans l'objet — et l'arbitrage compte : **30 uids de la XIV
figurent aussi dans les XV-XVII**.
→ `docs/decisions/archive-dossiers-xiv-1019.md`

Empirical findings:

- `dossierParlementaire.legislature` spans `{8, 11, 12, 13, 14, 15, 16, 17}`
  in a single file.
- `titreDossier.titre`: full human-readable title.
- `procedureParlementaire.{code,libelle}`: closed set of observed values.
- `initiateur.acteurs.acteur[]`: actor-level bill initiators. `acteur` is an
  object for a single initiator and a list for several (2482 vs 293 dossiers in
  the legislature-XVII archive); each entry carries `acteurRef` + `mandatRef`,
  never an inline type. 25 dossiers carry only `initiateur.organes` (body-level
  initiative, no named actor).
- `actesLegislatifs` is a recursive tree, including official reporters and
  procedural milestones.

Implemented path:

- `candidate_profile.fetch_textes_portes_officiels` /
  `_build_acteur_textes_portes_index` build `acteurRef -> dossiers` with known
  factual roles (`auteur`, `rapporteur`, `co-rapporteur`) and inferred
  procedural stage.
- This replaces legacy Nos* dossier lists for deputies.
- `gouvernement_textes.py` extracts the same `acteurRef`s per dossier
  (`initiateurs_acteur_refs`); `gouvernement_profile.py` resolves them against
  the government's own `membres[]` to fill `textes[].initiateurs` — the
  minister → bill link (723/725 government bills carry one, 1213 links, 556
  resolved). See `docs/decisions/gouvernement-textes-initiateurs.md`.
- `merge_profile.py` drops `dossiers_legislatifs`/`textes_portes` entries that
  have no factual `role` during migration/merge.

### Spike : origine (gouvernementale vs parlementaire) et statuts (`statutConclusion`/`codeActe`) (2026-08-14)

Spike documentaire pour #207 (préparation de #184), exécuté avec accès réseau
confirmé vers `data.assemblee-nationale.fr` : téléchargement et inspection
réelle de `Dossiers_Legislatifs.json.zip` (10,25 Mo ; **3044 vrais dossiers**
sous `json/dossierParlementaire/*.json` — le ZIP contient aussi 7056 fichiers
`json/document/*.json`, **décrits ici comme « sans rapport » jusqu'à #639 : c'est
faux**, chacun porte `dossierRef`, la seule clé sourcée qui rattache un texte
déposé à son dossier, et c'est celle dont le `texteLegislatifRef` d'un amendement
a besoin ; 21 936 des 21 937 uid distincts des trois archives en portent une, avec
0 divergence entre archives — voir `src/textes_dossiers_an.py` et
`docs/decisions/dossier-des-amendements-639.md`) et de
`AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip`
(historique complet des acteurs/mandats, ~13,6 Mo,
`.../17/amo/tous_acteurs_mandats_organes_xi_legislature/AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip`).
Les deux points bloquants de l'issue sont désormais confirmés avec des
exemples réels et des comptages exhaustifs sur l'échantillon complet, avec
une correction importante par rapport aux hypothèses de départ.

**Statut du dossier — confirmé, avec correction.**

Ce n'est **pas** `codeActe` qui porte adopté/rejeté/49.3 : les codes se
terminant par `-DEBATS-DEC` désignent seulement un type d'acte "Décision"
commun à toutes les issues (adoption, rejet, modification, etc.). Le statut
réel est porté par le sous-objet `statutConclusion.fam_code` de cet acte.
Valeurs observées (comptage exhaustif sur les 3044 dossiers) :

| `fam_code` | Libellé observé | Occurrences | Exemple |
|---|---|---|---|
| `TSORTF01` | adoptée | 487 | `DLR5L17N50939` |
| `TSORTF07` | rejetée | 40 | `DLR5L17N54196` (`AN1-DEBATS-DEC`) |
| `TSORTF06` | adopté via 49.3 (« considéré comme adopté [...] article 49, alinéa 3 ») | 4 | `DLR5L17N52428` |
| `TSORTF24` | rejeté via 49.3 (« considéré comme rejeté [...] article 49, alinéa 3 », motion de censure adoptée) | 1 | `DLR5L17N50588` |
| `TSORTF03` | adoptée sans modification | 62 | `DLR5L17N50168` |
| `TSORTF05` | modifiée | 118 | `DLR5L15N45886` |
| `TSORTF18` | adoptée art. 45 al. 3 (CMP) | 92 | `DLR5L17N50715` |
| `TSORTF19` | définitive art. 151-7 RAN | 27 | `DLR5L17N51596` |
| `TSORTF02` | adoptée avec modifications | 14 | `DLR5L15N45886` |

Ce comptage porte sur **tous** les dossiers d'une seule archive, toutes
origines confondues. `gouvernement_textes.py` ne mappe que les codes portés par
une **décision de séance** d'un dossier **gouvernemental** : 10 codes
(`TSORTF01/02/03/05/06/07/13/14/18/24`), tous mappés depuis #402 — dont
`TSORTF13` (« rejeté définitivement ») et `TSORTF14` (« voté par les deux
assemblées du Parlement en termes identiques »), absents de cette archive et
apparus avec les XV/XVI. `TSORTF19` n'apparaît sur aucune décision de séance de
dossier gouvernemental et n'est donc pas mappé. Les arbitrages — en particulier
`TSORTF02`, tranché en `navette_en_cours` sur données réelles — sont dans
`docs/decisions/gouvernement-textes-fam-codes-archives.md`.

Le retrait a son propre `codeActe` dédié, sans `statutConclusion` associé :
`AN1-RTRINI` (53 occurrences, ex. `DLR5L17N51314`) / `ANLUNI-RTRINI`
(29 occurrences, ex. `DLR5L17N52157`).

### Le piège des `codeActe` de commission : la saisine est automatique (2026-09-18)

**Un `codeActe` contenant `COM` ne dit pas qu'une commission a examiné le
texte.** La saisine de la commission saisie au fond est posée **le jour du
dépôt**, automatiquement, et l'arbre d'actes porte en plus des **conteneurs
d'étape** qui existent dès l'ouverture du dossier. Relevé sur les archives XV,
XVI et XVII, 10 764 dossiers, le 18/09/2026 — un dossier déposé et rien de plus :

```
AN1                       (conteneur d'étape, sans date)
AN1-DEPOT                 2024-01-25
AN1-COM                   (conteneur, sans date)
AN1-COM-FOND              (conteneur, sans date)
AN1-COM-FOND-SAISIE       2024-01-25   ← même date que le dépôt
```

84 codes distincts contiennent `COM`. Ceux qui attestent un examen réel sont
les réunions et les rapports : `AN1-COM-FOND-REUNION` (3 672),
`AN1-COM-FOND-RAPPORT` (1 095), `SN1-COM-FOND-RAPPORT` (997),
`AN1-COM-AVIS-REUNION` (703), `CMP-COM-RAPPORT-{SN,AN}` (285 / 281). Ceux qui
n'attestent rien : `-SAISIE` (6 410 AN + 2 738 SN), `-NOMIN` (1 133 AN +
1 003 SN, une nomination de rapporteur), et les conteneurs `-COM` / `-COM-FOND`
(6 410 chacun, jamais datés).

**Second piège, même arbre : un `codeActe` sans tiret est un conteneur.** Sur
les 17 codes nus, **16 ne portent jamais de date** — 6 418 `AN1`, 2 741 `SN1`,
1 463 `ANLUNI`, 1 415 `AN20`, 603 `PROM`, 284 `CMP`, 156 `CC`… Ils portent les
actes datés de leur étape, ils n'en sont pas un. `MOTION` est le seul exception
(8 occurrences, 8 datées).

Ce que ça a coûté : `"depose"` était inatteignable et 6 808 dossiers étaient
qualifiés « examiné en commission » sans l'avoir été.
→ `docs/decisions/examen-en-commission-997.md`

Exemple réel documentant les deux cas 49.3 sur un même dossier :
`DLR5L17N50588.json` (PLFSS 2025) — engagement de responsabilité en
1ère lecture (`CMP-DEBATS-AN-DEC`, `fam_code TSORTF24`, motion de censure
adoptée, chute du gouvernement Barnier, décembre 2024), puis nouvel
engagement en nouvelle lecture (`ANNLEC-DEBATS-DEC`, `fam_code TSORTF06`,
texte considéré comme adopté, février 2025).

Le code existant (`_stade_from_code_acte`,
`src/candidate_profile.py:1427-1446`) lit déjà `statutConclusion.libelle`
(pas `fam_code`) pour son seul stade `adopte`, ce qui confirme
indépendamment le chemin de champ documenté ici — mais reste conservateur :
il ne distingue pas les `fam_code` entre eux et ne traite ni rejeté, ni
retiré, ni 49.3.

**Origine gouvernementale vs parlementaire — confirmé, avec correction
importante.**

`initiateur` ne porte jamais de `codeType` inline (ni sur `acteurs.acteur[]`,
ni ailleurs dans le dossier) — seulement des références nues `acteurRef`
(+ `mandatRef`). La chaîne de résolution posée en hypothèse dans l'issue est
confirmée réelle de bout en bout : `acteurRef` → mandat avec
`typeOrgane == "GOUVERNEMENT"` → `organeRef` →
`organe.codeType == "GOUVERNEMENT"`. Exemple réel tracé : Sébastien Lecornu
(`PA643210`) → mandat gouvernemental en cours (`dateFin: null`) →
`organeRef PO873634` → `organe.codeType == "GOUVERNEMENT"`
(`libelleAbrege: "LECORNU II"`).

**Mais cette chaîne n'est confirmée que via le dataset `AMO30`** (historique
complet), **pas via `AMO10`** (mandats actifs uniquement — voir section
« Actors / mandates / bodies » plus haut, déjà utilisé ailleurs dans le
code) : `AMO10` ne verrait pas un ex-ministre toujours député aujourd'hui,
puisqu'il n'expose que les mandats en cours.

Or, utiliser `AMO30` sans filtrer par date de mandat (i.e. sans croiser
`mandatRef`/date du mandat gouvernemental avec la date de dépôt du texte)
produit des faux positifs mesurés : sur les 582 dossiers « Proposition de
loi » du dump (donc censés être d'origine parlementaire), 87 (14,9 %,
arrondi « ~15 % » dans le commentaire d'issue du 2026-08-12) ont au moins un
`acteurRef` co-signataire ayant été membre du gouvernement *à un moment
quelconque de son historique* — pas nécessairement au moment du dépôt du
texte (ex. `DLR5L17N54460`, `DLR5L17N50168`, `DLR5L17N50898`).

**Signal alternatif, plus simple et sans faux positif** : le préfixe de
`titreDossier.titre` — « Projet de loi » (origine gouvernementale, art. 39
de la Constitution) vs « Proposition de loi » (origine parlementaire) —
couvre 689 des 3044 dossiers (107 « Projet de loi » + 582 « Proposition de
loi ») sans aucune jointure ni faux positif. Les 2355 dossiers restants
(motions, résolutions, rapports, textes transmis du Sénat sans préfixe
standard, etc.) ne sont couverts par aucun des deux signaux et
nécessiteraient une inspection séparée si besoin.

**Recommandation pour les sous-issues suivantes** : privilégier le préfixe
de titre comme signal principal (simple, sans faux positif, couvre 689/3044
dossiers) ; réserver la chaîne `AMO30` — avec filtrage par date de mandat vs
date de dépôt, non implémenté dans ce spike — aux cas non couverts par le
préfixe.

**Conclusion du spike** : les deux points bloquants identifiés par l'issue
sont confirmés avec exemples réels et comptages exhaustifs. Le sous-ensemble
déjà en production (`depose`, `examine_commission`, `discute_seance`,
`adopte` approximatif, `promulgue`) reste inchangé et fiable pour son usage
actuel. L'implémentation des nouveaux statuts (rejeté, retiré, 49.3) et de
la distinction d'origine relève des sous-issues #208 (schéma) et #210
(parsing), pas de ce spike.

## Parliamentary questions (written/oral/government)

Unlike actors/files, these datasets use per-legislature paths:
`.../{legislature}/questions/{dataset}/{file}.json.zip`

| Type | Dataset | File | Approx. size (17th) |
|---|---|---|---|
| Written (QE) | `questions_ecrites` | `Questions_ecrites.json.zip` | ~45 MB |
| Government (QG) | `questions_gouvernement` | `Questions_gouvernement.json.zip` | ~5.2 MB |
| Oral without debate (QOSD) | `questions_orales_sans_debat` | `Questions_orales_sans_debat.json.zip` | ~3.1 MB |

Useful fields:

- `question.auteur.identite.acteurRef`: direct elected-official ID.
- `question.auteur.groupe.*`: group at question date.
- `question.minInt.developpe`: queried ministry.
- `question.indexationAN.analyses.analyse`: short subject summary.
- `question.textesQuestion...` and `question.textesReponse...`: full texts and
  publication dates.

Implemented in code:

- `candidate_profile._parse_question_entry`
- `_build_acteur_questions_index`
- `fetch_questions_officielles`
- Integration in `build_profile()` and normalization in
  `normalize_profil._normalize_intervention`
- Merge in `merge_profile.merge_raw_profile`

## Comptes rendus de séance (Syceron)

URL pattern:
```
https://data.assemblee-nationale.fr/static/openData/repository/{legislature}/vp/syceronbrut/syseron.xml.zip
```

Attention path/case:
- `vp` en minuscule (la variante `VP/` retourne 404)
- nom de fichier `syseron.xml.zip`

| Législature | Disponible | Taille ZIP | Statut |
|---|---|---|---|
| 13 | ❌ 404 | — | Non disponible |
| 14 | ❌ 404 | — | Non disponible |
| 15 | ✅ 200 | ~149 MB | Archivé (2022) |
| 16 | ✅ 200 | ~57 MB | Archivé (2024) |
| 17 | ✅ 200 | ~56 MB | Live, quotidien |

Format:
- ZIP vers `xml/compteRendu/CRSANR5L{legislature}*.xml` (un XML par séance)
- identifiants clés: `uid`, `seanceRef`, `sessionRef`
- métadonnées utiles: `metadonnees/dateSeance`, `metadonnees/etat`, `metadonnees/version`

Structure utile de contenu:
- `contenu/point` pour le bloc d'ordre du jour
- `paragraphe/orateurs/orateur/{id,nom,qualite}` pour l'orateur
- `paragraphe/texte` pour le texte (avec balises inline)

Intégration pipeline (active):
- fetch/cache XML via `src/syceron_debates.py`
- parsing via `src/parse_syceron.py`
- indexation acteur via `src/candidate_profile.py` (`_build_acteur_interventions_syceron_index`)
- fusion dans `interventions[]` via `fetch_interventions_syceron`

Mapping effectif dans `interventions[]`:
- `date` depuis `metadonnees/dateSeance` (normalisée)
- `type_detail` / `sujet` depuis `point/titreStruct/intitule` (fallback progressif)
- `texte` depuis `paragraphe/texte`
- `fonction` depuis `orateur/qualite`
- `source_url` conservée pour traçabilité

Contraintes/limites:
- pas de champ `theme` natif (classification dérivée seulement)
- pas de lien direct fiable vers `textes_portes[]` sans jointures additionnelles

Stratégie recommandée:
- full dump par législature (pas de téléchargement ciblé par séance)
- priorité produit: L17 puis L16, L15 en profondeur historique

## Agenda / meetings (committees) - low priority

`.../17/vp/reunions/Agenda.json.zip` (~7.8 MB).

Describes committee/plenary meetings (location, agenda, refs), but data is
organized by meeting/body rather than directly by `acteurRef`. Useful for
procedural chronology, not yet implemented.

## Extra-parliamentary bodies (CSV) - low priority

`.../17/amo/oep_csv_opendata/liste_organismes_extra_parlementaires_excel.csv`
(~1 MB, `;` separator, likely Latin-1 encoding).

Contains free-text member names rather than stable actor IDs, making reliable
matching risky (homonyms). Not implemented.
