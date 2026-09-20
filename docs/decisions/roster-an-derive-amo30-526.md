<a id="roster-an-derive-amo30-526"></a>
<a id="perimetre-17e-legislature-526"></a>
# Le roster des groupes AN est dérivé d'AMO30, derrière un drapeau baissé (#526, lot 1 de l'épic « une seule source AN ») (2026-08-26)

`2026-08-26`

> **En bref** — le roster AN dérivé d'AMO30 est livré derrière un drapeau baissé, avec l'écart publié entrée par entrée comme compteur de migration.

> **Entrée historique.** La bascule a eu lieu le même jour (#527, section
> ci-dessus) : le drapeau est à `True`, et l'option `--activer-roster-an`
> mentionnée plus bas a été **retirée** au profit de `--desactiver-roster-an`.
> Ce qui reste valable ici sans réserve : les mesures, les trois pièges et la
> condition de retrait de la §9.

**Ce lot ne bascule rien.** Il ajoute une source qui tourne **à côté** de
NosDéputés, publie l'écart entre les deux **entrée par entrée**, et laisse le
décompte de cet écart servir de compteur de migration. La bascule est le lot 1b.

## 1. Le problème

`group_roster.py` lit `https://www.nosdeputes.fr/deputes/json` — 814 Ko générés
à la volée, **aucune réponse sous 10 s** sur 24 appels mesurés (#518), puis un
**500 déterministe** trois runs durant (#524). Trois lots consécutifs ont été
consacrés à amortir les pannes de cette seule URL. Or la composition des
groupes est déjà **dans AMO30**
(`tous_acteurs_mandats_organes_xi_legislature`), que `candidate_profile.py`
télécharge et met en cache depuis #353/#354/#369/#467 pour quatre autres index
(`.cache/acteurs_historique_an/`). Le dépôt lit déjà tout ce qu'il faut :
`mandat.typeOrgane == "GP"` croisé avec `organe.codeType == "GP"`.

Trois gains, et le troisième n'est pas un bonus :

- **une seule source AN** à surveiller — la même que les scrutins et les
  amendements — au lieu d'un miroir tiers ;
- **Licence Ouverte (attribution)** au lieu d'ODbL *share-alike* (AGENTS §7) ;
- **la 17e législature devient accessible**. `LEGISLATURE_BY_BASE_URL`
  s'arrêtait à la 16e parce que NosDéputés n'a jamais été étendu au-delà : la
  limite était celle du miroir, pas celle des données.

## 2. Mesuré, pas supposé

Archive téléchargée le 26/08/2026 : **13,6 Mo**, **3 119 acteurs**, **63
organes `GP`**, index dérivé construit en **~0,6 s** (archive en cache), 833
acteurs portant un mandat `GP` de la 16e ou de la 17e. À comparer aux 814 Ko de
`/deputes/json` qui « ne répondaient jamais sous 10 s ».

Composition dérivée face aux effectifs **publiés** :

| Fiche publiée | membres publiés | AMO30 | sigle(s) AN | organe(s) |
| --- | --- | --- | --- | --- |
| `groupe-AN-LFI-16` | 76 | **76** | `LFI-NUPES` | `PO800490` |
| `groupe-AN-RN-16` | 90 | **90** | `RN` | `PO800520` |
| `groupe-AN-SOC-16` | 31 | **31** | `SOC`, `SOC-A` | `PO800496` + `PO830170` |
| `groupe-AN-LR-16` | 62 | 63 | `LR` | `PO800508` |
| `groupe-AN-REN-16` | 193 | 196 | `RE` | `PO800538` |

`src/an_roster.py --divergence` sur le corpus publié rend **0 membre publié que
le dérivé ignore** et **0 membre dérivé publié sous un autre slug**. L'écart
total est de **4**, et ce sont 4 acteurs **sans slug** :

| `acteur_ref` | Nom | Groupe | Mandat |
| --- | --- | --- | --- |
| `PA794914` | Alexandre Vincendet | `LR` 16e | 2022-06-29 → **2024-03-19** |
| `PA722070` | Pierre Henriet | `RE` 16e | 2022-06-29 → **2024-02-15** |
| `PA719032` | Bertrand Bouyx | `RE` 16e | 2022-06-29 → **2024-02-15** |
| `PA721522` | Xavier Batut | `RE` 16e | 2022-06-29 → **2023-08-29** |

Ce n'est pas « ~3 de plus » : c'est une **catégorie fermée et datée**. Les
quatre ont quitté leur groupe **avant la fin de la 16e législature**
(2024-06-09). NosDéputés ne publie que la **dernière** appartenance connue, ils
en sont donc absents ; sans profil publié, ils n'ont pas non plus d'entrée dans
la table du lot 2 (#525), donc pas de slug. Autrement dit AMO30 est **plus
complet**, et l'écart mesure exactement ce que le miroir perdait.

## 3. Trois pièges, et ce que le module en fait

**a. `NI` compte 592 membres sur la 16e — le filtrage par dates est
obligatoire.** L'organe « Non inscrit » **ouvre avant les groupes** :
2022-06-22 contre 2022-06-28 sur la 16e, 2024-07-01 contre 2024-07-18 sur la
17e. Tout le monde y transite : **576** mandats `2022-06-22 → 2022-06-28`, et
**577** mandats `NI` s'achevant le 2024-07-18 sur la 17e.

Règle retenue : *un mandat qui se termine **au plus tard** le jour où les
groupes de la législature se constituent est un transit, pas une
appartenance* — aucun groupe réel ne se termine avant d'exister. La date de
constitution est **lue dans le référentiel** (le plus petit `dateDebut` des
organes `GP` de la législature, hors `NI`), jamais écrite en dur : 2012-06-26,
2017-06-27, 2022-06-28, 2024-07-18. Effet mesuré : `NI` 16e **592 → 39**, `NI`
17e **640 → 94**, et **aucun autre groupe ne perd un seul membre** — le filtre
ne coupe que ce qu'il vise, et c'est testé sur les 10 entrées de la table.

Alternative écartée : *ne garder que les mandats ouverts à la fin de la
législature*. Elle reproduirait les 5 effectifs publiés à l'unité près — et
c'est précisément son défaut : elle **effacerait** les 4 membres ci-dessus,
c'est-à-dire qu'elle recopierait la perte du miroir au lieu de la mesurer.

**b. Les sigles diffèrent — table committée, pas heuristique.** Le sigle AN est
`organe.libelleAbrev` (`RE`, `LFI-NUPES`, `SOC-A`, `UDDPLR`), pas le sigle
publié (`REN`, `LFI`, `SOC`), et **pas** `libelleAbrege` non plus : celui-ci
écrit `LFI - NUPES` avec des espaces et rend `SOC` pour **les deux** organes
socialistes de la 16e — le champ qu'on aurait pris par réflexe est celui qui
fusionne silencieusement deux organes. La correspondance vit dans
`raw_data/groupes_reels.json`, clé `correspondance_sigles_an` : sigle publié,
législature, `sigles_an`, organes **mesurés**, effectif **mesuré**, date de
vérification, et l'écart **nommé entrée par entrée**.

Les organes committés ne servent **pas** à construire le roster — celui-ci
prend l'union des organes portant `sigles_an`, pour qu'un organe successif
nouvellement ouvert entre quand même plutôt que d'être perdu. Ils sont le
**fil-piège** : quand le mesuré cesse de coïncider avec le committé, l'AN a
bougé et la table doit être relue.

**c. Un groupe peut avoir deux organes successifs dans une même
législature.** `SOC` 16e : `PO800496` (2022-06-28 → 2023-10-18) puis
`PO830170` (2023-10-19 → 2024-06-09). Chacun compte 31 membres, et ce ne sont
pas 31 membres deux fois — c'est un groupe continu dont l'AN a rouvert
l'organe. Le module prend l'**union**, déduplique par acteur et **recolle les
périodes** (`mandat_debut` = le plus ancien, `mandat_fin` = le plus récent,
`None` l'emportant sur une date). Mesuré : sur le seul `PO800496`, les 31
membres sortiraient avec `mandat_fin = 2023-10-18` — **la moitié de l'année
perdue sans qu'aucun décompte ne bouge**. Même forme sur la 17e :
`AD` → `UDR` → `UDDPLR`.

## 4. La décision de périmètre : la 17e législature entre

AMO30 la sert, mais ce n'est **pas un gain gratuit** — c'est un élargissement
de corpus, tranché ici plutôt que subi plus tard. Le périmètre retenu est la
**continuité des 5 familles déjà publiées**, pas les 12 groupes de la
législature :

| 16e | → 17e | sigle AN | effectif | déjà un slug | profils à collecter |
| --- | --- | --- | --- | --- | --- |
| `AN:REN` | `AN:EPR` | `EPR` | 123 | 99 | 24 |
| `AN:LR` | `AN:DR` | `DR` | 64 | 42 | 22 |
| `AN:RN` | `AN:RN:17` | `RN` | 131 | 79 | 52 |
| `AN:LFI` | `AN:LFI:17` | `LFI-NFP` | 73 | 56 | 17 |
| `AN:SOC` | `AN:SOC:17` | `SOC` | 70 | 29 | 41 |
| | | **total** | **461** | **305** | **156** |

Les sigles publiés suivent l'AN (`EPR`, `DR`) et non la famille (`REN`, `LR`) :
« Renaissance » et « Les Républicains » ne sont plus les noms de ces groupes à
la 17e, et un fichier `groupe-AN-REN-17.json` publierait un nom que
l'Assemblée n'emploie pas. Chaque entrée nomme son prédécesseur (`succede_a`),
ce qui garde la continuité lisible sans la faire passer pour une identité.

Ce que l'élargissement coûte, écrit ici pour que le lot 1b n'ait pas à le
redécouvrir : **156 profils à collecter** (461 membres − 305 déjà couverts),
**5 fiches de groupe** de plus au quality gate (§4) et à
`audit_diff_profils`, **5 entrées** de plus dans `groupes_reels.json`, et
autant de slugs à ajouter à `raw_data/correspondance_acteurs_an.json` — dont
la couverture est un échec **dur** du gate (#525 §5b), donc à faire **avant**
la bascule et non pendant. La volumétrie de #429 est à revoir sur cette base.

Le périmètre **étendu à toute la législature** reste disponible et chiffré :
**641 membres hors `NI`**, dont **315** ont déjà un slug — soit 326 profils à
collecter au lieu de 156, pour 12 fiches de groupe. Il n'est pas retenu ici
parce que l'onglet Groupes suit les familles des candidats déclarés
(`raw_data/candidats.json`), pas l'hémicycle entier.

## 5. Le contrat de sortie ne change pas

`fetch_full_roster_an()` rend exactement ce que
`group_roster.fetch_full_roster` rend : des membres bruts portant
`groupe_sigle` — le sigle **publié**, pas celui de l'AN —, `slug`, `nom`,
`mandat_debut`, `mandat_fin`. `group_roster.filter_roster_by_sigle` s'y
applique **sans modification**, ce qui est la condition pour que le lot 1b soit
une bascule et non une réécriture. Testé : les 456 membres des 5 groupes de la
16e, filtrés par `REN`, rendent les 196 attendus.

Le slug vient du lot 2, lu **à l'envers** (`acteur_ref → slug`). Un acteur sans
entrée sort avec `slug: None` **et** dans `membres_sans_slug` du rapport, nommé
et daté : jamais absent, jamais inventé (AGENTS §2 règle 5). C'est ce qui rend
les 4 écarts de la 16e lisibles au lieu de les faire disparaître — la chaîne
aval (`build_roster_candidats_detaille`) ignore un membre sans slug **sans un
mot**, et c'est la forme exacte du trou muet de #510 et #501.

## 6. Le drapeau, et ce que « inactif » veut dire

`AN_ROSTER_ACTIF = False`, levé par `--activer-roster-an` (patron #510).
Inactif ne veut **pas** dire « rend une liste vide » : le module **refuse
bruyamment**. Un roster vide écrit sur disque est indiscernable d'un groupe
dissous, et c'est ce que #511 puis #524 ont payé.

L'inactivité est figée deux fois par `tests/test_an_roster.py` : le drapeau est
`False` dans le source, et **aucun module de `src/` n'importe `an_roster`**.
Un drapeau se lève par mégarde ; une absence d'appelant, non. Le jour où
`generate_roster_candidats.py` ou `generate_group_profiles.py` s'y branchent,
ce test échoue et rappelle que la bascule est une décision.

Le rapport de divergence n'est **pas** câblé dans `generate-data.yml` : le
brancher ferait télécharger 13,6 Mo dans `merge-and-pivot`, qui n'a pas de
raison de porter le cache AMO30 aujourd'hui. Il se lit à la demande
(`python3 src/an_roster.py --activer-roster-an --divergence`) et sa valeur du
jour — **4** — est consignée ci-dessus. Le câbler fait partie du lot 1b, avec
le cache qui va avec.

## 7. `LEGISLATURE_BY_BASE_URL` disparaît

La table domaine → législature n'avait qu'un usage : construire son propre
inverse. Elle est supprimée, `_BASE_URL_BY_LEGISLATURE_AN` est déclaré
directement. Ce n'est pas cosmétique : garder une table qui **apprend une
législature depuis un sous-domaine** laisserait entendre que c'est une façon
légitime de la connaître. Dans AMO30 la législature est une donnée du
référentiel — c'est exactement pourquoi la 17e y est.

## 8. Cache et coût

L'index dérivé (`.cache/acteurs_historique_an/index_groupes_politiques.json`)
suit les trois règles déjà payées ailleurs :

- **mémoïsé par chemin d'archive**, jamais par nom logique — les tests règlent
  leur propre archive par cas, et un mémo global ferait fuiter l'index d'un
  test dans le suivant (le piège qui avait fait revenir #377, AGENTS §5) ;
- **la clé porte l'entrée** (#505) : l'index enregistre la **taille** de
  l'archive dont il est tiré et se reconstruit si elle change. `.cache/` est
  partagé entre les jobs par la clé de cache CI ; un index construit sur une
  archive et servi à une autre, c'est la composition de la semaine passée
  publiée comme celle du jour ;
- **un index vide sur une archive lisible n'est jamais mis en cache** — le trou
  par lequel #510 est passé. « Archive absente » et « archive lisible sans
  aucun organe `GP` » lèvent tous deux `RosterAnIndisponible`, aucun ne rend
  `{}`.

Aucun appel réseau hors `data.assemblee-nationale.fr` : le module n'importe pas
`requests`, n'importe pas `group_roster`, et délègue l'unique téléchargement à
`candidate_profile._ensure_acteurs_historique_zip_downloaded`, déjà en place.
Testé.

## 9. Condition de retrait du double calcul

Le double calcul (AMO30 **à côté** de NosDéputés) s'arrête quand les **trois**
sont vraies, et pas avant :

1. `--divergence` rend `amo30_seulement = []` **et** `publie_seulement = []`
   sur les 5 fiches de la 16e — c'est déjà le cas au 26/08/2026 ;
2. `membres_sans_slug` est **vide** sur ces 5 fiches, c'est-à-dire que les 4
   acteurs ci-dessus ont une entrée dans `raw_data/correspondance_acteurs_an.json`
   (avec `ecart`/`motif`, comme `jordan-bardella`) ou une décision écrite de ne
   pas les publier. Aujourd'hui : **4** ;
3. les 5 groupes de la 17e sont publiés, donc le périmètre de la §4 est assumé
   plutôt que latent.

Alors `group_roster.fetch_full_roster` cesse d'être appelé pour l'Assemblée
(lot 1b), et le drapeau disparaît avec son module de repli. Sans ce critère
écrit, ce transitoire deviendrait permanent, comme les replis de lecture de
#431 et #432.

Ce qui **ne** justifie **pas** la bascule : « les 5 effectifs correspondent ».
Ils correspondent déjà, et il reste 4 membres que la chaîne aval laisserait
tomber sans un mot.

## 10. Ce qui n'est pas fait ici

- **aucun consommateur n'est migré** : `generate_roster_candidats.py`,
  `generate_group_profiles.py` et `generate-data.yml` sont inchangés ;
- **aucune fiche de la 17e n'est publiée** : la décision de périmètre est
  écrite et chiffrée, la collecte est le lot 1b ;
- **le Sénat n'est pas concerné** — AMO30 est un référentiel de l'Assemblée. Les
  deux entrées Sénat restent suspendues depuis #516 et gardent leur condition
  de reprise ;
- la fixture couvre les **législatures 16 et 17** seulement (les organes des
  13e-15e y sont, leurs mandats non) : aucune mesure ne doit être prise sur les
  législatures antérieures depuis la suite de tests.

Gardé par `tests/test_an_roster.py` (43 tests), sur
`tests/fixtures/amo30_gp_leg16_17.zip` — une **réduction** de l'archive réelle,
jamais une fixture rédigée : `syceron_minimal.xml` décrivait un schéma que l'AN
ne publie pas, et c'est ce qui a rendu #510 invisible aux tests pendant des
mois.

