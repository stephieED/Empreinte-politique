<a id="retrait-marqueur-regards-citoyens-deputes-890"></a>
# Un marqueur de provenance sans donnée derrière lui n'est plus une traçabilité, c'est une inexactitude (#890) (2026-09-13)

`2026-09-13`

> **En bref** — §7 écrit que `meta.licence_donnees` est **dérivé** et que sa condition de retrait « court d'elle-même » : la clause ODbL quitte un profil le jour où ce profil cesse de porter quoi que ce soit de Regards Citoyens. Mesuré le 13/09/2026 sur `origin/main` `7e48b4b05` par un parcours **récursif** des deux couches, **clés de dict comprises** — c'est ce qui manquait aux mesures précédentes, la trace du brut étant une **clé** et non une valeur : sur les **1 196 profils publiés**, **aucune donnée** n'en dérive. Le marqueur était seul à retenir la clause, et il ne partait pas tout seul : `_merge_pivot_sources` **unit par `type`** et ne retire jamais un type absent d'une collecte — ce que `retrait-senat-528` §3 annonçait comme automatique ne l'était pas, et 475 profils le portaient dix-huit jours plus tard. Retiré sur les **454 profils de député** (446 membres de roster, 8 candidats déclarés), **aux deux couches** : 454 entrées `sources[]` au pivot, 454 clés `meta.synchro_sources.nosdeputes` au brut. **21 profils qui touchent le Sénat le gardent**, et c'est ce qui rend le geste sûr : la clause ODbL survit sur le corpus, donc les pages publiées ne changent pas et les verrous de `tests/test_licences_530.py` n'ont rien à retourner. **Aucun `synchro_le` ne bouge** — les 11 profils dont la clé de journal porte un horodatage réel ont tous `assemblee_nationale` renseigné, donc le repli de `normalize_profil:647` n'est jamais emprunté.

## 1. Ce que la mesure précédente ne pouvait pas voir

`licences.licences_du_profil()` — la fonction de production, celle sur laquelle
le lot C de #839 a fondé son « 0 profil retenu par une donnée » — lit
**`sources[]` et `interventions[].source_url`**. Deux champs.

Une mesure d'absence qui ne parcourt pas l'objet entier ne prouve pas une
absence : elle prouve que deux champs sont vides. Le parcours récursif, clés
comprises, dit la même chose — mais lui l'établit.

| Ce qui reste, 13/09/2026 | Occ. | Fichiers | Nature | Côté |
| --- | ---: | ---: | --- | --- |
| `sources[].type` + `.url`, profils | 951 | 475 profils | marqueur | **AN** |
| `sources[].type` + `.url`, agrégats | 3 232 | 51 fiches | marqueur | AN, sauf 4 fiches Sénat |
| clé `meta.synchro_sources.nosdeputes`, brut | 475 | 475 profils | journal de synchro | AN |
| `meta.warnings[]` | 50 | 19 profils + 31 groupes | symptômes / phrases | mixte |
| `couverture.*.preuve` | 75 | 15 profils | déclaration vivante | Sénat |
| URL dans `source`, brut | 19 | 19 profils | seule URL au brut | **Sénat** |
| `membre_id` / `profils_sources` `nosdeputes:<slug>` | 51 | 4 fiches | intégrité référentielle | **Sénat** |
| `groupes_reels.json`, bloc de suspension | 2 | 1 | déclaration vivante | Sénat |

**Côté Assemblée, il ne reste que le marqueur.** Tout ce qui n'est pas le
marqueur est côté Sénat.

## 2. La trace du brut est une clé, pas une valeur

Un `grep` rendait 475 fichiers bruts, un parcours des valeurs n'en trouvait que
19. L'écart n'était pas une erreur de l'un des deux : la trace est
`meta.synchro_sources.nosdeputes`, **un nom de champ**. Les 19 valeurs sont les
URL `nosdeputes.fr` de 19 membres de roster sénatorial.

C'est la troisième forme du même piège — après « compter des entrées et annoncer
des profils » et « mesurer une absence sur trois listes ». **Une mesure
d'absence parcourt l'objet entier, clés comprises**, ou elle décrit l'endroit où
elle a regardé.

## 3. Pourquoi le retrait, et pas la prudence de le garder

Trois raisons, dans l'ordre de force.

**La condition de §7 est remplie et mesurée.** Rien de ce que publient ces 454
profils ne dérive de Regards Citoyens. Le lot B de #839 avait déjà jugé les
mandats sans `categorie_source` contre deux référentiels : **0 introuvable** sur
406, 280 reproduites par un référentiel vivant.

