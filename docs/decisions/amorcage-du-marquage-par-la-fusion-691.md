# La fusion défaisait le marquage de la collecte : un run vert qui n'a rien basculé (#691, lot 3c)

`2026-09-09`

> **En bref** — le run `34329085168` est **vert**, a committé 2 324 fichiers et **n'a basculé aucune tranche** : zéro suppression sous `raw_data/profiles/*/1[456].json`, aucun `derivee` committé, les 5,55 Go intacts ; **les shards avaient pourtant marqué** — vérifié dans l'artifact de `gabriel-attal` — et c'est la **fusion** qui a défait ce marquage : `merge_raw_dirs` lisait l'acteur par `_acteur_du_socle(out_dir, slug)`, le socle de **destination**, jamais marqué, donc `None`, donc aucun marquage, donc tranches réécrites ; le principe du lot 3b était juste — « la fusion ne résout pas d'identité, elle reconduit ce que la collecte a déclaré » — et l'implémentation lisait le mauvais fichier, la destination au lieu des **sources** ; **troisième run vert sans effet de la journée** après #786 (transport avalé par `continue-on-error`) et #788 (branche toujours `False`), et rien ne pouvait rougir puisque **ne pas marquer est un comportement légitime** — le défaut prudent posé exprès au lot 3b —, un non-effet et un défaut prudent étant indistinguables de l'extérieur ; le test ajouté ne vérifie donc pas une absence d'erreur mais un **effet** — un socle source marqué reste marqué après fusion et sa tranche disparaît du disque —, et il échoue sur le code d'avant ; **la bascule sera progressive** : `merge_raw_dirs` ne réécrit que les slugs présents dans les artifacts, chaque profil bascule le jour où sa collecte a réussi — plus lent qu'en une fois, et plus sûr ; **le run de TEST qui précédait portait le même défaut sans pouvoir le montrer** — son artifact était marqué, sa fusion l'a défait —, pour deux raisons dont la première n'est pas technique : **on n'a pas cherché l'effet** (la vérification a porté sur la liste annoncée, qui ne contenait pas « des tranches ont disparu »), et **le log ne le donnait pas à voir** puisque l'effet vit dans le commit et qu'un run de test ne committe pas ; `merge_raw_dirs` imprime donc désormais ce qu'elle a fait aux tranches — dérivées, en fichier, retirées ce run —, **uniquement** quand il y a quelque chose à dire (#510) et avec un compte de retraits **mesuré** socle avant/après plutôt que déduit du nombre de dérivées, un profil déjà basculé ne supprimant plus rien : **un mode de test ne vaut que ce que le log donne à voir**. 4 tests neufs, suite complète à 4 295, 0 échec.

## Le constat

Le run [`34329085168`](https://github.com/stephieED/Empreinte-politique-src/actions/runs/34329085168)
est **vert**, a committé `5e7b5dca` (2 324 fichiers), et **n'a basculé aucune
tranche** : zéro fichier supprimé sous `raw_data/profiles/*/1[456].json`, et
aucun `derivee` dans les manifestes committés.

```
"tranches": [{"legislature": "15", "fichier": "15.json", "nombre": 18751},
             {"legislature": "16", "fichier": "16.json", "nombre": 16915},
             {"legislature": "17", "fichier": "17.json", "nombre": 18893}]
```

Les 5,55 Go sont toujours là.

## La cause : le bon principe, le mauvais fichier

**Les shards, eux, avaient marqué.** Vérifié dans l'artifact
`raw-profiles-an-gabriel-attal` du run :

```
{"legislature": "15", "nombre": 340, "derivee": true, "acteur_ref": "PA722190"}
{"legislature": "16", "nombre": 3,   "derivee": true, "acteur_ref": "PA722190"}
{"legislature": "17", "fichier": "17.json", "nombre": 601}
```

C'est la **fusion** qui a défait ce marquage. `merge_raw_dirs` lisait l'acteur
par `_acteur_du_socle(out_dir, slug)` — le socle de **destination**, celui du
corpus committé, qui n'a jamais été marqué. Il rendait donc `None`, `partitionner`
ne marquait rien, et les tranches étaient réécrites depuis le profil recomposé.

Le principe posé au lot 3b était juste — « la fusion ne résout pas d'identité,
elle reconduit ce que la collecte a déclaré ». L'implémentation lisait le mauvais
fichier : la destination au lieu des sources.

## Décision

L'acteur se lit dans les socles **sources** — ceux que les shards viennent
d'écrire, dans `_artifacts/` —, et le premier qui en déclare un l'emporte. La
fusion reconduit alors ce que la collecte a marqué, ce qu'elle était censée
faire.

## Le motif, pour la troisième fois de la journée

**Un run vert qui n'a rien fait.** C'est #786 (le transport avalé par
`continue-on-error`), c'est #788 (une branche qui rendait `False` à tous les
coups), et c'est celui-ci. À chaque fois, le vert ne prouvait rien parce
qu'aucun garde-fou ne mesurait l'**effet** attendu, seulement l'absence
d'erreur.

Ici, rien ne pouvait rougir : ne pas marquer une tranche est un comportement
légitime — c'est le défaut prudent posé exprès au lot 3b, « sans `acteur_ref`,
rien n'est marqué ». Un non-effet et un défaut prudent sont indistinguables de
l'extérieur.

Le test ajouté ne vérifie donc pas une absence d'erreur mais un **effet** : un
socle source marqué doit rester marqué après fusion, et sa tranche disparaître
du disque. Il échoue sur le code d'avant — vérifié.

## Pourquoi le run de TEST ne l'avait pas vu non plus

Le run de test qui précédait, `34323318020`, tournait sur le même code et
portait le même défaut. Son artifact `raw-profiles-an-gabriel-attal` était bien
marqué (`derivee: true` sur 15 et 16), et sa fusion l'a défait exactement de la
même façon.

Il ne pouvait pas le montrer, pour deux raisons dont la première n'est pas
technique :

1. **on n'a pas cherché l'effet** — la vérification a porté sur la liste
   annoncée (matrice réduite, transport, profils fusionnés, « Manquants : 0 »,
   pas de commit), et cette liste ne contenait pas « des tranches ont
   disparu » : une absence d'erreur a été prise pour une preuve ;
2. **le log ne le donnait pas à voir** — l'effet vit dans le commit, et un run
   de test ne committe pas. Le seul endroit observable était l'artifact d'un
   shard, qu'il faut penser à ouvrir.

D'où la ligne que `merge_raw_dirs` imprime désormais :

```
  · tranches d'amendements : 812 dérivée(s) de l'archive, 509 en fichier, 812 fichier(s) retiré(s) ce run.
```

Elle n'apparaît **que** si une tranche est dérivée ou retirée : un compteur
toujours imprimé et presque toujours à zéro ne se lit plus (#510). Et les
fichiers retirés sont **mesurés** — socle relu avant et après écriture — et non
déduits du nombre de dérivées : un profil déjà basculé au run précédent ne
supprime plus rien, et l'annoncer serait faux.

**Un mode de test ne vaut que ce que le log donne à voir.** C'est la leçon qui
dépasse ce lot, et elle valait d'être payée une fois.

## Ce que la bascule sera : progressive

`merge_raw_dirs` ne réécrit que les slugs présents dans les artifacts. Les
profils qu'un run ne recollecte pas gardent leur socle et leurs tranches. La
bascule se fera donc **au fil des runs**, à mesure que chaque profil repasse par
la collecte — sans perte, la fusion étant additive, et sans étape de migration.

C'est plus lent qu'une bascule en une fois, et c'est plus sûr : chaque profil
bascule le jour où sa collecte a réussi.
