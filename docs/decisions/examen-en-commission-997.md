<a id="examen-en-commission-997"></a>
# Un texte renvoyé en commission n'est pas un texte examiné (#997) (2026-09-18)

`2026-09-18`

> **En bref** — La saisine de la commission est **automatique au dépôt**, et son
> `codeActe` contient `COM`. Deux fonctions en concluaient qu'un texte avait
> dépassé le dépôt : `"depose"` était inatteignable (279 des 728 dossiers
> gouvernementaux sortaient `navette_en_cours`) et **6 808 des 10 764 dossiers
> des archives XV à XVII étaient qualifiés `examine_commission` sans avoir été
> examinés**. Arbitré option B : c'est la **réunion de commission ou le dépôt du
> rapport** qui fait passer un texte de « déposé » à « examiné ». Une seule
> règle, `est_acte_au_dela_du_depot`, sert désormais les deux.

## Contexte

Signalé par la session « UI gouv » le 17/09/2026. Deux fonctions posaient la
même question et y répondaient toutes deux par « il existe un acte qui n'est pas
un dépôt » :

- `gouvernement_textes._determine_statut` — `a_acte_hors_depot` passait à `True`
  sur tout `codeActe` ne finissant pas par `-DEPOT` ;
- `candidate_profile._stade_from_code_acte` — rendait `examine_commission` pour
  tout code contenant `COM`, ce qui rendait sa branche `DEPOT` **morte**.

La seconde est la grave : le seuil d'`AGENTS.md` §6 (`stade ≥ examine_commission`)
est ce qui décide qu'un texte porté est montré au lecteur.

## Ce que la source publie, relevé le 18/09/2026

Archives XV, XVI et XVII, 10 764 dossiers. Un dossier déposé et rien de plus
porte exactement ceci — vérifié à la main sur `DLR5L16N49329`,
`DLR5L16N49108`, `DLR5L16N48166`, trois propositions de loi de Marine Le Pen,
14 nœuds d'actes chacune et aucun autre code :

```
AN1                       (conteneur d'étape, sans date)
AN1-DEPOT                 2024-01-25
AN1-COM                   (conteneur, sans date)
AN1-COM-FOND              (conteneur, sans date)
AN1-COM-FOND-SAISIE       2024-01-25   ← même jour que le dépôt
```

Les codes de commission, par effectif :

| Code | Occurrences | Atteste un examen ? |
| --- | ---: | --- |
| `AN1-COM` / `AN1-COM-FOND` | 6 410 chacun | non — conteneurs, jamais datés |
| `AN1-COM-FOND-SAISIE` | 6 410 | non — automatique au dépôt |
| `AN1-COM-FOND-NOMIN` | 1 133 | non (option A, écartée) |
| **`AN1-COM-FOND-REUNION`** | **3 672** | **oui** |
| **`AN1-COM-FOND-RAPPORT`** | **1 095** | **oui** |
| `SN1-COM-FOND-SAISIE` | 2 738 | non |
| `SN1-COM-FOND-RAPPORT` / `-NOMIN` | 997 / 1 003 | oui / non |
| `AN1-COM-AVIS-REUNION` / `-RAPPORT` | 703 / 129 | oui |
| `CMP-COM-RAPPORT-{SN,AN}` | 285 / 281 | oui |

84 codes distincts contiennent `COM`.

**Les conteneurs se reconnaissent à l'absence de tiret, et c'est mesuré** : sur
les 17 codes sans tiret, **16 ne portent jamais de date** — 6 418 `AN1`, 2 741
`SN1`, 1 463 `ANLUNI`, 1 415 `AN20`, 603 `PROM`, 284 `CMP`… `MOTION` est le seul
qui en porte une (8 occurrences, 8 datées), donc le seul acte réel parmi eux. Il
est nommé dans `_CODES_NUS_DATES` plutôt que déduit, et la limite est dite : un
code nu et daté qu'une archive future ajouterait serait pris pour un conteneur
jusqu'à ce qu'on l'ajoute.

## Décision

