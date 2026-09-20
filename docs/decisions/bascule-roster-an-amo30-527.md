<a id="bascule-roster-an-amo30-527"></a>
# La bascule : le roster des groupes AN vient d'AMO30 (#527, lot 1b de l'épic « une seule source AN ») (2026-08-26)

`2026-08-26`

> **En bref** — une ligne bascule, trois conséquences qu'elle ne porte pas seule.

**Ce lot bascule, et ne fait que cela.** Le lot 1 (#526) avait posé la source à
côté de celle en place, derrière un drapeau baissé, précisément pour que la
bascule soit une décision prise seule. La voici :
`an_roster.AN_ROSTER_ACTIF` passe à `True`, et `group_roster.fetch_full_roster`
délègue la clé `deputes` à `an_roster.fetch_full_roster_an`. Le reste du diff
est ce qu'il fallait pour que cette ligne ne mente pas.

## 1. La forme : une ligne, et un `git revert` qui la défait

L'aiguillage tient en une condition, dans **un seul** endroit du dépôt :

```python
if chambre == "deputes" and an_roster.AN_ROSTER_ACTIF:
    return an_roster.fetch_full_roster_an(legislature)
return fetch_full_roster_nosdeputes(chambre, legislature=legislature, session=session)
```

La lecture NosDéputés survit sous son propre nom,
`fetch_full_roster_nosdeputes` : elle sert le Sénat en régime normal, et
l'Assemblée si le drapeau retombe. Aucun appelant n'a eu à changer de fonction,
donc aucun ne changera pour revenir en arrière — c'est **ça**, l'assurance de
l'épic, et pas une branche parallèle qu'on maintiendrait en double.

Les deux verrous que le lot 1 avait posés dans `tests/test_an_roster.py` ne
sont pas retirés, ils sont **retournés** : le drapeau est figé à `True`, et la
liste des modules de `src/` qui importent `an_roster` est figée à
`{group_roster.py, group_profile.py}`. Un verrou qu'on supprime le jour où il
se déclenche n'a jamais rien gardé.

## 2. Mesuré : les 5 fiches de la 16e sont reproduites à l'identique

Régénération des 5 fiches AN sur les 476 profils pivot committés, roster dérivé
de l'archive AMO30, comparée aux fiches publiées :

| Fiche | `membres` | perdus | gagnés | `cohesion_votes` | `mandats_agreges` | `tags_agreges` | `couverture_roster` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `groupe-AN-REN-16` | 193 → **193** | **0** | 0 | 4 099 → 4 099 | 731 → 731 | 0 → 0 | 193/193 → 193/**196** |
| `groupe-AN-SOC-16` | 31 → **31** | **0** | 0 | 3 843 → 3 843 | 293 → 293 | 179 → 179 | 31/31 → 31/31 |
| `groupe-AN-RN-16` | 90 → **90** | **0** | 0 | 4 085 → 4 085 | 393 → 393 | 318 → 318 | 90/90 → 90/90 |
| `groupe-AN-LFI-16` | 76 → **76** | **0** | 0 | 3 973 → 3 973 | 403 → 403 | 0 → 0 | 76/76 → 76/76 |
| `groupe-AN-LR-16` | 62 → **62** | **0** | 0 | 3 832 → 3 832 | 465 → 465 | 0 → 0 | 62/62 → 62/**63** |

**Aucune perte sur aucune liste surveillée** par `audit_diff_profils` (#460,
#470) : `membres`, `cohesion_votes`, `mandats_agreges`,
`tags_thematiques_agreges`, `historique_noms`. Aucun scalaire surveillé ne
passe à `null`. Le roster de candidats sort inchangé lui aussi : **452**
candidats, `REN 193 · SOC 31 · RN 90 · LFI 76 · LR 62` — les mêmes qu'avant.

Le seul écart est `meta.couverture_roster.roster_total`, sur deux fiches, et
c'est un **gain de véracité** : REN comptait bien 196 membres sur la
législature et LR 63, dont 3 et 1 sans profil publié. Le miroir ne publiant que
la dernière appartenance connue, ces 4 étaient absents du **dénominateur**, ce
qui faisait lire une couverture de 100 % là où elle est de 98,5 %. Un
dénominateur qui exclut ce qu'il ne sait pas mesurer n'est pas une couverture
(règle 7, AGENTS §2). C'est une variation de valeur sur un scalaire surveillé,
donc rapportée et non bloquante — la bonne catégorie.

## 3. Ce que la bascule rend visible, et qui devait cesser d'être muet

AMO30 publie un `PA######` et de l'état civil, jamais un slug ; le slug vient
de la table committée du lot 2 (#525), lue à l'envers. Un membre qui n'y a pas
d'entrée entre donc dans le roster **sans slug** — cas qui n'existait pas avec
NosDéputés, dont le slug est l'identifiant.

Or `build_roster_candidats_detaille` ignore un membre sans slug depuis
toujours, et il l'ignorait **sans un mot** : le slug *est* le nom du fichier
pivot (#487), il n'y a rien d'autre à faire, mais se taire là-dessus est la
forme exacte du trou de #510 et #501. `membres_sans_slug()` les compte et les
**nomme** — groupe, état civil, dates de mandat — sur `stderr` et en annotation
`::warning::`.

Non bloquant, délibérément : ces 4-là sont une catégorie fermée, datée et
déclarée entrée par entrée dans `raw_data/groupes_reels.json`
(`correspondance_sigles_an[].ecart_membres`). Même arbitrage que les 5 389
identifiants non résolus de #510 et que les rejets attendus-et-permanents de
#474 : ce qui doit être bruyant, c'est **le nombre s'il bouge**. Les faire
bloquer interdirait tout run tant que la clause 2 de la §9 de #526 n'est pas
soldée — c'est-à-dire punirait le run pour une décision éditoriale en attente.

## 4. Le `meta.warnings` publié devait changer de source, pas seulement de code

`fraicheur_donnees` est un champ **publié**, et il disait « composition dérivée
de www.nosdeputes.fr, qui n'a plus été mis à jour depuis la dissolution du
9 juin 2024 ». Le laisser tel quel pendant que la composition vient d'AMO30
n'aurait pas été une imprécision de rédaction mais une atteinte à la règle 2
(traçabilité totale, AGENTS §2). `_avertissement_fraicheur_an()` suit donc le
drapeau, parce que les deux sources n'ont pas la même limite de fraîcheur :
AMO30 est le référentiel de l'Assemblée, une législature close y est
**complète**, mandats terminés en cours de législature compris — ce que le
miroir perdait, et ce que les 4 sans-slug mesurent.

## 5. Une panne de la nouvelle source coûte ce que coûtait l'ancienne

`an_roster` lève `RosterAnIndisponible` / `RosterAnInactif`, qui héritent de
`RuntimeError` ; les deux consommateurs interceptaient
`(ValueError, requests.RequestException)`, la forme des échecs NosDéputés. Sans
correction, une archive AMO30 absente aurait traversé le `except` et tué le job
sur une trace de pile — c'est-à-dire un `exit 1` qui annule le commit du run,
là où #518 et #524 ont payé pour obtenir un `exit 2` qui laisse les fiches
publiées en place et une annotation qui nomme la clé.

`group_roster.ERREURS_ROSTER` réunit donc les erreurs des **deux** sources, en
un seul endroit. `CorrespondanceSiglesInvalide` (#526) et
`CorrespondanceInvalide` (#525) héritent déjà de `ValueError` et n'avaient pas
besoin d'être ajoutées ; elles sont couvertes, et testées comme telles.

## 6. Ce qui est gagné, et ce qui ne l'est pas encore

Gagné, et vérifiable : **une seule source AN** — la même que les scrutins et
les amendements —, **Licence Ouverte** au lieu d'ODbL *share-alike* sur la
composition (AGENTS §7), et la fin de la dépendance à une URL dont trois lots
consécutifs (#518, #518 bis, #524) ont amorti les pannes. Zéro appel réseau
ajouté dans le chemin nominal d'un run qui collecte déjà des profils :
l'archive est celle que `candidate_profile._ensure_acteurs_historique_zip_downloaded`
télécharge et met en cache.

Pas encore fait, et pourquoi — voir §7 : la 17e législature reste hors
périmètre, `--divergence` n'est pas câblé en CI, et le double calcul n'est pas
retiré.

## 7. Le double calcul n'est PAS retiré ici, et c'est sa condition écrite qui le dit

La §9 de #526 fixe **trois** clauses, toutes nécessaires. État au 26/08/2026,
mesuré et non supposé :

| Clause | État |
| --- | --- |
| 1. `--divergence` rend `amo30_seulement = []` et `publie_seulement = []` sur les 5 fiches de la 16e | ✅ vérifié, 0 et 0 |
| 2. `membres_sans_slug` vide sur ces 5 fiches | ❌ **4** — `PA794914`, `PA722070`, `PA719032`, `PA721522` |
| 3. les 5 groupes de la 17e sont publiés | ❌ aucun |

Retirer le drapeau et le repli aujourd'hui reviendrait à déclarer remplie une
condition qu'on a soi-même écrite et qu'on mesure fausse. Le transitoire est
donc **borné, pas installé** : le drapeau est figé par un test, l'écart est
publié à chaque run par l'annotation `ROSTER_SANS_SLUG`, et les deux clauses
ouvertes sont dans `ROADMAP.md` avec leur décompte.

La clause 3 n'est pas un oubli mais une **découverte de ce lot**, qui mérite
d'être écrite : le périmètre de la 17e chiffré par #526 §4 (156 profils à
collecter) suppose 156 slugs de plus dans
`raw_data/correspondance_acteurs_an.json`. Or cette table associe un
`acteur_ref` à un **slug publié**, et un député de la 17e jamais collecté n'en
a pas : la seule façon de lui en donner un est de le **fabriquer** à partir de
l'état civil AMO30, ce que `build_correspondance_acteurs_an.py` refuse par
construction (#525) et qu'AGENTS §4 interdit pour l'`id` d'un profil. Publier
la 17e demande donc de trancher *comment un slug naît quand la source n'en
fournit pas* — une décision de schéma, pas une passe de collecte. Elle ne peut
pas tenir dans une PR de bascule.

## 8. Ce que ce lot ne fait pas non plus

- **`.github/workflows/generate-data.yml` n'est pas touché.** Deux conséquences
  à traiter par un humain : `prepare-roster-matrix` n'a **aucun cache**
  `.cache/acteurs_historique_an`, il téléchargera donc les 13,6 Mo de l'archive
  une fois par run (une fois, pas par shard — le roster du run est unique
  depuis #518) ; et le câblage de `--divergence` en CI, prévu par #526 §6,
  demande ce même cache pour ne pas faire porter le téléchargement à
  `merge-and-pivot`. Aucun des deux ne bloque un run : le premier est un coût,
  le second une commodité de lecture.
- **Le Sénat n'est pas concerné** — AMO30 est un référentiel de l'Assemblée.
  Les deux entrées restent suspendues depuis #516, avec leur condition de
  reprise.
- **Aucun profil n'est recollecté** : `source` d'un candidat de roster reste
  l'URL NosDéputés du slug, parce que c'est bien là que
  `candidate_profile.py` va lire le profil. La bascule porte sur la
  **composition**, pas sur la collecte.

Gardé par `tests/test_bascule_roster_an_527.py`, les tests d'aiguillage de
`tests/test_group_roster.py` et les deux verrous retournés de
`tests/test_an_roster.py`.

