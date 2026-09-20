<a id="limit-sample"></a>
# Déploiement progressif de l'extraction roster-driven : --limit vs --sample (2026-08-12)

`2026-08-12`

> **En bref** — déploiement progressif de l'extraction roster-driven : `--limit` contre `--sample`.

**Contexte** : #190 branche la liste roster-driven (#188) dans
`generate_all_profiles.py` (`--candidats raw_data/roster_candidats.json`).
Avant d'ouvrir l'extraction aux ~750 membres complets, une sous-issue CI
dédiée a besoin de pouvoir tester à petite échelle sans consommer tout le
budget CI.

**Décision** : ajouter les deux options plutôt que de trancher entre elles —
`--limit N` (les N premiers candidats, ordre déterministe du fichier source)
et `--sample N` (N candidats tirés aléatoirement sans remise), mutuellement
exclusives (`argparse` mutually exclusive group). `--limit` sert les tests
reproductibles (CI, `--resume` stable d'un run à l'autre) ; `--sample` sert la
vérification ponctuelle de la diversité de couverture (chambres/groupes
différents) sans dépendre de l'ordre du fichier. Aucune graine (`seed`) fixée
pour `--sample` : chaque run tire un échantillon différent, ce qui est
acceptable pour un usage de spot-check et documenté dans l'aide CLI.

*Alternative rejetée* : n'implémenter que l'un des deux (comme suggéré par
l'issue, "à trancher en implémentation") — rejeté car les deux usages
(reproductible pour la CI, aléatoire pour la diversité) sont distincts et peu
coûteux à supporter simultanément.

