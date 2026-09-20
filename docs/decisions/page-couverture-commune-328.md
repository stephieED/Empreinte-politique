# Une page de couverture commune, et deux mentions de fiche allégées (#328) — 09/09/2026

`2026-09-09`

> **En bref** — suite de [`pourquoi-en-methodologie-328`](decisions/pourquoi-en-methodologie-328.md), qui avait sorti le raisonnement de la fiche : **160 des 239 entrées de couverture sont identiques sur les 27 fiches** — bornes AMO30, scrutins, Syceron, preuves mot pour mot —, et ce qui varie est minoritaire et mesurable (`fait_etabli` 35, `non_collecte` 26, `textes_portes hors_couverture` 19) ; elles partent sur **`/couverture`**, deux parties et pas davantage — la frise « ce que le dépôt porte » et le tableau « ce qui manque, et sur quelles fiches » ; **l'institution est le premier niveau** (Assemblée, Gouvernement, Sénat, Parlement européen, mandats locaux), ses listes en dessous, les champs au repli, et **la fiche d'origine est une teinte, jamais un niveau** : trois fiches portant le même fait sur la même période vivent dans le **même rail**, superposées en `mix-blend-mode: multiply` — l'inverse a été essayé et rejeté, une piste par origine mettant trois lignes là où il y a un fait ; **la scission parlementaire/gouvernemental est lue sur trois champs publiés** et jamais sur un intitulé (#639) — `categorie === 'fonction_gouvernementale'`, `role === 'initiateur_projet_de_loi'`, et la qualité `fonction` du compte rendu, qui nomme une fonction gouvernementale sur **6 201 des 21 725 interventions** : elles se scindent donc comme les textes portés, 15 524 sous l'Assemblée et 6 201 sous le Gouvernement ; **la borne dessinée est celle que la source déclare**, pas le minimum des dates rencontrées (qui la rendrait tautologique), et la hachure s'arrête au plus tôt des deux — mesuré : la borne des textes portés dit le **21/06/2017** quand le corpus en porte depuis **12/2010**, hachurer jusqu'en 2017 effacerait sept ans de faits ; **les deux mentions de fiche gardent leurs chiffres et renvoient le pourquoi** à `/methodologie#votes` et `/methodologie#interventions`, où les deux paragraphes existaient déjà mot pour mot ; **la projection est calculée au build** (`scripts/couverture-corpus.mjs` → `public/data/couverture.json`, 32 Ko), comme les comparaisons de groupe (#329), avec un cache sur les dates plutôt qu'un drapeau — lire les quatre index d'amendements coûte 17 à 28 s et le refaire à chaque `npm run dev` serait intenable ; **deux indexations fausses trouvées en écrivant** : `scrutins.json` porte une liste et `scrutins_dossiers.scrutins` une table vers une chaîne, les traiter en objets rendait tous les votes vides sans lever la moindre erreur ; **alternative écartée** — garder la section complète sur chaque fiche et n'ajouter que la page, moindre risque et défaut intact, une limite de source affichée sous le nom d'une personne se lisant comme une limite de cette personne. 14 tests neufs, suite complète à 4 309, 0 échec.

## Contexte

La section « Ce qu'on n'a pas pu lire » de la fiche candidat portait 239 entrées
de couverture sur 27 fiches. **160 d'entre elles sont identiques sur les 27** :
la borne de l'AMO30 pour les mandats, celle des scrutins pour les votes, celle du
Syceron pour les interventions, avec leur preuve mot pour mot. Deux tiers de la
section ne parlaient donc pas du candidat affiché — elles décrivaient ce que
l'Assemblée nationale publie.

Ce qui varie d'une fiche à l'autre est mesurable et minoritaire : `fait_etabli`
(35 entrées), `non_collecte` (26), `textes_portes hors_couverture` (19).

Le même défaut existait sous deux figures. « Ce qu'il a voté » et « Ce qu'il a
dit » terminaient chacune par un bloc « Ce que cette figure ne sait pas » qui
mêlait deux choses de nature différente : **des chiffres vrais de cette
personne** (« 62 de ses 101 positions sont rattachées à une commission ») et
**un paragraphe d'explication identique sur les 30 fiches** (d'où vient le
rattachement, pourquoi la source ne publie la qualité que pour une fonction
particulière). Le second noyait le premier.

