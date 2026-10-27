<a id="repositionnement-relier-et-donner-a-voir-1329"></a>

# Le projet relie et donne à voir, plutôt qu'il ne rassemble : « tableau de bord de la vie parlementaire et gouvernementale » (#1329) (2026-10-27)

`2026-10-27`

> **En bref** — Le site se présentait comme un **agrégateur** : il rassemblait ce que les institutions publient. Arbitré par la propriétaire le 22/10/2026 : sa valeur est de **relier et donner à voir**. La collecte existe ailleurs ; ce que personne ne publie, ce sont les liens entre personne, groupe, gouvernement, texte, vote, amendement et décret, et une forme qui les rend lisibles. Le genre se nomme **« tableau de bord de la vie parlementaire et gouvernementale »**, avec deux gardes : aucun cadran « bon / mauvais », aucune esthétique fintech. Écartés : un outil de visualisation que le lecteur configure, le téléchargement des données pivot depuis le site, « plateforme d'analytics », « atlas ». **Rien ne change** des huit règles du §2, des sources ni du pipeline. Le point à surveiller : chaque lien est un choix, donc **chaque règle de rattachement doit être écrite et vérifiable** en méthodologie. Ce fichier est la décision d'ensemble ; six décisions de détail l'appliquent déjà.

## Ce qui a décidé

La propriétaire, le 22/10/2026, dans la conversation qui a ouvert #1329 :

> est-ce que la valeur ajoutée de notre travail n'est pas finalement le schéma
> pivot qui permet de croiser les différents objets et les données en général
> plus le travail de visualisation qui rend tout ceci accessible

Reformulé en « relier et donner à voir, plutôt que rassembler », et validé :
« oui c'est ça ». Elle a précisé le même jour que les données pivot ont de la
valeur « parce qu'elles nous permette de construire des vues qui permettent de
croiser des objets qui ne sont pas nativement croisés », et que c'est la
visualisation de ces croisements qui distingue le projet d'autres projets.

## Ce que le site apporte désormais

| Avant | Désormais |
| --- | --- |
| Rassembler ce que les institutions publient, et le donner à lire tel quel | **Relier** des objets que les sources publient séparément : une loi à la législature qui l'a votée, un acte réglementaire à un gouvernement, un groupe à celui qu'il continue, un rôle à sa législature et à son gouvernement |
| Une fiche par objet, rangée par type | Les fiches **mènent aux objets qu'elles croisent**, à l'endroit de leurs figures : législature, gouvernement et groupe entre eux, rôle d'un candidat vers sa législature et son gouvernement |
| Le procédé affiché : « Collecte et agrégation » | **Une forme qui rend les liens lisibles** : l'accueil montre un croisement (législatures × gouvernements) au lieu d'annoncer un procédé |

La collecte reste le socle : sans elle, rien à relier. Elle cesse d'être ce que
le projet dit de lui-même.

## Le nom du genre

**« Tableau de bord de la vie parlementaire et gouvernementale »**, arbitré le
22/10/2026.

- **« De la vie parlementaire et gouvernementale »**, et non « de l'action
  politique », sa première formulation : « action » appelle un bilan, et
  « politique » est plus large que le cœur permanent du corpus
  (`coeur-permanent-groupes-et-gouvernements`).
- **Première garde.** Un tableau de bord fait attendre des cadrans « bon /
  mauvais ». Les vues restent factuelles : aucun jugement, aucun score, aucun
  classement (§2 règle 1).
- **Seconde garde.** Le mot ne déplace pas la direction artistique vers
  l'esthétique fintech, que le brief écarte (« loin de Revolut »).
  → `direction-artistique-repositionnement-1329`

C'est le nom du positionnement, dans le dépôt. Au 27/10/2026, il n'est écrit sur
aucune page du site : la phrase du manifeste qui le portait a été refusée
(`manifeste-a-propos-repositionne-1329`), et le titre de l'accueil n'a pas
changé (arbitrage du 22/10, `accueil-tableau-de-bord-1329`).

## Alternatives écartées

| Proposition | Pourquoi |
| --- | --- |
| Un outil où le lecteur configure lui-même ses visualisations | écarté le 22/10/2026 : la valeur est dans les vues construites, pas dans un outil |
| Le téléchargement des données pivot depuis le site | écarté le même jour : les données pivot valent par les vues qu'elles permettent de construire |
| « Plateforme d'analytics » | promet des indicateurs de performance et un outil |
| « Atlas » | écarté |
| « Croise ce que les institutions publient séparément, et le donne à voir » | écartée comme nom du genre |
| « Tableau de bord de l'action politique » | première formulation ; « action » appelle un bilan, « politique » dépasse le cœur du corpus |

## Ce qui ne change pas

- **Les huit règles du §2.** Relier ne permet ni score, ni classement, ni
  taux individuel ; un lien affiché est un fait sourcé, ou il n'est pas affiché.
