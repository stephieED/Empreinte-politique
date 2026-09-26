<a id="defauts-d-inputs-sur-declenchement-programme-1054"></a>
# Un déclenchement programmé ne reçoit aucun input : les défauts s'appliquent en bash (#1054) (2026-09-26)

`2026-09-26`

> **En bref** — sur un `schedule:`, GitHub ne fournit **aucune** valeur d'input et les `default:` de `workflow_dispatch` ne s'appliquent pas ; mesuré sur les **douze** inputs du formulaire, **deux** divergeaient — `existing_profiles` et `add_uncovered_members`, tous deux lus par le bloc de décision du job roster —, et vides ils tombaient sur `--refresh-existing`, c'est-à-dire « rafraîchir l'existant et **ne plus jamais ajouter un membre non couvert** », sans erreur ni log alarmant ; correctif : le défaut s'applique en bash (`${VAR:-…}`), le geste que `incomplete_read_threshold` et `roster_limit` utilisaient déjà. **Le cron est activé dans le même lot**, à la cadence déjà écrite dans le fichier (`0 6 * * *`, UTC), et un test refuse désormais un cron actif sans ces défauts.

## 1. Ce qui empêchait de décommenter le cron

`generate-data.yml` porte depuis longtemps un `#schedule: - cron: '0 6 * * *'`,
commenté. Le décommenter aurait changé le comportement **en silence**.

Sur un déclenchement `workflow_dispatch`, GitHub applique les `default:`
déclarés. Sur un déclenchement `schedule`, il ne fournit **rien** : chaque
`${{ inputs.<nom> }}` rend la chaîne vide.

## 2. La mesure : deux inputs sur douze

Un input est **divergent** quand sa valeur vide ne produit pas ce que son
`default:` promet.

| Cas | Divergent ? |
| --- | --- |
| Booléen `default: false` (`cold_start`, `collect_interventions`, `collect_dossiers_legislatifs`, les quatre `allow_*`) | non — vide est *falsy*, donc identique |
| `test_slugs`, sans défaut | non — vide signifie « aucune restriction », ce qui est le mode ordinaire |
| `incomplete_read_threshold` (`3`), `roster_limit` (`0`) | **déjà protégés** en bash (`${THRESHOLD:-3}`, vide et zéro traités ensemble) |
| **`existing_profiles` (`refresh`)** | **oui** |
| **`add_uncovered_members` (`true`)** | **oui** |

Les deux divergents sont lus par le même bloc, celui qui décide la population du
job roster. Vides, il descend jusqu'au dernier `elif` :

```
EXISTING_PROFILES=""  → n'est pas "leave-as-is"
ADD_UNCOVERED=""      → n'est pas "true"   ⇒ POP_FLAG=(--refresh-existing)
```

`--refresh-existing` ne traite **que** l'existant. Un run programmé aurait donc
rafraîchi les profils déjà écrits et n'aurait plus jamais écrit le premier
profil d'un membre non couvert. **Aucune erreur, aucun log alarmant : une
couverture qui se figeait.** C'est le mode de défaillance de #562 — le code
juste, la donnée fausse, et rien pour le dire.

## 3. Décision

Le défaut s'applique **dans le script du step**, pas dans le formulaire :

```bash
EXISTING_PROFILES="${EXISTING_PROFILES:-refresh}"
ADD_UNCOVERED="${ADD_UNCOVERED:-true}"
```

Même geste que les deux inputs déjà protégés — ce lot n'invente rien, il
généralise. `OVERWRITE`, calculé côté GHA (`inputs.existing_profiles ==
'overwrite'`), rend `false` à vide, ce qui est exactement ce que `refresh` doit
produire : il n'avait pas besoin d'être touché.

**La règle qui en sort**, et qui vaut pour tout input qu'un job lit : *un
`default:` qui n'existe que dans le formulaire est une promesse que le
formulaire ne peut pas tenir.* → `docs/regles/ci.md` §3b.

## 4. L'activation, et ce que le lot ne fait pas

**Le cron est activé**, à la cadence qui était déjà écrite dans le fichier :
`0 6 * * *`, un passage quotidien. La ligne existait, commentée, et elle est
reprise **telle quelle** — l'horaire n'était pas une question ouverte, il
attendait seulement que le filet du §3 existe.

Deux choses que le bloc `on:` dit maintenant, parce qu'elles ne se lisent pas
dans une expression cron : l'heure est en **UTC**, GitHub ne connaissant pas
d'autre fuseau, et un déclenchement programmé peut être **servi en retard** en
heure de pointe. C'est une cadence, pas un rendez-vous.

Il ne touche pas à la **publication du code**, qui reste manuelle : un
job qui publierait l'arbre entier devrait le cloner (paquet git de 6,1 Gio,
arbre de 8,0 Go, contre ~14 Go de disque sur un runner) et pousserait du code
que personne n'a relu.

## 5. Les gardes

`tests/test_ci_inputs_workflow.py` **exécutait déjà** le vrai bloc de décision
pour les six combinaisons du formulaire. Trois tests s'y ajoutent :

| Test | Ce qu'il tient |
| --- | --- |
| `test_un_declenchement_programme_se_comporte_comme_le_formulaire` | Le septième cas — inputs vides — produit **exactement** ce que le formulaire produit sur ses défauts, et le log affiche les valeurs effectives (la seule trace dont `retry-generate-data.yml` dispose) |
| `test_les_defauts_en_bash_sont_ceux_du_formulaire` | Les deux valeurs sont écrites à deux endroits ; elles doivent dire la même chose, sinon le formulaire annonce un comportement que le cron ne tient pas |
| `test_aucun_autre_input_ne_diverge_a_vide` | La mesure du §2, rejouée : elle dira qu'un **treizième** input est arrivé sans protection |

Les deux régressions ont été vérifiées **par mutation** du workflow : retirer
les défauts bash (l'état d'avant ce lot) et les faire diverger du formulaire
font tomber les tests.

Au passage, un helper remplace des bornes en dur : plusieurs tests lisaient le
`default:` d'un input avec `index("      cold_start:")`, ce qui casse dès qu'un
input est inséré entre les deux.

## 6. L'alternative rejetée

**Déclarer les défauts une seconde fois dans un `env:` de workflow**, pour
n'avoir qu'un endroit à lire. Rejeté : `env:` ne sait pas dire « cette valeur si
l'input est vide » — il faudrait de toute façon un `||` par input, et
l'expression GHA `0 || 3` rend `3`, ce qui est précisément le piège que le
commentaire de `incomplete_read_threshold` documente depuis #511. Le bash, lui,
distingue vide de zéro.