## Décision

**Une page commune, `/couverture`, dit une fois ce qui est vrai du corpus.**
Elle porte deux parties, et pas davantage :

1. **« Ce que le dépôt porte, et depuis quand »** — une frise, l'institution au
   premier niveau (Assemblée nationale, Gouvernement, Sénat, Parlement européen,
   mandats locaux), ses listes en dessous, les champs de chaque liste au repli.
2. **« Ce qui manque, et sur quelles fiches »** — par liste, combien des fiches
   qui ont siégé la portent, qui manque parce que son mandat précède la borne, et
   qui manque sans cause connue.

**La fiche d'origine est une teinte, jamais un niveau de hiérarchie.** Candidats,
gouvernements, groupes : trois fiches peuvent porter le même fait sur la même
période. Elles vivent dans le **même rail**, superposées en `mix-blend-mode:
multiply`, et le mélange se voit. Une piste par origine mettait trois lignes là
où il y a un fait — c'est l'arbitrage du 09/09, pris après avoir essayé l'inverse.

**Les deux mentions de fiche gardent leurs chiffres et renvoient le pourquoi.**
« Ce qu'il a voté » renvoie à `/methodologie#votes`, « Ce qu'il a dit » à
`/methodologie#interventions`. Les deux paragraphes existaient déjà là-bas, mot
pour mot : la fiche les répétait.

**La projection est calculée au build, pas dans `pivot_data/`.**
`web/UI_finale/scripts/couverture-corpus.mjs` lit le pivot et écrit
`public/data/couverture.json` (32 Ko), appelé par `sync-data.mjs` — même
raisonnement que `comparaison-groupes.mjs` (#329). Elle ne crée aucun fait : elle
compte ce que les sept sorties portent déjà. En faire une huitième sortie
ajouterait un job, un cache et un budget CI pour un fichier que seule l'interface
lit.

Le cache porte sur les dates, pas sur un drapeau : lire les quatre index
d'amendements (141 Mo) coûte de 17 à 28 secondes selon la machine, et le refaire
à chaque `npm run dev` rendrait le démarrage insupportable. `sync-data` compare
la date du fichier produit à la plus récente de ses entrées, `couverture-corpus.mjs`
compris.

## Ce que la mesure a établi, et qui n'était pas prévu

| Fait mesuré | Conséquence |
| --- | --- |
| `interventions[].fonction` nomme une fonction gouvernementale sur **6 201** des 21 725 interventions | Les interventions se scindent comme les textes portés : 15 524 sous l'Assemblée, 6 201 sous le Gouvernement |
| La borne déclarée des textes portés est le **21/06/2017**, le corpus en porte depuis **12/2010** | La hachure s'arrête au plus tôt des deux : elle ne passe jamais par-dessus un fait |
| Les interventions déclarent leur borne en `fait_etabli`, pas en `couvert` | Les deux états valent « publiée à partir de » ; ne lire que le premier laissait la borne vide, donc aucune hachure, donc un blanc qui se lit « rien fait » (§2 règle 5) |
| `scrutins.json` porte une **liste**, `scrutins_dossiers.scrutins` une table vers une **chaîne** | Deux indexations fausses rendaient les votes vides sans lever la moindre erreur |

## Alternative écartée

**Garder la section complète sur chaque fiche, et n'ajouter que la page.** C'était
le choix du moindre risque : rien à retirer, rien à casser. Il laissait les 160
entrées identiques là où elles sont, c'est-à-dire là où un lecteur les prend pour
un fait sur la personne dont il lit la fiche. La duplication n'est pas un défaut
de volume, c'est un défaut de sens : une limite de source affichée sous le nom
d'une personne se lit comme une limite de cette personne.

**Une teinte par nature du fait (parlementaire / gouvernemental / de groupe)
plutôt que par fiche d'origine.** Essayée, et rejetée par la propriétaire : elle
rendait la scission parlementaire/gouvernement plus lisible dans le rail, mais
faisait perdre l'information « de quelle fiche ce trait vient-il », qui est la
question que la page pose. La scission institutionnelle est portée par la
hiérarchie, pas par la couleur.
