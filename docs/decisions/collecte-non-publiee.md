<a id="collecte-non-publiee"></a>
<a id="roster-jamais-ecrit-vide"></a>
# Un timeout ne peut plus écraser le roster, et rien de collecté ne reste non publié (#511) (2026-08-20)

`2026-08-20`

> **En bref** — rien de collecté ne reste non publié (seuil 0), et un timeout ne peut plus écrire un roster vide.

Run `32405297873` (20/08/2026, 18:49 → 19:10), **conclusion `success`**, 16 jobs
sur 16 verts, commit `68bc094` poussé sur `main`. Dans `merge-and-pivot`, étape
« Normalisation pivot roster-driven » :

```
  [!] Récupération du roster impossible pour ('deputes', '16') :
      … Read timed out. (read timeout=15)
  [!] Récupération du roster impossible pour ('senateurs', None) :
      … Read timed out. (read timeout=15)
→ 0 candidat(s) écrit(s) dans raw_data/roster_candidats.json.
```

`generate_roster_candidats.py` a écrit une liste vide et rendu 0. La passe
suivante — `generate_all_profiles.py --pivot-only --candidats
raw_data/roster_candidats.json` — a donc itéré sur zéro candidat.

**Mesuré sur `68bc094`** (`git ls-tree` sur les deux répertoires) : 229 profils
bruts, 209 pivots. Les 20 membres de roster collectés par ce run n'ont aucun
pivot, donc ne sont publiés nulle part. Vérifié sur trois d'entre eux
(`caroline-yadan`, `damien-adam`, `vincent-ledoux`) : `chambre: "deputes"`,
2 281 à 3 536 votes, 59 à 124 mandats chacun. De la donnée complète, sur le
disque, qui n'atteint aucune vue.

## Deux défauts, et ce que chacun coûte à pleine échelle

**1. Une donnée non résolue reçoit la pire valeur par défaut.** La fonction
refusait déjà d'écrire sur une **entrée** vide (« aucun groupe à agréger ») et
écrivait une **sortie** vide trois lignes plus bas, en rendant 0. Même
raisonnement, même fichier, trois lignes d'écart. C'est la règle 5 de AGENTS.md
§2, à la lettre.

**2. Personne ne rapprochait les deux comptes.** 229 et 209 — deux nombres que
le pipeline connaît, qu'aucun contrôle ne compare.

À `roster_limit = 0`, le même timeout ferait collecter 543 nouveaux membres et
n'en publierait aucun, pour un run d'une heure conclu en succès.

## Ce que le diagnostic de l'issue disait de trop

L'issue écrit que « le dégât a été borné **par chance** : `roster_candidats.json`
n'est pas dans le `git add` du workflow ». **Ce n'est pas de la chance.** Le
fichier est explicitement gitignoré depuis #413 §5 (`.gitignore` l. 65-72 :
« source de vérité = `raw_data/groupes_reels.json` »), précisément pour qu'il ne
dérive pas dans le temps.

Cette précision n'est pas cosmétique, elle **élimine une des trois pistes** :
comme le fichier n'est pas suivi, `actions/checkout` ne le restaure jamais sur le
runner. La piste « conserver l'existant plutôt que l'écraser » n'aurait donc
**rien à conserver** dans le seul contexte où l'incident s'est produit — il
n'existe aucun roster précédent sur le disque d'un job CI. Elle reste correcte en
local, où le fichier persiste, et le correctif la couvre gratuitement : ne pas
écrire, c'est laisser intact ce qui était là (`tests/test_generate_roster_candidats.py::test_un_roster_existant_n_est_pas_ecrase_par_une_collecte_en_echec`).

## Décision 1 — le roster n'est jamais écrit sur une collecte incomplète

`main()` refuse d'écrire et rend 1 sur **trois anomalies**, dans cet ordre :

| Anomalie | Ce qu'elle attrape |
| --- | --- |
| un fetch en échec (`None` dans `rosters_bruts`) | l'incident, et tout échec **partiel** |
| un groupe configuré rendant 0 membre, fetch réussi | un sigle renommé en amont |
| un roster total vide | le filet de dernier recours |

Le `bash -e` par défaut des steps GitHub Actions propage ce 1 : **le run ne peut
plus se conclure en succès.** Un run coupé là ne perd rien — les profils bruts
sont dans les artifacts, la fusion est additive, le run suivant publie.

## Le seuil de rétrécissement : tranché, et écarté au profit de la cause

La question posée était : faut-il aussi refuser un roster qui rétrécit fortement,
752 → 12 étant aussi suspect que 752 → 0 ? **Oui — mais un seuil chiffré est le
mauvais outil ici, pour deux raisons mesurées.**

