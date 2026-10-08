<a id="mandat-europeen-sans-parole-1163"></a>
# Un mandat de député européen sans prise de parole publiée se déclare, calculé à chaque run (#1163) (2026-10-08)

`2026-10-08`

> **En bref** — Emmanuel Maurel n'a aucune prise de parole européenne de 2014 à 2019, ni Raphaël Glucksmann de 2019 à 2024 : ce n'est pas leur silence, la source ne les publie pas (ParlTrack, dump et site, et l'API speeches du portail européen, mesurés le 07/10/2026). Arbitrage de la propriétaire, 08/10/2026 : la limite se déclare dans « Ce qu'on n'a pas pu lire », donc dans le profil de la personne. `couverture_profil.mandats_europeens_sans_parole` la **calcule** à chaque écriture du pivot : un mandat de député européen sans aucune prise de parole européenne datée dans sa période reçoit une entrée `hors_couverture`, `source: "parlement_europeen"`, de la portée du mandat. Sur le corpus du 07/10 (public `5555443e8`) : **2 profils** déclarés, exactement les deux mesurés.

## 1. Le constat

| Profil | Mandat | Prises de parole européennes publiées dans la période |
| --- | --- | ---: |
| Emmanuel Maurel | 01/07/2014 → 01/07/2019 | 0 (845 sur le mandat suivant) |
| Raphaël Glucksmann | 02/07/2019 → 15/07/2024 | 0 (128 sur le mandat suivant) |

Les sources sont mesurées dans `docs/sources/parltrack-et-europarl.md` (#1250).

## 2. La décision

- **Où** : `couverture.interventions` du profil, une entrée par mandat :
  `{etat: "hors_couverture", source: "parlement_europeen", portee: {debut, fin}}`. C'est
  la forme que l'interface lit déjà (`paroleEuropeenneNonCouverte.js`, #1239) ; aucun
  champ nouveau.
- **Comment** : dérivée dans `couverture_profil.deriver`, comme les autres bornes —
  jamais écrite à la main, jamais fusionnée pour elle-même.
- **Ce qui empêche de déclarer**, chacun parce que l'affirmation deviendrait une
  supposition (§2 règle 5) :
  - une prise de parole européenne **sans date** sur le profil : elle pourrait
    appartenir à n'importe quel mandat (Le Pen, Philippot, Mélenchon, sans écart à
    déclarer de toute façon) ;
  - **aucune** prise de parole européenne sur le profil : rien ne distingue alors une
    limite de la source d'une collecte qui n'a pas eu lieu ;
  - un mandat sans date de début.

## 3. Ce que la règle ne couvre pas, mesuré

Sur le même corpus, **53 profils** portent un mandat de député européen et **aucune**
prise de parole européenne (Alain Juppé, François Hollande, François Bayrou…). Rien ne
leur est déclaré : la règle exige qu'une collecte européenne ait rendu quelque chose
pour la personne. Ce sont des profils de roster et de gouvernement ; si l'interface
doit un jour parler de leur activité européenne, il faudra d'abord établir ce que leur
collecte lit.

## 4. Alternative écartée

**Une liste écrite à la main dans `config/`**, slug → périodes : elle ne verrait pas les
cas suivants, alors que le défaut vient de la source et se reproduira à chaque fiche
ParlTrack recréée.
