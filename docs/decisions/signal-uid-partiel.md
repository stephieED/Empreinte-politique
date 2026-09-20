<a id="signal-uid-partiel"></a>
# Couverture `uid` partielle : ce qui manquait n'était pas un verrou, c'était un signal (#447) (2026-08-19)

`2026-08-19`

> **En bref** — ce qui manquait sur la couverture `uid` partielle n'était pas un verrou, c'était un signal.

Le défaut de #450 a mis deux jours à être identifié, et il a d'abord été pris
pour de l'instabilité de collecte. La raison tient en une phrase : **rien ne le
signalait**. Ni les logs d'extraction — les 8 shards imprimaient la ligne
attendue — ni `merge-and-pivot`, qui annonçait « Total of 8 artifact(s)
downloaded », ni la quality gate, qui ne regardait que le *nombre* d'amendements
et jamais leur forme. Le run se terminait en `success`, et le seul symptôme
visible était un volume qui montait.

C'est le même mode d'échec que #185 (« amendements[] vide partout, détecté par
aucune section ») et que l'index absent qui « fait disparaître les amendements en
silence » : ce dépôt traite une panne muette comme un défaut à part entière, pas
comme un désagrément.

## La mesure ajoutée (§3c)

Pour chaque profil pivot AN, la §3c compte désormais les amendements portant un
`uid`, et classe :

- **100 %** — profil sur la clé corrigée de #440 ;
- **0 %** — profil entièrement sur l'ancienne clé : en retard de correction, pas
  dupliqué. C'est une frontière de conquête, **pas** un fait faux ;
- **partiel** — les deux versions du même amendement cohabitent. L'entrée est
  comptée deux fois, ce qui fausse les dénominateurs publiés (AGENTS.md §2.7).

Seul le cas **partiel** déclenche un avertissement. Signaler aussi les profils à
0 % noierait le signal utile sous les 119 profils qui attendent simplement leur
régénération — c'est exactement ainsi qu'un signal cesse d'être lu.

Un taux global (`dont uid : N (X %)`) accompagne le tout : c'est lui qui dit si
une re-mesure de #429 est exploitable, le comptage d'amendements distincts
reposant sur l'`uid`. Au 19/08/2026 : 229 254 / 727 132, soit 31,5 % — donc
non exploitable en l'état.

## Pourquoi soft, et pas un refus d'écriture

L'issue demandait « un contrôle qui refuse d'écrire un profil dont les
amendements sont partiellement sans `uid` ». Deux raisons de ne pas le faire là :

1. **Le mélange ne naît pas à l'écriture.** Chaque job écrit un profil homogène ;
   c'est la fusion des artifacts qui réunit les deux versions (#450). Un garde
   posé sur l'écriture ne verrait jamais le cas qu'il vise.
2. **Pendant la remise en état, les profils mixtes sont attendus.** Un échec dur
   bloquerait précisément les runs censés les corriger — le quality gate refuse
   le commit, donc la correction ne serait jamais committée.

La §3c est soft dans son entier depuis #378, pour une raison voisine. Ce qui
manquait n'était pas un verrou, c'était un signal : la §3c le rend visible dans
la console, dans le résumé Markdown, et en `::warning::` GitHub Actions.

