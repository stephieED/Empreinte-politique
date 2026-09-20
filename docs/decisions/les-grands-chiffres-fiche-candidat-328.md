<a id="les-grands-chiffres-fiche-candidat-328"></a>

# « Les grands chiffres » : une frise qui commande deux colonnes appariées (#328) (2026-09-02)

`2026-09-02`

> **En bref** — le bloc de tête de la fiche candidat, arbitré en maquette : la frise du parcours devient l'ossature et sa couleur relie chaque piste à sa colonne (bleu/bronze, le seul couple qui survive au daltonisme rouge-vert) ; la posture passe en **motifs** et distingue « non déclarée par l'Assemblée » de « non renseignée chez nous » ; les lignes sont **appariées** et ordonnées par degré d'engagement de l'acte, les tirets étant des faits (« un ministre ne vote pas », son siège est tenu par son suppléant) ; une concentration ne s'affirme que si un texte porte **plus que tous les autres réunis** — un P90 a été essayé et écarté parce qu'un percentile ne peut jamais se taire ; les dossiers se listent **par date**, jamais par volume ; l'empreinte thématique vient de la **commission saisie au fond**, sourcée, jamais d'un titre ; et la ligne « votes » est **retirée** après trois tentatives mesurées, parce que tout ce qui serait retenable y est soit interdit (§2 règles 3 et 7) soit inaffichable en un chiffre — c'est en la construisant qu'on a failli publier qu'Attal avait voté contre sa propre loi, ce qui a ouvert #711.

Bloc de tête de la fiche candidat, arbitré en maquette avec la propriétaire du
dépôt les 01 et 02/09/2026. Aucun code n'est écrit à ce jour : cette décision
fige ce qui a été tranché pour que l'implémentation ne le redécouvre pas.

