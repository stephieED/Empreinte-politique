# Les commandes du dépôt

**À quoi sert ce fichier.** Retrouver *la* commande sans rouvrir le code, six
mois plus tard. Chaque entrée dit **ce qu'elle fait**, **la commande**, et **ce
qu'elle produit** — rien d'autre. Le *pourquoi* vit ailleurs, et chaque entrée
dit où.

Toutes les commandes se lancent **depuis la racine du dépôt**, environnement
virtuel activé (voir `README.md`, section Installation).

**Python 3.12, et pas un autre.** C'est la version de la CI, et `src/` en emploie
la syntaxe : sous 3.11, `src/an_roster.py` ne se lit pas. Le piège est d'être
**silencieux** : `scripts/generer_decisions_par_module.py` ignorait le module et
écrivait une table différente de celle de la CI, que la suite refusait ensuite
sans dire pourquoi (11/09/2026). Il refuse désormais de tourner sous une version plus ancienne — mais
le `python3` d'une session cloud peut être un 3.11 : vérifier `python3 --version`,
ou appeler le Python du venv.

Les 45 exécutables du dépôt ne sont pas tous ici : **une commande est
documentée si la propriétaire peut avoir à la lancer elle-même**. Ce qui est
écarté et pourquoi : dernière section.

`tests/test_commandes_documentees.py` relit ce fichier à chaque run de la
suite : il vérifie que chaque script cité existe et que **chaque option longue
citée est déclarée dans son `argparse`**. Une option supprimée du code fait
rougir la suite ici, au lieu de survivre dans la doc.

---

## Générer des données

### Collecter les appartenances sénatoriales (#885)

```bash
python3 src/collecte_senat.py --export .cache/senat/export_sens.sql          # simulation
python3 src/collecte_senat.py --export .cache/senat/export_sens.sql --apply  # écrit le brut
```

Écrit le bloc `mandat_senatorial` dans `raw_data/profiles/<slug>.json`, **pour
les candidats déclarés seulement** — les membres de roster sont écartés et
comptés. L'export se télécharge depuis
`https://data.senat.fr/data/senateurs/export_sens.zip` puis se décompresse ; il
a déjà été servi **vide** (444 octets, 0 table, 13/09/2026 à 03 h 33), et la
commande s'arrête alors sans rien écrire.


### Un profil brut, un seul candidat

```bash
python3 src/candidate_profile.py jean-luc-melenchon
```

