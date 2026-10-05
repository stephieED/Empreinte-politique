<a id="lieu-d-election-sur-le-mandat-682"></a>
# Le lieu d'élection se porte sur le mandat, en entier, et non sur la personne (#682) (2026-10-05)

`2026-10-05`

> **En bref** — `identite.num_circo` valait « 6 » pour Jérôme Guedj, sans département : un numéro seul ne désigne aucune circonscription. AMO30 porte le lieu d'élection, complet, sur **chacun des 3 954 mandats de député**, et le pipeline n'en gardait qu'un champ sur cinq, rangé sur la personne. Chaque `mandat_electif` de l'Assemblée publie désormais `lieu_election` ; `identite.num_circo` reste publié à côté, avec une condition de retrait écrite.

## 1. Le constat

Relevé de l'issue, remesuré le 05/10/2026 sur l'archive AMO30 en cache et sur
le privé `2140244c4`.

| | Mesure |
| --- | --- |
| mandats `typeOrgane == "ASSEMBLEE"` de l'archive | 3 954 |
| dont `election.lieu` porte ses cinq champs | 3 954 |
| acteurs élus dans plus d'une circonscription | 54 |
| profils publiés dont la personne en a changé | 23, dont un candidat déclaré (Bernard Cazeneuve, 5e puis 4e de la Manche) |
| profils publiés portant `identite.num_circo` | 1 262 sur 1 402 |

Deux défauts : la projection gardait un champ sur cinq, celui qui ne veut rien
dire seul ; et elle le rangeait sur la personne, alors qu'une circonscription
qualifie un mandat — le défaut de niveau que #492 a corrigé pour `chambre`.

## 2. La décision

1. `candidate_profile._lieu_election` relève `election.lieu` d'un mandat ;
   `_periodes_mandats_assemblee` le pose sur chaque période. Les valeurs sont
   **recopiées telles que la source les écrit** — elle écrit « Normandie » pour
   un mandat de 2007, et ce n'est pas à nous de le corriger.
2. `mandats[].lieu_election`, sur les seuls `mandat_electif` :
   `{region, type_region, departement, num_departement, num_circo}`. Clé
   **facultative** : `null` si la source n'a pas de lieu, **absente** d'un mandat
   collecté avant ce lot — même arbitrage que `categorie_source` (#718).
3. `backfill_mandat_lieu_election`, aux deux étages : la clé d'un mandat ne
   contient pas le lieu, donc l'entrée déjà publiée ne le recevrait jamais.
4. `NOM_INDEX_IDENTITE` passe à `v5` : l'index d'identité en cache ne porte pas
   le lieu.
5. `validate_profil` refuse un lieu incomplet, et un lieu porté par autre chose
   qu'un mandat électif.

## 3. `identite.num_circo` reste, et voici quand il part

Le retirer est la régression d'un scalaire surveillé par le contrôle de perte :
elle se déclare, et demande un run à pertes déclarées pour un champ que plus
rien ne devrait lire. Le garder en doublon sans condition ferait du transitoire
un définitif par omission.

**Condition de retrait** : quand l'interface lit `mandats[].lieu_election` et
qu'aucun fichier de `web/UI_finale/src` ne lit plus `num_circo`. Le retrait est
alors un lot à lui, avec sa déclaration de perte.

## 4. Ce qui n'est pas vérifié

- Le corpus : le versement se mesure après un run. L'index d'identité est
  reconstruit à chaque version ; aucune case particulière n'est requise.
- Les mandats sénatoriaux et européens : ils ne portent pas ce champ, et le lot
  ne leur en donne pas. Le Sénat publie une circonscription d'une autre forme
  (le département) ; non instruit.

## 5. Ce que l'interface peut en faire

Rien n'est affiché par ce lot. « Député de l'Essonne (6e circonscription) » peut
maintenant s'écrire sans rien inventer ; c'est un texte publié, à montrer avant
d'être codé.
