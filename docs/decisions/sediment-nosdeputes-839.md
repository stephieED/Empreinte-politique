<a id="sediment-nosdeputes-839"></a>
# Le sédiment NosDéputés vit dans deux listes, et 492 prises de parole sont publiées deux fois (#839) (2026-09-12)

`2026-09-12`

> **En bref** — deux témoins recollectés à blanc (`jean-luc-melenchon`, `marine-le-pen`) le 12/09/2026 sur `origin/main` (`2299b0e8`), **sans un seul échec d'archive**, donc lisibles : le sédiment existe, il ne vit que dans `interventions[]` et `mandats[]`, et **`votes`, `amendements`, `textes_portes` et `identite` sont propres** (2 324 478 votes en `an:<legislature>:<numero>`, tous les amendements en `an:AMANR…`, 0 champ d'identité différent) ; **511 interventions portent un `intervention_id` entier** — la signature de l'ère NosDéputés, qu'aucune source vivante ne produit — sur **5 profils de candidats déclarés**, et **492 sont le doublon d'une entrée Syceron du même profil** (415 au texte strictement identique), la clé de fusion ayant changé avec la source en #529 ; `marine-le-pen` recollectée rend **1 866 interventions Syceron et 135 questions officielles à l'entrée près, et zéro entier**, ce qui confirme par la collecte ce que le corpus publié disait déjà ; d'où `src/purge_interventions_heritees.py`, **prudent comme #387** — une entrée n'est retirée que si sa jumelle est présente, les **19** sans jumelle restent publiées (Congrès de 2018, réunions de commission, interpellations que Syceron attribue à un orateur collectif ou à un autre député) — et lancé **aux deux couches**, un retrait au seul brut ne descendant jamais au pivot (#729) ; les **406 mandats sans `categorie_source`** relèvent de #718 (« marquer, jamais supprimer ») et de #729, **ce lot n'y touche pas** ; le marqueur `sources[]` reste sur **475 profils dont 470 ne portent plus aucune donnée** de Regards Citoyens, et son retrait est une décision éditoriale à effet juridique, hors de cette issue ; **NosSénateurs tient à 2 profils** et n'est pas touché — les 9 entrées sans source de `bruno-retailleau` **sont** toute sa carrière sénatoriale publiée ; et le protocole du témoin gagne une condition mesurée : **il se collecte en deux passes**, la seconde avec `--enrich-parltrack`, sans quoi tout l'européen manque et le diff est illisible.

## 1. Ce que le témoin devait trancher

L'issue posait deux questions d'une seule mesure : le corpus publié garde-t-il
des entrées qu'aucune version vivante du code ne produit, et les 511
interventions liées à Regards Citoyens sont-elles reproductibles depuis Syceron
aujourd'hui ?

La tentative du 11/09 avait échoué, la collecte tournant pendant un run CI. Les
conditions écrites alors ont été tenues : aucun run en cours, comparaison
limitée aux listes dont aucune archive n'a manqué, un témoin à la fois.

## 2. Le témoin choisi ne portait pas la question

`jean-luc-melenchon` ne porte **aucune** des 511 entrées. Elles sont sur cinq
profils de candidats déclarés : `marine-le-pen` (246), `jerome-guedj` (200),
`edouard-philippe` (50), `gabriel-attal` (10), `bruno-retailleau` (5). D'où un
second témoin, `marine-le-pen`, qui répond aux deux questions à la fois.

## 3. Une condition de protocole que la mesure a révélée

La première collecte rendait `interventions` 5 736 → 3 933, `votes` 2 586 →
1 016, `textes_portes` 37 → 33. **Aucune de ces pertes n'était du sédiment** :
l'enrichissement ParlTrack est une passe séparée du run (`merge-and-pivot`,
seconde passe pivot). Relancée avec `--enrich-parltrack`, elle ramène les trois
listes à l'identique.

**Un témoin se collecte donc en deux passes, comme le run.** Sans cela, le diff
accuse le code d'avoir perdu tout l'européen. Même cause pour `amendements`,
qui demande `--amendements`.

## 4. Ce qui ne se reproduit pas

| Liste | Trace NosDéputés | Reproductible |
| --- | --- | --- |
| `interventions` | **511** entrées à `intervention_id` entier, 5 profils | **492** oui, déjà publiées en double |
| `mandats` | **406** entrées sans `categorie_source`, 45 profils (38 `roster_groupe`, 7 `candidat_declare`) | non — et #718 a tranché : marquer |
| `votes` | aucune — 2 324 478 en `an:<legislature>:<numero>`, 11 013 européens à `scrutin_id` nul | — |
| `amendements` | aucune — tous en `an:AMANR…`, 7 303 non résolus déclarés | — |
| `textes_portes` | aucune — AN ou europarl ; les 85 sans `source_url` sont des rapports de mission AN portant un `dossier_id` | — |
| `identite` | aucune — 0 champ différent entre publié et recollecté, sur les deux témoins | — |

