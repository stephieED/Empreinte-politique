# Un profil publie tous ses mandats de député, et le compteur devient un témoin de couverture (#640) (2026-08-31)

`2026-08-31`

> **En bref** — le mandat électif était reconstruit depuis le couple unique `mandat_debut`/`mandat_fin` d'`identite_an` alors que le même objet portait `nb_mandats` (379 des 457 profils concernés publiaient moins que leur propre compteur, 612 mandats manquants) ; AMO30 porte bien l'historique (3 954 mandats ASSEMBLEE pour 3 117 acteurs, plus ancien 2002-06-19), regroupé sur `(legislature, dateDebut)` — jamais sur la seule législature, qui unirait les deux mandats de Bertrand Petit séparés par une élection annulée — pour 613 périodes nouvelles sur 393 profils, 26 écarts résiduels nommés et 18 doublons hérités que la fusion additive ne peut pas retirer.

`src/candidate_profile.py` reconstruisait le mandat électif d'un député depuis
un **couple unique** de dates porté par `identite_an` —
`mandat_debut`/`mandat_fin`, ceux du mandat courant. Le même objet portait
`nb_mandats`, le nombre de mandats exercés. Le compteur et la liste vivaient
dans le même dictionnaire sans jamais s'accorder.

Mesuré le 31/08/2026 sur `b684304f`, en comparant `identite.nb_mandats` du
profil brut au nombre de `mandat_electif` publiés (`chambre` ∈ {`AN`, `null`}) :

| | Profils |
| --- | ---: |
| Profils bruts portant `identite.nb_mandats` ≥ 1 | **457** / 481 |
| … publiant **moins** de `mandat_electif` que ce nombre | **379** |
| Mandats électifs manquants, au total | **612** |

Ce que la fusion additive rattrapait était fortuit : un profil accumulait autant
de mandats qu'il y avait eu de runs le voyant siéger sous des dates
différentes. Le mandat 2017-2022 de Marine Le Pen n'a été vu par aucun run — il
n'existait nulle part.

## La question d'abord, le code ensuite : AMO30 porte-t-il l'historique ?

**Oui, et la preuve est dans l'archive.** `json/acteur/PA720614.json`
(Marine Le Pen) porte **trois** mandats `typeOrgane == "ASSEMBLEE"` — 15e, 16e
et 17e législatures, `PM723016`, `PM797055`, `PM840315`. Sur l'archive entière :
**3 954 mandats ASSEMBLEE pour 3 117 acteurs**, tous datés, **aucun** sans
`legislature` ni sans `dateDebut`, le plus ancien au **2002-06-19** (XIIe
législature). La branche « si non, publier un `couverture.mandats` en
`hors_couverture` » de l'issue est donc sans objet.

`tests/fixtures/amo30_mandats_assemblee_640.zip` fige cette preuve : une
réduction **verbatim** de l'archive à quatre acteurs et les organes `GP` qu'ils
citent, 17 Ko. Pas une fixture écrite à la main — la question de départ est
factuelle, et une fixture inventée y répondrait par construction
(`syceron-archives-verifiees-parseur-510.md`).

## Décision 1 — regrouper sur `(legislature, dateDebut)`, jamais sur la seule législature

