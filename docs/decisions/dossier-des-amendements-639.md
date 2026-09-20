# Un amendement retrouve son dossier, et la clé qu'on lui avait retirée (#639, rang 3)

`2026-08-31`

> **En bref** — `fetch_amendements_officiels` écrivait `record["texte_vise"] = titre` **avant** l'écriture du profil brut : 293 582 des 484 132 amendements publiés (60,6 %) n'ont plus qu'un libellé, et les 190 550 qui ont gardé leur uid de document AN ne le doivent qu'aux trous de l'index de titres (59 263 pour la seule XIVe) ; la brique qui joint le texte au dossier — `json/document/*.json`, décrit « sans rapport, à filtrer » depuis le spike #207 — porte `dossierRef` sur **21 936 de ses 21 937 uid**, avec **0 divergence** entre les trois archives, et le rattachement se fait donc d'uid à uid, jamais par libellé même à l'égalité stricte (§2 règle 2) ; le `dossier_id` vit **une fois par texte** dans une table de fichier — 484 132 amendements ne visent que 2 248 textes distincts — ce qui coûte **+0,10 Mio mesuré après écriture** sur les quatre index (+0,04 sur `15.json`) contre +5,7 Mio pour un champ par amendement ; couverture immédiate **130 244 / 484 132 (26,9 %)** sans aucune recollecte et 99,4 % des codes présents sur XV-XVII, les 353 888 restants comptés et déclarés (291 177 en attente de recollecte, 59 236 de la XIVe dont aucune archive de dossiers n'est ingérée) ; aucun index figé n'est refusé, contrairement au rang 1 — les trois portent déjà le code.

*31/08/2026 — issue #639, rang 3. Les rangs 1 et 2 sont livrés
([[qualification-scrutins-et-cle-dossier-639]]) ; le rang 4 — le rattachement
scrutin → dossier — n'est pas traité ici.*

## Contexte

L'index d'amendements portait `texte_vise` dans deux états incompatibles, et
personne ne pouvait dire lequel en lisant une entrée.

| Forme de `texte_vise` | Amendements publiés | Exemple |
| --- | ---: | --- |
| uid de document AN | **190 550 / 484 132 (39,4 %)** | `PRJLANR5L14B1057` |
| titre de dossier, aucune clé | 293 582 (60,6 %) | « Système universel de retraite » |

**Les 60,6 % ne sont pas un plafond de la source.**
`candidate_profile.fetch_amendements_officiels` construisait un index `code de
texte → titre du dossier`, puis écrivait `record["texte_vise"] = titre` — le code
machine remplacé par un libellé **avant** l'écriture du profil brut, c'est-à-dire
dans la couche censée être au plus près de la source. Les 39,4 % qui ont survécu
sont ceux que cet index ne connaissait pas, la XIVe législature pour l'essentiel
(59 263 des 59 358 entrées) : la couverture était le fruit d'un manque, pas d'un
choix.

Et la brique qui joint un texte à son dossier n'avait jamais été ouverte.
`json/document/*.json`, seconde famille de fichiers des archives de dossiers
déjà téléchargées par le pipeline, était décrite depuis le spike #207 comme
« sans rapport, à filtrer » dans `docs/sources/an-opendata.md`. Relevé du
31/08/2026 sur les trois archives XV/XVI/XVII :

| | Mesure |
| --- | ---: |
| fichiers `json/document/` lus | 23 709 |
| uid distincts | 21 937 |
| portant un `dossierRef` | **21 936** |
| uid dont le `dossierRef` diverge d'une archive à l'autre | **0** |

Le seul document sans `dossierRef` est un texte supprimé, qui ne porte que son
`dateSuppression`. Il est en fixture.

## Décision

