<a id="actes-nominatifs-sortent-par-la-rubrique-1029"></a>

# Les actes nominatifs sortent du compte, par la rubrique du Journal officiel (#1029) (2026-09-25)

`2026-09-25`

> **En bref** — La section « Ce qu'il a fait entrer en vigueur » écartait les actes
> de personne par des formules de titre. 308 arrêtés « fixant la liste des personnes
> autorisées à exercer la profession de médecin » passaient au travers. La rubrique
> du sommaire du Journal officiel (`rubrique_des_actes`, #1134) tranche désormais ;
> le titre n'est plus qu'un repli, et la fiche publie combien d'actes en dépendent.

## Le problème

`ActesDuGouvernement` compte « ce qu'un gouvernement a fait entrer en vigueur ». Les
actes de personne — nomination, cessation, naturalisation — en sortent : les garder
ferait de la section un décompte de carrières.

Le tri se faisait sur le titre, par une liste de formules. Mesuré le 25/09/2026 sur la
fenêtre de Lecornu II : **308 arrêtés « fixant la liste des personnes autorisées à
exercer la profession de médecin »** nomment des personnes une par une et **n'emploient
aucune de ces formules**. Ils représentaient 78 % des actes qui nomment une loi.

**Et compter depuis les titres est une devinette, ce que trois filtres ont démontré** :
308, 321 et 366 pour la même famille d'actes, selon le motif employé. Un compte qui
change avec le motif n'est pas une mesure.

## La décision

**Les actes nominatifs sortent du compte, et c'est le Journal officiel qui dit
lesquels.** Le sommaire de chaque livraison DILA range ses textes — « Mesures
nominatives » contre « Textes généraux » — et `rubrique_des_actes` porte ce rangement,
aligné sur `ids`. `acteDePersonne(titre, rubrique)` lit la rubrique d'abord ; le titre
ne sert plus que de **repli**, là où le sommaire se tait.

La rubrique tranche **dans les deux sens** : un acte dont le titre dit « portant
nomination » mais que le JO range en textes généraux **revient** dans le compte. La
source range, le titre ne la contredit pas.

Sur la fenêtre de Lecornu II, la rubrique classe en mesures nominatives **la totalité**
des arrêtés d'autorisation d'exercice — 366 sur 366 —, quel que soit le filtre par
titre qu'on emploie pour les désigner.

## Ce que la couverture n'est pas

**Une rubrique absente n'est pas « acte général » (§2 règle 5).** La couverture n'est
pas uniforme et ne l'est jamais devenue par décret : mesurée le 25/09/2026 sur les
389 506 actes, elle va de **98,4 % en 2025 à 58,1 % en 2007**, avec 107 892 actes sans
rubrique. Le repli par le titre les tranche, et **la fiche publie combien**, sous le
compte des actes de personne — sinon le repli passerait pour le rangement de la source,
et deux absences se confondraient (règle de forme 7).

Effet mesuré sur le compte publié, avant → après :

| Gouvernement | Actes | Comptés avant | Comptés après | Repli par le titre |
| --- | --- | --- | --- | --- |
| Lecornu II | 19 041 | 11 121 | **10 383** | 2 % |
| Philippe II | 63 626 | 37 611 | **34 465** | 30 % |
| Fillon II | 65 399 | 38 888 | **37 829** | 43 % |

Deux petits gouvernements **montent** — Fillon I de 25 actes, Ayrault I de 6 — parce
que la rubrique leur rend des actes que le titre avait écartés à tort.

## L'alternative écartée

**Élargir les formules de titre.** Écartée parce qu'elle ne règle rien : elle produit
un quatrième compte, aussi arbitraire que les trois autres, et il faudrait la rouvrir à
chaque famille d'actes découverte. Mesuré au passage, un motif élargi (`s à exercer`
en sous-chaîne nue) ramasse un arrêté autorisant **une société** à fournir de
l'électricité et mord au milieu d'une phrase sans rapport.

**Le NOR** a été instruit et ne porte rien d'exploitable : sa dernière lettre est la
nature de l'acte — A pour arrêté, D pour décret — jamais sa portée.
