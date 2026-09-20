<a id="retrait-nosdeputes-529"></a>
# NosDéputés sort du pipeline (#529, lot 5 de l'épic « une seule source AN ») (2026-08-27)

`2026-08-27`

> **En bref** — le profil brut vient entièrement de l'open data AN.

**C'est un lot de retrait, pas de migration.** Chaque chemin qui passait par
NosDéputés.fr avait déjà migré, lot après lot : l'identité vers le référentiel
AMO30 (#355 puis #369 étape 4), les votes et les amendements vers l'open data
AN (#392, #403), les textes portés vers `fetch_textes_portes_officiels` (#400),
le roster de groupe vers `an_roster` (#526, bascule #527), et le Sénat est sorti
du périmètre (#528). Ce qui restait ici était **la dernière branche encore
appelée** : la recherche d'interventions, et le repli d'identité pour un député
absent des archives AN combinées.

Ce lot ne change donc pas de source. Il retire le code d'une source qui n'en
alimentait plus qu'une seule section — et il le fait en dernier parce que cette
section-là, `interventions`, est une liste surveillée **bloquante** (#460).

## 1. Ce qui est retiré

**`src/candidate_profile.py`** — la chaîne complète, du transport au résultat,
retirée d'un bloc parce qu'elle n'avait qu'un usage :

| Ce qui part | Ce que c'était |
| --- | --- |
| `BASE_URLS` | les 4 sous-domaines de législature, par chambre. Remplacé par `CHAMBRES_COLLECTEES`, qui garde le **garde-fou de chambre** sans la table d'URLs |
| `_get_with_watchdog`, `_get_payload`, `_TERMINAL_FAILURE`, `_try_urls` | le transport : `requests.get` sous budget mur (#443), 3 tentatives, court-circuit sur échec déterministe, essai `/json` puis `/xml` sur 4 domaines |
| `fetch_identity`, `_extract_parlementaire`, `_xml_to_data` | l'identité brute et son déballage |
| `_normalize_search_query`†, `fetch_recherche`, `fetch_all_intervention_results`, `fetch_all_intervention_results_from_domains` | le moteur de recherche d'interventions |
| `fetch_intervention_details`, `fetch_seance_context`, `_extract_speaker_identity_from_html`, `_classify_intervention`, `_classify_intervention_format`, `REACTION_COURTE_NB_MOTS_MAX`, `_to_int`, `_process_search_result`, `_extract_search_results` | le scraping HTML : l'orateur lu dans un `div.perso`, le sujet et les mots-clés lus dans la page de séance |
| `_extract_mandats`, `_extract_responsabilite_entries`, `_groupe_label` | les responsabilités lues dans un profil brut NosDéputés |
| `compteur_appels_nosdeputes` (#467), `compteur_requetes_sans_reponse` (#514), `WARNING_PREFIX_SOURCE_INJOIGNABLE`, l'étape 9quater et le canal `journal` | les deux compteurs et le warning qu'ils alimentaient |

† `_normalize_search_query` est la seule rescapée, et elle a **changé de
métier** : écrite pour aplatir casse et accents d'une requête envoyée au moteur
de recherche, elle sert désormais la correspondance slug ↔ acteur AN
(`_build_acteur_nom_index`, `_resolve_acteur_ref_par_slug`). Elle a déménagé à
côté de ses deux appelants. Son nom reste le sien : le changer effacerait la
seule chose que ce nom garde lisible, l'origine de la règle.

**`src/group_roster.py`** — la lecture NosDéputés **et toute la machinerie de
reprise qui l'entourait** : `fetch_full_roster_nosdeputes`, `_base_url_for`,
`_BASE_URL_BY_LEGISLATURE_AN`, `_LIST_ENDPOINT`, `_erreur_retentable`,
`_STATUTS_5XX_RETENTABLES`, `_ROSTER_MAX_ATTEMPTS`,
`_ROSTER_RETRY_BACKOFF_SECONDS`, `_ROSTER_TIMEOUT`. Cette machinerie avait coûté
deux incidents et deux lots (#518, #524) : elle était dimensionnée pour un
endpoint de **814 Ko généré à la volée**, dont « aucune réponse en moins de
10 s » avait été mesurée sur 24 appels, et qui a fini par servir un **500
déterministe** trois runs durant. Sur une archive lue depuis
`.cache/acteurs_historique_an/`, elle n'a plus d'objet — le téléchargement de
l'archive AMO30 a ses propres reprises, dans
`candidate_profile._ensure_acteurs_historique_zip_downloaded`.

Le module **reste**, contrairement à ce que l'issue proposait : il porte
`filter_roster_by_sigle`, le transit des rosters bruts par artifact (#518) et
`ERREURS_ROSTER`, que trois appelants lisent. Ce qui était « sans objet » après
le lot 1b, c'est sa lecture réseau, pas son contrat.

**`src/generate_all_profiles.py`** — le cumul `identite_sans_reponse`, le
`journal` qui le remontait, et la **temporisation de courtoisie** de
`process_candidat` : elle ménageait une API publique tierce. Ce qui reste sur le
réseau — l'open data AN — est du téléchargement d'archive mis en cache par
législature, pas des pages par candidat : il n'y a plus rien à lisser.

**Le renommage.** `normalize_nosdeputes.py` devient **`normalize_profil.py`**,
et sa fonction `normalize_nosdeputes()` devient `normalize_profil()`. Le nom
datait du jour où le profil brut venait effectivement de cette plateforme ; ce
module n'a jamais connu la source, seulement la **forme** du profil brut.
`_SOURCE_TYPE_MAP` part avec : `sources[].type` vaut `assemblee_nationale`, et
la chambre ne décide plus de la provenance parce qu'il n'y a plus qu'une
provenance. Le diagramme d'`AGENTS.md` §3 et `README.md` suivent.

**Alternative écartée : `normalize_an.py`.** Elle aurait aligné le nom sur
`normalize_europarl.py`, nommé d'après sa source. Écartée parce que ce module
est justement celui qui **ne connaît pas** la source : il lit la forme du
profil brut, et lui redonner un nom de source rejouerait dans dix-huit mois la
question qu'on tranche aujourd'hui.

**Les entrées antérieures de ce fichier ne sont pas réécrites.** Elles citent
`normalize_nosdeputes.py` : c'était son nom, et une décision datée qu'on
réécrit pour qu'elle colle au présent cesse d'être une décision datée. La
correspondance est ici, une fois.

## 2. La conséquence déclarée : les interventions

C'est le point à lire, et il n'est pas confortable.

Le repli NosDéputés a produit **496 des 789 interventions publiées**, parce que
Syceron — la source *primaire* — n'en indexait aucune : #510 a montré que
l'archive publie l'identifiant d'orateur **nu** (`<orateur><id>847629</id>`)
alors que le code y appliquait `re.fullmatch(r"PA\d+")`.

**Mis à jour au rebasage (27/08/2026).** La rédaction d'origine de cette
section décrivait un lot livré alors que le correctif de #510 était encore
inactif, et en tirait la conséquence « une collecte neuve rend
`interventions[] = questions officielles seules ». Cette conséquence n'existe
plus : #510 a été **activé** le 27/08/2026 (le drapeau
`SYCERON_RESOLUTION_ACTEUR_NU_ACTIVE` a disparu avec lui), trois minutes avant
que la branche de ce lot ne soit poussée. Syceron est désormais la source
unique **et alimentée** des prises de parole.

Ce qui suit reste vrai et reste le contrat du lot — ce sont les garde-fous qui
rendent une régression impossible à passer sous silence, que Syceron rende
beaucoup ou rien :

- **le corpus publié ne bouge pas.** La fusion additive ne retire rien
  (`merge_lists_by_key`, l'ancienne entrée gagne), et sous `--no-merge` le
  garde-fou de #465 refuse qu'une collecte **vide** écrase une section peuplée ;
- **une régression ne peut pas être muette.** `interventions` est une liste
  surveillée **bloquante** d'`audit_diff_profils` (#460/#470) : un run
  `cold_start` qui collecterait des questions (non vide, donc #465 ne joue pas)
  sans les prises de parole ferait **abort le commit**, en nommant les profils.
  C'est le seul garde-fou qui compte ici, et il était déjà armé ;
- **le vide est déclaré par profil.** `WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES`
  est publié dans `meta.warnings` dès que Syceron ne rend rien, et il **nomme
  #529** : une section vide se lit par défaut comme « cette personne n'a jamais
  parlé » (AGENTS.md §2 règle 5).

**Le préfixe de ce warning est délibérément inchangé.** Il valait
`"interventions syceron indisponibles (fallback nosdeputes)"` ; il vaut
`"interventions syceron indisponibles"`. Les warnings déjà publiés commencent
par le nouveau préfixe, donc l'agrégation par préfixe
d'`audit_pivot_dataset.compute_agregation_warnings` continue de les compter
avec les nouveaux. Un renommage complet aurait scindé en deux une même
population sans que rien ne le dise.

**Le prérequis du lot 4 est tenu.** L'issue posait #510 comme prérequis au sens
« interventions Syceron publiables ». Écrite avant #537, cette entrée
argumentait qu'on pouvait s'en passer ; l'argument n'a plus à servir. Reste
vraie la raison de fond : garder le collecteur NosDéputés aurait laissé armé un
chemin que plus rien ne justifiait, pour une donnée que le corpus conserve
déjà. Ce qui aurait été inacceptable, c'est que la perte soit **possible et
silencieuse** — elle est impossible sous fusion, et bloquante sous
`--no-merge`.

## 3. Ce qui n'est PAS retiré, et pourquoi

Le critère de l'issue est un `grep` sur le **code exécuté**, pas sur la prose.
Appliqué strictement, il laisse cinq emplacements, en deux familles. Aucun ne
collecte.

**(a) Ceux qui LISENT le corpus publié.** Les retirer casserait ce corpus
plutôt que de le nettoyer ; leur sort est le **lot 6**, avec les mentions
d'attribution ODbL :

| Emplacement | Pourquoi il reste |
| --- | --- |
| `schema_pivot.KNOWN_SOURCE_TYPES` ⊇ `{nosdeputes, nossenateurs}` | **476 profils publiés** portent l'un de ces types ; les retirer ferait refuser par `validate_profil()` le corpus qu'on vient de publier |
| `audit_pivot_dataset.MAPPING_CHAMBRE_SOURCES` (`AN`, `Senat`) | même population, vue par l'audit : sans elles, il déclarerait « incohérence chambre/sources » sur des profils parfaitement valides |
| `normalize_profil` relit `meta.synchro_sources.nosdeputes` en repli | les profils bruts collectés avant ce lot ne portent que cette clé, et la fusion additive les garde. Sauter ce repli ferait **reculer** `sources[].synchro_le` vers `genere_le` sur tout profil non recollecté — un horodatage de fraîcheur qui régresse sans qu'aucune donnée n'ait bougé |
| le repli `interventions[].mots_cles` → `tags_thematiques` | il dérive les **647 `tags_thematiques` publiés**, et les `mots_cles` viennent du scraping. Les couper ferait tomber une liste surveillée **bloquante** |

**(b) Ceux qui la NOMMENT dans un message, au passé.** Un texte destiné à un
lecteur, pas une URL qu'on appelle : le `meta.warnings` publié de
`group_profile._avertissement_fraicheur_an` (#527 a explicitement décidé qu'il
devait dire « et non plus de www.nosdeputes.fr » — deux versions successives
d'une même fiche doivent se relire l'une contre l'autre, règle 2), et le refus
de chambre de `group_roster.fetch_full_roster`, qui nomme
`archive.nossenateurs.fr` parce que c'est la panne qui a motivé #528.

Cette liste est **fermée et vérifiée** par
`tests/test_retrait_nosdeputes_529.py`, qui parcourt l'AST de `src/*.py` et ne
regarde que les **chaînes et les identifiants** — jamais les commentaires ni
les docstrings. Une sixième occurrence fait échouer la suite.

## 4. Le corpus ne bouge pas — sauf sur trois champs, tous non bloquants

Aucun fichier de `pivot_data/` n'est touché par ce lot. Ce qui suit décrit ce
qu'une **régénération** produirait de différent, et le classement de chacun
selon `audit_diff_profils` :

| Champ | Avant | Après | Statut |
| --- | --- | --- | --- |
| `sources[].type` (1re entrée) | `nosdeputes` / `nossenateurs` | `assemblee_nationale` | changement de valeur — **non bloquant** (#460) |
| `sources[].url` (1re entrée) | `https://www.nosdeputes.fr/<slug>` | la fiche AN de l'acteur (`.../OMC_PA####`) | idem |
| `meta.warnings` | `synchro_sources.nosdeputes : aucune synchro…` | `synchro_sources.assemblee_nationale : …` | `meta.warnings` n'est pas une liste surveillée |

Le warning de synchro change de clé pour une raison de fond : l'ancienne était
`None` sur presque tout le corpus **depuis #369** — un député résolu dans le
référentiel AN ne déclenchait aucun appel NosDéputés, donc aucune synchro à
horodater. Le warning décrivait le fonctionnement normal, ce qui est la
définition d'un warning qui ne dit plus rien. `assemblee_nationale` est
renseignée dès que l'identité est trouvée : à `None`, elle signale une vraie
absence de collecte.

`raw_data/roster_candidats.json` change aussi de `source` par entrée (fiche AN
au lieu de `<domaine>/<slug>`) : c'est un artifact de run, pas un fichier
publié. `filter_roster_by_sigle` fait désormais traverser l'`acteur_ref` du
membre, ce qui est ce qui rend cette URL possible — `None` quand la source n'en
publie pas, jamais inventée (règle 5).

## 5. Les transitoires des lots amont : ce qui est soldé, ce qui ne l'est pas

Le critère d'acceptation demande que les conditions de retrait des transitoires
des lots 1 et 4 soient **soldées, pas laissées ouvertes**. Voici l'état, sans
arrondi.

**Soldé — le repli de roster de #527.** La condition écrite était « le drapeau
et le repli tombent ensemble ». Le **repli** est retiré ici : il n'existe plus
de seconde source de roster. `AN_ROSTER_ACTIF` **reste**, et c'est délibéré :
ce n'est plus un aiguillage mais un **interrupteur**, et sa seule fonction est
désormais le refus bruyant (`RosterAnInactif`) que #511 et #524 ont payé pour
obtenir. Un roster vide écrit sur disque est indiscernable d'un groupe dissous.
Un drapeau qui ne bascule sur rien mais qui garde ce refus n'est pas un
transitoire : c'est un garde-fou.

**Soldé — le repli d'interventions de #510.** La condition écrite était
l'activation de Syceron. Elle **est remplie** depuis le 27/08/2026 : #537 a
activé la résolution de l'identifiant d'orateur nu et retiré le drapeau. Le
repli qu'elle devait remplacer part ici. Il ne reste ni transitoire, ni section
déclarée vide — la source primaire alimente réellement le chemin.

**NON soldé, et ce lot ne peut pas le solder — le double calcul de #526 §9.**
Des trois clauses écrites, la première tient (`membres_sans_slug` = 4, aucune
fiche de la 17e publiée), la deuxième est mesurée à chaque run
(`ROSTER_SANS_SLUG`), et la **troisième** exige de décider *comment naît un
slug quand la source n'en publie aucun*. C'est une décision de **schéma**, pas
une passe de collecte : AMO30 publie un `PA######` et l'état civil, et le slug
**est** l'`id` du profil (#487). La trancher ici aurait été la trancher en
passant, dans un lot de retrait. `--divergence` reste le compteur de migration,
et `an_roster.py --divergence` reste le moyen de le lire.

## 6. Les tests : relus un par un, pas renommés en masse

**Supprimés avec le code qu'ils décrivaient**, parce qu'un test qui fige un
comportement inexistant rend son retour indolore — l'arbitrage des deux
fixtures inventées de #510 :

- `tests/test_roster_reprise_reseau.py` et `tests/test_roster_timeout_lecture.py` :
  la politique de reprise et le plafond de lecture de `/deputes/json` ;
- `tests/test_interventions_senat_non_retenues.py` : pourquoi la collecte
  d'interventions sénatoriales rendait **zéro** (`fetch_intervention_details`
  lisait `url_nosdeputes`, l'archive publiait `url_nossenateurs`). Le fait
  mesuré reste écrit dans `#retrait-senat-528` §2 ; le code qui le produisait
  n'existe plus, et la condition de réouverture du §7 devra de toute façon être
  ré-établie sur la source de remplacement, pas sur celle-ci.

**Réécrits en place**, parce que le fait testé existe toujours à un autre
endroit : l'estampille de chambre sur le mandat électif est passée de
`_extract_mandats` à `build_profile`
(`tests/test_chambre_par_mandat.py`) ; l'aiguillage de `fetch_full_roster` est
devenu un refus (`tests/test_group_roster.py`) ; l'avertissement de fraîcheur
n'a plus qu'une rédaction (`tests/test_bascule_roster_an_527.py`) ; la chaîne
de budgets de #514 survit à la disparition de son transport
(`tests/test_budget_collecte_source_injoignable.py`).

**Laissés tels quels** : les fixtures qui portent `nosdeputes` **parce
qu'elles décrivent le corpus publié ou déjà collecté** — `sources[].type` des
pivots d'audit, URLs d'interventions et de dossiers dans les profils bruts,
`synchro_sources.nosdeputes`. Les renommer serait décrire un corpus qui
n'existe pas.

`tests/conftest.py` est inchangé : il coupe toujours `requests.Session.send`
et échoue bruyamment en nommant l'URL (#488).

## 7. Les deux retraits de `.github/workflows/` — faits au rebasage

L'agent qui a écrit ce lot ne pouvait pas modifier `.github/workflows/`, et
avait donc laissé deux points en suspens. Les deux sont soldés :

1. **`debug-network-shutdown-signal.yml` est supprimé dans ce lot.** C'était un
   workflow de diagnostic entièrement consacré à sonder
   `www.nosdeputes.fr/synthese/data/json` contre un groupe témoin. Il n'a plus
   d'objet.
2. **`--max-pages 5` a été retiré de `generate-data.yml` par #510**, avant même
   ce lot. Le compromis écrit ici — accepter le drapeau mais le signaler sur
   `stderr` — n'avait de sens que tant que la CI l'émettait encore. Plus aucun
   appelant ne le passe : `AIDE_MAX_PAGES_SANS_EFFET`,
   `signaler_max_pages_sans_effet` et leur test sont retirés au rebasage
   plutôt que livrés désarmés.

Reste hors périmètre de ce lot : `claude.yml` et `claude-code-review.yml`
listent encore les six domaines `*.nosdeputes.fr` / `*.nossenateurs.fr` dans
leur `allowedDomains`. C'est la permission réseau de l'agent, pas un chemin du
pipeline ; devenue inutile, elle n'est pas nuisible.

---

