<a id="dossiers-multi-archives-origine-document"></a>
# Dossiers législatifs : ingestion multi-archives, origine par document déposé, statut `promulgue` (#400) (2026-08-18)

`2026-08-18`

> **En bref** — ingestion multi-archives des dossiers, origine déterminée par document déposé, statut `promulgue` ajouté.

**Contexte** : `gouvernement_textes.py` ne lisait qu'une archive, celle de la
XVII législature. Elle est multi-législature mais ne garde des précédentes
qu'une **traîne résiduelle** : aucun projet de loi antérieur à la XVI. Les
gouvernements Borne, Castex et Philippe I/II étaient donc à zéro texte.

## Inventaire des archives

Deux conventions de nommage coexistent chez l'AN — c'est ce qui rend
l'inventaire non évident, et ce qui m'avait fait conclure à tort dans une
première version de #400 que seules les XVI/XVII existaient.

| Législature | Nom de fichier | Taille | Exploitable |
| --- | --- | --- | --- |
| 12, 13 | *(aucune des deux formes)* | — | non, 404 |
| 14 | `Dossiers_Legislatifs_XIV.json.zip` | 2,5 Mo | **non** |
| 15 | `Dossiers_Legislatifs_XV.json.zip` | 15,2 Mo | oui |
| 16 | `Dossiers_Legislatifs.json.zip` | 9,1 Mo | oui |
| 17 | `Dossiers_Legislatifs.json.zip` | 10,25 Mo | oui |

Le listing de répertoire est désactivé (404 même sur les chemins valides) :
l'inventaire ne peut pas être découvert dynamiquement et doit être tenu à jour
dans `AN_DOSSIERS_ARCHIVES`.

**La XIV est inexploitable** : changement d'architecture du jeu de données AN
entre la XIV et la XV (déjà constaté côté amendements). Son archive contient
un JSON monolithique de 36 Mo décompressés, structuré en
`export.textesLegislatifs.document[]` — 7120 `document`, **aucun
`dossierParlementaire`**. Fillon II/III (XIII) sont hors d'atteinte
définitivement.

## Origine : le document déposé, pas le titre

Le signal historique était le préfixe de `titreDossier.titre` (spike #207). Il
ne fonctionne que sur les XVI/XVII : **sur la XV les titres sont descriptifs**
(« Taxe sur les services numériques », « Démocratie plus représentative,
responsable, efficace ») et le filtre y retenait **zéro** projet de loi déposé
entre 2017 et 2019.

Le signal retenu est le **type du document réellement déposé** — préfixe de
l'uid du `texteAssocie` de l'acte `*-DEPOT` le plus ancien : `PRJL` (projet de
loi), `PION` (proposition), `PNRE` (résolution, hors champ). Sur le corpus
complet, le filtre par titre ne voyait que **271 des 726** dossiers
gouvernementaux.

`procedureParlementaire.code` sert de repli quand aucun document n'est
résolvable, et **seulement pour les codes univoques** : les codes 5 et 7
(« Projet **ou** proposition de loi organique/constitutionnelle ») en sont
exclus, car deviner violerait §2.5.

Le document **prime sur la procédure** quand les deux divergent : 8 dossiers de
règlement du budget sont typés « Proposition de loi ordinaire » à la source
alors que le document déposé est bien un `PRJL`. Le type du texte réellement
déposé fait foi.

## Déduplication inter-archives

Un dossier figure dans plusieurs archives. L'arbitrage se fait **par uid, la
législature la plus élevée l'emportant** : elle porte l'état le plus à jour des
`actesLegislatifs`, donc du statut — un texte « en navette » dans la XVI peut
être « adopté » dans la XVII.

Deux points d'implémentation non évidents :

- **Le nom de fichier dans le zip porte l'uid** (vérifié sans exception sur les
  10 967 dossiers). L'arbitrage se fait donc sur les seuls `namelist()`, sans
  rien désérialiser. Charger les trois archives en mémoire pour comparer
  coûterait plusieurs centaines de Mo, sur un pipeline qui a déjà connu deux
  OOM (#377, #392). `iter_dossiers_bruts` est un générateur : un seul dossier
  vivant à la fois.
- **L'arbitrage utilise `max()` explicite**, pas l'écrasement dans l'ordre de
  parcours. Ma première version dépendait de l'ordre d'appel — un test
  vérifiant l'invariance à l'ordre l'a attrapée.

## Statut `promulgue`

L'ingestion des archives anciennes a fait remonter **62 textes marqués
`navette_en_cours` et 3 marqués `rejete` qui portaient un acte de promulgation**
(`PROM`/`PROM-PUB`, publication au Journal officiel). Exemple : la convention
sur les infractions à bord des aéronefs, dernière décision de séance
« modifié » au Sénat le 2021-01-28, **promulguée le 2021-02-03** — publier
« en navette » en 2026 serait faux.

Décision (arbitrage humain, comme pour `adopte_cmp` en #397) : **statut dédié
`promulgue`**, appliqué comme correctif ciblé.

Il ne remplace **jamais** `adopte_cmp` ni `adopte_49_3` : ces statuts portent
la voie procédurale suivie, que `promulgue` ne dit pas. Les écraser ferait
disparaître le fait CMP ou 49.3 de 116 textes — exactement le collapse
qu'interdit §2.4. `retire` n'est pas écrasé non plus : retrait puis
promulgation est contradictoire, et trancher n'est pas notre rôle. Le warning
d'un `fam_code` non mappé est conservé même quand la promulgation détermine le
statut : le code reste inconnu et mérite d'être signalé.

## Résultat mesuré

| Gouvernement | Avant #400 | Après |
| --- | --- | --- |
| PHILIPPE_2 | 0 | **282** |
| CASTEX | 0 | **195** |
| BORNE | 0 | **110** |
| LECORNU_II | 60 | 63 |
| BAYROU | 26 | 35 |
| ATTAL | 8 | 24 |
| BARNIER | 10 | 13 |
| PHILIPPE | 0 | 1 |
| FILLON_2 / FILLON_3 | 0 | 0 (hors couverture définitive) |
| **Total** | **104** | **723** |

Sur les profils individuels — le gain le plus large, car la même archive
alimente `candidate_profile.py` (lignes 1945 et 2108) : index acteur→textes
portés de **1 076 → 1 643 acteurs** et **8 351 → 24 333 associations** (×2,9).

**Budget CI** : cache 14 → 46 Mo, index construit en 2,3 s pour **55 Mo de RSS**
— sans risque d'OOM grâce au générateur.

**Invalidation des index** : `index_texte_titre.json` et
`index_acteur_textes.json` sont renommés en `*_v2.json`. Sans nouveau nom, un
cache CI ou local existant aurait servi silencieusement l'ancien index
mono-archive, et le gain aurait été invisible sans que rien ne le signale.

**Reste à traiter** : 3 `fam_code` apparaissent dans les archives anciennes et
ne sont pas mappés — `TSORTF02` (« adoptée avec modifications », 53),
`TSORTF14` (« voté par les deux assemblées en termes identiques »), `TSORTF13`
(« rejeté définitivement »). Ils ne coûtent que 2 exclusions, la promulgation
déterminant le statut des autres. Même nature que #397.
*Traité en #402 — voir [la section dédiée](gouvernement-textes-fam-codes-archives.md) :
les 3 codes sont mappés, `TSORTF02` tranché sur données réelles.*

---

