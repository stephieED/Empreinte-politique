<a id="signature-titres-j3-fond-plein-et-implementation"></a>

# J3 sur fond plein, et son implémentation rétablie (2026-10-28)

`2026-10-28`

> **En bref** — Complète `signature-titres-de-section-j3`, qui laissait ouverte la variante de J3 et l'implémentation. La propriétaire a retenu **le fond plein** le 27/10/2026, à l'essai sur la fiche entière de la XVIIe législature. Le commit qui l'implémentait (`c54a5c3`) a été poussé sur la branche de #1365 deux minutes après la fusion de la PR : il n'a jamais atteint `main`, et le site a gardé le surligné jaune. Ce fichier consigne le choix et rétablit le code, inchangé.

## Ce qui est décidé

**Sur fond plein** : la bande de J3 masque le filigrane du site sous le titre, et le
titre reste net au-dessus des grands arcs du fond. La version transparente, où les
cercles de J3 croisent ces arcs, est écartée.

L'implémentation est celle de `c54a5c3`, reprise sans retouche :

| Fichier | Ce qui change |
| --- | --- |
| `index.css` | Le dessin unique : `--j3-filigrane` et `--j3-bande` |
| `GovernmentProfile.css` | `.gvp-section-titre-rang`, porté aussi par la fiche de législature |
| `CandidateProfile.css` | `.cp-section-tete` |
| `LigneeProfile.css` | `.lp-section-tete` |
| `DESIGN_SYSTEM.md` | §5, la signature des titres de section |

## Ce qui s'est passé

| Heure (Paris), 27/10/2026 | Événement |
| --- | --- |
| 10 h 12 | #1365 fusionnée, sur son seul commit de décision (`f4f6cfc`) |
| 10 h 14 | `c54a5c3`, l'implémentation, poussé sur la branche déjà fusionnée |

GitHub ne refuse pas un commit poussé sur une branche fusionnée, et la PR reste
affichée « fusionnée » sous un titre qui annonce l'implémentation. L'écart s'est vu le
28/10/2026, sur une capture locale de `main` qui montrait encore le surligné.

**À retenir** : avant de pousser sur une branche, vérifier que sa PR est encore
ouverte (`gh pr view <n> --json state`).

## Ce qui n'a pas été vérifié

J3 au téléphone (390 px) : vérifiée sur cette PR, voir son corps.
