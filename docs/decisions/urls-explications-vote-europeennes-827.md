# L'adresse est dérivée, l'existence est prouvée (#827)

`2026-09-10`

> **En bref** — les explications de vote sont la seule matière du corpus européen où le candidat dit lui-même pourquoi il a voté, et elles paraissaient **sans aucun lien** : mesuré sur les 7 candidats déclarés, **0 des 1 801 entrées `WEXP`** porte une adresse contre **100 %** des neuf autres types d'activité, le trou est d'un seul type ; la référence est pourtant dans l'intitulé **1 530 fois sur 1 801**, mais **on ne peut pas la vérifier** — `www.europarl.europa.eu` est derrière un pare-feu anti-robot AWS qui rend `HTTP 202` et 0 octet *à l'identique* pour un document réel, pour une référence inventée et pour `CETTE-URL-N-EXISTE-PAS`, y compris avec un User-Agent de navigateur ; d'où la règle : **l'existence est établie sur `data.europarl.europa.eu`**, sans pare-feu, puis l'adresse publique est écrite — la dérivation n'écrit que l'adresse, jamais la preuve, et **1 508 explications (83,7 %) reçoivent un lien pour 0 lien mort**, 271 n'en ayant aucune faute de référence citée et 22 parce que le document n'existe pas, dont **17 transmis par une autre institution** et une coquille de la source (`A9-0390/2017`, terme 9 annoncé en 2017) ; **le cadrage initial de l'issue était sans objet** — il opposait « page lisible » (31,7 % des références) et « PDF seul » (66,9 %), or ces taux ne mesurent que les formats de distribution du portail : les six documents « PDF seul » testés **s'ouvrent tous** sur le site public ; équivalence « portail 200 ⟺ page publique » éprouvée sur **18 URL ouvertes une à une dans un navigateur** par la propriétaire, seule façon de franchir le défi anti-robot — 13 confirmées s'ouvrent, 5 contrôles négatifs échouent, **0 divergence**, 2015→2024, types `A`/`B`/`RC` — mais **éprouvée n'est pas surveillée** : 18 URL, pas 1 508, et le pare-feu interdit tout contrôle continu ; le portail, lui, **ne déclare son débit qu'en le refusant** — aucune en-tête sur un 200, puis `429` + `Retry-After: 60` : une première passe sans pause a rendu **1 320 réponses 429 sur 1 424**, mesure entièrement perdue, la reprise à 0,6 s ayant coûté 47 minutes et 13 blocages, d'où le cache disque et le respect du `Retry-After` ; `existe()` rend **`None` et non `False`** quand la question n'a pas pu être posée (§2 règle 5), et sans résolveur aucune adresse n'est écrite. **Écarté** : l'URL de distribution du portail (export Word, et segment `reds_iPlRp` variant par document, donc non dérivable), l'URI ELI (200 partout, en `rdf+xml` — une adresse pour machine), et dériver sans vérifier. Corrige aussi une docstring qui citait « 1 fois sur 190 » : exact **pour Bardella** (189 de ses 190 n'ont pas de référence), faux comme taux du corpus. Suite complète à 4 404, 0 échec.

## Contexte

Les explications de vote sont la seule matière du corpus européen où le candidat
écrit lui-même pourquoi il a voté ainsi. Elles étaient publiées **sans aucun
lien** vers le document qu'elles commentent, ce qui heurte §2 règle 2.

Ce n'est pas une lacune générale de la source. Mesuré le 10/09/2026 sur
`ep_mep_activities.json.zst` (dump du 24/07/2026), population : les **7
candidats déclarés ayant un mandat européen** :

| Type d'activité | Entrées | Portent une adresse |
| --- | ---: | ---: |
| `CRE`, `WQ`, `IMOTION`, `MOTION`, `REPORT`, `OQ`, … | 4 862 | **100 %** |
| **`WEXP`** (explications de vote) | **1 801** | **0** |

Une entrée `WEXP` porte quatre clés — `title`, `date`, `text`, `term` — et ni
`url` ni `formats[]`. Le trou est d'un seul type.

## La référence est dans l'intitulé, 85 % du temps

`Mobilisation of the EGF: application EGF/2016/008 FI/Nokia (A8-0196/2017 - Petri Sarvamaa) FR`

**1 530 des 1 801** entrées citent un document. Les 271 autres ont un intitulé
en prose et n'auront **jamais** de lien : c'est un fait sur la source.

**Un chiffre a longtemps été cité de travers dans le code.** La docstring de
`_make_intervention` affirmait « la référence n'est dans l'intitulé qu'1 fois
sur 190 ». C'est exact **pour Bardella** — 189 de ses 190 explications n'en
citent aucune — et faux comme taux du corpus, où Philippot n'en manque que 7
sur 766. La population d'un chiffre se nomme (§9).

## Pourquoi l'adresse ne peut pas être publiée sans preuve

`www.europarl.europa.eu` est derrière un **pare-feu anti-robot AWS**. Toute
requête reçoit `HTTP 202`, 0 octet, `x-amzn-waf-action: challenge`, y compris
avec un User-Agent de navigateur complet. Vérifié :

| URL demandée | Réponse |
| --- | --- |
| `A-8-2017-0114_FR.html` (document réel) | 202, 0 octet |
| `Z-9-9999-9999_FR.html` (référence inventée) | 202, 0 octet |
| `CETTE-URL-N-EXISTE-PAS_FR.html` | 202, 0 octet |

