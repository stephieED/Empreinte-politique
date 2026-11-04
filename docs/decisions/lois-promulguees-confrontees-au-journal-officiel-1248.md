# Nos textes promulgués confrontés aux lois du Journal officiel, à chaque run (#1248) (2026-11-04)

`2026-11-04`

> **En bref** — le deuxième contrôle de totaux de #1248, et le seul indépendant de l'Assemblée : la table des lois du Journal officiel (DILA) contre nos textes promulgués (archives de l'AN), par numéro de loi, dans les deux sens. Ne sont signalées ni les 71 lois que l'open data de l'AN ne porte pas (déclarées, #1424), ni celles publiées après nos dossiers. Mesuré le 04/11/2026 : 1 091 lois du JO depuis le 20/06/2012, 0 écart.

## Contexte

Proposé le 03/11/2026 parmi les contrôles de totaux (« un indicateur de complétude de notre collecte en croisant les totaux… avec une autre source »), recommandé avec celui des scrutins parce que le Journal officiel est **la seule source indépendante de l'Assemblée**. Son premier croisement a ouvert #1424 : 71 lois absentes, et la table du JO jamais commitée. La première est un trou de la source, déclaré (`lois-absentes-de-l-open-data-an-1424`) ; la seconde est corrigée (#1434). Lancé par la propriétaire le 04/11/2026 (« controle des lois promulgués (1248) »).

## Décision

| Constat | Traitement |
| --- | --- |
| loi du JO (lois et lois organiques, depuis le 20/06/2012) absente de nos textes, déclarée dans `config/lois_absentes_open_data_an.json` | relevée, pas signalée |
| la même, publiée au JO après la date `an.dossiers` du fichier de fraîcheur | relevée, pas signalée : les dossiers de l'AN sont relevés chaque semaine, une loi plus récente n'est pas encore relue |
| la même, autrement | **signalée** |
| un de nos textes promulgués dont le numéro manque à la table du JO | **signalé** |
| une loi déclarée absente que nous publions | **signalée** : la liste est à revoir |

Même régime que les relectures : un signalement, une issue que le run ne ferme jamais (`lois-en-ecart-avec-la-source`), rien ne bloque. Une table ou des textes illisibles rendent le contrôle « non vérifié ».

## Mesure (04/11/2026, table et textes du run du 03/11)

| Population | Nombre |
| --- | ---: |
| Lois publiées au JO depuis le 20/06/2012 | 1 091 |
| … publiées chez nous | 1 019 |
| … déclarées absentes de l'open data de l'AN | 71 |
| … pas encore relues (2026-1015, publiée le 03/11, dossiers à jour au 02/11) | 1 |
| Écarts | 0 |

1 020 textes promulgués portent 1 019 numéros : la loi 2017-1338 l'est par deux uids de dossier (`DLR5L14N35824`, `DLR5L15N35824`). Relevé ici, non instruit.

## Ce qui n'a pas été vérifié

- Les lois constitutionnelles : la table du JO ne retient que les natures `LOI` et `LOI_ORGANIQUE`. Notre seule loi constitutionnelle publiée y figure pourtant (0 de nos numéros ne manque à la table) ; le contrôle signalerait la suivante si ce n'était pas le cas.
- **Ordre de fusion** : sans `config/lois_absentes_open_data_an.json` (PR #1435), les 71 lois seraient signalées comme perdues. #1435 doit être fusionnée avant celle-ci, ou publiée avec elle.
