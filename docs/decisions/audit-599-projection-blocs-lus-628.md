<a id="audit-599-projection-blocs-lus-628"></a>
# Un audit lit le corpus par projection, et son plafond de mémoire est dans un test (#628, 2026-08-30)

`2026-08-30`

> **En bref** — l'audit de #599, livré « rejouable », rangeait chaque profil entier dans un dict par slug (~3,9 Gio de pic, `exit 137` sur une machine à 4 Gio et swap saturé) alors que ses mesures ne lisent que `identite`, `identifiants`, `meta` et le cardinal des listes — 0,39 Mo sur 681,6 ; pic ramené à 113 Mio, rapport prouvé identique sur quatre quarts disjoints du corpus, et le plafond est désormais déduit dans le test du poids sur disque des blocs à relâcher.

## Contexte

`scripts/audit_fusion_blocs_599.py` a été livré par #599 comme **rejouable** :
c'est lui qui devait fournir la mesure « après » au critère de sortie de l'épic
#598. Le 30/08/2026 il ne rendait plus de rapport :

```
$ .venv/bin/python scripts/audit_fusion_blocs_599.py
Processus arrêté
code de sortie: 137          ← SIGKILL, tué par le noyau faute de mémoire
```

**Le code n'avait pas changé, la machine si** : 7,6 Gio de RAM dont 4,0
disponibles, **swap saturé** (2,0 Gio sur 2,0, 45 Mio libres). Sans soupape de
pagination, une demande de mémoire ne ralentit pas le système, elle fait choisir
une victime. Le défaut était donc **latent depuis le premier jour**, pas
intermittent : l'audit passait le 30/08 à 10:52 et 11:44 parce que la machine
était reposée.

## La cause : la bonne discipline d'un côté, pas de l'autre

Le script faisait deux lectures de corpus, et une seule était prudente.

