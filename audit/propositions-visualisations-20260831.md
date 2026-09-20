# Propositions de visualisations — ce qu'un citoyen doit comprendre, et en combien de temps

**Issue #594** — temps 2/4 de l'épic #324, débloqué par la revue #593
(`audit/revue-ui-20260829.md`). Brainstorming des 30 et 31/08/2026, mesures sur
`pivot_data/` à `e6af1a00`.

> **Ce document part des questions d'un citoyen, pas des champs du schéma.** Une
> vue n'est retenue que si elle répond à une question qu'une personne se pose.
> Une matière bien couverte qui ne répond à aucune reste en fouille — ou ne
> s'affiche pas.

**Méthode.** Pour chacun des trois profils, parcourir les champs **réellement
peuplés** et décider quoi construire — jamais trier une liste de vues déjà
imaginées. L'interface actuelle est un brouillon, une preuve d'intention : elle
n'est pas la référence, et rien ici ne se formule en « corriger l'existant ».

Toute valeur a été **recalculée**. Les mesures navigateur (hauteurs, poids
transférés, débordements) sont reprises de #593 et signalées comme non refaites.

---

## 0. Deux populations, et pas une

**C'est la distinction dont dépend tout le reste**, et ni #324 ni #593 ne la
faisaient. Les 481 profils pivot publiés ne sont pas 481 profils de candidat :

| Population | `meta.provenance` | Profils | Ce que c'est |
| --- | --- | ---: | --- |
| **Candidats déclarés** | `candidat_declare` | **13** | une page chacun — le manifeste liste **exactement** cet ensemble |
| **Membres de roster** | `roster_groupe` | **468** | matière première des agrégats ; **tous** cités par une fiche, zéro orphelin, aucun destiné à avoir une page |

**Un chiffre sur 481 mélange les deux et ne veut rien dire.** Ce que chacune porte :

| Matière | 13 candidats | Volume | 468 roster | Volume |
| --- | ---: | ---: | ---: | ---: |
| `mandats` | 10 / 13 | 529 | 459 / 468 | 40 581 |
| `votes` | 7 / 13 | 8 860 | 449 / 468 | 1 304 091 |
| `amendements` | 7 / 13 | 55 288 | 449 / 468 | 6 036 444 |
| `interventions` | **7 / 13** | **16 242** | **0 / 468** | **0** |
| `textes_portes` | **7 / 13** | **423** | 15 / 468 | 49 |
| `tags_thematiques` | **7 / 13** | **1 331** | **0 / 468** | **0** |

Les quatre dernières lignes corrigent le tableau de couverture de #324 :
`interventions` n'est pas « 7 profils sur 481, l'onglet serait vide sur 474 »,
c'est **7 candidats sur 13** — exactement ceux qui portent aussi votes et
amendements.

Conséquence de produit : les 468 noms de membres affichés par les fiches **ne
doivent pas devenir des liens**. Seuls les 7 candidats qui y figurent aussi.

---

## 1. Les questions d'un citoyen, et celles auxquelles le corpus sait répondre

C'est la grille qui décide de tout. Une vue existe parce qu'elle répond à une
ligne — pas parce qu'une matière est bien couverte.

| Ce qu'un citoyen demande | Réponse possible ? | Sur quoi |
| --- | --- | --- |
| A-t-elle déjà exercé un mandat ? Lequel, quand ? | **oui** | 511 `mandat_electif` datés et estampillés |
| **Sur les lois dont j'ai entendu parler, elle a voté quoi ?** | **oui, pour 7 des 13** | **916 scrutins sur l'ensemble d'un texte → 704 textes distincts** |
| A-t-elle voulu faire tomber un gouvernement ? | **oui** | 66 motions de censure, **1 adoptée** |
| Quelles lois a-t-elle portées elle-même ? | **oui, mais le champ est piégé** | 423 `textes_portes` — voir §4.4 |
| De quoi parle-t-elle en séance ? | **oui, pour 7 des 13** | 16 242 interventions, **100 % sourcées** |
| **S'occupe-t-elle de la santé, de l'école, des retraites ?** | **non** | aucun champ thème sur les 17 748 scrutins |
| Est-elle assidue ? Travaille-t-elle beaucoup ? | **interdit** — §2 règle 3 | à **écrire**, pas à taire |
| Est-elle plus ou moins X que Y ? | **interdit** — §2 règle 1 | idem |
| Puis-je vérifier ? | **oui sur 3 matières, non sur 3** | voir §7 |

**Deux lectures de ce tableau, et ce sont les conclusions du document.**

**La question la plus naturelle est celle à laquelle le site ne peut pas
répondre.** « S'occupe-t-elle de la santé ? » n'a aucune donnée derrière elle.
Ce n'est pas un manque d'interface : c'est le chantier que #324 a différé, et
tant qu'il n'est pas fait, la page ne peut proposer qu'une entrée par **texte** et
par **date**, jamais par sujet. Le produit doit l'écrire, pas le contourner par un
« thème dominant » qui est un repli.

