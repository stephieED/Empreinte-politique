<a id="actes-reglementaires-du-journal-officiel-1029"></a>
# Les actes réglementaires du Journal officiel, par mois et par mots (#1029 voie 1) (2026-09-22)

`2026-09-22`

> **En bref** — Le corpus ne voyait aucun décret ni arrêté : « carburant » rendait 0 texte, alors que le décret n° 2026-333 crée une indemnité carburant. Les décrets, arrêtés et ordonnances publiés depuis 2007 entrent, avec l'index de mots de leur titre et de leurs articles, un fichier par mois. 389 397 actes, ~210 Mo. Aucun rattachement à une personne : la source ne publie pas le signataire.

## Constat

#1029 demande d'extraire d'un mot-clé ce que le corpus porte sur un sujet. Trois
voies échappent au filtre, et la première est l'acte réglementaire — ce que
l'exécutif prend seul. Mesuré le 22/09/2026 sur les six derniers mois de
livraisons DILA : **18 actes** portent « carburant » dans leur titre et **91**
dans au moins un article, dont le décret créant l'indemnité carburant et ses
trois arrêtés de dates. Le corpus n'en publiait aucun.

#664 avait déjà établi, le 31/08/2026, que la nature et le ministère sont
balisés, que le signataire ne l'est pas, et que la licence est ouverte. Son objet
était « les décrets d'un gouvernement », écarté sur le volume ; la question posée
ici est autre — **trouver les actes d'un sujet**.

## Décision

1. **Périmètre** : natures `DECRET`, `ARRETE`, `ORDONNANCE`, publiées depuis le
   **01/01/2007** — la borne basse des fiches de gouvernement publiées.
   Arbitré le 22/09/2026 : « on doit pouvoir faire le tri sur toutes les données
   sans limite de date », comme pour les amendements.
2. **Titre ET articles** sont indexés, pas le titre seul : sur six mois, le titre
   trouve 18 actes « carburant », les articles 91, dont l'arrêté sur les prix de
   sortie des raffineries. Le besoin retenu pour la voie 2 valait ici : trouver.
3. **Un fichier par mois de publication**, `pivot_data/actes_reglementaires/<AAAA-MM>.json`.
   Un run ne relit que les livraisons des deux derniers mois et ne réécrit que
   ces fichiers-là.
4. **Même fabrique d'index que la voie 2** : `amendements_contenu` est importé —
   `mots_du_texte`, `forme_indexee`, l'encodage des renvois, les seuils. Une
   seule fabrique, un seul contrat de lecture pour l'interface.
5. **Aucun rattachement à une personne.** `<AUTORITE>` est vide sur tous les
   décrets : un acte se rattache à un gouvernement par sa date de publication, à
   un ministère par son libellé d'organe. « N décrets signés » n'est pas
   constructible, et c'est la source qui ferme le piège (#664).
6. **La date bouche-trou `2999-…`** de la source (386 actes) ne fait pas un mois :
   `sans-date.json`, `mois: null` (§2 règle 5).

## Mesures

Le 22/09/2026, sur le dump global (1 674 608 486 octets) et les 800 livraisons
quotidiennes du 13/07/2025 au 22/09/2026, lus en flux, 2 011 s, 0 erreur :

| Grandeur | Mesure |
| --- | ---: |
| Actes depuis 2007 | **389 397** (311 727 arrêtés, 76 664 décrets, 1 006 ordonnances) |
| Articles lus | 2 368 125 |
| Index de mots, découpé par mois | ~124 Mo |
| Métadonnées, nature et ministère en table | ~86 Mo |
| Actes portant « carbur… » | 1 184 |

## Alternatives rejetées

| Écartée | Mesure |
| --- | --- |
| Le titre seul | 0,4 Mo d'index sur six mois contre 2,8, mais 13 actes « carburant » contre 51 |
| Un index global, non découpé | 151 Mo — le moins lourd, mais aucun run ne peut le reconstruire : 3,8 Go de livraisons à relire |
| Un découpage par année | 171 Mo, 40 de moins que par mois, mais un run de décembre relit 1,8 Go pour l'année en cours |
| Un découpage par année avec un brut commité de l'année | 171 Mo + 26 Mo par année vivante, qui s'accumulent |
| Les décrets d'application des lois publiées (#664) | le lien `APPLICATION` n'est plus posé depuis 2024 : 0 des 188 lois du fonds promulguées depuis le 01/01/2024 |
| Rapprocher deux intitulés voisins (« ventre » / « vente ») | une forme devinée, publiée comme un fait |

## Ce que cette décision ne couvre pas

- **Ce que l'interface en affiche** : rien n'est décidé ici. L'index rend un acte
  trouvable ; la vue relève de l'épic #324.
- **Les décrets antérieurs à 2007** : le dump remonte à 1861, la borne est un
  choix de couverture, pas une limite de la source.
- **Les redélivrances d'actes anciens** : un acte publié avant le mois relu n'est
  pas mis à jour, même si la DILA le redélivre — un mois clos ne change plus.
