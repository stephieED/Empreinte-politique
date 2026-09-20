<a id="point-de-sauvegarde-dans-les-profils-518"></a>
# Un fichier de progression dans un répertoire de données (#518, troisième incident) (2026-08-24)

`2026-08-24`

> **En bref** — `Path.glob` rend les dotfiles : tout inventaire de `raw_data/profiles/` saute les noms commençant par un point.

**Le garde-fou « collecté mais non publié » n'a jamais rien laissé passer : il
n'a jamais eu l'occasion de passer. Depuis sa mise en service, il bloque sur un
fichier qui n'est pas un profil.**

## 1. Ce qui s'est passé

Run [`32773067295`](https://github.com/stephieED/Empreinte-politique-src/actions/runs/32773067295)
(24/08/2026 20:17), le premier après la fusion de #520. **22 jobs verts** — les
correctifs (a) à (d) ont tenu : les 8 shards roster passent, et le step
`Générer les profils de groupe parlementaire réel`, qui avait tué le run
précédent, est vert.

`merge-and-pivot` est tombé au step **26**, `Collecté mais non publié (avant
commit)` (#511), en **0 seconde**. `Committer et pousser` et le déploiement
skippés.

Et cette fois l'annotation de #519 a nommé le coupable, ce qui a réduit le
diagnostic à une lecture :

```
::error::COLLECTE_NON_PUBLIEE — 1 profil(s) collecté(s) sur 477 ne sont
publiés nulle part (seuil : 0). Slug(s) : .generation_checkpoint
```

**`.generation_checkpoint` n'est pas un profil.** C'est
`raw_data/profiles/.generation_checkpoint.json`, le point de sauvegarde de
`generate_all_profiles.py` (`DEFAULT_CHECKPOINT_PATH`) : un fichier de
**progression**, écrit **dans le répertoire des données**. `_slugs()` inventorie
ce répertoire par nom de fichier, y a lu un brut, n'a trouvé aucun pivot, et a
annulé le commit de 476 profils parfaitement collectés **et publiés**.

Reproduit à l'identique hors CI, message compris.

## 2. Pourquoi maintenant, et pourquoi ce n'était pas visible

Ce n'était pas « maintenant » : **aucun run n'a abouti depuis la mise en service
du contrôle**. Le dernier `success` de `generate-data.yml` est
[`32405297873`](https://github.com/stephieED/Empreinte-politique-src/actions/runs/32405297873)
(20/08), c'est-à-dire l'incident *fondateur* de #511, antérieur au contrôle. Les
runs suivants sont morts avant d'y arriver — sur le roster (#516), sur les
shards (#518), sur les fiches de groupe (#518 second incident) — sauf deux, le
`32738726729` (24/08 14:26) et celui-ci, tombés **au même step**. Le premier ne
laissait que le message constant, qui ne nomme personne ; #519 est ce qui a
rendu le second lisible.

Le fichier est `gitignore`d, donc invisible dans le dépôt ; il est écrit sur le
runner par les deux passes `--pivot-only` de `merge-and-pivot`, **juste avant**
le contrôle. `_save_checkpoint` n'est pas conditionné à `--resume` : une passe
qui ne reprendra jamais rien l'écrit quand même, 477 fois de suite.

## 3. Ce qui est corrigé, et à deux niveaux

**La cause** — `--no-checkpoint` sur les deux passes `--pivot-only` de
`merge-and-pivot` (et de `scripts/generate_data_local.sh`, qui doit rester le
miroir de la CI). Aucune des deux ne porte `--resume` : le fichier n'y avait
aucun usage. Les shards `extract-roster-groupes`, eux, gardent leur point de
reprise — c'est leur seule protection contre une préemption — et leur checkpoint
ne quitte jamais le runner : l'artifact est rempli depuis le manifeste (#450),
pas depuis le répertoire.

**Le symptôme** — `_slugs()` écarte les fichiers dont le nom commence par un
point. Ce n'est pas une exception nommée : `slugify()` ne produit que
`[a-z0-9-]` puis `.strip("-")`, donc **aucun slug ne peut commencer par un
point**. Le filtre découle d'une propriété du générateur de noms, et non d'une
liste à tenir à jour — c'est ce qui le rend sûr, et ce qui le rend durable.

**Et ce n'est pas une invention : c'est une convention du dépôt que le contrôle
de #511 n'avait pas reprise.** Quatre inventaires du même répertoire portent
déjà `if …name.startswith("."): continue` — `merge_profile.merge_raw_dirs`,
`scrutins_index`, `amendements_index`, `audit_legislature_votes`. La raison est
la même partout : `Path.glob("*.json")` **remonte les fichiers cachés**,
contrairement au module `glob` (vérifié — il rend bien
`.generation_checkpoint.json`). Deux ne l'avaient pas non plus, alignés ici, et
sans conséquence connue : `audit_volumetrie_profils` comptait le fichier comme
un profil dans ses volumétries (une mesure fausse reste fausse, règle 5) et
`purge_mandats_dupliques` le rangeait parmi ses « ignorés sans acteur ».

Les deux niveaux, et pas l'un ou l'autre. Corriger la seule cause laisserait le
contrôle prêt à retomber sur le prochain fichier de service ; corriger le seul
symptôme laisserait un fichier de progression dans un répertoire de données, où
chaque nouvel inventaire devra se souvenir de l'écarter.

**Aucune tolérance ajoutée** : le seuil reste 0, `allow_unpublished_profiles`
reste à `false`. Un profil non publié bloque toujours le commit. Ce qui change
est la population inventoriée, pas le verdict.

## 4. Alternative écartée : déplacer le point de sauvegarde

Le sortir de `raw_data/profiles/` traiterait les six inventaires d'un coup.
Écarté ici pour la destination, pas pour le principe : `.cache/` est restauré
par `actions/cache` d'un run à l'autre, et un checkpoint **survivant au run**
ferait sauter à `--resume` des candidats qu'il croirait traités — un roster
entier sauté en silence, c'est-à-dire la classe de défaut de #511, réintroduite
par le correctif. Un chemin neutre et jamais caché reste à choisir ; noté en
ROADMAP plutôt que décidé dans un correctif d'incident.

## 5. La seconde panne du même push : `Tests (pytest)` rouge sur `main`

Run [`32773016491`](https://github.com/stephieED/Empreinte-politique-src/actions/runs/32773016491).
`tests/test_ci_roster_unique_par_run.py::test_le_roster_brut_n_est_pas_committe`
lit `.gitignore`, **absent du sparse-checkout** de `tests.yml` : suite verte en
local (2 109 tests), `FileNotFoundError` en CI. Reproduit en clonant avec la
même liste blanche.

C'est le piège que le commentaire de cette liste annonce lui-même, et sa
**seconde** occurrence après #434. Ce qui manquait n'était pas l'avertissement,
c'était un échec **local**. `tests/test_ci_perimetre_sparse_checkout.py` relève
désormais les littéraux de chemin ancrés à la racine dans toute la suite et
vérifie que chacun est couvert — et vérifie l'autre sens, que `pivot_data/` et
`raw_data/profiles/` n'y entrent jamais (#473). Vérifié par mutation.

