# Ce que devient la donnée — les sorties de `pivot_data/`

Ce fichier décrit le **flux** : les sources, les fichiers, les schémas, la
volumétrie, et ce que le web lit. Il couvre les sorties de `pivot_data/` :
`profiles`, `groupes`, `lignees`, `gouvernements`, `amendements/`,
`scrutins.json`, `scrutins_dossiers.json`, `commissions_dossiers.json`,
`scrutins_europeens.json`, `dossiers_europeens.json`,
`actes_reglementaires/`, `textes_promulgues.json`.

**Sans les compter.** Le titre a annoncé « huit » puis « neuf » sorties pendant
que le disque en portait dix : `scrutins_dossiers.json` était décrit plus bas
sans figurer dans l'énumération, et `partis/` y figurait encore après son
retrait. Un inventaire chiffré se lit comme courant longtemps après avoir cessé
de l'être (`AGENTS.md` §8) ; la liste ci-dessus est vérifiable d'un `ls`, le
compte ne l'était pas.

`partis/` est sortie avec #906 ; `scrutins_europeens.json` et
`dossiers_europeens.json` sont entrés avec #901.

Trois voisins, et ce qui les sépare :

- **les règles** vivent dans `AGENTS.md` §2 et §3 — une règle derrière un lien
  est une règle qu'on manque ;
- **le pourquoi** vit dans `docs/decisions/`, un fichier par décision, indexé
  par `docs/technical_decisions.md` ;
- **ce que fait un run** — les jobs, le formulaire, les caches, les
  artifacts, les budgets, le push, la relance automatique — vit dans
  [`workflow-generate-data.md`](./workflow-generate-data.md). Ce fichier-ci n'en
  redit rien : il décrit ce qui est écrit, pas comment le run l'écrit.

Volumétrie mesurée le **30/08/2026** sur `origin/main` (`ad2cd016`), sur le
corpus **committé** — pas sur un run local.

---

## Les deux couches

| Couche | Ce que c'est | Qui la lit |
|---|---|---|
| `config/` | **ce qu'une personne a décidé et tapé** — les groupes et leurs lignées, la table Sycomore, la correspondance RNE (#1057). **Aucun run n'y écrit** ; le critère est qui écrit le fichier, jamais son nom | `groupes_config.py`, `mandats_anterieurs.py`, `collecte_mandats_locaux.py` |
| `raw_data/` | **au plus près de la source** — les votes y restent dénormalisés, chaque amendement y porte sa liste de cosignataires | la normalisation pivot, les deux constructeurs d'index, les audits |
| `pivot_data/` | le format commun à toutes les sources | **la seule couche que `web/` lit**, le quality gate, les agrégats |

