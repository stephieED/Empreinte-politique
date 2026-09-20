<a id="sujet-europeen-sans-boutons-a-la-fusion-980"></a>
# Le sujet nettoyé d'une question européenne n'atteignait pas l'entrée déjà publiée (#980) (2026-09-16)

`2026-09-16`

> **En bref** — #938 retire les boutons « PDF (… KB) DOC (… KB) » des titres à
> l'entrée du corpus. Les textes portés se sont corrigés au run suivant, mais
> **313 questions européennes** des candidats déclarés ont gardé leur sujet sale.
> Leur fusion garde l'ancienne entrée à identifiant égal. Un report nommé laisse
> désormais passer le sujet neuf, **seulement** s'il est exactement l'ancien sans
> ses boutons.

## Contexte

Signalé par la session interface le 16/09/2026, mesuré sur `origin/main`
`966dd18a3`, après le run `35112750639` qui portait déjà le code de #938 :

| Profil | Interventions européennes | Sujet sale |
| --- | ---: | ---: |
| marine-le-pen | 956 | 147 |
| florian-philippot | 1 585 | 128 |
| jean-luc-melenchon | 1 803 | 38 |

Ce sont toutes des questions : 305 questions écrites (QE) et 8 questions orales
(QO). Elles portent toutes un `intervention_id`, et aucune ne devient vide une
fois nettoyée. Aucun autre profil ni aucun autre champ n'est touché, et
`raw_data/` ne porte pas le motif.

**Pourquoi #973 s'est corrigée sans code, et pas ceci** : `merge_pivot_profile`
fusionne les textes portés par `merge_dossier_records`, où l'entrée neuve gagne,
et les interventions par `merge_lists_by_key`, où l'ancienne gagne. Le seul
report de sujet existant, `backfill_sujet_seance` (#710), ne vaut que pour
Syceron. C'est la famille décrite dans `docs/regles/fusion-et-index.md` : un
champ corrigé n'atteint jamais seul une entrée déjà collectée.

## Décision

1. **`backfill_sujet_europeen`, appelé dans `merge_pivot_profile`** juste après
   `backfill_sujet_seance`. Sur une intervention dont `source.institution` vaut
   `parlement_europeen`, le sujet neuf remplace l'ancien **si et seulement si**
   `titre_sans_boutons(ancien) == neuf`.
2. **Seul `sujet` change**, et la clé de fusion ne bouge pas (le défaut de #668
   ne se rejoue pas).
3. **Le nettoyage reste à l'entrée du corpus**, comme #938 l'a décidé. La fusion
   n'applique pas la règle : elle s'en sert pour **reconnaître** que l'entrée
   neuve est l'ancienne nettoyée.
4. **La règle quitte `parltrack_dumps` pour `src/titres_europeens.py`**, module
   sans dépendance. `merge_profile` est lu par le portail de qualité et par tous
   les audits, et ne doit pas tirer `zstandard` ni les dumps européens.
   `parltrack_dumps` la réexporte, et ses appelants ne changent pas.

Rien au brut : les interventions européennes n'entrent qu'au pivot, par
`enrich_pivot_with_parltrack`. Rien sur `tags_thematiques` : il dérive de
`theme_officiel`, `null` sur toute entrée européenne.

## Alternatives rejetées

- **« Le sujet neuf gagne »** sur toute intervention européenne. Un intitulé que
  la source aurait réécrit remplacerait silencieusement celui qui était publié :
  ce n'est plus la correction de #938, c'est une autre politique de fusion.
- **Appliquer `titre_sans_boutons` à la fusion**, sans entrée neuve. Cela corrige
  même une entrée qu'aucun run ne recollecte, mais la règle vivrait alors à deux
  étages. #938 a décidé de nettoyer une seule fois, à l'entrée du corpus.

## Vérification

`tests/test_sujet_europeen_sans_boutons_980.py` part d'une entrée **copiée** du
profil de Florian Philippot, et fabrique l'entrée neuve par le vrai chemin : un
dump, `build_activities_index`, puis `_make_intervention`. Le test de fusion
**échoue sur l'ancien code**. Le corpus ne sera corrigé qu'au prochain run, et
c'est là qu'il se mesure : 0 sujet contenant « KB) DOC ( » attendu sur les 32
profils des candidats déclarés.
