# La qualification d'un scrutin et la clé de son dossier étaient lues puis jetées (#639, rangs 1 et 2)

`2026-08-31`

> **En bref** — `typeVote` est renseigné sur 18 311 / 18 311 scrutins bruts et `dossiers_legislatifs[].id` sur 472 / 472 entrées, tous deux jetés à la projection : les 66 motions de censure étaient publiées `vote_texte` comme les 17 682 autres, et l'invariant §5 qui exige leur `texte_lie_id` était vacuement satisfait ; il devient exigible et n'est pas satisfiable (0 / 18 311 référence législative sur un scrutin AN), donc la clé absente est **déclarée** (`texte_lie_non_resolu.motif`) plutôt qu'inventée ou tue, et un cache de scrutins non qualifié — index figé committé compris — est refusé au lieu d'être relu.

*31/08/2026 — issue #639, rangs 1 et 2. Les rangs 3 (index d'amendements) et 4
(lien inverse dossier → scrutin) ne sont pas traités ici.*

## Contexte

Deux champs sourcés, déjà collectés, disparaissaient à la projection.

| Champ source | Où il est lu | Où il disparaissait | Couverture à la source |
| --- | --- | --- | ---: |
| `typeVote.codeTypeVote`, `demandeur.texte` | archives `…/loi/scrutins/` | `_parse_scrutins_zip`, projection à cinq champs | 18 311 / 18 311 · 18 226 / 18 311 |
| `dossiers_legislatifs[].id` (`DLR5L15N37607`) | profil brut | `_normalize_texte_porte`, dict de huit clés | 472 / 472 |

Conséquence mesurée sur `pivot_data/scrutins.json` (17 748 scrutins publiés) :
`type_vote` valait `vote_texte` sur les 17 748 et `type_scrutin` était `null`
sur les 17 748. **Les 66 motions de censure étaient donc publiées sous le même
type que les votes sur un texte**, et l'invariant d'`AGENTS.md` §5 — un
`type_vote == "motion_censure"` doit porter son `texte_lie_id` — était
vacuement satisfait : la valeur que le schéma attend n'était portée par aucune
donnée. Les retrouver demandait de chercher « censure » dans un libellé, une
heuristique là où la source donne un code fermé.

Côté textes portés, `dossier_id` était publié `null` — mais surtout **absent** :
la seule clé sourcée rattachant un texte porté à autre chose qu'un libellé était
jetée, alors que les fiches de gouvernement publient déjà le même identifiant
sous le même nom.

## Décision

**1. `codeTypeVote` devient `type_scrutin` (image 1:1) et `type_vote` (la seule
distinction dont les règles éditoriales ont besoin).**

| `codeTypeVote` | `type_scrutin` | `type_vote` | Publiés |
| --- | --- | --- | ---: |
| `SPO` scrutin public ordinaire | `public_ordinaire` | `vote_texte` | 17 312 |
| `SPS` scrutin public solennel | `solennel` | `vote_texte` | 361 |
| `MOC` motion de censure | `motion_censure` | `motion_censure` | 66 |
| `SAT` scrutin à la tribune | `tribune` | `vote_texte` | 9 |
| absent ou inconnu | `null` | `null` | 0 |

`KNOWN_TYPES_SCRUTIN` gagne `tribune` et `motion_censure` — on étend le
frozenset, on ne le contourne pas (`AGENTS.md` §4). `SSG` (Congrès) n'entre pas
dans la table : sa seule occurrence porte un uid `VTCGR…` et est écartée en
amont ; l'y inscrire serait du code mort laissant croire que le Congrès est
publié. La table est **fermée et sans défaut** : un code inconnu ne tombe pas
dans `SPO`, qui est pourtant 97,5 % des scrutins publiés — 17 312 / 17 748 (§2 règle 5).

`demandeur` (« Président du groupe … », « Conférence des présidents ») est
conservé tel quel : 17 664 renseignés sur les 17 748 publiés.

**2. Une motion de censure sans texte lié publie la déclaration de cette
absence, jamais une clé inventée.**

Qualifier les 66 motions rend l'invariant §5 exigible — et il n'est pas
satisfiable. Le scrutin AN ne porte **aucune** référence législative :
`objet.referenceLegislative` et `demandeur.referenceLegislative` sont nuls sur
**0 / 18 311** scrutins bruts des quatre législatures (relevé du 31/08/2026 sur
les archives réelles ; l'investigation de l'issue n'avait pu le vérifier que sur
la XIV). Et une partie des motions n'a **aucun texte à lier** : une motion de
l'article 49 alinéa 2 est spontanée, sans 49.3 en regard.

On applique donc le patron `*_non_resolu` déjà écrit du dépôt (`AGENTS.md` §5,
amendements sans uid AN) : `texte_lie_id: null` **plus** un
`texte_lie_non_resolu.motif` qui nomme la limite de la source.
`validate_scrutins_index` accepte la clé nulle **si et seulement si** la
déclaration est là — une motion muette reste une erreur de schéma. Ce n'est pas
un assouplissement de la règle 4 : la motion reste un fait procédural distinct,
et aucune position n'est dérivée d'un type.

**3. `textes_portes[].dossier_id` recopie `dossiers_legislatifs[].id`**, sous le
nom que `schema_gouvernement.REQUIRED_TEXTE_KEYS` porte déjà. Deux noms pour un
même identifiant obligeraient tout croisement à retomber sur le libellé, ce que
l'issue mesure comme impraticable (13 libellés communs aux trois matières, tous
budgétaires).

