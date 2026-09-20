<a id="licence-lot-6-530"></a>
# Le versant AN passe en Licence Ouverte, et `meta.licence_donnees` devient un champ dérivé (#530, lot 6 de l'épic « une seule source AN ») (2026-08-27)

`2026-08-27`

> **En bref** — « plus rien ne vient de NosDéputés » ne vaut pas « Licence Ouverte » : `meta.licence_donnees` devient un champ dérivé.

**Ce lot clôt l'épic #523, et il aurait été très facile de le clore faux.** La
formule qui vient à l'esprit — « plus rien ne vient de NosDéputés, donc le
corpus est sous Licence Ouverte » — est inexacte deux fois. Sur un produit dont
la règle éditoriale n°2 est la traçabilité intégrale, une mention légale qui
s'arrondit dans le sens du confort n'est pas un détail de forme.

## 1. Ce qui est vrai : la collecte française est intégralement sous Licence Ouverte

Depuis #528 (Sénat hors périmètre) et #529 (retrait du collecteur NosDéputés),
**aucune requête** du pipeline ne part vers Regards Citoyens. Identité, mandats,
composition des groupes, scrutins, amendements, dossiers législatifs, questions
écrites et débats en séance viennent tous de `data.assemblee-nationale.fr`, sous
**Licence Ouverte / Open Licence (Etalab)** : attribution obligatoire, **pas** de
partage à l'identique.

## 2. Ce qui reste vrai aussi, et que le lot ne surrend pas

**(a) ParlTrack reste sous ODbL v1.0**, partage à l'identique compris, pour le
versant européen. C'est une source **vivante** du pipeline
(`normalize_parltrack_dumps`), pas un héritage : elle n'a rien à voir avec le
retrait de Regards Citoyens et n'est donc pas concernée par lui.

**(b) Le corpus publié contient encore des champs dérivés de NosDéputés /
NosSénateurs**, et la fusion additive les conserve. Mesuré sur les 476 profils de
`pivot_data/profiles/` au commit `74c77c2` — c'est-à-dire **après** le premier
run complet post-#529 (run `33100214165`, vert, 447 profils réécrits) :

