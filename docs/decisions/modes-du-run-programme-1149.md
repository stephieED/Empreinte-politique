<a id="modes-du-run-programme-1149"></a>
# Un run programmé collecte comme un run complet, et les deux modes se lisent en un seul endroit (#1149) (2026-09-30)

`2026-09-30`

> **En bref** — un déclenchement `schedule` ne reçoit aucun input (#1054), donc les cases `collect_interventions` et `collect_dossiers_legislatifs` y valaient `false` : **la couverture des prises de parole n'avançait jamais toute seule**, ce qui a laissé une fiche de candidat déclaré en régime « extrait » jusqu'au 26/09 ; `epingler-le-code` publie désormais les deux modes effectifs du run, et les **seize** lectures du workflow passent par ses sorties — pas par une expression recopiée, **parce que des clés de cache en dépendent**. Le cron passe de 4 h à **20 h heure de Paris**.

## 1. Ce que le run nocturne ne faisait pas

Les défauts du formulaire sont `false` pour les deux cases, et un `schedule` ne
fournit rien : le run programmé tournait donc en mode minimal. Conséquence
mesurable : `olivier-becht`, seul candidat déclaré publié en régime « extrait »,
y serait resté indéfiniment — seule une collecte d'interventions le rattrape, et
elle ne partait jamais seule.

## 2. Pourquoi une sortie de job, et pas l'expression répétée

`inputs.collect_interventions` était lu à **quinze** endroits,
`inputs.collect_dossiers_legislatifs` à **cinq**. Recopier
`(inputs.X || github.event_name == 'schedule')` partout aurait marché — et aurait
laissé seize occasions d'en oublier une.

**Le coût d'un oubli n'est pas théorique** : ces lectures incluent des **clés de
cache**. Une clé restée sur l'ancienne forme restaurerait l'entrée d'un autre
mode, `actions/cache` sauterait la sauvegarde de ce que le run vient de
construire, et chaque shard retéléchargerait ce que le premier avait obtenu.
C'est [[cache-cle-amendements-separee]] (#424), puis #505, puis #657 : **trois
fois le même défaut**, à chaque fois des centaines de Mo, à chaque fois sans
aucun signal.

`epingler-le-code` précède tous les jobs concernés et n'a pas d'autre dépendance.
Il publie :

```yaml
interventions: ${{ inputs.collect_interventions || github.event_name == 'schedule' }}
dossiers_legislatifs: ${{ inputs.collect_dossiers_legislatifs || github.event_name == 'schedule' }}
```

Le contexte `needs` est par ailleurs le seul, avec `github` et `inputs`, que
`strategy` et `timeout-minutes` acceptent — les deux endroits où ces modes
entrent.

## 3. Ce que ça coûte, mesuré

Run `36247828382` (26/09, les deux cases cochées) contre `36181368061` (25/09,
mode par défaut) :

| | Par défaut | Complet | Écart |
| --- | --- | --- | --- |
| Durée totale | 58 min | **100 min** | + 42 min |
| Travail réel cumulé | 1 427 + 4 266 s | 1 563 + 5 009 s | **+ 9 min** |
| Durée d'un shard `extract-an` | 18-76 s | 27-103 s | négligeable |

**La collecte elle-même ne coûte que ~9 minutes.** Les 33 autres viennent des
deux bornes de #1137, qui s'appliquent justement dans ces modes :
`extract-an` repasse en série (la clé de cache change de forme, et la sonde ne
sait pas la composer), le roster repasse à deux vagues (les dossiers font
télécharger). **Les deux bornes sont conservées** : la première demanderait des
dépendances dans un job à `timeout-minutes: 5`, la seconde protège une rafale
réseau réelle. Elles restent ouvertes dans #1149.

## 4. L'heure

`0 18 * * *` — **20 h à Paris** en heure d'été, 19 h en heure d'hiver. GitHub ne
lit que l'UTC et aucune valeur fixe ne suit le changement d'heure.

**Et l'heure dit quand le run devient éligible, pas quand il démarre** : les deux
premiers runs programmés ont été servis avec **5 h 40** puis **6 h 19** de
retard. C'est mesuré, deux fois sur deux, et ce n'est pas un réglage.

## 5. Les gardes

`tests/test_ci_modes_du_run_1149.py` refuse toute lecture directe de
`inputs.collect_*` hors de la définition, exige que les jobs lecteurs dépendent
d'`epingler-le-code` — une sortie lue sans `needs:` s'évalue à la chaîne vide,
donc à « non », sans erreur ni log —, et vérifie que les sorties sont bien lues.
Un cinquième test tient le motif lui-même : les commentaires du workflow
**citent** les inputs qu'ils expliquent, et un garde qui ne les écarterait pas
échouerait sur sa propre justification.

Vérifié par mutation : une clé de cache remise en `inputs.collect_interventions`
fait tomber le garde.

Six fichiers de tests lisaient l'ancienne forme ; ils lisent désormais deux
constantes de `tests/_outils_ci.py`, pour que la source reste unique côté tests
aussi.

## 6. L'alternative rejetée

**Un `env:` au niveau du workflow.** Plus lisible, et inutilisable : le contexte
`env` n'existe ni dans `timeout-minutes`, ni dans `strategy`, ni dans le `if:`
d'un job — exactement les endroits où ces modes décident.
