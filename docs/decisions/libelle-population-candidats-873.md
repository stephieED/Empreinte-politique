<a id="libelle-population-candidats-873"></a>
# « 32 candidats déclarés » en comptait 30 : un libellé de provenance affirmait un statut (#873) (2026-09-12)

`2026-09-12`

> **En bref** — `population_profils.py` est **la** façon d'afficher un compte de profils (#630), et il nommait la provenance `candidat_declare` « **candidats déclarés** » ; or la provenance dit quelle population a fait collecter le profil, **jamais où en est la candidature** : `raw_data/candidats.json` porte 34 entrées, dont **2 au statut `decline`** (`laurent-wauquiez`, `jordan-bardella`), et les **32** profils de cette provenance les comptent — tout compteur du dépôt affichait donc « 32 candidats déclarés » pour une population qui en contient **30** ; relevé par la propriétaire le 12/09/2026 en relisant un compte du lot #839, où l'un des 7 profils portant un mandat sans estampille est précisément `laurent-wauquiez` ; le libellé devient **« candidats »** — il cesse d'affirmer le statut, garde le parallèle avec « membres de roster » et ne rallonge aucune ligne, sur **77 emplacements** de `src/` et `tests/` ; le compte **par statut** (30 déclarés, 2 déclinés) reste dans la liste éditoriale et **aucun outil ne le publie** : le publier demanderait que les audits lisent `raw_data/candidats.json`, ce qui est un autre lot ; option écartée : « collectés comme candidats », plus précise et plus longue, dans des lignes de console déjà chargées.

## 1. Le défaut

| | |
| --- | ---: |
| Entrées de `raw_data/candidats.json` | 34 |
| — statut `declare` | 32 |
| — statut `decline` | **2** |
| Profils pivot à provenance `candidat_declare` | **32**, les 2 déclinés compris |

Rendu affiché jusqu'ici :

> Profils publiés : 1180   (**32 candidats déclarés** · 1148 membres de roster)

C'est la faute que `AGENTS.md` §9 nomme : **une figure juste sur la mauvaise
population est une erreur, pas une approximation**.

## 2. Ce qui l'a fait voir

Le lot #839 a rapporté « 406 mandats sans `categorie_source`, sur 45 profils
dont 7 candidats déclarés ». La propriétaire a demandé si ces 7 comprenaient les
candidats ayant décliné. Ils les comprenaient : l'un des 7 est
`laurent-wauquiez`. Le compte juste s'écrit « 6 déclarés et 1 décliné » — et il
ne pouvait pas s'écrire, puisque l'outil ne connaît que la provenance.

## 3. La décision

`LIBELLE_CANDIDATS = "candidats"`.

> Profils publiés : 1180   (32 candidats · 1148 membres de roster)

Le libellé dit ce que le champ dit : cette population a été collectée comme
candidate. Il n'affirme plus rien sur l'état de la candidature.

## 4. Ce que le lot ne fait pas

**Publier le compte par statut.** 30 déclarés et 2 déclinés se lisent dans
`raw_data/candidats.json` ; aucun outil ne le publie, et le faire demanderait
que les audits lisent la liste éditoriale — un couplage qui mérite son propre
arbitrage.

**Toucher au gel de #760.** Un profil `decline` a sa collecte gelée, mais la
propriétaire a tranché le 12/09/2026 : **le gel ne vaut que pour la collecte en
CI**, et un profil gelé se corrige comme les autres.

## 5. L'alternative écartée

**« collectés comme candidats »** : plus précis, et plus long de douze
caractères dans des lignes de console qui portent déjà deux postes et un total.
Le gain de précision ne compensait pas l'encombrement — « candidats » suffit à
ne rien affirmer de faux.