Les tags suivent les interventions : `marine-le-pen` passe de **470 à 152**
tags une fois recollectée, les 318 perdus étant les `mots_cles` de NosDéputés
(« abattement », « africain », « agriculture »). Ils sont dérivés et recalculés
après la fusion (§4) : nettoyer les interventions les nettoie.

## 5. La décision : retirer les doublons, prudemment, aux deux couches

`src/purge_interventions_heritees.py`. Une entrée héritée n'est retirée que
si le profil porte, le **même jour**, une entrée Syceron dont le texte
normalisé contient le sien ou lui est égal — l'inclusion valant dans les deux
sens, le compte rendu définitif rendant d'un bloc ce que NosDéputés coupait.

Mesure identique aux deux couches, `raw_data/profiles` et
`pivot_data/profiles` : **492 retirées sur 4 profils, 19 conservées faute de
jumelle**.

**Limite connue, et assumée** : 204 des 492 jumelages portent sur un texte de
trois mots ou moins (« C'est vrai ! »). Si la même personne a prononcé deux
fois la même interjection le même jour, le rapprochement en confond les
occurrences. L'entrée retirée reste celle dont aucune source primaire ne porte
l'identifiant.

## 6. Les 19 sans jumelle

| Cas | Entrées | Ce qu'en dit la source primaire |
| --- | ---: | --- |
| Congrès du 09/07/2018 (`bruno-retailleau`) | 5 | hors Syceron : ce n'est pas une séance de l'Assemblée |
| Réunions de commission (`jerome-guedj`) | 3 | hors Syceron : séance publique seulement |
| Interpellations en séance publique | 11 | sur 4 vérifiées : orateur collectif (« MM. Olivier Faure et Jérôme Guedj »), attribution à un autre député (« Le bureau aussi ! », à Sébastien Chenu), ou rédaction définitive différente |

Elles restent publiées. Leur sort est un arbitrage éditorial, pas du ménage.

## 7. Ce que ce lot ne fait pas

- **Les 406 mandats sans `categorie_source`** : #718 a tranché le 03/09 —
  marquer, jamais supprimer ni accuser, parce qu'une part d'entre eux sont des
  mandats réels que l'AN nomme autrement et qu'un faux positif est
  irréversible. Les doublons démontrés relèvent de #729, ouverte.
- **Le marqueur `sources[]`** : 475 profils le portent, dont **470 sans aucune
  donnée** de Regards Citoyens. Le retirer fait tomber la clause ODbL (§7) :
  décision éditoriale à effet juridique, hors de cette issue.
- **NosSénateurs** : 2 profils, `bruno-retailleau` et `jean-luc-melenchon`, 33
  mandats sans source. Les 9 entrées de Retailleau sont toute sa carrière
  sénatoriale publiée — les retirer viderait sa fiche sans que rien ne les
  remplace. Position de la propriétaire le 12/09/2026 : on n'y touche pas tant
  qu'une alternative n'a pas été creusée ; le Sénat étant hors périmètre
  (#528), la seule connue est une table relue à la main sur sources primaires,
  comme `raw_data/mandats_anterieurs.json` (#860).

## 8. L'alternative écartée

**Un dépôt sœur et une recollecte complète du corpus**, envisagés par l'issue.
Deux témoins ont suffi à trancher, pour quelques minutes de collecte chacun :
le diff d'un run à blanc complet aurait mêlé le sédiment, les entrées qu'une
source n'a pas rendues ce jour-là et les données qui ont légitimement changé,
et il aurait fallu construire l'infrastructure avant de savoir s'il y avait
quelque chose à chercher.

**Détecter le sédiment par la collecte, à chaque fois.** Les deux signatures
trouvées se comptent sur le corpus publié, **sans réseau** : un
`intervention_id` entier, un mandat sans `categorie_source`. La collecte a
servi à les établir, pas à les compter.

## 9. Ce que le prochain run devra déclarer

`interventions` est une liste stable : le contrôle de perte bloquera. La perte
est voulue et nommée d'avance — 492 entrées, 4 profils — et se déclare par
`allow_declared_losses` après comparaison au rapport de la purge.
