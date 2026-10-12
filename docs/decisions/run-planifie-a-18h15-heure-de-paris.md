# Le run planifié part à 18 h 15, heure de Paris, et le workflow déclare son fuseau

`2026-10-12`

> **En bref** — le cron passe de `0 18` en UTC (20 h à Paris l'été, 19 h l'hiver) à `15 18` avec `timezone: "Europe/Paris"` : 18 h 15 toute l'année. La phrase « GitHub ne connaît que l'UTC », écrite dans le workflow, la règle CI et deux documents, n'est plus vraie.

## Contexte

La propriétaire a demandé, le 12/10/2026, que le run automatique parte à 18 h 15.

Le cron était `0 18 * * *`, lu en UTC. Le workflow, `docs/regles/ci.md`,
`docs/workflow-generate-data.md` et `modes-du-run-programme-1149` disaient tous
qu'aucun fuseau ne pouvait s'exprimer côté GitHub, et qu'une valeur fixe
décalait donc d'une heure deux fois par an. Le prochain changement d'heure est
le 25/10/2026 : une valeur UTC choisie pour 18 h 15 aurait été fausse treize
jours plus tard.

Relue le 12/10/2026, la documentation de GitHub Actions (`on.schedule`, et la
page des événements) décrit une clé `timezone`, facultative, qui prend un nom de
fuseau IANA ; sans elle le cron reste en UTC.

## Décision

```yaml
schedule:
  - cron: '15 18 * * *'
    timezone: "Europe/Paris"
```

Les deux lignes vont ensemble. `test_le_cron_dit_son_fuseau_et_reste_une_seule_cadence`
refuse un cron sans fuseau, ou avec un autre que `Europe/Paris` : retirer la
ligne ne casse rien et déplace le run de deux heures en été.

L'heure reste celle où le run devient **éligible**. Mesuré sur les huit runs
planifiés du 04 au 11/10/2026 (dépôt public) : sept ont démarré 20 à 23 minutes
après l'heure demandée, un 1 h 07 après. Un run demandé à 18 h 15 démarre donc
plutôt vers 18 h 35, et committe environ deux heures plus tard.

## Ce qui n'a pas été vérifié

Aucun run n'a encore été servi avec cette clé sur ce dépôt : la lecture vient de
la documentation. Le premier run planifié après la publication du workflow le
dira — son heure de création doit tomber vers 18 h 35 à Paris, et non 20 h 35.

## Alternative écartée

**Une valeur UTC fixe** (`15 16` pour l'été, `15 17` pour l'hiver) : juste
jusqu'au changement d'heure, fausse d'une heure ensuite, et à corriger à la main
deux fois par an.
