<a id="surligne-du-mot-recherche-garde"></a>

# Le surligné jaune reste sur le mot recherché, quand il quitte les titres de section (2026-10-27)

`2026-10-27`

> **En bref** — Complète `signature-titres-de-section-j3`. Les titres de section ont perdu leur surligné jaune, qui rappelait la charte d'un parti. Le même geste marque aussi le mot tapé dans « Chercher sur cette fiche », dans les verbatims et l'étiquette du filtre (`.xd-mot`, `.pp-mot`, `.cp-filtre-etiquette mark`, `.cp-filtre-mot`). La propriétaire l'a tranché le 27/10/2026 : « on garde le surligné pour les mots », et de même pour le nom du rang ouvert d'une lignée. Ce n'est plus une signature de titre mais une marque de sélection, l'usage fonctionnel du jaune dans la charte.

## Ce qui est décidé

| Usage du surligné | Fichier | Sort |
| --- | --- | --- |
| Titres de section | `GovernmentProfile.css`, `CandidateProfile.css`, `LigneeProfile.css` | Retiré, remplacé par J3 (`signature-titres-de-section-j3`) |
| Mot recherché dans un extrait de débat | `ExtraitsDuDebat.css` (`.xd-mot`) | **Gardé** |
| Mot recherché dans un verbatim de prise de parole | `ParolesParPeriode.css` (`.pp-mot`) | **Gardé** |
| Mot recherché dans l'étiquette du filtre et la barre | `Recherche.css` (`.cp-filtre-etiquette mark`, `.cp-filtre-mot`) | **Gardé** |
| Nom du rang ouvert d'une lignée | `LigneeProfile.css` (`.lp-rang-nom`) | **Gardé** (« oui », 27/10/2026) |

## Pourquoi c'est cohérent

La charte réserve le jaune à la sélection, à l'action et à la source (`DESIGN_SYSTEM.md`
§2). Sur un titre, le surligné était décoratif et répété à chaque section : c'est ce
qui le rapprochait d'une charte de parti. Sur un mot recherché, il ne paraît que
quand le lecteur a tapé quelque chose, et il dit « voici ce que vous cherchez ».
