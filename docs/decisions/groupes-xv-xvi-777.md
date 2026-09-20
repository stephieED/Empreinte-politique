# Sept groupes des XVe et XVIe entrent, LaREM en sort sur son coût (#777, #779)

`2026-09-08`

> **En bref** — #706 parlait de 2 groupes sans fiche puis de 4 ; remesuré sur les **27 candidats déclarés** avec `correspondance_sigles_an` pour autorité, c'est **19 couples touchés, 4 couverts, 15 sans fiche** — l'écart vient de la population, passée de 13 à 27, et le chiffre du ROADMAP porte lui aussi sur les 13 d'alors ; **le sigle ne se déduit pas, et deux cas sur huit l'ont prouvé** : le mandat dit « Ecolo - NUPES » quand l'organe s'appelle `ECOLO`, « GDR - NUPES » quand il s'appelle `GDR-NUPES`, d'où huit organes relus un par un dans l'index AMO30 ; **LaREM XVe sort sur une mesure** — 343 membres et 227 profils à collecter pour **un** bénéficiaire déjà publié, contre 72 pour les sept autres et six candidats servis —, et le chiffre qui tranche n'est pas le disque mais `merge-and-pivot`, seul job qui écrit : marge tombant de ×2,0 à ×1,5 sur son timeout de 60, quand un job tué par son timeout n'écrit rien (#498) ; **vérifié après coup**, le run `34241352524` a publié les sept fiches en **21,6 min**, marge ×2,8 ; reprise conditionnée à #691 ; sept gardes figeaient un nombre (« 10 entrées », « {16, 17} », « 456 membres ») et lisent désormais ce qu'elles vérifient — l'une cachait un `TypeError` sur `effectif_publie: null`, l'état normal d'une entrée non encore parue ; **ce que le lot n'a pas produit** : les 72 profils, le run n'ayant récupéré aucun artifact d'extraction.

## Le périmètre, remesuré

#706 parlait de 2 groupes sans fiche, puis de 4 après relecture. Mesuré le
08/09/2026 sur les **27 candidats déclarés** publiés, avec
`correspondance_sigles_an` comme autorité : **19 couples (groupe, législature)
touchés, 4 couverts, 15 sans fiche.**

L'écart vient de la population, pas de la méthode : elle est passée de 13 à 27
candidats déclarés entre les deux mesures. Le chiffre du `ROADMAP` — « parmi les
9 groupes qu'ils ont touchés, quatre sont hors d'atteinte » — porte lui aussi sur
les 13 d'alors.

| Législature | Sans fiche | Statut |
| --- | --- | --- |
| XVIe | 2 | publiées par ce lot |
| XVe | 6 | 5 publiées, LaREM différée (#779) |
| XIVe | 5 | arbitrage ouvert |
| XIIIe | 2 | hors d'atteinte : les scrutins commencent au 03/07/2012 |

## Le sigle ne se déduit pas, et deux cas l'ont prouvé

La table interdit de deviner un sigle (« `RE` ne se déduit pas de `REN` »). Le
piège s'est présenté deux fois sur huit :

- le mandat d'un candidat dit « **Ecolo - NUPES** », l'organe s'appelle `ECOLO` ;
- il dit « **GDR - NUPES** », l'organe s'appelle `GDR-NUPES`.

Une normalisation mécanique aurait produit deux sigles faux. Les huit organes ont
donc été relus un par un dans l'index AMO30 des groupes politiques, avec leur
`libelleAbrev`, leurs bornes et leur position déclarée.

## LaREM sort sur une mesure, pas sur un principe

| | Les sept | LaREM XVe seul |
| --- | ---: | ---: |
| Membres | 108 | **343** |
| Profils à collecter | **72** | **227** |
| Bénéficiaires | 6 candidats | **1** (Attal, déjà publié) |

Projeté sur les mesures réelles du run `34168924759` (652 profils, 77 min) :
`raw_data/profiles` à ~10,1 Go avec les sept contre ~13,5 Go avec LaREM, et
surtout **`merge-and-pivot` à ~30 min contre ~40**, soit une marge tombant de
×2,0 à ×1,5 sur son `timeout-minutes: 60`.

C'est ce dernier chiffre qui a tranché, et pas le disque : `merge-and-pivot` est
le **seul job qui écrit**, et tué par son timeout il n'écrit rien — toute la
collecte du run est alors perdue (#498). La règle du dépôt interdit de relever un
timeout sans mesurer ; réduire le lot était le geste symétrique.

**Vérifié après coup** : le run `34241352524` a publié les sept fiches avec
`merge-and-pivot` à **21,6 min**, marge ×2,8. La projection était juste, et
prudente.

La condition de reprise de LaREM est **#691** — les tranches d'amendements du
roster recopient 4,58 Gio déjà versionnés en 38 Mo pour les législatures 14/15/16,
ce qui est exactement ce qui rend un député de la XVe cher (médiane mesurée :
11,6 Mo). Rouvrir avant, c'est payer deux fois la même donnée.

## Sept gardes figeaient un nombre

Les assertions encodaient le périmètre de #700 — « 10 entrées », « les
législatures {16, 17} », « les cinq rosters de la 16e », « 456 membres ». Elles
lisent désormais ce qu'elles vérifient : le compte vient du fichier, les
législatures couvertes se lisent, et les comparaisons d'effectif se restreignent
aux entrées **publiées**.

L'une cachait un vrai défaut : `effectif_publie: null` moins un entier levait un
`TypeError` qui se lisait comme un défaut de données, alors que c'est l'état
normal d'une entrée configurée non encore parue.

Figer un nombre oblige à toucher quatre tests à chaque groupe publié — c'est-à-dire
à faire de la garde une formalité, et une formalité, on la met à jour sans la lire.

## Ce que le lot n'a pas produit

Les 72 profils de roster annoncés : le run qui a publié les fiches n'a récupéré
**aucun artifact d'extraction**, et les a donc bâties sur les profils déjà
committés. `effectif_publie` reste `null` sur les sept entrées jusqu'à un run
dont la collecte atteint `merge-and-pivot`. Voir #775 pour ce défaut de transport.
