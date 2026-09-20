# ROADMAP — Empreinte politique

Ce que GitHub ne sait pas tenir : les défauts connus, les **gros chantiers à
prévoir**, et les **constats de cadrage** qu'il ne faut pas re-trancher. La liste
des issues ouvertes, elle, vit dans GitHub — voir « Où en est le projet » ci-dessous.

**Pas les petits correctifs.** Un correctif de quelques lignes va dans une issue
GitHub, pas ici : un fichier qui accueille les petits fix redevient une liste de
tâches, c'est-à-dire ce que GitHub fait déjà mieux — et c'est exactement ainsi que
le tableau d'issues qui vivait ici s'est périmé.

Non relu automatiquement par les agents (contrairement à `AGENTS.md`) : à
consulter sur demande. Le rationale complet d'un élément différé vit dans
`docs/decisions/hors-perimetre.md` ; ici on garde ce qu'une session
qui démarre à froid doit savoir avant de rouvrir un sujet.

## Où en est le projet

**La liste des issues ouvertes n'est plus tenue ici.** Elle l'a été, et elle
dérivait en moins d'une heure : un tableau qui recopie l'état de GitHub se périme
à chaque lot livré, et un tableau faux est pire qu'un tableau absent — on le croit.

- **L'état à jour** : les [issues](https://github.com/stephieED/Empreinte-politique-src/issues)
  et les [milestones](https://github.com/stephieED/Empreinte-politique-src/milestones)
  du dépôt, qui sont la source de vérité.
- **En session Claude Code** : `/etat-issues` rend la synthèse par milestone et par
  priorité, mesurée à l'instant.

Ce fichier garde ce que GitHub ne sait pas tenir : le **pourquoi**. Les sections
ci-dessous — défauts connus, pistes non planifiées — et les constats de cadrage
qui suivent, dont chacun a coûté assez cher pour ne pas être re-découvert.

### Constats de cadrage, à ne pas re-trancher

**Le corpus a un plancher, et il n'est pas le même selon la matière
(mesuré le 01/09/2026 sur les archives en cache et les index figés).** Aucune
décision ne l'avait posé comme un choix éditorial ; il existait en fait, sans
être consigné, ce qui le rendait rouvrable au premier prétexte.

| Matière | Législatures disponibles | Depuis |
| --- | --- | --- |
| Scrutins | 14 · 15 · 16 · 17 | 03/07/2012 |
| Amendements | 14 · 15 · 16 (figés) · 17 | idem |
| Dossiers législatifs | **15** · 16 · 17 | 2017 |
| Interventions (Syceron) | **15** · 16 · 17 | 2017 |

**Rien avant la XIVe, et la XIVe est partielle** — des votes et des amendements,
mais ni dossiers ni interventions. Une fiche de groupe construite sur la XIVe
serait un squelette, et sur la XIIIe elle n'aurait aucune matière.

**Ce que ça interdit concrètement**, mesuré sur les mandats de groupe des 13
candidats déclarés : parmi les 9 groupes qu'ils ont touchés, quatre sont hors
d'atteinte — `UMP` (2007-2015), `Les Républicains` (2015-2017),
`Rassemblement-UMP` (2012-2013) et `SRC` (2012-2014). Deux sont atteignables et
ne le sont pas encore : `FI` (Mélenchon, 2017-2022) et `LaREM` (Attal,
2017-2018), tous deux dans la XVe, qui est complète. Les trois derniers ont déjà
leur fiche.

**Ne rouvrez pas « et si on remontait plus loin » sans regarder ce tableau
d'abord** : la limite n'est pas un arbitrage de périmètre, c'est ce que la source
publie.

**Rattacher un scrutin ou une intervention à sa loi : instruit, mesuré, écarté
(#639, 01/09/2026).** La tentation revient à chaque lecture du corpus, parce que
`texte_lie_id` est `null` sur les 17 748 scrutins publiés et qu'un champ vide se
lit comme un travail facile. Il ne l'est pas : **81,8 % des scrutins n'ont aucun
rattachement sourcé**, dont **100 % de la XIVe législature**, et côté
interventions l'AN ne publie **aucune** référence de dossier — 0 occurrence sur
1 206 comptes rendus Syceron, la seule route sourcée plafonnant à 0,097 % du
corpus. **Une borne déclarée ne rattrape pas ça** : le vide serait systématique
par période, et un lecteur y lirait « il n'a pas voté sur ces lois ».

Le détail, les trois routes chiffrées et surtout les **conditions de
réouverture** — trois pour les scrutins, deux pour les interventions, toutes
conjointes — sont dans
[`rattachement-au-dossier-interventions-et-scrutins-639`](docs/decisions/rattachement-au-dossier-interventions-et-scrutins-639.md).
Ne rouvrez pas sans les avoir relues : elles sont mesurables hors ligne.

**Un constat chiffré recopié d'une issue vieillit — #484 l'a démontré deux fois.**
L'issue est close depuis le 30/08/2026 ; ce qui suit n'est plus un appel à la
re-vérifier, c'est la trace de ce que la re-mesure a coûté. Son constat d'origine —
« `identite` toujours `null` » — était faux : mesuré le 28/08/2026 sur les **481 profils
publiés**,
c'était **5**, dont trois non-parlementaires créés par #539 pour qui l'`identite` nulle
est **attendue** — aucune source parlementaire ne les décrit.

**Re-mesuré le 30/08/2026, toujours sur les 481 profils pivot publiés : c'est 4, et ce
sont exactement les quatre attendus** — `nathalie-arthaud`, `marine-tondelier`,
`david-lisnard` (non-parlementaires #539) et `jordan-bardella` (mandat européen seul).
`jean-luc-melenchon` n'en fait plus partie : le lot #484/#597 a corrigé la fusion, et le
run `33307905880` a restauré son identité **par une collecte**. Il ne reste donc aucun
cas résiduel de ce défaut.

Ce que le constat garde de vrai, et pourquoi il n'est pas supprimé : **un constat chiffré
recopié d'une issue vieillit**, et celui-ci avait déjà été démenti une fois avant de
l'être une seconde. Re-mesurer reste le geste, pas relire.

**Plusieurs issues ouvertes sont des résidus de #539, pas des régressions.** Le bloc
`couverture` publie désormais la *cause* d'une liste vide ; il a donc rendu visibles
des silences qui vivaient dans `meta` sans que personne ne les y lise. Deux d'entre
elles partagent un même idiome : le marqueur XML `{"@xsi:nil": "true"}` d'AMO30,
recopié tel quel là où une valeur était attendue.

**La sérialisation #539 avant #486 est levée.** #539 est livré, et le modèle qu'il
publie — `couvert` / `fait_etabli` / `hors_couverture` / `non_collecte` (+ `cause`),
par liste métier, avec portée facultative — est celui sur lequel #486 se branche au
lieu d'en inventer un second. Voir `docs/decisions/couverture-listes-539.md`.

**Un paramètre commandait ce qu'il ne nommait pas.** Une extraction sautait les
profils déjà écrits, et `roster_limit=0` ne suffisait **pas** à les atteindre :
sans `--limit`, la branche d'exemption au saut n'était pas empruntée, si bien que
le mode « pas de plafond » corrigeait strictement moins que le mode échantillonné.
Trois runs ont été nécessaires pour le comprendre le 28/08. #577 a corrigé les
libellés ; **#578 a corrigé le découpage** — deux axes disjoints
(`existing_profiles` × `add_uncovered_members`, ce second champ étant un menu
`roster_coverage` jusqu'à ce que #590 en fasse une case), le cache à part, et
`roster_limit` réduit à un plafond. Voir
`docs/decisions/deux-axes-formulaire-578.md`.

**Ce qui n'a jamais été exécuté n'est pas connu.** L'épic #566 a sorti sept défauts
d'une seule répétition de la procédure de bornage, dont deux introduits le matin
même, et a infirmé deux affirmations de la documentation — le push forcé **fait**
baisser la taille annoncée par GitHub, immédiatement (513 → 240 Mo constatés). La
règle vaut pour la configuration autant que pour le code : un test qui vérifie qu'un
script *contient* la bonne chaîne ne dit rien de ce qu'il *fait*.

**Ce constat-ci est périmé depuis le 30/08/2026, et c'est la découpe qui l'a
périmé.** Il disait : « une convention coûte trois conflits par jour »,
`docs/technical_decisions.md` rangeant l'entrée la plus récente en tête, tous les
lots convergeaient sur la ligne 1, et il fallait isoler cette entrée dans un commit
final pour rendre le rebase mécanique. Depuis, **une décision = un fichier neuf**
sous `docs/decisions/` : deux lots simultanés écrivent deux fichiers différents et
n'entrent plus jamais en conflit dessus. Reste une ligne à ajouter en tête de
l'index — un conflit d'une ligne, trivial. Ne re-fusionnez pas les fichiers en
croyant simplifier : c'est exactement ce qui ramènerait les trois conflits par jour.
Convention d'écriture : `AGENTS.md` §8.

## Known bugs

- **Le téléphone : ça tient dans l'écran, ça ne s'y lit pas (#867, mesuré le
  12/09/2026).** Sept pages relevées à 360, 400 et 768 px — le relevé complet,
  avec ses captures et ses causes, est le
  [commentaire du 12/09 sur #867](https://github.com/stephieED/Empreinte-politique-src/issues/867#issuecomment-5645223332)
  et l'artifact qu'il cite. **Ne pas re-mesurer avant de corriger** ; trois
  constats seulement sont à connaître avant de rouvrir le sujet :
  **1.** « aucun débordement horizontal » était faux — deux causes nommées,
  `.cp-gouv-periode { white-space: nowrap }` (fiche candidat, document à 419 px
  et 440 px selon la fiche) et le chip `.gb-chip` le plus long (364 px à 360) ;
  correctifs d'une ligne, sans maquette.
  **2.** Quatre figures deviennent illisibles et **changent de forme plutôt que
  de rétrécir** : la frise du parcours (les graduations se superposent), la
  cascade des textes portés, le tableau de `/couverture` (720 px pour 280
  visibles, sans indice de défilement) et les cartes de membres du
  gouvernement. Chacune appelle une maquette avant le code.
  **3.** Rien n'a été vu sur un vrai téléphone : les captures viennent de
  Firefox. La taille du doigt, la latence au défilement et le rendu des polices
  ne sont pas mesurés.

- **Les mandats antérieurs sont sur les fiches, mais pas encore sur la fiche
  candidat (#860, mesuré le 12/09/2026).** `raw_data/mandats_anterieurs.json`
  porte **11 lignes relues pour 5 candidats** depuis #861, et la reprise #869 a
  posé le champ dérivé sur les **32** profils de candidats déclarés — 5 relus,
  27 déclarés `non_relu` — sans attendre un run, la pose étant une fonction pure.
  L'accueil nomme donc désormais les cinq fiches concernées.
  **Ce qui reste** : côté interface, seuls `sources.config.js` et
  `scripts/couverture-corpus.mjs` lisent le champ — **la fiche candidat ne le lit
  pas**, et sa frise du parcours commence à 2002 même pour une carrière qui
  démarre en 1988. La frise est la figure qui doit accueillir ces mandats, et
  c'est celle que le point mobile ci-dessus doit de toute façon refaire.
  **À ne pas re-découvrir** : quand la table relue change entre deux runs,
  `scripts/poser_mandats_anterieurs_860.py` repose le champ sans réseau —
  inutile de déclencher une collecte complète pour ça.

- **La méthodologie porte cinq chiffres écrits à la main, mesurés sur un corpus
  de 27 fiches (#328).** `MethodologyPage.jsx` affiche « 1 160 positions de
  dernière lecture », « 711 des 1 160 », « le banc seul en couvre 719 et le
  gouvernement seul 916 » — le manifeste en publie **30** aujourd'hui, et rien
  ne recalcule ces nombres. Ils ne sont pas faux par construction, ils sont
  **invérifiables** : aucune sortie ne les porte, aucun test ne les tient. La
  page `/couverture` montre la sortie du problème — tout ce qu'elle affiche
  vient de `couverture.json`, mesuré au build, et un test refuse un nombre à
  trois chiffres dans son JSX. La même mécanique reste à appliquer à la
  méthodologie.

- **Le seuil de publication des textes portés écarte 100 % d'une institution
  (#328).** `AGENTS.md` §6 ne publie qu'un texte parvenu au moins en commission.
  Les **405 textes portés européens** ont tous `stade_procedural: null` — la
  source européenne ne publie pas de stade —, donc aucun ne franchit le seuil :
  23 sur 23 chez Glucksmann, 45 sur 45 chez Maurel, 4 sur 4 chez Mélenchon. Un
  seuil qui écarte tout ce qu'il ne sait pas mesurer ne filtre plus, il
  supprime. Arbitrage éditorial ouvert : le seuil ne porte-t-il que sur les
  textes qui ont un stade ?

- **La §4 « Où il s'est écarté des siens » ne peut pas exister à l'européen
  (#328).** Elle compare une position à celle de son groupe, et les 23 fiches de
  groupe servies sont **21 AN et 2 Sénat, aucune européenne** ; le profil de
  Glucksmann ne porte même aucun mandat `groupe_politique`. La section reste
  présente et vide avec son motif — trou déclaré, pas comblé (§2 règle 5).

- **Les 11 013 votes européens et les 7 303 amendements européens n'ont pas
  encore leur rang par institution dans « En bref » (#328).** Ils arrivent d'un
  agrégat qui ne porte pas l'institution : `joinAmendements` projette huit
  champs et laisse celui-là, et `votesDuProfil` filtre sur deux règles de forme
  AN — `isWholeTextVote` exige `type_vote === 'vote_texte'` quand le PE porte
  `nature`, et la dernière lecture se cherche dans `scrutins.json`, où un
  `scrutin_id: null` n'entre jamais. Dernier morceau du lot institutionnel.

- **Un moment de séance sans grammaire plus fine sous lui reste publié comme un
  sujet (#710).** Le critère structurel de #710 écarte les créneaux de questions
  parce que la source range dessous des points `QG_1_1`/`QOSD_1_1`/`QPM_1_1` ;
  « Motion de censure » (243 profils tagués), « Motions de censure » (192) et
  « Déclaration du Gouvernement et débat » (125) n'ont aucune marque structurelle
  équivalente — ni `@valeur`, ni `sousIntitule`, ni code de point plus profond.
  Les fermer demande une source de plus, l'ordre du jour publié par l'AN
  (`vp/reunions/`), et donc un lot à part. Trou déclaré, pas comblé par un
  libellé (§2 règle 5).

- **Les tranches d'amendements du roster ne sont plus écrites pour les
  législatures closes — fait le 09/09/2026 (#691).** Le run `34344178203` a
  retiré **854 fichiers de tranches** (77 en XIV, 270 en XV, 507 en XVI, la
  totalité) et `raw_data/profiles/` est passé de **9,7 à 4,6 Gio**. Une tranche
  close est désormais *déclarée* `derivee` dans le manifeste et relue dans
  `raw_data/amendements_an_figes/`, qui portait déjà ces 624 180 amendements en
  38 Mo — et, ce qui a rendu le chantier court, leur **inversion par acteur**.

  **Ce qui reste, et pourquoi ce n'est pas la suite du même chantier :** la
  **législature 17**, **3,64 Go**, qu'aucune archive figée ne couvre. Elle y
  entrera le jour où elle sera figée ; la reconstruire depuis l'index pivot
  serait circulaire, puisque cet index est construit à partir des tranches.

  **Ce qu'il ne faut pas re-trancher :** le gain était et reste **nul sur le
  clone**. Le brut se compresse d'un facteur ~154, et **93 % du pack est de
  l'historique** — c'est un bornage qui allègerait le clone, jamais ce
  chantier-ci. Le gain est entier sur le **checkout**, et il est concentré sur
  `merge-and-pivot`, seul job qui matérialise tout `raw_data/profiles/`.

  **Ce que la mise en œuvre a démenti :** les deux obstacles annoncés ici
  n'en étaient pas. L'ordre des amendements n'en est pas un — `audit_diff_profils`
  relève une liste par un **entier**, donc une perte est une baisse de compte et
  jamais une différence de séquence. Et le filet anti-écrasement de
  `merge_profile` est **renforcé** : `old` valait ce qu'un run précédent avait
  réussi à collecter, hostage d'un cache CI non versionné ; il vaut désormais
  l'archive committée, vérité entière d'une législature close.
  → `docs/decisions/reconstruction-tranches-depuis-archive-691.md` et les trois
  décisions qui la suivent.

- **Aucun commit de données n'est couvert par la suite de tests, et le rétablir
  demande trois gestes hors du dépôt (#685).** Mesuré le 01/09/2026 : **0 des 15**
  commits de données arrivés sur `main` depuis le premier run de `tests.yml`
  (20/08) n'en porte un. Le dépôt n'a **aucune** clé de déploiement et le secret
  `DATA_PUSH_SSH_KEY` n'existe pas, donc le push repart sous le `GITHUB_TOKEN`,
  qui n'émet pas d'événement `push`. Remède : les trois gestes de
  `docs/decisions/push-donnees-cle-de-deploiement-508.md` §7, **dans cet ordre** —
  clé de déploiement + secret, entrée `DeployKey` dans les `bypass_actors`, puis
  seulement le check requis. Depuis #685 chaque run le signale ; il ne le répare
  pas.

- **`amendements_agreges` est un dénominateur publié qu'aucun contrôle pré-commit
  ne regarde** (relevé pendant #643, 31/08/2026). `audit_diff_profils.py` ne compare
  que les champs déclarés dans ses `Collection`, et `COLLECTION_GROUPES` ne nomme
  `amendements_agreges` ni dans ses listes ni dans ses scalaires : la correction de
  #643 fait tomber `AN:LFI` de 2 600 765 à 132 960 sans qu'aucune ligne du contrôle
  s'en aperçoive — et une régression future passerait tout aussi silencieusement.
  C'est la faille que #470 avait payée sur `tags_thematiques`, sur un autre champ.
  `allow_declared_losses` n'a donc rien à déclarer pour #643, contrairement à ce que
  son issue annonçait.
- **Chaque shard `extract-an` réindexe les archives Syceron 15 et 16 pour rien**
  (dérivé de #546, mesuré sur le run `33110395663` du 27/08/2026) : **113 à 219 s par
  shard**, le même travail refait par les 7 shards porteurs, soit 40 à 60 % de
  l'horloge de collecte. La clé `public-data-cache-an-*-interv` a fait un *exact key
  hit* sur une entrée écrite alors que ces deux archives étaient injoignables ;
  `actions/cache` saute alors sa sauvegarde, et l'index reconstruit est jeté à chaque
  fin de shard. C'est #505 sous une troisième forme — la clé porte le **mode**, jamais
  la **complétude** du contenu. **Corrigé dans #550** : la clé porte désormais une
  empreinte des législatures réellement indexées (`syc15.16.17-q14.15.16.17`), et le
  cache AN passe en `restore` sur la complétude *attendue* + `save` explicite sur la
  complétude *atteinte* — une entrée partielle n'occupe plus la clé d'une entrée
  complète, et une entrée de cache GitHub étant immuable, c'était la seule façon de
  reprendre la main dans la semaine. Gain mesuré : **908 s ≈ 15 min par run** (6 des
  7 shards porteurs ne réindexent plus). Ce que ça ne règle pas : le shard qui
  **construit** l'index paie toujours 244 s de construction à froid et reste tronqué —
  au plus un par semaine, contre `jean-luc-melenchon` à chaque run jusqu'ici. Voir
  `docs/decisions/cache-completude-interventions-550.md`.
- ~~**`meta.warnings[]` n'est pas un détecteur fiable de troncature**~~ pour un candidat
  qui porte aussi un profil UE (constaté sur `jean-luc-melenchon`, run `33110395663`) —
  **corrigé le 30/08/2026 par le lot #600**. La cause était que la fusion gardait les
  interventions d'`extract-an` et le `meta` du profil minimal écrit par
  `extract-ue-officiel`, avertissement de troncature compris : `merged = dict(new)`
  prenait le bloc du **dernier écrivain** en entier. Depuis, `meta` est composé clé par
  clé et les avertissements sont **unis par famille** — le profil minimal ne remplace
  plus rien en bloc, et un avertissement démenti par les données s'éteint explicitement.
  Le `::warning::` du run reste fiable, comme avant. Voir
  `docs/decisions/union-warnings-extinction-600.md` et
  `docs/decisions/budgets-extract-an-remesures-546.md`.
- **Rien ne compare ce que la collecte rend à ce que la publication porte**, liste par
  liste (#545). Les trois garde-fous armés avant commit regardent ailleurs :
  `audit_diff_profils` surveille les pertes entre deux états publiés, pas deux étages
  du même run ; `audit_collecte_non_publiee` raisonne sur des profils, jamais sur le
  contenu de leurs listes. C'est l'angle mort dans lequel #540 a vécu. Attention au
  faux positif : sur les six listes métier, `mandats` est légitimement **enrichi** par
  le pivot (+278) et `dossiers_legislatifs` y est **renommé** `textes_portes` — un
  contrôle naïf crierait à tort sur la moitié des champs.

- **L'attribution ODbL Regards Citoyens ne s'éteindra jamais sous fusion additive.**
  `merge_pivot_profile` **unit** `sources[]` par `type` : une entrée `nosdeputes`
  déjà publiée survit à chaque collecte AN, donc les 475 profils concernés
  garderont leur clause ODbL indéfiniment. Ce n'est pas un bug d'attribution — elle
  est due — mais l'échéance annoncée par #529 §4 (« la première entrée passe à
  `assemblee_nationale` au prochain run ») est fausse. Seul un run `cold_start` /
  `--no-merge` la ferait tomber, et c'est déjà un run à perte déclarée (#528).
  Voir `docs/decisions/licence-lot-6-530.md` §3.
- ~~**La clé de fusion pivot des interventions prend l'URL d'archive Syceron pour un
  identifiant**~~ (#540, découvert sur le run `33100214165` du 27/08/2026) —
  **corrigé (PR #544) et vérifié en conditions réelles** : sur le run
  `33110395663`, **16 242 interventions publiées**, le pivot égal au brut profil
  par profil — ni perte, ni dédoublement des 891 entrées antérieures. `_pivot_intervention_key` faisait
  `source_url or (date, sujet, texte[:50])` : le `or` court-circuite, et comme
  Syceron renseigne toujours `source_url` — l'URL du zip de la **législature**,
  identique pour toutes ses interventions — le repli discriminant n'était jamais
  atteint. 3 351 entrées se réduisaient à **17 publiées** pour Gabriel Attal. Mesuré
  sur les profils bruts et pivot committés : **891 interventions publiées pour
  7 767 collectées** (×8,7 — et non 7 500, qui était le décompte de la clé composite
  *lossy* proposée par l'issue, écartée pour cette raison). `normalize_profil()`
  était hors de cause pour la clé, mais c'est bien lui qui abandonnait l'`id` : le
  correctif le propage en `interventions[].intervention_id`, ce qui aligne la clé
  pivot sur celle de la fusion **brute**, seule à avoir survécu. Les quatre autres
  clés pivot sont saines. Ce n'était pas une régression de #510, qui a seulement
  rendu le défaut atteignable. Aucune passe de migration n'est nécessaire : les
  7 767 entrées sont déjà dans `raw_data/`, un run `--pivot-only` les publie. Voir
  `docs/decisions/cle-fusion-interventions-540.md`.

- ~~**#529 laisse deux retraits à faire dans `.github/workflows/`**~~ — **soldé le
  27/08/2026** au rebasage de la PR #538 : `debug-network-shutdown-signal.yml` est
  supprimé, et `--max-pages` avait déjà été retiré de `generate-data.yml` **et** du
  code par #510. Le compromis « accepter le drapeau mais le signaler » est parti avec
  lui plutôt que d'être livré désarmé. Voir
  `docs/decisions/retrait-nosdeputes-529.md` §7.
- Les deux groupes Sénat ont leur extraction **suspendue** depuis le 24/08/2026
  (certificat TLS expiré sur `archive.nossenateurs.fr`, runs `32463926808` et
  `32548486495`, #516) : leurs fiches publiées sont gelées. **Le retrait a depuis été
  tranché, et il est éditorial** (#528) : un certificat valide ne rouvre plus rien, et la
  reprise exige les trois conditions écrites au §7 de la décision. La formulation
  précédente de cette ligne — « reprise conditionnée à un certificat valide » — présentait
  comme ouverte une question déjà fermée. Voir
  `docs/decisions/retrait-senat-528.md` §5 et §7, et
  `docs/decisions/extraction-groupe-suspendue-516.md` pour le mécanisme de suspension.
- `fetch_full_roster` faisait **un seul essai** (timeout 15 s, aucun backoff) et
  chacune des 9 invocations d'un run reconstruisait le roster pour elle-même : le run
  `32738726729` (24/08/2026) y a perdu 4 shards sur 8, la même URL répondant aux 4
  autres. **Corrigé en #518** : reprise sur ce qui est retentable
  (timeout/`ConnectionError`/5xx, jamais `SSLError` ni 4xx), et roster unique par run
  transité par artifact depuis `prepare-roster-matrix` — ce qui ferme aussi la
  divergence possible entre la liste des shards et celle de `merge-and-pivot`. Voir
  `docs/decisions/roster-unique-par-run-518.md`.
- Le run `32750929942` (24/08/2026) a perdu son commit sur le **dernier** fetch de
  roster du run, celui de `generate_group_profiles.py` : `fetch_full_roster` héritait
  du plafond de 15 s des pages par candidat, alors qu'aucune réponse de
  `/deputes/json` (814 Ko généré à la volée) n'a été mesurée sous 10 s.
  **Corrigé en #518** : plafond propre `(15, 90)`, roster **brut** transité par le
  même artifact, code de sortie 2 « roster indisponible » toléré par le step (et lui
  seul), annotations `::error::` nommant la clé et les fiches sautées. Voir
  `docs/decisions/plafond-roster-et-commit-518.md`.
- Le run `32773067295` (24/08/2026) a perdu son commit sur `.generation_checkpoint`,
  le point de sauvegarde de `generate_all_profiles.py` écrit **dans**
  `raw_data/profiles/` : le garde-fou #511 l'a compté comme un profil brut sans pivot.
  Aucun run n'avait jamais franchi ce step. **Corrigé en #518** (`--no-checkpoint` sur
  les passes `--pivot-only`, et les fichiers cachés écartés des inventaires — `Path.glob`
  les remonte). Voir `docs/decisions/point-de-sauvegarde-dans-les-profils-518.md`.
- **Reste à faire** : sortir `DEFAULT_CHECKPOINT_PATH` de `raw_data/profiles/`, pour que
  chaque nouvel inventaire n'ait plus à se souvenir de l'écarter. La destination n'est pas
  triviale — `.cache/` est restauré d'un run à l'autre par `actions/cache`, et un
  checkpoint survivant au run ferait sauter à `--resume` des candidats jamais traités.
- Le même push a laissé `Tests (pytest)` **rouge sur `main`** (run `32773016491`) : un
  test lisait `.gitignore`, absent du sparse-checkout de `tests.yml`. **Corrigé en #518**
  (liste blanche + `tests/test_ci_perimetre_sparse_checkout.py`, qui fait échouer le cas
  en local). Deuxième occurrence du même piège après #434.
- Les anomalies de `generate_roster_candidats.py` et les slugs de
  `audit_collecte_non_publiee.py` restaient enterrés dans les logs de step : la seule
  annotation d'un run mort là-dessus était `Process completed with exit code 1`.
  **Corrigé en #518** (`::error::` via `src/gha.py`).
- Le run `32876863499` (24/08/2026) a perdu 3 jobs et son commit sur un **500 immédiat**
  de `www.nosdeputes.fr/deputes/json`, alors que la normalisation pivot des candidats
  déclarés (165 s) était verte. **Corrigé en #524** : l'exception remonte jusqu'à
  l'annotation, `merge-and-pivot` saute la branche roster au lieu d'annuler le commit,
  « tous les groupes suspendus » rend 2 (toléré par les 3 appelants), et un 500 n'est
  plus retenté. Voir `docs/decisions/cloisonnement-branche-roster-524.md`.
- **Sans objet depuis #529** : la panne visée était celle de
  `www.nosdeputes.fr/deputes/json`, qui n'est plus interrogé — le roster AN vient
  d'AMO30. Une suspension d'entrée AN reste possible, mais sur une autre cause.
- Les **20 profils orphelins** de `68bc094` (229 bruts / 209 pivots, incident #511 du
  20/08/2026) sont toujours dans `main`. Ils ne bloquent rien — les deux passes
  `--pivot-only` les publient, vérifié en #518 — mais ils ne disparaîtront qu'au
  premier run `generate-data` qui ira jusqu'au commit.
- `extract-an` traite ses candidats dans l'ordre du fichier et n'a pas de rotation :
  quand un budget de collecte de job est épuisé par une source dégradée, ce sont
  toujours les mêmes premiers slugs qui l'ont consommé. Constaté sur `extract-senat`,
  retiré depuis (#528) ; le défaut de conception, lui, n'est pas propre à ce job. Voir
  `docs/decisions/budget-collecte-source-injoignable-514.md`.
- `extract-roster-groupes` déclare `--budget-collecte-secondes 0` (absence de budget
  assumée, #514) faute d'une mesure sur ses 752 membres. À dimensionner si un shard
  roster meurt sur une source dégradée.
- 21 of the 207 profiles published as `chambre: "AN"` are known to the Senate's own
  roster, 18 with a still-open Senate mandate (measured 2026-08-20, #488). All but
  Retailleau are `roster_groupe`, so they are deliberately **out of scope**: no Senate
  group is aggregated, and their Senate past feeds nothing. #492 (sub-issue C) put the
  chamber on each **mandate**; #493 (D) made the profile level a derived `chambres` list.
  Neither corrects these 18 — they have **no `mandat_electif` at all**, so nothing can
  back a chamber for them, and #488 restricts bicameral collection to the 8
  `candidat_declare`. They now carry a `chambres du profil non corroborée` warning that
  says so. Correcting them is a **collection** matter, not a schema one. See
  `docs/decisions/deux-chambres-interrogees.md` and `docs/decisions/chambres-profil-derivees.md`.
- `mandats[].chambre` is `null` on **29 of the 511 published `mandat_electif`** (28 of the
  481 profiles, measured 2026-08-30 — down from 214 of 228 on `f5a828b`), and **those 29
  will never fill in**: 14 duplicate a mandate the same profile already publishes stamped
  (the source moved the merge key `label`/`debut`), 15 belong to a closed legislature the
  source no longer serves, so `merge_profile.backfill_mandat_chambre` has nothing to match.
  Each affected profile carries one `chambre de mandat électif non résolue` warning. A
  `--no-merge` run would clear them at the cost of deleting the 15 real mandates. See
  `docs/decisions/corroboration-chambres-publiees-486.md`.
- The UI still shows one parliamentary experience per candidate. The data model no longer
  stands in the way — #492 carries the chamber on each mandate, #493 publishes the
  profile-level `chambres` list — but the values only become real after a full
  regeneration re-collects the 228 published `mandat_electif`, all still at
  `chambre: null`. #486 sub-issue F (#495) and #324.
- In CI a candidate's `chambre` used to be decided by **artifact merge order** too:
  `extract-an` (`--source an`) and `extract-senat` (`--source senat`) were two scoped
  passes whose raw profiles met in `merge_raw_profile`, where
  `chambre = _prefer_non_empty(new, old)` let the last one landing win. #488 fixed the
  default `--source all` path, #493 narrowed this one, and **#528 closed it by
  removing the second pass**: there is now a single FR collection job. What remains
  open is upstream of CI — `chambre` is still the *fallback* of `deriver_chambres()`
  on profiles whose mandates carry no chamber, and the profile declares it.
- Profiles collected before 2026-08-18 carry amendements resolved through the
  old `numero`-keyed store: ~75% of a legislature's amendements are missing and
  ~40% of the remaining (member, amendement) links point at the wrong text/date/
  sort. The key is fixed and the frozen indexes rebuilt, but **the profiles
  themselves need a full regeneration** to be correct — no in-place migration is
  possible (the lost amendements were never written). See
  `docs/decisions/amendements-cle-uid.md`.
- `generate-data.yml`: `if: always()` upload/cache steps still don't survive
  a runner infrastructure `shutdown signal` (#228) for jobs that aren't
  matrix-sharded. `extract-an` is now sharded per-candidate (#344, see
  `docs/decisions/matrix-extract-an-par-candidat.md`) — the same
  mitigation for `extract-roster-groupes` (~750 members) remains deferred to
  the full-scale roster rollout, see `docs/decisions/seuil-couverture-groupe.md`.
- `generate-data.yml`: the weekly AN cache key may no longer be written back by
  `extract-an` / `extract-roster-groupes`. `extract-amendements-an` writes the
  exact key first, and `actions/cache` skips its post-job save after an exact
  key hit — so the ~290 MB of AN dumps each shard downloads would never be
  persisted. **Confirmed by run 32136438841 and fixed in #424**: amendements
  moved to their own `public-data-cache-amendements-*` key, AN jobs now list
  their cached directories explicitly (`docs/decisions/cache-cle-amendements-separee.md`).
- `generate-data.yml`: the same #424 defect had reappeared on the two cache
  directories only `collect_interventions=true` ever fills. **Fixed in #505**,
  with a different mechanism than the one first diagnosed: `extract-roster-groupes`
  never wrote the weekly key (it runs behind `extract-an` by `needs:`), the
  dissociation was between the two **modes** of `extract-an` — one key for the
  ISO week, two possible contents. The key now carries the mode, the `path:`
  keeps only the per-legislature indexes (never the 650,5 MB of archives, measured),
  and the roster job is `actions/cache/restore` on both its cache steps.
  See `docs/decisions/cache-mode-interventions-505.md`.
- `generate-data.yml`: a `Read timed out` on NosDéputés made
  `generate_roster_candidats.py` overwrite the roster with **0 candidate** and exit 0,
  so the roster pivot pass iterated on nothing — run `32405297873` concluded
  `success` with 229 raw profiles for 209 pivots, the 20 members it had just
  collected published nowhere. **Fixed in #511**: the roster is never written on a
  failed fetch, a 0-member configured group, or an empty result (a shrink threshold
  was measured and rejected — a partial failure drops 452 or 300 of 752 at once, and
  is observable at its cause); and `src/audit_collecte_non_publiee.py` now reconciles
  collected against published before every commit. See
  `docs/decisions/collecte-non-publiee.md`.
- `minoritaire` position unhandled in JS: `classifyDateInHemicycle` /
  `classifyTexteInHemicycle` (in `web/UI_finale/src/data/pivotAdapter.js` and
  archived `web/old/v3/js/render.js`) only handle `"majorite"` and `"opposition"`.
  The value `"minoritaire"` (valid per `schema_pivot.py` `KNOWN_POSITIONS_HEMICYCLE`)
  falls through to `"indetermine"` / `non_distingue`, mis-bucketing texts/amendments
  from minority-group periods when the legislative reading-mode filter is active.
- `pivot_data/gouvernements/gouvernement-BAYROU.json` publishes 12 `membres[]`
  where the current code rebuilds 9 — 2 strict duplicates removed by #480, plus
  an `astrid-panosyan-bouvet` entry (`debut: 2026-02-04`, `actif: true`) the
  code no longer reproduces. The pre-commit loss check blocks on it, and will at
  the next `merge-and-pivot` run, independently of #487 that measured it (see
  `docs/decisions/id-pivot-sans-prefixe.md`).

## Ideas not yet scheduled

- **Une recherche par mot-clé à l'intérieur d'une fiche** — idée de la propriétaire,
  13/09/2026, **pas priorisée**. Un champ qui filtre le contenu de la fiche affichée
  sur un mot : retrouver « retraites » dans les votes, les amendements, les textes
  portés et les interventions d'une personne, sans faire défiler quinze écrans.
  **Ce qu'il faudra trancher avant de commencer**, et qui n'est pas tranché : le mot
  cherché traverse des listes que la fiche ne charge pas toutes (les index de
  scrutins et d'amendements sont partagés et chargés à la demande) ; et une
  recherche qui ne trouve rien doit dire **si la liste est vide ou si elle n'est
  pas couverte** (§2 règle 5) — sinon elle se lit comme « cette personne ne s'en
  est jamais occupée ». Ne pas confondre avec un moteur de recherche **entre**
  fiches, qui est un autre sujet et poserait un classement (§2 règle 1).
- **Notifications de suivi (candidats/groupes)** — idée identifiée, **pas priorisée**.
  Piste retenue : un **flux RSS/Atom par candidat ou par groupe**, généré en sortie du
  pivot à partir du **diff entre deux régénérations** — zéro compte, zéro donnée
  personnelle, zéro modération de contenu tiers. Diffusion croisée envisagée sur LinkedIn
  (manuel d'abord) et X (API payante depuis 2026) ; **pas de subreddit propre**, pour une
  raison de responsabilité. Les trois refus et leurs raisons sont instruits et ne se
  re-tranchent pas : `docs/decisions/notifications-de-suivi.md`.
- Câbler `src/an_roster.py --divergence` dans `generate-data.yml` (prévu par #526 §6) :
  demande d'ajouter `.cache/acteurs_historique_an` au cache de `prepare-roster-matrix`,
  qui n'en a aucun et retélécharge donc 13,6 Mo par run depuis la bascule (#527).
- **#708 a tranché comment naît un slug** (clause 3 de #526 §9) : un acteur AMO30 sans
  entrée de correspondance reçoit `text_utils.slugify` de son état civil, la table
  gardant la priorité, et une collision reste un refus nommé. Les 156 de la 17e et les
  4 de la 16e (`PA794914` LR, `PA722070`/`PA719032`/`PA721522` REN) entrent donc. **Ce
  qui reste ouvert** : leur donner une entrée **relue** dans
  `raw_data/correspondance_acteurs_an.json` — la §5b du portail bloque leur publication
  sans elle, et `build_correspondance_acteurs_an.py` refuse toujours d'inventer (#525).
  C'est la clause 2 de #526 §9, et le seul geste qui manque pour que les fiches de la
  17e passent de 305/461 à leur couverture réelle. Coût mesuré d'un run : ~1,07 à
  1,44 Gio de profils bruts. Voir `docs/decisions/slug-fabrique-membre-de-roster-708.md`.
- **#715 a débloqué la publication, pas la relecture.** Le premier run à profiter de #708
  (`33613535746`, 02/09) a collecté 160 profils neufs et n'a **rien** committé : §5b, 160
  slugs sans entrée. La passe `--completer-derivees` écrit désormais leur entrée dans le
  run même qui les crée, estampillée `origine: "derivee"` — elle **gèle** l'identifiant,
  elle ne le prouve pas. **Ce qui reste ouvert** : ces 160 entrées n'ont été relues par
  personne, et la §5b publie leur compte à chaque run précisément pour que la file se
  voie. Les relire, c'est renseigner `prenom`/`nom` depuis AMO30 et basculer `origine` à
  `relue` — la clause 2 de #526 §9, inchangée. Voir
  `docs/decisions/entree-derivee-correspondance-715.md`.
- Le repli `fetch_full_roster_nosdeputes` est **retiré** (#529) ; `AN_ROSTER_ACTIF`
  reste, non plus comme aiguillage mais comme refus bruyant — un roster vide écrit
  sur disque est indiscernable d'un groupe dissous (#511/#524). La clause 3 de #526 §9
  — comment naît un slug quand la source n'en publie pas — est **close par #708** ; il
  reste la clause 2, la relecture des correspondances (ci-dessus). Voir
  `docs/decisions/retrait-nosdeputes-529.md` §5.
- `raw_data/correspondance_acteurs_an.json` n'est pas dans le sparse-checkout de
  `tests.yml` : sa couverture réelle est contrôlée par le quality gate à l'exécution,
  pas par la suite (les tests tournent sur fixture). L'y ajouter permettrait un test
  structurel sur la table committée elle-même (#525).

- Syceron debates are **live** since 27/08/2026 and the NosDéputés fallback is gone
  (#510); the index is sharded per actor. The three measurements this entry was
  waiting for have been taken on run `33100214165` (27/08, 22 jobs green, 52 min):
  **+6 963 interventions collected** on the five declared candidates that have a
  Syceron record, and no OOM. Two findings came out of it:
  - only **87** of those reached the published corpus — see #540, the pivot merge
    key (fixed, PR in review). Profile weight and group aggregates against #429's
    thresholds therefore **remain unmeasured**: they can only be judged once the fix
    ships and the **7 767** collected interventions are actually published — 891 are
    today;
  - `collect_interventions` drives **`extract-an` only**. The roster job carries
    `--skip-interventions` in hard (light extraction mode, #357), so the 468 roster
    profiles collect none. That was the right call when the roster only fed group
    aggregates; it is worth re-deciding now that those profiles are the published
    product. See `docs/decisions/syceron-actif-510.md`.

- Senate speeches were collectable but never attributed: `fetch_intervention_details`
  resolves a speaker through the document's `url_nosdeputes` key, which
  `archive.nossenateurs.fr` never emitted — it published `url_nossenateurs`. Every
  Senate intervention was therefore classified `mention` and dropped, which is why
  `extract-senat` hard-coded `--skip-interventions` (#501). **#528 retired the job and
  the chamber**: this is now a reopening cost, not a defect to fix — see the three
  conditions in `docs/decisions/retrait-senat-528.md` §7.
  The tripwire `tests/test_interventions_senat_non_retenues.py` was **deleted** on
  27/08/2026 with the chain it measured — `fetch_intervention_details` no longer
  exists (#510). Reopening is now harder, not easier: there is no Senate intervention
  path left to fix a key in. See `docs/decisions/interventions-senat-501.md`.

- `actions/checkout` is now the dominant per-shard cost in `generate-data.yml`:
  93–117 s measured per roster shard on run 32288588518, i.e. ~55 % of a shard,
  against ~65 s of actual extraction — and it is paid once per shard, so
  sharding multiplies it. A shallow/partial checkout (`fetch-depth`, sparse
  paths) would attack it, but the extraction jobs read the committed profile
  baseline, so what can be pruned has to be established first. Measure before
  deciding, see `docs/decisions/budget-execution-pleine-echelle-467.md`.

- `tests/test_amendements_download_modes.py` now dominates the suite: eleven
  teardowns wait 0.5 s each for a local HTTP server to stop — ~5.5 s of the
  11 s total (#473). The waits are part of the scenario under test (the three
  Range-download degradation states); shortening them means touching the module,
  not the test. Only worth doing if the CI job becomes a contention point.

- CI still deletes the partial amendements archive on download failure (#264
  `try/finally`), so it gains nothing from the byte-level resume of #241/#443
  between runs. The premise behind that deletion ("the archive is never reread
  to resume a download") stopped being true with cross-invocation resume.
  Reversing it trades weekly cache volume for resume — measure before deciding,
  see `docs/decisions/telechargement-an-trois-modes-defaillance.md`.

- Congrès scrutins (AN + Sénat at Versailles) are excluded from `votes[]`
  (`AN_SCRUTIN_UID_PREFIXE`): their numbering restarts at 1 inside the AN
  number space, so the only one published to date — the 2024-03-04 IVG
  constitutional vote — would cite the wrong source page and collide with AN
  scrutin n° 1 in group cohesion. Publishing it needs its own identifier and
  source URL, see `docs/decisions/votes-multi-legislature.md`.

- Refine thematic classifier: handle cross-theme items (e.g. tagged both
  `budget` and `sante`), add an explicit "non classifié" bucket instead of
  silently dropping low-confidence items.
- Evaluate surfacing `pivot_data/partis/` aggregates in a comparison panel
  (non-navigation context) rather than as a top-level tab.
- Senate adapter (votes/amendments/sponsored texts) — deferred, see
  `docs/decisions/hors-perimetre.md`. Also applies to the gouvernement
  view's `textes[]` (AN dossiers dump only, Senate-initiated bills not
  captured), confirmed in `docs/decisions/gouvernement-doc-cloture.md`.
- EU textes_portés/amendements via the official API — superseded by the
  Parltrack approach, see `docs/decisions/hors-perimetre.md` and
  `docs/decisions/investigation-sources-ue.md`.
- Precise ministerial portfolio title — **le constat d'origine (« no source
  identified ») est périmé** : la source existe et est câblée (AMO30
  `typeOrgane == "MINISTERE"`, #382/#383 puis #398/#474), `portefeuille` est renseigné
  sur les 127 entrées `membres[]` publiées. Ligne conservée tant que #644 n'a pas établi
  si le JORF est exploitable, voir `docs/decisions/hors-perimetre.md`.
- Composition des gouvernements : `gouvernement_roster.py` ne connaît que les ministres
  ayant déjà un profil pivot local (AMO30), soit **107 personnes distinctes sur les
  10 fiches publiées** et 3 `premier_ministre` sur 10 — et surtout aucun dénominateur,
  donc aucun moyen de dire ce qui manque (§2.5, §2.7). Piste : les décrets de nomination
  du JORF (bulk DILA / API Légifrance, Licence Ouverte), soit en source primaire de
  `membres[]`, soit seulement en indicateur de couverture. Cadrage, sources candidates
  et contraintes dans #644 — aucune n'a encore été ouverte.
- Extra-parliamentary bodies matching — homonym risk, see
  `docs/decisions/hors-perimetre.md`.
- Syceron (comptes rendus de séance) AN open data — fetch/caching, parse XML -> `interventions[]` et index `acteurRef -> interventions` implémentés ; intégration éditoriale aval encore à planifier. Voir `docs/sources/an-opendata.md`.
- Agenda/committee meetings dataset — low priority, see
  `docs/decisions/hors-perimetre.md`.
- Mayors — no dedicated collection module yet.
- Consolidate `test_quality_gate_syceron.py` and `test_quality_gate_groupes.py`
  (added by #193 for `_report_groupes`) into a single `test_check_quality_gate.py`
  covering all sections of `check_quality_gate.py`.
- `gouvernement_textes.py`: `AMO30` fallback for government-origin detection
  on dossiers without a "Projet de loi"/"Proposition de loi" title prefix
  (2355/3044 dossiers, mostly motions/résolutions/rapports) — needs mandate-date
  vs. deposit-date filtering to avoid the ~15% false-positive rate measured
  in #207 (ex-minister co-signatories). See `docs/decisions/gouvernement-textes-statut-210-version-initiale.md#gouvernement-textes-statut`.
- Surface `textes[].initiateurs` (minister → bill link, #435) in the
  gouvernement view: the data layer carries it, `web/` does not display it yet.
  Also unmeasured by `audit_gouvernement_dataset.py`/`check_quality_gate.py`
  (no coverage indicator for resolved vs. raw-`acteurRef` links, 556/1213
  today). See `docs/decisions/gouvernement-textes-initiateurs.md`.
- #431 (normalising `amendements[]` in profiles) is unblocked now that the store
  is keyed by `uid`, but its baseline must be re-measured: its 4 246 026 pairs /
  67 058 distinct amendements were counted on collapsed data. The shared
  deduplicated list is to be a single global file (arbitrated 2026-08-18); it
  will exceed GitHub's 100 MB blob limit, so it needs the same treatment already
  applied twice in this repo — per-actor sharding (#392) or gzip as for the
  frozen legislatures. See `docs/decisions/amendements-cle-uid.md`.
- Audit temporal-range cross-tables (`compute_plage_dates_*`, #316): no
  alerting on threshold yet (e.g. "profile doesn't cover the current
  legislature") — raw min/max indicator only. See
  `docs/decisions/audit-plages-temporelles.md`.
- `schema_groupe.py`: `amendements_agreges` has no date field, so its audit
  temporal-range cell is always `null` — schema change, out of scope for
  #316. See `docs/decisions/audit-plages-temporelles.md`.
- Same unconditional `meta.genere_le` re-stamping pattern as #343 (fixed for
  candidate pivots via `preserve_stable_freshness_timestamps`) likely applies
  to `group_profile.py`/`gouvernement_profile.py`/`parti_profile.py`, which
  rebuild their output unconditionally on every run with no old-vs-new
  content comparison — not confirmed with a real repro, out of scope for #343.
- Rattacher `_build_organe_index` (#353) aux mandats/responsabilités du profil
  député (commissions avec rôle, groupes d'amitié, engagements
  extra-parlementaires, groupe déclaré) : ces champs restent sourcés
  uniquement depuis NosDéputés après #355 (identité bio seule basculée vers
  l'AN). Voir `docs/decisions/bascule-identite-an-primaire.md`.
