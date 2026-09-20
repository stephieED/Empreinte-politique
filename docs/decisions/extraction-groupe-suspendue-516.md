<a id="extraction-groupe-suspendue-516"></a>
# Suspendre l'extraction des deux groupes Sénat, sans les retirer de la config (#516) (2026-08-24)

`2026-08-24`

> **En bref** — le bloc exige `depuis`, `motif`, `references`, `condition_reprise`.

**Décision temporaire, réversible d'une ligne, et datée.** Elle ne tranche pas
la question éditoriale du maintien des groupes Sénat — elle débloque le
pipeline pendant qu'elle reste ouverte.

## Ce qu'on répare

Les deux derniers runs de **Génération des données** ont échoué au même
endroit :

| Run | Date | Shards roster | Étape en échec |
| --- | --- | --- | --- |
| `32463926808` | 21/08/2026 | 6 échecs / 8 | `Construction de la liste roster-driven` |
| `32548486495` | 22/08/2026 | 8 échecs / 8 | idem, puis `Normalisation pivot roster-driven` |

L'étape est `python3 src/generate_roster_candidats.py`. Le script refuse
d'écrire un roster sur un fetch en échec (#511) et sort en 1 : le run s'arrête
au lieu de publier une composition de groupe non mesurée. **Ce n'est pas une
régression du garde-fou, c'est le garde-fou qui fait son travail** — et aucune
donnée n'est perdue, la fusion étant additive.

Le fetch qui échoue est `('senateurs', None)`. Vérifié le 24/08/2026 :
`https://archive.nossenateurs.fr/senateurs/json` rend une
`SSLError(CERTIFICATE_VERIFY_FAILED)` — certificat expiré. `requests` lève,
`fetch_rosters_bruts` note `None` pour la clé, l'anomalie « composition
INCONNUE, pas vide » se déclenche, sortie 1. Déterministe, sur les
**9 invocations** d'un run (8 shards + `merge-and-pivot`), ce qui explique le
8/8 du 22/08. Le Sénat n'a plus de repli : `BASE_URLS["senateurs"]` ne contient
qu'une entrée depuis la fermeture de `www.nossenateurs.fr`, et c'est ce
domaine-là.

Rien dans le dépôt ne corrige un certificat tiers. Ce qui est à nous, en
revanche, c'est la **portée** de la panne : une source Sénat à terre bloquait
aussi la collecte des **452 membres AN**, qui alimentent, eux, des agrégats
publiés.

## Suspendre, et non retirer

