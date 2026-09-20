<a id="constat-absence-mandats-anterieurs-860"></a>
# Une liste vide affirme quelque chose, donc elle porte sa source (#860) (2026-09-15)

`2026-09-15`

> **En bref** — `mandats_anterieurs: []` ne dit pas « rien à signaler » : il
> affirme qu'une personne n'a exercé **aucun mandat national avant le
> 19/06/2002**. C'est un fait publié, et §2 règle 2 veut qu'il renvoie à sa
> source primaire — ce qu'une liste pleine fait ligne par ligne, et qu'une liste
> vide ne pouvait pas faire. Une entrée sans mandat exige désormais un
> `constat` : l'URL consultée, la date, et la **méthode**. Douze candidats
> déclarés en reçoivent un, tiré de leur fiche Sycomore lue intégralement.

## Contexte

#861 avait posé la distinction qui compte, et elle tenait : un slug présent dans
la table est relu — sa liste, vide ou non, est complète ; un slug absent ne l'est
pas, et la fiche publie `null` + `non_relu`. « Aucun » et « on ne sait pas » ne
se confondaient déjà pas.

Restait un angle mort. Les cinq entrées de la table portaient toutes des
mandats, chacun avec sa `source_url` — Sycomore pour un député, un décret au JO
pour une fonction gouvernementale. Le jour où une entrée n'en porte aucun, la
fiche affirme sans rien montrer : la source vivait sur les lignes, et il n'y a
plus de ligne.

Le cas est devenu concret le 15/09/2026. Douze candidats déclarés ont vu leur
fiche Sycomore lue de bout en bout, mandat par mandat : aucun n'a de mandat
antérieur au 19/06/2002. Ces douze absences sont vérifiées et reproductibles —
et la table n'avait aucun endroit où l'écrire.

## Décision

Une entrée sans mandat est un **objet** `{"mandats": [], "constat": {…}}`, et
son constat porte les trois :

| Champ | Ce qu'il dit |
| --- | --- |
| `source_url` | la page consultée — https, sinon refus |
| `constate_le` | la date de la consultation, ISO |
| `methode` | **qui a regardé**, dans `KNOWN_METHODES_CONSTAT_ANTERIEUR` |

Une entrée qui porte des mandats reste une **liste**, et se voit refuser un
`constat` : deux endroits pour un même fait finissent par diverger.

Sur le pivot, `mandats_anterieurs_constat` accompagne la liste vide, et
seulement elle. Comme `mandats_anterieurs`, il est **reposé** à chaque écriture
depuis la table, jamais fusionné (#493, #530) : un constat retiré de la table
disparaît de la fiche au passage suivant.

## Pourquoi la méthode est nommée, et pourquoi elle est fermée

`lecture_fiche_sycomore` et `relecture_humaine` **ne se valent pas**, et les
confondre était le risque réel de ce lot.

La première est une lecture de la source primaire par le pipeline : le parseur
restitue à l'identique les quatre lignes relues à la main le 11/09, elle est
reproductible et se re-vérifie seule. La seconde est une **signature** — quelqu'un
a regardé et engage sa relecture. Rien d'automatique ne pose une signature à la
place de quelqu'un ; c'était l'engagement pris dans cette issue le 12/09, et un
champ `verifie_le` unique pour les deux l'aurait effacé sans que personne le
remarque.

## Ce que le lot ne fait pas

Quinze candidats déclarés restent `non_relu`. Sept d'entre eux sont nés après le
19/06/1979 et ne **pouvaient pas** être élus avant la borne — il fallait 23 ans,
l'âge n'a été abaissé à 18 que par la loi organique n° 2011-410 du 14 avril
2011. Sept autres n'ont ni poste national ni identifiant Sycomore sur Wikidata,
et leur article de Wikipédia ne mentionne aucun mandat. Le dernier,
`benoit-mathieu`, n'a ni article, ni acteur AMO30, ni date de naissance.

Aucun des trois cas n'est une source primaire, et **aucun n'entre dans la
table**. Ce qui les débloquerait est une recherche Sycomore par nom : le moteur
(`/sycomore/resultats`) rend la même page de 35 968 octets quels que soient les
paramètres, y compris pour `ROYAL` qui a pourtant une fiche — le témoin positif
échoue, donc l'absence de résultat ne prouve rien. Une fiche se lit très bien
quand on connaît son numéro ; on ne peut pas la chercher par son nom.

## Alternative écartée

**Un `verifie_le` unique, posé par le script sur les douze.** C'était une ligne
de code, et cela revenait à signer une relecture humaine avec une lecture
machine. La distinction aurait disparu du fichier, donc de la fiche, donc de ce
qu'un lecteur peut savoir de la valeur du constat.
