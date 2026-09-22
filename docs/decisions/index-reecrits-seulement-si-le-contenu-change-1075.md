<a id="index-reecrits-seulement-si-le-contenu-change-1075"></a>
# Un index partagé ne se réécrit que si son contenu change (#1075) (2026-09-22)

`2026-09-22`

> **En bref** — 13 des 18 fichiers de `pivot_data/` hors profils que committait un run ne changeaient que par `genere_le`, dont `amendements/15.json` (70 Mo, législature close). Un index s'écrit désormais par `json_io.ecrire_index_json`, qui n'écrit rien quand le contenu est identique : `genere_le` date le dernier changement réel.

## Constat

Soulevé par la propriétaire le 22/09/2026 : « la leg est finie donc
théoriquement, ce fichier n'est pas censé grossir ». Il ne grossissait pas —
72 943 843 octets sur les huit derniers commits qui le touchent —, mais il était
réécrit à chaque run. Entre les deux runs du 21/09, une seule valeur change :
`genere_le`.

Sur le commit du run `35648745220` (`034ea2926` côté privé), les 18 fichiers de
`pivot_data/` modifiés hors profils :

| Seul `genere_le` change (13) | Contenu changé (5) |
| --- | --- |
| `amendements/{14,15,16,17}.json` et `.cosignatures.json`, `scrutins.json`, `scrutins_dossiers.json`, `scrutins_europeens.json`, `documents_europeens.json`, `commissions_dossiers.json` | `dossiers_europeens.json`, 4 fiches de gouvernement |

Chaque run republiait ainsi plus de 259 Mo d’index (les seuls fichiers d’amendements, mesurés dans `docs/data-architecture.md`) pour une date, avec l'avertissement
GitHub « > 50 Mo » à chaque push, et un diff de commit qui ne disait plus ce que
le run avait changé.

## Décision

1. **`json_io.ecrire_index_json(chemin, document, serialiser)`** sérialise le
   document avec l'ancien `genere_le`, lu dans l'entête du fichier en place
   sans le désérialiser (70 Mo) ; s'il est identique **octet pour octet**, rien
   n'est écrit.
2. **Le même sérialiseur sert à comparer et à écrire** : un changement de format
   compte comme un changement. Chaque écrivain garde le sien (compact, indenté,
   compact avec saut de ligne).
3. Branché sur les sept écrivains : `amendements_index.ecrire`,
   `scrutins_index.ecrire`, `build_scrutins_dossiers`,
   `build_commissions_dossiers`, `documents_europeens`, `scrutins_europeens`,
   `dossiers_europeens`.

Vérifié sur les index publiés : chacun, régénéré avec un autre `genere_le`,
n'est pas réécrit, et le fichier reste octet pour octet celui du dépôt.

## Le critère est le contenu, jamais « législature close »

Réponse à la seconde question de la propriétaire : « sauf s'il y a de nouveaux
profils à collecter ». Un index ne contient pas toute la législature, mais les
amendements **des profils collectés**. Un nouveau candidat déclaré, ou un
membre de groupe, qui a siégé sous la 15e doit faire changer `15.json`. Figer
les législatures closes l'aurait interdit ; comparer le contenu le permet sans
règle de plus.

## Alternatives rejetées

- **Ne plus régénérer les législatures closes** : perd les amendements d'un
  profil nouvellement collecté, et le report `texte_vise` (#696) qui corrige
  des entrées anciennes.
- **Retirer `genere_le`** : le lecteur perd la date du dernier changement, que
  le contrat de #343 garantit déjà pour les profils.
- **Désérialiser l'ancien fichier pour comparer les structures** : plusieurs
  centaines de Mo de mémoire dans `merge-and-pivot` pour `15.json` seul ; la
  comparaison d'octets coûte deux chaînes.
