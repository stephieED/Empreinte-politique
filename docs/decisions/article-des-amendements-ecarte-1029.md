<a id="article-des-amendements-ecarte-1029"></a>

# Le champ `article` des amendements ne sera pas publié (#1029) (2026-09-25)

`2026-09-25`

> **En bref** — Le champ `article` est complet sur les quatre législatures : 685 723
> amendements nomment la division du texte qu'ils visent. Trois formes ont été
> maquettées sur données réelles le 25/09/2026. **La propriétaire les a toutes
> écartées : la donnée ne fait pas sens pour un lecteur.** Ce fichier existe pour que
> le champ ne soit pas redécouvert comme une occasion manquée.

## Ce que le champ porte, mesuré

Mesuré le 25/09/2026 sur `pivot_data/amendements/<lég>.json`, au commit de données du
run 36040086663 :

| Mesure | Valeur |
| --- | --- |
| Amendements portant une division | **685 723** sur quatre législatures |
| Textes visés | **2 572** — 34 amendements et 6 divisions par texte en médiane |
| Insertions (`Avant` / `Après`) plutôt que modifications (`A`) | **28,8 %** |
| Intitulés distincts, bruts → repliés | **3 342 → 2 978** |

**Le champ n'est pas en cause, et il n'est pas défectueux** : la jointure vers les
profils passe (François Ruffin 48 440 amendements retrouvés, Delphine Batho 9 035), et
`<lég>.contenu.json` porte le même champ aligné sur `ids`. Deux irrégularités ont été
mesurées et traitées en maquette, donc elles ne sont pas la raison du refus :
**319 intitulés portent plusieurs graphies** pour la même division (« ÉTAT B », « ETAT B »,
« ÉTAT&nbsp;B »), couvrant 89,3 % des amendements ; et **toutes les divisions ne sont pas
des articles** — 89,8 % le sont, 6,0 % sont un état budgétaire, 3,7 % un chapitre, un
titre, une annexe ou l'article unique, 0,5 % l'intitulé même du texte.

## Les trois formes examinées, et ce que chacune butait

Maquettées sur 4 textes réels et les 14 candidats publiés qui ont des amendements.

| Forme | Ce qu'elle montrait | Ce qui coinçait |
| --- | --- | --- |
| **A** · géographie d'un texte | Les divisions dans l'ordre du texte, et les amendements déposés sur chacune | Elle décrit un **texte**, et le site n'a pas d'objet « texte » : aucune page où la poser |
| **B** · amender ou ajouter | Deux totaux par personne, sans connaître aucun texte | Tient sur la fiche candidat sans coût de navigation, mais on ne peut rien en conclure |
| **C** · la personne dans le texte | Ses amendements dessinés dans le total du texte | Une division vide se lit « il n'a rien déposé » alors qu'il pouvait ne pas être en fonction |

## La décision

**Aucune des trois. Le champ n'est pas publié.** Arbitré par la propriétaire le
25/09/2026, sur maquette : la donnée ne fait pas sens pour un lecteur.

C'est l'application de la **règle de forme 1** (`DESIGN_SYSTEM.md` §6 bis) : *un chiffre
dont le lecteur ne peut rien tirer ne se publie pas*. Elle disqualifie une mesure vraie,
disponible et conforme — ce que ni `AGENTS.md` §2 ni le schéma ne savent faire, puisque
tous deux disent ce qui est interdit et jamais ce qui est inutile.

Le constat qui la soutient, et qui vaut pour les trois formes : **un numéro d'article ne
dit rien hors de son texte.** « Article 3 » n'est pas la même chose d'un texte à l'autre,
et les 2 572 textes visés n'ont, eux, aucune page sur le site — les objets publiés sont
les candidats, les groupes et les gouvernements.

## Ce que ça n'interdit pas

Le champ **reste collecté et publié dans le pivot** : il ne coûte rien, il est aligné sur
`ids`, et rien ne justifie de le retirer. Ce qui est écarté est sa **publication dans
l'interface**.

**Ne rouvrez pas sans un objet « texte » dans le site.** C'est la seule condition qui
change le raisonnement : la forme A devient alors la géographie d'une page qui existe, et
le numéro d'article retrouve le contexte qui lui manque aujourd'hui.
