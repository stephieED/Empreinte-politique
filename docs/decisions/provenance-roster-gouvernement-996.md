<a id="provenance-roster-gouvernement-996"></a>
# Les membres de gouvernement deviennent une population, et leur collecte part (#996, lot 3) (2026-09-18)

`2026-09-18`

> **En bref** — Le lot 2 avait donné un slug aux 311 membres des 17
> gouvernements, mais pas de population : ils n'entraient pas dans
> `roster_candidats.json`, le seul fichier que les shards lisent. `KNOWN_PROVENANCES`
> reçoit `roster_gouvernement`, et six modules cessent de tester l'égalité à
> `roster_groupe` pour dire « membre de roster » — cette égalité publiait un
> ministre en `candidat_declare` et jetait son `acteur_ref`. Mesuré sur
> `origin/main` avant correctif : `meta.provenance == "candidat_declare"` et
> `acteur_ref is None`, sans qu'aucune étape n'échoue.

## Contexte

Lot 3 de #996. Le lot 2 (`roster-gouvernements-amo30-996`) lit les organes
`GOUVERNEMENT` d'AMO30, résout 311 personnes, en fabrique 205 slugs, et les
verse dans `rosters_bruts.json` — ce qui suffisait à la passe de correspondance,
pas à la collecte.

**Ce que le run 35272626217 a montré, et qui n'était pas un défaut.** Ce run,
lancé le 17/09 à 22 h 44 pour créer les entrées de correspondance des 205
membres, en a créé **0** : `raw_data/correspondance_acteurs_an.json` est resté
octet pour octet celui du 12/09, 1 196 entrées. La cause est le deuxième des
trois filtres de `entrees_derivees` — **le profil doit être publié** — et les
205 n'en ont pas. Le run l'a dit sans ambiguïté :

```
-> 205 slug(s) déclaré(s) fabriqué(s) par le roster ; 0 entrée(s) dérivée(s) ajoutée(s) ; 0 refus.
```

Ce n'est pas circulaire. Dans `generate-data.yml`, la normalisation pivot
(l. 3016) précède la passe de correspondance (l. 3262), qui précède la §5b du
portail : le run qui collectera les 205 écrira leurs profils, **puis** leurs
entrées, puis passera la §5b — tout dans le même run. L'ordre est déjà le bon ;
il manquait seulement que la collecte parte.

## Décision

1. **`roster_gouvernement` entre dans `KNOWN_PROVENANCES`**, troisième valeur
   d'un vocabulaire fermé. Le `statut` écrit dans `roster_candidats.json` est
   repris **tel quel** comme `meta.provenance` par `generate_all_profiles` :
   c'est la seule raison pour laquelle les deux chaînes doivent être la même, et
   un test le tient plutôt que de le présumer.
2. **`population_profils.PROVENANCES_ROSTER`** dit désormais ce que « membre de
   roster » désigne. Six modules testaient l'égalité à `roster_groupe` ; c'est
   cette égalité qui portait le défaut (ci-dessous).
