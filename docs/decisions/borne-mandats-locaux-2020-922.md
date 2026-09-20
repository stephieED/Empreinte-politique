<a id="borne-mandats-locaux-2020-922"></a>
# Les mandats locaux commencent en 2020, et l'avant se déclare (#922) (2026-09-15)

`2026-09-15`

> **En bref** — Deux jeux couvrent 2020 → aujourd'hui sous Licence Ouverte 2.0 :
> le RNE pour les mandats **en cours**, les sortants 2020-2026 pour la mandature
> précédente. Les paliers antérieurs sont **écartés**, et pour deux raisons
> distinctes qu'il ne faut pas confondre : le jeu complet de 2014 et celui de
> 2020 ne déclarent **aucune licence**, et les seuls jeux de 2014 sous Licence
> Ouverte ne couvrent que le **premier tour**. Une fiche ne publiera donc rien
> avant 2020 — et **dira pourquoi**, au lieu de se taire.

## Contexte

#922 veut publier les mandats locaux. Quatre jeux de données ont été instruits.

| Jeu | Couverture | Licence | Format |
| --- | --- | --- | --- |
| **RNE** (`repertoire-national-des-elus-1`) | mandats **en cours**, 12 fichiers | **Licence Ouverte 2.0** | CSV, API tabulaire |
| **Sortants 2020-2026** (état au 27/02/2026) | la mandature 2020-2026 | **Licence Ouverte 2.0** | CSV, API tabulaire |
| Municipales 2020 | **premier tour seul** | **non spécifiée** | xlsx / txt |
| Municipales 2014 — « Liste des élus » | complète | **non spécifiée** | xls |
| Municipales 2014 — « Élus au 1er tour » | **premier tour seul** | Licence Ouverte | txt |

## Ce que la mesure a établi

**Les deux premiers jeux suffisent à couvrir 2020 → aujourd'hui**, et ils se
complètent : le RNE ne porte que la mandature qui vient de commencer — toutes les
dates municipales y sont au 15 ou 22/03/2026 —, les sortants portent la
précédente, avec `Date de début du mandat` **et** `Date de début de la fonction`.

Mesuré le 15/09/2026 : Tondelier `2020-05-18`, Lisnard `2020-05-18` et maire
depuis le `2020-05-23`, Bouamrane **`2020-06-28`** et maire depuis le
`2020-07-07`.

**Ce dernier chiffre écarte à lui seul le palier 2020** : Karim Bouamrane a été
élu au **second tour**, donc il est absent du jeu 2020, qui ne porte que le
premier. Le fichier des sortants le donne, et mieux. **Ajouter 2020
n'apporterait aucune date que nous n'ayons déjà, et il en manquerait.**

## Décision

1. **La couverture commence en 2020.** Deux jeux, tous deux sous Licence
   Ouverte 2.0, tous deux interrogeables par `tabular-api.data.gouv.fr` sans
   téléchargement de masse.

2. **Aucun palier antérieur n'est intégré.** Ni 2014, ni 2020.

3. **L'absence se déclare, elle ne se tait pas.** Une fiche ne doit jamais
   laisser lire « cette personne n'avait pas de mandat local avant 2020 » : elle
   doit dire que **nous ne pouvons pas le savoir**. C'est la borne de
   `couverture_dossiers.borne_couverture_textes` appliquée au versant local, et
   le régime de `mandats_anterieurs` + `non_relu` (#860).

   Le cas qui le rend concret : **Nathalie Arthaud a été conseillère municipale
   de Vaulx-en-Velin, élue en 2008.** Aucun jeu accessible ne le porte. Publier
   sa fiche sans rien dire en ferait une personne sans parcours local, ce qui est
   faux (§2 règle 5).

4. **Ce que le module de collecte devra porter**, quand il sera écrit : une
   borne publiée — la date à partir de laquelle la couverture existe — et un
   motif quand un mandat est hors de portée. Pas un `0`, pas une liste vide sans
   cause.

## Les deux raisons d'écarter, à ne pas confondre

Elles ne se réparent pas au même endroit, et l'une peut disparaître :

- **La licence non établie** — jeux complets de 2014 et de 2020, publiés par le
  ministère de l'Intérieur avec `license: notspecified`. §7 interdit de collecter
  ce qu'on ne peut pas attribuer. **Cette raison tomberait** si la licence était
  précisée par le producteur : la question serait alors rouverte, pas tranchée.
- **La couverture partielle** — les jeux de 2014 sous Licence Ouverte ne portent
  que le premier tour. Les intégrer ferait publier une couverture qui paraît
  complète et ne l'est pas, et la lacune serait invisible : rien, dans une fiche,
  ne distinguerait « pas élu » de « élu au second tour ». **Cette raison-là ne
  tombera pas**, le jeu ne changera plus.

## L'alternative rejetée

**Intégrer 2014 au premier tour, en déclarant la limite.** Écartée par la
propriétaire le 15/09/2026, et l'argument est de qualité plutôt que de volume :
une limite déclarée à l'échelle du corpus n'est pas lisible à l'échelle d'une
fiche. Le lecteur qui consulte un candidat ne sait pas si l'absence de mandat
2014 vient de la personne ou du tour où sa commune a voté — et cette
indétermination-là se propagerait à toutes les fiches, pour un gain d'une seule
mandature.

Mieux vaut une borne nette, dite une fois, qu'une couverture partielle dont
chaque absence est ambiguë.
