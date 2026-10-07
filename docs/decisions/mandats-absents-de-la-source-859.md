<a id="mandats-absents-de-la-source-859"></a>
# Un mandat que la source devrait porter et ne porte pas se cite à la main, dans un champ à part (#859) (2026-10-06)

`2026-10-06`

> **En bref** — la fiche de Xavier Bertrand commençait au 18/05/2007 dans une période qu'elle disait couverte depuis le 19/06/2002 : **trois mandats** manquaient. Deux causes, mesurées sur l'archive AMO30 : le référentiel ne porte **aucun gouvernement avant le 17/05/2007**, et il ne porte pas son mandat de député de la XIIe. Arbitrage de la propriétaire, 06/10/2026 : **les trois** sont cités depuis leur source primaire. Ils entrent par la table relue de #860, dans un bloc et un champ **à part** — `mandats_absents_de_la_source` —, parce que l'interface publie de `mandats_anterieurs` « exercés avant le 19 juin 2002 ».

## 1. La mesure

Sur `acteurs_historique.zip` (archive AMO30 en cache, datée du 17/08/2026),
relevée le 05/10/2026 et remesurée le 06/10 :

| `typeOrgane` | Mandats | Plus ancien |
| --- | --- | --- |
| `ASSEMBLEE` | 3 954, dont 572 de la XIIe | 19/06/2002 |
| `GOUVERNEMENT` | 659 | **17/05/2007** (Fillon I) |
| `MINISTERE` | 1 162 | 24/12/2002 — un seul avant le 17/05/2007 |

La fiche `PA267080` porte quatre mandats `ASSEMBLEE` : trois de la XIIIe, un de
la XIVe, aucun de la XIIe. Ce n'est pas un défaut de rattachement — l'issue le
supposait —, l'archive ne porte pas le mandat.

Les trois mandats, relus le 06/10/2026 :

| Mandat | Période | Source | Lecture |
| --- | --- | --- | --- |
| Député de l'Aisne, XIIe | 19/06/2002 → 30/04/2004 | Sycomore, fiche 11024 | directe |
| Secrétaire d'État à l'assurance maladie | 31/03/2004 → 31/05/2005 | décrets du 31/03/2004 et du 31/05/2005 | indirecte |
| Ministre de la santé et des solidarités | 02/06/2005 → 26/03/2007 | décrets du 02/06/2005 et du 26/03/2007 | indirecte |

« Indirecte » : Légifrance refuse les requêtes directes (HTTP 403), les décrets
sont lus par une récupération web qui résume la page — même limite, déclarée de
la même façon, que dans `mandats-anterieurs-couverture-860`.

## 2. La décision

**Ce qui était déjà arbitré.** #860 fait entrer les mandats d'avant le
19/06/2002 par une table relue, et sa table refusait toute ligne se terminant
dans la couverture : « un trou après la borne est un autre défaut (#859) ». Le
cas était mis de côté, pas tranché.

**Ce qui l'est maintenant.** Les trois mandats sont cités. Deux appliquent la
règle existante à une borne corrigée — une fonction gouvernementale de 2004 est
antérieure à ce que la source couvre, comme celles de Ségolène Royal le sont à
2002. Le troisième en crée une : citer à la main un mandat que la source couvre
en principe et ne porte pas.

**La forme**, tranchée par l'agent :

- `config/mandats_anterieurs.json` gagne un bloc `absents_de_la_source`
  (`slug → lignes`) ; le bloc `candidats` ne bouge pas, et Xavier Bertrand y
  reste « aucun mandat avant le 19/06/2002 », ce qui est vrai ;
- chaque ligne porte `absence.motif` — `gouvernement_anterieur_a_la_source` ou
  `mandat_non_porte_par_la_source` (`KNOWN_MOTIFS_MANDAT_ABSENT_DE_LA_SOURCE`) —
  et `absence.constate_le`. **Le motif se vérifie sur la ligne** : le premier
  exige une fonction gouvernementale terminée avant
  `BORNE_COUVERTURE_GOUVERNEMENT`, et une telle fonction ne peut pas porter le
  second ;
- sur la fiche, `mandats_absents_de_la_source`, reposé à chaque écriture par
  `appliquer_mandats_absents_de_la_source`, jamais fusionné ; `validate_profil`
  le tient ;
- **non relu n'est pas « aucun »** : un candidat hors du bloc publie `null` et
  `non_relu`. Une liste vide est refusée partout — elle affirmerait « la source
  porte tous ses mandats », ce que personne n'a constaté pour personne.

**Le garde-fou est l'inverse de celui de #860.** Là-bas, une ligne ne doit pas
entrer dans la couverture. Ici, une ligne que le corpus finit par porter — même
catégorie, périodes qui se chevauchent — **n'est plus publiée**, et le run le
signale par un avertissement : la table est à nettoyer. Sans cela, la fiche
citerait à la main ce qu'elle lit déjà à la source, en double.

## 3. Écarté

| Option | Pourquoi |
| --- | --- |
| Ajouter les lignes à `mandats_anterieurs` | quatre lecteurs de l'interface en publient « avant le 19 juin 2002 » (fiche, accueil, `/couverture`, mentions légales) : la phrase serait devenue fausse le jour du run |
| Les verser dans `mandats[]` | la frise les aurait dessinés comme des mandats lus à la source, avec une activité attendue derrière ; #860 a écarté cette forme sur maquette |
| Seulement les deux fonctions gouvernementales | recommandation de l'instruction du 05/10 ; écartée parce que la fiche Sycomore du mandat de député est en main |

## 4. Ce que le lot ne fait pas

- **Rien n'est affiché.** Aucune vue ne lit le nouveau champ. La mention de la
  fiche et sa rédaction sont à la session de l'interface, montrées avant d'être
  écrites.
- **La borne gouvernementale n'est pas encore dans `couverture`.**
  `couverture.mandats` publie toujours une seule borne, le 19/06/2002. La
  déclarer à part y ajoute une entrée dont la `preuve` est un texte que la fiche
  affiche : elle se montre d'abord. La constante existe
  (`mandats_anterieurs.BORNE_COUVERTURE_GOUVERNEMENT`) et la table la publie
  dans son `_meta`.
- **Les autres candidats ne sont pas relus.** 33 des 34 candidats déclarés
  publieront `non_relu`. Rien ne dit si l'un d'eux a un mandat postérieur à 2002
  absent d'AMO30 : seule une comparaison de chacun à Sycomore le dirait.
- **Les dates de Sycomore et d'AMO30 divergent ailleurs sur la même fiche**
  (Sycomore : 15/02/2009 → 15/12/2010 ; AMO30 : 20/06/2007 → 15/12/2010). Vu en
  relisant, non instruit.
