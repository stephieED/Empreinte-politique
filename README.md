# EMPREINTE POLITIQUE

![Projet en construction](https://img.shields.io/badge/PROJET-EN%20CONSTRUCTION-00E5FF?style=for-the-badge&labelColor=17141F)

> [!WARNING]
> **Ce projet est en construction.** Le pipeline et l'interface évoluent
> quotidiennement. Les données publiées sont réelles et sourcées, mais peuvent
> être incomplètes, et certaines absences portent encore une explication
> imprécise — ne pas conclure d'une liste vide sans lire son bloc `couverture`.
>
> L'état courant se lit dans les
> [issues ouvertes](https://github.com/stephieED/Empreinte-politique-src/issues).

**Empreinte politique** produit des « CV politiques » factuels et sourcés —
mandats, responsabilités, votes, textes portés, interventions en séance — pour
les candidats à l'élection présidentielle française de 2027, ainsi que pour les
groupes parlementaires et les gouvernements réels.

**Principe directeur** : tout fait affiché doit être traçable jusqu'à une source
primaire (un scrutin officiel, un dossier législatif, une révision précise de
Wikipédia). Le projet ne porte aucun jugement de valeur.

---

## Ce qu'on n'y trouvera pas

C'est ce qui distingue ce projet, et ce sont des règles non négociables,
dupliquées dans le schéma, dans la validation et dans la page méthodologie :

1. **Aucun jugement de valeur, aucun score, aucun classement.**
2. **Traçabilité intégrale** : chaque fait renvoie à une source primaire.
3. **Aucun taux de présence individuel n'est jamais publié.**
4. **Un 49.3 n'est jamais traité comme une position de vote** — c'est un fait de
   procédure, présenté comme tel.
5. **Une donnée manquante reste manquante**, jamais un `0` par défaut. Une liste
   vide se lit avec son bloc `couverture`, jamais toute seule.
6. Une position dans l'hémicycle exige une `source_url` vérifiable.
7. **Un ratio de groupe n'est publié qu'avec son numérateur, son dénominateur et
   une couverture suffisante** ; sinon `N/D`. Les écarts individu ↔ groupe sont
   du contrôle qualité interne, jamais public.
8. Les étiquettes thématiques sont des aides à la lecture, pas des positions
   déclarées par le candidat.

Le détail et le raisonnement : [`AGENTS.md`](AGENTS.md) §2 et §6.

## D'où viennent les données

| Source | Ce qu'elle apporte | Cadence | Licence |
|---|---|---|---|
| [Open data de l'Assemblée nationale](https://data.assemblee-nationale.fr/) | **La seule source de l'activité parlementaire française** depuis #529 : identité, mandats, votes, amendements, dossiers, comptes rendus Syceron, questions | quotidienne | Licence Ouverte (Etalab) — attribution |
| [Open data du Sénat](https://data.senat.fr/) | **Les appartenances sénatoriales seulement** depuis #885 — mandats, groupes, commissions, datés au jour près. Le jeu ne porte **ni scrutin ni compte rendu** : l'activité en séance n'est pas publiée | à chaque run | Licence Ouverte 2.0 (Etalab) — attribution |
| [Parltrack](https://parltrack.org) | Le volet européen des anciens eurodéputés | hebdomadaire (environ) | ODbL v1.0 — **partage à l'identique** |
| [Parlement européen](https://data.europarl.europa.eu/) | Le mandat européen | en direct, à chaque run | CC BY 4.0 — attribution, `User-Agent` identifiant le réutilisateur, 500 requêtes / 5 min |
| [EuroVoc](https://publications.europa.eu/webapi/rdf/sparql) | Le **nom français** d'une matière européenne, quand le Parlement n'en donne que l'identifiant, et son **domaine** (« 08 RELATIONS INTERNATIONALES »), lu dans le thésaurus | en direct, à chaque run | CC BY 4.0 — attribution, et indication des modifications |
| [Sycomore](https://www2.assemblee-nationale.fr/sycomore/recherche) (Assemblée nationale) | **Citée, pas collectée** : les mandats de député antérieurs au 19/06/2002, relus à la main un par un (#860) | aucune — table relue | tous droits réservés — **seuls des faits** (fonction, dates) repris, avec leur lien |
| Journal officiel ([Légifrance](https://www.legifrance.gouv.fr/)) | **Cité, pas collecté** : les fonctions gouvernementales antérieures au corpus, décret par décret (#860) | aucune — table relue | Licence Ouverte 2.0 (Etalab) — attribution |
| [Répertoire national des élus](https://www.data.gouv.fr/datasets/repertoire-national-des-elus-1) + sortants 2026 | **Les mandats locaux** des candidats déclarés depuis #922 — municipaux, maires, départementaux, régionaux, communautaires. La couverture **commence en 2020** ; avant, l'absence est déclarée et jamais lue comme « aucun mandat ». La source ne publie **aucune date de fin** | à chaque run, par l'API tabulaire | Licence Ouverte 2.0 (Etalab) — attribution |
| Wikipédia / Wikidata | Le suivi des candidatures déclarées | immédiate | CC BY-SA 4.0 / CC0 |
| [Conseil constitutionnel](https://www.conseil-constitutionnel.fr/) | **À venir** : la liste officielle des candidats et les parrainages, qui remplaceront Wikipédia pour dire qui est candidat. La loi du 6/11/1962 (art. 3) fixe les bornes — parrainages publiés au moins deux fois par semaine jusqu'au 12/03/2027, liste au plus tard le 26/03/2027 ; aucune date n'est annoncée | — | non connue à ce jour |
| NosDéputés / NosSénateurs | **Plus collectées** depuis #528/#529, mais des champs déjà publiés en dérivent | — | ODbL v1.0 — **partage à l'identique** |

Le corpus **n'est pas** sous une licence unique, et avoir cessé de collecter
Regards Citoyens n'y a rien changé (#530) : chaque profil déclare dans
`meta.licence_donnees` les licences dont son propre contenu relève, dérivées de
ses `sources[]` par `src/licences.py`. Le site HTML est une « œuvre dérivée »
ODbL (attribution suffisante) ; une republication des données brutes
téléchargeables déclenche le partage à l'identique.
→ [`AGENTS.md`](AGENTS.md) §7, `docs/decisions/licence-lot-6-530.md`.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

`requirements-dev.txt` tire `requirements.txt` (les dépendances d'exécution) et
y ajoute `pytest`. Pour un environnement d'exécution seul — ce que font les jobs
d'extraction — installer `requirements.txt`.

Toutes les commandes se lancent **depuis la racine du dépôt**, environnement
virtuel activé.

## Une première chose à lancer

Le profil d'un candidat, brut puis pivot :

```bash
python3 src/generate_all_profiles.py --only jean-luc-melenchon --pivot
```

Puis l'interface, sur les données présentes en local :

```bash
cd web/UI_finale
npm install     # la première fois seulement
npm run dev     # synchronise les données puis démarre Vite
```

**Toutes les autres commandes du dépôt sont dans
[`docs/commandes.md`](docs/commandes.md)** — générer, auditer, vérifier avant de
committer, opérer, voir ce que voit l'utilisatrice. Une commande y est
documentée si l'on peut avoir à la lancer soi-même, et
`tests/test_commandes_documentees.py` vérifie à chaque run que ce fichier ne
cite ni un script disparu ni une option qui n'existe plus.

## Où vit quoi

```
raw_data/      Entrées déclaratives + collecte brute (proche de la source)
  candidats.json            la liste éditoriale des candidats déclarés
  groupes_reels.json        les groupes parlementaires à produire
  gouvernements_reels.json  les gouvernements à produire, lus dans AMO30 à chaque run
  profiles/                 <slug>.json + une tranche par législature (#580)
pivot_data/    Le format pivot — la SEULE couche que web/ lit
  profiles/       <slug>.pivot.json
  groupes/        groupe-<SIGLE>-<leg>.json
  gouvernements/  gouvernement-<ID>.json
  lignees/        une fiche par lignée de groupe — la seule que web/ lit (#836)
  scrutins.json   index partagé des scrutins de l'Assemblée (#432)
  scrutins_europeens.json  les scrutins du PE cités, avec leurs effectifs par groupe (#901)
  dossiers_europeens.json  référence de procédure → titre, stade, commission au fond (#901)
  amendements/    index partagé des amendements, un fichier par législature (#431)
src/           Le pipeline (collecte, normalisation, agrégation, audits, gate)
scripts/       Les scripts d'exploitation (run local, bornage, rendu du formulaire)
web/UI_finale/ L'interface de production : React 19 + Vite
web/old/       Les générations de design archivées (v1–v7)
docs/          La documentation (voir ci-dessous)
tests/         La suite pytest
```

`.cache/` et `logs/` sont créés automatiquement et git-ignorés.

Un profil pivot ne se lit **plus seul** : ses votes et ses amendements ne sont
que des renvois (`{scrutin_id, position}`, `{amendement_id, role_signataire}`)
vers les index partagés — deux pour l'Assemblée, deux pour le Parlement européen
depuis #901. Pourquoi, et ce que ça a fait gagner :
[`docs/data-architecture.md`](docs/data-architecture.md).

## Où aller pour le reste

| Question | Fichier |
|---|---|
| **« Quelle était la commande, déjà ? »** | [`docs/commandes.md`](docs/commandes.md) |
| **« Que devient la donnée ? »** — flux, schémas, les sorties de `pivot_data/`, volumétrie | [`docs/data-architecture.md`](docs/data-architecture.md) |
| **« Que fait un run ? »** — les dix jobs, le formulaire de lancement, caches, artifacts, budgets, le push, la relance automatique | [`docs/workflow-generate-data.md`](docs/workflow-generate-data.md) |
| **« Comment marche l'extraction pilotée par roster ? »** — le seul job qui a une page à lui, les neuf autres étant des blocs de la page ci-dessus | [`docs/extract-roster-groupes.md`](docs/extract-roster-groupes.md) |
| **« Pourquoi c'est fait comme ça ? »** — une décision par fichier | [`docs/decisions/`](docs/decisions/), indexées par [`docs/technical_decisions.md`](docs/technical_decisions.md) |
| **« Où cette source publie-t-elle ce champ ? »** — Assemblée, Sénat, ParlTrack et Parlement européen : les références qui dérivent avec leur fournisseur, pas avec notre code | [`docs/sources/`](docs/sources/) |
| **Les règles non négociables, pour un agent comme pour un humain** | [`AGENTS.md`](AGENTS.md) |
| **Ce qui est planifié, et les défauts connus restés ouverts** | [`ROADMAP.md`](ROADMAP.md) |

## Ce que la couverture ne couvre pas encore

Le site le publie, et pas seulement ce fichier : **[« Sources »](https://empreinte-politique.fr/#/sources)**
(`#/sources`, anciennement `#/couverture`) montre, pour les trois populations publiées, ce que le dépôt
porte et depuis quand, puis par liste les fiches où elle manque. L'accueil en
donnait une version courte jusqu'à sa forme C (#951), qui l'a retirée. Deux tiers des
limites de couverture étaient jusque-là recopiés à l'identique sous chaque fiche,
où ils se lisaient comme des faits sur la personne affichée (#328).
→ [`docs/decisions/page-couverture-commune-328.md`](docs/decisions/page-couverture-commune-328.md)

- **Groupes** : seuls les groupes déclarés dans
  `raw_data/groupes_reels.json` sont produits, pas tous ceux qui existent — une
  fiche par groupe **et par législature** (31 au 14/09/2026), que l'interface
  publie en **une page par lignée** : 14 pages, la suite des fiches d'un même
  groupe (#329, #836). Les **5 groupes de la XVIIe** y sont
  entrés le 01/09/2026 (#700) ; leurs fiches paraissent au premier run qui
  suit, et couvriront **305 des 461** membres, les autres n'ayant pas encore de
  correspondance slug ↔ acteur AN. Les **2 groupes du Sénat restent suspendus**
  depuis le 24/08/2026, et #885 ne les rouvre pas : le Sénat est rentré pour ses
  **appartenances**, pas pour son activité, et `data.senat.fr` ne porte aucun
  scrutin. Le cœur d'une fiche de groupe resterait donc vide. Leurs fiches
  publiées restent en place, gelées.
  → [`docs/decisions/fiches-groupe-17e-legislature-700.md`](docs/decisions/fiches-groupe-17e-legislature-700.md),
  [`docs/decisions/retrait-senat-528.md`](docs/decisions/retrait-senat-528.md),
  [`docs/decisions/extraction-groupe-suspendue-516.md`](docs/decisions/extraction-groupe-suspendue-516.md)
- **Gouvernements** : ceux que le référentiel AMO30 de l'Assemblée publie, soit
  **17 depuis Fillon I (17/05/2007)**, lus à chaque run (#996) ; pas toute la
  Ve République. Aucune fonction gouvernementale du corpus n'est antérieure au
  18/05/2007, et les
  mandats 2002-2007 de Xavier Bertrand manquent dans une période que sa fiche
  dit couverte : #859.
  **Leur composition est complète depuis le 18/09/2026** : les 205 membres qui
  n'avaient pas de profil ont été collectés, et les **650 personnes recensées
  sur les 17 fiches sont toutes rattachées** — par `organe_ref`, plus par
  comparaison de libellés entre deux sources (#996, lots 3 et 4).
  `membres[]` porte une entrée **par période**, pas par personne : un ministre
  qui change de portefeuille en a plusieurs. Les deux comptes sont publiés
  côte à côte, `comptages.membres_distincts` et `membres_recenses`, et
  `len(membres)` n'est ni l'un ni l'autre.
  `membres[].portefeuille` et `premier_ministre` restent `null` quand aucun
  pivot local ne les porte — jamais un « Ministre » générique ni un nom déduit
  du libellé du gouvernement.
  **Sur quoi les membres ont pris la parole** : `tags_thematiques_agreges`
  (#1020) ne retient que ce qui a été dit **pendant le passage de chacun**, pas
  pendant toute la période du gouvernement — sans quoi la parole d'un ministre
  de trois jours devenu président de l'Assemblée serait comptée comme celle du
  gouvernement. Sa couverture se lit dans `comptages.membres_avec_interventions`,
  et elle est partielle tant que tous les membres n'ont pas leurs interventions
  collectées.
- **Membres des groupes** : l'extraction pilotée par roster vise la couverture
  quasi complète des membres des groupes configurés, mais elle n'est pas encore
  atteinte. Tant qu'elle ne l'est pas, `web/UI_finale` affiche un état « pas de
  donnée » explicite plutôt qu'un zéro trompeur (règle 5).
  → [`docs/decisions/seuil-couverture-groupe.md`](docs/decisions/seuil-couverture-groupe.md)
- **Votes AN** : open data officiel, 14<sup>e</sup> à 17<sup>e</sup> législature
  selon les dumps disponibles.
- **Textes portés et textes d'un gouvernement** : les archives de dossiers
  législatifs de l'Assemblée, **XIV<sup>e</sup> à XVII<sup>e</sup>** depuis
  #1019 — la borne recule ainsi au **20/06/2012**, première séance de la XIV<sup>e</sup>.
  Les XII<sup>e</sup> et XIII<sup>e</sup> **ne sont pas publiées** (404 au
  18/09/2026) : les gouvernements **Fillon I, II et III** restent hors
  couverture, et leur `textes: []` est une absence de source, jamais « aucun
  texte porté ». **Ayrault I aussi**, sa période s'achevant avant l'ouverture
  de la XIV<sup>e</sup>. L'interface porte la même borne
  (`GOVERNMENT_TEXTS_COVERAGE_START`), et un test la tient alignée sur le code.
  → [`docs/decisions/archive-dossiers-xiv-1019.md`](docs/decisions/archive-dossiers-xiv-1019.md)
- **Sénat** : **les appartenances, jamais l'activité** (#885, 13/09/2026). Le job
  `extract-senat` collecte mandats, groupes et commissions depuis `data.senat.fr`,
  datés au jour près — 133 appartenances sur 2 candidats déclarés. Le jeu ne porte
  **ni scrutin ni compte rendu** : la condition 2 de #528 §7 est **déclarée non
  remplie**, pas contournée, et les fiches de groupe sénatorial publient toujours
  0 vote de cohésion. La chambre `senateurs` du roster reste suspendue.
  → [`docs/decisions/reouverture-partielle-senat-885.md`](docs/decisions/reouverture-partielle-senat-885.md)
- **Parlement européen** : collecté via ParlTrack et le portail officiel, et lu
  comme une **institution à part entière** sur la fiche — **7 des 32 candidats
  déclarés** y ont siégé, et pour certains c'est **tout** leur mandat
  parlementaire. Les cinq listes sont publiées, et depuis #1007 les trois
  figures européennes se lisent comme leurs jumelles françaises, derrière le
  même commutateur : textes portés, amendements et **votes**.
  Ce que la fiche y range et comment, en une ligne chacun :
  **un texte, une position** — par dossier, le dernier scrutin, date puis rang
  dans la séance, faute de notion de lecture dans la nomenclature européenne ;
  **un thème** — les domaines EuroVoc du dossier, à défaut ses familles OEIL,
  jamais déduits d'un intitulé ; **une couleur par thème**, la même d'une figure
  et d'une fiche à l'autre.
  Quatre limites déclarées : les interventions et textes antérieurs au
  22/11/2016 portent la date de leur **republication** par ParlTrack, pas celle
  de la séance (#858) ; aucun dump ne porte le **sort** d'un amendement ni
  l'issue d'un dossier ; la section « Où il s'est écarté des siens » n'a aucune
  fiche de groupe européenne à quoi se comparer, et ne sera pas transposée ; et
  la couverture EuroVoc des dossiers **monte d'un run à l'autre** — un dossier
  que la collecte n'a pas encore interrogé n'est pas un dossier sans thème, sa
  famille OEIL le range en attendant (§2 règle 5).
  → [`docs/decisions/institution-dimension-de-la-fiche-328.md`](docs/decisions/institution-dimension-de-la-fiche-328.md),
  [`docs/decisions/lecture-europeenne-themes-et-votes-901.md`](docs/decisions/lecture-europeenne-themes-et-votes-901.md),
  [`docs/decisions/pas-d-ecarts-groupe-europeens-901.md`](docs/decisions/pas-d-ecarts-groupe-europeens-901.md),
  [`docs/sources/parltrack-et-europarl.md`](docs/sources/parltrack-et-europarl.md)
- **Interventions** : Syceron est la seule source depuis #529, et sa résolution
  d'identifiants d'acteur nus reste livrée inactive (#510) — une collecte
  fraîche ne rend donc que les questions officielles. Les prises de parole déjà
  publiées sont conservées par la fusion additive.
- **Mandats locaux** : publiés depuis #922 — **35 mandats sur 15 profils**,
  mesuré le 18/09/2026. Cette ligne disait « aucun n'est publié », ce que la
  table des sources ci-dessus contredisait quinze lignes plus haut. La
  couverture **commence en 2020** : les jeux complets de 2014 et 2020 ne
  déclarent aucune licence, et une absence avant cette borne se lit « non
  couvert », jamais « aucun mandat local ». La source ne publie **aucune date
  de fin** (#966). Le **portefeuille ministériel hors AN** reste, lui, hors
  périmètre.
  → [`docs/decisions/collecte-mandats-locaux-rne-922.md`](docs/decisions/collecte-mandats-locaux-rne-922.md),
  [`docs/decisions/hors-perimetre.md`](docs/decisions/hors-perimetre.md)
- **Biais de couverture** : un ancien parlementaire laisse des traces bien plus
  riches qu'un candidat qui ne l'a jamais été.

## Tests

```bash
pytest -q
```

La suite tourne en un peu plus d'une minute (**5 041 tests**, 79 s au 14/09/2026) et s'exécute sur chaque pull request
et chaque push sur `main` (`.github/workflows/tests.yml`). Elle est **découplée
du corpus vivant** : aucun test ne lit `pivot_data/` ni `raw_data/profiles/`,
aucun n'écrit sous l'un des deux, aucun ne sort sur le réseau (#473). Le job CI
le rend structurel — il ne pose sur le disque du runner qu'une liste blanche de
chemins, si bien qu'un test qui se recouplerait au corpus y échoue en nommant le
fichier. Les tests d'acceptation qui ont besoin de vrais profils lisent les
fixtures figées de `tests/fixtures/`.
→ [`docs/decisions/ci-tests-pytest.md`](docs/decisions/ci-tests-pytest.md)

## Neutralité éditoriale

Ce projet agrège des faits et des sources primaires. Il ne produit ni classement,
ni score, ni appréciation des positions politiques. L'ensemble des règles :
[`AGENTS.md`](AGENTS.md).

## Licence

**Le code est sous AGPL-3.0** ([`LICENSE`](LICENSE)) : utilisable, modifiable et
redistribuable, à une condition — qui met en ligne un service fondé sur une
version modifiée doit en publier le code sous la même licence.

**Les textes rédigés pour le site et la charte graphique sont tous droits
réservés** : une licence de logiciel porte sur le code, pas sur la prose ni sur
la marque.

**Les données, elles, gardent les licences de leurs sources** — et elles ne sont
pas les mêmes d'un champ à l'autre : l'obligation de partage à l'identique de
l'ODbL vit sur certains, pas sur tous (`AGENTS.md` §7, et
[`docs/decisions/licences.md`](docs/decisions/licences.md)). La licence du code
n'y change rien.
