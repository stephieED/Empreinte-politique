<a id="freshness-timestamps-groupes-gouvernements-partis"></a>
# Extension de la stabilité des horodatages aux profils groupe/gouvernement/parti (#343, complet) (2026-08-17)

`2026-08-17`

> **En bref** — stabilité des horodatages étendue aux profils groupe, gouvernement et parti.

**Contexte** : [[pivot-freshness-timestamps-stables]] (ci-dessous) corrigeait
le motif pour les seuls pivots candidats, en notant que
`group_profile.py`/`gouvernement_profile.py`/`parti_profile.py` étaient
« probablement » affectés du même défaut, mais sans repro confirmé — donc
laissé en ROADMAP plutôt que corrigé à l'aveugle.

**Repro obtenu** : deux exécutions successives de
`generate_gouvernement_profiles.py` sans aucune modification des données
sources donnent un contenu strictement identique (hors `meta`) mais un
`meta.genere_le` qui avance (`17:36:23` → `18:13:05`). Le motif était donc
bien présent, et sur les trois familles de documents.

**Décision** : réutiliser `preserve_stable_freshness_timestamps` telle quelle
plutôt que d'écrire une variante par script — les quatre types de documents
partagent exactement la même forme de fraîcheur (`meta.genere_le` +
`sources[].synchro_le`), vérifié sur les fichiers réellement produits.
Appliquée au point d'écriture de chacun : `group_profile.generate_groupe_profile_from_roster`,
`generate_gouvernement_profiles.generate_all`, `parti_profile` (boucle
d'écriture). Helper partagé `load_existing_document` ajouté dans
`merge_profile.py` pour relire le document précédent (illisible = traité
comme absent : la seule conséquence est un re-tamponnage, jamais une perte —
le document régénéré est écrit dans tous les cas).

**Correctif nécessaire à la généralisation — appariement des sources** :
la fonction indexait les anciennes sources par `type` seul. Ça suffisait pour
un pivot candidat (quelques sources, chacune d'un type distinct), mais pas
ici : un profil de groupe porte une source PAR MEMBRE, donc plusieurs
dizaines d'entrées de même `type` (mesuré : 63 sources pour 3 types distincts
sur `groupe-AN-REN-16`). Une clé sur le seul `type` les aurait toutes
écrasées sur la dernière, attribuant à chaque membre l'horodatage d'un autre.
Clé passée à `(type, url)`. L'appariement reste exact par construction :
`url` fait partie de l'empreinte comparée, donc si les empreintes sont
égales, les couples `(type, url)` le sont aussi.

**Mesure** : re-génération des trois familles à données inchangées —
**0 fichier modifié sur 27** (7 groupes + 10 partis + 10 gouvernements),
contre 27 avant le correctif. Vérifié aussi octet-pour-octet sur
`gouvernement-BAYROU.json`.

**Effet attendu au-delà de la traçabilité** : les commits automatiques du
pipeline ne porteront plus de diff sur ces 27 fichiers quand rien n'a changé,
ce qui rend enfin lisible la question « qu'est-ce qui a réellement bougé ce
run ? » — motif observé en pratique (123 fichiers modifiés pour zéro
changement de contenu, cf. l'entrée ci-dessous).

**Tests** : appariement `(type, url)` sur un document à sources multiples de
même type (test vérifié comme discriminant : il échoue si l'on revient à une
clé sur `type` seul), et `load_existing_document` (absent, corrompu, JSON
non-objet, cas nominal). Suite complète : 1155/1155.