**Une matière très couverte peut ne répondre à aucune question.** 55 288
amendements sur les 13 candidats, dont **92,2 % de cosignatures** : personne ne se
demande combien d'amendements quelqu'un a cosignés, et aucune visualisation ne
rend ce nombre parlant. Le premier jet de ces propositions consacrait sa vue la
plus détaillée à mieux dessiner cette barre — c'était répondre à la donnée, pas à
la question.

---

## 2. Les règles que toute vue doit tenir

### 2.1 Une liste vide dit **pourquoi**, et les quatre causes ne se disent pas pareil

Chaque liste vide du corpus est couverte par une entrée `couverture` qui en nomme
la cause — correspondance exacte, sans reste. Et les deux populations n'ont pas la
même :

| Liste vide | Candidats (sur 13) | Cause dominante | Roster (sur 468) |
| --- | ---: | --- | ---: |
| `mandats` | 3 | `fait_etabli` + `hors_couverture` | 9 `non_collecte` |
| `votes` / `amendements` | 6 | 4 `fait_etabli` | 19 `non_collecte` |
| `textes_portes` | 6 | 4 `fait_etabli`, 2 `hors_couverture` | 453 `non_collecte` |
| `interventions` | 6 | 4 `fait_etabli` | 468 `non_collecte` |

**Les vides des candidats sont presque tous des faits établis ; ceux du roster,
presque tous des non-collectes.** Le bloc sert donc **13 pages et 113 entrées**,
pas 3 800.

| État | Ce qu'il affirme | Ce que la page doit dire |
| --- | --- | --- |
| `couvert` | collecté, dans le périmètre, **réellement zéro** | un zéro publiable |
| `fait_etabli` | un fait **sur la personne** | une phrase sur elle, sourcée |
| `hors_couverture` | la source ne publie pas cette période | une phrase sur la **source**, avec sa borne |
| `non_collecte` | rien ne peut être affirmé | ni zéro, ni fait |

Aucun composant n'en lit une seule. `meta.warnings[]` non plus — **12 des 13
candidats en portent, 26 au total** — ni `genere_le`, ni `synchro_le`, ni
`provenance`.

### 2.2 Un ratio porte ses deux nombres, et son dénominateur n'est jamais une occasion manquée

| Dénominateur | Verdict |
| --- | --- |
| les scrutins où la personne **s'est prononcée** | **autorisé** |
| les scrutins où elle **aurait pu** se prononcer | **interdit** (§2 règle 3) — ça transforme une absence en information négative |

### 2.3 Une liste tronquée déclare sa règle, et la récence n'en est pas une bonne

Trois troncatures muettes aujourd'hui : 12 votes sur 1 016 à 4 976, 12 scrutins de
cohésion sur 3 832 à 4 099, 20 mots-clés.

**Mais la récence seule reproduit le défaut qu'elle prétend corriger** : les 5
dernières lois votées par Jérôme Guedj tombent sur **deux jours**, comme les 12
cartes actuelles tombent sur deux jours de 2022. Une fenêtre de récence est
honnête à condition d'être **annoncée comme telle**, jamais présentée comme un
choix des plus importantes.

### 2.4 Ce qui est interdit doit être **écrit**, pas seulement absent

Deux des neuf questions du §1 le sont. Une page qui se contente de ne pas y
répondre laisse croire qu'elle n'y a pas pensé.

### 2.5 Un vote ne s'affiche jamais seul

**Un fait vrai, sourcé et présenté sobrement peut tromper davantage qu'un propos
partisan** — parce que la sobriété lui donne de l'autorité. « A voté Contre la
perpétuité pour les crimes sexuels » est exact, et faux de sens. Affiché dans une
typographie neutre avec un badge « Source vérifiée », il porte plus loin qu'un
tweet.

Trois causes, toutes dans notre donnée :

1. **Le titre d'une loi est écrit par ses auteurs.** « Loi pour la confiance dans
   la vie publique » n'est pas une description, c'est un argument — et on
   l'affiche comme s'il était neutre.
2. **Un vote isolé perd sa place dans la séquence.** Ce qui l'explique est souvent
   ce qui l'a précédé : un amendement rejeté, une disposition ajoutée en séance.
3. **On affiche le vote sans le « pourquoi », alors que le « pourquoi » existe.**

**Ce que la donnée porte déjà, et que personne ne lit :**

