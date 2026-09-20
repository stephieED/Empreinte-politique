<a id="recherche-fiche-groupe-979"></a>

# La recherche sur la fiche de groupe couvre toute la lignée (#979) (2026-09-17)

`2026-09-17`

> **En bref** — La barre « Rechercher sur cette page » arrive sur la fiche de
> groupe. « En bref » et « Qui sont-ils » se retirent sous un mot, « Ce qu'on
> n'a pas pu lire » reste ; les sections 2 à 5 se recalculent sur la projection
> et empilent les groupes de la lignée où le mot trouve quelque chose. Les
> débats complets, que la projection ne porte pas, vivent dans un fichier à
> part chargé au premier mot.

## Contexte

La recherche de la fiche candidat a été livrée par #993
(`filtre-par-intitule-fiche-candidat-979`). La propriétaire a demandé le même
geste sur la fiche de groupe, avec deux différences : « Qui sont-ils » se
retire aussi, et « Ce qu'on n'a pas pu lire » ne change pas.

La page de groupe ne lit pas des profils mais une PROJECTION de lignée
(`vue-lignee.mjs`), calculée au build, et une lignée enchaîne plusieurs groupes
(Nouvelle Gauche XVe, puis Socialistes XVe, XVIe et XVIIe). Maquette sur les
Socialistes avec « retraite ».

## Décision

| Point | Retenu | Pourquoi |
| --- | --- | --- |
| Sections retirées | « En bref », « Qui sont-ils » | Demandé par la propriétaire |
| « Ce qu'on n'a pas pu lire » | **Inchangée** | Demandé par la propriétaire : ses signalements portent sur les fiches, pas sur le mot |
| Le recalcul | `filtrerLignee` réduit la projection maillon par maillon et recompte chaque figure sur les listes qu'elle transporte déjà : débats, textes, dossiers amendés par commission, scrutins par part, textes comparés par nature | Aucune donnée à retélécharger, les mêmes règles de lecture qu'hors recherche |
| Ce qui ne se recompte pas | **Tu sous un mot** : le total de scrutins agrégés (« sur N ») et le reste d'amendements sans type | Aucune liste ne les porte ; les laisser serait publier un total de carrière sous une figure filtrée |
| Les groupes d'une lignée | **Tous à la suite, sans flèches** (forme B) : chaque section empile les groupes où le mot trouve quelque chose, du plus récent au plus ancien ; tous vides, le plus récent dit que le mot ne trouve rien | « La recherche doit couvrir toute la lignée » ; un groupe resté derrière une flèche se manquait |
| Les débats | **Un fichier par lignée**, `<id>.debats.json`, chargé au premier mot | La projection n'en porte que 10 par groupe (10 sur 284 pour NG-15). Les y ajouter coûtait ~2 Mo sur 29 fiches, payés par chaque lecteur ; en `[intitulé, porteurs]` à part : 1,0 Mo pour les douze lignées, 115 Ko pour la socialiste, et rien sans recherche |
| La barre | `components/Recherche.jsx`, extraite de la fiche candidat | Un seul texte, une seule étiquette, une seule note pour les deux fiches |

Sous un mot, la liste des votes porte toutes les parts (« Tous les scrutins »),
les dossiers amendés de chaque commission sont dépliés, les lectures
antérieures sont ouvertes et les textes comparés s'affichent sans clic.

## Alternatives écartées

- **Un groupe à la fois, flèches conservées** (forme A) : page plus courte
  (5 441 px contre 11 878 sur « retraite »), mais la recherche ne couvrait que
  le groupe affiché.
- **Les débats complets dans la projection** : ~2 Mo de plus pour tous les
  lecteurs, recherche ou pas.
