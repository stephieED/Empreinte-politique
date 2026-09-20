<a id="syceron-acteur-ref-nu-510"></a>
# Syceron publie l'identifiant d'orateur NU, et n'a donc jamais rien indexé (#510) (2026-08-20)

`2026-08-20`

> **En bref** — la source primaire des interventions n'avait donc jamais rien indexé.

**État relu le 20/08/2026 à 19:34 UTC ; `origin/main` = `d7d8fb1`** (le run
`32405297873` a abouti et commité `68bc094` pendant l'instruction ; PR #509
mergée). Les mesures de corpus ci-dessous portent sur cette ref.

## Le défaut, et sa mesure

`src/candidate_profile.py`, `_parse_syceron_intervention_entry` :

```python
acteur_ref = intervention.get("orateur_id_source")
if not isinstance(acteur_ref, str) or not re.fullmatch(r"PA\d+", acteur_ref):
    return None
```

L'archive Syceron publie `<orateur><id>847629</id>` — **nu**. Le `fullmatch`
échouait donc sur **100 %** des entrées, et l'index de la source *primaire* des
interventions se construisait vide. Mesuré sur les **209 profils pivot** de
`d7d8fb1` : **789 interventions publiées, dont 0 venant de Syceron**
(`www.nosdeputes.fr` 446, `questions.assemblee-nationale.fr` 293,
`2017-2022.nosdeputes.fr` 50) — chiffre inchangé depuis `f1fff09`, le run
intermédiaire n'ayant rien fait entrer par ce chemin non plus.

Reproduit sur l'archive complète de la 17e législature (601 comptes rendus,
`content-length` 55 772 428 octets, `last-modified` 2026-08-20T02:05:52Z) :
l'index sort à **0 acteur, 0 intervention, 2 octets**, en 16,2 s de parcours.

Le motif est celui de #501 et de #470 : une collecte qui rend zéro **par
construction**, invisible parce qu'un autre chemin comble le silence — ici le
repli NosDéputés, qui *rend* quelque chose et n'alarme personne.

## Pourquoi les tests ne l'ont pas vu : les fixtures décrivent un schéma inventé

`tests/fixtures/syceron_minimal.xml` et `syceron_missing_fields.xml` portent
`<id>PA123456</id>` et un `<titreStruct><intitule>` sous `<point>`. **Ni l'un ni
l'autre n'existe dans l'archive.** Elles ont été écrites d'après l'idée qu'on se
faisait du format, pas d'après le format ; le parseur a donc été validé contre
sa propre hypothèse. `tests/fixtures/syceron_reel_leg17.xml`, extraite de
`CRSANR5L17S2025O1N053.xml`, porte désormais la structure réelle, et c'est sur
elle que se prend toute mesure.

## Le préfixage suffit — et ce n'est pas une inférence, c'est écrit dans la source

Trois vérifications indépendantes, sur les 601 comptes rendus de la 17e :

1. **La source écrit les deux formes côte à côte.** Le même `<paragraphe>` porte
   l'attribut `id_acteur="PA847629"` et l'élément `<orateur><id>847629</id>`.
   `id_acteur == "PA" + orateur/id` sur **289 701 des 289 702** paragraphes qui
   portent les deux. L'unique divergence est une anomalie de la source
   (`id_acteur="PA0"` en face de `<id>335612</id>`).
2. **Tous les identifiants nus se résolvent.** Les **673 sur 673** identifiants
   nus distincts non nuls existent en `PA<id>` dans le référentiel
   `.cache/acteurs_historique_an/index_identite.json` (3 117 acteurs), dont 662
   avec concordance de nom. Les 11 « discordances » sont des orateurs nommés par
   leur fonction (« Mme la présidente ») et correctement identifiés — la
   présidente et dix vice-présidents de la 17e.
3. **Les 92 identifiants « non retrouvés » de #505 ne sont pas d'un autre
   espace.** Population : les **225** profils bruts de `d7d8fb1` (sur 229)
   portant un `acteurRef` dans `identite.url_an_ou_senat`. **119** sont dans
   l'index de la 17e, **106** n'y sont pas — et **0 des 225** est absent du
   référentiel AN. Sur ces 106, **85** ont leur dernier mandat AN terminé
   **avant** le 18/07/2024 (Barbara Pompili, Bruno Studer, Bérangère
   Couillard…), **19** sont des sénateurs sans aucun mandat AN daté, et 2 ont un
   mandat AN en cours sans avoir pris la parole dans les 601 comptes rendus. Ils
   sont absents de la **législature**, pas de l'espace d'identifiants.

