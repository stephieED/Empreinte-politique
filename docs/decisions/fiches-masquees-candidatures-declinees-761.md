# Une candidature déclinée n'a plus de fiche dans l'interface (#761)

`2026-09-07`

> **En bref** — #760 avait sorti les déclinées du périmètre de **collecte**, donc leurs données cessaient d'être rafraîchies **pendant que leur fiche restait en ligne**, le pire des deux états ; `sync-data.mjs` **portait** déjà le `statut` dans le manifeste et ne s'en servait nulle part ; deux gestes, le second non cosmétique : le manifeste **exclut** les statuts masqués (`getCandidateProfile` rend `null` sans entrée, donc la fiche sort de la liste **et** de la navigation directe), et le profil **n'est pas copié** dans `public/data/profiles/` — celui qu'une exécution précédente y a laissé étant **supprimé**, faute de quoi la fiche « masquée » resterait servie à son URL, le script ne nettoyant pas son dossier de sortie ; **16 → 14** candidats au manifeste ; **masquer ne supprime rien de `pivot_data/`** (le `rmSync` ne vise que la sortie, et un test l'y confine — la même ligne pointée un cran plus haut supprimerait le corpus, #460/#470) et **ne retire personne d'un groupe** : les fiches de groupe sont bâties sur leur propre `membres[]`, et un député qui renonce à une candidature reste un député ; le masquage **se lève tout seul** si la personne redéclare ; **un seul ensemble, deux langages** — `STATUTS_MASQUES` (JS) et `STATUTS_GELES` (Python) disent « cette personne n'est plus candidate », et un test fait échouer la suite s'ils divergent, sur le patron de la table de sorts de #743 ; les séparer devra être une décision écrite, pas une dérive ; le masquage **se déclare** avec les slugs et jamais un compteur (#510) ; **ce que le lot ne fait pas** : `public/data/candidats.json` reste la copie intégrale de la liste éditoriale, déclinées comprises — aucun composant ne le lit, et cacher la trace d'une candidature qui a existé n'est pas ce que « masquer la fiche » veut dire. 9 tests neufs, suite complète à 3 987, 0 échec.

## Contexte

#760 a sorti les candidatures déclinées du périmètre de **collecte**. Leurs
données ont donc cessé d'être rafraîchies — pendant que leur fiche restait en
ligne. C'est le pire des deux états : une page qui se présente comme le CV
politique d'un candidat, alimentée par une collecte qu'on vient d'arrêter.

`web/UI_finale/scripts/sync-data.mjs` construit le manifeste depuis
`raw_data/candidats.json` en ne filtrant que sur la disponibilité du profil :

```js
const manifestCandidates = candidats.filter((c) => availableSlugs.has(c.slug))
```

Le `statut` y était **porté** — le manifeste l'expose depuis toujours — et
n'était utilisé nulle part pour décider ce qui s'affiche.

## Décision

| Mesure | Avant | Après |
| --- | --- | --- |
| Candidats au manifeste | 16 | **14** |
| Fiches masquées, nommées à chaque sync | — | **2** |

Deux gestes, et le second n'est pas cosmétique :

1. **le manifeste exclut les statuts masqués.** `getCandidateProfile` rend
   `null` quand le manifeste n'a pas l'entrée : la fiche disparaît de la liste
   *et* de la navigation directe ;
2. **le profil pivot n'est pas copié** dans `public/data/profiles/`, et celui
   qu'une exécution précédente y a laissé est **supprimé**. Le script ne nettoie
   pas son dossier de sortie ; sans cette suppression, la fiche « masquée »
   resterait servie à son URL — masquée du manifeste, et pourtant atteignable.

## Ce que masquer ne fait pas

**Rien n'est supprimé de `pivot_data/`.** Le profil reste publié dans le dépôt :
ce que la personne a fait au Parlement reste vrai, seule sa candidature a cessé.
Supprimer un fichier publié est une disparition qu'`audit_diff_profils` bloque
(#460/#470), et le `rmSync` de ce script ne vise que le dossier de **sortie** —
un test le vérifie, parce que la même ligne pointée un cran plus haut
supprimerait le corpus.

**Elle reste membre de son groupe.** Les fiches de groupe sont bâties sur le
`membres[]` du profil de groupe, qui ne passe pas par cette liste : masquer la
fiche *de candidat* ne retire personne d'un agrégat parlementaire, et ce serait
faux de le faire — un député qui renonce à une candidature reste un député. Le
rattachement candidat ↔ groupe, lui, ne s'applique plus : `availableSlugs`
exclut les masqués, donc aucun `groupIds` ne leur est recollé.

**Le masquage se lève tout seul**, comme le gel de #760 : si la personne
redéclare, le job de tête de #757 repasse son `statut` et sa fiche revient au
prochain déploiement.

## Un seul ensemble, deux langages

`STATUTS_MASQUES` (JS) et `STATUTS_GELES` (`src/perimetre_candidats.py`) disent
la même chose — « cette personne n'est plus candidate » — et rien dans les deux
langages ne les oblige à rester d'accord. `tests/test_fiches_masquees_761.py`
fait échouer la suite s'ils divergent, sur le patron de la table de sorts de
#743, le premier test du dépôt à confronter un `frozenset` Python à une table JS.

Les séparer un jour reste concevable — un statut collecté mais masqué, ou
l'inverse — mais ce sera une **décision écrite**, pas une dérive.

## Le masquage se déclare

`sync-data` nomme les fiches masquées à chaque exécution, avec leurs slugs et
non un compteur : une fiche retirée doit se distinguer d'une fiche qu'on a
oublié de produire (#510). C'est la même exigence qu'au périmètre de collecte
(#760), au même endroit du raisonnement.

## Ce que la décision ne fait pas

**Le fichier `public/data/candidats.json`** reste la copie intégrale de la liste
éditoriale, déclinées comprises. Il n'est lu par aucun composant de l'interface
— seul le manifeste l'est — et il porte la liste telle qu'elle est, statut
compris. Le masquer reviendrait à cacher la trace d'une candidature qui a
existé, ce qui n'est pas ce que « masquer la fiche » veut dire.

## Alternative écartée

**Filtrer dans l'UI plutôt qu'au manifeste.** Le composant aurait ignoré les
entrées `decline` ; le profil aurait continué d'être copié et servi, et la fiche
serait restée atteignable par URL directe. Masquer au plus près de la source
coûte moins et ferme les deux chemins d'un coup.

**Retirer l'entrée de `candidats.json`.** Elle sortirait du manifeste aussi, et
emporterait le fait que cette personne a été candidate — que la fiche de groupe
et l'historique continuent de refléter. `statut: decline` existe précisément
pour changer d'état sans perdre l'information (#753).