| Lecture | Méthode d'origine | Ce que ça retenait |
| --- | --- | ---: |
| Profils **bruts** | `profil_brut.charger_socle` — le socle seul, sans les amendements (#580) | 1,29 Gio |
| Profils **pivot** | `json.loads(chemin.read_text())` en boucle, **accumulés dans un dict par slug** | ~2,6 Gio |

L'énoncé de #628 dit « le brut est léger, correct ». **Il ne l'est pas** :
mesuré, le dictionnaire des 481 socles pèse 1,29 Gio à lui seul. Le socle est
allégé de ses amendements par #580, mais il porte encore `votes`, `mandats` et
`interventions` — et l'audit les retenait entiers pour n'en lire que le
cardinal.

C'est le motif de [[oom-lecture-amendements-par-candidat]] reproduit sur un
chemin neuf : **623 Mo de JSON sur disque ne tiennent pas dans 4 Gio**. Une
liste de petits dictionnaires occupe bien plus que le texte qui la décrit —
chaque `dict`, chaque clé, chaque chaîne porte son en-tête Python. Facteur de
gonflement **mesuré ici : × 4,2** (1 253 Mio de RSS pour 312 Mo de JSON lus).

## Ce que les mesures lisent réellement

Relevé dans le code, pas dans l'énoncé — #628 citait aussi `couverture`, qu'**aucune
mesure n'ouvre** :

| Côté | Bloc | Qui le lit |
| --- | --- | --- |
| pivot | `identite` | mesure 1 (`pivot_identite_absente`, `pivot_champ_perdu`) |
| pivot | `identifiants.hatvp` | mesure 1 (`hatvp_incoherent`) |
| pivot | `meta.warnings` | mesure 2 (warnings du brut non publiés) |
| brut | `identite` | mesure 1 |
| brut | `meta` | mesures 2 et 3 |
| brut | `votes`, `mandats`, `interventions`, `dossiers_legislatifs` | **leur cardinal seul** — « y en a-t-il ? », « combien ? » |

Sur le corpus committé du 30/08/2026, ces blocs pèsent **0,39 Mo sur les
681,6 Mo** que porte `pivot_data/profiles` — **0,06 %**. Le reste :
`amendements` 577,3 Mo, `votes` 67,1, `interventions` 22,2, `mandats` 12,6,
`couverture` 1,6.

## Décision

**Un audit qui parcourt un corpus le lit par projection.** Un document est lu,
réduit aux blocs que les mesures ouvrent, puis relâché — jamais rangé entier
dans une liste ni dans un dictionnaire indexé par slug.

Concrètement, dans `charger_corpus` :

- `BLOCS_PIVOT_LUS` et `BLOCS_BRUT_LUS` déclarent la liste blanche des blocs
  retenus ; ajouter une mesure qui lit un autre bloc, c'est ajouter ce bloc là ;
- des quatre listes parlementaires du socle, seul le **cardinal** est gardé
  (`nombre_d_entrees`, qui accepte la liste comme le décompte pour que les tests
  puissent continuer à nourrir les mesures avec de vraies listes) ;
- le `json.loads` complet **reste nécessaire** — un profil est écrit compact,
  sur une seule ligne (#433), il n'y a pas de lecture incrémentale sans
  dépendance nouvelle. Ce qui change est la **durée de vie** : le document
  entier est local à `_lire_pivot` et meurt à son retour.

## Ce que ça change, mesuré

| | Avant | Après |
| --- | ---: | ---: |
| Pic RSS, corpus committé (481 profils, 651 Mo) | **~3,9 Gio** extrapolé — plafond de 2,5 Gio touché au 234ᵉ pivot sur 481 | **113 Mio** |
| Verdict sur une machine à 4 Gio disponibles | `exit 137`, aucun rapport | rapport rendu en 11 s |
| Rapport produit | — | **identique** |

L'identité du rapport est prouvée, pas supposée. La version d'avant ne tenant
pas en mémoire sur le corpus entier, elle a été rejouée sur **quatre quarts
disjoints** de slugs dont l'union est le corpus (121 + 120 + 120 + 120 = 481),
et comparée quart par quart à la version d'après sur le même quart : rapports
**identiques** sur les quatre, hors `genere_le`.

`audit/fusion_blocs_599_avant.json`, lui, ne peut pas servir de référence : il
a été produit sur le corpus du **29/08** et committé (d30e1774, 30/08 18:28)
après le commit de données `8e2d3030` (30/08 11:42) qui l'a périmé. Son
`dernier_run` dit `2026-08-29` quand le corpus committé à côté de lui dit
`2026-08-30`, et son unique profil touché en mesure 1
(`jean-luc-melenchon`) porte depuis une identité AN complète. La ligne de base
« avant » de l'épic #598 décrit donc un corpus qui n'est plus celui du dépôt —
c'est un constat, pas une correction : réécrire une mesure « avant » lui
retirerait ce qu'elle vaut.

## Le plafond est dans un test, et il est déduit d'une règle

Sans test, le script repasserait sous le seuil au prochain ajout et on ne
l'apprendrait qu'en le relançant, sur une machine chargée, le jour où on en a
besoin. Trois exigences, et une contrainte qui commande la forme :

1. **Mesurer la mémoire réellement consommée** — `resource.getrusage(RUSAGE_SELF).ru_maxrss`,
   le pic du processus, sans dépendance externe. Dans un **sous-processus** :
   `ru_maxrss` est un maximum historique, et mesuré depuis pytest il porterait
   le pic de tous les tests déjà passés.
2. **Un plafond déclaré, pas ajusté à l'observation.** Un plafond relevé sur une
   exécution puis arrondi suit la dérive qu'il doit signaler. Celui-ci est une
   **règle** : *la croissance mémoire de l'audit doit rester sous le poids en
   octets, sur disque, des blocs qu'il lit et ne doit pas garder.* Le
   raisonnement tient en une ligne — la désérialisation JSON ne réduit jamais ;
   si l'audit croît de moins que le texte qu'il a lu, il ne peut pas le détenir.
3. **La CI ne télécharge pas le corpus** : `pivot_data` est hors de la liste
   blanche du sparse-checkout de `tests.yml`, et le garde-fou #473 échoue s'il
   réapparaît. La mesure porte donc sur des **fixtures**.

**Pourquoi un plafond mesuré sur fixtures vaut quelque chose.** Le défaut de
#628 n'est pas un défaut de volume, c'est un défaut de **rétention**, et la
rétention ne dépend pas de l'échelle : un chargeur qui range les documents
entiers les range à toutes les tailles. Le corpus-fixture (24 profils, 81 Mio
de blocs lourds) est bâti pour rendre le comportement impossible à manquer, et
ses entrées sont **petites** — un mapping à deux clés, la forme réelle depuis
#431 et #432 — parce que c'est cette forme-là qui gonfle d'un facteur 4. Rejoué
sur la version d'avant : **345 Mio de croissance pour un plafond de 81** ; sur
la version d'après : **0,0 Mio**, le pic de l'audit ne dépassant même pas celui
de ses propres imports. Le garde-fou sépare d'un facteur 4,3 — il ne passe pas
toujours, ce qui était la condition pour l'écrire.

Ce que ce test **ne** prouve pas, et le dit : ni la vitesse, ni le pic absolu
sur le corpus réel (mesuré ici, 113 Mio, et nulle part en CI). Un plancher
(`PLANCHER_POIDS_RELACHE`, 40 Mio) refuse le verdict si quelqu'un rétrécit les
fixtures jusqu'à ce que le plafond qu'elles déduisent ne prouve plus rien.

## Ce qui n'est pas corrigé ici, et ce que ça pèse

Le balayage de `src/` et `scripts/` (analyse AST des boucles sur
`glob("*.pivot.json")` dont le document chargé survit à l'itération) a trouvé
**trois autres accumulations**, laissées en l'état — elles n'entrent pas dans
#628 et deux d'entre elles ont sans doute besoin des listes qu'elles gardent :

| Endroit | Ce qu'elle accumule | Volume mesuré |
| --- | --- | ---: |
| `src/gouvernement_roster.py:load_profils_from_dir` | **tout** `pivot_data/profiles` dans une `list` — appelée par `generate_gouvernement_profiles.py`, `gouvernement_profile.py` et sa propre CLI | **2,42 Gio** extrapolés (plafond de 2,0 Gio touché au 381ᵉ profil sur 481, facteur × 3,79) |
| `src/audit_pivot_dataset.py` (chargement) | idem, tout le corpus dans une `list` | même ordre |
| `src/group_profile.py:generate_groupe_profile_from_roster` | les profils **entiers** du roster d'un groupe | jusqu'à **0,81 Gio** pour une seule fiche (LFI-NFP, 56 membres, 206 Mo sur disque) |

Les trois loups sont les mêmes : `check_quality_gate.py`, lui, fait déjà bien —
ses trois boucles sur le corpus n'accumulent que des lignes de synthèse et
relâchent le document à chaque tour.

## Alternatives écartées

- **Mémoïser ou augmenter le plafond.** [[oom-lecture-amendements-par-candidat]]
  a déjà mesuré qu'un cache non borné aggrave le cas ; et « relever le seuil »
  n'est pas un remède disponible dans ce dépôt (§3a, garde-fou blob #580).
- **Un parseur JSON incrémental** (`ijson`) pour ne désérialiser que les blocs
  utiles. Une dépendance de plus pour un gain que la projection obtient déjà :
  le pic est descendu à 113 Mio, dont le coût transitoire d'un seul document
  (7 Mo au plus gros) est une part négligeable.
- **Retenir `couverture` « au cas où ».** Un bloc gardé qu'aucune mesure
  n'ouvre est une donnée morte : elle ne coûte rien aujourd'hui et ment demain
  sur ce que l'audit lit.