| Mesure | Valeur |
| --- | --- |
| profils portant une entrée `sources[].type` Regards Citoyens | **475** sur 476 (`nosdeputes` 474, `nossenateurs` 2) |
| profils dont **toutes** les sources sont Regards Citoyens | **18** (identifiants préfixés `nosdeputes:`) |
| interventions publiées dont `source_url` pointe sur `www.nosdeputes.fr` | **511**, sur 5 profils (`marine-le-pen` 246, `jerome-guedj` 200, `edouard-philippe` 50, `gabriel-attal` 10, `bruno-retailleau` 5) |
| `tags_thematiques` publiés, dérivés des `mots_cles` scrapés | **1 161**, sur 6 profils |
| mandats sénatoriaux publiés | **2** (#528 §3) |

L'attribution ODbL leur est **due** (AGENTS.md §2 règle 2). C'est exactement la
règle que #528 §4 avait déjà écrite pour la mention NosSénateurs des mentions
légales : *« elle sortira quand les données sortiront, pas avant »*. Ce lot
l'applique, il ne la révise pas.

## 3. La correction de fond de #529 §4 : `sources[]` ne se remplace pas, elle s'unit

`#529` annonçait qu'à la régénération, la première entrée `sources[]` passerait
de `nosdeputes` à `assemblee_nationale`. **Ce n'est pas ce qui s'est produit**,
et c'est vérifiable sur les 8 candidats déclarés que le run `33100214165` a
recollectés : `edouard-philippe`, `jerome-guedj`, `gabriel-attal`,
`laurent-wauquiez`, `marine-le-pen` et `bruno-retailleau` portent, après ce run,
**à la fois** leur entrée `nosdeputes` et une entrée `assemblee_nationale`
fraîchement synchronisée.

`merge_profile._merge_pivot_sources` fusionne `sources[]` **par `type`**, en
gardant l'entrée dont la `synchro_le` est la plus récente. Un type absent de la
nouvelle collecte n'est donc pas retiré : il est conservé. C'est le comportement
voulu — retirer une entrée de `sources[]` serait effacer d'où vient une donnée
toujours publiée, soit précisément ce que #460/#470 surveillent — mais il rend
**fausse** l'échéance annoncée : la mention Regards Citoyens ne disparaîtra pas
« au prochain run », et sous fusion additive elle ne disparaîtra jamais toute
seule. Seule une régénération `cold_start` / `--no-merge` la ferait tomber, et
c'est déjà, par #528, un run à perte déclarée.

## 4. Décision : `meta.licence_donnees` est un champ DÉRIVÉ, plus une constante

Une constante se serait trompée dans les deux sens à la fois : trop permissive
sur les 475 profils qui gardent du Regards Citoyens, trop restrictive sur ceux
qui n'en auront plus. `src/licences.py` porte donc les quatre libellés
canoniques et une fabrique, `appliquer_licence_donnees(profil)`, qui recompose
la chaîne à partir de `sources[]` — plus une lecture des `interventions[]`, qui
survivent à la fusion sans que `sources[]` en garde forcément trace.

C'est le patron de #493 pour `chambres`, appliqué mot pour mot : *un champ dérivé
ne se fusionne pas, il se recalcule après la fusion de ce dont il dérive.* Le
recalcul est branché aux quatre endroits qui modifient `sources[]` :
`normalize_profil`, `normalize_europarl`, `enrich_pivot_with_parltrack` et
`merge_pivot_profile` (**y compris** sa branche « pas d'ancien profil », sans
quoi un premier pivot publierait autre chose qu'un pivot régénéré au même
contenu).

**La condition de retrait est écrite et elle s'exécute d'elle-même.** Le jour où
un profil ne portera plus ni source ni intervention Regards Citoyens, la clause
ODbL disparaîtra de *son* `licence_donnees` sans décision supplémentaire. C'est
l'inverse du transitoire qui devient permanent faute de critère écrit — le
défaut que les replis de lecture de #431 et #432 ont laissé s'installer.

Deux signaux ont été **écartés**, et c'est délibéré : `mandats[].chambre ==
"Senat"` (2 mandats) et `tags_thematiques[]` (6 profils). Les profils concernés
portent déjà une source Regards Citoyens ; un troisième signal n'aurait ajouté
qu'une occasion de diverger.

## 5. La migration de valeur, déclarée avant d'être subie

`audit_diff_profils` surveille `licence_donnees` comme un **scalaire** : un
changement de valeur est *rapporté*, non bloquant (#460). Il est ici déclaré à
l'avance, avec son décompte exact, obtenu en appliquant la nouvelle fabrique aux
476 profils publiés au commit `74c77c2` :

| Valeur projetée | Profils |
| --- | --- |
| `Licence Ouverte … + ODbL v1.0 (Regards Citoyens…)` | **446** |
| `Licence Ouverte … + ODbL v1.0 (Regards Citoyens…) + CC BY 4.0 (Parlement européen…)` | **10** |
| `ODbL v1.0 (Regards Citoyens…)` seule | **18** |
| `ODbL v1.0 (Regards Citoyens…) + CC BY 4.0 (Parlement européen…)` | **1** |
| `CC BY 4.0 (Parlement européen…)` seule | **1** (inchangée) |
| **Profils dont la valeur change** | **475 sur 476** |

**Aucun fichier de `pivot_data/` ni de `raw_data/` n'est touché par ce lot.** La
migration se produira au prochain run de `generate-data.yml`, profil par profil,
au fur et à mesure des réécritures — le run `33100214165` en a réécrit 447 sur
476, ce qui donne l'ordre de grandeur d'un seul passage. Éditer les 476 fichiers
à la main aurait produit exactement le même résultat en rendant illisible le
diff du prochain run, et en laissant la **source** de la valeur inchangée : la
prochaine régénération aurait réécrit l'ancienne chaîne par-dessus.

Onze profils gagnent au passage la mention **CC BY 4.0** du Parlement européen,
qu'ils auraient dû porter depuis toujours : `generate_all_profiles` greffe les
`sources[]` européennes sur un pivot AN sans toucher à sa licence, et seul le
profil européen **pur** (`jordan-bardella`) publiait donc l'attribution du PE.
Ce n'était pas le sujet du lot ; c'est le même défaut, trouvé en le corrigeant.

## 6. Où la formulation vit désormais, et ce qui n'a pas été touché

Une seule formulation, quatre supports qui la reprennent : `src/licences.py`
(machine), `AGENTS.md` §7 (agents), `web/UI_finale/src/data/sources.config.js`
(section « Sources & fraîcheur ») et
`web/UI_finale/src/pages/LegalNoticePage.jsx` (mentions légales). L'entrée
NosDéputés/NosSénateurs **reste** dans `sources.config.js` : la retirer ferait
tomber `sourcesConfig.length`, affiché en clair par `HowItWorks` (« N sources
publiques »), et surtout retirerait une attribution encore due. Son `type` dit
maintenant ce qu'elle est — *source retirée, attribution toujours due*.

`web/old/v3/mentions-legales.html` **n'est pas modifié**. C'est une génération
de design archivée (AGENTS.md §1), que `deploy-pages.yml` ne publie pas — son
filtre de chemins ne retient que `web/UI_finale/**`. Elle porte encore la clause
de partage à l'identique globale que `#licences` avait déjà relevée comme
inexacte sans la corriger : réécrire une archive falsifierait la trace de ce qui
a été publié à l'époque. `web/old/v3/methodologie.html`, que l'issue signalait
comme duplication possible, ne contient **aucune** mention de licence — rien à
aligner.

## 7. Les 27 fiches qui ne portaient aucune attribution

Les fiches de `pivot_data/groupes/` (7), `gouvernements/` (10) et `partis/` (10)
publiaient toutes `meta.licence_donnees: ""`. Ce n'était pas une mention fausse
mais une mention **absente**, sur des documents dérivés de données ouvertes qui
en exigent une (AGENTS.md §7) : `licence_donnees` y vient d'un argument CLI
`--licence` que le pipeline ne passe jamais.

Une constante n'aurait pas convenu — `groupe-Senat-LR` et `groupe-Senat-SER`
dérivent de NosSénateurs quand les fiches AN dérivent d'AMO30. Ces trois
fabriques portent toutes un `sources[]` exploitable : elles appellent donc la
même dérivation, **et seulement quand l'appelant n'impose rien**, pour que
`--licence` reste utilisable hors pipeline. Décompte projeté sur les fiches
publiées :

| Famille | Fiches | Valeur non vide au prochain run |
| --- | --- | --- |
| `groupes/` | 7 | **7** |
| `gouvernements/` | 10 | **10** |
| `partis/` | 10 | **6** — les 4 autres n'ont aucune source, et publier une licence pour elles serait inventer une attribution |

## 8. Ce qui reste ouvert

Rien n'est laissé en suspens sur le périmètre de l'issue. Un point est
**signalé** plutôt que corrigé : l'entrée `nossenateurs` de `jean-luc-melenchon`
porte une URL LCP, pas une URL NosSénateurs — `#528` §3 l'avait déjà relevé. La
dérivation lit le `type`, pas l'URL, et attribue donc à ce profil une licence
ODbL Regards Citoyens sur la foi d'une entrée mal estampillée à la collecte.
C'est conservateur (une attribution en trop, jamais en moins) et c'est le
`type` qu'il faudrait corriger, pas la licence.

