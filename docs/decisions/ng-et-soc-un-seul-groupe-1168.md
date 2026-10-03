# `NG` et `SOC` de la XVe sont un seul groupe, et une fiche se retire par son nom (#1168, lot 2b)

`2026-10-02`

> **En bref** — arbitré par la propriétaire le 02/10/2026 : « on applique la même règle pour tout le monde, on ne va pas commencer à faire des exceptions ». `Nouvelle Gauche` ferme le 11/09/2018, `Socialistes et apparentés` ouvre le 12 avec **30 personnes communes sur 33** : c'est un renommage, comme `MODEM`/`DEM`, et la table l'écrivait comme deux groupes reliés par un `succede_a`. L'entrée `AN:NG:15` rejoint `AN:SOC:15`, qui porte les deux organes et **39 personnes** ; la dérivation et la table sont désormais **identiques** (15 lignées, 31 groupes, 16 liens). La fiche `groupe-AN-NG-15.json` doit partir, et depuis le modèle à deux dépôts une donnée ne change que par un run : le retrait est **déclaré** dans `fiches_retirees[]` et appliqué par `generate_group_profiles.py`, **seulement si la fiche remplaçante porte les organes et tous les membres de la fiche retirée**. Essai réel hors dépôt : fiche réunie à 39 membres, aucun perdu, et la fiche de lignée ressort **identique en tout** sauf ses maillons (4 → 3). **Le run qui porte ce retrait se lance avec `allow_declared_losses=true`.**

## Le problème

Le lot 1 a montré un seul désaccord entre la règle et la table : `NG` et `SOC`
de la XVe. Deux fiches publiées, un `succede_a` — le seul de la table à relier
deux groupes d'une **même** législature — et un couple `NG-15 → SOC-16` à 12 sur
31 qui restait le plus haut écarté de l'audit, parce que `NG` était comparé seul.

Réunir les deux dans la table ne suffit pas. Un groupe sorti de `groupes[]`
n'est plus régénéré, mais **son fichier reste** : rien ne le supprime, et le
portail de qualité bloque alors sur « fiche de groupe publiée sans entrée »
(mesuré : c'est exactement ce qu'il rend avec la table réunie et la fiche encore
là). Et depuis le modèle à deux dépôts, les données ne se modifient que par un
run sur le dépôt public — le retrait ne peut pas être fait à la main.

## Ce qui est décidé

**La table.** `AN:SOC:15` porte `sigles_an: ["NG", "SOC"]`, les deux organes,
les deux noms dans `historique_organes_an`, la position `opposition` (les deux
organes s'accordent), 39 personnes. Son `succede_a` disparaît. L'entrée
`AN:NG:15` sort de `groupes[]` et de la table. La lignée `AN:LIGNEE:SOC` garde
son identifiant, donc son adresse.

**Le retrait, nommé.** Une clé `fiches_retirees[]` dans
`config/groupes_reels.json` : le fichier, le groupe, celui qui le remplace, la
date, le motif. `charger_fiches_retirees()` refuse un nom qui n'est pas une
fiche de groupe nue (ni chemin, ni remontée), une fiche que `groupes[]` déclare
encore, un remplaçant inconnu.

**La garde.** `generate_group_profiles.py` applique les retraits **après** la
génération, et `motif_de_refus_du_retrait()` ne laisse partir une fiche que si
celle qui la remplace porte :

- chacun de ses organes (`historique_noms[].organe_an`) ;
- chacun de ses membres (`membres[].membre_id`).

Refusé, le retrait laisse la fiche, émet `FICHE_NON_RETIREE`, et le portail
bloque : un retrait qui échoue arrête la publication, il ne publie pas un corpus
amputé. Une fiche déjà absente n'est ni retirée ni refusée — la déclaration
reste dans la table comme la trace du retrait.

## Pourquoi cette garde, et pas le contrôle de perte

Le contrôle de perte compare des cardinalités à un attendu. Ici la disparition
est voulue : il la verra de la même façon quel que soit le fichier retiré. La
garde est donc d'une autre nature — elle lit dans les deux fiches que rien de ce
que l'ancienne portait ne manque à la nouvelle.

Sur les fiches publiées aujourd'hui, elle **refuse** : `SOC-15` ne porte pas
l'organe `PO730946`. C'est le comportement attendu avant le run.

## Ce que l'essai réel donne

Génération lancée hors dépôt le 02/10/2026, sur les profils du dépôt privé et
l'archive AMO30 du cache, dans un répertoire temporaire.

| Fiche de groupe | `NG-15` publiée | `SOC-15` publiée | `SOC-15` réunie |
| --- | ---: | ---: | ---: |
| membres | 33 | 36 | **39** (l'union ; aucun manquant) |
| scrutins de cohésion | 4 130 | 4 182 | 4 208 |
| mandats agrégés | 287 | 385 | 406 |
| noms successifs | 1 | 1 | 2 |

La fiche `groupe-AN-NG-15.json` a été retirée par la garde, et elle seule.

| Fiche de lignée `AN:LIGNEE:SOC` | Publiée | Régénérée |
| --- | ---: | ---: |
| maillons | 4 | **3** |
| membres | 96 | 96 |
| scrutins de cohésion | 16 420 | 16 420 |
| mandats agrégés | 668 | 668 |
| tags thématiques | 1 739 | 1 739 |
| amendements distincts | 61 255 | 61 255 |

Le lecteur de la page ne perd rien : seule la liste des maillons raccourcit.

## Ce que le run dira, et ce qu'il faut lui donner

Deux pertes **bloquantes**, et elles sont attendues :

| Perte que le contrôle verra | Pourquoi |
| --- | --- |
| `pivot_data/groupes/groupe-AN-NG-15.json` a disparu | le retrait |
| `lignee-AN-SOC.json` : `maillons` 4 → 3 | la lignée compte une fiche de moins |

Le run se lance donc avec **`allow_declared_losses=true`**. Toute autre perte
signalée ce jour-là n'est pas celle-ci et se lit à part. Un run programmé, qui
ne reçoit aucun input, **échouera** sur ces deux pertes sans rien publier.

## Ce que ça change pour l'audit

Le plus haut couple écarté n'est plus `NG-15 → SOC-16` (12 sur 31) mais
`UDI-15 → LIOT-16` (8 sur 22) : la marge sous le seuil revient à 14 points. Les
liens déclarés passent de 17 à **16**, tous entre deux législatures.

## Alternatives écartées

- **Supprimer d'office toute fiche que la table ne nomme plus.** Une table mal
  fusionnée emporterait une fiche sans que personne l'ait décidé.
- **Laisser le contrôle de perte accepter seul les retraits déclarés.** Chaque
  tolérance de ce contrôle est cloisonnée, et `allow_declared_losses` est le
  geste prévu : retirer une fiche publiée mérite qu'un humain lance le run.
- **Garder deux fiches et écrire une exception dans la règle.** Écarté par la
  propriétaire.

## Ce qui n'a pas été vérifié

- L'essai a tourné sur les profils du dépôt **privé**, qui peuvent être en retard
  sur ceux du public : les décomptes du run peuvent différer de quelques unités.
- Le comportement de l'interface entre la fusion de ce lot et le run. Cherché :
  aucune occurrence de `AN:NG:15` ni de `groupe-AN-NG` dans `web/UI_finale/src` —
  elle lit les fiches de groupe par la liste des maillons de la lignée, que le
  run réécrit en même temps.
