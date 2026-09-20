# Une candidature déclinée sort du périmètre de collecte, sa fiche reste publiée (#760)

`2026-09-07`

> **En bref** — #757 avait fermé la boucle du périmètre sans en border la **sortie** : `prepare-an-matrix` retenait tout candidat à slug résolvable, donc une candidature déclinée gardait son shard — **2 sur 29** au 07/09/2026 (Wauquiez, Bardella), et la part ne fera que croître, l'article des candidatures comptant déjà **24** personnes sous « ayant décliné » ; un prédicat unique (`src/perimetre_candidats.py`) appliqué aux **deux** endroits qui décident du périmètre — la matrice et `generate_all_profiles` —, parce que le filtre vivait en dur dans le YAML et qu'une seconde copie aurait divergé sans faire échouer aucune étape (le défaut que #518 a supprimé côté roster) ; **29 → 27 shards** ; **geler n'est pas supprimer** : le profil reste publié avec sa dernière collecte (régime des fiches Sénat gelées de #528 ; supprimer un fichier publié est une disparition qu'`audit_diff_profils` bloque), et rien n'est perdu à la fusion — ne pas collecter ne produit pas une collecte **vide**, ça ne produit **aucune** collecte ; le gel **se lève tout seul** si la personne redéclare, la boucle de #757 s'en charge ; **un statut inconnu est collecté** — `STATUTS_GELES` est le seul ensemble fermé, et le défaut penche vers collecter de trop plutôt que vers écarter en silence, parce qu'une collecte en trop coûte un shard et se voit, quand un candidat écarté par une valeur ajoutée ailleurs disparaît sans que rien ne le dise (#510) ; le gel **se déclare** là où le périmètre est calculé (`::notice::CANDIDAT_GELE`, avec le slug et le statut, jamais un compteur), et le module entre dans la liste blanche de sparse-checkout de la matrice — un chemin lu mais absent ne fait pas échouer le checkout, il rend un fichier absent (#674) ; **ce que le lot ne fait pas** : dépublier la fiche d'une candidature déclinée, question éditoriale laissée ouverte. 11 tests neufs + 3 sur le contrat de la matrice, suite complète à 3 978, 0 échec.

## Contexte

#757 a fermé la boucle du périmètre — la liste pilote le run — sans en border la
**sortie**. `prepare-an-matrix` retenait tout candidat à slug résolvable, et rien
d'autre :

```python
slugs = [c["slug"] for c in data["candidats"] if c.get("slug")]
```

Une candidature déclinée gardait donc son shard. Au 07/09/2026 : **2 sur 29** —
Laurent Wauquiez et Jordan Bardella, passés `statut: decline` par #753. La part
ne fera que croître : l'article des candidatures compte déjà **24 personnes**
sous « Candidats pressentis ayant décliné », et la campagne les multipliera à
mesure qu'elle tranche.

Collecter quelqu'un qui a renoncé, c'est payer un shard **en série**
(`max-parallel: 1`) pour rafraîchir une fiche que plus rien ne fait bouger.

## Décision

Un prédicat unique, `src/perimetre_candidats.py`, appliqué aux **deux** endroits
qui décident du périmètre : la matrice et `generate_all_profiles`.

| Mesure | Avant | Après |
| --- | --- | --- |
| Shards `extract-an` | 29 | **27** |
| Candidats gelés, nommés à chaque run | — | **2** |

**Un seul endroit, parce que le filtre vivait en dur dans le YAML.** Recopié dans
le Python, il aurait divergé au premier lot qui touche l'un des deux — et une
divergence de périmètre ne fait échouer aucune étape : elle collecte quelqu'un
que la normalisation ignore, ou l'inverse. C'est exactement ce que #518 a
supprimé pour le roster.

## Geler n'est pas supprimer

**Le profil reste publié**, avec les données de sa dernière collecte. Ce que la
personne a fait au Parlement reste vrai ; seule sa candidature a cessé.
Supprimer un fichier publié est une disparition qu'`audit_diff_profils` bloque
(#460/#470), et le régime est celui des deux fiches de groupe Sénat de #528 —
gardées, gelées, déclarées.

**Rien n'est perdu à la fusion.** Ne pas collecter ne produit pas une collecte
vide, ça ne produit *aucune* collecte : la fusion additive n'a rien à écraser, le
contrôle de perte ne voit aucune perte, et la §5b garde son entrée de
correspondance intacte. La distinction « vide » / « absent » est celle que
[une collecte vide n'écrase jamais](collecte-vide-necrase-jamais.md) tient depuis
le début.

**Le gel se lève tout seul.** Si la personne redéclare, le job de tête de #757
repasse son `statut` à `declare` et son shard revient au run suivant. Aucune
intervention, aucune entrée à rouvrir : c'est la boucle qui le fait.

## Un statut inconnu est collecté, jamais écarté

`STATUTS_GELES` est fermé et volontairement petit — `{"decline"}` — et c'est le
**seul** ensemble fermé du module : tout ce qui n'y est pas est collecté, y
compris une valeur que le module ne connaît pas encore.

Le défaut penche donc vers **collecter de trop** plutôt que vers **écarter en
silence**, parce que les deux erreurs ne coûtent pas la même chose. Une collecte
en trop coûte un shard, et elle se voit. Un candidat écarté par une valeur de
statut ajoutée ailleurs — un lot futur, un correctif éditorial — disparaît du
périmètre sans que rien ne le dise, et personne ne cherche ce qu'on ne sait pas
manquant. C'est le patron de #510.

## Le gel se déclare

Un candidat qui sort du périmètre est **nommé là où le périmètre est calculé** :
`::notice::CANDIDAT_GELE` dans la matrice, une ligne dans le log de
`generate_all_profiles`. La sortie n'est pas un compteur : elle porte le slug et
le statut, parce que c'est ce qui distingue un périmètre **réduit** d'un
périmètre **amputé** (#510, #501).

Le module lit `src/perimetre_candidats.py` depuis la matrice, dont la liste
blanche de sparse-checkout le porte désormais : un chemin lu mais absent du
checkout ne fait pas échouer le checkout, il rend un fichier absent et la
collecte se replie en silence (#674).

## Ce que la décision ne fait pas

**Dépublier la fiche d'une candidature déclinée.** Elle reste en ligne, et ses
données cessent d'être rafraîchies — c'est le prix explicite du gel. La question
est éditoriale et elle reste ouverte : une fiche de candidat qui n'est plus
candidat doit-elle rester dans l'onglet **Candidats** ? Le gel la rend visible,
il ne la tranche pas.

## Alternative écartée

**Filtrer dans le YAML seulement.** Une ligne de moins, et le périmètre aurait eu
deux définitions : celle de la matrice et celle de `generate_all_profiles`, qui
lit la même liste quand on le lance à la main ou dans `scripts/generate_data_local.sh`.
Deux définitions du même périmètre, c'est un candidat collecté par l'une et
ignoré par l'autre — sans qu'aucune étape n'échoue.

**Supprimer l'entrée de `candidats.json`.** Elle sortirait du périmètre aussi,
et emporterait avec elle le fait que cette personne **a été** candidate, ce que
la fiche publiée continue de dire. Une suppression n'est pas un changement
d'état : c'est une perte d'information, et `statut: decline` existe précisément
pour l'éviter (#753).
