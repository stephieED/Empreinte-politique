# Les décisions qui gouvernent chaque module

**Fichier généré — ne pas le modifier à la main.**
`python3 scripts/generer_decisions_par_module.py` le réécrit ;
`tests/test_decisions_par_module.py` échoue s'il a dérivé.

[`docs/technical_decisions.md`](technical_decisions.md) va des décisions vers le
code et se lit par date. Cette table va dans l'autre sens : **ce module → ces
décisions**, pour qu'un agent qui ouvre un fichier de `src/` sache ce qui le
gouverne sans avoir à fouiller le répertoire des décisions.
Le critère, ce qu'il rate et pourquoi la table est générée :
[`docs/decisions/table-inversee-decisions-par-module.md`](decisions/table-inversee-decisions-par-module.md).

## Ce que « gouverne » veut dire ici

Une décision **gouverne** un module quand elle nomme **un symbole de tête de ce
module** — une fonction, une classe ou une constante définie au niveau du module —
soit qualifié (`merge_profile.fusionner_couverture`), soit nu à condition que ce
symbole soit défini dans ce seul module de `src/`. La colonne « nomme » dit
lesquels.

Une décision qui ne nomme que le **fichier** (`merge_profile.py`) ou le module nu
le **mentionne** sans le gouverner : elle dit qu'il est concerné, pas quel contrat
il doit tenir. Ces décisions-là sont listées à part, en fin de section.

Le critère est mécanique et volontairement faillible dans un sens précis : il rate
une décision qui gouverne un module sans nommer aucune de ses fonctions. En
échange il ne rouille pas — un symbole renommé ou supprimé retire le lien au lieu
de le laisser pointer vers du code qui n'existe plus.

---

## Les modules qui ne citent aucune de leurs décisions

Ce que ce fichier existe pour rendre visible. `tests/test_decisions_par_module.py`
échoue au-delà du seuil qu'il fixe.

| Module | Décisions qui le gouvernent |
| --- | ---: |
| `src/parse_syceron.py` | 4 |
| `src/perimetre_candidats.py` | 4 |
| `src/amendements_contenu.py` | 3 |
| `src/audit_pipeline.py` | 3 |
| `src/budget_collecte.py` | 3 |
| `src/json_io.py` | 3 |
| `src/purge_mandats_dupliques.py` | 3 |
| `src/rne_opendata.py` | 3 |
| `src/audit_gouvernement_dataset.py` | 2 |
| `src/avertissements.py` | 2 |
| `src/build_amendements_index.py` | 2 |
| `src/fetch_candidats_declares.py` | 2 |
| `src/titres_europeens.py` | 2 |
| `src/actes_reglementaires.py` | 1 |
| `src/candidate_profile_ue.py` | 1 |
| `src/collecte_mandats_locaux.py` | 1 |
| `src/documents_europeens.py` | 1 |
| `src/generate_lignee_profiles.py` | 1 |
| `src/gouvernement_roster_an.py` | 1 |
| `src/identifiants_wikidata.py` | 1 |
| `src/lignee_profile.py` | 1 |
| `src/mandats_anterieurs.py` | 1 |
| `src/normalize_europarl.py` | 1 |
| `src/normalize_senat.py` | 1 |
| `src/purge_interventions_heritees.py` | 1 |
| `src/retrait_heritage_senat.py` | 1 |
| `src/scrutins_dossiers_an.py` | 1 |
| `src/scrutins_legislature.py` | 1 |
| `src/senat_mandats.py` | 1 |
| `src/textes_promulgues.py` | 1 |
| `src/textes_vises_figes.py` | 1 |
| `src/verifier_transport_artifacts.py` | 1 |

---

## `src/actes_reglementaires.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Un acte publie les lois qu'il applique et celles qu'il cite, et ces liens se corrigent après coup (2026-09-23)](decisions/liens-des-actes-vers-les-lois.md) | `corriger_les_liens` |

Le mentionnent sans le gouverner : [`actes-reglementaires-du-journal-officiel-1029`](decisions/actes-reglementaires-du-journal-officiel-1029.md), [`table-figee-numero-de-loi-vers-jorftext`](decisions/table-figee-numero-de-loi-vers-jorftext.md).

## `src/amendements_contenu.py`