**4. Un cache de scrutins non qualifié est refusé, jamais relu.** « Un
répertoire qui existe n'est pas la preuve de ce qu'il contient » (`AGENTS.md`
§5) : `_scrutins_store_qualifie` refuse un store écrit sous l'ancienne
projection, côté cache disque **et** côté index figé committé. Le test porte sur
la **clé**, pas sur sa valeur — `type_scrutin` peut légitimement valoir `None`.

## Ce que le lot ne règle pas

- **Il ne constitue pas l'univers « votes sur l'ensemble d'un texte ».** `SPO`
  couvre indifféremment un vote sur un article, un amendement ou un texte
  entier : `vote_texte` reste un type grossier. La méthodologie publiée affirme
  que « les votes sur des articles ou amendements sont exclus de cette
  synthèse » — le corpus ne porte toujours aucune distinction permettant de
  constituer cet univers. Corriger cette phrase, ou constituer l'univers, reste
  entier.
- **Il ne rattache aucun scrutin à son dossier.** `texte_lie_id` reste `null`
  sur les 17 748.
- **Il ne dit pas quelles motions relèvent de l'alinéa 2 et lesquelles de
  l'alinéa 3.** Le partage se lit dans le libellé (22 / 44 sur les 66) et un
  libellé n'est pas une source (§2 règle 2).

## Régénération exigée

`raw_data/scrutins_an_figes/{14,15,16}` porte la projection à cinq champs.
`_load_frozen_scrutins_index` **refuse** désormais ces index et retélécharge
l'archive : tant que les trois n'ont pas été régénérés par
`python3 src/build_scrutins_index_figes.py --toutes`, chaque run paie 20,0 Mo de
téléchargement supplémentaire, et la qualification des 9 314 scrutins publiés
des législatures 14-16 attend la prochaine collecte complète des profils qui les
portent.

Le refus est délibéré. L'accepter en avertissant aurait laissé 43 des 66 motions
de censure étiquetées `vote_texte` — un fait faux — jusqu'à ce que quelqu'un
pense à relancer le script. Le coût du refus est borné et transitoire ; celui de
l'acceptation ne l'était pas.

**Rien n'est publié tant que les profils ne sont pas régénérés** : la
qualification transite par `raw_data/profiles/*.json`, et la fusion additive de
`merge_scrutins_index` conserve la valeur déjà publiée quand la nouvelle est
`null`. Un corpus à moitié régénéré ne porte donc jamais de fait faux, seulement
une qualification incomplète.

## Effet sur les contrôles

| Contrôle | Effet | Vérifié |
| --- | --- | --- |
| `audit_diff_profils` (index scrutins) | aucun : il compare la **longueur** de `scrutins[]` et deux scalaires | rejoué sur les 17 748 entrées réelles, avant/après : `bloquant: False`, 0 perte, 0 régression scalaire |
| `audit_diff_profils` (profils) | aucun : `textes_portes` garde sa longueur | rejoué sur les 283 entrées d'`edouard-philippe` |
| `audit_integrite_referentielle` | aucun : `dossier_id` et `texte_lie_id` ne sont dans aucun `Renvoi`, et il n'existe pas d'index de dossiers | lecture de `RENVOIS` |
| `audit_collecte_vs_publie` | aucun : `RELATIONS` somme des **longueurs** | — |
| Volume | `pivot_data/scrutins.json` 8,65 → ~10,2 Mo (+1,52 Mo mesuré, +20 Ko de déclarations) | loin du seuil d'alerte de 50 Mio de `garde_fou_blobs` |

## Alternatives écartées

**Ne publier la qualification que dans `type_scrutin`, laisser `type_vote` à
`vote_texte`.** Aurait évité de toucher à l'invariant §5 — au prix de publier,
sur le même scrutin, `type_scrutin: "motion_censure"` et `type_vote:
"vote_texte"`. Une contradiction visible vaut moins qu'une déclaration
explicite.

**Assouplir l'invariant §5 en le retirant.** Rejeté : l'exigence a un objet réel
— une motion ne doit jamais se lire comme une position sur le texte. Ce qui
manquait n'était pas la règle, c'était la forme « clé absente mais déclarée »,
que le dépôt écrit déjà ailleurs.

**Déduire le type depuis le libellé.** La reconnaissance par expression
régulière atteint 99,4 % sur l'intitulé. C'est une mesure de faisabilité, pas
une source (§2 règle 2) — et elle est ici inutile, la source donnant un code
fermé.

**Accepter les index figés en avertissant.** Voir ci-dessus.

## Un constat de mesure, hors périmètre

`objet.dossierLegislatif.dossierRef` — un `DLR…` sourcé, directement sur le
scrutin — est renseigné sur **2 608 / 8 434** scrutins bruts de la 17e
législature (30,9 %, 75 dossiers distincts), et **jamais renseigné sur les
législatures 14, 15 et 16** (0 / 9 876 ; la clé n'y figure même pas). L'investigation de l'issue n'avait examiné que
`objet.referenceLegislative` et concluait à 715 / 17 748 rattachements par lien
inverse. Le rang 4 est donc à réordonner : 2 608 rattachements **directs** sont
disponibles sur la législature en cours, sans parcourir l'arbre des dossiers.
Non implémenté ici — `texte_lie_id` change alors de sémantique et cela mérite sa
propre décision.

## Fait au passage

`_normalize_texte_porte` lisait `url_source`/`url_institution` pour composer
`source_url`, alors que la collecte AN écrit `source_url` depuis #400 : 468 des
472 entrées brutes portent cette clé, **aucune** ne porte les deux autres. Les
472 textes portés publiés étaient donc sans source primaire — un fait publié
sans sa source (§2 règle 2), dans la fonction même que le rang 2 modifie. Les
deux clés héritées de NosDéputés restent lues, elles vivent encore dans des
entrées collectées avant #529.
