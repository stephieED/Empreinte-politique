# Faisabilité : ce qui est disponible, dérivable, à pré-agréger, ou à collecter

**Issue #595** — temps 3/4 de l'épic #324, débloqué par le temps 2
(`audit/propositions-visualisations-20260831.md`). Chaque vue proposée au temps 2
reçoit ici **une** case, et chaque coût est **mesuré**, jamais projeté.

> **Épinglage.** Toutes les mesures portent sur le commit `4dda4d52`
> (`origin/main` au 31/08/2026, 12h05 UTC), lu par `git show` — jamais sur
> `pivot_data/` sur disque. Un run `generate-data.yml` était en cours pendant la
> mesure et réécrit cette couche : les chiffres ci-dessous ont une **base
> nommée**, et §1 dit lesquels le run va changer.

| | Ce que ça veut dire | Ce que ça coûte |
| --- | --- | --- |
| **A. Disponible** | le champ est publié et couvert | rien |
| **B. Dérivable côté client** | calculable dans le navigateur, sur ce que la page charge déjà | rien |
| **C. À pré-agréger par le pipeline** | calculable, mais pas dans un navigateur | un chantier `src/*.py` + schéma |
| **D. À collecter** | la donnée n'existe pas | un chantier de collecte, hors de cette épic |

**Les deux populations restent la clé de lecture.** Les 481 profils publiés sont
**13 `candidat_declare`** et **468 `roster_groupe`** — vérifié à `4dda4d52`. Un
chiffre sur 481 mélange les deux et ne veut rien dire.

---

## 0. Le résultat, en un tableau

| Case | Vues | Ce qu'il faut pour les servir |
| --- | ---: | --- |
| **A. Disponible** | **11** | rien — le champ est publié, personne ne le lit |
| **B. Dérivable côté client** | **9** | rien — mais 6 portent une **fragilité mesurée** ou sont bloquées, voir §2 |
| **C. À pré-agréger** | **3** vues, **4** agrégats | **+301 Kio de corpus et +16 s de run, mesurés** — et le gain est négatif en volume servi |
| **D. À collecter** | **4** | 4 issues hors épic, §5 |
| **Différé par arbitrage** | **2** | conditions déjà écrites, à ne pas rouvrir |

Le badge du §7 n'est pas compté : il se répartit sur cinq objets, dont trois sont
en **A**, un en **B** bloqué et un en **D**.

**La conclusion qui surprend : la case C ne coûte presque rien, et elle *rend* de
la place.** Le site sert aujourd'hui l'index d'amendements au navigateur pour y
recalculer des compteurs à chaque affichage ; pré-agréger les supprime des deux
côtés. Le détail chiffré est en §3.

---

## 1. Ce qui a bougé depuis le temps 2 — et pourquoi

Le temps 2 mesurait à `e6af1a00`. **Vingt-et-une grandeurs re-mesurées se
reproduisent à l'unité**, huit s'écartent — six pour une cause identifiée, deux
sans. **Deux tableaux ne se reproduisent pas du tout**, et c'est en §6.

### Les reproductions exactes

`8 860` positions et `55 288` signatures d'amendement et `16 242` interventions
sur les 13 candidats déclarés · `1 331` tags · `9 950 / 55 288 (18,0 %)` de sort
non renseigné · `484 132` amendements dans l'index · `0 / 484 132` avec
`source_url` · `66` motions de censure du **20/03/2013 au 06/07/2026, 1 adoptée**
et leur ventilation (Le Pen 33, Guedj 24, Mélenchon 5, Wauquiez 4, Philippe 3,
Bertrand 3, Attal 1) · `113 reaction_courte / 101 développées` sur les
explications de vote · `719` libellés de questions au gouvernement ·
`1 374 o` par intervention · `39,7 %` d'exécutif et `53,6 %` de réactions courtes
et **la ventilation par candidat des cinq lignes du §4.5** · `24 / 481` profils
sans profession · `725 / 725` textes de gouvernement sourcés et `67` promulgués ·
`comptages` de `BORNE` (**19 promulguées, 111 suivis, 43 en navette, 6 en 49.3**) ·
les `470 / 382 / 197 / 0 / 0` tags des fiches de groupe, **tous à
`nb_membres_porteurs: 1`** · les 5 nombres de scrutins agrégés des fiches AN.

### Les sept écarts

