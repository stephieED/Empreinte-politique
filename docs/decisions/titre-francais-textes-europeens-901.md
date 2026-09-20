<a id="titre-francais-textes-europeens-901"></a>
# Le titre français était téléchargé puis jeté (#901) (2026-09-16)

`2026-09-16`

> **En bref** — Les fiches affichaient « JOINT MOTION FOR A RESOLUTION on
> Azerbaijan… », le titre anglais du dump ParlTrack. Le portail du Parlement
> publie le **même document en 22 à 23 langues**, français compris — et
> `ResolveurDocuments` téléchargeait déjà cette réponse pour n'en tirer qu'un
> booléen d'existence. Le titre français est désormais publié, avec
> `titre_langue` qui dit dans quelle langue le titre l'est. **Aucune requête
> supplémentaire.**

## Contexte

La question de départ portait sur la matière des 628 résolutions sans dossier.
En instruisant l'accès au portail, la mesure a trouvé autre chose : sur 20 de
ces documents tirés au hasard, **20 sur 20** portent un titre français, et 19 un
titre anglais.

Or nos fiches publient l'anglais, parce que c'est ce que le dump ParlTrack
donne. Le portail, lui, était déjà interrogé — `ResolveurDocuments._interroger`
lit la réponse, en tire `True`/`False`, et jette le reste.

**Ce n'est pas une traduction que nous fabriquerions.** C'est la version
française officielle du même document, sous la licence du portail (§7,
attribution). Traduire nous-mêmes aurait été un fait non sourcé ; reprendre ce
que le Parlement publie est un fait sourcé comme un autre.

## Décision

| | |
| --- | --- |
| `titre` | le titre **français** dès que le portail en a un, sinon celui du dump |
| `titre_langue` | `"fr"` \| `"en"` \| `null` — dans quelle langue le titre publié est |

Le champ de langue n'est pas décoratif. Sans lui, plus rien ne permet de mesurer
combien de titres restent en anglais, ni d'empêcher un lecteur de croire que
nous traduisons. Arbitré le 16/09/2026, contre deux autres formes : remplacer
sans rien dire, ou garder les deux titres côte à côte.

**Le repli est la partie qui compte.** Quand le portail n'a rien — pas de
référence citée, document introuvable, question non posée, hors ligne — le titre
anglais du dump est conservé et `titre_langue` vaut `"en"`. Publier un titre
vide serait pire que le publier dans la mauvaise langue (§2 règle 5).

## Le coût : zéro requête de plus

Le portail est lent et limité — une requête toutes les 0,6 s, `429` avec
`Retry-After` au-delà, 13 blocages sur 1 320 requêtes lors de la mesure de #827.
Un second appel pour le titre aurait doublé la facture.

Il n'y en a pas : existence et titre viennent de **la même réponse**, et le
cache disque porte les deux. `documents-doceo-v1` mappait un doceo sur un
booléen ; **v2** le mappe sur `{"existe", "titre_fr"}`. Un cache v1 se relit
sans être invalidé — ses entrées valent « existe, titre inconnu », et le titre
se remplit à la prochaine interrogation.

## Les deux fabriques portent les mêmes clés

`textes_portes[]` a deux fabriques : les dossiers dont la personne est
rapporteure, et les activités portées. La première version de ce lot n'avait
posé `titre_langue` que sur la seconde, et
`test_les_deux_fabriques_portent_les_memes_cles` l'a refusée — c'est exactement
ce pour quoi ce test existe : une fiche ne doit pas distinguer deux textes selon
le chemin qui les a produits.

La fabrique des dossiers pose donc `titre_langue: "en"`, et c'est exact : le
titre d'un dossier vient du dump, en anglais, et aucun document `doceo` ne s'y
rattache pour aller chercher une version française.

## Ce que le lot ne fait pas

La **matière** des 628 résolutions sans dossier. Le portail la porte aussi —
`is_about` rend 2 à 9 concepts EUROVOC par document, sur les 20 de
l'échantillon — mais les concepts sont des URI numériques
(`eurovoc.europa.eu/2155`) qu'il faut résoudre en libellés, par le SPARQL de
l'Office des publications (`2155` → « opposition politique »). C'est un lot à
part, et il demande un arbitrage éditorial que le titre ne demande pas.
