# Les places de la XIVe se lisent dans le fichier du site de l'Assemblée, à l'état du 20/06/2017 (#1326)

`2026-10-22`

> **En bref** — les mandats de député de la XIVe publient `place_hemicycle` comme les XVe à XVIIe (#1317), lu dans `https://www.assemblee-nationale.fr/14/tribun/xml/place.txt`, le fichier qu'utilisait la carte de l'hémicycle du site, avec `etat_au` = `2017-06-20`. Le siège va au mandat XIVe ouvert ce jour-là dans AMO30, jamais à un mandat clos avant. `legislatures.json` range désormais les groupes de la XIVe par siège. Arbitré le 22/10/2026 : « oui on va utiliser le fichier de l'an du 20 juin 2017 ».

## Contexte

#1317 publie le siège de chaque mandat de député, lu dans l'archive AMO30 de
sa législature. La XIVe n'en a pas (`repository/14/…` répond 404) : ses
mandats publiaient `null` + `legislature_sans_archive_figee`, et
`legislatures.json` donnait ses groupes sans siège, dans un ordre sans
signification. Les fiches de groupe XIVe (#1328) et la fiche de législature
(#1314) en ont besoin.

Les sources examinées le 22/10/2026 sont décrites dans
`docs/sources/an-opendata.md`. L'archive AMO20 de la XIVe est inutilisable :
elle porte le siège XVe de 2018. Le fichier du site
`/14/tribun/xml/place.txt` est toujours servi (HTTP 200, 75 991 octets,
`last-modified` 07/02/2021) : `{"s<siège>": {"id": "<n° d'acteur sans PA>",
…}}`, plus une clé `"s"` sans numéro, et le champ `groupe` vide partout.

Mesuré le 22/10/2026 sur l'archive AMO30 courante du jour, hors dépôt puis
avec le code du lot :

| Constat | Valeur |
| --- | --- |
| Sièges numérotés du fichier | 547, 547 acteurs distincts |
| … dont l'acteur a un mandat XIVe ouvert le 20/06/2017 | 547 |
| Acteurs en mandat XIVe le 20/06/2017 dans AMO30 | 561 |
| … absents du fichier ou sous la clé `"s"` | 14, tous non-inscrits ce jour-là : 10 membres du gouvernement Cazeneuve, dont Alain Vidalies sous `"s"`, et 4 autres députés |
| Sièges XIVe des profils (`(legislature, dateDebut)`, #640), tous acteurs d'AMO30 | 655 : 547 avec une place, 107 `mandat_absent_de_l_archive`, 1 `source_sans_place` |

Siège médian par groupe au 20/06/2017, population = membres du groupe ce
jour-là avec une place : `LES-REP` 116 (197), `UDI` 232 (27), `RRDP` 285 (17),
non-inscrits 311,5 (26 sur 40), `SER` 455 (265), `GDR` 590 (15). Les captures
de l'Internet Archive de 2012 à 2015 donnent le même ordre.

## Décision

1. **`FICHIERS_PLACES_SITE_AN`** (`candidate_profile.py`) déclare la source
   de la XIVe : l'adresse et l'`etat_au` `2017-06-20`. **La date est déduite,
   pas déclarée par le fichier** : c'est le dernier jour de la législature, et
   ses 547 députés numérotés sont tous en mandat ce jour-là. Elle est posée en
   constante, comme les `etat_au` des archives figées.
2. **Le siège s'attache au mandat ouvert le `etat_au`**
   (`_places_par_mandat_site_an`), lu dans l'archive AMO30 courante, qui
   garde les mandats clos. L'index a la forme de celui des archives :
   `{acteurRef: {dateDebut: place}}`. Les segments d'un même siège partagent
   leur `dateDebut` (#640) et reçoivent la même place. Un siège clos avant le
   20/06/2017 n'en reçoit aucune : Frédéric Barbier a la place 558 sur son
   mandat ouvert le 08/02/2015, et `mandat_absent_de_l_archive` sur celui de
   2012-2014. Un identifiant sans mandat ouvert ce jour-là est écarté, jamais
   rattaché à un autre mandat.
3. **`numero` est le numéro de la clé, verbatim** (`"s467"` → `"467"`, sans
   zéros de tête, comme la source l'écrit). La clé `"s"` donne
   `source_sans_place`.
4. **Les motifs ne changent pas.** `legislature_sans_archive_figee` vaut
   désormais pour la XIIIe et avant ; son nom reste, parce qu'il est publié.
   Un téléchargement en échec ou un fichier illisible publie
   `archive_indisponible`, avec l'adresse du fichier.
5. **Le fichier se télécharge comme une archive figée** :
   `_telecharger_source_figee`, commun aux deux, avec un `.part` renommé au
   succès, un budget mur de 30 s, les reprises #1202 et une tentative par
   process. Il est rangé sous `.cache/acteurs_historique_an/figees/14/` avec
   son index : même `path:` de cache, workflow inchangé, épargné par la
   péremption hebdomadaire.
6. **`legislatures.json` lit le même index** : la XIVe passe par
   `legislatures_avec_places_hemicycle()`, et ses groupes se rangent par siège
   médian au 20/06/2017.
7. **La transition passe par le report existant** : les mandats XIVe déjà
   publiés avec `null` + `legislature_sans_archive_figee` reçoivent la place
   par `backfill_mandat_place_hemicycle`, aux deux étages. Une place résolue
   remplace un `null` et son motif. Le test de transition de #1317 le vérifie
   sur les mandats réels de Florent Boudié (467).

## Réutilisation

Ce fichier ne vient pas du portail open data. La page « Info site » de
l'Assemblée (`https://www.assemblee-nationale.fr/dyn/info-site`, lue le
22/10/2026) autorise la reproduction gratuite, dans le respect de l'intégrité
du document, avec l'auteur, la source et un lien vers l'original en ligne. Elle
exclut tout usage commercial ou publicitaire. Un numéro de siège est un fait,
publié avec l'adresse du fichier dans `source_url`. Aucun `sources[]` n'est
ajouté et `licence_donnees` ne bouge pas : c'est le même traitement que les
mandats antérieurs cités de Sycomore (`AGENTS.md` §7).

## Alternatives écartées

- **La capture de l'Internet Archive du 28/09/2015.** C'était la première
  recommandation, avant qu'on sache que le site sert toujours le fichier. Elle
  décrit un état antérieur à la dissolution d'ECOLO et au passage de `SRC` à
  `SER` (mai 2016), et elle est lue dans une copie plutôt que chez l'Assemblée.
- **L'archive AMO20 de la XIVe** (`repository/14/amo/…AMO20…`, 08/03/2018).
  Ses 154 places sur 750 mandats sont des sièges XVe recopiés.
- **Prêter le siège du fichier à tous les mandats XIVe d'un député.** Ce
  serait publier, sur un mandat clos en 2014, un siège lu en 2017.

## Non vérifié

- Le comportement sur un runner GitHub : le site de l'Assemblée pourrait
  refuser ses requêtes. Ce serait un `archive_indisponible`, jamais une place
  fausse.
- La date de l'état n'est écrite nulle part dans le fichier. Une
  régénération du fichier par l'Assemblée passerait inaperçue, à ceci près
  que des identifiants sans mandat ouvert au 20/06/2017 s'afficheraient en
  avertissement.