3 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Les actes réglementaires du Journal officiel, par mois et par mots (#1029 voie 1) (2026-09-22)](decisions/actes-reglementaires-du-journal-officiel-1029.md) | `forme_indexee`, `mots_du_texte` |
| [Trouver les amendements d'un sujet par leur exposé, sur les fiches (#1029) (2026-09-22)](decisions/amendements-par-mot-sur-les-fiches-1029.md) | `forme_indexee` |
| [Trouver les amendements d'un sujet : l'article visé et un index de mots de l'exposé (#1029) (2026-09-22)](decisions/index-de-mots-des-amendements-1029.md) | `forme_indexee` |

## `src/amendements_index.py`

3 décision(s) le gouvernent ; le module en cite 1.

| Décision | Nomme |
| --- | --- |
| [Un créneau de séance n'est pas un sujet, et le discriminant reste structurel (#710, 02/09/2026)](decisions/creneau-de-seance-nest-pas-un-sujet-710.md) | `backfill_texte_vise` |
| [Un amendement retrouve son dossier, et la clé qu'on lui avait retirée (#639, rang 3)](decisions/dossier-des-amendements-639.md) | `AmendementsIndex`, `resoudre_textes` |
| [Le `texte_vise` fautif se reprend depuis l'archive figée, pas par une fusion plus permissive (#696, 01/09/2026)](decisions/report-texte-vise-source-696.md) | `backfill_texte_vise`, `merge_amendements_index`, `resoudre_textes` |

Le mentionnent sans le gouverner : [`fiche-de-lignee-836`](decisions/fiche-de-lignee-836.md), [`index-reecrits-seulement-si-le-contenu-change-1075`](decisions/index-reecrits-seulement-si-le-contenu-change-1075.md), [`lectures-pipeline-par-projection-635`](decisions/lectures-pipeline-par-projection-635.md), [`normalisation-amendements`](decisions/normalisation-amendements.md), [`partition-profils-legislature-580`](decisions/partition-profils-legislature-580.md), [`point-de-sauvegarde-dans-les-profils-518`](decisions/point-de-sauvegarde-dans-les-profils-518.md), [`reconstruction-tranches-depuis-archive-691`](decisions/reconstruction-tranches-depuis-archive-691.md).

## `src/an_roster.py`

13 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [La bascule : le roster des groupes AN vient d'AMO30 (#527, lot 1b de l'épic « une seule source AN ») (2026-08-26)](decisions/bascule-roster-an-amo30-527.md) | `AN_ROSTER_ACTIF`, `RosterAnInactif`, `RosterAnIndisponible`, `fetch_full_roster_an` |
| [`debut_dans_groupe` se lit sur le mandat de groupe, plus sur le premier mandat électif (#653) (2026-08-31)](decisions/dates-appartenance-groupe-653.md) | `deriver_membres_organes`, `organes_du_groupe` |
| [L'effectif d'un groupe dans le temps : `min_historique` et `max_historique` portent leur date (#702) — 01/09/2026](decisions/effectif-du-groupe-dans-le-temps-702.md) | `_fusionner_periodes` |
| [Une entrée dérivée gèle un slug fabriqué, elle ne prouve plus rien (#715) (2026-09-02)](decisions/entree-derivee-correspondance-715.md) | `resoudre_slugs` |
| [Les lignées MoDem, Horizons et LIOT, et un tri qui plantait sur un seul député (#815)](decisions/lignees-modem-horizons-liot-815.md) | `deriver_roster_groupe`, `fusionner_intervalles` |
| [L'appartenance publiée cesse d'être une enveloppe (#809)](decisions/periodes-appartenance-809.md) | `_fusionner_periodes` |
| [La position politique d'un groupe est celle que l'Assemblée déclare, lue dans une table committée (#686) (2026-09-01)](decisions/position-politique-groupes-686.md) | `VERSION_INDEX_GP` |
| [NosDéputés sort du pipeline (#529, lot 5 de l'épic « une seule source AN ») (2026-08-27)](decisions/retrait-nosdeputes-529.md) | `AN_ROSTER_ACTIF`, `RosterAnInactif` |
| [Le Sénat sort du périmètre, et le job qui concluait vert sans rien produire est retiré (#528, lot 3 de l'épic « une seule source AN ») (2026-08-26)](decisions/retrait-senat-528.md) | `AN_ROSTER_ACTIF` |
| [Le roster des groupes AN est dérivé d'AMO30, derrière un drapeau baissé (#526, lot 1 de l'épic « une seule source AN ») (2026-08-26)](decisions/roster-an-derive-amo30-526.md) | `AN_ROSTER_ACTIF`, `RosterAnIndisponible`, `fetch_full_roster_an` |
| [Les membres d'un gouvernement reçoivent un identifiant de profil (#996, lot 2) (2026-09-17)](decisions/roster-gouvernements-amo30-996.md) | `resoudre_slugs` |
| [Un membre de roster sans correspondance relue reçoit un slug, et la collision reste un refus (#708) (2026-09-02)](decisions/slug-fabrique-membre-de-roster-708.md) | `MOTIFS_SLUG_NON_ATTRIBUE`, `resoudre_slugs` |
| [Trois fiches, et six lignées qui remontent enfin (#815, lot 2)](decisions/trois-fiches-de-continuite-815.md) | `est_mandat_de_transit` |

Le mentionnent sans le gouverner : [`periodes-jetees-par-le-filtre-809`](decisions/periodes-jetees-par-le-filtre-809.md).

## `src/audit_collecte_non_publiee.py`

Le mentionnent sans le gouverner : [`cle-fusion-interventions-540`](decisions/cle-fusion-interventions-540.md), [`cloisonnement-branche-roster-524`](decisions/cloisonnement-branche-roster-524.md), [`collecte-non-publiee`](decisions/collecte-non-publiee.md), [`collecte-vs-publie-545`](decisions/collecte-vs-publie-545.md), [`extraction-groupe-suspendue-516`](decisions/extraction-groupe-suspendue-516.md), [`fiches-groupe-17e-legislature-700`](decisions/fiches-groupe-17e-legislature-700.md), [`partition-profils-legislature-580`](decisions/partition-profils-legislature-580.md), [`roster-unique-par-run-518`](decisions/roster-unique-par-run-518.md).

## `src/audit_collecte_vs_publie.py`

2 décision(s) le gouvernent ; le module en cite 1.

| Décision | Nomme |
| --- | --- |
| [« Collecté = publié » compte une tranche dérivée dans l'archive (#691, lot 3a)](decisions/audit-compte-les-tranches-derivees-691.md) | `compter_listes_profil_brut` |
| [Le seuil de blob sort du critère de sortie, et les profils bruts se partitionnent par législature (#580) (2026-08-29)](decisions/partition-profils-legislature-580.md) | `compter_listes_profil_brut` |

Le mentionnent sans le gouverner : [`cle-fusion-textes-portes-668`](decisions/cle-fusion-textes-portes-668.md), [`collecte-vs-publie-545`](decisions/collecte-vs-publie-545.md), [`defaut-collecte-vs-panne-562`](decisions/defaut-collecte-vs-panne-562.md), [`dossier-des-amendements-639`](decisions/dossier-des-amendements-639.md), [`populations-profils-portees-par-les-outils-630`](decisions/populations-profils-portees-par-les-outils-630.md), [`qualification-scrutins-et-cle-dossier-639`](decisions/qualification-scrutins-et-cle-dossier-639.md), [`reconstruction-tranches-depuis-archive-691`](decisions/reconstruction-tranches-depuis-archive-691.md), [`reduction-nommee-collecte-vs-publie-888`](decisions/reduction-nommee-collecte-vs-publie-888.md), [`tranches-derivees-lecteur-691`](decisions/tranches-derivees-lecteur-691.md).

## `src/audit_diff_profils.py`

6 décision(s) le gouvernent ; le module en cite 2.

| Décision | Nomme |
| --- | --- |
| [Les agrégats publiés entrent dans le contrôle de perte, et l'ordre de grandeur reste hors contrat (#649) (2026-08-31)](decisions/agregats-publies-controle-perte-649.md) | `_resume_scalaire` |
| [Un amendement cosigné n'est pas N amendements : deux grandeurs, deux noms (#643) (2026-08-31)](decisions/amendements-distincts-et-signatures-643.md) | `COLLECTION_GROUPES`, `Collection` |
| [Le contrôle de perte nomme ce qui a disparu (#823)](decisions/controle-perte-nomme-les-echanges-823.md) | `_identites` |
| [L'effectif d'un groupe dans le temps : `min_historique` et `max_historique` portent leur date (#702) — 01/09/2026](decisions/effectif-du-groupe-dans-le-temps-702.md) | `COLLECTION_GROUPES` |
| [L'`id` d'un profil pivot est le slug : le préfixe de provenance était instable (#487) (2026-08-20)](decisions/id-pivot-sans-prefixe.md) | `COLLECTION_PROFILS` |
| [Le libellé d'organe du chef du gouvernement s'accorde en genre, la qualité jamais (#658) (2026-08-31)](decisions/libelle-chef-du-gouvernement-au-feminin-658.md) | `COLLECTION_GOUVERNEMENTS` |

Le mentionnent sans le gouverner : [`bascule-roster-an-amo30-527`](decisions/bascule-roster-an-amo30-527.md), [`boucle-perimetre-candidats-757`](decisions/boucle-perimetre-candidats-757.md), [`cache-amendements-existence-nest-pas-conformite`](decisions/cache-amendements-existence-nest-pas-conformite.md), [`chambres-profil-derivees`](decisions/chambres-profil-derivees.md), [`civilite-et-pcs-insee-659`](decisions/civilite-et-pcs-insee-659.md), [`cle-fusion-interventions-540`](decisions/cle-fusion-interventions-540.md), [`cle-fusion-textes-portes-668`](decisions/cle-fusion-textes-portes-668.md), [`collecte-interventions-reduite-au-theme-657`](decisions/collecte-interventions-reduite-au-theme-657.md), [`collecte-non-publiee`](decisions/collecte-non-publiee.md), [`collecte-vs-publie-545`](decisions/collecte-vs-publie-545.md), [`consommateurs-chambres-migres`](decisions/consommateurs-chambres-migres.md), [`controle-de-perte-avant-commit`](decisions/controle-de-perte-avant-commit.md), [`correspondance-acteurs-an-525`](decisions/correspondance-acteurs-an-525.md), [`creneau-de-seance-nest-pas-un-sujet-710`](decisions/creneau-de-seance-nest-pas-un-sujet-710.md), [`date-de-reference-des-comptes-de-groupe-653`](decisions/date-de-reference-des-comptes-de-groupe-653.md), [`dates-appartenance-groupe-653`](decisions/dates-appartenance-groupe-653.md), [`derniere-lecture-retenue-711`](decisions/derniere-lecture-retenue-711.md), [`destinataire-avertissements-642`](decisions/destinataire-avertissements-642.md), [`dossier-des-amendements-639`](decisions/dossier-des-amendements-639.md), [`doublons-textes-europeens-cle-doceo-901`](decisions/doublons-textes-europeens-cle-doceo-901.md), [`extraction-groupe-suspendue-516`](decisions/extraction-groupe-suspendue-516.md), [`fenetre-historique-donnees`](decisions/fenetre-historique-donnees.md), [`fenetre-recalibrage-551`](decisions/fenetre-recalibrage-551.md), [`fiches-groupe-17e-legislature-700`](decisions/fiches-groupe-17e-legislature-700.md), [`fiches-masquees-candidatures-declinees-761`](decisions/fiches-masquees-candidatures-declinees-761.md), [`filtre-publication-apres-fusion-641`](decisions/filtre-publication-apres-fusion-641.md), [`identite-profils-539`](decisions/identite-profils-539.md), [`licence-lot-6-530`](decisions/licence-lot-6-530.md), [`liste-candidats-declares-753`](decisions/liste-candidats-declares-753.md), [`mandat-electif-perdu-fausse-le-denominateur`](decisions/mandat-electif-perdu-fausse-le-denominateur.md), [`mandats-agreges-siege-vs-passe-656`](decisions/mandats-agreges-siege-vs-passe-656.md), [`mandats-electifs-liste-complete-640`](decisions/mandats-electifs-liste-complete-640.md), [`marquage-tranches-derivees-691`](decisions/marquage-tranches-derivees-691.md), [`nettoyage-sediment-839`](decisions/nettoyage-sediment-839.md), [`notifications-de-suivi`](decisions/notifications-de-suivi.md), [`overwrite-profiles-sans-purge-cache`](decisions/overwrite-profiles-sans-purge-cache.md), [`partition-profils-legislature-580`](decisions/partition-profils-legislature-580.md), [`perimetre-collecte-candidatures-declinees-760`](decisions/perimetre-collecte-candidatures-declinees-760.md), [`profession-code-nomenclature-641`](decisions/profession-code-nomenclature-641.md), [`publication-dun-job-annule`](decisions/publication-dun-job-annule.md), [`publication-scopee-artifacts`](decisions/publication-scopee-artifacts.md), [`qualification-perdue-a-la-fusion-639`](decisions/qualification-perdue-a-la-fusion-639.md), [`qualification-scrutins-et-cle-dossier-639`](decisions/qualification-scrutins-et-cle-dossier-639.md), [`qualification-textes-portes-689`](decisions/qualification-textes-portes-689.md), [`reconstruction-tranches-depuis-archive-691`](decisions/reconstruction-tranches-depuis-archive-691.md), [`restauration-interventions`](decisions/restauration-interventions.md), [`retrait-groupes-senat-nossenateurs`](decisions/retrait-groupes-senat-nossenateurs.md), [`retrait-nosdeputes-529`](decisions/retrait-nosdeputes-529.md), [`retrait-senat-528`](decisions/retrait-senat-528.md), [`roster-an-derive-amo30-526`](decisions/roster-an-derive-amo30-526.md), [`slug-fabrique-membre-de-roster-708`](decisions/slug-fabrique-membre-de-roster-708.md), [`tranches-derivees-lecteur-691`](decisions/tranches-derivees-lecteur-691.md).

## `src/audit_gouvernement_dataset.py`

2 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Épic #316 — tableaux croisés des plages temporelles (#317/#318/#320/#321) : bilan et décisions transverses (2026-08-15)](decisions/audit-plages-temporelles.md) | `compute_plage_dates_gouvernements` |
| [Un test d'acceptation adossé au corpus vivant rougit quand la donnée s'améliore (#457) (2026-08-20)](decisions/test-adosse-au-corpus-vivant.md) | `compute_taux_portefeuille_renseigne` |

Le mentionnent sans le gouverner : [`audit-pipeline-gouvernement`](decisions/audit-pipeline-gouvernement.md), [`couverture-dossiers-hors-couverture-vs-zero`](decisions/couverture-dossiers-hors-couverture-vs-zero.md).

## `src/audit_groupe_dataset.py`

6 décision(s) le gouvernent ; le module en cite 1.

| Décision | Nomme |
| --- | --- |
| [Un audit qui lit un champ déplacé ne se tait pas : il crie 62 000 fois (#726) (2026-09-03)](decisions/audit-champs-deplaces-726.md) | `MOTIFS_DATE_NON_RESOLUE`, `_plage_cohesion_votes`, `compute_plage_dates_groupes` |
| [Épic #316 — tableaux croisés des plages temporelles (#317/#318/#320/#321) : bilan et décisions transverses (2026-08-15)](decisions/audit-plages-temporelles.md) | `compute_plage_dates_groupes` |
| [Tous les comptes d'une fiche de groupe se rapportent à une date, et elle est publiée (#653) (2026-08-31)](decisions/date-de-reference-des-comptes-de-groupe-653.md) | `CHAMPS_EFFECTIF` |
| [L'effectif d'un groupe dans le temps : `min_historique` et `max_historique` portent leur date (#702) — 01/09/2026](decisions/effectif-du-groupe-dans-le-temps-702.md) | `compute_effectifs` |
| [Les 5 groupes de la XVIIe entrent dans `groupes[]`, et leur succession est déclarée comme une relecture (#700) (2026-09-01)](decisions/fiches-groupe-17e-legislature-700.md) | `compute_doublons_groupe_id` |
| [Tableau croisé des plages temporelles par groupe (#318, sous-issue 2/6 de #316) (2026-08-15)](decisions/plage-dates-groupes.md) | `compute_plage_dates_groupes`, `compute_tableau_croise_groupes` |

Le mentionnent sans le gouverner : [`audit-pipeline-gouvernement`](decisions/audit-pipeline-gouvernement.md), [`consommateurs-chambres-migres`](decisions/consommateurs-chambres-migres.md), [`merge-and-pivot-budget-permissions-413`](decisions/merge-and-pivot-budget-permissions-413.md), [`quality-gate-gouvernements`](decisions/quality-gate-gouvernements.md), [`senat-periode-debut`](decisions/senat-periode-debut.md), [`seuil-couverture-groupe`](decisions/seuil-couverture-groupe.md).

## `src/audit_integrite_referentielle.py`

Le mentionnent sans le gouverner : [`audit-des-rattachements`](decisions/audit-des-rattachements.md), [`collecte-non-publiee`](decisions/collecte-non-publiee.md), [`collecte-vs-publie-545`](decisions/collecte-vs-publie-545.md), [`dossier-des-amendements-639`](decisions/dossier-des-amendements-639.md), [`perimetre-controle-perte`](decisions/perimetre-controle-perte.md), [`purge-textes-portes-roster-747`](decisions/purge-textes-portes-roster-747.md), [`qualification-perdue-a-la-fusion-639`](decisions/qualification-perdue-a-la-fusion-639.md), [`qualification-scrutins-et-cle-dossier-639`](decisions/qualification-scrutins-et-cle-dossier-639.md), [`retrait-fiches-parti-906`](decisions/retrait-fiches-parti-906.md), [`retrait-marqueur-regards-citoyens-deputes-890`](decisions/retrait-marqueur-regards-citoyens-deputes-890.md), [`retrait-senat-528`](decisions/retrait-senat-528.md).

## `src/audit_legislature_votes.py`

Le mentionnent sans le gouverner : [`partition-profils-legislature-580`](decisions/partition-profils-legislature-580.md), [`point-de-sauvegarde-dans-les-profils-518`](decisions/point-de-sauvegarde-dans-les-profils-518.md), [`resolution-legislature-deux-mecanismes-432`](decisions/resolution-legislature-deux-mecanismes-432.md).

## `src/audit_mandats_reproductibles.py`

Le mentionnent sans le gouverner : [`reproductibilite-mandats-sans-estampille-839`](decisions/reproductibilite-mandats-sans-estampille-839.md).

## `src/audit_pipeline.py`

3 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Un taux de rattachement se publie avec sa population, et ne bloque jamais, 07/09/2026](decisions/audit-des-rattachements.md) | `_md_section_rattachements` |
| [`audit_pipeline.py` : intégration du rapport gouvernement (#321, sous-issue 5/6 de #316) (2026-08-15)](decisions/audit-pipeline-gouvernement.md) | `compute_vue_ensemble` |
| [Épic #316 — tableaux croisés des plages temporelles (#317/#318/#320/#321) : bilan et décisions transverses (2026-08-15)](decisions/audit-plages-temporelles.md) | `compute_vue_ensemble` |

Le mentionnent sans le gouverner : [`audit-champs-deplaces-726`](decisions/audit-champs-deplaces-726.md), [`lectures-pipeline-par-projection-635`](decisions/lectures-pipeline-par-projection-635.md).

## `src/audit_pivot_dataset.py`

12 décision(s) le gouvernent ; le module en cite 4.

| Décision | Nomme |
| --- | --- |
| [Un audit qui lit un champ déplacé ne se tait pas : il crie 62 000 fois (#726) (2026-09-03)](decisions/audit-champs-deplaces-726.md) | `_erreur_date` |
| [Épic #316 — tableaux croisés des plages temporelles (#317/#318/#320/#321) : bilan et décisions transverses (2026-08-15)](decisions/audit-plages-temporelles.md) | `_plage_dates_champ_simple`, `compute_plage_dates_candidats`, `compute_tableau_croise_candidats` |
| [Rapport d'audit pivot : détail réservé aux candidats déclarés, indicateurs de distribution retirés (2026-08-18)](decisions/audit-rapport-perimetre-candidats.md) | `_est_candidat`, `_stats_volumes` |
| [La chambre est un fait du mandat, pas du profil : `mandats[].chambre` estampillée à la collecte (#492) (2026-08-20)](decisions/chambre-par-mandat-electif.md) | `compute_agregation_warnings` |
| [`chambres` au niveau profil : une liste dérivée, et `chambre` qui n'en est plus que le premier élément (#493) (2026-08-20)](decisions/chambres-profil-derivees.md) | `MAPPING_CHAMBRE_SOURCES`, `compute_agregation_warnings`, `compute_coherence_chambre_sources` |
| [Les consommateurs de `chambre` migrés vers `chambres`, et le garde-fou qui datera son retrait (#494) (2026-08-20)](decisions/consommateurs-chambres-migres.md) | `MAPPING_CHAMBRE_SOURCES`, `compute_coherence_chambre_sources`, `compute_plage_dates_candidats`, `compute_repartition_chambre`, `compute_tableau_croise_candidats` |
| [La corroboration porte sur les chambres publiées, pas sur la complétude des mandats — et la condition de retrait de `chambre` devient atteignable (#486) (2026-08-30)](decisions/corroboration-chambres-publiees-486.md) | `MAPPING_CHAMBRE_SOURCES` |
| [Un paramètre commandait ce qu'il ne nommait pas (#578) (2026-08-29)](decisions/deux-axes-formulaire-578.md) | `compute_profils_perimes` |
| [Le passé sénatorial est un fait de carrière, pas une donnée d'activité : bicaméral pour les candidats seulement (#488) (2026-08-20)](decisions/deux-chambres-interrogees.md) | `compute_agregation_warnings` |
| [Trois lectures du corpus passent à la projection, et chacune a son plafond dans un test (#635, 2026-08-30)](decisions/lectures-pipeline-par-projection-635.md) | `BLOCS_LUS_AUDIT`, `ListeReduite`, `_cle_groupe`, `_plage_dates_champ_simple`, `_plage_dates_textes_portes`, `compute_plage_dates_candidats`, `compute_taux_remplissage`, `load_pivot_directory`, `reduire_liste` |
| [`--limit` + `--skip-existing` sur `extract-roster-groupes` : sélection progressive + rafraîchissement (2026-08-12)](decisions/limit-skip-existing-roster-groupes.md) | `compute_profils_perimes` |
| [NosDéputés sort du pipeline (#529, lot 5 de l'épic « une seule source AN ») (2026-08-27)](decisions/retrait-nosdeputes-529.md) | `MAPPING_CHAMBRE_SOURCES`, `compute_agregation_warnings` |

Le mentionnent sans le gouverner : [`audit-599-projection-blocs-lus-628`](decisions/audit-599-projection-blocs-lus-628.md), [`audit-pipeline-gouvernement`](decisions/audit-pipeline-gouvernement.md), [`destinataire-avertissements-642`](decisions/destinataire-avertissements-642.md), [`plage-dates-groupes`](decisions/plage-dates-groupes.md), [`populations-profils-portees-par-les-outils-630`](decisions/populations-profils-portees-par-les-outils-630.md), [`quality-gate-gouvernements`](decisions/quality-gate-gouvernements.md), [`retrait-senat-528`](decisions/retrait-senat-528.md).

## `src/audit_rattachements.py`

Le mentionnent sans le gouverner : [`audit-des-rattachements`](decisions/audit-des-rattachements.md).

## `src/audit_residus_source_retiree.py`

Le mentionnent sans le gouverner : [`nettoyage-sediment-839`](decisions/nettoyage-sediment-839.md), [`residus-source-retiree-839`](decisions/residus-source-retiree-839.md).

## `src/audit_sediment.py`

Le mentionnent sans le gouverner : [`audit-sediment-inventaire-839`](decisions/audit-sediment-inventaire-839.md), [`nettoyage-sediment-839`](decisions/nettoyage-sediment-839.md).

## `src/audit_volumetrie_profils.py`

2 décision(s) le gouvernent ; le module en cite 2.

| Décision | Nomme |
| --- | --- |
| [La coupure d'historique a tourné pour la première fois — et `--preparer` n'avait jamais imprimé sa procédure (#567) (2026-08-28)](decisions/bornage-execute-567.md) | `MOTIF_COMMIT_DONNEES` |
| [La fenêtre de 30 ne pose pas le plateau qu'on croit, et la table mesurée ne le dit pas (#551) (2026-08-28)](decisions/fenetre-recalibrage-551.md) | `FENETRE_COMMITS_DONNEES`, `MOTIF_COMMIT_DONNEES` |

Le mentionnent sans le gouverner : [`fenetre-historique-donnees`](decisions/fenetre-historique-donnees.md), [`partition-profils-legislature-580`](decisions/partition-profils-legislature-580.md), [`perimetre-coupure-575`](decisions/perimetre-coupure-575.md), [`point-de-sauvegarde-dans-les-profils-518`](decisions/point-de-sauvegarde-dans-les-profils-518.md), [`populations-profils-portees-par-les-outils-630`](decisions/populations-profils-portees-par-les-outils-630.md), [`profils-json-compact`](decisions/profils-json-compact.md), [`reconstruction-tranches-depuis-archive-691`](decisions/reconstruction-tranches-depuis-archive-691.md), [`volumetrie-arbre-de-travail-nest-pas-depot`](decisions/volumetrie-arbre-de-travail-nest-pas-depot.md).

## `src/avertissements.py`

2 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Le sédiment se compte avant de se juger : sept familles, deux couches, aucun retrait (#839, lot A) (2026-09-12)](decisions/audit-sediment-inventaire-839.md) | `AVERTISSEMENTS_HERITES` |
| [`meta.warnings[]` déclare son destinataire, dans un jumeau typé et aligné (#642) (2026-08-31)](decisions/destinataire-avertissements-642.md) | `AVERTISSEMENTS_HERITES`, `Avertissement`, `DESTINATAIRES_AVERTISSEMENT`, `PREFIXES_HERITES`, `avertissement`, `deriver_avertissements` |

Le mentionnent sans le gouverner : [`amendements-zero-pas-de-hard-fail`](decisions/amendements-zero-pas-de-hard-fail.md), [`bloc-lisible-sans-javascript-969`](decisions/bloc-lisible-sans-javascript-969.md), [`bloc-sans-fond-484`](decisions/bloc-sans-fond-484.md), [`constats-parltrack-perimes-683`](decisions/constats-parltrack-perimes-683.md), [`controle-perte-nomme-les-echanges-823`](decisions/controle-perte-nomme-les-echanges-823.md), [`couverture-dossiers-hors-couverture-vs-zero`](decisions/couverture-dossiers-hors-couverture-vs-zero.md), [`fiche-de-lignee-ui-329`](decisions/fiche-de-lignee-ui-329.md), [`liste-candidats-declares-753`](decisions/liste-candidats-declares-753.md), [`mentions-legales-sans-regards-citoyens`](decisions/mentions-legales-sans-regards-citoyens.md), [`profil-de-groupe-lecture-329`](decisions/profil-de-groupe-lecture-329.md), [`residus-source-retiree-839`](decisions/residus-source-retiree-839.md), [`retrait-senat-528`](decisions/retrait-senat-528.md), [`union-warnings-extinction-600`](decisions/union-warnings-extinction-600.md), [`verification-bout-en-bout-legislatures-figees`](decisions/verification-bout-en-bout-legislatures-figees.md).

## `src/budget_collecte.py`

3 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Une source injoignable ne consomme plus le timeout d'un job, et son silence cesse de se lire comme un constat (#514) (2026-08-21)](decisions/budget-collecte-source-injoignable-514.md) | `BudgetCollecte` |
| [`extract-senat` ne collecte plus d'interventions : la collecte n'en retenait aucune, par construction (#501) (2026-08-20)](decisions/interventions-senat-501.md) | `BudgetCollecte` |
| [Un seul roster par run, une reprise sur ce qui est retentable, et des échecs qu'on peut lire (#518) (2026-08-24)](decisions/roster-unique-par-run-518.md) | `annoncer_troncature` |

Le mentionnent sans le gouverner : [`budget-collecte-interventions`](decisions/budget-collecte-interventions.md).

## `src/build_amendements_index.py`

2 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Job CI dédié `extract-amendements-an` : construction inconditionnelle des 3 index de législature (#251) (2026-08-13)](decisions/amendements-index-job-dedie-ci.md) | `build_all_amendements_index` |
| [La reprise d'une archive figée se borne en temps, et le message ne dit plus « indisponible » (#1100) (2026-09-22)](decisions/reprise-archive-figee-bornee-en-temps-1100.md) | `JOB_TIMEOUT_MINUTES`, `budget_telechargement_secondes` |

Le mentionnent sans le gouverner : [`amendements-index-cache-only-consumers`](decisions/amendements-index-cache-only-consumers.md), [`cache-amendements-existence-nest-pas-conformite`](decisions/cache-amendements-existence-nest-pas-conformite.md), [`deux-versions-archive-amendements-1050`](decisions/deux-versions-archive-amendements-1050.md), [`fraicheur-index-amendements-749`](decisions/fraicheur-index-amendements-749.md), [`index-amendements-sharde-par-acteur`](decisions/index-amendements-sharde-par-acteur.md), [`oom-lecture-amendements-par-candidat`](decisions/oom-lecture-amendements-par-candidat.md), [`oom-reconstruction-amendements-figees`](decisions/oom-reconstruction-amendements-figees.md), [`pythonunbuffered-generate-data`](decisions/pythonunbuffered-generate-data.md).

## `src/build_amendements_index_figees.py`

Le mentionnent sans le gouverner : [`amendements-cle-uid`](decisions/amendements-cle-uid.md), [`amendements-legislatures-figees`](decisions/amendements-legislatures-figees.md), [`defaut-collecte-vs-panne-562`](decisions/defaut-collecte-vs-panne-562.md), [`deux-versions-archive-amendements-1050`](decisions/deux-versions-archive-amendements-1050.md), [`telechargement-an-prefixe-valide-443`](decisions/telechargement-an-prefixe-valide-443.md).

## `src/build_amendements_index_pivot.py`

1 décision(s) le gouvernent ; le module en cite 1.

| Décision | Nomme |
| --- | --- |
| [L'artifact des amendements passe avant la génération pivot, et son absence se dit (#1101) (2026-09-22)](decisions/artifact-amendements-avant-la-passe-pivot-1101.md) | `publier_contenus` |

Le mentionnent sans le gouverner : [`dossier-des-amendements-639`](decisions/dossier-des-amendements-639.md), [`fenetre-historique-donnees`](decisions/fenetre-historique-donnees.md), [`integrite-referentielle-pivot`](decisions/integrite-referentielle-pivot.md), [`reconstruction-tranches-depuis-archive-691`](decisions/reconstruction-tranches-depuis-archive-691.md), [`report-texte-vise-source-696`](decisions/report-texte-vise-source-696.md).

## `src/build_commissions_dossiers.py`

Le mentionnent sans le gouverner : [`index-reecrits-seulement-si-le-contenu-change-1075`](decisions/index-reecrits-seulement-si-le-contenu-change-1075.md), [`mise-en-oeuvre-des-grands-chiffres-328`](decisions/mise-en-oeuvre-des-grands-chiffres-328.md), [`vivier-de-points-et-empreinte-de-commission-328`](decisions/vivier-de-points-et-empreinte-de-commission-328.md).

## `src/build_correspondance_acteurs_an.py`

7 décision(s) le gouvernent ; le module en cite 4.

| Décision | Nomme |
| --- | --- |
| [Une entrée dérivée gèle un slug fabriqué, elle ne prouve plus rien (#715) (2026-09-02)](decisions/entree-derivee-correspondance-715.md) | `_slugs_publies` |
| [Un garde-fou posé sur `builtins.open` ne voit pas `pathlib` (#791) (2026-09-10)](decisions/lectures-du-depot-dans-les-tests-791.md) | `resolutions_candidats` |
| [La liste des candidats se collecte, et un déclaré entre sans slug (#753)](decisions/liste-candidats-declares-753.md) | `slugs_fabriques` |
| [La seconde déclaration lisait un champ que le corpus ne porte pas (#788)](decisions/nom-des-resolutions-vient-de-lappelant-788.md) | `resolutions_candidats` |
| [Les membres de gouvernement deviennent une population, et leur collecte part (#996, lot 3) (2026-09-18)](decisions/provenance-roster-gouvernement-996.md) | `entrees_derivees` |
| [Les membres d'un gouvernement reçoivent un identifiant de profil (#996, lot 2) (2026-09-17)](decisions/roster-gouvernements-amo30-996.md) | `slugs_fabriques` |
| [Un membre de roster sans correspondance relue reçoit un slug, et la collision reste un refus (#708) (2026-09-02)](decisions/slug-fabrique-membre-de-roster-708.md) | `_slugs_publies` |

Le mentionnent sans le gouverner : [`bascule-roster-an-amo30-527`](decisions/bascule-roster-an-amo30-527.md), [`correspondance-acteurs-an-525`](decisions/correspondance-acteurs-an-525.md), [`fiches-groupe-17e-legislature-700`](decisions/fiches-groupe-17e-legislature-700.md).

## `src/build_scrutins_dossiers.py`

Le mentionnent sans le gouverner : [`index-reecrits-seulement-si-le-contenu-change-1075`](decisions/index-reecrits-seulement-si-le-contenu-change-1075.md), [`rattachement-scrutin-dossier-758`](decisions/rattachement-scrutin-dossier-758.md).

## `src/build_scrutins_index.py`

Le mentionnent sans le gouverner : [`fenetre-historique-donnees`](decisions/fenetre-historique-donnees.md), [`integrite-referentielle-pivot`](decisions/integrite-referentielle-pivot.md), [`qualification-perdue-a-la-fusion-639`](decisions/qualification-perdue-a-la-fusion-639.md), [`rattachement-au-dossier-interventions-et-scrutins-639`](decisions/rattachement-au-dossier-interventions-et-scrutins-639.md).

## `src/build_scrutins_index_figes.py`

Le mentionnent sans le gouverner : [`qualification-scrutins-et-cle-dossier-639`](decisions/qualification-scrutins-et-cle-dossier-639.md), [`votes-multi-legislature`](decisions/votes-multi-legislature.md).

## `src/cache_an_empreinte.py`

Le mentionnent sans le gouverner : [`cache-completude-interventions-550`](decisions/cache-completude-interventions-550.md).

## `src/cache_an_fraicheur.py`

Le mentionnent sans le gouverner : [`cache-fraicheur-interventions-555`](decisions/cache-fraicheur-interventions-555.md).

## `src/candidate_profile.py`

94 décision(s) le gouvernent ; le module en cite 14.

| Décision | Nomme |
| --- | --- |
| [Trois absences publiées comme des faits (#556, #558, #560) (2026-08-29)](decisions/absences-publiees-comme-faits-556-558-560.md) | `AN_SCRUTINS_LEGISLATURES`, `NOM_INDEX_IDENTITE`, `NOM_INDEX_ORGANES`, `WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE`, `WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES`, `WARNING_PREFIX_VOTES_INTROUVABLES`, `_TYPE_ORGANE_NON_MAPPES`, `_champ_identite_an`, `_format_lieu_naissance`, `_format_nom_complet`, `_texte_an` |
| [Un membre de roster est collecté sous l'acteur que son roster nomme, jamais re-deviné par son nom (#850)](decisions/acteur-du-roster-850.md) | `ActeurContreditParLaTable`, `build_profile`, `fetch_identite_officielle_par_slug` |
| [La cascade des textes portés entre dans l'UI, et la section s'aligne sur la maquette (#328), 06/09/2026](decisions/alignement-section-propose-ui-328.md) | `_STADE_RANKS` |
| [Amendements : la clé du store est l'`uid`, jamais le `numero` (préalable à #431) (2026-08-18)](decisions/amendements-cle-uid.md) | `_aggregate_amendements_index`, `_load_frozen_amendement_index`, `_read_cached_amendements_acteur` |
| [Un amendement cosigné n'est pas N amendements : deux grandeurs, deux noms (#643) (2026-08-31)](decisions/amendements-distincts-et-signatures-643.md) | `_periodes_mandats_assemblee` |
| [Marqueur disque inter-jobs pour le cache d'échec amendements par législature (#246) (2026-08-13)](decisions/amendements-failed-legislature-marker-inter-jobs.md) | `AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS`, `AMENDEMENTS_DOWNLOAD_READ_TIMEOUT_SECONDS`, `_amendements_failed_legislatures` |
| [Spike : budget CI pour un job dédié `extract-amendements-an` et granularité de cache (#249) (2026-08-13)](decisions/amendements-index-budget-ci-cache-granularite.md) | `AMENDEMENTS_DOWNLOAD_BACKOFF_SECONDS`, `AMENDEMENTS_DOWNLOAD_CHUNK_BYTES`, `AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS`, `AMENDEMENTS_DOWNLOAD_READ_TIMEOUT_SECONDS`, `_download_amendements_zip` |
| [Bascule d'`extract-an`/`extract-roster-groupes` vers la lecture cache-only des amendements (#252) (2026-08-13)](decisions/amendements-index-cache-only-consumers.md) | `AN_AMENDEMENTS_PATH`, `AmendementsIndexError`, `WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES`, `_download_and_build_amendement_index`, `fetch_amendements_officiels` |
| [Séparer téléchargement/construction et lecture cache-only dans `_build_acteur_amendement_index` (#250) (2026-08-13)](decisions/amendements-index-cache-only-split.md) | `_download_and_build_amendement_index`, `_get_amendements_lock`, `fetch_amendements_officiels` |
| [Job CI dédié `extract-amendements-an` : construction inconditionnelle des 3 index de législature (#251) (2026-08-13)](decisions/amendements-index-job-dedie-ci.md) | `AN_AMENDEMENTS_PATH`, `_download_and_build_amendement_index`, `fetch_amendements_officiels` |
| [Non-régression sur échec de reconstruction d'un index amendements + indicateur de fraîcheur (#253) (2026-08-13)](decisions/amendements-index-non-regression-fraicheur.md) | `AmendementsIndexError`, `_amendements_legislature_failed_this_run`, `_download_and_build_amendement_index`, `_write_amendements_fraicheur` |
| [Quality gate : distinguer un index amendements jamais construit d'un index périmé (#254) (2026-08-13)](decisions/amendements-index-quality-gate-fraicheur.md) | `AN_AMENDEMENTS_PATH` |
| [Index amendements des législatures 15/16 : construction manuelle hors CI, committée (2026-08-13)](decisions/amendements-legislatures-figees.md) | `AMENDEMENTS_DOWNLOAD_CHUNK_BYTES`, `AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS`, `AMENDEMENTS_FIGEES_AMENDEMENTS_FILENAME`, `AMENDEMENTS_FIGEES_INDEX_PAR_ACTEUR_FILENAME`, `AN_AMENDEMENTS_LEGISLATURES_FIGEES`, `AN_AMENDEMENTS_PATH`, `_AMENDEMENT_SORT_MAP`, `_AMENDEMENT_TYPE_AUTEUR_MAP`, `_LEGACY_AMENDEMENT_SORT_EN_SEANCE_MAP`, `_aggregate_amendements_index`, `_derive_amendement_sort`, `_derive_amendement_sort_legacy`, `_download_amendements_zip`, `_download_and_build_amendement_index`, `_expand_aggregated_amendements_index`, `_extract_cosignataire_refs`, `_load_frozen_amendement_index`, `_parse_amendement_entry`, `_parse_amendement_entry_legacy`, `_parse_amendements_zip`, `_probe_amendements_total_size`, `fetch_amendements_officiels` |
| [Téléchargement par plages (Range) + isolation par législature pour les amendements officiels (#241) (2026-08-13)](decisions/amendements-range-download-legislature-isolation.md) | `AMENDEMENTS_DOWNLOAD_CHUNK_BYTES`, `AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS`, `AN_AMENDEMENTS_PATH`, `WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES`, `_amendements_failed_legislatures`, `_download_amendements_zip`, `build_profile`, `fetch_amendements_officiels` |
| [Le retry avec backoff des amendements (#225) transforme un échec instantané en blocage de plusieurs minutes par candidat (#239) (2026-08-13)](decisions/amendements-retry-blocage-legislature.md) | `AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS`, `AMENDEMENTS_DOWNLOAD_READ_TIMEOUT_SECONDS`, `AN_AMENDEMENTS_PATH`, `AmendementsIndexError`, `_amendements_failed_legislatures`, `fetch_amendements_officiels` |
| [Zéro amendement silencieux quand l'acteurRef est introuvable (#265, fix 5) (2026-08-17)](decisions/amendements-zero-silencieux-acteur-ref.md) | `WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES`, `build_profile`, `fetch_amendements_officiels` |
| [`fetch_identity` : identité (bio) des députés basculée sur l'AN comme source primaire, mandats/groupe restent sur NosDéputés (#355) (2026-08-16)](decisions/bascule-identite-an-primaire.md) | `_acteur_ref_to_pseudo_url`, `_build_acteur_nom_index`, `_build_organe_index`, `build_profile`, `fetch_identite_officielle`, `fetch_identite_officielle_par_slug` |
| [La bascule : le roster des groupes AN vient d'AMO30 (#527, lot 1b de l'épic « une seule source AN ») (2026-08-26)](decisions/bascule-roster-an-amo30-527.md) | `_ensure_acteurs_historique_zip_downloaded` |
| [Un bloc structuré sans fond n'écrase plus un bloc collecté (#484) (2026-08-30)](decisions/bloc-sans-fond-484.md) | `WARNING_AUCUN_MANDAT_FR` |
| [La liste des candidats pilote le périmètre du run, elle ne le documente plus (#757)](decisions/boucle-perimetre-candidats-757.md) | `_resolve_acteur_ref_par_slug` |
| [Une source injoignable ne consomme plus le timeout d'un job, et son silence cesse de se lire comme un constat (#514) (2026-08-21)](decisions/budget-collecte-source-injoignable-514.md) | `_mark_amendements_legislature_failed` |
| [Budget d'exécution à pleine échelle : 630 min annoncées, 55 mesurées (#467) (2026-08-20)](decisions/budget-execution-pleine-echelle-467.md) | `ACTEURS_HISTORIQUE_CACHE_DIR`, `_extract_mandats_officiels`, `_get_amendements_lock`, `fetch_amendements_officiels`, `fetch_organe` |
| [Budget CI de `extract-roster-groupes` : mesure réelle (#376) (2026-08-17)](decisions/budget-roster-mesure.md) | `fetch_amendements_officiels` |
| [L'existence d'un cache n'est pas la preuve de son contenu — et #447 n'avait pas de seconde cause (2026-08-19)](decisions/cache-amendements-existence-nest-pas-conformite.md) | `_cache_amendements_au_format_uid`, `_download_and_build_amendement_index`, `_read_cached_amendements_acteur`, `_scrutins_shard_path_acteur`, `_write_cached_amendements_agreges`, `_write_cached_scrutins`, `amendements_index_deja_figee`, `fetch_amendements_officiels` |
| [Cache amendements stocké et lu sous forme dédupliquée (#377) (2026-08-17)](decisions/cache-amendements-forme-dedupliquee.md) | `AMENDEMENTS_CACHE_DIR`, `_aggregate_amendements_index`, `_download_and_build_amendement_index`, `_expand_aggregated_amendements_index`, `_load_frozen_amendement_index`, `_parse_amendements_zip`, `_read_cached_amendements_acteur`, `_write_cached_amendements_agreges`, `amendements_index_deja_figee`, `fetch_amendements_officiels` |
| [La clé de cache AN porte la COMPLÉTUDE, et la sauvegarde devient explicite (#550) (2026-08-28)](decisions/cache-completude-interventions-550.md) | `AMENDEMENTS_FRAICHEUR_FILENAME`, `AN_QUESTIONS_PATH`, `AN_SCRUTINS_LEGISLATURES_FIGEES`, `_build_acteur_questions_index`, `_read_cached_interventions_syceron_acteur` |
| [Six tests lisaient le cache du poste : la CI était verte parce que la machine est vide (#721) (2026-09-03)](decisions/cache-du-poste-hors-des-tests-721.md) | `_build_acteur_interventions_syceron_index`, `_interventions_syceron_acteur`, `_read_cached_interventions_syceron_acteur`, `fetch_interventions_syceron` |
| [Les `restore-keys` du cache AN traversaient les semaines : la fraîcheur ne se met pas dans la clé, elle se lit dans celle qu'on a restaurée (#555) (2026-08-28)](decisions/cache-fraicheur-interventions-555.md) | `AMENDEMENTS_FRAICHEUR_FILENAME`, `AN_AMENDEMENTS_LEGISLATURES_FIGEES`, `AN_SCRUTINS_LEGISLATURES_FIGEES`, `_build_acteur_questions_index`, `_ensure_acteurs_historique_zip_downloaded`, `_read_cached_interventions_syceron_acteur` |
| [La clé de cache AN porte le MODE, et le job roster ne l'écrit plus (#505) (2026-08-20)](decisions/cache-mode-interventions-505.md) | `_build_acteur_interventions_syceron_index`, `_build_acteur_questions_index`, `_parse_syceron_intervention_entry`, `fetch_questions_officielles` |
| [Un mandat dit quel référentiel a établi sa catégorie, et l'absence n'accuse personne (#718) (2026-09-03)](decisions/categorie-source-des-mandats-718.md) | `_TYPE_ORGANE_TO_CATEGORIE` |
| [La chambre est un fait du mandat, pas du profil : `mandats[].chambre` estampillée à la collecte (#492) (2026-08-20)](decisions/chambre-par-mandat-electif.md) | `build_profile` |
| [La civilité et la nomenclature PCS de l'INSEE traversaient le pipeline sans y laisser de trace (#659) (2026-08-31)](decisions/civilite-et-pcs-insee-659.md) | `NOM_INDEX_IDENTITE`, `_build_acteur_identite_index`, `_champ_identite_an`, `_profession_an`, `_socproc_insee_an` |
| [Un cache porte le code qui l'a écrit : le correctif de #997 n'atteignait rien (2026-09-18)](decisions/cle-index-textes-portes-997.md) | `_build_acteur_textes_portes_index`, `_collect_acteur_roles`, `fetch_textes_portes_officiels` |
| [Un index Syceron en cache est un parsage en cache, et l'existence n'y est pas la conformité (#719) (2026-09-02)](decisions/conformite-index-syceron-719.md) | `SYCERON_CHAMP_QUALIFICATION`, `_reduire_au_theme`, `_scrutins_store_qualifie`, `_syceron_index_qualifie`, `_write_syceron_index_par_acteur` |
| [La correspondance slug ↔ acteur AN devient un artefact committé (#525, lot 2 de l'épic « une seule source AN ») (2026-08-26)](decisions/correspondance-acteurs-an-525.md) | `_resolve_acteur_ref_par_slug` |
| [Ce qu'une liste vide veut dire : les quatre états de couverture (#539) (2026-08-28)](decisions/couverture-listes-539.md) | `AN_AMENDEMENTS_PATH`, `AN_SCRUTINS_LEGISLATURES`, `WARNING_PREFIX_VOTES_INTROUVABLES`, `_resolve_acteur_ref_par_slug` |
| [Une question au gouvernement est datée par la parution de son compte rendu au JO (#1044) (2026-09-22)](decisions/date-des-questions-au-gouvernement-1044.md) | `_parse_question_entry` |
| [`debut_dans_groupe` se lit sur le mandat de groupe, plus sur le premier mandat électif (#653) (2026-08-31)](decisions/dates-appartenance-groupe-653.md) | `fetch_positions_hemicycle_officielles` |
| [882 interventions portaient une date que tout filtre écartait en silence (#1044) (2026-09-20)](decisions/dates-des-questions-en-iso-1044.md) | `normaliser_date_jo` |
| [`membres[]` publiait deux fois le même fait : dédupliquer sans effacer les changements de portefeuille (#480) (2026-08-20)](decisions/deduplication-entrees-membres.md) | `_build_acteur_positions_hemicycle_index` |
| [Une exception n'est pas une preuve, et un défaut de notre code n'est pas une panne de l'Assemblée nationale (#562) (2026-08-28)](decisions/defaut-collecte-vs-panne-562.md) | `AmendementsIndexError`, `ERREURS_SOURCE`, `WARNING_PREFIX_DEFAUT_COLLECTE`, `WARNING_PREFIX_VOTES_INTROUVABLES`, `_parse_amendement_entry`, `_texte_an`, `_tracer_echec_collecte`, `build_profile`, `fetch_amendements_officiels` |
| [`meta.warnings[]` déclare son destinataire, dans un jumeau typé et aligné (#642) (2026-08-31)](decisions/destinataire-avertissements-642.md) | `WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES`, `WARNING_PREFIX_VOTES_INTROUVABLES` |
| [Amendements AN : une seule connexion, une seule version (#1050) (2026-09-21)](decisions/deux-versions-archive-amendements-1050.md) | `AMENDEMENTS_DOWNLOAD_MAX_REDEMARRAGES_VERSION`, `SourceAmendementsIncoherenteError`, `_download_amendements_zip`, `_download_and_build_amendement_index`, `_parse_amendements_zip`, `_telecharger_flux`, `_tenter_segments_range` |
| [Un amendement retrouve son dossier, et la clé qu'on lui avait retirée (#639, rang 3)](decisions/dossier-des-amendements-639.md) | `fetch_amendements_officiels` |
| [Les dossiers du roster passent sous une case, le motif qui les écartait est tombé (#817)](decisions/dossiers-legislatifs-sous-le-formulaire-817.md) | `_build_acteur_textes_portes_index`, `_collect_initiateurs` |
| [Un texte renvoyé en commission n'est pas un texte examiné (#997) (2026-09-18)](decisions/examen-en-commission-997.md) | `_stade_from_code_acte` |
| [La parole des membres de groupe et de gouvernement publie un extrait de 280 caractères (#1029) (2026-09-22)](decisions/extrait-de-la-parole-des-rosters-1029.md) | `_reduire_a_l_extrait` |
| [Un filtre de publication posé avant la fusion ne filtre rien (#641, réouverture) (2026-08-31)](decisions/filtre-publication-apres-fusion-641.md) | `_profession_an` |
| [L'archive vivante se reprend au changement de semaine, les mortes jamais (#762), 07/09/2026](decisions/fraicheur-dossiers-762.md) | `AN_SCRUTINS_LEGISLATURES_FIGEES` |
| [La rotation de clé hebdomadaire était toute la politique de fraîcheur, et son propre repli la désamorçait (#749)](decisions/fraicheur-index-amendements-749.md) | `_download_and_build_amendement_index`, `amendements_index_en_cache_utilisable` |
| [`gouvernement_profile` : `premier_ministre` et `portefeuille` câblés depuis les mandats `MINISTERE` (#398) (2026-08-18)](decisions/gouvernement-premier-ministre-portefeuille.md) | `AN_ACTEURS_HISTORIQUE_ZIP_URL`, `_extract_mandats_officiels` |
| [`gouvernement_textes.py` : filtre de statut par décision de séance, pas par `codeActe`/`fam_code` seul (#210) (2026-08-14)](decisions/gouvernement-textes-statut.md) | `_build_acteur_textes_portes_index` |
| [`gouvernement_textes.py` : filtre de statut par décision de séance, pas par `codeActe`/`fam_code` seul (#210) (2026-08-14)](decisions/gouvernement-textes-statut-210-version-initiale.md) | `_build_acteur_textes_portes_index` |
| [`_build_acteur_identite_index` : couvrir les élu⋅e⋅s dont le mandat est terminé via `AMO30`, pas en combinant `AMO20` par législature (#354) (2026-08-16)](decisions/identite-acteurs-amo30.md) | `AN_ACTEURS_HISTORIQUE_ZIP_URL`, `_build_acteur_identite_index`, `_build_acteur_positions_hemicycle_index`, `_build_organe_index`, `_ensure_acteurs_historique_zip_downloaded`, `_select_mandat_assemblee_courant`, `build_profile` |
| [Index amendements shardé par acteur (#392) (2026-08-17)](decisions/index-amendements-sharde-par-acteur.md) | `_download_and_build_amendement_index`, `_expand_aggregated_amendements_index`, `fetch_amendements_officiels` |
| [`extract-senat` ne collecte plus d'interventions : la collecte n'en retenait aucune, par construction (#501) (2026-08-20)](decisions/interventions-senat-501.md) | `build_profile`, `fetch_questions_officielles` |
| [Un garde-fou posé sur `builtins.open` ne voit pas `pathlib` (#791) (2026-09-10)](decisions/lectures-du-depot-dans-les-tests-791.md) | `AMENDEMENTS_CACHE_DIR` |
| [Le libellé d'organe du chef du gouvernement s'accorde en genre, la qualité jamais (#658) (2026-08-31)](decisions/libelle-chef-du-gouvernement-au-feminin-658.md) | `_build_acteur_mandats_index` |
| [Chaque prise de parole porte l'ancre de sa page de séance à l'AN (#1087) (2026-09-22)](decisions/lien-vers-la-prise-de-parole-1087.md) | `_syceron_index_qualifie` |
| [Un profil publie tous ses mandats de député, et le compteur devient un témoin de couverture (#640) (2026-08-31)](decisions/mandats-electifs-liste-complete-640.md) | `_select_mandat_assemblee_courant`, `_select_mandat_par_type_courant` |
| [Le référentiel type l'organe, il n'y a rien à interpréter (#730) (2026-09-04)](decisions/mandats-gouvernementaux-en-commission-730.md) | `_TYPE_ORGANE_TO_CATEGORIE` |
| [Mandats commission/groupe_amitie/extra_parlementaire sourcés depuis l'AN, fetch_identity NosDéputés rendu conditionnel (#369, complet), watchdog générique sur tous les téléchargements zip (#370, complet) (2026-08-17)](decisions/mandats-officiels-an-369.md) | `_TYPE_ORGANE_TO_CATEGORIE`, `_build_acteur_identite_index`, `_build_acteur_mandats_index`, `_build_organe_index`, `_ensure_acteurs_historique_zip_downloaded`, `_extract_mandats_officiels`, `build_profile`, `fetch_identite_officielle_par_slug`, `fetch_organe`, `fetch_votes_officiels` |
| [Mode d'extraction léger pour `extract-roster-groupes` (#357, sous-issue 6/6 de #351) (2026-08-16)](decisions/mode-extraction-leger-roster.md) | `build_profile`, `fetch_textes_portes_officiels` |
| [Suppression de l'archive brute `amendements.zip` après construction de l'index (#264) (2026-08-17)](decisions/nettoyage-archive-brute-amendements.md) | `_download_amendements_zip`, `_download_and_build_amendement_index`, `_read_cached_amendements_acteur` |
| [Normaliser les amendements : le coût n'est pas l'amendement, c'est sa liste de cosignataires (#431) (2026-08-19)](decisions/normalisation-amendements.md) | `_expand_aggregated_amendements_index`, `_load_frozen_amendement_index`, `_parse_amendement_entry` |
| [Normalisation de `par_fonction` dans `mandats_agreges`, et requalification du défaut « catégorie commission » (#379) (2026-08-17)](decisions/normalisation-fonction-mandats-agreges.md) | `_TYPE_ORGANE_TO_CATEGORIE` |
| [OOM persistant : lecture per-candidat de l'index amendements, tentative de mémoïsation revertée (2026-08-17)](decisions/oom-lecture-amendements-par-candidat.md) | `AN_AMENDEMENTS_PATH`, `fetch_amendements_officiels` |
| [OOM lors de la relecture d'un index amendements figé déjà en cache (exécution locale) (2026-08-17)](decisions/oom-reconstruction-amendements-figees.md) | `AN_AMENDEMENTS_LEGISLATURES_FIGEES`, `AN_AMENDEMENTS_PATH`, `_download_and_build_amendement_index`, `amendements_index_deja_figee` |
| [`_build_organe_index` : résoudre `organeRef` via `AMO30` (historique) sans filtrage par `codeType` (#353) (2026-08-16)](decisions/organe-index-organeref.md) | `AN_ACTEURS_HISTORIQUE_ZIP_URL`, `_ACTEURS_HISTORIQUE_ZIP_LOCK`, `_build_acteur_positions_hemicycle_index`, `_build_organe_index`, `_build_organe_positions_index`, `_ensure_acteurs_historique_zip_downloaded`, `fetch_positions_hemicycle_officielles` |
| [Parallèle RAM entre l'exécution locale et les runners GitHub Actions hébergés, diagnostic ajouté (2026-08-17)](decisions/parallele-oom-local-runner-ci.md) | `build_profile`, `fetch_amendements_officiels` |
| [Un code de nomenclature n'est pas une profession, et « sans activité professionnelle » n'en est pas une (#641) (2026-08-31)](decisions/profession-code-nomenclature-641.md) | `_profession_an` |
| [La qualification d'un scrutin et la clé de son dossier étaient lues puis jetées (#639, rangs 1 et 2)](decisions/qualification-scrutins-et-cle-dossier-639.md) | `_load_frozen_scrutins_index`, `_parse_scrutins_zip`, `_scrutins_store_qualifie` |
| [Un projet de loi porté au nom du Gouvernement n'est pas une production personnelle (#689) (2026-09-01)](decisions/qualification-textes-portes-689.md) | `_build_acteur_textes_portes_index` |
| [Une question au gouvernement : un acte, et ses tours de parole reliés à lui (#1094) (2026-09-22)](decisions/question-au-gouvernement-acte-et-parole-1094.md) | `FORMAT_INDEX_QUESTIONS`, `_parse_question_entry` |
| [Rattacher une intervention ou un scrutin à son dossier : les deux volets restants sont écartés, mesure à l'appui (#639) (2026-09-01)](decisions/rattachement-au-dossier-interventions-et-scrutins-639.md) | `_parse_scrutins_zip`, `_reduire_au_theme` |
| [Le `texte_vise` fautif se reprend depuis l'archive figée, pas par une fusion plus permissive (#696, 01/09/2026)](decisions/report-texte-vise-source-696.md) | `fetch_amendements_officiels` |
| [La reprise d'une archive figée se borne en temps, et le message ne dit plus « indisponible » (#1100) (2026-09-22)](decisions/reprise-archive-figee-bornee-en-temps-1100.md) | `AMENDEMENTS_SOURCE_STALL_MAX_CYCLES`, `_download_amendements_zip` |
| [Résilience de `generate-data.yml` face aux `shutdown signal` runner : continue-on-error généralisé, watchdog réseau, retry générique sur `_get_payload`, retry `retry-generate-data.yml` non-régressif, et appels NosDéputés morts pour les députés (dossiers, votes) (2026-08-16)](decisions/resilience-generate-data-shutdown-signal.md) | `WARNING_PREFIX_VOTES_INTROUVABLES`, `build_profile`, `fetch_textes_portes_officiels`, `fetch_votes_officiels` |
| [Bug de résolution AN pour les prénoms composés, et gel runner déplacé sur l'étape 0 (run #47) (2026-08-17)](decisions/resolution-an-prenom-compose-et-gel-runner-etape0.md) | `_build_acteur_nom_index`, `_ensure_acteurs_historique_zip_downloaded`, `_normalize_search_query`, `fetch_identite_officielle_par_slug` |
| [Retrait de `fetch_activity_synthesis` (#356) (2026-08-16)](decisions/retrait-fetch-activity-synthesis.md) | `build_profile` |
| [NosDéputés sort du pipeline (#529, lot 5 de l'épic « une seule source AN ») (2026-08-27)](decisions/retrait-nosdeputes-529.md) | `CHAMBRES_COLLECTEES`, `WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES`, `_build_acteur_nom_index`, `_ensure_acteurs_historique_zip_downloaded`, `_normalize_search_query`, `_resolve_acteur_ref_par_slug`, `build_profile`, `fetch_textes_portes_officiels` |
| [Le Sénat sort du périmètre, et le job qui concluait vert sans rien produire est retiré (#528, lot 3 de l'épic « une seule source AN ») (2026-08-26)](decisions/retrait-senat-528.md) | `build_profile` |
| [Le roster des groupes AN est dérivé d'AMO30, derrière un drapeau baissé (#526, lot 1 de l'épic « une seule source AN ») (2026-08-26)](decisions/roster-an-derive-amo30-526.md) | `_ensure_acteurs_historique_zip_downloaded` |
| [Scission du cache CI `.cache` par sous-répertoire : écartée (#374, fermée non planifiée) (2026-08-17)](decisions/scission-cache-ci-ecartee.md) | `build_profile`, `fetch_amendements_officiels` |
| [La suite dit son monde au lieu d'en hériter (#767)](decisions/suite-independante-du-cache-local-767.md) | `ACTEURS_HISTORIQUE_CACHE_DIR`, `_ACTEURS_HISTORIQUE_INDEX_MEMO` |
| [Syceron : remplacement du scraping NosDéputés pour les débats en séance (2026-08-07)](decisions/syceron.md) | `_build_acteur_interventions_syceron_index`, `fetch_interventions_syceron` |
| [Syceron publie l'identifiant d'orateur NU, et n'a donc jamais rien indexé (#510) (2026-08-20)](decisions/syceron-acteur-ref-nu-510.md) | `_build_acteur_interventions_syceron_index`, `_normaliser_orateur_id_syceron`, `_parse_syceron_intervention_entry`, `_shard_path_acteur` |
| [Syceron activé, repli NosDéputés retiré, index tranché par acteur (#510) (2026-08-27)](decisions/syceron-actif-510.md) | `RefusDrapeauInterventionsSyceron`, `_normaliser_orateur_id_syceron`, `_parse_syceron_intervention_entry`, `_read_cached_interventions_syceron_acteur` |
| [Suite du 26/08/2026 : les trois archives vérifiées, les deux défauts de parseur corrigés](decisions/syceron-archives-verifiees-parseur-510.md) | `_scrutins_shard_path_acteur` |
| [`synchro_sources` publie la dernière récupération réussie, et pas son origine (#600) (2026-08-30)](decisions/synchro-sources-derniere-recuperation-600.md) | `_telecharger_flux`, `fetch_interventions_syceron`, `fetch_questions_officielles` |
| [Taxonomie des mandats : exploitation des `typeOrgane` AN non mappés (#382, option « mixte ») (2026-08-17)](decisions/taxonomie-mandats-typeorgane-an.md) | `_TYPE_ORGANE_NON_MAPPES`, `fetch_positions_hemicycle_officielles` |
| [Téléchargement AN : trois modes de défaillance, un seul principe — ne jamais jeter un préfixe valide (#443) (2026-08-19)](decisions/telechargement-an-prefixe-valide-443.md) | `AMENDEMENTS_DOWNLOAD_CHUNK_BYTES`, `AMENDEMENTS_SOURCE_STALL_MAX_CYCLES`, `AMENDEMENTS_SOURCE_STALL_WAIT_SECONDS`, `SourceAmendementsIndisponibleError`, `_download_amendements_zip`, `_est_erreur_http_definitive`, `_telecharger_flux`, `_tenter_get_sequentiel` |
| [L'union des avertissements peut ressusciter un démenti, et deux familles Syceron s'éteignent (#600) (2026-08-30)](decisions/union-warnings-extinction-600.md) | `WARNING_PREFIX_QUESTIONS_INDISPONIBLES` |
| [Votes : agrégation des législatures 14 à 17, index dédupliqué, 14/15/16 figées (#403) (2026-08-18)](decisions/votes-multi-legislature.md) | `AN_SCRUTINS_LEGISLATURES`, `AN_SCRUTINS_LEGISLATURES_FIGEES`, `AN_SCRUTIN_UID_PREFIXE`, `fetch_votes_officiels` |

Le mentionnent sans le gouverner : [`archive-dossiers-xiv-1019`](decisions/archive-dossiers-xiv-1019.md), [`consommateurs-chambres-migres`](decisions/consommateurs-chambres-migres.md), [`dossiers-multi-archives-origine-document`](decisions/dossiers-multi-archives-origine-document.md), [`gouvernement-roster-desambiguisation`](decisions/gouvernement-roster-desambiguisation.md), [`licences`](decisions/licences.md), [`mandats-agreges-famille-1`](decisions/mandats-agreges-famille-1.md), [`parlementaire-en-mission-nest-pas-ministre`](decisions/parlementaire-en-mission-nest-pas-ministre.md), [`partition-profils-legislature-580`](decisions/partition-profils-legislature-580.md), [`perimetre-controle-perte`](decisions/perimetre-controle-perte.md), [`plafond-roster-et-commit-518`](decisions/plafond-roster-et-commit-518.md), [`pythonunbuffered-generate-data`](decisions/pythonunbuffered-generate-data.md), [`qualification-perdue-a-la-fusion-639`](decisions/qualification-perdue-a-la-fusion-639.md), [`rattachement-des-membres-par-organe-996`](decisions/rattachement-des-membres-par-organe-996.md), [`retrait-marqueur-regards-citoyens-deputes-890`](decisions/retrait-marqueur-regards-citoyens-deputes-890.md), [`roster-unique-par-run-518`](decisions/roster-unique-par-run-518.md), [`trame-profil-candidat-328`](decisions/trame-profil-candidat-328.md).

## `src/candidate_profile_ue.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Données UE — investigation des sources (2026-08-04)](decisions/investigation-sources-ue.md) | `find_mep_by_name` |

Le mentionnent sans le gouverner : [`licence-parlement-europeen-cc-by-983`](decisions/licence-parlement-europeen-cc-by-983.md), [`reduction-nommee-collecte-vs-publie-888`](decisions/reduction-nommee-collecte-vs-publie-888.md).

## `src/check_quality_gate.py`

9 décision(s) le gouvernent ; le module en cite 9.

| Décision | Nomme |
| --- | --- |
| [Quality gate : distinguer un index amendements jamais construit d'un index périmé (#254) (2026-08-13)](decisions/amendements-index-quality-gate-fraicheur.md) | `_AMENDEMENTS_INDISPONIBLES_PREFIX`, `_AMENDEMENTS_LEGISLATURES`, `_report_amendements_freshness` |
| [Index amendements des législatures 15/16 : construction manuelle hors CI, committée (2026-08-13)](decisions/amendements-legislatures-figees.md) | `_AMENDEMENTS_LEGISLATURES`, `_AMENDEMENTS_LEGISLATURES_FIGEES` |
| [Quality gate : « 0 amendement collecté » reste non bloquant, mais cesse d'être discret (#378) (2026-08-18)](decisions/amendements-zero-pas-de-hard-fail.md) | `_report_amendements_coverage` |
| [Les consommateurs de `chambre` migrés vers `chambres`, et le garde-fou qui datera son retrait (#494) (2026-08-20)](decisions/consommateurs-chambres-migres.md) | `_report_amendements_coverage`, `_report_groupes`, `_report_low_interventions`, `_report_low_syceron_coverage` |
| [Suspendre l'extraction des deux groupes Sénat, sans les retirer de la config (#516) (2026-08-24)](decisions/extraction-groupe-suspendue-516.md) | `_report_groupes` |
| [La liste des gouvernements se lit dans AMO30, elle ne s'écrit plus à la main (#996) (2026-09-17)](decisions/liste-gouvernements-amo30-996.md) | `_report_gouvernements` |
| [`check_quality_gate.py` : section gouvernements (§5), couverture ministérielle proxy par `portefeuille` (#212) (2026-08-14)](decisions/quality-gate-gouvernements.md) | `_GROUPE_NETWORK_SIGNALS`, `_report_gouvernements`, `_report_groupes` |
| [Un seul roster par run, une reprise sur ce qui est retentable, et des échecs qu'on peut lire (#518) (2026-08-24)](decisions/roster-unique-par-run-518.md) | `_gha_annotation` |
| [Seuil de couverture de groupe (`--groupe-min-members`) : conservé faute de chiffres réels à pleine échelle (2026-08-12)](decisions/seuil-couverture-groupe.md) | `_report_groupes` |

Le mentionnent sans le gouverner : [`absences-publiees-comme-faits-556-558-560`](decisions/absences-publiees-comme-faits-556-558-560.md), [`audit-599-projection-blocs-lus-628`](decisions/audit-599-projection-blocs-lus-628.md), [`audit-plages-temporelles`](decisions/audit-plages-temporelles.md), [`chambres-profil-derivees`](decisions/chambres-profil-derivees.md), [`corroboration-chambres-publiees-486`](decisions/corroboration-chambres-publiees-486.md), [`couverture-dossiers-hors-couverture-vs-zero`](decisions/couverture-dossiers-hors-couverture-vs-zero.md), [`deux-chambres-interrogees`](decisions/deux-chambres-interrogees.md), [`fiches-groupe-17e-legislature-700`](decisions/fiches-groupe-17e-legislature-700.md), [`gouvernement-doc-cloture`](decisions/gouvernement-doc-cloture.md), [`gouvernement-profile-rattachement`](decisions/gouvernement-profile-rattachement.md), [`identifiants-groupes-et-successions-multiples-815`](decisions/identifiants-groupes-et-successions-multiples-815.md), [`mode-extraction-leger-roster`](decisions/mode-extraction-leger-roster.md), [`oom-reconstruction-amendements-figees`](decisions/oom-reconstruction-amendements-figees.md), [`partition-profils-legislature-580`](decisions/partition-profils-legislature-580.md), [`populations-profils-portees-par-les-outils-630`](decisions/populations-profils-portees-par-les-outils-630.md), [`retrait-fiches-parti-906`](decisions/retrait-fiches-parti-906.md), [`retry-generate-data-preemption`](decisions/retry-generate-data-preemption.md), [`slug-fabrique-membre-de-roster-708`](decisions/slug-fabrique-membre-de-roster-708.md), [`test-adosse-au-corpus-vivant`](decisions/test-adosse-au-corpus-vivant.md).

## `src/collecte_mandats_locaux.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [La correspondance slug ↔ acteur AN devient un artefact committé (#525, lot 2 de l'épic « une seule source AN ») (2026-08-26)](decisions/correspondance-acteurs-an-525.md) | `etat_civil` |

## `src/commissions_dossiers_an.py`

Le mentionnent sans le gouverner : [`archive-dossiers-xiv-1019`](decisions/archive-dossiers-xiv-1019.md), [`rattachement-scrutin-dossier-758`](decisions/rattachement-scrutin-dossier-758.md), [`vivier-de-points-et-empreinte-de-commission-328`](decisions/vivier-de-points-et-empreinte-de-commission-328.md).

## `src/correspondance_acteurs_an.py`

4 décision(s) le gouvernent ; le module en cite 2.

| Décision | Nomme |
| --- | --- |
| [La bascule : le roster des groupes AN vient d'AMO30 (#527, lot 1b de l'épic « une seule source AN ») (2026-08-26)](decisions/bascule-roster-an-amo30-527.md) | `CorrespondanceInvalide` |
| [La correspondance slug ↔ acteur AN devient un artefact committé (#525, lot 2 de l'épic « une seule source AN ») (2026-08-26)](decisions/correspondance-acteurs-an-525.md) | `est_declare_hors_an`, `resoudre_acteur_ref` |
| [Une entrée dérivée gèle un slug fabriqué, elle ne prouve plus rien (#715) (2026-09-02)](decisions/entree-derivee-correspondance-715.md) | `ECARTS_CONNUS` |
| [Un garde-fou posé sur `builtins.open` ne voit pas `pathlib` (#791) (2026-09-10)](decisions/lectures-du-depot-dans-les-tests-791.md) | `CHEMIN_PAR_DEFAUT`, `charger_correspondance` |

Le mentionnent sans le gouverner : [`civilite-et-pcs-insee-659`](decisions/civilite-et-pcs-insee-659.md), [`identite-profils-539`](decisions/identite-profils-539.md), [`larem-xv-apres-691-779`](decisions/larem-xv-apres-691-779.md), [`position-politique-groupes-686`](decisions/position-politique-groupes-686.md), [`preuve-de-borne-dite-une-fois-328`](decisions/preuve-de-borne-dite-une-fois-328.md), [`provenance-roster-gouvernement-996`](decisions/provenance-roster-gouvernement-996.md), [`repertoire-config-1057`](decisions/repertoire-config-1057.md), [`roster-an-derive-amo30-526`](decisions/roster-an-derive-amo30-526.md), [`roster-gouvernements-amo30-996`](decisions/roster-gouvernements-amo30-996.md), [`slug-fabrique-membre-de-roster-708`](decisions/slug-fabrique-membre-de-roster-708.md), [`sparse-checkout-extract-an-674`](decisions/sparse-checkout-extract-an-674.md), [`tranches-derivees-lecteur-691`](decisions/tranches-derivees-lecteur-691.md).

## `src/couverture_dossiers.py`

9 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [La XIVe législature n'était pas inexploitable, elle était monolithique (#1019) (2026-09-18)](decisions/archive-dossiers-xiv-1019.md) | `AN_DOSSIERS_LEGISLATURES_FIGEES`, `LEGISLATURES_DEBUT`, `statut_couverture_textes` |
| [Les mandats locaux commencent en 2020, et l'avant se déclare (#922) (2026-09-15)](decisions/borne-mandats-locaux-2020-922.md) | `borne_couverture_textes` |
| [Couverture des dossiers : « hors couverture de la source » ≠ « réellement à zéro » (#399) (2026-08-18)](decisions/couverture-dossiers-hors-couverture-vs-zero.md) | `AN_DOSSIERS_ARCHIVES`, `LEGISLATURES_DEBUT`, `borne_couverture_textes`, `statut_couverture_textes` |
| [Ce qu'une liste vide veut dire : les quatre états de couverture (#539) (2026-08-28)](decisions/couverture-listes-539.md) | `AN_DOSSIERS_ARCHIVES` |
| [Un amendement retrouve son dossier, et la clé qu'on lui avait retirée (#639, rang 3)](decisions/dossier-des-amendements-639.md) | `AN_DOSSIERS_ARCHIVES` |
| [Dossiers législatifs : ingestion multi-archives, origine par document déposé, statut `promulgue` (#400) (2026-08-18)](decisions/dossiers-multi-archives-origine-document.md) | `AN_DOSSIERS_ARCHIVES` |
| [L'archive vivante se reprend au changement de semaine, les mortes jamais (#762), 07/09/2026](decisions/fraicheur-dossiers-762.md) | `AN_DOSSIERS_ARCHIVES`, `AN_DOSSIERS_LEGISLATURES_ACTIVES`, `AN_DOSSIERS_LEGISLATURES_FIGEES` |
| [Profils de gouvernement : ne jamais réécrire sur une collecte incomplète, et cache dossiers dédié (#427) (2026-08-18)](decisions/gouvernement-textes-non-ecrasement.md) | `legislatures_ingerees` |
| [Résoudre la `legislature` d'un vote : deux mécanismes, pas un seul (#432) (2026-08-19)](decisions/resolution-legislature-deux-mecanismes-432.md) | `LEGISLATURES_DEBUT` |

Le mentionnent sans le gouverner : [`absences-publiees-comme-faits-556-558-560`](decisions/absences-publiees-comme-faits-556-558-560.md).

## `src/couverture_profil.py`

9 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [Trois absences publiées comme des faits (#556, #558, #560) (2026-08-29)](decisions/absences-publiees-comme-faits-556-558-560.md) | `DECISIONS_PIPELINE`, `MOTIFS_JAMAIS_PANNE`, `legislatures_du_profil` |
| [La collecte d'interventions des membres de roster est réduite au thème (#657) (2026-08-31)](decisions/collecte-interventions-reduite-au-theme-657.md) | `DECISIONS_ROSTER` |
| [Ce qu'une liste vide veut dire : les quatre états de couverture (#539) (2026-08-28)](decisions/couverture-listes-539.md) | `DECISIONS_PIPELINE`, `MOTIFS_PANNE` |
| [Une exception n'est pas une preuve, et un défaut de notre code n'est pas une panne de l'Assemblée nationale (#562) (2026-08-28)](decisions/defaut-collecte-vs-panne-562.md) | `MOTIFS_PANNE`, `_preuve_defaut_collecte` |
| [`meta.warnings[]` déclare son destinataire, dans un jumeau typé et aligné (#642) (2026-08-31)](decisions/destinataire-avertissements-642.md) | `MOTIFS_DEFAUT_COLLECTE`, `MOTIFS_JAMAIS_PANNE`, `MOTIFS_PANNE` |
| [Corriger là où un champ est jeté ne suffit pas : il faut trouver tous les endroits où l'objet est fabriqué (#901) (2026-09-14)](decisions/deux-fabriques-textes-portes-europeens-901.md) | `GroupeSuspendu` |
| [Les dossiers du roster passent sous une case, le motif qui les écartait est tombé (#817)](decisions/dossiers-legislatifs-sous-le-formulaire-817.md) | `DECISIONS_ROSTER` |
| [Le Parlement européen prend sa place sur `/couverture`, et cesse de déplacer les bornes de l'Assemblée — 11/09/2026 (#328)](decisions/parlement-europeen-sur-la-couverture-328.md) | `bornes_europeennes` |
| [L'européen entre dans les listes que la fiche a déjà (#683, lot 2)](decisions/stockage-europeen-dans-les-listes-existantes-683.md) | `bornes_europeennes` |

Le mentionnent sans le gouverner : [`couverture-remplacee-par-liste-602`](decisions/couverture-remplacee-par-liste-602.md), [`fiches-groupe-17e-legislature-700`](decisions/fiches-groupe-17e-legislature-700.md), [`lecture-dumps-parltrack-683`](decisions/lecture-dumps-parltrack-683.md), [`licence-jamais-en-dur-909`](decisions/licence-jamais-en-dur-909.md), [`pied-de-site-et-section-6-328`](decisions/pied-de-site-et-section-6-328.md), [`preuve-de-borne-dite-une-fois-328`](decisions/preuve-de-borne-dite-une-fois-328.md), [`retrait-residus-senat-908`](decisions/retrait-residus-senat-908.md).

## `src/documents_europeens.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Un délai dépassé chez EuroVoc a coûté toute la publication d'un run (#901) (2026-09-17)](decisions/eurovoc-muet-ne-bloque-pas-le-corpus-901.md) | `LibellesEurovocIndisponibles`, `_interroger_sparql`, `resoudre_domaines` |

Le mentionnent sans le gouverner : [`domaines-eurovoc-familles-oeil-901`](decisions/domaines-eurovoc-familles-oeil-901.md), [`index-reecrits-seulement-si-le-contenu-change-1075`](decisions/index-reecrits-seulement-si-le-contenu-change-1075.md), [`matieres-eurovoc-documents-901`](decisions/matieres-eurovoc-documents-901.md).

## `src/dossiers_europeens.py`

7 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [La couverture EuroVoc est plafonnée, et la limite est datée (#1052) (2026-09-23)](decisions/couverture-eurovoc-limite-datee-1052.md) | `ESSAIS_PAR_DOSSIER` |
| [Un dossier européen reçoit ses domaines EuroVoc de son texte adopté (#901) (2026-09-17)](decisions/domaines-eurovoc-des-dossiers-901.md) | `documents_de_seance` |
| [L'index des dossiers européens lit aussi les dossiers que les votes citent (#901) (2026-09-17)](decisions/dossiers-europeens-votes-901.md) | `references_visees` |
| [L'index européen ne lisait que les amendements, et 34 références ne résolvaient nulle part (#901) (2026-09-16)](decisions/index-europeen-lit-aussi-les-textes-portes-901.md) | `references_visees` |
| [L'index européen relit ce qu'il a publié : le cache n'est pas une mémoire (#1062) (2026-09-21)](decisions/index-europeen-reprend-ses-acquis-1062.md) | `reprendre_acquis` |
| [Les textes adoptés se lisent par liste annuelle, plus un par un (#1069) (2026-09-21)](decisions/textes-adoptes-par-liste-annuelle-1069.md) | `precharger_textes_adoptes` |
| [Les quatre saisines au fond européennes se distinguent, elles ne se fondent pas (#901) (2026-09-14)](decisions/trois-saisines-au-fond-europeennes-901.md) | `KNOWN_STATUTS_COMMISSION_AU_FOND`, `commissions_au_fond_non_resolu` |

Le mentionnent sans le gouverner : [`cascade-europeenne-une-porte-901`](decisions/cascade-europeenne-une-porte-901.md), [`domaines-eurovoc-familles-oeil-901`](decisions/domaines-eurovoc-familles-oeil-901.md), [`filtre-par-intitule-fiche-candidat-979`](decisions/filtre-par-intitule-fiche-candidat-979.md), [`index-dossiers-europeens-901`](decisions/index-dossiers-europeens-901.md), [`index-reecrits-seulement-si-le-contenu-change-1075`](decisions/index-reecrits-seulement-si-le-contenu-change-1075.md), [`matieres-eurovoc-documents-901`](decisions/matieres-eurovoc-documents-901.md), [`portail-europeen-hors-chemin-critique-1064`](decisions/portail-europeen-hors-chemin-critique-1064.md).

## `src/download_watchdog.py`

1 décision(s) le gouvernent ; le module en cite 1.

| Décision | Nomme |
| --- | --- |
| [Mandats commission/groupe_amitie/extra_parlementaire sourcés depuis l'AN, fetch_identity NosDéputés rendu conditionnel (#369, complet), watchdog générique sur tous les téléchargements zip (#370, complet) (2026-08-17)](decisions/mandats-officiels-an-369.md) | `download_with_watchdog` |

Le mentionnent sans le gouverner : [`budget-collecte-interventions`](decisions/budget-collecte-interventions.md).

## `src/europarl_documents.py`

8 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [Un portail muet coûtait 2 h 20 de run pour rien (#901) (2026-09-16)](decisions/disjoncteur-portail-europeen-901.md) | `MAX_ECHECS_CONSECUTIFS`, `PAUSE_ENTRE_REQUETES` |
| [Un dossier européen reçoit ses domaines EuroVoc de son texte adopté (#901) (2026-09-17)](decisions/domaines-eurovoc-des-dossiers-901.md) | `ResolveurDocuments` |
| [L'index européen relit ce qu'il a publié : le cache n'est pas une mémoire (#1062) (2026-09-21)](decisions/index-europeen-reprend-ses-acquis-1062.md) | `ResolveurDocuments` |
| [628 textes européens sans dossier, et le portail les classait déjà (#901) (2026-09-16)](decisions/matieres-eurovoc-documents-901.md) | `DOCEO_BASE`, `ResolveurDocuments` |
| [Les textes adoptés se lisent par liste annuelle, plus un par un (#1069) (2026-09-21)](decisions/textes-adoptes-par-liste-annuelle-1069.md) | `ResolveurDocuments` |
| [Le titre français cherchait sa référence là où elle n'est jamais (#901) (2026-09-16)](decisions/titre-francais-lu-dans-source-url-901.md) | `reference_doceo` |
| [Le titre français était téléchargé puis jeté (#901) (2026-09-16)](decisions/titre-francais-textes-europeens-901.md) | `ResolveurDocuments` |
| [L'adresse est dérivée, l'existence est prouvée (#827)](decisions/urls-explications-vote-europeennes-827.md) | `ResolveurDocuments` |

Le mentionnent sans le gouverner : [`licence-parlement-europeen-cc-by-983`](decisions/licence-parlement-europeen-cc-by-983.md).

## `src/fetch_candidats_declares.py`

2 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Les mandats antérieurs à la couverture de l'Assemblée entrent par une table relue (#860)](decisions/mandats-anterieurs-couverture-860.md) | `RAPPEL_MANDATS_ANTERIEURS`, `nouvelle_entree` |
| [Le script pose `decline` quand la source nomme la cause (#763)](decisions/sortie-nommee-par-la-source-763.md) | `note_de_sortie` |

Le mentionnent sans le gouverner : [`lectures-du-depot-dans-les-tests-791`](decisions/lectures-du-depot-dans-les-tests-791.md), [`liste-candidats-declares-753`](decisions/liste-candidats-declares-753.md).

## `src/garde_fou_blobs.py`

2 décision(s) le gouvernent ; le module en cite 1.

| Décision | Nomme |
| --- | --- |
| [Le seuil de blob sort du critère de sortie, et les profils bruts se partitionnent par législature (#580) (2026-08-29)](decisions/partition-profils-legislature-580.md) | `CONDUITE_A_TENIR` |
| [Les fiches de parti sortent : 25 sur 29 n'agrégeaient qu'un candidat, et personne ne les lisait (#906) (2026-09-13)](decisions/retrait-fiches-parti-906.md) | `REPERTOIRES_SURVEILLES` |

Le mentionnent sans le gouverner : [`collecte-interventions-reduite-au-theme-657`](decisions/collecte-interventions-reduite-au-theme-657.md), [`dossier-des-amendements-639`](decisions/dossier-des-amendements-639.md), [`qualification-scrutins-et-cle-dossier-639`](decisions/qualification-scrutins-et-cle-dossier-639.md), [`rattachement-au-dossier-interventions-et-scrutins-639`](decisions/rattachement-au-dossier-interventions-et-scrutins-639.md).

## `src/generate_all_profiles.py`

29 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [Un membre de roster est collecté sous l'acteur que son roster nomme, jamais re-deviné par son nom (#850)](decisions/acteur-du-roster-850.md) | `process_candidat` |
| [L'artifact des amendements passe avant la génération pivot, et son absence se dit (#1101) (2026-09-22)](decisions/artifact-amendements-avant-la-passe-pivot-1101.md) | `_rafraichir_index_amendements` |
| [Un bloc structuré sans fond n'écrase plus un bloc collecté (#484) (2026-08-30)](decisions/bloc-sans-fond-484.md) | `build_minimal_profile` |
| [La boucle du périmètre a cassé quatre fois au même endroit (#771, #775, #781)](decisions/boucle-candidats-quatre-corrections-781.md) | `_normaliser_en_pivot` |
| [Une source injoignable ne consomme plus le timeout d'un job, et son silence cesse de se lire comme un constat (#514) (2026-08-21)](decisions/budget-collecte-source-injoignable-514.md) | `_manifest_append`, `build_profile_any_chambre`, `process_candidat`, `valider_budgets` |
| [Budget d'exécution à pleine échelle : 630 min annoncées, 55 mesurées (#467) (2026-08-20)](decisions/budget-execution-pleine-echelle-467.md) | `_select_candidats_couverture`, `process_candidat` |
| [La chambre est un fait du mandat, pas du profil : `mandats[].chambre` estampillée à la collecte (#492) (2026-08-20)](decisions/chambre-par-mandat-electif.md) | `build_profile_any_chambre` |
| [Un timeout ne peut plus écraser le roster, et rien de collecté ne reste non publié (#511) (2026-08-20)](decisions/collecte-non-publiee.md) | `build_minimal_profile`, `process_candidat` |
| [Une exception n'est pas une preuve, et un défaut de notre code n'est pas une panne de l'Assemblée nationale (#562) (2026-08-28)](decisions/defaut-collecte-vs-panne-562.md) | `build_profile_any_chambre` |
| [Une fonction définie après `if __name__ == "__main__"` n'existe pas pour le script (#922) (2026-09-15)](decisions/definition-apres-le-bloc-execution-922.md) | `_verser_mandats_locaux` |
| [Un paramètre commandait ce qu'il ne nommait pas (#578) (2026-08-29)](decisions/deux-axes-formulaire-578.md) | `_select_candidats_couverture`, `process_candidat` |
| [Le passé sénatorial est un fait de carrière, pas une donnée d'activité : bicaméral pour les candidats seulement (#488) (2026-08-20)](decisions/deux-chambres-interrogees.md) | `build_minimal_profile`, `build_profile_any_chambre`, `process_candidat` |
| [Un amendement retrouve son dossier, et la clé qu'on lui avait retirée (#639, rang 3)](decisions/dossier-des-amendements-639.md) | `_rafraichir_index_amendements` |
| [Borner l'historique de données : ce que ça rend vraiment, et quand (#434) (2026-08-20)](decisions/fenetre-historique-donnees.md) | `_select_existants` |
| [Comment naît l'identité d'un profil, et où vont les identifiants de source (#539) (2026-08-28)](decisions/identite-profils-539.md) | `WARNING_PREFIX_CHAMBRE_EN_ECHEC`, `_effective_slug`, `_select_existants`, `process_candidat` |
| [`extract-senat` ne collecte plus d'interventions : la collecte n'en retenait aucune, par construction (#501) (2026-08-20)](decisions/interventions-senat-501.md) | `_manifest_append`, `build_profile_any_chambre` |
| [Un garde-fou posé sur `builtins.open` ne voit pas `pathlib` (#791) (2026-09-10)](decisions/lectures-du-depot-dans-les-tests-791.md) | `_MEMBRES_GROUPES_SUSPENDUS`, `vider_index_groupes_suspendus` |
| [`--limit` + `--skip-existing` sur `extract-roster-groupes` : sélection progressive + rafraîchissement (2026-08-12)](decisions/limit-skip-existing-roster-groupes.md) | `_select_candidats`, `_select_candidats_couverture`, `process_candidat` |
| [`extract-an` en matrix strategy par candidat, pour isoler la perte en cas de shutdown signal runner (#344) (2026-08-16)](decisions/matrix-extract-an-par-candidat.md) | `process_candidat` |
| [La seconde déclaration lisait un champ que le corpus ne porte pas (#788)](decisions/nom-des-resolutions-vient-de-lappelant-788.md) | `_normaliser_en_pivot`, `process_candidat` |
| [Un fichier de progression dans un répertoire de données (#518, troisième incident) (2026-08-24)](decisions/point-de-sauvegarde-dans-les-profils-518.md) | `DEFAULT_CHECKPOINT_PATH`, `_save_checkpoint` |
| [Les membres de gouvernement deviennent une population, et leur collecte part (#996, lot 3) (2026-09-18)](decisions/provenance-roster-gouvernement-996.md) | `build_profile_any_chambre`, `process_candidat` |
| [Le `texte_vise` fautif se reprend depuis l'archive figée, pas par une fusion plus permissive (#696, 01/09/2026)](decisions/report-texte-vise-source-696.md) | `_rafraichir_index_amendements` |
| [Retrait de `fetch_activity_synthesis` (#356) (2026-08-16)](decisions/retrait-fetch-activity-synthesis.md) | `build_minimal_profile` |
| [NosDéputés sort du pipeline (#529, lot 5 de l'épic « une seule source AN ») (2026-08-27)](decisions/retrait-nosdeputes-529.md) | `process_candidat` |
| [Le Sénat sort du périmètre, et le job qui concluait vert sans rien produire est retiré (#528, lot 3 de l'épic « une seule source AN ») (2026-08-26)](decisions/retrait-senat-528.md) | `SOURCE_VALUES` |
| [Un seul roster par run, une reprise sur ce qui est retentable, et des échecs qu'on peut lire (#518) (2026-08-24)](decisions/roster-unique-par-run-518.md) | `_annoter_github` |
| [Un run de test : même workflow, périmètre réduit, jamais de commit (#792)](decisions/run-de-test-perimetre-reduit-792.md) | `_normaliser_en_pivot` |
| [Régénérer l'existant : `--refresh-existing`, l'inverse de `--skip-existing` (#445) (2026-08-19)](decisions/telechargement-an-trois-modes-defaillance.md) | `_select_candidats_couverture` |

Le mentionnent sans le gouverner : [`amendements-legislatures-figees`](decisions/amendements-legislatures-figees.md), [`chambres-profil-derivees`](decisions/chambres-profil-derivees.md), [`cle-fusion-interventions-540`](decisions/cle-fusion-interventions-540.md), [`collecte-vs-publie-545`](decisions/collecte-vs-publie-545.md), [`consommateurs-chambres-migres`](decisions/consommateurs-chambres-migres.md), [`id-pivot-sans-prefixe`](decisions/id-pivot-sans-prefixe.md), [`integrite-referentielle-pivot`](decisions/integrite-referentielle-pivot.md), [`libelles-formulaire`](decisions/libelles-formulaire.md), [`licence-lot-6-530`](decisions/licence-lot-6-530.md), [`licences`](decisions/licences.md), [`limit-sample`](decisions/limit-sample.md), [`liste-candidats-declares-753`](decisions/liste-candidats-declares-753.md), [`marquage-tranches-derivees-691`](decisions/marquage-tranches-derivees-691.md), [`mode-extraction-leger-roster`](decisions/mode-extraction-leger-roster.md), [`normalisation-amendements`](decisions/normalisation-amendements.md), [`normalisation-votes`](decisions/normalisation-votes.md), [`oom-reconstruction-amendements-figees`](decisions/oom-reconstruction-amendements-figees.md), [`partition-profils-legislature-580`](decisions/partition-profils-legislature-580.md), [`perimetre-collecte-candidatures-declinees-760`](decisions/perimetre-collecte-candidatures-declinees-760.md), [`pivot-freshness-timestamps-stables`](decisions/pivot-freshness-timestamps-stables.md), [`provenance-pivot`](decisions/provenance-pivot.md), [`publication-scopee-artifacts`](decisions/publication-scopee-artifacts.md), [`reconstruction-tranches-depuis-archive-691`](decisions/reconstruction-tranches-depuis-archive-691.md), [`retry-generate-data-preemption`](decisions/retry-generate-data-preemption.md), [`sparse-checkout-extract-an-674`](decisions/sparse-checkout-extract-an-674.md), [`workers-fige-a-1`](decisions/workers-fige-a-1.md).

## `src/generate_gouvernement_profiles.py`

7 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [Cloisonnement de la branche roster, et le code 2 « suspension totale » (#524) (2026-08-26)](decisions/cloisonnement-branche-roster-524.md) | `EXIT_COLLECTE_INCOMPLETE` |
| [Extension de la stabilité des horodatages aux profils groupe/gouvernement/parti (#343, complet) (2026-08-17)](decisions/freshness-timestamps-groupes-gouvernements-partis.md) | `generate_all` |
| [Profils de gouvernement : ne jamais réécrire sur une collecte incomplète, et cache dossiers dédié (#427) (2026-08-18)](decisions/gouvernement-textes-non-ecrasement.md) | `COLLECTE_INCOMPLETE` |
| [Un bloc que la projection retire se lit à la demande, il ne revient pas dans la liste (#1020) (2026-09-18)](decisions/lecture-a-la-demande-des-interventions-1020.md) | `generate_all` |
| [Le `label` d'un mandat `MINISTERE` ne dit pas si c'est un maroquin (#474) (2026-08-20)](decisions/parlementaire-en-mission-nest-pas-ministre.md) | `COLLECTE_INCOMPLETE` |
| [Le plafond de lecture du roster, et le commit qui ne paie plus pour une source lente (#518, second incident) (2026-08-24)](decisions/plafond-roster-et-commit-518.md) | `EXIT_COLLECTE_INCOMPLETE` |
| [La fiche rattache ses membres par `organe_ref`, plus par un libellé comparé entre deux sources (#996, lot 4) (2026-09-18)](decisions/rattachement-des-membres-par-organe-996.md) | `charger_membres_roster` |

Le mentionnent sans le gouverner : [`audit-599-projection-blocs-lus-628`](decisions/audit-599-projection-blocs-lus-628.md), [`generation-fiches-lignees-836`](decisions/generation-fiches-lignees-836.md), [`gouvernement-ci-integration`](decisions/gouvernement-ci-integration.md), [`gouvernement-profile-rattachement`](decisions/gouvernement-profile-rattachement.md), [`lectures-pipeline-par-projection-635`](decisions/lectures-pipeline-par-projection-635.md).

## `src/generate_group_profiles.py`

2 décision(s) le gouvernent ; le module en cite 1.

| Décision | Nomme |
| --- | --- |
| [Cloisonnement de la branche roster, et le code 2 « suspension totale » (#524) (2026-08-26)](decisions/cloisonnement-branche-roster-524.md) | `EXIT_ROSTER_INDISPONIBLE` |
| [Le plafond de lecture du roster, et le commit qui ne paie plus pour une source lente (#518, second incident) (2026-08-24)](decisions/plafond-roster-et-commit-518.md) | `ResultatGeneration` |

Le mentionnent sans le gouverner : [`amendements-agreges-dans-la-periode-821`](decisions/amendements-agreges-dans-la-periode-821.md), [`consommateurs-chambres-migres`](decisions/consommateurs-chambres-migres.md), [`extraction-groupe-suspendue-516`](decisions/extraction-groupe-suspendue-516.md), [`fiches-groupe-17e-legislature-700`](decisions/fiches-groupe-17e-legislature-700.md), [`generation-fiches-lignees-836`](decisions/generation-fiches-lignees-836.md), [`gouvernement-profile-rattachement`](decisions/gouvernement-profile-rattachement.md), [`identifiants-groupes-et-successions-multiples-815`](decisions/identifiants-groupes-et-successions-multiples-815.md), [`integrite-referentielle-pivot`](decisions/integrite-referentielle-pivot.md), [`position-politique-groupes-686`](decisions/position-politique-groupes-686.md), [`roster-an-derive-amo30-526`](decisions/roster-an-derive-amo30-526.md), [`senat-periode-debut`](decisions/senat-periode-debut.md).

## `src/generate_lignee_profiles.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Les dix lignées sont écrites, et une mesure corrige le motif du recalcul (#836)](decisions/generation-fiches-lignees-836.md) | `verifier_partition` |

## `src/generate_roster_candidats.py`

9 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [La bascule : le roster des groupes AN vient d'AMO30 (#527, lot 1b de l'épic « une seule source AN ») (2026-08-26)](decisions/bascule-roster-an-amo30-527.md) | `build_roster_candidats_detaille`, `membres_sans_slug` |
| [Cloisonnement de la branche roster, et le code 2 « suspension totale » (#524) (2026-08-26)](decisions/cloisonnement-branche-roster-524.md) | `anomalies_roster`, `fetch_rosters_bruts`, `resume_exception` |
| [Un timeout ne peut plus écraser le roster, et rien de collecté ne reste non publié (#511) (2026-08-20)](decisions/collecte-non-publiee.md) | `fetch_rosters_bruts` |
| [Suspendre l'extraction des deux groupes Sénat, sans les retirer de la config (#516) (2026-08-24)](decisions/extraction-groupe-suspendue-516.md) | `fetch_rosters_bruts` |
| [Les 5 groupes de la XVIIe entrent dans `groupes[]`, et leur succession est déclarée comme une relecture (#700) (2026-09-01)](decisions/fiches-groupe-17e-legislature-700.md) | `build_roster_candidats_detaille` |
| [Les membres de gouvernement deviennent une population, et leur collecte part (#996, lot 3) (2026-09-18)](decisions/provenance-roster-gouvernement-996.md) | `candidats_des_gouvernements` |
| [NosDéputés sort du pipeline (#529, lot 5 de l'épic « une seule source AN ») (2026-08-27)](decisions/retrait-nosdeputes-529.md) | `membres_sans_slug` |
| [Le roster des groupes AN est dérivé d'AMO30, derrière un drapeau baissé (#526, lot 1 de l'épic « une seule source AN ») (2026-08-26)](decisions/roster-an-derive-amo30-526.md) | `build_roster_candidats_detaille`, `membres_sans_slug` |
| [Un membre de roster sans correspondance relue reçoit un slug, et la collision reste un refus (#708) (2026-09-02)](decisions/slug-fabrique-membre-de-roster-708.md) | `build_roster_candidats_detaille`, `membres_sans_slug`, `membres_slug_fabrique` |

Le mentionnent sans le gouverner : [`acteur-du-roster-850`](decisions/acteur-du-roster-850.md), [`collecte-interventions-reduite-au-theme-657`](decisions/collecte-interventions-reduite-au-theme-657.md), [`consommateurs-chambres-migres`](decisions/consommateurs-chambres-migres.md), [`liste-candidats-declares-753`](decisions/liste-candidats-declares-753.md), [`merge-and-pivot-budget-permissions-413`](decisions/merge-and-pivot-budget-permissions-413.md), [`plafond-roster-et-commit-518`](decisions/plafond-roster-et-commit-518.md), [`provenance-pivot`](decisions/provenance-pivot.md), [`retrait-fiches-parti-906`](decisions/retrait-fiches-parti-906.md), [`revue-workflows-ci-342`](decisions/revue-workflows-ci-342.md), [`roster-unique-par-run-518`](decisions/roster-unique-par-run-518.md), [`telechargement-an-trois-modes-defaillance`](decisions/telechargement-an-trois-modes-defaillance.md), [`web-v3-ui`](decisions/web-v3-ui.md).

## `src/gha.py`

Le mentionnent sans le gouverner : [`plafond-roster-et-commit-518`](decisions/plafond-roster-et-commit-518.md), [`roster-unique-par-run-518`](decisions/roster-unique-par-run-518.md).

## `src/gouvernement_profile.py`

5 décision(s) le gouvernent ; le module en cite 1.

| Décision | Nomme |
| --- | --- |
| [La parole d'un gouvernement se compte dans la fenêtre de chaque membre, pas dans celle du gouvernement (#1020) (2026-09-18)](decisions/agregat-parole-gouvernement-1020.md) | `agreger_tags_thematiques`, `fenetres_des_membres` |
| [`gouvernement_profile.py` : rattachement des textes par `date_depot`, exclusion silencieuse des dossiers non classifiables (#211) (2026-08-14)](decisions/gouvernement-profile-rattachement.md) | `build_gouvernement_profile` |
| [Un bloc que la projection retire se lit à la demande, il ne revient pas dans la liste (#1020) (2026-09-18)](decisions/lecture-a-la-demande-des-interventions-1020.md) | `agreger_tags_thematiques`, `build_gouvernement_profile` |
| [Trois lectures du corpus passent à la projection, et chacune a son plafond dans un test (#635, 2026-08-30)](decisions/lectures-pipeline-par-projection-635.md) | `_index_acteur_ref_vers_membre`, `build_gouvernement_profile` |
| [Un singulier et un pluriel sont le même sujet : la clé groupe, la source publie (#1042) (2026-09-20)](decisions/tags-singulier-et-pluriel-1042.md) | `agreger_tags_thematiques` |

Le mentionnent sans le gouverner : [`audit-599-projection-blocs-lus-628`](decisions/audit-599-projection-blocs-lus-628.md), [`audit-pipeline-gouvernement`](decisions/audit-pipeline-gouvernement.md), [`freshness-timestamps-groupes-gouvernements-partis`](decisions/freshness-timestamps-groupes-gouvernements-partis.md), [`gouvernement-premier-ministre-portefeuille`](decisions/gouvernement-premier-ministre-portefeuille.md), [`gouvernement-textes-fam-codes-archives`](decisions/gouvernement-textes-fam-codes-archives.md), [`gouvernement-textes-fam-codes-manquants`](decisions/gouvernement-textes-fam-codes-manquants.md), [`gouvernement-textes-initiateurs`](decisions/gouvernement-textes-initiateurs.md), [`hors-perimetre`](decisions/hors-perimetre.md), [`parlementaire-en-mission-nest-pas-ministre`](decisions/parlementaire-en-mission-nest-pas-ministre.md), [`pivot-freshness-timestamps-stables`](decisions/pivot-freshness-timestamps-stables.md).

## `src/gouvernement_roster.py`

15 décision(s) le gouvernent ; le module en cite 4.

| Décision | Nomme |
| --- | --- |
| [Un audit lit le corpus par projection, et son plafond de mémoire est dans un test (#628, 2026-08-30)](decisions/audit-599-projection-blocs-lus-628.md) | `load_profils_from_dir` |
| [La civilité et la nomenclature PCS de l'INSEE traversaient le pipeline sans y laisser de trace (#659) (2026-08-31)](decisions/civilite-et-pcs-insee-659.md) | `_normalise_fonction` |
| [`membres[]` publiait deux fois le même fait : dédupliquer sans effacer les changements de portefeuille (#480) (2026-08-20)](decisions/deduplication-entrees-membres.md) | `_source_url_portefeuille`, `build_gouvernement_roster`, `build_premier_ministre` |
| [`gouvernement_profile` : `premier_ministre` et `portefeuille` câblés depuis les mandats `MINISTERE` (#398) (2026-08-18)](decisions/gouvernement-premier-ministre-portefeuille.md) | `_est_mandat_appartenance_gouvernement` |
| [`gouvernement_roster.py` : désambiguïsation par libellé exact + garde-fou de période, pas l'inverse (#209) (2026-08-14)](decisions/gouvernement-roster-desambiguisation.md) | `build_gouvernement_roster` |
| [Profils de gouvernement : le lien ministre → texte (#435) (2026-08-18)](decisions/gouvernement-textes-initiateurs.md) | `acteur_ref_depuis_profil` |
| [L'`id` d'un profil pivot est le slug : le préfixe de provenance était instable (#487) (2026-08-20)](decisions/id-pivot-sans-prefixe.md) | `build_gouvernement_roster` |
| [Un bloc que la projection retire se lit à la demande, il ne revient pas dans la liste (#1020) (2026-09-18)](decisions/lecture-a-la-demande-des-interventions-1020.md) | `BLOCS_LUS_COMPOSITION`, `_lire_profil_projete`, `charger_profils_et_chemins`, `lecteur_interventions`, `load_profils_from_dir` |
| [Trois lectures du corpus passent à la projection, et chacune a son plafond dans un test (#635, 2026-08-30)](decisions/lectures-pipeline-par-projection-635.md) | `BLOCS_LUS_COMPOSITION`, `acteur_ref_depuis_profil`, `build_premier_ministre`, `load_profils_from_dir` |
| [Le libellé d'organe du chef du gouvernement s'accorde en genre, la qualité jamais (#658) (2026-08-31)](decisions/libelle-chef-du-gouvernement-au-feminin-658.md) | `FONCTIONS_MINISTERIELLES_OBSERVEES`, `LABELS_PORTEFEUILLE_PREMIER_MINISTRE_OBSERVES`, `_normalise_fonction`, `_normalise_libelle_organe`, `_normalise_typographique`, `build_gouvernement_roster`, `build_premier_ministre` |
| [Le référentiel type l'organe, il n'y a rien à interpréter (#730) (2026-09-04)](decisions/mandats-gouvernementaux-en-commission-730.md) | `FONCTIONS_MINISTERIELLES`, `_normalise_fonction` |
| [Le `label` d'un mandat `MINISTERE` ne dit pas si c'est un maroquin (#474) (2026-08-20)](decisions/parlementaire-en-mission-nest-pas-ministre.md) | `FONCTIONS_MINISTERIELLES`, `FONCTIONS_MINISTERIELLES_OBSERVEES`, `_est_mandat_appartenance_gouvernement`, `_normalise_fonction`, `_portefeuilles_du_mandat`, `_qualite_portefeuille`, `build_gouvernement_roster`, `build_premier_ministre` |
| [`check_quality_gate.py` : section gouvernements (§5), couverture ministérielle proxy par `portefeuille` (#212) (2026-08-14)](decisions/quality-gate-gouvernements.md) | `build_gouvernement_roster` |
| [La fiche rattache ses membres par `organe_ref`, plus par un libellé comparé entre deux sources (#996, lot 4) (2026-09-18)](decisions/rattachement-des-membres-par-organe-996.md) | `slugs_du_gouvernement` |
| [Un test d'acceptation adossé au corpus vivant rougit quand la donnée s'améliore (#457) (2026-08-20)](decisions/test-adosse-au-corpus-vivant.md) | `build_gouvernement_roster` |

Le mentionnent sans le gouverner : [`gouvernement-ci-integration`](decisions/gouvernement-ci-integration.md), [`gouvernement-profile-rattachement`](decisions/gouvernement-profile-rattachement.md), [`mandat-electif-perdu-fausse-le-denominateur`](decisions/mandat-electif-perdu-fausse-le-denominateur.md), [`perimetre-controle-perte`](decisions/perimetre-controle-perte.md).

## `src/gouvernement_roster_an.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Les membres d'un gouvernement reçoivent un identifiant de profil (#996, lot 2) (2026-09-17)](decisions/roster-gouvernements-amo30-996.md) | `construire_index_gouvernements` |

## `src/gouvernement_textes.py`

17 décision(s) le gouvernent ; le module en cite 6.

| Décision | Nomme |
| --- | --- |
| [La XIVe législature n'était pas inexploitable, elle était monolithique (#1019) (2026-09-18)](decisions/archive-dossiers-xiv-1019.md) | `_COLLECTIONS_MONOLITHE`, `_entrees_monolithiques`, `_uid_depuis_nom`, `parse_dossier_gouvernemental` |
| [Dossiers législatifs : ingestion multi-archives, origine par document déposé, statut `promulgue` (#400) (2026-08-18)](decisions/dossiers-multi-archives-origine-document.md) | `iter_dossiers_bruts` |
| [Un texte renvoyé en commission n'est pas un texte examiné (#997) (2026-09-18)](decisions/examen-en-commission-997.md) | `_CODES_NUS_DATES`, `_determine_statut`, `est_acte_au_dela_du_depot`, `est_examen_en_commission` |
| [La fiche de gouvernement dit d'abord où elle se situe (#330)](decisions/fiche-de-gouvernement-330.md) | `_determine_statut` |
| [L'archive vivante se reprend au changement de semaine, les mortes jamais (#762), 07/09/2026](decisions/fraicheur-dossiers-762.md) | `ensure_dossiers_zip_downloaded`, `rafraichir_dossiers_actifs` |
| [`gouvernement_textes` : 3 derniers `fam_code` mappés ; `TSORTF02` tranché sur données réelles (#402) (2026-08-18)](decisions/gouvernement-textes-fam-codes-archives.md) | `_FAM_CODE_STATUT_MAP`, `_STATUTS_CORRIGES_PAR_PROMULGATION` |
| [`gouvernement_textes` : 3 `fam_code` manquants excluaient 42 % des textes ; `adopte_cmp` ajouté à la nomenclature (#397) (2026-08-18)](decisions/gouvernement-textes-fam-codes-manquants.md) | `_FAM_CODE_STATUT_MAP` |
| [Profils de gouvernement : le lien ministre → texte (#435) (2026-08-18)](decisions/gouvernement-textes-initiateurs.md) | `parse_dossier_gouvernemental` |
| [Profils de gouvernement : ne jamais réécrire sur une collecte incomplète, et cache dossiers dédié (#427) (2026-08-18)](decisions/gouvernement-textes-non-ecrasement.md) | `fetch_dossiers_gouvernementaux` |
| [`gouvernement_textes.py` : filtre de statut par décision de séance, pas par `codeActe`/`fam_code` seul (#210) (2026-08-14)](decisions/gouvernement-textes-statut.md) | `DOSSIERS_CACHE_DIR`, `_est_decision_de_seance`, `ensure_dossiers_zip_downloaded` |
| [`gouvernement_textes.py` : filtre de statut par décision de séance, pas par `codeActe`/`fam_code` seul (#210) (2026-08-14)](decisions/gouvernement-textes-statut-210-version-initiale.md) | `DOSSIERS_CACHE_DIR`, `_est_decision_de_seance`, `ensure_dossiers_zip_downloaded` |
| [Mandats commission/groupe_amitie/extra_parlementaire sourcés depuis l'AN, fetch_identity NosDéputés rendu conditionnel (#369, complet), watchdog générique sur tous les téléchargements zip (#370, complet) (2026-08-17)](decisions/mandats-officiels-an-369.md) | `ensure_dossiers_zip_downloaded` |
| [Un profil de roster ne porte pas une liste que sa propre collecte déclare écartée — purge des 49 `textes_portes` résiduels (#747)](decisions/purge-textes-portes-roster-747.md) | `_determine_statut` |
| [Un projet de loi porté au nom du Gouvernement n'est pas une production personnelle (#689) (2026-09-01)](decisions/qualification-textes-portes-689.md) | `nature_texte_depose` |
| [Un scrutin ne dit pas quel texte il tranche : le lien se lit à l'envers (#758), 07/09/2026](decisions/rattachement-scrutin-dossier-758.md) | `_determine_statut`, `iter_dossiers_bruts` |
| [Résilience de `generate-data.yml` face aux `shutdown signal` runner : continue-on-error généralisé, watchdog réseau, retry générique sur `_get_payload`, retry `retry-generate-data.yml` non-régressif, et appels NosDéputés morts pour les députés (dossiers, votes) (2026-08-16)](decisions/resilience-generate-data-shutdown-signal.md) | `ensure_dossiers_zip_downloaded` |
| [Un texte porté dit ce qu'il est devenu, et son sort ne se déduit jamais de son stade (#743) (2026-09-06)](decisions/sort-des-textes-portes-743.md) | `_determine_statut`, `parse_dossier_gouvernemental` |

Le mentionnent sans le gouverner : [`audit-pipeline-gouvernement`](decisions/audit-pipeline-gouvernement.md), [`couverture-dossiers-hors-couverture-vs-zero`](decisions/couverture-dossiers-hors-couverture-vs-zero.md), [`gouvernement-ci-integration`](decisions/gouvernement-ci-integration.md), [`gouvernement-doc-cloture`](decisions/gouvernement-doc-cloture.md), [`gouvernement-profile-rattachement`](decisions/gouvernement-profile-rattachement.md), [`gouvernement-textes-statut-49-3-rejete`](decisions/gouvernement-textes-statut-49-3-rejete.md), [`hors-perimetre`](decisions/hors-perimetre.md), [`plafond-roster-et-commit-518`](decisions/plafond-roster-et-commit-518.md), [`quality-gate-gouvernements`](decisions/quality-gate-gouvernements.md).

## `src/gouvernements_amo30.py`

Le mentionnent sans le gouverner : [`liste-gouvernements-amo30-996`](decisions/liste-gouvernements-amo30-996.md), [`rattachement-des-membres-par-organe-996`](decisions/rattachement-des-membres-par-organe-996.md), [`repertoire-config-1057`](decisions/repertoire-config-1057.md).

## `src/group_profile.py`

33 décision(s) le gouvernent ; le module en cite 4.

| Décision | Nomme |
| --- | --- |
| [Un agrégat de fiche ne compte que la période de la fiche (#821)](decisions/amendements-agreges-dans-la-periode-821.md) | `_aggregate_amendements`, `_votes_de_legislature`, `aggregate_tags_thematiques` |
| [Un amendement cosigné n'est pas N amendements : deux grandeurs, deux noms (#643) (2026-08-31)](decisions/amendements-distincts-et-signatures-643.md) | `ContributionAmendements`, `CumulAmendementsDistincts`, `_aggregate_amendements`, `_compute_cohesion_votes`, `_member_eligibility_intervals`, `load_profil_from_file` |
| [Un audit lit le corpus par projection, et son plafond de mémoire est dans un test (#628, 2026-08-30)](decisions/audit-599-projection-blocs-lus-628.md) | `generate_groupe_profile_from_roster` |
| [La bascule : le roster des groupes AN vient d'AMO30 (#527, lot 1b de l'épic « une seule source AN ») (2026-08-26)](decisions/bascule-roster-an-amo30-527.md) | `_avertissement_fraicheur_an` |
| [La chambre est un fait du mandat, pas du profil : `mandats[].chambre` estampillée à la collecte (#492) (2026-08-20)](decisions/chambre-par-mandat-electif.md) | `_aggregate_mandats`, `_compute_cohesion_votes`, `_is_eligible_at`, `_mandats_electifs`, `_member_eligibility_intervals`, `build_groupe_profile`, `compute_ecarts_cohesion_internes` |
| [Tous les comptes d'une fiche de groupe se rapportent à une date, et elle est publiée (#653) (2026-08-31)](decisions/date-de-reference-des-comptes-de-groupe-653.md) | `_intervals_overlap`, `_select_mandat_a_la_date`, `_select_mandat_entree_unique` |
| [`debut_dans_groupe` se lit sur le mandat de groupe, plus sur le premier mandat électif (#653) (2026-08-31)](decisions/dates-appartenance-groupe-653.md) | `build_groupe_profile` |
| [Le passé sénatorial est un fait de carrière, pas une donnée d'activité : bicaméral pour les candidats seulement (#488) (2026-08-20)](decisions/deux-chambres-interrogees.md) | `_is_eligible_at`, `_member_eligibility_intervals` |
| [L'effectif d'un groupe dans le temps : `min_historique` et `max_historique` portent leur date (#702) — 01/09/2026](decisions/effectif-du-groupe-dans-le-temps-702.md) | `_appartenance_couvre`, `build_groupe_profile` |
| [Les fenêtres de parole se comptent depuis la date des données, pas depuis la clôture de la fiche (#1081) (2026-09-22)](decisions/fenetres-depuis-la-date-des-donnees-1081.md) | `bornes_des_fenetres` |
| [Extension de la stabilité des horodatages aux profils groupe/gouvernement/parti (#343, complet) (2026-08-17)](decisions/freshness-timestamps-groupes-gouvernements-partis.md) | `generate_groupe_profile_from_roster` |
| [Les dix lignées sont écrites, et une mesure corrige le motif du recalcul (#836)](decisions/generation-fiches-lignees-836.md) | `_aggregate_amendements` |
| [Juxtaposer deux positions sourcées n'est pas mesurer un écart (#328) — 01/09/2026](decisions/juxtaposition-position-groupe-328.md) | `compute_ecarts_cohesion_internes` |
| [Trois lectures du corpus passent à la projection, et chacune a son plafond dans un test (#635, 2026-08-30)](decisions/lectures-pipeline-par-projection-635.md) | `BLOCS_LUS_MEMBRE`, `_aggregate_amendements`, `_aggregate_mandats`, `_is_pivot_v1`, `aggregate_tags_thematiques`, `build_groupe_profile`, `compute_ecarts_cohesion_internes`, `contribution_amendements`, `generate_groupe_profile_from_roster`, `load_profil_from_file` |
| [Un mandat électif perdu ne manque pas seulement sur la fiche : il sort le membre du dénominateur de son groupe (#465) (2026-08-20)](decisions/mandat-electif-perdu-fausse-le-denominateur.md) | `_aggregate_amendements`, `_member_eligibility_intervals` |
| [`mandats_agreges` : agrégation catégorielle sur `mandats[]`, famille 1 (#361, sous-issue de #349) (2026-08-16)](decisions/mandats-agreges-famille-1.md) | `MANDATS_AGREGES_CATEGORIES`, `_aggregate_mandats`, `_compute_cohesion_votes`, `_intervals_overlap`, `_is_eligible_at`, `_member_eligibility_intervals`, `_select_mandat_entree_unique` |
| [Les mandats agrégés d'un groupe sont ceux exercés pendant l'appartenance (#853) (2026-09-22)](decisions/mandats-agreges-par-appartenance-853.md) | `_member_eligibility_intervals`, `periodes_d_appartenance` |
| [`mandats_agreges` : « qui y siège » et « qui y est passé » sont deux nombres, pas un (#656) (2026-08-31)](decisions/mandats-agreges-siege-vs-passe-656.md) | `_aggregate_mandats` |
| [Normaliser les amendements : le coût n'est pas l'amendement, c'est sa liste de cosignataires (#431) (2026-08-19)](decisions/normalisation-amendements.md) | `_aggregate_amendements` |
| [Normalisation de `par_fonction` dans `mandats_agreges`, et requalification du défaut « catégorie commission » (#379) (2026-08-17)](decisions/normalisation-fonction-mandats-agreges.md) | `_aggregate_mandats`, `_normalize_fonction_mandat` |
| [Normaliser les votes : une liste partagée, un mapping, et deux invariants devenus des jointures (#432) (2026-08-19)](decisions/normalisation-votes.md) | `_votes_de_legislature` |
| [La parole d'un groupe est celle tenue pendant l'appartenance, comptée sur 6 et 12 mois (#1073) (2026-09-22)](decisions/parole-de-groupe-par-appartenance-et-fenetre-1073.md) | `CLES_LUES_PAR_ENTREE`, `_interventions_retenues`, `_tags_du_membre`, `periodes_d_appartenance` |
| [L'appartenance publiée cesse d'être une enveloppe (#809)](decisions/periodes-appartenance-809.md) | `_appartenance_couvre` |
| [Un champ traverse la chaîne, ou il n'existe pas (#809)](decisions/periodes-jetees-par-le-filtre-809.md) | `_appartenance_couvre`, `appartenances_depuis_roster`, `projeter_profil_membre` |
| [Un profil de roster ne porte pas une liste que sa propre collecte déclare écartée — purge des 49 `textes_portes` résiduels (#747)](decisions/purge-textes-portes-roster-747.md) | `BLOCS_LUS_MEMBRE` |
| [Résoudre la `legislature` d'un vote : deux mécanismes, pas un seul (#432) (2026-08-19)](decisions/resolution-legislature-deux-mecanismes-432.md) | `_votes_de_legislature` |
| [Restaurer 789 interventions sans revenir sur le reste du schéma (#460) (2026-08-19)](decisions/restauration-interventions.md) | `aggregate_tags_thematiques` |
| [NosDéputés sort du pipeline (#529, lot 5 de l'épic « une seule source AN ») (2026-08-27)](decisions/retrait-nosdeputes-529.md) | `_avertissement_fraicheur_an` |
| [Groupes Sénat : ne pas renseigner `senat_periode_debut` dans `groupes_reels.json` (2026-08-12)](decisions/senat-periode-debut.md) | `generate_groupe_profile_from_roster` |
| [L'empreinte thématique d'une fiche est celle de sa législature (#825)](decisions/tags-agreges-dans-la-periode-825.md) | `_votes_de_legislature`, `aggregate_tags_thematiques` |
| [Un singulier et un pluriel sont le même sujet : la clé groupe, la source publie (#1042) (2026-09-20)](decisions/tags-singulier-et-pluriel-1042.md) | `aggregate_tags_thematiques` |
| [Taxonomie des mandats : exploitation des `typeOrgane` AN non mappés (#382, option « mixte ») (2026-08-17)](decisions/taxonomie-mandats-typeorgane-an.md) | `MANDATS_AGREGES_CATEGORIES` |
| [Votes : agrégation des législatures 14 à 17, index dédupliqué, 14/15/16 figées (#403) (2026-08-18)](decisions/votes-multi-legislature.md) | `_compute_cohesion_votes` |

Le mentionnent sans le gouverner : [`civilite-et-pcs-insee-659`](decisions/civilite-et-pcs-insee-659.md), [`consommateurs-chambres-migres`](decisions/consommateurs-chambres-migres.md), [`divergences-avec-le-groupe-328`](decisions/divergences-avec-le-groupe-328.md), [`fiche-de-lignee-ui-329`](decisions/fiche-de-lignee-ui-329.md), [`id-pivot-sans-prefixe`](decisions/id-pivot-sans-prefixe.md), [`identifiants-groupes-et-successions-multiples-815`](decisions/identifiants-groupes-et-successions-multiples-815.md), [`identite-profils-539`](decisions/identite-profils-539.md), [`mandats-electifs-liste-complete-640`](decisions/mandats-electifs-liste-complete-640.md), [`ne-jamais-committer-un-build-perime`](decisions/ne-jamais-committer-un-build-perime.md), [`pivot-freshness-timestamps-stables`](decisions/pivot-freshness-timestamps-stables.md), [`populations-profils-portees-par-les-outils-630`](decisions/populations-profils-portees-par-les-outils-630.md), [`profil-de-groupe-lecture-329`](decisions/profil-de-groupe-lecture-329.md), [`provenance-par-champ-603`](decisions/provenance-par-champ-603.md), [`provenance-roster-gouvernement-996`](decisions/provenance-roster-gouvernement-996.md), [`retrait-groupes-senat-nossenateurs`](decisions/retrait-groupes-senat-nossenateurs.md), [`syceron-acteur-ref-nu-510`](decisions/syceron-acteur-ref-nu-510.md), [`syceron-archives-verifiees-parseur-510`](decisions/syceron-archives-verifiees-parseur-510.md).

## `src/group_roster.py`

10 décision(s) le gouvernent ; le module en cite 4.

| Décision | Nomme |
| --- | --- |
| [Un membre de roster est collecté sous l'acteur que son roster nomme, jamais re-deviné par son nom (#850)](decisions/acteur-du-roster-850.md) | `filter_roster_by_sigle` |
| [La bascule : le roster des groupes AN vient d'AMO30 (#527, lot 1b de l'épic « une seule source AN ») (2026-08-26)](decisions/bascule-roster-an-amo30-527.md) | `ERREURS_ROSTER`, `fetch_full_roster` |
| [Suspendre l'extraction des deux groupes Sénat, sans les retirer de la config (#516) (2026-08-24)](decisions/extraction-groupe-suspendue-516.md) | `fetch_full_roster` |
| [Un champ traverse la chaîne, ou il n'existe pas (#809)](decisions/periodes-jetees-par-le-filtre-809.md) | `filter_roster_by_sigle` |
| [Le plafond de lecture du roster, et le commit qui ne paie plus pour une source lente (#518, second incident) (2026-08-24)](decisions/plafond-roster-et-commit-518.md) | `fetch_full_roster` |
| [NosDéputés sort du pipeline (#529, lot 5 de l'épic « une seule source AN ») (2026-08-27)](decisions/retrait-nosdeputes-529.md) | `ERREURS_ROSTER`, `fetch_full_roster`, `filter_roster_by_sigle` |
| [Le Sénat sort du périmètre, et le job qui concluait vert sans rien produire est retiré (#528, lot 3 de l'épic « une seule source AN ») (2026-08-26)](decisions/retrait-senat-528.md) | `ERREURS_ROSTER`, `filter_roster_by_sigle` |
| [Le roster des groupes AN est dérivé d'AMO30, derrière un drapeau baissé (#526, lot 1 de l'épic « une seule source AN ») (2026-08-26)](decisions/roster-an-derive-amo30-526.md) | `fetch_full_roster`, `filter_roster_by_sigle` |
| [Un seul roster par run, une reprise sur ce qui est retentable, et des échecs qu'on peut lire (#518) (2026-08-24)](decisions/roster-unique-par-run-518.md) | `fetch_full_roster` |
| [Un membre de roster sans correspondance relue reçoit un slug, et la collision reste un refus (#708) (2026-09-02)](decisions/slug-fabrique-membre-de-roster-708.md) | `filter_roster_by_sigle` |

Le mentionnent sans le gouverner : [`cloisonnement-branche-roster-524`](decisions/cloisonnement-branche-roster-524.md), [`profil-de-groupe-lecture-329`](decisions/profil-de-groupe-lecture-329.md), [`senat-periode-debut`](decisions/senat-periode-debut.md), [`votes-multi-legislature`](decisions/votes-multi-legislature.md).

## `src/groupes_config.py`

6 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [Trois absences publiées comme des faits (#556, #558, #560) (2026-08-29)](decisions/absences-publiees-comme-faits-556-558-560.md) | `anomalies_suspension`, `index_membres_de_groupes_suspendus` |
| [La bascule : le roster des groupes AN vient d'AMO30 (#527, lot 1b de l'épic « une seule source AN ») (2026-08-26)](decisions/bascule-roster-an-amo30-527.md) | `CorrespondanceSiglesInvalide` |
| [Corriger là où un champ est jeté ne suffit pas : il faut trouver tous les endroits où l'objet est fabriqué (#901) (2026-09-14)](decisions/deux-fabriques-textes-portes-europeens-901.md) | `resume_suspension` |
| [Suspendre l'extraction des deux groupes Sénat, sans les retirer de la config (#516) (2026-08-24)](decisions/extraction-groupe-suspendue-516.md) | `anomalies_suspension` |
| [Les 5 groupes de la XVIIe entrent dans `groupes[]`, et leur succession est déclarée comme une relecture (#700) (2026-09-01)](decisions/fiches-groupe-17e-legislature-700.md) | `CorrespondanceSiglesInvalide`, `_valider_successions`, `charger_correspondance_sigles`, `libelle_groupe` |
| [La position politique d'un groupe est celle que l'Assemblée déclare, lue dans une table committée (#686) (2026-09-01)](decisions/position-politique-groupes-686.md) | `CHEMIN_CONFIG_GROUPES`, `CLE_CORRESPONDANCE_SIGLES`, `CorrespondanceSiglesInvalide`, `charger_correspondance_sigles`, `entree_correspondance`, `position_politique_publiee` |

## `src/identifiants_wikidata.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [La liste des candidats pilote le périmètre du run, elle ne le documente plus (#757)](decisions/boucle-perimetre-candidats-757.md) | `ResolutionIndisponible` |

## `src/json_io.py`

3 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Un timeout ne peut plus écraser le roster, et rien de collecté ne reste non publié (#511) (2026-08-20)](decisions/collecte-non-publiee.md) | `ecrire_profil_json` |
| [Trouver les amendements d'un sujet : l'article visé et un index de mots de l'exposé (#1029) (2026-09-22)](decisions/index-de-mots-des-amendements-1029.md) | `ecrire_index_json` |
| [Un index partagé ne se réécrit que si son contenu change (#1075) (2026-09-22)](decisions/index-reecrits-seulement-si-le-contenu-change-1075.md) | `ecrire_index_json` |

Le mentionnent sans le gouverner : [`profils-json-compact`](decisions/profils-json-compact.md).

## `src/licences.py`

6 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [Le sédiment se compte avant de se juger : sept familles, deux couches, aucun retrait (#839, lot A) (2026-09-12)](decisions/audit-sediment-inventaire-839.md) | `LICENCE_PAR_TYPE_SOURCE` |
| [Une étiquette de licence écrite en dur survit à la source qu'elle décrit (#909) (2026-09-13)](decisions/licence-jamais-en-dur-909.md) | `LICENCE_PARLTRACK`, `appliquer_licence_donnees` |
| [Le versant AN passe en Licence Ouverte, et `meta.licence_donnees` devient un champ dérivé (#530, lot 6 de l'épic « une seule source AN ») (2026-08-27)](decisions/licence-lot-6-530.md) | `appliquer_licence_donnees` |
| [Le Parlement européen n'a qu'une licence dans ce dépôt : CC BY 4.0 (#983) (2026-09-16)](decisions/licence-parlement-europeen-cc-by-983.md) | `LICENCE_EUROPARL` |
| [Le nettoyage fait, la clause ODbL ne tiendrait plus que par un marqueur, sur 475 profils (#839, lot C) (2026-09-12)](decisions/residus-source-retiree-839.md) | `licences_du_profil` |
| [Un marqueur de provenance sans donnée derrière lui n'est plus une traçabilité, c'est une inexactitude (#890) (2026-09-13)](decisions/retrait-marqueur-regards-citoyens-deputes-890.md) | `appliquer_licence_donnees`, `licences_du_profil` |

Le mentionnent sans le gouverner : [`contact-et-comptes-publics-328`](decisions/contact-et-comptes-publics-328.md), [`licence-du-code-agpl-1032`](decisions/licence-du-code-agpl-1032.md), [`licences`](decisions/licences.md), [`nettoyage-sediment-839`](decisions/nettoyage-sediment-839.md), [`pages-statiques-methodologie-mentions-legales`](decisions/pages-statiques-methodologie-mentions-legales.md), [`regles-par-domaine-737`](decisions/regles-par-domaine-737.md).

## `src/lignee_profile.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Les dix lignées sont écrites, et une mesure corrige le motif du recalcul (#836)](decisions/generation-fiches-lignees-836.md) | `recalculer_agregats` |

## `src/lois_jorf.py`

Le mentionnent sans le gouverner : [`table-figee-numero-de-loi-vers-jorftext`](decisions/table-figee-numero-de-loi-vers-jorftext.md).

## `src/mandats_anterieurs.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Les mandats antérieurs à la couverture de l'Assemblée entrent par une table relue (#860)](decisions/mandats-anterieurs-couverture-860.md) | `appliquer_mandats_anterieurs`, `charger_table` |

Le mentionnent sans le gouverner : [`accueil-borne-par-institution-328`](decisions/accueil-borne-par-institution-328.md), [`borne-mandats-locaux-2020-922`](decisions/borne-mandats-locaux-2020-922.md), [`constat-absence-mandats-anterieurs-860`](decisions/constat-absence-mandats-anterieurs-860.md), [`correspondance-elus-rne-relue-922`](decisions/correspondance-elus-rne-relue-922.md), [`mention-mandats-anterieurs-fiche-candidat-860`](decisions/mention-mandats-anterieurs-fiche-candidat-860.md), [`repertoire-config-1057`](decisions/repertoire-config-1057.md), [`sediment-nosdeputes-839`](decisions/sediment-nosdeputes-839.md).

## `src/mep_profile.py`

1 décision(s) le gouvernent ; le module en cite 1.

| Décision | Nomme |
| --- | --- |
| [Une étiquette de licence écrite en dur survit à la source qu'elle décrit (#909) (2026-09-13)](decisions/licence-jamais-en-dur-909.md) | `normalize_parltrack` |

Le mentionnent sans le gouverner : [`chambres-profil-derivees`](decisions/chambres-profil-derivees.md), [`consommateurs-chambres-migres`](decisions/consommateurs-chambres-migres.md), [`id-pivot-sans-prefixe`](decisions/id-pivot-sans-prefixe.md), [`licences`](decisions/licences.md), [`mandats-officiels-an-369`](decisions/mandats-officiels-an-369.md).

## `src/merge_profile.py`

73 décision(s) le gouvernent ; le module en cite 5.

| Décision | Nomme |
| --- | --- |
| [La fusion défaisait le marquage de la collecte : un run vert qui n'a rien basculé (#691, lot 3c)](decisions/amorcage-du-marquage-par-la-fusion-691.md) | `_acteur_du_socle`, `merge_raw_dirs` |
| [Un bloc structuré sans fond n'écrase plus un bloc collecté (#484) (2026-08-30)](decisions/bloc-sans-fond-484.md) | `BLOCS_PROTEGES_DU_VIDE`, `_merge_pivot_sources`, `_prefer_non_empty`, `_synchro_la_plus_recente`, `bloc_sans_fond`, `merge_raw_profile`, `preserver_collectes_non_vides` |
| [Le correctif de #540 validé en conditions réelles, et les deux budgets qu'il a périmés (#546) (2026-08-27)](decisions/budgets-extract-an-perimes-546.md) | `clean_stale_interventions` |
| [Un mandat dit quel référentiel a établi sa catégorie, et l'absence n'accuse personne (#718) (2026-09-03)](decisions/categorie-source-des-mandats-718.md) | `_mandat_key`, `_pivot_mandat_key`, `backfill_mandat_categorie_source` |
| [La chambre est un fait du mandat, pas du profil : `mandats[].chambre` estampillée à la collecte (#492) (2026-08-20)](decisions/chambre-par-mandat-electif.md) | `backfill_mandat_chambre`, `merge_lists_by_key`, `merge_raw_dirs` |
| [`chambres` au niveau profil : une liste dérivée, et `chambre` qui n'en est plus que le premier élément (#493) (2026-08-20)](decisions/chambres-profil-derivees.md) | `_prefer_non_empty`, `backfill_mandat_chambre`, `merge_lists_by_key`, `merge_pivot_profile` |
| [Une URL de source n'est pas un identifiant : la clé de fusion des interventions (#540) (2026-08-27)](decisions/cle-fusion-interventions-540.md) | `_intervention_key`, `_pivot_amendement_key`, `_pivot_intervention_key`, `_pivot_mandat_key`, `_pivot_texte_key`, `_pivot_vote_key`, `clean_stale_interventions`, `clean_stale_textes_portes`, `merge_lists_by_key` |
| [Une clé de fusion en `a or b` change d'identité quand `a` se remplit (#668) (2026-08-31)](decisions/cle-fusion-textes-portes-668.md) | `_dossier_key`, `_intervention_key`, `_pivot_amendement_key`, `_pivot_intervention_key`, `_pivot_texte_key`, `_pivot_vote_key`, `_repli_texte_key`, `clean_stale_interventions`, `clean_stale_textes_portes`, `merge_dossier_records`, `merge_pivot_profile` |
| [La collecte d'interventions des membres de roster est réduite au thème (#657) (2026-08-31)](decisions/collecte-interventions-reduite-au-theme-657.md) | `merge_pivot_profile` |
| [Ce que la normalisation a le droit de faire : la table de relations collecté → publié (#545) (2026-08-28)](decisions/collecte-vs-publie-545.md) | `_pivot_vote_key` |
| [Un index Syceron en cache est un parsage en cache, et l'existence n'y est pas la conformité (#719) (2026-09-02)](decisions/conformite-index-syceron-719.md) | `backfill_sujet_seance` |
| [Les consommateurs de `chambre` migrés vers `chambres`, et le garde-fou qui datera son retrait (#494) (2026-08-20)](decisions/consommateurs-chambres-migres.md) | `_prefer_non_empty`, `merge_pivot_profile`, `merge_raw_profile` |
| [Un constat « aucune donnée » ne survit pas à l'arrivée de données (#683, lot 3)](decisions/constats-parltrack-perimes-683.md) | `FAMILLES_WARNINGS`, `clean_stale_interventions`, `clean_stale_textes_portes`, `merge_pivot_profile`, `retirer_constats_parltrack_perimes`, `unir_warnings` |
| [Un artifact ne porte plus que les champs que son job a collectés (#997) (2026-09-19)](decisions/contribution-par-champs-997.md) | `CHAMPS_PROTEGES_DU_VIDE`, `merge_raw_dirs`, `preserver_collectes_non_vides` |
| [La corroboration porte sur les chambres publiées, pas sur la complétude des mandats — et la condition de retrait de `chambre` devient atteignable (#486) (2026-08-30)](decisions/corroboration-chambres-publiees-486.md) | `FAMILLES_WARNINGS`, `_prefer_non_empty`, `backfill_mandat_chambre`, `merge_pivot_profile` |
| [La couverture européenne n'atteignait pas la fiche (#683, lot 4)](decisions/couverture-europeenne-tranchee-683.md) | `retirer_constats_parltrack_perimes` |
| [Ce qu'une liste vide veut dire : les quatre états de couverture (#539) (2026-08-28)](decisions/couverture-listes-539.md) | `_prefer_non_empty` |
| [La couverture se remplace à la maille où #539 la publie, et un cas non tranchable se déclare (#602) (2026-08-30)](decisions/couverture-remplacee-par-liste-602.md) | `FAMILLES_WARNINGS`, `_prefer_non_empty`, `fusionner_couverture` |
| [Un créneau de séance n'est pas un sujet, et le discriminant reste structurel (#710, 02/09/2026)](decisions/creneau-de-seance-nest-pas-un-sujet-710.md) | `backfill_mandat_chambre`, `backfill_sujet_seance`, `backfill_vote_qualification`, `merge_pivot_profile` |
| [Une question au gouvernement est datée par la parution de son compte rendu au JO (#1044) (2026-09-22)](decisions/date-des-questions-au-gouvernement-1044.md) | `normaliser_dates_interventions` |
| [882 interventions portaient une date que tout filtre écartait en silence (#1044) (2026-09-20)](decisions/dates-des-questions-en-iso-1044.md) | `merge_lists_by_key`, `normaliser_dates_interventions` |
| [`meta.warnings[]` déclare son destinataire, dans un jumeau typé et aligné (#642) (2026-08-31)](decisions/destinataire-avertissements-642.md) | `_prune_stale_warnings`, `unir_warnings` |
| [Le passé sénatorial est un fait de carrière, pas une donnée d'activité : bicaméral pour les candidats seulement (#488) (2026-08-20)](decisions/deux-chambres-interrogees.md) | `_prefer_non_empty`, `merge_raw_profile` |
| [Un amendement retrouve son dossier, et la clé qu'on lui avait retirée (#639, rang 3)](decisions/dossier-des-amendements-639.md) | `_amendement_key` |
| [Un texte européen est identifié par son document, pas par son titre (#901) (2026-09-16)](decisions/doublons-textes-europeens-cle-doceo-901.md) | `_pivot_texte_key`, `merge_dossier_records` |
| [La parole des membres de groupe et de gouvernement publie un extrait de 280 caractères (#1029) (2026-09-22)](decisions/extrait-de-la-parole-des-rosters-1029.md) | `aligner_collecte_reduite`, `promouvoir_forme_complete` |
| [Borner l'historique de données : ce que ça rend vraiment, et quand (#434) (2026-08-20)](decisions/fenetre-historique-donnees.md) | `merge_raw_profile` |
| [Un filtre de publication posé avant la fusion ne filtre rien (#641, réouverture) (2026-08-31)](decisions/filtre-publication-apres-fusion-641.md) | `FILTRES_PUBLICATION_IDENTITE`, `_composer_identite`, `bloc_sans_fond`, `deriver_provenance_champs`, `filtrer_identite_publiee`, `merge_pivot_profile` |
| [Extension de la stabilité des horodatages aux profils groupe/gouvernement/parti (#343, complet) (2026-08-17)](decisions/freshness-timestamps-groupes-gouvernements-partis.md) | `load_existing_document`, `preserve_stable_freshness_timestamps` |
| [Un champ qu'une contribution ne porte pas n'est plus effacé (#997) (2026-09-19)](decisions/fusion-conserve-les-champs-absents-997.md) | `CHAMPS_PROTEGES_DU_VIDE`, `_prefer_non_empty`, `merge_raw_profile` |
| [Un dossier déjà collecté n'apprenait plus rien : au brut aussi, la neuve gagne (#997) (2026-09-18)](decisions/fusion-dossiers-brut-la-neuve-gagne-997.md) | `CHAMPS_PROTEGES_DU_VIDE`, `_dossier_key`, `backfill_dossier_nature`, `backfill_sort_texte_porte`, `merge_dossier_records`, `merge_lists_by_key`, `merge_raw_profile` |
| [Profils de gouvernement : ne jamais réécrire sur une collecte incomplète, et cache dossiers dédié (#427) (2026-08-18)](decisions/gouvernement-textes-non-ecrasement.md) | `preserve_stable_freshness_timestamps` |
| [L'`id` d'un profil pivot est le slug : le préfixe de provenance était instable (#487) (2026-08-20)](decisions/id-pivot-sans-prefixe.md) | `merge_pivot_profile`, `merge_raw_profile` |
| [Index amendements shardé par acteur (#392) (2026-08-17)](decisions/index-amendements-sharde-par-acteur.md) | `_amendement_key` |
| [`extract-senat` ne collecte plus d'interventions : la collecte n'en retenait aucune, par construction (#501) (2026-08-20)](decisions/interventions-senat-501.md) | `preserver_collectes_non_vides` |
| [Le versant AN passe en Licence Ouverte, et `meta.licence_donnees` devient un champ dérivé (#530, lot 6 de l'épic « une seule source AN ») (2026-08-27)](decisions/licence-lot-6-530.md) | `_merge_pivot_sources`, `merge_pivot_profile` |
| [Chaque prise de parole porte l'ancre de sa page de séance à l'AN (#1087) (2026-09-22)](decisions/lien-vers-la-prise-de-parole-1087.md) | `reporter_id_syceron` |
| [Un profil publie tous ses mandats de député, et le compteur devient un témoin de couverture (#640) (2026-08-31)](decisions/mandats-electifs-liste-complete-640.md) | `_pivot_mandat_key` |
| [Le référentiel type l'organe, il n'y a rien à interpréter (#730) (2026-09-04)](decisions/mandats-gouvernementaux-en-commission-730.md) | `merge_pivot_profile` |
| [`merge-and-pivot` : garde-fou #390 hors `main`, entrées de configuration, budget de temps mur, permissions (#413) (2026-08-18)](decisions/merge-and-pivot-budget-permissions-413.md) | `merge_pivot_profile` |
| [`overwrite_profiles` : écraser les profils sans purger le cache (2026-08-19)](decisions/overwrite-profiles-sans-purge-cache.md) | `merge_lists_by_key` |
| [Le `label` d'un mandat `MINISTERE` ne dit pas si c'est un maroquin (#474) (2026-08-20)](decisions/parlementaire-en-mission-nest-pas-ministre.md) | `preserve_stable_freshness_timestamps` |
| [Le seuil de blob sort du critère de sortie, et les profils bruts se partitionnent par législature (#580) (2026-08-29)](decisions/partition-profils-legislature-580.md) | `merge_raw_dirs` |
| [Un champ d'identité publié ne meurt plus sans un run à perte déclarée (#601) (2026-08-30)](decisions/permanence-champs-identite-601.md) | `fusionner_identite` |
| [`genere_le`/`synchro_le` des pivots ne doivent avancer que si le contenu change réellement (#343) (2026-08-16)](decisions/pivot-freshness-timestamps-stables.md) | `_pivot_content_fingerprint`, `merge_pivot_profile`, `preserve_stable_freshness_timestamps` |
| [Un fichier de progression dans un répertoire de données (#518, troisième incident) (2026-08-24)](decisions/point-de-sauvegarde-dans-les-profils-518.md) | `merge_raw_dirs` |
| [Profils écrits en JSON compact, groupes et gouvernements indentés (#433) (2026-08-18)](decisions/profils-json-compact.md) | `_pivot_content_fingerprint`, `preserve_stable_freshness_timestamps` |
| [Quelle source a rempli quel champ, et quand — un bloc à côté d'`identite` (#603) (2026-08-30)](decisions/provenance-par-champ-603.md) | `_accorder_hatvp`, `_composer_identite`, `_merge_pivot_sources`, `fusionner_identite` |
| [Provenance des profils pivot : candidat_declare vs roster_groupe (2026-08-10)](decisions/provenance-pivot.md) | `_prefer_non_empty`, `merge_pivot_profile` |
| [Un préfixe de flux est valide, un préfixe de profil est faux (#460) (2026-08-20)](decisions/publication-dun-job-annule.md) | `merge_raw_profile` |
| [Un artifact = la contribution d'un job : ce qu'on publie décide de ce qu'on peut corriger (#450) (2026-08-19)](decisions/publication-scopee-artifacts.md) | `merge_raw_dirs` |
| [185 doublons hérités retirés : l'outil existait, il n'avait jamais été relancé (#729) (2026-09-04)](decisions/purge-doublons-herites-729.md) | `merge_pivot_profile` |
| [La qualification d'un scrutin se perdait entre la collecte et le profil brut (#639, rang 1) (2026-08-31)](decisions/qualification-perdue-a-la-fusion-639.md) | `CHAMPS_QUALIFICATION_VOTE`, `_pivot_vote_key`, `_vote_key`, `backfill_mandat_chambre`, `backfill_vote_qualification`, `merge_lists_by_key`, `merge_raw_profile` |
| [Un projet de loi porté au nom du Gouvernement n'est pas une production personnelle (#689) (2026-09-01)](decisions/qualification-textes-portes-689.md) | `_dossier_key`, `backfill_dossier_nature`, `backfill_mandat_chambre`, `backfill_vote_qualification`, `merge_raw_profile` |
| [Une question au gouvernement : un acte, et ses tours de parole reliés à lui (#1094) (2026-09-22)](decisions/question-au-gouvernement-acte-et-parole-1094.md) | `backfill_sujet_question`, `merge_pivot_profile` |
| [Une somme de longueurs suppose que chaque entrée collectée est distincte, et le portail européen le dément (#888) (2026-09-13)](decisions/reduction-nommee-collecte-vs-publie-888.md) | `_repli_texte_key` |
| [Le `texte_vise` fautif se reprend depuis l'archive figée, pas par une fusion plus permissive (#696, 01/09/2026)](decisions/report-texte-vise-source-696.md) | `backfill_dossier_nature` |
| [Résilience de `generate-data.yml` face aux `shutdown signal` runner : continue-on-error généralisé, watchdog réseau, retry générique sur `_get_payload`, retry `retry-generate-data.yml` non-régressif, et appels NosDéputés morts pour les députés (dossiers, votes) (2026-08-16)](decisions/resilience-generate-data-shutdown-signal.md) | `merge_raw_dirs` |
| [Retrait de `fetch_activity_synthesis` (#356) (2026-08-16)](decisions/retrait-fetch-activity-synthesis.md) | `merge_raw_profile` |
| [Un marqueur de provenance sans donnée derrière lui n'est plus une traçabilité, c'est une inexactitude (#890) (2026-09-13)](decisions/retrait-marqueur-regards-citoyens-deputes-890.md) | `_merge_pivot_sources` |
| [NosDéputés sort du pipeline (#529, lot 5 de l'épic « une seule source AN ») (2026-08-27)](decisions/retrait-nosdeputes-529.md) | `merge_lists_by_key` |
| [Le Sénat sort du périmètre, et le job qui concluait vert sans rien produire est retiré (#528, lot 3 de l'épic « une seule source AN ») (2026-08-26)](decisions/retrait-senat-528.md) | `_merge_pivot_sources`, `merge_lists_by_key` |
| [Revue transversale des workflows GitHub Actions : ce qui est gardé, ce qui est corrigé (#342) (2026-08-18)](decisions/revue-workflows-ci-342.md) | `merge_pivot_profile` |
| [Le groupe européen dit son sigle et ce que la source en dit, sans changer de catégorie (#863) (2026-09-12)](decisions/sigle-groupe-europeen-863.md) | `_mandat_key`, `backfill_mandat_organe_source` |
| [Un texte porté dit ce qu'il est devenu, et son sort ne se déduit jamais de son stade (#743) (2026-09-06)](decisions/sort-des-textes-portes-743.md) | `_dossier_key`, `merge_dossier_records`, `merge_lists_by_key` |
| [Le sujet nettoyé d'une question européenne n'atteignait pas l'entrée déjà publiée (#980) (2026-09-16)](decisions/sujet-europeen-sans-boutons-a-la-fusion-980.md) | `backfill_sujet_europeen`, `backfill_sujet_seance`, `merge_dossier_records`, `merge_lists_by_key`, `merge_pivot_profile` |
| [`synchro_sources` publie la dernière récupération réussie, et pas son origine (#600) (2026-08-30)](decisions/synchro-sources-derniere-recuperation-600.md) | `merge_raw_profile` |
| [Régénérer l'existant : `--refresh-existing`, l'inverse de `--skip-existing` (#445) (2026-08-19)](decisions/telechargement-an-trois-modes-defaillance.md) | `merge_raw_dirs` |
| [Le lecteur accepte une tranche dérivée, et le silence reste une panne (#691, lot 2)](decisions/tranches-derivees-lecteur-691.md) | `merge_dossier_records` |
| [Une panne de transport n'est pas une source absente (#786)](decisions/transport-artifacts-panne-ou-absence-786.md) | `merge_raw_dirs` |
| [L'union des avertissements peut ressusciter un démenti, et deux familles Syceron s'éteignent (#600) (2026-08-30)](decisions/union-warnings-extinction-600.md) | `_defaut_collecte_dementi_par_les_donnees`, `merge_pivot_profile`, `merge_raw_profile` |
| [Vérification de bout en bout des législatures figées 15/16 (#273, clôture de l'epic #268) (2026-08-17)](decisions/verification-bout-en-bout-legislatures-figees.md) | `_amendement_key`, `_prune_stale_warnings` |
| [Votes : agrégation des législatures 14 à 17, index dédupliqué, 14/15/16 figées (#403) (2026-08-18)](decisions/votes-multi-legislature.md) | `merge_lists_by_key` |

Le mentionnent sans le gouverner : [`bascule-identite-an-primaire`](decisions/bascule-identite-an-primaire.md), [`deux-axes-formulaire-578`](decisions/deux-axes-formulaire-578.md), [`investigation-sources-ue`](decisions/investigation-sources-ue.md), [`marquage-tranches-derivees-691`](decisions/marquage-tranches-derivees-691.md), [`profession-code-nomenclature-641`](decisions/profession-code-nomenclature-641.md), [`reconstruction-tranches-depuis-archive-691`](decisions/reconstruction-tranches-depuis-archive-691.md), [`restauration-interventions`](decisions/restauration-interventions.md).

## `src/normalize_europarl.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Une somme de longueurs suppose que chaque entrée collectée est distincte, et le portail européen le dément (#888) (2026-09-13)](decisions/reduction-nommee-collecte-vs-publie-888.md) | `dedupliquer_appartenances` |

Le mentionnent sans le gouverner : [`chambre-par-mandat-electif`](decisions/chambre-par-mandat-electif.md), [`chambres-profil-derivees`](decisions/chambres-profil-derivees.md), [`collecte-non-publiee`](decisions/collecte-non-publiee.md), [`consommateurs-chambres-migres`](decisions/consommateurs-chambres-migres.md), [`deux-chambres-interrogees`](decisions/deux-chambres-interrogees.md), [`doublons-europarl-729`](decisions/doublons-europarl-729.md), [`id-pivot-sans-prefixe`](decisions/id-pivot-sans-prefixe.md), [`identite-profils-539`](decisions/identite-profils-539.md), [`licence-lot-6-530`](decisions/licence-lot-6-530.md), [`pivot-freshness-timestamps-stables`](decisions/pivot-freshness-timestamps-stables.md), [`provenance-par-champ-603`](decisions/provenance-par-champ-603.md), [`provenance-pivot`](decisions/provenance-pivot.md), [`retrait-nosdeputes-529`](decisions/retrait-nosdeputes-529.md).

## `src/normalize_parltrack_dumps.py`

15 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [Une clé de déduplication ne doit dépendre d'aucun champ qui apparaît (#827)](decisions/cle-de-fusion-qui-depend-dun-champ-volatil-827.md) | `enrich_pivot_with_parltrack` |
| [`meta.warnings[]` déclare son destinataire, dans un jumeau typé et aligné (#642) (2026-08-31)](decisions/destinataire-avertissements-642.md) | `WARNING_PREFIX_PARLTRACK_AUCUNE_DONNEE` |
| [Corriger là où un champ est jeté ne suffit pas : il faut trouver tous les endroits où l'objet est fabriqué (#901) (2026-09-14)](decisions/deux-fabriques-textes-portes-europeens-901.md) | `_make_texte_porte_activite`, `enrich_pivot_with_parltrack` |
| [L'`id` d'un profil pivot est le slug : le préfixe de provenance était instable (#487) (2026-08-20)](decisions/id-pivot-sans-prefixe.md) | `enrich_pivot_with_parltrack` |
| [Ce qui manquait aux amendements européens n'était ni une collecte ni une lecture, mais un référentiel (#901) (2026-09-14)](decisions/index-dossiers-europeens-901.md) | `STADE_UE_PAR_LIBELLE_SOURCE` |
| [L'index des scrutins européens publie les effectifs, jamais le sort (#901) (2026-09-14)](decisions/index-scrutins-europeens-901.md) | `_porte_sur_ensemble` |
| [Le lecteur des dumps ParlTrack n'avait jamais lu une ligne (#683, lot 1)](decisions/lecture-dumps-parltrack-683.md) | `_role_signataire` |
| [Le versant AN passe en Licence Ouverte, et `meta.licence_donnees` devient un champ dérivé (#530, lot 6 de l'épic « une seule source AN ») (2026-08-27)](decisions/licence-lot-6-530.md) | `enrich_pivot_with_parltrack` |
| [La projection d'un index est une fabrique, et elle jetait la référence de dossier (#901) (2026-09-14)](decisions/projection-index-activites-jette-le-dossier-901.md) | `_make_texte_porte`, `_make_texte_porte_activite` |
| [Un profil de roster ne porte pas une liste que sa propre collecte déclare écartée — purge des 49 `textes_portes` résiduels (#747)](decisions/purge-textes-portes-roster-747.md) | `_make_texte_porte` |
| [L'européen entre dans les listes que la fiche a déjà (#683, lot 2)](decisions/stockage-europeen-dans-les-listes-existantes-683.md) | `NATURES_VOTE_SUR_ENSEMBLE` |
| [Le sujet nettoyé d'une question européenne n'atteignait pas l'entrée déjà publiée (#980) (2026-09-16)](decisions/sujet-europeen-sans-boutons-a-la-fusion-980.md) | `_make_intervention`, `enrich_pivot_with_parltrack` |
| [L'empreinte thématique d'une fiche est celle de sa législature (#825)](decisions/tags-agreges-dans-la-periode-825.md) | `_make_intervention` |
| [Le titre français cherchait sa référence là où elle n'est jamais (#901) (2026-09-16)](decisions/titre-francais-lu-dans-source-url-901.md) | `_titre_publie` |
| [L'adresse est dérivée, l'existence est prouvée (#827)](decisions/urls-explications-vote-europeennes-827.md) | `_make_intervention` |

Le mentionnent sans le gouverner : [`investigation-sources-ue`](decisions/investigation-sources-ue.md).

## `src/normalize_profil.py`

9 décision(s) le gouvernent ; le module en cite 4.

| Décision | Nomme |
| --- | --- |
| [Trois absences publiées comme des faits (#556, #558, #560) (2026-08-29)](decisions/absences-publiees-comme-faits-556-558-560.md) | `_uri_hatvp_publiable` |
| [Une URL de source n'est pas un identifiant : la clé de fusion des interventions (#540) (2026-08-27)](decisions/cle-fusion-interventions-540.md) | `_normalize_intervention` |
| [Une clé de fusion en `a or b` change d'identité quand `a` se remplit (#668) (2026-08-31)](decisions/cle-fusion-textes-portes-668.md) | `_normalize_texte_porte` |
| [Un filtre de publication posé avant la fusion ne filtre rien (#641, réouverture) (2026-08-31)](decisions/filtre-publication-apres-fusion-641.md) | `_profession_publiable` |
| [Normaliser les amendements : le coût n'est pas l'amendement, c'est sa liste de cosignataires (#431) (2026-08-19)](decisions/normalisation-amendements.md) | `_normalize_amendement` |
| [Un code de nomenclature n'est pas une profession, et « sans activité professionnelle » n'en est pas une (#641) (2026-08-31)](decisions/profession-code-nomenclature-641.md) | `_profession_publiable`, `_uri_hatvp_publiable` |
| [La qualification d'un scrutin et la clé de son dossier étaient lues puis jetées (#639, rangs 1 et 2)](decisions/qualification-scrutins-et-cle-dossier-639.md) | `_normalize_texte_porte` |
| [Restaurer 789 interventions sans revenir sur le reste du schéma (#460) (2026-08-19)](decisions/restauration-interventions.md) | `_normalize_intervention` |
| [Un marqueur de provenance sans donnée derrière lui n'est plus une traçabilité, c'est une inexactitude (#890) (2026-09-13)](decisions/retrait-marqueur-regards-citoyens-deputes-890.md) | `_SOURCE_TYPE_PROFIL_FR` |

Le mentionnent sans le gouverner : [`civilite-et-pcs-insee-659`](decisions/civilite-et-pcs-insee-659.md), [`collecte-interventions-reduite-au-theme-657`](decisions/collecte-interventions-reduite-au-theme-657.md), [`collecte-vs-publie-545`](decisions/collecte-vs-publie-545.md), [`corroboration-chambres-publiees-486`](decisions/corroboration-chambres-publiees-486.md), [`creneau-de-seance-nest-pas-un-sujet-710`](decisions/creneau-de-seance-nest-pas-un-sujet-710.md), [`identite-profils-539`](decisions/identite-profils-539.md), [`licence-lot-6-530`](decisions/licence-lot-6-530.md), [`provenance-par-champ-603`](decisions/provenance-par-champ-603.md), [`purge-textes-portes-roster-747`](decisions/purge-textes-portes-roster-747.md), [`qualification-perdue-a-la-fusion-639`](decisions/qualification-perdue-a-la-fusion-639.md), [`qualification-textes-portes-689`](decisions/qualification-textes-portes-689.md), [`retrait-nosdeputes-529`](decisions/retrait-nosdeputes-529.md).

## `src/normalize_senat.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Un libellé corrigé ne remplace pas l'ancien, il s'ajoute — et le dernier marqueur part enfin (#908, suite de #912) (2026-09-14)](decisions/fusion-additive-et-libelle-corrige-912.md) | `normalize_mandats` |

## `src/parltrack_dumps.py`

8 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [Corriger là où un champ est jeté ne suffit pas : il faut trouver tous les endroits où l'objet est fabriqué (#901) (2026-09-14)](decisions/deux-fabriques-textes-portes-europeens-901.md) | `build_dossiers_index`, `build_stades_dossiers_index` |
| [Le lecteur des dumps ParlTrack n'avait jamais lu une ligne (#683, lot 1)](decisions/lecture-dumps-parltrack-683.md) | `DUMPS_LUS`, `DumpParltrackIllisible`, `_lire_dump`, `_perimetre`, `definir_perimetre_meps`, `iter_dump_zst` |
| [La projection d'un index est une fabrique, et elle jetait la référence de dossier (#901) (2026-09-14)](decisions/projection-index-activites-jette-le-dossier-901.md) | `VERSION_SCHEMA_INDEX`, `build_activities_index` |
| [Un profil de roster ne porte pas une liste que sa propre collecte déclare écartée — purge des 49 `textes_portes` résiduels (#747)](decisions/purge-textes-portes-roster-747.md) | `get_dossiers_for_mep` |
| [Le stade d'un dossier européen se publie dans sa propre nomenclature, jamais traduit en stade français (#901) (2026-09-13)](decisions/stade-procedural-europeen-901.md) | `VERSION_SCHEMA_INDEX`, `_empreinte_perimetre`, `build_dossiers_index` |
| [L'européen entre dans les listes que la fiche a déjà (#683, lot 2)](decisions/stockage-europeen-dans-les-listes-existantes-683.md) | `definir_perimetre_meps` |
| [Le sujet nettoyé d'une question européenne n'atteignait pas l'entrée déjà publiée (#980) (2026-09-16)](decisions/sujet-europeen-sans-boutons-a-la-fusion-980.md) | `build_activities_index` |
| [Un titre européen perd ses boutons de téléchargement, et rien d'autre (#901) (2026-09-15)](decisions/titres-europeens-sans-boutons-901.md) | `VERSION_SCHEMA_INDEX`, `build_activities_index` |

Le mentionnent sans le gouverner : [`investigation-sources-ue`](decisions/investigation-sources-ue.md), [`mandats-officiels-an-369`](decisions/mandats-officiels-an-369.md).

## `src/parse_syceron.py`

4 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Un créneau de séance n'est pas un sujet, et le discriminant reste structurel (#710, 02/09/2026)](decisions/creneau-de-seance-nest-pas-un-sujet-710.md) | `_CODE_GRAMMAIRE_QUESTION`, `_CODE_GRAMMAIRE_SUJET`, `_TYPE_DETAIL_MAP`, `_TYPE_DETAIL_PAR_CODE_GRAMMAIRE`, `_creneaux_de_questions`, `_iter_paragraphes`, `_point_porteur_du_sujet` |
| [« Ce qu'il a dit » publie les mots, et les range par période politique (#328) (2026-09-09)](decisions/paroles-par-periode-328.md) | `_infer_format` |
| [Syceron publie l'identifiant d'orateur NU, et n'a donc jamais rien indexé (#510) (2026-08-20)](decisions/syceron-acteur-ref-nu-510.md) | `_parse_interventions`, `_parse_orateur` |
| [Suite du 26/08/2026 : les trois archives vérifiées, les deux défauts de parseur corrigés](decisions/syceron-archives-verifiees-parseur-510.md) | `_parse_orateur` |

Le mentionnent sans le gouverner : [`cle-fusion-interventions-540`](decisions/cle-fusion-interventions-540.md), [`conformite-index-syceron-719`](decisions/conformite-index-syceron-719.md), [`lien-vers-la-prise-de-parole-1087`](decisions/lien-vers-la-prise-de-parole-1087.md), [`syceron`](decisions/syceron.md).

## `src/perimetre_candidats.py`

4 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Une candidature déclinée n'a plus de fiche dans l'interface (#761)](decisions/fiches-masquees-candidatures-declinees-761.md) | `STATUTS_GELES` |
| [Un garde-fou posé sur `builtins.open` ne voit pas `pathlib` (#791) (2026-09-10)](decisions/lectures-du-depot-dans-les-tests-791.md) | `RESOLUTIONS_PAR_DEFAUT`, `_MEMO_RESOLUTIONS`, `declare_hors_an_par_identifiant` |
| [La seconde déclaration lisait un champ que le corpus ne porte pas (#788)](decisions/nom-des-resolutions-vient-de-lappelant-788.md) | `declare_hors_an_par_identifiant` |
| [Une candidature déclinée sort du périmètre de collecte, sa fiche reste publiée (#760)](decisions/perimetre-collecte-candidatures-declinees-760.md) | `STATUTS_GELES` |

## `src/population_profils.py`

4 décision(s) le gouvernent ; le module en cite 2.

| Décision | Nomme |
| --- | --- |
| [Le sédiment se compte avant de se juger : sept familles, deux couches, aucun retrait (#839, lot A) (2026-09-12)](decisions/audit-sediment-inventaire-839.md) | `provenance_du_profil` |
| [« 32 candidats déclarés » en comptait 30 : un libellé de provenance affirmait un statut (#873) (2026-09-12)](decisions/libelle-population-candidats-873.md) | `LIBELLE_CANDIDATS` |
| [Les deux populations de `pivot_data/profiles/` sont portées par les outils, pas par une consigne (#630, 2026-08-30)](decisions/populations-profils-portees-par-les-outils-630.md) | `Ventilation`, `ventiler_chemins` |
| [Les membres de gouvernement deviennent une population, et leur collecte part (#996, lot 3) (2026-09-18)](decisions/provenance-roster-gouvernement-996.md) | `PROVENANCES_ROSTER` |

Le mentionnent sans le gouverner : [`agents-sans-comptes-volatils`](decisions/agents-sans-comptes-volatils.md).

## `src/profil_brut.py`

8 décision(s) le gouvernent ; le module en cite 4.

| Décision | Nomme |
| --- | --- |
| [La fusion défaisait le marquage de la collecte : un run vert qui n'a rien basculé (#691, lot 3c)](decisions/amorcage-du-marquage-par-la-fusion-691.md) | `partitionner` |
| [Un audit lit le corpus par projection, et son plafond de mémoire est dans un test (#628, 2026-08-30)](decisions/audit-599-projection-blocs-lus-628.md) | `charger_socle` |
| [« Collecté = publié » compte une tranche dérivée dans l'archive (#691, lot 3a)](decisions/audit-compte-les-tranches-derivees-691.md) | `partitionner`, `recomposer` |
| [Un artifact ne porte plus que les champs que son job a collectés (#997) (2026-09-19)](decisions/contribution-par-champs-997.md) | `charger_profil_brut`, `projeter_contribution` |
| [L'écriture marque les tranches closes, et le `nombre` vient de l'archive (#691, lot 3b)](decisions/marquage-tranches-derivees-691.md) | `ecrire_profil_brut`, `partitionner`, `recomposer` |
| [Le seuil de blob sort du critère de sortie, et les profils bruts se partitionnent par législature (#580) (2026-08-29)](decisions/partition-profils-legislature-580.md) | `PartitionIllisible`, `charger_profil_brut`, `ecrire_profil_brut`, `partitionner`, `recomposer` |
| [Un shard d'extraction ne matérialise que son propre profil (#674) — 31/08/2026](decisions/sparse-checkout-extract-an-674.md) | `slugs_du_repertoire` |
| [Le lecteur accepte une tranche dérivée, et le silence reste une panne (#691, lot 2)](decisions/tranches-derivees-lecteur-691.md) | `PartitionIllisible`, `_nom_declaree`, `charger_tranches`, `iter_amendements_du_profil`, `partitionner`, `recomposer` |

Le mentionnent sans le gouverner : [`absences-publiees-comme-faits-556-558-560`](decisions/absences-publiees-comme-faits-556-558-560.md).

## `src/purge_interventions_heritees.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Le nettoyage fait, la clause ODbL ne tiendrait plus que par un marqueur, sur 475 profils (#839, lot C) (2026-09-12)](decisions/residus-source-retiree-839.md) | `purge_profil` |

Le mentionnent sans le gouverner : [`sediment-nosdeputes-839`](decisions/sediment-nosdeputes-839.md).

## `src/purge_mandats_doublons_europarl.py`

Le mentionnent sans le gouverner : [`doublons-europarl-729`](decisions/doublons-europarl-729.md).

## `src/purge_mandats_dupliques.py`

3 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [185 doublons hérités retirés : l'outil existait, il n'avait jamais été relancé (#729) (2026-09-04)](decisions/purge-doublons-herites-729.md) | `_normalize_label` |
| [Purge des mandats hérités dupliqués : appariement prudent (#387) (2026-08-17)](decisions/purge-mandats-dupliques-prudence.md) | `_PREFIXES_NATURE` |
| [280 des 406 mandats sans estampille sont portés par un référentiel vivant, et aucun n'est introuvable (#839, lot B) (2026-09-12)](decisions/reproductibilite-mandats-sans-estampille-839.md) | `_normalize_label` |

Le mentionnent sans le gouverner : [`categorie-source-des-mandats-718`](decisions/categorie-source-des-mandats-718.md), [`collecte-vs-publie-545`](decisions/collecte-vs-publie-545.md), [`partition-profils-legislature-580`](decisions/partition-profils-legislature-580.md), [`point-de-sauvegarde-dans-les-profils-518`](decisions/point-de-sauvegarde-dans-les-profils-518.md), [`purge-mandats-nosdeputes-718`](decisions/purge-mandats-nosdeputes-718.md).

## `src/purge_mandats_nosdeputes.py`

Le mentionnent sans le gouverner : [`purge-mandats-nosdeputes-718`](decisions/purge-mandats-nosdeputes-718.md).

## `src/rafraichir_dossiers_actifs.py`

Le mentionnent sans le gouverner : [`fraicheur-dossiers-762`](decisions/fraicheur-dossiers-762.md).

## `src/reprise_mandats_gouvernementaux.py`

Le mentionnent sans le gouverner : [`purge-doublons-herites-729`](decisions/purge-doublons-herites-729.md).

## `src/retrait_heritage_senat.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Le dernier marqueur Regards Citoyens part quand il ne couvre plus rien, et pas avant (#908) (2026-09-13)](decisions/retrait-residus-senat-908.md) | `mandats_electifs_remplaces` |

## `src/rne_opendata.py`

3 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Un artifact ne porte plus que les champs que son job a collectés (#997) (2026-09-19)](decisions/contribution-par-champs-997.md) | `mandats_locaux` |
| [Un champ qu'une contribution ne porte pas n'est plus effacé (#997) (2026-09-19)](decisions/fusion-conserve-les-champs-absents-997.md) | `mandats_locaux` |
| [Le fichier des sortants a vieilli ses élus d'un siècle, et cinq mandats ont disparu (#922) (2026-09-16)](decisions/sortants-annee-decalee-922.md) | `PAGES_MAX` |

Le mentionnent sans le gouverner : [`collecte-mandats-locaux-rne-922`](decisions/collecte-mandats-locaux-rne-922.md).

## `src/schema_gouvernement.py`

11 décision(s) le gouvernent ; le module en cite 1.

| Décision | Nomme |
| --- | --- |
| [Les agrégats publiés entrent dans le contrôle de perte, et l'ordre de grandeur reste hors contrat (#649) (2026-08-31)](decisions/agregats-publies-controle-perte-649.md) | `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL`, `validate_profil_gouvernement` |
| [`gouvernement_profile.py` : rattachement des textes par `date_depot`, exclusion silencieuse des dossiers non classifiables (#211) (2026-08-14)](decisions/gouvernement-profile-rattachement.md) | `KNOWN_CHAMBRES_DEPOT_TEXTE`, `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL` |
| [`gouvernement_textes` : 3 `fam_code` manquants excluaient 42 % des textes ; `adopte_cmp` ajouté à la nomenclature (#397) (2026-08-18)](decisions/gouvernement-textes-fam-codes-manquants.md) | `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL`, `make_empty_comptages_statuts` |
| [Profils de gouvernement : le lien ministre → texte (#435) (2026-08-18)](decisions/gouvernement-textes-initiateurs.md) | `REQUIRED_TEXTE_KEYS`, `validate_profil_gouvernement` |
| [`gouvernement_textes.py` : filtre de statut par décision de séance, pas par `codeActe`/`fam_code` seul (#210) (2026-08-14)](decisions/gouvernement-textes-statut.md) | `validate_profil_gouvernement` |
| [`gouvernement_textes.py` : filtre de statut par décision de séance, pas par `codeActe`/`fam_code` seul (#210) (2026-08-14)](decisions/gouvernement-textes-statut-210-version-initiale.md) | `validate_profil_gouvernement` |
| [`KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL` : ajout de `rejete_49_3` (#208, réouverte) (2026-08-14)](decisions/gouvernement-textes-statut-49-3-rejete.md) | `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL`, `validate_profil_gouvernement` |
| [La qualification d'un scrutin et la clé de son dossier étaient lues puis jetées (#639, rangs 1 et 2)](decisions/qualification-scrutins-et-cle-dossier-639.md) | `REQUIRED_TEXTE_KEYS` |
| [`check_quality_gate.py` : section gouvernements (§5), couverture ministérielle proxy par `portefeuille` (#212) (2026-08-14)](decisions/quality-gate-gouvernements.md) | `validate_profil_gouvernement` |
| [Le sort d'un texte entre dans la fiche, à côté de son stade et jamais à sa place (#743 dans #328), 07/09/2026](decisions/sort-des-textes-dans-la-fiche-328.md) | `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL` |
| [Un texte porté dit ce qu'il est devenu, et son sort ne se déduit jamais de son stade (#743) (2026-09-06)](decisions/sort-des-textes-portes-743.md) | `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL` |

Le mentionnent sans le gouverner : [`agregat-parole-gouvernement-1020`](decisions/agregat-parole-gouvernement-1020.md), [`deduplication-entrees-membres`](decisions/deduplication-entrees-membres.md), [`gouvernement-doc-cloture`](decisions/gouvernement-doc-cloture.md), [`gouvernement-premier-ministre-portefeuille`](decisions/gouvernement-premier-ministre-portefeuille.md), [`hors-perimetre`](decisions/hors-perimetre.md), [`pivot-freshness-timestamps-stables`](decisions/pivot-freshness-timestamps-stables.md), [`web-v3-ui`](decisions/web-v3-ui.md).

## `src/schema_groupe.py`

7 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [Les agrégats publiés entrent dans le contrôle de perte, et l'ordre de grandeur reste hors contrat (#649) (2026-08-31)](decisions/agregats-publies-controle-perte-649.md) | `make_empty_amendements_stats` |
| [Tous les comptes d'une fiche de groupe se rapportent à une date, et elle est publiée (#653) (2026-08-31)](decisions/date-de-reference-des-comptes-de-groupe-653.md) | `validate_profil_groupe` |
| [L'effectif d'un groupe dans le temps : `min_historique` et `max_historique` portent leur date (#702) — 01/09/2026](decisions/effectif-du-groupe-dans-le-temps-702.md) | `valeur_borne_effectif`, `validate_profil_groupe` |
| [Les 5 groupes de la XVIIe entrent dans `groupes[]`, et leur succession est déclarée comme une relecture (#700) (2026-09-01)](decisions/fiches-groupe-17e-legislature-700.md) | `ETABLISSEMENTS_SUCCESSION`, `POSITIONS_POLITIQUES_GROUPE`, `_valider_succede_a` |
| [L'origine de la date de référence nomme le critère, plus un événement (#808)](decisions/origine-date-reference-nomme-le-critere-808.md) | `ORIGINES_DATE_REFERENCE`, `ORIGINE_DATE_REFERENCE_CLOTURE`, `ORIGINE_DATE_REFERENCE_CLOTURE_HERITEE` |
| [L'appartenance publiée cesse d'être une enveloppe (#809)](decisions/periodes-appartenance-809.md) | `validate_profil_groupe` |
| [La position politique d'un groupe est celle que l'Assemblée déclare, lue dans une table committée (#686) (2026-09-01)](decisions/position-politique-groupes-686.md) | `POSITIONS_POLITIQUES_GROUPE`, `resumer_position_politique` |

Le mentionnent sans le gouverner : [`audit-champs-deplaces-726`](decisions/audit-champs-deplaces-726.md), [`audit-plages-temporelles`](decisions/audit-plages-temporelles.md), [`consommateurs-chambres-migres`](decisions/consommateurs-chambres-migres.md), [`dates-appartenance-groupe-653`](decisions/dates-appartenance-groupe-653.md), [`pivot-freshness-timestamps-stables`](decisions/pivot-freshness-timestamps-stables.md), [`plage-dates-groupes`](decisions/plage-dates-groupes.md).

## `src/schema_pivot.py`

55 décision(s) le gouvernent ; le module en cite 5.

| Décision | Nomme |
| --- | --- |
| [Trois absences publiées comme des faits (#556, #558, #560) (2026-08-29)](decisions/absences-publiees-comme-faits-556-558-560.md) | `validate_profil` |
| [La parole d'un gouvernement se compte dans la fenêtre de chaque membre, pas dans celle du gouvernement (#1020) (2026-09-18)](decisions/agregat-parole-gouvernement-1020.md) | `deriver_tags_thematiques` |
| [La cascade des textes portés entre dans l'UI, et la section s'aligne sur la maquette (#328), 06/09/2026](decisions/alignement-section-propose-ui-328.md) | `KNOWN_STADES_PROCEDURAUX` |
| [La cascade des textes portés passe au versant européen : une porte, et la nomenclature de la source (#901) (2026-09-16)](decisions/cascade-europeenne-une-porte-901.md) | `STADES_UE_NON_PUBLIES` |
| [Un mandat dit quel référentiel a établi sa catégorie, et l'absence n'accuse personne (#718) (2026-09-03)](decisions/categorie-source-des-mandats-718.md) | `KNOWN_CATEGORIE_SOURCES` |
| [`chambres` au niveau profil : une liste dérivée, et `chambre` qui n'en est plus que le premier élément (#493) (2026-08-20)](decisions/chambres-profil-derivees.md) | `ChambresDerivees`, `KNOWN_CHAMBRES`, `ORDRE_CHAMBRES`, `appliquer_chambres`, `deriver_chambres`, `validate_profil` |
| [La civilité et la nomenclature PCS de l'INSEE traversaient le pipeline sans y laisser de trace (#659) (2026-08-31)](decisions/civilite-et-pcs-insee-659.md) | `CHAMPS_IDENTITE_TEXTE_LIBRE`, `validate_profil` |
| [La collecte d'interventions des membres de roster est réduite au thème (#657) (2026-08-31)](decisions/collecte-interventions-reduite-au-theme-657.md) | `KNOWN_COLLECTES_INTERVENTION` |
| [Collecter les mandats locaux : une catégorie à part, et une fin qu'on n'invente pas (#922) (2026-09-15)](decisions/collecte-mandats-locaux-rne-922.md) | `KNOWN_CATEGORIES`, `KNOWN_CATEGORIE_SOURCES`, `appliquer_chambres` |
| [Les consommateurs de `chambre` migrés vers `chambres`, et le garde-fou qui datera son retrait (#494) (2026-08-20)](decisions/consommateurs-chambres-migres.md) | `appliquer_chambres`, `deriver_chambres`, `lire_chambres` |
| [Une liste vide affirme quelque chose, donc elle porte sa source (#860) (2026-09-15)](decisions/constat-absence-mandats-anterieurs-860.md) | `KNOWN_METHODES_CONSTAT_ANTERIEUR` |
| [La corroboration porte sur les chambres publiées, pas sur la complétude des mandats — et la condition de retrait de `chambre` devient atteignable (#486) (2026-08-30)](decisions/corroboration-chambres-publiees-486.md) | `ChambresDerivees`, `ORDRE_CHAMBRES`, `deriver_chambres`, `lire_chambres` |
| [La couverture se remplace à la maille où #539 la publie, et un cas non tranchable se déclare (#602) (2026-08-30)](decisions/couverture-remplacee-par-liste-602.md) | `LISTES_COUVERTES`, `valider_couverture` |
| [Un créneau de séance n'est pas un sujet, et le discriminant reste structurel (#710, 02/09/2026)](decisions/creneau-de-seance-nest-pas-un-sujet-710.md) | `deriver_tags_thematiques` |
| [Une exception n'est pas une preuve, et un défaut de notre code n'est pas une panne de l'Assemblée nationale (#562) (2026-08-28)](decisions/defaut-collecte-vs-panne-562.md) | `marqueur_defaut_code`, `validate_profil`, `valider_couverture` |
| [`meta.warnings[]` déclare son destinataire, dans un jumeau typé et aligné (#642) (2026-08-31)](decisions/destinataire-avertissements-642.md) | `KNOWN_SOURCE_TYPES`, `validate_profil`, `valider_avertissements` |
| [Un amendement retrouve son dossier, et la clé qu'on lui avait retirée (#639, rang 3)](decisions/dossier-des-amendements-639.md) | `validate_amendements_index` |
| [La parole des membres de groupe et de gouvernement publie un extrait de 280 caractères (#1029) (2026-09-22)](decisions/extrait-de-la-parole-des-rosters-1029.md) | `KNOWN_COLLECTES_INTERVENTION`, `extrait_de_texte` |
| [Ce qui a été dit, sur les fiches de gouvernement et de groupe (#1029) (2026-09-22)](decisions/extraits-de-parole-sur-les-fiches-1029.md) | `extrait_de_texte`, `url_seance_an` |
| [La fiche de gouvernement dit d'abord où elle se situe (#330)](decisions/fiche-de-gouvernement-330.md) | `deriver_tags_thematiques` |
| [Un filtre de publication posé avant la fusion ne filtre rien (#641, réouverture) (2026-08-31)](decisions/filtre-publication-apres-fusion-641.md) | `CHAMPS_IDENTITE_TEXTE_LIBRE` |
| [Deferred / out-of-scope investigations](decisions/hors-perimetre.md) | `KNOWN_CATEGORIES` |
| [Comment naît l'identité d'un profil, et où vont les identifiants de source (#539) (2026-08-28)](decisions/identite-profils-539.md) | `KNOWN_SOURCE_TYPES`, `poser_identifiant`, `validate_profil` |
| [L'institution est une dimension de la fiche, pas une section — 10/09/2026 (#328)](decisions/institution-dimension-de-la-fiche-328.md) | `KNOWN_CHAMBRES`, `deriver_chambres` |
| [Rien ne vérifiait que les clés publiées résolvent : le contrôle d'invariance (#485) (2026-08-20)](decisions/integrite-referentielle-pivot.md) | `validate_profil` |
| [Données UE — investigation des sources (2026-08-04)](decisions/investigation-sources-ue.md) | `validate_profil` |
| [Trois lectures du corpus passent à la projection, et chacune a son plafond dans un test (#635, 2026-08-30)](decisions/lectures-pipeline-par-projection-635.md) | `lire_chambres` |
| [Chaque prise de parole porte l'ancre de sa page de séance à l'AN (#1087) (2026-09-22)](decisions/lien-vers-la-prise-de-parole-1087.md) | `url_seance_an` |
| [Les mandats antérieurs à la couverture de l'Assemblée entrent par une table relue (#860)](decisions/mandats-anterieurs-couverture-860.md) | `KNOWN_INSTITUTIONS_ANTERIEURES`, `validate_profil` |
| [Normaliser les amendements : le coût n'est pas l'amendement, c'est sa liste de cosignataires (#431) (2026-08-19)](decisions/normalisation-amendements.md) | `validate_amendements_index`, `validate_profil` |
| [Normaliser les votes : une liste partagée, un mapping, et deux invariants devenus des jointures (#432) (2026-08-19)](decisions/normalisation-votes.md) | `validate_profil`, `validate_scrutins_index` |
| [`genere_le`/`synchro_le` des pivots ne doivent avancer que si le contenu change réellement (#343) (2026-08-16)](decisions/pivot-freshness-timestamps-stables.md) | `make_empty_profil` |
| [Les deux populations de `pivot_data/profiles/` sont portées par les outils, pas par une consigne (#630, 2026-08-30)](decisions/populations-profils-portees-par-les-outils-630.md) | `KNOWN_PROVENANCES` |
| [La position politique d'un groupe est celle que l'Assemblée déclare, lue dans une table committée (#686) (2026-09-01)](decisions/position-politique-groupes-686.md) | `POSITION_POLITIQUE_AN_VERS_PIVOT` |
| [Quelle source a rempli quel champ, et quand — un bloc à côté d'`identite` (#603) (2026-08-30)](decisions/provenance-par-champ-603.md) | `BLOCS_PROVENANCE_CHAMPS`, `valider_provenance_champs` |
| [Provenance des profils pivot : candidat_declare vs roster_groupe (2026-08-10)](decisions/provenance-pivot.md) | `KNOWN_PROVENANCES`, `validate_profil` |
| [Les membres de gouvernement deviennent une population, et leur collecte part (#996, lot 3) (2026-09-18)](decisions/provenance-roster-gouvernement-996.md) | `KNOWN_PROVENANCES`, `validate_profil` |
| [Un profil de roster ne porte pas une liste que sa propre collecte déclare écartée — purge des 49 `textes_portes` résiduels (#747)](decisions/purge-textes-portes-roster-747.md) | `validate_profil` |
| [La qualification d'un scrutin se perdait entre la collecte et le profil brut (#639, rang 1) (2026-08-31)](decisions/qualification-perdue-a-la-fusion-639.md) | `validate_scrutins_index` |
| [La qualification d'un scrutin et la clé de son dossier étaient lues puis jetées (#639, rangs 1 et 2)](decisions/qualification-scrutins-et-cle-dossier-639.md) | `KNOWN_TYPES_SCRUTIN`, `validate_scrutins_index` |
| [Un projet de loi porté au nom du Gouvernement n'est pas une production personnelle (#689) (2026-09-01)](decisions/qualification-textes-portes-689.md) | `KNOWN_ROLES_TEXTE`, `validate_profil` |
| [Une question au gouvernement : un acte, et ses tours de parole reliés à lui (#1094) (2026-09-22)](decisions/question-au-gouvernement-acte-et-parole-1094.md) | `rattacher_parole_aux_questions` |
| [Rattacher une intervention ou un scrutin à son dossier : les deux volets restants sont écartés, mesure à l'appui (#639) (2026-09-01)](decisions/rattachement-au-dossier-interventions-et-scrutins-639.md) | `LISTES_COUVERTES` |
| [Restaurer 789 interventions sans revenir sur le reste du schéma (#460) (2026-08-19)](decisions/restauration-interventions.md) | `validate_profil` |
| [NosDéputés sort du pipeline (#529, lot 5 de l'épic « une seule source AN ») (2026-08-27)](decisions/retrait-nosdeputes-529.md) | `KNOWN_SOURCE_TYPES`, `validate_profil` |
| [Le Sénat sort du périmètre, et le job qui concluait vert sans rien produire est retiré (#528, lot 3 de l'épic « une seule source AN ») (2026-08-26)](decisions/retrait-senat-528.md) | `KNOWN_CHAMBRES`, `KNOWN_SOURCE_TYPES` |
| [Le groupe européen dit son sigle et ce que la source en dit, sans changer de catégorie (#863) (2026-09-12)](decisions/sigle-groupe-europeen-863.md) | `KNOWN_TYPES_ORGANE_SOURCE` |
| [Le sort d'un texte entre dans la fiche, à côté de son stade et jamais à sa place (#743 dans #328), 07/09/2026](decisions/sort-des-textes-dans-la-fiche-328.md) | `KNOWN_MOTIFS_SORT_NON_RESOLU`, `KNOWN_SORTS_TEXTE_PORTE` |
| [Un texte porté dit ce qu'il est devenu, et son sort ne se déduit jamais de son stade (#743) (2026-09-06)](decisions/sort-des-textes-portes-743.md) | `KNOWN_SORTS_TEXTE_PORTE`, `KNOWN_STADES_PROCEDURAUX` |
| [Le stade d'un dossier européen se publie dans sa propre nomenclature, jamais traduit en stade français (#901) (2026-09-13)](decisions/stade-procedural-europeen-901.md) | `KNOWN_STADES_PROCEDURAUX` |
| [L'européen entre dans les listes que la fiche a déjà (#683, lot 2)](decisions/stockage-europeen-dans-les-listes-existantes-683.md) | `COLLECTE_SANS_VERBATIM_SOURCE` |
| [L'empreinte thématique d'une fiche est celle de sa législature (#825)](decisions/tags-agreges-dans-la-periode-825.md) | `deriver_tags_thematiques`, `legislature_de_intervention` |
| [Un singulier et un pluriel sont le même sujet : la clé groupe, la source publie (#1042) (2026-09-20)](decisions/tags-singulier-et-pluriel-1042.md) | `cle_tag_thematique`, `deriver_tags_thematiques`, `forme_publiee` |
| [Taxonomie des mandats : exploitation des `typeOrgane` AN non mappés (#382, option « mixte ») (2026-08-17)](decisions/taxonomie-mandats-typeorgane-an.md) | `KNOWN_CATEGORIES`, `validate_profil` |
| [La trame du profil candidat : l'institution est une colonne, jamais un chapitre (#328)](decisions/trame-profil-candidat-328.md) | `KNOWN_POSITIONS_HEMICYCLE`, `lire_chambres` |

Le mentionnent sans le gouverner : [`gouvernement-premier-ministre-portefeuille`](decisions/gouvernement-premier-ministre-portefeuille.md), [`retrait-fetch-activity-synthesis`](decisions/retrait-fetch-activity-synthesis.md), [`synchro-sources-derniere-recuperation-600`](decisions/synchro-sources-derniere-recuperation-600.md), [`verification-bout-en-bout-legislatures-figees`](decisions/verification-bout-en-bout-legislatures-figees.md).

## `src/scrutins_dossiers_an.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Un scrutin ne dit pas quel texte il tranche : le lien se lit à l'envers (#758), 07/09/2026](decisions/rattachement-scrutin-dossier-758.md) | `cle_depuis_uid` |

## `src/scrutins_europeens.py`

Le mentionnent sans le gouverner : [`cascade-europeenne-une-porte-901`](decisions/cascade-europeenne-une-porte-901.md), [`index-reecrits-seulement-si-le-contenu-change-1075`](decisions/index-reecrits-seulement-si-le-contenu-change-1075.md), [`index-scrutins-europeens-901`](decisions/index-scrutins-europeens-901.md), [`lecture-europeenne-themes-et-votes-901`](decisions/lecture-europeenne-themes-et-votes-901.md), [`pas-d-ecarts-groupe-europeens-901`](decisions/pas-d-ecarts-groupe-europeens-901.md).

## `src/scrutins_index.py`

6 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [Un audit qui lit un champ déplacé ne se tait pas : il crie 62 000 fois (#726) (2026-09-03)](decisions/audit-champs-deplaces-726.md) | `ScrutinsIndex` |
| [L'index des scrutins européens publie les effectifs, jamais le sort (#901) (2026-09-14)](decisions/index-scrutins-europeens-901.md) | `decomposer_id` |
| [Le seuil de blob sort du critère de sortie, et les profils bruts se partitionnent par législature (#580) (2026-08-29)](decisions/partition-profils-legislature-580.md) | `iter_votes_du_repertoire` |
| [La qualification d'un scrutin se perdait entre la collecte et le profil brut (#639, rang 1) (2026-08-31)](decisions/qualification-perdue-a-la-fusion-639.md) | `_valeur_scrutin`, `merge_scrutins_index` |
| [La qualification d'un scrutin et la clé de son dossier étaient lues puis jetées (#639, rangs 1 et 2)](decisions/qualification-scrutins-et-cle-dossier-639.md) | `merge_scrutins_index` |
| [Un scrutin ne dit pas quel texte il tranche : le lien se lit à l'envers (#758), 07/09/2026](decisions/rattachement-scrutin-dossier-758.md) | `MOTIF_TEXTE_LIE_NON_SOURCE` |

Le mentionnent sans le gouverner : [`index-reecrits-seulement-si-le-contenu-change-1075`](decisions/index-reecrits-seulement-si-le-contenu-change-1075.md), [`normalisation-votes`](decisions/normalisation-votes.md), [`point-de-sauvegarde-dans-les-profils-518`](decisions/point-de-sauvegarde-dans-les-profils-518.md).

## `src/scrutins_legislature.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Ce qu'une liste vide veut dire : les quatre états de couverture (#539) (2026-08-28)](decisions/couverture-listes-539.md) | `LEGISLATURES_AN` |

## `src/senat_mandats.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Le libellé d'un organe sénatorial se lit sur la colonne complète, pas sur l'abrégée (#912) (2026-09-13)](decisions/libelles-senat-colonne-complete-912.md) | `composer_mandats` |

## `src/senat_opendata.py`

2 décision(s) le gouvernent ; le module en cite 1.

| Décision | Nomme |
| --- | --- |
| [Collecter les mandats locaux : une catégorie à part, et une fin qu'on n'invente pas (#922) (2026-09-15)](decisions/collecte-mandats-locaux-rne-922.md) | `TABLES_REFUSEES` |
| [Le libellé d'un organe sénatorial se lit sur la colonne complète, pas sur l'abrégée (#912) (2026-09-13)](decisions/libelles-senat-colonne-complete-912.md) | `reparer_mojibake` |

Le mentionnent sans le gouverner : [`frise-segments-pleins-et-senat-885`](decisions/frise-segments-pleins-et-senat-885.md).

## `src/syceron_debates.py`

6 décision(s) le gouvernent ; le module en cite 3.

| Décision | Nomme |
| --- | --- |
| [Trois absences publiées comme des faits (#556, #558, #560) (2026-08-29)](decisions/absences-publiees-comme-faits-556-558-560.md) | `SYCERON_AVAILABLE_LEGISLATURES` |
| [La clé de cache AN porte la COMPLÉTUDE, et la sauvegarde devient explicite (#550) (2026-08-28)](decisions/cache-completude-interventions-550.md) | `SYCERON_AVAILABLE_LEGISLATURES` |
| [Ce qu'une liste vide veut dire : les quatre états de couverture (#539) (2026-08-28)](decisions/couverture-listes-539.md) | `SYCERON_AVAILABLE_LEGISLATURES` |
| [Mandats commission/groupe_amitie/extra_parlementaire sourcés depuis l'AN, fetch_identity NosDéputés rendu conditionnel (#369, complet), watchdog générique sur tous les téléchargements zip (#370, complet) (2026-08-17)](decisions/mandats-officiels-an-369.md) | `_download_syceron_zip` |
| [Syceron publie l'identifiant d'orateur NU, et n'a donc jamais rien indexé (#510) (2026-08-20)](decisions/syceron-acteur-ref-nu-510.md) | `SYCERON_AVAILABLE_LEGISLATURES` |
| [Suite du 26/08/2026 : les trois archives vérifiées, les deux défauts de parseur corrigés](decisions/syceron-archives-verifiees-parseur-510.md) | `SYCERON_AVAILABLE_LEGISLATURES` |

Le mentionnent sans le gouverner : [`cache-du-poste-hors-des-tests-721`](decisions/cache-du-poste-hors-des-tests-721.md), [`plafond-roster-et-commit-518`](decisions/plafond-roster-et-commit-518.md), [`syceron`](decisions/syceron.md).

## `src/text_utils.py`

Le mentionnent sans le gouverner : [`boucle-perimetre-candidats-757`](decisions/boucle-perimetre-candidats-757.md), [`slug-fabrique-membre-de-roster-708`](decisions/slug-fabrique-membre-de-roster-708.md).

## `src/textes_dossiers_an.py`

Le mentionnent sans le gouverner : [`archive-dossiers-xiv-1019`](decisions/archive-dossiers-xiv-1019.md), [`dossier-des-amendements-639`](decisions/dossier-des-amendements-639.md), [`fraicheur-dossiers-762`](decisions/fraicheur-dossiers-762.md).

## `src/textes_promulgues.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Les textes promulgués sont une population du Parlement, pas d'un gouvernement (2026-09-23)](decisions/textes-promulgues-population-du-parlement.md) | `chambre_premiere_lecture` |

Le mentionnent sans le gouverner : [`liens-des-actes-vers-les-lois`](decisions/liens-des-actes-vers-les-lois.md), [`table-figee-numero-de-loi-vers-jorftext`](decisions/table-figee-numero-de-loi-vers-jorftext.md).

## `src/textes_vises_figes.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Le `texte_vise` fautif se reprend depuis l'archive figée, pas par une fusion plus permissive (#696, 01/09/2026)](decisions/report-texte-vise-source-696.md) | `est_uid_texte`, `lire_textes_vises` |

## `src/titres_europeens.py`

2 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Le sujet nettoyé d'une question européenne n'atteignait pas l'entrée déjà publiée (#980) (2026-09-16)](decisions/sujet-europeen-sans-boutons-a-la-fusion-980.md) | `titre_sans_boutons` |
| [Un titre européen perd ses boutons de téléchargement, et rien d'autre (#901) (2026-09-15)](decisions/titres-europeens-sans-boutons-901.md) | `titre_sans_boutons` |

## `src/tranches_amendements_figees.py`

7 décision(s) le gouvernent ; le module en cite 1.

| Décision | Nomme |
| --- | --- |
| [Les agrégats publiés entrent dans le contrôle de perte, et l'ordre de grandeur reste hors contrat (#649) (2026-08-31)](decisions/agregats-publies-controle-perte-649.md) | `signatures` |
| [Un agrégat de fiche ne compte que la période de la fiche (#821)](decisions/amendements-agreges-dans-la-periode-821.md) | `signatures` |
| [Un amendement cosigné n'est pas N amendements : deux grandeurs, deux noms (#643) (2026-08-31)](decisions/amendements-distincts-et-signatures-643.md) | `signatures` |
| [« Collecté = publié » compte une tranche dérivée dans l'archive (#691, lot 3a)](decisions/audit-compte-les-tranches-derivees-691.md) | `reconstruire_tranche`, `signatures` |
| [Les dix lignées sont écrites, et une mesure corrige le motif du recalcul (#836)](decisions/generation-fiches-lignees-836.md) | `signatures` |
| [L'écriture marque les tranches closes, et le `nombre` vient de l'archive (#691, lot 3b)](decisions/marquage-tranches-derivees-691.md) | `reconstruire_tranche`, `signatures` |
| [Reconstruire une tranche d'amendements depuis l'archive figée (#691, lot 1)](decisions/reconstruction-tranches-depuis-archive-691.md) | `_normaliser_nil`, `mapping_pivot`, `reconstruire_tranche` |

## `src/verifier_archivage_swh.py`

Le mentionnent sans le gouverner : [`donnees-versionnees-integrite`](decisions/donnees-versionnees-integrite.md), [`fenetre-recalibrage-551`](decisions/fenetre-recalibrage-551.md), [`perimetre-coupure-575`](decisions/perimetre-coupure-575.md).

## `src/verifier_transport_artifacts.py`

1 décision(s) le gouvernent ; le module en cite 0.

| Décision | Nomme |
| --- | --- |
| [Une panne de transport n'est pas une source absente (#786)](decisions/transport-artifacts-panne-ou-absence-786.md) | `inventaire` |