Le correctif est donc un préfixage, pas une table de correspondance.

## Quatre formes d'identifiant, trois écartées par construction

`_normaliser_orateur_id_syceron` rend `(acteur_ref, motif)`. Comptes mesurés sur
la 17e (population : les 109 628 paragraphes que le parseur actuel voit) :

| Forme | Motif | Occurrences | Sort |
| --- | --- | ---: | --- |
| `847629` | `identifiant_nu_prefixe` | 104 239 | indexée sous `PA847629` |
| absente | `absent` | 3 932 | écartée (didascalie, applaudissements) |
| `0` | `orateur_collectif_anonyme` | 1 153 | écartée (« Un député du groupe RN ») |
| `-125799` | `pseudo_acteur_hors_referentiel` | 304 | écartée |
| autre | `forme_inattendue` | **0** | écartée + warning |

`0` ne doit **jamais** devenir `PA0` : c'est un orateur collectif, pas une
personne. Les identifiants négatifs sont des pseudo-acteurs de rôle ; l'archive
écrit alors `id_acteur="PA-125799"`, une valeur syntaxiquement formée qui ne
résout rien dans le référentiel.

**Ce que le rejet des négatifs coûte, mesuré plutôt que supposé** : 318
occurrences sur la 17e, pour **57 personnes distinctes**, dont **10** apparaissent
*aussi* sous un identifiant positif ailleurs dans les mêmes comptes rendus — 69
occurrences, soit **0,06 %** des 109 628 paragraphes vus. La plus fournie est
« M. François Bayrou » (42), alors Premier ministre. Ce sont donc 69 prises de
parole attribuables qui restent hors index. Les rattacher demanderait une
correspondance **par nom**, que `parse_syceron._parse_orateur` refuse déjà par
principe (« correspondance ambiguë : on préfère ne rien attribuer »), et qui sur
des homonymes fabriquerait des faits. Le choix est donc de les écarter — mais de
les **compter**.

## Le sort des non-résolus : un agrégat par législature, jamais un warning par entrée

5 389 rejets pour la seule 17e. Un warning par entrée serait pire que le
silence — c'est l'arbitrage de #492, où un warning par mandat aurait fait 214
occurrences là qu'un agrégat par profil dit la même chose. Et comme dans #474,
où les 92 parlementaires en mission sont écartés **sans** trace parce que leur
exclusion est attendue et permanente, les trois premiers motifs ne sont pas des
anomalies : ils sont comptés, pas signalés.

Ce qui est signalé, c'est **`forme_inattendue`** — à 0 mesuré. Non nul, il dit
que la forme de l'identifiant a de nouveau bougé sous le code. C'est le
compteur-témoin de ce défaut-ci.

## La garde §2.5 qui manquait, et par laquelle le défaut est passé

#505 refusait déjà de mettre en cache un index construit sur une archive
**absente** (`fichiers_lus == 0`). Mais un `{}` construit à partir de 601 comptes
rendus **lus** passait, lui, pour un résultat : une donnée manquante figée en
zéro mesuré, propagée à tous les shards de la semaine par la clé de cache.

Désormais, un index vide bâti sur une archive lisible n'est ni mis en cache ni
rendu en silence. Le mode par défaut, où l'index vide est le comportement
*attendu*, conserve la mise en cache — ne plus le faire ferait re-parcourir
l'archive (16 s) à chaque candidat, au débit du budget de 240 s de #498 — mais
il n'est plus muet non plus.

Les deux modes écrivent dans **deux fichiers d'index distincts**
(`index_par_acteur.json` / `index_par_acteur_acteurs_nus.json`) :
`.cache/syceron_an` est partagé entre les shards, et servir un index de 2 octets
à un run en mode actif serait exactement le défaut que #505 vient de corriger.

## Ce que l'activation coûterait — et pourquoi elle n'est pas prise ici

Le correctif est livré **inactif par défaut**
(`--activer-interventions-syceron`). Mesures sur la 17e législature complète :

| | Aujourd'hui | Avec la résolution |
| --- | ---: | ---: |
| Index sur disque (législature 17) | **2 octets**, 0 acteur | **136,8 Mio, 673 acteurs, 104 239 interventions** |
| Construction de l'index | 16,2 s | 23,6 s |
| Relecture de l'index, par candidat et par législature | instantanée | **1,56 s, 563 Mio de RSS** |

