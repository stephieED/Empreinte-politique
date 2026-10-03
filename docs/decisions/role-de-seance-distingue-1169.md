<a id="role-de-seance-distingue-1169"></a>
# La présidence de séance se distingue d'une prise de parole, et le corpus déjà écrit le reçoit (#1169) (2026-10-02)

`2026-10-02`

> **En bref** — publier le volume de parole d'un groupe comptait la conduite de la séance comme sa parole : **13 797 des 39 581 prises de parole d'Ensemble pour la République à la XVIIe, soit 35 %, sont de sa présidente d'Assemblée** ; Syceron ne le dit ni dans `<qualite>` (vide sur **100 %** des paragraphes de présidence) ni dans son attribut `roledebat` (**41 %** seulement), mais le **libellé de l'orateur** le dit à 100 % — d'où un champ `role_seance` dérivé de ce libellé, posé à la collecte, **2,6 Mio** contre 42 Mio si l'on publiait le libellé entier ; et parce que la fusion est additive, un report nommé le pose sur les **1 217 456** interventions déjà publiées, qu'aucun run ne remplirait sinon.

## 1. Le besoin, et la mesure qui le rend réel

La revue d'ergonomie de la fiche de groupe prépare une figure du volume de parole
par membre et par débat. Mesuré par la session qui la prépare, sur les fichiers
servis : Ensemble pour la République, XVIIe, **39 581 prises de parole sur 1 843
débats**, dont **13 797 (35 %) de Yaël Braun-Pivet** — 7 940 commençant par « La
parole est à », 7 858 de dix mots ou moins. Sur le débat « droit à l'aide à
mourir », 4 704 des 6 819. En regard, LIOT à la XVIIe : 3 287 prises de parole,
aucun orateur au-dessus de 13 %.

Un compte brut publierait donc la **conduite de la séance** comme la parole du
groupe.

## 2. Ce que la source porte, et où

Mesuré le 02/10/2026 sur 60 comptes rendus de la XVIIe en cache
(33 924 paragraphes, parseur XML et non expression régulière) :

| Signal | Ce qu'il dit | Couverture de la présidence |
| --- | --- | --- |
| `<qualite>` de l'orateur, publié sous `fonction` | ministre, rapporteur, rapporteur général, président de commission | **0 %** — vide sur les 3 667 paragraphes de présidence |
| l'attribut `roledebat="president"` | la présidence | **41 %** (3 666 sur 8 970) |
| le **libellé** de l'orateur (`<nom>`) | « M. le président », « Mme la présidente » | **100 %** (8 970), un seul faux positif |
| `code_parole` | rien d'utile ici | vide sur 99,5 % des paragraphes |

Les 3 132 paragraphes qui contiennent « La parole est à » sans porter `roledebat`
sont presque tous la présidence (2 304 « Mme la présidente », 827 « M. le
président ») : ils portent `code_grammaire="PAROLE_GENERIQUE"`.

**Une correction à un constat intermédiaire de ce lot** : `fonction` avait été
annoncé « vide sur tout le corpus » d'après un échantillon de 25 profils — tous
des membres de roster sans rôle gouvernemental. C'est faux comme généralisation :
Attal porte « ministre délégué » sur 1 867 entrées et « Premier ministre » sur
810, Retailleau « ministre d'État » sur 347. `fonction` marche ; il ne dit
simplement jamais la présidence.

## 3. Le champ, et pourquoi il est dérivé

`role_seance`, une seule valeur fermée : `presidence`. Dérivé du libellé par
`schema_pivot.role_seance_depuis_orateur()`, **ancré des deux côtés** — un
orateur qui CITE la formule (« La parole est à M. le président Marc Fesneau »)
n'est pas la présidence, et c'est mesuré : un cas sur 60 comptes rendus.

**Pourquoi pas `orateur_nom` publié verbatim** : 8,5 % des entrées d'index
portent un libellé de présidence, et publier le libellé partout coûterait
**42 Mio** sur le corpus contre **2,6 Mio** pour ce champ seul (mesuré sur
101 946 entrées d'index). `_reduire_au_theme` compte ses octets à 90 près ; ce
lot suit la même règle.

**La clé n'est jamais posée à `null`** : une entrée sans elle n'affirme rien sur
le rôle (§2 règle 5), là où `"role_seance": null` se lirait « mesuré, et ce
n'était pas la présidence ».

**Et la forme réduite la garde.** C'est le point qui décide de l'utilité du lot :
la forme réduite est celle des **membres de roster**, donc exactement la
population dont les fiches de groupe agrègent la parole.

## 4. Le report, et ce qu'il n'est pas

La fusion est additive : l'entrée ancienne gagne. **Aucun champ ajouté après coup
n'atteint le corpus déjà écrit** — le besoin s'est présenté trois fois (#710 le
sujet, #1087 l'ancre, celui-ci), et la preuve est dans les runs : les deux du
30/09 ont collecté les interventions et n'ont **ajouté aucune entrée ni rempli
aucun champ** (1 217 456 des deux côtés, zéro delta sur les quatre régimes).

`reporter_faits_de_source` généralise donc `reporter_id_syceron` sur une **liste
nommée** :

```python
CHAMPS_FAITS_DE_SOURCE = ("id_syceron", "fonction", "role_seance")
```

**Nommée, et pas « tous les champs absents »** : un champ que la collecte peut
légitimement rendre vide pour une raison tenant au run se remplirait depuis un
autre run, ce qui serait
[[collecte-vide-necrase-jamais]] retourné. La liste ne contient donc ni champ
dérivé (il se recompose), ni champ qu'une relecture humaine renseigne
(`succede_a`, `position_politique`).

**Seulement là où rien n'est écrit, et dans un seul sens.** Une valeur publiée
n'est jamais remplacée — ni par du vide, ni par une autre valeur. Le report
écrit, il ne corrige pas.

`reporter_id_syceron` reste, comme cas à une seule clé : #1087 le nomme et des
tests l'exercent.

## 5. Ce que ça ne fait pas

- **Rien n'est rempli avant un run** avec `collect_interventions`. Le corpus
  publié reste sans `role_seance` jusque-là, et une fiche ne peut donc pas encore
  séparer la présidence.
- **Les autres rôles ne sont pas touchés** : rapporteur et membre du gouvernement
  sont déjà dans `fonction`, qui bénéficie du même report.
- **Les interjections des bancs** restent écartées en amont (#839 : `PA0` avec
  `code_parole` vide, jamais attribuées).
- **Non mesuré** : si « rapporteur » distingue le rapporteur du texte de celui
  d'un avis, et ce que `<qualite>` donne sur les présidents de commission.

## 6. L'alternative rejetée

**Dériver la présidence à l'affichage**, en lisant le début du texte (« La parole
est à »). Rejeté sur mesure : la formule n'est présente que sur **1 720 des
8 970** paragraphes de présidence — elle en manque 81 %, et elle attrape un
orateur qui la cite. Un fait de la source se lit dans la source, pas dans la
prose qu'elle transporte.
