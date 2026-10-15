<a id="budgets-par-gouvernement-1053"></a>

# Budgets sur la fiche de gouvernement : l'année revient à qui l'a fait voter (#1053) (2026-10-13)

`2026-10-13`

> **En bref** — La maquette de la section budget est arrêtée : une cascade des
> recettes et des dépenses, deux colonnes « reçoit / dépense » par mission, et les
> mêmes colonnes pour les caisses de sécurité sociale. Une année revient au
> gouvernement sous lequel sa loi de finances a été promulguée.
> `src/budgets_gouvernements.py` compose ces données dans un fichier à part ; la
> collecte garde désormais la mission.

## Contexte

Les collectes de #1281, #1282 et #1283 étaient en production sans lecteur. La
maquette, itérée avec la propriétaire les 12 et 13/10/2026, a d'abord compté les
mois du gouvernement, puis buté sur les missions, que la source ne publie que par
année entière. Sa décision, le 13/10 : « il faut faire par période de budget voté
par le gouvernement ».

## Décision

1. **La règle de période.** Un exercice revient au gouvernement sous lequel sa loi
   de finances initiale a été promulguée, date lue dans `textes_promulgues.json`.
   Elle rejoint l'arbitrage du 08/10 : l'exercice est l'unité, rien n'est réparti.
   Aucune année ne figure sur deux fiches ; un gouvernement qui n'a fait voter
   aucun budget n'a pas la section.
2. **Seulement le réalisé.** Les montants votés ont été retirés de la maquette le
   13/10 ; le fichier ne les reprend pas. La collecte les garde.
3. **Un fichier à part**, `pivot_data/budgets_gouvernements.json`, et non un bloc
   de la fiche de gouvernement : le schéma de la fiche et sa validation ne bougent
   pas, et la section peut évoluer sans eux.
4. **La collecte garde la mission** des exercices 2023 à 2025, seuls fichiers qui
   la portent. Un exercice déjà publié sans elle se relit une fois.
5. **Les caisses suivent la même année par analogie.** Leur budget est voté par la
   loi de financement de la Sécurité sociale, dont les dates ne sont pas lues.

## Ce que la mesure a réglé au passage

L'écart d'environ 5 Md€ entre le total des dépenses du jeu mensuel et la somme des
missions, signalé sans explication depuis le 12/10, **est la ligne
« Remboursements et dégrèvements d'impôts locaux »** : comptée dans les dépenses
nettes du budget général, absente des missions gardées. Mesuré sur 2023, 2024 et
2025 : l'égalité tient à moins de 1 M€. Le fichier la publie à côté des missions.

## Les programmes sous chaque mission (14/10/2026)

Demandé par la session interface pour le survol d'une mission : chaque mission
publie ses `programmes[]`, avec leur nom et leur montant réalisé, et son montant
est leur somme. La collecte garde le nom du programme là où la source l'écrit ;
un exercice publié sans lui se relit une fois. Relu hors dépôt le 14/10/2026 :
« Engagements financiers de l'État » 2024 = 6 programmes, 58,8 Md€, dont le 117
(« Charge de la dette et trésorerie de l'État (crédits évaluatifs) ») pour 49,3.

## Alternatives écartées

- **Les mois du gouvernement** : exacts pour les recettes et les dépenses par
  nature, impossibles pour les missions ; deux moitiés d'une même carte donnaient
  deux déficits.
- **Les années que le gouvernement a touchées** : une même année sur plusieurs
  fiches, lue comme attribuée à chacun.
- **Le prorata des mois** : une estimation publiée comme un fait (§2 règles 2 et 5).

## Ce qui reste

La section de la fiche (`web/UI_finale`) n'est pas écrite. Le mot « Emprunt »,
retenu sur la maquette pour ce que les recettes ne couvrent pas, n'est appuyé sur
aucune ligne des fichiers collectés : il lui faut une source avant publication.
Les dates des lois de financement de la Sécurité sociale ne sont pas lues.
