<a id="telephone-titres-bulles-fil-et-cartes-1372"></a>

# Au téléphone, les titres s'effacent derrière les onglets, et chaque section est une carte (#1372, 2026-10-28)

`2026-10-28`

> **En bref** — Complète `telephone-une-section-par-ecran-1372`, fusionnée avant ces retouches. Essayé au doigt le 28/10/2026, le glissement a fait apparaître cinq redites ou gênes, arbitrées le jour même sur l'aperçu : le titre de section redisait l'onglet (le « i » passe contre l'onglet courant, forme F2) ; le fil d'Ariane et les cases de période passent au-dessus des onglets, sur toutes les sections ; le nom de la fiche s'efface de la page « En bref » ; **chaque section redevient une carte blanche**, resserrée — A′ les avait retirées, mais textes et figures se lisaient mal sur le motif du fond. Tout cela sous 720 px ; l'ordinateur ne change pas.

## Ce qui est décidé

| Point | Choix | Sa raison, dans ses mots ou mesurée |
| --- | --- | --- |
| Titre de section | Retiré de l'écran, gardé pour les lecteurs d'écran ; le filet numéroté part avec lui | « le titre de section est redondant » avec l'onglet courant |
| Sa bulle | **F2** : un « i » contre l'onglet courant, qui ouvre la bulle sous la rangée, texte repris tel quel | Préférée à F1 (« i » fixe au bout de la rangée) et F3 (bande J3 sans titre) — maquette https://claude.ai/artifact/He5UYxLsUtgBZMgSK6gmAE |
| Fil d'Ariane et cases 6/12 mois | Au-dessus des onglets, visibles sur toutes les sections | « afin qu'ils soient accessibles sur toutes les sections » |
| Nom de la fiche sur « En bref » | Retiré de l'écran (gardé pour les lecteurs d'écran et les moteurs de recherche) | Le fil d'Ariane, juste au-dessus, le dit déjà |
| Fond des sections | **Une carte blanche par section**, qui mord de 8 px sur la marge, 14 px de marge intérieure ; ses cartes intérieures perdent leur cadre | « il s'agit surtout de ne pas avoir nos textes et infographie sur le motif de fond d'écran car on perd bcp en clarté » |

## Les mesures

| Mesure (Mélenchon, 390 px) | Avant A′ | A′ | Maintenant |
| --- | --- | --- | --- |
| Texte depuis le bord | 61 px (médiane) | 18 px | 24 px |
| Texte de section posé sur le motif | non | partout | nulle part ; seuls le fil et l'en-tête de la fiche restent sur le fond |

**Écartée** : rendre son fond à chaque carte de bloc plutôt qu'à la section. Les pastilles « En qualité de… » et les phrases posées entre deux cartes restaient alors sur le motif.

## Un défaut trouvé en route

Choisir « 12 derniers mois » peut retirer une section de la fiche : l'onglet courant
glissait alors sur la section voisine, puisque le composant la suivait par son rang. Il
la suit désormais par son **titre**.

## Comment c'est construit

- La rangée d'onglets est rendue, par un portail, dans un emplacement que
  `GlissementSections` pose dans le `<main>` juste après le bloc du fil ; ce bloc et
  l'emplacement portent `data-glisse-fixe` et ne se masquent jamais.
- La bulle sous l'onglet reprend le contenu de la bulle de l'en-tête (`.ib-bulle`),
  lu dans la page : aucun texte n'est écrit dans le composant. Un lien interne y reste
  une navigation de l'application.
- `styles/telephone.css` porte la carte de section ; la règle d'A′ qui aplatissait les
  cartes s'applique désormais à leurs cartes intérieures.

## Ce qui n'a pas été vérifié

- La bulle F2 n'a été essayée qu'en émulation, pas au doigt.
- Le nom de la fiche n'est plus en grand nulle part au téléphone : un lecteur arrivé
  par un lien partagé le lit dans le fil d'Ariane, en 15 px gras. Signalé, non tranché.
