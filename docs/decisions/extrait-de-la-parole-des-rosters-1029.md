<a id="extrait-de-la-parole-des-rosters-1029"></a>
# La parole des membres de groupe et de gouvernement publie un extrait de 280 caractères (#1029) (2026-09-22)

`2026-09-22`

> **En bref** — Pour dire ce qu'un ministre ou un député de roster a dit, le corpus n'avait que le thème (#657). Arbitré le 22/09/2026 : un extrait de 280 caractères pour tous les profils de groupes et de gouvernement, le texte entier restant chez l'Assemblée (#1087). ≈ 460 Mo estimés sur les deux étages.

## Le besoin

Remonté par l'interface pour #1029 (« carburant ») : quatre ministres de
Lecornu II interviennent dans dix séances de questions au gouvernement, et le
corpus ne dit pas ce qu'ils ont annoncé. #657 avait réduit au thème la parole
des 1 183 561 entrées de roster (1 123 321 de groupe, 60 240 de gouvernement,
22/09/2026), candidats déclarés exceptés.

## Le chemin de l'arbitrage

| Proposé | Coût estimé | Sort |
| --- | ---: | --- |
| Verbatim entier des 205 profils de ministres | ≈ 45 Mo | retenu d'abord (PR #1086), puis remplacé |
| Verbatim entier de toute la parole de roster | ≈ 1,6 Go | écarté : +22 % sur un arbre de 7,4 Go |
| **Extrait de 280 caractères, groupes et gouvernement, lien vers l'AN** | **≈ 460 Mo** | **retenu** |

Mesuré sur 12 765 interventions de cinq candidats : la coupe tronque 51 % des
textes, et ajoute 204 octets par entrée en moyenne (médiane 231). Le chiffre de
460 Mo est une projection sur 1 183 561 entrées, aux deux étages.

## Décision

1. `schema_pivot.extrait_de_texte` : 280 caractères au plus, coupés à la
   dernière fin de phrase si elle tombe dans la seconde moitié, sinon au dernier
   blanc. **Rien n'est ajouté au verbatim** : `texte_tronque` dit que le texte
   continue. Un propos coupé au milieu d'une phrase peut se lire à l'envers de
   ce qui a été dit (§2 règle 1).
2. `collecte: "extrait"`, nouvelle valeur de `KNOWN_COLLECTES_INTERVENTION`. La
   forme réduite (`candidate_profile._reduire_a_l_extrait`) garde tout ce que
   la forme thème gardait, plus `texte` et `texte_tronque`.
3. Le répertoire d'index réduit devient `index_par_acteur_extrait` : son
   contenu change, son nom aussi — un cache de l'ancienne forme ne se relit pas.
4. `merge_profile.promouvoir_forme_complete` : une forme plus riche remplace une
   plus pauvre (thème < extrait < complète), aux deux étages, **jamais
   l'inverse**. `aligner_collecte_reduite` fait dire à
   `meta.collecte_reduite.interventions` la forme la plus pauvre encore publiée.
5. Les candidats déclarés restent collectés en entier.

## Ce qui suit

- **Premier run avec `collect_interventions=true`** : c'est lui qui recollecte
  et fait passer les entrées publiées à l'extrait. Sans cette case, rien ne
  change.
- **L'interface lit `collecte === 'theme_seul'`** à trois endroits
  (`parolesParPeriode.js`, `couverture-corpus.mjs`, `vue-parole-gouvernement.mjs`) :
  elle doit apprendre `extrait`.
- Le lien vers le texte entier est #1087.

## Alternative rejetée

**Ajouter « … » à l'extrait** : ce serait écrire dans le verbatim. Le drapeau
porte l'information sans toucher au texte.