*Il n'a pas de base de comparaison là où il servirait.* Le fichier étant
gitignoré, un job CI n'a aucun roster précédent : un test de rétrécissement y
serait du code mort, dans le seul endroit qui compte.

*La granularité d'une panne n'est pas le membre, c'est la clé de fetch entière.*
Population : les 752 entrées de `raw_data/roster_candidats.json` produit le
19/08/2026 à 11:16 depuis les 7 groupes de `raw_data/groupes_reels.json`.

| Clé de fetch | Membres | Part |
| --- | ---: | ---: |
| `('deputes', '16')` | 452 | 60,1 % |
| `('senateurs', None)` | 300 | 39,9 % |

| Groupe | Membres |
| --- | ---: |
| `AN:REN` | 193 |
| `AN:RN` | 90 |
| `AN:LFI` | 76 |
| `AN:LR` | 62 |
| `AN:SOC` | 31 |
| `Senat:LR` | 235 |
| `Senat:SER` | 65 |

Un échec **partiel** n'enlève donc pas « quelques » membres : il en enlève 452 ou
300 d'un coup, et laisse un roster **non vide** qu'aucun test de vacuité ne
verrait. Or cet échec est **directement observable** — `fetch_rosters_bruts` le
consigne déjà, l'information était simplement jetée. Détecter la cause donne zéro
faux positif et zéro constante arbitraire ; un seuil devrait être placé sous 40 %
pour attraper le même cas, sans qu'aucune mesure ne le fonde.

Reste le seul mécanisme de rétrécissement qui ne passe pas par un échec réseau :
un sigle qui ne matche plus en amont, donc un groupe filtré à 0. D'où la
deuxième anomalie — un groupe configuré à 0 membre bloque, quel que soit le
total. Les 7 groupes rendent aujourd'hui entre 31 et 235 membres ; aucun n'est
proche de 0, et un groupe réellement dissous se retire de la config en une ligne.

`--autoriser-roster-incomplet` existe pour le travail local et pour qu'une panne
de ce garde-fou ne bloque pas indéfiniment. **Il n'est câblé sur aucun input du
workflow**, délibérément — le remède d'une source en timeout est de relancer, pas
de publier quand même — et un test le vérifie.

## Décision 2 — un contrôle « collecté mais non publié », branché avant commit

`src/audit_collecte_non_publiee.py` rapproche `raw_data/profiles/<slug>.json` et
`pivot_data/profiles/<slug>.pivot.json`. **Troisième angle**, et c'est pourquoi
c'est un contrôle à part :

