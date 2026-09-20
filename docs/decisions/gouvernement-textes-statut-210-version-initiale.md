<a id="gouvernement-textes-statut"></a>
# `gouvernement_textes.py` : filtre de statut par décision de séance, pas par `codeActe`/`fam_code` seul (#210) (2026-08-14)

`2026-08-14`

> **En bref** — version initiale de la décision ci-dessus, laissée en double dans le fichier d'origine — `TSORTF24` y est encore non résolu.

**Contexte** : #210 (sous-issue de #184) demandait la collecte des dossiers
législatifs d'origine gouvernementale et l'extraction de leur statut, en
s'appuyant sur le mapping `statutConclusion.fam_code` confirmé par le spike
#207 (déjà reporté dans `docs/sources/an-opendata.md`, section « Spike : origine »).
Vérification sur données réelles (téléchargement direct de
`Dossiers_Legislatifs.json.zip` le 2026-08-14, mêmes deux dossiers cités par
le spike, `DLR5L17N50588`/`DLR5L17N54196`) : un dossier accumule souvent
*plusieurs* actes portant `statutConclusion` à des dates différentes (une
décision par lecture/chambre, plus les constats de CMP et les décisions du
Conseil constitutionnel), et pas seulement les 4 `fam_code` confirmés. Deux
angles morts non couverts par le spike :
1. Le Conseil constitutionnel (`CC-CONCLUSION`) et l'accord/désaccord de CMP
   (`CMP-DEC`) portent eux aussi un `statutConclusion` (`fam_code` `TCD0x`/
   `TCCMP01`), postérieur en date à la décision de séance qui a réellement
   tranché le sort du texte (constaté sur `DLR5L17N50588` : `CC-CONCLUSION`
   daté du 2025-02-28, après l'adoption via 49.3 du 2025-02-12) — un simple
   « dernier `statutConclusion` par date » aurait donc rapporté un statut
   inexistant plutôt que le vrai statut final.
2. Le code de décision de CMP ne se termine pas par `-DEBATS-DEC` mais par
   `-AN-DEC`/`-SN-DEC` (`CMP-DEBATS-AN-DEC`, `CMP-DEBATS-SN-DEC`) : un filtre
   `codeActe.endswith("-DEBATS-DEC")` les exclut à tort, alors que ce sont de
   vraies décisions de séance (constaté sur `DLR5L17N50588`, l'unique
   occurrence connue de `TSORTF24` dans le dataset).

**Décision** :
1. `_est_decision_de_seance(code_acte)` filtre sur `"-DEBATS-" in code_acte
   and code_acte.endswith("-DEC")` plutôt qu'un `endswith` unique, pour
   couvrir les codes de CMP sans réintroduire `CC-CONCLUSION`/`CMP-DEC` (qui
   ne contiennent pas `-DEBATS-`).
2. Seule la décision de séance **chronologiquement la plus récente** parmi
   celles-ci détermine le statut du dossier (pas le dernier `statutConclusion`
   toutes origines confondues) — un dossier adopté en 1ère lecture puis
   modifié par la seconde chambre reste en navette, pas « adopté ».
3. `fam_code == "TSORTFnull"` (constaté sur un acte de décision sans issue
   tranchée) est traité comme absence d'événement, jamais comme un `fam_code`
   inconnu à signaler.
4. `TSORTF24` (rejeté consécutivement à l'engagement de l'art. 49.3, motion
   de censure adoptée) est mappé à `statut = "rejete_49_3"` + `sort_49_3 =
   True`, symétrique d'`adopte_49_3` — voir
   [[gouvernement-textes-statut-49-3-rejete]] (#208 réouverte) pour l'ajout de
   ce statut à la nomenclature fermée, qui rend la combinaison représentable
   par `schema_gouvernement.validate_profil_gouvernement` sans warning.
5. Infrastructure de téléchargement : `gouvernement_textes.py` devient la
   source canonique de `AN_DOSSIERS_ZIP_URL`/`DOSSIERS_CACHE_DIR` et d'un
   `ensure_dossiers_zip_downloaded()` partagé (écriture atomique via fichier
   `.part`) ; `candidate_profile.py` (`_build_texte_titre_index`,
   `_build_acteur_textes_portes_index`) importe désormais ces symboles au
   lieu de dupliquer le téléchargement (deux blocs identiques avant ce
   correctif) — un seul cache pour ce fichier ~10 Mo, comme demandé par #210.

**Alternative rejetée** : implémenter la chaîne `initiateur.acteurs.acteur[]
-> mandat GOUVERNEMENT -> organeRef` (dataset `AMO30`) comme signal
d'origine. Rejetée pour ce module : ~15 % de faux positifs sans filtrage par
date de mandat vs date de dépôt (co-signataires ex-ministres, mesuré par le
spike #207), pour ne couvrir que les dossiers hors préfixe de titre (2355 sur
3044, majoritairement motions/résolutions/rapports hors périmètre éditorial).
Seul le préfixe de titre (« Projet de loi » vs « Proposition de loi »,
689/3044 dossiers, aucun faux positif) est implémenté ; `AMO30` reste un
repli possible pour un futur complément, non fait ici.

