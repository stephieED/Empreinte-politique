<a id="partition-profils-legislature-580"></a>
<a id="garde-fou-blob-580"></a>
# Le seuil de blob sort du critère de sortie, et les profils bruts se partitionnent par législature (#580) (2026-08-29)

`2026-08-29`

> **En bref** — le profil brut se partitionne par législature (56,0 → 23,4 Mo) et le plafond de blob devient un garde-fou du quality gate, pas un critère de sortie.

Deux décisions prises ensemble, et qui ne tiennent qu'ensemble. **A** seule
reviendrait à déclarer le problème hors sujet ; **B** seule laisserait un
critère de sortie qui ne peut structurellement jamais être atteint.

---

## A. « Aucun blob au-dessus de 50 Mo » n'était pas un critère

### Ce qui n'allait pas

Le critère de sortie de l'épic volumétrie #429
([#critere-sortie-volumetrie-429](critere-sortie-volumetrie-429.md)) portait
quatre clauses. Trois décrivent des **propriétés du dépôt** — sa taille après
`gc`, le coût d'un push, la préservation du mapping. La quatrième décrivait un
**événement** : le franchissement d'un seuil par un fichier.

Un critère, on l'atteint. Celui-là se déclenche. Et il s'est déclenché **le jour
même de son écriture** : le 28/08/2026 il annonçait 38,6 Mo pour le plus gros
blob ; le 29/08, le run de données ayant doublé les amendements, le plus gros
fichier du dépôt pèse **56,0 Mo** (`raw_data/profiles/mathilde-panot.json`).

GitHub l'avait dit, au push :

```
remote: warning: File raw_data/profiles/mathilde-panot.json is 56.00 MB;
remote: this is larger than GitHub's recommended maximum file size of 50.00 MB
```

**Personne ne l'a vu.** Pas parce que l'avertissement manquait — il était là,
dans les journaux du run — mais parce que **rien ne disait quoi en faire**. Un
chiffre sans conduite à tenir n'appelle aucune action, donc n'en déclenche
aucune.

### Ce qui a été écarté : relever le seuil

C'est la lecture qui vient d'abord, et la mesure la condamne. Au 29/08/2026,
sur `raw_data/profiles` :

| Seuil | Fichiers |
| --- | ---: |
| > 50 Mo | **8** |
| > 45 Mo | **54** |
| > 40 Mo | 59 |

**Quarante-six fichiers sont massés entre 45 et 50 Mo.** Ce sont les mêmes
députés cosignant les mêmes amendements : ils franchissent la ligne **en bloc**
à chaque correction de collecte. Le seuil ne surplombe pas une queue de
distribution, il est planté au milieu d'une falaise. Le porter à 60 Mo
achèterait un cycle de correction, pas davantage.

### Ce qui est retenu

**Le critère de sortie de #429 garde ses trois clauses mesurables**, et elles
sont **atteintes** — re-mesurées le 29/08/2026 sur le corpus doublé :

| Clause | Seuil GitHub | 20/08 | **29/08** | Marge | |
| --- | --- | ---: | ---: | ---: | --- |
| Dépôt après `gc --prune=now` | 5 Go *(déconseillé)* | 294 Mo | **627 Mo** | × 8 | ✅ |
| Coût d'un push | 2 Go *(refus)* | ~174 Mo | **204 Mo** | × 10 | ✅ |
| Mapping préservé | — | ✓ | *non re-mesuré* | — | ✅ |

Le push de 204 Mo est celui du run qui a doublé les amendements — **le pire cas
observé, pas un run ordinaire**. Le mapping n'est **pas** re-mesuré : le run du
28/08 n'a fait qu'ajouter de la donnée, et `allow_declared_losses` aurait bloqué
le commit en cas de perte. C'est un argument, pas une preuve, et c'est consigné
comme tel.

**La taille du plus gros fichier devient un garde-fou surveillé**, porté par
`src/garde_fou_blobs.py` et branché en **§7 du quality gate**
(`check_quality_gate.py`), c'est-à-dire dans le contrôle qui décide si le commit
de données part ou non.

| Seuil | Effet | Ce qu'il protège |
| ---: | --- | --- |
| **50 Mio** | **avertit** (`::warning::`, non bloquant) | le seuil recommandé par GitHub, celui de l'avertissement au push |
| **80 Mio** | **bloque** (`::error::`, `exit 1`, commit annulé) | la marge de manœuvre : 20 Mio avant le refus, c'est-à-dire le temps de découper |
| 100 Mio | *(GitHub)* | la limite **dure** : push refusé, et un blob déjà committé ne se retire plus sans réécrire l'historique |

**Pourquoi bloquer à 80 et pas à 100.** Un contrôle qui n'alerterait qu'à la
limite dure alerterait au moment où il est trop tard : le blob est alors déjà
écrit dans un commit, et le retirer demande une réécriture d'historique. Les
20 Mio d'écart sont le délai laissé pour agir.

**Pourquoi dans le quality gate et pas dans la suite de tests.** `tests.yml`
sparse-checkout délibérément **sans** `raw_data/profiles` (#473) : aucun test ne
peut mesurer le corpus, et un test qui le lirait serait vert en local et sans
objet en CI. Le gate, lui, tourne juste avant le commit, sur le corpus réel.
C'est le seul endroit d'où le constat est possible.

### La conduite à tenir — le point qui manquait

Elle est **imprimée avec le constat**, console et résumé de job, et versionnée
dans `garde_fou_blobs.CONDUITE_A_TENIR` (donc testée, `tests/test_garde_fou_blobs_580.py`) :

1. **Identifier le champ qui pèse** —
   `python3 src/audit_volumetrie_profils.py --profils-bruts-dir raw_data/profiles --echantillon 1`
   nomme le fichier le plus lourd et le poids de chacun de ses champs.
2. **Partitionner sur un champ déjà présent**, comme B ci-dessous l'a fait pour
   `amendements` sur `legislature` (56,0 → 23,4 Mo). Jamais dénormaliser, jamais
   dédupliquer, jamais rogner un champ.
3. **Si le fichier est déjà partitionné, découper plus fin** (par texte, par
   session) — la partition existante donne le motif à suivre.
4. **NE PAS relever le seuil** — la falaise ci-dessus.
5. **NE PAS supprimer de données** pour passer sous le seuil : ce serait
   échanger une limite d'hébergement contre une perte de collecte. Principe
   directeur de #429 : *normaliser, jamais supprimer.*

---

## B. Partitionner `raw_data/profiles` par législature

### La mesure qui décide

Décomposition du plus gros profil brut, 56,00 Mo :

| Champ | Poids | Part |
| --- | ---: | ---: |
| `amendements` | **54,15 Mo** | **96,7 %** |
| `votes` | 1,83 Mo | 3,3 % |
| tout le reste | 0,02 Mo | 0,0 % |

Et chaque amendement porte **déjà** son champ `legislature` : mesuré sur les
481 profils, **6 091 732 amendements, 0 sans `legislature`, 0 sans `uid`, 0
`uid` dupliqué à l'intérieur d'un profil**, quatre valeurs seulement (`"14"`,
`"15"`, `"16"`, `"17"`).

Découpe simulée sur `mathilde-panot.json` :

| | |
| --- | ---: |
| socle *(tout sauf les amendements)* | 1,85 Mo |
| législature XV | 9,48 Mo |
| législature XVI | 21,31 Mo |
| législature XVII | 23,37 Mo |
| **plus gros fichier après découpe** | **23,37 Mo** |

**56,0 → 23,4 Mo, sans supprimer un octet.** Et ça survit à l'achèvement des
archives : même complétées, les plus gros fragments restent autour de 30 Mo.

### Ce que ce n'est pas

**Ce n'est pas la normalisation écartée par #434.** Celle-là déduplique les
cosignatures et **transforme** la donnée. Ici c'est un partitionnement de
fichier sur un champ existant : la couche source-near reste exactement ce
qu'elle est, aux mêmes octets près. Aucun champ n'est retiré, réécrit ni
dédupliqué — `recomposer(partitionner(p)) == p`, ordre de la liste **et** ordre
des clés compris.

### La disposition retenue

```
raw_data/profiles/
├── mathilde-panot.json          ← le socle : le profil SAUF `amendements`
└── mathilde-panot/              ← les tranches, un fichier par législature
    ├── 15.json
    ├── 16.json
    └── 17.json
```

Le socle porte, à la place exacte qu'occupait `amendements`, un manifeste :

```json
"amendements_partitionnes": {
  "schema": "profil-brut-partitionne-v1",
  "total": 52310,
  "tranches": [
    {"legislature": "15", "fichier": "15.json", "nombre": 9120},
    {"legislature": "16", "fichier": "16.json", "nombre": 20100},
    {"legislature": "17", "fichier": "17.json", "nombre": 23090}
  ],
  "ordre": [[0, 9120], [1, 20100], [2, 23090]]
}
```

**Pourquoi un socle `<slug>.json` + un répertoire frère, et pas un répertoire
par profil** (`mathilde-panot/profil.json` + `mathilde-panot/amendements-15.json`) :

1. **Le slug reste énumérable au même endroit.** Les `glob("*.json")` du dépôt
   qui listent les profils bruts continuent de rendre exactement les 481 mêmes
   noms — `glob` n'est pas récursif, et un répertoire n'est pas un `.json`. Un
   répertoire par profil aurait fait rendre **zéro** à chacun de ces appels :
   une population vide, donc un audit qui conclut « aucun écart » sans avoir
   rien rapproché — le défaut §2.5 sous sa forme la plus coûteuse.
2. **La découvrabilité humaine.** Qui parcourt `raw_data/profiles/` voit la même
   liste de personnes qu'avant, et à côté de chaque nom un répertoire du même
   nom dont le contenu se lit sans documentation : `16.json`, ce sont les
   amendements de la 16<sup>e</sup> législature. Chaque tranche est en outre un
   document autonome (`schema`, `slug`, `legislature`, `amendements`) : elle
   s'explique sans le socle.
3. **Le socle reste un document complet** pour tout ce qui n'est pas amendement.
   Il pèse 1,85 Mo là où le profil en pesait 56 :
   `scrutins_index.iter_votes_du_repertoire` lisait 7,5 Go pour n'y chercher que
   des votes ; il en lira ~0,9, **sans une ligne de changement**.

**Pourquoi `ordre`, un codage par plages.** Il restitue l'ordre d'origine de la
liste, quel que soit cet ordre. Mesuré sur les 481 profils : **445 sont
parfaitement groupés** par législature, 36 ne le sont pas — le maximum observé
est de **5 plages** pour 4 législatures. Le codage coûte donc quelques dizaines
d'octets et rend l'aller-retour exact partout, plutôt que « exact sauf sur 36
profils ».

**Pourquoi `amendements` est ABSENT du socle, et non `[]`.** §2.5 du dépôt :
une donnée absente est absente, jamais un `0` mesuré. Une liste vide se
confondrait avec « ce profil n'a déposé aucun amendement » — un fait réel, que
la découpe doit pouvoir continuer d'exprimer. Corollaire assumé : un profil dont
`amendements` vaut réellement `[]` **n'est pas partitionné du tout** (ni
manifeste, ni répertoire) — la partition est un remède au volume, pas une
cérémonie.

### La transition : double lecture, pas migration atomique

Elle **ne peut pas** être atomique. La forme monolithique est committée dans le
dépôt, et la migration des 481 profils est une réécriture de ~600 Mo qui se
décide et se déclenche, pas qui se glisse dans une PR de code. Une PR qui
basculerait code et données d'un coup serait aussi une PR qu'on ne peut pas
relire.

**Donc : tous les lecteurs acceptent les deux formes**, par une porte unique,
`profil_brut.charger_profil_brut(chemin)` — un fichier monolithique est rendu
tel quel, un socle est recomposé depuis ses tranches. **L'écriture, elle, ne
produit plus que la forme partitionnée** : un profil relu puis réécrit migre de
lui-même, sans perdre d'octet. C'est vrai de `merge_raw_dirs` comme de
`generate_all_profiles`, donc **un run de données complet migre le corpus** même
sans le script de migration.

**Le filet qui rend un lecteur oublié visible existait déjà.**
`audit_collecte_vs_publie.py` compare, liste par liste, ce que
`raw_data/profiles` porte et ce que `pivot_data/profiles` publie, et **annule le
commit** dès qu'une liste publiée est en déficit (#545). Il est adapté ici pour
compter les tranches — et **le compte est mesuré, tranche par tranche, jamais
lu au `total` du manifeste** (#576, #579 : un contrôle qui recopie un chiffre
déclaré n'a rien contrôlé). À partir de là, tout lecteur oublié en aval se
déclare de lui-même en CI, avec le slug et les deux comptes. C'est la pièce
maîtresse de la sûreté du lot, plus que n'importe quel test.

**Une partition cassée refuse, elle ne rend jamais une liste vide.** Tranche
annoncée mais absente, compte qui ne tombe pas, schéma de partition inconnu,
nom de fichier qui sortirait du répertoire : `PartitionIllisible`. Le contraire
d'un `get("amendements", [])`, qui republierait un profil amputé sans que rien
ne le dise.

### Les lecteurs et écrivains adaptés

| Fichier | Ce qu'il faisait | Ce qui change |
| --- | --- | --- |
| `src/profil_brut.py` | *(nouveau)* | la porte unique : découpe, recomposition, I/O, énumération |
| `src/generate_all_profiles.py` | lisait/écrivait `<slug>.json` | lit par `charger_profil_brut`, écrit par `ecrire_profil_brut` |
| `src/merge_profile.py` (`merge_raw_dirs`) | fusionnait des `<slug>.json` | idem — **c'est ici que la migration se fait à chaque run** |
| `src/candidate_profile.py` (CLI `--out`) | écrivait `<slug>.json` | écrit socle + tranches ; `--out` reste un chemin de socle |
| `src/amendements_index.py` | chargeait le profil entier pour ses amendements | itère **tranche par tranche** : le pic mémoire tombe de 56 à 23,4 Mo |
| `src/audit_collecte_vs_publie.py` | comptait `amendements` dans le socle | `compter_listes_profil_brut` mesure les tranches |
| `src/audit_volumetrie_profils.py` | `stat()` sur un fichier | poids = socle + tranches ; `rglob` pour l'arbre de travail ; champs mesurés sur le profil recomposé |
| `src/audit_diff_profils.py` | lisait `len(doc["amendements"])` | lit le `total` du manifeste — cet audit compare deux **déclarations**, des deux côtés de la même façon, et le manifeste est vérifié ailleurs |
| `src/purge_mandats_dupliques.py` | lisait et réécrivait le profil entier | lit et réécrit le **socle seul** (les mandats y sont) ; le manifeste est round-trippé tel quel |
| `.github/actions/publish-written-profiles/action.yml` | copiait un fichier par entrée du manifeste | copie le socle **et** son répertoire de tranches |
| `src/scrutins_index.py` | lisait les votes du profil entier | **inchangé** — `votes` est dans le socle ; il y gagne 7,5 Go → ~0,9 |
| `src/audit_collecte_non_publiee.py` | slugs par nom de fichier | **inchangé** — `chemin.is_file()` écarte déjà les répertoires |
| `src/audit_legislature_votes.py` | votes, `glob("*.json")` | **inchangé** — même raison |
| `src/check_quality_gate.py` | `meta.warnings` du raw | **inchangé** (les warnings sont dans le socle) ; **+ §7**, le garde-fou de A |
| `.github/workflows/generate-data.yml` | `find raw_data/profiles -name "*.json" -delete`, `git add raw_data/profiles` | **inchangé** — `find` et `git add` sont récursifs |

### Ce qui reste à faire, et dans quel ordre

La migration des données **n'est pas dans cette PR** — 481 profils réécrits,
c'est un commit de ~600 Mo qui se décide.

1. Fusionner cette PR (code, script, tests, documentation). Le dépôt continue de
   tourner sur la forme monolithique : tous les lecteurs l'acceptent.
2. Constat, sans rien écrire :
   `python3 src/migrer_profils_partitionnes_580.py --profils-dir raw_data/profiles --out-json audit/migration-580.json`
   — noter l'**empreinte de corpus** rendue en fin de rapport.
3. Migration réelle : le même appel avec `--apply`. **L'empreinte de corpus doit
   être identique à celle du run à blanc** : c'est la preuve, en un chiffre, que
   rien du contenu n'a changé. Le script compare, profil par profil, le nombre
   d'amendements, le multi-ensemble des `uid`, et l'égalité stricte du document
   recomposé — avant d'écrire, puis après relecture du disque. À la moindre
   divergence il remet l'octet d'origine et s'arrête.
4. Vérifier la volumétrie :
   `python3 src/check_quality_gate.py --raw-dir raw_data/profiles …` — la §7 doit
   annoncer « aucun fichier au-dessus de 50 Mo ».
5. `git add raw_data/profiles && git commit` — le commit contient 481 socles
   réécrits et ~1 500 tranches créées.
6. **Attendu au `git status` et au prochain contrôle de perte** : les 481 profils
   bruts changent intégralement (JSON compact sur une ligne, #433 — le diff est
   illisible par construction, et l'était déjà). `audit_diff_profils` n'est
   lancé en CI que sur `pivot_data`, qui ne bouge pas : aucun faux positif à
   déclarer, et **`allow_declared_losses` n'a pas à être armé**.

---

