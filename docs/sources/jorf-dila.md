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
  depuis 2024** : 0 des 188 lois du fonds promulguées depuis le 01/01/2024 en porte un, contre
  68,6 % des lois de 2015. La qualification est un travail éditorial différé, de délai non
  publié. `CITATION` n'en est pas un substitut (#664).
- **Les coquilles du titre** : « ventre de la branche énergie d'Alstom », « oubre-mer ». Un
  index de mots les porte telles quelles ; rien n'est rapproché.
- **Légifrance en 403** (Cloudflare) et l'API PISTE en OAuth : l'`ID_ELI` publié par la DILA
  mène à la page d'un acte pour un humain, pas depuis la CI.
- **JORFSearch ne doit pas être appelé** : son `robots.txt` interdit les points d'entrée
  `?format=JSON` et l'opérateur n'annonce aucune licence (#644).
- **`tarfile` en mode flux** garde la fiche de chaque membre lu : sur le dump global, le
  processus atteint 1,5 Go avant d'avoir rien produit si la liste n'est pas vidée.

## Volumétrie mesurée le 22/09/2026

389 397 actes depuis le 01/01/2007 — 311 727 arrêtés, 76 664 décrets, 1 006 ordonnances —, de
18 076 (2012) à 22 111 (2007) par an, pour 2 368 125 articles lus.

Voir `docs/decisions/actes-reglementaires-du-journal-officiel-1029.md` (ce qui est publié et
pourquoi) et l'issue #664 (l'exploration, et le verdict sur les décrets d'application).
