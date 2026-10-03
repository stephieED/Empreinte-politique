# Un audit propose les filiations de groupe, et la table reste écrite à la main (#1168)

`2026-10-02`

> **En bref** — `src/audit_filiation_lignees.py` compare les liens `succede_a` de `config/groupes_reels.json` à la composition des groupes lue dans AMO30, selon le critère arbitré le 02/10/2026 (personnes communes sur l'effectif du **plus petit** des deux groupes, à partir de la moitié). **Il n'écrit rien et ne publie rien** : il nomme un lien déclaré que la composition ne soutient plus, un couple qui passe le seuil sans être déclaré, un organe de l'Assemblée sans entrée. Trois précisions que la mesure a imposées et que le critère ne disait pas : l'unité est le **groupe** (union de ses organes), les **non-inscrits sont exclus** — avec eux, 34 couples d'organes passent le seuil à tort —, et un groupe sans membre connu n'est **pas mesuré**. Mesuré sur l'archive AMO30 publiée le 02/10/2026 à 02:34, et sur celle du cache (17/08/2026), aux résultats identiques : **17 liens déclarés retrouvés sur 17**, aucun couple proposé à tort, plus bas retrouvé **55 %** (17 sur 31), plus haut écarté **39 %** (12 sur 31, `NG-15 → SOC-16`) — et non 36 %, le chiffre consigné jusque-là. « Proposer ou publier » reste à arbitrer.

## Le problème

Les liens qui composent les lignées sont écrits à la main, et rien ne signalait
qu'un lien déclaré ne tenait plus, qu'un lien manquait, ou que l'Assemblée avait
ouvert un groupe que la table ignore — la question 4 de #1168. Le critère de
comparaison a été arbitré le 02/10/2026 (PR #1170) ; il n'en existait aucune
implémentation.

## Ce qui est décidé

Un audit, et seulement un audit. `auditer_filiation()` est une fonction pure ;
`rapport_filiation()` charge la table committée et l'index des groupes. La table
reste la seule chose que `succession_publiee()` lit, `etabli_par` reste
`relecture_humaine`, et aucun `lignee_id` ne peut bouger (#836).

| Rubrique du rapport | Écart ? |
| --- | --- |
| lien déclaré sous le seuil | oui |
| couple au seuil ou au-dessus, non déclaré | oui |
| couples non déclarés les plus proches du seuil | non — la marge |
| organe de groupe sans entrée dans la table | non — nommé |
| lien dont un côté n'a aucun membre connu | non — nommé |

Le seuil est une constante (`SEUIL_NUMERATEUR`, `SEUIL_DENOMINATEUR`), comparée
en entiers, et **pas une option** : une option inviterait à le rouvrir à chaque
lecture.

## Trois précisions que le critère ne disait pas

**L'unité est le groupe, pas l'organe.** La mesure du 02/10 comptait des paires
d'organes (19 entre législatures). Un groupe renommé tient en plusieurs organes
— `SOC`/`SOC-A`, `MODEM`/`DEM` — et l'audit prend leur union, résolue par sigle
comme le roster (`an_roster.organes_du_groupe`). Un organe que la table ignore
est comparé seul. Au niveau du groupe, les 17 liens déclarés sont 17 mesures.

**Les non-inscrits sont exclus.** Presque tous les députés passent par `NI` à
l'ouverture d'une législature (592 personnes en XVIe, 640 en XVIIe). Mesuré sur
les paires d'organes des XVe-XVIIe :

| Périmètre | Couples comparés | Déclarés retrouvés | Proposés à tort |
| --- | ---: | ---: | ---: |
| avec `NI` | 372 | 19 sur 19 | **34** |
| sans `NI` | 319 | 19 sur 19 | 0 |

L'exclusion était faite dans la mesure d'origine (« hors NI », dans #1168) et
n'était pas écrite dans la règle.

**Un groupe sans membre connu n'est pas mesuré.** Ni retrouvé, ni manqué
(`AGENTS.md` §2 règle 5). Le cas est réel : l'archive réduite des tests porte les
organes de la XVe sans leurs mandats.

## Ce que la mesure corrige

| Chiffre consigné le 02/10 | Remesuré |
| --- | --- |
| plus haut couple écarté : 36 % (`UDI-AGIR-15 → LIOT-16`) | **39 %**, 12 sur 31 (`NG-15 → SOC-16`) |
| marge sous le seuil : 14 points | **11 points** ; 5 au-dessus, inchangé |

`NG-15 → SOC-16` n'est pas un candidat ordinaire : `NG` devient `SOC` **dans** la
XVe (30 des 33 membres de `NG`), et la table écrit ce renommage comme une
succession. L'audit le marque `meme_legislature` sans le trancher. Rattaché à
`SOC-15` comme organe, il disparaîtrait de la liste des écartés.

## Ce que l'audit ne tranche pas

- **Proposer ou publier** (question 3 de #1168) : à la propriétaire.
- **Les sept organes de la XVe sans entrée** — `LC`, `UDI-AGIR`, `UDI-I`,
  `UDI-A-I`, `UDI_I`, `LT`, `AGIR-E`. Ils sont nommés et ne comptent pas comme
  écart : les compter rendrait l'audit rouge en permanence, et rien dans la table
  ne permet aujourd'hui de dire qu'une absence est voulue. Conséquence assumée :
  un groupe ouvert demain par l'Assemblée sera **listé**, pas signalé en erreur.
- **Les renommages dans une législature** : mesurés dans #1168 (81-100 % contre
  43 % et moins), non exploités ici.
- **Les législatures antérieures à la XVe** : la règle n'y a pas été éprouvée, et
  l'audit se borne aux législatures que la table couvre.

## Alternatives écartées

- **Une option `--filiation` dans `an_roster.py`**, au patron de `--positions`.
  Le module dérive un roster ; la comparaison de deux rosters est un autre objet,
  et il porte déjà 1 455 lignes.
- **Un bloc du portail de qualité.** L'archive AMO30 n'est pas lue par l'étape
  qui génère les fiches (#686), et un lien que la composition ne soutient plus
  demande une relecture, pas un échec de run.
- **Passer par `charger_index_gp` pour une archive nommée.** Il réécrit l'index
  du cache partagé à la taille de l'archive passée : l'essai sur l'archive
  réduite a fait tomber l'index commun de 2 119 acteurs à 833. Une archive nommée
  est lue par `construire_index_gp`, sans cache.

## Sur quelle archive

Deux, lues l'une après l'autre le 02/10/2026 : celle du cache partagé (17/08/2026,
13 597 729 octets) et celle que l'Assemblée publie ce jour (02:34, 13 618 930
octets), téléchargée à part et passée par `--archive`. **Mêmes 17 liens, mêmes
décomptes**, à une personne près sur un effectif : `LIOT-17` fait 26 personnes
dans la première, 27 dans la seconde — le lien `LIOT-16 → LIOT-17` reste à 14 sur
22, sa base étant le départ.
