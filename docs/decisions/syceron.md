<a id="syceron"></a>
# Syceron : remplacement du scraping NosDéputés pour les débats en séance (2026-08-07)

`2026-08-07`

> **En bref** — Syceron remplace le scraping NosDéputés pour les débats en séance.

**Contexte** : l'enrichissement des `interventions[]` avec le texte intégral des prises de
parole reposait jusqu'ici sur les métadonnées extraites via l'API NosDéputés (titre,
date, type) sans le texte complet des débats.

**Décision** : intégrer les comptes rendus de séance Syceron (AN Open Data,
`/vp/syceronbrut/syseron.xml.zip`) comme source primaire pour le texte intégral des
interventions en séance (L15, L16, L17).

**Pourquoi Syceron plutôt que le scraping HTML NosDéputés** : le scraping HTML de
NosDéputés/NosDeputes.fr pour les textes de débat est fragile (structure HTML non
contractuelle, susceptible de changer sans préavis, pas de version JSON officielle pour
le texte brut des interventions). Les données Syceron sont publiées directement par
l'Assemblée nationale sur son portail open data officiel sous licence Open (Etalab),
dans un format XML structuré et stable. *Alternative rejetée* : continuer avec le
scraping NosDéputés seul — non retenu car la source officielle AN est disponible,
plus fiable, et homogène avec le reste du pipeline.

**Pourquoi des modules dédiés (`syceron_debates.py`, `parse_syceron.py`) plutôt qu'une
intégration directe dans `candidate_profile.py`** : les ZIP Syceron sont des dumps
volumineux (55–149 MB) contenant des centaines de fichiers XML par législature. Le
téléchargement/cache et le parsing XML représentent des responsabilités distinctes qui
alourdiraient `candidate_profile.py` sans apport pour sa lisibilité. La séparation permet
aussi de tester le parseur de façon indépendante et de réutiliser `syceron_debates.py`
dans d'autres jobs (par exemple analyse thématique groupes) sans dépendre du pipeline
profil. `candidate_profile.py` appelle ces modules via `_build_acteur_interventions_syceron_index`
et `fetch_interventions_syceron`, ce qui reste cohérent avec le pattern déjà établi pour
les autres jeux AN (scrutins, amendements, dossiers).

Voir [`docs/sources/an-opendata.md`](../sources/an-opendata.md) (section Syceron) pour la
cartographie des URLs, la structure XML utile et la stratégie de téléchargement.

