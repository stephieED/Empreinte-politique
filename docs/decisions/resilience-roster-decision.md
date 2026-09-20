<a id="resilience-roster-decision"></a>
# Résilience de `extract-roster-groupes` : le sharding reste nécessaire (#347) (2026-08-17)

`2026-08-17`

> **En bref** — le sharding de `extract-roster-groupes` reste nécessaire, chiffres à l'appui.

**Contexte** : #347 demandait de trancher, *avec des chiffres*, si une
stratégie de sharding restait nécessaire une fois le coût par membre réduit,
ou si `--skip-existing --resume` suffisait. Ses deux prérequis (mode léger
#357, retrait de `synthese_activite` #356) et la mesure de budget (#376) sont
livrés ; #392 a ensuite divisé le coût marginal par 2,3.

**Re-mesure après #392** (même protocole que [[budget-roster-mesure]] :
extraction légère, `--workers 1`, échantillons aléatoires) :

| | Coût marginal | Roster complet (752) |
|---|---|---|
| Avant #392 | 11,7 s | ≈ 148 min |
| **Après #392** | **5,05 s** | **≈ 63 min** |

*Correction d'une extrapolation erronée* : après #392 j'avais annoncé ~15 min
pour un run complet, en déduisant le coût résiduel de la différence
`11,7 − 10,9`. C'était faux. La lecture d'amendements mesurée isolément
(10,9 s) surestimait sa part dans un run réel, où le cache de pages du
système amortit les relectures. Seule la mesure de bout en bout fait foi :
**5,05 s/membre**, pas ~1 s.

**Décision — point 3 : oui, le sharding reste nécessaire, mais pas pour la
raison d'origine.** Deux problèmes distincts subsistent :
1. **63 min dépasse le timeout de 60 min.** 60 min couvrent ~712 des 752
   membres — un run complet ne tient pas d'un seul tenant.
2. **Une préemption fait perdre tout le job.** Vérifié : le checkpoint
   `--resume` (`raw_data/profiles/.generation_checkpoint.json`) est
   **gitignoré**, donc il ne sert qu'à l'intérieur d'un run, jamais entre
   deux ; et l'`Upload artifact` en `if: always()` ne s'exécute pas sur
   `shutdown signal` (angle mort #228). Rien n'atteint `merge-and-pivot`,
   rien n'est committé. La réponse à « `--skip-existing --resume` suffit-il ? »
   est donc **non**, et ce indépendamment du coût.

À la limite actuelle (20 membres, ~1,7 min) aucun des deux ne mord : le
sharding n'est nécessaire **que** pour le passage à l'échelle. Conception
reportée dans #394 plutôt que traitée ici, conformément au « hors périmètre »
que #347 s'était donné (pas de conception détaillée avant que le passage à
pleine échelle soit décidé, #192).

**Décision — point 4 : `roster_extraction_limit` par défaut inchangé à 20.**
Le faire passer à 0 *serait* la décision de passer à pleine échelle, qui
appartient à #192. La description de l'input porte désormais les coûts
mesurés (1,7 min à 20 · 25 min à 300 · 59 min à 700 · 63 min à 752) et
indique que le timeout actuel autorise une montée progressive jusqu'à ~700
sans rien changer d'autre — l'information nécessaire à la décision, sans la
prendre.

**Commentaire de budget mur** mis à jour avec les deux jeux de mesures
(avant/après #392) et ce que le timeout couvre réellement.

