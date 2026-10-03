# L'index des interventions porte la version du parseur qui l'a écrit (#1169)

`2026-10-03`

> **En bref** — la PR #1169 a ajouté `role_seance` au parseur Syceron et annoncé que « le corpus déjà écrit la reçoit ». Mesuré le 03/10/2026 après un run lancé **avec** la collecte des interventions (`37123323269`) : **0** `role_seance` sur les 30 244 interventions de `yael-braun-pivet`, au profil brut comme au pivot. Le run a relu l'index des interventions qu'il garde en cache, écrit avant #1169 ; la qualification de #710/#1087 lit la **présence d'une clé**, et `role_seance` n'est posée que sur les paragraphes de présidence — elle ne peut pas qualifier un index de cette façon. Correctif : `SYCERON_VERSION_INDEX`, écrite dans chaque répertoire d'index (`version_index.txt`), exigée à la relecture, et ajoutée à l'empreinte de la clé de cache (`-p1169`). Un index d'une autre version est reconstruit, et la clé change pour qu'il puisse être sauvé. **Cinquième fois** que le dépôt paie un correctif qui change le contenu d'un index sans changer sa clé (#639, #689, #997, #1019).

## Le problème

`_syceron_index_qualifie` (#719) décide si l'index en cache est réutilisable. Il
lit une tranche et cherche une clé que le parseur courant écrit sur **toutes** les
entrées — `sujet_code_grammaire` (#710), puis `id_syceron` (#1087).

`role_seance` ne se prête pas à ce test : la clé est **absente** quand l'entrée
n'est pas une présidence de séance, par construction (§2 règle 5). Un index
d'avant #1169 et un index d'après sont donc indiscernables à la clé. #1169 n'a
rien changé d'autre : l'index ancien a été jugé conforme, relu, et le run a
republié les interventions sans rôle.

| Mesuré le 03/10/2026, après le run `37123323269` | Résultat |
| --- | --- |
| interventions de `yael-braun-pivet` collectées par ce run | 30 244 |
| dont portant `role_seance` | **0** (brut et pivot) |
| clés d'une entrée de son profil brut | `collecte, date, id, id_syceron, legislature, session_ref, sujet, sujet_code_grammaire, texte, texte_tronque, type_detail, url` |

## Ce qui est décidé

**Une version de contenu, écrite et exigée.**

| Où | Quoi |
| --- | --- |
| `candidate_profile.SYCERON_VERSION_INDEX` | `"1169"` |
| `_write_syceron_index_par_acteur` | écrit `version_index.txt` dans le répertoire d'index, **avant** la bascule `os.replace` |
| `_syceron_index_qualifie` | refuse un index dont la version manque ou diffère — avant même de chercher la clé |
| `cache_an_empreinte` | l'empreinte finit par `-p<version>` ; une législature dont l'index est d'une autre version n'est pas comptée |

**Pourquoi la version entre dans la clé.** Sans elle, le run suivant restaure le
cache de la semaine par la clé exacte, juge l'index périmé, le reconstruit — et ne
peut pas le sauver, `actions/cache` ne réécrivant jamais une clé existante. Chaque
run de la semaine le reconstruirait. Avec elle, la clé attendue est nouvelle : le
cache ancien n'est restauré que par préfixe, l'index reconstruit est sauvé sous la
nouvelle clé, et les runs suivants le relisent.

**La règle, pour la suite** : toute PR qui change ce que le parseur écrit dans une
entrée incrémente `SYCERON_VERSION_INDEX` dans le même lot. Écrite dans
`docs/regles/interventions-syceron.md`.

## Ce que ça coûte, et ce qui n'est pas mesuré

Le premier run qui collecte les interventions après la fusion **reconstruit
l'index des trois législatures** : le cache ne garde que l'index, jamais les
archives — environ 650 Mo à retélécharger depuis l'Assemblée, puis le parsage.
Le temps que cela prend dans un run n'a pas été mesuré.

## Alternatives écartées

- **Qualifier par la présence de `role_seance`.** Elle n'est posée que sur les
  présidences : un index correct dont la plus petite tranche ne contient aucune
  présidence serait refusé, et un index ancien n'a aucun moyen de la porter.
- **Renommer le répertoire d'index.** Le même effet, mais le nom est repris dans
  le `path:` du cache du workflow, dans l'empreinte et dans le portail : quatre
  endroits à garder d'accord, contre une constante.
- **Purger le cache à la main.** Marche une fois, et laisse le défaut entier pour
  le prochain champ.
