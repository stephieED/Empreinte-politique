# UDR entre comme une lignée à elle seule : la scission qu'on croyait tenir n'existe pas (#815)

`2026-09-11`

> **En bref** — #815 et #836 réservaient un arbitrage à la **scission** UDR, décrite comme « `AD` quitte `DR` le 11/09/2024 pendant que `DR` poursuit ». **La mesure sur AMO30 l'a infirmée avant l'arbitrage** : **0** des 16 membres d'`AD` n'a siégé dans `DR`, les deux groupes naissent le même jour (18/07/2024), et **2** seulement des 16 viennent de `LR-16`, qui en a envoyé **41** vers `DR`. `AD` → `UDR` → `UDDPLR` sont deux **renommages** en cours de XVIIe — mêmes 16 acteurs, puis 15 sur 16 —, le motif `SOC`/`SOC-A`. Arbitrage de la propriétaire, 11/09/2026 : **UDR entre comme une lignée à elle seule, sans prédécesseur**. Une fiche `UDR-17`, union des trois organes (PO845520, PO847173, PO872880), **18** membres, 2 déjà publiés (Ciotti, D'Intorni) et 16 à collecter ; lignée `AN:LIGNEE:UDR`, « Union des droites pour la République ». Déclarer `LR-16` comme prédécesseur aurait affirmé une succession pour 2 membres sur 16 (§2 règle 2). La question « comment écrire une scission » n'a plus de cas dans le corpus : elle attendra le premier. Quatre passages du code et des tests présentaient la scission comme un fait ; ils portent désormais la mesure. Suite complète à **4 514**, 0 échec.

## La mesure

| Organe | Période | Acteurs |
| --- | --- | ---: |
| `DR-17` PO845425 | 18/07/2024 → en cours | 64, dont 41 venus de `LR-16` |
| `AD-17` PO845520 | 18/07/2024 → 11/09/2024 | 16, dont 2 venus de `LR-16` |
| `UDR-17` PO847173 | 12/09/2024 → 04/09/2025 | 16 — les mêmes qu'`AD` |
| `UDDPLR-17` PO872880 | 05/09/2025 → en cours | 17 — dont 15 d'`UDR` |

`AD ∩ DR` = **0**. Il n'y a ni départ ni poursuite : deux groupes distincts,
constitués ensemble à l'ouverture de la législature.

## Ce qui avait rendu la prémisse plausible

La date du 11/09/2024 est bien celle d'un événement — la **fermeture d'`AD`**, le
jour où il devient `UDR` — et `LR-16` s'est bien partagé entre deux groupes à la
XVIIe. Mais un partage à 41 contre 2 n'est pas une scission de `DR`, et un
renommage n'est pas un départ. La phrase assemblait deux faits vrais en un faux.

## La décision

- une fiche `UDR-17`, `sigles_an: ["AD", "UDR", "UDDPLR"]`, l'union des trois organes ;
- **aucun `succede_a`** ; `tests/test_an_roster.py` porte la liste explicite des
  groupes de la XVIIe déclarés sans prédécesseur, pour qu'un oubli reste un échec ;
- la lignée `AN:LIGNEE:UDR`, un seul maillon, nommée d'après le maillon le plus
  récent (règle de #845).

## Écarté

| Option | Pourquoi |
| --- | --- |
| `succede_a: [LR-16]` | une succession pour 2 membres sur 16 : un fait faux publié sur la fiche |
| Hors périmètre | un groupe de la XVIIe sans fiche, pour aucune raison de source |

## Ce qui reste de #815

Les filiations de la XVe (`LT` → LIOT, `AGIR-E` → HOR) et `historique_noms`.
