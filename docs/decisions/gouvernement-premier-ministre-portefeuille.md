<a id="gouvernement-premier-ministre-portefeuille"></a>
# `gouvernement_profile` : `premier_ministre` et `portefeuille` câblés depuis les mandats `MINISTERE` (#398) (2026-08-18)

`2026-08-18`

> **En bref** — deux taux à zéro documentés comme limites de source ne l'étaient plus.

**Contexte** : l'audit remontait deux taux à **zéro absolu** — `premier_ministre`
0/10, `membres[].portefeuille` 0/36 — documentés comme des limites de source.
Les deux justifications étaient périmées : #382/#383 avaient mappé
`typeOrgane == "MINISTERE"` (l'intitulé précis du portefeuille) en
`fonction_gouvernementale`, mais `gouvernement_roster.py` / `gouvernement_profile.py`
n'avaient pas été recâblés pour le lire. La donnée était **déjà dans le dépôt**,
inexploitée.

## Deux natures de mandats dans une même catégorie

`categorie == "fonction_gouvernementale"` en mélange deux, du même zip AMO30 :

| `typeOrgane` | Label | Ce qu'il dit |
| --- | --- | --- |
| `GOUVERNEMENT` | « Gouvernement (BORNE) » | l'appartenance à CE gouvernement |
| `MINISTERE` | « Ministère de l'éducation nationale et de la jeunesse » | le portefeuille précis |

Seul le **label** les distingue (`_est_mandat_appartenance_gouvernement`) :
`categorie` est identique, et `position_dans_hemicycle` n'est renseigné que sur
les premiers. Le rattachement à un gouvernement continue de passer par le
premier — désambiguïsation éditoriale par `libelle_an`, inchangée depuis #209 —
et le portefeuille ne fait que l'enrichir.

> **Corrigé depuis (#474)** — la ligne « `MINISTERE` → le portefeuille précis »
> de ce tableau était fausse, et le paragraphe qui la suit ne l'est plus qu'à
> moitié. Le label sépare bien les deux `typeOrgane`, mais un mandat
> `MINISTERE` n'est pas nécessairement un maroquin : un parlementaire en
> mission en porte un aussi, avec pour label le ministère **auprès duquel** il
> est missionné. Voir [[parlementaire-en-mission-nest-pas-ministre]].

## Chevauchements multiples : tous, jamais un choix arbitraire

Un ministre peut changer de portefeuille en cours de gouvernement. Mesuré sur le
dépôt : 15 membres ont un seul portefeuille chevauchant, 3 en ont deux, 1 en a
trois (Laurent Wauquiez sous Fillon III). L'option retenue est **une entrée
`membres[]` par période de portefeuille**, avec les dates du portefeuille et non
celles du mandat d'appartenance — ce que `schema_gouvernement.py` décrivait déjà
(« un enregistrement par ministre et par période si changement de
portefeuille »). Fondre les périodes en une seule entrée aurait effacé un des
portefeuilles réellement occupés ; en choisir un aurait été arbitraire (§2.5).

Vérification préalable sur données réelles : **aucun** mandat `MINISTERE` ne
déborde de la période du mandat d'appartenance qu'il chevauche (0 cas sur 24).
Les dates du portefeuille sont donc reprises telles quelles, sans rognage — rien
n'est recalculé.

## Traçabilité : d'où vient la `source_url`

Le schéma exige une `source_url` dès que `portefeuille` est renseigné. Or les
mandats `MINISTERE` sortent de `candidate_profile._extract_mandats_officiels`
**sans** `source_url` (aucun mandat de ce chemin n'en porte). Le repli retenu est
la `source_url` du mandat d'appartenance du même membre : les deux mandats
viennent du **même** zip `AN_ACTEURS_HISTORIQUE_ZIP_URL`, le second se contentant
de la porter explicitement. Ce n'est donc pas une URL choisie pour satisfaire le
validateur, c'est la source réelle de l'intitulé. Sans aucune URL disponible,
`portefeuille` retombe à `null` **avec un warning** plutôt que d'être publié
sans traçabilité (§2.3).

*Alternative écartée* : corriger `_extract_mandats_officiels` pour poser
`source_url` sur tous les mandats du référentiel. C'est la correction de fond,
mais elle impose de régénérer les 68 pivots individuels (coût réseau complet) et
déborde de #398 — le repli donne exactement la même URL en attendant.

## `premier_ministre` : le cumul de deux faits, jamais la période seule

Le Premier ministre est le membre de CE gouvernement dont un mandat `MINISTERE`
porte le label « Premier ministre ». Passer par le mandat d'appartenance hérite
de la désambiguïsation déjà éprouvée du roster : l'appariement par la seule
période aurait été fragile (deux gouvernements successifs se suivent d'un jour,
et un même Premier ministre peut en diriger deux — Philippe I puis II).

`acteur_ref` est extrait de `identite.source_url`
(`.../deputes/fiche/OMC_PA722190`) par simple motif, `schema_pivot` n'exposant
pas ce champ ; une fiche d'une autre forme (Sénat) donne `None` plutôt qu'un
identifiant reconstruit. Deux candidats donneraient `None` **avec un warning** :
trancher serait arbitraire. Aucun cas dans les données actuelles.

## Résultat mesuré (audit régénéré)

| Indicateur | Avant | Après |
| --- | --- | --- |
| `premier_ministre` renseigné | 0/10 (0 %) | **3/10 (30 %)** |
| `membres[].portefeuille` renseigné | 0/36 (0 %) | **24/41 (58,5 %)** |
| Warnings de collecte | 0 | 0 |

Le dénominateur passe de 36 à 41 : c'est l'effet du découpage par période de
portefeuille, pas de nouveaux membres. Les 3 Premiers ministres sont Attal
(gouvernement Attal) et Édouard Philippe (Philippe I et II) ; les 7 autres n'ont
pas de profil pivot dans le dépôt et restent `null` **à juste titre** — ce
chiffre progressera mécaniquement avec le passage à pleine échelle du roster
(#394/#192), sans qu'aucune valeur ne soit inventée entre-temps.

Le quality gate reste passant (`exit 0`) : la couverture ministérielle
incomplète y est un signal *soft*, désormais informatif (« 8/11 portefeuilles
confirmés » plutôt que « 0/11 »).

---

