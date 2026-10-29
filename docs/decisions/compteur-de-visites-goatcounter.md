<a id="compteur-de-visites-goatcounter"></a>

# Le compteur de visites : GoatCounter, sans cookie (2026-10-29)

`2026-10-29`

> **En bref** — Le site compte ses visites avec GoatCounter, choisi par la propriétaire le 29/10/2026 : sans cookie, sans donnée personnelle (des totaux seulement), hébergé chez Hetzner en Finlande et en Allemagne, gratuit pour un site non commercial. C'est le premier script tiers exécuté chez le lecteur, ce que la décision `nous-soutenir-don-par-lien-1033` avait évité pour Ko-fi. Les mentions légales le disent dans une section « Mesure d'audience », texte arrêté par la propriétaire.

## Le problème

La propriétaire veut suivre le nombre de visites. Le site est servi par GitHub Pages, qui ne publie aucune statistique de visite : sans script, rien ne se mesure.

## La décision

| Outil | Retenu ou écarté | Raison |
| --- | --- | --- |
| **GoatCounter** | retenu | gratuit pour un site non commercial, code ouvert, aucun cookie pour compter, aucune adresse IP ni visite individuelle conservée, hébergé en Finlande et en Allemagne (goatcounter.com, pages « privacy » et « gdpr », lues le 29/10/2026) |
| Plausible | écarté | équivalent, mais payant (environ 9 €/mois) |
| Cloudflare Web Analytics | écarté | entreprise américaine |
| Google Analytics | écarté | cookies et bandeau de consentement, contraire à l'esprit du site |

**Ce que la décision Ko-fi évitait, et pourquoi on y revient.** Le 19/10/2026, le widget Ko-fi a été écarté parce que « le site cesserait d'être le seul à s'exécuter chez le lecteur ». Le compteur est ce script tiers, assumé : sans cookie et sans donnée personnelle, il ne demande ni bandeau ni consentement, d'après son éditeur. Ce point n'a pas été confirmé auprès de la CNIL.

## Ce qui est fait

- `index.html` porte le script : il compte la page d'arrivée.
- `CompteurDeVisites.jsx` compte chaque page suivante, puisque l'application change de page sans recharger. Une adresse égale à la dernière comptée ne l'est pas deux fois. Sans script (bloqueur), rien ne se passe.
- Les articles et leur index le portent dans leur pied, écrit par `scripts/chrome-instantane.mjs` (`COMPTEUR`).
- GoatCounter ignore de lui-même les visites depuis `localhost`.
- `tests/test_compteur_de_visites.py` tient la même adresse partout, le comptage des changements de page et la présence dans chaque article.

Vérifié dans Chromium, envois interceptés et annulés pour ne pas fausser les chiffres : arrivée, changement de page, retour arrière et article comptent chacun une fois.

## Ce qui n'est pas vérifié

- L'avis de la CNIL sur l'absence de bandeau.
- Le comptage réel sur le site publié, une fois la PR fusionnée et déployée : à lire dans le tableau de bord `https://empreinte-politique.goatcounter.com`.
