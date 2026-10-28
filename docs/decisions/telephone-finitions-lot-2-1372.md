<a id="telephone-finitions-lot-2-1372"></a>

# Au téléphone, les finitions sans nouvelle forme ; la ligne d'en-tête du gouvernement dit sa période (#1372, 2026-10-28)

`2026-10-28`

> **En bref** — Lot 2 de #1372 : les composants qui se lisaient mal au téléphone et se corrigent sans changer de forme, relevés par la revue du 28/10/2026 (92 constats, https://claude.ai/artifact/UaZ6kLT56iHox41a33krUT). Pastille « En qualité de… » d'un seul tenant, mention 49.3 lue d'une traite, « 11 235 » au lieu de « 11235 », « XIVe » au lieu de « XIVE », devise sans puce en tête de ligne, articles séparés par un filet, plus de mot seul en dernière ligne, marge de 18 px partout. Et, arbitré le même jour, **la ligne sous le nom d'un gouvernement ne nomme plus son Premier ministre** : elle dit la période, comme celle d'une législature ; le lien vers sa fiche passe dans « Qui le composait ».

## Ce qui change

| Composant | Défaut mesuré (390 px) | Correction | Où |
| --- | --- | --- | --- |
| Pastille « En qualité de député(e) européen(ne) · 1 451 » | En boîte flexible, libellé centré sur deux lignes, « · » seul en haut, nombre décroché | Texte à la suite, aligné à gauche, le nombre collé à son point | `ParolesParPeriode.css` |
| Mention 49.3 | Trois colonnes étroites lues en zigzag | Une phrase continue | `CandidateProfile.css`, `GovernmentProfile.css` |
| Chiffres clés des actes | « 20660 » : l'insécable fine (U+202F) de `toLocaleString` s'effaçait | L'insécable ordinaire, comme `formatNumber` | `ActesDuGouvernement.jsx` |
| Intitulés des maillons d'une lignée | « XIVE » : l'intitulé est en capitales | L'ordinal garde sa minuscule (`.lp-ordinal`) | `LigneeProfile.jsx`, `.css` |
| Devise de l'accueil | Seconde ligne ouverte par une puce (« • 0 score • 0 filtre ») | Deux paires sous 480 px, la puce de tête retirée | `Baseline.css` |
| Articles d'une période | Une carte par article dans la carte de section | Un filet entre articles | `ArticlesDeLaPeriode.css` |
| Fins de ligne | Une année seule (« …sécurité sociale pour / 2026 ») | `text-wrap-style: pretty` sur la fiche | `ExplorerLayout.css` |
| Marges | 16 px sur les fiches de gouvernement et de législature, 20 px au pied du site, 18 ailleurs | 18 px partout | `GovernmentProfile.css`, `PiedDeSite.css` |

## La ligne d'en-tête du gouvernement

« Sébastien Lecornu, Premier ministre · depuis le 11 octobre 2025 · 13 mois » était
« trop centré sur le 1er ministre alors qu'il s'agit du gouvernement » (la propriétaire,
28/10/2026). Deux versions proposées ; **A retenue** :

| | Gouvernement en cours | Gouvernement achevé |
| --- | --- | --- |
| **A, retenue** | Depuis le 11 octobre 2025 · 13 mois | Du 10 janvier 2024 au 5 septembre 2024 · 8 mois |
| B, écartée | … · Premier ministre : Sébastien Lecornu | … · Premier ministre : Gabriel Attal |

La ligne portait **le seul lien** de la fiche vers une fiche de candidat (4 Premiers
ministres sur 17 en ont une, mesuré le 28/10/2026 sur le rendu). Il passe sur le nom
du Premier ministre dans sa carte de « Qui le composait » ; le clic suit le lien sans
déplier les rattachés. Le cas « Premier ministre non publié » disparaît de l'en-tête :
la composition le porte.

## Ce qui n'a pas été corrigé, et pourquoi

- **Les légendes à 8 px du bord** (`.cp-car-cle`, `.odj-leg`) : marge négative voulue,
  pour que le fond de l'entrée choisie dépasse du texte, qui reste sur la marge.
- **Le « i » isolé sous un titre** : J3 (#1373) l'a réglé, et au téléphone le titre a
  disparu (`telephone-titres-bulles-fil-et-cartes-1372`).
- Les composants qui demandent une nouvelle forme — filtres en pastilles, navigation de
  période, tableaux à colonnes, figures dessinées, listes longues — sont au lot 3, avec
  maquette.

## Ce qui n'a pas été vérifié

Au doigt, sur un vrai téléphone : seul le rendu en émulation (Chromium, 390 × 844).
