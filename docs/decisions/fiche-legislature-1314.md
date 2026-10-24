# La fiche d'une législature lit les fichiers par objet de Backend, et un seul adaptateur (#1314)

`2026-10-22`

> **En bref** — La fiche `/legislatures/<n>` montre le travail de l'Assemblée sur une législature, en cinq sections arbitrées en maquette les 21 et 22/10/2026 (https://claude.ai/artifact/BHyLiaMR5m1TwbsfHFgVFV) : En bref, Qui siégeait, Les textes de la législature, Le travail des commissions, Ce qu'on n'a pas pu lire. **Elle lit les fichiers par objet que Backend publie** (#1325) : `pivot_data/legislatures.json` et `pivot_data/dossiers_an/<n>.json`, joints à `textes_promulgues.json` et `commissions_dossiers.json`. L'interface ne recalcule que les mots des titres du nuage. Tant que ces fichiers manquent, aucune législature n'entre dans le manifeste. Les noms de champs ne sont lus qu'à un endroit, `web/UI_finale/src/utils/legislature.js`.

## Le problème

La maquette lisait trois sources hors du dépôt : l'archive XVIe des dossiers
législatifs (titre, étape, initiateur, date de dépôt de chaque dossier), l'archive
AMO30 XVIe (fonction et groupe de l'initiateur) et les places de l'hémicycle.
L'interface ne lit que `pivot_data/` : rien de cela ne pouvait passer tel quel.

## La décision

- **Un fichier par objet, pas par législature** (arbitré par la propriétaire avec
  Backend, #1325) : `legislatures.json` porte les bornes sourcées (ouverture, fin,
  mode de fin, terme prévu) et les groupes rangés par place médiane (#1317 ;
  XIVe par le fichier du site, #1332) ; `dossiers_an/<n>.json` une ligne par
  dossier (titre, initiateurs, dates, étape à l'Assemblée, dernière adoption,
  votes solennels, 49.3). La promulgation et la commission se joignent depuis
  les fichiers qui les publient déjà. `sync-data.mjs` les copie, et n'ouvre une
  législature au manifeste que si les deux existent.
- **Un seul adaptateur** côté interface (`utils/legislature.js`) : si Backend nomme
  autrement un champ, c'est là qu'il se rattrape.
- **La position d'un groupe vient des fiches de groupe**, jointes par l'organe de
  l'Assemblée : les sigles des deux sources diffèrent (« LFI-NUPES », « LFI »).
  La XVIIe n'en a aucune (AMO30 du 19/10/2026 : aucun des 14 groupes) ; la XIVe
  les reçoit avec ses fiches de groupe (#1328).
- **Une loi compte pour la législature où l'Assemblée l'a adoptée** (arbitré le
  21/10, #1320) ; tant que la date d'adoption manque, la date de promulgation dans
  la période en tient lieu.
- **L'origine d'un texte se lit dans son initiateur**, jamais dans le préfixe du
  texte : en maquette, le préfixe se trompait pour 30 des 218 textes XVIe promulgués,
  adoptés ou rejetés.
- **Le nuage global écarte les mots présents dans au moins 7 des 9 commissions**
  (commissions spéciales réunies) : 16 mots en XVIe, de « public » à « usage ».
  Règle calculée, sans exception choisie à la main (22/10).

## Relecture en local du 22/10/2026

- Le chiffre de l'hémicycle est un nombre de **députés** au jour de référence, pas
  de sièges : 561 en XIVe au 20/06/2017, 574 en XVIIe, contre 577 sièges.
- Chaque sigle porte son nombre de députés et son nom complet au survol ; la liste
  numérotée sous la figure, dont les numéros ne renvoyaient à rien, est retirée.
- Les non-inscrits, qui n'ont pas de bloc de sièges, passent en bout d'hémicycle.
- Un gouvernement nommé le dernier jour d'une législature n'est pas dans sa frise
  (Philippe II, 20/06/2017).
- **Le sigle d'un groupe est celui du jour de référence** quand la fiche de groupe
  du site en garde un autre (arbitré le 22/10/2026 : « ceux du 20 juin 2017 ») :
  les fiches de groupe XIVe portent le sigle de leur premier organe (SRC, UMP),
  l'hémicycle XIVe affiche SER et LES-REP. Le sigle du site reste quand ses lettres
  se retrouvent dans l'ordre dans celui de l'Assemblée (LFI pour LFI-NUPES, SOC pour
  SOC-A, UDR pour UDDPLR, REN pour RE) : sur les quatre législatures, seuls les deux
  groupes XIVe changent.

### Relecture du 23/10/2026, arbitrée sur maquette

- **Une législature sans aucune position publiée** (XVIIe : aucun des groupes dans
  AMO30) dessine ses groupes en **deux tons d'encre alternés**, ceux de l'accueil,
  sans arc de position ; la légende ne garde que les non-inscrits (forme B, sur
  quatre). Un groupe sans position au milieu de groupes qui en ont (UDI en XVe,
  19 députés) garde son gris clair, et la légende le nomme « Position non publiée ».
- **« Qui siège »** pour la législature en cours, « Qui siégeait » pour les autres.
- **Les commissions spéciales tiennent une seule rangée** des rayonnages,
  « Commissions spéciales (N) », le nom de la section des commissions.
- **Sur téléphone**, les sigles de l'hémicycle grossissent et s'écartent des
  sièges ; le nombre des groupes de moins de 30 députés et tout sigle qui
  chevaucherait un plus grand restent dans la bulle des sièges ; l'arc passe entre
  les sièges et les sigles, sans libellé.
- **La frise de la législature en cours** (forme C, sur trois) court jusqu'au
  terme légal (19/06/2029), pleine jusqu'à aujourd'hui, marqué en jaune ; la suite
  reste vide. Les gouvernements se rangent sur autant de rangées qu'il le faut, et
  le dernier s'aligne à gauche de son repère quand il touche le bord.
- **Le début de la XVIIe reste le 01/07/2024** : c'est la date que l'Assemblée
  publie, et aucune des quatre législatures n'a pour début sa première séance.
- **Cinq bulles**, écrites ou reprises mot pour mot par la propriétaire, rendues
  sur la fiche avant d'être codées, recopiées dans
  `tests/test_bulles_fiche_legislature.py`. Seule « Ce qu'on n'a pas pu lire »
  renvoie à la méthodologie : aucune section n'y décrit encore les législatures.
- L'en-tête perd sa ligne en capitales, comme les trois autres fiches
  (`en-tete-des-fiches-homogene`).

## Écarté en maquette

Les tailles par nombre d'amendements (« pas comparable d'une loi à l'autre »), la
date de la loi comme figure, le meuble des textes sans décision (1 316 en XVIe), et
les mots-clés calculés sur les couvertures des livres (abandonnés le 21/10).
Le 23/10 : pour la XVIIe sans positions, l'actuel (légende de quatre couleurs
absentes), un seul ton pour tous les groupes, et les deux tons avec l'arc
« Position non publiée » gardé ; pour sa frise, l'échelle arrêtée à aujourd'hui,
et la suite en pointillé avec une mention.
