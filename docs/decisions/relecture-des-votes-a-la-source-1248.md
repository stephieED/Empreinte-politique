# Relire à la source quelques votes publiés, à chaque run (#1248) (2026-10-30)

`2026-10-30`

> **En bref** — premier contrôle du dépôt qui retourne à la source. À chaque run, dix scrutins publiés sont tirés (sept des trente derniers jours, trois sur tout le corpus) et chaque position est relue sur la page publique de l'Assemblée, personne par personne. Le contrôle signale sans bloquer, et tient une issue que le run ne ferme jamais. Un non-votant que la page nomme et que l'open data ne cite pas est une « divergence entre sources », listée sans issue. Sur trois tirages d'essai (30 scrutins, 30/10/2026) : 4 080 positions concordantes, 0 écart, 3 divergences.

## Contexte

#1248 (07/10/2026) : les seize audits du dépôt comparaient les données entre elles, aucun ne retournait à la source. Le contrôle devait tourner sans la propriétaire, lire **par une autre route** que la collecte, partir de ce qui est publié, et distinguer « non vérifié » de « différent ».

La seconde route est la page de scrutin du site de l'Assemblée (`/dyn/<législature>/scrutins/<n>`). C'est aussi le `source_url` publié au lecteur. Elle liste les votants **nommément** par position, avec leur identifiant de député, pour les quatre législatures du corpus (vérifié sur un scrutin de chacune). La collecte, elle, lit les archives open data.

## Décisions de la propriétaire, 30/10/2026

| Question | Réponse |
| --- | --- |
| Périmètre du lot 1 | les positions de vote, 10 scrutins par run, sans bloquer, issue en cas d'écart |
| Tirage | « 7 sur les 30 derniers jours et le reste sur tout ». Au hasard sur tout le corpus, 10 tirages donnaient 0,4 scrutin récent par run : 768 des 19 078 scrutins publiés dataient des trente derniers jours |
| Non-votant nommé par la page, absent de l'open data | **option B** : une divergence entre sources, listée à part, sans issue. L'option A (un écart) ouvrait une issue un run sur deux pour une cause connue |

## Ce que les essais ont établi

**Le scrutin 8705, signalé sur #1248 (503 « pour » sur la page, 501 chez nous), n'est pas un écart.** Les deux « pour » manquants sont les deux non-inscrits qui ont voté, Véronique Besse et Philippe Bonnecarrère. Le corpus ne collecte pas de profil pour les non-inscrits (`raw_data/non_inscrits.json` les nomme, avec `membre_id` nul). Les 568 autres positions concordent. D'où la comparaison **personne par personne** : un total aurait signalé cet écart qui n'en est pas un, et aurait pu en masquer un vrai qui l'aurait compensé.

**Un votant peut être nommé sans lien.** Sur le scrutin 3305, Manon Bouquin est écrite en texte (`<span>`), sans lien vers sa fiche. La première version ne lisait que les liens : elle a compté sept faux écarts sur deux scrutins. Le test porte un extrait copié de cette page.

**La divergence de la XVIe.** L'archive open data de la XVIe ne cite Yaël Braun-Pivet, présidente de l'Assemblée, que dans 357 de ses 4 106 scrutins. La page la nomme « non votant » partout. Notre profil reproduit l'archive : 350 positions `non_votant` sur la XVIe, contre 9 108 sur la XVIIe, dont l'archive la cite. Ce n'est pas une erreur de collecte, mais un fait que l'open data omet.

## Décision

`src/relecture_votes_source.py`, dans `merge-and-pivot`, après `validate_profil` :

| Cas | Verdict | Issue |
| --- | --- | --- |
| même position | concordant | — |
| position différente, position nommée par la page et absente chez nous, ou l'inverse | écart | oui |
| non-votant nommé par la page, avec profil, sans position chez nous | divergence entre sources | non |
| votant sans profil (non-inscrit) | hors périmètre | non |
| page injoignable, ou de forme inconnue | non vérifié | non |

- Les positions `absent` et `excuse` ne se comparent pas : la page ne liste pas les absents, et aucune page de présence n'est lue (§2 règle 3).
- La lecture s'arrête à la section « Mises au point » : ce qu'un député dit avoir voulu voter n'est pas le vote enregistré.
- La graine est le numéro du run.
- **Le run ne ferme jamais l'issue**, à la différence de celle de #1223. Un tirage sans écart ne dit rien des scrutins qu'il n'a pas tirés, donc rien de l'écart signalé avant.

## Alternatives écartées

- **Comparer les totaux** : voir le scrutin 8705 ci-dessus.
- **Rappeler le module de collecte** : ce serait la même route, et cela ne prouverait rien (#1248).
- **Bloquer le commit sur un écart** : un tirage au sort qui bloquerait rendrait les runs imprévisibles. C'est la même raison que pour #1223.

## Non vérifié, et suites

- Le contrôle est écrit par une session d'agent : son indépendance vient de la route, pas de l'auteur (#1248).
- Les pages de la XIVe ont été lues sur un seul scrutin (n° 6, trois non-votants nommés) ; leur forme sur les autres n'est pas mesurée. Une forme inconnue rend la page « non vérifiée », jamais un écart.
- Suites envisagées sur #1248 : les dates de mandat (fiche député), les signatures d'amendement.
