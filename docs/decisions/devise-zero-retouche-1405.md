<a id="devise-zero-retouche-1405"></a>

# La devise devient « 100 % sourcé • 0 retouche • 0 score • 0 classement » (#1405) (2026-10-30)

`2026-10-30`

> **En bref** — deux des quatre mentions de la devise arrêtée le 18/09/2026 (`baseline-du-site-1026`) étaient fausses, et le site lui-même les contredisait. « 100 % automatisé » : la liste des candidats déclarés est tenue à la main (la page Sources l'écrit), et les mandats d'avant 2002 sont recopiés de Sycomore dans `config/mandats_anterieurs.json`. « 0 filtre » : le site retient la dernière lecture d'un texte, les seuls votes sur un texte entier, et un texte n'apparaît qu'une fois examiné, ce que /methodologie explique. La propriétaire a gardé la forme (quatre tuiles, un chiffre en grand) et retenu, le 30/10/2026, **« 100 % sourcé • 0 retouche • 0 score • 0 classement »**. Les deux places, la définition unique dans `Baseline.jsx` et l'espace insécable sont inchangés.

## Le contexte

Un lecteur du fil r/developpeurs (30/10/2026) disait ne pas faire confiance à
un site inconnu « qui en plus a des tournures de LLM ». Deux relectures
extérieures (GPT, Gemini) ont relevé, entre autres, « 100 % automatisé » comme
une affirmation que le site ne tient pas.

La PR #1405, ouverte par Copilot, remplaçait les tuiles par deux phrases :
« Chaque fait renvoie à sa source • Aucune note, aucun classement ». Écartée
par la propriétaire : juste, mais sans force (« ce n'est pas parce qu'un texte
est juste qu'il fonctionne »). En `nowrap`, elle faisait aussi déborder
l'accueil à 511 px de large sur un écran de 360 et de 390 px.

## La décision

| Mention | Ce qu'elle engage |
| --- | --- |
| **100 % sourcé** | règle 2 : chaque fait porte le lien de sa source primaire |
| **0 retouche** | aucun fait n'est modifié une fois lu à la source. Un rapprochement relu par une personne (l'identité d'un candidat) relie deux fiches, il ne change pas un fait ; une ligne de Sycomore recopie la source et la cite |
| **0 score** | règle 1 : ni note, ni rang |
| **0 classement** | règle 1, et la règle d'écriture « entre groupes, rien qui se lise comme un classement » |

« 0 retouche » garde l'idée que la propriétaire voulait conserver de
« automatisé » : personne ne réécrit les données.

## Alternatives écartées

| Forme | Raison |
| --- | --- |
| « Chaque fait renvoie à sa source • Aucune note, aucun classement » (Copilot) | juste, mais ne se retient pas ; débordait au téléphone |
| « 100 % sourcé • 0 score • 0 classement » (trois tuiles) | perd l'idée qu'on ne retouche pas les données |
| « … • 0 avis » | plus vague que « classement » |

## Ce qui n'a pas été vérifié

Que « 0 retouche » tienne pour chaque table de `config/` : les groupes et leurs
filiations y sont décidés par une personne, mais ce sont des rattachements,
pas des faits modifiés. À relire si une table de `config/` venait à corriger
une valeur publiée par une source.
