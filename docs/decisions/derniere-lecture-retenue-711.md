<a id="derniere-lecture-retenue-711"></a>

# La règle « dernière lecture » d'AGENTS.md §6 est implémentée, et c'est la DATE qui ordonne (#711) (2026-09-02)

`2026-09-02`

> **En bref** — `AGENTS.md` §6 la publie depuis l'origine, le `DESIGN_SYSTEM` §6 la cite comme la voix de la maison et la page de méthodologie l'annonçait **au lecteur** ; **aucun code ne l'appliquait** — `isWholeTextVote` (#672) sélectionnait les votes sur l'ensemble d'un texte et s'arrêtait là. Mesuré au commit de données `f635cb60` sur les 17 748 scrutins publiés : **925** votes sur l'ensemble d'un texte, **697** textes une fois les lectures repliées, 187 textes votés plusieurs fois, donc **228 scrutins (24,6 %)** comptaient une lecture déjà comptée. Sur les **13 profils `candidat_declare`**, `gabriel-attal` passe de 150 votes à **111 textes** et de « 140 pour · 7 contre · 3 abstentions » à **« 103 · 6 · 2 »** — et ce qui disparaît **retire une affirmation fausse** : son « contre » de première lecture du 17/06/2025 sur le projet de loi de simplification de la vie économique, qu'il avait déposé comme Premier ministre, alors que la loi a été adoptée sur le **texte de la CMP** le 14/04/2026, scrutin où aucune position de lui n'est enregistrée (dire pourquoi il y manque publierait une absence individuelle, §2 règle 3). **Le regroupement par libellé est permis** parce que `regrouper-nest-pas-joindre-639` l'autorise **au sein d'une même source** et surtout parce que son **mode d'échec est sûr** — un intitulé mal replié *échoue à regrouper*, il ne rapproche jamais à tort, l'inverse exact de `texte_vise` (#696) où un appariement par libellé aurait **fusionné** des textes distincts. **La date ordonne, jamais le rang** : le rang n'est pas un champ, il n'existe que dans l'intitulé et il y manque **51 fois sur 925**, et **4 groupes** mettent les deux ordres en contradiction (le PLFR 2017 porte deux « première lecture » encadrant une « lecture définitive »). Le vocabulaire des mentions, **dupliqué et incomplet des deux côtés** (`lecture.js` et `utils/groupe.js`), est écrit une seule fois et les deux ancrages s'en déduisent : le cadrage en nommait 8, la mesure en trouve **16** dont **4 coquilles de la source**, **874 / 925** sont repliés et **51** ne le sont pas (49 sans parenthèse finale, 2 en `(art. 34-1 de la Constitution)`) ; les ordinaux **en chiffres** exigent le mot « lecture » derrière eux, sans quoi le `(2ème vote)` de `an:14:1086` souderait un scrutin annulé à son remplaçant, et le `(2)` du PLFR 2020 (2) distingue **deux textes**. Les **51 sans mention ne deviennent pas des premières lectures** (§2 règle 5) : ils gardent leur titre nu, qui *est* la clé, et 14 rejoignent ainsi un groupe — `an:14:594`, dernière lecture de la transparence de la vie publique, n'en porte aucune. La clé porte la **législature** : sans elle **10 groupes** souderaient deux textes homonymes de deux législatures, et compter deux fois est un manque quand souder serait une affirmation. **La dernière lecture se lit sur le CORPUS**, pas sur les votes de la personne — 120 textes contre 111 sur `gabriel-attal` — et un corpus absent se **déclare** (`derniereLectureDisponible`) au lieu de retomber sur une règle de repli muette (#510). **Ce qui reste faux est mesuré** : 9 groupes, **20 scrutins des 925, borne haute**, portent deux fois la même mention à des dates différentes dans une même législature — le sens de l'erreur reste le bon, le scrutin retenu est toujours un scrutin réel de la personne, ce qui se perd est un texte et jamais une position attribuée à tort. `audit_diff_profils` ne voit rien et **c'est correct** : aucun fichier de `pivot_data/` n'est touché, les 925 positions restent publiées et ce qui baisse est un **dénominateur affiché**, ni scalaire surveillé ni liste stable. Ni collecte ajoutée, ni rattachement au dossier rouvert ; `ecartsAvecLeGroupe` et `grandesLois` sont **volontairement** laissés non repliés. 36 tests, **12 mutations vérifiées échouantes**, dont deux fixtures renforcées après avoir passé au vert sur un module amputé.

## Le contexte

`AGENTS.md` §6 publie, depuis l'origine de la table : « `votes[]` vote sur le
texte (`vote_texte`, **dernière lecture**) — Public ». Le
`web/UI_finale/DESIGN_SYSTEM.md` §6 la cite comme exemple de la voix de la
maison : *« "Lecture la plus avancée retenue pour chaque texte", pas "votes
comptés" »*. Et la page de méthodologie l'annonçait **au lecteur** :
« Pour un même texte, seule la lecture la plus avancée connue est conservée
dans la synthèse. »

**Aucun code ne l'implémentait.** `web/UI_finale/src/utils/lecture.js`
sélectionnait les votes portant sur l'ensemble d'un texte (`isWholeTextVote`,
#672) et s'arrêtait là.

Mesuré le 02/09/2026 au commit de données `f635cb60`, sur les 17 748 scrutins
publiés de `pivot_data/scrutins.json` :

| Mesure | Valeur |
| --- | ---: |
| Scrutins « sur l'ensemble d'un texte » (`isWholeTextVote`) | **925** |
| Textes distincts, lectures repliées | **697** |
| Textes votés plusieurs fois | 187 |
| **Scrutins comptant une lecture déjà comptée** | **228 — 24,6 %** |

Un quart des votes affichés étaient des relectures du même texte.

## Ce que ça retire, mesuré

Sur les **13 profils `candidat_declare`** (les 468 `roster_groupe` ne sont pas
une page) :

| slug | positions publiées | dont sur l'ensemble d'un texte | textes après repli |
| --- | ---: | ---: | ---: |
| `jerome-guedj` | 2 906 | 221 | **168** |
| `marine-le-pen` | 1 813 | 215 | **132** |
| `jean-luc-melenchon` | 1 016 | 165 | **101** |
| `laurent-wauquiez` | 826 | 160 | **124** |
| `gabriel-attal` | 2 035 | 150 | **111** |
| `edouard-philippe` | 141 | 94 | **74** |
| `xavier-bertrand` | 123 | 75 | **59** |
| les 6 autres | 0 | 0 | 0 |

Sur `gabriel-attal`, « 140 pour · 7 contre · 3 abstentions » devient
« **103 · 6 · 2** ».

**Le « contre » qui disparaît est le point de la règle.** Le *projet de loi de
simplification de la vie économique*, qu'il avait déposé comme Premier ministre
le 24/04/2024 : il a voté **contre en première lecture** le 17/06/2025
(`an:17:2458`), mais la loi a été adoptée sur le **texte de la commission mixte
paritaire** le 14/04/2026 (`an:17:6184`), scrutin où **aucune position de lui
n'est enregistrée**. Publier son « contre » comme sa position sur cette loi
aurait été **faux** — et dire pourquoi il manque au scrutin final publierait une
absence individuelle, que §2 règle 3 interdit. Le texte n'est donc pas affiché.

## La décision

**Le regroupement par texte et la sélection de la dernière lecture vivent dans
`web/UI_finale/src/utils/lecture.js`, au même endroit qu'`isWholeTextVote`** —
`cleDuTexteVote`, `grouperLecturesParTexte`, `derniereLecture`,
`selectDerniereLectureVotes`. Le regroupement **part** de
`selectWholeTextVotes` : il n'existe pas de seconde définition de « vote sur
l'ensemble d'un texte », c'est la contrainte que #672 a posée.

### Pourquoi le regroupement par libellé est permis ici

[`regrouper-nest-pas-joindre-639`](regrouper-nest-pas-joindre-639.md) autorise à
**regrouper** des faits d'une **même source** par leur propre libellé — les 925
intitulés viennent tous des scrutins de l'Assemblée — et interdit de **joindre**
deux sources par ressemblance de libellé.

**Et le mode d'échec est sûr : un intitulé mal replié ÉCHOUE À REGROUPER, il ne
rapproche jamais à tort.** Deux lectures restent alors comptées séparément,
c'est-à-dire l'état d'avant ce lot. C'est l'inverse exact de `texte_vise`
(#696), où un appariement par libellé aurait **fusionné** des textes distincts.
C'est cet argument, et lui seul, qui sépare ce lot de ce que #672 et #639 ont
interdit.

### La DATE ordonne, jamais le rang

Le rang de lecture **n'est pas un champ** : la projection de scrutin porte
`date`, `legislature`, `numero_scrutin`, `sort`, `texte`, `type_scrutin`,
`type_vote`, `demandeur` (#639). Le rang n'existe que **dans l'intitulé**, et il
y manque 51 fois sur 925. Le repli sert à **grouper** ; la date **ordonne**.

Et l'ordre par rang serait **faux** là où les deux divergent — **4 groupes**
mesurés, tous des textes budgétaires dont l'Assemblée réemploie le titre :

| Texte | Scrutins, par date |
| --- | --- |
| PLFR pour 2017 | 06/11 *(1ʳᵉ)* · 14/11 *(définitive)* · **12/12 *(1ʳᵉ)*** |
| PLFR pour 2020 | 19/03 *(1ʳᵉ)* · 23/07 *(CMP)* · **10/11 *(1ʳᵉ)*** |
| PL de règlement du budget | 13/07/22 · 27/07/22 · 03/08/22 *(définitive)* · **05/06/23 *(1ʳᵉ)*** |
| PL spéciale (art. 45 LOLF) | 16/12/24 *(1ʳᵉ)* · **23/12/25 *(1ʳᵉ)*** |

Un tri par rang retiendrait la lecture définitive ou la CMP, qui ne sont pas les
plus récentes.

### Le vocabulaire des mentions, mesuré, et écrit une seule fois

Distribution des mentions finales sur les 925 :

| Mention | Scrutins | | Mention | Scrutins |
| --- | ---: | --- | --- | ---: |
| première lecture | 546 | | 2e lecture | 2 |
| texte de la commission mixte paritaire | 158 | | troisième lecture | 2 |
| lecture définitive | 54 | | 1re lecture | 1 |
| **(aucune mention)** | **51** | | texte cmp | 1 |
| deuxième lecture | 48 | | premiere lecture | 1 |
| nouvelle lecture | 46 | | *commisison mixte paritaire* | 1 |
| texte de la commission paritaire | 8 | | *commisson mixte pariraire* | 1 |
| 1ère lecture | 3 | | *lecture défintive* · *défnitive* | 1 · 1 |

Le cadrage de l'issue en nommait **8** ; la mesure en trouve **16**, dont
**quatre coquilles de la source** — et elle compte **51** intitulés sans
mention, non 53 : **49** sans aucune parenthèse finale, **2** dont la parenthèse
finale n'est pas une lecture (voir plus bas). Après repli, **874 / 925** sont
repliés et **51** ne le sont pas ; ce compte est **mesuré**, pas supposé.

Le vocabulaire vivait **dupliqué** : `MENTION_DE_LECTURE` dans `lecture.js` et
`MENTION_LECTURE` dans `utils/groupe.js`, tous deux incomplets. Il est désormais
écrit une fois (`MENTIONS_DE_LECTURE`), et **les deux ancrages s'en déduisent** :
`MENTION_DE_LECTURE` (en fin d'intitulé, pour nommer et pour regrouper) et
`MENTION_DE_LECTURE_PARTOUT` (n'importe où, ce dont `designationDuTexte` a
besoin : **547** scrutins portent du texte **après** la parenthèse). Effet
mesuré du vocabulaire élargi sur la fiche de groupe : **60 des 17 748** scrutins
changent de désignation, **1 283 → 1 271** désignations distinctes — que des
fusions de `(1ère lecture)` / `(2ème lecture)`.

### Les 51 intitulés sans mention ne deviennent pas des premières lectures

Ils gardent leur **titre nu**, qui est justement la clé de regroupement — **14
d'entre eux** rejoignent ainsi un groupe portant d'autres lectures. Aucun rang
ne leur est attribué (§2 règle 5), et c'est la date qui les ordonne. Le cas
`an:14:594` le montre : la dernière lecture du *projet de loi relatif à la
transparence de la vie publique* (17/09/2013) **ne porte aucune mention**, là où
une table de rangs aurait retenu la « nouvelle lecture » du 23/07/2013.

### Ce qui n'est PAS une mention, et ne doit jamais être retiré

- **`(article 34-1 de la Constitution)`** et **`(art. 34-1 de la Constitution)`**
  — 1 scrutin chacun : une résolution de l'article 34-1 n'a pas de lecture.
- **`(2)`** du *projet de loi de finances rectificative pour 2020 (2)* : la
  parenthèse distingue **deux textes**, pas deux lectures.
- **`(2ème vote)`** de `an:14:1086`, le scrutin qui **remplace** le scrutin
  annulé `an:14:1085`.

D'où la forme de la liste : les ordinaux **en chiffres** exigent le mot
« lecture » derrière eux. Les ordinaux **en lettres** restent nus, comme avant
ce lot — c'est ce qui retire `(seconde délibération)`, et le changer déplacerait
547 désignations de fiche de groupe pour une raison étrangère à ce lot.

### La clé porte la LÉGISLATURE

Sans elle, **10 groupes** souderaient deux textes homonymes votés dans deux
législatures différentes (« projet de loi relatif à la protection des enfants »,
XVe puis XVIIe). Un texte réellement repris après une dissolution reste donc
compté deux fois : **c'est un manque, pas une affirmation**. La clé portant la
législature, le `numero_scrutin` redevient un ordinal valide pour départager un
ex aequo de date — il repart à 1 à chaque législature (§5) — et **un seul groupe
des 697** en a besoin (`an:15:2769` / `an:15:2770`, 25/06/2020).

### La dernière lecture se lit sur le CORPUS, pas sur les votes de la personne

`votesDuProfil` reçoit `scrutinsIndex` depuis `pivotAdapter`. Mesuré sur
`gabriel-attal` : ordonner **ses propres** lectures rend **120** textes,
ordonner celles du **corpus** en rend **111**. Les 9 d'écart sont des textes dont
il a voté une lecture antérieure et **pas** la dernière — dont la loi de
simplification. Sans le corpus, la règle publiée n'est pas celle qui s'applique.

**Corpus absent ⇒ la fonction le déclare** (`derniereLectureDisponible`) et la
vue affiche une liste vide de cause `non_collecte`. Elle ne retombe **pas** sur
les seuls votes de la personne : une règle de repli qui remplace silencieusement
la règle publiée est ce qui a rendu #510 invisible.

### Le libellé affiché dit la règle

`LAST_READING_LABEL` (« dernière lecture retenue pour chaque texte ») accompagne
le **chiffre** ; `LAST_READING_RULE` (`phrase` + `pourquoi`, patron de
`WHOLE_TEXT_VOTE_BOUND`) est publié sur la fiche candidat **et** dans la
méthodologie. Un compteur qui replie sans le dire ment par omission
(`DESIGN_SYSTEM` §6 : chaque métrique porte sa propre limite). Le décompte
publie ses deux dénominateurs : « *N* textes — dernière lecture retenue pour
chaque texte » puis « tirés de *M* votes sur l'ensemble d'un texte, parmi *T*
positions » (§2 règle 7).

## Ce qui reste faux, mesuré et non corrigé

**9 groupes — 20 scrutins des 925, borne HAUTE** — portent **deux fois la même
mention de lecture à des dates différentes dans une même législature** : deux
collectifs budgétaires d'une même année, deux lois spéciales, deux prorogations
de l'état d'urgence. Certains sont **légitimes** (un intitulé qui omet sa mention
deux fois de suite : `an:14:536` / `an:14:594` sur la transparence de la vie
publique), les autres soudent deux textes distincts.

**Le sens de l'erreur reste le bon.** Le scrutin retenu est toujours un scrutin
**réel** de la personne, jamais un vote inventé : ce qui se perd est un texte,
jamais une position attribuée à tort. C'est pourquoi aucun garde-fou n'est ajouté
ici — une règle qui refuserait de replier sur « deux mentions identiques »
casserait les 3 groupes légitimes pour revenir à l'état d'avant ce lot, et le
critère est le plus faible là où les deux mentions sont absentes.

## Ce que ce lot ne fait pas

- **Il ne rouvre pas le rattachement d'un scrutin à son dossier législatif** :
  instruit et écarté, 81,8 % des scrutins sans rattachement sourcé
  ([`rattachement-au-dossier-interventions-et-scrutins-639`](rattachement-au-dossier-interventions-et-scrutins-639.md)).
- **Il n'ajoute aucune collecte.** Le rang de lecture depuis l'open data AN est
  hors périmètre, à instruire séparément **si** le repli par intitulé se révèle
  insuffisant.
- **Il ne touche pas `ecartsAvecLeGroupe`.** Les écarts sont publiés **scrutin
  par scrutin**, datés, sourcés et jamais totalisés (§2 règle 7) : une
  divergence en première lecture est un fait sur **ce scrutin**, pas une
  affirmation sur la loi. Les replier retirerait des faits sourcés sans rien
  corriger.
- **Il ne touche pas `grandesLois`** (fiche de groupe), qui existe précisément
  pour montrer **le mouvement d'une lecture à l'autre** et les affiche toutes,
  nommées. Seul son vocabulaire de mentions cesse d'être une copie divergente.

## Le contrôle de perte

`audit_diff_profils` ne voit rien, et **c'est correct** : ce lot ne touche
**aucun fichier de `pivot_data/`**. Le repli est une **règle d'affichage** — les
925 positions restent publiées dans `votes[]`, et le contrôle de perte porte sur
le corpus, pas sur ce que la vue en montre. Ce que la baisse concerne est un
**dénominateur affiché**, qui n'existe nulle part sur disque et n'est donc ni un
scalaire surveillé (#649) ni une liste stable.

## L'alternative écartée

**Ordonner les lectures de la personne plutôt que celles du corpus.** Moins
coûteux (aucun paramètre à passer) et sans risque de « texte qui disparaît ».
Écarté parce qu'il conserve exactement l'affirmation fausse que ce lot existe
pour retirer : le « contre » de première lecture de Gabriel Attal serait publié
comme sa position sur une loi adoptée sur un texte de CMP qu'il n'a pas voté.
Mesuré : 120 textes au lieu de 111 sur ce profil.

## Vérification

`tests/test_derniere_lecture_711.py` — 36 tests, sur le patron de
`tests/test_selection_vote_ensemble_672.py` : lecture du **code exécuté**
(commentaires retirés) et **rejeu en Python des motifs extraits du fichier JS**,
chaque étape n'étant appliquée que si le corps JS l'applique. Le dépôt n'a pas de
runner JS (`oxlint` seul).

**Douze mutations vérifiées échouantes** le 02/09/2026 : repli neutralisé (4),
première lecture au lieu de la dernière (5), législature retirée de la clé,
garde « lecture sans date » retirée, exception « une seule lecture » retirée,
tri par numéro retiré, ordinaux en chiffres n'exigeant plus « lecture »,
ancrage en fin retiré, normalisation retirée, vocabulaire ramené à celui d'avant
ce lot (4), corpus remplacé par les votes de la personne, corpus retiré de la
signature. Deux fixtures ont dû être **renforcées** parce qu'elles passaient au
vert sur un module amputé : l'ex aequo est écrit dans l'ordre inverse de l'ordre
attendu (un tri stable sans départage rendait la bonne réponse par hasard), et la
paire d'apostrophes porte la typographique **à l'intérieur du titre**, `l'ensemble`
étant déjà accepté sous les deux formes par `OUVERTURE_VOTE_ENSEMBLE`.

**Ce qui n'est pas mesurable ici** : aucun des 925 scrutins ne porte de mention
ailleurs qu'en fin d'intitulé, et aucun n'a de `date` ou de `legislature`
absente. L'ancrage en fin et la garde « lecture sans date » sont donc des gardes
dont l'effet n'est **pas** observable sur la population que ce lot replie — 432
des 17 748 publiés ont une mention non finale, tous des votes sur un article ou
un amendement qu'`isWholeTextVote` écarte. Elles sont testées pour cela, plutôt
que supposées.
