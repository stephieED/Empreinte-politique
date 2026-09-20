<a id="index-dossiers-europeens-901"></a>
# Ce qui manquait aux amendements européens n'était ni une collecte ni une lecture, mais un référentiel (#901) (2026-09-14)

`2026-09-14`

> **En bref** — la fiche de `raphael-glucksmann` affiche « 590 amendements · **0 dossiers** ». J'ai d'abord conclu que rien ne lisait `amendement_non_resolu.texte_vise`. **C'était faux** : `pivotAdapter.js` le lit et le projette, la session interface l'a vérifié. Le `texte_vise` est là, sur **100 %** des 7 303 amendements européens — mais `resolveDossier` le cherche dans l'index **français**, ne l'y trouve pas, et `"2021/0136(COD)"` reste un code de procédure sans titre attaché, que l'écran ne peut afficher qu'en brut. `pivot_data/dossiers_europeens.json` est ce référentiel : **355 des 367** références visées, **125 Ko**.

## 1. Trois diagnostics successifs, et seul le troisième était juste

| Étape | Diagnostic | Verdict |
| --- | --- | --- |
| L'issue #901 | « une entrée européenne ne porte que trois clés » | faux : `amendement_non_resolu` en porte dix, quatre à 100 % |
| Mon instruction | « rien ne lit `texte_vise` » | **faux** : `pivotAdapter.js` le lit et le projette |
| La session interface | « ce qui manque est un référentiel » | **juste** |

La leçon vaut au-delà de ce lot : **un symptôme à l'écran ne nomme pas sa cause**. « 0 dossiers » pouvait signifier trois choses — pas collecté, pas lu, pas résolu — et j'ai tranché deux fois sans ouvrir le code qui affiche. Le compteur a d'ailleurs sa propre règle, écrite : `profilCandidat.js:1011` pose que la clé est `dossier_id` **seul**, jamais un repli sur `texte_vise`. C'est un arbitrage, pas un oubli.

## 2. Ce que l'index porte, et ce qu'il refuse

Référence → titre, type de procédure, stade, URL de la fiche officielle. Mesuré le 14/09/2026 :

| | |
| --- | ---: |
| Références distinctes visées par les 7 303 amendements | **367** |
| Résolues dans `ep_dossiers` | **355** (96,7 %) |
| Amendements ainsi couverts | **6 925** (94,8 %) |
| Poids | **125 Ko** |

**Les 12 non résolues sont toutes de 2024-2025** : le dump des dossiers est plus ancien que celui des amendements. C'est une absence **datée**, que le script énumère sur la sortie d'erreur — elle n'est ni comblée ni tue (§2 règle 5).

**Les titres ne sont pas traduits.** La source publie en anglais ; traduire un intitulé législatif produirait un titre que personne n'a écrit et qu'aucune source ne confirme (§2 règle 2).

**Le stade passe par la table de `textes_portes[]`** — `normalize_parltrack_dumps.STADE_UE_PAR_LIBELLE_SOURCE`, seule fabrique de cette correspondance. La recopier ici ferait diverger deux tables le jour où la source ajoute une valeur.

## 3. Trois espaces de noms, et aucun ne déborde sur l'autre

`an:` nomme un scrutin de l'Assemblée, `pe:` un scrutin européen ([#901](index-scrutins-europeens-901.md)), `pe-dossier:` un dossier européen. Un test vérifie que les deux préfixes européens ne se préfixent pas l'un l'autre : `resolveDossier` et `resolveAmendement` cherchent dans des tables différentes, et une collision ferait résoudre un dossier comme un scrutin.

La `source_url` pointe vers `oeil.secure.europarl.europa.eu`, la fiche de procédure officielle du Parlement — une source primaire, pas l'agrégateur qui nous l'a fait connaître.

## 4. Ce que ce lot ne fait pas

**Il ne remplit pas `dossier_id`** sur les amendements européens. L'interface décide si elle joint par `texte_vise` et sous quelles conditions ; le pipeline fournit la table, pas la politique d'affichage. Et `profilCandidat.js:1011` a déjà tranché que le compteur de dossiers n'accepte pas ce repli — le changer serait un arbitrage éditorial, pas une conséquence de cet index.
