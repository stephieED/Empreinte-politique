<a id="refonte-inputs-workflow"></a>
# Le formulaire de lancement disait pourquoi, pas quoi (2026-08-20)

`2026-08-20`

> **En bref** — un formulaire de lancement dit quoi, pas pourquoi : 575 mots de description ramenés à des libellés.

Les neuf inputs de `workflow_dispatch` portaient **~575 mots** de description,
jusqu'a 138 pour `roster_extraction_limit` seul. Elles avaient grossi par
sedimentation : chaque incident y ajoutait son rationale, ses numeros d'issue
et ses mesures.

Un formulaire de lancement se lit sous contrainte de temps, souvent au moment
ou quelque chose ne va pas. Un essai y est ignore. Les descriptions ne disent
plus que **ce que fait** l'input ; le pourquoi vit ici, atteignable par ancre.

## Renommage, en anglais

Demande explicite. Les noms melangeaient trois conventions (`fresh_run`,
`tolerer_pertes_profils`, `max_pages`).

| avant | apres |
| --- | --- |
| `fresh_run` | `cold_start` |
| `overwrite_profiles` | inchange (deja anglais et exact) |
| `roster_refresh_existing` | `refresh_existing_only` |
| `threshold` | `incomplete_read_threshold` |
| `tolerer_pertes_profils` | `allow_declared_losses` |
| `tolerer_references_orphelines` | `allow_broken_references` |
| `extract_interventions` | `collect_interventions` |
| `max_pages` | `nosdeputes_max_pages` |
| `roster_extraction_limit` | `roster_limit` |

## Les trois confusions traitees

**`roster_limit` s'applique PAR SHARD.** Dit en une ligne dans la description,
la ou 138 mots l'enterraient. C'est ce qui explique le forcage a un seul shard
des qu'elle est non nulle.

**`cold_start` implique `overwrite_profiles`.** Les deux booleens se
recouvraient sans que rien ne le dise ; cocher les deux n'a jamais eu de sens.
Chaque description nomme desormais l'autre.

*Alternative ecartee* : fusionner les deux en un `type: choice` a trois modes
(incremental / overwrite / cold_start). C'est le design correct — il rend la
combinaison absurde impossible par construction — mais `fresh_run` compte **22
usages** et `overwrite_profiles` **8**, avec des conditions composees. Une
refonte de logique conditionnelle a l'occasion d'une tache de nommage aurait
melange deux risques. A rouvrir separement.

**Les deux tolerances ne se ressemblaient que par le prefixe.** `allow_declared_losses`
couvre une perte legitime et **declaree** ; `allow_broken_references` couvre une
reference cassee, qui n'a jamais de cas d'emploi normal. Les nouveaux noms les
opposent au lieu de les rapprocher, et la description du second porte la
distinction explicitement (verifiee par test).

## Une regression trouvee en route, et le garde-fou qui manquait

`retry-generate-data.yml` ne relit pas les inputs du run precedent — l'API ne
les expose pas — il les **reconstruit en analysant les logs**, puis redeclenche
par `gh workflow run -f nom=valeur`. Ce couplage est reel mais invisible : rien
dans l'un ne reference l'autre.

Deux pannes silencieuses ont ete constatees le meme jour :

1. **`-f workers=...` survivait a la suppression de l'input** (#workers-fige-a-1,
   une heure plus tot). Le dispatch aurait echoue en 422 « Unexpected inputs
   provided » — decouvert seulement le jour ou une relance devient necessaire.
2. **Au renommage, les lectures `steps.inputs.outputs.X` ont ete mises a jour
   mais pas les `echo "X=..." >> $GITHUB_OUTPUT`.** La relance serait repartie
   sur les valeurs par defaut au lieu de celles du run d'origine, sans erreur ni
   trace : un run `cold_start=true` relance en incremental. C'est exactement la
   regression que le commentaire de la relance dit avoir deja corrigee une fois.

`tests/test_ci_inputs_workflow.py` verifie desormais les deux sens du contrat,
plus le plafond de 40 mots par description. Le premier test a ete verifie en
echec sur l'etat reel de `main`.

Nettoyage associe : l'extraction de `workers` depuis le log d'`extract-senat`,
sa sortie sans consommateur et les trois commentaires devenus faux ont ete
retires. Les cinq noms d'etape `(fresh_run uniquement)` sont alignes — la
relance en selectionne un **par son nom**.