**1. Le code source cesse d'être écrasé.** `fetch_amendements_officiels` écrit
le `texteLegislatifRef` tel que la source le donne. `_build_texte_titre_index`
et son collecteur `_collect_texte_codes` sont **supprimés**, pas neutralisés :
son unique appelant était l'écrasement, et laisser la fabrique en place aurait
laissé le défaut à une ligne de distance (leçon de #510).

**2. Le rattachement se fait d'uid à uid.** `textes_dossiers_an.py` construit
`{uid de document → {dossier_id, titre}}` depuis `document.dossierRef` et le
`titreDossier.titre` du dossier visé. Le rapprochement par libellé — même par
égalité stricte, même à 99 % — reste exclu (`AGENTS.md` §2 règle 2) : deux
dossiers peuvent partager un intitulé, et une clé dérivée d'une chaîne n'est pas
une clé sourcée.

**3. Le `dossier_id` vit une fois par texte, dans une table de fichier.** C'est
le choix d'encodage du lot, et il est mesuré. Les 484 132 amendements publiés ne
visent que **2 248 textes distincts** — un facteur de duplication de 215, pire
que le ×3,9 qui avait justifié #431. Le libellé lisible, qui vivait recopié dans
chaque `texte_vise`, la rejoint.

```json
{"schema_version": "amendements-v1", "legislature": "17",
 "textes": {"PIONANR5L17BTC0699": {"dossier_id": "DLR5L17N50879",
                                   "titre": "Pour plus de sport et moins de sucre"}},
 "amendements": {"an:AMANR5L17…": {"texte_vise": "PIONANR5L17BTC0699", "sort": "adopte"}}}
```

Taille **réellement mesurée après écriture**, en rejouant `charger` +
`resoudre_textes` + `ecrire` sur les quatre fichiers publiés à `fab16bbf` :

| Fichier | Avant | Après | Delta | Textes en table |
| --- | ---: | ---: | ---: | ---: |
| `14.json` | 13,68 Mio | 13,68 Mio | +0,00 | 2 |
| `15.json` | 51,11 Mio | **51,14 Mio** | +0,04 | 301 |
| `16.json` | 32,57 Mio | 32,59 Mio | +0,03 | 171 |
| `17.json` | 24,95 Mio | 24,99 Mio | +0,04 | 255 |
| **total** | 122,31 Mio | 122,41 Mio | **+0,10** | |

Un `dossier_id` par amendement aurait coûté **+5,7 Mio** (29 octets × 484 132),
dont +5,9 Mio sur le seul `15.json`, déjà au-dessus du seuil d'alerte de 50 Mio
de `src/garde_fou_blobs.py`. La table en coûte 57 fois moins que la variante
« table + référence courte par amendement » chiffrée à +1,8 Mio dans l'issue,
parce qu'elle n'ajoute **aucun** champ par amendement : `texte_vise` est déjà la
référence courte.

**4. La table est optionnelle et n'a pas de version de schéma nouvelle.** Les
quatre fichiers publiés n'ont pas de clé `textes` ; l'exiger ferait échouer
`validate_amendements_index` sur tout le corpus avant sa régénération. Elle est
validée si elle est là — une entrée sans `dossier_id` est refusée, parce qu'un
texte non résolu n'a **pas d'entrée du tout** : une entrée à `null` coûterait des
octets pour ne rien dire de plus qu'une absence. Même patron que
`meta.provenance_champs` (#603).

**5. Un amendement sans dossier identifiable reste sans dossier, et il se
compte.** `resoudre_textes` rend `{textes_resolus, textes_sans_dossier,
amendements_rattaches, amendements_sans_dossier}`, imprimés par les deux points
d'entrée. **Il y en a deux, et un seul est exécuté en CI** : aucun workflow
n'appelle `build_amendements_index_pivot.py` (0 occurrence dans les six fichiers
de `.github/workflows/`), le job `merge-and-pivot` passe par
`generate_all_profiles._rafraichir_index_amendements`. Ne câbler la jointure que
dans le CLI l'aurait rendue **inerte en production** sans qu'aucun test ne
bronche ; `tests/test_dossier_amendements_639.py` verrouille les deux.
`--skip-dossiers-legislatifs` (mode léger du job roster, #357) s'en abstient :
un run qui refuse d'ouvrir ces archives n'a pas à les télécharger par la bande.

Et une table vide — archives indisponibles — n'ajoute rien et **n'efface rien** :
la règle « une collecte vide n'écrase jamais »
([[collecte-vide-necrase-jamais]]) appliquée à un index dérivé.

## Couverture obtenue

Mesurée sur les 484 132 amendements publiés, **sans aucune recollecte** : la
seule reconstruction de l'index suffit, parce que les 39,4 % qui ont gardé leur
code sont résolubles tout de suite.

| Législature | Amendements | Rattachés | | Codes présents | Codes résolus |
| --- | ---: | ---: | ---: | ---: | ---: |
| 14 | 59 358 | **27** | 0,0 % | 59 263 | 27 |
| 15 | 206 771 | 64 131 | 31,0 % | 65 022 | 64 131 |
| 16 | 121 110 | 31 514 | 26,0 % | 31 559 | 31 514 |
| 17 | 96 893 | 34 572 | 35,7 % | 34 706 | 34 572 |
| **total** | **484 132** | **130 244** | **26,9 %** | 190 550 | 130 244 |

**353 888 amendements restent sans dossier**, pour deux raisons qu'il ne faut pas
confondre :

- **291 177** parce que leur `texte_vise` est un libellé — la perte que le
  pipeline s'infligeait, et qui ne se répare qu'à la recollecte (voir ci-dessous) ;
- **59 236** parce qu'ils sont de la **XIVe législature**, dont aucune archive de
  dossiers n'est ingérée (`AN_DOSSIERS_ARCHIVES` couvre XV, XVI, XVII). Là, c'est
  un plafond de la couverture, pas un défaut : 27 documents de la XIVe traînent
  dans les archives des législatures suivantes, et c'est tout.

Sur les législatures XV-XVII, un code présent est résolu à **99,4 %**
(130 217 / 131 287).

**Projection après recollecte complète — une projection, pas une mesure.** Si
les entrées portant aujourd'hui un libellé retrouvaient leur code et se
résolvaient au taux mesuré sur les codes de leur propre législature, le corpus
passerait à **≈ 421 400 / 484 132 (87,0 %)** : ≈ 203 900 sur la XVe, ≈ 120 900
sur la XVIe, ≈ 96 500 sur la XVIIe, et toujours 27 sur la XIVe. L'hypothèse est
plutôt conservatrice — les codes qui ont survécu à l'écrasement sont précisément
ceux que l'index de titres ne connaissait pas, donc les moins bien placés pour
figurer dans un dossier. Le chiffre ne sera vérifiable qu'après la recollecte, et
il n'est **pas** mesuré ici.

## Régénération exigée

| Étape | Ce qu'elle débloque | Coût |
| --- | --- | --- |
| Une reconstruction de l'index (passe pivot de `merge-and-pivot`) | les **130 244** rattachements ci-dessus | nul — les archives sont déjà dans le cache `.cache/dossiers_an` restauré par ce job |
| Une collecte complète des profils AN | les 291 177 amendements dont le `texte_vise` est un libellé | celui d'un run complet |

La seconde étape traverse la fusion additive sans perte : `_amendement_key` de
`merge_profile.py` keye sur l'`uid`, la nouvelle entrée gagne, et le code
remplace donc le titre sur les entrées déjà écrites. Rien n'est publié de faux
entre les deux : un amendement non recollecté garde son libellé et reste
simplement sans dossier.

**Aucun index figé n'est refusé, contrairement au rang 1.** Les trois index de
`raw_data/amendements_an_figes/` portent déjà l'uid du document en `texte_vise`
(vérifié sur les trois : `"texte_vise": "PRJLANR5L15B1088"`) : l'écrasement
n'avait jamais lieu au parsing, seulement à la lecture. Il n'y a donc rien à
reconstruire, et refuser ces index ferait payer 350-650 Mo de téléchargement pour
rien.

## Effet sur les contrôles

| Contrôle | Effet | Vérifié |
| --- | --- | --- |
| `audit_diff_profils` (index amendements) | aucun : `amendements` est une **liste signalée** et les scalaires surveillés (`schema_version`, `legislature`, `licence_donnees`) ne bougent pas | rejoué sur les 8 fichiers réels avant/après : `bloquant: False`, 0 perte, 484 132 → 484 132 |
| `audit_integrite_referentielle` | aucun : `RENVOIS` ne cite pas `textes`, et il n'existe pas d'index de dossiers vers lequel une clé pourrait être orpheline | lecture de `RENVOIS` |
| `audit_collecte_vs_publie` | aucun : `RELATIONS` somme des **longueurs** de listes | lecture de `RELATIONS` |
| `validate_amendements_index` | table validée si présente, jamais exigée | 4 / 4 fichiers réels réécrits validés sans erreur |
| `garde_fou_blobs` | `15.json` reste au-dessus du seuil d'**alerte** de 50 Mio, où il était déjà, et à 28,9 Mio de l'échec dur | mesure ci-dessus |
| `*.cosignatures.json` | inchangés au bit près (hors `genere_le`) | `cmp` sur les 4 fichiers |

## Alternatives écartées

**Un champ `dossier_id` par amendement.** L'encodage le plus simple et le plus
lisible depuis un enregistrement isolé. Écarté sur mesure : +5,7 Mio pour une
information qui ne prend que 2 248 valeurs, sur l'index qui a déjà franchi le
seuil d'alerte de volume. `AmendementsIndex.dossier_de()` rend le rattachement en
une ligne, sans que l'appelant ait à connaître la table.

**Résoudre à la collecte plutôt qu'à la construction de l'index.** Aurait écrit
le `dossier_id` dans `raw_data/profiles`, couche source-near. Écarté : le job
`merge-and-pivot` a déjà les archives de dossiers en cache, et résoudre là
rattache les 130 244 amendements **déjà publiés** sans attendre une recollecte
complète. La collecte, elle, garde la seule chose qui lui revient : ne pas
détruire la clé qu'elle reçoit.

**Retrouver le code perdu en inversant l'index des titres.** Le libellé publié
est celui du dossier, et l'inverser rattacherait une grande partie des 293 582
entrées sans recollecte. C'est une jointure par chaîne, et elle est fausse dès
que deux dossiers partagent un intitulé — exactement ce que `AGENTS.md` §2
règle 2 interdit. Non mesuré, volontairement : mesurer un taux de réussite
donnerait envie de s'en servir.

**Bumper `schema_version` en `amendements-v2`.** `validate_amendements_index`
compare la version par égalité stricte : les quatre fichiers publiés seraient
devenus invalides avant leur régénération, et le contrôle qualité aurait bloqué
le commit qui les corrige.

## Ce que le lot ne règle pas

- **La XIVe législature reste sans dossiers**, faute d'archive ingérée. Ajouter
  une archive XIV à `AN_DOSSIERS_ARCHIVES` est un chantier à part : elle change
  aussi les textes portés, les fiches de gouvernement et `couverture_dossiers`.
- **Il ne rattache aucun scrutin ni aucune intervention.** Le rang 4 attend son
  arbitrage, les interventions sont hors périmètre (0 `DLR` dans les 601 comptes
  rendus Syceron de la XVIIe).
- **Il ne publie aucune vue par loi.** Le croisement est ce que l'épic #324 fera
  de la clé ; ce lot ne fait que la rendre disponible.
