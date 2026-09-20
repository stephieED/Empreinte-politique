<a id="normalisation-fonction-mandats-agreges"></a>
# Normalisation de `par_fonction` dans `mandats_agreges`, et requalification du défaut « catégorie commission » (#379) (2026-08-17)

`2026-08-17`

> **En bref** — normalisation de `par_fonction` : deux référentiels aux conventions typographiques différentes comptaient à part.

**Défaut 1 — casse de `fonction` (corrigé)** : depuis [[mandats-officiels-an-369]],
les mandats proviennent de deux référentiels aux conventions typographiques
différentes — NosDéputés écrit `"membre"`, l'Assemblée nationale `"Membre"`.
`_aggregate_mandats` comptait sur la valeur brute : le même rôle était éclaté
en deux entrées (`'membre': 521` **et** `'Membre': 312`), donnant à lire deux
rôles distincts là où il n'y en a qu'un — trompeur au sens de la règle de
traçabilité (AGENTS.md §2).

*Décision* : `_normalize_fonction_mandat` normalise casse et espaces
surnuméraires, **sans** toucher au genre ni aux accents. `président` et
`présidente` (comme `co-rapporteur`/`co-rapporteure`) sont des libellés
institutionnels réellement distincts : les fusionner effacerait une
information portée par la source. Une fonction absente reste `non_precise`,
distincte de « simple membre » (§2.5, donnée manquante ≠ valeur par défaut).
*Mesuré après régénération* : `membre` unifié à 833, **0 collision de casse**
restante, variantes genrées préservées.

**Défaut 2 — catégorie `commission` trop large : requalifié, pas un défaut du
pipeline actuel.** Le constat initial (197 libellés sur 246 classés
`commission` n'en sont pas : « Comité de massif des Alpes », « Bureau de
l'Assemblée nationale »…) est exact, mais l'investigation a infirmé la cause
supposée :

1. *Le mapping AN est fidèle.* Vérifié sur `pascale-boyer` : ses 15 mandats
   AN mappés `commission` ont tous `typeOrgane == "COMPER"` et un libellé
   commençant bien par « Commission ». Aucun faux positif issu de
   `_TYPE_ORGANE_TO_CATEGORIE`.
2. *L'hypothèse « ça vient des profils non résolus AN » est fausse aussi* :
   les plus gros contributeurs sont tous résolus AN. Et le seul profil
   réellement jamais résolu AN du jeu (`bruno-retailleau`, sénateur) affiche
   0 suspect.
3. *Cause réelle : données périmées conservées par la fusion additive.* Les
   profils bruts portent `synchro nosdeputes` au 14/08 — antérieur à l'étape
   4 de #369, quand `_extract_mandats` mappait encore en dur toutes les
   `responsabilites` NosDéputés vers `commission`. Preuve décisive :
   `pascale-boyer` régénérée avec `--no-merge` donne **15 commissions,
   0 suspect**, contre 38/26 avec fusion.

*Conséquence* : aucune décision éditoriale sur la taxonomie n'est requise —
le pipeline produit déjà la bonne catégorisation. Ce qui reste est une
question d'hygiène de données (purger les entrées héritées), avec une
tension réelle : un `--no-merge` global purgerait aussi des données
légitimement préservées par la fusion additive (ex. les amendements de la
législature 17 conservés d'un run à l'autre, mécanisme de résilience #241).
Laissé ouvert dans #379 plutôt que tranché ici.

**Tests** : normalisation de casse, préservation des variantes genrées,
`non_precise` pour une fonction absente ou vide — les deux premiers vérifiés
comme discriminants (ils échouent si l'on retire la normalisation). Suite
complète : 1158/1158.

