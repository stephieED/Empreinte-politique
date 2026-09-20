<a id="scission-cache-ci-ecartee"></a>
# Scission du cache CI `.cache` par sous-répertoire : écartée (#374, fermée non planifiée) (2026-08-17)

`2026-08-17`

> **En bref** — scinder le cache CI par sous-répertoire : écartée, avec les chiffres qui l'écartent.

**Contexte** : #374 proposait de scinder le cache GitHub Actions partagé
`public-data-cache-an-*` (`path: .cache`) en deux entrées — amendements d'un
côté, le reste de l'autre — au motif que chaque shard `extract-an` restaurait
~915 Mio alors qu'il n'avait besoin que de `.cache/acteurs_an/` à l'étape 0
(résolution d'identité), sur un budget de 5 min/shard.

**Réévaluation après [[cache-amendements-forme-dedupliquee]] (#377) et
[[nettoyage-archive-brute-amendements]] (#264)** :

1. *L'argument principal a disparu.* #374 chiffrait le gaspillage sur les
   « 3 archives amendements ≈ 1,22 Gio ». #264 supprime `amendements.zip`
   dès l'index construit : ces archives n'entrent plus jamais dans le cache.
2. *Les index ont fondu.* #377 : législature 16 de 4,67 Go à 211 Mo. Clé AN
   mesurée après coup : 965 Mo au total, dont 673 Mo d'amendements (69 %) —
   mais des données désormais réellement utiles, plus des archives jetables.
3. *Défaut logique de la proposition elle-même* : `extract-an` **consomme**
   les amendements (`build_profile` appelle `fetch_amendements_officiels`
   pour tout `chambre == "deputes"`, et ce job traite des députés), tout
   comme `extract-roster-groupes`. Les deux jobs qui restaurent cette clé ont
   donc besoin des 673 Mo **dans le même job** : scinder en deux entrées
   restaurées au même endroit ne supprime aucun octet, il les déplace.

**Décision : fermée non planifiée.** Le bénéfice ne se matérialiserait que
via une restauration *différée* (un second `actions/cache/restore` placé plus
bas dans le job), pas via la simple scission proposée — et il resterait
limité au seul chemin d'erreur (un shard gelé avant d'atteindre les
amendements aurait perdu moins de temps). Coût/bénéfice défavorable face à un
changement structurel sur 3 jobs, avec un risque de course sur l'écriture du
cache partagé déjà documenté (#248 sous-issue 4). À rouvrir en visant la
restauration différée si le budget de 5 min/shard redevient contraignant
après la recalibration de #376.

**Note connexe** : la législature 17 dispose d'un index construit avec succès
(`derniere_construction_reussie: true`, 193 Mo) — les `IncompleteRead` sur
son archive ne sont donc pas systématiques, contrairement à ce que laissaient
penser les runs précédents et à ce qui avait été affirmé dans les entrées
antérieures de ce fichier.

