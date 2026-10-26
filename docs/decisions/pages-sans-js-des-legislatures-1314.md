<a id="pages-sans-js-des-legislatures-1314"></a>

# Les fiches de législature ont leur page servie, lisible sans JavaScript (#1314) (2026-10-26)

`2026-10-26`

> **En bref** — `/legislatures/<n>` était la seule fiche sans fichier au build : `scripts/pages-par-adresse.mjs` ne connaissait pas les législatures (aucune occurrence, mesuré le 26/10/2026), si bien que l'adresse répondait par le repli `404.html` — la page s'affichait, mais un moteur de recherche lisait une erreur et aucun robot ne lisait de texte (`pages-par-adresse-969`). Chaque législature du manifeste a désormais son fichier, son titre — « XVIe législature (2022-2024) — groupes, textes et commissions », « XVIIe législature (depuis 2024) — … » —, la description commune des fiches, et un texte lisible sans JavaScript : ses bornes et son mode de fin, les gouvernements qui ont gouverné pendant elle, ses groupes dans l'ordre des sièges. Textes arbitrés par la propriétaire le 26/10/2026. Au build du 26/10/2026 : 4 pages, 81 pages publiées en tout.

## Ce que le texte porte, et ce qu'il ne porte pas

| Porte | Ne porte pas |
| --- | --- |
| « Assemblée nationale · du 22/06/2022 au 09/06/2024 · close par la dissolution » | le nombre de députés par groupe, qui demanderait d'écrire sa date |
| les gouvernements, par la règle de la fiche : un gouvernement nommé le dernier jour n'y a pas gouverné | les non-inscrits, qui ne forment pas un groupe |
| les groupes, sous le nom de leur fiche quand le site en a une | aucun compte d'activité (§2 règle 1), comme les autres fiches |

Le nom d'une législature vit dans `src/data/nomsDesLegislatures.js`, module sans
import que la fiche et le script lisent tous deux, comme les adresses par défaut.

## Alternative écartée

**Un balisage Schema.org**, comme les autres fiches : le vocabulaire n'a pas de
type pour une législature, et en forcer un ferait dire au balisage autre chose
que la page.
