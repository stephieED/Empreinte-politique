<a id="budget-roster-mesure"></a>
# Budget CI de `extract-roster-groupes` : mesure réelle (#376) (2026-08-17)

`2026-08-17`

> **En bref** — budget CI de `extract-roster-groupes` mesuré, à la place d'un `timeout-minutes` provisoire.

**Contexte** : le `timeout-minutes: 60` de ce job était marqué « provisoire »
depuis sa création, sans aucune mesure de débit — contrairement aux
amendements, qui avaient eu leur spike dédié
([[amendements-index-budget-ci-cache-granularite]]).

**Protocole** : extraction légère telle que la CI l'exécute
(`--skip-interventions --skip-dossiers-legislatifs`, `--workers 1`), deux
échantillons **aléatoires** du roster (`--sample`, pas `--limit` : les 20
premiers déterministes auraient pu biaiser par l'ordre du fichier source).
Volontairement **sans** `--skip-existing` : on mesure le coût de traitement
réel d'un membre, c'est-à-dire le cas d'un run à pleine échelle où presque
tout est à collecter.

| Échantillon | Temps | RSS max |
|---|---|---|
| N=8 | 137,9 s | 1,54 Go |
| N=16 | 231,7 s | 1,48 Go |

**Modèle** : `T(N) ≈ 44 s + 11,7 s × N` (44 s de coût fixe, 11,7 s par membre).

**Projections** : roster complet (752 membres) ≈ **148 min** ; restant à
collecter (688) ≈ 135 min. Le timeout de 60 min couvre
`(3600 − 44) / 11,7 ≈ **300 membres**`, soit 15× la valeur par défaut de
`roster_extraction_limit` (20, qui coûte ~5 min).

**Décision — timeout inchangé à 60 min**, mais le commentaire passe de
« provisoire » à *mesuré*, avec ce que la valeur couvre réellement. L'inflater
pour faire tenir un run complet aurait entériné le gaspillage décrit
ci-dessous au lieu de le corriger.

**Le vrai blocage n'est pas le timeout** : **93 % du coût par membre est la
relecture de l'index amendements** (10,9 s sur 11,7 s). `fetch_amendements_officiels`
relit 673 Mo de JSON à *chaque* candidat, soit ~500 Go de parsing sur un run
complet — et ce coût est payé même pour les candidats sans aucun amendement
(48 profils sur 90 en ont). Suivi dans #392, prérequis technique du passage à
pleine échelle.

**Point 4 de l'issue — `--skip-existing --resume` suffit-il à borner la perte
en cas d'échec ?** Non, et c'est vérifiable : le fichier de point de
sauvegarde (`raw_data/profiles/.generation_checkpoint.json`) est **gitignoré**,
donc `--resume` ne sert qu'à l'intérieur d'un même run, jamais entre deux.
Entre runs, la seule progression préservée est celle des profils effectivement
committés par `merge-and-pivot`. Or si le job roster est préempté, son
`Upload artifact` en `if: always()` ne s'exécute pas ([[resilience-generate-data-shutdown-signal]],
angle mort #228) : rien n'atteint `merge-and-pivot`, rien n'est committé, et
**toute la progression du run est perdue**. À 20 membres (~5 min) c'est
indolore ; à 300 (~60 min) beaucoup moins. Le sharding (#347) garde donc sa
justification — mais elle tient à la **résilience**, pas au coût CPU, que
#392 traite séparément.

**Point 5 — recalibrage de `--groupe-min-coverage-pct`** : impossible à ce
stade, et pour la même raison qu'en 2026-08-12 ([[seuil-couverture-groupe]]) —
il faudrait des taux de couverture issus d'un run à pleine échelle, qui reste
bloqué par #392. Non traité plutôt que fixé dans le vide.

**Limite de cette mesure, assumée** : réalisée en local, pas sur un runner
GitHub hébergé — chemin réseau différent. Elle reste représentative sur le
poste dominant (la relecture d'index est CPU/disque, pas réseau), mais les
appels réseau résiduels (~0,8 s/membre) pourraient différer en CI. Même
réserve que celle déjà consignée pour le spike amendements.

