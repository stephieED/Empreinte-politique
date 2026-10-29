# Un groupe de la XIVe ne publie pas « aucun sujet » : sa parole n'est pas collectée (#1337) (2026-10-29)

`2026-10-29`

> **En bref** — les 7 fiches de groupe de la XIVe et les 3 lignées faites de ses seuls groupes publiaient `tags_thematiques_agreges: []`, qui se lit « aucun sujet de parole ». Or l'Assemblée ne publie pas de comptes rendus de séance avant la XVe : rien n'est collecté. Ces fiches publient désormais `null`, accompagné de `tags_thematiques_non_resolu` (`motif: "hors_couverture"`, les législatures couvertes, la preuve). La borne est celle des interventions des profils (`couverture_profil.BORNES["interventions"]`), lue et jamais recopiée. Les fiches de la XVe à la XVIIe ne changent pas.

## Contexte

Mesuré sur `pivot_data/` le 29/10/2026 (`origin/main` `823b0c6e70`) :

| Fiches | Sujets publiés |
| --- | ---: |
| 7 groupes de la XIVe (`ECOLO-14`, `GDR-14`, `R-UMP-14`, `RRDP-14`, `SRC-14`, `UDI-14`, `UMP-14`) | 0 chacune |
| 3 lignées de la seule XIVe (`ECOLO-14`, `R-UMP`, `RRDP`), publiées sur le site | 0 chacune |
| `SOC-15`, pour comparaison | 1 936 |

Le 22/10/2026 (constat de l'issue), aucune intervention de l'Assemblée des
profils pivot n'était datée d'avant le 21/06/2017. Le filtre par législature
écartait le reste à juste titre : 126 446 interventions d'une autre législature
écartées pour `SRC-14`, d'après ses `meta.warnings`.

## Décision

1. **`tags_thematiques_agreges: null`** sur une fiche de groupe de l'Assemblée
   dont la législature n'est pas dans `BORNES["interventions"].legislatures`.
   La fonction est `couverture_profil.parole_hors_couverture(chambre, legislature)`.
2. **`tags_thematiques_non_resolu`** à côté : `{motif, legislatures_couvertes,
   preuve}`. Le motif reprend l'état `hors_couverture` des profils
   (`schema_pivot.ETAT_HORS_COUVERTURE`) au lieu d'un mot nouveau. La preuve est
   la `limite_source` de la borne : une limite de la source, pas un choix de
   notre part (#560).
3. **Si et seulement si** : le bloc n'existe qu'avec une liste `null`, et une
   liste `null` exige le bloc. `schema_groupe.valider_tags_non_resolu` le
   vérifie, pour la fiche de groupe comme pour la lignée.
4. **Une lignée** publie `null` quand **tous** ses maillons le font, et reprend
   leur bloc. Un seul maillon couvert suffit à publier la liste : la lignée
   `GDR` (XIVe à XVIIe) garde ses sujets.

## Ce qui n'a pas bougé

- Le contrôle de perte avant commit compte 0 entrée avant (`[]`) comme après
  (`null`) : il ne signale rien.
- Les lecteurs de l'interface (`groupe.js`, `vue-lignee.mjs`) lisent déjà
  `tags_thematiques_agreges || []`. Ils ne cassent pas, mais **ils n'affichent
  pas encore le motif** : c'est le travail de l'interface (#1314).

## Alternatives écartées

- **Garder `[]` et ajouter un avertissement dans `meta.warnings`** : la liste
  vide resterait la donnée, et l'avertissement une phrase que personne ne lit.
  §2 règle 5 veut `null`.
- **Exiger dans le validateur qu'une fiche de la XIVe porte `null`** : une fiche
  gelée par `extraction_suspendue`, non régénérée, ferait échouer le portail. La
  règle est tenue par la fabrique et par les tests.
- **Ajouter les sujets aux `couverture` des profils** : `tags_thematiques` en est
  exclu à dessein, c'est une aide à la lecture dérivée sans source propre.

## Non vérifié

- Les fichiers publiés : ils changeront au premier run après la fusion.
- L'affichage sur les trois lignées de la XIVe, tant que l'interface ne lit pas
  le motif.
