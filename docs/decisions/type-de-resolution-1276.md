# Une proposition de résolution dit ce qu'elle demande (#1276)

`2026-10-12`

> **En bref** — sous `nature_texte: proposition_de_resolution`, le pivot rangeait sans les distinguer un vœu au Gouvernement, une résolution européenne, une modification du Règlement et une **demande de commission d'enquête** ; le titre n'en dit rien, l'Assemblée intitulant ces dossiers par leur objet seul. Elle le dit sur le **document déposé** (`classification.sousType.code`) : 1 807 des 1 810 dossiers de résolution des archives XIV à XVII, sept codes. `textes_portes[]` gagne `type_resolution` (`KNOWN_TYPES_RESOLUTION`) et son motif d'absence. Rien n'est lu dans un titre, `role` n'en dérive pas, aucun compte publié ne change. **L'affichage reste à faire, côté interface.**

## Contexte

L'instantané « conditions d'enseignement » (#1217) présente parmi les textes
déposés sur l'école « Les violences commises sur les mineurs dans les temps
périscolaires et extrascolaires » (`DLR5L17N53361`). C'est une proposition de
résolution **tendant à la création d'une commission d'enquête** : le lecteur lit
un texte de fond là où un député demande une enquête.

Le pivot ne pouvait pas le dire. `nature_texte` (#689) s'arrête à
`proposition_de_resolution`, et le titre publié est celui du dossier, tel que la
source le donne.

## Ce que la source porte

Le dossier ne distingue rien : `procedureParlementaire` vaut
`{"code": "8", "libelle": "Résolution"}` pour toutes. Le document déposé — celui
que `nature_texte_depose` lit déjà pour son préfixe — porte la distinction dans
`classification.sousType`. Mesure et table complète :
`docs/sources/an-opendata.md`, « Ce qu'une proposition de résolution demande ».

## Décision

`gouvernement_textes.type_resolution_depose` lit `sousType.code` du document de
dépôt et le traduit par `TYPE_RESOLUTION_PAR_SOUS_TYPE` :

| Code de la source | `type_resolution` |
| --- | --- |
| `APPART341` | `article_34_1` |
| `TVXINSTITEUROP` | `travaux_institutions_europeennes` |
| `COMENQ` | `creation_commission_d_enquete` |
| `MODREGLTAN` | `modification_reglement_an` |
| `ACCPRESRP` | `mise_en_accusation_president` |
| `SUSPOURS` | `suspension_de_poursuites` |
| `PROPACTCOM` | `propositions_d_actes_communautaires` |

Le champ et son motif voyagent ensemble, sur le patron de `sort` /
`sort_non_resolu` (#743, #747) :

| Texte | `type_resolution` | `type_resolution_non_resolu` |
| --- | --- | --- |
| pas une résolution | `null` | `null` — la question ne se pose pas |
| résolution de l'Assemblée, type lu | une des sept valeurs | `null` |
| résolution de l'Assemblée, type non lu | `null` | `{"motif": …}`, toujours |
| résolution du Parlement européen | clé absente | clé absente |

Motifs : `sans_document`, `document_absent`, `sous_type_absent`,
`sous_type_inconnu` (avec le `code` reçu), et `non_relu` — l'entrée a été
collectée avant ce lot et aucun run n'a relu son dossier.

**Pas de report à la fusion.** `merge_dossier_records` fait gagner l'entrée
neuve : dès qu'un run relit un dossier, l'entrée arrive avec son type. Un
dossier que l'Assemblée ne sert plus reste `non_relu` — un trou déclaré.

**L'index change de nom** (`index_acteur_textes_v6.json`) : un cache porte le
code qui l'a écrit, et un `_v5` relu republierait les résolutions sans type.

Coût : l'index complet des quatre archives se construit en 16 s et 215 Mio
(poste local, une exécution), lecture des documents comprise.

## Ce que la décision ne couvre pas

- **L'affichage.** Aucun écran ne lit le champ. Le libellé — en mots de lecteur —
  et son emplacement sur la fiche de candidat, la fiche de lignée et les
  instantanés sont à arbitrer et à écrire côté interface (commentaire du
  12/10/2026 sur #1276).
- **Les agrégats.** Les fiches de groupe, de lignée et de gouvernement ne
  recopient pas le champ : il sera versé quand l'interface dira où elle le lit.
- **Les lois.** `sousType` existe aussi sur les projets et propositions de loi
  (organique, constitutionnelle, de finances, autorisant une ratification) :
  non lu ici.
- **Les résolutions européennes.** Elles ne passent pas par cette lecture et ne
  portent pas la clé.
- **Les autres titres abrégés** relevés par l'issue (`DLR5L17N53767`) : non
  regardés.

## Alternatives rejetées

- **Lire le titre long du document** (« proposition de résolution tendant à la
  création d'une commission d'enquête relative à… »). Une clé tirée d'un libellé
  rouille et se tait en rouillant (#672) ; le code de classification dit la même
  chose sans être rédigé.
- **Publier le code de la source tel quel** (`COMENQ`). Le pivot écrit ses
  valeurs fermées en `snake_case` français, et une abréviation interne de
  l'Assemblée ne se lit pas.
- **Ajouter des valeurs à `nature_texte`** (`proposition_de_resolution_commission_d_enquete`…).
  `role` en dérive et `validate_profil` tient les deux ensemble : chaque valeur
  ajoutée aurait déplacé des rôles et des comptes publiés.
