# Un champ traverse la chaîne, ou il n'existe pas (#809)

`2026-09-11`

> **En bref** — #809 a câblé `mandat_periodes` de bout en bout — roster, appartenances, membre de fiche, compteur de présence, schéma, validation — et le champ n'a **jamais atteint une seule fiche** : `filter_roster_by_sigle` est une **projection par clés** qui recopie chaque entrée champ par champ, et le nouveau n'y figurait pas. Le run `34538350163` a régénéré les 23 fiches de groupe, `date_reference.origine` y a bien pris sa nouvelle valeur (#808 passait par un autre chemin), et **zéro membre ne portait `periodes[]`**. C'est la règle que `docs/regles/fusion-et-index.md` énonce depuis #492, #639, #641, #696, #710 et #718 — un champ ajouté n'atteint pas tout seul un consommateur qui projette — appliquée cette fois non à une fusion mais à un **filtre**. **Les tests de #809 ne pouvaient pas le voir** : ils appelaient `appartenances_depuis_roster` directement, en sautant le filtre, et décrivaient donc la chaîne telle que le lot l'imaginait. Le correctif est d'une ligne ; le test qui l'accompagne part du roster et va jusqu'à l'appartenance, filtre compris, et vérifie sur la chaîne réelle que `REN-16` rend bien ses **196 membres avec périodes, dont 8 à périodes multiples**.

## Ce qui s'est passé

#809 remplaçait l'enveloppe d'appartenance par le détail des périodes. Le lot a
touché six endroits : `an_roster` qui produit `mandat_periodes`,
`appartenances_depuis_roster` qui le transporte, le membre de fiche qui le
publie, `_appartenance_couvre` qui le lit, le schéma qui le décrit, la
validation qui le contrôle.

Il en manquait un, au milieu.

```python
roster.append({
    "slug": member.get("slug"),
    "nom": member.get("nom"),
    "mandat_debut": member.get("mandat_debut"),
    "mandat_fin": mandat_fin,
    ...
})
```

`filter_roster_by_sigle` **reconstruit** chaque entrée champ par champ. C'est
délibéré — chaque champ qui traverse porte sa justification en commentaire — et
c'est précisément ce qui fait qu'un champ neuf n'y entre pas de lui-même.

## Comment ça s'est vu

Le run `34538350163` a régénéré les 23 fiches de groupe. `date_reference.origine`
y a pris `derniere_appartenance_close` (#808), donc la génération a bien tourné
avec le code du jour. Et **aucun membre ne portait `periodes[]`** — 0 sur les
196 de `REN-16`.

Deux lots livrés ensemble, un qui s'applique et l'autre pas : c'est ce qui a
permis d'écarter tout de suite l'hypothèse d'une fiche non régénérée.

## Pourquoi les tests ne l'ont pas vu

Les tests de #809 appelaient `appartenances_depuis_roster(filtres)` avec des
entrées construites à la main, **en sautant `filter_roster_by_sigle`**. Ils
vérifiaient que la fonction du milieu transporte ce qu'on lui donne — ce qui
était vrai — et non que la chaîne le lui donne.

C'est le défaut nommé par #726 : *une fixture qui décrit le monde tel que le
code l'imagine ne peut pas révéler que le monde a bougé.* Ici la fixture
décrivait la chaîne telle que le lot la croyait.

Le test ajouté part du roster et va jusqu'à l'appartenance, filtre compris.

## La règle, et sa cinquième occurrence

`docs/regles/fusion-et-index.md` l'énonce pour la **fusion** : « A field added
to the schema never reaches an already-collected entry on its own ». #492, #639,
#641, #696, #710, #718 en sont les occurrences.

Celle-ci l'étend : ce n'est pas seulement la fusion qui projette, c'est **tout
consommateur qui recopie les entrées à la main**. Un filtre, une projection de
lecture (`projeter_profil_membre`, #635), un sérialiseur. Le symptôme est le
même — le champ existe à la source et n'arrive jamais — et le remède aussi :
suivre la chaîne entière, et la tester de bout en bout plutôt que par morceaux.

Suite complète à 4 463, 0 échec.
