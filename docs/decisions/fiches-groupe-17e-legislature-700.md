<a id="fiches-groupe-17e-legislature-700"></a>
# Les 5 groupes de la XVIIe entrent dans `groupes[]`, et leur succession est déclarée comme une relecture (#700) (2026-09-01)

`2026-09-01`

> **En bref** — les 5 fiches de groupe publiées décrivent toutes la **XVIe**, close le 09/06/2024, alors que `correspondance_sigles_an` portait **déjà** les cinq groupes de la XVIIe, mesurés et relus le 26/08/2026 ; ce qui manquait tenait en cinq entrées du tableau **`groupes[]`**, le seul que le pipeline lise pour savoir quelles fiches produire, et la mention laissée dans la config — « la publication est le lot 1b » — désignait **#527**, qui a basculé la *source* du roster sur AMO30 et s'est fermée sans publier une fiche : elle est retirée, et un test échoue si elle revient ; **« 156 nouveaux profils » ne se reproduit pas** — `build_roster_candidats_detaille` laisse tomber un membre sans slug et un slug ne s'invente pas (#525), donc un run produit **0 profil brut neuf** : les 461 membres de la XVIIe rendent **304 slugs distincts** (`belkhir-belhaddad` siège dans deux groupes), **303 sont déjà dans le roster de la XVIe**, le seul propre à la XVIIe est `laurent-wauquiez`, et **304 / 304 ont déjà leur profil brut ET leur pivot** ; le roster de candidats passe de 452 à **453**, le poids ne bouge pas (`raw_data/profiles/` = **7,70 Gio** pour 481 slugs, médiane **11,8 Mio**, max **58,0 Mio**, garde-fou #580 à 80 Mio **par fichier**), et les 156 sans slug coûteraient +1,8 à +2,5 Gio le jour où quelqu'un les instruit (#691) ; `groupe_nom` est le `organe.libelle` **verbatim** de l'archive, remesuré en test sur la réduction `amo30_gp_leg16_17.zip` ; **`succede_a` passe sur la fiche** parce que `web/` ne lit que `pivot_data/`, **optionnel** comme #686 et #653, et il reprend le patron de #686 avec **une dissymétrie qui est le fait** : `position_politique` **exige** un `source_url`, `succede_a` l'**interdit** — l'Assemblée ouvre et ferme des organes (`PO800508` clos le 09/06/2024, `PO845425` ouvert le 18/07/2024), elle ne les chaîne pas, et c'est `etabli_par: "relecture_humaine"` (vocabulaire fermé à **une** valeur) plus `verifie_le` qui disent d'où l'affirmation vient, la preuve publiée étant les `sigles_an`/`organes_an` du prédécesseur, verbatim ; une succession qui ne résout pas est refusée **deux fois** (patron #485) — dans la table, **après** la boucle pour que le verdict ne dépende pas de l'ordre des entrées, et au **§4 du portail**, seuil 0, sur un `succede_a.fichier` qui ne désigne aucun document publié ; **`groupe_id` reste opaque** — `AN:EPR`/`AN:DR` sans suffixe, `AN:RN:17`/`AN:SOC:17`/`AN:LFI:17` avec, donc pas uniformément `<chambre>:<sigle>` —, mesuré tenable parce que **rien ne le découpe** dans le dépôt et figé par un test qui interdit un `split(":")` dessus ; les quatre garde-fous sont vérifiés un par un (le **§4b accepte** `non_declaree`, valeur publiée : 0 erreur dure sur les 10 fiches AN montées en `tmp_path` — rien à y corriger ; §5b, `audit_collecte_non_publiee` et `audit_diff_profils` sont sans objet, un fichier qui apparaît étant un gain) ; **ce qui reste à trancher** : la couverture des cinq fiches sera de **305 / 461 (66,2 %)** contre 99,1 % sur la XVIe, `AN:SOC:17` tombant à **29 / 70 (41,4 %)**, et `min_coverage_pct` valant **0** — désactivé depuis #193 faute de chiffres réels — une fiche à 41 % passerait le portail sans un avertissement en publiant une `position_majoritaire` par scrutin calculée sur 29 des 70 membres ; aucun run n'a été lancé, les cinq fiches n'existent pas encore.

