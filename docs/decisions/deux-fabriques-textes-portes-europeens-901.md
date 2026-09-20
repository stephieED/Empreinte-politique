<a id="deux-fabriques-textes-portes-europeens-901"></a>
# Corriger là où un champ est jeté ne suffit pas : il faut trouver tous les endroits où l'objet est fabriqué (#901) (2026-09-14)

`2026-09-14`

> **En bref** — [le lot du stade](stade-procedural-europeen-901.md) a livré `stade_procedural` sur les textes portés européens, et le run qui l'a suivi a montré ce qu'il avait manqué : **12 des 383** en portaient un, soit **3 %**. Il y a **deux fabriques** de `textes_portes[]` européens, et une seule avait été corrigée. `_make_texte_porte_activite` — 371 entrées sur 383 — écrivait `stade_procedural: None` en dur. La source donnait pourtant de quoi le résoudre : une activité cite la référence de procédure qu'elle vise, sur **144 des 146** entrées `REPORT` mesurées.

## 1. La même erreur, deux fois dans la même journée

Le 14/09/2026 au matin, la reformulation du motif de suspension du Sénat avait buté sur un fait identique : **deux fabriques de preuve**, `GroupeSuspendu.preuve` pour les profils et `groupes_config.resume_suspension` pour les fiches de groupe, dont une seule avait été traitée.

Le patron d'erreur est le même, et il mérite d'être nommé : **j'ai cherché où le champ était jeté, pas tous les endroits où l'objet est construit.** Un `grep` sur `stade_procedural` rendait bien les deux occurrences — la seconde, `"stade_procedural": None`, ressemblait à une valeur par défaut légitime et non à un chemin concurrent.

Ce qui l'a révélé n'est pas une relecture : c'est le **run**. Une correction de normalisation ne se vérifie pas sur le code, elle se vérifie sur le corpus qu'elle produit.

## 2. Ce que la source donne, et qui n'était pas lu

| Population | Champ | Couverture |
| --- | --- | ---: |
| Activités `REPORT` (échantillon de 300 MEP) | `dossiers[]` — la référence de procédure visée | **144 / 146** |
| Références visées par les amendements européens | présentes dans l'index des stades | **355 / 367** (96,7 %) |
| Dossiers du dump portant un `stage_reached` | — | **20 442 / 23 885** (85,6 %) |

`build_stades_dossiers_index` rend `{reference: stage_reached}` pour tous les dossiers du dump. Il ne fait **pas** doublon avec `build_dossiers_index` : celui-ci répond « de quels dossiers cette personne est-elle rapporteure » et n'indexe que ceux-là, celui-là répond « où en est ce dossier » pour une référence quelconque — y compris celles que les activités citent, et dont la personne n'est pas rapporteure au sens de `committees[].rapporteur`.

Il est aussi **plat et minuscule** : deux chaînes par dossier, contre six champs par entrée, et sans périmètre de MEP — une référence est une référence.

## 3. Une absence de plus, et elle est distincte

Les deux fabriques publient désormais les mêmes motifs, pour qu'une fiche ne distingue pas deux textes selon le chemin qui les a produits. Un quatrième cas apparaît, propre aux activités :

| Motif | Quand |
| --- | --- |
| `source_sans_stade` | le dossier est connu, la source ne publie pas son stade |
| `stade_source_inconnu` | la source publie un libellé que la table ne connaît pas — **avec la valeur reçue** |
| **`activite_sans_dossier`** | l'activité ne vise aucune référence : il n'y a rien à interroger |

Le dernier n'est pas un synonyme du premier. « La source se tait sur ce dossier » et « il n'y a pas de dossier » sont deux faits différents, et les confondre ferait compter comme une lacune de la source ce qui est une propriété de l'activité (§2 règle 5).

## 4. `reference_dossier`, publié par les deux fabriques

Besoin remonté par l'interface le 14/09/2026 : les 383 textes portés européens ne portaient **aucune** référence, et ne pouvaient donc rejoindre ni [l'index des dossiers](index-dossiers-europeens-901.md) ni rien d'autre — « une liste sans axe ».

Le champ porte le **même nom** que sur un vote (`scrutin_non_resolu.reference_dossier`) : c'est le même espace de références, et lui donner deux noms obligerait chaque consommateur à connaître le chemin qui a produit l'entrée. Un test vérifie que les deux fabriques publient le même jeu de clés, à `nature_texte` près — la seule qui soit propre aux activités.

## 5. Ce que le garde-fou des caches a attrapé

Construire l'index depuis `enrich_pivot_with_parltrack` a fait lire le **cache réel du poste** à un test existant, et `CacheDuPosteLuDansUnTest` (#721) l'a refusé. C'est le bon comportement : un test qui lit `.cache/` passe ou échoue selon ce qu'une collecte locale y a laissé, et la CI ne le voit jamais.

L'index n'est d'ailleurs construit **que si** une activité portée existe : le bâtir pour un profil qui n'en a aucune coûterait un parcours de dump pour rien.

## 6. Ce que ce lot ne fait pas

Il ne mesure pas l'effet réel sur les 383 textes portés : cela demande un run, et c'est ce run qui dira si la couverture atteint les 85,6 % du dump ou reste en deçà. **Le lot précédent a été validé sur le code et démenti par le corpus** ; celui-ci ne sera vérifié qu'après régénération.
