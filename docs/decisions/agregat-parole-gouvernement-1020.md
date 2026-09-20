<a id="agregat-parole-gouvernement-1020"></a>
# La parole d'un gouvernement se compte dans la fenêtre de chaque membre, pas dans celle du gouvernement (#1020) (2026-09-18)

`2026-09-18`

> **En bref** — La fiche de gouvernement ne pouvait pas dire sur quoi ses
> membres ont pris la parole, là où la fiche de groupe le fait. Elle porte
> désormais `tags_thematiques_agreges`, sur le modèle du groupe, **à deux
> divergences près**. La première décide de tout : le groupe filtre par
> législature, un gouvernement doit filtrer par la **fenêtre de passage de
> chaque membre**. Mesuré : sur Borne, 25 704 entrées deviennent 15 750, et
> **Yaël Braun-Pivet passe de 8 968 à 0**.

## Contexte

Besoin remonté par la session « UI gouv » le 18/09/2026, avec l'accord de la
propriétaire. La fiche de lignée consomme `tags_thematiques_agreges` pour sa
section « Sur quoi ils ont pris la parole » ; `schema_gouvernement.py` n'avait
aucun champ équivalent.

La propriétaire a tranché deux points avant l'écriture : reproduire la logique
des groupes, et filtrer par période de gouvernement — **en signalant elle-même
qu'une personne peut n'y être qu'une portion du temps**. C'est cette dernière
remarque qui a fait la mesure ci-dessous.

## Décision

**Le roster dit qui, la fenêtre du membre dit quand, la fabrique d'étiquettes
ne change pas.**

1. `fenetres_des_membres` rend `{membre_id: [(début, fin), …]}` — l'**union**
   des entrées `membres[]` d'une personne, qui en a une par période de
   portefeuille (#398).
2. `agreger_tags_thematiques` retient les interventions datées dans l'une de
   ces fenêtres, puis rappelle `deriver_tags_thematiques` — la fabrique unique
   de #710. Rien n'est dupliqué : le repli `theme_officiel` puis `mots_cles`
   est dedans.
3. **Une étiquette compte une fois par membre.** L'agrégat dit combien de
   personnes ont parlé d'un sujet, jamais combien de fois : un compte
   d'occurrences serait un indice d'activité (§2 règle 1).
4. **Aucun ratio n'est publié.** `nb_membres_porteurs` est rendu seul, son
   dénominateur `comptages.membres_avec_interventions` est publié à côté.

## Divergence 1 — le filtre, et pourquoi il ne peut pas être la législature

Le groupe retient les interventions par la **législature lue dans
l'identifiant**, jamais déduite d'une date (#403, même règle que les votes et
les amendements). Un gouvernement ne peut pas : sa période n'est pas une
législature. Borne court du 17/05/2022 au 09/01/2024, à cheval sur la XVe et
la XVIe. Mesuré sur les interventions de ses 55 membres :

| | |
| --- | ---: |
| Total | 97 898 |
| Législature 15 / 16 / 17 | 33 904 / 34 620 / 29 374 |
| Retenues par un filtre `{15, 16}` | **68 524** |

Sept ans de parole pour un gouvernement de vingt mois. Le filtre est donc la
période, sur la **date publiée** de l'intervention — que la source porte à
99,99 %, 97 893 des 97 898. Ce n'est pas une entorse à #403, qui interdit de
*déduire une législature* d'une date : ici rien n'est déduit, un fait daté est
retenu dans une période que le référentiel déclare.

**Et la fenêtre est celle du membre, pas celle du gouvernement.** C'est la
remarque de la propriétaire, et elle vaut 39 % :

| | Période du gouvernement | Période du membre |
| --- | ---: | ---: |
| Borne | 25 704 | **15 750** |
| Philippe II | 40 719 | **25 264** |

Ce que le filtre grossier faisait entrer est pire que le volume :

| Personne | Fenêtre gouv. | Fenêtre membre |
| --- | ---: | ---: |
| **Yaël Braun-Pivet** (Borne) | 8 968 | **0** |
| **François de Rugy** (Philippe II) | 11 310 | 1 058 |
| Olivier Véran | 2 930 | 838 |

Braun-Pivet a été ministre **trois jours** (24 → 27 juin 2022) avant de
présider l'Assemblée ; de Rugy de même. Leurs interventions dans la fenêtre du
gouvernement sont celles d'une présidence de séance — la parole d'en face, pas
celle du banc. Sans ce filtre, « la parole du gouvernement Borne » aurait été
la leur.

**Sa fenêtre existe grâce à #996 lot 4** : elle vient du mandat libellé
`"Gouvernement"` sans sigle, que l'ancien rattachement par libellé jetait.
Sans lui, Braun-Pivet n'aurait eu aucune fenêtre — et ses 8 968 entrées
seraient passées.

## Divergence 2 — une intervention sans date est écartée

Le groupe **retient** ses entrées sans législature : une donnée manquante ne
permet pas d'exclure. Ici elles sont écartées, et comptées.

La raison n'est pas la même de part et d'autre. Une législature dure cinq ans
et une entrée non datée y tombe probablement ; un gouvernement dure quelques
mois, et rien ne permet de l'y placer. L'y mettre affirmerait sans source
(§2 règle 5). Mesuré : **5 entrées sur 97 898** chez Borne — un choix sans
conséquence de volume, mais qui a une direction.

Les deux comptes partent en `meta.warnings`, jamais en silence.

## Mesuré sur trois fiches, code en place

| | Membres | Avec interventions dans leur fenêtre | Étiquettes |
| --- | ---: | ---: | ---: |
| Borne | 55 | 24 | 881 |
| Philippe II | 50 | 21 | 29 |
| Lecornu II | 39 | 19 | 631 |

**Philippe II rend 29 étiquettes pour 21 membres porteurs**, contre 881 pour
Borne. Ce n'est pas un défaut de ce lot : `theme_officiel` vient de Syceron, et
la XVe n'est pas couverte de la même façon (#657 le constatait déjà, « la 15e
législature n'étant pas mesurable »). La couverture se lit dans
`membres_avec_interventions`, elle n'est pas dissimulée.

## Ce que ce lot ne fait pas

**Il ne collecte rien.** Les 205 profils `roster_gouvernement` de #996 portent
`interventions: []` : la collecte a été déclarée écartée au run qui les a
créés. `membres_avec_interventions` vaut donc 24 sur 55 chez Borne, et le dira
tant que ce sera vrai. Un run avec `collect_interventions: true` les collectera
en mode réduit au thème — le mécanisme existe depuis #657, et c'est exactement
ce qu'il a fait pour les groupes, dont l'empreinte est passée de « celle d'une
seule personne » à 76 porteurs sur 76.

**Il ne dit pas qui a dit quoi.** Le rattachement d'une prise de parole à son
auteur dans la fiche est un besoin distinct, posé par « UI gouv » et non
traité ici.

## Alternative rejetée

**Filtrer par la ou les législatures du gouvernement**, pour coller à la lettre
au modèle du groupe. Mesuré ci-dessus : +53 000 entrées sur Borne, dont la
totalité de la parole de sa présidente d'Assemblée.

**Publier `poids_relatif` comme le fait `tags_thematiques_agreges` du groupe.**
Rejeté par le précédent du dépôt lui-même : `mandats_agreges` a retiré ce champ
au profit d'un dénominateur publié, « pour que le lecteur voie *5 / 76* et non
un pourcentage seul (§2.7) ». L'agrégat du groupe n'a pas suivi ; le nouveau ne
reproduit pas ce retard. Aligner celui du groupe est un lot à part, sur des
fiches déjà publiées et déjà lues.
