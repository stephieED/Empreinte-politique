<a id="concurrence-shards-extraction-412"></a>
# Jobs d'extraction de `generate-data.yml` : résilience au *skip*, concurrence des shards, factorisation (#412) (2026-08-18)

`2026-08-18`

> **En bref** — résilience au *skip*, concurrence des shards d'extraction, factorisation du préambule.

**Contexte** : première sous-issue d'application de la revue transversale
[[revue-workflows-ci-342]] — les 9 jobs de `.github/workflows/generate-data.yml`
relus job par job. Contrairement à l'epic, ce ticket **modifie le YAML**.

## 1. `continue-on-error:` ne protège pas d'un job *skipped*

Erreur de raisonnement partagée par tout l'historique du fichier (#222, #251,
#344, #394) : `continue-on-error: true` transforme un **échec** en non-bloquant,
mais un job *skipped* skippe ses dépendants quoi qu'il arrive. Or les deux jobs
préparatoires de matrix (`prepare-an-matrix`, `prepare-roster-matrix`) n'avaient
ni `continue-on-error:` ni repli : leur échec — ou un matrix simplement **vide**
— skippait `extract-an`, donc `extract-roster-groupes`, donc `merge-and-pivot`.
**Le run entier ne produisait rien**, exactement l'inverse de ce que l'en-tête
de `merge-and-pivot` affirmait depuis #222.

Correctif, en trois pièces qui ne valent qu'ensemble :

- `if: ${{ !cancelled() }}` sur `extract-roster-groupes` et `merge-and-pivot` :
  seule une annulation externe arrête encore la chaîne. C'est la formulation qui
  rend enfin vrai le « on fusionne ce qui a réussi » du fichier.
- Repli de forme sur les matrix : `fromJson(… || '[]')` pour `extract-an`,
  `fromJson(… || '[0]')` (et `shard_total || '1'`) pour `extract-roster-groupes`
  — sans quoi `fromJson('')` échoue à l'évaluation, avec un message que
  l'interface Actions ne rattache à rien.
