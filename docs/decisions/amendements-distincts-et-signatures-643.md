# Un amendement cosigné n'est pas N amendements : deux grandeurs, deux noms (#643) (2026-08-31)

`2026-08-31`

> **En bref** — `_aggregate_amendements` comptait une entrée de profil par signataire et la publiait sous le mot « amendements » (92,2 % des entrées du corpus sont des cosignatures, d'où « 2 600 765 amendements déposés » pour les 76 députés d'`AN:LFI`) ; `amendements_agreges` compte désormais les amendements **distincts** et les signatures vivent sous leur nom, le facteur allant de × 5,0 à × 31,7 selon la fiche et le taux d'adoption bougeant dans les deux sens (`AN:SOC` 7,24 % → 14,54 %, `AN:LFI` 5,01 % → 2,99 % sur le seau `depute`) ; la déduplication passe par un cumul partagé par fiche — 132 960 amendements retenus au lieu de 2 647 601 signatures — et deux bandes de sort de plus rendent les six bandes sommantes, dont les 33,3 % de sorts absents qu'un décompte muet publierait comme des zéros.

`src/group_profile.py::_aggregate_amendements` itérait `for profil in profils:
for entree in profil["amendements"]` et faisait `nb_amendements += 1` **par
entrée de profil**, donc **une fois par signataire**. 92,2 % des entrées
d'amendement du corpus sont des cosignatures. La fiche `/groupes/AN-LFI-16`
publiait ainsi « 2 600 765 amendements déposés » pour un groupe de 76 députés.

## L'ampleur, re-mesurée

Mesuré le 31/08/2026 sur `f50a9439`, en comparant le seau `depute` — le seul
comparable (AGENTS.md §6) — publié, au nombre d'`amendement_id` **distincts**
signés par au moins un membre de la fiche. Les deux colonnes portent donc la
**même population**, ce que le tableau de l'issue ne faisait pas : il opposait
un seau `depute` publié à un décompte de distincts tous types confondus, d'où
des facteurs et des taux légèrement différents (× 4,6 à × 31,1, `AN:LFI`
3,32 %, `AN:SOC` 16,50 %).

| Groupe | Membres | Signatures `depute` | Distincts `depute` | Facteur | Taux publié | Taux sur les distincts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `AN:RN` | 90 | 1 175 535 | 37 093 | **× 31,7** | 2,51 % | 2,50 % |
| `AN:LFI` | 76 | 2 600 765 | 131 202 | **× 19,8** | 5,01 % | **2,99 %** |
| `AN:SOC` | 31 | 618 368 | 54 186 | **× 11,4** | 7,24 % | **14,54 %** |
| `AN:LR` | 62 | 923 446 | 156 899 | **× 5,9** | 3,55 % | 3,57 % |
| `AN:REN` | 193 | 654 775 | 132 128 | **× 5,0** | 31,23 % | **17,91 %** |
| `Senat:LR` / `Senat:SER` | 15 / 5 | 0 | 0 | — | — | — |

Deux propriétés rendent ce défaut plus grave qu'une inflation :

1. **le facteur va de × 5,0 à × 31,7 selon la fiche.** Les chiffres publiés ne
   sont pas faux d'un même coefficient : ils ne sont **pas comparables entre
   eux**, et rien à l'écran ne le laisse deviner ;
2. **le taux d'adoption bouge dans les deux sens.** `AN:SOC` double (7,24 % →
   14,54 %) pendant qu'`AN:LFI` tombe (5,01 % → 2,99 %). Numérateur et
   dénominateur sont gonflés par des nombres de cosignataires différents, donc
   le biais n'a pas de direction connue. C'est exactement ce que la §2 règle 7
   protège : un ratio publié dont le dénominateur n'est pas ce qu'il prétend
   être.

## Décision 1 — deux grandeurs, deux noms, et le taux sur les distincts

`amendements_agreges` compte désormais les amendements **distincts** portés par
au moins un membre. Les signatures ne sont pas perdues — elles décrivent une
activité réelle du groupe — mais elles vivent sous leur nom, dans un bloc
`signatures` qui ne porte **que son compte** :

```json
"amendements_agreges": {
  "nb_amendements": 56895,          // amendements distincts
  "nb_adoptes": 9386, "nb_rejetes": 19164, "nb_irrecevables": 6966,
  "nb_retires_ou_tombes": 13249,
  "nb_sort_non_renseigne": 8130, "nb_sort_non_reconnu": 0,
  "taux_adoption": 0.165,           // sur les distincts
  "nb_sans_identifiant": 0,
  "par_type_deposant": { "depute": { … }, … },
  "signatures": {
    "nb_signatures": 627068,
    "par_type_deposant": { "depute": { "nb_signatures": 618368 }, … }
  }
}
```

