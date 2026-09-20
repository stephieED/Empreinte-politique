<a id="retrait-senat-528"></a>
# Le Sénat sort du périmètre, et le job qui concluait vert sans rien produire est retiré (#528, lot 3 de l'épic « une seule source AN ») (2026-08-26)

`2026-08-26`

> **En bref** — décision éditoriale, pas technique ; coût mesuré quasi nul sur le corpus publié.

**La décision est éditoriale, elle a été prise, et elle est ici.** Elle n'a pas
été déduite d'une panne : `archive.nossenateurs.fr` sert un certificat expiré
depuis le 24/08/2026 (#516) et c'est ce qui a posé la question, pas ce qui y
répond. Les deux issues possibles étaient « le Sénat sort du périmètre » et
« une source de remplacement est évaluée » — `data.senat.fr` / `www.senat.fr`,
dont **l'existence comme source exploitable n'est pas établie** : le runner CI
n'a pas pu les sonder (hors périmètre réseau autorisé), et personne n'a mesuré
ce qu'elles publient. Choisir la seconde branche aurait été s'engager sur une
source dont on ne sait rien.

**Décision : le Sénat sort du périmètre du produit.** Pour l'instant — la
condition de réouverture est écrite au §7 et elle est vérifiable.

## 1. Le corollaire, et la vraie raison de l'urgence

`extract-senat` **tournait, échouait sur 8 candidats sur 8, et concluait vert**
à chaque run depuis le 24/08 : `8 candidat(s) sans profil parce que la source
n'a pas répondu`, 0 profil écrit, artifact `raw-profiles-senat` absent — que
`merge-and-pivot` affichait ensuite en rouge, au mauvais endroit. La suspension
de #516 ne couvrait que le **roster de groupe** sénatorial, pas la **collecte
des candidats** sur la même source morte.

C'est exactement le motif de #501 et de #510 : *une collecte qui rend zéro par
construction, invisible parce qu'un autre chemin comble le silence.* Un job vert
qui ne produit rien est un mensonge du tableau de bord. Deux sorties étaient
acceptables — le suspendre explicitement, ou assumer le job à vide en le
déclarant. Le retrait règle le point sans troisième état à maintenir.

## 2. Le coût de données, mesuré sur les 476 profils committés

| Mesure | Valeur |
| --- | --- |
| entrées `sources[]` de type `nossenateurs` | **2** (`jean-luc-melenchon`, `bruno-retailleau`) |
| interventions sénatoriales publiées | **0** |
| `mandats[]` estampillés `chambre: "Senat"` | **2** (une par profil) |
| profils dont `chambres` contient `Senat` | **2** sur 476 |
| `cohesion_votes` sur `groupe-Senat-LR` / `groupe-Senat-SER` | **0** et **0** |
| membres de ces deux fiches | 15 et 5 |

Les 0 interventions ne sont pas une surprise : #501 avait déjà établi que
**toutes** les interventions sénatoriales étaient jetées par construction
(`fetch_intervention_details` lit `url_nosdeputes`, l'archive publie
`url_nossenateurs`). Les 0 `cohesion_votes` non plus : aucun jeu de données de
scrutins sénatoriaux exploitable n'a jamais été branché.

## 3. La perte est DÉCLARÉE, pas subie

Deux régimes, et ils ne perdent pas la même chose :

- **fusion additive** (le régime nominal) : `sources` est **remplacé** par la
  nouvelle collecte (`_merge_pivot_sources`), donc les **2** entrées
  `nossenateurs` disparaissent au premier profil régénéré. `mandats` est
  **additif** (`merge_lists_by_key`) : les 2 mandats sénatoriaux **restent**, et
  `chambres` — recalculé, jamais fusionné (#493) — continue donc de porter
  `Senat` sur les deux profils. Rien d'autre ne bouge ;
- **`cold_start` / `overwrite_profiles`** (`--no-merge`) : les 2 mandats
  sénatoriaux ne sont plus recollectés par personne. `mandats` est une **liste
  stable surveillée** par `audit_diff_profils` (#460/#470) : ce run-là sera donc
  **bloqué au commit**, et devra passer par `allow_declared_losses`. C'est le
  comportement voulu — une perte légitime se déclare, elle ne se contourne pas
  en retirant le contrôle.

Sur `sources`, la perte est **rapportée et non bloquante** : c'est déjà la
catégorie que #460 lui donne. Elle est ici **annoncée à l'avance**, avec son
compte exact (2) et ses deux slugs, ce qui est la différence entre une perte
déclarée et une perte constatée après coup.

Un détail relevé au passage, non corrigé ici : l'entrée `nossenateurs` de
`jean-luc-melenchon` porte une URL **LCP** (`lcp.fr/actualites/...`), pas une
URL NosSénateurs. Le `type` a été estampillé depuis la chambre de collecte, pas
depuis l'URL. Elle disparaît avec le reste ; la noter évite de croire qu'on perd
une source primaire sénatoriale — il n'y en avait qu'une, celle de
`bruno-retailleau`.

## 4. Ce qui est retiré, et ce qui ne l'est pas

Retiré :

- le job **`extract-senat`** de `.github/workflows/generate-data.yml`, ses
  `needs:` chez `extract-roster-groupes` et `merge-and-pivot`, son entrée de
  cache `public-data-cache-senat-*`, son artifact `raw-profiles-senat` et le
  répertoire `_artifacts/senat` de la fusion ;
- **`--source senat`** : `SOURCE_VALUES` vaut `("an", "ue", "all")`. La valeur
  est refusée par argparse — un run qui la demande encore échoue à la ligne de
  commande, il ne tourne pas à vide ;
- **`CHAMBRES = ["deputes"]`** dans `generate_all_profiles.py` ;
- **`BASE_URLS["senateurs"]`** dans `candidate_profile.py`, et avec lui
  `fetch_votes` (votes NosSénateurs) et
  `fetch_dossiers`/`fetch_dossiers_for_legislatures` (dossiers législatifs
  NosSénateurs) : ces trois fonctions n'avaient plus d'appelant. La branche de
  repli « utiliser `votes_raw` » de l'étape 6 est partie avec elles ;
- **`senat_periode_debut`** et `_member_matches_legislature` (`group_roster.py`,
  #191) : ce filtre côté client n'existait que parce que l'archive sénatoriale
  servait toutes les périodes sur un domaine unique ;
- **`docs/extract-senat.md`**.

**Pas** retiré, et c'est le point important :

- les **2 fiches `groupe-Senat-*.json` publiées** restent sur disque, figées,
  toujours servies par l'onglet Groupes. Supprimer un fichier publié est une
  **disparition**, que `audit_diff_profils` bloque (#460/#470) ; suspendre
  n'est pas retirer, c'est déjà la règle de #516 ;
- les **2 entrées Sénat de `raw_data/groupes_reels.json`**, qui restent
  `extraction_suspendue` (voir §5) ;
- les **mandats sénatoriaux déjà collectés** sur `jean-luc-melenchon` et
  `bruno-retailleau` : la fusion additive ne retire rien, et effacer un fait de
  carrière collecté serait une falsification, pas un changement de périmètre ;
- la **mention de NosSénateurs.fr dans les mentions légales** (`LegalNoticePage`)
  et dans la FAQ : tant que des champs publiés en dérivent, l'attribution ODbL
  reste due (règle 2, AGENTS §2). Elle sortira quand les données sortiront, pas
  avant.

## 5. La `condition_reprise` des 2 groupes suspendus, tranchée

Elle disait : *« un certificat valide sur archive.nossenateurs.fr […] ou une
source Sénat de remplacement. À défaut de l'un des deux d'ici fin 2026, trancher
la question éditoriale ».* La question éditoriale **a été tranchée**, avant
l'échéance : la laisser en l'état ferait attendre une décision déjà prise, et un
certificat renouvelé rouvrirait automatiquement une collecte que le produit ne
veut plus.

Les deux entrées restent donc `extraction_suspendue: true`, **avec la même
forme** (`depuis`, `motif`, `references`, `condition_reprise` — le bloc est en
échec dur sans eux, #516), et une `condition_reprise` réécrite : la reprise
n'est plus conditionnée à un état de source mais à la **réouverture explicite du
périmètre éditorial**, dans l'ordre écrit au §7. Un certificat valide ne suffit
plus, et c'est le sens de la décision.

## 6. Le budget de job, recalculé sans `extract-senat`

`generate-data.yml` documente un plafond autorisé (somme des timeouts) et un
temps mur mesuré. Le Sénat pesait **15 min** dans le premier et **4,6 min** dans
le second, et il n'était le maillon dimensionnant d'aucun des deux depuis #501.

| | avant | après |
| --- | --- | --- |
| jobs | 9 (2 préparatoires, 6 d'extraction, 1 de fusion) | **8** (2, **5**, 1) |
| chaîne la plus longue (plafond) | `max(30 + 5·8 ; 60 ; 15)` = 70, + 60·S + 60 | `max(30 + 5·8 ; 60)` = **70**, + 60·S + 60 |
| plafond à S=1 / S=8 | 190 / 610 min | **190 / 610 min** (inchangé) |
| temps mur mesuré (run 32288588518) | 54,9 min | **54,9 min** (le Sénat n'était pas sur le chemin critique) |

**Le plafond ne bouge pas, et c'est le résultat.** Les 15 min du Sénat étaient
déjà dominées par les 70 min d'`extract-an` dans le `max()` du premier étage :
le retirer ne libère aucun temps mur. Ce qui disparaît est un job de runner et
~32 requêtes par run vers une source morte. Le calcul est écrit ici pour que la
prochaine relecture n'ait pas à le refaire — c'est l'oubli d'`extract-senat` dans
ce `max()` qui a produit le « 190 min » faux publié jusqu'à #413.

## 7. Condition de réouverture

Sans critère écrit, un « pour l'instant » devient définitif par omission — c'est
ce que #431 et #432 ont montré sur leurs replis de lecture. Le Sénat ne
réintègre le périmètre que si les **trois** conditions suivantes sont réunies,
**dans cet ordre** :

1. **une source est établie**, pas supposée : `data.senat.fr` ou `www.senat.fr`
   sondés pour de vrai, avec ce qu'ils publient effectivement (identités,
   mandats, scrutins nominatifs, comptes rendus) et sous quelle licence. « Le
   site répond » n'est pas une source ;
2. **elle rend au moins un agrégat publiable** — un `cohesion_votes` non nul sur
   une fiche de groupe sénatorial, ou des interventions rattachables à un
   orateur. Les deux fiches publiées portent `cohesion_votes: 0` : rouvrir pour
   reproduire ce zéro serait rouvrir pour rien (règle 7) ;
3. **la décision éditoriale est reprise explicitement**, ici, avec sa date. Le
   §2 restera vrai après réouverture : le coût de données du retrait était
   quasi nul, donc l'argument de réouverture ne pourra pas être « on perd des
   données », il devra être « on en gagne, et voici lesquelles ».

Tant que ces trois points ne sont pas écrits, `archive.nossenateurs.fr` qui
redeviendrait joignable ne change **rien** : la source est morte pour le produit,
pas seulement pour son certificat.

## 8. Le non-retour est outillé, pas confié à la relecture

Trois refus bruyants, tous testés :

- `candidate_profile.build_profile("senateurs", …)` lève un `ValueError` qui
  **nomme la décision** et renvoie à cette section, au lieu d'un `KeyError` sur
  `BASE_URLS` ;
- `group_roster._base_url_for("senateurs", …)` lève avant toute requête réseau —
  une source retirée ne se sollicite pas « pour voir », c'est ce que #516 a payé.
  Le `ValueError` appartient à `ERREURS_ROSTER`, donc les trois appelants le
  traitent en « roster indisponible » (`exit 2`, fiches publiées intactes) et non
  en trace de pile qui coûte le commit du run (#518/#524) ;
- `--source senat` est refusée par argparse.

Et deux gels : `tests/test_retrait_senat_528.py` échoue si `extract-senat`
réapparaît dans `generate-data.yml`, si `--source senat` y revient, ou si
`nossenateurs` redevient une base d'URL ;
`test_le_senat_nest_plus_interroge_meme_pour_un_candidat_declare` échoue si
`CHAMBRES` regagne une entrée. Même mécanique que les deux tests retournés de
#527 sur `AN_ROSTER_ACTIF` : un verrou qu'on supprime le jour où il se déclenche
n'a jamais rien gardé.

## 9. Effet sur #486 / #495, et sur ce que l'UI affiche

Les deux profils à carrière bicamérale sont `jean-luc-melenchon`
(`chambres: ["AN", "Senat", "PE"]`, mandat sénatorial 2004-09-26 → 2010-01-07)
et `bruno-retailleau` (`chambres: ["AN", "Senat"]`, mandat sénatorial ouvert
depuis 2004-09-26). **Rien de ce qu'ils publient ne disparaît** en régime
nominal : mandats, `chambres`, `chambre`, votes, textes portés, interventions
sont tous conservés par la fusion additive. L'UI (`pivotAdapter`,
`CHAMBRE_LABELS`) continue donc d'afficher « Sénateur » sur la frise de
`bruno-retailleau` et les années sénatoriales de `jean-luc-melenchon`.

Le seul écart visible est la **liste des sources** de leurs fiches, qui perd une
entrée chacune (§3). Sur `bruno-retailleau`, celle qui part est la seule URL
NosSénateurs primaire du corpus.

Ce que ce lot **ne fait pas** : il ne dérive toujours pas `chambre` des mandats
(sous-issue D de #486) et ne porte pas la chambre sur chaque mandat au-delà de ce
que #492 a fait (sous-issue C). Le retrait du Sénat ne referme pas #486 — il
retire une source de collecte, pas une carrière déjà publiée. La distinction
compte : `chambre` reste `"AN"` sur Retailleau, sénateur en exercice, et c'est
toujours le fait faux que #486 décrit.

## 10. Ce que la suite de tests a dû abandonner, et pourquoi c'est écrit

Six tests ont perdu leur sujet avec la source, et les remplacer par du silence
aurait été la mauvaise façon de fermer ce lot :

- les quatre tests de `senat_periode_debut` (#191) : le filtre n'existe plus.
  Il en reste un, qui vérifie que `filter_roster_by_sigle` ne filtre **que** sur
  le sigle ;
- `test_un_profil_partiel_declare_ce_que_la_source_n_a_pas_rendu` (#514) :
  il regardait les sections `votes` et `dossiers législatifs` de
  `sections_vides`, qui n'existaient que sur le chemin sénatorial. Côté AN, ces
  champs viennent de l'open data, qui déclare ses propres échecs et n'incrémente
  pas `compteur_requetes_sans_reponse`. La distinction que le test protégeait —
  « un vide obtenu par silence n'est pas un constat » — reste couverte sur
  `identité` par les deux tests qui l'encadraient ;
- `test_from_roster_senat_warning_couverture_roster_senat_present` : la branche
  qui posait les deux avertissements Sénat sur une fiche de groupe est partie.
  Les fiches publiées gardent leurs avertissements, elles ne sont plus
  régénérées.

Trois autres blocs de tests CI sont partis avec le job : les quatre tests de
cohérence des deux budgets d'`extract-senat` (`test_ci_budget_par_job.py`) et
les quatre de son `timeout-minutes` (`test_ci_interventions_par_job.py`). Ils
portaient sur SES chiffres — 160 s par candidat, 600 s pour le job, 15 min de
plafond — pas sur une règle transposable telle quelle : les recopier sur un
autre job serait exactement l'erreur que #514 corrige, un chiffre mesuré sur une
population appliqué à une autre. Ce qu'il faudra refaire le jour où une
invocation repasse en `REGIME_BORNE` est écrit à leur place, dans le fichier.
Une des huit règles n'était PAS propre au Sénat — « pas de
`--budget-interventions-secondes` sous `--skip-interventions`, ce serait un
réglage mort » — et a été réécrite en test générique sur `MODE_JAMAIS`.

`JOBS_CACHE_LARGE_TOLERES` redevient **vide** dans les deux fichiers qui le
portent, plutôt que de garder le nom d'un job disparu : une tolérance qui
survit à son bénéficiaire est une porte ouverte que personne ne relit.

**Les fixtures Sénat de `tests/fixtures/` ne sont PAS retirées, et c'est
délibéré.** Celles qui décrivaient une *collecte* sénatoriale étaient toutes
inline dans les fichiers de tests (`IDENTITE_SENATEUR`, `_senateurs_payload`,
`_senateurs_raw_members`, `_GROUPE_LR_SENAT`) : elles ont été supprimées ou
rejouées sur l'Assemblée. Celles qui restent sous `tests/fixtures/` décrivent
des **valeurs publiées** — `chambre: "Senat"`, `sources[].type:
"nossenateurs"`, un `id` hérité `nossenateurs:<slug>` — qui restent valides dans
le schéma pivot (`KNOWN_CHAMBRES`, `KNOWN_SOURCE_TYPES`) et présentes dans les
476 profils committés. Les retirer ferait cesser les audits
(`audit_pivot_dataset`, `audit_diff_profils`, `audit_integrite_referentielle`)
de couvrir un état qui existe réellement dans le corpus : ce serait retirer un
contrôle, pas du code mort.

Les scénarios de `test_budget_collecte_source_injoignable.py`, eux, ont été
**rejoués sur l'Assemblée** plutôt que supprimés : les mesures venaient du Sénat,
le mécanisme n'en venait pas. `BASE_URLS` y est réduit à un domaine par la
doublure, parce que c'était la propriété de l'archive sénatoriale — un seul
domaine, donc un pire cas à 2 formats × 3 tentatives — que ces tests éprouvent,
pas le domaine lui-même.

---

