<a id="table-figee-numero-de-loi-vers-jorftext"></a>
# La jointure loi → acte passe par une table figée du numéro de loi (2026-09-23)

`2026-09-23`

> **En bref** — Les actes désignent une loi par son identifiant au Journal officiel, les archives de l'Assemblée par son numéro — et par son NOR, absent sur 412 des 1 015 textes promulgués. Joindre par le NOR laissait donc 40 % des textes sans leurs actes. `raw_data/lois_jorf.json` fait le pont par le numéro : construite une fois sur le fonds (8 820 numéros, 0,83 Mo), puis tenue à jour par les livraisons que le run lit déjà.

## Constat

Deux sources, deux façons de nommer la même loi :

| Côté | Ce qu'il publie |
| --- | --- |
| `pivot_data/actes_reglementaires/` (Journal officiel) | l'identifiant `JORFTEXT` de la loi appliquée ou citée |
| `pivot_data/textes_promulgues.json` (archives de l'Assemblée) | le **numéro** de loi (`2013-595`), et le **NOR** sur 603 des 1 015 seulement — l'archive de la XIVe ne le publie pas |

Mesuré le 23/09/2026 : la jointure par NOR résout **603 / 1 015**, celle par
numéro **1 015 / 1 015**. Sans table, l'interface lisait une colonne dont 40 %
des lignes n'avaient aucun acte — non parce qu'il n'y en a pas, mais parce que la
clé manquait.

## Décision

1. **Une table figée, committée sous `raw_data/`**, comme les index de
   législatures closes : `numéro de loi → [[identifiant JORFTEXT, date], …]`.
   8 820 numéros, 0,83 Mo, construite en une lecture du fonds le 23/09/2026.
2. **Elle se tient à jour sans appel réseau de plus** : une loi promulguée paraît
   dans la même livraison quotidienne que les actes, que l'étape
   `actes_reglementaires` parcourt déjà. Elle note les lois en chemin et fusionne
   avec la table committée.
3. **Un numéro garde ses deux enregistrements** quand la source publie la loi
   deux fois — l'original et son rectificatif, 106 cas sur les 1 754 numéros
   depuis 2007 (`2007-1544` → 30/10/2007 et 10/11/2007). Un acte peut citer l'un
   ou l'autre ; n'en garder qu'un ferait échouer la jointure sans le dire. La
   publication d'origine est en tête, et `textes_promulgues.json` publie
   `jorftext` puis `jorftext_autres`.
4. **Un numéro non résolu reste `null`** : l'absence se déclare (§2 règle 5).

## Alternatives rejetées

| Écartée | Pourquoi |
| --- | --- |
| Joindre par le NOR | 603 / 1 015 — et l'échec porte sur toute une législature, donc sur une période entière de l'histoire publiée |
| Répéter le NOR de la loi sur chaque acte | alourdit 238 fichiers pour une information qui appartient à la loi, et ne résout toujours pas la XIVe |
| Lire le fonds à chaque run pour résoudre à la volée | 25 minutes de réseau par run, pour une correspondance qui ne bouge que d'une poignée de lignes par semaine |
