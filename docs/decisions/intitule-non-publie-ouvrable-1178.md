<a id="intitule-non-publie-ouvrable-1178"></a>

# La ligne « Intitulé non publié » s'ouvre comme les autres, sur les fiches de groupe et de gouvernement (#1178) (2026-10-04)

`2026-10-04`

> **En bref** — La ligne « Intitulé non publié » comptait les prises de parole
> sans titre de débat et **ne s'ouvrait pas** : sur la XVe législature elle
> pesait des dizaines de milliers d'entrées, 19,6 Mo à charger au clic pour un
> seul groupe. L'arbitrage du 04/10/2026 était « on attend » : elle
> redeviendrait ouvrable quand elle serait petite. Les intitulés publiés depuis
> (#1189, #1197) l'ont rendue petite — **1 307 prises de parole sur 677 100**
> pour les 31 fiches de groupe, contre 74 870 sur 680 068 ; **137** sur les
> fiches de gouvernement. La propriétaire l'a rouverte le soir même : ses
> textes sont servis, elle s'ouvre comme toute autre ligne.

## Le contexte

Une prise de parole dont le compte rendu ne donne pas l'intitulé reste comptée
(`AGENTS.md` §2 règle 5) et se range sous « Intitulé non publié »
([`reponse-au-retour-ux-fiche-groupe`](reponse-au-retour-ux-fiche-groupe.md)).
Tant que la ligne était énorme, le build ne servait pas ses textes : elle se
comptait et ne s'ouvrait pas.

## La mesure

Sur les données reconstruites depuis `main` (`935f4a6ec`, données du run fini
le 04/10/2026 à 17 h 07) :

| Population | Sans intitulé | Total |
| --- | ---: | ---: |
| Prises de parole des 31 fiches de groupe | 1 307 | 677 100 |
| dont La République en Marche, XVe (la plus grande ligne) | 840 | 86 707 |
| Prises de parole des fiches de gouvernement | 137 | 130 753 |
| dont Castex · Philippe II · Bayrou | 75 · 58 · 4 | — |

22 des 31 fiches de groupe portent encore la ligne ; les quatorze autres
fiches de gouvernement n'en portent aucune.

**Elle n'apparaît plus dans les dix débats affichés d'aucune fiche.** Son
meilleur rang est le 27e, sur La République en Marche (XVe). Elle se lit sous
un mot recherché, ou si une pastille de nature la fait remonter.

## La décision

`vue-lignee.mjs` et `vue-parole-gouvernement.mjs` ne sautent plus les textes
sans intitulé ; `LigneeProfile.jsx` et `GovernmentProfile.jsx` rendent la ligne
comme les autres. L'italique du libellé reste : il dit que ce n'est pas un
intitulé de la source. La méthodologie ne dit plus « cette ligne ne s'ouvre
pas ».

## Alternative écartée

Attendre encore, ou retirer la ligne. La retirer ferait disparaître 1 307
prises de parole du compte ; attendre n'avait plus d'objet, la condition posée
étant remplie.

## Ce qui n'a pas été vérifié

L'ouverture par un vrai clic : aucune fiche n'affiche la ligne dans ses dix
premiers débats. Les tests du domaine passent, et le build sert bien les
textes.
