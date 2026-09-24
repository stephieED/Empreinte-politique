<a id="part-d-application-non-publiable-1029"></a>

# La part d'application ne se publie pas (#1029) (2026-09-24)

`2026-09-24`

> **En bref** — La fiche de gouvernement devait mettre en regard, par matière, la part des décrets qui **appliquent** une loi et celle qui n'en déclare aucune — « ce que le Parlement a fait faire » contre « ce que le gouvernement a pris seul ». Mesuré le 24/09/2026 sur les **31 199 décrets numérotés** du fonds : la part « applique » tombe de **42 % en 2012 à 0 % depuis 2024**, pendant que la part « cite » monte. Retard de qualification chez Légifrance et changement de pratique d'enregistrement se superposent, et **nos données ne savent pas les séparer** : une telle figure comparerait la chaîne de publication du Journal officiel, pas l'action publique. Écarté. Ce qui reste publiable, c'est **ce que les actes font** — volume, nature, ministère — sur la fenêtre d'un gouvernement, et la mise en regard des deux répartitions **par matière**, chacune en part de son propre total.

## Le contexte

`docs/decisions/actes-reglementaires-du-journal-officiel-1029.md` a versé au pivot les décrets,
arrêtés et ordonnances depuis 2007, et #1108 a publié la jointure : pour chaque acte, les lois
qu'il **applique** et celles qu'il **cite** (`liens_lois`). La source distingue les deux, et un
décret qui cite une loi en visa n'en est pas un décret d'application (§2 règle 2).

La figure envisagée découlait naturellement de cette distinction : par matière, la part des actes
qui appliquent une loi, en regard de celle qui n'en déclare aucune.

## La mesure qui l'écarte

Décrets **numérotés** — la population à nommer, 31 199 sur 76 677 : les 45 478 décrets sans numéro
sont des nominations et des mutations, et les compter ferait tomber la part « applique » à 9 %
pour une raison qui n'a rien à voir avec le sujet.

| Année de publication | Décrets numérotés | applique | cite | aucun lien déclaré |
| --- | ---: | ---: | ---: | ---: |
| 2012 | 1 474 | **42 %** | 17 % | 41 % |
| 2016 | 1 860 | 26 % | 34 % | 40 % |
| 2020 | 1 681 | **4 %** | 47 % | 50 % |
| 2023 | 1 345 | 1 % | 40 % | 59 % |
| 2024 | 1 227 | **0 %** | 43 % | 57 % |
| 2026 | 848 | **0 %** | 39 % | 61 % |

Deux effets se superposent, et c'est ce qui rend la figure impossible :

- **un retard de qualification**, déjà documenté côté lois — aucune loi promulguée depuis 2024 ne
  porte de lien `APPLICATION`, alors qu'une loi de 2024 est citée par un acte aussi souvent qu'une
  loi de 2023 (`docs/sources/jorf-dila.md`) ;
- **un changement de pratique** : la chute commence bien avant 2024, et « cite » monte exactement
  pendant que « applique » descend. Une part de ce qui était enregistré comme application l'est
  désormais comme visa.

**Rien dans les données ne permet de dire lequel des deux on mesure.** Une figure par gouvernement
sortirait pleine sur Borne ou Castex et vide sur Lecornu II — et un lecteur y lirait un fait
politique là où il n'y a qu'un état de la chaîne éditoriale de Légifrance.

## La décision

- **Aucune figure publiée ne repose sur la part d'application**, ni sur son complément « sans lien
  déclaré ». La règle du module tient toujours et s'applique ici : un acte sans lien n'est **pas**
  un acte pris sans loi.
- **Ce qui reste publiable** sur la fenêtre d'un gouvernement : ce que les actes **sont** — leur
  nombre, leur nature, leur ministère — et, par matière, **deux répartitions mises en regard**,
  chacune en part de son propre total (textes promulgués d'un côté, actes de l'autre). Aucune
  division de l'un par l'autre, aucune échelle commune entre 49 lois et 18 605 actes.
- **La mesure se remesure, elle ne se fige pas** : le trou se referme par l'arrière, et tout
  chiffre de couverture porte la date où il a été pris. Celui-ci est du 24/09/2026.

## L'alternative écartée

**Fusionner « applique » et « cite » en « porte un lien vers une loi »**, pour retrouver une
grandeur stable. Elle l'est un peu plus — 43 % en 2012, 60 % en 2016, 39 % en 2026 — mais elle
dérive encore, et surtout elle met dans le même compte un décret d'application et un acte qui
cite une loi en visa. C'est exactement la distinction que la source prend la peine de publier et
que §2 règle 2 demande de garder.

**Restreindre la figure aux années où la qualification est stable** (avant 2016). Écarté : aucun
gouvernement de la période couverte par le site n'y est.
