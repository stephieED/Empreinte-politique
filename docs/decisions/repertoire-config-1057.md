<a id="repertoire-config-1057"></a>
# Un répertoire `config/` : ce qu'une personne décide ne vit plus dans `raw_data/` (#1057) (2026-09-21)

`2026-09-21`

> **En bref** — les trois fichiers écrits à la main quittent `raw_data/` pour `config/` ; la règle « les données viennent du dépôt public, le code du privé » devient vraie sans exception.

**Contexte** : `raw_data/` est censé porter ce que la collecte a rendu. Il
portait aussi trois fichiers que personne ne collecte —
`groupes_reels.json`, `mandats_anterieurs.json`,
`correspondance_elus_rne.json` — écrits à la main, et qui sont des décisions.

La confusion n'était pas seulement esthétique. La navette entre les deux
dépôts tient en une règle : **les données viennent du dépôt public, le code
vient du privé**, portée par la constante `DONNEES=(pivot_data raw_data)` de
`scripts/sync_depots.sh`. Cette règle laissait ces trois fichiers du mauvais
côté : une correction de lignée ne voyageait pas avec le code qui la lit.

**Décision : un répertoire `config/`, et le critère est qui écrit le fichier.**

| Répertoire | Qui écrit | Exemples |
| --- | --- | --- |
| `raw_data/`, `pivot_data/` | **un run** | `profiles/`, `candidats.json`, `correspondance_acteurs_an.json`, `gouvernements_reels.json` |
| `config/` | **une personne** | `groupes_reels.json`, `mandats_anterieurs.json`, `correspondance_elus_rne.json` |

`gouvernements_reels.json` **reste dans `raw_data/` malgré son nom** : il est
produit par `src/gouvernements_amo30.py --out` à chaque run. Le critère est
l'écriture, jamais le nom.

## Pourquoi `groupes_reels.json` n'est pas dérivable, alors que les gouvernements le sont

Depuis [[bascule-roster-an-amo30-527]], **la composition** de chaque groupe
vient d'AMO30. Ce que le fichier garde est ce qu'AMO30 ne publie pas :

- **la lignée.** Cinq des douze rassemblent des sigles différents —
  `LAREM-15, REN-16, EPR-17` ; `LR-15, LR-16, DR-17` ; `ECOLO-16, ECOS-17` ;
  `NG-15, SOC-15, SOC-16, SOC-17` ; `FI-15, LFI-16, LFI-17`. AMO30 publie un
  organe par législature et ne dit **jamais** qu'un groupe succède à un autre :
  affirmer qu'EPR-17 continue REN-16 est un jugement, pas une lecture. Les
  entrées portent d'ailleurs un `verifie_le`, date de vérification humaine ;
- **la sélection** — quels groupes méritent une fiche, question de périmètre
  éditorial, liée aux candidats déclarés ayant un mandat réel ;
- `extraction_suspendue`, une décision d'exploitation.

Un gouvernement, lui, est un organe borné qu'AMO30 nomme et date : il se
dérive, et il se dérive effectivement.

## Le déplacement

`git mv` des trois fichiers, puis **147 occurrences dans 89 fichiers** — code,
workflow, tests, documentation. Une référence oubliée casse à la lecture du
fichier, bruyamment, sans jamais produire de donnée fausse : c'est le bon sens
de l'échec pour ce genre de lot.

**Les fichiers de décision et `docs/archive/` ne sont pas réécrits.** Une
décision ne s'édite pas en place : elle dit ce qui était vrai le jour où elle a
été prise, et le chemin qu'elle cite l'était. C'est cette page-ci qui porte le
déplacement.

**Alternative écartée : garder les fichiers dans `raw_data/` et tenir une liste
d'exceptions** dans la règle de synchronisation. Elle marche, et elle demande
qu'une liste reste synchronisée avec le `git add` du workflow ; une divergence
y annulerait des données sans bruit. Un répertoire dont le nom dit la règle ne
peut pas diverger d'elle-même.
