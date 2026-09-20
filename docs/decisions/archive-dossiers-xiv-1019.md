<a id="archive-dossiers-xiv-1019"></a>
# La XIVe législature n'était pas inexploitable, elle était monolithique (#1019) (2026-09-18)

`2026-09-18`

> **En bref** — `couverture_dossiers.py` écrivait que l'archive XIV a « une
> structure incompatible […], aucun `dossierParlementaire` ». **Elle en porte
> 3 432**, chacun sous cette clé exactement comme dans le format par fichier :
> seul l'EMBALLAGE change. `parse_dossier_gouvernemental` les traite sans une
> exception et rend **573 dossiers d'origine gouvernementale** avec un seul
> warning. La borne de couverture recule du 21/06/2017 au **20/06/2012**, et
> quatre fiches de gouvernement cessent d'être vides.

## Contexte

Demande de la propriétaire, relayée par la session « UI gouv » le 18/09/2026 :
sept fiches de gouvernement sur dix-sept publiaient `textes: []`. Le point de
départ était une phrase de notre propre code, tenue pour acquise depuis #399.

**Elle était fausse sur son point décisif.** Mesuré sur l'archive téléchargée le
18/09 (2,5 Mo, 36 Mo décompressés, un seul fichier) :

| | |
| --- | ---: |
| `export.dossiersLegislatifs.dossier[]` | **3 432** |
| … chacun sous la clé `dossierParlementaire` | oui |
| `export.textesLegislatifs.document[]` | 7 120 |
| `parse_dossier_gouvernemental` — exceptions | **0** |
| … dossiers d'origine gouvernementale | **573** |
| … warnings | **1** |
| … `fam_code` inconnus | **0** |

Aucune seconde table de statuts n'est nécessaire : la nomenclature de la XIV est
celle des suivantes.

Les XIIe et XIIIe, elles, répondent **404**, revérifié le 18/09. Les
gouvernements Fillon I, II et III restent donc hors couverture — une absence de
source, déclarée et non comblée.

## Décision

**Lire la XIV, par un second mode de lecture, détecté sur la FORME de l'archive
et jamais sur son numéro de législature.**

1. `_entrees_monolithiques(chemin, cle_racine)` rend `{uid: objet}` quand le zip
   ne contient qu'un `.json` ; `{}` sinon, ce qui rebranche le format par
   fichier. Une archive future de l'un ou l'autre format est lue sans qu'on
   revienne ici.
2. **`_COLLECTIONS_MONOLITHE` encode l'asymétrie d'emballage**, seule subtilité
   du format : un dossier est `{"dossierParlementaire": {…}}`, un document est
   l'objet **nu**. Inverser les deux fait tomber 5 tests.
3. L'arbitrage des doublons ne change pas : il porte sur l'uid, et la
   législature la plus haute gagne. Ce n'est pas théorique — **30 uids de la XIV
   figurent aussi dans les XV-XVII**, et sans cet arbitrage on republierait un
   état périmé.
4. `LEGISLATURES_DEBUT[14] = "2012-06-20"`, **relu dans l'organe `ASSEMBLEE` de
   la 14e législature d'AMO30** et non de mémoire. La même lecture confirme les
   trois dates déjà en table, au jour près.
5. La 14 naît dans `AN_DOSSIERS_LEGISLATURES_FIGEES` : dissoute depuis 2017,
   son archive ne changera plus, un run n'a pas à la rafraîchir (#762).

## Ce que ça change, mesuré

| | Avant | Après |
| --- | ---: | ---: |
| Dossiers lus, toutes archives | 10 764 | **14 166** |
| … uids distincts | 10 764 | **14 166** (aucun doublon) |
| … d'origine gouvernementale | 728 | **1 301** (+573) |
| Borne de couverture | 2017-06-21 | **2012-06-20** |
| Libellé | XV–XVII | **XIV–XVII** |

La XIV n'apporte que 3 402 des 3 432 dossiers : les 30 doublons sont allés aux
archives plus récentes, comme la règle l'exige. Les comptes des XV, XVI et XVII
sont inchangés (4 880 / 2 750 / 3 134) — le second mode n'a rien perturbé.

Rendement par fiche : **Ayrault II 187, Valls II 254, Cazeneuve 81, Valls 44,
Philippe I 7**.

## Ayrault I reste vide, et ce n'est PAS un zéro mesuré

Sa fenêtre (16/05 → 18/06/2012) se termine **avant** l'ouverture de la XIV :
elle relève de la XIIIe, dont l'archive répond 404. `statut_couverture_textes`
le classe `hors_couverture`, et son `textes: []` ne doit jamais se lire comme
« aucun texte porté » (§2 règle 5).

Un premier jet de cette décision affirmait l'inverse — « zéro mesuré, pas zéro
faute de source ». C'était l'erreur exacte que `couverture_dossiers.py` existe
pour empêcher, et c'est le calcul du statut, pas la relecture, qui l'a prise.

Fillon I, II et III sont dans le même cas, et définitivement.

## Trois caches invalidés d'avance

Ajouter une archive change ce que trois index **contiennent**, donc leurs clés :

- `index_acteur_textes_v4` → **`_v5`** (`candidate_profile`) ;
- `index_texte_dossier_v1` → **`_v2`** (`textes_dossiers_an`) ;
- `index_dossier_commission_v1` → **`_v2`** (`commissions_dossiers_an`).

Ce n'est pas de la prudence gratuite : **on vient de le payer le matin même**.
Le correctif de stade de #997 a été publié et n'a rien changé pendant un run
entier, parce que `.cache/dossiers_an` est restauré d'une semaine sur l'autre
par les `restore-keys` du workflow et que l'index était relu tel quel
(→ [`cle-index-textes-portes-997`](cle-index-textes-portes-997.md)).

## Alternative rejetée

**Convertir l'archive XIV au format par fichier à l'ingestion**, pour n'avoir
qu'un seul mode de lecture. Rejeté : il faudrait écrire 3 432 fichiers sur
disque à chaque run, ou committer une archive dérivée que plus rien ne relie à
sa source. Le second mode coûte une fonction de trente lignes et laisse la
source intacte.

**Charger l'archive par morceaux pour éviter les 36 Mo en mémoire.** Rejeté :
sans nom de fichier, l'uid ne se lit que dans l'objet, donc il faut désérialiser
pour savoir ce que l'archive contient. 36 Mo pour une archive est borné et
mesuré, loin des « plusieurs centaines de Mo » que `_uid_depuis_nom` évite sur
les trois archives par fichier (#377, #392).
