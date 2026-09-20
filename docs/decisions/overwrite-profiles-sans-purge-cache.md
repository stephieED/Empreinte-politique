<a id="overwrite-profiles-sans-purge-cache"></a>
# `overwrite_profiles` : écraser les profils sans purger le cache (2026-08-19)

`2026-08-19`

> **En bref** — écraser les profils sans purger le cache : deux axes distincts, déjà.

**Contexte** : la correction de clé des amendements (#440, préalable à #431)
impose un premier run **en écrasement**. Les profils committés n'ont pas de
champ `uid` ; la nouvelle clé de fusion est `uid or source_url or (numero,
texte_vise, date)`. Le même amendement reçoit donc deux clés différentes avant
et après, et la fusion additive le compte **deux fois**. Vérifié en appelant
`merge_lists_by_key` : un amendement en entrée de chaque côté, deux en sortie.

Sur 4,2 millions de paires, cela doublerait le volume et fausserait tous les
comptages, agrégats de groupe compris.

**Le piège** : le seul mode d'écrasement exposé en CI était `fresh_run`, qui
fait aussi `rm -rf .cache`. Or purger le cache oblige à re-télécharger les
archives AN — ~300 Mo — auprès d'une source dont l'indisponibilité a bloqué
trois chantiers en deux jours ([[cache-cle-amendements-separee]] #424,
[[gouvernement-textes-non-ecrasement]] #427, et la reconstruction des index
figés de #440, arrêtée plusieurs heures). On aurait échangé un risque de
doublons contre un risque de run entièrement bloqué.

**Décision** : nouvel input `overwrite_profiles`, qui pose `--no-merge` sans
rien purger.

| `fresh_run` | `overwrite_profiles` | `--no-merge` | purge cache | `--merge-existing` |
| --- | --- | --- | --- | --- |
| false | false | non | non | oui |
| false | **true** | **oui** | **non** | non |
| true | false | oui | oui | non |

`overwrite_profiles` agit aussi sur les profils de groupe (`--merge-existing`
désactivé) : réintégrer des membres depuis un fichier produit avec l'ancien
schéma ramènerait précisément les données que l'écrasement vise à remplacer.

**Reconstruction par le retry** : `retry-generate-data.yml` déduit
`overwrite_profiles` de la combinaison « `--no-merge` présent dans la commande
d'extraction **et** `fresh_run` faux » — les deux seuls inputs qui posent ce
flag. Sans cela, un run préempté serait relancé en fusion additive, soit
exactement le scénario de doublons que ce mode évite. La déduction s'appuie sur
`an_log` et doit donc figurer **après** sa définition ; la placer avant la
rendrait toujours fausse, silencieusement — un test vérifie cet ordre.

**Garde-fous** : `tests/test_ci_cache_paths.py` vérifie qu'aucun step de
nettoyage n'est conditionné à `overwrite_profiles`, que tous les `MERGE_FLAG`
considèrent les deux inputs — un job qui n'en regarderait qu'un fusionnerait
pendant que les autres écrasent, produisant des doublons sur ce seul job — et
que le retry reconstruit puis transmet l'input. Vérifiés discriminants par
sabotage des trois invariants.

**Contrôle associé** : `src/audit_diff_profils.py` compare les profils
régénérés à une référence git, par profil et par champ. Écraser abandonne la
mémoire de la fusion additive, qui protège des collectes ratées — les 283
textes de la XV d'Édouard Philippe lui doivent leur survie. Le contrôle porte
sur le détail et non sur les totaux : la correction de clé fait exploser les
amendements, et ce gain masquerait n'importe quelle perte de votes.

---
