<a id="aucune-semaine-ne-force-la-reconstruction-1127"></a>
# Aucun changement de semaine ne force la reconstruction d'un index : le préfixe nu traverse les semaines (#1127) (2026-10-02)

`2026-10-02`

> **En bref** — #1127 attendait le premier run de la semaine W40 pour voir `document_depuis_archive` tourner en CI, la clé de cache portant la semaine ISO ; le run a eu lieu le **28/09**, a réussi, et **n'a rien reconstruit** : `17.contenu.json` porte toujours `genere_le = 2026-09-27T07:44` et n'a pas bougé depuis, parce que le log dit `Cache hit for restore-key: public-data-cache-amendements-2026-W39` — **le repli par préfixe sert l'entrée de la semaine précédente**, et le contenu était déjà là. L'issue a donc été fermée `not planned` : elle attendait un rendez-vous qui n'existe pas.

## 1. Ce que l'issue supposait

> *« lundi elle devient `2026-W40`, la clé exacte n'existera pas, le job passera
> `--reconstruire-actives`, et la XVIIe sera retéléchargée puis reconstruite. »*

Le raisonnement est juste sur la **clé exacte**, et faux sur la conséquence.

## 2. Ce qui s'est passé

Run programmé `36396696042`, 28/09/2026 — premier de la semaine ISO W40, 52 jobs
verts.

```
key:          public-data-cache-amendements-2026-W40
restore-keys: public-data-cache-amendements-
Cache hit for restore-key: public-data-cache-amendements-2026-W39
```

`--reconstruire-actives` **a bien été posé**. Il n'a trouvé aucune archive
manquante à refaire : le contenu restauré depuis W39 était complet.

Mesuré sur les quatre commits de données suivants : `17.contenu.json` garde
`genere_le = 2026-09-27T07:44:08`, et ses compteurs sont identiques d'un run à
l'autre — **125 090 ids, 35 070 mots, 125 086 articles**. Les trois législatures
figées datent du 23 et du 24/09.

## 3. Pourquoi, et ce n'est pas un défaut

C'est le **préfixe nu** de [[cache-fraicheur-interventions-555]], et c'en est la
raison d'être : sur un miss de la clé exacte, `actions/cache` sert l'entrée la
plus récente qui commence par le préfixe — donc celle de la semaine précédente.
#555 l'a mesuré et conservé délibérément : le retirer rouvrirait #424, et
jetterait avec les archives vivantes les index des législatures **closes**, dont
le réchauffement inter-semaines est légitime.

**Conséquence, et c'est ce que cette décision fixe** : la semaine ISO périme
l'entrée *nominalement*, jamais son *contenu*. Un index déjà construit survit à
tous les changements de semaine.

## 4. Ce qui exercerait réellement la fabrique depuis archive

Trois événements, et **ils se décident** — ils ne s'attendent pas :

- `cold_start`, qui saute les restaurations ;
- un cache purgé à la main ;
- un changement de schéma qui invalide le contenu (`path` modifié, donc version
  d'entrée changée).

C'est aussi le jour qui mesurerait la **plage sans borne** de
[[plage-sans-borne-archives-figees-1123]] et qui rouvrirait
[[conservation-du-prefixe-laissee-ouverte-1125]] : les trois attendent le même
événement, et aucun calendrier ne l'amène.

## 5. Ce que le run a quand même prouvé

| Point de #1127 | Résultat |
| --- | --- |
| Pas de `Killed` ni de code 137 | **vérifié** — aucun, dans aucun job des quatre runs du 26 au 30/09. C'était le dépassement mémoire que #1122 devait supprimer |
| `17.contenu.json` lisible | **oui** — `charger()` l'accepte, clés conformes, `prefixe_ids = AMANR5L17` |
| `article` sur `17.json` | **stable** — 123 522 / 123 524, contre 123 505 / 123 507 à la ligne de base du 24/09 |
| La ligne d'indexation `✓ N mot(s)` | **absente** — rien n'a été indexé |

**Une erreur à ne pas refaire, et je l'ai faite** : j'ai d'abord annoncé #1127
« vérifiée, résultat bon », en prenant pour preuve la ligne
`tranches d'amendements : 1451 dérivée(s) de l'archive` de `merge-and-pivot`. Les
tranches d'amendements et l'index de mots sont deux chemins différents. Ce qui a
tranché, c'est `genere_le` — un horodatage que le fichier porte lui-même, pas une
ligne de journal qui lui ressemble.
