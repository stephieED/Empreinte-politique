<a id="perimetre-controle-perte"></a>
# Le périmètre du contrôle de perte : ce qu'il couvre, ce qu'il ne couvre pas (#470) (2026-08-20)

`2026-08-20`

> **En bref** — les cinq couches publiées et les deux index partagés, pas seulement les profils.

Le contrôle branché par #460 avant le commit de données ([[controle-de-perte-avant-commit]])
avait deux angles morts, et les deux ont laissé passer une perte réelle **alors
qu'il tournait** :

1. il ne lisait que `pivot_data/profiles`, jamais `groupes/`, `partis/`,
   `gouvernements/`, ni les index partagés `scrutins.json` et `amendements/` ;
2. il ne comparait que des **longueurs de listes**, si bien qu'un scalaire qui
   régresse lui était invisible.

Les deux pertes, reproduites depuis l'historique :

| perte | avant | après | vue par le contrôle |
| --- | --- | --- | --- |
| `groupe-AN-SOC-16` · `cohesion_votes` (`25f7bc7` → `a125e9e`) | 814 | **0** | non |
| `groupe-AN-SOC-16` · `mandats_agreges` | 44 | 23 | non |
| `groupe-AN-REN-16` · `mandats_agreges` | 1 032 | 646 | non |
| `parti` sur 3 profils (`e4d71cf` → `ffa24ec`) | renseigné | **null** | non |

La première n'est pas une fiche incomplète : c'est un **dénominateur publié
devenu faux** (AGENTS.md §2.7). La seconde était invisible partout, y compris à
l'écran — `pivotAdapter` retombe sur `manifestEntry.parti`, issu de
`candidats.json` : la donnée publiée était fausse et l'affichage restait juste.

## Le périmètre, désormais explicite

Un périmètre tacite se croit complet ; celui-ci s'énonce, dans le module, dans
le rapport Markdown produit à chaque run, et ici.

| couche | listes bloquantes | listes signalées | scalaires surveillés |
| --- | --- | --- | --- |
| `profiles` | `votes`, `mandats`, `textes_portes`, `interventions`, `tags_thematiques`, `dossiers_legislatifs` | `amendements`, `sources` | `id`, `nom`, `chambre`, `parti`, `groupe`, `identite`, `meta.provenance` |
| `groupes` | `membres`, `cohesion_votes`, `mandats_agreges`, `tags_thematiques_agreges`, `historique_noms` | `sources` | `groupe_id`, `groupe_sigle`, `groupe_nom`, `chambre`, `legislature`, `periode.debut`, `meta.couverture_roster.roster_total` |
| `partis` | `candidats`, `tags_thematiques_agreges` | `sources` | `parti_id`, `parti_nom` |
| `gouvernements` | `membres`, `textes` | `sources` | `gouvernement_id`, `nom`, `premier_ministre`, `periode.debut` |
| `scrutins.json` | — | `scrutins` | `schema_version`, `licence_donnees` |
| `amendements/` | — | `amendements` | `schema_version`, `legislature`, `licence_donnees` |

Trois familles de constats **bloquent** : un fichier disparu, une baisse sur une
liste bloquante, un scalaire surveillé passé de renseigné à `null`.

## De quel côté chaque arbitrage penche, et pourquoi

Ce contrôle décide si un commit de données part. Un faux positif bloque la
publication de données saines ; un faux négatif laisse passer une perte. Chaque
choix a donc été instruit contre l'historique réel — les 13 transitions
committées entre le 16 et le 20/08/2026 — et non contre une intuition.

**Scalaire `renseigné → null` : bloquant.** 10 occurrences sur ces 13
transitions, **10 défauts réels**, aucun faux positif — les quatre `parti`
écrasés par la passe roster-driven, les trois `parti` des restaurations de
#460/#465, deux `identite`, un `groupe`. Le contrat de fusion l'interdit déjà
explicitement (AGENTS.md §3 : « Scalars: new value if populated, else keep old
— **never regress to null** ») : une régression vers `null` est une violation de
contrat, jamais un fait mesuré (règle §2.5).

**Changement de valeur d'un scalaire : signalé, non bloquant.** 129 occurrences
sur les mêmes transitions, quasi toutes légitimes : normalisations (`'REN'` →
`'Renaissance'`, `'LREM'` → `'Ensemble pour la République'`), accents
(`'Edouard Philippe'` → `'Édouard Philippe'`), bascules de source
(`nosdeputes` ↔ `nossenateurs`, et le `chambre` qui suit), `meta.provenance` qui
alterne `candidat_declare` / `roster_groupe` selon l'ordre des passes. Bloquer
là-dessus interdirait presque tous les commits de données. **Faux négatif
assumé** : un changement suspect — Mélenchon passant de `AN` à `Senat` — est
relevé dans le rapport, à charge de relecture humaine. C'est le seul endroit du
contrôle où la décision revient à un lecteur.

