<a id="bascule-identite-an-primaire"></a>
# `fetch_identity` : identité (bio) des députés basculée sur l'AN comme source primaire, mandats/groupe restent sur NosDéputés (#355) (2026-08-16)

`2026-08-16`

> **En bref** — l'identité (bio) des députés bascule sur l'AN comme source primaire ; mandats et groupe restent sur NosDéputés.

**Contexte** : sous-issue 4/6 de #351, une fois l'index identité AN étendu
(#352), les `organeRef` résolus (#353) et la couverture multi-législatures
en place (#354). L'énoncé demandait de « basculer `fetch_identity` vers la
source officielle AN, avec repli NosDéputés uniquement si un candidat reste
introuvable dans les archives AN combinées ».

**Constat qui borne le périmètre réel** : le payload NosDéputés consommé par
`fetch_identity` sert à *deux* choses distinctes dans `build_profile` : les
champs biographiques (profession, naissance, HATVP...) et les
mandats/responsabilités + groupe parlementaire déclaré
(`_extract_mandats`, `groupe_sigle`/`groupe_nom`). Cette seconde partie n'est
**pas** encore sourcée depuis l'AN : #353 a construit l'index
`organeRef -> {sigle, nom, type}` mais son rattachement aux mandats du profil
(commissions avec rôle, groupes d'amitié, engagements extra-parlementaires)
est explicitement noté « non traité ici » dans sa propre décision — futur
travail, pas dans le périmètre de cette sous-issue. Basculer *tout*
`fetch_identity` vers l'AN aurait donc silencieusement vidé `mandats[]` et
`groupe_sigle`/`groupe_nom` pour tous les députés, une régression bien plus
large que ce que l'énoncé visait.

**Décision : ne basculer que les champs biographiques.** L'identité (bio) est
désormais résolue en priorité via `fetch_identite_officielle_par_slug`,
nouvelle fonction qui résout un `acteur_ref` AN directement depuis le slug
NosDéputés par correspondance de nom normalisé (`_build_acteur_nom_index`,
réutilise la même normalisation que le fallback nom de
`fetch_activity_synthesis`) — donc sans dépendre d'un appel réseau NosDéputés
préalable pour extraire l'URL AN, contrairement à l'ancien enrichissement
« 5bis » qui ne faisait que compléter des champs après coup. NosDéputés
reste la seule source pour les mandats/groupe, et sert de repli complet
d'identité uniquement quand le candidat est absent des archives AN
combinées (`identite_an is None`).

**Effet de bord positif, cas résiduel réduit à zéro pour l'identité (bio)** :
un député qui n'a plus de fiche exploitable sur nosdeputes.fr (ex. mandat
clos d'une législature ancienne) n'obtenait auparavant *aucune* identité —
`fetch_identite_officielle` (5bis) n'était jamais appelée car nichée sous le
bloc « parlementaire NosDéputés valide ». Désormais l'identité (bio) est
renseignée même dans ce cas, avec une URL AN synthétique
(`_acteur_ref_to_pseudo_url`, même format que le champ `url_an` de
NosDéputés) qui débloque en cascade tous les autres appels officiels AN
qui n'ont besoin que d'en extraire l'`acteur_ref` (votes, amendements,
textes portés, positions hémicycle) — seuls `mandats[]`/`groupe_sigle`
restent vides dans ce cas résiduel, avec le warning `mandats introuvables`
dédié (pas `identité introuvable`, pour ne pas mélanger les deux causes dans
`merge_profile.py`, qui filtre chaque warning sur son propre champ).

**Homonymie** : `_build_acteur_nom_index` peut associer plusieurs
`acteur_ref` à un même nom normalisé (rare mais réel sur un référentiel de
3117 acteurs, XIe-XVIIe législature). `fetch_identite_officielle_par_slug`
renonce (retourne `None, None`) plutôt que de choisir arbitrairement — pas de
règle éditoriale explicite là-dessus, mais attribuer une biographie au
mauvais élu serait pire qu'un repli NosDéputés.

**Non traité ici, reste dans le périmètre de #353/futur** : rattacher
`_build_organe_index` aux mandats du profil (commissions avec rôle, groupes
d'amitié, extra-parlementaire) et au groupe parlementaire déclaré — une fois
fait, le repli NosDéputés pourrait se réduire encore, potentiellement à zéro
pour les députés couverts par le référentiel AN.

