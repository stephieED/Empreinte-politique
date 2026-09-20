#!/usr/bin/env python3
"""
schema_pivot.py — Schéma pivot v1 (format commun indépendant de la source).

Ce module définit le schéma pivot unique vers lequel toutes les sources sont
converties (NosDéputés/NosSénateurs, Parltrack, Wikidata). Il ne contient
aucune logique de collecte : c'est un contrat de structure.

Principe directeur : chaque fait doit remonter à sa source primaire.
Chaque section comporte soit une `source_url` soit des métadonnées de synchro
dans le bloc `sources[]`.

Format d'un profil pivot v1 :
{
    "schema_version": "1",
    "id": "jean-luc-melenchon",             # = le slug, sans préfixe (#487)
    "nom": "Jean-Luc Mélenchon",
    "chambres": ["AN", "Senat"],             # #493 — LISTE des chambres où la personne a
                                             # siégé, valeurs de KNOWN_CHAMBRES, dans l'ordre
                                             # de ORDRE_CHAMBRES. **Dérivée**, jamais
                                             # collectée : voir `deriver_chambres()`, seule
                                             # fabrique de ce champ ET de `chambre`.
                                             # Se LIT par `lire_chambres()` (#494), jamais en
                                             # direct : le corpus publié ne la porte pas encore.
    "chambre": "AN",                         # "AN" | "Senat" | "PE" | "mairie" | null
                                             # #493 — n'est plus une donnée autonome : c'est
                                             # `chambres[0]`, donc incapable de contredire
                                             # `chambres`. Champ de transition ; #494 a migré
                                             # tous ses consommateurs du pipeline, il n'en reste
                                             # qu'un dans l'interface (#495). Condition de
                                             # retrait écrite dans
                                             # docs/decisions/chambres-profil-derivees.md,
                                             # vérifiée par tests/test_garde_fou_chambre.py.
    "parti": null,                           # parti politique (depuis candidats.json si dispo)
    "groupe": "La France Insoumise",         # groupe parlementaire déclaré par la source
    "identite": {                            # bloc biographique, tout est nullable/optionnel
        "civilite": "Mme",                   # #659 — civilité de l'état civil AMO30
                                             # (`etatCivil.ident.civ`), renseignée sur les
                                             # 3 117 fiches : « M. » 2 106, « Mme » 1 011.
                                             # JAMAIS dérivée d'un prénom : sans la source,
                                             # `null` (§2 règle 5). Facultative — absente des
                                             # 477 profils qui publiaient `identite` avant ce
                                             # lot, comme `identifiants` (#539) l'a été.
        "profession": "Avocat",              # activité professionnelle déclarée (référentiel AN)
                                             # TEXTE LIBRE, et il le reste : c'est
                                             # `famille_socioprofessionnelle` ci-dessous qui
                                             # porte la nomenclature (#641, #659)
        "famille_socioprofessionnelle": "Employés",   # #659 — nomenclature PCS de l'INSEE,
                                             # niveau famille (`profession.socProcINSEE.famSocPro`),
                                             # telle que l'Assemblée nationale l'applique.
                                             # 2 177 fiches sur 3 117 (70 %) ; `null` sur les 940
                                             # que la source ne classe pas — et « non classé »
                                             # n'est PAS la famille « Sans profession déclarée »,
                                             # qui est, elle, une valeur de la nomenclature
                                             # (85 fiches). Publiée VERBATIM, variantes
                                             # typographiques comprises : regrouper est
                                             # l'affaire de qui agrège.
        "categorie_socioprofessionnelle": "Employés de commerce",  # #659 — second niveau
                                             # (`socProcINSEE.catSocPro`), 37 libellés distincts.
                                             # Renseigné exactement quand la famille l'est.
        "date_naissance": "1951-08-19",       # ISO-8601, date seule (référentiel AN)
        "lieu_naissance": null,              # ville + département/pays, texte libre ; fourni
                                             # par le référentiel AN (acteurs)
        "num_circo": "13",                    # numéro de circonscription tel que fourni par la
                                             # source ; absent pour un sénateur ou un mandat sans circonscription
        "uri_hatvp": null,                   # lien vers la déclaration HATVP (Haute Autorité pour
                                             # la Transparence de la Vie Publique), source AN (acteurs).
                                             # Une URI ou `null` — JAMAIS un objet (#556) : AMO30
                                             # rend `{"@xsi:nil": "true"}` pour « pas de
                                             # déclaration », et un dict non vide est truthy, donc
                                             # un consommateur qui teste `if uri_hatvp` croit tenir
                                             # un lien. 191 profils sur 481 le publiaient ainsi.
                                             # `validate_profil` le refuse désormais.
        "source_url": null                   # URL de la fiche source utilisée pour ce bloc
    },
    "identifiants": {                        # #539 — identifiants de SOURCE, publiés.
                                             # `id` est le slug et rien d'autre : le préfixe
                                             # `nosdeputes:`/`europarl:` qui portait une source
                                             # dans l'identité a été retiré (#487), et
                                             # l'information qu'il portait vit ici, nommée.
                                             # Toutes les clés de KNOWN_IDENTIFIANTS sont
                                             # présentes, toutes sont nullables : `null` = « pas
                                             # d'identifiant connu dans ce référentiel », jamais
                                             # « non applicable » (§2.5). Bloc ABSENT = profil
                                             # publié avant #539, jamais « aucun identifiant ».
        "an": "PA1567",                      # acteur AMO30 (`PA<chiffres>`), depuis la table
                                             # committée raw_data/correspondance_acteurs_an.json
                                             # (#525) : le `PA` cesse d'être RÉ-RÉSOLU par
                                             # correspondance de nom à chaque run — il est publié.
        "senat": null,                       # aucun référentiel sénatorial établi depuis #528 :
                                             # `null` sur tout le corpus, et c'est un fait déclaré.
        "europarl": "131580",                # identifiant MEP de l'Open Data Portal du PE, chaîne
                                             # de chiffres. C'est lui qui préfixait l'`id` de
                                             # `jordan-bardella`.
        "hatvp": null                        # URI de la déclaration HATVP. RECOPIÉ depuis
                                             # `identite.uri_hatvp`, qui reste en place et que
                                             # l'interface lit là-bas. Deux emplacements, une seule
                                             # fabrique — `normalize_profil` écrit les deux d'un
                                             # coup. Le compte réel est **279 profils sur 479** au
                                             # 28/08 (285 sur 481 au 29/08) : la mesure de 465 qui
                                             # circulait comptait les 191 marqueurs `xsi:nil`
                                             # comme des présences (#556).
    },
    "mandats_locaux_couverture": {           # #922 — CE QUE L'APPARIEMENT AU RÉPERTOIRE
                                             # NATIONAL A DONNÉ, publié même quand aucun mandat
                                             # n'en est sorti. `appariement` est fermé :
                                             # date_naissance / table_relue / ecarte /
                                             # aucun_mandat_trouve / non_relu. Les deux derniers
                                             # se ressemblent et ne se confondent jamais — l'un
                                             # est un constat, l'autre un aveu.
                                             # PAS dans `couverture` : sa nomenclature est fermée
                                             # sur cinq listes métier, et les mandats locaux
                                             # vivent dans `mandats[]` avec les autres.
                                             # `borne_couverture` (2020) voyage ici plutôt que
                                             # dans un document : une fiche doit pouvoir dire,
                                             # sans rien aller chercher, que rien avant cette
                                             # date n'a pu être vérifié.
        "appariement": "date_naissance",
        "borne_couverture": "2020",
        "synchro_le": "2026-09-15T12:00:00+0200",
    },
    "couverture": {                          # #539 — POURQUOI une liste est vide. Indexé par
                                             # liste métier (LISTES_COUVERTES), chaque liste
                                             # portant AU MOINS UNE entrée : aucun défaut
                                             # implicite, « pas d'entrée = couvert »
                                             # réintroduirait l'ambiguïté que le bloc retire et
                                             # ferait porter à l'UI une hypothèse qu'aucune
                                             # mesure n'étaye.
                                             # `tags_thematiques` n'y figure PAS : c'est une aide
                                             # à la lecture dérivée des autres listes (§2.8), sans
                                             # source propre donc sans borne propre.
                                             # Bloc absent = profil publié avant #539.
                                             # Fabrique unique : couverture_profil.deriver().
                                             # #683 — une entrée peut porter "source"
                                             # ("parlement_europeen"), FACULTATIF, dont
                                             # l'absence signifie « Assemblée nationale » :
                                             # c'est le cas de 100 % des entrées écrites
                                             # avant ce champ. Il départage deux écrivains
                                             # dont l'un a interrogé une source que l'autre
                                             # n'a pas interrogée (merge_profile,
                                             # _sources_couvertes) — jamais le texte de la
                                             # preuve, qui n'est pas un identifiant.
        "votes": [
            {
                "etat": "couvert",           # ETATS_COUVERTURE, fermé — vocabulaire aligné sur
                                             # celui déjà fermé pour les gouvernements
                                             # (couverture_dossiers.py, #399) :
                                             # "couvert"         — collecté, dans le périmètre de
                                             #                     la source, RÉELLEMENT zéro. Un
                                             #                     zéro publiable (§2.5 interdit
                                             #                     de confondre un zéro mesuré
                                             #                     avec une absence, pas de le
                                             #                     publier) ;
                                             # "fait_etabli"     — un fait sur la PERSONNE :
                                             #                     « jamais élu·e à l'Assemblée
                                             #                     nationale » ;
                                             # "hors_couverture" — la source ne couvre pas cette
                                             #                     période. JAMAIS un fait sur la
                                             #                     personne ;
                                             # "non_collecte"    — rien ne peut être affirmé.
                "cause": null,               # CAUSES_NON_COLLECTE — obligatoire SI ET SEULEMENT
                                             # SI etat == "non_collecte", interdite sinon. Le
                                             # « si et seulement si » est ce qui empêche la cause
                                             # d'être omise en silence.
                                             # "panne"        — un run n'a pas rendu ; la preuve
                                             #                  est le warning ou le journal ;
                                             # "par_decision" — une politique de pipeline a
                                             #                  délibérément écarté la collecte ;
                                             #                  la preuve NOMME la politique (le
                                             #                  drapeau et l'issue). 469 profils
                                             #                  sur 476 pour `interventions`
                                             #                  (#357).
                "portee": {"legislature": 17},
                                             # FACULTATIVE : `{"legislature": n}` ou
                                             # `{"debut": "...", "fin": "..."}`. Absente, l'entrée
                                             # vaut pour tout le profil. Une couverture à cheval
                                             # s'exprime en DEUX entrées — jamais par un cinquième
                                             # état `partielle` qu'il faudrait désambiguïser.
                "preuve": "...",             # OBLIGATOIRE : borne d'archive, identifiant de
                                             # source, entrée de la table de correspondance, ou
                                             # politique nommée. Une entrée sans preuve serait une
                                             # affirmation sans source (§2.2).
                "constate_le": "2026-08-28"  # OBLIGATOIRE, date ISO du constat.
            }
        ],
        "amendements": [],                   # même forme ; voir LISTES_COUVERTES
        "textes_portes": [],
        "interventions": [],
        "mandats": []
    },
    "sources": [                             # traçabilité de chaque source utilisée
        {
            "type": "assemblee_nationale",   # "assemblee_nationale" | "europarl" |
                                             # "parltrack" | "wikidata" |
                                             # "nosdeputes" | "nossenateurs"
                                             # (historiques : plus produites
                                             #  depuis #529, encore publiées)
            "url": "https://...",            # URL canonique de la fiche source
            "synchro_le": "2026-07-29T..."   # ISO-8601 de la dernière synchro réussie
        }
    ],
    "mandats": [
        {
            "label": "Commission des affaires étrangères",
            "categorie": "commission",       # "mandat_electif" | "commission" |
                                             # "groupe_amitie" | "groupe_politique" |
                                             # "extra_parlementaire" | "autre" |
                                             # "commission_enquete" | "mission_information" |
                                             # "groupe_etudes" | "delegation"
                                             # (voir KNOWN_CATEGORIES)
            "fonction": "membre",            # ex. "membre", "président", "rapporteur"
            "debut": "2022-01-01",
            "fin": null,
            "actif": true,
            "chambre": null,                 # #492 — présent UNIQUEMENT sur les mandats de
                                             # categorie "mandat_electif" ; "AN" | "Senat" |
                                             # "PE" | null (voir KNOWN_CHAMBRES). Sémantique
                                             # exacte : *la chambre dont le jeu de données a
                                             # rendu ce mandat*, estampillée à la collecte —
                                             # un fait de collecte traçable (§2.2), pas une
                                             # déduction. C'est le niveau où l'information
                                             # est vraie : un mandat appartient à une chambre,
                                             # une personne n'y est pas réductible (#486).
                                             # `null` = chambre non déterminée (mandat collecté
                                             # avant #492, conservé par la fusion additive) :
                                             # jamais une valeur par défaut (§2.5), et un
                                             # warning `chambre de mandat électif non résolue`
                                             # le dit dans meta.warnings.
            "source_url": null,              # URL de la fiche source, si disponible
            "position_dans_hemicycle": null, # "majorite" | "opposition" | "minoritaire" |
                                             # "gouvernement" | null ; champ éditorial le plus
                                             # sensible du schéma. Ne JAMAIS renseigner sans une
                                             # source primaire vérifiable (déclaration officielle
                                             # du groupe, liste du socle de soutien au gouvernement,
                                             # JO, ou positionPolitique/codeType du référentiel
                                             # officiel des organes de l'Assemblée nationale) — voir
                                             # source_url ci-dessus, qui devient obligatoire dès que
                                             # ce champ est renseigné. "gouvernement" n'est utilisé
                                             # que sur un mandat de categorie
                                             # "fonction_gouvernementale" (voir KNOWN_CATEGORIES).
            "mode_declenchement": null,      # commissions d'enquête uniquement :
                                             # "droit_tirage" | "demande_votee" | null
            "suspendu_pour_fonction_gouvernementale": null
            # période de suspension du mandat pour cause de fonction ministérielle :
            # {"debut": "2024-01-08", "fin": "2024-09-05", "suppleant_id": "slug-du-suppleant"}
            # ou null si non applicable.
        }
    ],
    "votes": [                               # MAPPING seul (#432) : un scrutin est identique
                                             # pour tous ses votants, son méta vit une seule fois
                                             # dans pivot_data/scrutins.json (schéma scrutins-v1).
                                             # Ne garder ici que ce qui est propre au membre.
        {
            "scrutin_id": "an:17:1234",      # "an:<legislature>:<numero_scrutin>" — la législature
                                             # fait partie de l'identifiant parce que le numéro
                                             # repart de 1 à chaque législature (AGENTS.md §5).
                                             # null UNIQUEMENT si le scrutin n'a pas pu être
                                             # résolu ; "scrutin_non_resolu" est alors obligatoire.
            "position": "pour"               # "pour" | "contre" | "abstention" | "non_votant"
                                             # | "absent" | "excuse" | null
                                             # "absent" : aucune trace de vote (implicite ou explicite)
                                             # "excuse" : absence justifiée/notifiée à la source
            # "groupe_au_moment_du_vote": "SOC"
                                             # FACULTATIF — écrit seulement s'il est renseigné.
                                             # Son absence signifie "non renseigné", exactement
                                             # comme null : seule exception à la convention
                                             # "missing = null" (§4), et elle est chiffrée —
                                             # le champ n'est jamais peuplé (0 sur 398 085) et
                                             # l'écrire coûtait 12,1 Mo de null, 40 % du mapping.
            # "scrutin_non_resolu": {...}    # FACULTATIF, et anormal : enregistrement complet du
                                             # vote (date, texte, sort, type_vote…) conservé tel
                                             # quel quand aucune législature n'a pu être résolue.
                                             # Ni supprimé ni doté d'une clé inventée (§2.5).
                                             # #683 — il porte "institution": "parlement_europeen"
                                             # sur un vote du PE, qui n'a JAMAIS de scrutin_id :
                                             # l'index partagé est keyé `an:<leg>:<num>` et
                                             # `decomposer_id` refuse tout autre préfixe. Le
                                             # marqueur n'est pas décoratif — c'est lui que
                                             # `couverture_profil.bornes_europeennes` lit pour
                                             # dire quelle borne s'applique à quelle part de la
                                             # liste. Idem dans `amendement_non_resolu`, et sous
                                             # `interventions[].source.institution`.
        }
    ],
    "textes_portes": [                       # dossiers dont l'élu est auteur ou rapporteur
        {
            "titre": "Proposition de loi ...",
            "titre_langue": None,            # #901 — "fr" | "en" | null, sur les seules entrées
                                             # européennes. Le dump ParlTrack donne le titre en
                                             # ANGLAIS ; le portail du Parlement publie le même
                                             # document en 22-23 langues, et le résolveur
                                             # téléchargeait déjà cette réponse pour en tirer un
                                             # booléen d'existence. Ce n'est donc PAS une
                                             # traduction que nous fabriquons : c'est la version
                                             # française officielle. Le champ dit dans quelle
                                             # langue le titre publié est — sans lui, plus rien
                                             # ne permet de mesurer combien restent en anglais,
                                             # ni d'empêcher de croire que nous traduisons.
                                             # null sur une entrée AN, dont le titre est français
                                             # par construction.
            # "institution": "parlement_europeen"
                                             # FACULTATIF (#683) — présent sur les seules entrées
                                             # du Parlement européen. Son absence signifie
                                             # « Assemblée nationale », qui est le cas de 100 %
                                             # des entrées écrites avant ce lot : l'écrire
                                             # partout aurait été un backfill sans fait nouveau.
            "dossier_id": "DLR5L15N37607",   # identifiant AN du dossier législatif (#639).
                                             # Même nom que gouvernements textes[].dossier_id :
                                             # c'est la seule clé qui rattache un texte porté
                                             # autrement que par son libellé. null si la source
                                             # n'en donne pas — jamais reconstruit d'un titre.
            "role": "rapporteur",            # "initiateur_projet_de_loi" |
                                             # "auteur_proposition_de_loi" |
                                             # "auteur_proposition_de_resolution" |
                                             # "auteur" | "rapporteur" | "co-rapporteur"
                                             # DÉRIVÉ de (rôle brut × nature_texte), #689 —
                                             # jamais collecté, jamais fusionné.
            "nature_texte": null,            # "projet_de_loi" | "proposition_de_loi" |
                                             # "proposition_de_resolution" | null (#689).
                                             # Le fait sourcé : préfixe de l'uid du document
                                             # déposé (PRJL/PION/PNRE). null = la source ne
                                             # l'établit pas — jamais tiré du libellé.
            "type_rapport": null,            # nomenclature officielle, descriptive uniquement :
                                             # "rapporteur_fond" | "rapporteur_avis" |
                                             # "rapporteur_special_budget" | "mission_information"
                                             # | "rapporteur_general" | null
            "stade_procedural": null,        # "depose" | "examine_commission" |
                                             # "inscrit_ordre_jour" | "discute_seance" |
                                             # "adopte" | "promulgue" | null
                                             # PROGRESSION, jamais une issue (#743)
            "sort": null,                    # l'ISSUE du dossier, cf. KNOWN_SORTS_TEXTE_PORTE.
                                             # Lu dans `statutConclusion.fam_code` par la même
                                             # fonction que les fiches de gouvernement (#743).
                                             # `null` s'accompagne TOUJOURS de sort_non_resolu
            "sort_non_resolu": {             # présent SEULEMENT si `sort` est null, et il
                "motif": "sans_decision"     # l'explique. cf. KNOWN_MOTIFS_SORT_NON_RESOLU
            },
            "date_min": "2022-01-01",
            "date_max": "2022-06-30",
            "legislature": "16",
            "source_url": null
        }
    ],
    "amendements": [                         # MAPPING seul (#431). Le méta de l'amendement —
                                             # texte_vise, sort, date, numero, type_deposant,
                                             # premier_signataire, co_signataires — vit une
                                             # seule fois dans pivot_data/amendements/<legis>.json
                                             # (+ .cosignatures.json), pas une fois par
                                             # signataire : 810 552 paires pour 207 238
                                             # amendements distincts, et 77,7 M entrées de
                                             # cosignatures pour 4,96 M distinctes.
                                             # Voir docs/decisions/normalisation-amendements.md
        {
            "amendement_id": "an:AMANR5L17PO59047BTC1376P0D1N000012",  # <source>:<uid AN>.
                                             # L'uid est la seule clé unique : le `numero`
                                             # repart à chaque texte (121 805 amendements pour
                                             # 30 616 numéros distincts en législature 17) —
                                             # docs/decisions/amendements-cle-uid.md
            "role_signataire": "auteur_principal"  # SEUL champ propre au membre :
                                             # "auteur_principal" | "cosignataire"
        },
        {                                    # amendement qu'aucun uid ne rattache : ni supprimé,
                                             # ni doté d'une clé inventée (AGENTS.md §2.5)
            "amendement_id": null,
            "role_signataire": "cosignataire",
            "amendement_non_resolu": {       # enregistrement complet, conservé tel quel
                "texte_vise": "Projet de loi de finances 2025",
                "sort": "irrecevable",       # "adopté" | "rejeté" | "retiré" | "tombé" |
                                             # "non_soutenu" | "irrecevable" (statut distinct
                                             # de "rejeté" — voir base_juridique_irrecevabilite)
                "base_juridique_irrecevabilite": "art. 40",  # "art. 40" | "art. 45" | null ;
                                             # renseigné uniquement si sort == "irrecevable"
                "premier_signataire": "jean-dupont",   # slug, sans préfixe de provenance (#487)
                "co_signataires": [],        # liste d'identifiants AN des co-signataires
                "type_deposant": "depute",   # "gouvernement" | "commission_rapporteur" | "depute"
                "date": "2024-10-15",
                "numero": "CL42",
                "source_url": null
            }
        }
    ],
    "interventions": [
        {
            # Identifiant de l'intervention, propagé VERBATIM depuis le profil
            # brut (#540) : `syceron_<uid du compte rendu>_<rang du paragraphe>`
            # côté débats AN, `question_<uid>` côté questions officielles,
            # l'entier NosDéputés pour les entrées héritées d'avant #529. Null
            # si le brut n'en porte pas. C'EST la clé de fusion pivot — une
            # `source_url` n'en est pas une : Syceron publie l'URL de l'archive
            # de la législature, la même pour toutes ses interventions.
            "intervention_id": "syceron_CRSANR5L16S2023O1N055_000399",
            "date": "2023-03-15",
            "type_detail": "loi",            # "loi" | "question" | ...
            "sujet": "Budget 2024",
            "theme_officiel": null,          # thème officiel du débat si fourni par
                                             # une source institutionnelle (sinon null)
            "seance": null,                  # métadonnées de séance officielles (dict)
            "dossier": null,                 # métadonnées de dossier officiel (dict)
            "source": null,                  # métadonnées de source officielle (dict)
            "texte": "...",                  # extrait (180 premiers caractères)
            "fonction": "Rapporteur",        # rôle institutionnel au moment de l'intervention
            "format": "prise_de_parole_developpee",  # ou "reaction_courte"
            "mots_cles": ["budget", "fiscalité"],
            "source_url": "https://...",
            # Champs supplémentaires présents uniquement si type_detail == "question"
            # (questions parlementaires officielles, source open data AN) :
            # #657 — présent UNIQUEMENT sur une entrée réduite au thème, et
            # l'entrée n'a alors que `intervention_id`, `date`, `type_detail`,
            # `theme_officiel`, `source_url`, `source` et cette clé. Les autres
            # sont ABSENTES, pas nulles : le verbatim n'a pas été demandé, ce
            # qui est un fait sur le run et non sur la personne.
            "collecte": "theme_seul",        # KNOWN_COLLECTES_INTERVENTION ; absent = forme complète
            "sous_type": "QE",               # "QE" (écrite) | "QG" (au gouvernement) | "QOSD" (orale sans débat)
            "ministere": "Ministère...",     # ministère interrogé (texte libre)
            "reponse": "...",                # texte de la réponse, si disponible (null sinon)
            "date_reponse": "2023-04-20",    # date JO de la réponse (null si pas encore répondu)
        }
    ],
    "tags_thematiques": ["budget", "fiscalité"],  # bruts, avant harmonisation Phase 4
    "meta": {
        "schema_version": "1",
        "genere_le": "2026-07-29T...",
        "licence_donnees": "ODbL ...",
        "warnings": [],                      # les messages, inchangés depuis toujours
        "avertissements": [                  # #642 — LE JUMEAU TYPÉ de `warnings`, aligné
                                             # entrée par entrée, dans le même ordre.
                                             # Facultatif : absent des 481 profils publiés
                                             # avant le lot. Présent, il est complet.
            {
                "message": "votes introuvables : ...",   # identique à warnings[i]
                "destinataire": "lecteur",   # DESTINATAIRES_AVERTISSEMENT, fermé ;
                                             # null = personne ne l'a déclaré, jamais
                                             # un rangement par défaut (§2 règle 5)
            }
        ],
        "provenance": "candidat_declare",         # "candidat_declare" | "roster_groupe"
                                             # | "roster_gouvernement" ;
                                             # voir KNOWN_PROVENANCES
        "provenance_champs": {               # #603 — D'OÙ VIENT CETTE VALEUR, et de quand.
                                             # À ne pas confondre avec `provenance` ci-dessus,
                                             # qui dit pourquoi ce profil existe. Facultatif :
                                             # absent des 481 profils publiés avant ce lot.
                                             # Ni à confondre avec `couverture`, qui dit
                                             # POURQUOI UNE LISTE EST VIDE : les deux coexistent
                                             # et n'ont pas la même maille — par liste métier
                                             # pour l'une, par champ pour l'autre.
            "identite": {                    # seul bloc décrit ; voir BLOCS_PROVENANCE_CHAMPS
                "profession": {
                    "source": "assemblee_nationale",  # KNOWN_SOURCE_TYPES, ou null si inconnue
                    "synchro_le": "2026-08-30T..."    # null si la source est inconnue
                }
            }
        }
    }
}

Usage :
    from schema_pivot import SCHEMA_VERSION, make_empty_profil, validate_profil
"""

