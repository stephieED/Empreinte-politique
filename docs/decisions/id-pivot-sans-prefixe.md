<a id="id-pivot-sans-prefixe"></a>
# L'`id` d'un profil pivot est le slug : le préfixe de provenance était instable (#487) (2026-08-20)

`2026-08-20`

> **En bref** — le préfixe changeait de valeur sur une carrière inchangée.

Sous-issue A de l'épic #486.
`normalize_nosdeputes` construisait `f"{source_type}:{slug}"`, où `source_type`
venait de `_SOURCE_TYPE_MAP` (`deputes` → `nosdeputes`, `senateurs` →
`nossenateurs`). L'`id` est désormais le **slug** seul.

## Ce n'est pas la redondance qui a tranché, c'est l'instabilité

Le préfixe était redondant — la provenance est consignée trois fois ailleurs
(`sources[].type`, `identite.source_url`, `meta.provenance`) — mais la
redondance seule ne justifiait pas une migration. Ce qui l'a justifiée est
mesuré : entre `25f7bc7` et `01ffa7f`, sur les mêmes 209 profils et sur des
carrières inchangées, **deux profils ont changé d'`id`, en sens opposés** :

| Profil | Avant | Après |
| --- | --- | --- |
| `jean-luc-melenchon` | `nosdeputes:` | `nossenateurs:` |
| `stephane-mazars` | `nossenateurs:` | `nosdeputes:` |