AMO30 scinde un même siège en plusieurs enregistrements quand il est interrompu
puis repris. Xavier Bertrand (`PA267080`) a **trois** enregistrements de 13e
législature, tous ouverts au 2007-06-20, fermés au 2007-07-19, 2010-12-15 et
2012-06-19, chaque fois sur `causeFin = "Nomination comme membre du
Gouvernement"`. C'est un siège, pas trois mandats : les publier séparément
donnerait trois entrées de même `debut` et de même libellé, donc **la même clé
de fusion** (`merge_profile._pivot_mandat_key`) — deux des trois
disparaîtraient sans un mot. Ils sont recollés en union de périodes, le geste
que [#roster-an-derive-amo30-526](roster-an-derive-amo30-526.md) applique déjà
aux organes successifs d'un groupe.

**Regrouper sur la seule législature aurait fabriqué un fait faux**, et la
donnée le dit : Bertrand Petit (`PA344201`) a deux mandats de 16e législature,
2022-06-19 → 2022-12-02 (*élection annulée par le Conseil constitutionnel*)
puis 2023-01-29 → 2024-06-09 (partielle). Les unir publierait un mandat
couvrant deux mois pendant lesquels il n'était pas député. Marie-Christine
Dalloz porte le même motif sur la 17e. La date d'ouverture sépare les deux cas
sans arbitrage.

## Décision 2 — `dateDebut`, pas `datePriseFonction`

Les deux diffèrent (`2022-06-19` contre `2022-06-22` pour l'ouverture de la
16e), et le corpus publié porte **les deux conventions** : les mandats collectés
du temps de NosDéputés ont la seconde. La mesure tranche, sur les 477 profils
publiés dont l'acteur AN est résolu :

| Champ lu comme `debut` | Entrées reproduisant une entrée déjà publiée |
| --- | ---: |
| `dateDebut` | **457** |
| `datePriseFonction` | 13 |

`datePriseFonction` orphelinerait la quasi-totalité du corpus publié — la
fusion additive ne retirant jamais l'ancienne entrée, chaque profil publierait
deux fois chaque mandat. C'est aussi le champ que
`_select_mandat_assemblee_courant` lit depuis #354.

## Décision 3 — le groupe du libellé est le **dernier rejoint pendant le mandat**

Un libellé de mandat électif porte le groupe entre parenthèses. Trois candidats
ont été mesurés sur les 1 070 périodes reconstruites :

| Règle | Périodes portant un groupe |
| --- | ---: |
| le groupe courant de l'acteur | 1 070, mais **faux** hors du mandat en cours (Édouard Philippe et Xavier Bertrand seraient « Les Républicains » sur un mandat UMP) |
| un groupe unique couvrant tout le mandat | 503 sur 1 070 |
| **le dernier groupe rejoint pendant le mandat** | **1 069** sur 1 070 |

La deuxième échoue pour une raison structurelle : **tout le monde commence non
inscrit**. Les groupes ne sont constitués qu'après l'ouverture d'une
législature, si bien qu'AMO30 porte pour chaque élu un mandat `GP` de quelques
jours vers `NI`. C'est le transit que #526 a mesuré sur les rosters, au même
endroit et de la même façon. Prendre le **dernier** l'écarte par construction —
il est premier, jamais dernier — et rend, pour un député qui n'a pas changé de
groupe, le seul qu'il ait eu. Même logique de sélection que
`_select_mandat_par_type_courant`, appliquée à une fenêtre au lieu de la
carrière entière. Aucun groupe recouvrant ⇒ pas de parenthèse, jamais un groupe
par défaut (AGENTS.md §2 règle 5).

**Exception assumée : la période courante garde le groupe courant.** La clé de
fusion d'un mandat est `(label, categorie, fonction, debut)` ; un libellé qui
bouge ferait apparaître un doublon de période au lieu de retrouver l'entrée
publiée. Les deux raisons vont dans le même sens — c'est aussi le groupe vrai
aujourd'hui.

## Décision 4 — `nb_mandats` ne bouge pas, il devient le témoin

`nb_mandats` reste le compte d'**enregistrements** AMO30, et la liste compte les
**sièges**. Les deux ne sont plus censés être égaux, et l'écart est nommé :

| Effet mesuré sur les 481 profils publiés | |
| --- | ---: |
| Périodes reconstruites (477 profils dont l'acteur AN est résolu) | **1 070** |
| … déjà publiées à l'identique | 457 |
| … **nouvelles** | **613**, sur **393** profils |
| `mandat_electif` AN/`null` publiés avant | 491 |
| Profils dont `nb_mandats` reste supérieur au nombre de périodes | **26** (écart total **29**) |

Les 26 profils résiduels sont tous du motif Xavier Bertrand : un siège
interrompu par une nomination au gouvernement compte pour plusieurs
enregistrements AMO30 et pour un seul mandat. Lisser cet écart demanderait de
publier des périodes qui se recouvrent ; le nommer coûte une ligne.

Deux bornes de couverture restent, et ne sont pas des défauts de ce lot :

- **AMO30 ne remonte pas avant le 2002-06-19.** Une carrière ouverte à la XIe
  législature ou plus tôt est publiée tronquée, et le référentiel ne porte rien
  qui permette de le dire profil par profil.
- **Les quatre profils sans acteur AN résolu** (`david-lisnard`,
  `jordan-bardella`, `marine-tondelier`, `nathalie-arthaud`) ne gagnent rien :
  ils n'ont jamais siégé à l'Assemblée, et
  [#correspondance-acteurs-an-525](correspondance-acteurs-an-525.md) le déclare.

## Ce que la correction ne peut pas réparer

**18 profils publieront deux entrées pour un même mandat**, et c'est
irrécupérable depuis ce lot. Leur entrée publiée porte une date d'ouverture de
la convention NosDéputés (17 fois `2022-06-22` au lieu de `2022-06-19` ;
`laurent-wauquiez` a le cas jumeau sur le libellé, « Les Républicains » figé sur
un mandat 2012-2017 commencé sous l'UMP). La fusion additive ne retire jamais
une entrée ancienne, et `audit_diff_profils` **bloque le commit** sur une
disparition : les nettoyer demande une passe délibérée à perte déclarée, pas un
correctif de collecte. 18 sur 1 070, nommés plutôt que lissés.

## Conséquence non traitée ici : les dénominateurs des fiches de groupe

Le commentaire de #640 mesure que `membres_eligibles` — calculé par
chevauchement entre la date d'un scrutin et les périodes de `mandat_electif`
(#492) — vaut **5 pour les 31 membres d'`AN:SOC`**, ce qui rend `quorum_atteint`
et tous les ratios de cohésion faux (§2 règle 7). La cause est bien celle
corrigée ici, mais la réparation demande une **régénération** des cinq fiches de
groupe, avec l'écart avant/après mesuré. `src/group_profile.py` n'est pas touché
par ce lot.

## Alternative écartée — publier un enregistrement AMO30 par entrée

Le plus fidèle à la source, et inexploitable : trois entrées de même `debut`
s'effondrent en une à la fusion, laquelle des trois survivant n'étant pas
déterministe. Une donnée perdue en silence est pire qu'une donnée regroupée en
le disant.

## Alternative écartée — renseigner `suspendu_pour_fonction_gouvernementale`

Les segments recollés portent `causeFin = "Nomination comme membre du
Gouvernement"`, et le schéma a le champ. Mais un mandat clos par une nomination
sans reprise (Gabriel Attal, 16e législature) est **terminé**, pas suspendu, et
AGENTS.md §5 interdit précisément de confondre les deux. Distinguer les deux cas
demande de lire `datePriseFonction` segment par segment : hors périmètre de ce
lot, et à instruire séparément.
