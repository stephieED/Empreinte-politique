<a id="index-des-decisions-sans-resume"></a>

# L'index des décisions ne recopie plus les résumés, et les deux index se cherchent sans se lire en entier (2026-10-26)

`2026-10-26`

> **En bref** — une liste de lecture remise à une session neuve a rempli **28 % de son contexte** dès le premier message (mesure de la propriétaire, 26/10/2026) : `docs/technical_decisions.md` (**530 Ko**, 541 décisions) et `docs/decisions-par-module.md` (**210 Ko**) en faisaient les deux tiers. L'index ne recopie plus le résumé « En bref » de chaque décision : sa ligne porte la date, les ancres et le titre, et pèse **108 Ko** au lieu de 530. Le résumé reste obligatoire dans le fichier de la décision, qui est la source, et rien n'est perdu. `AGENTS.md` dit, pour les deux index : les chercher, ne jamais les charger en entier. `tests/test_index_decisions.py` refuse un index généré de 300 Ko ou plus.

## Contexte

Chaque ligne de l'index reprenait mot pour mot le résumé de sa décision. Mesuré
sur `main` le 26/10/2026 : 529 736 octets pour les 541 lignes, dont 107 625
pour la date, les ancres et le titre. `docs/decisions-par-module.md`, lui, ne
porte pas les résumés ; sa taille vient du nombre de modules et de décisions
croisés.

## Décision

- `scripts/generer_index_decisions.py` compose la ligne sans « — résumé ».
  `lire_decision` exige toujours le résumé : une décision sans lui reste
  refusée.
- La table « où chercher quoi » d'`AGENTS.md` ajoute « Search it, never load it
  whole » aux deux index. Aucune taille n'y est écrite : elle bouge à chaque
  décision.
- L'index se régénère sur `main` après la fusion, comme toujours (#1174) : la PR
  ne le committe pas.

## Ce que l'on perd

La lecture chronologique par les résumés, que le générateur décrivait comme
ayant « de la valeur en soi ». Un titre dit la décision dans la plupart des cas
(médiane de 86 caractères, 365 titres sur 541 de 80 caractères ou plus), mais pas
toujours : « Données UE — investigation des sources », « Deferred / out-of-scope
investigations », « La suite dit son monde au lieu d'en hériter (#767) » ne
disent pas ce qui a été tranché. Pour ceux-là, il faut ouvrir la décision ou
chercher dans `docs/decisions/`.

## Alternatives écartées

- **Découper l'index par année**, avec un index court des dernières décisions :
  toucher le générateur, son workflow et les liens existants vers
  `technical_decisions.md#<ancre>`, dont des centaines vivent hors du dépôt.
- **Garder la première phrase du résumé**, coupée à environ 150 caractères :
  environ 190 Ko, pour un gain d'usage que la recherche dans les décisions
  donne déjà.
- **La consigne seule**, sans alléger l'index : elle n'empêche pas une lecture
  par erreur.

## Ce qui n'a pas été vérifié

Le nombre de titres qui ne disent pas leur décision : quatre sur quinze lus,
sans compte sur les 541. Aucune session n'a encore été lancée avec l'index
allégé.
