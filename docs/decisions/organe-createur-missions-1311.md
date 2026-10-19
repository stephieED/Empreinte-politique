# Une mission d'information dit quel organe l'a créée (#1311)

`2026-10-19`

> **En bref** — un mandat `mission_information` ne disait pas quelle commission ou délégation avait créé la mission, alors qu'AMO30 le publie (`organeParent`) et que `_build_organe_index` lisait déjà le fichier sans le garder. Chaque mission collectée à l'Assemblée porte désormais `organe_createur` (`{organe_ref, nom, sigle, type}`), ou `null` avec un motif fermé qui distingue « la source n'en nomme pas » de « nommé mais introuvable ». Reporté sur les missions déjà publiées, aux deux étages. Mesuré sur 196 missions débutées depuis le 22/06/2022 : 185 résolues, 11 sans parent à la source.

## Contexte

L'instantané sur la commission des affaires culturelles et de l'éducation
(#1309) a besoin de savoir quelles missions d'information cette commission a
créées. Sur `public/main` (19/10/2026), une mission publiée portait `label`,
`fonction`/`type`, `debut`, `fin`, `actif`, `categorie_source` — ni l'uid de
l'organe mission, ni son parent. Aucun module de `src/` ne lisait
`organeParent`.

La source, elle, le dit : `organe.organeParent` est l'uid de l'organe créateur
dans `json/organe/POxxxx.json`. Sur toute l'archive, il vaut une chaîne ou
`null`, jamais un marqueur `xsi:nil` ni une liste.

Mesuré le 19/10/2026 sur l'archive AMO30 du jour, **en appliquant le code du
lot** (`resoudre_organe_createur`), population = **organes** `MISINFO` /
`MISINFOCOM` / `MISINFOPRE` distincts débutés depuis le 22/06/2022 — des
missions, pas des mandats de députés :

| Constat | Missions |
| --- | ---: |
| total | 196 |
| organe créateur résolu | 185 — `COMPER` 149, `DELEG` 36 |
| `source_sans_organe_createur` | 11 — 6 `MISINFOCOM`, 5 `MISINFOPRE` |
| `organe_createur_introuvable` | 0 |
| créées par la commission des affaires culturelles et de l'éducation | 14 (9 XVIe, 5 XVIIe) |

## Décision

1. **L'index des organes garde `parent`** (`organeParent` verbatim) pour tous
   les organes, et **change de nom** : `index_organes_v2.json` →
   `index_organes_v3.json`. Le cache GitHub Actions restaure le répertoire
   `.cache/acteurs_historique_an` entier ; un `v2` relu comme s'il portait le
   champ ferait de chaque mission une mission « sans organe créateur », un faux
   constat. Le `path:` du cache n'est pas touché, donc le workflow non plus. Les
   deux autres lecteurs du fichier (`reprise_mandats_gouvernementaux`,
   `commissions_dossiers_an`) suivent le nom.
2. **Le champ `organe_createur`**, sur les seules `mission_information` que
   `_extract_mandats_officiels` produit : `{organe_ref, nom, sigle, type}`,
   `type` étant le `codeType` de la source, non traduit. Recopié au pivot par
   `_normalize_mandat`. **Aucune autre catégorie** ne porte la clé, même quand
   AMO leur donne un parent (commissions d'enquête, groupes d'études…) : hors
   périmètre de l'issue.
3. **`null` porte toujours `organe_createur_non_resolu.motif`**
   (`KNOWN_MOTIFS_ORGANE_CREATEUR_NON_RESOLU`) :
   `source_sans_organe_createur` — la source ne nomme aucun parent, un fait,
   rien à réparer ; `organe_createur_introuvable` — un parent est nommé et le
   référentiel ne le résout pas, le motif porte l'`organe_ref`. **Une mission
   commune n'est jamais attribuée à l'une des commissions qui la composent** :
   la source ne le dit pas.
4. **La clé est facultative** : son absence dit « collectée avant #1311 et
   jamais recollectée depuis ». `validate_profil()` vérifie la forme quand la
   clé est là, et refuse un motif sans clé, une clé sur une autre catégorie,
   un `null` sans motif connu, un organe résolu accompagné d'un motif.
5. **La fusion n'apporte pas le champ seule** — mesuré sur les cinq missions
   de `jean-luc-melenchon` publiées sur `public/main` : `_mandat_key` et
   `_pivot_mandat_key` ne le contiennent pas, l'entrée ancienne gagne, et
   aucune ne le reçoit. D'où le report nommé `backfill_mandat_organe_createur`,
   câblé **aux deux étages** (brut et pivot) : il pose la clé (motif compris)
   sur une mission qui ne l'a pas, remplace un `null` par un organe résolu, et
   **ne remplace jamais un organe résolu par `null`**. La clé de fusion n'est
   pas touchée (défaut de #668). Le test de transition part du bloc `mandats`
   réel des deux couches, copié dans
   `tests/fixtures/jean_luc_melenchon_mandats_1311.json`, et échoue quand le
   report est neutralisé.

## Alternative écartée

**Publier l'uid du parent seul** (`organe_parent: "PO59046"`), à résoudre côté
interface. Écarté : l'interface ne lit que `pivot_data/`, qui ne publie pas le
référentiel des organes ; l'uid serait un identifiant sans nom pour le lecteur,
et la résolution se ferait loin de la source qui la garantit.

**Ajouter le champ à la clé de fusion.** Écarté pour la raison de #668 : la
mission déjà publiée et la mission recollectée ne partageraient plus de clé, et
chaque mission serait publiée deux fois.

## Non vérifié

- Le comportement sur le corpus entier : la transition est testée sur un
  profil réel (cinq missions, deux cas), pas sur les profils de roster. Le
  décompte de la vérification attendue par l'issue — les mandats
  `mission_information` de `public/main` par organe créateur — ne peut se faire
  qu'après un run.
- Une mission publiée hors de `_extract_mandats_officiels` (héritage d'une
  source retirée, entrée que l'AN ne sert plus) restera sans clé : aucun run ne
  la recollecte. Leur nombre n'est pas mesuré ici.