## 1. Le problème : la configuration était prête, et personne ne l'a lue

Les 5 fiches de groupe publiées décrivent toutes la **XVIe** législature, close
le 09/06/2024. `raw_data/groupes_reels.json` → `correspondance_sigles_an`
portait **déjà** les cinq groupes de la XVIIe, mesurés et relus le 26/08/2026 :
sigles AN, organes, effectifs, membres avec slug, prédécesseur. Ce qui manquait
tenait en cinq entrées du tableau **`groupes[]`** — le seul que
`generate_roster_candidats.py` et `generate_group_profiles.py` lisent pour savoir
quelles fiches produire. Une table de correspondance ne produit aucune fiche.

Les cinq entrées portaient la même mention : *« Fiche non publiée : périmètre
élargi à la 17e législature (#526), la publication est le lot 1b. »* **« Lot 1b »
est #527**, qui a basculé la *source* du roster sur AMO30, l'a livré, et s'est
fermée le 26/08/2026 avec ses neuf cases cochées — sans publier une seule fiche.
La publication n'a jamais été le lot de personne, et la mention l'a rendue
invisible en donnant l'impression qu'elle était prise en charge. Elle est
retirée par ce lot ; `tests/test_fiches_groupe_17e_700.py` échoue si elle
revient.

## 2. Ce qui a été mesuré ici, et ce qui ne se reproduit pas

Mesuré le 01/09/2026 sur `1db5c051`, archive AMO30 du 17/08/2026 en cache local.

| Groupe XVIIe | Organe | Membres (roster AMO30) | dont avec slug | sans slug |
| --- | --- | ---: | ---: | ---: |
| `AN:EPR` | `PO845407` | 123 | 99 | 24 |
| `AN:RN:17` | `PO845401` | 131 | 79 | 52 |
| `AN:LFI:17` | `PO845413` | 73 | 56 | 17 |
| `AN:SOC:17` | `PO845419` | 70 | 29 | 41 |
| `AN:DR` | `PO845425` | 64 | 42 | 22 |
| **total** | | **461** | **305** | **156** |

Les cinq organes attendus par la table sont exactement les cinq trouvés dans
l'archive : le fil-piège de #526 tient.

**Ce qui ne se reproduit pas — « 156 nouveaux profils » est faux.** Le cadrage de
l'issue lit la soustraction `461 − 305` comme le nombre de profils à collecter.
Ce n'en est pas un : `generate_roster_candidats.build_roster_candidats_detaille`
**laisse tomber un membre sans slug**, et un slug ne s'invente pas
(`build_correspondance_acteurs_an.py` refuse, §5b du portail hard-faile sur un
slug publié sans entrée, #525). Les 156 ne sont donc jamais collectés — ils sont
comptés et **nommés** par l'annotation `ROSTER_SANS_SLUG` (#527).

Et les 305 le sont déjà : **304 slugs distincts** (`belkhir-belhaddad` siège dans
deux groupes de la XVIIe), dont **303 sont aussi dans le roster de la XVIe** et
un seul est propre à la XVIIe, `laurent-wauquiez` — candidat déclaré, donc
collecté à ce titre. Mesuré : **0 des 304 n'est sans profil brut, 0 sans pivot**.

| Grandeur | Cadrage de l'issue | Mesuré ici |
| --- | ---: | ---: |
| Profils bruts neufs produits par un run | 156 | **0** |
| Slugs XVIIe distincts | — | 304 |
| dont déjà dans `raw_data/profiles/` et `pivot_data/profiles/` | — | **304 / 304** |
| Croissance du roster de candidats (union XVIe ∪ XVIIe) | — | 452 → **453** |

**Le poids ne bouge donc pas.** `raw_data/profiles/` pèse **7,70 Gio** pour 481
slugs (socle + tranches par législature), médiane **11,8 Mio** par slug, maximum
**58,0 Mio** — loin des 80 Mio du garde-fou de #580, qui porte sur **un
fichier**, pas sur un répertoire. Ce lot n'ajoute rien. L'ordre de grandeur est
noté pour le jour où quelqu'un instruira les 156 : **+1,8 Gio** à la médiane,
**+2,5 Gio** à la moyenne, soit +23 % à +32 % — c'est #691 qui porte ce sujet.

## 3. La décision

### 3.1 Cinq entrées dans `groupes[]`, recopiées

`roster_chambre: "deputes"`, `chambre: "AN"`, `legislature: "17"`, et
`groupe_id` / `groupe_sigle` / `fichier` **recopiés** de la table voisine — un
test vérifie l'égalité champ par champ, sans quoi le §4b du portail hard-faile.

`groupe_nom` n'est **pas** dans la table : il est pris **verbatim** dans
`organe.libelle` de l'archive (`Ensemble pour la République`, `Droite
Républicaine`, `La France insoumise - Nouveau Front Populaire`, `Rassemblement
National`, `Socialistes et apparentés`), et le test le remesure sur la réduction
verbatim `tests/fixtures/amo30_gp_leg16_17.zip`. Les 5 fiches de la XVIe ne
suivent pas toutes cette règle — `La France insoumise - NUPES` pour un organe
libellé `…Nouvelle Union Populaire écologique et sociale` : c'est un état de
fait constaté, pas un précédent, et il n'est pas repris.

### 3.2 `succede_a` est publié, et déclaré comme une relecture humaine

La vue empilée de #329 a besoin de la succession, et seule la configuration la
portait : `web/` lit `pivot_data/`. Le champ passe donc sur la fiche —
**optionnel**, comme `position_politique` (#686) et `date_reference` (#653) :
les 7 fiches publiées avant le lot ne le portent pas et ne doivent pas devenir
invalides, et les 5 fiches de la XVIe ne le porteront jamais (la XVe n'est pas
couverte par ce dépôt — `None`, pas un trou).

```json
"succede_a": {
  "groupe_id": "AN:LR",
  "fichier": "groupe-AN-LR-16.json",
  "legislature": "16",
  "sigles_an": ["LR"],
  "organes_an": ["PO800508"],
  "etabli_par": "relecture_humaine",
  "verifie_le": "2026-08-26"
}
```

**`succede_a` est notre affirmation, pas un champ de l'AN.** L'Assemblée ouvre et
ferme des organes — `PO800508` clos le 09/06/2024, `PO845425` ouvert le
18/07/2024 — elle ne les chaîne jamais. Le bloc reprend donc le patron de #686
avec **une dissymétrie qui est le fait, pas une inconséquence** :

| | `position_politique` (#686) | `succede_a` (#700) |
| --- | --- | --- |
| Nature | déclaration de la source, recopiée | lecture de ce dépôt |
| `source_url` | **obligatoire**, même sur `non_declaree` | **interdite**, refusée par le schéma |
| D'où ça vient | `organe.positionPolitique` | `etabli_par: "relecture_humaine"` |
| La preuve | `organes[]` + `valeur_source` verbatim | `sigles_an` / `organes_an` du prédécesseur, verbatim |
| Daté par | `verifie_le` | `verifie_le` |

Une URL de référentiel posée à côté d'une affirmation que le référentiel n'écrit
nulle part la ferait lire comme sourcée : c'est l'inverse de la règle 2 d'
`AGENTS.md` §2. Le refus est un **invariant de schéma**, pas une convention —
`_valider_succede_a` liste `source_url` comme une erreur.

`ETABLISSEMENTS_SUCCESSION` n'a **qu'une** valeur, et il n'y en aura pas de
seconde tant qu'aucune source ne publiera la succession : une valeur
`source_ouverte` ajoutée « au cas où » laisserait croire que ce cas existe.

### 3.3 Une succession qui ne résout pas est refusée, à deux endroits

Le patron de #485 : une référence orpheline publie un renvoi sans objet.

- **Dans la table** (`groupes_config._valider_successions`, appelée par
  `charger_correspondance_sigles`) : un `succede_a` qui nomme un `groupe_id`
  absent, une auto-succession, ou un prédécesseur sans `fichier` font lever
  `CorrespondanceSiglesInvalide`. La validation est faite **après** la boucle et
  non dedans : au fil de l'eau, le verdict dépendrait de l'ordre des entrées
  dans le fichier, et un prédécesseur écrit plus bas passerait pour introuvable.
- **Dans le §4 du portail** : une fiche publiée dont `succede_a.fichier` ne
  désigne aucun document de `pivot_data/groupes/` est un **échec dur**, seuil 0.
  C'est le seul contrôle qui ait le répertoire publié sous la main ; la table,
  elle, ne connaît pas `pivot_data/`.

### 3.4 `groupe_id` reste opaque — le constat est figé, pas corrigé

`AN:EPR` et `AN:DR` n'ont pas de suffixe (sigle neuf), `AN:RN:17`, `AN:SOC:17` et
`AN:LFI:17` en ont un (sigle réutilisé). `groupe_id` n'est donc **pas**
uniformément `<chambre>:<sigle>`, contrairement à ce que l'en-tête de
`schema_groupe.py` affirmait.

Mesuré avant de conclure : **rien ne le découpe**. Ses consommateurs sont
l'unicité (`audit_groupe_dataset.compute_doublons_groupe_id`), des libellés de
journal (`groupes_config.libelle_groupe`, `couverture_profil`), le renvoi de
`succede_a`, et l'`id` que `web/UI_finale/src/data/pivotAdapter.js` recopie — pas
un `split(":")` dans tout le dépôt. Les renommer casserait dix identifiants
publiés, dont cinq déjà servis par l'onglet Groupes, pour un gain nul.
`test_aucun_code_du_depot_ne_decoupe_un_groupe_id` fige la condition qui rend ce
choix tenable : le jour où quelqu'un écrit `groupe_id.split(":")[1]`, les trois
entrées suffixées rendent un sigle juste et une législature perdue — un bug muet.

## 4. Ce qu'un run produira, et les quatre garde-fous vérifiés un par un

**Cinq fiches neuves** — `groupe-AN-EPR-17.json`, `-RN-17`, `-LFI-17`, `-SOC-17`,
`-DR-17` — **zéro profil brut neuf**, un candidat de plus dans le roster (453),
un fetch de roster de plus par run (clé `("deputes", "17")`, lue dans la même
archive AMO30 déjà en cache : aucun téléchargement supplémentaire).

| Garde-fou | Verdict | Pourquoi |
| --- | --- | --- |
| §4b position politique (#686) | **passe** | les 5 entrées portent `non_declaree` avec `valeur_source: null` ; `non_declaree` est une **valeur publiée**, dans `POSITIONS_POLITIQUES_GROUPE`, et le §4b compare position publiée et position committée — égales. Vérifié en montant les 10 fiches AN en `tmp_path` : 0 erreur dure. Rien à corriger dans le §4b. |
| §5b slug ↔ acteur AN (#525) | **passe** | aucun slug nouveau n'est publié ; les 156 sans slug ne sont jamais collectés. |
| `audit_collecte_non_publiee` (#511) | **passe** | il rapproche `raw_data/profiles/*.json` et `pivot_data/profiles/*.pivot.json`, jamais le roster et le publié. Un membre sans slug n'entre dans aucun des deux. Écart mesuré aujourd'hui : 0. |
| `audit_diff_profils` (#460/#470) | **passe** | un fichier qui apparaît part dans `gains`, non bloquant ; aucune baisse ne se calcule sur un fichier sans « avant ». Les cinq fiches sont des ajouts. |

**Un cinquième effet, qui n'est pas un garde-fou mais une conséquence** : le §4
du portail hard-faile sur `fichier manquant` tant que les cinq fiches n'existent
pas. C'est sans danger dans le run — `generate_group_profiles.py` s'exécute avant
`check_quality_gate.py` dans `merge-and-pivot` — mais `python3
src/check_quality_gate.py` lancé sur l'arbre committé **avant** le premier run
signale cinq fichiers manquants. C'est l'état normal de toute entrée nouvelle, et
l'ordre inverse (publier avant de configurer) n'existe pas : rien ne générerait
les fiches.

## 5. Ce que ce lot ne fait pas, et qui reste à trancher

**La couverture des cinq fiches sera de 305 / 461 (66,2 %)**, contre 452 / 456
(99,1 %) sur les cinq fiches de la XVIe. Par groupe :

| Fiche | `couverture_roster` attendue | |
| --- | ---: | ---: |
| `groupe-AN-EPR-17` | 99 / 123 | 80,5 % |
| `groupe-AN-LFI-17` | 56 / 73 | 76,7 % |
| `groupe-AN-DR-17` | 42 / 64 | 65,6 % |
| `groupe-AN-RN-17` | 79 / 131 | 60,3 % |
| `groupe-AN-SOC-17` | 29 / 70 | **41,4 %** |

Le seuil relatif du §4 (`min_coverage_pct`) vaut **0**, donc **désactivé** :
il a été ajouté par #193 « pour permettre une recalibration future une fois des
chiffres réels disponibles », et ces chiffres n'existaient pas encore. Le seuil
absolu (`min_members`, défaut **1**) ne se déclenche pas non plus. Une fiche
`AN:SOC:17` couvrant 41 % de son groupe passerait donc le portail **sans un
avertissement**, en publiant par scrutin une `position_majoritaire` et un
`taux_coherence` calculés sur 29 des 70 membres — or c'est exactement la donnée
que la vue empilée juxtaposera à la position d'un membre.

`meta.couverture_roster` le **dit** sur la fiche, ce qui satisfait la traçabilité
(§2 règle 2) ; ce que le seuil à 0 ne fait pas, c'est le **signaler au run**.
Recalibrer un seuil est une décision de la propriétaire (`AGENTS.md` §11) : ce
lot mesure et n'arbitre pas.

Restent **hors périmètre** et non instruits : les XIVe et XVe (la configuration
ne les prépare pas), la vue empilée elle-même (#329), et la variation d'effectif
à l'intérieur d'une législature couverte (#702).

## 6. L'alternative écartée

**Laisser `succede_a` dans la configuration seule.** C'est l'état d'avant, et il
ne tient pas : `web/` ne lit que `pivot_data/`, donc la vue empilée n'aurait rien
à empiler. Publier le champ sans `etabli_par` était l'autre voie — écartée pour
la raison inverse : un `groupe_id` posé nu à côté de champs tous sourcés se lit
comme sourcé, et la rupture entre deux législatures se lisserait en continuité
que l'Assemblée n'écrit pas.

## 7. Ce qui n'a pas été vérifié

- **Aucun run n'a été lancé** : les cinq fiches n'existent pas, et tout ce que
  la §4 annonce d'elles est dérivé du code et des mesures ci-dessus, pas d'un
  document produit.
- La couverture annoncée (305 / 461) suppose que les 304 pivots restent lisibles
  et que le roster du run rende les mêmes membres que l'archive du 17/08/2026 ;
  une archive plus récente peut avoir ouvert ou fermé un organe, et c'est
  précisément ce que le fil-piège `organes_an` sert à faire échouer bruyamment.
- La vue empilée n'est pas conçue : ce lot lui fournit une donnée, pas un écran.