**Index partagés : signalés, non bloquants.** Une baisse du nombre d'entrées
distinctes serait grave — « an uncommitted index leaves every mapping pointing
at nothing, silently » — mais elle est aussi le résultat attendu d'une
correction de clé, ce qu'ont fait #431 et #432. Or ce sont des **totaux de
corpus**, pas des mesures par fiche : les rendre bloquants forcerait l'opérateur
à relancer avec `tolerer_pertes_profils=true`, qui désarme du même coup les
contrôles **précis** par profil et par groupe. Bloquer sur le compteur le plus
grossier pour faire taire les plus fins serait le pire des échanges. La
**disparition** d'un fichier d'index, elle, reste bloquante : elle n'a aucune
explication légitime.

**`sources` : signalé, non bloquant.** Son historique montre des baisses
(16 → 15, 4 → 3, 3 → 2) qui accompagnent tantôt une perte réelle, tantôt une
sous-collecte non rejouée. Quand elle accompagne une perte réelle, le champ qui
la cause vraiment bloque déjà.

**`membres` d'un groupe : bloquant, mais pas `effectif.actuel`.** Le premier est
un enregistrement dont la disparition est une perte ; le second compte les
membres **actifs** et baisse légitimement quand un élu quitte le groupe.

## Trois erreurs dans le diagnostic de l'issue, corrigées

- **`votes_source` n'existe pas dans le pivot.** L'issue le cite parmi les
  « autres scalaires exposés ». Mesuré sur les 209 profils de `3a8455a` et sur
  7 refs de l'historique : la clé n'apparaît nulle part. C'est un champ de
  `raw_data/profiles` (`candidate_profile.py`), que la passe pivot ne reporte
  pas. Non surveillé, donc.
- **`dossiers_legislatifs` est inerte pour la même raison** — il figurait dans
  les champs stables depuis l'origine et ne pouvait jamais se déclencher :
  aucun pivot ne porte cette clé, `normalize_nosdeputes` la verse dans
  `textes_portes`. Conservé (il couvre `--profils-dir raw_data/profiles`), mais
  il ne faut pas le compter comme une protection.
- **La perte de `parti` ne date pas de `a125e9e^`**, comme l'écrit
  [[mandat-electif-perdu-fausse-le-denominateur]]. `a125e9e` **et** `e4d71cf`
  portent encore les trois `parti`. La régression est entrée en `ffa24ec` — la
  première des deux restaurations — et a été corrigée en `e82406a`. Le
  mécanisme décrit reste juste ; c'est la datation qui était fausse.

Et un angle mort que l'issue ne nommait pas : **`tags_thematiques` n'était
surveillé nulle part**. C'est un champ publié (AGENTS.md §6), passé de 647 à 0
dans le run que #460 documente — le rapport de #460 le comptait dans ses dégâts
sans que le contrôle le regarde. Il rejoint les listes bloquantes.

## Ce que le contrôle étendu trouve dès sa première exécution

Passé sur `25f7bc7` → `3a8455a`, il signale une perte **toujours présente dans
le corpus** : `jean-luc-melenchon.pivot.json` · `identite`, un bloc renseigné en
`25f7bc7` et `null` depuis `a125e9e`. Personne ne l'avait vue — c'est
exactement la classe de défaut que #470 décrit, et elle n'est pas corrigée ici :
c'est une donnée à restaurer, pas un défaut d'outil, et la mêler à l'extension
du contrôle mélangerait deux sujets. Consignée pour qu'elle ne se reperde pas.

## Le dimensionnement, qui était le vrai risque

Ce script tourne **avant** le commit : s'il meurt, rien n'est publié, et un
garde-fou qui meurt est pire qu'un garde-fou absent — il donne une assurance
qu'il ne tient pas. Il s'est déjà fait tuer par l'OOM killer une fois
([[controle-de-perte-avant-commit]]).

Mesuré sur le corpus réel (`3a8455a`, 209 profils, `--ref HEAD`, même machine,
`/usr/bin/time -v`, médiane de trois exécutions) :

| | durée | RSS max |
| --- | --- | --- |
| avant — profils seuls | 2,79 s | 133,4 Mio |
| **après — 5 couches + 2 index** | **4,74 s** | **184,8 Mio** |
| après, `--seulement-profils` | 2,89 s | 133,4 Mio |

Sous les 236 Mio que #460 avait actés, pour six collections au lieu d'une. La
troisième ligne isole le coût : à périmètre égal, la réécriture ne coûte rien —
tout l'écart vient des cinq collections ajoutées. Deux règles y suffisent :

- **un seul document en mémoire à la fois**, jamais le corpus — la lecture en
  flux du `git cat-file --batch` de #460 sert désormais toutes les collections ;