Maquettes de référence : [Attal](https://claude.ai/code/artifact/4640f53c-d09f-434d-9c1d-f510140f4121)
(deux rôles) et [Guedj](https://claude.ai/code/artifact/3758633c-1b38-48b6-9c0a-4f97dce7c848)
(un seul).

## 1. Le nom, et ce qu'il a coûté d'y arriver

**« Les grands chiffres »**, précédé d'une seule ligne : *« Ce que cette personne
a engagé. »*

Deux noms ont été essayés et écartés. **« Coup d'œil »** promettait de la
rapidité, pas du contenu. **« L'essentiel »** promettait une synthèse que le
bloc ne délivre pas : ce qu'on a construit est un tableau de bord, pas un
résumé. Le nommer honnêtement libère la place pour un vrai résumé ailleurs.

**La ligne d'introduction a été réduite trois fois.** Elle opposait d'abord le
vote (réaction) aux actes d'initiative, en deux phrases accentuées ; puis en
énumérant les cinq lignes ; puis à ces cinq mots. Le motif de chaque coupe est le
même, et c'est la règle qui gouverne tout ce bloc :

> **Le texte explicatif est un aveu d'échec.** Si une phrase doit expliquer un
> chiffre, c'est la forme qui n'a pas fait son travail.

## 2. La frise commande les colonnes

**Le parcours n'est pas une section à part : c'est l'ossature du bloc.** Une
piste par rôle, et **la couleur fait le lien** — une piste et sa colonne portent
la même.

Le constat qui l'a imposé, sur `gabriel-attal` : *« ses 5 points marquants ont
l'air d'être en tant que ministre de l'éducation, mais ça a l'air de minimiser sa
carrière »*. Cinq catégories fixes décrivent le métier d'un député ; chez un
ancien ministre elles se remplissent de ce que son ministère a produit, et son
travail parlementaire disparaît. **Sa carrière alterne cinq fois**, et son
mandat en cours est parlementaire — rien dans la version précédente ne le disait.

### Le code couleur : bleu contre bronze

`--parl:#2E4A7D` et `--gouv:#8A6512`. **C'est le seul couple qui survive au
daltonisme rouge-vert**, le plus répandu, et ni l'un ni l'autre ne se lit comme
positif ou négatif — ce sont deux métiers, pas deux notes. Le vert et le rouge
sont pris par les positions de vote (`DESIGN_SYSTEM` §2), le jaune signal est
réservé à la sélection, à l'action et à la source vérifiée.

### La posture en motifs, pas en couleur

La piste parlementaire porte `mandats[].position_dans_hemicycle` (#686) par
**motif** — plein, hachuré, semis, contour plein, contour tireté — parce que la
couleur code déjà le rôle. Cinq états, et **deux absences distinctes qui ne se
confondent pas** :

- **« non déclarée par l'Assemblée »** — une valeur publiée (`non_declaree`) ;
  c'est le cas des **cinq groupes de la XVIIᵉ** ;
- **« non renseignée chez nous »** — contour tireté, le vocabulaire que
  `DESIGN_SYSTEM` §5 emploie déjà pour une appartenance non renseignée.

Sur `gabriel-attal` les trois mandats sont dans trois états différents ; sur
`jerome-guedj` la posture **change** — majorité en 2012-2014 (SRC), opposition
en 2022-2024 (SOC), non renseignée avant et depuis.

### Un parlementaire en mission n'est pas un membre du gouvernement

`jerome-guedj` porte deux `fonction_gouvernementale` avec
`fonction: "en mission"`, dont une **en cours**. Ce sont des missions auprès d'un
ministère, pas des appartenances : elles reçoivent une **piste distincte, en gris
neutre** — ni bleu ni bronze. Le critère d'appartenance réelle est
`appartenancesGouvernementales`, soit **6 des 13 candidats déclarés**.

## 3. Les lignes sont appariées, et ordonnées par degré d'engagement

Des objets de même nature se font face et se traitent pareil. L'ordre est un
gradient **sur la nature des actes**, jamais sur les personnes :

| Ligne | À l'Assemblée | Au gouvernement |
| --- | --- | --- |
| Textes portés | propositions de loi | projets de loi |
| Amendements | dossiers + dépôts | **—** un ministre ne dépose pas d'amendement |
| Mandats en commission | commission + nombre distinct | **—** un ministre n'y siège pas |
| Questions au gouvernement | posées | prises de parole depuis le banc |
| Interventions | situées / total | situées / total |

**Les tirets sont des faits, pas des vides.** « Un ministre ne vote pas » — son
siège est tenu par son suppléant, vérifié sur Attal : ses 2 035 positions tombent
exactement dans ses trois périodes parlementaires.

**Chaque colonne compte contre son propre total.** « 211 / 577 » d'un côté, « 367
/ 2 759 » de l'autre : le total du profil (3 963) disparaît, et les deux colonnes
ne se mélangent plus. Le mot **« situées »** porte la limite sans phrase — 211 se
rapporte aux interventions qui portent un sujet, pas à toutes.

## 4. Ce que chaque chiffre porte, et la règle qui se tait

**Un nombre sans son objet ne dit rien.** « 24 / 67 mandats en commission » — et
quoi ? Chaque ligne nomme donc ce sur quoi elle porte, et **seuls les nombres
sont en gros** ; l'objet reste à l'échelle des libellés.

### La concentration ne s'affirme que là où elle se prouve

Sur les amendements, une ligne « N d'entre eux sur X » n'apparaît que si **ce
texte porte plus que tous les autres réunis**. Aucune constante arbitraire : c'est
un fait, pas un seuil.

Mesuré sur les 13 candidats déclarés : elle parle pour `gabriel-attal` (43 de ses
49, soit 88 %) et `laurent-wauquiez` (182 de ses 326, 56 %) ; elle **se tait**
pour `jerome-guedj` (24 %), `marine-le-pen` (17 %) et `jean-luc-melenchon` (21 %).

**Un percentile a été essayé et écarté** : un P90 sélectionne toujours 10 % des
dossiers, donc il ne peut **jamais** ne rien dire. Sur `marine-le-pen` il faisait
ressortir 9 textes sur 83 par construction, pas parce que neuf se détachaient.

### Les dossiers se listent par date, jamais par volume

Déposer beaucoup d'amendements sur un texte peut être un travail de fond comme
une stratégie de blocage, et le nombre ne les distingue pas. Couronner « le plus
amendé » chez Attal mettait en avant un texte de **2017** et rendait invisible
qu'il amende encore en **novembre 2024**, sous son mandat en cours.

### L'empreinte thématique vient de la commission saisie, jamais d'un titre

La commission saisie au fond (`AN1-COM-FOND-SAISIE`) qualifie chaque dossier
amendé. **Elle est sourcée** : l'Assemblée affecte, nous recopions — la déduire
d'un titre serait une classification construite par ce dépôt, ce que §4 qualifie
d'acte éditorial à propos des catégories INSEE. Le libellé dit **« examinées
par »**, jamais « travaille sur » : « Lois » couvre l'immigration, la justice et
les institutions.

**Aucun seuil ne décide qu'il y a une tendance.** `laurent-wauquiez` a 4 et 4 à
égalité en tête : il n'y a pas de tendance, et ce n'est pas nous qui le décidons.

## 5. Les votes sont sortis du bloc

**Arbitrage rendu le 02/09/2026, après trois tentatives mesurées.** La question
posée était : *« qu'est-ce qu'un lecteur peut en sortir ? »* Réponse : rien.

| Piste | Verdict |
| --- | --- |
| La répartition brute | dit ce que la posture disait déjà — « 103 pour sur 111 » chez un député de la majorité |
| Le compte des écarts à sa posture | **interdit** — indice individuel par une autre route (§2 règle 7) |
| Les scrutins nommés | ne passe pas l'échelle — 6 chez Attal, **46** chez Le Pen |
| Un thème des textes votés | **impossible** — aucun rattachement sourcé (#639, écarté) |
| Une part des scrutins auxquels il a participé | **interdit** — taux d'assiduité (§2 règle 3) |

Ce qui reste publiable — **un scrutin nommé, avec son objet et la position du
groupe à côté** — demande de la place et du contexte : c'est une **section**, pas
une ligne de tableau de bord. La ligne d'introduction renvoie donc les votes plus
bas au lieu de les taire.

**Un fait a failli être publié faux, et c'est ce qui a ouvert #711.** `gabriel-attal`
a voté **contre l'ensemble du projet de loi de simplification de la vie
économique** en première lecture (17/06/2025), texte que son gouvernement avait
déposé quand il était Premier ministre (24/04/2024). Mais la loi a été adoptée
sur le **texte de la commission mixte paritaire** le 14/04/2026, scrutin où
**aucune position de lui n'est enregistrée** — et on ne peut pas dire pourquoi,
ce serait publier une absence individuelle. Sans la règle « dernière lecture »
d'`AGENTS.md` §6, que rien n'implémente, la page affirmait qu'il avait voté
contre sa propre loi.

### Un constat de corpus, mesuré, qui ne peut pas être publié tel quel

Sur les dernières lectures : `jerome-guedj` (opposition) vote **pour 74 %** des
textes finaux, `marine-le-pen` **55 %**, `laurent-wauquiez` est à l'équilibre
(61 contre / 58 pour). **Un député d'opposition ne vote pas majoritairement
contre** — seul `jean-luc-melenchon` correspond au cliché, à 74 % contre.

C'est un fait de corpus, pas une donnée de fiche : le publier sur une page
individuelle supposerait une comparaison aux autres. Il est consigné ici parce
qu'il a coûté une mesure et qu'il oriente les vues à venir.

## 6. Les colonnes sont conditionnelles, et il y a trois cas

| Cas | Profils | Rendu |
| --- | ---: | --- |
| Les deux rôles | 6 | deux colonnes |
| **Parlement seul** | `jean-luc-melenchon`, `marine-le-pen`, `jerome-guedj`… | **une colonne pleine largeur** |
| **Ni l'un ni l'autre** | `david-lisnard`, `jordan-bardella`, `marine-tondelier`, `nathalie-arthaud` — **4 sur 13** | **le bloc n'a rien à montrer** |

**Le troisième cas n'est pas tranché.** Bardella a un mandat européen, Lisnard
est maire : deux formes d'activité que ce gabarit ignore. L'arbitrage —
introduire le travail européen et municipal, ou retirer le bloc de ces fiches —
est ouvert, et la propriétaire le tient pour un gros chantier.

## 7. Emplacement dans la page

**Le bloc reste en tête, mais devient une section repliable** que le lecteur
déroule ou non. Il est dense — c'est assumé, c'est un tableau de bord — et il ne
doit pas s'imposer avant que le lecteur ait choisi de le lire.

## 8. Ce qui bloque l'implémentation

- **#710** — 13,8 % des sujets d'intervention publiés sont des intitulés de
  séance. Tant qu'il n'est pas livré **et qu'un run n'a pas passé**, aucune ligne
  de thème n'est utilisable : les questions de `gabriel-attal` sont à 98 % sous
  « Questions au Premier ministre », celles de `jerome-guedj` sous « Questions au
  gouvernement ».
- **#711** — la règle « dernière lecture » n'est implémentée nulle part.
- **#700 / #708** — les fiches de groupe de la XVIIᵉ et les 156 membres écartés :
  sans eux, la posture reste non renseignée sur les mandats en cours.

## Alternative écartée

**Deux gabarits, l'un pour les profils qui ont alterné, l'autre pour les
autres.** Tentant, et refusé : deux gabarits rendent deux fiches incomparables,
ce que la garantie par rôle cherchait précisément à éviter. Le gabarit est
unique ; ce sont les **lignes et les colonnes** qui apparaissent ou non, selon ce
que la donnée porte.
