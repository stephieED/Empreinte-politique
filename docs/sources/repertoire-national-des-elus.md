# Répertoire national des élus — référence de source

> **Statut : vivante.** Interrogée à chaque run depuis #922, pour les **mandats
> locaux des candidats déclarés**. Ce fichier dérive avec son fournisseur, pas
> avec notre code.

## Ce que nous interrogeons

Deux jeux distincts, tous deux publiés par le ministère de l'Intérieur sur
`data.gouv.fr`, tous deux sous **Licence Ouverte 2.0 (Etalab)** — attribution
seule, pas de partage à l'identique.

| Jeu | Ce qu'il porte | Rythme |
| --- | --- | --- |
| `repertoire-national-des-elus-1` | les mandats **en cours** | trimestriel |
| `elections-municipales-2026-maires-et-conseillers-municipaux-sortants` | la mandature **2020-2026**, état au 27/02/2026 | figé |

Les deux se complètent et ne se remplacent pas : le RNE ne porte que la
mandature qui vient de commencer, le fichier des sortants porte la précédente,
avec sa date de début de mandat **et** de fonction.

## Par l'API tabulaire, jamais en téléchargement

`tabular-api.data.gouv.fr` expose chaque CSV en REST, filtrable par colonne :

```
GET /api/resources/<rid>/data/?Nom de l'élu__exact=PHILIPPE&Date de naissance__exact=1970-11-28
```

~160 requêtes filtrées côté serveur par run, contre **76 Mo** de CSV à
télécharger. D'où l'absence de cache sur le job : il n'y a rien à cacher.

**Le `rid` change à chaque publication trimestrielle** — l'URL d'un fichier porte
sa date (`20260811-155100`). Il se résout par
`/api/1/datasets/<slug>/`, jamais en dur : le coder figerait le corpus au jour où
quelqu'un l'a copié, sans que rien ne le dise.

## Les fichiers, et ceux que nous refusons

Le RNE en publie douze. Nous en lisons neuf — conseillers municipaux, maires,
conseillers d'arrondissement, communautaires, départementaux, régionaux, membres
d'assemblée, et les deux des Français de l'étranger.

**Trois sont refusés à la lecture** : `elus-deputes-dep`, `elus-senateurs-sen`,
`elus-representants-Parlement-européen-rpe`. Ces mandats-là, nous les collectons
déjà à leur source institutionnelle, avec leur propre datation. Les lire
publierait le même mandat deux fois, sans que rien ne dise laquelle des deux
dates fait foi.

## Ce que la source ne publie pas

**Aucune date de fin.** Les colonnes sont `Date de début du mandat` et
`Date de début de la fonction`. On obtient une suite de **débuts datés** et
d'**états constatés à une date** — « maire du Havre depuis le 28/06/2020,
constaté le 27/02/2026 » est sourçable ; « jusqu'en mars 2026 » serait une
inférence.

**Aucun identifiant de personne.** L'appariement se fait sur l'état civil, d'où
la table relue `raw_data/correspondance_elus_rne.json` pour les candidats dont le
corpus n'a pas la date de naissance.

## Cinq pièges, tous mesurés

**Les diacritiques sont incohérents.** « Edouard » sans accent et « Jérôme »
avec, dans le même fichier. Apparier sur le prénom tel qu'écrit rendait Édouard
Philippe **sans aucun mandat**, alors qu'il est maire du Havre — et l'échec est
entièrement silencieux.

**Le patronyme seul ne veut rien dire.** « MATHIEU » rend des centaines de lignes
chez les conseillers municipaux ; avec le prénom, aucune. Le nombre exact bouge à
chaque publication : le re-mesurer, ne pas le citer.

**Le même mandat est publié dans deux fichiers.** Un maire figure chez les
conseillers municipaux avec la fonction « Maire », *et* chez les maires. La clé
de déduplication est `(lieu, date de début)`, jamais le fichier d'origine.

**Le fichier des sortants publie des naissances au XXIᵉ siècle.** Il donnait
l'année sur deux chiffres ; convertie en ISO, une année basse a pris le mauvais
siècle. Relevé le 16/09/2026 dans `mun2026-cm-sortants-20260227` : David Lisnard,
né le 02/02/1969, y est né le **2069**-02-02 ; Édouard Philippe, le
**2070**-11-28 ; Gabriel Attal, né en 1989, est correct. Interroger la seule date
exacte ne rend **rien** — cinq mandats 2020-2026 de candidats déclarés
disparaissaient ainsi sans erreur. Le seuil de bascule n'est pas publié : les deux
formes sont demandées, et le nom est vérifié sur chaque ligne. Le jour où le
producteur corrige le fichier, la forme décalée ne rend plus rien et la forme
exacte prend le relais — rien à retirer.

**Une date de naissance peut dépasser une page.** L'API rend 50 lignes par page au
plus, et signale la suivante dans `links.next`. Relevé le 16/09/2026 : **49** élus
sortants partagent une même date de naissance, à une ligne du plafond. Lire la
seule première page perd en silence la personne en 51ᵉ position.

## Ce qui est hors de portée, et pourquoi

La couverture commence en **2020**. Les jeux antérieurs ont été instruits et
écartés pour deux raisons **distinctes**, dont une seule peut tomber :

- les jeux **complets** de 2014 et de 2020 ne déclarent **aucune licence**
  (`notspecified`) — réversible si le producteur la précise ;
- les jeux de 2014 sous Licence Ouverte ne couvrent que le **premier tour** —
  définitif, le jeu ne changera plus.

Une absence avant cette borne se **déclare**, elle ne se lit jamais comme
« aucun mandat local ».

→ `docs/decisions/collecte-mandats-locaux-rne-922.md`,
  `docs/decisions/borne-mandats-locaux-2020-922.md`,
  `docs/decisions/correspondance-elus-rne-relue-922.md`