- `set -euo pipefail` dans le step de calcul de `prepare-an-matrix` (celui de
  `prepare-roster-matrix` l'avait déjà) : un `python3` en échec y écrivait
  silencieusement `slugs=` dans `$GITHUB_OUTPUT`. Mieux vaut échouer là où la
  cause est lisible.

Un matrix vide reste possible (aucun candidat à slug résolvable) : il est
désormais **annoncé** — `::warning::` + bloc de résumé — au lieu de se déduire
d'un job grisé.

*Alternative rejetée* : donner `continue-on-error: true` aux jobs préparatoires.
Ça ne traite rien — c'est précisément le mécanisme qui ne couvre pas le skip.

## 2. `max-parallel: 1` : conservé, mais la justification écrite était fausse

Question laissée ouverte par #342, tranchée ici. Le plafond venait de #222, en
mitigation d'un **plafond de dépense Actions suspecté** (#221) —
[[verification-billing-actions]] a infirmé cette hypothèse (quota non atteint,
$0 facturé, cause retenue = préemption d'infrastructure). Et le « pic de 4 jobs
simultanés » qu'il prétendait préserver est **6** depuis #344/#394.

Décision : **conserver `max-parallel: 1`** sur les deux matrix, sur les deux
arguments qui tiennent encore, et eux seuls —

1. **Cache** (l'argument réellement valide de #222) : les shards se passent le
   cache AN chaud de proche en proche ; en parallèle, chacun retéléchargerait
   les dumps AN Open Data.
2. **Prudence réseau** : 8 shards parallèles frapperaient simultanément les
   mêmes sources AN/NosDéputés.

Coût assumé et chiffré : ~63 min de temps mur en run complet du roster contre
~8 min en parallèle ([[budget-roster-mesure]]). Ce que le shardage apporte à
`max-parallel: 1` est la **borne de perte sur préemption** (63 min → ~8 min),
pas la vitesse — c'est aussi ce que #394 achetait réellement.

*Alternative rejetée* : ouvrir le parallélisme maintenant. Le gain (55 min de
temps mur sur un run complet qui n'est pas encore la configuration par défaut,
`roster_extraction_limit=20`) ne justifie pas d'engager en même temps un
changement de profil de charge réseau et une hypothèse de cache **non validée**
(§3). À rouvrir si §3 se confirme et que le run complet devient la norme.

## 3. Réserve tranchée depuis : le cache AN n'était effectivement plus réécrit

> **Confirmée et corrigée par #424** (run `32136438841`, 2026-08-18). Le log de
> post-job attendu ci-dessous a été obtenu, sur les 8 shards `extract-an` et le
> shard roster. Coût mesuré : **~438 Mo re-téléchargés par run**. Voir
> [[cache-cle-amendements-separee]]. Le texte d'origine est conservé tel quel
> ci-dessous : la démarche — ne pas corriger sur une hypothèse d'analyse
> statique, exiger un log réel — reste la bonne, et c'est elle qui a produit le
> critère d'acceptation du correctif.

### Texte d'origine

`extract-amendements-an` s'exécute en premier et écrit la **clé exacte**
`public-data-cache-an-<semaine>`. Les jobs suivants restaurent donc cette clé
exacte — et `actions/cache` **saute la sauvegarde post-job dès qu'il y a eu
exact key hit**. Si c'est bien le cas ici, ce que télécharge `extract-an`
(`acteurs_an`, `scrutins_an`, `dossiers_an`, ~290 Mo) n'est jamais persisté dans
la clé de la semaine, et chaque shard de chaque run le re-télécharge.

**Aucun correctif appliqué** : la conclusion dépend d'un log de post-job réel
(« Cache hit occurred on the primary key, not saving cache »), qu'aucun run
n'a encore fourni. La réserve est écrite dans le YAML, à l'endroit exact
(commentaire du `actions/cache` d'`extract-an`), avec le correctif envisagé :
clé propre à `extract-amendements-an` (`public-data-cache-amendements-*`, path
`.cache/amendements_an`), en laissant `…-an-*` à `extract-an`. C'est presque la
proposition fermée en #374, mais pour une raison différente — là-bas réduire le
volume restauré, ici restaurer la capacité d'écriture.

## 4. Deux actions composites locales, et pas une de plus

`.github/actions/bootstrap-extraction` (horodatage + relevé mémoire OOM +
`setup-python` + `pip install`) et `.github/actions/job-diagnostics` (blocs de
résumé « job annulé » / « job en échec »), appliquées aux 6 jobs d'extraction :
~145 lignes de duplication en moins pour une indirection d'un seul niveau.

Deux points de sémantique, faciles à casser dans une reprise :

- Les `if: cancelled()` / `if: failure()` restent portés par le **step
  appelant**. Évalués dans l'action, ils porteraient sur l'état de ses propres
  steps — ce n'est pas le même test.
- Une action locale suppose le `actions/checkout` du job déjà fait : un job
  annulé avant la fin de son checkout n'aura pas son résumé. Angle mort
  résiduel assumé (le cas majoritaire, préemption en cours d'extraction #228,
  reste couvert).

Le relevé mémoire `free -h` est du coup appliqué aux **6** jobs, et plus
seulement à `extract-an`/`extract-roster-groupes` : `extract-amendements-an`
manipule les plus gros volumes (archives ~1,2 Gio) et en était le seul dépourvu.

*Alternative rejetée* : factoriser aussi `MERGE_FLAG`/`INTERV_FLAG`/
`MAX_PAGES_FLAG`. `retry-generate-data.yml` reconstruit les inputs du run échoué
en **grepant le texte bash substitué** de ces steps dans les logs ; les déplacer
casserait ce couplage. Contrainte non évidente, désormais écrite en commentaire
dans le YAML (et dans l'action composite, pour qui viendrait l'y ajouter).

*Alternative rejetée* : factoriser « Semaine ISO courante », « Nettoyage
complet (fresh_run) » et `actions/cache` — 3 à 4 lignes chacun, corps déjà
divergents, clé de cache différente par job. La variabilité y domine la
duplication.

## 5. Garde-fou de volume sur `extract-an`

Le commentaire « recalculer si `raw_data/candidats.json` change
significativement » n'était outillé par rien : à 5 min par shard en série, un
passage à 40 candidats porterait ce seul job à 200 min sans aucun signal.
`prepare-an-matrix` émet désormais un `::warning::` au-delà de `AN_SHARDS_WARN`
(16, soit ~80 min), valeur unique et modifiable en place.

## 6. Nommage : `raw-profiles-parltrack` → `parltrack-dumps`

Seul écart de la famille `raw-profiles-*` : cet artifact ne contient pas de
profils bruts mais les dumps `.zst` ParlTrack, consommés dans `.cache/parltrack`
par `merge-and-pivot`. Aucun consommateur hors du run courant (le retry ne
manipule pas d'artifacts) → renommé.

**Hors périmètre, traité ailleurs** : budget de temps mur et libellés « JOB n/4 »
périmés, garde-fou #390, permissions par job (#413) ; reconstruction des inputs
du retry (#414).
