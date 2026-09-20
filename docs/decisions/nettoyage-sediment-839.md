<a id="nettoyage-sediment-839"></a>
# 516 entrées retirées aux deux couches, et les tags recomposés dans la foulée (#839, lot D) (2026-09-12)

`2026-09-12`

> **En bref** — le nettoyage lui-même, appliqué le 12/09/2026 sur `origin/main` : **511 interventions** héritées sur 5 profils de candidats déclarés (`marine-le-pen` 246, `jerome-guedj` 200, `edouard-philippe` 50, `gabriel-attal` 10, `bruno-retailleau` 5) et **5 onglets de page** publiés comme des commissions sur `jean-luc-melenchon`, **aux deux couches** — un retrait au seul brut ne descend jamais au pivot (#729) ; les 19 entrées **sans jumelle** partent aussi, arbitrage de la propriétaire adossé à la source : vérifiées une par une dans les archives de l'AN, 6 n'y figurent pas, 4 sont attribuées à quelqu'un d'autre, 3 à un orateur collectif que #510 refuse de découper, 6 à la personne sous `PA0` ou un identifiant **négatif** — deux formes qui portent **toutes** `id_mandat="-1"` sur les 118 033 paragraphes mesurés, les `PA0` avec un `code_parole` vide : l'AN ne rattache ces propos à **aucun mandat** ; le drapeau `--retirer-sans-jumelle` reste **explicite** et le défaut prudent ; **les champs dérivés sont recomposés dans la foulée** (§4) — `marine-le-pen` passe de **470 à 152 tags**, exactement ce que sa collecte à blanc du matin avait rendu, ce qui vérifie le nettoyage par une autre voie ; **`edouard-philippe` tombe de 154 à 4 tags**, parce que ses 2 326 interventions Syceron n'en portent que 14 avec un thème officiel — la soupe de mots-clés de l'ancienne source faisait tout le reste ; **8 entrées de même forme sont conservées**, les organes réels du Sénat de `bruno-retailleau`, protégés par une liste close de libellés ; les mandats reproduits ne sont **pas** touchés : ils relèvent de #718 (marquer) et de #729 (doublons), ouverte ; l'audit du lot A rend désormais **0** sur les deux familles d'interventions, et le contrôle de perte déclare 6 baisses attendues, entrée pour entrée.

## 1. Ce qui est retiré, et où

| Famille | Entrées | Profils | Couches |
| --- | ---: | --- | --- |
| `interventions[]` à identifiant entier | **511** | 5 candidats déclarés | brut **et** pivot |
| `mandats[]` : onglets de page publiés comme commissions | **5** | `jean-luc-melenchon` | brut **et** pivot |

Les deux outils simulent par défaut et n'écrivent que sous `--apply`. Chacun est
idempotent.

## 2. Pourquoi les 19 sans jumelle partent aussi

Le lot précédent les conservait : sans jumelle Syceron, la prudence de #387
refusait de les retirer. La propriétaire a demandé la vérification qui manquait —
« c'est l'Assemblée nationale qui fait foi, mais il faut être sûr qu'on n'a rien
raté ». Les 19 ont donc été confrontées aux trois archives.

| Ce que l'AN publie | Entrées |
| --- | ---: |
| rien : le texte est absent de toute l'archive | 6 |
| la prise de parole, attribuée à **quelqu'un d'autre** (Chenu ×2, Arrighi, de Fournas) | 4 |
| la prise de parole, attribuée à un **orateur collectif** incluant la personne | 3 |
| la prise de parole, attribuée nommément à la personne sous `PA0` ou un identifiant **négatif** | 6 |

**Ce sont les 6 dernières qui ont tranché.** Mesuré sur 200 comptes rendus de la
XVIe, 118 033 paragraphes : 1 834 `PA0` et 11 identifiants négatifs, **100 %
avec `id_mandat="-1"`**, et tous les `PA0` avec un `code_parole` vide. L'AN
publie le nom et dit, dans la même balise, qu'aucun mandat n'est derrière : ce
sont les interruptions lancées du banc, et — pour les 5 du Congrès du 09/07/2018
— la parole d'un sénateur, sans mandat à l'Assemblée, hors périmètre (#528).

Les publier sous le nom de la personne ajouterait un lien que la source refuse
de faire. C'est le même défaut que l'`id_acteur` contredit de #510.

**La vérification a coûté trois méthodes fausses**, et c'est ce qui la rend
crédible : borner la recherche à la date exacte rate les séances de nuit, dont
le compte rendu porte la veille ; chercher le texte exact rate l'espace
insécable fine que l'AN met avant « ! » ; ne lire que le premier `<texte>` d'un
paragraphe rate les interruptions, qui y sont imbriquées.

## 3. Les champs dérivés sont recomposés, pas laissés au prochain run

§4 : un champ dérivé se recompose après chaque étape qui le déplace. Un retrait
d'interventions en déplace deux — `tags_thematiques`, qui en dérive entièrement
(#710), et `meta.licence_donnees`, que `licences.py` recompose depuis `sources[]`
**et** les URL d'interventions (#530).

Sans cette recomposition, le corpus committé publierait des tags dérivés
d'entrées qui n'y sont plus, jusqu'au prochain run.

| Profil | Tags avant | Après |
| --- | ---: | ---: |
| `marine-le-pen` | 470 | **152** |
| `jerome-guedj` | 382 | 204 |
| `gabriel-attal` | 221 | 204 |
| `edouard-philippe` | 154 | **4** |
| `bruno-retailleau` | 53 | 51 |

**152, c'est exactement ce que la collecte à blanc de `marine-le-pen` avait
rendu le matin même.** Le nettoyage est donc vérifié par une seconde voie, la
collecte, et non par sa propre logique.

**Les 4 tags d'`edouard-philippe` sont un constat, pas un défaut** : ses 2 326
interventions Syceron ne portent un `theme_officiel` que **14 fois**. Le reste
de son empreinte thématique venait des mots-clés de l'ancienne source
(« abattement », « africain »…), qui ne sont pas des thèmes déclarés (§2 règle
8). La fiche en sort plus pauvre et plus vraie.

## 4. Ce que le lot ne touche pas

- **Les 401 mandats sans `categorie_source` restants** : #718 a tranché
  « marquer, jamais supprimer », et les doublons démontrés relèvent de #729,
  ouverte. Le lot B a mesuré que **280 sur 406** sont portés par un référentiel
  vivant.
- **Les 8 entrées sans date de `bruno-retailleau`** : des organes réels du
  Sénat. La liste close de libellés existe pour elles — un critère de forme seul
  les emporterait.
- **Le marqueur `sources[]`**, sur 475 profils : décision éditoriale à effet
  juridique (§7), mesurée par le lot C et laissée à la propriétaire.

## 5. Ce que le prochain run devra déclarer, à l'entrée près

`interventions`, `mandats` et `tags_thematiques` sont des listes stables : le
contrôle de perte **bloquera**. Les baisses sont voulues et nommées d'avance —
**11 constats**, mesurés le 12/09/2026 par
`python3 src/audit_diff_profils.py --ref <sha avant nettoyage> --seulement-profils` :

| Fichier | Champ | Avant | Après |
| --- | --- | ---: | ---: |
| `bruno-retailleau.pivot.json` | `interventions` | 486 | 481 |
| `bruno-retailleau.pivot.json` | `tags_thematiques` | 53 | 51 |
| `edouard-philippe.pivot.json` | `interventions` | 2 376 | 2 326 |
| `edouard-philippe.pivot.json` | `tags_thematiques` | 154 | 4 |
| `gabriel-attal.pivot.json` | `interventions` | 3 963 | 3 953 |
| `gabriel-attal.pivot.json` | `tags_thematiques` | 221 | 204 |
| `jean-luc-melenchon.pivot.json` | `mandats` | 86 | 81 |
| `jerome-guedj.pivot.json` | `interventions` | 2 702 | 2 502 |
| `jerome-guedj.pivot.json` | `tags_thematiques` | 382 | 204 |
| `marine-le-pen.pivot.json` | `interventions` | 3 203 | 2 957 |
| `marine-le-pen.pivot.json` | `tags_thematiques` | 470 | 152 |

Somme des interventions retirées : **511**. Mandats : **5**.

Le run ajoutera ses propres baisses, sur les **fiches de lignée** : les tags
agrégés sont recalculés depuis les membres, et **508 étiquettes** perdent leur
seul porteur (`AN-RN` 311, `AN-SOC` 178, `AN-REN` 17, `Senat-LR` 2). Ce sont des
mots isolés hérités — « souffrance », « nucléaire », « budget » — qui
s'affichaient à côté de vrais intitulés de texte.

**La déclaration se fait par `allow_declared_losses=true` au lancement**, après
comparaison du rapport du run à ce tableau, jamais en abaissant un seuil. Un
écart, même d'une entrée, doit arrêter le run plutôt que d'être déclaré.

Après le run, deux vérifications closent le lot :

1. `python3 src/audit_sediment.py` — les deux familles d'interventions à **0**,
   `mandats[] actifs et sans aucune date` à **8**, les autres inchangées ;
2. `python3 src/audit_residus_source_retiree.py` — plus aucun profil dont la
   clause ODbL est retenue par une **donnée**.

La couverture des tags qui restent est un sujet à elle seule, ouvert en #876.

## 6. L'alternative écartée

**Laisser le prochain run recomposer les tags.** Il le ferait, et entre le merge
et le run — une à deux heures, parfois un jour — la couche que `web/` lit
publierait une empreinte thématique tirée d'interventions absentes. Un corpus
committé doit être cohérent à l'instant où il est committé.
