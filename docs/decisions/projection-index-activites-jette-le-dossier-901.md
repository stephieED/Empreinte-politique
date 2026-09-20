<a id="projection-index-activites-jette-le-dossier-901"></a>
# La projection d'un index est une fabrique, et elle jetait la référence de dossier (#901) (2026-09-14)

`2026-09-14`

> **En bref** — Corriger les deux fabriques de textes portés européens n'a rien
> changé au corpus : le run suivant a republié **12 stades sur 383**. Le champ
> était détruit une étape plus haut, dans la projection à six clés de
> `build_activities_index`. Un motif d'absence unanime — 371 sur 371 — était le
> symptôme, et les tests ne pouvaient pas le voir parce qu'ils fabriquaient
> eux-mêmes le champ manquant.

## Contexte

#901 publie le stade procédural d'un texte porté européen. Le lot a d'abord
corrigé `_make_texte_porte` (les dossiers dont la personne est rapporteure), puis
— constatant 12 stades sur 383 — `_make_texte_porte_activite` (les rapports,
avis et propositions de résolution). La décision
[deux fabriques](deux-fabriques-textes-portes-europeens-901.md) enregistre ce
second geste.

Le run `34853965676` (14/09/2026, 16 h 11 → 18 h 05 Paris, commit `1e503dd46`)
devait le vérifier. Il a publié **12 stades sur 383**, à l'unité près le chiffre
d'avant.

## Ce que la mesure a dit

Les 371 entrées sans stade portaient toutes le même motif, et **toutes** est le
mot qui compte :

| Mesure sur `1e503dd46` | Valeur |
| --- | ---: |
| textes portés européens publiés | 383 |
| avec un stade | 12 (3,1 %) |
| sans stade, motif `activite_sans_dossier` | **371 / 371 (100 %)** |
| sans stade et sans motif | 0 |

La fabrique avait donc bien tourné — elle déclarait son absence, conformément à
`AGENTS.md` §2 règle 5. Mais un motif renseigné à **100 %** ne décrit pas une
source : il décrit un chemin de code. La source, mesurée le même jour sur les
4 585 fiches du dump `ep_mep_activities` (population : toutes les fiches du
dump, pas les 7 candidats déclarés à identifiant européen), porte `dossiers`
sur `REPORT` 9 593 / 9 935 (96,6 %) et `MOTION` 44 684 / 60 362 (74,0 %).

## La cause

`_make_texte_porte_activite` lit `entree["dossiers"]`. Mais `entree` ne vient pas
du dump : elle vient de `build_activities_index`, qui **projette** chaque entrée
sur six clés — `titre`, `date`, `reference`, `source_url`, `legislature`,
`texte`. `dossiers` n'en faisait pas partie.

**Une projection est une fabrique.** On avait cherché « tous les endroits où
l'objet est fabriqué » et trouvé deux fonctions nommées `_make_*`. La troisième
ne portait pas ce nom et ne ressemblait pas à une fabrique : c'est une boucle
d'indexation, écrite pour un tout autre besoin, et qui décide pourtant de ce que
les fabriques avales pourront lire.

## Décision

1. **`build_activities_index` conserve `dossiers`.** Le commentaire sur place
   nomme la distinction que la suite du code doit tenir : `reference` est le
   **document** (`A9-0240/2022`), `dossiers` la **procédure**
   (`2022/2852(RSP)`). Se rabattre sur la première interrogerait l'index des
   stades avec une clé qu'il n'a jamais.

2. **`VERSION_SCHEMA_INDEX` passe de 2 à 3.** Sans cela le correctif n'aurait
   atteint aucun run : `build_activities_index` relit l'index caché tant que sa
   date dépasse celle du dump, et le cache CI
   `public-data-cache-parltrack-<semaine>` restaure les deux. Le dump n'étant pas
   retéléchargé, l'index amputé aurait resservi une semaine entière — code juste,
   corpus inchangé. L'empreinte est portée par le **nom du fichier** exactement
   pour ça : faire rater le cache plutôt que le faire mentir (#510, #505).

3. **La chaîne est tenue de bout en bout par un test qui ne fabrique aucune
   entrée intermédiaire** : `tests/test_projection_activites_conserve_dossiers_901.py`
   part d'un dump, passe par l'index, et regarde ce qui sort. Les cinq
   assertions échouent quand on retire la ligne de projection.

4. **`activite_sans_dossier` reste atteignable, et doit le rester.** 26 % des
   `MOTION` et 89 % des `COMPARL` ne visent aucune référence : c'est un fait de
   la source. Ce qui était faux, c'est qu'il était unanime.

## Alternative rejetée

**Déduire la référence de procédure depuis `reference`, la référence de
document.** Les deux nomenclatures ne se déduisent pas l'une de l'autre, et un
appariement par ressemblance rattacherait un stade au mauvais dossier —
`AGENTS.md` §2 règle 1 et règle 2. Une référence absente reste absente, déclarée
par son motif.

## Ce que ça apprend sur les tests

`tests/test_stade_textes_europeens_activites_901.py` passait pendant tout
l'incident. Il appelle les fabriques sur des entrées **que le test construit**,
`dossiers` compris : il vérifie qu'une fonction sait lire un champ, jamais
qu'elle le reçoit.

C'est le défaut que `AGENTS.md` nomme déjà pour l'audit (#726) — *une fixture
décrivant le monde comme le code l'imagine ne peut pas révéler que le monde a
bougé*. Il vaut ici pour une chaîne interne, où rien n'avait bougé chez la
source : c'est notre propre projection qui mentait, et une fixture écrite à la
main la court-circuitait. **Dès qu'un test fabrique l'entrée d'une étape, il
cesse de couvrir ce que l'étape d'avant lui transmet.**
