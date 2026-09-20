# Suite du 26/08/2026 : les trois archives vérifiées, les deux défauts de parseur corrigés

`2026-08-26`

> **En bref** — les trois archives Syceron vérifiées au `content-length`, et les deux défauts de parseur (traversée, titre de point) corrigés.

Les **trois** archives de `SYCERON_AVAILABLE_LEGISLATURES` ont été téléchargées
et vérifiées au `content-length` (148 954 869 / 57 553 703 / 55 772 428 octets,
2 768 comptes rendus). Ce que le 20/08 n'avait pas pu faire, faute d'une source
qui répondait.

## La forme de l'identifiant est la même sur les trois

| Législature | Comptes rendus | `identifiant_nu_prefixe` | `forme_inattendue` | `id_acteur == "PA"+id` |
| --- | ---: | ---: | ---: | ---: |
| 15 | 1 562 | 633 764 | **0** | 636 594 / 638 901 |
| 16 |   605 | 305 862 | **0** | 307 086 / 307 403 |
| 17 |   601 | 287 789 | **0** | 289 015 / 289 016 |

**Aucune archive ne publie l'identifiant préfixé**, et aucune n'en publie une
forme que le code ne reconnaît pas. Le préfixage vaut donc pour les trois, et le
compteur-témoin reste à zéro là où il a été mesuré — ce qui était exactement le
point à lever avant toute activation.

## Ce que la source refuse d'attribuer, et qu'on ne force pas