from collections import Counter, defaultdict
import re
from datetime import date as _date
import time
from typing import Any, NamedTuple, Optional
from avertissements import DESTINATAIRES_AVERTISSEMENT
from amendements_index import (
    SCHEMA_VERSION as AMENDEMENTS_SCHEMA_VERSION,
    COSIGNATURES_SCHEMA_VERSION as AMENDEMENTS_COSIGNATURES_SCHEMA_VERSION,
    decomposer_id as decomposer_id_amendement,
    legislature_de_id as legislature_amendement,
)
from scrutins_index import decomposer_id

# Version du schéma ; à incrémenter si une rupture de compatibilité est introduite.
# Les consommateurs peuvent vérifier profil["schema_version"] == SCHEMA_VERSION.
SCHEMA_VERSION = "1"

# Clés obligatoires au niveau racine du profil pivot.
REQUIRED_TOP_LEVEL_KEYS: frozenset[str] = frozenset({
    "schema_version", "id", "nom", "chambre", "sources",
    "mandats", "votes", "textes_portes", "interventions",
    "amendements", "tags_thematiques", "meta",
})

# Clés obligatoires dans le bloc "meta".
REQUIRED_META_KEYS: frozenset[str] = frozenset({
    "schema_version", "genere_le", "licence_donnees", "warnings",
})

# Champs dont la valeur doit être une liste.
_LIST_KEYS = (
    "votes", "mandats", "textes_portes", "interventions",
    "amendements", "tags_thematiques", "sources",
)

# Types de sources reconnus (extensible, liste non-exhaustive).
#
# `nosdeputes` et `nossenateurs` ne sont plus PRODUITS depuis #529 (lot 5) —
# `normalize_profil` écrit `assemblee_nationale` — mais ils restent VALIDES :
# 476 profils publiés en portent une, et les retirer d'ici ferait refuser par
# `validate_profil()` le corpus qu'on vient de publier. Un schéma qui n'accepte
# plus ce qu'il a écrit hier n'est pas une simplification, c'est une perte.
# Leur sort, avec les mentions d'attribution ODbL, est le lot 6.
KNOWN_SOURCE_TYPES: frozenset[str] = frozenset({
    "nosdeputes", "nossenateurs", "parltrack", "wikidata", "assemblee_nationale", "europarl",
    # #885 : data.senat.fr, producteur Sénat, Licence Ouverte. Distinct de
    # `nossenateurs`, qui désignait un réutilisateur tiers sous ODbL — la
    # confusion coûterait la clause de partage à l'identique dans le mauvais sens.
    "senat",
})

# Valeurs de chambre reconnues.
KNOWN_CHAMBRES: frozenset[str] = frozenset({"AN", "Senat", "PE", "mairie"})

#: Valeur unique de `interventions[].collecte` (#657). Elle déclare une entrée
#: collectée SANS son verbatim, pour peupler `theme_officiel` — donc
#: `tags_thematiques` — sans payer les 413 Mio que la forme complète coûterait
#: pour les 468 membres de roster.
COLLECTE_THEME_SEUL = "theme_seul"

#: Formes de collecte reconnues sur une entrée d'`interventions[]` (#657).
#: L'ABSENCE de la clé est la forme complète, et c'est délibéré : une clé
#: toujours présente ferait de la forme pleine une valeur parmi d'autres, alors
#: qu'elle est le défaut, et rendrait les 16 242 entrées déjà publiées
#: rétroactivement « non déclarées ».
#: #683 — la source ne publie **aucun** verbatim, et ce n'est pas notre run qui
#: l'a écarté. `theme_seul` dit « le verbatim n'a pas été demandé » (un fait sur
#: le run) ; celui-ci dit « il n'existe pas chez la source » (un fait sur la
#: source). Les confondre rangerait sous une décision de collecte ce que le
#: Parlement européen ne publie pas — deux absences qui ne se confondent
#: jamais (§2 règle 5).
COLLECTE_SANS_VERBATIM_SOURCE = "sans_verbatim_source"

KNOWN_COLLECTES_INTERVENTION: frozenset[str] = frozenset({
    COLLECTE_THEME_SEUL,
    COLLECTE_SANS_VERBATIM_SOURCE,
})

# Ordre canonique de `chambres` (#493). Il rend la liste **stable** d'un run à
# l'autre — sans lui, l'ordre suivrait celui des mandats, que la fusion additive
# fait varier — et fixe quelle chambre devient le scalaire `chambre` quand une
# carrière en compte plusieurs.
# `AN` avant `Senat` n'est pas arbitraire : c'est la convention déjà documentée
# par #488, où `CHAMBRES = ["deputes", "senateurs"]` et « le premier de CHAMBRES
# l'emporte quand les deux répondent ». La reprendre ici garantit qu'aucun
# scalaire publié ne change de valeur du seul fait que la dérivation le remplace.
ORDRE_CHAMBRES: tuple[str, ...] = ("AN", "Senat", "PE", "mairie")

# Chambre de **collecte** (« quel jeu de données a répondu ») → chambre pivot.
# Définie ici, et non dans `normalize_profil` qui la portait seul, parce que
# `lire_chambres()` en a besoin elle aussi : `check_quality_gate` teste depuis
# toujours `chambre in ("AN", "deputes")`, et cette tolérance ne doit pas se
# perdre en migrant (#494). Deux tables séparées auraient pu diverger en silence.
CHAMBRE_COLLECTE_VERS_PIVOT: dict[str, str] = {
    "deputes": "AN",
    "senateurs": "Senat",
}


class ChambresDerivees(NamedTuple):
    """Résultat de `deriver_chambres()` : les deux champs, et ce qui les étaye.

    L'état de la dérivation est retourné explicitement plutôt que redéduit par
    l'appelant : c'est lui qui décide de publier le warning de #493 (§2.5), et
    c'est le compteur qui dira quand `chambre` peut être retiré.
    """

    #: Liste ordonnée (ORDRE_CHAMBRES), sans doublon, valeurs de KNOWN_CHAMBRES.
    chambres: list[str]
    #: `chambres[0]`, ou `None` si `chambres` est vide. Jamais autre chose.
    chambre: Optional[str]
    #: `True` si **chaque** entrée de `chambres` est étayée par un
    #: `mandat_electif` estampillé — donc vrai, vide de sens mais vrai, sur une
    #: liste vide, qui ne publie aucune chambre. `False` seulement quand une
    #: chambre est publiée sans qu'aucun mandat ne la dise, c'est-à-dire quand
    #: la chambre de collecte figure sur sa seule parole. C'est ce booléen qui
    #: déclenche le warning de #493, et son passage à `True` sur tout le corpus
    #: est la condition 2 du retrait de `chambre`.
    #:
    #: Il ne dit **rien** de la complétude des mandats : un `mandat_electif`
    #: sans estampille est déclaré par le warning de #492, qui le compte
    #: (#486 — jusque-là, ce prédicat le redéclarait, ce qui gageait le retrait
    #: d'un champ de niveau profil sur une complétude de niveau mandat que la
    #: fusion additive ne peut pas atteindre).
    corroboree: bool
    #: Les entrées de `chambres` qu'aucun mandat estampillé n'étaye — en pratique
    #: la seule chambre de collecte. Nommées dans le warning : « on publie AN
    #: parce que le jeu de données AN a répondu, pas parce qu'un mandat le dit ».
    chambres_non_corroborees: list[str]
    #: Nombre de `mandat_electif` sans chambre déterminée (#492) : c'est lui qui
    #: décroît à mesure que la recollecte avance.
    mandats_non_estampilles: int