| Matière | Volume | Ce que ça donne |
| --- | ---: | --- |
| **Explications de vote développées** | **101** sur les 13 candidats | la personne dit elle-même pourquoi elle vote ainsi — Mélenchon 123 entrées au total, Guedj 42, Attal 33 |
| Amendements du même dossier | **130 244 rattachés** (#639 rang 3) | ce sur quoi on s'est battu dans le texte |
| Le dossier AN | `dossier_id` | exposé des motifs, débats, rapports |

⚠️ Sur les 214 entrées `explication_vote`, **113 sont des `reaction_courte`** — des
interjections, pas des explications. Seules les **101 développées** sont
exploitables, et le filtre est obligatoire.

**Quatre règles, toutes tenables sans éditorialiser :**

| Règle | Pourquoi |
| --- | --- |
| **Jamais un vote seul** — il s'affiche dans la liste des scrutins du même texte | la séquence *est* le contexte |
| **Le titre complet, jamais un raccourci** | « Réponses immédiates aux phénomènes troublant l'ordre public » abrégé en « ordre public » devient un slogan |
| **L'explication de vote à côté du vote, quand elle existe** | ce sont **ses mots à elle**, sourcés — pas notre glose |
| **Le lien vers le dossier AN comme sortie systématique** | on ne résume pas la loi, on mène à ce qui la décrit |

**Et une chose à refuser explicitement : résumer un texte.** « Ce texte visait
à… » est une glose que rien ne source. Une glose neutre en apparence est
précisément le vecteur du biais décrit ici.

**Le remède n'est pas plus d'explication, c'est moins d'isolement.** Un vote
présenté seul est une citation hors contexte ; le même vote dans sa séquence, avec
les mots de la personne à côté, ne l'est plus.

### 2.6 Regrouper n'est pas joindre

Regrouper des faits d'une **même** source par leur libellé est permis ; joindre des
faits de **sources différentes** en décrétant qu'ils visent le même objet est une
affirmation qu'aucune ne fait. Voir
[`docs/decisions/regrouper-nest-pas-joindre-639.md`](../docs/decisions/regrouper-nest-pas-joindre-639.md).

---

## 3. Les trois niveaux de lecture

| Niveau | Durée | Ce qu'on doit en retirer | État |
| --- | --- | --- | --- |
| **Coup d'œil** | ~30 s | qui c'est, ce qu'elle a fait, sur quelle période | **absent partout** — premier écran à 57,6 % de chrome en 1280 px, 63,3 % en 390 px *(#593)* |
| **Lecture** | ~3 min | ce qui distingue son activité, sans la comparer à personne | partiel et trompeur |
| **Fouille** | sans limite | la liste exhaustive, traçable | existe, et c'est le seul niveau servi |

---

## 4. Profil candidat — 13 pages

### Le coup d'œil : trois éléments, et rien d'autre

```
┌──────────────────────────────────────────────────────────────────────┐
│  Jérôme Guedj                          Parti Socialiste (PS)         │
│  Inspecteur général des affaires sociales                            │
│  Député à l'Assemblée nationale depuis le 07/07/2024                 │
│  précédemment du 22/06/2022 au 09/06/2024              [source →]    │
├──────────────────────────────────────────────────────────────────────┤
│  Sur les 182 lois soumises à un vote sur l'ensemble du texte         │
│  auxquelles il a pris part :                                         │
│      130 Pour   ·   39 Contre   ·   13 Abstention                    │
│  Positions documentées. Les absences ne sont pas publiées.           │
├──────────────────────────────────────────────────────────────────────┤
│  Les 3 plus récentes                                                 │
│  21/07/2026  ABSTENTION  Projet de loi relatif à la protection       │
│                          des enfants                      [source →] │
│  21/07/2026  POUR        Proposition de loi visant à protéger les    │
│                          mineurs …                        [source →] │
│  21/07/2026  CONTRE      Projet de loi visant à offrir des réponses  │
│                          immédiates …                     [source →] │
└──────────────────────────────────────────────────────────────────────┘
```

**Rien n'y est déduit.** La circonscription n'apparaît pas : le profil ne porte
qu'un `num_circo` sans département.

⚠️ **Le décompte de la deuxième ligne est contesté et reste à trancher.** « 130
Pour » sans savoir sur quelles lois ne se comprend pas ; sans lui, les trois lois
citées sont trois anecdotes. La ligne est conservée ici avec ses trois conditions
— dénominateur = les lois où la personne s'est prononcée, jamais de pourcentage
ni de barre, mention « absences non publiées » — et l'arbitrage reste ouvert.

### 4.1 · Le mandat, en une phrase — et l'absence de mandat aussi

**Le repli actuel affirme.** La qualité sous le nom est `identite.profession`, ou à
défaut un libellé fabriqué depuis `chambre`. Sur les 481 profils : **24 sans
`profession`**, dont **20 sans aucun `mandat_electif`** — le libellé affirme alors
un mandat que le profil ne porte pas — et **3** rendus « Ancien(ne) élu(e) ».

**Refuse :** une ancienneté en années décimales ; un « thème dominant »
(`DEFAULT_THEME = 'Institutions'` absorbe tout libellé non classé — 225 des 338
votes du seau de Mélenchon n'ont rencontré aucun mot-clé, et 269 des 282 votes
classés « Europe » le sont par la sous-chaîne `'ue'` dans « publiq**ue** ») ; un
décompte de « Responsabilités » sans unité.

### 4.2 · Les lois votées — la vue qui porte le produit

**916 des 17 748 scrutins portent sur *l'ensemble* d'un texte** — le vote final,
le seul qu'un citoyen comprend sans rien connaître — et se ramènent à **704 textes
distincts**.

| Candidat | Positions | dont sur l'ensemble | **Lois distinctes** | Pour / Contre / Abst. |
| --- | ---: | ---: | ---: | --- |
| Guedj | 2 906 | 212 | **182** | 130 / 39 / 13 |
| Le Pen | 1 813 | 204 | **171** | 82 / 66 / 23 |
| Wauquiez | 826 | 155 | **128** | 58 / 63 / 7 |
| Attal | 2 035 | 144 | **120** | 109 / 8 / 3 |
| Mélenchon | 1 016 | 165 | **119** | 17 / 87 / 15 |
| Philippe | 141 | 95 | **79** | 11 / 60 / 8 |
| Bertrand | 123 | 77 | **64** | 6 / 51 / 7 |

**Un critère de sélection sourcé existe** : le nombre de scrutins publics qu'un
texte a suscités — un fait sur le débat parlementaire, pas un jugement sur les
personnes. Il fait remonter les lois dont on a entendu parler : budget 2026 (927
scrutins), aide à mourir (839), PLFSS 2026 (520), retraites universelles (270).

| Loi | Guedj | Le Pen | Attal | Wauquiez |
| --- | --- | --- | --- | --- |
| Aide à mourir | Pour | Contre | Pour | Contre |
| PLFSS 2026 | Pour | Contre | Pour | Abstention |
| Souveraineté agricole | Contre | Pour | Pour | Pour |
| Ordre public | Contre | Pour | Pour | Pour |

**Et les cases vides disent quelque chose.** Budget 2026 : 927 scrutins, **zéro
vote sur l'ensemble**, parce qu'adopté par 49.3 — et la fiche `LECORNU_II` en
porte la preuve. La case devient « **adopté sans vote (art. 49.3)** ».

**À écrire en petites lignes :** le critère de tri. Un classement non explicité sur
un site qui promet « aucun classement » se lit comme un classement.

### 4.3 · Les motions de censure — un registre à part

**66 motions**, du 20/03/2013 au 06/07/2026, dont **une seule adoptée**. Le Pen 33,
Guedj 24, Mélenchon 5, Wauquiez 4, Philippe 3, Bertrand 3, Attal 1 (non-votant).

**Refuse :** un compte présenté comme un trait de caractère. « A voté la censure 33
fois » se lit comme une mesure d'opposition alors que **c'est presque une
tautologie** — seuls les soutiens d'une motion votent. La vue est une **liste datée
et nommée**, et elle porte le sort : rejetée 65 fois sur 66.

### 4.4 · Les textes portés — et le contresens qu'ils produisent

**Les 283 textes portés d'Édouard Philippe, dont 149 promulgués, sont ceux de son
gouvernement.** Son mandat de député s'achève le 15/06/2017, ses textes sont datés
2017-2020, et **281 sur 283 sont au titre près les 282 textes de
`gouvernement-PHILIPPE_2`**.

Le croisement date × périodes de `mandats[]` le désamorce :

| Candidat | Textes | Pendant une **fonction gouvernementale** | Pendant un **mandat électif** |
| --- | ---: | ---: | ---: |
| Philippe | 283 | **283** | 0 |
| Attal | 34 | 31 | 3 |
| Retailleau | 36 | 1 | 35 |
| Mélenchon | 33 | 0 | 33 |
| Wauquiez / Guedj | 9 / 5 | 0 | 9 / 5 |

**Deux énoncés distincts, non comparables.** Comme parlementaire : 3 à 35 textes.
Comme membre de l'exécutif : à rattacher à la fiche de gouvernement.

**Et pour un Premier ministre, rien n'est attribuable** : Philippe est initiateur de
281 des 282 textes de son gouvernement, Borne de 110 sur 111. L'initiateur *unique*
ne discrimine pas davantage — les 117 textes concernés ont tous le même. Retenu :
sa fonction, sa durée, et le renvoi vers la fiche de son gouvernement.

**Les 0 texte de `FILLON_2` et `FILLON_3` ne sont pas un bug** : ces gouvernements
s'achèvent avant le 21/06/2017, borne des dossiers législatifs. Wauquiez, Bertrand
et Royal ont été ministres et leur bilan n'est **pas mesurable** : la page doit
l'écrire, jamais afficher « 0 ».

### 4.5 · Les interventions — la vue la mieux servie, écartée sur la mauvaise population

| Mesure, sur les 13 candidats | Valeur |
| --- | ---: |
| Candidats porteurs | **7 / 13** |
| Interventions | **16 242** |
| … avec `source_url` | **16 242 / 16 242 (100 %)** |
| … avec un `sujet` | 14 817 (91,2 %) |

`type_detail` structure la vue : `debat` 7 295 · `loi` 4 095 ·
`question_gouvernement` 3 459 · `question` 840 · `motion_censure` 298 ·
`explication_vote` 214.

**Retenu : les sujets sur lesquels il/elle a interpellé le gouvernement.** Les
questions au gouvernement portent **719 libellés courts écrits par l'AN** —
« Réforme des retraites », « Pouvoir d'achat », « Situation à Mayotte ». Pas une
classification de notre fait : les sujets qu'ils ont choisi de soulever.

**Mais deux champs jamais lus changent le sens du volume :**

| Candidat | Total publié | dont **exécutif** (`fonction`) | dont **réactions courtes** (`format`) | **Discours comme élu·e** |
| --- | ---: | ---: | ---: | ---: |
| Attal | 3 963 | 3 555 | 1 829 | **189** |
| Mélenchon | 3 933 | 35 | 2 360 | **1 553** |
| Philippe | 2 376 | **2 376** | 1 036 | **0** |
| Guedj | 2 702 | 0 | 1 664 | **1 038** |
| Le Pen | 2 247 | 0 | 1 260 | **987** |

39,7 % du corpus est prononcé **au nom du gouvernement**, 53,6 % sont des
`reaction_courte` — une interjection, pas un discours.

**Refuse :** une fréquence ou une moyenne ; un nuage de mots, qui pondère donc
classe.

### 4.6 · Les amendements — en fouille, jamais sur le premier écran

55 288 sur les 13 candidats, dont **92,2 % de cosignatures** à l'échelle du corpus.
Ce qui reste publiable : un **ratio à dénominateur explicite**, et la **bande « sort
non renseigné »** — **9 950 des 55 288 (18,0 %)** portent un `sort` nul.

**Refuse :** un taux d'adoption tous déposants confondus (interdit, §6 —
`type_deposant` ne connaît que `depute` 468 822 et `commission_rapporteur`
15 310) ; un badge de traçabilité (**0 / 484 132** portent une `source_url`).

