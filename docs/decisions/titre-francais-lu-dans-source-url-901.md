<a id="titre-francais-lu-dans-source-url-901"></a>
# Le titre français cherchait sa référence là où elle n'est jamais (#901) (2026-09-16)

`2026-09-16`

> **En bref** — Le run `35087127267` a publié **0 titre français** sur 694
> textes portés européens. Trois défauts, dont un seul suffisait :
> `_titre_publie` cherchait le document **dans le titre**, qui ne le cite
> jamais ; une entrée en cache n'était **jamais réinterrogée**, contrairement à
> ce que sa docstring promettait ; et la clé du cache CI était **fixe**, donc
> jamais réécrite. Le test du lot d'origine passait sur un titre inventé.

## Ce que le corpus a montré

`textes_portes[].titre_langue`, mesuré sur `origin/main` `c6990c688` : `"en"`
sur 380 entrées, absent sur 314 (les anciennes copies des doublons retirés par
`doublons-textes-europeens-cle-doceo-901.md`), **`"fr"` sur zéro**.

## Défaut 1 — le mauvais champ

`_titre_publie` appelait `reference_doceo(entree["titre"])`. Cette fonction lit
une référence de la forme « (A9-0227/2024) », que portent les **intitulés
d'explications de vote** (#827) — pas les titres de résolutions. Mesuré : **aucun
des 694 titres** n'en contient. Le document ne sortait jamais, le résolveur
n'était jamais interrogé, et chaque titre retombait sur l'anglais.

L'information est ailleurs, et elle est sûre : `source_url`. Vérifié sur le dump
réel `ep_mep_activities` : les 252 activités de Florian Philippot portent un
`source_url` dont le document se lit, en `http://` comme en `https://`.

**Pourquoi le test ne l'a pas vu.** Il plaçait une référence dans le titre :
`{"titre": "… (A9-0227/2024)"}`. Aucune entrée réelle n'a cette forme. Le test
vérifiait que le code faisait ce qu'on avait imaginé, pas que le corpus
ressemblait à ce qu'on avait imaginé — le mode de défaillance que
`audit-champs-deplaces-726.md` décrit. Les tests réécrits portent des entrées
**copiées du corpus**, et l'un d'eux tient la prémisse démentie : aucun titre réel
ne porte de référence.

## Défaut 2 — la promesse que rien ne tenait

`_charger` annonçait qu'une entrée v1 « se remplira à la prochaine
interrogation ». `_entree` rendait pourtant toute entrée présente **sans jamais
réinterroger**. Un document connu comme existant restait sans titre ni concepts
pour toujours.

Une entrée écrite par un lecteur plus ancien se reconnaît désormais à
`concepts is None` — le lecteur courant écrit toujours une liste, vide ou non —
et elle est réinterrogée **une fois**, quand l'appelant demande le titre ou les
concepts. **Jamais pour la seule existence** : les ~1 500 explications de vote
déjà en cache ne demandent que `existe()`, et les redemander toutes coûterait un
run entier pour rien. Un document connu comme inexistant n'est pas redemandé
non plus.

Sur échec réseau, l'entrée connue est **rendue** plutôt que perdue : ne pas
avoir pu compléter une entrée n'efface pas ce qu'on savait déjà.

## Défaut 3 — une clé de cache qui ne tournait pas

`key: public-data-cache-europarl-documents-v1`, fixe. `actions/cache` ne
réécrit jamais une clé qui existe : le journal du run le dit — *« Cache hit
occurred on the primary key, not saving cache »*. Le cache restauré à chaque
run était celui de sa **première** sauvegarde, et tout ce que les runs suivants
avaient appris était jeté.

La clé porte désormais `${{ github.run_id }}`, avec un repli par préfixe : elle
ne touche jamais juste, chaque run sauvegarde, et le suivant reprend le plus
récent.

**Ce n'est pas le piège de #749**, où un repli désamorçait la rotation d'un cache
qu'on voulait reconstruire chaque semaine. Ce cache-ci **accumule** : reprendre
l'état précédent est exactement ce qu'on veut.

## Ce que cela coûte au prochain run

Les documents des textes portés n'étaient pas dans le cache figé : ils seront
interrogés une fois par la normalisation — c'est ce que l'index des documents
faisait déjà, pour 18 minutes au run `35087127267`. L'index des documents les
trouvera ensuite en cache. Le coût total ne bouge pas ; il change d'étape.

## Ce que ce lot ne sait pas encore

Combien de titres passeront en français. Le portail limite cette machine depuis
le matin (diagnostic dans `disjoncteur-portail-europeen-901.md`), et la mesure
ne peut venir que du run. `disjoncte` dans le résumé dira si la passe s'est
arrêtée en route.
