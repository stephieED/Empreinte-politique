# La liste des cosignataires d'un amendement est celle de la copie de son premier signataire (#1429) (2026-11-04)

`2026-11-04`

> **En bref** — corrige un postulat de [la normalisation des amendements](normalisation-amendements.md), qui a construit l'index publié sur « chaque copie porte la liste complète, la dernière vue vaut la première » (0 divergence sur 810 552 paires, mesuré le 19/08/2026). Ce n'est plus vrai dès qu'une signature est retirée à la source : 652 des 108 367 amendements de la XVIIe publiaient 8 294 signatures que l'archive ne portait plus (04/11/2026). L'index prend désormais la liste de la copie du **premier signataire**, vide comprise ; sans elle, la dernière copie non vide. Mesuré contre l'archive : cette copie égale la source pour 142 393 des 142 434 amendements de la XVIIe. Les profils, eux, ne sont pas corrigés ici.

## Contexte

L'alerte #1425 (contrôle des signatures, #1248 lot 3) a tiré l'amendement n° I-3250 du PLF 2027 : 8 cosignataires sur la page de l'Assemblée, dans l'open data à l'unité et dans l'archive du 03/11/2026, et 22 dans notre index. Le mécanisme, détaillé dans #1429 :

1. la collecte du 12/10/2026 écrit l'amendement, avec sa liste de 22, dans la tranche de chacun de ses signataires ;
2. 14 signatures sont retirées à la source ;
3. les signataires restés sont recollectés et leurs copies portent la liste de 8 ;
4. la collecte ne rend plus l'amendement aux 14 partants, et la fusion additive garde leur copie ;
5. `amendements_index.construire_index` retenait la liste « vue en dernier », et c'est une copie périmée qui l'a emporté.

Le 04/11/2026, 1 253 des 142 434 amendements de la XVIIe présents dans les tranches de profils avaient des copies divergentes.

## Décision

Arbitrée par la propriétaire le 04/11/2026 (« oui », sur la question « On commence par la deuxième piste : l'index prend la liste de cosignataires de la source ? »). La source n'est pas lue par la construction de l'index, qui ne lit que les profils : la règle prend donc **la copie qui la reflète**, celle du premier signataire (`role_signataire == "auteur_principal"`).

| Copies présentes | Liste retenue |
| --- | --- |
| celle du premier signataire | la sienne, **vide comprise** (tous les cosignataires partis) |
| aucune du premier signataire (auteur sans profil) | la dernière copie non vide, comme avant |
| une copie du premier signataire sans le champ `co_signataires` | ne fait pas foi : une liste non lue n'est pas une liste vide (§2 règle 5) |

`merge_amendements_index` laisse cette liste remplacer celle de l'index précédent, et une liste vide la retire. Une liste qu'aucune copie du premier signataire ne contredit reste, comme avant : un run partiel ne retire rien.

## Mesure (04/11/2026)

Tranches `raw_data/profiles/*/17.json` de `main` (données du 03/11), comparées à l'archive `Amendements.json.zip` de la XVIIe (03/11, 16 h 20) :

| Population : 142 434 amendements de la XVIIe des tranches | Nombre |
| --- | ---: |
| Copie du premier signataire égale à la source | 142 393 |
| Copie du premier signataire différente | 6 (1 à 36 cosignataires en trop ; des retraits postérieurs à la collecte, probablement) |
| Sans copie du premier signataire | 35, dont 30 où l'unique copie égale la source |

## Ce que cette décision ne corrige pas

- **Les profils.** Un député dont la signature a été retirée garde `role_signataire: cosignataire` dans sa tranche et son pivot, donc sur sa fiche et dans les signatures de son groupe (`amendements_agreges.signatures`). Le retrait nommé reste à écrire (#1429, piste 1) : c'est une perte voulue, qui demandera un run avec `allow_declared_losses`.
- **Le contrôle du lot 3** (#1248) continuera de signaler ces profils tant qu'ils ne seront pas corrigés.
- Les XVe et XVIe ne sont pas mesurées : leurs archives sont figées.

## Alternative écartée

- **Lire la liste dans l'archive** au moment de construire l'index : c'est la source elle-même, mais `merge-and-pivot` ne garde pas l'archive (352 Mo pour la XVIIe), et la copie du premier signataire la reflète déjà dans 142 393 cas sur 142 434.
- **La liste majoritaire parmi les copies** : sur l'amendement n° 3250, les 14 copies périmées l'emportaient sur les 9 à jour.
