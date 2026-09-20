# Trois teintes pour quatre institutions, et la sarcelle réservée au Sénat — 11/09/2026 (#328)

`2026-09-11`

> **En bref** — une seule institution a une couleur officielle réutilisable (l'Union, `#003399`) ; une fois ce bleu pris, le cercle ne loge plus trois autres familles sans parenté, donc le Sénat sort du système de couleurs et la sarcelle `#169E9E` lui est réservée pour le jour où il sera rebranché.

## Ce qui a déclenché la reprise

Le lot institutionnel avait ajouté deux teintes — `--pe: #514f96`, `--senat: #8f4a6d` — en levant la
règle « trois teintes et pas quatre » du DESIGN_SYSTEM sur la foi d'un ΔE mesuré **en CIE76 sur
Lab**. Le validateur de la compétence `dataviz` mesure en **OKLab**, et son verdict est l'inverse :

| Palette | Daltonisme | Vision normale |
| --- | ---: | ---: |
| Le couple d'origine seul (Assemblée + gouvernement) | 12,9 | 15,9 |
| **Les quatre du lot** | **2,8** (Sénat ↔ Assemblée) | **8,7** (PE ↔ Assemblée), seuil 15 |

Sur la frise, qui ne porte aucun texte par décision, un lecteur daltonien ne pouvait pas séparer
les années de Mélenchon au Sénat de ses années à l'Assemblée.

## Ce que les références officielles donnent, et ce qu'elles interdisent

| Institution | Référence | Utilisable |
| --- | --- | --- |
| Union européenne | `#003399`, Pantone Reflex Blue de l'emblème | **oui** |
| Gouvernement | bleu France `#000091` (DSFR) | **non** — « l'usage du *Bleu France* comme marque d'État est réservé par la loi aux services officiels `.gouv.fr` » |
| Sénat | son rouge traditionnel | **non** — c'est le rouge du vote « contre » |
| Assemblée nationale | aucune charte publiée | rien à reprendre |

## La contrainte qui décide

Une teinte n'est pas « distincte » parce que son ΔE passe : deux voisines de 42° se lisent comme
une **famille**, donc comme une hiérarchie entre deux institutions de même rang. En exigeant une
séparation de familles, et une fois retirées celles qui portent déjà un sens — vert « pour »,
rouge « contre », jaune d'emphase — il ne reste que **deux arcs** du cercle : le chaud et le
magenta. Deux arcs ne logent pas trois institutions. **Zéro combinaison** sur les 32 teintes
compatibles avec `#003399` mesurées une par une.

## Décision

Trois teintes, une institution en retrait.

| | Teinte | |
| --- | --- | --- |
| Parlement européen | `#003399` | le bleu de l'emblème |
| Gouvernement | `#9E6F29` | ocre — la famille du bronze d'avant |
| Assemblée nationale | `#803060` | prune |
| Sénat | l'encre des absences, `#9A958D` | pas de teinte propre |

ΔE 10,7 sous protanopie, **21,0** en vision normale, **72°** d'écart minimum : aucune paire ne
peut se lire comme une famille. Le seul contrôle en échec porte sur `#003399` lui-même, plus
sombre que la bande de clarté — c'est la couleur officielle, elle ne se négocie pas.

Le Sénat se désigne de lui-même : sur les deux fiches concernées, il n'a ni vote, ni amendement,
ni intervention — la collecte est hors périmètre (#528) —, et sa colonne est repliée d'entrée.

## Ce qui est réservé pour plus tard

**Le jour où le Sénat est rebranché, il prend la sarcelle `#169E9E`.** Arbitrage rendu le
11/09/2026, consigné ici pour que la teinte ne soit pas prise par autre chose entre-temps. Elle
avait été essayée pour l'Assemblée et écartée : à 42° du bleu de l'Union, elle fabriquait un lien
visuel entre les deux parlements. Au Sénat, ce voisinage ne dit rien de faux.

## Une divergence assumée

`FriseCouverture.css` garde ses trois teintes de **population** — `--pop-cand: #3f5166`,
`--pop-gouv: #8a6b4c`, `--pop-grp: #6f5b7a`. Elles valaient celles de la fiche ; elles ne les
valent plus. Ce ne sont pas les mêmes objets : `/couverture` colorie **de quelle fiche vient un
trait**, la fiche candidat colorie **dans quel hémicycle un acte a eu lieu**. Les aligner
demanderait de refaire la même démonstration sur une autre contrainte, et n'a pas été fait ici.

## Alternative écartée

Quatre familles sans référence officielle — ocre, sarcelle, indigo, prune — qui passent tous les
contrôles à 60° d'écart. Écartée par la propriétaire : l'Union doit porter son bleu, et le prix
d'une quatrième teinte serait une palette plus saturée que la direction artistique.

## Ce que ça change dans la méthode

La couleur ne se juge plus à l'œil : `scripts/validate_palette.js` de la compétence `dataviz`
rend cinq verdicts en une commande. Il ne compare **pas** les palettes entre elles — la vérification
qu'une institution ne se lit pas comme une position de vote reste à faire à la main, et elle a
écarté une famille que le validateur acceptait (un gouvernement en olive à ΔE 1,8 du rouge
« contre » sous protanopie).