Sur le corpus de `d7d8fb1` (229 profils bruts, 209 pivot), **112** reçoivent
des interventions de la 17e : **+21 767** entrées, **+25,7 Mio** de brut
(1 566,2 → 1 591,9 Mio, ×1,02) et **+20,3 Mio** de pivot (100,7 → 121,0 Mio,
**×1,20**). Par profil touché : médiane +108,6 Kio de brut et +88,4 Kio de
pivot, facteur médian **×1,17**, maximum **×6,8** — `yael-braun-pivet`, 738,3
Kio → 5 027,4 Kio pour 7 026 interventions. Pour **une** législature sur les
trois de `SYCERON_AVAILABLE_LEGISLATURES`.

Confrontation aux trois chantiers du jour :

- **#429** (volumétrie, projection à 752 membres) : la projection ne comptait
  aucune intervention Syceron. À refaire avant activation.
- **#500** (budget de 240 s par candidat) : dimensionné sur une source rendant
  zéro. `_build_acteur_interventions_syceron_index` relit l'index **à chaque
  candidat et pour chaque législature** — ~4,7 s par candidat sur trois
  législatures (1,56 s mesurées par lecture ; 1,66 s de bout en bout pour les
  7 026 interventions de `PA721908`), et 563 Mio de RSS. Le remède est celui
  déjà appliqué aux
  amendements et aux scrutins (`_shard_path_acteur`, #392/#403) : **une tranche
  par acteur** au lieu d'un index monolithique. Non fait ici.
- **#505** (cache calibré sur un index de 2 octets) : à revalider sur ~410 Mio
  d'index pour trois législatures, si la 17e est représentative.

**Et surtout : ce que le correctif déverrouille n'est pas publiable en l'état.**
Deux défauts *indépendants* de #510, mesurés sur la même archive, tous deux issus
de la même cause — les fixtures inventées :

1. `parse_syceron._parse_interventions` fait `point.findall("paragraphe")`, non
   récursif, alors que les `<point>` sont **imbriqués jusqu'à nivpoint 5** :
   **212 264 des 321 892** paragraphes de la 17e sont invisibles, soit les deux
   tiers du débat. Une extraction récursive rend **231 218** interventions pour
   674 acteurs, contre 104 239.
2. `<titreStruct>` n'existe pas sous `<contenu>` — **0** occurrence sur les 601
   comptes rendus ; le titre du point vit dans `<point><texte>`. Donc `sujet`,
   `type_detail` et `theme_officiel` sortent à `None`, `"debat"` et `None` sur
   **100 %** des 104 239 entrées. Or Syceron **remplace** la liste
   d'interventions (`profile["interventions"] = syceron_interventions`) et
   `tags_thematiques` en est dérivé : activer sans corriger cela publierait
   104 239 interventions sans thème à la place de 789 qui en portent. Et le
   titre de point n'est pas davantage un thème — les plus fréquents sont
   « discussion générale » (16 467), « suspension et reprise de la séance »
   (6 769), « article 1er » : de la procédure, pas de la matière (§2 règle 8).
   Le vrai sommaire thématique existe, mais ailleurs :
   `<metadonnees><sommaire>`, non lu aujourd'hui.

Activer maintenant reviendrait à publier un ordre de grandeur de données en
plus, tronquées aux deux tiers et sans thème, à la place de données qui en
portent. **La décision d'activation est donc séparée du correctif**, et
subordonnée à ces deux corrections de parseur puis à une nouvelle mesure.

## Ce qui n'avait PAS été vérifié le 20/08 — et l'a été le 26/08

*(Tout ce qui suit dans cette sous-section décrit l'état du 20/08/2026. La suite,
datée du 26/08, est plus bas.)*

**La forme de l'identifiant sur les législatures 15 et 16.** Une seule archive a
été téléchargée — la 17e — conformément à la consigne de ne pas marteler une
source qui tombait en `IncompleteRead` tout l'après-midi du 20/08. Les 39,8 Mo
de `.cache/syceron_an/17/syseron.xml.zip.part` (téléchargement interrompu du
19/08) ont d'ailleurs fourni 71,4 % de l'archive sans aucune requête, complétés
par **une seule** requête `Range` de 15 926 540 octets ; l'assemblage passe le
contrôle CRC des 601 membres. `SYCERON_AVAILABLE_LEGISLATURES` en contient
trois : rien ne garantit que les archives antérieures publient l'identifiant
sous la même forme, et c'est **exactement le genre d'écart entre contextes qui a
produit ce défaut**. À vérifier avant toute activation.

Non vérifié non plus : que les 673 acteurs de la 17e couvrent bien tous les
députés en exercice, et l'effet sur les agrégats de groupe (`group_profile`)
d'une multiplication par 28 du volume d'interventions du corpus.

---