**Option B — réunion de commission ou dépôt du rapport.** Deux prédicats dans
`gouvernement_textes.py`, qui en est déjà la source canonique pour
`candidate_profile.py` (celui-ci l'importe depuis #210) :

1. `est_examen_en_commission(code)` — `COM` **et** (`REUNION` ou `RAPPORT`) ;
2. `est_acte_au_dela_du_depot(code)` — ni un dépôt, ni un conteneur nu, ni un
   acte de commission qui n'est pas un examen.

`-AVIS` est retenu à côté de `-FOND` : une commission saisie pour avis qui se
réunit a examiné le texte. L'arbitrage porte sur l'acte, pas sur la commission
qui le pose.

## Mesuré, avant / après

| | Avant | Après |
| --- | ---: | ---: |
| `depose`, sur 728 dossiers d'origine gouvernementale | 1 | **280** |
| `navette_en_cours`, même population | 337 | **58** |
| Dossiers dont le stade le plus avancé est `examine_commission` (10 764) | 7 219 | **411** |
| … qui passent à `depose` | — | 6 798 |
| … qui n'ont plus aucun stade | — | 10 |
| Entrées `textes_portes[]` au-dessus du seuil §6 (9 104 sur 1 177 profils) | 9 104 | **3 885** |
| … qui passent sous le seuil | — | **5 219 (57,3 %)** : 4 958 chez les membres de roster, 261 chez les candidats déclarés |

Les 10 dossiers qui perdent tout stade n'ont aucun acte `-DEPOT` dans l'archive :
`stade_procedural: null` y dit « non établi », ce qui est la réponse juste
(§2 règle 5), et non un rangement par défaut.

## Ce que cette décision NE fait pas

**Elle ne retire rien du corpus.** Un texte seulement déposé est collecté et
publié comme avant, sous `stade_procedural: "depose"` — 1 355 entrées le
portaient déjà au 18/09/2026, sur 11 050. Ce lot corrige une **étiquette**.

**Elle ne décide pas ce que le lecteur voit.** Le seuil §6 est appliqué dans
`web/UI_finale` (`profilCandidat.js`, `STADES_PUBLIES`), pas à la collecte, et
§6 prévoit un accès aux textes en deçà « via explicit user toggle ». Après ce
correctif, le filtre actuel masquerait 5 219 entrées qu'il montre aujourd'hui —
dont la totalité des textes portés de Marine Le Pen (21) et de Nicolas
Dupont-Aignan (33), correctement étiquetés `depose`. **Comment traiter la
catégorie « déposé » à l'écran est un arbitrage d'interface**, rendu par la
propriétaire avec la session UI, et il reste ouvert.

## Une fixture décrivait un monde que la source ne produit pas

`test_statut_navette_en_cours_quand_deja_examine_sans_decision` portait
`AN1-COM` **daté du 2024-02-01**. `AN1-COM` n'est jamais daté dans les trois
archives. L'intention du test était juste — « examiné sans décision de séance →
navette » — mais sa fixture faisait passer un renvoi pour un examen, et c'est
elle qui rendait le défaut invisible. Elle porte désormais
`AN1-COM-FOND-REUNION`. Même patron que #556 : une fixture écrite d'après ce que
le code imagine ne peut pas révéler que le monde est autre.

## Alternatives rejetées

**Option A — la nomination d'un rapporteur (`-COM-FOND-NOMIN`, 1 133 AN +
1 003 SN).** Elle dit que la commission s'organise, pas qu'elle a examiné. Un
rapporteur nommé sur un texte jamais mis à l'ordre du jour de la commission
reste un texte non examiné.

**Option C — la discussion en séance (`-DEBATS`).** Plus strict, et faux dans
l'autre sens : les textes réellement examinés en commission mais jamais venus en
séance redescendraient à « déposé », alors que leur examen a eu lieu et est
sourcé.

**Garder deux règles, une par fonction.** C'est l'état qui a produit le défaut :
les deux posaient la même question sans le savoir, donc une seule des deux
pouvait être corrigée sans que rien ne le signale.
