<a id="fin-de-mandat-reportee"></a>
# Une date de fin de mandat publiée après la première collecte est reportée (2026-10-08)

`2026-10-08`

> **En bref** — signalé par la session COM (article « violences sexuelles et sexistes ») : la commission spéciale « réponse intégrale » (`PO884839`) compte 125 mandats, dont 118 sans fin chez nous contre 88 à l'Assemblée. Mesuré sur tout le corpus contre AMO30 du 08/10/2026 : **au moins 767 mandats publiés « en cours » sur 273 profils sont fermés à la source**. La clé d'un mandat ne contient pas sa fin, et la fusion additive garde l'entrée ancienne : un mandat collecté ouvert le restait pour toujours. `merge_profile.backfill_mandat_fin` reporte désormais la fin, aux deux couches.

## 1. La mesure

Profils pivot de main `3665078d3` rapprochés d'AMO30 du 08/10/2026, par acteur, libellé de l'organe et date de début. C'est un minimum : un mandat dont le libellé ne se rapproche pas n'est pas compté.

| Catégorie | Mandats fermés à la source, ouverts chez nous |
| --- | ---: |
| commission | 428 |
| groupe d'amitié | 103 |
| groupe d'études | 72 |
| commission d'enquête et spéciale | 71 |
| mission d'information | 36 |
| délégation | 29 |
| extra-parlementaire | 14 |
| fonction gouvernementale | 11 |
| autre | 3 |
| **Total** | **767, sur 273 profils**, parmi 12 874 mandats de l'Assemblée publiés sans fin |

## 2. La décision

- `backfill_mandat_fin` se place juste après la fusion par clé, au brut (`_mandat_key`) comme au pivot (`_pivot_mandat_key`), à côté des autres reports (`backfill_mandat_lieu_election`, #682).
- **La collecte du jour l'emporte dès qu'elle porte une fin**, y compris pour corriger une fin déjà publiée : c'est la source qui dit quand le mandat s'est terminé. `actif` suit.
- **Une fin publiée n'est jamais effacée** par une collecte qui n'en porte pas.

Rejoué sur six profils réels (collecte par `_extract_mandats_officiels` sur AMO30 du 08/10, puis `merge_raw_profile`) : Anne Stambach-Terrenoir reçoit sa fin du 22/09, Christian Baptiste ses deux périodes, Agnès Canayer passe de 3 mandats ouverts à 0. Aucun mandat n'est perdu.

## 3. La limite

AMO30 est renouvelé une fois par semaine en CI (#555, péremption au changement de semaine). Une fin publiée en cours de semaine atteint donc la fiche au plus tard la semaine suivante.