def deriver_chambres(
    mandats: Optional[list[dict[str, Any]]], repli: Any = None
) -> ChambresDerivees:
    """Dérive `chambres` (liste) et `chambre` (scalaire) des `mandat_electif` (#493).

    **Seule fabrique des deux champs.** C'est ce qui les rend incapables de se
    contredire : `chambre` n'est pas une donnée collectée à côté d'une donnée
    dérivée, c'est `chambres[0]`. L'invariant est vérifié par `validate_profil`.

    Pourquoi une liste plutôt qu'un scalaire : une carrière peut traverser deux
    chambres, et le scalaire en efface une (épic #486 — Retailleau publié `AN`
    alors qu'il siège au Sénat depuis 2004, Mélenchon publié `Senat` alors qu'il
    a été député 2017-2022). Pourquoi une liste plutôt qu'une chaîne concaténée :
    `chambre in ("AN", "deputes")` renvoie `False` sur `"AN; Senat"` **sans lever
    d'erreur**, là où `"AN" in chambres` est explicite et testable.

    Pourquoi pas « la chambre du mandat en cours » — l'option que posait #493 :
    mesurée sur les 209 profils publiés de `b2c34f4`, elle produit **114 `null`
    sur 209** (55 % du corpus), dont `edouard-philippe` et `jean-luc-melenchon`
    parmi les 8 `candidat_declare`. Elle remplace un fait faux par un autre : la
    carrière de député de Retailleau disparaîtrait comme disparaissent
    aujourd'hui les années sénatoriales de Mélenchon.

    Args:
        mandats: `mandats[]` du profil pivot. Seules les entrées de catégorie
                 `mandat_electif` sont lues, et seule leur `chambre` (#492) —
                 jamais un libellé. Déduire « PE » de « Mandat de député
                 européen » remettrait une chaîne collectée au cœur d'un champ
                 fermé, exactement ce que #492 a écarté.
        repli: chambre de collecte du profil — *quel jeu de données a répondu*.
               Elle est **toujours ajoutée** à la liste, jamais substituée à ce
               que disent les mandats et jamais écartée par eux. Ce n'est pas une
               valeur par défaut au sens de §2.5 : c'est une donnée observée,
               reprise telle quelle. Mais elle n'est **pas étayée par un mandat**,
               et l'appelant doit le déclarer dans `meta.warnings` dès que
               `corroboree` est faux. Justification mesurée :
               docs/decisions/chambres-profil-derivees.md.

               « Toujours ajoutée » est le point que deux simulations en lecture
               seule sur les 209 profils publiés de `b2c34f4` ont dû corriger, et
               la raison est toujours la même — *retirer une chambre observée est
               une suppression*, ce que le pipeline ne fait jamais :

               - un repli « utilisé seulement si rien n'est estampillé » faisait
                 basculer **7 profils de `AN`/`Senat` vers `PE`** (`marine-le-pen`,
                 `damien-abad`, `jean-luc-melenchon`, `philippe-juvin`,
                 `constance-le-grip`, `anne-sophie-frigout`, `yannick-vaugrenard`) :
                 leurs mandats européens sont estampillés `PE` par
                 `normalize_europarl`, quand leurs mandats AN, collectés avant
                 #492, restent à `null` ;
               - un repli « utilisé tant que la couverture est incomplète » en
                 laissait **un** : `yannick-vaugrenard`, dont le seul
                 `mandat_electif` collecté est européen. Tous ses mandats électifs
                 étant estampillés, la couverture passait pour complète et son
                 `AN` disparaissait — le sortant de
                 `check_quality_gate.population_an`.

               La complétude de `mandats[]` n'est donc pas celle d'une carrière :
               un profil peut n'avoir aucun `mandat_electif` français collecté
               sans avoir cessé de siéger. C'est pourquoi `corroboree` dit
               seulement « chaque chambre publiée est étayée par un mandat », et
               jamais « voici toute la carrière ».

    Returns:
        Un `ChambresDerivees`.
    """
    estampillees: set[str] = set()
    n_non_estampilles = 0
    for m in mandats or []:
        if not isinstance(m, dict) or m.get("categorie") != "mandat_electif":
            continue
        chambre_mandat = m.get("chambre")
        # `isinstance(..., str)` avant l'appartenance : un profil malformé peut
        # porter une liste ou un dict là, et `x in frozenset` lève alors un
        # TypeError. Cette fonction tourne dans le pipeline, avant toute
        # validation — une entrée mal formée doit produire « chambre non
        # déterminée », pas tuer un shard d'extraction.
        if isinstance(chambre_mandat, str) and chambre_mandat in KNOWN_CHAMBRES:
            estampillees.add(chambre_mandat)
        else:
            n_non_estampilles += 1

    toutes = set(estampillees)
    if isinstance(repli, str) and repli in KNOWN_CHAMBRES:
        toutes.add(repli)

    chambres = [c for c in ORDRE_CHAMBRES if c in toutes]
    non_corroborees = [c for c in chambres if c not in estampillees]
    # `corroboree` porte sur ce qui est PUBLIÉ dans `chambres`, et sur rien
    # d'autre (#486). Deux clauses ont été retirées de ce prédicat, chacune
    # parce qu'elle faisait déclarer non corroborée une liste que rien ne
    # contredit — mesuré sur les 481 profils pivot publiés du 30/08/2026, où le
    # warning est publié 31 fois et où **30 de ces 31 occurrences énoncent un
    # problème que leur propre phrase dénie** :
    #
    # - `bool(chambres)` : une liste vide ne publie aucune chambre, donc aucune
    #   chambre non étayée. Sur 3 des 481 profils (`david-lisnard`,
    #   `marine-tondelier`, `nathalie-arthaud` — aucun mandat parlementaire,
    #   aucune chambre de collecte), le warning se lisait « chambres=[], dont
    #   aucune sans mandat électif estampillé pour l'étayer, et 0 mandat(s)
    #   électif(s) encore sans chambre » : il ne nommait aucun problème.
    # - `not n_non_estampilles` : un `mandat_electif` sans estampille est un
    #   manque de la COLLECTE d'un mandat, pas un défaut d'étai de la liste. Il
    #   a déjà son propre avertissement, celui de #492, qui le nomme et le
    #   compte. Sur 27 des 481 profils, cette clause faisait publier « chambres
    #   du profil non corroborée : chambres=['AN'], dont aucune sans mandat
    #   électif estampillé pour l'étayer » — la liste était intégralement
    #   étayée, et le titre disait le contraire.
    #
    # Ce que le prédicat ne dit toujours pas — et #493 l'écrivait déjà :
    # « chaque chambre publiée est étayée » n'a jamais voulu dire « voici toute
    # la carrière ». Un mandat non estampillé peut cacher une chambre absente de
    # la liste ; c'est le warning de #492 qui le déclare, pas celui-ci.
    corroboree = not non_corroborees

    return ChambresDerivees(
        chambres,
        chambres[0] if chambres else None,
        corroboree,
        non_corroborees,
        n_non_estampilles,
    )


def appliquer_chambres(profil: dict[str, Any]) -> ChambresDerivees:
    """(Re)pose `chambres` et `chambre` sur `profil`, d'après ses `mandats` (#493).

    À appeler **après toute modification de `mandats[]`**, et pas seulement à la
    construction du profil. `chambres` est un champ dérivé : il ne se fusionne
    pas, il se recalcule — sinon il décrit un ensemble de mandats qui n'est plus
    celui du profil. Trois endroits mutent `mandats[]` après la normalisation, et
    tous les trois doivent repasser ici :

    - `merge_profile.merge_pivot_profile`, dont la fusion additive rend
      `mandats[]` **surensemble** de l'ancien comme du neuf ;
    - `merge_profile.backfill_mandat_chambre` (#492), qui estampille après coup
      un mandat déjà connu — un mandat qui gagne sa chambre doit faire gagner sa
      chambre au profil ;
    - `generate_all_profiles`, qui verse les `mandat_electif` européens dans le
      pivot AN/Sénat par un `mandats.extend(...)` : sans ce recalcul, un profil
      bicaméral AN + PE publierait `chambres: ["AN"]`, en effaçant le PE —
      exactement le défaut que #486 reproche au scalaire.

    Le repli reste la valeur courante de `profil["chambre"]` : c'est ce qui
    garantit qu'un scalaire déjà publié ne régresse jamais vers `null`.
    """
    derivation = deriver_chambres(profil.get("mandats"), repli=profil.get("chambre"))
    profil["chambres"] = derivation.chambres
    profil["chambre"] = derivation.chambre
    return derivation


#: La législature portée par un identifiant d'entrée de l'Assemblée nationale.
#: Trois familles la portent au même endroit, juste après `R5L` :
#: `syceron_CRSANR5L16S…` (compte rendu de séance), `question_QANR5L15QE…`
#: (question écrite) et `syceron_CRSJOCGR5L16S…` (Congrès). Mesuré le
#: 10/09/2026 sur les 937 130 interventions des 1 035 profils publiés :
#: 929 680 identifiants la portent, 124 ne la portent pas, 1 486 sont des
#: questions, 5 329 relèvent du Parlement européen.
_RE_LEGISLATURE_INTERVENTION = re.compile(r"R5L(\d+)")


