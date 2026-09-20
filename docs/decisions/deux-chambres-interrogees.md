<a id="deux-chambres-interrogees"></a>
# Le passé sénatorial est un fait de carrière, pas une donnée d'activité : bicaméral pour les candidats seulement (#488) (2026-08-20)

`2026-08-20`

> **En bref** — les deux chambres ne sont interrogées que pour les candidats déclarés.

Sous-issue B de l'épic **#486**. Ne touche pas au schéma pivot (la chambre sur
chaque mandat est la sous-issue C), ne corrige pas le profil de Mélenchon
(#484), ne change aucune valeur de `chambre` publiée (sous-issue D).

## Le défaut

`generate_all_profiles.build_profile_any_chambre` retenait **la première chambre
qui rendait une identité** (`CHAMBRES = ["deputes", "senateurs"]`) et avalait
les échecs par un `except Exception: continue` qui n'écrivait qu'une ligne de
log. Deux conséquences, toutes deux observées :

1. un parlementaire présent des deux côtés est classé par **l'ordre de la
   boucle** — Retailleau, sénateur en exercice, publié `chambre: "AN"` ;
2. une **défaillance transitoire** réattribue la chambre publiée sans trace
   (Mélenchon, basculé de `AN` à `Senat`, #484).

## Le périmètre : la provenance, pas la chambre

La collecte bicamérale ne vaut que pour un profil de **candidat**
(`meta.provenance == "candidat_declare"`). Le partage est déjà dans les
données :

| Provenance | Profils (209) | Rôle |
| --- | ---: | --- |
| `candidat_declare` | **8** | le CV publié |
| `roster_groupe` | **201** | matière première d'agrégation groupe/gouvernement |

**Pourquoi ce n'est pas un arbitrage nouveau.** Aucun jeu de données Sénat
structuré n'est exploitable — pas de scrutins nominatifs, `ameli.zip` est un
dump SQL de 717 Mo, `dossiers-legislatifs.csv` n'a pas de champ auteur (§ *Senate
votes, amendments, sponsored texts*, reconfirmé pour la vue Gouvernement).
Conséquence directe, vérifiable dans le corpus : **aucun groupe sénatorial n'est
agrégé**. Les deux fichiers publiés le disent —
`groupe-Senat-LR.json` et `groupe-Senat-SER.json` portent `cohesion_votes: 0`,
là où `groupe-AN-REN-16.json` en porte 4 099.

Le passé sénatorial d'un membre de roster n'alimente donc **rien**. Le seul
usage légitime est **biographique**, sur un CV de candidat : « a été sénateur de
2004 à 2010 » est un fait de carrière, pas une donnée d'activité.

**La population réelle**, mesurée sur `raw_data/candidats.json` :

| | |
| --- | ---: |
| candidats déclarés | 13 |
| … à slug résolvable (seuls à atteindre la collecte FR) | **8** |
| … dont le slug figure au roster complet du Sénat | **2** |

Ces deux-là sont `jean-luc-melenchon` et `bruno-retailleau` — **exactement les
deux cas qui ont motivé l'épic**. Les 21 autres profils que le premier relevé de
cette issue signalait (Larcher, Deroche, Procaccia, Guené, Raynal, Mazars…) sont
tous `roster_groupe`, donc hors périmètre.

## Ce que coûtait la généralisation, et pourquoi elle est écartée

L'issue supposait qu'« un 404 est bon marché ». **C'est faux sur cette source**,
et c'est ce qui achève de justifier la restriction.

Mesuré le 20/08/2026 entre 14:45 et 14:55 UTC, avec le `User-Agent` et le
`TIMEOUT=15` du projet, en 7 requêtes (courtoisie : quelques requêtes suffisent
à établir un coût unitaire, le reste s'extrapole) :

| requête | statut | durée |
| --- | --- | --- |
| `/gabriel-attal/json` | 404 | 9,25 s |
| `/aurore-berge/json` | 404 | 15,91 s |
| `/bruno-retailleau/json` | 200 | 12,62 s |
| `/bruno-retailleau/votes/json` | 404 | 8,99 s |
| `/gabriel-attal/votes/json` | 404 | 10,56 s |
| `/jean-luc-melenchon/json` | 200 | 14,98 s |
| `/gabriel-attal/json` (2ᵉ passage) | 200 (page générique) | 10,20 s |

Médiane **≈ 10,6 s**, min 8,99 s, max 15,91 s. Une requête `curl` sur la même
URL a mis **66,7 s**, dont **63,3 s de poignée de main TLS** — la latence n'est
pas dans le transfert, elle est dans l'établissement de connexion.

Coût **par candidat**, mesuré de bout en bout avec le vrai code
(`fetch_identity` + `fetch_votes`, mode d'extraction léger) : `gabriel-attal`
**21,1 s / 2 requêtes**, `aurore-berge` **17,7 s / 2 requêtes**. Deux requêtes,
pas une : l'identité *et* les votes sont demandés au Sénat.

Ces chiffres sont un **majorant d'un mauvais jour** — `www.nosdeputes.fr` a
répondu en 12,3 s puis dépassé 120 s dans la même fenêtre, toute
l'infrastructure Regards Citoyens était dégradée. Mais la forme tient : sur ces
domaines, une réponse négative se compte en **secondes**.

D'où la projection, sur le seul job qui n'utilise pas `--source`,
**`extract-roster-groupes`** (752 membres, 8 shards, ~94 par shard) :

| | par candidat | par shard (94) | pleine échelle (752) |
| --- | --- | --- | --- |
| bicaméral généralisé au roster | +19,5 s | **+30,6 min** | **+4 h 04** |
| bicaméral restreint aux candidats | **0 s** | **0 s** | **0 s** |

Les 19,5 s se décomposent en ~19 s de réseau et **0,5 s de temporisation de
courtoisie** : `process_candidat` ne temporise que si la source publique a
réellement été appelée (#467). Généraliser l'appel Sénat **rendrait cette
temporisation due pour chaque membre**, c'est-à-dire réinstallerait exactement
ce que #467 avait supprimé (12,0 s pour 24 membres). Un shard roster tourne en
~200 s, dont ~130 s de frais fixes : la version généralisée multipliait son
temps d'extraction par ~40.

**La restriction de périmètre ramène ce surcoût à zéro sur le roster**, et à
16 requêtes au total sur les 8 candidats à slug.

## L'index d'existence : construit, mesuré, retiré

Une première version chargeait le roster complet du Sénat
(`archive.nossenateurs.fr/senateurs/json` — **1 requête, 1 357 entrées,
1,09 Mo, 9,53 s**, historique compris) et n'appelait le Sénat que pour les slugs
qui y figurent. À 752 membres c'était le bon geste : ÷10 sur le surcoût, même
motif que #369, #392 et #403.

À 8 candidats, l'arithmétique s'inverse :

| | requêtes | temps |
| --- | ---: | ---: |
| sans index | 8 × 2 = **16** | ~2 min 36 s |
| avec index | 1 + 2 × 2 = **5** | ~48 s |

L'index fait gagner **1 min 48 s** — sur un chemin qu'**aucun job CI n'emprunte**
(voir ci-dessous). En regard, il coûtait ~60 lignes, un cache de module, un
verrou, une distinction `None`/`frozenset()` à ne pas confondre, un troisième
type de warning, et surtout **un mode de défaillance neuf** : index injoignable
⇒ Sénat non interrogé, silencieusement si le warning n'est pas relu. Une
collecte conditionnelle de plus, dans une issue qui existe parce qu'un chemin
conditionnel a fait disparaître un fait.

**Retiré.** Pour un candidat, les deux chambres sont interrogées, sans
condition. La mesure, elle, reste : c'est elle qui établit que la
généralisation au roster n'était pas finançable.

## Une correction au diagnostic : en CI, la boucle n'est pas seule à décider

`grep generate_all_profiles.py .github/workflows/generate-data.yml` :
**aucun job n'exécute la commande sans `--source` sur `raw_data/candidats.json`.**
`extract-an` passe `--source an`, `extract-senat` `--source senat`,
`extract-ue-officiel` `--source ue`, `merge-and-pivot` `--pivot-only` ; seul
`extract-roster-groupes` omet `--source`, et il travaille sur
`raw_data/roster_candidats.json`.

Autrement dit, **en CI un candidat est déjà interrogé sur les deux chambres**,
par deux jobs scopés distincts, dont les profils bruts se rejoignent à la fusion
additive — où `merge_raw_profile` fait `chambre = _prefer_non_empty(new, old)`.
La chambre publiée d'un candidat y dépend donc aussi de **l'ordre d'arrivée des
artifacts**, pas seulement de la boucle corrigée ici.

Cette PR ne prétend pas régler ce second chemin : il relève de la sous-issue D
(`chambre` dérivée plutôt que collectée). Elle règle le chemin par défaut —
`--source all`, celui de toute exécution locale et de la valeur documentée du
drapeau — et rend le cas bicaméral **nommé** partout où il se produit.

## Ce que le profil publie

Deux types de warnings dans `meta.warnings` — donc dans le jeu de données
publié, pas seulement dans un log de run. Même modèle que #474 : le texte avant
le premier `:` est le *type* agrégé par
`audit_pivot_dataset.compute_agregation_warnings`.

| type | quand | portée |
| --- | --- | --- |
| `carrière sur deux chambres` | les deux chambres rendent une identité ; nomme l'autre chambre et sa `source` | candidats (structurellement impossible ailleurs) |
| `collecte de chambre en échec` | une chambre a levé une exception ; nomme la chambre et la raison | **tous les profils** |

Le second n'est **pas** restreint aux candidats, et c'est délibéré. Il ne se
déclenche que sur une exception réelle — jamais en régime nominal, donc jamais
en volume — et il signale une `chambre` publiée qu'une panne a choisie à notre
place. `chambre` est lu par `group_profile`, `check_quality_gate` et le contrôle
de perte de #470 : le taire sur les 201 profils de roster rétablirait, pour eux,
le silence exact que cette issue corrige (AGENTS.md §2.5). C'est l'inverse du
cas #474, où ne rien émettre sur les 92 parlementaires en mission était juste
parce que leur exclusion est le comportement **attendu**.

Les deux cas que l'issue demandait de distinguer le sont : « aucune chambre ne
répond » reste le statut `introuvable` (déjà géré), « une échoue, l'autre
répond » produit le warning nommé.

## Quand les deux chambres répondent : convention d'ordre, dite explicitement

C'est le cas Retailleau, et il fallait bien écrire quelque chose dans `chambre`
tant que la sous-issue C n'a pas porté la chambre sur chaque mandat.

**La première chambre de `chambres` est retenue** — `deputes`, donc `chambre:
"AN"`. La valeur publiée ne change pas ; ce qui change, c'est qu'elle cesse
d'être muette : le profil dit qu'une identité existe des deux côtés, nomme
l'autre source, et dit que « AN » vient d'une **convention d'ordre de collecte**
et non d'une comparaison des mandats.

L'alternative — dériver la chambre du mandat en cours, ce qui ferait basculer
Retailleau sur `Senat` — a été écartée pour la raison même que l'épic énonce :
elle **effacerait sa carrière de député** comme on efface aujourd'hui son mandat
sénatorial. On remplacerait un fait faux par un autre.

## Le risque `group_profile`, instruit et mesuré : exposition nulle

`group_profile._member_eligibility_intervals` retient **tous** les
`mandat_electif` sans distinction de chambre, et `_is_eligible_at` est une
**union** d'intervalles. Un mandat sénatorial ajouté à un profil de membre
élargirait donc sa fenêtre d'éligibilité, et le compterait absent sur des
scrutins AN postérieurs à son départ de l'Assemblée. Le cas dangereux est
étroit — un mandat Sénat ne peut pas chevaucher un mandat AN (incompatibilité
constitutionnelle) — mais réel : **un changement de chambre en cours de
législature**.

Il faut pour cela un profil **à la fois candidat et membre d'un groupe publié**.
Mesuré sur les 7 groupes du corpus :

| candidat | groupe | `cohesion_votes` | connu du Sénat |
| --- | --- | ---: | --- |
| `gabriel-attal` | `groupe-AN-REN-16` | 4 099 | **non** |
| `marine-le-pen` | `groupe-AN-RN-16` | 3 405 | **non** |
| `jerome-guedj` | `groupe-AN-SOC-16` | 814 | **non** |
| `bruno-retailleau` | `groupe-Senat-LR` | **0** | oui |

**Exposition nulle**, pour deux raisons indépendantes :

1. les trois candidats dont le groupe a un dénominateur de cohésion réel ne
   sont **pas** connus du Sénat — aucun mandat sénatorial ne peut leur être
   ajouté ;
2. le seul bicaméral, Retailleau, appartient à un groupe sénatorial dont
   `cohesion_votes` vaut 0, et son unique `mandat_electif` publié
   (2004-09-26 → `null`) **est déjà** le mandat sénatorial.

Et surtout : **cette PR n'ajoute aucun mandat à aucun profil.** Le profil de la
seconde chambre est collecté puis abandonné ; seul un warning en sort. Le risque
appartient à la sous-issue C, celle qui fusionnera réellement les mandats des
deux chambres. Verrouillé par
`test_le_profil_de_lautre_chambre_nest_pas_fusionne`.

*(Un chiffre de 224 scrutins avait d'abord circulé sur Mazars : il était calculé
contre les 17 535 scrutins de l'index entier, alors que `cohesion_votes` est
strictement borné à une législature — `groupe-AN-SOC-16.json` ne contient que
des `an:16:*`, 814 entrées. Le risque réel est celui décrit ci-dessus, et il est
nul aujourd'hui.)*

## Interaction avec `build_minimal_profile`, signalée et non corrigée

Quand la collecte FR échoue entièrement et qu'un mandat européen existe,
`build_minimal_profile` écrit un squelette (`chambre: None`, `identite` à six
champs vides). #484 a montré la suite : la fusion additive garde l'ancienne
`chambre` non-null (`_prefer_non_empty`) tandis que le squelette, *truthy*,
écrase une `identite` réelle — la chambre est collante, l'identité ne l'est pas.

Cette issue **ne corrige pas cette asymétrie** (c'est #484), mais elle empêche
l'échec d'être muet : les warnings `collecte de chambre en échec` partent
désormais avec le squelette dans le profil brut. **Limite assumée** : sur ce
chemin `chambre` vaut `None`, donc le pivot est construit par
`normalize_europarl`, qui ne relit pas `meta.warnings` du brut. La trace
s'arrête à `raw_data/` dans ce cas précis.

## Le garde-fou de test qui manquait

L'index Sénat, dans sa première version, a fait entrer un appel réseau dans
**62 tests existants** sans qu'aucun n'échoue :
`tests/test_generate_all_profiles.py` est passé de 0,50 s à **13,4 s**,
exactement la pathologie que #473 avait supprimée. La règle « aucun test ne
touche le réseau » était **auditée une fois**, pas tenue.

D'où `tests/conftest.py` : une fixture `autouse` qui coupe
`requests.Session.send` — le point de passage de `requests.get`, `requests.post`
et de toute session construite ailleurs — et échoue en nommant l'URL. **La
boucle locale reste ouverte** : 11 tests de `test_amendements_download_modes`
montent un `http.server` sur `127.0.0.1` pour éprouver la reprise par `Range`
sur un vrai socket ; le critère est « sortir de la machine », pas « parler
HTTP ». Le sparse-checkout du workflow couvre l'autre moitié de la règle (le
corpus vivant absent du disque), celle-ci couvre le réseau.