Ce n'est pas un accident isolé, c'est le comportement normal d'un identifiant
dérivé de « quel site a répondu ce jour-là » : `generate_all_profiles` s'arrête
à la première chambre qui répond, et une défaillance transitoire de
`nosdeputes.fr` suffit à faire basculer le préfixe (#488, #484). L'option
concurrente — garder le préfixe en cessant de le lire comme une chambre — a été
écartée pour cette raison : **documenter la sémantique d'un identifiant qui
change ne le stabilise pas.**

## Le slug peut porter l'identité, et rien ne joignait sur l'`id`

Sur les 209 profils de `01ffa7f` : **209 slugs distincts, aucun doublon**, et
`raw_profile["slug"]` égale le nom de fichier sur les 209 — l'`id`, le slug et
le chemin ne font donc qu'un.
`merge_raw_profile` fusionne par chemin de fichier, `audit_diff_profils` compare
par chemin, l'UI joint sur le slug (`manifest.candidates.find((c) => c.slug ===
id)`) et expose `id: c.slug`. Le seul lecteur du préfixe dans tout le dépôt est
`group_profile.py:1295` (`--merge-existing`), et il le **retire** pour récupérer
le slug : un `id` déjà sans préfixe le traverse inchangé.

## Le cas européen : `europarl:131580` (Bardella)

Un seul profil portait un `id` qui ne dérivait pas de son slug. Le retirer ne
coûte aucune traçabilité (§2.2) : le numéro `131580` apparaît **25 fois** dans
le profil, dont 24 hors de l'`id` — la source EP et le `source_url` de chacun
des 22 mandats européens. `normalize_europarl` prend donc un paramètre `slug`
optionnel qui devient l'`id`.

**Reste à câbler, et c'est dit ici plutôt que découvert plus tard** : le
paramètre existe et est testé, mais ses deux appelants sont dans
`src/generate_all_profiles.py` (l. 520 et 675), fichier qu'une autre issue en
vol (#488) réécrit au même moment. Le câblage est d'un mot-clé —
`slug=effective_slug` — et il appartient à qui touchera ce fichier ensuite.
Jusque-là, `jordan-bardella` conserve `europarl:131580` : c'est le seul profil
du corpus dont l'`id` n'est pas son slug, et il n'est pas instable pour autant
(l'identifiant EP ne dépend pas de quelle chambre a répondu). L'énoncé « l'`id`
est le slug » vaut donc pour 208 des 209 profils tant que ce mot-clé n'est pas
posé.

**Sans slug, aucun slug n'est inventé.** `ue_profile` n'en porte pas, et le seul
qu'on pourrait en tirer viendrait de `nom_complet` — donc d'une donnée de
collecte, exactement le défaut qu'on retire. Le repli reste
`europarl:<identifiant_pe>`. Même raisonnement pour `mep_profile.py:351`
(`parltrack:{ep_id}`), laissé tel quel : c'est un outil autonome dont les seules
entrées sont un nom ou un identifiant EP, et **aucun profil de
`pivot_data/profiles/` n'en sort** (0 sur 209 à `01ffa7f` ; le pipeline appelle
`normalize_parltrack_dumps.enrich_pivot_with_parltrack`, qui enrichit un pivot
existant sans en créer).

## La réserve instruite avant de coder : ce que le contrôle de perte en fait

`gouvernement_roster` publie `membre_id: profil["id"]`. Changer la convention
réécrit **113 entrées dans 10 fichiers**, et le contrôle de perte étendu par
#470 tourne dans `merge-and-pivot` **en échec dur avant le commit**, sur tout
`pivot_data/`. Si la réécriture s'y lisait comme une régression, la correction
bloquerait le commit qu'elle doit produire.

Scénario rejoué, pas déduit — rosters reconstruits des deux côtés par
`build_gouvernement_roster` depuis les 209 pivots de `01ffa7f`, puis
`audit_diff_profils --ref HEAD` sur les six collections, avec un **témoin** :
les mêmes rosters reconstruits **sans** le changement d'`id`. Différence entre
les deux rapports :

| Constat | Témoin | Avec #487 |
| --- | ---: | ---: |
| `profiles` · changement de valeur d'un scalaire (`id`) | 0 | **208** |
| `gouvernements` · perte sur liste stable | 1 | 1 |
| pertes bloquantes **ajoutées** par #487 (6 collections) | — | **0** |

Deux régimes se combinent, et aucun ne bloque :

- **Les 113 `membre_id` sont invisibles au contrôle.** `membre_id` vit à
  l'intérieur d'une entrée de `membres[]`, et le contrôle ne compare d'une liste
  que sa **cardinalité** — inchangée, 113 avant, 113 après. Les scalaires
  surveillés d'un gouvernement sont `gouvernement_id`, `nom`,
  `premier_ministre`, `periode.debut` ; `membre_id` n'en est pas. Le rapport le
  dit déjà sous « Hors périmètre » : « la **valeur** des entrées d'une liste :
  seule leur cardinalité est comparée. » Idem pour les `membre_id` des groupes.
- **Les 208 `id` de profils sont vus, signalés, non bloquants.** `id` *est* un
  scalaire surveillé de `COLLECTION_PROFILS` ; le passage `nosdeputes:x` → `x`
  est un changement de valeur (A → B), le régime que #470 a explicitement
  retenu comme non bloquant. Seule une régression `renseigné → null` bloque, et
  il n'y en a aucune.

L'unique constat bloquant du run — `gouvernement-BAYROU.json · membres : 12 →
9` — **est présent à l'identique dans le témoin** : il ne vient pas de #487. Il
vient de ce que les fichiers de gouvernement committés datent d'avant la
déduplication de [[deduplication-entrees-membres]] (2 entrées) et d'une
troisième entrée `astrid-panosyan-bouvet` (« Ministère de l'économie… »,
`debut: 2026-02-04`, `actif: true`) que le code actuel ne reproduit plus. Le
prochain `merge-and-pivot` bloquera dessus **indépendamment de cette issue** ;
c'est à instruire à part.

## Migration : par régénération, sans table de correspondance

`normalize_nosdeputes` reconstruit l'`id` à chaque passage, et
`merge_pivot_profile` part de `dict(new)` sans jamais rattraper `id` : la valeur
régénérée l'emporte sur l'ancienne, y compris préfixée (vérifié, et figé par
`tests/test_id_pivot_sans_prefixe.py`). Aucun fichier de `pivot_data/` n'a été
réécrit à la main.

Conséquence collatérale, inerte aujourd'hui :
`amendements[].amendement_non_resolu.premier_signataire` reprend l'`id` du
profil (`normalize_nosdeputes.py:230`) et suit donc la nouvelle forme — zéro
occurrence sur le corpus, dont la couverture `uid` est de 100 %.

## Le garde-fou

Un test qui vérifie `id == slug` serait faible : un préfixe **stable**
réintroduit le passerait. `tests/test_id_pivot_sans_prefixe.py` vérifie donc que
l'`id` **ne dépend d'aucune donnée de collecte** — chaque champ du profil brut
autre que `slug` est absenté puis remplacé par huit variantes, et l'`id` ne doit
pas bouger. Sans le correctif, il échoue en nommant la cause : « l'`id` a suivi
le champ collecté `'chambre'` ».

`_SOURCE_TYPE_MAP` n'est pas supprimé : il reste la source de `sources[].type`,
où il décrit la provenance d'**une source** — ce qui est vrai et stable.