def legislature_de_intervention(intervention_id: Any) -> Optional[str]:
    """Législature portée par l'identifiant d'une intervention AN.

    `syceron_CRSANR5L16S2023O1N245_000286` → `"16"`. Lecture **structurelle**
    de l'identifiant, jamais une déduction depuis la date : c'est l'Assemblée
    qui l'y écrit, exactement comme `legislature_de_uid` la lit sur l'`uid`
    d'un amendement (#821).

    `None` quand l'identifiant ne suit aucune forme connue — un appelant qui
    filtre par période doit alors **conserver** l'entrée et déclarer son
    compte, plutôt que de lui attribuer une législature par défaut : rien ne
    prouve qu'elle soit hors période, et l'écarter ferait passer une ignorance
    pour un fait (§2 règle 5).
    """
    if not isinstance(intervention_id, str):
        return None
    m = _RE_LEGISLATURE_INTERVENTION.search(intervention_id)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Un singulier et un pluriel sont le même sujet (#1042)
# ---------------------------------------------------------------------------
#
# `theme_officiel` est l'intitulé d'un point de séance, tel que le compte rendu
# l'écrit. L'Assemblée écrit tantôt « motion de censure », tantôt « motions de
# censure », et ces deux formes arrivaient sur la fiche comme DEUX sujets —
# première et deuxième ligne du gouvernement Borne, 19 porteurs et 12.
# Signalé par la session « UI gouv » le 20/09/2026.
#
# Mesuré avant d'écrire la règle, sur un profil publié sur quatre : **4 025
# clés, 10 à plusieurs formes**. C'est peu, et c'est très visible — ces
# étiquettes-là sont fréquentes, donc elles remontent en tête.
#
# **La clé groupe, la forme publiée reste observée.** Sur ces 10 clés, **4 ont
# une forme normalisée que la source n'écrit jamais** : « pénurie de
# médicament », « fermeture de classe ». Publier la clé fabriquerait un
# intitulé que personne n'a écrit, ce que §2 règle 2 interdit. La forme retenue
# est donc la plus FRÉQUENTE parmi celles observées, l'ordre alphabétique
# départageant une égalité — déterministe, et toujours une forme de la source.


def cle_tag_thematique(tag: str) -> str:
    """La clé de regroupement d'une étiquette : pluriel simple, mot à mot.

    Volontairement naïve, et bornée à ce qu'elle sait faire. Elle ne lemmatise
    pas, ne connaît pas les pluriels irréguliers, et ne rapproche que ce qu'un
    `s` final sépare. Une table d'alias ou une lemmatisation déciderait que
    deux intitulés publiés n'en font qu'un — c'est une normalisation
    éditoriale, et elle n'a pas été arbitrée.

    Le seuil de 3 lettres ne protège que les mots les plus courts — « gaz »
    reste intact, « sens » devient « sen » et « ours » devient « our ». **Sans
    conséquence, et c'est mesuré** : la clé ne sert qu'à REGROUPER, la forme
    publiée reste celle de la source, et il faudrait qu'un « sen » existe par
    ailleurs dans le corpus pour que deux sujets se confondent. Sur les 4 025
    clés d'un profil publié sur quatre, les 10 groupes formés sont tous des
    variantes singulier/pluriel du même intitulé.
    """
    return " ".join(
        mot[:-1] if len(mot) > 3 and mot.endswith("s") else mot
        for mot in tag.split()
    )


def forme_publiee(formes: "Counter[str]") -> str:
    """La forme à publier pour un groupe : la plus fréquente, puis l'alphabet.

    Jamais la clé : elle peut n'avoir jamais été écrite par la source.
    """
    return min(formes.items(), key=lambda item: (-item[1], item[0]))[0]


def deriver_tags_thematiques(interventions: Optional[list[dict[str, Any]]]) -> list[str]:
    """Les tags thématiques d'un profil, dérivés de ses interventions.

    `theme_officiel` quand l'intervention en porte un — il vient du compte rendu
    officiel de l'AN —, `mots_cles` sinon. Le repli sur `mots_cles` est CONSERVÉ
    par #529 alors que plus rien ne les collecte : ils sont dans les profils déjà
    collectés, que la fusion additive garde, et les retirer ferait tomber les 647
    `tags_thematiques` publiés qui en dérivent — une liste surveillée bloquante
    (#460/#470). On ne collecte plus cette matière ; on continue de savoir la lire
    (AGENTS.md §2 règle 5).

    **Fabrique unique, et champ DÉRIVÉ, comme `chambres` (#710).** La fusion
    pivot unissait l'ancienne liste et la neuve : un tag publié une fois y restait
    pour toujours, et aucune correction de `theme_officiel` — celle de #710 comme
    une autre — ne pouvait l'en déloger. Un champ dérivé se recalcule, il ne se
    fusionne pas ; sinon il décrit un ensemble d'interventions qui n'est plus
    celui du profil.

    **Le recalcul est un no-op sur l'état publié**, ce qui est la preuve qu'il ne
    perd rien par lui-même : mesuré le 02/09/2026 sur les 481 profils publiés,
    les 39 782 couples (profil, tag) publiés sont exactement ceux que cette
    fonction rend depuis les `interventions[]` de ces mêmes profils, sur 0 profil
    d'écart. Ce qui change ensuite ne vient donc que de la correction des
    interventions elles-mêmes.
    """
    formes: dict[str, Counter] = defaultdict(Counter)
    for i in interventions or []:
        if not isinstance(i, dict):
            continue
        theme = i.get("theme_officiel")
        if theme and isinstance(theme, str):
            cleaned = theme.strip().lower()
            if cleaned:
                formes[cle_tag_thematique(cleaned)][cleaned] += 1
        else:
            for kw in (i.get("mots_cles") or []):
                if not isinstance(kw, str):
                    continue
                cleaned = kw.strip().lower()
                if cleaned:
                    formes[cle_tag_thematique(cleaned)][cleaned] += 1
    return sorted(forme_publiee(compte) for compte in formes.values())


def lire_chambres(profil: Any) -> list[str]:
    """Les chambres d'un profil pivot, **côté lecture** — seule porte d'entrée (#494).

    Tout consommateur du niveau profil passe par ici, et aucun ne lit plus
    `chambre` ni `chambres` directement. C'est ce qui rend la condition de retrait
    du scalaire mécaniquement vérifiable (`tests/test_garde_fou_chambre.py`) :
    quand cette fonction est le dernier lecteur, `chambre` peut partir, et il
    suffit d'y supprimer une branche.

    **Pourquoi un repli est nécessaire aujourd'hui, et pas seulement commode** :
    `chambres` est produite par #493, mais aucun des 209 profils publiés ne la
    porte encore (mesuré sur `07e9147`, le 20/08/2026 — 0/209). Elle n'apparaîtra
    qu'après un run complet. Un consommateur qui lirait `chambres` sans repli
    verrait donc une liste vide sur tout le corpus : `population_an` passerait de
    207 à **0** et le signal de régression qu'elle porte s'éteindrait en silence,
    sur le corpus même qu'il surveille. Le repli n'élargit rien — il rend la
    migration lisible avant la régénération, pas après.

    **Ce repli-ci a une fin écrite**, contrairement à ceux de #431 et #432 qui
    sont devenus permanents faute de critère : il disparaît avec le scalaire, à la
    condition de retrait de docs/decisions/chambres-profil-derivees.md.

    Args:
        profil: un profil pivot. Un objet non-dict rend `[]` — cette fonction
                tourne dans le pipeline comme dans les rapports, avant toute
                validation, et une donnée malformée doit produire « chambre non
                déterminée », jamais une exception.

    Returns:
        Les chambres de `KNOWN_CHAMBRES`, dédoublonnées, dans l'ordre de
        `ORDRE_CHAMBRES`. Liste vide si la chambre n'est pas déterminée — jamais
        `None`, jamais une valeur par défaut (§2.5) : `[]` dit « on ne sait pas »,
        et `"AN" in []` est faux, ce qui est le comportement voulu.
    """
    if not isinstance(profil, dict):
        return []

    brut = profil.get("chambres")
    if isinstance(brut, list):
        # `chambres` présente fait foi, y compris vide : la fabrique garantit
        # `chambre == chambres[0]`, donc une liste vide veut dire un scalaire nul.
        # Retomber sur le scalaire ici ne pourrait que ressusciter une valeur que
        # `validate_profil` refuse déjà comme divergente.
        retenues = {c for c in brut if isinstance(c, str) and c in KNOWN_CHAMBRES}
        return [c for c in ORDRE_CHAMBRES if c in retenues]

    scalaire = profil.get("chambre")
    if isinstance(scalaire, str):
        scalaire = CHAMBRE_COLLECTE_VERS_PIVOT.get(scalaire, scalaire)
        if scalaire in KNOWN_CHAMBRES:
            return [scalaire]
    return []


def libelle_chambres(chambres: list[str], vide: str = "?") -> str:
    """Rendu d'une liste de chambres pour un rapport : `"AN+PE"`, ou `vide` (#494).

    Vit ici, à côté de `lire_chambres()`, parce que trois rapports l'affichent
    (`check_quality_gate` §3, `audit_pivot_dataset` × 2) et qu'un séparateur qui
    diverge d'un rapport à l'autre rendrait les tableaux incomparables. `vide`
    dit « chambre non déterminée » — jamais une chambre par défaut (§2.5).
    """
    return "+".join(chambres) if chambres else vide


# Positions de vote reconnues.
KNOWN_POSITIONS: frozenset[str] = frozenset({
    "pour", "contre", "abstention", "non_votant",
    "absent",   # aucune trace de vote (absence implicite ou explicite)
    "excuse",   # absence justifiée / notifiée à la source primaire
})

# Catégories de mandats reconnues. "groupe_politique" désigne une période
# d'appartenance à un groupe politique (distincte du mandat électif global),
# utilisée pour dater les changements de groupe et les rattacher à une
# position dans l'hémicycle (voir position_dans_hemicycle ci-dessous).
# "fonction_gouvernementale" désigne une période d'appartenance à un
# gouvernement (ministre, secrétaire d'État...), datée par le référentiel
# officiel des organes de l'Assemblée nationale (organe.codeType ==
# "GOUVERNEMENT") ; distincte de mandats[].suspendu_pour_fonction_gouvernementale,
# qui documente la suspension corrélative du mandat électif, pas la fonction
# gouvernementale elle-même.
# Les 4 dernières catégories sont issues de #382/#383 (option « mixte ») :
# le référentiel officiel AN distingue une vingtaine de `typeOrgane`, dont
# près de la moitié des mandats n'étaient jusque-là pas exploités faute de
# catégorie pour les accueillir — commissions d'enquête, missions
# d'information, groupes d'études et délégations se retrouvaient tous rangés
# sous `commission` par l'ancien mapping NosDéputés, ce qui trompait sur leur
# nature (voir docs/decisions/taxonomie-mandats-typeorgane-an.md).
# Choix de granularité : une catégorie par nature institutionnelle
# réellement distincte pour l'utilisateur, pas une par `typeOrgane` — les
# variantes internes (MISINFO/MISINFOCOM/MISINFOPRE, CNPE/CNPS, GE/GEVI,
# DELEG/API/OFFPAR) sont regroupées.
#: Référentiel qui a ÉTABLI la catégorie d'un mandat (#718). Vocabulaire fermé,
#: clé **facultative** : son absence dit « personne ne l'a établie », jamais
#: « héritée » — un mandat que la source ne sert plus (#486 : 29 des 511
#: `mandat_electif` publiés) serait sinon accusé à tort. Même forme que
#: `interventions[].collecte` (#657), dont l'absence est aussi un sens.
#:
#: `an` : la catégorie vient du `codeType` de l'organe AMO30, par
#: `_TYPE_ORGANE_TO_CATEGORIE` — ou des deux chemins qui lisent la même archive
#: (`mandat_electif`, `groupe_politique`/`fonction_gouvernementale`).
#: `europarl` : la catégorie vient du Parlement européen.
KNOWN_CATEGORIE_SOURCES: frozenset[str] = frozenset({"an", "europarl", "senat", "rne"})

#: #863 — la **nature de l'organe telle que la source la classe**, quand elle la
#: classe. `categorie` répond à « comment le pivot le range » ; ce champ répond à
#: « ce que la source en dit », et c'est ce qui permet de reconnaître un groupe
#: politique européen **sans lire son intitulé**. Clé facultative, comme
#: `categorie_source` : son absence dit que la source n'a pas classé
#: l'appartenance — c'est le cas des entrées `AUTRE` du portail européen.
KNOWN_TYPES_ORGANE_SOURCE: frozenset[str] = frozenset({
    "groupe_politique_europeen",
    "parti_national_au_parlement_europeen",
    "commission_parlementaire_europeenne",
    "delegation_parlementaire_europeenne",
    "groupe_de_travail_europeen",
    "organe_dirigeant_europeen",
    "mandat_parlementaire_europeen",
    # #885 — les organes du Sénat. Les deux derniers n'ont **pas** de catégorie
    # pivot propre : ils sont rangés `autre`, et c'est ici que leur nature
    # survit au rangement.
    "mandat_senatorial",
    "groupe_politique_senatorial",
    "commission_senatoriale",
    "groupe_etudes_senatorial",
    "groupe_amitie_senatorial",
    "groupe_information_senatorial",
    "groupe_liaison_senatorial",
    "organisme_extra_parlementaire_senat",
})

KNOWN_CATEGORIES: frozenset[str] = frozenset({
    "mandat_electif", "commission", "groupe_amitie", "groupe_politique",
    "extra_parlementaire", "fonction_gouvernementale", "autre",
    "commission_enquete", "mission_information", "groupe_etudes", "delegation",
    # #922 — un mandat LOCAL (municipal, départemental, régional, communautaire).
    # Volontairement distinct de `mandat_electif`, qui n'est pas qu'une
    # étiquette : `appliquer_chambres` en dérive `chambres[]`, et compte les
    # `mandat_electif` SANS chambre comme un défaut de collecte (#492). Y verser
    # un conseiller régional ferait sonner cette garde à tort — un conseil
    # régional n'est pas une chambre parlementaire, et n'a pas vocation à
    # apparaître dans `chambres[]`.
    "mandat_local",
})

# Position dans l'hémicycle (majorité/opposition/minoritaire/gouvernement).
# Champ éditorial sensible : ne doit jamais être renseigné sans
# mandats[].source_url pointant vers une source primaire vérifiable (voir
# validate_profil). "minoritaire" correspond à la qualification officielle
# "Minoritaire" de l'Assemblée nationale (groupe ni majoritaire ni
# d'opposition formelle). "gouvernement" qualifie une période d'appartenance
# à un gouvernement (l'élu n'est alors ni majorité ni opposition au sens
# parlementaire du terme, mais membre de l'exécutif) : cette valeur n'est
# jamais déduite depuis un mandat de catégorie autre que
# "fonction_gouvernementale".
KNOWN_POSITIONS_HEMICYCLE: frozenset[str] = frozenset({
    "majorite", "opposition", "minoritaire", "gouvernement",
})

# Correspondance `organe.positionPolitique` (référentiel AMO30 de l'Assemblée
# nationale) → valeur du schéma. L'Assemblée qualifie **elle-même** chacun de
# ses groupes politiques ; ce n'est donc pas une qualification que ce dépôt
# produit, et il n'y a rien ici à inférer (AGENTS.md §2 règle 1).
#
# Canonique, parce que deux consommateurs la lisent et qu'ils publient la même
# valeur à deux étages différents : `candidate_profile` sur
# `mandats[].position_dans_hemicycle` d'un profil individuel (#354), et
# `an_roster` sur `position_politique` d'une fiche de groupe (#686). Deux
# tables jumelles auraient dérivé — c'est exactement ce que la table des sigles
# de #526 refuse déjà, un cran plus loin.
#
# Une valeur absente ou hors table n'a **pas** d'entrée ici : elle se publie
# `non_declaree` (fiche de groupe) ou se traduit par une absence de mandat
# qualifié (profil individuel), jamais par un repli sur « opposition », qui est
# 24 des 40 organes qualifiés (AGENTS.md §2 règle 5).
POSITION_POLITIQUE_AN_VERS_PIVOT: dict[str, str] = {
    "Majoritaire": "majorite",
    "Minoritaire": "minoritaire",
    "Opposition": "opposition",
}

# Mode de déclenchement d'une commission d'enquête.
KNOWN_MODES_DECLENCHEMENT: frozenset[str] = frozenset({"droit_tirage", "demande_votee"})

# Nomenclature officielle des types de rapport (descriptive, pas une catégorie
# de valorisation éditoriale).
KNOWN_TYPES_RAPPORT: frozenset[str] = frozenset({
    "rapporteur_fond", "rapporteur_avis", "rapporteur_special_budget", "mission_information",
    "rapporteur_general",
})

#: L'ISSUE d'un dossier porté, distincte de son STADE (#743). Le stade encode une
#: progression — `depose` → … → `promulgue` — et un dossier n'en porte que le cran
#: le plus avancé atteint ; l'absence du cran suivant est un fait de la source à
#: sa date, jamais un sort. **« Non adopté » ne devient pas « rejeté »**, et ce
#: champ ne doit pas permettre de le déduire : il se lit à côté du stade, pas à sa
#: place.
#:
#: Mêmes valeurs que `schema_gouvernement.KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL`,
#: parce que c'est la MÊME source lue par la MÊME fonction
#: (`gouvernement_textes._determine_statut`, sur `statutConclusion.fam_code`) —
#: la duplication est verrouillée par un test, les deux schémas restant par
#: ailleurs indépendants.
KNOWN_SORTS_TEXTE_PORTE: frozenset[str] = frozenset({
    "depose", "navette_en_cours", "adopte", "adopte_49_3", "adopte_cmp",
    "promulgue", "rejete", "rejete_49_3", "retire",
})

#: Pourquoi un texte porté ne porte pas son sort (#743). Fermé, et chaque motif
#: se répare ailleurs : `fam_code_inconnu` est un code que la source a ajouté et
#: que la table ne connaît pas, `sans_decision` est un dossier qui n'a pas encore
#: atteint de décision de séance — un état légitime, pas une lacune —, et
#: `archives_indisponibles` est une panne du run. Les confondre ferait passer un
#: état normal pour un défaut.
KNOWN_MOTIFS_SORT_NON_RESOLU: frozenset[str] = frozenset({
    "fam_code_inconnu",
    "sans_decision",
    "archives_indisponibles",
    # #747 — les trois motifs ci-dessus sont ceux de l'archive AN, et #743 n'a
    # instruit que ce chemin. Le dossier ParlTrack, lui, ne porte AUCUNE issue :
    # `get_dossiers_for_mep` indexe reference, titre, comite, role, date,
    # source_url, et rien d'autre. Ce n'est ni un trou à combler ni une panne,
    # c'est ce que la source dit — et le dire est la seule façon de ne pas
    # publier une absence sans cause (§2 règle 5).
    "source_sans_sort",
})

# Stade procédural d'un texte, pour identifier ce qui a été réellement débattu.
#: Les stades de la procédure **française**, dans leur ordre d'avancement. Le
#: seuil de publication de `AGENTS.md` §6 est un rang dans cette liste.
STADES_PROCEDURAUX_AN: frozenset[str] = frozenset({
    "depose", "examine_commission", "inscrit_ordre_jour", "discute_seance",
    "adopte", "promulgue",
})

#: Les stades de la procédure **européenne**, un par valeur de
#: `procedure.stage_reached` (#901). Seize, relevées sur le dump entier le
#: 13/09/2026 : 20 442 des 23 885 dossiers en portent une.
#:
#: **Étendues, jamais traduites** — c'est l'arbitrage du 13/09/2026, et il tient
#: à un contre-exemple : « Procedure completed » n'est pas `promulgue`, puisque
#: « Procedure rejected » est une procédure achevée elle aussi. Ranger un fait
#: européen sous une étiquette française inventerait ce que la source ne dit pas
#: (§2 règle 2). Le préfixe `ue_` rend la provenance lisible dans la valeur même,
#: et empêche qu'un rang français s'applique à l'une d'elles par distraction.
STADES_PROCEDURAUX_UE: frozenset[str] = frozenset({
    "ue_procedure_achevee",
    "ue_procedure_achevee_acte_delegue_en_vigueur",
    "ue_procedure_achevee_acte_delegue_rejete",
    "ue_procedure_achevee_attente_publication_jo",
    "ue_procedure_caduque_ou_retiree",
    "ue_procedure_rejetee",
    "ue_phase_preparatoire_parlement",
    "ue_attente_decision_commission",
    "ue_attente_decision_finale",
    "ue_attente_position_parlement_1re_lecture",
    "ue_attente_parlement_1re_lecture",
    "ue_attente_parlement_2e_lecture",
    "ue_attente_vote_parlement",
    "ue_attente_debat_vote_pleniere",
    "ue_attente_position_conseil_1re_lecture",
    "ue_attente_decision_conseil_2e_lecture",
})

#: Le stade européen qui NE se publie pas — le seul, et il est nommé plutôt que
#: la liste de ses quinze contraires (#901, arbitré le 14/09/2026).
#:
#: Le seuil de `AGENTS.md` §6 est un **rang** dans la liste française : « au
#: moins parvenu en commission ». Aucun stade européen n'a de rang dans cette
#: liste, et l'appliquer tel quel écartait les **383** textes portés européens —
#: `raphael-glucksmann` affichait « 0 publiés » en en portant 23.
#:
#: La nomenclature européenne est **plate** : ses seize valeurs ne s'ordonnent
#: pas, « Procedure completed » et « Awaiting committee decision » décrivent des
#: états, pas des degrés. La règle se dit donc par exclusion, et elle exclut ce
#: qui correspond au `depose` français : un texte dont le Parlement n'a encore
#: rien examiné. **58 dossiers sur les 20 442** qui portent un stade.
#:
#: Un stade que la source ajouterait ensuite n'est pas publié tant qu'il n'est
#: pas rangé ici : il sort déjà `stade_procedural: null` + son motif, et une
#: valeur inconnue qui se publierait par défaut ferait entrer dans le corpus un
#: état que personne n'a qualifié (§2 règle 5).
STADES_UE_NON_PUBLIES: frozenset[str] = frozenset({"ue_phase_preparatoire_parlement"})

#: Les stades européens qu'un texte porté doit avoir pour être publié.
STADES_UE_PUBLIES: frozenset[str] = STADES_PROCEDURAUX_UE - STADES_UE_NON_PUBLIES

KNOWN_STADES_PROCEDURAUX: frozenset[str] = STADES_PROCEDURAUX_AN | STADES_PROCEDURAUX_UE

# Nature du texte déposé, telle que la source l'encode (#689) : préfixe de l'uid
# du document associé au premier acte de dépôt — `PRJL` / `PION` / `PNRE`, lu par
# `gouvernement_textes.nature_texte_depose`, la même fonction que celle dont les
# fiches de gouvernement tirent l'origine d'un texte. `None` veut dire que la
# source ne l'établit pas (missions d'information, commissions d'enquête,
# déclarations du Gouvernement : 11 des 472 entrées publiées, dont 5 d'initiateur),
# jamais « aucune ».
#
# **Jamais tiré du libellé.** Les dossiers de la XV<sup>e</sup> portent des
# intitulés descriptifs — « Bioéthique », « CETA », « Coopération avec le
# Luxembourg » — et un discriminant « commence par *Projet de loi* » y manque
# 283 des 304 textes portés hors mandat électif des candidats déclarés. Une clé
# dérivée d'un libellé rouille, et se tait en rouillant (#672).
KNOWN_NATURES_TEXTE: frozenset[str] = frozenset({
    "projet_de_loi", "proposition_de_loi", "proposition_de_resolution",
})

# Rôle factuel de l'élu sur le texte. ``None`` signifie que la source ne
# permet pas de distinguer auteur, rapporteur et co-rapporteur.
#
# **`auteur` a été scindé par #689**, et ce n'est pas un renommage. Sous cette
# seule valeur cohabitaient deux actes de nature différente : la proposition de
# loi qu'un·e parlementaire dépose, et le projet de loi qu'un membre du
# Gouvernement porte au nom de l'exécutif — 316 des 472 entrées publiées, dont
# 282 des 283 d'`edouard-philippe`, toutes déposées pendant qu'il était Premier
# ministre. Un bilan de gouvernement est collectif ; l'attribuer à une personne
# donne à lire une productivité parlementaire irréelle, et rend deux candidats
# incomparables sous le même nom.
#
# Le rôle est **dérivé** de (rôle brut × `nature_texte`) par
# `normalize_profil._normalize_texte_porte` — jamais collecté, jamais fusionné,
# comme `chambres` (#493) et `meta.licence_donnees` (#530). `validate_profil`
# refuse toute contradiction entre les deux : c'est ce qui rend la redondance
# sûre, exactement comme `chambre` ne peut pas contredire `chambres[0]`.
#
# `auteur` SURVIT, et sa définition se rétrécit : « initiateur déclaré par la
# source sur un dossier dont elle n'établit pas la nature ». Il ne peut donc
# plus désigner un projet de loi. Il reste aussi la valeur des entrées
# collectées avant #689, tant qu'un run réel ne les a pas requalifiées — d'où
# sa présence ici, et le compteur de la §8 du quality gate qui mesure cette
# population décroissante.
KNOWN_ROLES_TEXTE: frozenset[str] = frozenset({
    "initiateur_projet_de_loi",
    "auteur_proposition_de_loi",
    "auteur_proposition_de_resolution",
    "auteur",
    "rapporteur",
    "co-rapporteur",
})

# Rôle d'initiateur attendu pour chaque nature (#689). Une entrée dont le rôle
# est un rôle d'initiateur DOIT porter la nature correspondante, et
# réciproquement : deux champs qui disent la même chose ne valent que s'ils ne
# peuvent pas se contredire. Les rôles de rapport (`rapporteur`,
# `co-rapporteur`) sont hors table : rapporter un projet de loi est une
# fonction parlementaire ordinaire, quelle que soit la nature du texte.
ROLE_INITIATEUR_PAR_NATURE: dict[str, str] = {
    "projet_de_loi": "initiateur_projet_de_loi",
    "proposition_de_loi": "auteur_proposition_de_loi",
    "proposition_de_resolution": "auteur_proposition_de_resolution",
}

#: Rôles d'initiateur, tous natures confondues — `auteur` compris, qui est
#: l'initiateur d'un texte dont la nature n'est pas établie.
ROLES_INITIATEUR_TEXTE: frozenset[str] = frozenset(
    set(ROLE_INITIATEUR_PAR_NATURE.values()) | {"auteur"}
)

# Type de scrutin, métadonnée du vote indépendante de son résultat. Image 1:1
# du `codeTypeVote` de l'open data AN depuis #639 : SPO -> public_ordinaire,
# SPS -> solennel, SAT -> tribune, MOC -> motion_censure. Mesuré sur les
# 17 748 scrutins publiés : 17 312 · 361 · 9 · 66. `null` reste possible — un
# code inconnu n'est jamais rangé d'office dans le plus fréquent (§2 règle 5).
# SSG (Congrès) est absent : ces scrutins sont écartés en amont sur leur uid.
KNOWN_TYPES_SCRUTIN: frozenset[str] = frozenset({
    "public_ordinaire", "solennel", "tribune", "motion_censure",
})

# Type d'entrée de vote : un vote sur motion de censure liée à un 49.3 est
# toujours une entrée de vote séparée, jamais fusionnée avec la position sur
# le texte concerné.
KNOWN_TYPES_VOTE: frozenset[str] = frozenset({"vote_texte", "motion_censure"})

# Version du schéma de `pivot_data/scrutins.json` (#432). Distincte de
# SCHEMA_VERSION : la liste partagée des scrutins et les profils évoluent
# séparément, et les confondre obligerait à réécrire tous les profils pour un
# changement qui ne les touche pas.
SCRUTINS_SCHEMA_VERSION = "scrutins-v1"

# Provenance de la `legislature` d'un scrutin (#432, voir scrutins_legislature).
# Nomenclature fermée, et le point n'est pas cosmétique : une législature
# dérivée d'un calendrier ne doit jamais passer pour une donnée collectée.
KNOWN_PROVENANCES_LEGISLATURE: frozenset[str] = frozenset({
    "collectee", "resolue_par_jumeau", "derivee_du_calendrier",
})

# Type de déposant d'un amendement.
KNOWN_TYPES_DEPOSANT: frozenset[str] = frozenset({
    "gouvernement", "commission_rapporteur", "depute",
})

# Rôle de signature de l'élu sur un amendement.
KNOWN_ROLES_SIGNATAIRE_AMENDEMENT: frozenset[str] = frozenset({
    "auteur_principal", "cosignataire",
})

# Base juridique d'irrecevabilité d'un amendement (art. 40 : recevabilité
# financière ; art. 45 : lien avec le texte — "cavalier législatif").
KNOWN_BASES_IRRECEVABILITE: frozenset[str] = frozenset({"art. 40", "art. 45"})

# Provenance du profil (meta.provenance) : POURQUOI ce profil existe. Trois
# valeurs, une par population de pivot_data/profiles/ (src/population_profils.py
# les nomme et les ventile, #630) :
#   - "candidat_declare" : candidat déclaré à la présidentielle
#     (raw_data/candidats.json, source éditoriale) — sa fiche est publiée ;
#   - "roster_groupe" : extrait via le roster réel d'un groupe parlementaire
#     (generate_roster_candidats.py, #188) — il existe pour être agrégé ;
#   - "roster_gouvernement" : membre d'un gouvernement recensé par AMO30 et
#     qu'aucun roster de groupe n'amène (#996 lot 3). 124 de ces personnes
#     n'ont jamais été députées : sans cette provenance, la fiche d'un
#     gouvernement n'agrégerait que celles qui l'ont été.
# Politique de fusion (voir merge_profile.merge_pivot_profile) : un profil
# "candidat_declare" n'est jamais rétrogradé vers une provenance de roster par
# une régénération roster-driven du même slug, pour ne jamais perdre
# l'enrichissement éditorial déjà présent (parti, etc.).
KNOWN_PROVENANCES: frozenset[str] = frozenset({
    "candidat_declare", "roster_groupe", "roster_gouvernement",
})

# --- #539 : identifiants de source, publiés dans le pivot -------------------

#: Référentiels dont un profil publie l'identifiant (`identifiants`). Fermé
#: comme les autres `KNOWN_*` : on étend le frozenset, on ne le contourne pas.
#: Les quatre clés sont TOUJOURS présentes dans le bloc — une clé absente
#: laisserait un lecteur choisir entre « pas d'identifiant » et « le producteur
#: n'y a pas pensé », ce que le bloc existe précisément pour éviter (§2.5).
KNOWN_IDENTIFIANTS: frozenset[str] = frozenset({"an", "senat", "europarl", "hatvp"})

#: Institutions d'un mandat national ANTÉRIEUR à la couverture de l'Assemblée
#: (#860), porté par `mandats_anterieurs` depuis `raw_data/mandats_anterieurs.json`.
#: Le Sénat n'y est pas : #528 a sorti du périmètre jusqu'à l'usage biographique
#: « a été sénateur de … à … ». L'y ajouter est la reprise de cette décision.
KNOWN_INSTITUTIONS_ANTERIEURES: frozenset[str] = frozenset({"assemblee_nationale", "gouvernement"})

#: Motif d'une fin de mandat antérieur publiée `null` (§2 règle 5).
KNOWN_MOTIFS_MANDAT_ANTERIEUR_NON_RESOLU: frozenset[str] = frozenset({"source_primaire_non_trouvee"})

#: Motif d'un `mandats_anterieurs` publié `null` sur une fiche de candidat.
KNOWN_MOTIFS_MANDATS_ANTERIEURS_NON_RESOLUS: frozenset[str] = frozenset({"non_relu"})

#: Comment une ABSENCE de mandat antérieur a été constatée (#860). Une liste
#: vide affirme « aucun mandat avant le 19/06/2002 » : §2 règle 2 veut savoir
#: sur quoi. Les deux valeurs ne se valent pas et ne se remplacent pas —
#: `lecture_fiche_sycomore` est une lecture de la source primaire par le
#: pipeline, reproductible ; `relecture_humaine` est une signature, que rien
#: d'automatique ne pose à la place de quelqu'un.
KNOWN_METHODES_CONSTAT_ANTERIEUR: frozenset[str] = frozenset(
    {"lecture_fiche_sycomore", "relecture_humaine"}
)


def valider_mandats_anterieurs(profil: dict[str, Any]) -> list[str]:
    """`mandats_anterieurs` (#860) : une liste relue, ou `null` avec son motif."""
    errors: list[str] = []
    valeur = profil.get("mandats_anterieurs")
    non_resolu = profil.get("mandats_anterieurs_non_resolu")
    if valeur is None:
        motif = (non_resolu or {}).get("motif") if isinstance(non_resolu, dict) else None
        if motif not in KNOWN_MOTIFS_MANDATS_ANTERIEURS_NON_RESOLUS:
            errors.append(
                "'mandats_anterieurs' vaut null sans 'mandats_anterieurs_non_resolu.motif' "
                f"dans {sorted(KNOWN_MOTIFS_MANDATS_ANTERIEURS_NON_RESOLUS)} (§2 règle 5)."
            )
        return errors
    if not isinstance(valeur, list):
        return ["'mandats_anterieurs' doit être une liste ou null."]
    if non_resolu is not None:
        errors.append("'mandats_anterieurs_non_resolu' présent sur une liste relue.")
    # Une liste VIDE affirme « aucun mandat avant le 19/06/2002 » : c'est un
    # fait publié, et il porte sa source comme les autres (§2 règle 2). Une
    # liste pleine, elle, la porte ligne par ligne — le constat y serait un
    # second endroit pour le même fait.
    constat = profil.get("mandats_anterieurs_constat")
    if not valeur:
        if not isinstance(constat, dict):
            errors.append(
                "'mandats_anterieurs' est une liste vide sans "
                "'mandats_anterieurs_constat' : une absence constatée dit sur quoi "
                "elle se fonde (§2 règle 2)."
            )
        else:
            if not str(constat.get("source_url") or "").startswith("https://"):
                errors.append("'mandats_anterieurs_constat.source_url' absente ou non https.")
            if constat.get("methode") not in KNOWN_METHODES_CONSTAT_ANTERIEUR:
                errors.append(
                    f"'mandats_anterieurs_constat.methode' {constat.get('methode')!r} hors "
                    f"de {sorted(KNOWN_METHODES_CONSTAT_ANTERIEUR)}."
                )
            if not constat.get("constate_le"):
                errors.append("'mandats_anterieurs_constat.constate_le' absent.")
    elif constat is not None:
        errors.append(
            "'mandats_anterieurs_constat' présent sur une liste non vide — la "
            "source vit alors sur chaque ligne."
        )
    for i, m in enumerate(valeur):
        if not isinstance(m, dict):
            errors.append(f"mandats_anterieurs[{i}] : objet attendu."); continue
        if m.get("institution") not in KNOWN_INSTITUTIONS_ANTERIEURES:
            errors.append(f"mandats_anterieurs[{i}] : institution {m.get('institution')!r} inconnue.")
        if not m.get("source_url"):
            errors.append(f"mandats_anterieurs[{i}] : source_url absente (§2 règle 2).")
        if not m.get("debut"):
            errors.append(f"mandats_anterieurs[{i}] : debut absent.")
        if m.get("fin") is None and (m.get("fin_non_resolue") or {}).get("motif") not in KNOWN_MOTIFS_MANDAT_ANTERIEUR_NON_RESOLU:
            errors.append(f"mandats_anterieurs[{i}] : fin nulle sans motif (§2 règle 5).")
    return errors

#: Forme attendue de chaque identifiant. `None` = aucune contrainte de forme.
#: `an` reprend le motif de `correspondance_acteurs_an` mot pour mot : deux
#: expressions du même invariant divergeraient en silence.
_FORMES_IDENTIFIANTS: dict[str, Optional[str]] = {
    "an": r"^PA\d+$",
    "senat": None,
    "europarl": r"^\d+$",
    "hatvp": r"^https?://",
}

#: Compilée une fois : `validate_profil` s'en sert aussi pour `identite.uri_hatvp`
#: (#556), qui est la MÊME valeur que `identifiants.hatvp` — donc la même forme,
#: lue au même endroit. Deux motifs pour un seul champ divergeraient en silence.
_RE_HATVP = re.compile(_FORMES_IDENTIFIANTS["hatvp"] or "")

#: Listes métier dont la couverture est déclarée (#539). **Cinq**, et pas six :
#: `tags_thematiques` n'en est pas une — c'est une aide à la lecture DÉRIVÉE des
#: autres listes (AGENTS.md §2.8), sans source propre donc sans borne propre.
#: `sources` et `chambres` sont dérivées de la même façon.
LISTES_COUVERTES: tuple[str, ...] = (
    "mandats", "votes", "textes_portes", "interventions", "amendements",
)

#: Les quatre états de couverture (#539). Nomenclature fermée, alignée sur celle
#: déjà fermée pour les gouvernements (`couverture_dossiers.py`, #399) plutôt que
#: réinventée.
#:
#: `couvert` est le complément sans lequel les trois autres ne suffisent pas :
#: c'est l'état où une liste vide DIT VRAI — collecté, dans le périmètre de la
#: source, réellement zéro. Sans lui, une liste sans entrée retombe dans « on ne
#: sait pas » et le produit perd le zéro constaté, qui est précisément ce qu'il
#: existe pour donner. §2.5 interdit de confondre un zéro mesuré avec une
#: absence, pas de publier le premier.
#:
#: `partielle` de #399 ne devient PAS un cinquième état : la portée l'exprime en
#: **deux entrées**, qui disent en plus *où* passe la frontière.
ETAT_COUVERT = "couvert"
ETAT_FAIT_ETABLI = "fait_etabli"
ETAT_HORS_COUVERTURE = "hors_couverture"
ETAT_NON_COLLECTE = "non_collecte"

ETATS_COUVERTURE: frozenset[str] = frozenset({
    ETAT_COUVERT, ETAT_FAIT_ETABLI, ETAT_HORS_COUVERTURE, ETAT_NON_COLLECTE,
})

#: Cause d'un `non_collecte` — obligatoire **si et seulement si** l'état vaut
#: `non_collecte`. Le « si et seulement si » est ce qui empêche la cause d'être
#: omise en silence : sans lui, une entrée `non_collecte` sans cause repasserait
#: pour un défaut de saisie plutôt que pour ce qu'elle est, une affirmation
#: incomplète.
#:
#: **Trois causes depuis #562, et pas deux.** `panne` dit « la source n'a pas
#: répondu » : c'est une affirmation SUR L'ASSEMBLÉE NATIONALE. Y ranger un
#: défaut de notre propre code lui impute une faute qui n'est pas la sienne —
#: mesuré : 99 profils publiés sur 481 déclaraient une panne AN pour un
#: `TypeError` du dépôt (tri d'amendements sur une date `xsi:nil`). D'où
#: `defaut_collecte`, le troisième terme : la collecte n'a pas abouti, et c'est
#: nous. Un lecteur n'a pas à savoir lequel des deux, mais le produit n'a pas le
#: droit de se tromper de coupable.
CAUSE_PANNE = "panne"
CAUSE_PAR_DECISION = "par_decision"
CAUSE_DEFAUT_COLLECTE = "defaut_collecte"

CAUSES_NON_COLLECTE: frozenset[str] = frozenset({
    CAUSE_PANNE, CAUSE_PAR_DECISION, CAUSE_DEFAUT_COLLECTE,
})

#: Marqueurs qui trahissent qu'une `preuve` n'est pas une preuve mais le texte
#: d'une **exception de programmation** (#562).
#:
#: `preuve` est le champ qui distingue une affirmation sourcée d'une affirmation
#: nue (AGENTS.md §2.2) : il doit nommer une source, une borne d'archive ou une
#: décision. Y recopier un message d'exception le vide de son sens tout en
#: passant le seul contrôle qui existait — « chaîne non vide ». C'est ainsi que
#: `'<' not supported between instances of 'dict' and 'str'` s'est retrouvé
#: publié comme preuve sur 99 profils sur 481.
#:
#: La liste ne bannit PAS toute mention d'exception : une preuve de `panne` cite
#: légitimement ce que la source a renvoyé, y compris le nom d'une erreur réseau
#: (`ConnectionError`, `IncompleteRead`, `SSLError`…) — c'est un fait sur la
#: source. Ce qui est refusé, ce sont les marqueurs qui ne peuvent venir que
#: d'un **défaut de code** : ils ne disent rien de la source, seulement de nous.
#: Vérifié sur les 3 766 entrées de couverture des 481 profils publiés au
#: 28/08/2026 : 99 rejetées, toutes de la même famille, aucune autre.
PREUVE_MARQUEURS_DEFAUT_CODE: tuple[str, ...] = (
    "Traceback (most recent call last)",
    "not supported between instances",
    "unsupported operand type",
    "object has no attribute",
    "object is not subscriptable",
    "object is not callable",
    "object is not iterable",
    "TypeError",
    "AttributeError",
    "KeyError",
    "IndexError",
    "NameError",
    "UnboundLocalError",
    "ZeroDivisionError",
    "RecursionError",
    "AssertionError",
    "NotImplementedError",
)

#: `File "…", line 42` — l'autre forme, sans nom de classe.
_PREUVE_CADRE_PYTHON = re.compile(r'File "[^"]+", line \d+')


def marqueur_defaut_code(preuve: str) -> Optional[str]:
    """Le marqueur d'exception trouvé dans `preuve`, ou `None` si elle est saine."""
    for marqueur in PREUVE_MARQUEURS_DEFAUT_CODE:
        if marqueur in preuve:
            return marqueur
    trouve = _PREUVE_CADRE_PYTHON.search(preuve)
    return trouve.group(0) if trouve else None


#: Champs d'`identite` qui portent un LIBELLÉ recopié d'AMO30 (#659), donc une
#: chaîne ou `null` — jamais un objet.
#:
#: `uri_hatvp` n'est pas dans la liste : il a sa propre règle, plus étroite
#: (c'est une URI, et sa forme est vérifiée). `num_circo` et `date_naissance`
#: non plus, et c'est mesuré : le corpus publié les écrit en chaîne, mais
#: `num_circo` arrive en `int` de certains profils bruts, et refuser un entier
#: là où la source dit un numéro serait une règle de type déguisée en règle
#: d'absence. Ce qui réunit les champs retenus, c'est l'origine — `json/acteur/*.json`, dont le convertisseur XML rend
#: `{"@xsi:nil": "true"}` pour n'importe quel élément déclaré vide, sans
#: connaître le nom du champ (#556). Un dict non vide est truthy : un
#: consommateur qui teste `if identite["civilite"]` croit tenir une civilité.
#:
#: La règle porte sur le TYPE, pas sur le contenu : elle refuse le marqueur, pas
#: un libellé inattendu. Fermer les valeurs de `civilite` en `frozenset KNOWN_*`
#: aurait été possible — la source n'en écrit que deux, `M.` et `Mme`, sur ses
#: 3 117 fiches — mais ferait échouer le contrôle qualité en dur le jour où
#: l'Assemblée en écrit une troisième, sur une donnée qu'elle seule décide.
CHAMPS_IDENTITE_TEXTE_LIBRE: tuple[str, ...] = (
    "civilite",
    "profession",
    "famille_socioprofessionnelle",
    "categorie_socioprofessionnelle",
    "lieu_naissance",
)


#: Blocs de champs dont la provenance est publiée champ par champ (#603).
#:
#: **Un seul pour l'instant, et c'est une décision, pas un début d'inventaire.**
#: La provenance par champ ne répond à une question que là où PLUSIEURS SOURCES
#: écrivent le même champ. Mesuré le 30/08/2026 : `src/group_profile.py` ne lit
#: jamais `identite` (zéro occurrence) et ne consomme que des listes, déjà
#: fusionnées additivement — sur une liste, l'entrée porte déjà sa source. Le
#: seul bloc composé champ par champ est `identite` (#601), et c'est là que le
#: conflit de sources existe : un profil peut avoir un mandat européen en plus
#: de son mandat national.
#:
#: `identifiants` est composé clé par clé lui aussi (#539) mais n'entre pas ici :
#: chacune de ses clés EST le nom de sa source (`an`, `europarl`, `hatvp`), donc
#: sa provenance est déjà lisible sans second bloc.
BLOCS_PROVENANCE_CHAMPS: tuple[str, ...] = ("identite",)


#: Clés exactes d'une entrée de `meta.avertissements` (#642). Fermées : une clé
#: en plus serait une seconde façon de dire quelque chose, sans que rien la
#: valide.
CLES_AVERTISSEMENT: frozenset[str] = frozenset({"message", "destinataire"})


def valider_avertissements(avertissements: Any, warnings: Any) -> list[str]:
    """Vérifie `meta.avertissements[]`, le jumeau typé de `meta.warnings[]` (#642).

    Trois invariants, et c'est le troisième qui fait travailler le bloc :

    1. **Forme fermée.** Une entrée est un dict de `CLES_AVERTISSEMENT`, ni plus
       ni moins. `destinataire` est une valeur de `DESTINATAIRES_AVERTISSEMENT`
       ou `null` — « personne ne l'a déclaré », comme `provenance_champs`
       publie `{"source": null}` plutôt que d'omettre l'entrée (#603).
    2. **La clé est obligatoire, la valeur peut être inconnue.** Une entrée sans
       `destinataire` est refusée : l'omission serait une troisième façon de
       dire « on ne sait pas », à côté du `null` qui le dit déjà. C'est le même
       « si et seulement si » que `couverture[].cause` sur `non_collecte`
       (#539).
    3. **L'alignement avec `warnings`.** Même longueur, mêmes messages, même
       ordre. C'est ce qui interdit au jumeau de dériver : un avertissement
       publié sans entrée typée, ou une entrée typée qui ne correspond à aucun
       avertissement publié, est refusé au lieu de passer inaperçu — le défaut
       exact que ce lot corrige.
    """
    errors: list[str] = []

    if not isinstance(avertissements, list):
        return [
            "'meta.avertissements' doit être une liste, reçu : "
            f"{type(avertissements).__name__}."
        ]

    for i, entree in enumerate(avertissements):
        prefixe = f"meta.avertissements[{i}]"
        if not isinstance(entree, dict):
            errors.append(
                f"{prefixe} doit être un dict, reçu : {type(entree).__name__}."
            )
            continue
        inconnues = sorted(set(entree) - CLES_AVERTISSEMENT)
        if inconnues:
            errors.append(
                f"{prefixe} porte des clés hors nomenclature : {inconnues!r}. "
                f"Clés connues : {sorted(CLES_AVERTISSEMENT)}."
            )
        if not isinstance(entree.get("message"), str):
            errors.append(f"{prefixe}.message doit être une chaîne.")
        if "destinataire" not in entree:
            errors.append(
                f"{prefixe} ne déclare pas de destinataire. La clé est "
                "obligatoire ; `null` dit « inconnu », l'omission ne dit rien "
                "(#642)."
            )
        else:
            destinataire = entree.get("destinataire")
            if destinataire is not None and destinataire not in DESTINATAIRES_AVERTISSEMENT:
                errors.append(
                    f"{prefixe}.destinataire non reconnu : {destinataire!r}. "
                    f"Valeurs connues : {sorted(DESTINATAIRES_AVERTISSEMENT)}, "
                    "ou null."
                )

    if isinstance(warnings, list):
        if len(avertissements) != len(warnings):
            errors.append(
                f"'meta.avertissements' compte {len(avertissements)} entrée(s) "
                f"pour {len(warnings)} avertissement(s) publié(s) : le jumeau "
                "typé est aligné sur `meta.warnings`, entrée par entrée (#642)."
            )
        else:
            for i, (entree, warning) in enumerate(zip(avertissements, warnings)):
                if not isinstance(entree, dict):
                    continue
                if entree.get("message") != str(warning):
                    errors.append(
                        f"meta.avertissements[{i}].message ne reprend pas "
                        f"meta.warnings[{i}] : {entree.get('message')!r} vs "
                        f"{str(warning)!r}."
                    )

    return errors


def valider_provenance_champs(provenance: Any, profil: dict[str, Any]) -> list[str]:
    """Vérifie `meta.provenance_champs` d'un profil pivot (#603).

    Trois invariants, et le troisième est celui qui fait travailler le bloc :

    1. **Forme fermée.** Les blocs décrits sont ceux de `BLOCS_PROVENANCE_CHAMPS`,
       chaque entrée porte exactement `source` et `synchro_le`, et `source` est
       `null` ou l'un des `KNOWN_SOURCE_TYPES`.
    2. **Une date sans source n'est pas une traçabilité.** `synchro_le` renseigné
       avec `source` à `null` publierait un horodatage que rien ne rattache — la
       forme même d'une preuve qui n'en est pas une (§2.2).
    3. **Complétude, dans les deux sens.** Tout champ publié et renseigné du bloc
       décrit a son entrée ; aucune entrée ne décrit un champ que le bloc ne
       publie pas. Sans le premier sens, l'absence d'entrée deviendrait une
       seconde façon de dire « on ne sait pas », à côté de `source: null` qui le
       dit déjà — et deux façons de dire la même chose, c'est celle qu'on oublie
       de lire qui gagne. Sans le second, on publierait la provenance d'une
       valeur qui n'existe pas.
    """
    if not isinstance(provenance, dict):
        return [
            "'meta.provenance_champs' doit être un dict, reçu : "
            f"{type(provenance).__name__}."
        ]

    errors: list[str] = []
    inconnus = sorted(set(provenance) - set(BLOCS_PROVENANCE_CHAMPS))
    if inconnus:
        errors.append(
            f"meta.provenance_champs décrit des blocs hors nomenclature : "
            f"{inconnus!r}. Blocs connus : {list(BLOCS_PROVENANCE_CHAMPS)}."
        )

    for nom_bloc in BLOCS_PROVENANCE_CHAMPS:
        if nom_bloc not in provenance:
            continue
        entrees = provenance.get(nom_bloc)
        if not isinstance(entrees, dict):
            errors.append(
                f"meta.provenance_champs.{nom_bloc} doit être un dict, reçu : "
                f"{type(entrees).__name__}."
            )
            continue

        bloc = profil.get(nom_bloc)
        publies = {
            champ
            for champ, valeur in (bloc.items() if isinstance(bloc, dict) else ())
            if valeur not in (None, "", [], {})
        }
        manquants = sorted(publies - set(entrees))
        if manquants:
            errors.append(
                f"meta.provenance_champs.{nom_bloc} est incomplète : {manquants!r} "
                "sont publiés et renseignés sans provenance. Une provenance "
                "inconnue se déclare (source: null), elle ne s'omet pas (§2.5)."
            )
        orphelins = sorted(set(entrees) - publies)
        if orphelins:
            errors.append(
                f"meta.provenance_champs.{nom_bloc} décrit des champs que "
                f"'{nom_bloc}' ne publie pas : {orphelins!r}."
            )

        for champ, entree in entrees.items():
            errors.extend(_valider_entree_provenance(nom_bloc, champ, entree))
    return errors


def _valider_entree_provenance(nom_bloc: str, champ: str, entree: Any) -> list[str]:
    prefixe = f"meta.provenance_champs.{nom_bloc}.{champ}"
    if not isinstance(entree, dict):
        return [f"{prefixe} doit être un dict, reçu : {type(entree).__name__}."]

    errors: list[str] = []
    attendues = {"source", "synchro_le"}
    if set(entree) != attendues:
        errors.append(
            f"{prefixe} porte {sorted(entree)!r}, attendu exactement "
            f"{sorted(attendues)!r}."
        )

    source = entree.get("source")
    if source is not None and source not in KNOWN_SOURCE_TYPES:
        errors.append(
            f"{prefixe}.source non reconnue : {source!r}. "
            f"Valeurs connues : {sorted(KNOWN_SOURCE_TYPES)}, ou null."
        )

    synchro_le = entree.get("synchro_le")
    if synchro_le is not None and not isinstance(synchro_le, str):
        errors.append(
            f"{prefixe}.synchro_le doit être un horodatage (chaîne) ou null, "
            f"reçu : {type(synchro_le).__name__}."
        )
    if source is None and synchro_le is not None:
        errors.append(
            f"{prefixe} date une provenance qu'elle ne nomme pas : "
            f"synchro_le={synchro_le!r} avec source=null. Un horodatage que rien "
            "ne rattache à une source n'est pas une traçabilité (§2.2)."
        )
    return errors


def valider_couverture(couverture: Any) -> list[str]:
    """Vérifie le bloc `couverture` d'un profil pivot (#539).

    Isolée de `validate_profil` parce que la fabrique (`couverture_profil.py`)
    s'en sert pour se contrôler elle-même, et que les tests l'exercent seule :
    la règle est écrite une fois, appliquée aux deux bouts.

    Renvoie la liste des erreurs ; liste vide = bloc conforme.
    """
    if not isinstance(couverture, dict):
        return [f"'couverture' doit être un dict, reçu : {type(couverture).__name__}."]

    errors: list[str] = []
    inconnues = sorted(set(couverture) - set(LISTES_COUVERTES))
    if inconnues:
        errors.append(
            f"'couverture' porte des listes hors nomenclature : {inconnues!r}. "
            f"Listes connues : {list(LISTES_COUVERTES)}."
        )
    manquantes = sorted(set(LISTES_COUVERTES) - set(couverture))
    if manquantes:
        errors.append(
            f"'couverture' est incomplète : {manquantes!r} sans entrée. La "
            "complétude est obligatoire — un défaut implicite « pas d'entrée = "
            "couvert » réintroduirait l'ambiguïté que le bloc retire."
        )

    for liste in LISTES_COUVERTES:
        entrees = couverture.get(liste)
        if entrees is None:
            continue
        if not isinstance(entrees, list):
            errors.append(
                f"couverture.{liste} doit être une liste d'entrées, reçu : "
                f"{type(entrees).__name__}."
            )
            continue
        if not entrees:
            errors.append(
                f"couverture.{liste} est vide : chaque liste métier porte au "
                "moins une entrée."
            )
            continue
        for i, entree in enumerate(entrees):
            errors.extend(_valider_entree_couverture(liste, i, entree))
    return errors


def _valider_entree_couverture(liste: str, i: int, entree: Any) -> list[str]:
    prefixe = f"couverture.{liste}[{i}]"
    if not isinstance(entree, dict):
        return [f"{prefixe} doit être un dict, reçu : {type(entree).__name__}."]

    errors: list[str] = []
    etat = entree.get("etat")
    if etat not in ETATS_COUVERTURE:
        errors.append(
            f"{prefixe}.etat non reconnu : {etat!r}. "
            f"Valeurs connues : {sorted(ETATS_COUVERTURE)}."
        )

    # Le « si et seulement si » de la cause, dans les deux sens.
    cause = entree.get("cause")
    if etat == ETAT_NON_COLLECTE:
        if cause not in CAUSES_NON_COLLECTE:
            errors.append(
                f"{prefixe}.cause est obligatoire sur un '{ETAT_NON_COLLECTE}' et "
                f"doit valoir l'une de {sorted(CAUSES_NON_COLLECTE)}, reçu : "
                f"{cause!r}. Sans elle, « nous n'avons pas réussi à collecter » et "
                "« nous avons choisi de ne pas collecter » se confondent."
            )
    elif cause is not None:
        errors.append(
            f"{prefixe}.cause ({cause!r}) n'a de sens que sur un "
            f"'{ETAT_NON_COLLECTE}', pas sur {etat!r}."
        )

    preuve = entree.get("preuve")
    if not (isinstance(preuve, str) and preuve.strip()):
        errors.append(
            f"{prefixe}.preuve est obligatoire : borne d'archive, identifiant de "
            "source, entrée de la table de correspondance ou politique nommée. "
            "Une entrée sans preuve est une affirmation sans source (§2.2)."
        )
    else:
        # « Chaîne non vide » ne suffit pas : c'est ce seul contrôle qui a laissé
        # passer un message de `TypeError` comme preuve sur 99 profils (#562).
        marqueur = marqueur_defaut_code(preuve)
        if marqueur is not None:
            errors.append(
                f"{prefixe}.preuve porte un fragment d'exception de programmation "
                f"({marqueur!r}) : {preuve!r}. Une exception n'est pas une source. "
                "Une preuve nomme une source, une borne ou une décision ; un défaut "
                f"de code se publie en cause '{CAUSE_DEFAUT_COLLECTE}', avec sa "
                "trace en meta.warnings, jamais dans ce champ (§2.2)."
            )

    constate_le = entree.get("constate_le")
    if not isinstance(constate_le, str):
        errors.append(f"{prefixe}.constate_le est obligatoire (date ISO).")
    else:
        try:
            _date.fromisoformat(constate_le)
        except ValueError:
            errors.append(
                f"{prefixe}.constate_le n'est pas une date ISO : {constate_le!r}."
            )

    portee = entree.get("portee")
    errors.extend(_valider_portee(prefixe, portee))
    # `portee` est facultative en général — mais pas sur un `hors_couverture` :
    # dire qu'une source ne couvre pas, sans dire QUOI, n'informe personne, et
    # une entrée globale de cet état contredirait la liste entière.
    if etat == ETAT_HORS_COUVERTURE and portee is None:
        errors.append(
            f"{prefixe} déclare '{ETAT_HORS_COUVERTURE}' sans portée : une source "
            "qui ne couvre pas doit dire ce qu'elle ne couvre pas."
        )
    return errors


def _valider_portee(prefixe: str, portee: Any) -> list[str]:
    """`portee` est FACULTATIVE : absente, l'entrée vaut pour tout le profil."""
    if portee is None:
        return []
    if not isinstance(portee, dict):
        return [
            f"{prefixe}.portee doit être un dict ou null, reçu : "
            f"{type(portee).__name__}."
        ]
    if not portee:
        return [
            f"{prefixe}.portee est un dict vide : une portée qui ne borne rien "
            "n'est pas une portée — l'omettre dit exactement la même chose."
        ]

    errors: list[str] = []
    inconnues = sorted(set(portee) - {"legislature", "debut", "fin"})
    if inconnues:
        errors.append(
            f"{prefixe}.portee porte des clés non reconnues : {inconnues!r}. "
            "Formes admises : {'legislature': n} ou {'debut': ..., 'fin': ...}."
        )
    if "legislature" in portee:
        legislature = portee["legislature"]
        if not isinstance(legislature, int) or isinstance(legislature, bool) or legislature <= 0:
            errors.append(
                f"{prefixe}.portee.legislature doit être un entier positif, reçu : "
                f"{legislature!r}."
            )
        if "debut" in portee or "fin" in portee:
            errors.append(
                f"{prefixe}.portee mêle 'legislature' et un intervalle de dates : "
                "les deux formes disent la même chose de deux façons, et la "
                "seconde ne dit pas laquelle croire."
            )
    for borne in ("debut", "fin"):
        valeur = portee.get(borne)
        if valeur is None:
            continue
        if not isinstance(valeur, str):
            errors.append(
                f"{prefixe}.portee.{borne} doit être une date ISO, reçu : "
                f"{type(valeur).__name__}."
            )
            continue
        try:
            _date.fromisoformat(valeur)
        except ValueError:
            errors.append(
                f"{prefixe}.portee.{borne} n'est pas une date ISO : {valeur!r}."
            )
    return errors


#: Ordre de publication des clés d'`identifiants`. Stable d'un run à l'autre —
#: sans lui git verrait une différence à chaque régénération.
ORDRE_IDENTIFIANTS: tuple[str, ...] = ("an", "senat", "europarl", "hatvp")


def identifiants_vides() -> dict[str, Optional[str]]:
    """Bloc `identifiants` complet, toutes valeurs à `null` (#539)."""
    return {cle: None for cle in ORDRE_IDENTIFIANTS}


def poser_identifiant(profil: dict[str, Any], cle: str, valeur: Any) -> None:
    """Écrit `identifiants[cle]` sur un profil, sans jamais l'écraser par `null`.

    La seule fabrique du bloc, et le pendant de `_prefer_non_empty` côté fusion :
    un profil AN + PE passe par deux normaliseurs, et le second ne doit pas
    effacer ce que le premier a établi. Une valeur vide est ignorée, jamais
    écrite — `null` veut dire « aucun identifiant connu », pas « le dernier
    écrivain n'en avait pas » (§2.5).
    """
    if cle not in KNOWN_IDENTIFIANTS:
        raise ValueError(
            f"identifiants.{cle} n'est pas un référentiel connu "
            f"({sorted(KNOWN_IDENTIFIANTS)}) — on étend KNOWN_IDENTIFIANTS, "
            "on ne le contourne pas."
        )
    bloc = profil.get("identifiants")
    if not isinstance(bloc, dict):
        bloc = identifiants_vides()
        profil["identifiants"] = bloc
    for manquante in ORDRE_IDENTIFIANTS:
        bloc.setdefault(manquante, None)
    if valeur is None:
        return
    # Refus BRUYANT d'une valeur qui n'est pas une chaîne. Ce n'est pas de la
    # rigueur gratuite : 186 des 476 profils publiés portent, dans
    # `identite.uri_hatvp`, le marqueur XML brut `{"@xsi:nil": "true"}` — le
    # « pas de déclaration » d'AMO30 recopié tel quel au lieu d'être lu. Un
    # `str(valeur)` obligeant aurait publié cet objet comme identifiant HATVP
    # sur 186 profils, et le schéma ne l'aurait pas rattrapé puisqu'il serait
    # devenu une chaîne. L'appelant filtre, ou il apprend qu'il a un défaut.
    if not isinstance(valeur, str):
        raise TypeError(
            f"identifiants.{cle} : une chaîne ou null, pas {type(valeur).__name__} "
            f"({valeur!r}). Une valeur non normalisée par l'appelant n'est pas un "
            "identifiant — voir les 186 `uri_hatvp` au format XML nil du corpus."
        )
    if not valeur.strip():
        return
    bloc[cle] = valeur.strip()


def valider_identifiants(identifiants: Any) -> list[str]:
    """Vérifie le bloc `identifiants` d'un profil pivot (#539)."""
    if not isinstance(identifiants, dict):
        return [
            f"'identifiants' doit être un dict, reçu : {type(identifiants).__name__}."
        ]

    errors: list[str] = []
    inconnues = sorted(set(identifiants) - KNOWN_IDENTIFIANTS)
    if inconnues:
        errors.append(
            f"'identifiants' porte des référentiels non reconnus : {inconnues!r}. "
            f"Valeurs connues : {sorted(KNOWN_IDENTIFIANTS)}."
        )
    manquants = sorted(KNOWN_IDENTIFIANTS - set(identifiants))
    if manquants:
        errors.append(
            f"'identifiants' est incomplet : {manquants!r} absent(s). Les quatre "
            "clés sont toujours présentes — `null` dit « pas d'identifiant connu », "
            "une clé absente ne dit rien (§2.5)."
        )
    for cle, forme in _FORMES_IDENTIFIANTS.items():
        valeur = identifiants.get(cle)
        if valeur is None:
            continue
        if not isinstance(valeur, str):
            errors.append(
                f"identifiants.{cle} doit être une chaîne ou null, reçu : "
                f"{type(valeur).__name__}."
            )
            continue
        if forme and not re.match(forme, valeur):
            errors.append(
                f"identifiants.{cle} ne respecte pas la forme attendue "
                f"({forme}) : {valeur!r}."
            )
    return errors


def make_empty_profil(id_: str, nom: str, provenance: str = "candidat_declare") -> dict[str, Any]:
    """Crée un profil pivot v1 vide avec des valeurs par défaut.

    Args:
        id_: identifiant unique du profil. Pour un profil de
             `pivot_data/profiles/`, c'est le **slug** — le nom du fichier,
             sans préfixe de provenance (#487, épic #486) : le préfixe
             `nosdeputes:`/`nossenateurs:` dérivait de la chambre qui avait
             répondu à la collecte, donc changeait de valeur sur une carrière
             inchangée. Ex. "jean-luc-melenchon".
             Les outils autonomes qui construisent un pivot sans slug
             (`mep_profile.py --ep-id`) gardent un identifiant de source
             explicite, ex. "parltrack:197451" : mieux vaut ça qu'un slug
             inventé à partir d'un nom collecté.
        nom: nom complet de l'élu.
        provenance: origine du profil, "candidat_declare" (défaut, raw_data/candidats.json),
                    "roster_groupe" (extraction pilotée par le roster réel d'un
                    groupe parlementaire, #188) ou "roster_gouvernement" (membre
                    d'un gouvernement recensé par AMO30, #996). Voir KNOWN_PROVENANCES.

    Returns:
        Profil pivot dict initialisé, prêt à être enrichi.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "id": id_,
        "nom": nom,
        # #493 : les deux champs sortent de `deriver_chambres()` et de nulle part
        # ailleurs. Un profil vide n'a pas de mandat, donc pas de chambre.
        "chambres": [],
        "chambre": None,
        "parti": None,
        "groupe": None,
        "identite": None,
        # #539 : les quatre clés sont toujours là, à `null` par défaut. Un bloc
        # partiel laisserait un lecteur choisir entre « pas d'identifiant » et
        # « le producteur n'y a pas pensé » — c'est ce que le bloc retire.
        "identifiants": identifiants_vides(),
        "sources": [],
        "mandats": [],
        "votes": [],
        "textes_portes": [],
        "interventions": [],
        "amendements": [],
        "tags_thematiques": [],
        "meta": {
            "schema_version": SCHEMA_VERSION,
            "genere_le": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "licence_donnees": "",
            "warnings": [],
            # #642 : le jumeau typé, vide et présent. Sa présence dit « ce
            # profil est passé par le lot et n'a rien à déclarer » ; son
            # absence dit « ce profil est antérieur ».
            "avertissements": [],
            "provenance": provenance,
        },
    }


def validate_profil(
    profil: dict[str, Any], scrutins_index: Any = None, amendements_index: Any = None
) -> list[str]:
    """Vérifie les invariants de base du schéma pivot v1.

    `scrutins_index` (facultatif, un `ScrutinsIndex`) : depuis #432, le méta
    d'un scrutin vit dans `pivot_data/scrutins.json` et le profil n'en garde que
    le mapping. Deux invariants deviennent donc des **jointures** et ne sont
    vérifiés que si l'index est fourni : qu'un `scrutin_id` référencé existe, et
    la règle 4 (un 49.3 ne porte jamais de position). Sans index, ils sont
    sautés — jamais déclarés valides par défaut.

    `amendements_index` (facultatif, un `AmendementsIndex`) : même mécanique
    depuis #431. `type_deposant`, `sort` et `base_juridique_irrecevabilite` ont
    migré vers l'index et sont validés par `validate_amendements_index` ; ne
    reste ici qu'un invariant devenu jointure — qu'un `amendement_id` référencé
    existe — vérifié seulement si l'index est fourni, sauté sinon.

    Validation structurelle de premier niveau (clés obligatoires, types,
    schema_version) plus les invariants de contenu des champs sensibles :
    position_dans_hemicycle/source_url, mode_declenchement, forme du
    scrutin_id et de l'amendement_id, type_rapport, stade_procedural,
    role_signataire des amendements, et
    structure des champs optionnels de débats officiels dans interventions[]
    (theme_officiel, seance, dossier, source).

    Args:
        profil: dict à valider.

    Returns:
        Liste d'erreurs (liste vide = profil valide).
    """
    errors: list[str] = []

    if not isinstance(profil, dict):
        return [f"Le profil doit être un dict, reçu : {type(profil).__name__}."]

    missing_top = REQUIRED_TOP_LEVEL_KEYS - set(profil.keys())
    if missing_top:
        errors.append(f"Clés manquantes au niveau racine : {sorted(missing_top)}.")

    version = profil.get("schema_version")
    if version != SCHEMA_VERSION:
        errors.append(
            f"schema_version inattendu : {version!r} (attendu : {SCHEMA_VERSION!r})."
        )

    if not profil.get("id"):
        errors.append("'id' est vide ou absent.")

    if not profil.get("nom"):
        errors.append("'nom' est vide ou absent.")

    chambre = profil.get("chambre")
    if chambre is not None and chambre not in KNOWN_CHAMBRES:
        errors.append(
            f"'chambre' non reconnue : {chambre!r}. Valeurs connues : {sorted(KNOWN_CHAMBRES)}."
        )

    # #493 — `chambres` (liste) et `chambre` (scalaire) coexistent le temps de la
    # migration des consommateurs (#494). La clé n'est **pas** dans
    # REQUIRED_TOP_LEVEL_KEYS : les profils publiés avant #493 ne la portent pas,
    # et les déclarer invalides ne dirait rien de vrai sur eux. Elle le devient
    # quand `chambre` est retiré — c'est l'autre moitié de la condition de retrait
    # (docs/decisions/chambres-profil-derivees.md).
    #
    # Absente, on ne valide rien. Présente, elle est tenue à l'invariant qui fait
    # tout l'intérêt du couple : `chambre == chambres[0]`. Sans cette
    # vérification, la coexistence redeviendrait exactement ce que #493 refuse —
    # un champ collecté à côté d'un champ dérivé, et la question « lequel croire ».
    if "chambres" in profil:
        chambres = profil.get("chambres")
        if not isinstance(chambres, list):
            errors.append(
                f"'chambres' doit être une liste, reçu : {type(chambres).__name__}."
            )
        else:
            inconnues = [c for c in chambres if c not in KNOWN_CHAMBRES]
            if inconnues:
                errors.append(
                    f"'chambres' contient des valeurs non reconnues : {inconnues!r}. "
                    f"Valeurs connues : {sorted(KNOWN_CHAMBRES)}."
                )
            if len(set(chambres)) != len(chambres):
                errors.append(f"'chambres' contient des doublons : {chambres!r}.")
            attendu = [c for c in ORDRE_CHAMBRES if c in chambres]
            if not inconnues and chambres != attendu:
                errors.append(
                    f"'chambres' n'est pas dans l'ordre canonique : {chambres!r} "
                    f"(attendu : {attendu!r}). Voir ORDRE_CHAMBRES."
                )
            scalaire_attendu = chambres[0] if chambres else None
            if chambre != scalaire_attendu:
                errors.append(
                    f"'chambre' ({chambre!r}) contredit 'chambres' ({chambres!r}) : "
                    f"le scalaire est chambres[0], soit {scalaire_attendu!r}. "
                    "Les deux champs se dérivent de la même source "
                    "(schema_pivot.deriver_chambres) et ne peuvent pas diverger."
                )

    identite = profil.get("identite")
    if identite is not None and not isinstance(identite, dict):
        errors.append(f"'identite' doit être un dict ou null, reçu : {type(identite).__name__}.")

    # #539 — `identifiants` suit le précédent de `chambres` (#493) : la clé n'est
    # PAS dans REQUIRED_TOP_LEVEL_KEYS, parce que les 476 profils publiés avant ce
    # lot ne la portent pas et que les déclarer invalides ne dirait rien de vrai
    # sur eux. Absente, on ne valide rien ; présente, elle est tenue à ses
    # invariants — les quatre clés, et la forme de chaque identifiant.
    if "identifiants" in profil:
        errors.extend(valider_identifiants(profil.get("identifiants")))

    # #539 — même précédent pour `couverture` : absente sur les 476 profils
    # publiés avant ce lot, donc validée seulement si présente. Sa complétude
    # (les cinq listes) est vérifiée DANS `valider_couverture` : un bloc partiel
    # est une erreur, un bloc absent n'en est pas une.
    if "couverture" in profil:
        errors.extend(valider_couverture(profil.get("couverture")))

    # #860 — facultatif, comme `couverture` : seuls les candidats déclarés le
    # portent, et un profil de roster n'en a pas l'usage. Présent, il est tenu :
    # une liste relue dont chaque ligne a sa source, ou `null` et son motif.
    if "mandats_anterieurs" in profil:
        errors.extend(valider_mandats_anterieurs(profil))

    # `identite.uri_hatvp` porte un LIEN, donc une chaîne ou `null` — jamais un
    # objet (#556).
    #
    # Cette règle est écrite AVANT celle de la recopie, et c'est le correctif de
    # fond : la règle de recopie ci-dessous ne se déclenche que si les deux
    # champs sont truthy et différents. Or `_uri_hatvp_publiable` ramène le
    # marqueur XML d'AMO30 à `None` avant d'alimenter `identifiants.hatvp`. Le
    # couple était donc (marqueur, `None`) — le second membre falsy, la
    # comparaison sautée, **le défaut silencieux**. La contrainte censée
    # signaler la divergence la NEUTRALISAIT : 191 profils sur 481 publiaient
    # `identite.uri_hatvp = {"@xsi:nil": "true"}` et passaient la validation.
    #
    # Le contrôle porte sur la forme du champ lui-même, pas sur son accord avec
    # un autre : un champ ne peut pas être validé par ce qu'un voisin en a fait.
    if isinstance(identite, dict) and "uri_hatvp" in identite:
        uri_hatvp = identite.get("uri_hatvp")
        if uri_hatvp is not None and not isinstance(uri_hatvp, str):
            errors.append(
                f"identite.uri_hatvp doit être une URI (chaîne) ou null, reçu : "
                f"{type(uri_hatvp).__name__} ({uri_hatvp!r}). Une absence "
                "déclarée par la source — le marqueur XML `xsi:nil` d'AMO30 — "
                "n'est pas une valeur : un consommateur qui teste "
                "`if profil['identite']['uri_hatvp']` obtient True sur un dict "
                "non vide et croit tenir un lien HATVP (§2.5, #556)."
            )
        elif isinstance(uri_hatvp, str) and uri_hatvp.strip() and not _RE_HATVP.match(
            uri_hatvp
        ):
            errors.append(
                f"identite.uri_hatvp n'est pas une URI : {uri_hatvp!r}. Même "
                "règle que identifiants.hatvp — un lien qui ne mène nulle part "
                "ne vaut pas mieux qu'une absence, il vaut moins (#556)."
            )

    # #659 — même contrainte de FORME sur les trois champs d'identité que ce lot
    # ajoute, et pour la même raison qu'`uri_hatvp` : ils sont recopiés d'AMO30,
    # dont le convertisseur XML rend `{"@xsi:nil": "true"}` pour tout élément
    # vide. Le filtrage vit à la lecture (`candidate_profile._champ_identite_an`,
    # #556) ; ce contrôle-ci est ce qui le rend VÉRIFIABLE côté publié, là où
    # `audit_diff_profils` ne compare que la PRÉSENCE du bloc `identite` et ne
    # verrait jamais une clé ajoutée, retirée, ni son contenu changé (#649).
    #
    # Et l'enjeu est plus qu'esthétique : la fusion ne fait jamais régresser un
    # scalaire vers `null` (`collecte-vide-necrase-jamais.md`), donc un marqueur
    # publié une fois y resterait, indéfiniment, même après correction de la
    # collecte. Le refus est donc à l'entrée, pas après.
    if isinstance(identite, dict):
        for cle in CHAMPS_IDENTITE_TEXTE_LIBRE:
            if cle not in identite:
                continue
            valeur = identite.get(cle)
            if valeur is not None and not isinstance(valeur, str):
                errors.append(
                    f"identite.{cle} doit être un libellé (chaîne) ou null, reçu : "
                    f"{type(valeur).__name__} ({valeur!r}). Une absence déclarée "
                    "par la source — le marqueur XML `xsi:nil` d'AMO30 — n'est "
                    "pas une valeur (§2 règle 5, #556/#659)."
                )

    # L'invariant qui fait tout l'intérêt du couple : `identifiants.hatvp` est la
    # RECOPIE de `identite.uri_hatvp`, jamais une seconde collecte. Deux valeurs
    # différentes voudraient dire qu'une des deux est fausse, sans dire laquelle.
    if isinstance(identite, dict) and isinstance(profil.get("identifiants"), dict):
        uri_hatvp = identite.get("uri_hatvp")
        publie = profil["identifiants"].get("hatvp")
        if uri_hatvp and publie and uri_hatvp != publie:
            errors.append(
                f"identifiants.hatvp ({publie!r}) contredit identite.uri_hatvp "
                f"({uri_hatvp!r}) : le premier est la recopie du second, pas une "
                "seconde collecte."
            )
        # L'autre moitié de la divergence, et celle que le corpus porte
        # réellement : une `uri_hatvp` renseignée et un `identifiants.hatvp`
        # vide. Les deux champs sortent de la même fabrique
        # (`normalize_profil`), donc l'écart ne peut venir que d'une
        # `uri_hatvp` que `_uri_hatvp_publiable` a refusée. Le dire ici évite
        # qu'un futur filtre plus large rétablisse le silence.
        if isinstance(uri_hatvp, str) and uri_hatvp.strip() and not publie:
            errors.append(
                f"identite.uri_hatvp est renseignée ({uri_hatvp!r}) et "
                "identifiants.hatvp est vide : le second est la recopie du "
                "premier, donc l'écart signale que la valeur a été jugée "
                "impubliable sans que le champ d'origine soit corrigé (#556)."
            )

    for key in _LIST_KEYS:
        val = profil.get(key)
        if val is not None and not isinstance(val, list):
            errors.append(f"'{key}' doit être une liste, reçu : {type(val).__name__}.")

    # position_dans_hemicycle est le champ éditorial le plus sensible du schéma :
    # il ne doit jamais être renseigné sans une source primaire vérifiable.
    mandats = profil.get("mandats")
    if isinstance(mandats, list):
        for i, m in enumerate(mandats):
            if not isinstance(m, dict):
                continue
            if m.get("position_dans_hemicycle") is not None and not m.get("source_url"):
                errors.append(
                    f"mandats[{i}].position_dans_hemicycle est renseigné sans "
                    "source_url : ce champ requiert une source primaire vérifiable."
                )
            mode_declenchement = m.get("mode_declenchement")
            if mode_declenchement is not None and mode_declenchement not in KNOWN_MODES_DECLENCHEMENT:
                errors.append(
                    f"mandats[{i}].mode_declenchement non reconnu : {mode_declenchement!r}. "
                    f"Valeurs connues : {sorted(KNOWN_MODES_DECLENCHEMENT)}."
                )
            # #492 : la chambre d'un mandat est une valeur fermée. `null` reste
            # licite (chambre non déterminée) ; une valeur hors nomenclature ne
            # l'est pas — c'est ainsi qu'une chambre brute non mappée
            # ("deputes", "senateurs") se ferait passer pour une chambre pivot.
            chambre_mandat = m.get("chambre")
            if chambre_mandat is not None and chambre_mandat not in KNOWN_CHAMBRES:
                errors.append(
                    f"mandats[{i}].chambre non reconnue : {chambre_mandat!r}. "
                    f"Valeurs connues : {sorted(KNOWN_CHAMBRES)}."
                )
            # #718 : le référentiel qui a établi la catégorie. La clé est
            # FACULTATIVE et son absence est un sens — « personne ne l'a
            # établie » —, donc `None` n'est pas une valeur licite : il dirait
            # la même chose que l'absence sous une forme qui ressemble à un
            # constat. Une valeur hors nomenclature, elle, ferait passer un
            # référentiel inventé pour une source.
            if "categorie_source" in m:
                source_categorie = m.get("categorie_source")
                if source_categorie not in KNOWN_CATEGORIE_SOURCES:
                    errors.append(
                        f"mandats[{i}].categorie_source non reconnu : "
                        f"{source_categorie!r}. Valeurs connues : "
                        f"{sorted(KNOWN_CATEGORIE_SOURCES)} — ou la clé absente, "
                        "qui dit que personne n'a établi la catégorie."
                    )

            # #863 : même forme, même raison — la clé est facultative, son
            # absence dit que la source n'a pas classé l'appartenance, et une
            # valeur hors nomenclature ferait passer une classification inventée
            # pour celle de la source.
            if "type_organe_source" in m:
                type_organe = m.get("type_organe_source")
                if type_organe not in KNOWN_TYPES_ORGANE_SOURCE:
                    errors.append(
                        f"mandats[{i}].type_organe_source non reconnu : "
                        f"{type_organe!r}. Valeurs connues : "
                        f"{sorted(KNOWN_TYPES_ORGANE_SOURCE)} — ou la clé absente, "
                        "qui dit que la source n'a pas classé l'organe."
                    )

    # Depuis #432, `votes[]` est un MAPPING : `type_scrutin`, `type_vote`,
    # `texte_lie_id` et `sort` ont migré vers `pivot_data/scrutins.json` et sont
    # validés par `validate_scrutins_index`. Ne restent ici que les invariants
    # du mapping lui-même — plus la règle 4, qui est une jointure et n'est donc
    # vérifiable qu'avec l'index (voir `scrutins_index` ci-dessous).
    votes = profil.get("votes")
    index_par_id = (scrutins_index.par_id if scrutins_index is not None else None)
    if isinstance(votes, list):
        for i, v in enumerate(votes):
            if not isinstance(v, dict):
                continue
            scrutin_id = v.get("scrutin_id")
            if scrutin_id is None:
                # Un vote sans identifiant DOIT porter son enregistrement
                # complet : sans lui, la donnée serait perdue au lieu d'être
                # seulement non normalisée (AGENTS.md §2.5).
                if not isinstance(v.get("scrutin_non_resolu"), dict):
                    errors.append(
                        f"votes[{i}] : 'scrutin_id' absent sans 'scrutin_non_resolu'. "
                        "Un vote qu'on ne sait pas rattacher garde son enregistrement "
                        "complet — il n'est ni supprimé, ni doté d'une clé inventée."
                    )
            else:
                legislature, numero = decomposer_id(scrutin_id)
                if legislature is None or numero is None:
                    errors.append(
                        f"votes[{i}].scrutin_id mal formé : {scrutin_id!r}. "
                        "Forme attendue : 'an:<legislature>:<numero_scrutin>'."
                    )
                elif index_par_id is not None and scrutin_id not in index_par_id:
                    errors.append(
                        f"votes[{i}].scrutin_id introuvable dans l'index des scrutins : "
                        f"{scrutin_id!r}. Le mapping pointerait dans le vide."
                    )
            position = v.get("position")
            if position is not None and position not in KNOWN_POSITIONS:
                errors.append(
                    f"votes[{i}].position non reconnue : {position!r}. "
                    f"Valeurs connues : {sorted(KNOWN_POSITIONS)}."
                )
            # Règle 4 : un 49.3 n'est jamais une position. Le `sort` vivant
            # désormais sur le scrutin, la vérification est une jointure — elle
            # n'est possible qu'avec l'index, et est silencieusement sautée
            # sans lui plutôt que faussement validée.
            if index_par_id is not None and position is not None:
                scrutin = index_par_id.get(scrutin_id) or {}
                if scrutin.get("sort") == "adopte_sans_vote_49_3":
                    errors.append(
                        f"votes[{i}] : le scrutin {scrutin_id} a sort='adopte_sans_vote_49_3' "
                        f"mais ce vote porte une position ({position!r}) — 49.3 = absence de "
                        "vote, jamais une position (AGENTS.md règle 4)."
                    )

    # role / type_rapport / stade_procedural : nomenclature factuelle, jamais une
    # catégorie éditoriale de valorisation.
    textes_portes = profil.get("textes_portes")
    if isinstance(textes_portes, list):
        for i, t in enumerate(textes_portes):
            if not isinstance(t, dict):
                continue
            role = t.get("role")
            if role is not None and role not in KNOWN_ROLES_TEXTE:
                errors.append(
                    f"textes_portes[{i}].role non reconnu : {role!r}. "
                    f"Valeurs connues : {sorted(KNOWN_ROLES_TEXTE)}."
                )
            # #689 : `nature_texte` est le fait sourcé, `role` en dérive pour un
            # initiateur. Les deux ne peuvent pas se contredire — c'est ce qui
            # rend la redondance sûre, et non une seconde vérité à côté de la
            # première (même invariant que `chambre` / `chambres[0]`, #493).
            nature_texte = t.get("nature_texte")
            if nature_texte is not None and nature_texte not in KNOWN_NATURES_TEXTE:
                errors.append(
                    f"textes_portes[{i}].nature_texte non reconnue : {nature_texte!r}. "
                    f"Valeurs connues : {sorted(KNOWN_NATURES_TEXTE)}."
                )
            elif role in ROLES_INITIATEUR_TEXTE:
                attendu = ROLE_INITIATEUR_PAR_NATURE.get(nature_texte, "auteur")
                if role != attendu:
                    errors.append(
                        f"textes_portes[{i}] : role={role!r} contredit "
                        f"nature_texte={nature_texte!r}, qui appelle {attendu!r} "
                        "(#689). Le rôle d'un initiateur est dérivé de la nature "
                        "du texte, jamais collecté à côté d'elle."
                    )
            type_rapport = t.get("type_rapport")
            if type_rapport is not None and type_rapport not in KNOWN_TYPES_RAPPORT:
                errors.append(
                    f"textes_portes[{i}].type_rapport non reconnu : {type_rapport!r}. "
                    f"Valeurs connues : {sorted(KNOWN_TYPES_RAPPORT)}."
                )
            stade_procedural = t.get("stade_procedural")
            if stade_procedural is not None and stade_procedural not in KNOWN_STADES_PROCEDURAUX:
                errors.append(
                    f"textes_portes[{i}].stade_procedural non reconnu : {stade_procedural!r}. "
                    f"Valeurs connues : {sorted(KNOWN_STADES_PROCEDURAUX)}."
                )
            # #743 — le sort et son motif d'absence sont deux faces d'une seule
            # information, et la contradiction est l'erreur qui compte : porter
            # les deux dirait à la fois « voici son issue » et « voici pourquoi
            # elle manque ». Un `sort` nul SANS motif serait pire encore : une
            # absence sans cause, que §2 règle 5 refuse.
            sort = t.get("sort")
            non_resolu = t.get("sort_non_resolu")
            if sort is not None and sort not in KNOWN_SORTS_TEXTE_PORTE:
                errors.append(
                    f"textes_portes[{i}].sort non reconnu : {sort!r}. "
                    f"Valeurs connues : {sorted(KNOWN_SORTS_TEXTE_PORTE)}."
                )
            if sort is not None and non_resolu is not None:
                errors.append(
                    f"textes_portes[{i}] porte à la fois sort et sort_non_resolu — "
                    "un sort résolu n'a pas de motif d'absence."
                )
            # #747 — l'invariant que ce commentaire promettait sans l'imposer.
            # 49 entrées ont vécu un mois avec `sort` ET `sort_non_resolu` nuls
            # : une absence sans cause, que §2 règle 5 refuse, et que ce bloc
            # laissait passer parce qu'il ne contrôlait `sort_non_resolu` que
            # lorsqu'il était NON nul. Le contrôle de la contradiction ne
            # couvrait donc que la moitié bruyante du couple.
            if sort is None and non_resolu is None:
                errors.append(
                    f"textes_portes[{i}] porte `sort: null` sans sort_non_resolu — "
                    "une absence doit nommer sa cause (AGENTS.md §2 règle 5)."
                )
            if non_resolu is not None:
                if not isinstance(non_resolu, dict):
                    errors.append(f"textes_portes[{i}].sort_non_resolu doit être un dict.")
                elif non_resolu.get("motif") not in KNOWN_MOTIFS_SORT_NON_RESOLU:
                    errors.append(
                        f"textes_portes[{i}].sort_non_resolu.motif inconnu : "
                        f"{non_resolu.get('motif')!r}. Valeurs connues : "
                        f"{sorted(KNOWN_MOTIFS_SORT_NON_RESOLU)}."
                    )

    # Depuis #431, `type_deposant`, `sort` et `base_juridique_irrecevabilite` ont
    # migré vers l'index des amendements : leur validation a suivi les champs et
    # vit dans `validate_amendements_index`. Ne restent ici que les invariants du
    # mapping — plus l'existence de la cible, qui est une jointure et n'est donc
    # vérifiable qu'avec l'index.
    amendements = profil.get("amendements")
    index_amendements = (
        amendements_index.par_id if amendements_index is not None else None
    )
    if isinstance(amendements, list):
        for i, a in enumerate(amendements):
            if not isinstance(a, dict):
                continue
            role_signataire = a.get("role_signataire")
            if role_signataire is not None and role_signataire not in KNOWN_ROLES_SIGNATAIRE_AMENDEMENT:
                errors.append(
                    f"amendements[{i}].role_signataire non reconnu : {role_signataire!r}. "
                    f"Valeurs connues : {sorted(KNOWN_ROLES_SIGNATAIRE_AMENDEMENT)}."
                )
            amendement_id = a.get("amendement_id")
            if amendement_id is None:
                # Un amendement sans identifiant DOIT porter son enregistrement
                # complet : sans lui, la donnée serait perdue au lieu d'être
                # seulement non normalisée (AGENTS.md §2.5).
                if not isinstance(a.get("amendement_non_resolu"), dict):
                    errors.append(
                        f"amendements[{i}] : 'amendement_id' absent sans "
                        "'amendement_non_resolu'. Un amendement qu'on ne sait pas "
                        "rattacher garde son enregistrement complet — il n'est ni "
                        "supprimé, ni doté d'une clé inventée."
                    )
                continue
            if decomposer_id_amendement(amendement_id) is None:
                errors.append(
                    f"amendements[{i}].amendement_id mal formé : {amendement_id!r}. "
                    "Forme attendue : 'an:<uid AN>'."
                )
            elif index_amendements is not None and amendement_id not in index_amendements:
                errors.append(
                    f"amendements[{i}].amendement_id introuvable dans l'index des "
                    f"amendements : {amendement_id!r}. Le mapping pointerait dans le vide."
                )

    interventions = profil.get("interventions")
    if isinstance(interventions, list):
        for i, inter in enumerate(interventions):
            if not isinstance(inter, dict):
                continue
            theme_officiel = inter.get("theme_officiel")
            if theme_officiel is not None and not isinstance(theme_officiel, str):
                errors.append(
                    f"interventions[{i}].theme_officiel doit être une chaîne ou null, "
                    f"reçu : {type(theme_officiel).__name__}."
                )
            for key in ("seance", "dossier", "source"):
                val = inter.get(key)
                if val is not None and not isinstance(val, dict):
                    errors.append(
                        f"interventions[{i}].{key} doit être un dict ou null, "
                        f"reçu : {type(val).__name__}."
                    )
            # #657 : `collecte` est une valeur fermée, pas un texte libre. Une
            # valeur inconnue ferait passer une forme non déclarée pour une
            # forme déclarée — pire que pas de marqueur du tout.
            if "collecte" in inter:
                collecte = inter.get("collecte")
                if collecte not in KNOWN_COLLECTES_INTERVENTION:
                    errors.append(
                        f"interventions[{i}].collecte inconnu : {collecte!r} "
                        f"(attendu : {sorted(KNOWN_COLLECTES_INTERVENTION)}, ou "
                        "clé absente pour une entrée complète)."
                    )

    meta = profil.get("meta")
    if not isinstance(meta, dict):
        errors.append("'meta' doit être un dict.")
    else:
        missing_meta = REQUIRED_META_KEYS - set(meta.keys())
        if missing_meta:
            errors.append(f"Clés manquantes dans 'meta' : {sorted(missing_meta)}.")
        if meta.get("schema_version") != SCHEMA_VERSION:
            errors.append(
                f"meta.schema_version inattendu : {meta.get('schema_version')!r} "
                f"(attendu : {SCHEMA_VERSION!r})."
            )
        if not isinstance(meta.get("warnings"), list):
            errors.append("'meta.warnings' doit être une liste.")
        # meta.provenance : absent = rétro-compatible (traité comme "candidat_declare"
        # par les consommateurs, voir merge_profile.merge_pivot_profile), donc validé
        # uniquement s'il est présent.
        provenance = meta.get("provenance")
        if provenance is not None and provenance not in KNOWN_PROVENANCES:
            errors.append(
                f"meta.provenance non reconnue : {provenance!r}. "
                f"Valeurs connues : {sorted(KNOWN_PROVENANCES)}."
            )

        # #603 — même précédent que `identifiants` (#539) et `couverture` :
        # absent des 481 profils publiés avant ce lot, donc validé seulement s'il
        # est présent. Présent, il est tenu à sa complétude : un champ publié
        # sans provenance ferait de l'absence d'entrée une seconde façon de dire
        # « on ne sait pas », à côté de `source: null` qui le dit déjà.
        if "provenance_champs" in meta:
            errors.extend(
                valider_provenance_champs(meta.get("provenance_champs"), profil)
            )

        # #642 — même précédent que `couverture` (#539) et `provenance_champs`
        # (#603) : le bloc est absent des 481 profils publiés avant le lot, donc
        # validé seulement s'il est présent. **Un avertissement non typé n'est
        # pas refusé** : un schéma qui n'accepte plus ce qu'il a écrit hier
        # n'est pas une simplification, c'est une perte (même raison que
        # `KNOWN_SOURCE_TYPES` pour `nosdeputes`). La tolérance a une condition
        # de retrait écrite, et un compteur qui la mesure — voir
        # `docs/decisions/destinataire-avertissements-642.md`.
        if "avertissements" in meta:
            errors.extend(
                valider_avertissements(meta.get("avertissements"), meta.get("warnings"))
            )

    return errors


def validate_scrutins_index(index: dict[str, Any]) -> list[str]:
    """Vérifie `pivot_data/scrutins.json` (schéma `scrutins-v1`, #432).

    Les invariants qui portaient sur `votes[]` avant la normalisation ont suivi
    les champs : `type_scrutin`, `type_vote`, `texte_lie_id` (motion de censure)
    et la forme de l'identifiant se vérifient désormais ici, une fois par
    scrutin au lieu d'une fois par votant.

    La règle 4 (49.3 = jamais une position) reste chez `validate_profil` : elle
    joint un `sort` d'ici à une `position` de là-bas, et c'est côté profil que la
    position vit.
    """
    errors: list[str] = []

    if not isinstance(index, dict):
        return ["L'index des scrutins doit être un objet JSON."]

    version = index.get("schema_version")
    if version != SCRUTINS_SCHEMA_VERSION:
        errors.append(
            f"schema_version de l'index : {version!r}, attendu {SCRUTINS_SCHEMA_VERSION!r}."
        )

    scrutins = index.get("scrutins")
    if not isinstance(scrutins, list):
        return errors + ["Clé 'scrutins' manquante ou de mauvais type (liste attendue)."]

    vus: set[str] = set()
    for i, scrutin in enumerate(scrutins):
        if not isinstance(scrutin, dict):
            errors.append(f"scrutins[{i}] n'est pas un objet.")
            continue

        scrutin_id = scrutin.get("id")
        legislature, numero = decomposer_id(scrutin_id) if scrutin_id else (None, None)
        if legislature is None or numero is None:
            errors.append(
                f"scrutins[{i}].id mal formé : {scrutin_id!r}. "
                "Forme attendue : 'an:<legislature>:<numero_scrutin>'."
            )
        else:
            # L'identifiant est dérivé de ces deux champs : une divergence
            # rendrait la liste incohérente avec elle-même, et un consommateur
            # qui décomposerait l'id n'obtiendrait pas ce que porte le champ.
            if str(scrutin.get("legislature")) != legislature:
                errors.append(
                    f"scrutins[{i}] : id {scrutin_id!r} et legislature "
                    f"{scrutin.get('legislature')!r} divergent."
                )
            if str(scrutin.get("numero_scrutin")) != numero:
                errors.append(
                    f"scrutins[{i}] : id {scrutin_id!r} et numero_scrutin "
                    f"{scrutin.get('numero_scrutin')!r} divergent."
                )
            if scrutin_id in vus:
                errors.append(f"scrutins[{i}] : identifiant en double ({scrutin_id!r}).")
            vus.add(scrutin_id)

        provenance = scrutin.get("legislature_provenance")
        if provenance not in KNOWN_PROVENANCES_LEGISLATURE:
            errors.append(
                f"scrutins[{i}].legislature_provenance non reconnue : {provenance!r}. "
                f"Valeurs connues : {sorted(KNOWN_PROVENANCES_LEGISLATURE)}. "
                "Une législature dérivée ne doit jamais passer pour collectée."
            )

        type_scrutin = scrutin.get("type_scrutin")
        if type_scrutin is not None and type_scrutin not in KNOWN_TYPES_SCRUTIN:
            errors.append(
                f"scrutins[{i}].type_scrutin non reconnu : {type_scrutin!r}. "
                f"Valeurs connues : {sorted(KNOWN_TYPES_SCRUTIN)}."
            )

        type_vote = scrutin.get("type_vote")
        if type_vote is not None and type_vote not in KNOWN_TYPES_VOTE:
            errors.append(
                f"scrutins[{i}].type_vote non reconnu : {type_vote!r}. "
                f"Valeurs connues : {sorted(KNOWN_TYPES_VOTE)}."
            )
        # Un vote de motion de censure doit dire à quel texte il se rapporte,
        # ou dire pourquoi il ne le peut pas. La seconde branche a été ouverte
        # par #639 : le scrutin AN ne publie AUCUNE référence législative
        # (0/18 311 sur les législatures 14-17), et une motion de l'article 49
        # alinéa 2 n'a de toute façon pas de texte à lier. Exiger la clé sans
        # alternative aurait laissé le seul choix entre publier un fait faux
        # (`vote_texte` sur 66 motions) et taire une qualification sourcée.
        # Patron `*_non_resolu` du dépôt : clé nulle + déclaration à côté.
        if type_vote == "motion_censure" and not scrutin.get("texte_lie_id"):
            declaration = scrutin.get("texte_lie_non_resolu")
            if not isinstance(declaration, dict) or not declaration.get("motif"):
                errors.append(
                    f"scrutins[{i}] : type_vote='motion_censure' sans 'texte_lie_id' "
                    "ni 'texte_lie_non_resolu.motif' (le texte 49.3 concerné doit être "
                    "identifié, ou son absence déclarée — jamais fusionné avec le vote "
                    "sur le texte)."
                )

    return errors


def validate_amendements_index(index: dict[str, Any]) -> list[str]:
    """Vérifie un fichier de `pivot_data/amendements/` (schéma `amendements-v1`, #431).

    Les invariants qui portaient sur `amendements[]` avant la normalisation ont
    suivi les champs : `type_deposant`, `sort`/`base_juridique_irrecevabilite` et
    la forme de l'identifiant se vérifient désormais ici, **une fois par
    amendement au lieu d'une fois par signataire** — 207 238 vérifications au
    lieu de 810 552.

    Un fichier porte **une** législature : chaque identifiant doit être de cette
    législature-là, sans quoi un consommateur qui ne charge que la XVIIe verrait
    disparaître des amendements rangés au mauvais endroit.
    """
    errors: list[str] = []

    if not isinstance(index, dict):
        return ["L'index des amendements doit être un objet JSON."]

    version = index.get("schema_version")
    if version != AMENDEMENTS_SCHEMA_VERSION:
        errors.append(
            f"schema_version de l'index : {version!r}, attendu {AMENDEMENTS_SCHEMA_VERSION!r}."
        )

    legislature_fichier = index.get("legislature")
    if not legislature_fichier:
        errors.append(
            "Clé 'legislature' manquante : elle est portée une fois par fichier "
            "et jamais par entrée, donc son absence rend les entrées inclassables."
        )

    # `textes` (#639) : table de fichier `texte_vise -> {dossier_id, titre}`.
    # OPTIONNELLE — les quatre fichiers publiés avant #639 n'en ont pas, et
    # l'exiger ferait échouer la validation de tout le corpus avant sa
    # régénération. Un texte sans dossier résolu n'a pas d'entrée du tout :
    # une entrée à `dossier_id: null` coûterait des octets pour ne rien dire de
    # plus qu'une absence.
    textes = index.get("textes")
    if textes is not None:
        if not isinstance(textes, dict):
            errors.append(
                "Clé 'textes' de mauvais type (objet {texte_vise: {dossier_id, titre}} attendu)."
            )
        else:
            for texte_vise, entree in textes.items():
                if not isinstance(entree, dict):
                    errors.append(f"textes[{texte_vise!r}] n'est pas un objet.")
                    continue
                dossier_id = entree.get("dossier_id")
                if not isinstance(dossier_id, str) or not dossier_id:
                    errors.append(
                        f"textes[{texte_vise!r}].dossier_id manquant : un texte "
                        "sans dossier résolu n'a pas d'entrée dans la table."
                    )

    amendements = index.get("amendements")
    if not isinstance(amendements, dict):
        return errors + [
            "Clé 'amendements' manquante ou de mauvais type (objet {id: amendement} attendu)."
        ]

    for amendement_id, amendement in amendements.items():
        if not isinstance(amendement, dict):
            errors.append(f"amendements[{amendement_id!r}] n'est pas un objet.")
            continue

        uid = decomposer_id_amendement(amendement_id)
        if uid is None:
            errors.append(
                f"amendements[{amendement_id!r}] : identifiant mal formé. "
                "Forme attendue : 'an:<uid AN>'."
            )
        elif legislature_fichier and legislature_amendement(amendement_id) not in (
            None, str(legislature_fichier)
        ):
            errors.append(
                f"amendements[{amendement_id!r}] : l'uid porte la législature "
                f"{legislature_amendement(amendement_id)!r} mais le fichier déclare "
                f"{legislature_fichier!r}."
            )

        type_deposant = amendement.get("type_deposant")
        if type_deposant is not None and type_deposant not in KNOWN_TYPES_DEPOSANT:
            errors.append(
                f"amendements[{amendement_id!r}].type_deposant non reconnu : "
                f"{type_deposant!r}. Valeurs connues : {sorted(KNOWN_TYPES_DEPOSANT)}."
            )

        base_juridique = amendement.get("base_juridique_irrecevabilite")
        if amendement.get("sort") == "irrecevable" and not base_juridique:
            errors.append(
                f"amendements[{amendement_id!r}] : sort='irrecevable' sans "
                "'base_juridique_irrecevabilite' (l'irrecevabilité est un statut "
                "distinct d'un simple rejet)."
            )
        if base_juridique is not None and base_juridique not in KNOWN_BASES_IRRECEVABILITE:
            errors.append(
                f"amendements[{amendement_id!r}].base_juridique_irrecevabilite non "
                f"reconnue : {base_juridique!r}. "
                f"Valeurs connues : {sorted(KNOWN_BASES_IRRECEVABILITE)}."
            )

        # `co_signataires` n'a rien à faire ici : il vit dans le fichier
        # compagnon. L'y retrouver signalerait une régression vers la forme
        # lourde, celle qui pèse 59 % de l'index.
        if "co_signataires" in amendement:
            errors.append(
                f"amendements[{amendement_id!r}] porte 'co_signataires' : les "
                "cosignatures vivent dans <legislature>.cosignatures.json, jamais "
                "dans le fichier de méta (75,7 Mo sur 128,8)."
            )

    return errors


def validate_amendements_cosignatures(index: dict[str, Any]) -> list[str]:
    """Vérifie un fichier `<legislature>.cosignatures.json` (#431).

    Fichier compagnon volontairement minimal : `{id: [références AN]}`. Il est
    séparé parce qu'aucun consommateur ne lit les cosignatures aujourd'hui et
    qu'elles pèsent 59 % de l'index — mais elles ne sont jamais supprimées, un
    réseau de cosignatures étant de la matière première d'analyse (#324).
    """
    errors: list[str] = []

    if not isinstance(index, dict):
        return ["L'index des cosignatures doit être un objet JSON."]

    version = index.get("schema_version")
    if version != AMENDEMENTS_COSIGNATURES_SCHEMA_VERSION:
        errors.append(
            f"schema_version de l'index : {version!r}, attendu "
            f"{AMENDEMENTS_COSIGNATURES_SCHEMA_VERSION!r}."
        )

    cosignatures = index.get("co_signataires")
    if not isinstance(cosignatures, dict):
        return errors + [
            "Clé 'co_signataires' manquante ou de mauvais type (objet {id: [refs]} attendu)."
        ]

    for amendement_id, refs in cosignatures.items():
        if decomposer_id_amendement(amendement_id) is None:
            errors.append(
                f"co_signataires[{amendement_id!r}] : identifiant mal formé. "
                "Forme attendue : 'an:<uid AN>'."
            )
        if not isinstance(refs, list):
            errors.append(
                f"co_signataires[{amendement_id!r}] n'est pas une liste."
            )
            continue
        if not refs:
            errors.append(
                f"co_signataires[{amendement_id!r}] est une liste vide : un "
                "amendement sans cosignataire est absent du fichier, il n'y "
                "figure pas avec une liste vide."
            )

    return errors
