# Le lecteur accepte une tranche dérivée, et le silence reste une panne (#691, lot 2)

`2026-09-09`

> **En bref** — le lot 1 laissait **deux questions ouvertes** présentées comme des obstacles ; les deux se sont résolues par la mesure et **dans le sens inverse** : (1) l'**ordre** n'en est pas un, `audit_diff_profils` relève une liste par un **entier** (`_listes` rend un `int`) et une perte est une **baisse de compte**, jamais une différence de séquence — le garde-fou a été construit pour voir disparaître des enregistrements, pas pour figer un ordre que rien ne publie ; (2) le **filet de `merge_profile`** est **renforcé** et non affaibli — `old` vaut aujourd'hui « ce qu'un run précédent a réussi à collecter », donc dépend de `.cache/amendements_an/`, un cache CI non versionné, quand `old` dérivé vaut l'**archive committée**, vérité entière d'une législature close à laquelle une collecte ne peut rien ajouter ; **mesuré exhaustivement : 854 tranches sur 854 couvertes** (77/77 en XIV, 270/270 en XV, 507/507 en XVI) ; `profil_brut` sert donc une tranche que le manifeste **déclare** dérivable (`derivee: true` + `acteur_ref`), avec trois propriétés qui répondent chacune à une manière de se tromper — **le manifeste doit le dire et le silence reste une panne** (chercher l'archive « au cas où » ferait lire une tranche **perdue** comme une tranche dérivée et republierait un profil amputé, #580), l'**acteur vient du manifeste** et non d'une jointure (`profil_brut` ne connaît pas la table de correspondance et n'a pas à l'apprendre pour relire un profil), le **`nombre` est un contrôle et non une source** (#576, #579) ; **un défaut trouvé en écrivant** : trois lecteurs indexaient le manifeste par `fichier[: -len(".json")]` recopié à l'identique, et une tranche dérivée n'ayant pas de `fichier`, l'un des trois aurait divergé en silence — `_nom_declaree` est la seule définition, comptée par un test ; **rien n'est encore marqué ni cessé d'être écrit**, le lot 3 devant traiter `audit_collecte_vs_publie` (qui lit la forme **sur le disque** et compterait « 0 amendement collecté »), l'`ordre` écrit par `partitionner`, et le sparse-checkout d'`extract-an` (#674) ; **alternative écartée** : déduire la dérivation de l'absence du fichier — plus court d'une clé, et ça supprime la seule différence entre « plus écrite » et « disparue ». 11 tests neufs, suite complète à 4 213, 0 échec.

## Contexte

Le lot 1 a prouvé qu'une tranche d'amendements se reconstruit exactement depuis
`raw_data/amendements_an_figes/` — 120 profils, 568 771 amendements, zéro écart.
Il laissait **deux questions ouvertes**, présentées comme des obstacles. Les
deux se sont résolues par la mesure, et **dans le sens inverse** de ce qui était
craint.

## Question 1 — l'ordre : le contrôle de perte compte, il ne compare pas

Le lot 1 annonçait qu'un réordonnancement « produirait un diff sur tous les
profils, que le contrôle de perte lirait comme un changement ». Vérifié dans
`audit_diff_profils.comparer` : le relevé d'une liste est un **entier**.

```python
def _listes(releve, champ) -> int:
    return int(releve.get("listes", {}).get(champ, 0))
```

Une perte est une **baisse de compte**, jamais une différence de séquence. Un
réordonnancement est donc invisible à ce garde-fou, et c'est correct : il a été
construit pour voir disparaître des enregistrements, pas pour figer un ordre que
rien ne publie.

Ce qui reste vrai, et qui n'est pas un obstacle : un profil recomposé depuis une
tranche dérivée porte ses amendements dans l'ordre de l'archive, pas dans celui
de la collecte. Les comptes tombent, `recomposer` accepte, et le lot 3 devra
écrire un `ordre` cohérent avec l'archive au moment où `partitionner` marquera
une tranche dérivée.

## Question 2 — le filet de `merge_profile` : il est renforcé, pas affaibli

`merge_dossier_records(old, new, …)` conserve les entrées de `old` absentes de
`new` : c'est ce qui empêche une collecte vide d'effacer des amendements déjà
collectés (`collecte-vide-necrase-jamais.md`). Le lot 1 craignait que supprimer
les tranches supprime ce filet.

C'est l'inverse, et la raison tient à ce qu'est chaque source :

| | `old` aujourd'hui | `old` dérivé |
| --- | --- | --- |
| Origine | ce qu'un run **précédent** avait réussi à collecter | l'archive **committée** |
| Dépend de | `.cache/amendements_an/`, un cache CI non versionné | rien |
| Complétude | celle du dernier run réussi | celle de la législature, close et figée |

Pour une législature **close**, l'archive est la vérité entière : une collecte ne
peut rien y ajouter. Le filet cesse donc de dépendre d'un cache qui peut être
froid.

**Mesuré, exhaustivement** : les acteurs de **854 tranches sur 854** sont
présents dans l'index par acteur de leur législature — 77/77 en XIV, 270/270 en
XV, 507/507 en XVI. Aucun profil n'a de tranche close que l'archive ne
couvrirait pas.

## Décision

`profil_brut` sait servir une tranche que le manifeste **déclare** dérivable :

```json
{"legislature": "16", "derivee": true, "acteur_ref": "an:PA720892", "nombre": 16915}
```

Trois propriétés, et chacune répond à une manière de se tromper.

**Le manifeste doit le dire, et le silence reste une panne.** Aller chercher
l'archive « au cas où le fichier manquerait » ferait lire une tranche **perdue**
comme une tranche dérivée, et republierait un profil amputé sans que rien ne le
signale. Une tranche non marquée dont le fichier manque lève toujours
`PartitionIllisible` (#580).

**L'acteur est porté par le manifeste, pas résolu par une jointure.**
`profil_brut` ne connaît pas `raw_data/correspondance_acteurs_an.json` et n'a pas
à l'apprendre pour relire un profil.

**Le `nombre` annoncé est un contrôle, pas une source.** `recomposer` le
confronte au compte reconstruit et refuse l'écart — un contrôle qui lit sa
conclusion dans le document qu'il contrôle ne contrôle rien (#576, #579).

## Un défaut trouvé en écrivant : trois copies du même calcul

`charger_tranches`, `recomposer` et `iter_amendements_du_profil` indexaient
chacun le manifeste par `fichier[: -len(".json")]`, recopié à l'identique. Une
tranche dérivée n'ayant **pas** de `fichier`, l'un des trois aurait divergé sans
que rien ne le dise. `_nom_declaree` est désormais la seule définition, et un
test compte les lectures du champ.

## Ce que ce lot ne fait toujours pas

**Rien n'est marqué `derivee` dans le corpus, et rien ne cesse d'être écrit.**
Le lot 3 devra traiter, dans cet ordre :

1. **`audit_collecte_vs_publie`** lit la forme **sur le disque** et compterait
   « 0 amendement collecté » face à des millions publiés — ce que son propre
   docstring donne comme le défaut à éviter. Il doit compter depuis l'archive,
   ce qui préserve son principe : l'archive n'est pas le document qu'il contrôle.
2. **`partitionner`** doit marquer les tranches closes et écrire un `ordre`
   cohérent avec l'archive.
3. Le **sparse-checkout d'`extract-an`** (#674) devra inclure
   `raw_data/amendements_an_figes/`, sans quoi un shard lira une archive absente
   et lèvera — la panne étant alors correcte, mais évitable.

## Alternative écartée

**Déduire la dérivation de l'absence du fichier.** Un manifeste sans marque, un
répertoire vide, et le lecteur qui devine. C'est plus court d'une clé, et ça
supprime la seule différence entre « cette tranche n'est plus écrite » et
« cette tranche a disparu » — la distinction que `PartitionIllisible` porte
depuis #580.
