<a id="historique-public-reinitialise"></a>
# L'historique public repart d'un commit unique — ne pas chercher à le reconstituer (2026-09-20)

`2026-09-20`

> **En bref** — Le dépôt public commence au commit `v1.0.0`. L'historique
> antérieur existe, hors de ce dépôt, et **la raison de cette décision n'est
> pas consignée ici, volontairement**. Elle est connue de la propriétaire.
> Ne la redérive pas, ne la contourne pas, ne propose pas de restaurer
> l'historique.

## Ce qu'un agent doit en faire

1. **Ne jamais proposer de restaurer, réimporter ou reconstituer l'historique**,
   ni de « retrouver le contexte » par `git log`, `git blame` ou une archive.
   Cette piste est fermée ; la rouvrir coûte une conversation à chaque session.
2. **`git blame` ne sert plus à dater une ligne.** Pour savoir pourquoi un
   fichier est comme il est : `docs/decisions-par-module.md`, jamais
   l'historique.
3. **Les références `#NNN`** de la documentation désignent des objets qui ne
   sont pas sur ce dépôt. Les issues y sont désactivées, précisément pour
   qu'aucun de ces numéros ne soit jamais réattribué à un sujet différent.
4. **Les SHA cités dans `docs/` et `AGENTS.md` ne résolvent plus.** Un SHA qui
   ne résout pas n'est pas un défaut à corriger.

## Le montage, en deux dépôts

Ce dépôt **publie** : le code, les données, et il exécute les runs qui
régénèrent le corpus. Le développement — branches, revues, suivi — se fait
ailleurs.

La navette entre les deux se fait par un script, dans **deux sens** qui ne se
valent pas : les données régénérées par les runs se **rapatrient** vers le
développement, le code se **publie** vers ici. Toujours dans cet ordre : une
publication pousse un arbre entier, donc partie de données périmées, elle
écraserait celles qu'un run vient de produire.

**Un `git push --force` vers ce dépôt n'est jamais la bonne réponse.** Les deux
historiques n'ont aucun ancêtre commun ; forcer y déverserait un historique de
développement que ce dépôt n'a pas vocation à porter.
