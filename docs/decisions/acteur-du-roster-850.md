# Un membre de roster est collecté sous l'acteur que son roster nomme, jamais re-deviné par son nom (#850)

`2026-09-11`

> **En bref** — le run `34575181245` a laissé **6 membres de roster sans profil**, donc absents de **5 fiches de groupe AN**, alors que le roster AMO30 nommait leur acteur. Le roster le transmettait, mais **encodé dans une URL** (`source`) que rien ne relisait, et la collecte le re-devinait depuis le slug par la **correspondance par nom** : échec sur la ponctuation que le slug avait perdue (O'Petit, K/Bidi, M'jid El Guerrab, Morel-À-L'Huissier), refus — légitime — devant deux homonymes (Béatrice Descamps, Jean-Louis Masson). **La mesure a précédé le code, et elle a changé le lot** : aucune attribution au mauvais acteur dans le corpus publié — **0 écart** sur les 1 892 entrées membres des 28 fiches AN, en vérifiant contre AMO30 que l'acteur de chaque profil appartient à un organe du groupe qui le liste, sans passer par la table dont 16 entrées sur 1 174 seulement ont une origine vérifiée ; le défaut est de **couverture**, pas de véracité, et il n'y avait rien à purger. L'entrée de roster porte désormais `acteur_ref` **en clair**, `process_candidat` le transmet pour un membre de roster et pour lui seul, et `fetch_identite_officielle_par_slug` le prend **avant** toute résolution — sauf s'il **contredit la table committée**, auquel cas rien n'est collecté et les deux acteurs sont nommés (la règle de #757). **Effet mesuré avant de pousser** : sur les 1 140 entrées de la vraie liste de roster, 1 134 ont une entrée de table et **toutes** s'accordent avec le roster ; les 6 qui n'en ont pas sont **exactement** les six introuvables. Le correctif ne change le comportement que pour eux. Suite complète à **4 510**, 0 échec.

## Le défaut

```
roster AMO30 ──acteur_ref──▶ entrée de roster_candidats.json ──slug seul──▶ collecte
                               (source = …/OMC_PA266788)            │
                                                                    ▼
                                           _resolve_acteur_ref_par_slug(slug)
                                           table ? non (slug fabriqué, #708)
                                           nom ? « pierre morel a l huissier »
                                                 ≠ « pierre morel a l'huissier »
                                           → None → « Aucune identité trouvée »
```

L'entrée de table qui fige un slug fabriqué n'est écrite qu'**après** la
collecte, par la passe hors ligne de `merge-and-pivot` (#715) : elle arrive
trop tard pour la collecte qui en aurait besoin.

| Membre | Cause | Fiches |
| --- | --- | --- |
| Claire O'Petit | ponctuation | LAREM-15 |
| M'jid El Guerrab | ponctuation | LAREM-15 |
| Émeline K/Bidi | ponctuation | GDR-16, GDR-17 |
| Pierre Morel-À-L'Huissier | ponctuation | LIOT-16 |
| Béatrice Descamps | homonymie (PA392736, PA720696) | LIOT-16 |
| Jean-Louis Masson | homonymie (PA2116, PA346218) | LR-15 |

## Ce que la mesure préalable a établi

La question grave n'était pas « qui manque » mais « qui a été rattaché au mauvais
acteur ». Trois contrôles, aucun ne passant par la table :

| Contrôle | Population | Écarts |
| --- | --- | ---: |
| acteur du profil ∈ acteurs AMO30 des organes du groupe qui le liste | 1 892 entrées membres des 28 fiches AN | 0 |
| un même acteur porté par deux profils | 1 035 profils pivot | 0 |
| entrée de table contredite par le profil publié | 1 174 entrées | 0 |

La correspondance par nom refuse quand elle doute et échoue sur la ponctuation ;
elle n'a rattaché personne à tort dans ce qui est publié.

## La décision

- `generate_roster_candidats` écrit `acteur_ref` **en clair** dans chaque entrée.
  Le champ traversait déjà `filter_roster_by_sigle` depuis #529 : vérifié sur la
  vraie chaîne — les 1 140 entrées le portent, et après le découpage en 8 shards.
- `process_candidat` le transmet **pour un membre de roster seulement**. Un
  candidat déclaré résout son acteur par la table, où #757 exige deux sources
  concordantes ; un champ de liste n'y remplace pas une preuve.
- `fetch_identite_officielle_par_slug(slug, acteur_ref)` prend l'acteur fourni
  **avant** toute résolution — et lève `ActeurContreditParLaTable` si la table a
  tranché ce slug autrement : rien n'est collecté, le message nomme les deux
  acteurs, et `build_profile` l'imprime en plus de le consigner, un profil sans
  identité n'étant pas écrit.

## Écarté

**Écrire l'entrée dérivée de #715 avant la collecte.** Elle résoudrait les six,
mais en faisant passer par la table un fait que le roster porte déjà, et en
avançant une écriture que #715 a placée **après** la publication pour ne dériver
que de profils effectivement collectés.

**Assouplir la normalisation des noms** — apostrophes, barres — pour que le slug
retrouve la clé. Elle réglerait quatre cas sur six et laisserait les deux
homonymes, et elle rendrait la correspondance par nom **plus permissive** :
exactement le sens dans lequel on ne veut pas l'emmener.

## Limite

Les six paraîtront au prochain run : leurs profils ne sont pas collectés par ce
lot, qui ne change que le code.
