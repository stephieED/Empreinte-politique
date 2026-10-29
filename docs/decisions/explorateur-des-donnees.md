# Un explorateur local des données, en tableaux reliés (2026-10-29)

`2026-10-29`

> **En bref** — la propriétaire veut naviguer dans `pivot_data/` et `raw_data/` « d'une entrée à l'autre », en tableaux et en arborescence, ce que le JSON brut ne permet pas. `scripts/explorateur.sh` construit une base SQLite (`src/explorateur_donnees.py`, bibliothèque standard seule) et l'ouvre dans Datasette, en local, sur `127.0.0.1`. Chaque liste d'un document devient une table reliée à son parent ; les identifiants connus (`scrutin_id`, `membre_id`, `groupe_id`, `lignee_id`) deviennent des liens ; la table `documents` montre le document entier en arborescence repliable. Lecture seule, base sous `.cache/explorateur/`, reconstruite seulement quand le commit du dossier a changé. Arbitré le 29/10/2026 sur deux essais (« les 2 » : pivot et brut).

## Contexte

Trois formes ont été comparées le 29/10/2026 : VisiData dans le terminal
(écarté : « dans le terminal, ce n'est pas très user friendly »), Datasette dans
le navigateur, une page sur mesure. Deux essais de Datasette, hors dépôt, ont
été faits sur la machine de la propriétaire :

- v1, des tables choisies à la main : 35 Mo, 63 s. Elle a demandé à naviguer
  dans tout le contenu du JSON ;
- v2, l'aplatissement générique : 49 tables, 1,1 Go, 17 min sur `pivot_data`.

Construction réelle par ce module, le 29/10/2026 sur le dossier partagé
(`d4aafdf023`), `pivot_data` **et** `raw_data` : **115 tables (dont 69 du brut),
2,1 Go, 2 min 45**, 1,6 Gio de mémoire au plus. La bibliothèque standard
(`executemany`, journal coupé) va six fois plus vite que `sqlite-utils` pour
deux fois plus de données.

## Décision

1. **Un aplatissement générique**, pas un schéma écrit à la main : un champ
   ajouté au pivot apparaît dans l'explorateur sans toucher au code.
2. **Les liens se posent à la création des tables.** Les ajouter ensuite
   recopie chaque table une fois par lien : la v2 a été arrêtée après plus de
   40 minutes ainsi.
3. **Bibliothèque standard pour construire, Datasette pour afficher**
   (deux pièges du corpus payés en route : des clés portent des guillemets
   doubles, et `raw_data/lois_jorf.json` indexe 8 820 lois dont les valeurs
   sont des listes ; au-delà de 50 clés, un dictionnaire devient une table
   fille). Datasette est installé par la commande dans `.cache/explorateur/venv`
   (`scripts/explorateur/requirements.txt`) : ni la CI ni le pipeline n'en
   dépendent.
4. **Ce qui n'est pas chargé** : les votes et les amendements des membres des
   groupes (`roster_groupe`). Mesuré le 29/10/2026 sur le pivot : 2 515 359
   votes et 11 189 872 entrées d'amendements, contre 32 812 et 191 951 pour les
   43 profils de candidats déclarés. Chaque profil allégé le dit
   (`votes__non_charge`). Le document entier, de même, n'est gardé que pour les
   candidats déclarés et les membres des gouvernements (118 Mo, contre 1,9 Go de
   profils roster).
5. **Une photo, datée par son commit** (`_construction`). La commande ne
   reconstruit que si le commit du dossier a changé ; `--construire` et
   `--sans-reconstruire` forcent l'un ou l'autre. Un fichier de données modifié
   sans commit n'est donc pas vu tant qu'on ne force pas.
6. **Local seulement** : le serveur écoute sur `127.0.0.1`. L'ouvrir sur
   Internet (un tunnel, pour l'usage au téléphone) a été écarté.

## Alternatives écartées

- **VisiData** : rien à coder, mais une interface au clavier.
- **Une page sur mesure** : la plus coûteuse, et une page de plus à entretenir.
- **Charger les votes et amendements des membres des groupes** : une base de
  plusieurs dizaines de Go pour un contenu que les fiches de groupe résument.

## Non vérifié

- La construction répétée après chaque rapatriement : une seule construction
  complète a été mesurée.
- Sur la page d'une seule ligne, Datasette 0.65 affiche la valeur d'un lien
  sans le rendre cliquable ; les tableaux, eux, le rendent.
