<a id="libelle-chef-du-gouvernement-au-feminin-658"></a>
# Le libellé d'organe du chef du gouvernement s'accorde en genre, la qualité jamais (#658) (2026-08-31)

`2026-08-31`

> **En bref** — `/gouvernements/BORNE` affichait « Non renseigné » alors qu'Élisabeth Borne figure dans ses propres `membres[]` : son mandat porte `label = "Première ministre"` (libellé de l'organe `PO791580`, accordé) et `fonction = "Premier ministre"` (qualité, jamais accordée), et le libellé était comparé par égalité stricte, sans même la normalisation typographique appliquée à la qualité trois lignes plus bas ; le balayage des **1 162 mandats `MINISTERE` de l'archive AMO30** (3 117 fiches acteur) tranche la question ouverte — `libQualite` n'a **que 9 valeurs, toutes au masculin**, donc une ministre déléguée est bien reconnue et `_normalise_fonction` n'a aucune raison d'être relâchée — tandis que le genre se joue sur le libellé d'organe, d'où une liste fermée relue et datée (`LABELS_PORTEFEUILLE_PREMIER_MINISTRE_OBSERVES`) plutôt qu'une règle de genre ; le double verrou de #474 reste entier et n'est pas théorique au féminin (`yannick-chenevard`, publié, porte « Première ministre » / `en mission`), 0 membre publié manqué côté qualité (260 mandats, toutes classées) ; la seule qualité restée non classée, « Haut-commissaire », est ajoutée à la liste blanche sur un motif qui est une **lecture du référentiel et non une appréciation institutionnelle** — ses 4 mandats (2 personnes) sont rangés `typeOrgane == "MINISTERE"` sous des organes de `codeType == "MINISTERE"`, celui de Jean-Paul Delevoye étant intitulé « Ministère des solidarités et de la santé – Retraites » — pour un delta mesuré de **0 mandat, 0 personne et 0 fiche** (ni Hirsch ni Delevoye n'a de profil publié : c'est un pré-positionnement verrouillé par un test) ; `premier_ministre` passe de 3/10 à **4/10** fiches, `BORNE` seule bougeant.

**Contexte** : `/gouvernements/BORNE` affichait « Premier ministre : Non
renseigné » alors qu'Élisabeth Borne figure dans les `membres[]` de sa propre
fiche. Son mandat `MINISTERE`, dans `pivot_data/profiles/elisabeth-borne.pivot.json` :

| Champ | Valeur | Origine dans AMO30 |
| --- | --- | --- |
| `label` | **« Première ministre »** | `organe.libelle` de `PO791580` |
| `fonction` | « Premier ministre » | `infosQualite.libQualite` du mandat |
| période | 2022-05-17 → 2024-01-09 | `dateDebut`/`dateFin` |

