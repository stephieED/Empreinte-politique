# Un pied de site, un badge qui dit ce qu'il fait, et §6 qui cesse de répéter le corpus (#328) — 09/09/2026

`2026-09-09`

> **En bref** — trois défauts de la même famille, tous mesurés sur la page rendue : **il y avait trois pieds** — accueil, explorateur, et **rien du tout** sur les pages statiques —, donc un contact absent de la méthodologie, des mentions légales et de la couverture ; un **seul composant** les remplace sur les quatre carcasses, **l'adresse écrite en entier** parce qu'elle se copie (coût mesuré et assumé : le pied passe de 66 à **148 px** partout), **les pages en mots et les comptes en icônes** — la forme dit la nature du lien —, chaque icône gardant son `aria-label` en toutes lettres et une cible de 30 px : elle remplace le libellé **à l'écran**, jamais pour un lecteur d'écran ni pour le doigt ; **le badge cesse de dire « vérifiée »**, un contrôle que nous ne faisons pas — et **« Source officielle » a été écarté sur mesure** : sur les 23 499 liens publiés des 32 fiches candidats, 19 fiches de groupe et 10 fiches de gouvernement, 22 988 pointent vers l'Assemblée ou le Parlement européen mais **511 vers nosdeputes.fr**, un tiers — le mot aurait été faux 511 fois, quand « Lien de source non publié » ne bouge pas parce qu'il parle de NOUS ; **§6 rend l'état daté et plus la borne**, dont le discriminant est l'**état** garanti par `couverture_profil._deriver` et non une reconnaissance du texte (#639) — partition exacte sur les 32 fiches, **180 entrées de borne sur 286, soit 6 413 des 8 328 mots rendus** ; **la mémoire des preuves devient celle de la SECTION, ce qui renverse #802**, dont la raison — ne pas faire disparaître la borne AMO30 de « Votes » — tombe avec la borne, et ce qui restait se répétait cinq fois pour rien : **700 mots sur la fiche Retailleau**, 140 par liste pour le seul certificat de suspension ; **deux affirmations retirées parce que fausses** — « rangés sous le même rôle « auteur » … aucun champ ne la porte », alors que `role` sépare projets et propositions sur **570 des 575** et que la phrase était publiée **deux fois**, et « dont la législature en cours », écrit en dur et vérifié nulle part (faux sur Retailleau) ; le **bloc Assiduité / Classement / 49.3 quitte la fiche**, « aucun classement » y apparaissant **trois fois** sur une même page ; mesuré après : Retailleau 870 → **237** mots, Tondelier 441 → **133**, Mélenchon 358 → **185**, et « aucun classement » 3 → 1, « taux de présence » 2 → 0 ; **alternative écartée** — replier les bornes derrière un `<details>`, zéro risque et défaut intact, la borne n'étant pas trop longue mais **au mauvais endroit**. 12 tests neufs, suite complète à 4 324, 0 échec.

## Contexte

Trois défauts de la même famille, tous mesurés sur la page rendue.

**Le pied.** Il y en avait trois — `landing-footer` sur l'accueil, `explorer-footer`
sur les vues de profil, et **rien du tout** sur les pages statiques. Le contact et
les deux comptes étaient donc absents de la méthodologie, des mentions légales et
de la page de couverture. Trois pieds pour un même site sont trois pieds qui
divergent, et une adresse absente d'une page sur deux est une adresse qu'on
n'écrit pas.

**Le badge « Source vérifiée ».** Il affirme un contrôle que nous ne faisons pas.
`sourceBadge(url)` est vrai quand un `source_url` existe et qu'il est publié : le
badge est ce lien, rien d'autre.

**§6 répétait le corpus, et se répétait.** Sur `delphine-batho`, « aucun
classement » apparaissait **trois fois** sur la même page — le bloc des refus en
§6, le pied de la fiche juste en dessous, le pied du site. Et les preuves de borne
pesaient **6 413 des 8 328 mots** rendus sur les 32 fiches : elles disent ce que
l'Assemblée publie, jamais quoi que ce soit sur la personne affichée.

## Décision

### Un seul pied, sur les quatre carcasses

`PiedDeSite` remplace les trois. Trois colonnes : la marque et la phrase
éditoriale, les pages du site, « Nous joindre ». **L'adresse s'écrit en entier** —
elle se copie, elle se retient, elle ne demande ni survol ni clic. Coût mesuré et
assumé : le pied passe de 66 à **148 px**, sur toutes les pages.

**Les pages sont des mots, les comptes sont des icônes.** La forme dit la nature
du lien : un mot mène à une page du site, une icône ouvre autre chose. Chaque
icône garde son `aria-label` en toutes lettres et une cible de 30 px — elle
remplace le libellé **à l'écran**, jamais pour un lecteur d'écran ni pour le doigt.

Le pied ne porte pas « aucun taux de présence individuel ». La règle §2 n° 3 reste
publiée — méthodologie, « Ce que vous ne trouverez pas ici », FAQ de l'accueil —,
mais elle était répétée jusqu'à trois fois sur une même fiche.

### Le badge dit « Source », et rien de plus

**« Source officielle » a été écarté sur mesure.** Sur les **23 499 liens publiés**
des 32 fiches de candidats déclarés, des 19 fiches de groupe et des 10 fiches de
gouvernement :

| Hôte | Liens | |
| --- | --- | --- |
| `data.` / `www.` / `questions.assemblee-nationale.fr`, `europarl.europa.eu` | 22 988 | officiel |
| `nosdeputes.fr` (456 + 55) | **511** | tiers — Regards Citoyens |

Le mot aurait été faux 511 fois — exactement les 511 que la clause ODbL d'AGENTS.md
§7 nomme. Son pendant, « Lien de source non publié », ne bouge pas : il parle de
NOUS, quand « non vérifié » ferait porter le doute sur la donnée.

Que la source fasse foi **parce qu'elle est institutionnelle** est une phrase vraie
et argumentée : elle se dit une fois, en méthodologie et dans le bloc Sources de
l'accueil, jamais en trois mots répétés sous chaque fait.

### §6 : la borne part, l'état daté reste

Le discriminant est l'**état**, et il est garanti à la source — pas reconnu au
texte, ce qui serait une jointure par ressemblance (#639). `couverture_profil._deriver`
attache `borne.preuve` à `couvert` et `hors_couverture`, et bascule sur
`fait_etabli` dès que la preuve devient propre à la personne.

| État | Preuve | Occurrences | Devient |
| --- | --- | --- | --- |
| `couvert` + `hors_couverture` | la borne de source | **180** | l'état daté reste, la preuve part sur `/couverture` |
| `fait_etabli` | aucun acteur AMO30 pour cette personne | 75 | reste |
| `non_collecte` | collecte écartée, groupe suspendu | 31 | reste |

Partition exacte, zéro exception sur les 32 fiches.

**La mémoire des preuves devient celle de la section**, ce qui renverse #802 : ce
dédoublonnage avait été limité à la liste parce qu'une mémoire partagée aurait fait
disparaître la borne AMO30 de « Votes » après que « Mandats » l'avait écrite. Cette
raison tombe avec la borne. Ce qui reste est propre à la personne ou au run,
identique d'une liste à l'autre, et se répétait cinq fois pour rien — **700 mots
sur la fiche Retailleau**, dont 140 par liste pour le seul certificat de suspension
Sénat/LR.

### Deux affirmations retirées parce qu'elles sont fausses

**« Rangés sous le même rôle "auteur" … aucun champ ne la porte. »** Mesuré sur les
textes portés des 32 fiches : `role` sépare projets et propositions sur **570 des
575** — `initiateur_projet_de_loi` (313) contre `auteur_proposition_de_loi` (183) et
`auteur_proposition_de_resolution` (59) ; les 5 restants portent `auteur` sans
`nature_texte`. La phrase était publiée **deux fois**, en §2 et en §6. Le fait vrai
— combien de textes sont des projets de loi signés comme ministre — reste sous la
cascade de « Ce qui est proposé ».

**« dont la législature en cours »** était écrit en dur dans la phrase de
qualification de groupe et vérifié nulle part : sur Bruno Retailleau, dont le mandat
à l'Assemblée est clos, la fiche l'affirmait quand même (§2 règle 2).

Au passage, trois accords cassés à *n* = 1 (« aucun de ses 1 mandats électifs »), et
la limite de qualification qui ne se déclenche plus quand elle porte sur l'unique
mandat d'un profil — ce n'est pas une lacune de corpus, c'est la situation ordinaire.

Et l'en-tête réduit porte **« Empreinte politique »**, pas « Empreinte » : c'est le
moment où le lecteur n'a plus le logo sous les yeux.

## Mesuré après

| Fiche | §6 avant | §6 après |
| --- | --- | --- |
| `bruno-retailleau` | 870 mots | **237** |
| `marine-tondelier` | 441 | **133** |
| `segolene-royal` | 414 | **146** |
| `edouard-philippe` | 414 | **171** |
| `jean-luc-melenchon` | 358 | **185** |
| `delphine-batho` | 353 | **180** |

Et sur la page entière : « aucun classement » passe de 3 occurrences à 1, « taux de
présence » de 2 à 0.

## Alternative écartée

**Replier les preuves de borne derrière un `<details>`.** Zéro suppression, aucun
risque de perdre un fait. Mais les 260 mots restent sur la page — DESIGN_SYSTEM §7
règle 2 dit qu'« une limite tient en deux mots, une explication en paragraphe », et
un paragraphe replié reste un paragraphe. Surtout, le repli n'aurait rien réglé du
vrai défaut : la borne n'est pas trop longue, elle est **au mauvais endroit**.

**Ajouter « aucun taux de présence individuel » au pied du site** plutôt que de le
laisser tomber avec le pied de fiche. Écarté par la propriétaire : la règle reste
publiée trois fois ailleurs, et un pied qui récite les interdits sur chaque page
les banalise.