- **Les sources.** Aucune n'est ajoutée ni retirée par ce repositionnement.
- **Le pipeline.** Collecte, normalisation, fusion et agrégats restent ce qu'ils
  sont ; le schéma pivot est déjà ce qui permet de croiser les objets.
- **La hiérarchie du 30/09/2026** : groupes et gouvernements au cœur, candidats
  en volet borné par l'élection (`coeur-permanent-groupes-et-gouvernements`).

## Le point à surveiller

Le mot « agrégateur » protégeait : « nous ne faisons que relayer ». Dire « nous
relions » reconnaît que chaque lien est un choix — les lignées vivent dans
`config/` parce que ce sont des jugements (#1057). Le repositionnement n'est donc
solide que si **chaque règle de rattachement est écrite et vérifiable** dans la
méthodologie, avec sa source et ce qu'elle manque, au même titre qu'une source.

Les règles déjà décidées, chacune dans sa décision :

| Lien | Règle | Décision |
| --- | --- | --- |
| Loi → législature | la dernière adoption par l'Assemblée, et non l'ouverture du dossier ni la promulgation | `adoption-an-lois-promulguees-1320` |
| Acte réglementaire → gouvernement, ministère | la date de parution et l'organe ; jamais une personne, la source ne publiant pas le signataire | `actes-reglementaires-du-journal-officiel-1029` |
| Groupe → groupe qu'il continue (lignée) | la comparaison des membres ; les liens sont écrits dans `config/` | `critere-de-filiation-des-lignees-1168`, `lien-etabli-par-comparaison-1168` |
| Membre → position majoritaire de son groupe | un scrutin à la fois, jamais compté | `AGENTS.md` §2 règle 7 |
| Prise de parole → point de séance | le point sous lequel elle est prononcée, son sujet lu dans la structure du compte rendu et jamais dans un libellé ; un créneau (« Questions au gouvernement ») n'est pas un sujet | `docs/regles/interventions-syceron.md` (§3e) |
| Rôle d'un candidat → législature, gouvernement | la période que le rôle recouvre le plus longtemps | `rattachement-par-periode-fiche-candidat-1329` |

La méthodologie en dit déjà une partie, fiche par fiche — par exemple « Une loi
est rattachée à la législature qui l'a votée », dans la famille « Fiche de
législature ». Aucune famille ne les réunit, et la règle de rattachement par
période n'y est pas encore.

## Les décisions de détail qui l'appliquent

| Date | Ce qui change | Décision |
| --- | --- | --- |
| 23/10/2026 | L'accueil montre un croisement — frise des législatures et des gouvernements, Assemblée par groupe — au lieu d'annoncer « Le concept » | `accueil-tableau-de-bord-1329` |
| 26/10/2026 | Le fil d'Ariane remplace le tiroir ; les fiches de législature, de gouvernement et de groupe se relient à l'endroit de leurs figures ; « Articles sur cette période » | `fil-d-ariane-a-la-place-du-tiroir-1329` |
| 26/10/2026 | « Sans groupe connu à l'Assemblée » ; « Articles » juste après la recherche | `libelle-sans-groupe-et-ordre-de-la-barre-1329` |
| 26/10/2026 | Les cases « 6 / 12 derniers mois » sur la seule législature en cours | `periode-sur-la-legislature-en-cours-1329` |
| 26/10/2026 | Chaque rôle d'un candidat mène à sa législature et à son gouvernement | `rattachement-par-periode-fiche-candidat-1329` |
| 26/10/2026 | Le manifeste de `/a-propos` ne se dit plus agrégateur | `manifeste-a-propos-repositionne-1329` |

Les documents du dépôt suivent dans le même lot que ce fichier : `AGENTS.md` §1,
`README.md`, et un complément à la direction artistique
(`direction-artistique-repositionnement-1329`).

## Ce qui reste

- **La famille de méthodologie « Comment les objets sont reliés »** : pas
  commencée. Elle réunit les règles du tableau ci-dessus ; la règle de
  rattachement par période est la première à écrire. Texte à valider avec la
  propriétaire.
- **La fiche par texte de loi** : pas commencée, à maquetter. C'est l'objet qui
  croise le plus d'autres objets, et il n'a pas de fiche.
- **La description de `/a-propos` pour les moteurs de recherche**
  (`web/UI_finale/scripts/metadonnees-pages.mjs`) dit encore « publie ce que les
  institutions publient, collecté par un programme ». C'est un texte publié :
  à arbitrer par la propriétaire.

## Ce qui n'a pas été vérifié

- La liste des alternatives écartées est celle du corps de #1329 ; la
  conversation du 22/10/2026 elle-même n'a pas été relue.
- Aucun test ne tient ce repositionnement : une ligne éditoriale ne se teste
  pas, comme la hiérarchie de `coeur-permanent-groupes-et-gouvernements`. Ce qui
  se tient, ce sont les règles de rattachement, une à une, dans leurs propres
  tests.
