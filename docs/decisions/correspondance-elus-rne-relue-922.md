<a id="correspondance-elus-rne-relue-922"></a>
# Apparier un candidat à un élu du RNE : par la date de naissance, sinon par relecture (#922) (2026-09-15)

`2026-09-15`

> **En bref** — Le RNE n'expose aucun identifiant de personne. La clé praticable
> est `(nom, prénom, date de naissance)`, et elle résout **17 des 32 candidats
> déclarés** sans intervention. Les 15 autres n'ont pas de date de naissance
> chez nous : apparier au nom seul a déjà produit un faux positif (#885), et le
> nom + prénom seuls en produisent encore un — Nathalie Arthaud à
> Limey-Remenauville. D'où une table **committée et relue**, sur le patron de
> #860 et #525. Elle identifie une **personne**, jamais un mandat : elle ne se
> périme pas quand les mandats changent.

## Contexte

#922 veut publier les mandats locaux, absents de tout le corpus. La source
existe — le Répertoire national des élus, Licence Ouverte 2.0 — mais elle ne
publie **aucun identifiant de personne**. L'appariement se fait sur l'état civil.

## Ce que la mesure a établi, le 14 et le 15/09/2026

**Sur les 32 candidats déclarés à slug résolvable, 17 portent une date de
naissance** (toutes venues d'`assemblee_nationale`). Pour eux, l'appariement est
automatique et sûr : seules 4 personnes de tout le RNE sont nées le 28/11/1970,
et une seule s'appelle Philippe.

**Les 15 autres se répartissent en deux populations que rien ne distingue sur
disque** :

| | n | |
| --- | ---: | --- |
| Députés européens | 4 | Bardella, Philippot, Massard, Glucksmann — leur date de naissance **est déjà collectée**, sous `mandat_europeen.date_naissance`, et n'atteint pas `identite` |
| Sans aucun mandat | 11 | aucune de nos trois sources institutionnelles ne les résout |

**Trois pièges, tous payés en mesurant** :

1. **Le patronyme seul ne veut rien dire.** 400 « MATHIEU » chez les conseillers
   municipaux, 148 « VERDIER », 93 « LALANNE ». Avec le prénom : 0, 1 et 0.
2. **Les diacritiques sont incohérents dans la source.** « Edouard » sans accent
   et « Jérôme » avec, dans le même fichier. Apparier sur le prénom tel qu'écrit
   rendait **Édouard Philippe sans aucun mandat**, alors qu'il est maire du
   Havre — un échec entièrement silencieux.
3. **Deux fichiers sur neuf ne suffisent pas.** Marine Tondelier est absente des
   conseillers municipaux en cours (son mandat s'est achevé en mars 2026) : elle
   est dans le fichier **régional**. S'arrêter aux deux premiers aurait conclu
   « aucun mandat local ».

## Décision

1. **La date de naissance est la clé quand le corpus la porte.** 17 candidats
   sur 32, sans relecture. Elle règle du même coup le problème des diacritiques.

2. **Sinon, une relecture humaine**, consignée dans
   `raw_data/correspondance_elus_rne.json` — table committée, une ligne par
   candidat relu, avec sa preuve. Le patron est celui de `mandats_anterieurs.json`
   (#860) et de la correspondance slug ↔ acteur AN (#525).

3. **La table identifie une personne, pas un mandat.** C'est ce qui rend le
   process soutenable : une relecture par candidat, une fois, qui survit aux
   municipales. Les mandats, eux, sont relus à chaque run.

4. **Trois verdicts fermés** — `confirme`, `ecarte`, `aucun_mandat_trouve` — et
   le contrat de relevé de #860 : un candidat **présent** a été relu, son verdict
   est complet pour les neuf fichiers ; un candidat **absent** n'a pas été relu,
   et sa fiche doit le dire. Absent n'est pas « aucun mandat » (§2 règle 5).

5. **Deux silences ne se valent pas.** Quatre candidats ont une page Wikipédia où
   aucun mandat local ne figure : l'absence est corroborée. Deux n'ont aucune
   page : `corroboration: "absente"` le dit, plutôt que de les publier pareil.

## La date de naissance dans la table n'est pas circulaire

L'issue redoutait, à juste titre, qu'on valide l'appariement par la donnée qu'il
a produite. Une ligne `confirme` porte pourtant la date de naissance telle que le
RNE l'écrit — et ce n'est pas elle qui établit l'appariement : c'est la
relecture, sur la commune et une source primaire. Elle sert à **retrouver** les
lignes de la personne au run suivant sans dépendre de l'orthographe.

**Elle ne doit jamais être reversée dans `identite.date_naissance`** : ce serait
publier comme fait sur la personne une valeur qu'aucune de nos sources
institutionnelles ne rend. Un test le verrouille par le `_meta`.

## L'alternative rejetée

**Apparier au nom et au prénom sans relecture.** Elle a été mesurée, et elle
échoue sur un cas des cinq : Nathalie Arthaud apparaît **une seule fois** dans
tout le RNE, à Limey-Remenauville — 300 habitants, Meurthe-et-Moselle. La
candidate a été conseillère municipale de **Vaulx-en-Velin** en 2008, et la date
de naissance de la ligne ne correspond pas à la sienne. **Une correspondance
unique ne prouve pas l'identité** : c'est la forme exacte du faux positif
`jean-louis-masson` de #885.

## Ce que la table ne couvre pas, et qui se déclare

Le RNE ne porte que les mandats **en cours**. Un mandat achevé n'y est pas, et
son absence n'en est pas la négation : le mandat municipal de Nathalie Arthaud,
commencé en 2008, n'est porté par aucun jeu accessible. Le fichier des sortants
2020-2026 (Licence Ouverte 2.0 lui aussi) comble la mandature précédente ; le
palier 2014 reste à instruire.
