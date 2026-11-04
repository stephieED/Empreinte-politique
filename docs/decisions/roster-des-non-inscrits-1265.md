# Les députés non inscrits deviennent une population, et leur collecte part (#1265, second lot) (2026-11-04)

`2026-11-04`

> **En bref** — le premier lot de #1265 a publié la **liste** des non-inscrits (`raw_data/non_inscrits.json`) et déclaré qu'il ne collectait aucun profil : « Les faire entrer dans la collecte est un autre lot ». Ce lot ouvre la troisième porte du roster, sur le modèle de celle des gouvernements (#996, lot 3) : `KNOWN_PROVENANCES` reçoit `roster_non_inscrit`, qui entre dans `PROVENANCES_ROSTER`, et `generate_roster_candidats.py` verse les non-inscrits qu'aucun groupe ni gouvernement n'amène. Mesuré le 04/11/2026 sur l'archive AMO30 du jour : 322 non-inscrits hors transit d'ouverture, 297 déjà portés par un profil, **25 ajoutés**.

## Contexte

Relevé le 03/11/2026 en instruisant les effectifs des groupes (#1248, lot 5) : Véronique Besse et Philippe Bonnecarrère, non-inscrits en exercice, n'avaient pas de profil. Remesuré le 04/11/2026 : **25 personnes** sur les quatre législatures, dont Gilbert Collard, Jacques Bompard, Marion Maréchal-Le Pen, Emmanuelle Ménard, Louis Aliot. La propriétaire a fait rouvrir #1265 le 04/11/2026 (« Peut-on plutôt réouvrir cette issue ? »), puis lancer le lot (« lance le lot de 1265 »).

Aucune des 25 n'a appartenu à un groupe suivi : AMO30 ne leur connaît que l'organe « Non inscrit » (et l'UMP de la XIIIe pour Guy Lefrand, une législature que le corpus ne couvre pas). Aucune n'avait d'entrée dans la table de correspondance. **Correction** : Monique Lubin avait d'abord été citée, de mémoire, comme passée par le groupe socialiste de la XIVe ; AMO30 ne lui connaît que l'organe « Non inscrit » de cette législature.

## Décision

| Question | Réponse | Raison |
| --- | --- | --- |
| Qui ? | les membres de l'organe « Non inscrit » de chaque législature depuis la XIVe, **hors transit d'ouverture** | la règle de `non_inscrits.json` et du roster (`an_roster.est_mandat_de_transit`) : sans elle, les 577 députés de chaque législature entreraient par cette porte |
| Et ceux qui ont un profil ? | les portes « groupe » et « gouvernement » gagnent, reconnues par `acteur_ref` **ou** par slug | une personne passée par un groupe garde sa provenance, donc sa place dans les agrégats ; deux portes qui la nommeraient différemment ne la collecteraient pas deux fois |
| Quels slugs ? | `an_roster.resoudre_slugs` sur l'union des acteurs des groupes et des gouvernements | la même union que la porte des gouvernements : deux homonymes ne reçoivent pas le même slug |
| La table de correspondance ? | la liste entre dans le roster brut (clé `non_inscrits`), et `--completer-derivees` dérive l'entrée des slugs fabriqués dans le run | le chemin de #715 ; les 25 slugs sont fabriqués |
| Les agrégats ? | aucun | les non-inscrits ne sont pas un groupe : leurs votes et leurs amendements entrent dans le corpus, pas dans une fiche de groupe |
| Une panne ? | une archive illisible, ou sans organe de gouvernement, fait sauter **cette porte seule** | même régime que la porte des gouvernements ; la fusion additive garde les profils déjà collectés |

## Ce que ça change

- Le premier run après fusion collecte 25 profils de plus. Rien ne change à l'écran : le site ne publie de page que pour les candidats déclarés.
- Les amendements de ces députés ont désormais une copie du premier signataire, que l'index (#1431) et le retrait des signatures retirées (#1433) prennent pour preuve.
- Les outils ventilent la nouvelle population (« non-inscrits ») à côté des trois autres.

## Ce qui n'a pas été vérifié

- Le temps ajouté à la collecte : 25 profils sur environ 1 850, répartis entre les huit shards.
- Le comportement de la §5b du portail de qualité sur ces 25 slugs fabriqués avant que la passe de correspondance ne les couvre : c'est le chemin des gouvernements, non rejoué ici.
