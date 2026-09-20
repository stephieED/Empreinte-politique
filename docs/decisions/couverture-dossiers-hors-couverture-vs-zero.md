<a id="couverture-dossiers-hors-couverture-vs-zero"></a>
# Couverture des dossiers : « hors couverture de la source » ≠ « réellement à zéro » (#399) (2026-08-18)

`2026-08-18`

> **En bref** — « hors couverture de la source » n'est pas « réellement à zéro » : le warning cesse d'affirmer un défaut de données.

**Contexte** : le quality gate signalait « aucun texte porté malgré une
période renseignée » pour tout gouvernement dont `textes[]` était vide. Après
#400, il ne restait que Fillon II/III — dont la XIII<sup>e</sup> législature
n'a **aucune archive publiée**. Le warning affirmait donc un défaut de
données là où il n'y a qu'une limite de source : un « 0 texte porté » se lit
comme un fait mesuré (§2.5), et ces warnings, qui ne diminueront jamais,
diluent les signaux réels — c'est exactement ce qui avait masqué #397 (473
warnings noyant 45 exclusions bien réelles).

## Décision : dériver la borne des législatures ingérées

Nouveau module `src/couverture_dossiers.py`, **stdlib pure, sans I/O** :

- il porte désormais `AN_DOSSIERS_ARCHIVES` (déplacé depuis
  `gouvernement_textes.py`, qui le ré-exporte — un seul inventaire) ;
- il y adjoint `LEGISLATURES_DEBUT` (date de première séance) ;
- `borne_couverture_textes()` = début de la plus ancienne législature
  ingérée, soit **2017-06-21** avec les archives XV/XVI/XVII ;
- `statut_couverture_textes(debut, fin)` classe une période en
  `couverte` / `partielle` / `hors_couverture` / `indeterminee`.

Le module est stdlib pure **parce que** ses deux consommateurs de rapport
(`audit_gouvernement_dataset.py`, `check_quality_gate.py`) ne doivent jamais
importer `requests` ni toucher au réseau : c'est ce qui interdisait de lire
l'inventaire directement dans `gouvernement_textes.py`.

Conséquences :

- **quality gate** : un `textes[]` vide n'est un avertissement que si la
  période est `couverte`. Hors couverture (ou à cheval), le constat passe
  dans un bloc **information** distinct, non compté dans les avertissements
  qualité. Les deux gouvernements Fillon quittent ainsi le compteur.
- **audit** : nouvelle section « Couverture des textes portés », borne
  affichée dans l'en-tête, et `N/D (hors couverture)` au lieu d'un `N/D` nu
  dans le tableau des plages. `nb_textes` reste `null` quand le champ
  `textes` est absent — `[]` (zéro observé) et champ absent (donnée
  manquante) ne sont pas fondus.
- **UI** (`GovernmentProfile.jsx`) : une note explicite le périmètre quand la
  couverture est partielle ou nulle, et le vide affiche « période non
  couverte […] ce n'est pas un “aucun texte porté” » au lieu du message
  générique.

## Alternative écartée : porter la couverture dans `meta` du profil

Inscrire `meta.couverture_textes` à la génération aurait été plus traçable
(la donnée dirait elle-même ce qu'elle couvre), mais aurait imposé un
changement de schéma **et** une régénération complète de `pivot_data` pour
que l'information apparaisse — les fichiers déjà committés seraient restés
muets, obligeant de toute façon à un repli calculé. La dérivation à la
lecture donne le bon résultat immédiatement, sur les données existantes.

## Duplication assumée côté UI

`pivotAdapter.js` redéfinit la borne (`GOVERNMENT_TEXTS_COVERAGE_START`) :
l'UI lit les JSON pivot, pas le code Python. La divergence est verrouillée
par un test (`tests/test_couverture_dossiers.py`) qui relit la constante dans
le fichier JS et la compare à `borne_couverture_textes()` — ajouter une
archive sans mettre l'UI à jour fait échouer la suite.

## Note connexe : libellé IncompleteRead

Le gate affichait « Erreurs IncompleteRead — Détectées : 0 » alors que le log
du même run montrait 5/9 segments repris en retry. Le comptage
(échecs **non rattrapés**) est le bon ; seul le libellé prêtait à confusion.
Renommé « Erreurs IncompleteRead non rattrapées », avec une ligne explicite
en console et en Markdown. Seuil inchangé.

Le warning « couverture ministérielle incomplète » est reformulé dans le même
esprit : « portefeuilles confirmés **par une source primaire** — absence de
confirmation, pas absence de portefeuille ». #398 l'a depuis rendu informatif
plutôt que systématique (« 8/11 » au lieu de « 0/11 ») sans le faire
disparaître : la couverture reste partielle tant que tous les ministres n'ont
pas de profil pivot.

---