Aucun `nb_adoptes` du côté des signatures : le sort est une propriété de
l'amendement, pas de la signature, et l'y publier inviterait précisément le
taux que ce lot retire. Aucun champ publié ne disparaît non plus — c'est le
nom `nb_amendements` qui retrouve son sens, pas le champ qui change de nom
(`audit_diff_profils` bloque les disparitions, les 7 fiches sont publiées).

## Décision 2 — la déduplication a besoin d'un état partagé, pas d'un compteur

`ContributionAmendements` (#635) est **additive** : chaque membre est réduit à
des compteurs et ses entrées relâchées. Dédoublonner ne l'est pas — deux
membres qui cosignent le même amendement doivent le compter une fois —, il faut
donc un état commun aux membres d'une fiche. C'est
`CumulAmendementsDistincts`, que le chargeur crée **une fois par fiche** et
passe à chaque `load_profil_from_file`.

Le partage n'est pas un détail d'implémentation, c'est la condition pour ne pas
racheter la mémoire que #635 vient de rendre :

| Ce qu'on retient | `AN:LFI` | `AN:LR` |
| --- | ---: | ---: |
| un ensemble d'identifiants **par membre** | 2 647 601 | 928 832 |
| **un** cumul pour la fiche | 132 960 | 159 143 |

Le cumul ne retient d'un amendement qu'un couple *(bande de sort, seau de type
de déposant)*, les deux pris dans des ensembles fermés : les chaînes et le
couple lui-même sont partagés, seule l'entrée de dictionnaire est neuve. La
plus grosse fiche mesurée tient dans ~25 Mo. Le pipeline complet, régénérant une
fiche depuis les profils réels et l'index des 484 132 amendements, a un pic
mesuré à **510 Mio / 6,2 s** sur `AN:SOC` (31 membres) et **605 Mio / 18,2 s**
sur `AN:LFI` (76 membres, 2 647 601 signatures) — index compris. Les deux
sorties reproduisent à l'unité une mesure indépendante faite hors pipeline.

Ne rien passer reste **correct** : `_aggregate_amendements` fusionne les cumuls
qu'il trouve, et un cumul partagé n'est absorbé qu'une fois. La correction ne
dépend donc pas du câblage, seul son coût en dépend.

**Le piège, mesuré :** la table des cumuls déjà absorbés retient l'**objet**,
pas son `id()`. Un profil qui porte encore ses entrées voit sa contribution
calculée dans la boucle et relâchée à l'itération suivante ; CPython réattribue
alors l'adresse, et un `set` d'entiers déclarait « déjà absorbé » un cumul
jamais vu — trois membres portant chacun un amendement sans identifiant en
publiaient deux.

## Décision 3 — deux bandes de sort de plus, et l'invariant qui va avec

Les quatre compteurs de sort ne sommaient pas à `nb_amendements`, et le
résidu était invisible. Sur les 132 960 amendements distincts d'`AN:LFI`,
**44 243 (33,3 %) portent un `sort` nul** — 22,8 % à l'échelle des signatures
`depute` de la même fiche, ce qui montre au passage que la déduplication
**concentre** les absences plutôt que de les diluer. Les taire publierait un
tiers d'absences comme des zéros (§2 règle 5).

Deux bandes, parce que deux absences différentes :

| Compteur | Ce qu'il dit | Mesure |
| --- | --- | ---: |
| `nb_sort_non_renseigne` | le `sort` est **absent** | 8 130 sur `AN:SOC`, 44 243 sur `AN:LFI` |
| `nb_sort_non_reconnu` | le `sort` est **présent** mais hors nomenclature | **0** — les 484 132 amendements de l'index ne portent que sept libellés |

Le second est un **compteur sous surveillance** (AGENTS.md §3d), pas une
donnée : le jour où l'AN ajoute un libellé, le ranger sous « non renseigné »
publierait une valeur présente comme une absence, l'erreur exactement
symétrique. Avec les deux, les six bandes somment à `nb_amendements` — un
invariant vérifiable, verrouillé par un test, et ce qui rend une barre empilée
honnête.

`gouvernement` et `inconnu` restent publiés à zéro dans `par_type_deposant`
pour la même raison : structurellement vides sur les 7 fiches, sous
surveillance, jamais supprimés en silence.

## Décision 4 — une entrée sans identifiant n'est pas dédoublonnable, et le dit

Une entrée sans `amendement_id` n'est rapprochable d'aucune autre : la fusionner
demanderait une clé, et on n'en invente pas (§2 règle 5). Elle est donc comptée
**telle quelle**, une fois par signataire — et `nb_sans_identifiant` publie
combien, avec un `meta.warnings` dès qu'il n'est pas nul. Sans lui,
`nb_amendements` mélangerait en silence des amendements dédoublonnés et des
signatures, ce qui est le défaut que ce lot corrige, sous une autre forme.

**Zéro cas sur les 7 fiches publiées au 31/08/2026.** C'est en revanche la forme
normale des amendements du Parlement européen (ParlTrack les livre sans `uid`
AN) et celle de toute entrée d'avant #431 restée autoportante.

## Alternative écartée — garder `nb_amendements` sur les signatures et ajouter `nb_amendements_distincts`

Le champ publié aurait gardé sa valeur, donc son sens faux, et la fiche aurait
porté côte à côte deux nombres dont le plus visible reste celui qui annonce
2,6 millions d'amendements pour 76 députés. Le mot « amendements » désigne des
amendements : c'est la **valeur** qui était fausse, pas le nom.

## Alternative écartée — dédoublonner dans `_aggregate_amendements`

Il faudrait que les `amendement_id` survivent à la projection de #635, soit
2 647 601 chaînes pour la seule fiche LFI, retenues jusqu'à l'agrégation. C'est
la mémoire que #635 vient d'écarter, rachetée pour un résultat identique.

## Ce que ce lot ne corrige pas, et qu'il faut lire avant de régénérer

**Le contrôle de perte ne verra pas la chute.** `audit_diff_profils.py` ne
compare que les champs déclarés dans ses `Collection`, et `COLLECTION_GROUPES`
ne nomme `amendements_agreges` ni dans ses listes ni dans ses scalaires : la
chute de 2,6 M à 133 k sur `AN:LFI` passera sans un mot, et
`allow_declared_losses` n'a rien à déclarer. Un dénominateur publié
(§2 règle 7) qu'aucun contrôle pré-commit ne regarde, c'est la faille que #470
avait payée sur `tags_thematiques` — à instruire séparément,
`audit_diff_profils.py` étant hors du périmètre de ce lot.

**La bande « sort non renseigné » n'est publiée que côté données.** L'UI
(`web/UI_finale/src/data/pivotAdapter.js`, `AMENDMENT_OUTCOME_KEYS`) empile
trois segments — adopté, rejeté, irrecevable — et ne lit ni les retirés/tombés
ni les deux nouvelles bandes. Tant qu'elle ne les lit pas, la barre publie un
tiers d'absences comme des zéros. C'est le lot UI de l'épic #324 (#594).

**`membres_eligibles` va bouger dans le même run, pour une autre raison.** La
régénération des 5 fiches AN qu'exige ce lot est aussi la première depuis
#647 (#640), qui reconstruit tous les mandats électifs. `membres_eligibles`
— le dénominateur de `cohesion_votes`, calculé par chevauchement avec ces
périodes (#492) — passe de moyennes dérisoires à l'effectif réel du groupe.
Mesuré le 31/08/2026 en rejouant `_periodes_mandats_assemblee` sur l'archive
AMO30 en cache et `_member_eligibility_intervals` sur chaque scrutin publié
(la colonne « avant » reproduit à l'unité les valeurs publiées, ce qui valide
la mesure) :

| Fiche | Membres | Scrutins | `membres_eligibles` moyen avant | après #647 | Facteur |
| --- | ---: | ---: | ---: | ---: | ---: |
| `AN:RN` | 90 | 4 085 | 10,6 | **88,6** | × 8,4 |
| `AN:SOC` | 31 | 3 843 | 4,8 | **30,9** | × 6,4 |
| `AN:LFI` | 76 | 3 973 | 15,2 | **75,0** | × 4,9 |
| `AN:LR` | 62 | 3 832 | 18,4 | **60,9** | × 3,3 |
| `AN:REN` | 193 | 4 099 | 90,0 | **180,0** | × 2,0 |

C'est une **simulation** : les périodes reconstruites sont unies aux intervalles
publiés sans passer par la fusion réelle des profils, et aucun run n'a encore
été lancé. `taux_participation`, `taux_coherence` et `quorum_atteint` bougeront
d'autant. `_compute_cohesion_votes` n'est pas touché par ce lot — il n'y a rien
à y corriger : la fonction lisait fidèlement des mandats incomplets.
