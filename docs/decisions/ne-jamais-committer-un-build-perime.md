<a id="ne-jamais-committer-un-build-perime"></a>
# Ne jamais committer un build produit avec du code périmé (#390) (2026-08-17)

`2026-08-17`

> **En bref** — ne jamais committer un build produit avec du code périmé : le checkout d'un job de fusion date du déclenchement.

**Contexte** : run `#266`. `merge-and-pivot` fait `actions/checkout` sans
`ref`, donc sur le SHA de `main` figé au **déclenchement** du run — alors que
le job ne démarre qu'après les 5 jobs d'extraction, ~18 min plus tard. La PR
#381 (correctif #379) a été mergée dans cette fenêtre. Le job a donc
régénéré `pivot_data/groupes/*.json` avec l'**ancien** `src/group_profile.py`
et tenté de le committer. Seul un conflit de rebase a empêché d'écraser le
correctif.

**Le conflit était une chance, pas le problème.** Le cas dangereux est
l'inverse : quand git parvient à merger proprement, la donnée périmée est
publiée **en silence**.

**Arbitrage (utilisatrice)** : ne rien committer, et relancer sur le `main` à
jour. L'asymétrie le justifie — ne rien committer coûte un run et toute la
donnée dérivée est régénérable ; committer un build périmé publie une erreur.
Refuser de committer est donc le **défaut**, pas le cas d'échec.

**Option écartée — `ref: main` au checkout** (ma recommandation initiale) :
elle réduirait la fenêtre, mais le job dériverait avec du code neuf à partir
d'artifacts extraits avec du code ancien — un état mixte, plus cohérent
qu'aujourd'hui mais toujours pas cohérent. La relance sur un `main` à jour
rend cette option **inutile** : tous les jobs du nouveau run partagent alors
le même SHA, ce qui est correct par construction plutôt que « moins faux ».
Un seul mécanisme au lieu de deux.

*Autres options écartées* : rebase + régénération in situ (correcte mais
nettement plus complexe à câbler ; gardée en réserve, et elle éviterait de
jeter l'extraction — la partie coûteuse et fragile — si la fréquence des
abandons le justifiait) ; discipline de branche (non outillable) ; toute
résolution « la version du run gagne » (`-X theirs`, force-push), qui aurait
ici réintroduit sciemment le bug #379.

**Implémentation** :
- Step `Vérifier que le code de génération n'a pas changé pendant le run`,
  placé **juste avant** le commit — position choisie pour couvrir toute la
  fenêtre (déclenchement → commit) ; une vérification en début de job n'en
  couvrirait qu'une partie tout en donnant une fausse assurance.
- Condition volontairement **étroite** : `src/` uniquement. Un commit de doc
  ou de données ne déclenche rien — c'est le cas que la boucle de retry du
  push sait traiter depuis [[retry-push-merge-and-pivot-bash-e]] (#389).
- Marqueur `GENERATION_CODE_CHANGED_DURING_RUN` émis en `::error::`, détecté
  par `retry-generate-data.yml` comme **second motif de relance**, distinct de
  la signature de préemption runner — sinon le résumé attribuerait à tort une
  préemption. Le plafond d'une seule tentative automatique préexistant
  s'applique identiquement, ce qui borne le risque de boucle si `main` bouge
  encore pendant la relance.

**Vérifié sur dépôts git réels** (remote bare + clones), en exécutant le step
tel quel :
- *Commit concurrent sur `docs/` seulement* → `✓ src/ inchangé — commit sûr`,
  exit 0. Aucun faux positif : c'est le cas nominal que le retry doit
  absorber, pas abandonner.
- *PR touchant `src/` mergée pendant le run* (scénario exact du run #266) →
  fichiers modifiés listés, marqueur émis, exit 1, résumé explicite écrit
  dans `$GITHUB_STEP_SUMMARY`.

**Non résolu, assumé** : une relance jette le travail d'extraction déjà fait
(~20 min, et c'est la partie exposée aux `IncompleteRead`). Acceptable tant
que la condition d'abandon reste étroite ; à reconsidérer via l'option
« rebase + régénération » si la fréquence réelle des abandons le justifie —
donnée à mesurer, pas à supposer.

