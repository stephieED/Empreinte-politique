<a id="retry-push-merge-and-pivot-bash-e"></a>
# La boucle de retry du push ne rebouclait jamais (`bash -e`) (#389) (2026-08-17)

`2026-08-17`

> **En bref** — la boucle de retry du push ne rebouclait jamais, faute de `defaults: shell` (`bash -e`).

**Contexte** : run `#266`. Toutes les étapes de données de `merge-and-pivot`
ont réussi ; seul le push final a échoué, et le log ne montrait qu'une
« tentative 1/3 » là où le step en promet 3.

**Cause** : le workflow ne déclare aucun `defaults: shell`, donc GitHub
Actions exécute chaque `run:` avec `bash -e {0}`. Le `git rebase` en conflit
retournant un code non nul, le shell terminait immédiatement le step — les
tentatives 2 et 3 n'existaient que sur le papier, et le
`::error::Échec après 3 tentatives` en fin de boucle n'était **jamais**
atteint. Le diagnostic affiché en cas d'échec réel était donc trompeur, ce
qui a longtemps masqué le défaut : le retry paraissait fonctionner puisque
personne ne voyait de message contredisant.

Effet secondaire : le step se terminait avec le dépôt du runner **en rebase
inachevé** (`.git/rebase-merge/` présent, index en conflit).

**Correctif** : `set +e` sur la seule portée de la boucle (restauré ensuite),
et sortie immédiate sur conflit — un conflit de rebase ne se résout jamais en
rebouclant, les deux côtés ayant réécrit les mêmes fichiers générés. Ajout
d'un `git rebase --abort` avant de sortir, pour laisser le dépôt propre. Le
message final distingue désormais les deux causes : conflit de rebase (cas du
run #266, cause traitée séparément dans #390) vs. rejet persistant après 3
rebases réussis (concurrence soutenue) — la première ne se traite pas par un
retry, la seconde si.

**Vérifié sur dépôts git réels**, en exécutant le step sous `bash -e` comme
le fait GitHub Actions :
- *Ancien code, conflit* : une seule « tentative 1/3 », aucun message
  d'erreur final, `.git/rebase-merge/` laissé en place — défaut reproduit à
  l'identique.
- *Nouveau code, conflit* : message explicite désignant la bonne cause, exit
  1, dépôt propre.
- *Nouveau code, commit concurrent sur un fichier disjoint* (le cas que le
  retry vise depuis le run #29) : « tentative 2/3 », **push réussi**, les deux
  commits préservés sur le remote. Ce scénario ne fonctionnait pas non plus
  avant le correctif.

**Périmètre** : uniquement la mécanique de retry. La raison pour laquelle un
conflit survient — le job régénère des fichiers générés depuis un SHA figé et
écrase le travail d'une PR mergée entre-temps — reste ouverte dans #390.
Corriger la boucle seule ne rend pas le run #266 vert : elle transforme un
échec confus en échec explicite.