Retirer les deux entrées de `raw_data/groupes_reels.json` marcherait — c'est la
variante (c2) instruite dans l'issue — mais ferait **disparaître deux fichiers
publiés** (`groupe-Senat-LR.json`, `groupe-Senat-SER.json`), donc une perte
bloquante pour `audit_diff_profils` (#460/#470), à couvrir une fois par
`allow_declared_losses`. C'est irréversible en pratique, et la question posée
était explicitement **temporaire**.

Une entrée porte donc un bloc `extraction_suspendue` (`src/groupes_config.py`) :

```json
"extraction_suspendue": {
  "depuis": "2026-08-24",
  "motif": "…",
  "references": ["#516", "run 32548486495"],
  "condition_reprise": "…"
}
```

Il coupe la **collecte** sans toucher au **publié**. Les trois consommateurs de
la config s'alignent, et c'est la condition pour que la suspension veuille dire
quelque chose :

| Consommateur | Groupe suspendu |
| --- | --- |
| `generate_roster_candidats.py` | clé de fetch jamais construite ; ses membres ne sont pas collectés ; son absence n'est **pas** une anomalie #511 |
| `generate_group_profiles.py` | ni fetché ni régénéré, et **pas compté en échec** — le compter ferait sortir le script en 1 à chaque run |
| `check_quality_gate._report_groupes` | contrôles **durs** maintenus (fichier présent, JSON et schéma valides — il est toujours publié et servi), contrôles **souples** arrêtés (ils mesurent la collecte de ce run, qui n'a rien collecté ici), ligne `⏸ Suspendus` à part, jamais dans « OK » |

Les trois étages du script de roster (fetch, aplatissement, anomalies) voient
la suspension. Un seul qui ne la verrait pas rouvrirait la clé de fetch, ou
transformerait le groupe en « 0 membre retenu » : la panne serait simplement
déplacée.

## Les quatre champs sont exigés, et le gate le vérifie

Une suspension sans motif, sans date, sans référence ni condition de reprise
est un assouplissement silencieux qui devient permanent par oubli — la forme
exacte contre laquelle #511 a été écrit. `anomalies_suspension()` exige les
quatre, et le quality gate en fait une **erreur dure**, au même titre qu'un
champ `fichier` absent : c'est la config qui est en défaut, pas la donnée.
`"extraction_suspendue": true` est refusé pour la même raison.

`condition_reprise` est le champ qui empêche le « temporaire » de durer. Pour
les deux entrées Sénat : *un certificat valide sur `archive.nossenateurs.fr`,
ou une source de remplacement ; à défaut de l'un des deux d'ici fin 2026,
trancher la question éditoriale.*

## Ce que ça coûte, mesuré

- la cible de collecte passe de **752 à 452** membres : les deux `couverture_roster`
  publiées portent `roster_total` 235 (`Senat:LR`) et 65 (`Senat:SER`), soit les
  300 du Sénat déjà relevés en #511. Sur ces 300, **20 avaient un profil**
  (`profils_disponibles` 15 + 5) : ce sont eux, moins `bruno-retailleau` — qui
  reste collecté par `extract-senat` en tant que `candidat_declare` — qui
  cessent d'être rafraîchis. Aucun n'est supprimé ;
- `groupe-Senat-LR.json` et `groupe-Senat-SER.json` restent **publiés et
  servis** par l'onglet Groupes, gelés à leur dernière génération réussie. Ils
  portent `cohesion_votes: 0` (aucun jeu de données de vote sénatorial n'est
  intégré, #488/#501) et `Senat:SER` est clos depuis le 13/07/2009 : ce qui
  gèle est une composition et des mandats agrégés, pas une activité ;
- les profils pivot des 20 sénateurs restent en place — rien ne disparaît, donc
  ni `audit_diff_profils` ni `audit_collecte_non_publiee` (#511) n'ont à être
  désarmés. **Aucune tolérance (`allow_declared_losses` et consorts) n'est
  requise pour ce changement.**

## Ce que ça ne corrige pas

Les échecs **entrelacés** du 21/08 (shard 0 et shard 3 démarrent à la même
seconde, l'un passe, l'autre non) sont une panne transitoire, même signature
que l'incident #511 du 20/08. La suspension ne les couvre pas. Restent en
attente, hors périmètre ici (ROADMAP) :

- **retry avec backoff** sur `fetch_full_roster` — 1 seul essai, timeout 15 s,
  aucun repli aujourd'hui ; à ne retenter que sur ce qui est retentable
  (timeout, `ConnectionError`, 5xx), jamais sur `SSLError` ni 4xx ;
- **un seul roster par run**, construit par `prepare-roster-matrix` et transité
  par artifact : 9 invocations × 2 requêtes = 18 requêtes par run aujourd'hui,
  et le run n'aboutit que si les 18 passent. Cela supprimerait aussi un effet
  de bord latent — `--shard i/N` partitionne par position modulo, donc deux
  shards construits sur deux fetchs différents ne partitionnent plus la même
  population ;
- **anomalies en `::error::`**, pour que la cause remonte sur la page du run :
  la seule annotation des deux runs est `Process completed with exit code 1`.

## Alternatives écartées

- **Retirer les deux groupes de la config** : irréversible en pratique (deux
  fichiers publiés disparaissent, `allow_declared_losses` à porter une fois),
  alors que la demande était temporaire. Reste la sortie de secours si la
  source ne revient pas.
- **Dégrader par clé de fetch** (échouer si l'AN tombe, continuer avec un
  `meta.warnings` si seul le Sénat tombe) : modifie le contrat de #511 — « la
  granularité d'une panne est la clé de fetch entière ». Une décision de config
  datée est préférable à un garde-fou assoupli, qui vaudrait pour toutes les
  pannes futures, y compris celles qu'on n'a pas instruites.
- **`--autoriser-roster-incomplet` en CI** : publierait une composition de
  groupe non mesurée. Le drapeau existe pour le travail local (#511), il n'est
  câblé sur aucun input de `generate-data.yml`, délibérément.

Guardé par `tests/test_groupes_suspendus.py` (17 tests : pas de fetch, pas
d'anomalie, pas d'échec, fichier publié intact, contrôles durs maintenus,
suspension non documentée refusée, config du dépôt documentée).

---