Produit : `raw_data/profiles/<slug>.json` (le **socle**) plus une tranche
`raw_data/profiles/<slug>/<legislature>.json` par législature pour les
amendements (#580). `--out` nomme le socle ; les tranches sont son répertoire
frère. `--chambre deputes` est la seule valeur : le Sénat est hors périmètre
(#528).

### Le profil pivot d'un seul candidat

```bash
python3 src/generate_all_profiles.py --only jean-luc-melenchon --pivot
```

Produit : le brut **et** `pivot_data/profiles/<slug>.pivot.json`.

### Tous les candidats déclarés

```bash
python3 src/generate_all_profiles.py --pivot
```

Lit `raw_data/candidats.json`. Produit les bruts, les pivots, et reconstruit au
passage les deux index partagés. Options de conduite les plus utiles :

| Option | Effet |
|---|---|
| `--skip-existing` | ne régénère pas un profil déjà écrit |
| `--refresh-existing` | l'inverse : ne régénère **que** l'existant |
| `--limit 20` / `--sample 20` | déploiement progressif / échantillon aléatoire |
| `--workers 4` | parallélisme entre candidats (défaut 4 ; baisser si l'API renvoie 429) |
| `--resume` | reprend après interruption |
| `--budget-collecte-secondes 160` | plafond de collecte **par candidat** ; `0` déclare l'absence de plafond |
| `--budget-job-secondes 600` | plafond de collecte pour **tout le run** |
| `--no-merge` | remplace au lieu de fusionner (la fusion est additive par défaut) |
| `--skip-interventions` | ne collecte ni débats Syceron ni questions officielles |
| `--interventions-theme-seul` | collecte les débats **sans leur verbatim** et laisse les questions officielles ; chaque entrée publiée porte `collecte: "theme_seul"`. Sans effet sur un slug de `raw_data/candidats.json`. Incompatible avec `--skip-interventions` |

Renormaliser sans aucun appel réseau, depuis les bruts déjà collectés :

```bash
python3 src/generate_all_profiles.py --pivot-only --no-checkpoint
```

→ `docs/workflow-generate-data.md` pour ce que le run fait job par job,
`docs/data-architecture.md` pour ce que la donnée devient.

### La couverture complète des groupes (extraction pilotée par roster)

```bash
python3 src/generate_roster_candidats.py
python3 src/generate_all_profiles.py --candidats raw_data/roster_candidats.json --pivot --skip-existing
```

Produit : `raw_data/roster_candidats.json` (la composition réelle des groupes
de `raw_data/groupes_reels.json`, au lieu de la liste éditoriale), puis les
profils de ses membres. `--skip-existing` combiné à `--limit` fait avancer la
frontière de couverture d'un run à l'autre au lieu de retenter les mêmes.

Pour peupler aussi l'empreinte thématique des fiches de groupe, ajouter
`--interventions-theme-seul` : les débats sont collectés sans leur verbatim,
et `tags_thematiques` cesse d'être vide (#657). C'est ce que le job CI fait
quand `collect_interventions` est coché.

→ `docs/extract-roster-groupes.md`.

### Tout le pipeline, en local plutôt qu'en CI

```bash
./scripts/generate_data_local.sh
```

Enchaîne les mêmes étapes que `generate-data.yml` sur la machine. Se relance en
arrière-plan par défaut et rend la main en affichant le PID et le journal
(`logs/`, git-ignoré) ; `BACKGROUND=false ./scripts/generate_data_local.sh` le
garde attaché au terminal. **Rien n'est committé ni poussé** : relire
`git status` avant de committer soi-même.

Réglages, passés en variables d'environnement — mêmes axes que le formulaire de
lancement :

| Variable | Défaut | Input `workflow_dispatch` correspondant |
|---|---|---|
| `EXISTING_PROFILES` | `refresh` | `existing_profiles` |
| `ADD_UNCOVERED_MEMBERS` | `true` | `add_uncovered_members` |
| `COLD_START` (alias `FRESH_RUN`) | `false` | `cold_start` |
| `THRESHOLD` | `3` | `incomplete_read_threshold` |
| `WORKERS` | `1` | *(local seulement — figé à 1 en CI)* |
| `EXTRACT_INTERVENTIONS` | `false` | `collect_interventions` |
| `ROSTER_EXTRACTION_LIMIT` | `0` (sans plafond) | `roster_limit` |
| `BACKGROUND` | `true` | *(local seulement)* |

→ `docs/workflow-generate-data.md` §2 pour les deux axes du formulaire (#578).

### Une fiche de groupe parlementaire

Tous les groupes déclarés dans `raw_data/groupes_reels.json`, en un run :

```bash
python3 src/generate_group_profiles.py --validate
```

Produit : `pivot_data/groupes/groupe-<SIGLE>-<leg>.json`. Codes de sortie :
`0` tout va bien, **`2` roster indisponible** (rien n'est écrit, les fiches
publiées restent intactes), `1` une génération a réellement échoué.
`--merge-existing` conserve les membres déjà connus qu'un fetch incomplet
n'aurait pas rendus.

### Les fiches de lignée de groupe

Une fiche par **lignée** — la suite des fiches qu'un même groupe a portées au
fil des législatures. C'est ce que l'interface publie ; les fiches par
législature en sont les maillons. À lancer **après** `generate_group_profiles.py`,
dont il lit les sorties :

```bash
python3 src/generate_lignee_profiles.py --validate
```

Produit : `pivot_data/lignees/lignee-<chambre>-<sigle>.json`, une par entrée de
`lignees[]` dans `raw_data/groupes_reels.json`. Ne touche pas au réseau. Sort
`1` si la configuration est fausse (aucune fiche écrite) ou si une lignée a
échoué ; `0` sinon. Compter **~2 min** et **~1,5 Gio** de mémoire pour les dix.

Un maillon déclaré dont la fiche de groupe n'est pas sur le disque fait échouer
**sa** lignée, jamais les autres — et l'écrire amputée est refusé.

Un seul groupe, à la main :

```bash
python3 src/group_profile.py --groupe-id "AN:SOC" --groupe-sigle SOC \
    --groupe-nom "Socialistes et apparentés" --chambre AN --legislature 16 \
    --out pivot_data/groupes/groupe-SOC-16.json \
    pivot_data/profiles/jerome-guedj.pivot.json pivot_data/profiles/boris-vallaud.pivot.json
```

### Une fiche de gouvernement

La liste des gouvernements se lit dans le référentiel AMO30 (#996) ; le fichier
est réécrit à chaque run, ne pas l'éditer à la main :

```bash
python3 src/gouvernements_amo30.py --out raw_data/gouvernements_reels.json
```

Le roster des membres de gouvernement part avec celui des groupes : dans
`rosters_bruts.json`, et — depuis #996 lot 3 — dans `roster_candidats.json`,
d'où leur collecte part. `--sans-gouvernements` débranche les deux :

```bash
python3 src/generate_roster_candidats.py --sans-gouvernements \
    --rosters-bruts-out raw_data/rosters_bruts.json
```

Puis tous les gouvernements de cette liste :

```bash
python3 src/generate_gouvernement_profiles.py --validate \
    --rosters-bruts raw_data/rosters_bruts.json \
    --commissions-dossiers pivot_data/commissions_dossiers.json
```

Produit : `pivot_data/gouvernements/gouvernement-<ID>.json`.

`--rosters-bruts` rattache les membres par `organe_ref` (#996 lot 4) au lieu de
comparer le libellé de leurs mandats à celui de la config. Le fichier est
produit par la commande précédente et n'est **pas committé** : sans lui, le
repli par libellé s'applique et les fiches sont produites quand même — la
sortie dit laquelle des deux voies a servi.

`--commissions-dossiers` (défaut `pivot_data/commissions_dossiers.json`) donne
l'index d'où chaque texte tire sa **commission saisie au fond** (#689) — la
matière qu'une fiche peut afficher sans qu'on en invente une. Absent, illisible
ou vide, chaque texte publie `commission_non_resolue.motif = index_indisponible`,
et jamais un silence : une panne du run ne doit pas se lire « aucun texte n'a de
commission ».

Un seul gouvernement :

```bash
python3 src/gouvernement_profile.py --gouvernement-id "gouvernement:BAYROU" \
    --out pivot_data/gouvernements/gouvernement-BAYROU.json --validate
```

### L'index des scrutins européens

```bash
python3 src/scrutins_europeens.py --profils-dir pivot_data/profiles \
    --out pivot_data/scrutins_europeens.json
```

Produit : `pivot_data/scrutins_europeens.json` — les scrutins du Parlement
européen que les profils publiés citent, avec les effectifs pour / contre /
abstention et leur ventilation par groupe politique. Lit le dump `ep_votes`
déjà en cache ; `--force-download` le rafraîchit.

### L'index des dossiers européens

```bash
python3 src/dossiers_europeens.py --profils-dir pivot_data/profiles \
    --out pivot_data/dossiers_europeens.json
```

Produit : `pivot_data/dossiers_europeens.json` — référence de procédure →
intitulé, type, stade, familles OEIL et domaines EuroVoc, pour les dossiers que
les amendements, les textes portés et les votes européens citent. C'est ce qui
donne un titre lisible derrière « 2021/0136(COD) ».

Les domaines EuroVoc interrogent le portail du Parlement **20 minutes au plus par
run** (`--budget-secondes N`, défaut 1200), dans la limite de `--plafond-requetes N`
requêtes nouvelles (défaut 1 500), le cache répondant sans compter. `--sans-domaines` construit l'index sans aucune requête réseau.

### L'index des documents européens (matières EuroVoc)

```bash
python3 src/documents_europeens.py --profils-dir pivot_data/profiles \
    --out pivot_data/documents_europeens.json
```

Produit : `pivot_data/documents_europeens.json` — pour chaque document `doceo`
cité par un texte porté européen, ses **matières EuroVoc**, libellés en
français. Il existe pour ce que l'index des dossiers ne couvre pas : une
résolution déposée en séance n'ouvre aucune procédure, donc n'a ni commission
au fond ni entrée dans `dossiers_europeens.json`.

Interroge le réseau, à la différence des deux index ci-dessus : le portail du
Parlement pour les concepts — dans la réponse que le résolveur télécharge déjà,
donc **sans requête de plus** — et l'Office des publications pour les libellés,
par lots de 100 concepts. Si le portail se tait, la passe s'arrête après cinq
silences et le dit en fin de sortie.

### La table des commissions saisies au fond

```bash
python3 src/build_commissions_dossiers.py
python3 src/build_commissions_dossiers.py --no-merge

# Le rattachement d'un scrutin à son dossier, et l'issue de ce dossier (#758).
# Mêmes archives, même parcours : un scrutin AN ne nomme pas le texte qu'il
# tranche, le lien n'existe qu'en sens inverse dans `voteRefs`.
python3 src/build_scrutins_dossiers.py
python3 src/build_scrutins_dossiers.py --no-merge

# Reprendre les archives de dossiers encore vivantes (#762) — la 17e seulement,
# les 15e et 16e étant dissoutes. Le workflow l'appelle quand la clé de cache
# hebdomadaire n'a pas été touchée ; à la main, pour forcer une reprise.
python3 src/rafraichir_dossiers_actifs.py
```

Produit : `pivot_data/commissions_dossiers.json` — par dossier législatif, la
commission que l'Assemblée a saisie au fond, lue sur l'acte
`AN1-COM-FOND-SAISIE` des archives déjà en cache et résolue en organe par le
référentiel AMO30. C'est ce que « L'essentiel » de la fiche candidat publie pour
répartir les dossiers amendés ; sans ce fichier, la répartition n'est pas
affichée, et elle n'est **jamais** déduite d'un intitulé de dossier.

La fusion est additive : un run sans archive lisible conserve la table publiée.
`--no-merge` reconstruit de zéro et exige donc que les trois archives aient été
lues.
→ `docs/decisions/vivier-de-points-et-empreinte-de-commission-328.md`.

### Un profil d'eurodéputé (Parltrack), et la date de son cache

```bash
python3 src/mep_profile.py --name "Manon Aubry"
python3 src/mep_profile.py --list
python3 src/mep_profile.py --show-cache-date
```

Affiche le profil sur la sortie standard (`--out` pour écrire un fichier). Le
premier appel télécharge de gros dumps dans `.cache/parltrack/` :
`--show-cache-date` dit de quand ils datent.

### La liste des candidats déclarés

```bash
python3 src/fetch_candidats_declares.py
python3 src/fetch_candidats_declares.py --ecrire --resoudre-identifiants
python3 src/fetch_candidats_declares.py --html capture.html --json
```

Produit : un rapport de relecture sur la sortie standard, et **rien d'autre**
tant que `--ecrire` n'est pas posé.

| Option | Ce qu'elle fait |
| --- | --- |
| `--ecrire` | ajoute dans `raw_data/candidats.json` les déclarés qui n'y sont pas. **Additif** : aucune entrée existante n'est supprimée ni modifiée |
| `--html` | rejoue une capture locale du HTML rendu au lieu d'interroger le réseau |
| `--json` | rend les deux sens de l'écart en JSON |
| `--echouer-si-ecart` | sort en 3 si la source et le fichier diffèrent |
| `--resoudre-identifiants` | résout l'acteur AN de chaque déclaré par identifiant externe (Wikidata `P4123`) et lui **fabrique un slug** quand la chaîne aboutit (#757) |
| `--resolutions-out` | écrit les résolutions dans un fichier, que la passe hors ligne de `merge-and-pivot` relit. Implique `--resoudre-identifiants` |
| `--correspondance` | table slug ↔ acteur AN, lue pour savoir quels slugs sont déjà pris |
| `--article` | change l'article Wikipédia lu (défaut : celui des candidatures) |
| `--candidats` | change le fichier écrit (défaut : `raw_data/candidats.json`) |

Avec `--resoudre-identifiants`, un candidat ajouté **reçoit son slug** dès que
Wikidata porte son identifiant AN (ou établit qu'il n'en a pas) : il entre alors
dans le périmètre du run suivant, et sa correspondance est écrite hors ligne par
`build_correspondance_acteurs_an.py --completer-candidats`. Sans identifiant
résolvable, il entre **sans `slug`** — donc sans shard `extract-an` et sans
publication — et il est **nommé** dans le rapport.
`famille_politique`, `date_declaration` et la source primaire de la déclaration
restent à compléter à la main dans tous les cas. Une entrée que la source range sous « Candidatures retirées » ou « Candidats
pressentis ayant décliné » reçoit `statut: decline` (#763) — c'est un fait lu, et
la note cite la section à la lettre. Celle qui disparaît des déclarés **sans**
qu'aucune de ces sections ne la nomme est signalée et **jamais modifiée** :
déplacement, renommage, cause inconnue. Un statut `officiel` ne bascule jamais —
il viendra du Conseil constitutionnel.

Rien n'est écrit si la collecte échoue : page illisible, section
« Candidats déclarés » introuvable, ou zéro candidat extrait font sortir en 1
sans toucher au fichier.

---

## Auditer

Ce sont des **outils internes de qualité**, jamais des rapports publiables :
pas de score, pas de classement (`AGENTS.md` §2.1). Aucun n'écrit dans
`pivot_data/` ni dans `raw_data/`.

Les quatre premiers partagent le même contrat d'options : `--output-json` /
`--output-md` non renseignés par défaut (le JSON part sur la sortie standard,
le Markdown est simplement sauté), `--staleness-days 30` fixe le seuil
au-delà duquel une fiche dont toutes les sources sont anciennes est signalée,
et `--output-dir DOSSIER` écrit les deux fichiers sous un nom horodaté au lieu
de les nommer un par un.

### Le sédiment : ce que le corpus garde d'une source retirée

```bash
python3 src/audit_sediment.py
python3 src/audit_sediment.py --par-profil --json sediment.json
```

Produit : un tableau par couche — `raw_data/profiles` **et** `pivot_data/profiles`,
les deux, parce qu'un retrait appliqué au seul brut ne descend jamais au pivot
(#729) — et par famille : interventions à identifiant entier, mandats sans
`categorie_source`, mandats actifs sans aucune date, `sources[]` sous licence
Regards Citoyens, avertissements hérités, preuves de couverture citant la source
retirée. `--profiles-dir` restreint à une couche, et se répète.

**Ne retire rien, ne juge rien** : c'est le compteur de référence, à relancer
après chaque run. Une famille revenue à zéro qui remonte est une régression.

### La reproductibilité des mandats sans `categorie_source`

```bash
python3 src/audit_mandats_reproductibles.py
python3 src/audit_mandats_reproductibles.py --introuvables --json verdicts.json
python3 src/audit_mandats_reproductibles.py --only jean-luc-melenchon
```

Produit : un verdict par entrée, contre **deux** référentiels — AMO30 lu dans
`.cache/acteurs_historique_an/` et le bloc `mandat_europeen` du profil brut,
qu'AMO30 ne porte pas. Aucun appel réseau.

`--introuvables` liste ce qui demande une relecture à la main ; `--pivot-dir` et
`--brut-dir` déplacent les deux couches lues. **Aucun retrait ne se déduit de
cette sortie** : « aucune date », « acteur non résolu » et « référentiel vide »
déclarent ce que la mesure n'a pas établi, ils ne jugent pas (§2 règle 5).

### Ce que les profils devraient encore à la source retirée

```bash
python3 src/audit_residus_source_retiree.py
python3 src/audit_residus_source_retiree.py --par-profil --retirer-orphelines --json residus.json
```

Produit : pour chaque profil concerné, ce qui retient la clause ODbL une fois le
nettoyage **simulé** — une donnée encore publiée, ou le seul marqueur
`sources[]`. La licence est recomposée par `licences.licences_du_profil()`, la
fonction de production. Rien n'est écrit.

`--retirer-orphelines` pose en plus le retrait des interventions héritées sans
jumelle Syceron. Le retrait du marqueur lui-même n'est pas un geste technique :
c'est une décision éditoriale à effet juridique (§7).

### Les profils pivot

```bash
python3 src/audit_pivot_dataset.py --input-dir pivot_data/profiles \
    --output-json audit_pivot.json --output-md audit_pivot.md --staleness-days 30
```

Produit : volumétrie (dont la répartition `candidat_declare` / `roster_groupe`),
complétude, cohérence, fraîcheur des sources, `meta.warnings[]` agrégés, et deux
tableaux croisés `votes` / `textes_portes` / `amendements` / `interventions`.
Les candidats déclarés y figurent nommément ; les profils issus du roster sont
agrégés par groupe, jamais membre par membre.

### Les fiches de groupe

```bash
python3 src/audit_groupe_dataset.py --input-dir pivot_data/groupes \
    --scrutins pivot_data/scrutins.json \
    --output-json audit_groupe.json --output-md audit_groupe.md
```

Produit : mêmes axes que ci-dessus pour `pivot_data/groupes`, plus les
`cohesion_votes`, les `amendements_agreges` et l'écart de couverture du roster.

`--scrutins` (défaut `pivot_data/scrutins.json`) fournit l'index partagé d'où
vient la **date** de chaque scrutin de cohésion : `cohesion_votes[]` ne porte
qu'un `scrutin_id` depuis #432. Un index absent ou vide n'est pas une panne —
les plages temporelles sont vides et le rapport le **déclare** (#726).

### Les fiches de gouvernement

```bash
python3 src/audit_gouvernement_dataset.py --input-dir pivot_data/gouvernements \
    --output-json audit_gouvernement.json --output-md audit_gouvernement.md
```

Produit : mêmes axes pour `pivot_data/gouvernements`, plus la présence de
`premier_ministre`, le taux de `membres[].portefeuille` renseigné, et la
**couverture des archives de dossiers** — pour qu'« hors couverture de la
source » ne se lise jamais « vraiment zéro » (#399).

### Les trois d'un coup

```bash
python3 src/audit_pipeline.py --output-json audit_pipeline.json --output-md audit_pipeline.md
```

Il porte lui aussi `--scrutins` (même défaut, même rôle), qu'il passe à l'audit
des groupes.

Produit : les trois rapports détaillés plus une « vue d'ensemble » (totaux
audités, erreurs de lecture, warnings agrégés). Pure composition — aucun calcul
nouveau. Volontairement **jamais** branché sur la CI (#178). Un répertoire
manquant est une erreur explicite, code de sortie 1, jamais une trace d'appel.

### À quoi ressemble un rapport

Sans toucher au corpus, sur les fixtures figées de la suite de tests. Une
commande ne peut pas être périmée, un exemple committé si :

```bash
python3 src/audit_pivot_dataset.py --input-dir tests/fixtures/audit_pivot \
    --output-json audit_pivot_exemple.json --output-md audit_pivot_exemple.md
```

Même chose avec `--input-dir tests/fixtures/audit_groupe` et
`tests/fixtures/audit_gouvernement` pour les deux autres.

### La clé `(legislature, numero_scrutin)` est-elle utilisable ?

```bash
python3 src/audit_legislature_votes.py
python3 src/audit_legislature_votes.py --out audit/legislature_votes.md
```

Passe de corpus, sans réseau, qui **ne modifie aucun fichier**. Sortie 0 si
toutes les législatures de votes sont résolues, 1 sinon. À lancer avant de se
fier à la clé : `numero_scrutin` repart à 1 à chaque législature.
→ `docs/decisions/resolution-legislature-votes.md`.

### Un texte porté européen est-il publié deux fois ?

```bash
python3 scripts/purger_doublons_textes_europeens_901.py
python3 scripts/purger_doublons_textes_europeens_901.py --ecrire
```

Sans `--ecrire`, **rien n'est modifié** : le script nomme les profils concernés
et compte. Un texte européen n'a pas de `dossier_id` et était identifié par son
titre ; #938 a nettoyé les titres, et 311 textes ont été publiés deux fois.
La clé est corrigée — un texte européen est désormais identifié par son document
`doceo` —, mais la fusion additive ne retire jamais ce qui est déjà publié.

Le contrôle de perte **bloque** ensuite, et c'est voulu : 311 entrées de moins
sur une liste stable. La perte se déclare (`--tolerer-pertes`, ou l'entrée
« INTENDED REMOVAL » du formulaire), elle ne se contourne pas.
→ `docs/decisions/doublons-textes-europeens-cle-doceo-901.md`.

### Une explication de vote est-elle publiée deux fois ?

```bash
python3 scripts/purger_doublons_interventions_827.py
python3 scripts/purger_doublons_interventions_827.py --ecrire
```

Sans `--ecrire`, **rien n'est modifié** : le script nomme les profils concernés
et compte. #827 a donné un `source_url` aux explications de vote, or leur clé de
déduplication passait par ce champ : elles ont été publiées **deux fois**, une
fois sans lien et une fois avec. La clé est corrigée, mais la fusion additive ne
retire jamais ce qui est déjà publié.

Ne touche que les interventions **sans** `intervention_id` : celles qui en ont
un partagent leur clé de contenu par centaines de milliers, faute de sujet et de
texte en mode thème-seul.
→ `docs/decisions/cle-de-fusion-qui-depend-dun-champ-volatil-827.md`.

### Un profil de roster porte-t-il une liste que sa collecte déclare écartée ?

```bash
python3 scripts/purger_textes_portes_roster_747.py --verifier
python3 scripts/purger_textes_portes_roster_747.py --dry-run
python3 scripts/purger_textes_portes_roster_747.py
```

`--verifier` ne modifie rien : sortie 0 si aucun profil de roster ne porte de
`textes_portes` alors que son `meta.collecte_ecartee` le déclare écarté, 1
sinon. Sans drapeau, la purge s'applique aux **deux** étages — les slugs cibles
étant établis sur le pivot, seul étage qui porte `meta.provenance`. Passe de
corpus, sans réseau, idempotente.
→ `docs/decisions/purge-textes-portes-roster-747.md`.

### Une fiche de candidat sait-elle dire que sa carrière commence avant 2002 ?

```bash
python3 scripts/poser_mandats_anterieurs_860.py --verifier
python3 scripts/poser_mandats_anterieurs_860.py --dry-run
python3 scripts/poser_mandats_anterieurs_860.py
```

`--verifier` ne modifie rien : sortie 0 si tout profil de candidat déclaré porte
`mandats_anterieurs` — la liste relue s'il est dans la table, `null` et son motif
`non_relu` sinon —, 1 s'il en manque. Sans drapeau, la reprise repose le champ
sur les profils déjà écrits, depuis `raw_data/mandats_anterieurs.json`.

À lancer quand la table relue change **entre deux runs** : le pipeline repose ce
champ dérivé à chaque écriture de profil, donc un run complet le ferait aussi —
mais au prix de sa collecte, alors que la reprise ne demande aucun réseau. Passe
de corpus, idempotente, candidats déclarés seulement : un membre de roster ne
publie pas de fiche. → `docs/decisions/mandats-anterieurs-couverture-860.md`.

**Elle saute les profils gelés** (statut `decline`, #760), depuis le 16/09/2026 : la passe des
candidats déclarés ne les réécrit pas, et la reprise ne fait pas ce que le run refuse de faire.
Un constat posé dans la table pour un candidat gelé **n'atteint pas sa fiche** — c'est le cas de
Jordan Bardella, que rien ne régénère. Laurent Wauquiez, gelé mais membre d'un groupe, le reçoit
par la passe des groupes au run suivant. Le décompte imprimé exclut les gelés.

### Volumétrie : ce que pèse le corpus et ce que rapporterait chaque levier

```bash
python3 src/audit_volumetrie_profils.py --profils-dir pivot_data/profiles \
    --echantillon 60 --out audit/volumetrie.md
```

Produit : le poids mesuré des profils et le gain de chaque levier d'allègement
(compactage, gzip, externalisation d'un champ vers un index dédié), plus une
projection vers `--cible`. Mesure des leviers qui **déplacent** la donnée, pas
qui la suppriment. → `docs/decisions/` (#429).

Variante hors dépôt, pour générer le roster complet sans polluer l'arbre
versionné (~6 Go de churn sinon) :

```bash
./scripts/mesure_volumetrie_roster.sh
```

Écrit dans `../empreinte-mesure-volumetrie` par défaut (`OUT_DIR`), journal sous
`logs/`. Rien n'est jamais committé.

---

## Vérifier avant de committer

Ce sont les **cinq contrôles que la CI exécute avant chaque commit de données**,
tous relançables à la main à l'identique. Chacun tourne dans son propre
processus, et **aucune tolérance n'en désarme un autre**.

### Le quality gate — le seul gate bloquant

```bash
python3 src/check_quality_gate.py
```

Sortie 0 = le commit est autorisé. Sections dures : `IncompleteRead` au-delà du
seuil, fichier de groupe ou de gouvernement manquant ou invalide, format des
index amendements figés, slug publié sans correspondance AN (§5b), et la §7 qui
**échoue à 80 Mio** sur le plus gros fichier versionné (avertissement dès
50 Mio). Réglages courants :

```bash
python3 src/check_quality_gate.py --threshold 0
python3 src/check_quality_gate.py --low-interventions 5
python3 src/check_quality_gate.py --groupe-min-coverage-pct 50
python3 src/check_quality_gate.py --amendements-staleness-days 14
python3 src/check_quality_gate.py --blob-warn-mo 0
```

→ `docs/data-architecture.md` (le tableau des sections, dur/souple).

### Contrôle de perte — une régénération ne retire jamais de la donnée

```bash
python3 src/audit_diff_profils.py --ref HEAD
```

Compare **deux états** de `pivot_data/`. Trois constats bloquent : un fichier
**disparu**, une **baisse sur une liste stable**, un **scalaire surveillé qui
passe de renseigné à `null`**. Le reste est rapporté sans bloquer. Une perte
légitime se **déclare** (`--tolerer-pertes`), elle ne se contourne pas en
retirant le contrôle.

### Intégrité référentielle — chaque clé publiée résout

```bash
python3 src/audit_integrite_referentielle.py
python3 src/audit_integrite_referentielle.py --sans-amendements
```

Vérifie une **invariance dans un seul état** : depuis les deux index partagés,
un vote ou un amendement n'a de sens que si sa clé résout dans l'index qu'elle
désigne. Sortie non nulle en nommant fichier et clé. `--sans-amendements` ne
contrôle que les scrutins, bien moins cher.

### Tout ce qui est collecté est-il publié ?

```bash
python3 src/audit_collecte_non_publiee.py
```

Sortie non nulle dès qu'un `raw_data/profiles/<slug>.json` n'a pas son
`pivot_data/profiles/<slug>.pivot.json`. Seuil **0**. Ne parse aucun profil —
deux listes de noms de fichiers.

### Chaque liste publiée porte-t-elle ce qui a été collecté ?

```bash
python3 src/audit_collecte_vs_publie.py
```

Le contrôle précédent raisonne sur des **profils** ; celui-ci sur le **contenu
de leurs listes** — un pivot présent mais vidé de ses interventions lui est
irréprochable. Chaque liste publiée déclare dans `RELATIONS` les chemins du brut
dont elle est la somme, d'où un seuil **0** partout. Le déficit bloque,
l'excédent est rapporté.

Les quatre derniers écrivent aussi un rapport avec `--out` (Markdown) et
`--out-json`.
→ `docs/workflow-generate-data.md` §8 pour leur placement exact dans le run.

---

## Opérer

### Régénérer la table slug ↔ acteur AN

```bash
python3 src/build_correspondance_acteurs_an.py --verifier
python3 src/build_correspondance_acteurs_an.py
```

`--verifier` n'écrit rien et sort 1 s'il manque un slug ; sans lui, la table
`raw_data/correspondance_acteurs_an.json` est complétée et réécrite. Les
entrées existantes sont reconduites **verbatim** — c'est du travail relu — et un
slug non résolu est **nommé sur stderr** plutôt qu'inventé. C'est le remède
quand le quality gate §5b échoue en nommant un slug **hérité**.

```bash
python3 src/build_correspondance_acteurs_an.py \
  --completer-derivees --rosters-bruts raw_data/rosters_bruts.json
```

Passe **additive et hors ligne** (#715), celle que `merge-and-pivot` lance avant
le portail : elle ajoute une entrée `origine: "derivee"` pour les seuls slugs
que `raw_data/rosters_bruts.json` déclare **fabriqués** (#708), c'est-à-dire
dérivés de l'état civil de leur acteur — il n'y a là aucun rapprochement à
prouver, seulement l'identifiant à **geler**. Elle ne lit ni AMO30 ni le réseau,
ne réécrit aucune entrée relue, et refuse en nommant le slug si le profil publié
ne porte pas exactement l'acteur que le roster déclare.
→ `docs/decisions/correspondance-acteurs-an-525.md`,
`docs/decisions/entree-derivee-correspondance-715.md`.

```bash
python3 src/build_correspondance_acteurs_an.py \
  --completer-candidats --resolutions raw_data/resolutions_candidats.json
```

Sa **jumelle pour les candidats déclarés** (#757), aux mêmes propriétés —
additive, hors ligne, disjointe. Elle ajoute une entrée `origine: "sourcee"`
pour les slugs dont l'acteur AN a été résolu par **identifiant externe**
(Wikidata `P4123`, au job de tête du run) — un rapprochement, donc, mais
**sourcé et daté** plutôt que relu.

Elle n'écrit que si le profil publié **corrobore** la résolution : l'acteur
déclaré doit être celui que le profil porte, et le fait négatif
(`ecart: "hors_an"`) exige que les **deux** sources se taisent — pas de `P4123`,
et aucun acteur dans le profil qu'AMO30 a produit. En désaccord, aucune entrée :
le slug est nommé, la §5b bloquera, et un humain arbitre.
→ `docs/decisions/boucle-perimetre-candidats-757.md`.

### J'ai écrit une décision : mettre l'index à jour

```bash
python3 scripts/generer_index_decisions.py
python3 scripts/generer_index_decisions.py --verifier
```

`docs/technical_decisions.md` est **généré** depuis les fichiers de
`docs/decisions/` (#840) — il ne s'édite pas à la main. Chaque décision porte
son titre, sa date et son résumé `> **En bref** — …` ; le script les assemble,
de la plus récente à la plus ancienne.

C'est ce qui supprime les conflits : un lot n'écrit que **son** fichier, que
personne d'autre ne touche. `--verifier` ne modifie rien, sortie 1 si l'index a
dérivé.
→ `docs/decisions/index-decisions-genere-840.md`.

### Régénérer la table « ce module → ces décisions »

```bash
python3 scripts/generer_decisions_par_module.py --verifier
python3 scripts/generer_decisions_par_module.py
```

`--verifier` n'écrit rien et sort 1 si le fichier committé a dérivé du dépôt ;
sans lui, `docs/decisions-par-module.md` est réécrit. À relancer après avoir
ajouté ou modifié une décision, ajouté ou renommé un module de `src/`, ou
renommé une fonction qu'une décision nomme. `tests/test_decisions_par_module.py`
fait la même vérification dans la suite.
→ `docs/decisions/table-inversee-decisions-par-module.md`.

### Vérifier que les SHA cités sont archivés dans Software Heritage

```bash
python3 src/verifier_archivage_swh.py
python3 src/verifier_archivage_swh.py --json --sans-issues
```

Relève les SHA **effectivement cités** dans les `.md` suivis et les corps
d'issues, puis demande à Software Heritage s'ils résolvent. Trois verdicts, par
code de sortie : `0` vérifié, `1` des SHA manquent (**ne pas couper**), `2`
indéterminé — quota épuisé ou API injoignable, on n'a rien établi.
`--sans-issues` se limite aux fichiers du dépôt (pas de `gh` requis).
**À lancer avant tout bornage d'historique**, jamais après.

### Borner l'historique de données

Deux scripts, deux contrats. **La mesure d'abord** — elle ne touche à rien :

```bash
./scripts/borner_historique_donnees.sh --mesurer
./scripts/borner_historique_donnees.sh --mesurer --fenetre 30
```

Clone le dépôt dans un répertoire temporaire, y applique la coupure, repacke et
rend le gain **réel**. Ne pousse jamais, ne modifie jamais `main`.

**L'exécution ensuite**, par le runner guidé — sept étapes dont trois
irréversibles, dans un ordre dont une seule inversion est irrattrapable :

```bash
./scripts/executer_bornage_guide.sh --lister
./scripts/executer_bornage_guide.sh --fenetre 30
./scripts/executer_bornage_guide.sh --reprendre logs/bornage_<horodatage>.log
```

`--lister` affiche les sept étapes et sort sans rien faire. Le runner impose
l'ordre, refuse d'avancer sur une précondition en échec, et tient un journal de
ce qui a été fait. `--etape N` n'exécute qu'une étape, `--jusqu-a N` s'arrête
après la N-ième.

### Sortir de `commission` les mandats que l'AN type « gouvernement » (#730)

```bash
python3 src/reprise_mandats_gouvernementaux.py            # simulation
python3 src/reprise_mandats_gouvernementaux.py --apply     # applique
```

Huit mandats ministériels étaient publiés en `commission`, sur l'organe
`Gouvernement`. Le critère est **le typage du référentiel** — l'index d'organes
AN type cet organe `GOUVERNEMENT`, et c'est le seul libellé dans ce cas — jamais
une lecture du libellé. Une entrée dont la période est déjà couverte par un
`fonction_gouvernementale` du profil est **retirée** ; sinon elle est
**requalifiée**, parce que la retirer effacerait une période réelle.

Simulation par défaut, idempotent, et sans effet si l'index d'organes manque
(`.cache/acteurs_historique_an/index_organes_v2.json`) : un critère qui ne peut
pas s'établir ne se devine pas.

### Les migrations ponctuelles

Déjà appliquées au corpus. Elles restent relançables : **`--verifier` ne
modifie rien** et dit si le corpus est conforme.

```bash
python3 src/migrer_identite_couverture_539.py --verifier
python3 src/migrer_absences_publiees_556_558_560.py --verifier
python3 src/migrer_profils_partitionnes_580.py --verifier-seulement
python3 src/purge_mandats_dupliques.py --only jean-luc-melenchon
python3 src/purge_interventions_heritees.py
python3 src/purge_interventions_heritees.py --profiles-dir pivot_data/profiles
python3 src/purge_mandats_nosdeputes.py
python3 src/purge_mandats_nosdeputes.py --profiles-dir pivot_data/profiles
```

Pour écrire réellement : retirer `--verifier` sur les deux premières, passer
`--apply` sur les cinq dernières. Chacune est décrite dans la décision qui porte
son numéro, sous `docs/decisions/`.

`purge_interventions_heritees.py` se lance **deux fois, une fois par couche** :
la fusion est additive aux deux étages, et un retrait appliqué au seul brut ne
descend jamais dans `pivot_data/` (#729). Il ne retire une intervention héritée
que si sa jumelle Syceron est présente dans le même profil ; sans jumelle, il la
conserve et le dit. `--retirer-sans-jumelle` étend le retrait à celles-là —
vérifiées une par une dans les archives de l'AN, qui ne les rattache à aucun
mandat (#839). Au pivot, il **recompose les champs dérivés** (`tags_thematiques`,
`meta.licence_donnees`) après le retrait, comme la fusion le fait (§4).

`purge_mandats_nosdeputes.py` se lance aussi une fois par couche. Il retire un mandat
**sans `categorie_source`** dont la fonction commence par une minuscule : la forme
qu'écrivait la collecte NosDéputés, qu'aucune source vivante n'établit (#718). Au
pivot, il recompose `chambres`.

`purge_mandats_non_faits.py` retire les onglets de page publiés comme des
commissions, sur une **liste close** de libellés : même signature de forme que
des organes réels du Sénat, qu'il conserve et compte.

```bash
python3 src/purge_mandats_non_faits.py
python3 src/purge_mandats_non_faits.py --profiles-dir pivot_data/profiles --apply
```

`purge_mandats_doublons_europarl.py` retire le mandat européen publié **deux
fois** parce que le portail du Parlement européen publie deux fois la même
appartenance — l'une classée, l'autre non. Il ne touche que le **pivot** : le
brut garde les deux entrées de la source (#580).

```bash
python3 src/purge_mandats_doublons_europarl.py
python3 src/purge_mandats_doublons_europarl.py --apply
```

---

## Voir ce que voit l'utilisatrice

### Le formulaire de lancement, tel que GitHub l'affiche

```bash
python3 scripts/rendu_formulaire.py
```

Rend les inputs `workflow_dispatch` de `generate-data.yml` **tels qu'ils
apparaîtront à l'écran**, largeur comprise. **À lancer avant de toucher à un
libellé** : relire le YAML masque exactement le défaut corrigé par #578.
→ `docs/workflow-generate-data.md` §2.

### L'interface, en local

```bash
cd web/UI_finale
npm install
npm run dev
```

`npm install` seulement la première fois. `npm run dev` synchronise d'abord les
données pivot vers `public/data/` (généré, git-ignoré) puis démarre Vite. La
couverture affichée se limite aux candidats, groupes et gouvernements qui ont un
fichier pivot en local.

### Ce qu'un moteur de recherche voit du site en ligne

```bash
node web/UI_finale/scripts/verifier-referencement.mjs
```

Parcourt le `sitemap.xml` du site **en ligne** et relève, adresse par adresse :
statut HTTP, `<title>`, `canonical`, longueur du texte lisible **sans
JavaScript**, et types du balisage Schema.org — validés contre le vocabulaire
publié par schema.org, que `--sans-vocabulaire` permet de ne pas télécharger
(#1008). Sort en échec si une adresse ne répond pas 200, si un titre
manque, si deux pages partagent le même titre, ou si une fiche a perdu son texte
en clair (#969). Une autre base s'ajoute en argument — un build local servi
comme GitHub Pages, jamais `vite preview`, qui ne reproduit pas son 404.

Les générations de design archivées (`web/old/`, v1–v7) sont du HTML statique :

```bash
python3 -m http.server 8000
```

### La suite de tests

```bash
pytest -q
```

Environ 11 s. Aucun test ne lit `pivot_data/` ni `raw_data/profiles/`, n'écrit
sous l'un des deux, ni ne sort sur le réseau (#473).
→ `docs/decisions/ci-tests-pytest.md`.

---

## Ce qui n'est pas ici, et pourquoi

Le dépôt compte **46 exécutables** (41 modules `src/` avec un CLI, 5 scripts).
Ce fichier en documente **33**. Les 13 autres ont un CLI, mais personne n'a de
raison de les taper :

| Écarté | Pourquoi |
|---|---|
| `src/candidate_profile_ue.py` | `generate_all_profiles.py` l'appelle déjà pour chaque candidat ; son CLI sert au débogage |
| `src/gouvernement_roster.py` | ne produit que la composition ministérielle, un étage de `gouvernement_profile.py` |
| `src/group_roster.py`, `src/an_roster.py` | la composition réelle d'un groupe, lue par les générateurs ; leur CLI est une vue de débogage |
| `src/merge_profile.py` | la fusion additive, appelée à chaque régénération |
| `src/build_scrutins_index.py`, `src/build_amendements_index_pivot.py` | les deux index partagés — `generate_all_profiles.py --pivot` les reconstruit au bon moment, et l'ordre compte |
| `src/build_amendements_index.py` | le point d'entrée du job CI `extract-amendements-an`. Son unique drapeau force la reconstruction des législatures non figées au changement de semaine ISO, et le job l'arme seul depuis la sortie de son `actions/cache` — jamais à taper (`docs/decisions/fraicheur-index-amendements-749.md`) |
| `src/build_scrutins_index_figes.py`, `src/build_amendements_index_figees.py` | les législatures closes (14/15/16) : construites **une fois**, hors ligne, puis committées sous `raw_data/`. La procédure complète et ses modes de défaillance sont dans `docs/decisions/amendements-legislatures-figees.md` et `docs/decisions/votes-multi-legislature.md` |
| `src/cache_an_fraicheur.py`, `src/cache_an_empreinte.py` | la mécanique de cache des jobs CI, sans usage local |
| `src/verifier_transport_artifacts.py` | compare l'inventaire des artifacts d'un run à ce qui est arrivé sur le disque (#786) ; il n'a de sens qu'à l'intérieur du run qu'il inspecte, et hors CI il le dit et rend la main |

Aucun n'est mort. Onze sont sur le chemin d'exécution du pipeline, et
`docs/workflow-generate-data.md` dit quel job les appelle ; les deux derniers
sont des constructions ponctuelles, hors ligne, dont la procédure est écrite
dans la décision qui les porte.

Les deux index partagés, eux, se reconstruisent à la main quand un run a été
interrompu : la commande et **l'ordre à respecter** sont dans
`docs/data-architecture.md`, avec la raison de cet ordre.
