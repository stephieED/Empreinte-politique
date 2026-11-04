# 71 lois promulguées manquent à l'open data de l'Assemblée : le trou est déclaré, pas comblé (#1424) (2026-11-04)

`2026-11-04`

> **En bref** — des 1 085 lois publiées au Journal officiel depuis le début de la XIVe, 71 n'ont leur promulgation dans aucune des quatre archives `Dossiers_Legislatifs` de l'Assemblée (2012 à 2020). Ce n'est pas un défaut de notre lecture : toute promulgation présente porte son numéro. C'est un trou de la source, vérifié sur un cas : un dossier ouvert sous la XIVe et promulgué sous la XVe manque à l'archive de la XVe. Le trou est **déclaré** dans `config/lois_absentes_open_data_an.json`, il n'est pas comblé depuis le site de l'Assemblée.

## Contexte

Le contrôle de complétude des lois promulguées (#1248) croise la table du Journal officiel (`raw_data/lois_jorf.json`) avec nos textes promulgués (`pivot_data/textes_promulgues.json`). Le premier croisement, le 03/11/2026, a trouvé 71 lois absentes, ce qui a ouvert #1424. Le même croisement a montré que la table du Journal officiel n'était jamais commitée : c'est corrigé à part, en #1434.

## Ce que la mesure a établi (04/11/2026)

| Archive | Dossiers | Promulgations (`PROM-PUB`) | sans `codeLoi` | Dossiers d'une autre législature |
| --- | ---: | ---: | ---: | ---: |
| XIVe (un fichier, figé le 09/03/2018) | 3 432 | 412 | 0 | 0 |
| XVe | 4 980 | 319 | 0 | 0 |
| XVIe | 2 943 | 147 | 0 | 149 |
| XVIIe | 3 390 | 153 | 0 | 196 |

- 69 des 71 numéros n'apparaissent dans aucune archive ; 2 n'y sont que cités par un autre dossier.
- Cas vérifié : la loi 2018-287 (droit des contrats). Son dossier `DLR5L14N35818` est dans l'archive de la XIVe, sans promulgation ; il est absent de celle de la XVe ; le site de l'Assemblée affiche « Loi n°2018-287 du vendredi 20 avril 2018 ». Nous le publions « navette en cours », le dernier acte que porte la source.
- Par année de publication : 2012 : 16, 2013 : 16, 2014 : 11, 2015 : 8, 2016 : 1, 2018 : 12, 2019 : 5, 2020 : 2.

## Décision

Arbitrée par la propriétaire le 04/11/2026 (« oui », sur la question « On déclare ce trou de la source (documentation de la source, et une liste des lois absentes de l'open data pour le futur contrôle des lois), sans compléter depuis le site ? »).

- `config/lois_absentes_open_data_an.json` liste les 71 lois (numéro, `JORFTEXT`, date de publication), avec la méthode et la cause vérifiée. Elle est écrite à la main, une fois : aucun run ne l'écrit (`config/`, #1057).
- `pivot_data/textes_promulgues.json` ne les porte pas, et rien ne les y ajoute. Un dossier comme `DLR5L14N35818` garde le statut que porte la source.
- Le futur contrôle des lois promulguées (#1248) lira cette liste : une loi qui y figure n'est pas un écart de notre collecte ; une loi absente qui n'y figure pas en est un.

## Alternative écartée

- **Compléter depuis le site de l'Assemblée** : retrouver chaque dossier et lire sa page, pour 71 lois sur 1 085. C'est une nouvelle forme de collecte (pages du site, et non open data), à décider pour elle-même ; la page du site ne fait pas partie des sources collectées des textes promulgués.

## Ce qui n'a pas été vérifié

- La cause pour les 70 autres lois, en particulier les 20 de 2014 à 2016 : elle demanderait des dossiers ouverts sous la XIIIe. Légifrance bloque les robots et les livraisons de la DILA ne remontent qu'à 2025, ce qui empêche de lire leur titre par leur numéro.
- Le nombre de dossiers publiés avec un statut que le site contredit : le champ `statut` suit le dernier acte, pas la promulgation, et ne permet pas de les repérer.