| Contrôle | Ce qu'il compare | Pourquoi il ne voit pas #511 |
| --- | --- | --- |
| `audit_diff_profils` (#460/#470) | un **avant** et un **après** | rien n'a été *perdu* : les deux compteurs montent |
| `audit_integrite_referentielle` (#485) | les clés **publiées** résolvent-elles | ce qui n'a jamais été publié ne porte aucune clé |
| `audit_collecte_non_publiee` (#511) | le **collecté** et le **publié** | — |

C'est cette troisième piste qui traite la cause : les deux premières décisions
protègent *ce chemin-ci*, celle-ci protège la classe entière — « une passe qui
itère sur moins que ce que le run a collecté ». `--limit` mal propagé, liste de
candidats tronquée, shard de pivot en échec produisent le même silence.

**Seuil 0, mesuré et non arrondi.** Population : les 12 commits produits par un
run `generate-data` entre `604c8d6` (16/08/2026) et `e82406a` (20/08/2026),
relevés par `git ls-tree` sur les deux répertoires.

| Commit | Bruts | Pivots | Écart |
| --- | ---: | ---: | ---: |
| `604c8d6` … `e82406a` (12 commits) | 48 → 209 | 48 → 209 | **0** partout |
| `68bc094` (l'incident) | 229 | 209 | **20** |

Le corpus a plus que quadruplé sur la période sans jamais produire un seul
écart : ce n'est pas une valeur basse, c'est une **invariance**. Un seuil non nul
n'aurait aucune mesure pour le fonder et laisserait passer, à pleine échelle, la
perte de plusieurs centaines de membres.

Un treizième commit de la période, `acfc0a4`, montre 42 écarts. Il ne fait pas
partie de la population : ce n'est pas un run CI mais un commit local
intermédiaire (`scripts/generate_data_local.sh` entre extraction et pivot), et
les 42 avaient leur pivot au commit suivant. Le contrôle tourne dans
`merge-and-pivot`, **après** les deux passes pivot, où cet état n'existe pas.

**Pourquoi un brut sans pivot est toujours une anomalie**, et pas parfois « rien
à publier » : `generate_all_profiles.process_candidat` **n'écrit aucun fichier**
quand la collecte ne rend ni identité française ni mandat européen (statut
`introuvable`, retour avant `ecrire_profil_json`) ; et un brut à `chambre: null`
porte forcément un `mandat_europeen`, seule branche qui produise ce cas
(`build_minimal_profile`), donc `normalize_europarl` lui rend un pivot. Un brut
sans pivot signifie **« jamais présenté à une passe pivot »**.

Rapporté **sans bloquer** : un pivot sans brut. À 0 aujourd'hui, mais légitime —
rien ne supprime un pivot dont le brut aurait été retiré. Compteur de dérive,
même raisonnement que les entrées d'index jamais référencées de #485.

## L'emplacement, qui est la moitié du contrôle

Après les **deux** passes `generate_all_profiles.py --pivot-only` : celle de
`raw_data/candidats.json`, puis celle de `raw_data/roster_candidats.json`. Entre
les deux, **tout membre de roster est légitimement sans pivot** — y brancher le
contrôle signalerait 543 écarts sur un run parfaitement sain. Verrouillé par
`tests/test_ci_collecte_non_publiee.py::test_le_controle_suit_les_deux_passes_de_normalisation_pivot`,
**vérifié par mutation** : le step déplacé avant la passe roster fait échouer le
test (« le contrôle précède la dernière passe pivot »), l'appel retiré aussi.

## Dimensionnement — mesuré à pleine échelle, pas projeté

Ce contrôle **ne parse aucun profil**. Il compare deux listes de noms de
fichiers, et c'est la seule façon de tenir le corpus à mémoire bornée : les
profils bruts pèsent 1 642 Mo à 229 profils (médiane 7,4 Mo, **maximum
26,5 Mo**), et parser le plus gros coûterait à lui seul plus que le plafond de
236 Mio acté par #460. Une classification par contenu — « ce brut était-il
normalisable ? » — aurait exigé cette lecture ; la propriété démontrée plus haut
la rend inutile.

Mesuré par `/usr/bin/time -v`, médiane de trois exécutions, même machine pour les
trois lignes :

| Contrôle | Durée | RSS max |
| --- | ---: | ---: |
| perte (#460/#470), 209 profils | 5,31 s | 192,6 Mio |
| intégrité (#485), 209 profils | 3,16 s | 166,8 Mio |
| **collecté/publié (#511), 229 bruts + 209 pivots** | **0,05 s** | **13,7 Mio** |
| **collecté/publié, 752 + 752 (doublure)** | **0,08 s** | **13,9 Mio** |
| collecté/publié, 752 bruts + 0 pivot (le pire cas) | 0,06 s | 13,9 Mio |

Les deux dernières lignes sont des **mesures**, pas des projections : la doublure
est un répertoire de 752 + 752 noms de fichiers, construit puis supprimé. Entre
229 et 752, la RSS bouge de 0,2 Mio — elle est celle de l'interpréteur, pas du
corpus.

Les trois contrôles sont des **processus successifs**, pas un seul : le pic du
job reste celui du plus coûteux, le contrôle de perte, et ce contrôle-ci ne le
déplace pas. Il ajoute 0,08 s à un job mesuré à 7,5 min pour un budget de 60.

*(Les valeurs de perte/intégrité relevées ici sur cette machine — 192,6 et
166,8 Mio — sont légèrement au-dessus des 186,6 et 162,0 mesurées par #485 sur la
sienne ; l'ordre et les écarts sont identiques, et c'est la comparaison qui
compte, pas la valeur absolue.)*

## Trois tolérances, toujours cloisonnées

`--tolerer-non-publies` (input `allow_unpublished_profiles`, libellé
« LAST RESORT ») est distinct de `--tolerer-pertes` (« INTENDED REMOVAL ») et de
`--tolerer-orphelins` (« EMERGENCY ONLY »). #470 a documenté le piège : rendre
bloquant un contrôle grossier force l'opérateur à relancer avec la tolérance, ce
qui désarme du même coup les contrôles précis. Testé dans les deux sens.

## Ce que ça change pour le run complet

Les 20 profils de `68bc094` seront pivotés au run suivant — la passe pivot roster
n'est bornée par aucun `--limit`, elle traite les 752 entrées du roster
régénéré, et les 20 ont leur profil brut sur le disque. Ce n'est plus une
supposition : si un seul ne l'était pas, le contrôle **annule le commit et le
nomme**.

