<a id="avertissements-europeens-reecrits-1161"></a>

# Deux avertissements européens ne se lisent plus tels quels sur la fiche candidat (#1161) (2026-10-08)

`2026-10-08`

> **En bref** — `docs/decisions/destinataire-avertissements-642.md` fait afficher par la fiche les avertissements de `meta.avertissements` dont le destinataire est `lecteur`. Deux d'entre eux, écrits côté données pour les mandats européens, sortaient mot pour mot dans « Ce qu'on n'a pas pu lire ». Arbitré par la propriétaire sur maquette le 02/10/2026, livré le 08/10 : **« votes non publiés » n'est plus adressé au lecteur, « explications de vote » est réécrit**. Le filtre et la réécriture sont faits **par l'interface** ; les données, elles, n'ont pas changé.

## Le contexte

Mesuré le 08/10/2026 sur `main` 98327b0c0, sur les 35 profils de candidats :

| Message, destinataire `lecteur` | Fiches | Ce que le lecteur voyait |
| --- | ---: | --- |
| « Parlement européen — votes non publiés : N scrutin(s)… » | 6 | « 19840 scrutin(s) du Parlement européen portent sur un amendement… » |
| « Parlement européen — explications de vote : N des M explication(s)… » | 5 | « 48 des 48 explication(s) de vote sont publiées sans lien… ParlTrack transcrit l'annexe… » |

## La décision

- **Votes non publiés** : plus affiché. Il dit un choix, pas un manque, et rien
  ne dit la même chose côté français.
- **Explications de vote** : intitulé « Explications de vote au Parlement
  européen », texte « Ses 48 explications de vote sont publiées sans lien vers
  le document officiel. » — sans « (s) », sans parenthèse, sans le nom de la
  source.
- Deux variantes écrites par l'agent, confirmées par la propriétaire le
  08/10/2026 : « 46 de ses 683 explications de vote sont publiées… » quand une
  partie seulement l'est, « 1 de ses 49 explications de vote est publiée… » au
  singulier.
- `explicationsSansLien` (`profilCandidat.js`) relit les deux nombres dans le
  message. **Un message qui ne suit pas la forme attendue reste affiché tel
  quel** : on ne fait pas disparaître ce qu'on n'a pas su lire. PR #1256.

Dans la même PR, deux autres points de #1161 : le type `explication_de_vote` du
Parlement européen prend le libellé « Explications de vote » (5 fiches) ; la
mention « aucune fiche n'est publiée pour les groupes où cette personne a
siégé » ne s'affiche plus pour une personne sans mandat parlementaire.

## L'alternative écartée

Corriger les deux messages là où ils sont écrits, côté données
(`src/merge_profile.py`, `src/normalize_parltrack_dumps.py`). C'est la voie la
plus propre et elle reste ouverte ; l'interface a été corrigée d'abord parce que
le défaut était à l'écran.

## Ce qui reste

- Si la forme d'un des deux messages change côté données, il ressort brut.
- Un troisième message brut, hors de l'issue : « ParlTrack: aucune donnée
  trouvée pour le député européen (identifiant ParlTrack 131580)… » sur le profil
  de Jordan Bardella. Non vérifié : s'il s'affiche, son profil étant gelé.
- Non vérifié à l'écran.
