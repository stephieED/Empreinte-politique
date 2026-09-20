<a id="mesure-publiee-devenue-fausse-886"></a>
# Une mesure écrite dans un texte publié devient fausse le jour où un lot déplace le corpus (#886) (2026-09-13)

`2026-09-13`

> **En bref** — trois textes visibles à l'écran affirmaient « **511 interventions dont l'URL de source pointe encore vers nosdeputes.fr** » et « rien de ce qu'elles ont produit n'a été effacé ». Le commit `475a1b3e2` du **27/08/2026** les a écrits, et ils étaient **vrais** ce jour-là, mesurés au commit de données `74c77c2`. Le commit `cf71e06c5` du **12/09/2026** — « 511 interventions et 5 onglets de page retirés, aux deux couches » — les a rendus faux. Seize jours. La cause n'est pas une négligence : [`nettoyage-sediment-839`](nettoyage-sediment-839.md) §3 avait bien posé la règle « un retrait recompose ses champs dérivés dans la foulée », et l'avait appliquée aux **données** — tags, `meta.licence_donnees`. Il ne l'a pas appliquée à la **prose**, qui vit dans `web/UI_finale` et était hors de son périmètre. La règle s'étend donc : **un texte publié qui cite un chiffre est un champ dérivé de plus**, et le lot qui déplace ce chiffre le recompose ou le corpus publie une affirmation fausse indéfiniment. Trois textes, et non deux : `Faq.jsx` portait la même phrase. Mesuré le 13/09/2026 sur `origin/main` `79719b29e`, **0** intervention à URL Regards Citoyens et **0** intervention portant un `mots_cles`, aux deux couches — la phrase ne décrivait plus rien du tout.

## 1. Ce qui était affiché, et ce que le corpus portait

| Affirmation publiée | Où | Mesure du 13/09/2026 |
| --- | --- | ---: |
| « 511 interventions dont l'URL de source pointe encore vers nosdeputes.fr » | `sources.config.js:20` | **0**, aux deux couches |
| « des prises de parole (dont l'URL de source pointe encore vers nosdeputes.fr) … restent publiés » | `LegalNoticePage.jsx:104` | **0** |
| « les mots-clés dont sont dérivés les tags thématiques » | `sources.config.js:20`, `Faq.jsx:12` | **0** intervention portant un `mots_cles` |
| « rien de ce qu'elles ont produit n'a été effacé » | `sources.config.js:22`, `Faq.jsx:12` | **511** interventions retirées |

La dernière phrase était déjà signalée comme à reformuler par la propriétaire ; les trois autres ne l'étaient pas.

## 2. Ce qui reste vrai, et que les trois textes disent maintenant

Des **mandats** et des **éléments d'identité** collectés avant 2026 dérivent encore de Regards Citoyens. Sur **1 196 profils publiés** (32 candidats déclarés, 1 164 membres de roster) :

| Marqueur `sources[].type` | Profils | Population |
| --- | ---: | --- |
| `nosdeputes` | **474** | 465 membres de roster, 9 candidats déclarés |
| `nossenateurs` | **2** | 2 candidats déclarés |
| au moins l'un des deux | **475** | 476 entrées — `bruno-retailleau` porte les deux |

L'attribution ODbL reste donc due, et les trois textes continuent de la porter. Ce qui change, c'est qu'ils nomment les champs qui l'engagent **réellement** au lieu d'en citer un qui n'existe plus.

## 3. Ce que l'incident apprend, et qui généralise #839

`nettoyage-sediment-839` §3 avait la bonne règle : « un retrait recompose les champs dérivés dans la foulée, ou le corpus committé publie une dérivation d'entrées qu'il ne porte plus ». Son motif était le délai — « entre le merge et le run, une à deux heures, parfois un jour ». **Sur la prose, il n'y a pas de délai : il n'y a pas de run qui repasse.** Une phrase fausse le reste jusqu'à ce que quelqu'un la relise, et personne ne relit une phrase qui était vraie quand elle a été écrite.

C'est la même leçon que [`borne-mandats-acteur-nest-pas-depute`](borne-mandats-acteur-nest-pas-depute.md) §4 — « un commentaire juste ne protège pas d'un texte faux : ce qui est publié doit porter sa propre mesure » — vue depuis l'autre bout : là, le commentaire du code était juste et la phrase publiée fausse ; ici, la phrase publiée était juste et c'est le **corpus** qui a bougé sous elle.

**La conséquence pratique** : un lot qui retire ou ajoute des entrées doit chercher son propre chiffre dans `web/UI_finale/src` avant de se clore. `sources.config.js`, `LegalNoticePage.jsx` et `Faq.jsx` sont les trois fichiers qui en portent ; `lecture.js:259` en porte un quatrième, en commentaire, qui justifie le libellé `SOURCE_BADGE_VERIFIED` par « 511 pointent vers nosdeputes.fr » — non corrigé ici parce qu'il n'est pas affiché, mais il est désormais faux lui aussi et son argument ne tient plus.

## 4. Les verrous sont respectés, pas modifiés

`tests/test_licences_530.py` gèle les textes affichés : la page des mentions légales doit nommer « NosDéputés.fr », « NosSénateurs.fr » et « Open Database License (ODbL) v1.0 » (l. 196), et `sources.config.js` doit garder son entrée `nosdeputes-nossenateurs` avec « Plus collectée », « ODbL v1.0 » et « attribution » (l. 222). **Les trois réécritures conservent tout cela** : c'est la mention de l'attribution qui est gelée, pas la description du contenu. Suite passée : `test_licences_530.py`, `test_page_couverture.py`, `test_retrait_nosdeputes_529.py` — **80 passed**.

## 5. L'alternative écartée

**Ne corriger que les deux phrases nommées et laisser les deux autres.** Elles ont la même cause, elles sont dans le même bloc de texte pour l'une et dans un fichier voisin pour l'autre, et une correction partielle aurait laissé la page d'accueil affirmer « rien n'a été effacé » à côté d'une page de mentions légales disant le contraire. Le périmètre suit le défaut, pas l'énoncé qui l'a signalé.
