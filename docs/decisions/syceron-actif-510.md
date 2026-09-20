<a id="syceron-actif-510"></a>
# Syceron activé, repli NosDéputés retiré, index tranché par acteur (#510) (2026-08-27)

`2026-08-27`

> **En bref** — un repli qui remplace la source primaire masque sa panne.

Décision d'opérateur, prise sur les mesures du 26/08 rappelées ci-dessus, et
demandée en ces termes : « active le drapeau et retire le repli vers
nosdéputés ». Les deux moitiés vont ensemble et n'auraient pas de sens séparées
— un repli qui *remplace* la source primaire est précisément ce qui a rendu #510
invisible pendant toute sa durée de vie.

## Ce qui change

**1. Le drapeau n'existe plus, la résolution est le comportement.**
`SYCERON_RESOLUTION_ACTEUR_NU_ACTIVE` et `activer_resolution_acteur_nu_syceron`
sont retirés ; `_parse_syceron_intervention_entry` appelle toujours
`_normaliser_orateur_id_syceron`. Le mode d'avant n'est pas *conservé pour
mémoire* : il ne rendait pas « moins » d'interventions, il en rendait **zéro**
sur les trois archives, et le garder sous un drapeau, c'était garder armé l'état
exact du défaut. `--activer-interventions-syceron` reste **déclaré** dans les
deux CLI, avec une action qui **refuse bruyamment** en nommant la décision
(`RefusDrapeauInterventionsSyceron`) : un `unrecognized arguments` laisserait
croire à une option inconnue — ou pire, à une collecte Syceron désactivée. Même
forme de refus que `--source senat` (#528).

**2. Le repli NosDéputés est retiré du chemin interventions**, et avec lui toute
la chaîne qui n'existait que pour lui : `fetch_recherche`,
`fetch_all_intervention_results{,_from_domains}`, `_process_search_result`,
`_extract_search_results`, `fetch_intervention_details`, `fetch_seance_context`,
`_classify_intervention`, `_extract_speaker_identity_from_html`,
`_classify_intervention_format`, `REACTION_COURTE_NB_MOTS_MAX`, `_to_int`, et
les options `--max-pages` des deux CLI. Ce n'était pas un préliminaire
négligeable : la recherche seule coûtait **90 s** sur `jean-luc-melenchon` (run
32379928098), imputées au budget de 240 s de #500. C'est autant de rendu à la
source primaire.

Conséquences en chaîne, toutes assumées ici :

- `interventions` **n'a plus qu'une source de débat** (plus les questions
  officielles, qui n'ont jamais doublé Syceron mais l'ont complété) ;
- une collecte Syceron vide **reste vide**, et le déclare :
  `interventions syceron indisponibles` (§2.5). Le préfixe est volontairement un
  **préfixe** de l'ancien libellé (`… (fallback nosdeputes)`), pour que les
  warnings déjà écrits dans le corpus restent reconnaissables ;
- `interventions` sort de la liste `sections_vides` de #514 : la recherche
  NosDéputés était le **seul** point du chemin à passer par `_get_payload`, donc
  ce compteur ne pouvait plus qu'attribuer à NosDéputés une panne qui n'est pas
  la sienne. Même raisonnement que #528 pour `votes` et `dossiers législatifs` ;
- `normalize_nosdeputes` n'est **pas** touché : la fusion additive conserve les
  interventions NosDéputés déjà collectées, et elles doivent continuer à se
  normaliser. Retirer leur *lecture* ferait disparaître du corpus publié des
  faits déjà acquis — ce que le contrôle de perte de #460/#470 bloque.

**3. L'index Syceron est tranché par acteur.** C'était « le dernier verrou
technique » ; il n'était pas dans #510 tant que le drapeau restait baissé, il
l'est devenu à la seconde où l'activation a été décidée. `.cache/syceron_an/<
législature>/index_par_acteur/PA######.json`, publié d'un seul `os.replace`
depuis un répertoire `.partiel` — patron de #392 (amendements) et #403
(scrutins), et règle d'AGENTS.md : *un cache disque évite un re-téléchargement,
jamais un re-parsing*. Sans lui, l'activation relisait **1 664,8 Mio** d'index à
**chaque candidat et pour chaque législature** : 12,5 s et 3,8 Gio de pic de RSS
mesurés le 26/08. Trois propriétés viennent avec :

- `_read_cached_interventions_syceron_acteur` rend `None` (index indisponible)
  ou `[]` (acteur absent de la législature) — jamais la même chose, règle 5 ;
- le répertoire est **basculé**, jamais rempli en place : un répertoire qui
  existe et qui est incomplet se lit « cet acteur n'a pas parlé », le défaut
  exact de #447 ;
- les deux index plats hérités (`index_par_acteur.json`, 2 octets, et
  `index_par_acteur_acteurs_nus.json`) sont **supprimés** à la publication et
  ne sont plus jamais relus. Servir un index de 2 octets à un run qui sait
  résoudre les identifiants nus, c'est le défaut de cache de #505.

Le verrou de législature devient **réentrant** (la lecture de tranche le prend,
et retombe sur la construction qui le reprend), et un mémo process retient les
index construits mais **non publiés** — clé par **chemin** de cache, jamais par
nom logique : c'est le piège qui a fait revert #377, nommé dans AGENTS.md.

## Ce qui est mesuré, et ce qui ne l'est pas

**Mesuré** : la suite complète, **2 222 tests, 0 échec** — dont la tranche par
acteur, la non-publication d'un index vide sur archive lisible, la suppression
des index plats hérités, le refus du drapeau, et le fait qu'un second candidat
ne reparcoure plus un seul compte rendu.

**Non mesuré, et ce n'est pas un détail** : cet environnement ne peut ni
télécharger les archives (2 768 comptes rendus, 262 Mo) ni régénérer le corpus.
Donc, à vérifier au premier run réel :

- le **coût par candidat** et le **pic de RSS** de la nouvelle forme. Ils sont
  bornés par *construction* — une tranche d'acteur lue au lieu de l'index —, pas
  par une mesure. Le pic de la **construction** (une fois par législature et par
  process, sous verrou) n'a pas changé ;
- le **poids des profils publiés** et l'effet sur les **agrégats de groupe** :
  1 227 415 interventions indexables contre 789 publiées aujourd'hui. À
  confronter aux seuils de #429 — et le contrôle de perte de #460/#470 verra une
  **hausse** massive, pas une perte, donc il ne bloquera pas ;
- l'**entrée de cache de #505** : `.cache/syceron_an/*/index_par_acteur` passe de
  ~21 Mo à l'ordre du Go (1 664,8 Mio sur disque avant compression) face au quota
  de 10 Go du dépôt. Si elle le sature, c'est la mise en cache de l'index qu'il
  faudra trancher — pas le contenu de l'index. Le `path:` a été changé **à
  l'identique dans les deux jobs** qui le déclarent : la version d'une entrée est
  un hachage du `path`, deux écritures divergentes sous la même clé ne se
  verraient pas ;
- le **budget de #500** : les 240 s perdent les ~90 s de recherche NosDéputés et
  gagnent le coût de lecture des tranches. Le solde n'est pas mesuré.

**Vérifié au premier run réel** (`33100214165`, 27/08/2026 — 22 jobs verts,
52 min). Trois des quatre points sont tranchés :

- **coût par candidat et budget de #500** : les shards `extract-an` tiennent
  entre **2,3 et 6,7 min** sur un budget de 9 min, sans OOM ni troncature. Le
  solde de la bascule est positif. **Corrigé par le second run** — cette
  conclusion ne vaut que pour un corpus où Syceron n'était pas encore publié :
  une fois la collecte complète, un shard monte à **8,9 min** et un profil sort
  **tronqué**. Voir [#budgets-extract-an-perimes-546](budgets-extract-an-perimes-546.md) ;
- **entrée de cache de #505** : `.cache/syceron_an/*/index_par_acteur` pèse
  **109 Mo**, pas « l'ordre du Go » redouté ci-dessus, face au quota de 10 Go
  du dépôt. La mise en cache de l'index n'a pas à être tranchée ;
- **poids des profils publiés et agrégats de groupe** : toujours **non
  mesurable**, et pour une raison qui n'était pas soupçonnée ici — voir
  ci-dessous.

**Ce que la prédiction n'a pas tiré.** Le troisième point ci-dessus annonçait,
correctement, que « le contrôle de perte de #460/#470 verra une **hausse**
massive, pas une perte, donc il ne bloquera pas ». La conséquence n'a pas été
tirée : si le garde-fou ne bloque pas, alors **rien** n'attrape un effondrement
de clé côté publication. C'est l'angle mort exact dans lequel #540 a vécu — la
fusion pivot traitait l'URL d'archive Syceron comme un identifiant
d'intervention, et n'en publiait donc qu'une poignée par profil : **891 entrées
publiées sur 7 767 collectées**. La hausse attendue a bien eu lieu (789 entrées
publiées avant l'activation, 891 après), et c'est elle qui a masqué un
effondrement d'un facteur 8,7 : un contrôle qui ne sait lire que le signe d'une
variation ne peut pas voir ça. Voir
[#cle-fusion-interventions-540](cle-fusion-interventions-540.md).

## Ce que le retrait coûte ailleurs

`tests/test_interventions_senat_non_retenues.py` est **supprimé** : il gardait
l'asymétrie `url_nosdeputes` / `url_nossenateurs` de #501, mesurée sur
`fetch_intervention_details`, qui n'existe plus. La condition de réouverture du
Sénat (#528 §7) n'est pas affaiblie pour autant — elle est **durcie** : il ne
s'agit plus de faire lire une clé à un lecteur existant, mais de construire un
chemin d'interventions sénatoriales qui n'existe plus du tout. C'est une
décision à prendre, plus un correctif à appliquer.

## Ce qui n'est pas fait

Rien n'a été tenté sur les 92 identifiants du corpus que la 17e ne retrouvait
pas (relevé d'origine de #510) : les trois archives sont désormais indexées, ce
qui déplace la question sans la trancher. Et la volumétrie publiée n'est pas
bornée ici — aucun échantillonnage, aucune troncature de texte : ce serait une
décision éditoriale distincte, pas une conséquence de l'activation.

## Garde-fous

`tests/test_syceron_acteur_ref.py` (34 tests), `tests/test_parse_syceron.py`,
`tests/test_index_interventions_cache_partiel.py` (forme du cache, index plats
hérités supprimés, tranche d'acteur absent ≠ index indisponible),
`tests/test_candidate_profile.py` (une collecte Syceron vide ne convoque
personne), `tests/test_budget_interventions.py`.

