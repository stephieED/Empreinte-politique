# L'index des décisions est généré, il ne s'édite plus (#840)

`2026-09-11`

> **En bref** — `docs/technical_decisions.md` était maintenu à la main et **tous les lots y écrivaient au même endroit**, une ligne insérée en tête : deux branches parallèles conflictaient systématiquement — **quatre rebases en une heure** le 10/09/2026, sur des lots qui ne se recouvraient pas, et une résolution manuelle dans l'interface GitHub ne pouvait pas régénérer `decisions-par-module.md`, donc les tests tombaient ensuite sans que rien n'ait été mal fait. L'index est désormais **produit** depuis les fichiers de `docs/decisions/`, chacun portant sa date et son résumé `> **En bref** — …` : un lot n'écrit que **son propre fichier**, que personne d'autre ne touche, et le conflit devient **structurellement impossible** au lieu d'être seulement rare. **La migration est prouvée sans perte** — index régénéré comparé champ par champ à l'ancien sur les 279 décisions : **0** date changée, **0** résumé altéré, **0** ancre perdue, une ancre **gagnée** (`gouvernement-textes-statut`, qui existait dans son fichier sans être indexée) et 14 titres devenus plus précis, l'index ayant simplifié `(#683, lot 4)` en `(#683)`. Le résumé vit **dans** la décision et non à côté, parce que la lecture chronologique du projet a de la valeur pour qui ouvre le fichier ; les alias d'ancres deviennent de **vraies** ancres HTML, si bien qu'un lien `decisions/<nom>.md#<alias>` atterrit enfin quelque part. **Écarté** : insérer en fin plutôt qu'en tête — deux ajouts au même endroit conflictent de la même façon —, et une stratégie de merge dans `.gitattributes`, qui ferait disparaître le conflit **en perdant une ligne en silence**.

## Le problème

Deux fichiers étaient modifiés par tous les lots, toujours au même endroit :
`docs/technical_decisions.md` en tête, les gros fichiers de tests en fin. Git ne
peut pas deviner lequel des deux ajouts passe en premier — il refuse et demande
un arbitrage humain, à chaque fois.

Mesuré le 10/09/2026 : chaque merge remettait la PR suivante en conflit. #834
mergée → #835 en conflit ; #835 mergée → #837 ; #837 mergée → #838. Le coût est
linéaire dans le nombre de PR ouvertes, et il ne dépend **pas** de ce que les
lots font.

Un troisième effet expliquait pourquoi résoudre dans l'interface GitHub ne
suffisait pas : `docs/decisions-par-module.md` est **produit par un script**. Le
résoudre à la main donne un fichier qui ne correspond plus à ce que le script
rendrait, et son test le détecte.

## La décision

`docs/technical_decisions.md` rejoint `docs/decisions-par-module.md` : **un
fichier généré, jamais édité**.

Chaque décision porte de quoi produire sa ligne :

```markdown
# Le titre de la décision (#issue)

`2026-09-11`

> **En bref** — le résumé qui devient la ligne d'index.
```

`scripts/generer_index_decisions.py` les assemble, de la plus récente à la plus
ancienne. `--verifier` ne touche à rien et sort 1 si l'index a dérivé.

## Ce qui a été préservé, et prouvé

Le résumé rédigé de chaque ligne **a de la valeur en soi** : c'est la lecture
chronologique du projet, souvent plus utile que le fichier de décision. Il ne
devait pas disparaître dans l'opération — il a été **déplacé**, pas réécrit, et
il est désormais lu **aussi** par qui ouvre le fichier.

Vérification, index régénéré comparé champ par champ à l'ancien :

| Sur les 279 décisions | |
| --- | ---: |
| Fichiers indexés | 279 → **279**, les mêmes |
| Dates changées | **0** |
| Résumés altérés | **0** |
| Ancres perdues | **0** |
| Ancres gagnées | **1** |
| Titres modifiés | 14 |

L'ancre gagnée est `gouvernement-textes-statut` : elle existait dans son fichier
et le dépôt la citait, mais l'index ne la portait pas. Les 14 titres deviennent
**plus précis** — l'index avait simplifié `(#683, lot 4)` en `(#683)`, et c'est
maintenant le titre du fichier qui fait foi, nettoyé du suffixe de date qui
doublait la ligne juste en dessous.

## Deux pièges rencontrés à la migration

**Une ancre vivait avant le titre.** La première version reconstruisait le
fichier depuis son `#` de niveau 1 et perdait tout ce qui le précédait —
`<a id="gouvernement-textes-statut"></a>` a disparu, et
`test_toute_decision_citee_dans_le_depot_existe` l'a vu. La migration préserve
désormais le préambule.

**Les alias devaient être de vraies ancres.** Une première version les portait
dans un commentaire `<!-- alias: … -->`, ce que le test ne reconnaissait pas —
à juste titre : un lien `decisions/<nom>.md#<alias>` doit atterrir quelque part.
Ils sont désormais de vraies balises d'ancre dans le fichier, et le générateur
les y lit. Des centaines de liens `technical_decisions.md#<ancre>` existent hors du
dépôt, dans des commentaires d'issues non réécrivables : une ancre ne se renomme
ni ne se supprime.

## Ce que ce lot ne fait pas

**Les fichiers de tests.** C'est l'autre moitié du problème, et elle n'a pas de
génération possible — seulement une convention que le dépôt applique déjà à
moitié : **un fichier de tests par lot**, nommé par son issue.
`tests/test_controle_perte_echanges_823.py` et
`tests/test_urls_explications_vote_827.py` n'ont jamais conflicté, étant neufs.
Le conflit du 10/09 est venu de tests ajoutés à la fin de
`tests/test_group_profile.py`, partagé par tous les lots touchant ce module.

## Écarté

- **Insérer en fin d'index plutôt qu'en tête** : deux ajouts au même endroit
  conflictent de la même façon.
- **Une stratégie de merge dans `.gitattributes`** : ferait disparaître le
  conflit en perdant **silencieusement** une ligne, ce qui est pire.
- **Cesser de committer les fichiers générés** : ils sont lus hors session, et
  les tests qui les gardent existent pour qu'ils ne dérivent pas.

Suite complète à 4 449, 0 échec.