3. **Les membres entrent dans `roster_candidats.json`**, via
   `candidats_des_gouvernements()`, appelée **après** le portail d'anomalies du
   roster et **avant** l'écriture : après, parce qu'un roster de groupe
   incomplet ne doit pas déclencher un téléchargement d'AMO30 de plus ; avant,
   parce que les deux fichiers doivent décrire la même collecte à la même
   seconde (#518).
4. **Le roster des groupes gagne la déduplication.** Une personne à la fois
   députée et ministre reste `roster_groupe`. Ce n'est pas un détail de tri :
   `group_profile.py` agrège sur la provenance, et rétrograder un membre de
   groupe le retirerait de la cohésion de son groupe. Son rattachement au
   gouvernement ne passe pas par la provenance mais par `acteur_ref` (lot 4),
   donc rien n'est perdu.
5. **Le poste « membres de gouvernement » de la ventilation ne s'affiche que
   s'il pèse.** Avant le premier run de collecte il vaudrait `0` sur chaque
   ligne de chaque rapport : c'est du bruit, pas une ventilation. Les deux
   populations historiques restent affichées même à zéro — c'est le zéro d'un
   corpus vide, et le voir est le premier signe qu'on ventile le mauvais
   répertoire.
6. **Un échec de lecture de l'archive reste non fatal**, et la conséquence est
   assumée : ce run ne collecte alors aucun membre de gouvernement, la fusion
   additive garde ceux du run précédent, et il ne publie pas une composition
   amputée (§2 règle 5).

## Le défaut que l'égalité portait, mesuré avant correctif

Six modules écrivaient `provenance == "roster_groupe"` pour dire « membre de
roster ». Deux de ces six décidaient quelque chose d'irréversible. Mesuré sur
`origin/main` `9feca027f` le 18/09/2026, en passant une entrée de statut
`roster_gouvernement` à `process_candidat` :

| Ce qui était décidé | Sur l'ancien code | Conséquence |
| --- | --- | --- |
| `meta.provenance` du pivot publié | `candidat_declare` | le ministre est compté comme une fiche à publier, et la ventilation des outils le range chez les candidats |
| `acteur_ref` transmis à la collecte | `None` | **124 des 311 membres n'ont jamais été députés** : aucune recherche par nom ne les retrouve dans AMO30, donc leur collecte ne part pas |
| `collecte_bicamerale` | `True` | un appel Sénat par membre, pour un acteur AN |
| `KNOWN_PROVENANCES` | sans la valeur | `validate_profil()` refuse : `meta.provenance non reconnue` |
| Ventilation des outils | poste `provenance inconnue` | les 205 comptés comme une anomalie |
| §2 du portail | « inattendus », nommés un par un | les 468 lignes de fausse alerte que #630 avait retirées, de retour |

Aucune de ces six lignes n'aurait fait échouer une étape. C'est la forme exacte
du trou muet de #510 et #501 — et la raison pour laquelle
`PROVENANCES_ROSTER` est un `frozenset` importé, et non une égalité recopiée.

`collecte_bicamerale` n'est **pas** verrouillé par un test : sur une seule
chambre il n'a aucun effet observable, et `build_profile_any_chambre` le dit
lui-même. Un test qui l'affirmerait quand même décrirait l'endroit où l'on a
regardé, pas le comportement.

## Ce que ce lot ne fait pas

**Il ne rattache aucun membre à sa fiche de gouvernement** — c'est le lot 4, qui
lira les membres dans le roster par `acteur_ref`. Les 17 fiches continuent donc
de publier la composition issue des profils déjà collectés, à côté de
`comptages.membres_recenses`, qui dit le dénominateur réel (de 19 pour
Lecornu I à 55 pour Borne, mesuré le 18/09/2026).

**Il ne crée pas les 205 entrées de correspondance** : elles naîtront dans le
run qui publiera leurs profils, par le chemin décrit en contexte.

## Budget, mesuré sur le run 35272626217

`roster_limit` vaut `0` par défaut (pas de plafond, depuis #578), donc le
prochain run collecte les 205 en une fois, répartis sur 8 shards :

| | Mesuré au 17/09 | Après ce lot, projeté |
| --- | ---: | ---: |
| Membres de roster collectés | 1 145 | 1 350 (+18 %) |
| `extract-roster-groupes`, shard le plus lent | 8 min 25 | ~10 min |
| `merge-and-pivot` (limite 120 min) | 58 min | à re-mesurer |

Les shards sont parallèles, donc leur budget n'est pas en cause.
`merge-and-pivot` normalise en pivot **tous** les profils : +17 % de population
sur un job déjà à 58 min de ses 120, c'est la seule ligne à re-mesurer au
prochain run — et un débit projeté n'est pas un débit mesuré
(`docs/decisions/budget-temps-domaines-dossiers-901.md`).

## Alternative rejetée

**Réutiliser `roster_groupe` pour les membres de gouvernement**, en les
distinguant par `notes` ou par la présence d'`acteur_ref` dans un organe
`GOUVERNEMENT`. Rejeté : `meta.provenance` répond à « pourquoi ce profil
existe », et deux populations sous une même valeur rendent la question sans
réponse — c'est précisément ce que #630 a mesuré comme coûtant une épic
recadrée. Un agent qui ventile aurait lu « 1 350 membres de roster » sans
pouvoir dire lesquels alimentent un groupe et lesquels un gouvernement.

**Faire des membres de gouvernement une population affichée d'office, même à
zéro.** Rejeté par le point 5 : avant le premier run de collecte, le poste
serait un `0` sur chaque ligne de chaque rapport, et c'est un bruit qui
apprend à ne plus lire la ventilation.
