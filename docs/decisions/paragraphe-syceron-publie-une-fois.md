<a id="paragraphe-syceron-publie-une-fois"></a>
# Un paragraphe de compte rendu republié sous un autre rang n'est publié qu'une fois (2026-10-08)

`2026-10-08`

> **En bref** — signalé par la session interface le 08/10/2026 (consigné dans #1261), remesuré sur main `3665078d3` : **643 prises de parole en trop sur 81 profils**, chaque fois le même paragraphe de l'Assemblée (`id_syceron`) publié sous deux ou trois identifiants. 399 d'octobre 2026 : l'Assemblée a republié les comptes rendus de la session ouverte le 01/10 en les renumérotant, et notre identifiant porte le rang du paragraphe. 244 de février 2021 et juillet 2017 : le même paragraphe sous un identifiant de la XVe et un de la XVIe. Le premier cas se reproduirait à chaque run de la session, et gonflait les comptes d'octobre d'environ 17 %. Arbitrage de la propriétaire, 08/10 : corriger avant le run de 18:01. `merge_profile.dedoublonner_paragraphes_syceron` ferme désormais la fusion des interventions, au brut comme au pivot.

## 1. La mesure

| Doublons | Entrées en trop | Profils |
| --- | ---: | ---: |
| Octobre 2026 (`…S2027O1…`, comptes rendus renumérotés) | 399 | 40 |
| Février 2021 et juillet 2017 (préfixe XVe / XVIe) | 244 | 42 (1 en commun avec octobre) |
| Total | **643** | **81** |

Les 497 groupes de doublons sont le même paragraphe : même date, même texte. Trois diffèrent par une coquille que la republication a corrigée (« çà » → « ça »). `id_syceron` est donc stable et unique.

Rejoué sur les 81 profils réels : `merge_pivot_profile` et `merge_raw_profile` retirent chacun **643** entrées, rien d'autre.

## 2. La décision

- **Qui reste** : la forme la plus riche (jamais une forme plus pauvre, #1029), puis la copie que la collecte du jour vient de rendre (numérotation et texte actuels de la source), puis la première. Elle prend la place de la première copie.
- **Aux deux couches**, dans la fusion elle-même et pas comme retrait nommé à part : le défaut est une identité instable, il se reproduirait à chaque run. Le brut reste fidèle à ce que la source publie *aujourd'hui* : un paragraphe, une fois.
- **La garde « collecté = publié » rejoue la même fonction** dans la réduction de la relation `interventions`, *avant* le retrait de #1177 : additionner les deux comptes retirerait deux fois un paragraphe à la fois doublé et retiré.
- Seules les prises de parole Syceron sont concernées (identifiant `syceron_…` et `id_syceron` renseigné). Une question écrite ou une parole européenne n'est jamais dédoublonnée.

## 3. Alternatives écartées

- **Changer la clé de fusion pour `id_syceron`** : la fusion additive garde l'ancienne liste entière, donc les copies déjà publiées seraient restées. Elle aurait aussi gardé l'ancien rang plutôt que celui que la source publie.
- **Ne corriger qu'au pivot** : le brut aurait gardé les copies, et la garde « collecté = publié » aurait lu 643 entrées collectées et publiées nulle part.
