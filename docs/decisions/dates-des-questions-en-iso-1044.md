<a id="dates-des-questions-en-iso-1044"></a>
# 882 interventions portaient une date que tout filtre écartait en silence (#1044) (2026-09-20)

`2026-09-20`

> **En bref** — La collecte des questions recopiait `infoJO.dateJO` telle que
> la source la présente : **715 interventions publiées en `JJ/MM/AAAA`** quand
> tout le reste du corpus est en ISO, plus 167 sans date. Les filtres par
> période comparent des chaînes ISO — ces entrées ne tombaient dans **aucune**
> fenêtre et disparaissaient sans être comptées comme écartées. La date est
> normalisée à la collecte, **et** les entrées déjà publiées sont reprises.

## Contexte

Signalé par la session « UI gouv » le 20/09/2026, à la demande de la
propriétaire, et remesuré côté backend sur le corpus entier.

| | |
| --- | ---: |
| Interventions publiées | 1 217 384 |
| Dates en `JJ/MM/AAAA` | **715** |
| Dates vides ou nulles | **167** |
| Profils touchés | **12**, tous `candidat_declare` |
| `type_detail` | **`question`**, sans exception |

Dupont-Aignan 236, Mélenchon 130, Ruffin 127, Roussel 112, Le Pen 108,
Faure 71, et six autres.

## Décision

**Normaliser à la collecte, et reprendre ce qui est publié.** Les deux, parce
que l'une sans l'autre ne change rien de visible.

1. `candidate_profile.normaliser_date_jo` rend `AAAA-MM-JJ` à partir de
   `JJ/MM/AAAA`, laisse passer une date déjà ISO, et rend `None` sur une valeur
   vide. Appliquée à `date` **et** `date_reponse`, qui suivaient le même chemin.
2. `merge_profile.normaliser_dates_interventions` reformate les entrées déjà
   présentes, **aux deux étages** — brut et pivot.

## Pourquoi la seconde moitié n'est pas facultative

Les interventions se fusionnent par `merge_lists_by_key` : additif pur,
**l'entrée ancienne gagne**, au brut comme au pivot. Une date publiée une fois
en `JJ/MM/AAAA` n'aurait donc jamais été corrigée par une régénération. C'est
le défaut de #997 — un correctif de qualification qui n'atteint pas le corpus
parce que la fusion ne le laisse pas passer — au même endroit et pour la même
raison.

## Ce que cette passe n'est pas

**Pas un `backfill_*`.** Les backfills reportent une information que la
collecte neuve apporte ; ici rien n'est apporté, une valeur est **reformatée**.
Le jour désigné ne change pas, la transformation se vérifie à l'œil, et elle
s'applique donc sans regarder `new`.

**Pas une invention.** Une forme inconnue passe telle quelle plutôt que d'être
transformée en une date plausible : elle restera visible. Et **les 167 dates
vides ne se réparent pas** — la source ne les porte pas, elles restent une
absence à déclarer (§2 règle 5).

## Garde

`tests/test_dates_questions_iso_1044.py`, sept cas : la normalisation et ses
refus, la passe sur des entrées anciennes, et surtout **le corpus déjà publié
repris par la fusion** — le cas qui échoue si l'on ne corrige que la collecte.

## Effet attendu

Au prochain run, les 715 dates deviennent lisibles par les filtres de période.
Sur les fiches de gouvernement l'effet est nul : ces 12 profils sont des
candidats déclarés, dont aucun n'a été ministre sur la période concernée. Sur
la fiche candidat, ces entrées rentrent dans le découpage par période.