### 4.7 · Ce que le site sait, et ce qu'il ne sait pas

L'onglet « Données » — aujourd'hui une phrase générique et ~800 px de vide *(#593)*
— devient la fiche de couverture : les **113 entrées** de `couverture`, les **26
avertissements** de 12 des 13 candidats, `genere_le`, `provenance`, `synchro_le`.
**C'est ici que le mandat de lecture du bloc `couverture` est nommé** : un bloc
publié dont personne n'a la charge de l'afficher redevient invisible.

Les **475 noms de membres** affichés par les fiches : **468 sont des membres de
roster**, sans page et sans devoir en avoir. Seuls les **7 candidats**.

---

## 5. Profil de groupe — 7 fiches

Ces pages ne publient **aucun profil individuel** : elles publient des agrégats.

### Le coup d'œil

> **La France insoumise — NUPES** · Assemblée nationale, 16ᵉ législature
> Sur les **62 lois** votées dans leur ensemble où le quorum était atteint :
> **42 Contre · 12 Pour · 8 Abstention**. Couverture : **76 / 76 membres**.

| Groupe | Scrutins agrégés | sur l'ensemble | + quorum | Position majoritaire |
| --- | ---: | ---: | ---: | --- |
| `AN:RN` | 4 085 | 208 | 64 | 39 Pour · 17 Contre · 8 Abst. |
| `AN:LFI` | 3 973 | 209 | 62 | 42 Contre · 12 Pour · 8 Abst. |
| `AN:SOC` | 3 843 | 206 | 51 | 24 Pour · 16 Contre · 11 Abst. |
| `AN:REN` | 4 099 | 207 | 45 | 43 Pour · 2 Contre |
| `AN:LR` | 3 832 | 202 | 31 | 25 Pour · 4 Contre · 2 Abst. |

### 5.1 · La cohésion en six nombres, jamais en barre

Vérifié sur les 12 cartes affichées d'`AN:LFI` : `taux_coherence` = 0,0667 pour les
douze, `taux_coherence_hors_absents` = 1,0, **un seul votant sur 15**, quorum non
atteint, toutes du 07/06/2024. **Ce que la barre restitue est la participation.**

Le remplacement est dans le fichier : `1 pour · 0 contre · 0 abstention · 14
absents — sur 15 membres éligibles`.

**Refuse les trois taux**, y compris `taux_coherence_hors_absents` — « plus
honnête » reste un indice.

**L'unanimité est la règle, la division est rare — donc listable** : 1 scrutin
« très divisé » sur `AN:LFI`, 5 sur `AN:RN`, 20 sur `AN:SOC`, 31 sur `AN:LR`.

### 5.2 · Les 12 cartes deviennent une sélection déclarée

`slice(0, 12)` prend les 12 **premiers dans l'ordre du fichier**. Règle écrite à
l'écran : les 12 plus récents **où le quorum était atteint, sur N agrégés** — 608
sur 3 973 pour `AN:LFI`, 237 sur 3 832 pour `AN:LR`.

### 5.3 · Les effectifs, rapportés à une date

**Trois décomptes coexistent** : `effectif`, `membres[]`, `roster_total`. Pour les
5 fiches AN, `membres[]` ≈ `roster_total` — **l'écart n'existe que sur le Sénat**
(15 / 235), un périmètre éditorial assumé.

**Arbitrage rendu** : tous les comptes d'une fiche se rapportent à une **date de
référence publiée** — la clôture de la législature. « Actuel » et « actifs »
affirmaient un présent qui n'existe pas sur une fiche close.

| Fiche | `effectif` avant | **au 09/06/2024** |
| --- | ---: | ---: |
| `AN:REN` | 85 | **169** |
| `AN:RN` | 75 | **88** |
| `AN:LFI` | 60 | **75** |
| `AN:LR` | 38 | **61** |

Ce que l'ancien champ comptait : **les membres portant un mandat électif encore
ouvert**, soit les réélus de 2024.

**Refuse :** un taux de renouvellement — 108 / 193 est un indice comparable entre
groupes ; une durée moyenne d'appartenance ; un histogramme d'effectif par année,
**calculable et faux** (il afficherait « LFI avait 1 député en 2012 » et « le RN
0 » : il mesure combien des membres actuels étaient déjà députés cette année-là).

### 5.4 · Les commissions — « y siège » n'est pas « y est passé »

**« 67 des 76 membres siègent à la commission des finances » serait faux : ils sont
5.** Sur ces 67, **44 y ont siégé un seul jour**.

Le motif est concentré : **43 % des adhésions de `commission` durent un jour**,
contre 0 à 5 % dans toutes les autres catégories. Cause trouvée dans AMO30 : un
député n'appartient qu'à **une commission permanente à la fois**, donc toute
bascule temporaire s'écrit fin + nouveau début — **93,2 % des paires consécutives
sont contiguës**.

**Arrêté :** au coup d'œil, les membres qui y siègent à la date de référence,
rapportés à l'effectif. Le cumul historique en second, nommé comme tel.

### 5.5 · L'empreinte thématique — à ne pas afficher

**Elle est celle d'une seule personne** : 470 tags sur `AN:RN` portés par Marine Le
Pen, 382 sur `AN:SOC` par Jérôme Guedj, 197 sur `AN:REN` par Gabriel Attal.
`AN:LFI` et `AN:LR` en affichent **zéro**.

Les 468 membres de roster publient `tags_thematiques: []` et `interventions: []`.
Et ce ne sont pas les huit thèmes stables mais des mots-clés bruts : `a69`,
`abattement`, `accueil`.

**Arbitrage : peupler la donnée plutôt que retirer la vue**, par une collecte
réduite au thème — `theme_officiel` est renseigné sur **45,6 %** des 16 242
interventions, contre 3,1 % pour le repli `mots_cles`. Le poids vient du champ
`texte` (**1 374 octets par intervention**, ~1,5 Go extrapolés aux 468) ; le thème
ne pèse rien. **Reste à établir** que Syceron permette de ne lire que ça — sinon
l'économie porte sur le volume publié, pas sur le budget CI.

### 5.6 · `meta` — tout est là, rien n'est lu

`couverture_roster.etat` vaut `dans_le_perimetre` sur les 5 fiches AN et
`hors_perimetre` sur les 2 du Sénat ; la `preuve` fait **0 caractère** sur les
premières et **1 680** sur `Senat:LR`. **La preuve n'existe que là où il y a
quelque chose à expliquer** — la règle d'affichage est donc « s'il y a une preuve,
on l'affiche », et elle ne produit du texte que sur 2 pages sur 7.

`fraicheur_donnees` dit ce qu'aucune autre source ne dit : sur les fiches Sénat,
que `archive.nossenateurs.fr` est **arrêté** et que la fiche reflète la dernière
donnée avant l'arrêt, **pas la composition actuelle**.

Et `seuil_quorum` — `0.5` — manque là où les cartes affichent « quorum non
atteint » sans dire ce qu'est le quorum.

---

## 6. Profil de gouvernement — 10 fiches

Une fiche de gouvernement n'est pas le profil d'une personne : la question est
**« qu'est-ce que ce gouvernement a fait passer, et comment »**.

### Le coup d'œil

> **Gouvernement Élisabeth Borne** · du 21/05/2022 au 09/01/2024
> **19 lois promulguées** · 111 textes suivis, dont 43 encore dans la navette
> **6 textes adoptés sans vote (article 49.3)**

299 textes sont adoptés sur 725, mais **67 seulement sont promulgués**. « Adopté »
n'est pas « devenu une loi », et les deux pastilles sont aujourd'hui au même
niveau. Le 49.3 est le fait le plus lisible qu'une fiche porte, et sur
`LECORNU_II` il est à **4 800 px du haut** *(#593)*.

### 6.1 · `textes` — l'objet le mieux sourcé du corpus

**725 / 725 avec `source_url` et `dossier_id`**, 723 / 725 avec `initiateurs`. Rien
d'autre n'atteint ça.

**Une règle d'affichage à tenir : un statut ne s'affiche jamais sans sa date.**
`navette_en_cours` affirme un présent ; l'écart médian entre la fin du gouvernement
et le dernier acte de ses textes en navette va de 107 jours (`ATTAL`) à **369 jours
(`PHILIPPE_2`, max 1 110)**. Ce n'est pas un défaut de donnée — le pipeline lit
correctement — mais **le statut décrit le dossier, pas le gouvernement**, et un
dossier survit au gouvernement qui l'a déposé : le CETA, déposé sous Philippe en
2019, a eu un acte en **mars 2024**.

### 6.2 · `membres` — et `actif` y est juste

127 entrées, **107 distincts par fiche mais 55 sur le corpus**, 127 / 127 sourcées,
**12 actifs — tous sur `LECORNU_II`**. Le cadre d'une fiche de gouvernement *est*
le gouvernement, donc « actif » veut dire quelque chose — contrairement aux fiches
de groupe.

**Les doublons n'en sont pas** : ce sont des changements de portefeuille — Woerth
trois fois sous `FILLON_2`. À regrouper par `membre_id`, jamais en cartes séparées.

Le chef manque sur **7 fiches sur 10**, pour deux causes distinctes — le libellé au
féminin (#658, corrigé) et l'absence de profil pivot (#644, fermé sur un verdict
négatif).

### 6.3 · `meta` — le manque structurel

Quatre clés, **zéro avertissement sur les dix fiches**, et **aucun bloc de
couverture**.

| Objet | Sait dire pourquoi il est incomplet ? |
| --- | --- |
| Profil de candidat | **oui** — `couverture`, 4 états, 113 entrées |
| Fiche de groupe | **oui** — `couverture_roster.etat` + `preuve` |
| **Fiche de gouvernement** | **non** |

C'est ce qui explique que le seul bon message du site — celui de `FILLON_2`, la
**seule route sur onze** où une absence porte sa cause — vienne d'une constante
codée en dur. Or `BORNE` publie 23 personnes pour un gouvernement d'une
quarantaine, et rien ne l'écrit.

### 6.4 · Une vue qui n'était dans aucune trame : « cette loi est-elle appliquée ? »

Les 725 textes sont **législatifs** : le suivi s'arrête à la promulgation. Une loi
promulguée n'est pas une loi appliquée.

**333 des 725 textes portent déjà le NOR de leur loi** (`infoJO.referenceNOR`), et
le JORF publie `<LIEN typelien="APPLICATION">` — **108 179 occurrences**. La
jointure se ferait sur un **identifiant officiel des deux côtés**.

**Refuse :** un délai moyen, un « taux d'application » comparé entre
gouvernements, et une absence de décret présentée comme un manquement — toutes les
lois n'en appellent pas. `<AUTORITE>` étant **vide sur 380 / 380 décrets**, « N
décrets signés » n'est de toute façon pas constructible : la garantie vient de la
source, pas d'une règle qu'on s'impose.

**Case D, et la mesure du 31/08 la rend inexploitable en l'état.** Le taux de
résolution a été mesuré sur les **349 lois** de nos fiches portant un NOR, contre
le fonds JORF complet : **135 portent au moins un décret d'application**, et
celles qui résolvent en portent une médiane de 7,5 (max 65), avec un délai médian
de **57 jours** entre la loi et son premier décret.

**Mais la part s'effondre avec la récence, et le zéro n'est pas un manque de
recul :**

| Année de promulgation | Lois | Avec décret | Part |
| ---: | ---: | ---: | ---: |
| 2018 | 41 | 35 | **85,4 %** |
| 2020 | 42 | 21 | 50,0 % |
| 2022 | 37 | 15 | 40,5 % |
| 2023 | 41 | 10 | 24,4 % |
| **2024** | 22 | **0** | **0 %** |
| **2025** | 18 | **0** | **0 %** |

Vérifié sur l'ensemble du fonds : **aucune des 188 lois promulguées depuis 2024 ne
porte de lien `APPLICATION`**. La preuve est directe — la loi immigration de 2024,
redélivrée en août 2026, porte **138 liens tous `CITATION`**, dont le décret
2024-799. Le lien existe ; la **qualification** « application » n'est pas posée.
C'est une requalification éditoriale de Légifrance, faite après coup, **dont le
délai n'est pas publié**.

`CITATION` n'est pas un substitut : 5 352 occurrences contre 1 302 `APPLICATION`
sur les mêmes lois. S'en servir affirmerait une relation que la source ne déclare
pas (§2.6).

**Conséquence : la vue afficherait « aucun décret d'application » sur toutes les
lois récentes** — le faux vide exact qu'interdit §2 règle 5. Et **un tableau par
gouvernement serait pire** : `ATTAL`, `BARNIER`, `BAYROU` et `LECORNU_II` seraient
à zéro pour une raison qui ne les concerne pas.

---

## 7. Un badge, une promesse

Le badge « Source vérifiée » apparaît à l'identique dans les trois vues et n'est un
lien que dans une. La donnée décide de qui peut le porter :

| Objet | `source_url` | Badge |
| --- | ---: | --- |
| Scrutins | **17 748 / 17 748** | **oui** |
| Interventions (13 candidats) | **16 242 / 16 242** | **oui** |
| Textes de gouvernement | **725 / 725** | oui, déjà le cas |
| Amendements | **0 / 484 132** | **non** |
| `textes_portes[]` | **0 / 472** | **non** — corrigé par #639 rang 2, attend un run |
| `mandats[]` | 1 302 / 41 110 (3,2 %) | non |

**Un badge non cliquable là où les autres le sont apprend au lecteur à ne plus
essayer.**

---

## 8. Le catalogue du 17/08, repris ligne à ligne

| # | Proposition | Sort | Motif, mesuré sur la bonne population |
| ---: | --- | --- | --- |
| 1 | Participation aux scrutins `142 / 180` | **écartée** | son dénominateur est « ce qu'elle aurait pu voter » |
| 2 | Chronologie des mandats | **reprise, réduite** | 511 `mandat_electif` sur 41 110 : une frise serait à 99 % des groupes d'amitié |
| 3 | Histogramme par thématique | **écartée** | aucun champ thème sur les 17 748 scrutins |
| 4 | Détail Pour/Contre/Abstention | **reprise** → §5.1 | les six comptes sont dans la donnée, jamais rendus |
| 5 | 49.3 isolé des statistiques de vote | **reprise et promue** → §6 | fait le plus lisible d'une fiche, aujourd'hui à 4 800 px du haut |
| 6 | Sankey des textes | **remplacée** → §6.1 | 7 statuts déjà comptés ; un Sankey ajoute une lecture, pas une information |
| 7 | Ratio adoptés/déposés + barre par sort | **reprise, en fouille** → §4.6 | ne répond à aucune question du §1 |
| 8 | Interventions par commission | **reprise, dépouillée** → §4.5 | 7 candidats sur 13, 100 % sourcées ; le nuage de mots est écarté |
| 9 | Hémicycle interactif | **écartée** | `position_dans_hemicycle` sur 1 024 / 41 110 mandats (2,5 %) |
| 10 | Amendements gouvernementaux | **écartée** | **zéro** amendement gouvernemental sur 484 132 |
| — | *(absente)* | **ajoutée** → §4.2 | le vote sur *l'ensemble* : 916 scrutins, 704 textes |
| — | *(absente)* | **ajoutée** → §4.3 | les 66 motions de censure |
| — | *(absente)* | **ajoutée** → §2.1, §4.7 | la lecture du bloc `couverture` |
| — | *(absente)* | **ajoutée** → §4.4 | le contresens des textes portés d'Édouard Philippe |
| — | *(absente)* | **ajoutée** → §6.4 | « cette loi est-elle appliquée ? » |

**La jointure membre × groupe de #324** — « a voté Pour ; son groupe a voté
Contre » — n'est **pas retenue au premier tour** : mesurée sur les 13 candidats,
elle donne **17 divergences, 10 sous quorum** (Guedj 9, Le Pen 1, les onze autres
rien), parce que les 7 fiches de groupe ne couvrent que la XVIe quand **50,7 % des
positions publiées sont en XVIIe**. Elle touche par ailleurs à §2 règle 7, qui
réserve les écarts individu/groupe au contrôle interne.

---

## 9. Ce que le brainstorming a produit

**Onze issues**, dont **neuf closes** et six déjà en production. Aucune n'était
connue avant.

| Issue | Sujet | État |
| --- | --- | --- |
| #640 | 613 mandats électifs manquants sur 393 profils | **close, en production** |
| #641 | 8 professions publiées en code de nomenclature | **close, en production** |
| #642 | avertissements : 80 internes, 35 lisibles, rien ne les séparait | **close** |
| #643 | signatures comptées comme amendements — × 5 à × 32 | **close, en production** |
| #649 | les agrégats publiés n'étaient surveillés par rien | **close** |
| #653 | `debut_dans_groupe` + cadrage par date de référence | **close** |
| #656 | « y siège » / « y est passé » | **close** |
| #658 | Premier ministre non reconnu au féminin | **close** |
| #659 | `civilite` et la nomenclature PCS de l'INSEE | **close** |
| #639 | clé de dossier législatif — rangs 1-3 livrés | **rang 4 différé** |
| #657 | empreinte thématique d'une seule personne | **ouverte** |

**Le motif dominant, sur cinq d'entre elles : deux grandeurs différentes sous un
seul nom.** Signatures et amendements · « y siège » et « y est passé » · entrée
dans le groupe et premier mandat électif · plomberie et explication au lecteur ·
« aujourd'hui » et « à la clôture ».

---

## 10. Ce qui attend le temps 3 (#595)

Chaque vue de ce document doit y recevoir sa case — **A** disponible, **B**
dérivable côté client, **C** à pré-agréger, **D** à collecter.

Les cases **D** connues, avec leur mesure :

| Chantier | Couverture mesurée |
| --- | --- |
| **Thématisation** | aucun champ thème sur les 17 748 scrutins — **la question la plus naturelle d'un citoyen, et la seule sans réponse possible** |
| Fiches de groupe en législature XVII | **aucune** — 665 654 des 1 312 951 positions publiées (50,7 %) sans groupe de référence |
| Scrutins sénatoriaux | `Senat:LR` et `Senat:SER` portent **0** scrutin agrégé |
| `source_url` sur amendements | **0 / 484 132** |
| Décrets d'application | jointure NOR balisée des deux côtés, **taux de résolution non mesuré** (#664) |
| Interventions des membres de roster | **0 / 468** — collecte réduite au thème (#657) |
