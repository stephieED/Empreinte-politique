# `echanges.dila.gouv.fr` — le fonds du Journal officiel (DILA)

> **Statut : collectée depuis le 22/09/2026** (#1029 voie 1). Explorée d'abord par
> [`#664`](https://github.com/stephieED/Empreinte-politique-src/issues/664), qui a établi le
> balisage et la licence, puis branchée pour les **actes réglementaires** — décrets, arrêtés,
> ordonnances — publiés depuis le 01/01/2007. Le module `src/actes_reglementaires.py` relit à
> chaque run les livraisons des deux derniers mois. Ce fichier décrit ce que le
> **fournisseur** publie, et dérive avec lui, non avec notre code.

## Producteur et licence

Producteur **DILA** (Direction de l'information légale et administrative). **Licence Ouverte**
— `fr-lo` dans l'API `data.gouv.fr` (jeu `jorf-les-donnees-de-l-edition-lois-et-decrets-du-journal-officiel`).
Attribution seule, **pas de partage à l'identique** : un jeu dérivé se republie sous simple
attribution. L'étiquette canonique est `licences.LICENCE_JORF`, jamais recopiée en dur
(AGENTS.md §7).

## Ce que le fournisseur publie

| Livraison | Ce qu'elle porte | Poids |
| --- | --- | ---: |
| `Freemium_jorf_global_20250713-140000.tar.gz` | le fonds entier, de **1861** à la date de livraison | 1 674 608 486 octets |
| `JORF_<AAAAMMJJ>-<HHMMSS>.tar.gz` | une livraison par jour, parfois deux | de 87 Ko à ~10 Mo |

**Le dump global est une livraison UNIQUE du 13/07/2025**, que la DILA n'a jamais renouvelée.
Les livraisons quotidiennes ne remontent donc pas plus loin : au 22/09/2026, 800 livraisons
couvrent le 13/07/2025 → aujourd'hui (2,1 Go). C'est ce qui impose un remplissage initial en
local et un index commité, plutôt qu'une reconstruction à chaque run.

Une archive porte deux arborescences utiles : `.../texte/version/JORF/TEXT/.../JORFTEXT<id>.xml`
(un texte) et `.../article/JORF/ARTI/.../JORFARTI<id>.xml` (un article, qui nomme son texte).

## Le conteneur : la table des matières du JO (#1134)

À côté des fichiers d'actes, chaque livraison porte un **conteneur** sous
`.../jorf/global/conteneur/`. C'est le SOMMAIRE du Journal officiel du jour, et
la seule pièce où la source déclare la **portée** d'un texte.

```
<STRUCTURE_TXT>
  <TM><TITRE_TM>Journal officiel "Lois et Décrets"</TITRE_TM>
    <TM><TITRE_TM>Décrets, arrêtés, circulaires</TITRE_TM>
      <TM><TITRE_TM>Mesures nominatives</TITRE_TM>
        <TM><TITRE_TM>Ministère de la santé…</TITRE_TM>
          <LIEN_TXT idtxt="JORFTEXT000054812249" titretxt="Arrêté du 28 août 2026 fixant la liste…"/>
```

Trois rubriques sous « Décrets, arrêtés, circulaires » : **Textes généraux**,
**Mesures nominatives**, **Conventions collectives**. Relevé le 25/09/2026 sur
la livraison `JORF_20260909-003012` : 29 textes généraux, 52 mesures
nominatives, 6 conventions collectives sur 105 textes rangés.

**La jointure est directe** : `LIEN_TXT/@idtxt` est l'identifiant `JORFTEXT`,
donc `prefixe_ids + ids[i]` de nos fichiers-mois. Rien à apparier par titre.

**Ce que le conteneur permet, et que rien d'autre ne permet.** Les arrêtés
« fixant la liste des personnes autorisées à exercer en France la profession de
médecin » sont des autorisations individuelles, mais leur titre n'emploie aucune
formule d'acte de personne. Le JO les classe en « Mesures nominatives ».

**Ce qui ne marche pas.** Le **NOR** ne porte que la nature : sa dernière lettre
est `A` pour un arrêté, `D` pour un décret — 76 622 et 19 992 sur les 97 423 NOR
de 60 mois du fonds. Rien sur la portée.

## Les champs lus, et ce qu'ils valent

| Champ | Où | Couverture mesurée |
| --- | --- | --- |
| `<NATURE>` | `META_COMMUN` | 1 766 / 1 768 textes du 01–29/08/2026 (#664). Vocabulaire fermé : `ARRETE`, `DECRET`, `LOI`, `AVIS`, `ORDONNANCE`, `DECISION`… |
| `<DATE_PUBLI>` | `META_TEXTE_CHRONICLE` | 100 % — **sauf la date bouche-trou `2999-…`**, portée par 386 actes du fonds depuis 2007 |
| `<MINISTERE>` | `META_TEXTE_VERSION` | 380 / 380 décrets et 929 / 934 arrêtés de la fenêtre (#664) ; 260 libellés distincts depuis 2007 |
| `<NOR>` | `META_TEXTE_CHRONICLE` | 9 364 / 9 368 actes des six derniers mois. Ses 3 premières lettres sont le code ministère |
| `<NUM>` | `META_TEXTE_CHRONICLE` | **sépare le décret réglementaire (numéroté) du décret individuel** : 112 / 380 décrets de la fenêtre de #664 |
| `<AUTORITE>` | `META_TEXTE_VERSION` | **vide sur les 380 / 380 décrets**. Le signataire n'est pas publié |
| `<BLOC_TEXTUEL>` | fichier d'article | le corps de l'article, en HTML léger |
| `<CONTEXTE><TEXTE …>` | fichier d'article | nomme le texte de l'article, avec sa `nature` et sa `date_publi` — c'est ce qui permet de filtrer sans attendre le texte |

## Les pièges

- **`<AUTORITE>` vide** : « N décrets signés par X » n'est pas constructible. Un acte se
  rattache à un gouvernement par sa date et à un ministère par `<MINISTERE>` — jamais à une
  personne (#664).
- **La date `2999-…`** est une sentinelle, pas une date. Rangée dans une année, elle se lirait
  comme un fait (§2 règle 5) : ces actes vont dans `sans-date.json`.
- **Les redélivrances** : une archive quotidienne contient aussi des textes anciens republiés —
  8 926 sur 22 595 textes lus dans six mois de livraisons. Le filtre est `DATE_PUBLI`, jamais
  la date de la livraison.
- **`typelien="APPLICATION"`**, qui relie une loi à ses décrets d'application, **n'est plus posé
  depuis 2024**, et c'est un **retard de qualification, pas une absence de décrets**. Remesuré le
  23/09/2026 sur les 13 267 lois du fonds (dump global + 803 livraisons, 431 976 liens lus) :

  | Année de promulgation | Lois du fonds | Avec un lien `APPLICATION` | Avec au moins un acte qui les **cite** |
  | --- | ---: | ---: | ---: |
  | 2019 | 76 | 36 (47 %) | 48 (63 %) |
  | 2021 | 96 | 37 (38 %) | 60 (62 %) |
  | 2023 | 79 | 28 (35 %) | 52 (65 %) |
  | **2024** | 50 | **0** | **28 (56 %)** |
  | **2025** | 84 | **0** | **52 (61 %)** |

  Une loi de 2024 est citée par un acte aussi souvent qu'une loi de 2023 : les décrets sont là,
  la source ne les a pas encore qualifiés. Le taux décroît d'ailleurs bien avant 2024 — 71 % en
  2015 —, ce qui fait de la qualification un travail éditorial différé, de délai non publié.

  **Cette couverture se remesure, elle ne se fige jamais** : le trou se referme par l'arrière, des
  liens apparaissant sur des lois promulguées des mois plus tôt. Tout chiffre de couverture par
  année porte donc la date où il a été pris, ici le 23/09/2026.

  **Le même trou, vu depuis les actes** (24/09/2026). Sur les **31 199 décrets numérotés** du
  fonds — la population à nommer : les 45 478 décrets sans numéro, nominations et mutations, n'en
  sont pas —, par **année de publication** :

  | Année | Décrets numérotés | applique | cite | aucun lien déclaré |
  | --- | ---: | ---: | ---: | ---: |
  | 2012 | 1 474 | **42 %** | 17 % | 41 % |
  | 2016 | 1 860 | 26 % | 34 % | 40 % |
  | 2020 | 1 681 | **4 %** | 47 % | 50 % |
  | 2023 | 1 345 | 1 % | 40 % | 59 % |
  | 2024 | 1 227 | **0 %** | 43 % | 57 % |
  | 2026 | 848 | **0 %** | 39 % | 61 % |

  Deux choses s'y lisent que la table des lois ne montre pas. La chute commence **bien avant le
  retard** — 42 % en 2012, 26 % en 2016, 4 % en 2020 —, et **« cite » monte pendant que
  « applique » descend** : une part de ce qui était qualifié d'application est désormais
  enregistré comme un simple visa. Retard de qualification et changement de pratique se
  superposent, et **rien dans les données ne permet de les séparer**. C'est la raison pour
  laquelle aucune figure publiée ne repose sur la part d'application
  (`docs/decisions/part-d-application-non-publiable-1029.md`).

  **Ce que la livraison ne porte pas, et qui manquerait le plus** : la **rubrique**
  du Journal officiel — « Textes généraux », « Mesures nominatives », « Conventions
  collectives ». Le pivot n'a que la nature (`DECRET`, `ARRETE`, `ORDONNANCE`), donc
  la distinction entre un acte réglementaire et un acte individuel se devine dans les
  titres. Ce que ça coûte, mesuré le 25/09/2026 sur Lecornu II : **308 des 395 actes
  qui nomment une loi** sont des arrêtés « fixant la liste des personnes autorisées à
  exercer la profession de médecin », pris en application de la LFSS 2007 — des actes
  nominatifs qu'aucune formule du filtre n'attrape. Question posée à la session
  Backend le 25/09/2026 ; tant qu'elle n'est pas tranchée, le filtre par titres est la
  règle et non un repli.

  L'axe est l'**année de publication de l'acte**, jamais une législature : un décret n'appartient
  à aucune, il se rattache au gouvernement en fonction à sa parution.

  `CITATION` **n'est pas un substitut** : un décret qui cite une loi dans ses visas n'en est pas un
  décret d'application, et publier l'un pour l'autre affirmerait une relation que la source ne
  déclare pas (§2 règle 2). Il sert à mesurer le retard, jamais à combler le trou.
- **L'intitulé déclaratif ne rattrape rien.** Un acte écrit parfois « pris pour l'application de la
  loi n° 2024-42 » : 353 actes du fonds le font, pour 103 lois, et l'usage s'effondre après 2012
  (35 actes cette année-là, 8 en 2024). Sur nos dossiers promulgués, cette voie gagne **5** lois,
  dont **une seule** promulguée depuis 2024 (mesuré le 23/09/2026).
- **Les coquilles du titre** : « ventre de la branche énergie d'Alstom », « oubre-mer ». Un
  index de mots les porte telles quelles ; rien n'est rapproché.
- **Légifrance en 403** (Cloudflare) et l'API PISTE en OAuth : l'`ID_ELI` publié par la DILA
  mène à la page d'un acte pour un humain, pas depuis la CI.
- **JORFSearch ne doit pas être appelé** : son `robots.txt` interdit les points d'entrée
  `?format=JSON` et l'opérateur n'annonce aucune licence (#644).
- **`tarfile` en mode flux** garde la fiche de chaque membre lu : sur le dump global, le
  processus atteint 1,5 Go avant d'avoir rien produit si la liste n'est pas vidée.

## La jointure loi → actes d'application, et sa population

La jointure se fait par **identifiant**, jamais par ressemblance : le NOR de la loi, que l'acte
publie dans son lien, ou le numéro de loi (`2024-42`) quand l'acte le cite dans son intitulé.

**La population à joindre est celle des dossiers promulgués des archives de l'AN**, pas celle des
`textes[]` des fiches de gouvernement : 607 dossiers portent un NOR de parution, dont **259 qu'une
fiche de gouvernement ne porte pas** — un texte promulgué peut être porté par un parlementaire.
Mesuré le 23/09/2026 sur les 10 967 dossiers des archives.

| Mesure du 23/09/2026 | Résultat |
| --- | ---: |
| Nos dossiers promulgués retrouvés dans le fonds, par égalité de NOR | 607 / 608 |
| Avec au moins un acte d'application qualifié | **209**, pour 1 493 actes |
| Promulgués depuis 2024 | 175, dont **0** qualifiés et **90** cités par au moins un acte (678 actes citants) |

**Un acte s'attribue au gouvernement en fonction à sa date de parution, pas à celui qui a fait voter
la loi** : le délai médian loi → premier acte est de 57 jours, quartile haut 115 (#664), donc une
loi de fin de mandature voit ses décrets pris par le gouvernement suivant.

## Volumétrie mesurée le 22/09/2026

389 397 actes depuis le 01/01/2007 — 311 727 arrêtés, 76 664 décrets, 1 006 ordonnances —, de
18 076 (2012) à 22 111 (2007) par an, pour 2 368 125 articles lus.

Voir `docs/decisions/actes-reglementaires-du-journal-officiel-1029.md` (ce qui est publié et
pourquoi) et l'issue #664 (l'exploration, et le verdict sur les décrets d'application).