**Garder l'attribution n'est pas plus prudent, c'est inexact.** Le corpus
déclarait devoir une attribution pour une source dont plus rien n'est publié.
§2 règle 2 exige de tracer ce qui est là ; elle n'exige pas de tracer ce qui
n'y est plus, et une licence due à tort est une affirmation fausse comme une
autre (#886).

**Le marqueur ne partait pas tout seul, et ne peut pas revenir.**
`_merge_pivot_sources` unit `sources[]` par `type` et garde l'entrée la plus
fraîche : un type absent d'une nouvelle collecte n'est jamais retiré.
`retrait-senat-528` §3 écrivait l'inverse — « `sources` est remplacé …
disparaissent au premier profil régénéré » — et le corpus l'a démenti. Dans
l'autre sens, depuis #529 `normalize_profil` écrit
`_SOURCE_TYPE_PROFIL_FR = "assemblee_nationale"` en dur et `candidate_profile`
n'écrit plus la clé de journal : **aucun code producteur n'est touché ici**, le
retrait est définitif par construction.

## 4. Le périmètre, et pourquoi il s'arrête aux députés

**454 profils de député** — 446 membres de roster, 8 candidats déclarés.
**21 profils touchent le Sénat et gardent le marqueur** : 19 membres de roster
sénatorial, plus `bruno-retailleau` et `jean-luc-melenchon`.

Les 19 ne publient **aucune** chambre, leur collecte étant suspendue (#528).
Une liste vide n'est pas « pas le Sénat », c'est « on ne sait pas » — §2 règle 5
interdit de lire une absence comme un constat, et `raw_data` porte encore leur
URL `nosdeputes.fr`. Les emporter ici retirerait l'attribution **avant** d'avoir
une source pour la remplacer ; c'est le lot de #885.

Conséquence mesurée, et c'est elle qui rend le geste sûr : **la clause ODbL
survit sur 21 profils**. `LegalNoticePage.jsx` et `sources.config.js` doivent
continuer de nommer NosDéputés.fr, NosSénateurs.fr et l'ODbL v1.0. Les verrous
de `tests/test_licences_530.py:196` et `:222` n'ont rien à retourner, et la
seconde jambe de la clause — ParlTrack, source vivante, 6 profils — n'est pas
touchée non plus.

## 5. Aux deux couches, et ce qui ne bouge pas

Retiré du seul pivot, le marqueur redescendrait du brut au prochain passage de
normalisation : c'est la leçon de #729, « un sédiment retiré du seul brut ne
descend jamais au pivot », prise dans l'autre sens.

- **pivot** : les entrées `sources[]` marquées, puis `meta.licence_donnees`
  **recomposé** par `licences.appliquer_licence_donnees` (§4 : un champ dérivé
  se recompose, il ne se fusionne pas) ;
- **brut** : la clé `meta.synchro_sources.nosdeputes`.

**Aucun `synchro_le` ne bouge.** `normalize_profil:647` lit
`synchro_sources["assemblee_nationale"] or synchro_sources["nosdeputes"]`. Les
**11** profils dont la clé porte un horodatage réel — et non `None` — ont tous
`assemblee_nationale` renseigné au 12/09/2026 : la branche de repli n'est jamais
empruntée. Vérifié profil par profil **avant** d'écrire le module, parce qu'une
clé qu'on croit vide et qui ne l'est pas est exactement la forme qu'une perte
silencieuse prend.

**0 profil ne se retrouve sans source** : simulé avec la fonction de production
avant d'appliquer.

## 6. L'alternative rejetée : tout retirer d'un coup

Emporter dans le même lot les 51 identifiants `nosdeputes:<slug>` des fiches
`Senat-LR`/`Senat-SER`, les 19 URL brutes et le bloc de suspension aurait rendu
le corpus « propre » en une passe. Deux raisons de ne pas le faire.

Les 51 identifiants sont des **clés d'intégrité référentielle** : les retirer
sans les remplacer casserait le lien entre une fiche de groupe et ses membres,
et `audit_integrite_referentielle` bloquerait le commit — à juste titre.

Le bloc de suspension et les 75 preuves de couverture qui en dérivent ne sont
**pas du sédiment** : ce sont des déclarations produites à chaque run, qui
disent pourquoi une collecte est suspendue. Elles s'éteignent quand la cause
s'éteint, c'est-à-dire avec #885 — les retirer à la main publierait un corpus
qui ne dit plus pourquoi il lui manque quelque chose.

## 7. Ce que ça laisse ouvert

Les agrégats — **3 232 occurrences sur 51 fiches** de groupe, lignée,
gouvernement et parti — portent toujours le marqueur. Ils sont **recalculés**
depuis les profils à chaque run : la question est de savoir si leur `sources[]`
se recompose comme celle d'un profil, ou si elle se fusionne additivement comme
celle des profils l'a fait. Non mesuré ici, et c'est la suite naturelle de ce
lot.
