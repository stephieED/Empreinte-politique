<a id="sortants-annee-decalee-922"></a>
# Le fichier des sortants a vieilli ses élus d'un siècle, et cinq mandats ont disparu (#922) (2026-09-16)

`2026-09-16`

> **En bref** — Dans le fichier des sortants des municipales 2026, les dates de
> naissance ont pris un siècle : David Lisnard, né en 1969, y est né en **2069**.
> Interrogé sur la seule date exacte, le fichier ne rendait rien, et **5 mandats
> 2020-2026** de candidats déclarés ont disparu sans erreur — Lisnard (Cannes),
> Philippe (Le Havre), Roussel (Saint-Amand-les-Eaux), Bouamrane
> (Saint-Ouen-sur-Seine), Bertrand (Saint-Quentin). Les deux formes de la date
> sont désormais demandées, et les pages de réponse sont suivies jusqu'au bout.

## Le signalement, et la signature du défaut

La session interface a vu la mairie de Cannes durer six mois sur la frise de
David Lisnard — mars à septembre 2026 — au lieu de six ans. Le corpus ne portait
que ses trois mandats en cours ; le brut aussi : la perte était à la collecte.

La mesure sur les 32 candidats déclarés a donné la signature : les **quatre**
mandats clos que le corpus portait appartenaient tous à des candidats nés **après
1980** (Verdier, Tondelier, Attal, Brun). Aucun candidat né avant n'en avait un.

## La cause, relevée à la source

`tabular-api.data.gouv.fr`, 16/09/2026 :

| Personne | Née | Date publiée par les sortants |
| --- | --- | --- |
| David Lisnard | 1969-02-02 | **2069**-02-02 |
| Édouard Philippe | 1970-11-28 | **2070**-11-28 |
| Gabriel Attal | 1989-03-16 | 1989-03-16 |

La décision de collecte (`collecte-mandats-locaux-rne-922.md`) avait vu que ce
fichier écrivait l'année sur deux chiffres (« 28/06/20 ») ; la conversion en ISO
a placé les années basses au XXIᵉ siècle. Le répertoire en cours, lui, est
correct : les mandats en cours arrivaient bien.

## Décision

**Deux formes de la date, toujours.** La date réelle et la même un siècle plus
tard. Le seuil de bascule n'est **pas deviné** — 1969 est décalé, 1989 ne l'est
pas, et rien ne publie la frontière. Aucun élu ne peut être né après 2050, donc
la forme décalée ne peut désigner qu'une date corrompue ; et `concerne()` vérifie
le nom et le prénom sur chaque ligne, sous les deux formes.

**Le jour où le producteur corrige son fichier**, la forme décalée ne rend plus
rien et la forme exacte prend le relais. Rien à retirer, rien à reconfigurer.

**Toutes les pages.** Le module ne lisait que la première page de 50 lignes.
Mesuré le même jour : 49 élus sortants partagent une même date de naissance.
Aucun candidat n'était encore perdu ainsi, mais le premier le serait en silence.
`links.next` est suivi, jusqu'à `PAGES_MAX = 20` pour qu'un serveur défaillant
n'emballe pas la boucle.

## Vérifié contre la source, de bout en bout

Le module corrigé, exécuté sur l'API réelle :

| Candidat | Avant | Après |
| --- | --- | --- |
| David Lisnard | 3 mandats, aucun clos | **4**, dont Cannes 2020-05-18 clos |
| Édouard Philippe | 2 | **3**, dont Le Havre 2020-06-28 clos |
| Xavier Bertrand | 3 | **4**, dont Saint-Quentin 2020-05-18 clos |
| Gabriel Attal (témoin) | 2, dont Vanves clos | **2** — inchangé |

Sur les 24 candidats déclarés interrogeables par date, la forme décalée rend
exactement **5** mandats clos, et la forme exacte les **4** déjà publiés.

## Pourquoi les tests ne l'avaient pas vu

Le faux serveur de `test_rne_opendata_922.py` **ignore le filtre de la requête** :
il rend les mêmes lignes quelle que soit la date demandée. Il décrivait l'API
comme le code l'imaginait (#726), et aucune erreur de filtrage ne pouvait s'y
voir. Les nouveaux tests utilisent un faux serveur qui applique le filtre
`__exact` et la pagination comme le vrai, sur les lignes relevées à la source.

**La mesure de la décision de collecte était juste, et le code qui l'a suivie ne
la reproduisait plus.** Elle annonçait « Lisnard : 4 mandats, dont un clos » ;
le corpus en a publié 3. Une vérification faite une fois, à la main, ne protège
pas le code qui vient après — un test sur un serveur fidèle, si.

## Ce que cela coûte, et ce que cela demande

Les interrogations par date doublent : ~24 requêtes par candidat au lieu de ~13,
sur une API conçue pour cela. Les mandats retrouvés sont des **ajouts** : la
fusion additive les accepte au prochain run, sans retrait ni perte déclarée.