- **les `*.cosignatures.json` ne sont jamais ouverts.** Mesuré fichier par
  fichier, `15.cosignatures.json` coûte à lui seul **222 Mio** de RSS à parser,
  plus que tout le reste du contrôle réuni, pour 25,7 Mo sur disque. Aucun
  consommateur ne les lit (AGENTS.md §3). Ils sont **listés** — donc leur
  disparition, le seul cas catastrophique, est détectée gratuitement — mais
  jamais rapatriés : le `--batch` ne les demande même pas.

Le motif d'exclusion est **négatif** (`*.cosignatures.json`) et non positif :
`fnmatch` laisse `*` traverser le point, si bien qu'un `[0-9]*.json` censé ne
retenir que `14.json` attraperait aussi `14.cosignatures.json`. Écrit dans
l'autre sens, l'économie de mémoire aurait été silencieusement annulée.

Les index n'ont d'ailleurs **pas** vocation à grossir avec le corpus : leurs
207 238 amendements distincts sont déjà le chiffre de pleine échelle
d'AGENTS.md — ils sont construits à partir des archives AN figées, pas des
209 membres actuels. Le passage à 752 membres n'y changera rien.

## Ce que le contrôle ne couvre toujours pas

Énuméré ici *et* dans le rapport produit à chaque run, parce qu'un périmètre
qu'on ne dit pas se croit complet :

- ~~**l'intégrité référentielle** entre un `votes[].scrutin_id` d'un profil et
  `pivot_data/scrutins.json`, ou entre un `amendements[].amendement_id` et son
  index~~ — **comblé par #485**, voir [[integrite-referentielle-pivot]].
  `src/audit_integrite_referentielle.py` tourne dans `merge-and-pivot`, juste
  après ce contrôle-ci et avant le commit, et couvre les trois renvois de
  `pivot_data/` (`votes[].scrutin_id`, `cohesion_votes[].scrutin_id` d'un
  groupe, `amendements[].amendement_id`). Ce contrôle-ci ne le couvrira jamais,
  et c'est structurel : il compare un **avant** et un **après**, quand
  l'intégrité référentielle est une **invariance dans un état donné** — deux
  couches régénérées de façon cohérente-mais-fausse ne bougent aucun compteur.
  Deux contrôles complémentaires, avec **deux tolérances cloisonnées** :
  `tolerer_pertes_profils` ne désarme pas `tolerer_references_orphelines`, et
  réciproquement. La raison invoquée ici — « il faudrait tenir les deux
  ensembles de clés en mémoire simultanément » — était **fausse** : il n'en faut
  qu'un, le petit, et le côté référençant se parcourt un document à la fois ;
- **le contenu des entrées d'une liste** : seule leur cardinalité est comparée.
  Un `votes[]` dont toutes les positions basculeraient à `null` passerait ;
- **le contenu d'un scalaire de type bloc** (`identite`, `premier_ministre`) :
  seule sa présence est comparée ;
- **le contenu des `*.cosignatures.json`**, pour la raison de mémoire ci-dessus ;
- **`effectif` d'un groupe** : des compteurs dérivés, qui bougent
  légitimement dans les deux sens et dont les listes amont sont déjà
  surveillées. `amendements_agreges` et `comptages` figuraient ici pour le même
  motif ; sa seconde moitié était fausse et
  [[agregats-publies-controle-perte-649]] la mesure — sur `a125e9e` la fiche
  `AN:LFI-16` perd ses 11 561 amendements et son `taux_adoption` sans qu'une
  seule liste amont bouge. Les deux blocs sont désormais surveillés, en
  **scalaires** : leur disparition bloque, la baisse de leur valeur est relevée ;
- **le changement de valeur d'un scalaire**, non bloquant par choix (ci-dessus).

## Les tests sont adossés aux pertes réelles

`tests/test_audit_diff_agregats.py` rejoue les deux pertes depuis des fixtures
figées (`tests/fixtures/audit_diff_pertes_reelles/`, provenance dans
`meta.fixture`, sur le modèle de `tests/fixtures/gouvernement_roster/`), jamais
depuis le corpus vivant — absent du disque en CI ([[ci-tests-pytest]]). Les
listes y sont réduites à leur cardinalité, seule chose que le contrôle lise :
les 814 entrées réelles de `cohesion_votes` pèsent 1,3 Mo dont pas une n'est
lue.

Deux tests portent la démonstration plus que les autres :
`test_le_perimetre_d_avant_470_etait_aveugle_a_la_perte_soc16`, qui applique
l'ancien périmètre aux fixtures de groupe et ne relève rien, et
`test_ce_run_ne_perdait_aucune_liste_et_passait_donc_inapercu`, qui montre que
sur le run où `parti` a disparu **toutes** les listes ne faisaient que croître —
`jean-luc-melenchon` y regagnait 1 016 votes et 18 721 amendements. Un contrôle
de longueurs de listes y voyait un run exemplaire.