| Grandeur | Temps 2 | À `4dda4d52` | Cause |
| --- | ---: | ---: | --- |
| `mandats` du corpus | 41 110 | **41 723** | **#640** livré : +613 mandats électifs |
| `mandat_electif` | 511 | **1 124** | idem, +613 |
| `mandats` avec `source_url` | 1 302 | **1 915** | idem, +613 — les 613 en portent tous un |
| `position_dans_hemicycle` | 1 024 / 41 110 | **1 024 / 41 723** | numérateur inchangé, dénominateur porté par #640 |
| `textes_portes` du corpus | 472 | **940** | **doublement exact ×2**, voir ci-dessous |
| `couverture` des 13 candidats | 113 entrées | **112** | **non expliquée** |
| `meta.warnings` des 13 candidats | 26 | **24** | **non expliquée** |
| chef manquant sur les fiches de gouvernement | 7 / 10 | **6 / 10** | **#658** livré (libellé au féminin) |

**Le doublement des textes portés est mécanique, et le comptage distinct reproduit
le temps 2.** 846 entrées sur les 13 candidats déclarés pour **423 distinctes** —
un doublement exact, `source_url` peuplé sur exactement la moitié. 94 entrées sur
les 468 membres de roster pour **49 distinctes** : 45 paires et 4 entrées uniques.
La fusion a ajouté l'entrée de forme neuve (#639 rang 2, avec sa source) **à côté**
de l'ancienne au lieu de la remplacer. Le run en cours ramène 940 à **472**
(reprise #668), et les deux chiffres du temps 2 — 423 et 49 — sont les bons.

### Les cinq points en vol, et ce qu'ils bloquent

| Sujet | État vérifié à `4dda4d52` | Vues concernées |
| --- | --- | --- |
| **#657** — interventions des 468 membres de roster | **0 / 468**, confirmé | §5.5 empreinte thématique |
| **#641** — professions en code de nomenclature | **5 profils**, tous `roster_groupe`, **0 des 13 candidats** | **aucune page candidat** — voir §2 |
| **#639 rang 1** — `type_scrutin` | **`null` sur 17 748 / 17 748**, et `type_vote` vaut `vote_texte` sur 17 748 / 17 748 | §4.2, §4.3, §5.0 |
| **#639 rang 4** — scrutin → dossier | différé, condition écrite | §2.5, §4.2 |
| **#668** — textes portés | doublement ×2 confirmé | §4.4, §7 |

**#641 ne bloque aucune page.** Les 5 profils qui publient
`(85) - Personne diverse sans activité professionnelle` — `benedicte-auzanot`,
`frederic-boccaletti`, `julie-lechanteux`, `laure-lavalette`, `sylvie-ferrer` —
sont **tous des membres de roster**, dont aucun n'a ni ne doit avoir de page. Le
défaut reste réel ; il n'est pas sur le chemin des 13 pages de candidat.

**#639 rang 1 coûte plus que `type_scrutin`.** Les index figés portent aussi
`type_vote: motion_censure` (**43** sur les 9 876 scrutins des législatures 14-16)
et `demandeur` — **ni l'un ni l'autre n'atteint le pivot**. Ce qui répond à la
troisième question ouverte du dernier commentaire de #639 : oui, `demandeur` subit
le même sort, `pivot_data/scrutins.json` ne porte pas la clé.

---

## 2. Les vues, une par une

### 2.1 · Profil candidat — 13 pages

| § | Vue | Case | Sur quoi, mesuré |
| --- | --- | :---: | --- |
| 4.0 | Coup d'œil — identité, qualité, mandat en cours et précédent | **A** | `identite` peuplé sur 9 / 13 candidats ; `mandats` sur 10 / 13. **Pas touché par #641** |
| 4.0 | Décompte P/C/A sur les lois votées dans leur ensemble | **B** ⚠ | `scrutins.json` est déjà chargé par la page (0,46 Mo gzip). Sélection par **reconnaissance de libellé** — fragile, voir ci-dessous |
| 4.0 | Les 3 lois les plus récentes | **B** | `votes[].scrutin_id` × `scrutins.json`, `date` peuplée 17 748 / 17 748 |
| 4.1 | Le mandat en une phrase, et l'absence de mandat | **A** | `mandats[].categorie`, `debut`, `fin`, `actif` ; 4 des 13 candidats sans `profession`, dit comme tel |
| 4.2 | Les lois votées + le critère de tri (nb de scrutins suscités) | **B** ⚠ | le critère est un décompte sur `scrutins.json`. Les cases « 49.3 » viennent de `comptages.par_statut` des 10 fiches de gouvernement — **0,6 Mo au total**, chargeables |
| 4.3 | Les 66 motions de censure, datées et avec leur sort | **B** ⚠ | `sort` peuplé 17 748 / 17 748 ; **66 / 66 retrouvées** par reconnaissance de libellé. **Deviendrait A** avec #639 rang 1 |
| 4.4 | Textes portés × périodes de mandat | **B** 🚫 | tout est dans le profil (`date_min`/`date_max` × `mandats[].debut`/`fin`). **Bloquée tant que le doublement ×2 n'est pas repris** : la page compterait 566 textes pour Philippe au lieu de 283 |
| 4.5 | Interventions — sujets, ventilation exécutif / format | **A** (13 candidats) · **D** (468 roster) | `source_url` 16 242 / 16 242, `type_detail` 100 %, `format` 100 %, `fonction` 39,7 %. **0 / 468** sur le roster (#657) |
| 4.6 | Amendements — sort, ratio à dénominateur explicite, bande « non renseigné » | **C** | c'est **l'agrégat C1**, §3 |
| 4.7 | Onglet « Données » — couverture, avertissements, fraîcheur | **A** | `couverture` sur **481 / 481**, 112 entrées sur les 13 candidats, 24 avertissements sur 12 d'entre eux, `genere_le` et `provenance` publiés. **Aucun composant n'en lit un seul** |
| 2.5 | Le titre complet, la séquence des scrutins du même texte | **B** ⚠ | `texte` peuplé 17 748 / 17 748 ; le regroupement par libellé est **permis** (§2.6) |
| 2.5 | L'explication de vote à côté du vote | **différé** | 101 développées publiées, mais rapprocher une intervention Syceron d'un scrutin d'archive est une **jointure entre sources** — `regrouper-nest-pas-joindre-639.md` |
| 2.5 | Le lien vers le dossier AN comme sortie | **A** sur amendements et gouvernements · **indisponible** sur votes et interventions | `dossier_id` : **725 / 725** textes de gouvernement, **1 792** textes de l'index d'amendements. Les interventions portent `dossier = {point_ordre_du_jour}`, **pas un identifiant** ; les scrutins n'en portent aucun (rang 4 différé) |

### ⚠ La fragilité qui touche cinq vues : la reconnaissance de libellé

Cinq des vues ci-dessus sélectionnent les scrutins « portant sur l'ensemble d'un
texte » en cherchant `l'ensemble` dans `scrutins.json.texte`. **Cette sélection
dépend de la forme de l'apostrophe, et l'écart est mesurable :**

| Motif | Scrutins retenus |
| --- | ---: |
| sous-chaîne `l'ensemble` n'importe où, apostrophe ASCII | **916** |
| sous-chaîne `l’ensemble` n'importe où, apostrophe typographique | **22** |
| **union des deux, sous-chaîne** | **938** |
| en tête de libellé, apostrophe ASCII | **910** |
| en tête de libellé, apostrophe typographique | **22** |
| **union des deux, en tête** | **932** |

*Recontrôlé le 31/08/2026 par l'agent principal, à `4dda4d52` et à `957a9efa` —
valeurs identiques aux deux SHA. Les deux lignes de sous-chaîne reproduisent la
mesure d'origine ; les trois lignes « en tête » sont ajoutées, parce que l'écart
entre les deux motifs est lui-même un défaut.*

**L'apostrophe fait perdre 22 scrutins. Le motif naïf en fait gagner 6 qui n'ont
rien à y faire.** Les deux erreurs sont de sens contraire et ne se compensent pas :

| Ce que le motif naïf produit | Nombre | Nature |
| --- | ---: | --- |
| Scrutins « sur l'ensemble » **manqués** | **22** | tous en législatures **16 (12) et 17 (10)**, les plus récentes |
| Scrutins **capturés à tort** | **6** | 2 votes sur un **amendement**, 2 sur un **article**, 1 **motion de rejet préalable**, 1 libellé « sur l'ensemble » interne |

Les 6 faux positifs sont éditorialement plus graves que les 22 manqués : un vote
sur un amendement ou une motion de rejet compté comme un vote sur l'ensemble d'un
texte publie une position que la personne n'a pas prise — §2 règle 4 pour la
motion, §2 règle 2 pour les autres. Un vote manqué est un vide ; un vote inventé
est une affirmation.

Les 22 manqués ne sont pas répartis au hasard : **l'apostrophe typographique
n'apparaît que dans les législatures 16 et 17**, c'est-à-dire les plus récentes.
Un motif naïf perd donc silencieusement des votes récents — exactement le
« elle rouille » que
`docs/decisions/regrouper-nest-pas-joindre-639.md` reproche à une clé dérivée d'un
libellé.

**C'est l'argument le plus concret pour #639 rang 1.** Les index figés portent
`type_scrutin` sur les 9 876 scrutins des législatures 14-16
(`public_ordinaire` 9 535, `solennel` 289, `motion_censure` 43, `tribune` 9). Une
sélection sur ce champ serait **sourcée** et ne rouillerait pas. Elle ferait
passer §4.2, §4.3 et §5.0 de **B fragile** à **A**.

### 2.2 · Profil de groupe — 7 fiches

| § | Vue | Case | Sur quoi, mesuré |
| --- | --- | :---: | --- |
| 5.0 | Coup d'œil — N lois sous quorum, position majoritaire, couverture | **B** ⚠ | `cohesion_votes` × `scrutins.json` ; **3 973 / 3 973** entrées d'`AN:LFI` résolvent dans l'index. Même fragilité de libellé |
| 5.1 | La cohésion en six nombres, jamais en barre | **A** | `pour`, `contre`, `abstention`, `absents`, `excuses`, `non_votant`, `membres_eligibles`, `quorum_atteint` publiés sur les **19 832** entrées des 5 fiches AN |
| 5.2 | Les 12 cartes deviennent une sélection déclarée | **B** | `slice(0, 12)` est déjà dans `pivotAdapter.js` ; le dénominateur à afficher est `cohesion_votes.length` |
| 5.3 | Les effectifs rapportés à une date de référence | **A** | `date_reference` (`2024-06-09`, origine `cloture_legislature`), `effectif.a_la_date_de_reference`, `membres[].present_a_la_date_de_reference` — publiés (#653) |
| 5.4 | Commissions : « y siège » ≠ « y est passé » | **A** | `mandats_agreges[].nb_membres_a_la_date_de_reference` et `nb_membres_cumul_historique` publiés (#656) |
| 5.5 | L'empreinte thématique | **D** | **0 / 468** membres de roster portent une intervention ou un tag. Voir §5 — et §4, qui infirme la prémisse |
| 5.6 | `meta` — couverture du roster, preuve, fraîcheur, seuil de quorum | **A** | `couverture_roster.etat` et `preuve` publiés sur 7 / 7 ; rien n'est lu |

### 2.3 · Profil de gouvernement — 10 fiches

| § | Vue | Case | Sur quoi, mesuré |
| --- | --- | :---: | --- |
| 6.0 | Coup d'œil — promulguées, suivis, navette, 49.3 | **A** | `comptages.par_statut` publié sur 10 / 10. Reproduit `BORNE` : 19 · 111 · 43 · 6 |
| 6.1 | `textes` — un statut ne s'affiche jamais sans sa date | **A** | `source_url` **725 / 725**, `dossier_id` **725 / 725**, `initiateurs` 723 / 725, `date_dernier_evenement` publiée |
| 6.2 | `membres` regroupés par `membre_id` | **B** | 127 entrées, `source_url` 127 / 127, `actif` 12 (toutes sur `LECORNU_II`) |
| 6.2 | Le chef du gouvernement | **A** sur 4 / 10 · **manquant** sur 6 / 10 | `premier_ministre` publié sur `ATTAL`, `BORNE`, `PHILIPPE`, `PHILIPPE_2`. #644 fermé sur verdict négatif |
| 6.3 | Une fiche de gouvernement qui sait dire pourquoi elle est incomplète | **C** | **0 avertissement et aucun bloc de couverture sur les 10 fiches.** Agrégat **C2**, §3 |
| 6.4 | « Cette loi est-elle appliquée ? » | **C puis D** | **le NOR n'est publié sur aucun des 725 textes** — un chantier pipeline précède le chantier de collecte. Agrégat **C3**, §3 |

### 2.4 · Transverse

| § | Vue | Case | Mesuré à `4dda4d52` |
| --- | --- | :---: | --- |
| 7 | Badge « source vérifiée » sur les scrutins | **A** | 17 748 / 17 748 |
| 7 | … sur les interventions des 13 candidats | **A** | 16 242 / 16 242 |
| 7 | … sur les textes de gouvernement | **A** | 725 / 725 |
| 7 | … sur les `textes_portes` | **B** 🚫 | **423 / 846** — la moitié exacte, artefact du doublement. **472 / 472 après reprise** |
| 7 | … sur les amendements | **D** | **0 / 484 132** |
| 7 | … sur les mandats | **non** | 1 915 / 41 723 (**4,6 %**) |

---

## 3. La case C : quatre agrégats, avec leurs coûts mesurés

### C1 · `amendements_agreges` par profil — l'agrégat qui porte la case

**Ce qu'il contient et à quelle vue il sert.** Les compteurs par bande de sort
(`nb_adoptes`, `nb_rejetes`, `nb_irrecevables`, `nb_retires_ou_tombes`,
`nb_sort_non_renseigne`), leur ventilation `par_type_deposant`, et le nombre de
textes visés. Il sert **§4.6** — le ratio à dénominateur explicite et la bande
« sort non renseigné ». La forme existe déjà : c'est **exactement** celle de
`amendements_agreges` des fiches de groupe, et `src/group_profile.py` calcule déjà
une contribution **par membre** (`ContributionAmendements`) — elle n'est
simplement jamais écrite dans le profil.

**Coût en volume — mesuré, en construisant le bloc sur les 481 profils :**

| Population | Bloc médian | Total |
| --- | ---: | ---: |
| 13 candidats déclarés | **645 o** | 6,0 Kio sur 27,0 Mo (**+0,022 %**) |
| 468 membres de roster | **663 o** | 294,8 Kio sur 595,2 Mo (**+0,048 %**) |
| **Corpus** | — | **+300,7 Kio sur 622,2 Mo, soit +0,047 %** |

Le plus gros profil publié pèse **6,77 Mo** ; `src/garde_fou_blobs.py` avertit à
50 MiB et échoue à 80 MiB. **Le piège de #580 n'est pas approché d'un facteur
1 000.**

**Coût en temps de run — mesuré, référence 66 min :**

| Étape | Mesure |
| --- | ---: |
| Chargement des 4 index (484 132 entrées) | **1,9 s** |
| Jointure des **6 091 732** entrées publiées des 481 profils | **14,0 s** |
| Passe autonome complète (lecture `git show` + parse comprise) | **29,0 s** |
| **Part d'un run de 66 min** | **+0,4 % en pipeline, +0,7 % en passe autonome** |

**Ce qui le rend faux s'il n'est pas recalculé.** Le bloc est une **jointure** :
il change dès que l'index d'amendements change, et l'index change à chaque
recollecte. Trois exemples déjà vus : la correction de la clé `uid` (§5), la
correction #643 qui a divisé les compteurs de groupe par 5 à 32, la recollecte du
rang 3 qui a fait passer le rattachement de 26,9 % à 98-100 %. **Un agrégat figé
qui survit à l'une de ces corrections publie un dénominateur que plus rien ne
soutient — la condition C4 de #539 mot pour mot.** Il se recalcule à chaque run,
après le pivot et avec l'index du run.

**Et le gain est négatif en volume servi.** C'est le point que le corps de #595 ne
pouvait pas voir : `web/UI_finale/scripts/sync-data.mjs` copie **déjà** les quatre
index dans `public/data/amendements/`, et `pivotAdapter.js` les joint **déjà**
dans le navigateur, deux fois, pour calculer ces compteurs à chaque affichage.

| Page de candidat | Index chargés | Sur le fil (gzip) | JSON à parser | Empreinte mémoire |
| --- | --- | ---: | ---: | ---: |
| Attal, Le Pen | 15 + 16 + 17 | 3,79 Mo | 99,1 Mo | **~522 Mio** |
| Guedj | 14 + 16 + 17 | 2,48 Mo | 64,6 Mo | **~345 Mio** |
| Mélenchon | 15 | 1,84 Mo | 48,1 Mo | **~250 Mio** |
| Philippe, Bertrand | 14 | 0,53 Mo | 13,7 Mo | **~73 Mio** |
| *toutes*, en plus | `scrutins.json` | 0,46 Mo | 8,3 Mo | **~38 Mio** |

**Les « 122 Mo » du corps de #595 ne sont pas un coût de téléchargement.** L'index
gzippe à **3,8 %** de sa taille : les quatre législatures voyagent en 4,3 Mo. Le
coût réel est l'**empreinte mémoire après parsing** — jusqu'à 522 Mio sur la page
d'Attal, ce qui n'est pas tenable sur un téléphone d'entrée de gamme. Pré-agréger
permet à `sync-data.mjs` de ne plus servir l'index du tout : **−112,7 Mo dans le
site construit**, et l'empreinte de la page retombe au profil plus `scrutins.json`.

⚠ **Un point de schéma à trancher, pas ici.** `taux_adoption` au niveau du *total*
tous déposants confondus est interdit par §6 (« Never — misleading »). Les fiches
de groupe le publient déjà, documenté comme non comparable ; sur un profil
individuel, la prudence est de ne publier `taux_adoption` que dans le seau
`depute`, et des comptes bruts ailleurs.

### C2 · Un bloc `couverture` sur les fiches de gouvernement

**Ce qu'il contient et à quelle vue il sert.** Les quatre états de `couverture`
(`couvert`, `fait_etabli`, `hors_couverture`, `non_collecte`) appliqués à
`textes` et `membres`, avec leur portée et leur preuve. Il sert **§6.3** — et il
ferme l'asymétrie que le temps 2 nomme : le profil de candidat sait dire pourquoi
il est incomplet (481 / 481 portent un bloc), la fiche de groupe aussi
(`couverture_roster` sur 7 / 7), **la fiche de gouvernement non — 0 / 10, et zéro
avertissement**.

**Coût en volume.** Le bloc médian d'un profil pèse **3 902 o** pour 8-9 entrées.
Sur 10 fiches : **~39 Kio**, contre 581 Kio publiés aujourd'hui. Négligeable.

**Coût en temps de run.** Nul en mesure : les bornes existent déjà — la constante
`GOVERNMENT_TEXTS_COVERAGE_START` est **codée en dur dans `pivotAdapter.js`**, en
miroir de `src/couverture_dossiers.py`. Le chantier consiste à publier ce que le
code sait déjà, pas à le calculer.

**Ce qui le rend faux.** Une borne d'archive qui bouge, ou un gouvernement dont
la période cesse de croiser la couverture ingérée. `FILLON_2` et `FILLON_3`
publient 0 texte parce qu'ils s'achèvent avant le 21/06/2017 : c'est **le** cas
qui doit porter une phrase, et il est aujourd'hui servi par une constante en dur
côté navigateur — une valeur figée qui survivrait à un déplacement de la borne.

### C3 · Le NOR publié sur les textes de gouvernement

**Ce qu'il contient et à quelle vue il sert.** `infoJO.referenceNOR`, la référence
officielle de la loi promulguée. Il sert **§6.4**, dont il est le **préalable** :
la jointure vers le JORF se fait sur un identifiant balisé des deux côtés, et
notre côté ne le publie pas.

**Coût en volume.** Un NOR fait 12 caractères. Le temps 2 mesure 333 des 725
textes porteurs côté source ; publié, cela fait **moins de 10 Kio sur 10 fiches**.

**Coût en temps de run.** Nul : le champ est déjà lu dans l'archive AN pour
décider du statut `promulgue`.

**Ce qui le rend faux.** Une requalification par Légifrance, ou un texte
repromulgué. Le NOR est un identifiant, pas un fait — il est stable ; c'est le
**lien** vers le décret qui ne l'est pas, et c'est pourquoi le chantier D reste
séparé (§5).

⚠ **Publier le NOR n'ouvre pas la vue.** La mesure du 31/08 la rend inexploitable :
**aucune des 188 lois promulguées depuis 2024 ne porte de lien `APPLICATION`**.
Cet agrégat rend la jointure *possible* ; il ne rend pas la vue *affichable*.

### C4 · Une borne de couverture datée sur `scrutins.json`

**Ce qu'il contient et à quelle vue il sert.** La condition de reprise, écrite
dans `docs/decisions/regrouper-nest-pas-joindre-639.md`, du rang 4 de #639 : le
rattachement scrutin → dossier se publie **le jour où `scrutins.json` sait porter
une borne de couverture datée**. Vérifié à `4dda4d52` : le fichier porte
`schema_version`, `genere_le`, `licence_donnees` et la liste — **aucune borne**.

**Coût en volume.** Quelques centaines d'octets sur un fichier de 8,25 Mo.

**Coût en temps de run.** Nul : la borne est le résultat d'un décompte que la
construction de l'index fait déjà.

**Ce qui le rend faux.** Une borne figée pendant que la couverture progresse —
c'est précisément le motif : l'AN ne renseigne `dossierRef` que depuis mars 2026,
et la couverture avance d'elle-même. Une borne qui ne se recalcule pas ferait
afficher « aucun vote rattaché » sur des lois qui en ont.

**Cet agrégat lève une condition ; il ne décide pas de la reprise.** Le rang 4
reste différé, et ce document ne rouvre pas cet arbitrage.

---

## 4. Ce qu'une mesure infirme

**Une seule, et elle porte sur la prémisse de #657.**

Le temps 2 §5.5 arbitre « peupler la donnée plutôt que retirer la vue », par une
collecte réduite au thème, au motif que « `theme_officiel` est renseigné sur
45,6 % des 16 242 interventions ». **Les 45,6 % se reproduisent exactement. Le
champ n'est pas un thème.**

Ses **536 valeurs distinctes** sur les 13 candidats déclarés sont des **intitulés
de point d'ordre du jour**, pas des sujets :

| Valeur de `theme_officiel` | Occurrences |
| --- | ---: |
| `Projet de loi de financement rectificative de la sécurité sociale pour 2023` | 531 |
| `Projet de loi de finances rectificative pour 2022` | 365 |
| `Motions de censure` | 279 |
| `Déclaration du Gouvernement et débat` | 236 |

Le champ voisin `dossier` confirme la nature de la matière : il vaut
`{"point_ordre_du_jour": "Questions au Gouvernement > Fermeture des marchés
ouverts"}`, **jamais un identifiant**.

**Ce que ça change, et ce que ça ne change pas.** Collecter ce champ sur les 468
membres de roster donnerait « sur quels textes cette personne a pris la parole »
— utile, et joignable aux textes. Cela **ne** donnerait **pas** de réponse à
« s'occupe-t-elle de la santé, de l'école, des retraites ? », qui reste la
question la plus naturelle du §1 et la seule sans donnée derrière elle. La
thématisation reste **entière**, et son report par #324 n'est pas entamé.

**Le dimensionnement de #657, mesuré sur les 16 242 interventions des 7 candidats
porteurs** (sur 13 déclarés) et projeté à 468 membres au même volume par membre :

| Forme collectée | o / intervention | Projeté sur 468 membres |
| --- | ---: | ---: |
| complète (telle qu'aujourd'hui) | 1 374 | **1,39 Gio** |
| sans le champ `texte` | 739 | 0,75 Gio |
| réduite à 6 champs | 315 | 0,32 Gio |
| `date` + `type_detail` + `theme_officiel` | **93** | **0,09 Gio** |

Le champ `texte` pèse **46 %** du poids sérialisé. La forme la plus réduite ajoute
~197 Kio par profil de roster — sans risque pour le garde-fou de #580, et sans
commune mesure avec la forme complète.

---

## 5. La case D : quatre chantiers, hors de cette épic

Une issue par chantier, avec sa couverture mesurée à `4dda4d52`. **Aucune n'est
ouverte par ce lot** — elles sont listées pour l'être.

| # | Chantier | Couverture mesurée | Ce que ça débloque |
| --- | --- | --- | --- |
| **D1** | **Thématisation** | **aucun champ thème** sur les 17 748 scrutins ; `theme_officiel` n'en est pas un (§4) ; `tags_thematiques` sur **7 des 13 candidats déclarés, 0 des 468 membres de roster** | la seule question du §1 sans réponse possible. **Différée par arbitrage** (#324, 29/08) : à instruire pour elle-même |
| **D2** | **Interventions des membres de roster** | **0 / 468** | §5.5. Traité par **#657, en vol** — dimensionnement en §4 |
| **D3** | **`source_url` sur les amendements** | **0 / 484 132** | le badge du §7. Aujourd'hui le seul objet publié en volume qui ne peut pas le porter |
| **D4** | **Décrets d'application** | jointure NOR balisée des deux côtés — mais **NOR publié sur 0 / 725 textes** (préalable **C3**), et **0 des 188 lois promulguées depuis 2024** porte un lien `APPLICATION` | §6.4. **La mesure du 31/08 la rend inexploitable en l'état** : la vue afficherait le faux vide qu'interdit §2 règle 5 |

**Les deux chantiers écartés par le temps 2 le restent**, et ce document ne les
rouvre pas : les amendements gouvernementaux (**0 sur 484 132** —
`type_deposant` ne connaît que `depute` et `commission_rapporteur`) et
l'hémicycle interactif (**1 024 / 41 723 mandats, 2,5 %**).

---

## 6. Ce qui n'a pas pu être vérifié

| Point | Pourquoi |
| --- | --- |
| Les **333 / 725** textes portant un NOR **côté source** | `raw_data/` des dossiers AN est hors du checkout de ce lot. Chiffre repris du temps 2, **non refait** |
| Les **108 179** occurrences de `<LIEN typelien="APPLICATION">` du JORF, et les taux du §6.4 | même raison, et aucun accès réseau. Repris du temps 2, **non refaits** |
| L'**empreinte mémoire côté navigateur** | mesurée en CPython (~5 × le JSON brut). Un moteur JS a un autre profil : l'ordre de grandeur tient, le chiffre exact **n'est pas mesuré** |
| Les mesures navigateur de #593 (hauteurs, chrome, débordements) | non refaites, comme au temps 2 |
| Les colonnes « sur l'ensemble », « + quorum » et « position majoritaire » du **§5** et du **§4.2** du temps 2 | **ne se reproduisent pas.** Les colonnes voisines se reproduisent à l'unité (les 5 nombres de scrutins agrégés, les 7 nombres de positions). La règle de sélection et de déduplication n'est pas écrite dans le document, et aucune des trois essayées ne retrouve les valeurs publiées. **L'ordre de grandeur tient, les chiffres exacts sont à refaire quand la règle sera écrite** |
| La dérive d'**une** entrée de `couverture` et de **deux** avertissements sur les 13 candidats déclarés | constatée, cause non identifiée |

---

## 7. Ce qu'il faudrait ouvrir

Six issues, aucune ouverte par ce lot.

| Rang | Titre proposé | Case | Pourquoi maintenant |
| ---: | --- | :---: | --- |
| 1 | **`amendements_agreges` par profil : publier ce que le navigateur recalcule** | **C1** | +301 Kio et +16 s mesurés, contre −112,7 Mo servis et −522 Mio d'empreinte sur la page la plus lourde. Le calcul par membre existe déjà dans `src/group_profile.py` |
| 2 | **La sélection des votes « sur l'ensemble » ne doit dépendre ni d'une apostrophe ni d'une sous-chaîne** | — | **22 scrutins manqués** (tous en législatures 16-17) et **6 capturés à tort** (amendement, article, motion de rejet). Les deux erreurs sont de sens contraire. Se résout par #639 rang 1, ou se documente comme borne |
| 3 | **Une fiche de gouvernement doit savoir dire pourquoi elle est incomplète** | **C2** | 0 / 10 portent un bloc de couverture ; la seule bonne phrase du site vient d'une constante en dur dans `pivotAdapter.js` |
| 4 | **Publier `infoJO.referenceNOR` sur les textes de gouvernement** | **C3** | 0 / 725 publiés. Préalable à D4, et utile seul (identifiant officiel de la loi) |
| 5 | **`source_url` sur les amendements** | **D3** | 0 / 484 132 — le seul objet en volume qui ne peut pas porter le badge du §7 |
| 6 | **Décrets d'application : instruire la requalification Légifrance** | **D4** | 0 des 188 lois promulguées depuis 2024 porte un lien `APPLICATION` ; le délai de requalification n'est pas publié |

**Sont déjà couverts par une issue ouverte**, à ne pas dupliquer : #639 rang 1
(`type_scrutin`, `type_vote`, et **`demandeur`** — la troisième question de son
dernier commentaire trouve ici sa réponse : non, il n'est pas publié), #641
(5 profils, aucun sur le chemin d'une page), #657 (interventions du roster,
dimensionné en §4), #668 (doublement des textes portés).

**Restent différés, avec leur condition déjà écrite** : #639 rang 4 (borne de
couverture sur `scrutins.json` — l'agrégat C4 la lève, sans décider de la reprise)
et la thématisation (#324, 29/08).
