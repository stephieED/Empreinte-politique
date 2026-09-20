# Les dossiers du roster passent sous une case, le motif qui les écartait est tombé (#817)

`2026-09-10`

> **En bref** — `extract-roster-groupes` portait `--skip-dossiers-legislatifs` **en dur** depuis #357 au motif que « les textes portés ne sont consommés par aucun agrégat de groupe », or c'est le motif même que #657 avait démonté une liste plus tôt, et le commentaire du workflow portait les deux **côte à côte** : la justification périmée, puis sa réfutation sur le cas jumeau ; **17 profils sur 1 035** publiaient des `textes_portes`, tous `candidat_declare`, **zéro** membre de roster — `AN:DR` montrait 1 membre sur 86 —, alors que la collecte en rendrait **887 sur 1 021 pour 9 895 dossiers**, chiffre que l'issue n'avait pas mesuré ; le coût est de **3,0 s** de construction d'index et **57 Mio** de RSS, une fois par processus puis un `dict.get()` par membre, sur une archive que ce job **restaure déjà** (#505). Le drapeau passe sous `collect_dossiers_legislatifs` (défaut `false`) plutôt que d'être retiré, comme #657 l'a fait pour les interventions ; libellé relu à l'écran avant d'être écrit (§11), et la première rédaction — « roster members too » — écartée parce que les candidats déclarés sont collectés par `extract-an` indépendamment de cette case. **La couverture n'avait rien à changer** : `meta.collecte_ecartee` prime sur l'inférence et cessera simplement de nommer `textes_portes`, tandis que `DECISIONS_ROSTER` reste juste pour les 19 profils d'avant #539 — l'en retirer publierait « couvert » sur des listes vides. `tests/test_ci_inputs_workflow.py` a repris ce lot en **exécutant** le bash du workflow : il refuse une expression `${{ }}` dans le script, la première rédaction en portait une, deux tests sont tombés et ils avaient raison. Suite complète à 4 423, 0 échec.

## Contexte

`extract-roster-groupes` portait `--skip-dossiers-legislatifs` **en dur** depuis
#357, sous ce motif, écrit dans le workflow :

> les textes portés ne sont consommés par aucun agrégat de groupe (#349)

C'est exactement le motif que #657 a démonté une liste plus tôt, pour les
interventions — et le commentaire du workflow portait les deux, côte à côte :
la justification périmée, puis sa réfutation sur le cas jumeau.

Signalé par la session UI en travaillant la §3 « Ce qu'ils proposent » de la
fiche de groupe : cette vue **lit** les textes portés.

## Ce que ça coûtait, mesuré

| | |
| --- | ---: |
| Profils publiant des `textes_portes` | **17 sur 1 035**, tous `candidat_declare` |
| Membres de roster en publiant | **0** |

Conséquence en maquette : `AN:DR` montrait **1 membre sur 86**, la macronie
**1 sur 220**.

## Ce que ça rendrait, mesuré aussi

Index `acteur → dossiers` construit depuis l'archive bulk, croisé avec les
profils publiés, le 10/09/2026 :

| | |
| --- | ---: |
| Membres de roster portant des dossiers | **887 sur 1 021** |
| Dossiers au total | **9 895** |

L'issue annonçait « 14 profils sur 953 » côté manque ; côté gain, elle n'avait
pas mesuré. Une fiche de groupe passerait de « 1 membre sur 86 » à la
quasi-totalité.

## Ce que ça coûte au job, mesuré

`_build_acteur_textes_portes_index()` construit l'index **une fois par
processus** depuis l'archive bulk, puis c'est un `dict.get()` par membre. Ce
n'est pas une collecte par profil.

| | |
| --- | ---: |
| Construction de l'index | **3,0 s** |
| RSS maximum | **57 Mio** |
| Acteurs indexés | 1 643 |

L'archive est déjà **restaurée** par ce job (`.cache/dossiers_an`, restauration
seule depuis #505) : aucun téléchargement supplémentaire quand le cache est
chaud. Le budget du shard roster — 60 min, ~10 s fixes + 1,9 s par membre —
n'est pas menacé.

## La décision

Le drapeau passe **sous une case du formulaire**, `collect_dossiers_legislatifs`
(défaut `false`), et non retiré en dur. Même forme que `collect_interventions`
depuis #657 : la charge se choisit run par run.

Libellé, relu à l'écran avant d'être écrit (`scripts/rendu_formulaire.py`,
AGENTS.md §11) :

```
│Collect roster members' carried legislative files                │
│[ ] collect_dossiers_legislatifs                                 │
```

Il ne dit pas « roster members too » — première rédaction, écartée par la
propriétaire : les candidats déclarés sont collectés par `extract-an`,
indépendamment de cette case, qui ne gouverne que le roster.

## La couverture suit d'elle-même

`couverture_profil` publie `non_collecte`/`par_decision` sur `textes_portes` des
profils de roster. Deux chemins, et seul le second est une inférence :

- **`meta.collecte_ecartee`** (#539) — la trace écrite **par la collecte** des
  listes qu'elle a sautées. Elle prime sur toute inférence, et elle sera
  simplement absente de `textes_portes` le jour où le run les collecte.
- **`DECISIONS_ROSTER`**, le repli par provenance, **désarmé dès que le run a
  déclaré quoi que ce soit** (`run_a_declare`). Il ne sert plus qu'aux 19
  profils publiés avant #539, qui ne portent aucune trace de leurs drapeaux —
  et pour eux `skip_dossiers_legislatifs` reste vrai. L'y laisser est donc
  juste ; l'en retirer publierait « couvert » sur des listes vides.

C'est le même mécanisme que #657 a éprouvé sur les interventions, et il n'avait
rien à changer ici.

## Ce qu'il ne faut PAS en dériver

**« Qui a initié quoi ».** `_collect_initiateurs` lit `initiateur.acteurs.acteur`,
une liste où premier signataire et cosignataires sont mélangés, tous sortant
sous `auteur_proposition_de_loi` / `auteur_proposition_de_resolution`. « Le
groupe a porté ce texte » est publiable ; « untel l'a initié » ne l'est pas
(§2 règle 2). La déduplication sur `dossier_id` est déjà bonne : un texte
cosigné compte pour un.

## Un garde-fou a repris ce lot

`tests/test_ci_inputs_workflow.py` **exécute** le bloc bash de décision du job
pour vérifier ses combinaisons, et refuse toute expression `${{ }}` dans le
script — elles doivent vivre en `env:`. La première rédaction en portait une :
deux tests sont tombés, et ils avaient raison. Une table de correspondance
vérifiée par lecture de texte ne prouve rien de ce qui tourne.

Suite complète à 4 423, 0 échec.