Un profil brut n'est jamais publié tel quel. Un profil pivot ne se relit jamais
ligne à ligne : son format ne porte aucun sens (voir *Format d'écriture JSON*).

## Les sources

| Source | Ce qu'elle alimente | Périmètre |
|---|---|---|
| Open data de l'**Assemblée nationale** — référentiel acteurs AMO30, scrutins, amendements, dossiers législatifs, comptes rendus Syceron | tout le volet français : identité, mandats, votes, amendements, textes portés, interventions, roster de groupe, textes gouvernementaux | **source française unique depuis #529** |
| **Open Data Portal du Parlement européen** (+ **5 dumps ParlTrack** en enrichissement) | `mandat_europeen` du profil brut, normalisé par `normalize_europarl.py` ; puis, pour les **7 candidats déclarés à identifiant européen**, les `amendements[]` et `textes_portes[]` européens (`normalize_parltrack_dumps.py`) | volet UE. **Le lecteur des dumps était cassé depuis l'origine** — format NDJSON supposé contre tableau JSON publié — et ces sept profils publiaient « aucune donnée trouvée » sur eux (#683). Réparé le 09/09/2026 : **7 828 amendements** et 12 textes portés. Depuis le lot 2 (#683), les votes sur l'ensemble d'un texte, les interventions, les questions, les propositions de résolution et les **explications de vote** entrent dans les listes existantes — jamais un bloc parallèle — chaque entrée portant `institution: "parlement_europeen"`, que `couverture_profil.bornes_europeennes` lit pour dire quelle borne s'applique à quelle part. Mesuré sur les 7 : **12 939 votes sur un texte** (et 87 078 scrutins d'amendement écartés, comptés et déclarés), 4 584 interventions, 397 textes portés. **Les explications de vote reçoivent leur lien depuis #827** : ParlTrack n'en donne aucun (0 des 1 801 entrées `WEXP`, contre 100 % des neuf autres types), la référence est tirée de l'intitulé et l'adresse publique du Parlement écrite — mais seulement après que `data.europarl.europa.eu` a confirmé que le document existe, `www.europarl.europa.eu` étant derrière un pare-feu anti-robot qui rend `HTTP 202` à l'identique pour une URL vraie et pour une inventée. **1 508 sur 1 801 (83,7 %) liées, 0 lien mort** ; le cache `.cache/europarl/documents_doceo.json` évite de repayer les 47 minutes d'interrogation du portail à chaque run **Le titre est publié en FRANÇAIS** depuis le 16/09/2026 (#901) : le dump ParlTrack le donne en anglais, le portail publie le même document en 22-23 langues, et `ResolveurDocuments` téléchargeait déjà cette réponse pour en tirer un booléen d'existence — le titre français était récupéré puis jeté. Ce n'est pas une traduction fabriquée, c'est la version officielle. `textes_portes[].titre_langue` (`"fr"` | `"en"` | `null`) dit dans quelle langue le titre publié est : sans lui, plus rien ne mesure combien restent en anglais. Le repli conserve le titre anglais quand le portail n'a rien — un titre dans la mauvaise langue vaut mieux qu'un titre vide (§2 règle 5). **Aucune requête de plus** : existence, titre et concepts EuroVoc viennent de la même réponse, et le cache `.cache/europarl/documents_doceo.json` est en `documents-doceo-v3` (`{existe, titre_fr, concepts}`). **Le document se lit dans `source_url`, jamais dans le titre** : la première version cherchait une référence dans le titre, aucun des 694 titres n'en porte, et le run 35087127267 a publié **0 titre français** (16/09/2026). Une entrée écrite par un lecteur plus ancien se reconnaît à `concepts: null` et est **réinterrogée une fois** quand le titre ou les concepts sont demandés — jamais pour la seule existence. En CI, la clé de cache change **à chaque run** (`…-documents-v3-<run_id>`) : une clé fixe n'était jamais réécrite, et le cache restauré restait celui de sa première sauvegarde. |
| **Wikipédia** — article « Candidatures à l'élection présidentielle française de 2027 » (`fetch_candidats_declares.py`) | la liste des **candidats déclarés**, écrite dans `raw_data/candidats.json` | ajout **additif** seul : une entrée existante n'est jamais modifiée, et un candidat ajouté entre **sans slug**, donc hors collecte, jusqu'à relecture de sa correspondance AN (#753) |
| **Répertoire national des élus** (data.gouv.fr) — **collecté depuis #922**, par la `tabular-api` | `config/correspondance_elus_rne.json`, table **relue à la main** (#922) : elle apparie un candidat déclaré à un élu du RNE quand le corpus n'a **pas** sa date de naissance. Elle identifie une **personne**, jamais un mandat — elle ne se périme donc pas quand les mandats changent. Trois verdicts fermés : `confirme`, `ecarte`, `aucun_mandat_trouve` | La date de naissance résout **17 des 32 candidats déclarés** sans relecture ; les 15 autres relèvent de la table. Un candidat **absent** n'a pas été relu — absent n'est pas « aucun mandat » (§2 règle 5). Deux silences s'y distinguent : l'absence corroborée par une page Wikipédia, et celle qui ne l'est pas (`corroboration: "absente"`). Les **mandats locaux eux-mêmes sont collectés depuis #922** — couverture à partir de 2020, une absence antérieure étant déclarée et jamais lue comme « aucun mandat local » |
| **EuroVoc** (Office des publications, point SPARQL) | les **libellés français** des concepts dont le portail EP donne l'identifiant, et depuis le 17/09/2026 leur **domaine** EuroVoc, lu dans le thésaurus (concept → microthésaurus → domaine). Rien n'est découvert ni classé ici : le classement est celui du thésaurus (#901) | **deux** requêtes `VALUES` par **100 concepts**, une pour les libellés, une pour les domaines — 4 libellés en 0,22 s au 16/09/2026 ; 979 domaines sur 980 concepts au 17/09/2026. CC BY 4.0, attribution et indication des modifications. Un code sans libellé est **déclaré**, jamais inventé |
| **Journal officiel** — livraisons de la **DILA** (`echanges.dila.gouv.fr`), collectées depuis #1029 | `pivot_data/actes_reglementaires/<AAAA-MM>.json` : les décrets, arrêtés et ordonnances publiés depuis le 01/01/2007, avec l'index de mots de leur titre et de leurs articles (`actes_reglementaires.py`) | **Aucun rattachement à une personne** — la source laisse le signataire vide : un acte se rattache à un gouvernement par sa date de publication, à un ministère par son organe (#664). Le texte des actes n'est pas republié. Un run ne relit que les **deux derniers mois** ; le fonds a été construit une fois en local, le dump global de la DILA étant une livraison unique du 13/07/2025. À ne pas confondre avec la ligne suivante, où le JO est **cité** décret par décret pour des fonctions antérieures au corpus |
| **Sycomore** (Assemblée) et **décrets au Journal officiel** — CITÉS, jamais collectés | `config/mandats_anterieurs.json`, table **relue à la main** (#860) : les mandats nationaux d'un candidat déclaré **antérieurs au 19/06/2002**, début des données de l'Assemblée — une source primaire par ligne. Reposée sur chaque pivot de candidat en `mandats_anterieurs` à l'écriture, comme un champ dérivé | **Trois états, jamais deux** (#860, 15/09/2026) : des mandats trouvés — la liste, chaque ligne portant sa source ; une **absence constatée** — liste vide **plus** `mandats_anterieurs_constat` (`source_url`, `constate_le`, `methode` dans `KNOWN_METHODES_CONSTAT_ANTERIEUR` = `lecture_fiche_sycomore` | `relecture_humaine`), parce qu'une liste vide affirme « aucun mandat avant le 19/06/2002 » et qu'un fait publié porte sa source (§2 règle 2) ; enfin **personne n'a regardé** — `null` + `non_relu`. Les comptes par état sont imprimés par `scripts/poser_mandats_anterieurs_860.py --dry-run`, jamais figés ici. Le Sénat n'y entre pas (#528) : les 2 mandats de sénateur de Mélenchon sont nommés dans la table, non portés |

Deux sources ont été **retirées**, et ce fichier les nomme pour que personne ne
les recherche :

- **NosDéputés.fr / NosSénateurs.fr ne sont plus interrogés (#529, 27/08/2026)**.
  Le transport, la recherche d'interventions, le scraping HTML et le repli de
  roster sont partis d'un bloc. Ce qui **reste** est de la lecture du corpus déjà
  publié, jamais de la collecte : les valeurs `nosdeputes`/`nossenateurs` de
  `sources[].type`, l'attribution ODbL due aux champs déjà publiés (#530), et les
  interventions déjà collectées, qu'aucune régénération ne retire.
  → `docs/decisions/retrait-nosdeputes-529.md`
- **L'ACTIVITÉ sénatoriale est hors périmètre (#528), les APPARTENANCES sont
  revenues (#885)** — et la nuance est tout le sujet. #528 a retiré le job
  `extract-senat` et fermé `candidate_profile.build_profile` à
  `chambre="deputes"`, qui l'est toujours. #885 a **rouvert un job du même nom,
  par une autre porte** : `data.senat.fr`, lu par `src/senat_opendata.py`, qui
  écrit le seul bloc `mandat_senatorial` dans les profils bruts des candidats
  déclarés appariés — jamais un profil sénatorial complet.
  **Ce que le Sénat ne rend toujours pas** : ni scrutins, ni comptes rendus. La
  condition 2 du §7 de #528 est **déclarée non remplie**, pas contournée, et les
  deux fiches `groupe-Senat-*.json`, gelées depuis #516, ont été **retirées le
  16/09/2026** avec leurs deux lignées : elles dérivaient de NosSénateurs et
  n'étaient plus publiées par le site (`retrait-groupes-senat-nossenateurs.md`).
  → `docs/decisions/retrait-senat-528.md`, et l'issue #885

## Le flux

```mermaid
graph TD
    %% ── SOURCES ──────────────────────────────────────────────
    SAN["Open data Assemblée nationale<br/>AMO30 acteurs · Scrutins · Amendements<br/>Dossiers législatifs · Syceron"]
    SUE["Parlement européen (Open Data Portal)<br/>+ dumps ParlTrack"]
    SWK["Wikipédia — article des candidatures"]

    %% ── ENTRÉES ÉDITORIALES ─────────────────────────────────
    CAND["raw_data/candidats.json<br/>(éditorial, tenu à la main)"]
    ROST["raw_data/roster_candidats.json<br/>(généré — generate_roster_candidats.py)"]
    GRPC["config/groupes_reels.json"]
    GOUC["raw_data/gouvernements_reels.json"]

    SWK --> WIKI["fetch_candidats_declares.py<br/>ajoute les déclarés, slug: null"]
    WIKI -->|ajout additif| CAND
    CAND -.->|slug + correspondance AN,<br/>relus à la main| CAND
    GRPC --> ROST

    %% ── COLLECTE ────────────────────────────────────────────
    SAN --> CFR["candidate_profile.py"]
    SUE --> CUE["candidate_profile_ue.py + mep_profile.py"]
    CAND --> GAP["generate_all_profiles.py"]
    ROST --> GAP
    GAP --> CFR
    GAP --> CUE

    CFR --> RAW["raw_data/profiles/&lt;slug&gt;.json (socle)<br/>+ &lt;slug&gt;/&lt;legislature&gt;.json (amendements, #580)<br/>relu par profil_brut.py, jamais par json.load"]
    CUE --> RAW

    %% ── INDEX PARTAGÉS : LUS DEPUIS LE BRUT ─────────────────
    RAW -->|"AVANT la passe pivot<br/>(jointure de corpus)"| SCR["pivot_data/scrutins.json<br/>scrutins-v1 — build_scrutins_index.py"]
    RAW -->|"APRÈS la passe pivot,<br/>une seule fois"| AMD["pivot_data/amendements/&lt;legislature&gt;.json<br/>+ .cosignatures.json — amendements-v1<br/>build_amendements_index_pivot.py"]

    %% ── NORMALISATION ───────────────────────────────────────
    RAW --> NRM["normalize_profil.py<br/>normalize_europarl.py"]
    SCR -->|résout la législature d'un vote| NRM
    NRM --> PIV["pivot_data/profiles/&lt;slug&gt;.pivot.json<br/>schema_pivot.py"]

    %% ── AGRÉGATS ────────────────────────────────────────────
    PIV --> GRP["group_profile.py<br/>(via generate_group_profiles.py)"]
    GRPC --> GRP
    ROSTB["roster du run<br/>group_roster.py — zéro fetch en CI (#518)"] --> GRP
    GRP --> LIG["lignee_profile.py<br/>(via generate_lignee_profiles.py, #836)"]
    PIV --> GVR["gouvernement_roster.py<br/>(aucun réseau — mandats des pivots locaux)"]
    SAN --> GVT["gouvernement_textes.py<br/>dump Dossiers_Legislatifs.json.zip"]
    GVR --> GVP["gouvernement_profile.py<br/>(via generate_gouvernement_profiles.py)"]
    GVT --> GVP
    GOUC --> GVP

    GRP --> OGR["pivot_data/groupes/groupe-*.json<br/>schema_groupe.py"]
    LIG --> OLI["pivot_data/lignees/*.json<br/>schema_lignee.py"]
    GVP --> OGO["pivot_data/gouvernements/gouvernement-*.json<br/>schema_gouvernement.py"]

    %% ── GATE ────────────────────────────────────────────────
    PIV --> QG["check_quality_gate.py<br/>seul gate bloquant, avant le commit"]
    OGR --> QG
    OLI --> QG
    OGO --> QG
    SCR --> QG
    AMD --> QG
```

**Les deux index sont construits depuis les profils BRUTS, pas depuis les
pivots** — c'est le brut qui garde l'enregistrement complet du vote et la liste
des cosignataires ; le pivot n'en a plus que la clé. Et ils ne se construisent
pas au même moment : voir *Les deux index partagés*.

## Les deux sources d'entrée de l'extraction individuelle

`generate_all_profiles.py --candidats` accepte deux fichiers, qui pilotent
**trois** périmètres : `raw_data/roster_candidats.json` en porte deux depuis
#996 lot 3, distingués par leur `statut`, repris tel quel en `meta.provenance`.

| Source | Fichier | Qui la produit | Portée | `meta.provenance` |
|---|---|---|---|---|
| Éditoriale (défaut) | `raw_data/candidats.json` | tenue à la main | candidats/présidentiables déclarés ou pressentis — **13** au 30/08/2026 | `candidat_declare` |
| Roster-driven | `raw_data/roster_candidats.json` | `generate_roster_candidats.py`, depuis `config/groupes_reels.json` | tous les membres réels des groupes configurés **dont l'extraction n'est pas suspendue** — 10 des 12 depuis #700 (5 XVIe + 5 XVIIe), les 2 groupes Sénat restant gelés (#516). Un membre **sans slug** n'entre pas dans le roster (`build_roster_candidats_detaille` le laisse tomber). **Depuis #708** un acteur AMO30 qu'aucune entrée de `raw_data/correspondance_acteurs_an.json` ne couvre reçoit `text_utils.slugify(état civil)`, la table gardant la priorité absolue ; `ROSTER_SANS_SLUG` ne compte plus que les **collisions** non tranchées, et `ROSTER_SLUG_FABRIQUE` (`::notice::`) nomme qui entre sans correspondance relue — la §5b du portail bloque leur publication tant qu'elle manque (#525). **Depuis #715**, `merge-and-pivot` écrit cette entrée dans le run même qui crée le profil — `build_correspondance_acteurs_an.py --completer-derivees`, passe additive et hors ligne, estampille `origine: "derivee"` — de sorte que le slug est gelé avant d'être publié, et la table entre dans le `git add` du workflow. | `roster_groupe` |
| Roster-driven — gouvernements | `raw_data/roster_candidats.json` (mêmes entrées, `statut` distinct) | `generate_roster_candidats.candidats_des_gouvernements`, depuis les organes `GOUVERNEMENT` d'AMO30 (#996 lot 3) | les membres des gouvernements qu'AMO30 recense et qu'aucun roster de groupe n'amène. **Le roster des groupes gagne la déduplication** : une personne à la fois députée et ministre reste `roster_groupe`, sans quoi elle sortirait de la cohésion de son groupe. Son rattachement au gouvernement passe par l'`organe_ref` du roster (lot 4), pas par la provenance. `acteur_ref` est transmis à la collecte — une part de ces personnes n'a jamais été députée, donc aucune recherche par nom ne les retrouve dans AMO30 (#850). `--sans-gouvernements` débranche la passe ; un échec de lecture de l'archive est non fatal et ne collecte alors aucun membre, plutôt que d'en publier une liste amputée (§2 règle 5). | `roster_gouvernement` |

Même format d'entrée, même pipeline de collecte et de normalisation. Un même
`slug` peut apparaître dans les deux : `merge_profile.merge_pivot_profile()` ne
rétrograde **jamais** un profil `candidat_declare` vers une provenance de
roster, la source éditoriale prime.

`meta.provenance` est un vocabulaire **fermé** de trois valeurs
(`schema_pivot.KNOWN_PROVENANCES`), une par population de `pivot_data/profiles/`,
que `src/population_profils.py` nomme et ventile — tout compte de profils
affiché par un outil porte sa ventilation (#630). `PROVENANCES_ROSTER` y
regroupe les deux provenances de roster, pour les modules qui les traitent de
la même façon : collecte réduite au thème, `acteur_ref` transmis, preuve de
couverture.
→ [`docs/decisions/provenance-pivot.md`](./decisions/provenance-pivot.md),
  [`docs/decisions/provenance-roster-gouvernement-996.md`](./decisions/provenance-roster-gouvernement-996.md)

En CI, la voie roster-driven est un job dédié, `extract-roster-groupes`, distinct
d'`extract-an`/`extract-ue-officiel` et longtemps fixé au **mode d'extraction
léger** (`--skip-dossiers-legislatifs`, #357). **Les deux axes de ce mode sont
passés sous le formulaire** : les interventions suivent `collect_interventions`
depuis #657, sous une forme **réduite au thème**, et les dossiers législatifs
suivent `collect_dossiers_legislatifs` depuis #817. Les deux étaient posés en dur
au même motif — « aucun agrégat de groupe ne les consomme » — et il était faux
les deux fois : `tags_thematiques` dérive intégralement des interventions.
→ [`docs/decisions/collecte-interventions-reduite-au-theme-657.md`](./decisions/collecte-interventions-reduite-au-theme-657.md)
→ [`extract-roster-groupes.md`](./extract-roster-groupes.md)

`tags_thematiques` est un champ **dérivé** depuis #710, par la fabrique unique
`schema_pivot.deriver_tags_thematiques` : il se recalcule après la fusion pivot
comme `chambres` après la fusion des mandats, au lieu d'unir l'ancienne liste et
la neuve — l'union rendait tout tag immortel, et aucune correction de
`theme_officiel` ne pouvait l'en déloger.
→ [`docs/decisions/creneau-de-seance-nest-pas-un-sujet-710.md`](./decisions/creneau-de-seance-nest-pas-un-sujet-710.md)

## Le profil brut n'est plus un fichier (#580)

`amendements` pesait **96,7 % du plus gros profil brut** (54,15 des 56,00 Mo,
mesuré sur le corpus de #580) ; huit fichiers dépassaient l'avis GitHub à 50 Mo
et **cinquante-quatre** les 45 Mo — les mêmes députés cosignant les mêmes
amendements, ils franchissent la ligne *ensemble* à chaque correction de
collecte.

Chaque amendement portant déjà sa `legislature`, la liste est **partitionnée sur
un champ déjà présent** :

- `raw_data/profiles/<slug>.json` — le profil **moins** `amendements`, plus un
  manifeste `amendements_partitionnes` à sa place exacte ;
- `raw_data/profiles/<slug>/<legislature>.json` — une tranche par législature.

56,0 → 23,4 Mo pour le plus gros profil, **pas un octet perdu**. Ce n'est **pas**
la normalisation écartée par #434 : rien n'est dédupliqué, dénormalisé ni élagué.
`votes`, `mandats`, `interventions` restent dans le socle.

Lecture : **`src/profil_brut.py`, jamais `json.load` direct**.
`charger_profil_brut()` accepte les deux formes (monolithique et partitionnée),
`iter_amendements_du_profil()` diffuse tranche par tranche, et une partition
cassée lève `PartitionIllisible` au lieu de rendre une liste vide. Écriture :
toujours la forme partitionnée, donc un run complet migre le corpus tout seul ;
migration hors run par `src/migrer_profils_partitionnes_580.py`, idempotent.

**Depuis #691, une tranche de législature CLOSE n'est plus écrite** — elle est
*déclarée* dans le manifeste et relue dans `raw_data/amendements_an_figes/` :

```json
{"legislature": "15", "nombre": 18751, "derivee": true, "acteur_ref": "PA720892"}
{"legislature": "17", "fichier": "17.json", "nombre": 18893}
```

Le run `34344178203` (09/09/2026) a retiré **854 fichiers de tranches** —
77 en XIV, 270 en XV, 507 en XVI, la totalité — et `raw_data/profiles/` est
passé de **9,7 à 4,6 Gio**. Il ne reste que la XVIIe, **3,64 Go** : elle est
vivante, son archive figée n'existera qu'à la dissolution, et la reconstruire
depuis l'index pivot serait circulaire.

Trois propriétés gouvernent cette forme, et elles se lisent ensemble :

- **le manifeste doit dire `derivee`, et le silence reste une panne.** Une
  tranche annoncée sans marque et dont le fichier manque lève toujours
  `PartitionIllisible` : chercher l'archive « au cas où » ferait lire une
  tranche *perdue* comme une tranche dérivée ;
- **le `nombre` est celui de l'ARCHIVE**, pas de la collecte. Un écart
  n'empêche donc jamais de relire un profil ; il se déclare à l'écriture par
  `nombre_collecte`, écrit uniquement en cas de divergence ;
- **l'ordre devient par blocs** dès qu'une tranche est dérivée. Aucun
  consommateur ne lit l'ordre — `audit_diff_profils` relève une liste par un
  entier —, et l'aller-retour identique octet pour octet reste vrai pour tout
  profil sans tranche dérivée.

L'équivalence a été mesurée avant la bascule : **120 profils, 568 771
amendements, trois législatures, zéro écart** champ par champ. Deux champs sont
dérivés — `role_signataire`, qui vient de `index_par_acteur.json.gz`, et
`legislature`, que porte le nom du fichier.

→ `docs/decisions/reconstruction-tranches-depuis-archive-691.md`,
  `docs/decisions/tranches-derivees-lecteur-691.md`,
  `docs/decisions/marquage-tranches-derivees-691.md`

Le plus gros fichier versionné est un garde-fou surveillé : `src/garde_fou_blobs.py`
est la **§7 du quality gate** — avertissement à 50 Mio, **échec du commit à
80 Mio**. Ni « monter le seuil » ni « supprimer de la donnée » n'est un remède
disponible.

→ `docs/decisions/partition-profils-legislature-580.md`

### Ce que porte un profil brut

Le socle, champ par champ — c'est la matière que la normalisation pivot
reprend :

| Champ | Contenu |
|---|---|
| `identite` | nom, civilité, groupe politique, profession, circonscription… Depuis #659 le bloc porte `civilite` (`etatCivil.ident.civ` d'AMO30, 3 117/3 117 fiches) et les deux niveaux de la nomenclature PCS de l'INSEE — `famille_socioprofessionnelle`/`categorie_socioprofessionnelle`, depuis `profession.socProcINSEE` (2 177/3 117) —, recopiés verbatim et `null` quand la source ne classe pas, ce qui n'est **pas** la famille « Sans profession déclarée » |
| `mandats` | **tous** les mandats électifs (#640 : une entrée par siège, regroupée sur `(legislature, dateDebut)` d'AMO30 — plus le seul mandat courant) **et** les responsabilités réelles, avec rôle, dates et drapeau `actif` |
| `votes` | positions de vote et leur source (`votes_source`, qui liste **toutes** les législatures couvertes). Chaque vote porte sa `legislature` et son `url_source` — la page du scrutin AN — puisqu'un profil couvre désormais plusieurs législatures |
| `dossiers_legislatifs` | les dossiers législatifs de la chambre. Renommé `textes_portes` dans le pivot ; son `id` (`DLR5L15N37607`, 423 / 423 au 07/09/2026) y devient `dossier_id` depuis #639 — même nom que `gouvernements/*.json` → `textes[].dossier_id`. Chaque entrée porte depuis #689 sa `nature_texte` (`projet_de_loi` / `proposition_de_loi` / `proposition_de_resolution` / `null`), lue par `gouvernement_textes.nature_texte_depose` dans la même archive que les fiches de gouvernement — le préfixe de l'uid du document déposé, jamais le libellé. **Et depuis #743 son `sort`** : l'ISSUE du dossier (`KNOWN_SORTS_TEXTE_PORTE`, les mêmes neuf valeurs que `textes[].statut` d'une fiche de gouvernement, lues par la même fonction), qui ne se déduit **jamais** de `stade_procedural` — celui-ci encode une progression, et l'absence du cran suivant est un fait de la source à sa date. Un `sort` nul porte **toujours** `sort_non_resolu.motif` (`sans_decision` / `fam_code_inconnu` / `archives_indisponibles` / `source_sans_sort`), et `validate_profil()` refuse depuis #747 les deux ensemble **comme les deux absents** — une absence sans cause est refusée par §2 règle 5. **Un profil dont `meta.collecte_ecartee` déclare cette liste écartée n'en porte aucune entrée** : les 628 membres de roster publient tous `textes_portes: []`, et les 49 entrées résiduelles d'avant #357 ont été purgées (#747) |
| `interventions` | prises de parole : date, sujet, texte, rôle du moment, format estimé sur la longueur. Source depuis #510 : les comptes rendus Syceron de l'AN **uniquement**, plus les questions officielles QE/QG/QOSD. Le verbatim entier est publié pour les candidats déclarés ; les membres de roster (groupes et gouvernement) publient depuis #1029 un **extrait** de 280 caractères au plus, coupé en fin de phrase ou de mot (`collecte: "extrait"`, `texte_tronque`), les entrées plus anciennes restant réduites au thème (`collecte: "theme_seul"`, #657) jusqu'à leur recollecte. Chaque entrée Syceron porte `id_syceron` depuis #1087 : l'ancre de la prise de parole sur la page de séance de l'AN, dont le lien se construit par `schema_pivot.url_seance_an` (`…/dyn/<lég>/comptes-rendus/seance/<uid>#<id_syceron>`) — `source_url` reste l'archive. Les questions sont datées en ISO (#1044) ; une **QG**, posée à l'oral, n'a jamais de texte de question chez la source, et porte en `date` la parution au Journal officiel de son compte rendu, la même que `date_reponse` (arbitré le 22/09/2026). Une QG est **un acte** (l'entrée questions.an) et **ses tours de parole** (les entrées Syceron `question_gouvernement`, de 1 à 13 par question) : depuis #1094, chaque tour dont l'acte est publié dans le même profil et confirmé par le thème porte `question_ref`, l'`intervention_id` de l'acte — champ **dérivé** par `schema_pivot.rattacher_parole_aux_questions`, recalculé après chaque fusion. Mesuré le 22/09/2026 sur les 167 QG des 12 candidats déclarés qui en ont : 74 actes reliés sur le corpus publié, 122 projetés après la relecture des sujets de la XVe (`ANALYSE.ANA`, que le parseur ne lisait pas). Le repli par recherche NosDéputés a été retiré, donc une collecte vide **reste vide** et se déclare dans `meta.warnings[]`. Une entrée portant `collecte: "theme_seul"` (#657) a été collectée **sans son verbatim** : ses champs lourds sont absents, jamais publiés à `null`, et `meta.collecte_reduite` porte la déclaration du run. `sujet_code_grammaire` (#710) accompagne `sujet` **au brut seulement** : c'est le `code_grammaire` du point d'ordre du jour qui l'a fourni, le fait sourcé derrière le sujet, et le critère que lit `merge_profile.backfill_sujet_seance` |
| `amendements_partitionnes` | le manifeste des tranches, à la place exacte qu'occupait `amendements` (#580) |
| `mandats_locaux` | le bloc du Répertoire national des élus (#922), sur les candidats déclarés seulement. Il porte **toujours** son `appariement` — `date_naissance`, `table_relue`, `ecarte`, `aucun_mandat_trouve`, `non_relu` — **même quand il ne contient aucun mandat** : « relu, aucun mandat » et « personne n'a encore regardé » sont deux faits, et aucun ne se lit dans une liste vide (§2 règle 5). Il porte aussi `borne_couverture` (2020), qui voyage avec la donnée plutôt que de vivre seulement dans un document. `generate_all_profiles._verser_mandats_locaux` verse ses mandats dans `mandats[]` du pivot et y dépose `mandats_locaux_couverture` |
| `mandat_europeen` | présent seulement si le candidat a des enregistrements au Parlement européen. Il porte aussi l'**état civil** publié par le portail — `date_naissance`, `lieu_naissance` —, que `normalize_europarl` verse dans `identite` du pivot **depuis #922**. Il ne le faisait pas : les quatre candidats déclarés dont tout le parcours est européen ressortaient sans date de naissance, donc non appariables au Répertoire national des élus, alors que la donnée était collectée. Recopié verbatim, un lieu mal espacé compris (« Saint- Brieuc ») |
| `meta.warnings` | la transparence sur les collectes manquantes ou incomplètes |
| `meta.synchro_sources` | un horodatage ISO-8601 par source |


**`mandat_local` n'est pas un `mandat_electif`, et c'est voulu (#922).** Ce dernier
commande `chambres[]` : `appliquer_chambres` en dérive la liste, et le schéma compte
les `mandat_electif` **sans chambre** comme un défaut de collecte (#492). Y verser un
conseiller régional ferait sonner cette garde à chaque run — un conseil régional n'est
pas une chambre parlementaire, et n'a pas vocation à paraître dans `chambres[]`. Les
mandats locaux vivent donc dans `mandats[]` avec les autres, sous leur propre catégorie
et `categorie_source: "rne"`.


## Format d'écriture JSON

Les profils individuels (`raw_data/profiles/`, `pivot_data/profiles/`) sont
écrits **compacts** via `src/json_io.py` : l'indentation représentait 35 % de leur
volume (#433). Groupes, gouvernements, rosters et rapports d'audit
restent en `indent=2`, parce qu'ils se relisent à l'œil.

Un profil ne se lit jamais ligne à ligne : le format ne porte aucun sens.
→ `docs/decisions/profils-json-compact.md`

## Les deux index partagés

Ce sont les **seules dépendances entre fichiers** de `pivot_data/` : un profil
publié ne se lit plus seul, ni pour ses votes ni pour ses amendements. Les deux
doivent entrer dans le `git add` du workflow — un index non committé laisse
chaque mapping pointer sur rien, **silencieusement**.

Ils ne sont pas construits au même moment, et la différence n'est pas
d'organisation :

| | `pivot_data/scrutins.json` | `pivot_data/amendements/` |
|---|---|---|
| Schéma | `scrutins-v1` (#432) | `amendements-v1` (#431) |
| Construit par | `src/build_scrutins_index.py` (CLI), ou `generate_all_profiles.py` en cours de run | `src/build_amendements_index_pivot.py` (CLI), ou `generate_all_profiles.py` |
| Quand | **avant** la passe pivot — et **une seconde fois après**, dans un run qui collecte : les profils écrits pendant la boucle n'existaient pas au premier appel | **après** la passe pivot, **une seule fois** |
| Pourquoi cet ordre | résoudre la `legislature` d'un scrutin est une **jointure de corpus** (`src/scrutins_legislature.py`) : le jumeau étiqueté vit dans un autre profil. La normalisation a besoin de l'index. | la clé d'un amendement est son `uid` AN, et sa législature se lit **dans** l'uid. Rien à résoudre ; un passage préalable relirait 1,5 Go pour rien. |
| Lu depuis | `raw_data/profiles/` | `raw_data/profiles/` |
| Fusion | additive (sauf `--no-merge`) ; le second passage fusionne **toujours** | additive (sauf `--no-merge`) |

Une passe partielle ne doit jamais retirer des entrées que d'autres profils
référencent encore — c'est la leçon de #450, au niveau de l'index. Un scrutin
dont la législature reste irrésoluble fait **échouer** la construction : l'index
n'est pas écrit amputé, et aucune valeur par défaut n'est posée (AGENTS.md §2.5).

`amendement_id` vaut `an:<uid AN>`, et la législature se lit **dans** l'uid,
jamais depuis la date. Un profil pivot ne garde que
`{amendement_id, role_signataire}`, et pour un vote que `{scrutin_id, position}`.

**L'index des amendements est shardé par législature** : un fichier global unique
dépasserait la limite de blob de 100 Mo de GitHub. Les cosignatures vivent dans
un fichier compagnon `<legislature>.cosignatures.json` (schéma
`amendements-cosignatures-v1`) parce qu'elles font la majorité de l'index et
qu'**aucun consommateur ne les lit** — elles ne sont **jamais supprimées** pour
autant : un réseau de cosignatures est de la matière d'analyse (#324).

**Chaque fichier porte une table `textes`** (#639) : `texte_vise` → `{dossier_id,
titre}`, restreinte aux textes que ses amendements visent. `texte_vise` est l'uid
du **document** AN amendé (`PIONANR5L17BTC0699`), `dossier_id` celui de son
**dossier** législatif (`DLR5L17N50879`), lu dans `document.dossierRef` des
mêmes archives que les textes portés (`src/textes_dossiers_an.py`). La table est
**optionnelle** — les fichiers publiés avant #639 n'en ont pas — et un texte non
résolu n'y a **pas d'entrée** : `AmendementsIndex.dossier_de()` rend alors `None`,
jamais un rattachement par défaut. Une table plutôt qu'un champ par amendement
parce que 484 132 amendements ne visent que 2 248 textes distincts : +0,10 Mio
mesuré sur les quatre index, contre +5,7 Mio pour un `dossier_id` par entrée.
→ `docs/decisions/dossier-des-amendements-639.md`

**Un `texte_vise` qui n'est pas un uid se reprend depuis l'archive figée** (#696).
La fusion additive de l'index laisse gagner « la nouvelle valeur si elle est
renseignée », et un **intitulé** l'est : 2 500 des 484 132 amendements publiés au
01/09/2026 portaient encore le titre du dossier que la collecte d'avant #639 y
écrivait, tous en XVe. `amendements_index.backfill_texte_vise` relit la valeur
sourcée dans `raw_data/amendements_an_figes/<legislature>/`, entre la fusion et
la résolution des dossiers — jamais reconstruite depuis le titre, jamais
appariée par libellé. Ce qu'il ne peut pas réparer (législature sans archive
figée, amendement absent de l'archive) est **compté**, jamais comblé.
→ `docs/decisions/report-texte-vise-source-696.md`

Législatures 14/15/16 : dossiers clos, index AN bruts committés sous
`raw_data/amendements_an_figes/` et jamais re-téléchargés
(`docs/decisions/amendements-legislatures-figees.md`) ; même principe pour
`raw_data/scrutins_an_figes/`. Ces index-là se construisent **une fois, hors
ligne** (`src/build_amendements_index_figees.py`,
`src/build_scrutins_index_figes.py`) : la procédure et ses modes de défaillance
sont dans `docs/decisions/amendements-legislatures-figees.md` et
`docs/decisions/votes-multi-legislature.md`.

### Ce que les deux index ont fait gagner

Mesuré sur les **209 profils committés** du corpus de #431/#432 — la population
est celle-là, pas le corpus d'aujourd'hui :

| Scrutins (#432) | avant | après |
| --- | --- | --- |
| `votes[]` dans les profils | 179,8 Mo | 17,9 Mo |
| index partagé | — | 8,1 Mo |
| **total** | **179,8 Mo** | **26,0 Mo (−85,5 %)** |
| `cohesion_votes` des groupes | 6,23 Mo | 3,41 Mo (−45,3 %) |

| Amendements (#431) | avant | après |
| --- | --- | --- |
| `amendements[]` dans les profils | 1 342,4 Mo | 73,8 Mo de mapping |
| index partagé (méta) | — | 54,4 Mo |
| index partagé (cosignatures) | — | 75,7 Mo |
| **total** | **1 342,4 Mo** | **203,9 Mo (−84,8 %)** |

Le même index de scrutins sert les profils **et** les groupes : les 4 104
scrutins des groupes sont tous inclus dans les 17 422 des profils. Un fichier
d'amendements global unique pèserait déjà 130,1 Mo — au-delà de la limite
GitHub de 100 Mo par blob — et une législature portant aussi ses cosignatures
atteindrait 120,3 Mo pour la XV<sup>e</sup> à couverture complète : d'où un
fichier par législature, plus un compagnon.

### La `legislature` d'un scrutin, et pourquoi elle se résout

`votes[].numero_scrutin` repart à 1 à chaque législature : la clé d'un scrutin
est `(legislature, numero_scrutin)`. Or **22,5 % des votes collectés ne portent
aucune législature** (chemin de collecte antérieur à #403). `src/scrutins_legislature.py`
la résout par deux mécanismes, jamais confondus : jointure sur un **jumeau
étiqueté** (la donnée existe déjà ailleurs, étiquetée), puis **calendrier des
législatures** (une dérivation, tracée comme telle). Ce qu'ils ne résolvent pas
**échoue bruyamment** — jamais de valeur par défaut (AGENTS.md §2.5), et l'index
n'est pas écrit amputé.

Avant de se fier à la clé, `src/audit_legislature_votes.py` fait la passe de
corpus qui dit si elle est utilisable (voir
[`commandes.md`](./commandes.md)). Rapport de référence :
`audit/legislature_votes_20260819.md`.
→ `docs/decisions/resolution-legislature-votes.md`

### La qualification d'un scrutin (#639)

Une entrée de `scrutins.json` porte, depuis #639, ce que
`typeVote.codeTypeVote` dit du scrutin — un champ que l'archive renseigne sur
**18 311 / 18 311** scrutins bruts et que la projection jetait :

| `codeTypeVote` | `type_scrutin` | `type_vote` | Attendus (17 748) |
|---|---|---|---:|
| `SPO` | `public_ordinaire` | `vote_texte` | 17 312 |
| `SPS` | `solennel` | `vote_texte` | 361 |
| `MOC` | `motion_censure` | `motion_censure` | 66 |
| `SAT` | `tribune` | `vote_texte` | 9 |
| absent / inconnu | `null` | `null` | 0 |

S'y ajoute `demandeur` (« Président du groupe … », « Conférence des
présidents »), renseigné sur 17 664 des 17 748. Le tout pèse +1,52 Mo,
soit ~10,2 Mo pour l'index.

**La colonne dit ce que la source qualifie, pas ce que le fichier portait.** Le
run `33395056902` a publié `type_scrutin: null` et `demandeur: null` sur les
17 748, et `type_vote: "vote_texte"` sur les 17 748 : la qualification
n'atteignait pas `pivot_data/`, parce que `merge_raw_profile` fusionne `votes[]`
en additif pur et que le vote déjà collecté gardait ses sept clés d'avant #639.
`backfill_vote_qualification` reporte les trois champs sur l'entrée ancienne, et
`type_vote` n'a plus de valeur par défaut dans l'index. Chaque profil régénéré
qualifie les scrutins qu'il a votés ; la couverture se remplit run après run.
→ `docs/decisions/qualification-perdue-a-la-fusion-639.md`

Une entrée `motion_censure` porte `texte_lie_id: null` **et**
`texte_lie_non_resolu.motif` : le scrutin AN ne publie aucune référence
législative (0 / 18 311), et une motion de l'article 49 alinéa 2 n'a pas de
texte à lier. `vote_texte` reste **grossier** — `SPO` couvre indifféremment un
vote sur un article, un amendement ou un texte entier.

**Les trois index figés de `raw_data/scrutins_an_figes/` portent la
qualification** depuis leur reconstruction du 31/08/2026 : 1 354 scrutins pour
la XIVe, 4 417 pour la XVe, 4 105 pour la XVIe, dont respectivement 4, 5 et 34
motions de censure (les 23 autres des 66 sont dans la XVIIe, retéléchargée à
chaque run). Un index qui ne la porterait pas serait refusé, jamais relu —
`_load_frozen_scrutins_index` teste la **clé**, pas sa valeur.
→ `docs/decisions/qualification-scrutins-et-cle-dossier-639.md`

→ `docs/decisions/normalisation-votes.md`,
`docs/decisions/normalisation-amendements.md`

## Fusion additive : ce que la régénération ne retire jamais

`merge_profile.py`, appelé à chaque régénération sauf `--no-merge` :

| Champ | Règle |
|---|---|
| `votes`, `mandats`, `interventions` | additif, l'ancienne entrée gagne (`merge_lists_by_key`) |
| `amendements`, `textes_portes` | la nouvelle entrée gagne (`merge_dossier_records`) — permet de corriger un stade ou une issue |
| `dossiers_legislatifs` (brut) | additif, l'ancienne entrée gagne — mais `nature_texte` est **reportée** sur elle par `backfill_dossier_nature` (#689), sans quoi un champ ajouté à la collecte n'atteindrait jamais les entrées déjà collectées |
| scalaires | nouvelle valeur si renseignée, sinon on garde l'ancienne — jamais de régression vers `null` |

Clé de fusion d'un amendement : son `amendement_id`, ou — pour une entrée non
résolue — l'enregistrement conservé sous `amendement_non_resolu`. Se clé sur le
seul mapping ferait s'effondrer toutes les entrées non résolues en une seule.

Les agrégats (groupes, gouvernements) passent par
`merge_profile.load_existing_document` et
`preserve_stable_freshness_timestamps` : une régénération ne fait pas bouger un
horodatage de fraîcheur qui n'a pas de raison de bouger.

→ `docs/decisions/collecte-vide-necrase-jamais.md`, et les autres entrées de
fusion indexées par `docs/technical_decisions.md`.

## Les sorties publiées

| Sortie | Produite par | Schéma | Volumétrie au 30/08/2026 |
|---|---|---|---|
| `pivot_data/profiles/` | `normalize_profil.py`, `normalize_europarl.py` | `src/schema_pivot.py` | **1 382** fiches committées, 1 407 Mo (mesuré 18/09/2026, commit de données `f71dcdd6c`) — **trois populations**, voir `src/population_profils.py` |
| `pivot_data/groupes/` | `group_profile.py` (roster réel + pivots locaux) | `src/schema_groupe.py` | **30** fiches, 83 Mo (mesuré 11/09/2026, commit de données `62db21a9`) — 28 AN et 2 Sénat gelées, une par groupe **et** par législature (#700). Il y en avait **7** au 30/08/2026, pour 11 Mo. Depuis #1073, `tags_thematiques_agreges` ne compte que la parole tenue **pendant** l'appartenance au groupe, et porte `nb_membres_porteurs_par_fenetre` (12 et 6 mois) avec leurs bornes et leur dénominateur dans `fenetres_parole` ; depuis #853, `mandats_agreges` est borné de même (82 846 → 44 891 entrées membre × mandat sur les 29 fiches AN, mesuré le 22/09/2026) — mesuré le 22/09/2026 sur les 11 fiches de la XVIIe, l'agrégat passe de 60–230 Ko à 99–371 Ko par fiche |
| `pivot_data/lignees/` | `generate_lignee_profiles.py` → `lignee_profile.py` (#836) | `src/schema_lignee.py` | **13** fiches, 48 Mo (mesuré 11/09/2026, commit de données `62db21a9` — la sortie n'existait pas au 30/08) — une par LIGNÉE de groupe, c'est-à-dire par suite de fiches chaînées sur `succede_a` : 30 fiches de groupe pour 13 lignées, dont 2 lignées Sénat à un seul maillon. `membres` et `cohesion_votes` y sont des UNIONS, `amendements_agreges` et `tags_thematiques_agreges` des RECALCULS depuis `profiles[].amendements`. Écrites en **compact** : le critère de #433 est « relu à la main », et une fiche de lignée pèse jusqu'à 11,5 Mo. C'est la SEULE collection que l'interface publie pour les groupes — une fiche de lignée absente est une page du site en moins, d'où la §4c du portail |
| `pivot_data/gouvernements/` | `gouvernement_roster.py` + `gouvernement_textes.py` → `gouvernement_profile.py` | `src/schema_gouvernement.py` | **17** fiches, 1,1 Mo (mesuré 18/09/2026, commit de données `f71dcdd6c`) |
| `pivot_data/scrutins.json` | index partagé, ci-dessus | `scrutins-v1` | **17 748** scrutins, 9 Mo (~10,2 Mo une fois la qualification de #639 régénérée) |
| `pivot_data/scrutins_europeens.json` | `scrutins_europeens.py` (dump ParlTrack `ep_votes`) | `scrutins-europeens-v1` | **5 571** scrutins, 3,8 Mo (mesuré 14/09/2026) — ceux que les 7 profils européens citent, sur les 44 648 du dump. Porte les **effectifs** pour/contre/abstention et leur ventilation par groupe politique, jamais de liste nominative ni de `sort` déduit (#901) |
| `pivot_data/documents_europeens.json` | `documents_europeens.py` (portail EP + EuroVoc) | `documents-europeens-v2` | **335 documents cités** par les `source_url` doceo des textes portés européens (mesuré 16/09/2026) — `doceo` → `matieres: [{code, libelle, domaine}]`, **libellés en FRANÇAIS**. **`domaine`** (v2, 17/09/2026) est le domaine EuroVoc du concept, `{code, libelle}` lu dans le thésaurus (concept → microthésaurus → domaine) : **979 des 980 concepts** le résolvent, 21 domaines, aucun concept à deux domaines ; une matière sans domaine porte `domaine: null` et le document la déclare dans `domaines_non_resolu` (`domaine_eurovoc_introuvable`, codes nommés ; `eurovoc_injoignable` si le thésaurus est resté muet après trois essais, et alors l'index est publié quand même). C'est l'axe de couleur de la cascade européenne, ce qui distingue cet index de celui des dossiers. **Il existe pour ce que l'index des dossiers ne couvre pas** : sur les **383** textes portés européens distincts des 32 candidats déclarés, **327** ne citent aucun dossier (56 en citent un ; mesuré le 16/09/2026 après le retrait de 311 doublons, #963 — le compte « 628 des 694 » qui circulait les incluait) — des résolutions déposées en séance, qui n'ouvrent pas de procédure, donc sans commission au fond ni entrée dans `dossiers_europeens.json`. **Un index et non un champ sur chaque texte** : les occurrences se répètent d'un profil à l'autre, même raison qu'en #431. Les concepts viennent du portail EP (`is_about`), dans la réponse que `ResolveurDocuments` télécharge déjà — **aucune requête de plus au Parlement** ; seuls les libellés coûtent, chez l'Office des publications, **par lots SPARQL** (100 concepts par requête). **Trois absences, qui ne se confondent pas** : `portail_non_interroge` (la question n'a pas pu être posée), `source_sans_concept` (le portail répond et ne classe pas), `libelle_eurovoc_introuvable` (le concept existe, son libellé manque — les codes sont nommés). Aucune entrée n'est sans matière ni motif. **Piège du lot** : 625 des `source_url` sont en `http://` contre 56 en `https://` — un filtre sur la seule forme moderne rendait 56 documents au lieu de 335, sans erreur visible |
| `pivot_data/dossiers_europeens.json` | `dossiers_europeens.py` (dump ParlTrack `ep_dossiers`) | `dossiers-europeens-v4` | **389** dossiers (mesuré 16/09/2026). **`domaines`** (v4, 17/09/2026) : les domaines EuroVoc du dossier, `[{code, libelle, concepts}]` triés par nombre de concepts, lus sur son **document de séance** (texte adopté d'abord), que nomme `domaines_document` — EuroVoc est attaché à un document, jamais à une procédure. Aucun domaine n'est « le » domaine du dossier : c'est une lecture de l'interface. Essai du 17/09/2026 sur les 367 dossiers amendés par les candidats déclarés : **292** avec domaines, soit **5 507 des 7 303 amendements** ; 5,2 domaines par dossier en moyenne. Absences déclarées dans `domaines_non_resolu.motif` : `aucun_document_de_seance`, `documents_non_classes`, `question_non_posee` (budget en temps par run, les dossiers amendés passent d'abord, puis les plus récents ; mesuré au run `35231390627`, annulé : 301 dossiers avec domaines après 1 501 requêtes en 88 minutes ; depuis #1069, les textes adoptés se lisent par liste annuelle — passe locale du 21/09/2026, cache vide : 2 396 dossiers avec domaines sur 4 642), `eurovoc_injoignable`, `domaine_eurovoc_introuvable`. La couverture des dossiers votés monte d'un run à l'autre. **`familles`** (v3, 17/09/2026) : la famille OEIL de chaque matière — le premier segment du code — avec son libellé **anglais**, lu sur tout le dump (le plus récent l'emporte) : **389 dossiers sur 389**, 8 familles, aucune sans libellé (mesuré sur le dump du 17/08) ; une famille sans libellé serait déclarée dans `familles_non_resolu` (`libelle_famille_oeil_introuvable`) — les références que les profils publiés citent, sur 401 : les `texte_vise` des amendements, les `reference_dossier` des textes portés **et**, depuis le 17/09/2026, les `reference_dossier` des **votes** européens (4 630 références citées par les 11 013 positions de vote, dont 296 seulement étaient indexées ; estimation sur le dump du 17/08 : **4 642** dossiers, 3,4 Mo, tous avec leurs familles), seconde source ajoutée le 16/09/2026 (34 références, dont 30 `RSP`, ne résolvaient nulle part) ; référence → titre, type de procédure, stade, **matières** et **commissions saisies au fond**. **`matieres`** (#901, 16/09/2026) est la classification OEIL du dossier — `procedure.subject` — publiée en `{code, libelle}` triés par code : **389 dossiers sur 389**, y compris les **40 `RSP`** qu'aucune commission au fond ne couvre, 790 matières pour 238 codes distincts, aucune sans libellé. La source la donne sous **deux formes** — un dict `{"6.20.03": "…"}` sur 387 dossiers, une liste de chaînes où code et libellé sont collés sur 2 — et les deux sont lues, sans quoi deux dossiers perdraient leur matière sans erreur visible. **Ce n'est pas un vocabulaire fermé** : la nomenclature est hiérarchique (`6.20.03` se replie en `6.20` puis `6`) et le Parlement la fait vivre ; un `KNOWN_*` la fossiliserait. Un dossier sans matière porterait `matieres_non_resolu.motif = "source_sans_matiere"` — aucun ne le fait aujourd'hui. **Commissions saisies au fond** (345 dossiers sur 389, 25 sigles — le fait équivalent à la commission au fond d'un dossier AN, #328). **Élargir le périmètre n'élargit pas cet axe** : sur les 34 dossiers entrés le 16/09, **4** portent une commission au fond, les 30 `RSP` n'en ayant pas chez la source — ce que l'extension apporte à une fiche est le **stade**, pas la commission. Les 12 absentes sont de 2024-2025, le dump des dossiers étant plus ancien que celui des amendements (#901). **Les quatre libellés de la source se distinguent, ils ne se fondent pas** : `type_source` garde le verbatim, `statut` le lit en vocabulaire fermé — `au_fond`, `au_fond_conjointe`, `ancienne_au_fond`, `ancienne_au_fond_conjointe`. Écraser publierait comme compétente une commission **dessaisie**, et effacerait qu'une saisine est **partagée**. Les 44 dossiers sans commission nommée portent `commissions_au_fond_non_resolu.motif` : **38** `source_sans_commission_au_fond` (le dump n'en porte aucune) et **6** `saisine_conjointe_sans_commission_nommee` (la source affirme une saisine conjointe et laisse les sigles à la liste vide). 345 + 6 + 38 = 389, et aucune entrée n'est sans commission ni motif |
| `pivot_data/amendements/` | index partagé, ci-dessus | `amendements-v1` + `amendements-cosignatures-v1` | **484 132** amendements distincts, 259 Mo (index + compagnons) |
| `pivot_data/amendements/<lég>.contenu.json` | `amendements_contenu.py` (archive AN), publié par `build_amendements_index_pivot.py` (#1029) | `amendements-contenu-v1` | Pour **tous** les amendements de l'archive (pas seulement ceux de l'index) : `ids` (uid AN, triés), `articles` (`[titre, position]` alignés sur `ids`) et `mots` — l'**index de mots** de l'exposé sommaire, `{mot: renvois}`, un renvoi étant la position dans `ids`, écrite en écarts successifs base 36 (`amendements_contenu.decoder`). `ids` porte l'uid sans `prefixe_ids` (`AMANR5L17`), à recoller (`uid_complet`). Un mot : minuscules, sans accents, ≥ 4 lettres, ramené à sa forme de base quand elle existe dans l'index (`fusion_des_formes`, `forme_indexee` : `fiscaux` → `fiscal`), présent dans au plus 3 % des amendements (`seuil_frequence`). Chercher un mot = le normaliser, le ramener à sa forme indexée contre les clés de `mots`, décoder. L'exposé lui-même n'est pas publié ; il se lit chez l'AN (`…/dyn/<lég>/amendements/<uid>`). Mesuré le 22/09/2026 : XIV 167 420 amendements / 19,4 Mo, XV 311 934 / 37,0 Mo, XVI 163 789 / 19,8 Mo, XVII 124 929 / 16,8 Mo — 93,0 Mo, 29,4 Mo compressés, 72 408 mots distincts, 23,1 M de renvois. Les législatures closes se construisent une fois (une par run), la XVIIe avec son index. Chaque amendement de `<lég>.json` porte en outre `article` (`[titre, position]`), posé depuis ce fichier : +3 à +9 Mo par législature |
| `pivot_data/actes_reglementaires/<AAAA-MM>.json` | `actes_reglementaires.py` (livraisons DILA du Journal officiel, #1029 voie 1) | `actes-reglementaires-v1` | Un fichier par **mois de publication** : les décrets, arrêtés et ordonnances parus depuis le 01/01/2007 (`borne_basse`). `ids` (identifiants `JORFTEXT` sans `prefixe_ids`), `actes` aligné sur `ids` (`[rang de nature, titre, date de publication, rang de ministère, NOR, numéro]`, avec les tables `natures` et `ministeres`), et `mots` — l'**index de mots** du titre et de tous les articles, même fabrique et même lecture que `<lég>.contenu.json` ci-dessus (`amendements_contenu.decoder`, `forme_indexee`, seuil de 3 % des actes du mois). Le texte des actes n'est pas publié : il se lit chez Légifrance. **Aucun rattachement à une personne** — la source laisse `<AUTORITE>` vide ; un acte se rattache à un gouvernement par sa date et à un ministère par son libellé d'organe (#664). Les actes que la source date de `2999-…` vont dans `sans-date.json`, `mois: null`. **`liens_lois`** (23/09/2026) donne, pour les actes qui en portent, les lois qu'ils **appliquent** et celles qu'ils **citent**, par identifiant `JORFTEXT` : `{id: [[appliquées], [citées]]}`. La source distingue les deux, et un décret qui cite une loi en visa n'en est pas un décret d'application (§2 règle 2). Une clé **absente** est un acte **sans lien déclaré**, jamais un acte sans loi — la qualification est différée chez Légifrance, et aucune loi promulguée depuis 2024 n'en portait au 23/09/2026. Parce qu'elle arrive après coup, un acte **redélivré** par la source voit ses seuls liens repris dans le fichier de son mois, déjà clos (`corriger_les_liens`, `liens_revus_le`) ; le reste de sa ligne ne bouge pas, son index de mots n'étant pas reconstruit. Mesuré le 22/09/2026 sur le dump global et les 800 livraisons quotidiennes : **389 397 actes** (311 727 arrêtés, 76 664 décrets, 1 006 ordonnances), 2 368 125 articles lus, ~124 Mo d'index de mots et ~86 Mo de métadonnées. Un run ne relit que les deux derniers mois ; le fonds a été construit une fois en local, le dump global étant une livraison unique du 13/07/2025 |
| `raw_data/lois_jorf.json` | `lois_jorf.py`, alimentée par `actes_reglementaires.py` en chemin | `lois-jorf-v1` | **Référentiel dérivé, committé** comme les index de législatures figées : `numéro de loi → [[identifiant JORFTEXT, date de parution], …]`. Il fait le pont entre les `liens_lois` des actes, qui désignent une loi par son identifiant au Journal officiel, et les textes promulgués, que les archives de l'Assemblée n'identifient que par leur numéro et — sur 603 des 1 015 seulement — leur NOR. Construit une fois sur le fonds entier (**8 820 numéros**, 0,83 Mo, 23/09/2026), puis tenu à jour par les livraisons que le run lit déjà. **Un numéro peut porter deux enregistrements** — la publication d'origine et son rectificatif, 106 cas sur les 1 754 numéros depuis 2007 : les deux sont gardés, la plus ancienne en tête |
| `pivot_data/textes_promulgues.json` | `textes_promulgues.py` (archives de dossiers AN + `commissions_dossiers.json`) | `textes-promulgues-v1` | Une entrée par dossier **promulgué** : `date_promulgation`, `numero_loi`, `nor`, `titre`, `nature_procedure` (projet, proposition, ratification de traité, texte organique…), `commission` (la table ci-dessous, recopiée pour donner la **matière** de la ligne ; `null` quand elle manque, jamais devinée depuis l'intitulé) `jorftext` (+ `jorftext_autres` quand la loi a été publiée deux fois) — l'identifiant de la loi au Journal officiel, résolu par `raw_data/lois_jorf.json`, **1 015 / 1 015** au 23/09/2026 quand le NOR n'en résoudrait que 603 — et `chambre_premiere_lecture` — **dérivée de la date du dépôt le plus ancien**, tout dossier promulgué portant les deux dépôts, le second étant la transmission. Mesuré le 23/09/2026 sur les quatre archives : **1 015** textes promulgués (2012 → 2026), 0,47 Mo ; 336 propositions de loi ordinaires, 297 ratifications de traités, 273 projets de loi ordinaires ; 606 en première lecture à l'Assemblée, 409 au Sénat ; 0 sans numéro de loi, 0 sans commission, **412 sans NOR** (l'archive de la XIVe n'en publie pas). **Ce fichier ne porte aucun lien vers les décrets d'application** : la source ne qualifie plus ce lien depuis 2024 (`docs/sources/jorf-dila.md`) |
| `pivot_data/commissions_dossiers.json` | `build_commissions_dossiers.py` (#328) | `commissions-dossiers-v1` | **6 024** dossiers renvoyés en commission au fond (mesuré 01/09/2026 sur les archives XV/XVI/XVII), 1,2 Mo — **produit et versionné depuis le commit de données `5de11422`** (02/09/2026). Consommé par `generate_gouvernement_profiles.py` (`--commissions-dossiers`), qui en tire `textes[].commission_saisie_au_fond` (#689) |
| `pivot_data/scrutins_dossiers.json` | `build_scrutins_dossiers.py` (#758) | `scrutins-dossiers-v1` | **715** scrutins rattachés à **561** dossiers (mesuré 07/09/2026 sur les archives XV/XVI/XVII), 72 ko. Deux tables : `scrutins` (`clé de scrutin → uid de dossier`) et `dossiers` (`uid → {statut, sort_49_3}`). **Un scrutin AN ne nomme pas le texte qu'il tranche** — `objet.referenceLegislative` est nul sur 0/18 311 scrutins bruts —, le lien n'existe qu'en sens inverse dans `actesLegislatifs[].voteRefs`. Couvre **423 des 697 textes en dernière lecture (61 %)**, dont 412 avec une commission par jointure dans `commissions_dossiers.json`. Les 39 % restants sont une absence déclarée, jamais comblée par ressemblance de titre |

Populations, pour qu'aucun de ces chiffres ne se lise de travers : les 481
profils sont les **fiches committées**, pas les candidats déclarés (13) ni les
membres du roster ; les 484 132 amendements sont les entrées **distinctes de
l'index publié**, pas les paires (membre, amendement) ; les 17 748 scrutins sont
ceux de l'index publié, profils **et** groupes confondus — les scrutins des
groupes y sont entièrement inclus, une seule liste sert les deux.

Détail par législature de l'index des amendements :

| Législature | Amendements distincts | Amendements portant au moins un cosignataire |
|---:|---:|---:|
| 14 | 59 358 | 59 358 |
| 15 | 206 771 | 131 714 |
| 16 | 121 110 | 82 355 |
| 17 | 96 893 | 79 726 |
| **Total** | **484 132** | **353 153** |

### `pivot_data/profiles/` — les profils individuels

Le socle de tout le reste : les trois agrégats ne lisent que ça. Produits par
`generate_all_profiles.py --pivot` (ou `--pivot-only`, sans réseau) depuis les
profils bruts. Les données manquantes restent `null`, jamais `0` (AGENTS.md
§2.5). L'`id` d'un pivot est son **slug**, sans préfixe de provenance (#487) : la
provenance vit dans `sources[].type`, `identite.source_url` et
`meta.provenance`.

Le schéma pivot v1 est défini dans `src/schema_pivot.py` ; **le contrat clé par
clé est dans `AGENTS.md` §4**, avec les contraintes de validation en §5. À quoi
ressemble un fichier :

```json
{
  "schema_version": "1",
  "id": "jean-luc-melenchon",
  "nom": "Jean-Luc Melenchon",
  "chambres": ["AN"],
  "chambre": "AN",
  "parti": null,
  "groupe": "La France Insoumise",
  "sources": [
    {"type": "assemblee_nationale", "url": "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA1234", "synchro_le": "2026-07-29T..."},
    {"type": "assemblee_nationale", "url": "https://data.assemblee-nationale.fr/", "synchro_le": "2026-07-29T..."}
  ],
  "identite": { },
  "mandats": [ ],
  "votes": [ ],
  "textes_portes": [ {"titre": "...", "dossier_id": "DLR5L15N37607",
                     "role": "initiateur_projet_de_loi",   // dérivé de (rôle brut × nature), #689
                     "nature_texte": "projet_de_loi",      // le fait sourcé (PRJL/PION/PNRE)
                     "stade_procedural": "adopte",         // la PROGRESSION : le cran le plus avancé atteint
                                                           // `examine_commission` exige une RÉUNION ou un
                                                           // RAPPORT de commission depuis #997 : la saisine
                                                           // est automatique au dépôt et n'atteste rien
                     "sort": "promulgue",                  // l'ISSUE, #743 — jamais déduite du stade
                     "sort_non_resolu": null,              // non nul SI ET SEULEMENT SI `sort` est nul, #747
                     "...": null} ],
  "amendements": [ ],
  "interventions": [ ],
  "tags_thematiques": ["budget", "fiscalite"],
  "meta": {"schema_version": "1", "genere_le": "...", "warnings": [],
           "provenance": "candidat_declare", "licence_donnees": "...",
           "provenance_champs": {"identite": {"profession": {
               "source": "assemblee_nationale", "synchro_le": "..."}}}}
}
```

Trois pièges de lecture, sur ce fichier précisément :

- **`meta.provenance_champs` et `meta.provenance` ne disent pas la même chose**
  (#603). Le second dit *pourquoi ce profil existe* (`candidat_declare` /
  `roster_groupe` / `roster_gouvernement`) ; le premier dit *d'où vient chaque valeur d'`identite`, et
  de quand*. Il ne décrit **que** `identite`, seul bloc composé champ par champ
  (#601), et il est **facultatif** : les 481 profils publiés avant ce lot ne le
  portent pas. Une provenance inconnue s'y lit `{"source": null,
  "synchro_le": null}` — elle ne s'omet jamais.
  Ne pas le confondre non plus avec `couverture`, qui dit *pourquoi une liste
  est vide*, à la maille de la liste métier et non du champ ; ni avec
  `meta.collecte_reduite` (#657), qui dit qu'une liste a été collectée **à
  moitié** — trois questions distinctes, trois blocs.
  → `docs/decisions/provenance-par-champ-603.md`

- **`sources[].type` peut valoir `nosdeputes` / `nossenateurs` sur un profil
  publié**, alors qu'une collecte fraîche ne produit plus qu'`assemblee_nationale`
  depuis #529. Ce sont des valeurs **valides** de `KNOWN_SOURCE_TYPES` : les
  retirer ferait rejeter par `validate_profil()` le corpus qu'on vient de
  publier. #530 a mesuré qu'elles ne disparaissent pas d'elles-mêmes —
  `merge_pivot_profile` unit `sources[]` par type, donc une entrée déjà publiée
  survit à une collecte AN, et l'attribution ODbL reste due.
- **`meta.licence_donnees` est dérivé, jamais constant** : `src/licences.py` le
  recompose depuis `sources[]` après chaque étape qui les change. Ne jamais
  écrire un libellé de licence en dur ailleurs.
  → `docs/decisions/licence-lot-6-530.md`

### `pivot_data/groupes/` — les groupes parlementaires réels

Les groupes à produire sont déclarés dans `config/groupes_reels.json` : **12
entrées** — 5 groupes AN de la XVIe, **5 groupes AN de la XVIIe** (ajoutés par
#700, `docs/decisions/fiches-groupe-17e-legislature-700.md` : leurs fiches
paraissent au premier run qui suit) et, jusqu'au 16/09/2026, 2 Sénat —
(`Senat:LR`, `Senat:SER`, suspendues depuis le 24/08/2026 puis **retirées** avec leurs
fichiers et leurs lignées : `retrait-groupes-senat-nossenateurs.md`). **Une fiche par groupe ET par
législature** : le nom de fichier le porte depuis l'origine
(`groupe-AN-REN-16.json`).
Une entrée `extraction_suspendue` est **ignorée sans être un échec** : ni fetch,
ni régénération, et sa fiche déjà publiée reste en place, gelée à sa dernière
génération réussie (#516, `docs/decisions/extraction-groupe-suspendue-516.md`).

`generate_group_profiles.py` mutualise **un seul roster par couple (chambre,
législature)** — la source n'expose pas d'endpoint par groupe, le filtrage par
sigle se fait côté client (`group_roster.filter_roster_by_sigle`). En CI il n'y a
**aucun fetch** : `--rosters-bruts` relit le roster brut collecté au début du run
(artifact `roster-candidats`), ce qui garantit que la composition publiée est
celle du corpus collecté, et non une liste relue ~7 min plus tard (#518,
`docs/decisions/plafond-roster-et-commit-518.md`).
Un roster indisponible fait sortir le script en **2**, pas en 1 : aucune fiche
n'a été touchée, donc le run peut committer le reste ; un vrai plantage de
génération reste en 1 et fait échouer le step.

`historique_noms` porte les **organes successifs du groupe dans sa législature**
— `SOC` puis `SOC-A` sur la XVIe, `MODEM` puis `DEM` sur la XVe, `AD`, `UDR` puis
`UDDPLR` sur la XVIIe —, chacun avec son `sigle`, son `nom`, ses bornes d'organe et
son `organe_an` (#815). Recopié de `historique_organes_an` dans
`correspondance_sigles_an`, mesuré sur AMO30 et committé comme la position
politique (#686) : l'étape ne lit aucune archive. Une fiche non mesurée — les deux
Sénat, gelées — garde une liste vide.

`group_profile.py` **n'interroge pas le réseau** : il agrège des pivots locaux —
membres et périodes, cohésion de vote par scrutin, tags thématiques agrégés,
mandats agrégés (catégoriel : `commission`, `commission_enquete`,
`mission_information`, `groupe_etudes`, `delegation`, `groupe_amitie`,
`extra_parlementaire` — voir `MANDATS_AGREGES_CATEGORIES`, périmètre élargi par
#382, `docs/decisions/taxonomie-mandats-typeorgane-an.md`), amendements agrégés
avec ventilation par sort et par type de déposant. Une entrée de
`mandats_agreges` porte **deux comptages distincts et un dénominateur**, jamais
un nombre unique (#656,
`docs/decisions/mandats-agreges-siege-vs-passe-656.md`) : `nb_membres_actifs`
— **qui y siège** —, `nb_membres_cumul_historique` — **qui y est passé**,
adhésions d'un jour comprises — et `effectif_reference`, la couverture
disponible du groupe qui sert de dénominateur aux deux. 1 165 des 2 708
adhésions de commission publiées par les 7 fiches (43 %) durent une journée ou
moins, parce qu'un⋅e député⋅e n'appartient qu'à une commission permanente à la
fois et que toute bascule temporaire y est écrite comme un mandat à part
entière : sous le seul `nb_membres` d'avant, la fiche `AN-LFI-16` faisait siéger
67 de ses 76 membres à la commission des finances, quand ils sont 5. `poids_relatif` a disparu avec
lui — il ne disait plus de laquelle des deux grandeurs il était le poids. `amendements_agreges` compte
les amendements **distincts** portés par au moins un membre — un amendement
cosigné par trois d'entre eux en est un — et les **signatures** apposées par les
membres vivent à côté, sous `signatures` (#643,
`docs/decisions/amendements-distincts-et-signatures-643.md`) : les confondre
publiait « 2 600 765 amendements déposés » pour les 76 députés d'`AN:LFI`, avec
un facteur de × 5,0 à × 31,7 selon la fiche. La couverture roster/profils disponibles
est **tracée** (`meta.couverture_roster`), pour ne jamais confondre effectif réel
et effectif effectivement agrégé — un ratio ne se publie qu'avec numérateur,
dénominateur et couverture suffisante (AGENTS.md §2.7).

**`position_politique` porte la qualification que l'Assemblée donne elle-même
au groupe** (#686, `docs/decisions/position-politique-groupes-686.md`) —
`organe.positionPolitique` du référentiel AMO30, recopiée et jamais produite :
`majorite`, `minoritaire`, `opposition`, plus deux valeurs que le lot dérive,
`non_declaree` (aucun organe qualifié — les **14 groupes de la XVIIe**, l'AN ne
qualifiant qu'une législature achevée) et `divergente` (deux organes successifs
qui se contredisent, mesuré nul à ce jour). Le bloc porte sa **preuve** :
`source_url`, obligatoire même sur `non_declaree`, `verifie_le`, et `organes[]`
— un enregistrement par organe, dans l'ordre de succession, avec la chaîne
source verbatim. `position` est le **résumé dérivé** de ces déclarations, et le
schéma refuse un résumé qu'elles ne portent pas.

La valeur vient de la table committée `correspondance_sigles_an` de
`config/groupes_reels.json` (clé `position_politique_an`), **jamais d'une
ressemblance de sigle** : nos fiches disent `REN` et `LFI`, le référentiel dit
`RE` et `LFI-NUPES`. Aucune archive n'est lue au moment de générer ;
`python3 src/an_roster.py --positions` sert de fil-piège, et le **§4b du portail
de qualité** fait échouer le commit, seuil 0, si une fiche AN publiée n'a pas
son entrée. Le champ est **optionnel** : les 7 fiches publiées avant le lot ne le
portent pas, et les 2 `groupe-Senat-*`, retirées le 16/09/2026, ne l'ont jamais porté — AMO30 ne
qualifie que les organes de l'Assemblée.

**`succede_a` nomme le groupe de la législature précédente dont celui-ci prend
la suite** (#700, `docs/decisions/fiches-groupe-17e-legislature-700.md`) —
`{groupe_id, fichier, legislature, sigles_an, organes_an, etabli_par,
verifie_le}`. C'est **notre affirmation, pas un champ de l'AN** : l'Assemblée
ouvre et ferme des organes (`PO800508` clos le 09/06/2024, `PO845425` ouvert le
18/07/2024), elle ne les chaîne pas. D'où une dissymétrie voulue avec
`position_politique` : celui-ci **exige** un `source_url`, `succede_a`
l'**interdit** — le schéma refuse le bloc s'il en porte un. C'est `etabli_par`
(`relecture_humaine`, vocabulaire fermé à une valeur) et `verifie_le` qui disent
d'où l'affirmation vient ; la preuve publiée est les `sigles_an` / `organes_an`
du prédécesseur, recopiés verbatim de la table. Le champ est **optionnel** : les
7 fiches publiées avant le lot ne le portent pas, et les 5 de la XVIe ne le
porteront jamais (la XVe n'est pas couverte). `fichier` est ce qui fait que
l'affirmation **atteint un document** : le **§4 du portail** hard-faile, seuil
0, s'il ne désigne rien dans `pivot_data/groupes/`, et
`groupes_config.charger_correspondance_sigles` refuse une cible qui ne résout
pas dans la table.

`membres[].debut_dans_groupe` / `fin_dans_groupe` sont les dates du **mandat de
groupe politique de la législature de la fiche**, que le roster porte déjà
(`mandat_debut` / `mandat_fin`) : transit écarté, organes successifs recollés
(#526). Elles ne sont **pas** dérivées des mandats électifs du profil — depuis
#647 un profil porte toute sa carrière, et « premier mandat électif » datait
l'entrée dans un groupe de la XVIe à 2002 (#653,
`docs/decisions/dates-appartenance-groupe-653.md`). Sans roster, ou pour un
membre qu'il ne rend pas, les deux dates sortent `null` et `meta.warnings` les
compte : jamais de repli sur le mandat électif.

**Tous les comptes d'une fiche se rapportent à `date_reference`**, publiée dans
la fiche (#653) : la clôture de la période du groupe quand toutes les
appartenances sont refermées (`cloture_legislature`, `2024-06-09` pour les cinq
fiches AN de la XVIe), la date de génération tant qu'une reste ouverte
(`generation`). Trois compteurs s'y rapportent et le disent dans leur nom —
`effectif.a_la_date_de_reference`,
`mandats_agreges[].nb_membres_a_la_date_de_reference`,
`membres[].present_a_la_date_de_reference`. Ils s'appelaient `actuel`, `actifs`
et `actif` et se lisaient « aujourd'hui », ce qui, sur une fiche de législature
close, mesurait la carrière ultérieure des membres et non le groupe :
`effectif.actuel` valait exactement le nombre de membres encore député⋅es (85
des 193 de `AN:REN-16`, quand 169 y siégeaient à la clôture). `periode.actif`
n'est pas concerné : il décrit la période, pas un effectif à un instant.

`date_reference` est **optionnelle** : les 2 fiches `groupe-Senat-*` gelées par
#516 ne l'ont jamais portée, et ont été retirées le 16/09/2026. Tout lecteur doit
accepter les deux (`audit_groupe_dataset.CHAMPS_EFFECTIF` le fait).

**L'amplitude sur la période** (#702) : `effectif.min_historique` et
`effectif.max_historique` valaient `null` sur les 7 fiches depuis l'origine du
schéma. Ils publient désormais `{"valeur": 167, "date": "2024-03-09"}` — un
minimum sans sa date est un nombre sans fait, et deux champs voisins se
recopient l'un sans l'autre. L'effectif est réévalué à chaque
`debut_dans_groupe` et au **lendemain** de chaque `fin_dans_groupe` (la borne de
fin est inclusive), sur la **fenêtre de la fiche** : `periode.debut` →
`periode.fin`, `date_reference.date` prenant le relais de la borne haute tant
que la période est ouverte, jamais au-delà. À valeur égale, la **première** date
atteinte. Mesuré sur les 5 fiches AN de la XVIe : REN 167 → 175, RN 87 → 89,
LFI 74 → 75, LR et SOC plates (61, 31). L'écart entre `membres[]` et
`a_la_date_de_reference` (24 sur `AN:REN-16`) est de la **rotation**, pas une
amplitude.

Les deux champs sortent `null`, **motif publié dans `meta.warnings`**, dès
qu'une entrée `membres[]` n'a pas de `debut_dans_groupe` (seuil 0) : ce membre
n'est comptable à aucune date, et les bornes obtenues sans lui sont des bornes
inférieures (0 / 452 sur les 5 fiches AN ; 14 / 15 et 4 / 5 sur les 2 fiches
Sénat gelées). Trois formes se lisent — `null`, entier nu hérité, objet
`{valeur, date}` —, une seule se produit ; `schema_groupe.valeur_borne_effectif`
rend l'entier des trois. Limite qu'aucun `null` ne couvre : `membres[]` ne porte
qu'un intervalle par membre (périodes recollées, #526), donc un départ suivi
d'un retour est invisible et l'amplitude est un **minorant**.
→ [`effectif-du-groupe-dans-le-temps-702.md`](decisions/effectif-du-groupe-dans-le-temps-702.md)

À ne pas confondre avec le job CI `extract-roster-groupes`, qui utilise aussi
`group_roster.py` (via `generate_roster_candidats.py`) mais pour produire des
profils **individuels** bruts couvrant tous les membres du roster, en amont de
l'agrégation faite ici. → [`extract-roster-groupes.md`](./extract-roster-groupes.md)

### `pivot_data/gouvernements/` — les gouvernements

**La liste des gouvernements est lue dans AMO30 à chaque run** (#996, 17/09/2026) :
`src/gouvernements_amo30.py` écrit `raw_data/gouvernements_reels.json`, un
gouvernement par organe `GOUVERNEMENT`, avec `organe_ref`, `libelle_an`
(`libelleAbrege`) et `periode` (`viMoDe`) **verbatim**. **17** gouvernements dans
l'archive du 17/08/2026, de Fillon I (17/05/2007) à Lecornu II (le seul dont
`periode.fin` est `null`) ; Raffarin et Villepin n'y figurent pas. Jusqu'au
17/09/2026, la liste était **écrite à la main** (#209) : 10 fiches, sans Fillon I,
Ayrault I et II, Valls I et II, Cazeneuve ni Lecornu I. Les dates d'AMO30
élargissent les périodes des 10 fiches existantes, sans jamais les rétrécir.
**Les membres sont rattachés par `organe_ref`** depuis #996 lot 4 :
`slugs_du_gouvernement` lit dans le roster brut qui appartient à cet organe, et
la **période de l'organe** sert de garde temporel. Le libellé ne décide plus de
l'appartenance — il ne fait plus que départager les mandats d'une même
personne, ce que la période ne peut pas faire pour deux gouvernements qui se
touchent d'un jour. Sans roster, le repli par libellé s'applique et les fiches
sont produites quand même.

**Sur quoi les membres ont pris la parole** (#1020) : `tags_thematiques_agreges`
porte une entrée par étiquette — `tag` et `nb_membres_porteurs`, **sans ratio**,
son dénominateur étant `comptages.membres_avec_interventions` publié à côté
(§2.7). Même fabrique d'étiquettes que la fiche de groupe
(`deriver_tags_thematiques`, #710), et une étiquette compte **une fois par
membre** : l'agrégat dit combien de personnes ont parlé d'un sujet, jamais
combien de fois (§2 règle 1).

Le filtre, lui, diffère du groupe : celui-ci retient par **législature** lue
dans l'identifiant (#403), un gouvernement retient par la **fenêtre de passage
de chaque membre**, sur la date publiée. Une période de gouvernement n'est pas
une législature, et une personne n'y siège souvent qu'un moment — mesuré sur
Borne, ce filtre retire 39 % des entrées, dont les 8 968 de Yaël Braun-Pivet,
ministre trois jours puis présidente de l'Assemblée. Une intervention **sans
date est écartée et comptée**, là où le groupe retient ses entrées sans
législature : un gouvernement dure quelques mois, rien ne permet d'y placer une
entrée non datée (§2 règle 5).
→ [`docs/decisions/agregat-parole-gouvernement-1020.md`](./decisions/agregat-parole-gouvernement-1020.md)

**La matière vient d'une lecture à la demande, pas de `profils`.** Les profils
chargés par le job sont **projetés** sur cinq blocs (#635) et ne portent pas
`interventions` — 38,1 % du volume du corpus, mesuré le 18/09/2026. L'agrégation
les lit donc **une personne à la fois** sur disque
(`gouvernement_roster.lecteur_interventions`), et le document meurt à chaque
retour : 650 lectures pour 311 personnes distinctes, 13,5 s et 0,22 Gio de RSS
pour les 17 fiches. Avant ce correctif, les 17 fiches publiaient `[]` et un
`membres_avec_interventions` à `0`. Sans lecteur, l'agrégat n'est **pas
calculé** : le comptage vaut `null` et un warning le dit, plutôt qu'un zéro qui
se lirait « aucun membre n'a parlé ». **Les zéros qui restent sont des faits** —
les interventions collectées commencent le 28/06/2017, donc les neuf
gouvernements antérieurs à Philippe II n'ont rien à agréger.
→ [`docs/decisions/lecture-a-la-demande-des-interventions-1020.md`](./decisions/lecture-a-la-demande-des-interventions-1020.md)

**Deux comptages, deux populations.** `comptages.membres_recenses` (lot 2)
compte les **personnes** que l'AN recense, qu'elles aient un profil ou non ;
`comptages.membres_distincts` (lot 4) compte les personnes que `membres[]`
porte. `len(membres)`, lui, n'est ni l'un ni l'autre : `membres[]` a une entrée
par **période**, un ministre qui change de portefeuille en cours de
gouvernement en ayant plusieurs (#398). Les deux comptages restent des entiers,
jamais un taux (§2 règle 7). `membres_recenses` vaut `null` quand la liste ne le
porte pas — un recensement inventé ferait lire « 2 des 2 membres » là où il en
manque 19.
→ [`docs/decisions/rattachement-des-membres-par-organe-996.md`](./decisions/rattachement-des-membres-par-organe-996.md)

**Le roster des gouvernements entre dans `rosters_bruts.json`** (lot 2, non
committé, produit à chaque run) sous la clé `gouvernements:`, à côté des
`deputes:<legislature>` : un membre par personne, avec son `slug`, son
`slug_origine` et ses `mandat_periodes`. C'est ce qui donne un identifiant de
profil aux ministres jamais députés — mesuré le 17/09/2026 : 311 membres, 106
slugs repris de la table de correspondance, **205 fabriqués**, aucun bloqué —,
et ce qui fait créer leurs entrées de correspondance (§5b du portail). Depuis le
lot 3 ces membres entrent aussi dans `roster_candidats.json` sous
`statut: "roster_gouvernement"`, donc les shards les collectent ; depuis le lot
4, ce même roster est relu par `generate_gouvernement_profiles.py`
(`--rosters-bruts`) pour rattacher les membres aux fiches.
Deux matériaux, jamais mélangés :

- **la composition** — `gouvernement_roster.py`, **aucun appel réseau** : il
  parcourt les pivots individuels déjà sur disque et en extrait les mandats
  `categorie == "fonction_gouvernementale"`. Un membre n'est retenu que si le
  libellé du mandat correspond **exactement** au `libelle_an` déclaré dans la
  config **et** que la période chevauche celle du gouvernement — l'AN n'expose
  que `organe.libelleAbrege` (« BORNE », « LECORNU II »), ambigu entre deux
  gouvernements homonymes lors d'un remaniement. Un ministre qui change de
  portefeuille produit **une entrée `membres[]` par période**, jamais un
  portefeuille choisi arbitrairement parmi les siens. `premier_ministre` se dérive
  du même matériau et reste `null` si aucun profil local ne porte le mandat —
  jamais une valeur déduite du nom du gouvernement (AGENTS.md §2.5) ; c'est le cas
  des 7 Premiers ministres sans profil pivot dans le dépôt.
  `portefeuille` (#398) vient des mandats `typeOrgane == "MINISTERE"`, mais le
  label ne suffit **pas** : un parlementaire en mission (art. LO144) porte le même
  type de mandat, avec pour label le ministère **auprès duquel** il est missionné.
  Seule `mandats[].fonction` les sépare — liste blanche `FONCTIONS_MINISTERIELLES`
  (#474, `docs/decisions/parlementaire-en-mission-nest-pas-ministre.md`).
  `portefeuille` retombe à `null` avec un warning si aucune `source_url` n'est
  traçable, le schéma l'exigeant dès que l'intitulé est renseigné.
- **les textes** — `gouvernement_textes.py`, seule fonction réseau du lot
  (`ensure_dossiers_zip_downloaded`), lit le dump AN `Dossiers_Legislatifs.json.zip`
  (une archive par législature, #400, dédupliquées par uid, la législature la plus
  élevée faisant foi). **Quatre archives depuis #1019 — XIV à XVII — et deux
  formats** : la XIV est monolithique (un seul JSON, les objets dans deux
  tableaux), les autres portent un fichier par objet. La détection se fait sur
  la forme de l'archive, jamais sur son numéro. La borne de couverture recule
  ainsi au **2012-06-20**, et les XII/XIII restent hors d'atteinte (404). L'origine gouvernementale (art. 39) se lit sur le **type du
  document déposé** — préfixe de l'uid du `texteAssocie` de l'acte `*-DEPOT` le
  plus ancien : `PRJL` = projet de loi, `PION` = proposition, `PNRE` = résolution.
  `procedureParlementaire.code` ne sert que de repli, et **jamais** pour les codes
  5 et 7 (« projet **ou** proposition »), parce que deviner violerait
  AGENTS.md §2.5.

`gouvernement_profile.py` combine les deux : c'est **lui** qui rattache un texte à
un gouvernement, par recouvrement de `date_depot` avec la période — jamais par
date de conclusion, un texte déposé sous A puis conclu sous B restant crédité à A.
Il résout aussi `textes[].initiateurs` vers un `membre_id` quand l'`acteurRef`
correspond à un membre retenu ; sinon l'`acteurRef` brut est conservé avec
`membre_id = null`, jamais rattaché à un profil approchant (#435).

Depuis #689, il joint chaque texte à `pivot_data/commissions_dossiers.json` **par
`dossier_id`** — jamais par le titre — et publie `textes[].commission_saisie_au_fond`
(`{organe_ref, sigle, nom, type}`), la matière que l'Assemblée assigne elle-même au
dossier. Quand elle manque, `commission_non_resolue.motif` dit **laquelle** des
trois causes, qui ne se réparent pas au même endroit : `depot_senat` (l'index est
celui de l'AN, le Sénat est hors périmètre #528 — **174 textes, et jamais
réparable**), `absente_de_l_index` (un trou de l'index AN, **0** aujourd'hui,
compteur-témoin), `index_indisponible` (une panne du run). Mesuré sur les 725
textes : **381/381 des dépôts AN résolvent**, 170/344 des dépôts Sénat, **551 au
total (76,0 %)** — dont **532 `COMPER`** (permanentes, une matière) et **19 `CNPS`**
(spéciales, créées pour un texte). Le `type` est verbatim, et c'est lui qui sépare
les matières de la traîne sans qu'un seuil ait à le faire (§2 règle 1).
`comptages.par_statut` est un **dénombrement**, aucun taux ni pourcentage nulle
part (AGENTS.md §2.1). Le 49.3 est un booléen `sort_49_3` porté par le texte,
jamais fusionné avec une position de vote (AGENTS.md §2.4).

`generate_gouvernement_profiles.py` ne fetch le dump et ne charge les pivots
qu'**une seule fois** pour tout le batch — miroir de `generate_group_profiles.py`,
et c'est aussi ce qui interdit le double-comptage d'un texte entre deux
gouvernements requêtés séparément. Comme pour les groupes, une collecte réseau
incomplète sort en **2** (`EXIT_COLLECTE_INCOMPLETE`) et **aucun profil n'est
réécrit** (#427).

**La couverture des textes a une borne, et elle est publiée.** Les archives de
dossiers ingérées couvrent les législatures **XV à XVII**, à partir du
**21/06/2017** (`src/couverture_dossiers.py`, `borne_couverture_textes()`).
Avant cette borne, un `textes[]` vide n'est **pas** « aucun texte porté » : c'est
une absence de source, qui ne doit jamais se lire comme un fait mesuré
(AGENTS.md §2.5). Sur les 10 gouvernements déclarés au 30/08/2026 :
**6 couverts**, **1 partiel** (Philippe II, à cheval sur la borne) et **3 hors
couverture** (Fillon II, Fillon III, Philippe I). La même borne est reprise
côté web (`GOVERNMENT_TEXTS_COVERAGE_START` dans `pivotAdapter.js`) et
`tests/test_couverture_dossiers.py` échoue si les deux valeurs divergent.

**Limite propre à cette vue** : `gouvernement_textes.py` ne lit que le dump AN.
Un texte dont le Sénat est la chambre de dépôt *primaire* n'est jamais vu, alors
que `schema_gouvernement.py` expose `chambre_depot_initial` (`"AN"` | `"Senat"`)
et pourrait laisser croire à une couverture bicamérale complète.
→ `docs/decisions/gouvernement-doc-cloture.md`,
`docs/decisions/hors-perimetre.md`

Un `docs/pipeline-gouvernement.md` séparé avait été proposé en #214 puis laissé
en suspens : cette section le rend inutile — un seul fichier décrit toutes les
sorties.

## Du pivot au web (`web/UI_finale`)

```mermaid
graph TD
    PIV["pivot_data/profiles/"] --> SYNC["web/UI_finale/scripts/sync-data.mjs"]
    PGR["pivot_data/groupes/"] --> SYNC
    PLI["pivot_data/lignees/<br/>lues, NON copiées"] --> SYNC
    PGO["pivot_data/gouvernements/"] --> SYNC
    SCR["pivot_data/scrutins.json"] --> SYNC
    AMD["pivot_data/amendements/"] --> SYNC
    COM["pivot_data/commissions_dossiers.json"] --> SYNC
    SDO["pivot_data/scrutins_dossiers.json"] --> SYNC
    CAND["raw_data/candidats.json"] --> SYNC

    SYNC --> MAN["public/data/manifest.json<br/>candidates + groupes + lignees + gouvernements<br/>(+ groupIds[] par candidat)"]
    SYNC --> PUB["public/data/ — profiles · groupes · gouvernements<br/>+ scrutins.json + amendements/ + commissions_dossiers.json<br/>+ scrutins_dossiers.json"]
    SYNC --> CVR["public/data/couverture.json<br/>projection au build — ce que le dépôt porte,<br/>par institution / liste / champ"]
    SYNC --> VLI["public/data/lignees/&lt;id&gt;.json<br/>projection au build — une par lignée (#329)"]
    SYNC --> VPG["public/data/gouvernements/&lt;id&gt;.paroles.json<br/>projection au build — le détail d'un sujet de parole (#330)<br/>chargée au premier clic, 1,2 Mo pour les 17"]

    VPG --> IDX
    MAN --> IDX["src/data/index.js<br/>getCandidateProfile / getLigneeProfile / …"]
    PUB --> IDX
    VLI --> IDX
    IDX --> ADP["src/data/pivotAdapter.js<br/>buildCandidateView / buildGovernmentView"]
    ADP --> VC["Candidats — /candidats/:id"]
    IDX --> VG["Groupes — /groupes/:lignee<br/>LigneeProfile.jsx, sans adaptateur"]
    ADP --> VO["Gouvernement — GovernmentProfilePage.jsx"]
    CVR --> VCV["Sources — /sources"]
```

- **`<id>.paroles.json`, une par gouvernement (#330)** — le détail d'un sujet de
  parole : pour chaque intitulé de débat, les membres qui y sont intervenus,
  leurs dates et leur nombre de tours de parole. Écrite par
  `scripts/vue-parole-gouvernement.mjs`, **chargée au premier clic** et jamais
  avec la fiche (1,2 Mo pour les dix-sept). Elle ne porte **pas de verbatim** :
  les 205 profils de membres de gouvernement sont collectés en mode réduit au
  thème, et `texte` n'existe que sur les profils de candidats déclarés.
  Sa clé est celle de l'agrégat — `theme.strip().lower()`, comme
  `deriver_tags_thematiques` —, sans quoi aucun sujet ne se rapproche.
  **Depuis #1074 (22/09/2026), chaque membre y porte aussi `seances`** — la
  date de chaque séance et ses tours, `[[date, tours], …]` : sans elles, un
  intervalle `premiere`–`derniere` qui chevauche le début d'une fenêtre ne dit
  pas combien de tours tombent dedans (26 couples membre × débat sur 1 427 chez
  Lecornu II pour six mois). Individuel sans difficulté : la fiche publie déjà
  chaque ministre par son nom.
- **`donnees.json` (#1074)** — `{ "au": "AAAA-MM-JJ" }`, la date depuis laquelle
  les cases « 6 derniers mois » et « 12 derniers mois » se comptent. `sync-data`
  la lit sur la **`date_reference` des fiches de groupe**, la plus récente — là
  où Backend compte ses propres fenêtres (`fenetres_parole`, #1077) —, pour
  qu'une seule date vaille sur toutes les fiches. Sans date lisible, le fichier
  n'est pas écrit et les cases ne filtrent rien : aucune date n'est inventée.
- `sync-data.mjs` copie les artefacts vers `public/data/` (Vite ne sert pas de
  fichiers situés hors du dossier du projet) et génère `manifest.json`. Il
  **signale** l'absence de `scrutins.json`, de `pivot_data/amendements/`, de
  `commissions_dossiers.json` ou de `scrutins_dossiers.json` au lieu de la
  taire : sans les deux premiers, les votes et les amendements s'afficheraient
  vides ; sans le troisième, « L'essentiel » de la fiche candidat n'affiche pas
  la répartition des dossiers amendés par commission saisie au fond ; sans le
  quatrième, « Ce qu'il a voté » n'affiche ni la matière ni le sort final des
  textes votés (#328). Aucun des quatre n'est déduit d'un intitulé de dossier
  (§2 règle 1), et l'index illisible se distingue de l'entrée absente —
  `rattachementDisponible` dit « le fichier n'a pas pu être lu », ce qui n'est
  pas « ce texte n'a pas de commission saisie au fond » (même distinction que
  #510).
- **`couverture.json` est une projection, pas une huitième sortie du pivot**
  (#328). `scripts/couverture-corpus.mjs` lit `pivot_data/` au build et écrit
  32 Ko : ce que le dépôt porte, rangé par institution → liste → champ, avec les
  bornes déclarées et, par liste, les fiches où elle manque. Elle ne crée aucun
  fait — elle compte ce que les sorties de `pivot_data/` portent déjà. En faire une sortie de
  `pivot_data/` ajouterait un job, un cache et un budget CI pour un fichier que
  seule l'interface lit ; même raisonnement que la projection de lignée (#329).
  Depuis le 11/09/2026 il porte le **Parlement européen comme institution** à
  cinq listes, lues sur leurs marqueurs publiés (`scrutin_non_resolu.institution`,
  `amendement_non_resolu.institution`, `institution`, `source.institution`,
  `categorie_source`), et un bloc **`accueil`** — une borne par institution, et
  les fiches hors couverture (Sénat, aucun mandat, `mandats_anterieurs`) — que
  `/sources` lit depuis la forme C de l'accueil (#951), pour sa seule rubrique
  `anterieurs`. Depuis le 16/09/2026, `institutions[]` compte aussi les
  **mandats locaux** (`categorie: "mandat_local"`) sous la clé `local`, avec leur
  `borne` tirée de `mandats_locaux_couverture.borne_couverture`. Une `portee` européenne de profil n'y est jamais prise
  pour une borne : c'était le cas, et les votes de l'Assemblée commençaient en
  2004.
  Le fichier n'est **pas versionné** (`public/data/` est ignoré par git) et sa
  reconstruction est conditionnée aux dates de ses entrées : lire les quatre
  index d'amendements coûte 17 à 28 s, et le refaire à chaque `npm run dev`
  rendrait le démarrage insupportable.
- **La page de groupe lit une projection de lignée, pas une fiche** (#329).
  L'interface publie une fiche par LIGNÉE déclarée (`pivot_data/lignees/`,
  #836) ; `scripts/vue-lignee.mjs` en écrit, au build, ce que la page lit —
  ~1 Mo pour la lignée socialiste, contre 5,3 Mo de fiche de lignée et 11 Mo de
  maillons —, calculé par les règles de `src/utils/groupe.js` et
  `src/utils/lignee.js` que le navigateur importe aussi. Les fiches de lignée ne
  sont pas copiées ; les projections de comparaison par législature
  (`comparaison-groupes.mjs`) ne sont plus servies, elles sont lues en mémoire.
  **Les débats complets d'une lignée** s'écrivent à côté, dans
  `public/data/lignees/<id>.debats.json` (#979) : la projection ne porte que les
  dix débats les plus portés de chaque groupe, la recherche sur la fiche doit
  les couvrir tous. `[intitulé, porteurs]` et un dénominateur par groupe —
  1,0 Mo pour les douze lignées, 115 Ko pour la socialiste (mesuré le
  17/09/2026) —, chargé par la page au premier mot tapé seulement.
  `scripts/amendements-lignees.mjs` y ajoute les amendements de chaque maillon
  par commission saisie au fond, relus dans les profils et l'index, et ne sert
  la répartition d'un type de déposant que si elle **retombe sur le total
  publié** par la fiche. La même passe relève les **textes portés** des membres
  dans la législature du maillon — un dossier une fois, au stade le plus
  avancé (`textesDuMaillon`) —, que la page dessine avec la cascade de la fiche
  candidat ; aucune fiche de groupe ne publie cet agrégat. Chaque maillon porte
  aussi ses `signalements`, ce que sa fiche signale d'elle-même (section 6). Cache sur les dates, comme `couverture.json` : 59 s et
  1,2 Gio de RSS pour tout `sync-data` à froid, mesurés le 11/09/2026.
- Le manifeste liste les candidats **déclarés** de `raw_data/candidats.json`,
  filtrés sur l'existence d'un profil sur disque — ne pas fabriquer la promesse
  d'une page absente. `groupIds[]` est rattaché par candidat pour permettre le
  filtrage côté client sans télécharger les fiches de groupe (certaines dépassent
  500 Ko).
- `src/data/index.js` expose l'API de fetch (`getCandidateProfile`,
  `getLigneeProfile`, `getCandidatesList`, `getGroupsList`) ;
  `src/data/pivotAdapter.js` transforme le pivot d'un candidat ou d'un
  gouvernement en objets d'affichage. `getGroupsList` rend une entrée par
  lignée ; une adresse de fiche par législature (`/groupes/AN-SOC-17`) mène à
  sa lignée.
- Les trois onglets sont **Candidats**, **Groupes**, **Gouvernement**. Il n'y a
  pas d'onglet Partis, et il n'y a plus de `pivot_data/partis/` : la sortie a été
  retirée avec #906, faute de lecteur.

## Contrôles

**`src/check_quality_gate.py` est le seul gate bloquant**, exécuté avant le
commit de données. Ses sections, dans l'ordre :

| Section | Ce qu'elle contrôle | Bloquant ? |
|---|---|---|
| 1 | `IncompleteRead` dans les profils pivot, groupes, gouvernements et profils bruts, contre un seuil | oui, au-delà du seuil |
| 2 | Couverture candidats (`raw_data/candidats.json` vs profils pivot) | non |
| 3 / 3b | Interventions faibles ; couverture Syceron | non |
| 3c / 3d | Couverture amendements AN ; fraîcheur de l'index | non (#378) |
| 3e | **Format** des index amendements figés — un index keyé par `numero` attribue des amendements au mauvais texte, ce n'est pas une donnée simplement périmée | **oui** |
| 4 | Groupes : fichier manquant, JSON invalide, schéma invalide (dur) ; effectif et couverture (souple) | oui sur le dur |
| 5 | Gouvernements — miroir de la §4 : fichier manquant, JSON invalide, schéma invalide (dur) ; couverture ministérielle, `textes[]` vide sur une période **couverte** par les archives, `IncompleteRead` (souple) | oui sur le dur |
| 5b | Correspondance slug ↔ acteur AN (`raw_data/correspondance_acteurs_an.json`) | **oui** |
| 6 | Couverture ParlTrack (optionnelle) | non |
| 7 | Garde-fou taille de blob (#580) : avertit à 50 Mio, **échoue à 80 Mio** | oui à 80 Mio |

Un gouvernement **hors couverture** des archives de dossiers n'est pas signalé
comme un défaut mais porté en information : l'absence y vient de la source, pas
des données (#399, AGENTS.md §2.5).

Les quatre contrôles supplémentaires exécutés avant le commit dans le job
`merge-and-pivot` — perte, intégrité référentielle, collecté/non publié,
collecté vs publié — sont décrits dans
[`workflow-generate-data.md`](./workflow-generate-data.md).

### Audits internes (manuels, jamais en CI)

Distincts du gate, sans score ni classement (AGENTS.md §2.1) :

- `src/audit_pivot_dataset.py` — `pivot_data/profiles`
- `src/audit_groupe_dataset.py` — `pivot_data/groupes` (volumétrie, complétude,
  cohérence, fraîcheur des sources, warnings agrégés, tableau croisé des volumes
  par groupe : membres, `cohesion_votes`, `tags_thematiques_agreges`,
  `amendements_agreges`)
- `src/audit_gouvernement_dataset.py` — `pivot_data/gouvernements` (mêmes axes,
  plus la présence de `premier_ministre`, le taux de `membres[].portefeuille`
  renseigné et les `comptages.par_statut` agrégés)
- `src/audit_pipeline.py` — point d'entrée manuel qui exécute **les trois**
  ci-dessus en appelant directement leurs fonctions (pas de sous-processus) et
  compile une « vue d'ensemble » : totaux audités, erreurs de lecture et warnings
  agrégés. Pure composition des rapports, aucune logique de calcul nouvelle.

`audit_pipeline.py` n'est **pas** intégré à `.github/workflows/generate-data.yml`
— choix explicite (#178) : usage manuel uniquement.

Les commandes de ces quatre audits, et celle qui régénère un rapport d'exemple
sur les fixtures figées plutôt que de lire un exemple committé (une commande ne
peut pas être périmée, un fichier figé si) : [`commandes.md`](./commandes.md),
section « Auditer ».

## Les commandes

Toutes regroupées par intention dans **[`commandes.md`](./commandes.md)** :
générer, auditer, vérifier avant de committer, opérer, voir ce que voit
l'utilisatrice.

Une seule mérite d'être rappelée ici, parce que c'est **l'ordre** qui compte et
qu'il est expliqué plus haut : quand un run a été interrompu, les deux index
partagés se reconstruisent à la main, les scrutins **avant** la passe pivot et
les amendements **après**.

```bash
python3 src/build_scrutins_index.py
python3 src/build_amendements_index_pivot.py
```

La table des commissions saisies au fond (#328) est indépendante des deux : elle
dérive du référentiel, pas du corpus, et se reconstruit quand on veut.

```bash
python3 src/build_commissions_dossiers.py
```

Les deux fusionnent additivement avec l'existant ; `--no-merge` reconstruit à
partir de zéro et exige donc le corpus **complet**.
