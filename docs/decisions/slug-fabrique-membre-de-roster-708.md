<a id="slug-fabrique-membre-de-roster-708"></a>
# Un membre de roster sans correspondance relue reçoit un slug, et la collision reste un refus (#708) (2026-09-02)

`2026-09-02`

> **En bref** — `build_roster_candidats_detaille` laisse tomber un membre sans slug **depuis toujours**, et c'était inoffensif tant que NosDéputés servait le roster avec ses slugs ; #527 a basculé la source sur AMO30, qui ne publie qu'un `PA######`, et l'exclusion est devenue **muette** — la cause n'était pas une table incomplète mais une **circularité**, `raw_data/correspondance_acteurs_an.json` étant construite depuis les profils **publiés** : pour avoir un profil il fallait un slug, pour avoir un slug il fallait un profil, et la table était donc **fermée**, ce que la mesure montre en creux (les **304 / 304** membres de la XVIIe qu'elle couvre avaient tous déjà siégé avant la XVIIe) ; `an_roster.resoudre_slugs` ouvre **une** porte — `text_utils.slugify(état civil AMO30)`, la seule fabrique de slugs du dépôt — avec la **table devant, sans exception**, ce qui est la garantie de #487/#668 (un changement de **nom d'usage** ne déplace pas l'identifiant d'une personne déjà collectée, et 4 des 10 écarts de #525 en sont) et sur l'index GP **entier**, jamais les groupes configurés ; trois motifs fermés refusent tout slug (`nom_absent`, `slug_deja_publie` — le slug visé appartient à **quelqu'un d'autre**, `hors_an` compris —, `homonymie_amo30`), le même slug porté par la **même** personne n'étant structurellement pas une collision puisque la table est lue d'abord ; **`ROSTER_SANS_SLUG` change de sens sans devenir faux** — il compte désormais ce qui reste *réellement* écarté et non un état que personne ne pouvait quitter : **0** sur les **1 662 acteurs de l'index GP sans entrée de table** (dont les 160 des 10 groupes configurés), une mesure du corpus et non une propriété du code —, et son miroir `ROSTER_SLUG_FABRIQUE` (en `notice`) nomme qui entre par une porte que personne n'a relue ; **fabriquer le slug d'un membre neuf n'est pas combler une entrée relue** (#525 §6 refuse de réécrire une preuve relue ; ici il n'y a **rien** à contredire) et la distinction tient parce que la **§5b du portail échoue en dur, seuil 0**, sur tout profil publié sans entrée : un slug fabriqué sert à *collecter*, jamais à *publier* ; **la condition de retrait de la table (#525 §7) est inchangée** — ce lot contourne son absence à l'entrée d'un membre nouveau, il ne la rend pas facultative ; **le coût est mesuré et non extrapolé** : les profils bruts étant partitionnés par législature (#580), un primo-député de 2024 pèse socle + une tranche = **6,8 Mio** en médiane (8,7 en moyenne) et non les 11,8 Mio de la médiane du corpus entier, donc **1,07 Gio** (médianes) à **1,44 Gio** (moyennes) pour les 156 entrants — **1,7 à 2,3 fois moins** que les « +1,8 à +2,5 Gio » qui circulaient (145 ne siègent qu'en XVIIe, 11 ont siégé avant, dont 3 en XIIe/XIIIe que le corpus ne couvre pas : borne déclarée) ; six mutations vérifiées échouantes (fabrication, règle de collision, priorité de la table, les deux compteurs, `slug_origine` à travers `filter_roster_by_sigle`) ; **aucun run n'a été lancé** — les 156 profils n'existent pas, et la couverture des 5 fiches de la XVIIe (305 / 461, `AN:SOC:17` à 41,4 %, #700) ne remonte que le jour où ils sont collectés **et** leur correspondance relue.

## 1. Le défaut : une exclusion qui n'a pas de date d'apparition, seulement une date de bascule

`build_roster_candidats_detaille` laisse tomber un membre sans slug **depuis
toujours** — `src/generate_roster_candidats.py` l'écrit lui-même, et ce n'était
pas un oubli : tant que NosDéputés servait le roster, il n'existait pas de
membre sans slug, puisque le slug **était** l'identifiant de la source.

Ce qui a changé, c'est la source. #527 a basculé la composition des groupes AN
sur AMO30, qui ne publie qu'un `PA######` et de l'état civil. À partir de ce
jour, la ligne inoffensive est devenue une **exclusion silencieuse** : un
membre qu'aucune correspondance ne couvre entre dans le roster brut et en
ressort sans être collecté.

#527 avait posé le compteur qu'il fallait (`ROSTER_SANS_SLUG`, « comptés et
nommés, jamais absents sans un mot »), et le compteur a fait son travail : 4
écarts sur la XVIe, puis **156 des 461 entrées des 5 rosters de la XVIIe**,
33,8 %. Mais **compter n'est pas ouvrir la porte** : personne ne pouvait entrer,
et le compteur ne le disait pas non plus, parce qu'il nommait un symptôme
(« pas d'entrée dans la table ») sans nommer la cause.

## 2. La cause : une circularité, pas une table incomplète

Le slug se résolvait par `raw_data/correspondance_acteurs_an.json` (#525), lue
à l'envers (`acteur_ref → slug`). Or cette table est **construite depuis les
profils publiés** (`build_correspondance_acteurs_an._slugs_publies`).

> Pour avoir un profil il fallait un slug ; pour avoir un slug il fallait un
> profil.

La table n'était donc pas « en retard » : elle était **fermée**. Aucun run,
aucune relecture, aucune régénération ne pouvait y faire entrer quelqu'un que
le dépôt n'avait jamais collecté. C'est ce qui explique la forme de la mesure :
les 304 membres de la XVIIe déjà couverts par la table sont, **sans
exception**, des députés qui avaient déjà siégé avant la XVIIe (mesuré le
02/09/2026 : 304 / 304). Les 145 primo-députés de 2024 n'ont pas d'analogue
publié — ils n'ont jamais pu en avoir un.

## 3. La décision : `an_roster.resoudre_slugs`, une porte et une seule

Un acteur AMO30 **sans entrée de table** reçoit `slugify(état civil AMO30)` —
`text_utils.slugify`, **la fonction qui fabrique déjà tous les autres slugs du
dépôt**. Il n'y a pas de seconde fabrique, et un test l'exige : deux fabriques
dériveraient le jour où l'une des deux est corrigée.

Quatre propriétés, aucune décorative.

**La table passe devant, sans exception.** Dès qu'un acteur y a une entrée, son
slug en vient, quoi que dise l'état civil du jour. C'est la garantie de
stabilité : un changement de **nom d'usage** ne déplace pas l'identifiant d'une
personne déjà collectée — le piège de #487 (un `id` qui changeait de valeur sur
une carrière inchangée) et de #668 (une clé `a or b` qui change de branche le
jour où `a` se remplit). #525 §7 mesure que **4 des 10 écarts de la table sont
des noms d'usage**, c'est-à-dire des valeurs qui bougent : la priorité de la
table n'est pas une politesse envers un fichier relu, c'est ce qui empêche
`audit_diff_profils` de lire un renommage comme une **disparition** (#460/#470).

**Trois cas ne reçoivent jamais de slug fabriqué** (`MOTIFS_SLUG_NON_ATTRIBUE`,
vocabulaire fermé au patron des `KNOWN_*`) :

| motif | ce qui est refusé |
| --- | --- |
| `nom_absent` | AMO30 ne rend aucun état civil slugifiable |
| `slug_deja_publie` | le slug visé appartient à **quelqu'un d'autre** dans la table (`acteur_ref` différent, ou `hors_an` déclaré) |
| `homonymie_amo30` | deux acteurs AMO30 **sans entrée** visent le même slug |

C'est la règle de #525 §5, celle de « une deuxième *Alexandra Martin* élue » :
attribuer en silence, ce serait écrire les votes d'une personne dans le profil
d'une autre — la clé collante de #540, sur le seul identifiant que le dépôt
possède. Ces trois-là se tranchent à la main dans la table, comme les 10
résidus de #525. **Le même slug porté par la même personne n'est pas une
collision** : la table étant consultée avant, ce cas ne peut structurellement
pas se produire — et un test le verrouille, parce qu'inverser l'ordre
écarterait d'un coup tous les membres déjà publiés, avec un motif pointant sur
eux-mêmes.

**L'univers de résolution est l'index GP entier, jamais les groupes demandés.**
Un identifiant dont la valeur dépendrait de `raw_data/groupes_reels.json`
changerait le jour où la config change.

**Les deux compteurs se lisent ensemble, et aucun n'est redondant.**
`membres_slug_fabrique` (annotation `ROSTER_SLUG_FABRIQUE`, en `notice`) dit
**qui entre par une porte que personne n'a relue** ; `membres_sans_slug`
(`ROSTER_SANS_SLUG`, en `warning`) dit **qui reste dehors et pourquoi**.

## 4. `ROSTER_SANS_SLUG` change de sens sans devenir faux

C'est le point que ce lot pouvait rater. Une fabrication **sans** contrôle de
collision aurait ramené ce compteur à zéro **par construction** : ce n'est pas
satisfaire le compteur de #527, c'est le supprimer en le laissant en place.

Depuis #708 il ne compte plus « pas d'entrée dans la table » — un état que
personne ne pouvait quitter — mais **ce qui n'a pas pu être attribué**. Mesuré
le 02/09/2026 sur les **1 662 acteurs de l'index GP sans entrée de table**
(dont les 160 des 10 groupes configurés) : **0**. Ce zéro est une mesure du
corpus, pas une propriété du code : le jour où deux homonymes sont élus sans
que l'AN les désambiguïse, il vaut 2 et l'annotation les nomme. Un test le
vérifie sur une table de collision montée en `tmp_path`, et le portail
n'en fait pas un blocage — une collision se relit, elle n'arrête pas un run.

## 5. Fabriquer le slug d'un membre neuf n'est pas combler une entrée relue

#525 §6 interdit une chose précise : `build_correspondance_acteurs_an.py` **ne
comble pas** une correspondance depuis `identite.source_url`, alors même que ce
champ porte souvent le bon `PA######`. Ce refus tient, et ce lot n'y touche pas.

La distinction n'est pas de degré, elle est de nature :

| | #525 §6, interdit | #708, fait ici |
| --- | --- | --- |
| Objet | une entrée **existante**, relue et prouvée | un acteur qui n'a **aucune** entrée |
| Ce qui serait écrasé | une preuve relue à la main | rien |
| Ce qu'on produit | une correspondance sans preuve, présentée comme relue | un identifiant de travail, **déclaré** comme fabriqué |
| Durée de vie | définitive, invisible | jusqu'à la relecture, que la §5b du portail **exige** |

Le dernier point est ce qui rend la distinction défendable plutôt que
rhétorique : **§5b de `check_quality_gate.py` échoue en dur, seuil 0, sur tout
profil publié sans entrée de table** (#525). Un slug fabriqué ne peut donc pas
être *publié* — il ne peut que servir à *collecter*, dans la fenêtre d'un run
non commité, et c'est précisément la fenêtre où la table n'a pas encore pu être
écrite. Le slug est alors gelé dans la table par la relecture, et la priorité
du §3 le rend immuable ensuite.

## 6. La condition de retrait de la table est **inchangée**

#525 §7 la dit : la table disparaît le jour où **la source publie elle-même la
correspondance** — un identifiant stable et externe dans AMO30 (slug
NosDéputés, `uri_hatvp` systématique, identifiant Wikidata).

**Ce lot ne remplit pas cette condition et ne l'assouplit pas.** Il ne rend pas
la table facultative : il contourne son absence **à l'entrée d'un membre
nouveau**, et laisse intacte l'obligation d'y avoir une entrée relue avant
publication. Sans cette phrase écrite, la table deviendrait facultative par
accident — exactement la façon dont les replis de lecture de #431 et #432 sont
devenus permanents.

## 7. Ce que ça coûte, mesuré et non extrapolé

L'estimation qui circulait — « +1,8 à +2,5 Gio » (ligne d'index de #700, via
#691) — était l'extrapolation de la **médiane du corpus entier** (11,8 Mio sur
481 profils) sur 156 personnes. Elle mesure la mauvaise population : un député
élu en 2024 ne porte pas le volume d'un député en poste depuis 2012.

Les profils bruts étant partitionnés par législature (#580, un socle plus une
tranche `<leg>.json`), le coût d'une mandature courte se **mesure** au lieu de
se déduire. Mesuré le 02/09/2026 sur `raw_data/profiles/` (481 slugs, 7,70 Gio) :

| population | n | médiane | moyenne |
| --- | ---: | ---: | ---: |
| socle `<slug>.json` | 481 | 1,5 Mio | 1,8 Mio |
| tranche `17.json` | 316 | 5,2 Mio | 7,2 Mio |
| profil complet, membre XVIIe déjà publié | 304 | 19,6 Mio | 20,9 Mio |

Les 156 entrants se répartissent en **145 qui ne siègent qu'en XVIIe** — socle
+ une tranche, **6,8 Mio** en médiane, 8,7 en moyenne — et **11 qui ont siégé
avant**, jusqu'à 15,1 Mio pour celui qui couvre XVe, XVIe et XVIIe. Projection
sur les empreintes réelles : **1,07 Gio** sur les médianes, **1,44 Gio** sur les
moyennes — **1,7 à 2,3 fois moins** que le chiffre qui circulait. Le garde-fou
de #580 (80 Mio **par fichier**) n'est pas approché : la plus grosse tranche
`17.json` du corpus pèse 22,9 Mio.

Deux bornes de la projection sont **déclarées et non mesurées** : 3 des 11 ont
un mandat de groupe en XIIe ou XIIIe, législatures que le corpus ne couvre pas
(plancher à la XIVe, 47 tranches) — leur coût réel est donc supérieur au
chiffre ci-dessus ; et la tranche `14.json` n'est mesurée que sur 47 profils.

## 8. L'alternative écartée

**Attribuer le slug le plus proche en cas de collision** — suffixer, préférer
l'`acteur_ref` le plus petit, préférer le mandat le plus récent. Écartée : un
identifiant tiré au sort est pire qu'un identifiant absent (§2 règle 5), et le
gagnant changerait le jour où l'AN attribue un `PA######` plus petit. Le slug
est le **nom du fichier publié** : le déplacer, c'est publier deux fois la même
personne, ou perdre la première.

**Élargir `build_correspondance_acteurs_an.py` pour qu'il propose une entrée
par membre de roster.** Écartée pour ce lot, mais ce n'est pas un refus de
principe : c'est le geste qui *ferme* la boucle, et il suppose de décider ce
qui tient lieu de **preuve** pour quelqu'un dont aucun profil n'existe. Tant
qu'il n'est pas fait, la §5b bloque la publication et l'annotation
`ROSTER_SLUG_FABRIQUE` nomme la file d'attente.

## 9. Ce qui n'est pas vérifié

Aucun run n'a été lancé : les 156 profils bruts n'existent pas, et la
projection du §7 est un calcul sur des tranches mesurées, pas une collecte
observée. La **couverture** des 5 fiches de la XVIIe — 305 / 461 aujourd'hui,
`AN:SOC:17` à 41,4 % (#700) — ne remonte que le jour où ces profils sont
collectés **et** leur correspondance relue : ce lot lève le premier verrou, pas
le second.
