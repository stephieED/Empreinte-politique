# La table des groupes se met à jour depuis AMO30, sans réécrire ce qui est nommé (#1168, lot 2a)

`2026-10-02`

> **En bref** — `groupes_amo30.py --mettre-a-jour` rapporte la dérivation à une table existante et rend la table **complétée** : un organe renommé rejoint son groupe, un groupe nouveau entre avec son lien calculé **une fois** et sa lignée, les champs que la source dit (noms successifs, position, effectif) se rafraîchissent — et **rien de ce qui est nommé n'est réécrit** (sigle publié, identifiants, `succede_a`). Demandé par la propriétaire le 02/10/2026 : « que les lignées ne soient reconstruites que lorsqu'il y a un nouveau groupe ». Éprouvé en repartant d'une table qui ne connaît que la XVe : la mise à jour ajoute **21 groupes** et retrouve **32 groupes sur 32, 17 liens sur 17, 15 lignées sur 15**. Sur la table d'aujourd'hui et l'archive du 02/10/2026, elle ne change qu'**un effectif** (`LIOT-17`, 26 → 27) et signale `NG`/`SOC` à fusionner. **Aucun job ne l'appelle** : c'est le lot 2a. Constat qui commande la suite : le run ne peut rien écrire dans `config/`, recopié du dépôt privé à chaque run — la table tenue par le run devra vivre dans `raw_data/`, comme celle des gouvernements.

## Le problème

Le lot 1 dérive les groupes et leurs lignées de la source seule. Un run ne peut
pas publier cette dérivation telle quelle : elle n'a ni sigle publié, ni adresse
de page, et la recalculer à chaque run laisserait un lien bouger sans relecture.

La propriétaire a posé les deux contraintes le 02/10/2026 : un groupe nouveau
s'ajoute seul ; les lignées ne se reconstruisent que pour un groupe nouveau.

## Ce qui est décidé

`mettre_a_jour_table(document, index)` est une fonction pure : elle rend une
copie complétée et un journal. Trois règles, dans cet ordre.

| Règle | Ce qu'elle couvre |
| --- | --- |
| Ce qui est nommé ne se réécrit jamais | `groupe_sigle`, `groupe_id`, `groupe_nom`, `lignee_id`, `lignee_nom`, `fichier`, `succede_a`, les notes écrites à la main |
| Ce que la source dit se rafraîchit | `historique_organes_an`, `position_politique_an`, `effectif_amo30` — sur les organes que l'entrée porte déjà |
| Un organe que la table ignore y entre | dans le groupe dont il est le renommage ; sinon comme groupe nouveau |

**Un groupe nouveau** reçoit pour sigle le **premier** sigle que l'Assemblée lui a
donné : c'est celui qu'un run aurait vu le jour de sa naissance, et l'identifiant
ne dépend donc pas du moment où le groupe entre. Son lien vers la législature
précédente est celui que la règle de la moitié trouve, écrit avec `succede_a` ;
il hérite de la lignée de son prédécesseur, ou ouvre la sienne.

## Ce qui ne se tranche pas reste dehors

| Journal | Cas | Ce que fait la mise à jour |
| --- | --- | --- |
| `en_attente` | aucun mandat n'a commencé dans le groupe (jour de l'ouverture) | n'ajoute rien ; le run suivant le verra |
| `non_tranches` | le groupe succède à des groupes de **deux lignées** | n'ajoute rien : choisir sa page serait choisir à la place de la source |
| `non_tranches` | l'identifiant ou l'identifiant de lignée est déjà pris | n'ajoute rien, sortie 1 |
| `a_fusionner` | deux entrées de la table sont un seul groupe renommé | signale, ne fusionne pas |

`AGENTS.md` §2 règle 5 : une absence est déclarée, jamais comblée.

## Ce que la mesure donne

Archive AMO30 publiée le 02/10/2026 à 02:34.

**Sur la table d'aujourd'hui (32 entrées)** : un champ rafraîchi — l'effectif de
`LIOT-17`, 26 → 27 — et un signalement, `AN:NG:15` et `AN:SOC:15` à fusionner.
Appliquée à sa propre sortie, elle ne change plus rien.

**En repartant d'une table qui ne connaît que la XVe (12 entrées)** :

| | Reconstruit | Table d'aujourd'hui |
| --- | ---: | ---: |
| Groupes ajoutés | 21 | — |
| Groupes identiques (mêmes organes) | **32** | 32 |
| Liens identiques | **17** | 17 |
| Lignées identiques (mêmes organes) | **15** | 15 |

Aucun cas non tranché, aucun en attente. **Ce qui diffère, ce sont les noms** :
cinq identifiants prennent le sigle de l'Assemblée au lieu du nôtre —
`AN:RE:16` pour `AN:REN:16`, `AN:LFI-NUPES:16`, `AN:GDR-NUPES:16`,
`AN:LFI-NFP:17`, `AN:AD:17` pour `AN:UDR:17`. C'est attendu : un nom ne se dérive
pas, et c'est pourquoi les 32 entrées existantes gardent les leurs.

## Le constat qui commande la suite : `config/` est du code

`.github/actions/code-du-prive` recopie tout le dépôt privé sur le checkout du
run, **sauf** `pivot_data/` et `raw_data/`, avec `rsync --delete`. Un fichier que
le run écrirait dans `config/` serait publié, puis écrasé au run suivant.

Donc la table que le run tient à jour doit vivre dans `raw_data/` — c'est ce que
fait déjà `raw_data/gouvernements_reels.json` (#1129). `config/groupes_reels.json`
devient son point de départ. Ce déplacement touche tous les lecteurs de la table
et `generate-data.yml` : c'est le lot 2c, pas celui-ci.

## Ce qui reste du lot 2

| Sous-lot | Contenu | Pourquoi à part |
| --- | --- | --- |
| 2b | fusionner `NG` et `SOC` de la XVe (arbitré le 02/10/2026 : « la même règle pour tout le monde ») et retirer `groupe-AN-NG-15.json` | une fiche publiée disparaît : le contrôle de perte bloque un fichier qui s'en va, il faut un retrait nommé |
| 2c | la table vit dans `raw_data/`, un job la met à jour, les lecteurs la lisent là | touche `generate-data.yml`, publié à la main sur le dépôt public |

## Ce qui reste ouvert

- **Le nom affiché d'un groupe entré seul ne suit pas un renommage ultérieur** :
  `groupe_nom` est écrit à l'entrée et n'est plus touché. Les noms successifs,
  eux, sont dans `historique_organes_an`, qui se rafraîchit. À arbitrer.
- **Un sigle de l'Assemblée publié tel quel** (`LFI-NUPES`, `UDI_I`) : ce que
  l'interface en fait n'a pas été regardé.
- **La borne à la XVe** (point C du plan).

## Alternatives écartées

- **Recalculer tous les liens à chaque run.** `SOC-15 → SOC-16` est à 17 sur 31 ;
  un lien pourrait apparaître ou disparaître sans relecture, et la propriétaire a
  demandé l'inverse.
- **Fusionner d'office deux entrées que la règle réunit.** Cela retire une fiche
  publiée ; un retrait se nomme et se vérifie, il ne se fait pas en passant.
- **Choisir la lignée la plus recouvrante pour un groupe issu de deux.** Ce
  serait un classement que la règle ne porte pas.
