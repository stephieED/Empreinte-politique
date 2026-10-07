<a id="validation-des-profils-dans-le-run-1223"></a>
# `validate_profil()` tourne dans le run, et une fiche hors schéma ouvre une issue (#1223) (2026-10-06)

`2026-10-06`

> **En bref** — `validate_profil()` porte les invariants du schéma et **aucun job ne l'exécutait** : 16 des 34 fiches de candidats déclarés publiées ne le passaient pas, 38 erreurs d'une seule famille, écrites depuis trois semaines. Le vocabulaire est étendu aux **neuf** types de mandat local que la collecte peut écrire, et le validateur tourne désormais à chaque run. Arbitrage de la propriétaire, 06/10/2026 : il **signale sans bloquer**, par **une issue** que le run ouvre, tient à jour et ferme lui-même — une ligne dans le résumé du run est l'endroit où ces erreurs seraient restées non lues.

## 1. Le constat

Mesuré le 05/10/2026 et remesuré le 06/10 sur le privé `4275c239d`,
`validate_profil()` passé sur les fichiers de `pivot_data/profiles/` :

| Population | Profils | Hors schéma | Erreurs |
| --- | --- | --- | --- |
| candidats déclarés | 34 | 16 | 38 |
| membres de groupe | 1 166 | 0 | 0 |
| membres de gouvernement | 202 | 0 | 0 |

Les 38 erreurs : `mandats[].type_organe_source` vaut `conseil_municipal` (22),
`conseil_communautaire` (9), `conseil_regional` (5) ou `conseil_departemental`
(2). Le lot des mandats locaux (#922) les écrit depuis le 15/09/2026 sans avoir
étendu `KNOWN_TYPES_ORGANE_SOURCE`. La consigne « étendre le frozenset, jamais
le contourner » n'avait de garde que si le validateur tournait.

## 2. La décision

**Le vocabulaire.** Neuf valeurs, et non quatre : toutes celles de
`rne_opendata.FICHIERS_LOCAUX`. Le corpus n'en portait que quatre le jour de la
mesure ; déclarer celles-là seules aurait laissé la cinquième produire la même
erreur au premier maire collecté. Un test lit la collecte, pas le corpus.

**Le validateur dans le run.** `src/audit_validation_profils.py`, après les
quatre contrôles d'avant-commit, un profil à la fois.

**Il signale, il ne bloque pas.** La question posée à la propriétaire : une
fiche de candidat hors schéma doit-elle arrêter le run ou être signalée ? Elle a
retenu le signalement, à condition qu'il soit bruyant, et l'issue parmi trois
moyens :

| Moyen | Pourquoi pas |
| --- | --- |
| Annotation d'erreur sur le run | ne se voit que si l'on ouvre le run |
| Le run publie puis finit en échec | « rouge » ne voudrait plus dire « rien n'a été publié », ce qui brouille tous les autres échecs |
| **Une issue tenue par le run** | retenue |

**L'issue.** Une seule, reconnue à l'étiquette `fiches-hors-schema`, sur le
dépôt de développement. Le run l'ouvre, réécrit son corps et la commente à
chaque passage tant que le défaut dure, et la ferme quand il ne le trouve plus.
Elle décrit ce qui a été **publié** : le step ne tourne que si le push a eu
lieu.

**Le jeton.** Le run tourne sur le dépôt public, les issues vivent sur le
privé : `SRC_READ_TOKEN`, en lecture seule, ne peut pas en écrire. Un secret
distinct, `SRC_ISSUES_TOKEN`, limité à `Issues: Read and write` sur le dépôt
privé. Sans lui le step avertit et n'ouvre rien — il ne se tait pas.

## 3. Écarté

| Option | Pourquoi |
| --- | --- |
| Bloquer le commit pour les fiches de candidats déclarés | recommandation de l'agent ; écartée par la propriétaire au profit du signalement |
| Élargir les droits de `SRC_READ_TOKEN` | un jeton lu par chaque job d'extraction, qui exécute du code réseau, n'a pas à pouvoir écrire sur le dépôt privé |
| Ouvrir l'issue sur le dépôt public | le public est la vitrine ; le suivi vit sur le privé |
| Un bloc de plus dans `check_quality_gate.py` | le portail bloque ou imprime ; ni l'un ni l'autre n'est ce qui a été arbitré |

## 4. Limites déclarées

- **Les deux jointures de `validate_profil()` ne sont pas rejouées** — un
  scrutin et un amendement référencés existent, et la règle 4 sur le 49.3 :
  elles demandent les index, et `audit_integrite_referentielle.py` (#485) les
  tient en bloquant.
- **L'étape d'issue n'a pas tourné en conditions réelles.** Elle est rejouée en
  test avec un faux `gh`, dans ses cinq cas ; le premier run qui la porte est le
  second après la fusion (le YAML publié par un run sert au suivant).
- **Rien ne vérifie que le jeton est posé ni qu'il n'a pas expiré**, sinon
  l'avertissement du step le jour où une fiche est hors schéma.
- Depuis quand le validateur ne tournait plus, et s'il a jamais tourné, n'a pas
  été établi.
