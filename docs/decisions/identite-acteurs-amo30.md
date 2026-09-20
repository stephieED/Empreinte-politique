<a id="identite-acteurs-amo30"></a>
# `_build_acteur_identite_index` : couvrir les élu⋅e⋅s dont le mandat est terminé via `AMO30`, pas en combinant `AMO20` par législature (#354) (2026-08-16)

`2026-08-16`

> **En bref** — couvrir les élu·es dont le mandat est terminé via `AMO30`, pas en combinant `AMO20` par législature.

**Contexte** : sous-issue 3/6 de #351. `_build_acteur_identite_index`
utilisait `AMO10` ("deputes_actifs_mandats_actifs_organes"), limité aux
~577 député⋅e⋅s actifs de la législature en cours — aucune entrée pour un élu
dont le mandat est terminé. L'issue proposait de combiner les archives
`AMO20_dep_sen_min_tous_mandats_et_organes*`, une par législature (15/16/17
confirmées disponibles en amont, 14 non trouvée sous les noms testés).

**Décision : réutiliser `AMO30` (`AN_ACTEURS_HISTORIQUE_ZIP_URL`), déjà en
production pour #353, plutôt que combiner des archives `AMO20` par
législature.** Vérifié par téléchargement réel (13,6 Mo, 3117
`json/acteur/*.json`, contre 577 sur `AMO10`) : `AMO30` a la même structure
que `AMO10` (`etatCivil`, `profession`, `adresses`, `mandats` — vérifié champ
par champ sur des député⋅e⋅s actifs et d'anciens député⋅e⋅s de législatures
12 à 17), mais couvre déjà tous les acteurs référencés depuis la XIe
législature — un strict sur-ensemble de ce qu'aurait apporté la combinaison
`AMO20` sur 14-17, sans avoir à retrouver l'URL introuvable de la 14e ni à
gérer 3-4 téléchargements/parseurs distincts. `AMO30` est de plus déjà
téléchargé (et mis en cache disque) par `_build_organe_index`/
`_build_acteur_positions_hemicycle_index` lors de la construction d'un profil
député : `_build_acteur_identite_index` réutilise le même
`_ensure_acteurs_historique_zip_downloaded` (issue #353) — zéro
téléchargement réseau supplémentaire dans le cas courant où organes et
identité sont tous deux résolus pour le même profil, aligné avec l'objectif
de réduction des requêtes réseau redondantes posé par l'épic #351.

**Effet de bord à corriger : sélection du mandat `ASSEMBLEE` pertinent.**
`AMO10` ne contenant qu'un mandat actif par acteur, l'ancien code prenait le
premier mandat `typeOrgane == "ASSEMBLEE"` rencontré pour en tirer
circonscription/place hémicycle. Sur `AMO30`, un acteur réélu a plusieurs
mandats `ASSEMBLEE` (un par législature) : prendre le premier trouvé aurait pu
renvoyer une circonscription obsolète pour un élu actif. Nouvelle fonction
`_select_mandat_assemblee_courant` : préfère le mandat sans `dateFin` (en
cours) s'il existe, sinon celui dont `dateDebut` est le plus récent (élu dont
le mandat est terminé).

**Alternative rejetée : combiner `AMO20` par législature.** Aurait nécessité
un téléchargement/parseur par législature (3-4 archives), une logique de
fusion pour dédupliquer un même acteur présent dans plusieurs `AMO20`
(réélections), et une couverture bornée à 14-17 — contre XIe-17e pour `AMO30`
sans effort supplémentaire. Écarté une fois `AMO30` confirmé structurellement
identique et déjà intégré au pipeline.

**Non traité ici** : le branchement des champs déjà extraits mais non encore
consommés par `build_profile` (`contact`, `numero_departement`, `numero_circo`,
`place_hemicycle`, `nom_complet`) dans le schéma pivot — prérequis posé par
la sous-issue 1, exploité par la sous-issue 4 de #351.

