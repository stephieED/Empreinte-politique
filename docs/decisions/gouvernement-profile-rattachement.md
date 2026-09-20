<a id="gouvernement-profile-rattachement"></a>
# `gouvernement_profile.py` : rattachement des textes par `date_depot`, exclusion silencieuse des dossiers non classifiables (#211) (2026-08-14)

`2026-08-14`

> **En bref** — rattachement des textes par `date_depot`, et exclusion des dossiers non classifiables.

**Contexte** : #211 combine la sortie de `gouvernement_roster.py` (composition
ministérielle, pure) et `gouvernement_textes.py` (dossiers d'origine
gouvernementale, non filtrés par gouvernement — le rattachement était
explicitement laissé hors périmètre par sa docstring) en un profil de
gouvernement complet conforme à `schema_gouvernement.py`.

**Décision** :
1. Rattachement d'un dossier à un gouvernement par recouvrement de sa
   `date_depot` avec `periode` (bornes incluses, `periode.fin = None` = borne
   haute ouverte), jamais par `date_dernier_evenement` — un texte déposé sous
   un gouvernement A puis conclu sous un gouvernement B reste crédité à A, qui
   l'a initié (décision déjà actée dans le plan d'implémentation de #184, voir
   docstring `gouvernement_textes.py`). Une `date_depot` absente exclut
   silencieusement le dossier (jamais de rattachement par défaut).
2. Un dossier dont `statut` est `None` (fam_code inconnu côté
   `gouvernement_textes.py`, voir [#gouvernement-textes-statut](gouvernement-textes-statut-210-version-initiale.md#gouvernement-textes-statut))
   ou dont `chambre_depot_initial` est `None` (aucun acte `-DEPOT`
   identifiable) est exclu de `textes[]`, avec un warning explicite dans
   `meta.warnings` : le schéma n'admet aucune valeur `null` sur ces deux
   champs (`KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL`/`KNOWN_CHAMBRES_DEPOT_TEXTE`),
   et inventer une valeur par défaut violerait la règle AGENTS.md §2.5.
   Conséquence directe : `comptages.par_statut` ne compte que les dossiers
   effectivement inclus dans `textes[]`, jamais un dossier exclu.
3. Anti double-comptage : dédoublonnage par `dossier_id` au sein d'un même
   appel à `build_gouvernement_profile` (protège contre un dossier présent
   deux fois dans l'entrée non filtrée) ; `generate_gouvernement_profiles.py`
   ne fetch les dossiers et ne charge les profils pivot qu'UNE SEULE fois
   pour l'ensemble du batch (mutualisé entre tous les gouvernements), comme
   `generate_group_profiles.py` le fait pour le roster par `(chambre,
   legislature)`. Vérifié sur les 10 gouvernements réels de
   `raw_data/gouvernements_reels.json` (run du 2026-08-14) : 61 `dossier_id`
   dans `textes[]` au total, tous distincts, aucun partagé entre deux
   fichiers `pivot_data/gouvernements/*.json`.
4. `comptages.par_statut` : uniquement des entiers bruts (dénombrement),
   aucun taux ni pourcentage — vérifié par test explicite sur les clés du
   dict (règle AGENTS.md §2.1).
5. `sources[]` du profil de gouvernement : dédoublonnées, mais limitées aux
   profils pivot des membres effectivement retenus dans `membres[]` (pas de
   tous les profils passés en entrée, qui couvrent potentiellement
   l'ensemble du dépôt local) — sinon un gouvernement à faible couverture
   afficherait des sources sans rapport avec ses membres réels.

**Vérification manuelle (critère d'acceptation #211)** : `gouvernement:ATTAL`
généré en conditions réelles inclut le dossier `DLR5L16N50115` (« Projet de
loi autorisant la ratification de la convention n°155 sur la sécurité et la
santé des travailleurs, 1981 »), déposé le 2024-06-12 (dans la période Attal,
2024-01-10/2024-09-05), `statut = "adopte"`. Confirmé contre
`assemblee-nationale.fr` : promulguée sous le n° 2025-983 au Journal officiel
du 23/10/2025.

**Hors périmètre** : `premier_ministre` reste `null` (aucune source encore
câblée pour le déterminer) ; intégration à `check_quality_gate.py` (#6) et
CI/CD (#9) non traitées ici.
*Périmé depuis #398 — voir [la section dédiée](gouvernement-premier-ministre-portefeuille.md) :
`premier_ministre` et `membres[].portefeuille` sont câblés depuis les mandats
`MINISTERE`. La source existait déjà, elle n'était pas consommée.*

