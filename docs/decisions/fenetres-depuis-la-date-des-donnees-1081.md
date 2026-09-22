<a id="fenetres-depuis-la-date-des-donnees-1081"></a>
# Les fenêtres de parole se comptent depuis la date des données, pas depuis la clôture de la fiche (#1081) (2026-09-22)

`2026-09-22`

> **En bref** — #1077 ancrait « 6 mois » et « 12 mois » sur `date_reference`, qui est la date de clôture d'une fiche close : RN-16 publiait « 6 mois » du 09/12/2023 au 09/06/2024. Le besoin (#1073) disait « depuis la date des données ». Les fenêtres partent désormais de la date de génération sur toutes les fiches ; une fiche close a des fenêtres vides.

## Constat

Relevé par l'interface (#1081) sur `69cbe6cee` : 16 des 29 fiches AN publiaient
des débats « sur 6 mois » alors qu'elles sont closes depuis 2022 ou 2024
(RN-16 : 503 débats, REN-16 : 602). L'interface les lit comme les six derniers
mois des données (#1074).

L'erreur est dans #1077 : `date_reference` répond à « à quelle date les
compteurs d'effectif sont pris » (#653) — la clôture pour une fiche close. Ce
n'est pas la question d'une fenêtre glissante.

## Décision

`bornes_des_fenetres` part de la **date de génération**, identique sur toutes
les fiches, et ne commence jamais avant `periode.debut`. Rien d'autre ne
change : le filtre d'appartenance vide de lui-même les fenêtres d'une fiche
close.

Mesuré le 22/09/2026 sur les **18 fiches AN closes** : fenêtres vides sur les
18 — aucun membre, aucun porteur.

## Coût assumé

Les bornes d'une fiche close avancent avec la date des données : ses 18 fiches
(45 Mo, JSON indenté) changent à chaque run, là où elles étaient stables. Le
diff se réduit à quelques lignes de bornes, et `genere_le` suit. L'alternative —
ne pas publier de fenêtre sur une fiche close — a été écartée par la demande :
des bornes qui montrent le vide, lisibles par tout lecteur du fichier.
