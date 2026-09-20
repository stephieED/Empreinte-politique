# `synchro_sources` publie la dernière récupération réussie, et pas son origine (#600) (2026-08-30)

`2026-08-30`

> **En bref** — une date en retard sur le profil est un fait (la source n'a pas été re-collectée), pas une anomalie ; l'origine cache/réseau n'existe pas et ne sera pas publiée sans lecteur.

Le champ n'avait pas de définition écrite. Il en a maintenant une, et elle a été
choisie contre une lecture qui paraissait plus rigoureuse.

## Ce que le champ enregistre réellement

`time.strftime()` posé **au moment où la collecte réussit dans le processus**, et
seulement si elle a rendu quelque chose — `candidate_profile.py:4896`, `:5022`,
`:5094`, `:5121`, toutes gardées par un `if` sur le résultat.

Ce n'est donc ni l'heure du run, ni l'heure à laquelle la source a produit sa
donnée : c'est **l'heure de notre dernière récupération réussie**.

## Le constat qui a posé la question

Mesuré le 30/08/2026 sur les **477 profils bruts qui portent un bloc
`meta.synchro_sources`**, sur 481 :

| Lecture | Profils |
| --- | ---: |
| Au moins une synchro antérieure de plus de 0,5 j au `genere_le` du même profil | 16 |
| … dont l'écart ne porte que sur `nosdeputes`, source retirée par #529 | 9 |
| … dont l'écart porte sur une source **encore écrite** | **7** |

Retard maximal : **2,71 j**, sur `assemblee_nationale_questions` et
`assemblee_nationale_syceron`.

**La cause n'est pas le cache.** Une première explication — « des archives
servies par le cache hebdomadaire » — a été avancée puis **infirmée** en lisant
le code : le run n'avait pas `collect_interventions`, donc les jobs `extract-an`
portaient `--skip-interventions`, donc ces deux sources n'ont **pas été
collectées du tout** et leur tampon n'a jamais été posé. La date du run
précédent survit alors à la fusion. Elle est exacte.

Consigné parce que l'explication fausse est plausible et qu'elle reviendra.

## La décision

**`synchro_sources.<source>` publie la dernière récupération réussie.** Une date
en retard sur le `genere_le` du profil est un fait, pas une anomalie : elle dit
que cette source n'a pas été re-collectée par ce run.

L'alternative — « la synchronisation de ce run », donc `null` pour une source
non collectée — est **écartée** : elle remplacerait une date vraie par un vide.
C'est §2.5 retournée contre elle-même, qui interdit de publier une absence là où
une donnée existe autant que l'inverse.

## L'origine de la date — cache ou téléchargement — n'est pas publiée

Trois raisons, dans cet ordre.

1. **L'information n'existe pas.** La distinction cache / réseau vit dans
   `.cache/` et `actions/cache` ; aucun appelant de `_telecharger_flux` ne la
   remonte, et rien ne la thread jusqu'à la pose du tampon. La produire est un
   lot de **collecte** — traverser `fetch_interventions_syceron`,
   `fetch_questions_officielles` et leurs équivalents —, pas un lot de fusion.
2. **La publier changerait le schéma**, sous n'importe quelle forme : valeur
   devenue objet, clé sœur `meta.synchro_origines`, ou enrichissement de
   `sources[].synchro_le`, que `schema_pivot.py:149` déclare comme une chaîne
   ISO. `meta` est publié tel quel dans le pivot ; il n'y a pas de troisième voie.
3. **Un champ publié que rien ne lit est le constat n° 1 de la revue #593** :
   3 800 entrées de `couverture` sur 481 profils, qu'aucun composant de l'UI ne
   lit. Ajouter une origine sans lecteur reproduirait exactement ça.

Ce qu'il fallait vraiment corriger n'était pas l'absence d'origine : c'était
qu'**aucune définition n'était écrite**. C'est ce fichier.

Si le besoin de tracer l'origine revient, la voie est de la **consigner hors du
profil** — résumé de run, artefact d'audit —, jamais de l'ajouter au publié sans
lecteur.

## Ce que le lot #600 change, indépendamment de cette décision

`synchro_sources` est fusionné **par source**, à la valeur la plus **récente**.
Le recopiage en bloc disparaît : `merge_raw_profile` recopiait l'ancien
dictionnaire **entier** quand le nouvel écrivain n'en portait pas — c'est ce qui
publiait une date au 19/08 sur un profil régénéré le 29/08 — le défaut de
l'issue #484, dont la décision est écrite à part.
