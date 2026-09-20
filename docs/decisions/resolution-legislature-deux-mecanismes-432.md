# Résoudre la `legislature` d'un vote : deux mécanismes, pas un seul (#432) (2026-08-19)

`2026-08-19`

> **En bref** — résoudre la `legislature` d'un vote demande deux mécanismes — jumeau étiqueté puis calendrier — jamais un défaut.

`votes[].numero_scrutin` repart à 1 à chaque législature ([[votes-multi-legislature]],
#403) : la clé d'un scrutin est `(legislature, numero_scrutin)`. Toute
normalisation des votes en dépend — or **89 687 votes sur 398 085 (22,5 %),
répartis sur 83 profils, ne portent aucune législature**. Ils viennent du chemin
de collecte antérieur à #403, qui n'interrogeait qu'une législature et ne
renseignait donc pas le champ.

Le coût de ne rien faire est chiffrable : la clé compte alors **21 520** scrutins
« distincts » là où il n'y en a que **17 422** — 23 % de sur-comptage, et 4 098
scrutins stockés deux fois dans la liste dédupliquée qu'introduit #432. Combler
`legislature` est donc un préalable, pas un nettoyage de confort.

## Deux mécanismes, parce qu'ils ne sont pas de même nature

**1. Jointure sur un jumeau étiqueté.** Le même scrutin — même
`(numero_scrutin, date)` — apparaît ailleurs dans le corpus **avec** sa
législature. Ce n'est pas une inférence, c'est une **résolution** : la donnée
existe déjà, étiquetée, dans un autre profil. Mesuré : **4 098 des 4 104**
paires, **zéro ambiguïté** — aucune paire ne porte deux législatures différentes.

Ce mécanisme est nécessairement **global au corpus**, et c'est le point non
évident : un profil est soit entièrement sur l'ancien chemin de collecte, soit
entièrement sur le nouveau. Les deux formes ne coexistent jamais dans le même
fichier, donc le jumeau vit toujours **ailleurs**. Une résolution profil par
profil ne trouverait rien.

**2. Calendrier des législatures**, pour les 6 paires restantes. Datées du
25/11/2022 au 16/12/2023, elles sont en plein XVI, à plus de six mois de la
dissolution de juin 2024 : aucune zone grise. C'est une **dérivation**, et elle
est tracée comme telle (`derivee_du_calendrier`) — jamais présentée comme
collectée.

**3. Tout le reste échoue bruyamment.** Aucune valeur par défaut, aucun
rattachement à « la législature la plus probable » (AGENTS.md §2.5). Sont
irrésolubles : une date hors de tout intervalle connu, une date absente ou
malformée, un jumeau contradictoire, et une législature collectée absente du
calendrier — ce dernier cas signalant un calendrier à étendre, pas une donnée à
corriger.

## Le trou de cinq semaines

La XVI se termine à la dissolution du **09/06/2024**, la XVII ouvre le
**18/07/2024**. Les cinq semaines qui les séparent n'appartiennent à **aucune**
législature. Un vote qui y serait daté échoue, plutôt que d'être rattaché au
voisin le plus proche — c'est exactement le genre de trou qu'un repli silencieux
comblerait en inventant une donnée.

Pour la même raison la XVII est laissée **ouverte** (`fin=None`) plutôt que
bornée à une date lointaine : une borne factice se périmerait sans bruit le jour
d'une dissolution, et rattacherait alors des votes de la XVIII à la XVII.

## Le calendrier a été validé contre les données, pas seulement contre l'usage

Confronté aux **308 398 votes qui portent déjà leur législature** : aucun ne
tombe hors de l'intervalle de la sienne.

| Législature | Calendrier | Étendue réelle des votes |
| --- | --- | --- |
| 14 | 2012-06-20 → 2017-06-20 | 2012-07-03 → 2016-11-22 |
| 15 | 2017-06-21 → 2022-06-21 | 2017-07-04 → 2022-02-24 |
| 16 | 2022-06-22 → 2024-06-09 | 2022-07-11 → 2024-06-07 |
| 17 | 2024-07-18 → en cours | 2024-10-08 → 2026-07-21 |

Un test vérifie en outre que les dates d'ouverture concordent avec
`couverture_dossiers.LEGISLATURES_DEBUT`, déjà présent au dépôt : deux
calendriers qui divergeraient rattacheraient les votes et les textes à des
périodes différentes, sans que rien ne le signale.

## Résultat sur le corpus (19/08/2026, `e42631a`)

| | Scrutins | Paires (membre, vote) |
| --- | --- | --- |
| collectée | 17 416 | 308 398 |
| résolue par jumeau étiqueté | — | 89 671 |
| dérivée du calendrier | 6 | 16 |
| **irrésoluble** | **0** | **0** |

4 profils seulement dépendent d'une dérivation calendaire, pour 16 paires.

## Ce que la résolution ne change pas — vérifié

Les 89 687 votes sans législature se résolvent **tous** en « 16 ». Or
`group_profile._votes_de_legislature` conserve aujourd'hui un vote sans
législature pour **n'importe quelle** législature de groupe (`v.get("legislature")
or legislature`). Comme tous les groupes existants sont de la XVI, la cohésion
reste donc **identique** après résolution — c'est le critère d'acceptation de
#432, satisfait par construction et non par chance.

Ce repli cache en revanche un **défaut latent** : un groupe de la XVII
absorberait ces 89 687 votes de la XVI. Il ne sera retiré qu'avec la
normalisation elle-même — le retirer avant, sur des données non encore résolues,
supprimerait 89 687 votes de la cohésion de la XVI, ce qui serait une régression.

## Pourquoi une passe séparée, qui n'écrit rien

`src/audit_legislature_votes.py` ne modifie aucun fichier et rend un code de
sortie. Un chantier qui découvrirait ses cas irrésolubles **au milieu** d'une
migration de schéma devrait la défaire ; ici, on le sait avant de commencer.
Même raison d'être que [[budget-roster-mesure]] : mesurer avant de généraliser.