Les 2 625 paragraphes où `id_acteur` **contredit** le préfixage sont désormais
écartés, sous le motif `attribution_refusee_par_la_source`. 2 592 portent
`id_acteur="PA0"` — l'orateur collectif — et **2 524** d'entre eux ont un
`<nom>` qui cite *deux* orateurs (« M. André Chassaigne et M. Jean-Paul Lecoq »)
là où `<orateur><id>` n'en porte qu'un. Retenir le premier fabriquerait une
prise de parole (§2 règle 2) ; c'est l'arbitrage que
`parse_syceron._parse_orateur` applique déjà aux orateurs multiples. Comme les
trois autres rejets, celui-ci est **compté, pas signalé par entrée** (#474).

## Défaut nº1 : le parcours voyait 12,5 % du débat, pas un tiers

Le diagnostic du 20/08 était juste mais sous-estimé, et sur la mauvaise cause
unique. Deux mécanismes se superposent dans la source, et le parcours n'en
suivait aucun :

1. **`nivpoint` n'est pas l'imbrication XML.** Les points de niveau 1, 2 et 3
   (1 749 + 5 085 + 4 831 sur la 17e) sont des **frères** à la profondeur XML 1,
   tous titrés ; les niveaux 4 et 5 (16 300 + 1 347) sont, eux, **imbriqués**
   jusqu'à la profondeur 9 — et **jamais titrés**. Un paragraphe de niveau 4 ne
   se rattache donc à son sujet ni par ses ancêtres XML seuls, ni par `nivpoint`
   seul. Il faut une pile de titres alimentée en ordre de document, à laquelle
   l'imbrication se superpose.
2. **Les paragraphes ne sont pas tous enfants d'un `<point>`.** Un conteneur
   intermédiaire non documenté, `<interExtraction>`, porte **86 163 des 103 213**
   paragraphes d'un échantillon de 200 comptes rendus de la 15e. C'est lui qui
   explique l'essentiel de l'écart, et c'est pourquoi la 15e était la plus
   touchée.

Mesure du parcours d'origine, sur les trois archives : **180 755 des 1 444 564**
paragraphes vus, soit **12,5 %** — 29 194 / 788 095 sur la 15e (3,7 %),
41 933 / 335 800 sur la 16e (12,5 %), 109 628 / 320 669 sur la 17e (34,2 %). Le
périmètre, lui, est inchangé : on reste « sous un `<point> `»,
`<ouvertureSeance>` et `<finSeance>` restent hors champ. Le parcours corrigé
n'élargit pas la portion retenue, il atteint celle qui était déjà déclarée.

## Défaut nº2 : le sujet, et pourquoi le titre de point n'en est pas un

`<titreStruct>` sous `<contenu>` : **0 occurrence sur les 162 073 points** des
trois législatures. Confirmé, et le titre vit bien dans `<point><texte>`.

Le `<metadonnees><sommaire>`, que le 20/08 désignait comme « le vrai sommaire
thématique », **n'apporte rien** : mesuré sur la 17e, son `<intitule>` est
rigoureusement le `<point><texte>` du point qu'il référence sur **12 035 des
12 038** jointures par `id_syceron`. Il n'est donc pas lu — une piste écartée
par la mesure, pas par principe.

Ce qui sépare un titre de matière d'un intitulé de procédure est **structurel** :
c'est le `code_grammaire` du point, vocabulaire contrôlé de la source. Sur les
30 322 points de la 17e, trois codes seulement portent un titre de matière —
`TITRE_TEXTE_DISCUSSION` (1 093 : « droit à l'aide à mourir », « projet de loi
de finances pour 2026 »), `QG_1_1` (1 804 : « crise agricole », « prix des
carburants »), `QOSD_1_1` (815 : « permis de conduire », « zéro artificialisation
nette »). Tous les autres titrés sont procéduraux : `DISC_ARTICLES_*`,
`SUSP_SEANCE_1_1`, `RAP_REGLEMENT_1_1`, `DISC_GENERALE_1`, `PRESENTATION_1_0`,
`VOTE_ENS_*`, `FIN_SEAN_1_2`, `SOUS_TITRE_TEXTE_DISCUSSION`.

`sujet` prend donc le titre du point **titré porteur de sujet le plus profond**,
et `None` sinon — `None` est un résultat, pas un défaut (§2 règle 5), et
publier « suspension et reprise de la séance » (1 009 occurrences) comme thème
violerait la règle 8. Le titre reste lisible dans `point_ordre_du_jour`, qui
devient la **chaîne** des points englobants (« Lutte contre les fraudes sociales
et fiscales > Discussion des articles (suite) > Article 9 terdecies ») : du
contexte traçable, pas un thème. `type_detail` suit la même logique — le
`code_grammaire` d'abord (`QG_1_1` → `question_gouvernement`), la regex sur les
titres seulement en repli.

Résultat : `sujet` est renseigné sur **88,0 %** des 1 227 415 interventions
indexables (84,8 % sur la 15e, 93,9 % sur la 16e, 88,9 % sur la 17e), contre
**0 %**. Un second compteur-témoin est armé sur ce chiffre : un index dont
*aucune* entrée ne porte de sujet est annoncé, parce que c'est précisément
l'état que #510 avait laissé, invisible faute que rien ne le dise (§2.5).

## Les fixtures inventées sont retirées, pas seulement dépréciées

`syceron_minimal.xml` et `syceron_missing_fields.xml` sont **supprimées**. Les
laisser en place « pour la robustesse » revenait à garder sous test un schéma que
l'AN ne publie pas — c'est la cause commune de #510 et de ses deux défauts de
parseur, et le 20/08 ne l'avait désarmée qu'à moitié. `tests/test_parse_syceron.py`
est réécrit sur deux **réductions verbatim** de comptes rendus réels, obtenues en
supprimant des frères et jamais en écrivant du balisage :

- `syceron_reel_leg17_structure.xml` (CRSANR5L17S2026O1N187) : points frères de
  nivpoint 1, 2 et 3, point imbriqué de nivpoint 4 non titré, `<interExtraction>`,
  les codes porteurs de sujet et ceux qui ne le sont pas, et un
  `<metadonnees><sommaire>` réel ;
- `syceron_reel_leg17_attribution_refusee.xml` (CRSANR5L17S2026O1N015) : l'unique
  cas de la 17e où `id_acteur` contredit le préfixage.

## Le drapeau reste INACTIF — et la correction a renchéri l'activation

Corriger le parseur n'a pas rapproché l'activation, il l'a éloignée : la charge
a été multipliée par ~7,5. Mesures refaites sur les trois archives complètes, en
mode actif (construction puis relecture, RSS maximum du process) :

| Législature | Index sur disque | Construction | Relecture / candidat | RSS à la relecture |
| --- | ---: | ---: | ---: | ---: |
| 15 | **866,2 Mio** | 81,1 s | **6,40 s** | 3 838 Mio |
| 16 | **410,5 Mio** | 34,5 s | **3,21 s** | 1 825 Mio |
| 17 | **388,1 Mio** | 32,0 s | **2,91 s** | 1 745 Mio |
| **total** | **1 664,8 Mio** | **147,6 s** | **12,52 s** | — |

Confrontation aux trois chantiers, refaite :

- **#500** (240 s par candidat) : l'index est relu **à chaque candidat et pour
  chaque législature**, soit **12,5 s par candidat** — 5,2 % du budget consommés
  avant d'avoir collecté quoi que ce soit, et un pic de **3,8 Gio de RSS** sur la
  seule 15e. Le remède reste celui des amendements et des scrutins
  (`_scrutins_shard_path_acteur`, #392/#403) : **une tranche par acteur** au lieu
  d'un index monolithique. **Toujours pas fait** — c'est le dernier verrou
  technique de l'activation, et il n'est pas dans #510.
- **#505** (cache calibré sur un index de 2 octets) : la clé de la semaine
  porterait **1,66 Gio**. À revalider avant, pas après.
- **#429** (volumétrie) : 1 227 415 interventions indexables contre **789**
  publiées aujourd'hui. La projection à 752 membres n'en compte aucune.

En mode **inactif** — celui de la production — le coût reste celui d'un parcours
d'archive à froid : 21,8 s pour la 17e (contre 16,2 s), une fois par législature
et par semaine, pour un index de 2 octets toujours mis en cache et toujours
annoncé.

**Ce qui reste à faire avant d'activer**, dans l'ordre : la tranche par acteur,
puis une mesure de l'effet sur le poids des profils et sur les agrégats de
groupe, puis la revalidation du cache. La décision elle-même reste celle d'un
opérateur, en connaissance de ces chiffres.

## Ce qui n'est toujours PAS vérifié

- que les acteurs indexés couvrent bien tous les députés en exercice de chaque
  législature ;
- l'effet sur les agrégats de groupe (`group_profile`) d'une multiplication par
  ~1 500 du volume d'interventions du corpus ;
- l'effet sur le poids des profils publiés : la mesure du 20/08 (+20,3 Mio de
  pivot pour la 17e seule) portait sur 104 239 interventions, il y en a
  désormais 1 227 415 sur les trois — elle est à refaire, et elle ne peut l'être
  qu'en régénérant le corpus.

## Garde-fous

`tests/test_syceron_acteur_ref.py` : la forme réelle de l'archive, la
normalisation cas par cas — attribution refusée comprise —, la garde §2.5 sur
index vide, le parcours des points imbriqués, le remplissage de `sujet`, le
compteur-témoin d'un index sans aucun sujet, et le refus de réintroduire les
fixtures inventées. `tests/test_parse_syceron.py` (27 tests) : le parcours et le
sujet, mesurés uniquement sur des réductions verbatim de l'archive.

**Ce qui précède décrit l'état livré INACTIF.** Le drapeau a été levé et le repli
retiré le 27/08/2026 : ce qui reste vrai (mesures d'archive, forme de
l'identifiant, défauts de parseur) et ce qui ne l'est plus (les deux modes, les
deux fichiers d'index, l'inactivité par défaut) sont départagés par la section
[#syceron-actif-510](syceron-actif-510.md).

---