**Aucun job ne peut vérifier ces adresses** — ni à la collecte, ni au contrôle
qualité, ni plus tard. Une URL dérivée publiée sans preuve serait
indétectablement fausse, et **22 le sont déjà** : 17 documents transmis par une
autre institution (type `C`, comme `C9-0212/2020`), une coquille de la source
(`A9-0390/2017` annonce le terme 9 pour 2017, qui commence en 2019), et 2 cas
isolés.

## La décision

> Le job demande au **portail open data** si le document existe — celui-là n'a
> pas de pare-feu et répond `200` ou `404`. S'il existe, on publie l'adresse du
> **site public**, celle qu'un lecteur peut ouvrir.

La dérivation n'écrit que l'adresse ; l'existence vient d'une source
interrogeable. Deux formes de conversion, et la seconde n'est pas une variante
de la première :

- `B8-0240/2017` → `B-8-2017-0240`
- `RC-B8-0292/2018` → `RC-8-2018-0292` — **la lettre disparaît**

| | Explications | |
| --- | ---: | ---: |
| Lien publié, existence prouvée | **1 508** | **83,7 %** |
| Sans lien — aucune référence citée | 271 | 15,0 % |
| Sans lien — document introuvable | 22 | 1,2 % |
| **Liens morts publiés** | **0** | |

## Comment l'équivalence a été établie, et ce qu'elle vaut

Le pare-feu interdisant toute vérification automatique, les URL ont été ouvertes
**une à une dans un navigateur par la propriétaire** — seule façon de franchir
le défi JavaScript. Échantillon choisi pour ses cas limites : **18 URL**.

| Groupe | URL | Attendu | Résultat |
| --- | ---: | --- | --- |
| Documents que le portail confirme | 13 | s'ouvrent | **13/13** |
| dont résolutions communes `RC-` | 2 | s'ouvrent | **2/2** |
| dont documents « PDF seulement » au portail | 6 | s'ouvrent | **6/6** |
| Contrôles négatifs (404 au portail, plus une référence inventée) | 5 | échouent | **5/5** |

**Zéro divergence**, sur 2015→2024 et les types `A`, `B`, `RC`.

Le résultat le plus utile est celui des six « PDF seulement » : **le format que
le portail expose n'a aucune incidence** sur l'existence de la page publique. Un
cadrage antérieur de cette issue opposait « page lisible » (31,7 % des
références) et « PDF seul » (66,9 %) — cette distinction ne mesure que les
formats de distribution du portail et ne dit rien de ce qu'un lecteur peut
ouvrir. Toute la comparaison qui en découlait était sans objet.

**Éprouvée, jamais surveillée.** 18 URL, pas 1 508, et le pare-feu interdit tout
contrôle continu. Si le Parlement change sa chaîne de publication, rien ne nous
en avertira.

## Le débit du portail se déclare en le dépassant

Aucune réponse `200` ne porte d'en-tête de limite. Une première passe sans pause
a rendu **1 320 réponses `429` sur 1 424** — mesure entièrement perdue. La
limite ne s'annonce qu'une fois franchie : `HTTP 429` + `Retry-After: 60`.

Reprise à une requête toutes les 0,6 s : **47 minutes**, et **13 blocages de
60 s** malgré la pause. D'où deux choses dans `ResolveurDocuments` : le respect
du `Retry-After`, et un cache disque qui rend la seconde passe gratuite. Un 404
y est mis en cache **comme un 200** — c'est un fait établi sur le document, pas
un échec de collecte.

## Ce que le résolveur ne fait jamais

`existe()` rend `None`, et non `False`, quand la question n'a pas pu être posée
— hors ligne, portail injoignable. Une ignorance publiée comme un fait négatif
est ce que §2 règle 5 interdit, et l'appelant doit pouvoir distinguer « ce
document n'existe pas » de « nous n'avons pas pu demander ». Sans résolveur,
aucune adresse n'est écrite : c'est l'état d'avant ce lot, et le comportement
des tests, que `tests/conftest.py` prive de réseau depuis #473.

## Écarté

- **Publier l'URL de distribution du portail**
  (`data.europarl.europa.eu/distribution/reds_iPlRp/…_fr.html`) : c'est un export
  Word converti — 1 400 caractères de feuille de style Microsoft avant le premier
  mot, sans habillage ni navigation. Et le segment `reds_iPlRp` **varie par
  document** (trois valeurs sur dix interrogés) : non dérivable de toute façon.
- **Publier l'URI ELI** (`data.europarl.europa.eu/eli/dl/doc/<doceo>`) : répond
  200 partout, en `application/rdf+xml`. Une adresse pour machine.
- **Dériver sans vérifier** : 22 liens morts connus, et un nombre inconnu
  d'autres, sans aucun moyen de les détecter.

## Une hypothèse écartée par la mesure

La rareté du HTML au portail n'est ni un délai de traitement ni une traduction
manquante : sur 8 documents dont la version française n'a pas de HTML, **aucune
des 23 ou 24 langues publiées n'en a**. Le format n'est pas produit, pour
personne. La bascule se situe en **2018** — 97-99 % de HTML jusqu'en 2017, 0 %
en 2023-2024. Cause **non établie**, et sans effet sur la décision.

Suite complète à 4 404, 0 échec.
