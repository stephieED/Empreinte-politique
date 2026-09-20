<a id="roster-gouvernements-amo30-996"></a>
# Les membres d'un gouvernement reçoivent un identifiant de profil (#996, lot 2) (2026-09-17)

`2026-09-17`

> **En bref** — Aucun module ne pouvait donner de slug à une personne jamais
> députée : l'index d'AMO30 ne retient que les acteurs porteurs d'un mandat de
> groupe politique. `gouvernement_roster_an.py` lit les organes `GOUVERNEMENT`,
> résout les slugs **sur l'union** des deux index, et verse les membres dans
> `rosters_bruts.json`. Mesuré : **311 membres, 106 slugs repris de la table,
> 205 fabriqués, aucun bloqué.** La fiche publie aussi le dénominateur,
> `comptages.membres_recenses`.

## Contexte

Lot 2 de #996. Le lot 1 a donné 17 fiches de gouvernement ; leur composition
reste celle des profils déjà collectés. Pour collecter les 205 membres qui n'ont
pas de profil, il faut d'abord qu'ils aient un identifiant — et une entrée dans
`correspondance_acteurs_an.json`, sans laquelle la §5b du portail, seuil 0,
refuse tout profil publié.

## Décision

1. **`construire_index_gouvernements`** lit les organes `GOUVERNEMENT` et les
   mandats qui les visent, dans la même forme que l'index GP : `organes`,
   `mandats`, `acteurs`. Une archive sans aucun organe lève (#510).
2. **Les slugs passent par `an_roster.resoudre_slugs`**, sans le réécrire : la
   table de correspondance passe devant, un slug n'est fabriqué que pour un
   acteur jamais relu.
3. **L'union des acteurs des deux index** sert d'univers de collision. Sans elle,
   un ministre et un député homonymes pourraient recevoir le même slug le même
   jour. La sortie, elle, est filtrée aux seuls membres de gouvernement.
4. **Une personne, une entrée** : un ministre de deux gouvernements a deux
   `mandat_periodes`, pas deux entrées — c'est une personne à collecter.
5. **`rosters_bruts.json`, clé `gouvernements:`** : c'est ce fichier que
   `build_correspondance_acteurs_an.slugs_fabriques` lit pour créer les entrées
   dérivées. Les membres n'entrent **pas** dans `roster_candidats.json` : la
   collecte est le lot suivant.
6. **Échec non fatal** : une archive illisible n'écrit pas la clé et laisse le
   roster des groupes intact. `--sans-gouvernements` débranche la passe.
7. **`comptages.membres_recenses`** sur la fiche : le dénominateur de `membres[]`,
   personnes distinctes sur toute la vie du gouvernement, de 19 (Lecornu I) à 55
   (Borne). `null` quand la liste ne le porte pas.

## Mesuré, sur l'archive du 17/08/2026

| | |
| --- | ---: |
| Gouvernements | 17 |
| Membres, personnes distinctes | 311 |
| Slugs repris de la table | 106 |
| **Slugs fabriqués** | **205** |
| Acteurs sans slug (homonymie, état civil manquant) | **0** |

## Alternative rejetée

**Étendre l'index GP aux mandats de gouvernement.** Il aurait fallu changer sa
version, donc invalider son cache pour tous les shards du roster, pour une
information qui ne sert pas aux groupes.