`build_premier_ministre` exige le **cumul** des deux (#474). La qualité passait ;
le libellé était comparé par `!=` à la constante `"Premier ministre"` — égalité
stricte, sans même la normalisation typographique appliquée à la qualité trois
lignes plus bas. **Les deux champs viennent d'endroits différents de la source
et ne s'accordent pas en genre.**

## Le balayage : ce qui s'accorde, et ce qui ne s'accorde pas

Relevé le 2026-08-31 sur `.cache/acteurs_historique_an/acteurs_historique.zip`
(3 117 fiches acteur), sur les **1 162 mandats `typeOrgane == "MINISTERE"`**,
en rejouant l'extraction de `candidate_profile._build_acteur_mandats_index`.

`libQualite` porte **9 valeurs distinctes, toutes au masculin** :

| `libQualite` | Mandats | Personnes | Classée aujourd'hui |
| --- | ---: | ---: | --- |
| `en mission` | 396 | 290 | non ministérielle |
| `Ministre` | 343 | 161 | ministérielle |
| `Secrétaire d'État` | 218 | 114 | ministérielle |
| `Ministre délégué` | 146 | 100 | ministérielle |
| `Ministre d'État, ministre` | 19 | 10 | ministérielle |
| `Premier ministre` | 17 | 11 | ministérielle |
| `Garde des sceaux, ministre de la justice` | 16 | 8 | ministérielle |
| **`Haut-commissaire`** | **4** | **2** | **ministérielle — ajoutée ici, voir plus bas** |
| `Ministre d'État, Garde des Sceaux, ministre de la justice` | 3 | 3 | ministérielle |

La question ouverte par l'issue — « une **ministre déléguée** est-elle
reconnue ? » — a donc une réponse mesurée : **oui**, parce que la source ne
l'écrit jamais au féminin. `FONCTIONS_MINISTERIELLES_OBSERVEES` n'a manqué
aucune forme féminine, pour la raison qu'il n'y en a pas.

Le genre se joue sur le **libellé d'organe**, et là il est bien présent : onze
libellés `MINISTERE` de l'archive portent « la Première ministre », dont un
seul est celui du chef du gouvernement — l'organe `PO791580`. Les dix autres
sont des maroquins **auprès de** Matignon (« Ministère auprès de la Première
ministre, chargé des relations avec le Parlement », « Secrétariat d'État auprès
de la Première ministre, chargé de la mer »…), qui ne doivent surtout pas être
confondus avec lui.

### Combien de membres sont manqués aujourd'hui

Deux populations, à ne pas confondre.

| Population | Mesure | Manqués |
| --- | --- | ---: |
| Les 260 mandats `MINISTERE` des **481 profils publiés** | 8 qualités rencontrées, **toutes classées** | **0** |
| Les 1 162 mandats `MINISTERE` de **l'archive AMO30** | 1 qualité alors non classée (`Haut-commissaire`) | 4 mandats, 2 personnes |
| Les **10 fiches de gouvernement publiées** | libellé de chef non reconnu | 1 (`BORNE`) |

La ligne du milieu a été traitée, et le paragraphe suivant raconte comment.

### `Haut-commissaire` : la question s'est posée, la source l'a tranchée

Ce balayage a laissé **une** qualité non classée, et la première rédaction de
cette décision proposait de l'y laisser : classer un haut-commissaire parmi les
maroquins ressemblait à une appréciation institutionnelle, qu'aucune source du
dépôt n'autorisait à porter (§2 règle 2). Le raisonnement était juste sur le
principe et faux sur les faits — **le référentiel qualifie déjà ces mandats**,
et il suffisait de le lire :

| Acteur | `organeRef` | `organe.libelle` | Période |
| --- | --- | --- | --- |
| `PA1051` Jean-Paul Delevoye | `PO766969` | **« Ministère des solidarités et de la santé – Retraites »** | 2019-09-04 → 2019-12-17 |
| `PA387853` Martin Hirsch | `PO383001` | « Haut-commissariat aux solidarités actives contre la pauvreté » | 2007-05-18 → 2007-06-18 |
| `PA387853` Martin Hirsch | `PO388139` | (même intitulé) | 2007-06-19 → 2009-01-12 |
| `PA387853` Martin Hirsch | `PO418119` | « … et Haut-commissariat à la jeunesse » | 2009-01-12 → 2010-03-22 |

Les quatre mandats portent `typeOrgane == "MINISTERE"`, aux côtés des ministres
et des secrétaires d'État ; les quatre organes de rattachement portent
eux-mêmes `codeType == "MINISTERE"` ; et celui de Delevoye est littéralement
intitulé « Ministère ». Le motif inscrit dans le code n'est donc pas « un
haut-commissaire équivaut à un ministre » — ce serait notre avis — mais
**« classé `MINISTERE` par la source »**, ce qui est un fait vérifiable, daté et
re-mesurable. La distinction est exactement celle que §2 règle 2 impose.

`"Haut-commissaire"` entre donc dans `FONCTIONS_MINISTERIELLES_OBSERVEES`, et
les 9 valeurs de `libQualite` de l'archive sont désormais **toutes classées**,
sans zone grise.

**Effet mesuré de cet ajout, isolément** — sortie de `build_gouvernement_roster`
et `build_premier_ministre` rejouée sur les 481 profils publiés, avec puis sans
la valeur dans la liste blanche :

| Indicateur | Delta |
| --- | ---: |
| Mandats changeant de classement (corpus publié) | **0** |
| Personnes concernées | **0** |
| Fiches de gouvernement dont la sortie diffère | **0** sur 10 |
| Warnings | 0 → 0 |

Aucun des deux acteurs n'a de profil pivot publié : `Haut-commissaire` apparaît
**0 fois** dans les 260 mandats `MINISTERE` du corpus. L'ajout est un
**pré-positionnement**, pas une correction — le jour où Hirsch ou Delevoye
obtient un profil (extraction pilotée par roster, #394/#192), son portefeuille
sera publié avec sa `source_url` au lieu de retomber `null` accompagné du
warning « qualité inconnue ». C'est le seul moment où la différence se verra, et
c'est pour ce moment-là que le test la verrouille.

Pas de fixture pour ce cas : inventer un pivot pour deux personnes qui n'en ont
pas serait la fixture fabriquée que #510 a fait supprimer. Le test cite les
identifiants d'organe et rejoue le classement sur les fabriques synthétiques
déjà employées par le fichier pour les cas latents (même parti que
`test_build_premier_ministre_missionne_nefface_pas_le_vrai_premier_ministre`).

## Décision : une liste fermée de libellés, pas une règle de genre

`LABEL_PORTEFEUILLE_PREMIER_MINISTRE` (scalaire) devient
`LABELS_PORTEFEUILLE_PREMIER_MINISTRE_OBSERVES` (tuple relu et daté), comparé
après normalisation typographique :

```python
LABELS_PORTEFEUILLE_PREMIER_MINISTRE_OBSERVES = ("Premier ministre", "Première ministre")
```

C'est le patron déjà employé par `FONCTIONS_MINISTERIELLES_OBSERVEES` juste
au-dessus et par `correspondance_sigles_an` dans `raw_data/groupes_reels.json` :
énumérer ce qui a été vu, après vérification, plutôt que deviner.

**`_normalise_fonction` n'est pas relâchée.** Elle reste purement
typographique — casse et espaces — et le balayage donne la raison de fond de ne
pas y toucher : rapprocher les genres sur `libQualite` ne réparerait rien,
puisque `libQualite` n'a pas de féminin. La normalisation est extraite dans
`_normalise_typographique` et exposée sous **deux** noms,
`_normalise_fonction` et `_normalise_libelle_organe`, pour que l'asymétrie
entre les deux champs se lise à l'appel au lieu de se deviner. Elle gagne au
passage un effet mesurable : `\s` couvre l'espace insécable, que la source AN
pose dans certains libellés d'organe (6 mandats `MINISTERE` de l'archive).

**Le double verrou de #474 reste entier**, et il n'est pas théorique au
féminin. Le même organe `PO791580` porte, dans l'archive, un mandat de qualité
`en mission` — et ce mandat est **publié** : `yannick-chenevard` porte
« Première ministre » / `en mission` du 2023-03-17 au 2023-09-19. Il ne devient
pas chef du gouvernement, et surtout il n'**efface** pas Élisabeth Borne : deux
candidats feraient retourner `None`. C'est le dégât que #474 a nommé, ici en
version féminine, à une nuance près — Chenevard ne porte aucun mandat
d'appartenance `Gouvernement (BORNE)`, donc le cas reste latent comme celui de
David Amiel.

## Résultat mesuré

Rejeu de `build_premier_ministre` sur les 481 profils publiés (`origin/main`,
`2660ed36`) pour les 10 gouvernements configurés :

| Indicateur | Avant | Après |
| --- | --- | --- |
| `premier_ministre` renseigné | 3/10 | **4/10** |
| Membres publiés (10 fiches) | 127 | 127 |
| Warnings émis | 0 | 0 |
| Fiches modifiées | — | `BORNE` seule |

Les deux volets du lot ne se recouvrent pas : le libellé féminin fait bouger
`BORNE` et rien d'autre, `Haut-commissaire` ne fait bouger aucune fiche.

Aucune autre fiche ne bouge, dans aucun sens. `premier_ministre` étant un
scalaire surveillé par `audit_diff_profils` (`COLLECTION_GOUVERNEMENTS`), le
sens `null` → renseigné ne bloque rien ; le sens inverse serait bloqué, et
n'arrive pas ici.

## Ce que cette décision ne traite pas

Les **six** autres fiches sans chef (`BARNIER`, `BAYROU`, `CASTEX`,
`LECORNU_II`, `FILLON_2`, `FILLON_3`) relèvent de **#644** : le chef n'est pas
dans le roster, faute de profil pivot. C'est un chantier de collecte, pas de
reconnaissance — et l'interdiction de déduire le chef du **nom** du
gouvernement reste ce qui empêche de publier « Michel Barnier » sans source.

L'issue demandait aussi de **distinguer les deux « Non renseigné » à l'écran** :
« le chef n'est pas dans notre référentiel » n'est pas « nous n'avons pas su le
reconnaître ». C'est une modification d'interface (`web/`), hors du périmètre de
ce lot.

*Alternative écartée* : dériver la forme féminine par règle (accepter
« Première » partout où « Premier » est attendu). Une règle de genre est
sémantique, elle sortirait du contrat écrit de la normalisation, et elle
accepterait des libellés que personne n'a relus — alors que la liste fermée
rend visible, datée et révisable la seule forme que la source produit
réellement.

---
