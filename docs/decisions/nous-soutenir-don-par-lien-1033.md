<a id="nous-soutenir-don-par-lien-1033"></a>

# La page /nous-soutenir : le don par un lien vers Ko-fi, sans rien charger (#1033) (2026-10-19)

`2026-10-19`

> **En bref** — le site ouvre une page `/nous-soutenir` à trois leviers : le don, le code, le partage. Arbitré le 19/10/2026 : le don passe par **Ko-fi**, branché sur **Stripe**, en **simple lien sortant**. Rien de Ko-fi n'est chargé sur le site, ni script ni cadre : il ne pose donc aucun cookie, et les mentions légales n'ont pas de section « cookies et tiers » à ouvrir. La barre d'objectif de Ko-fi reste sur Ko-fi pour la même raison. La propriétaire voulait une solution **sans inscription du donateur** : Ko-fi et Buy Me a Coffee l'offrent, Liberapay, GitHub Sponsors et sans doute Open Collective ne l'offrent pas. Ko-fi a été préféré parce qu'il ne prélève rien sur un don ponctuel et que l'argent arrive directement sur le compte Stripe, sans solde gardé par la plateforme. **Écartés** : Buy Me a Coffee (5 % prélevés, des soldes retenus rapportés), Liberapay (compte exigé du donateur), Open Collective Europe (8 % plus une participation proposée au donateur), un widget embarqué, et l'affichage sur le site d'un total des dons sur 30 jours.

## Le contexte

L'issue #1033 demandait un bouton ou un widget vers une plateforme de micro-don
(Buy Me a Coffee, Ko-fi), un lien vers le dépôt et des boutons de partage. Elle
laissait ouvertes trois questions : un lien ou un widget ; la cohérence de la
mention fiscale avec les mentions légales (« non professionnel et non
commercial ») ; et la phrase de `/a-propos`, qui disait « aucun financement
extérieur ».

## Les plateformes comparées le 19/10/2026

| Plateforme | Don sans compte | Prélèvement sur un don ponctuel | Frais de paiement |
| --- | --- | --- | --- |
| **Ko-fi** | Oui, en invité (aide officielle) | 0 % | Stripe ou PayPal, ~3 % |
| Buy Me a Coffee | Oui, pour un don ponctuel (aide officielle) | 5 % | Stripe, ~2,9 % + 0,30 $ |
| Liberapay | Non, selon un témoignage d'utilisateur non vérifié sur le site | 0 % | 3 à 5 % |
| Open Collective Europe | Non trouvé | 8 %, plus ~15 % proposés au donateur | en plus |
| GitHub Sponsors | Non, compte GitHub exigé | — | — |

Les plaintes rapportées sur Ko-fi tiennent surtout aux retenues de **PayPal**
sur un compte neuf, jusqu'à 21 jours. Branché sur Stripe, Ko-fi ne garde jamais
l'argent. Celles rapportées sur Buy Me a Coffee portent sur des soldes retenus
par la plateforme elle-même. Reddit n'a pas pu être lu : il bloque l'outil de
recherche de l'agent.

## La décision

- **Ko-fi, branché sur Stripe, en lien sortant** (`KOFI` dans `SoutenirPage.jsx`).
- **La forme A**, retenue sur maquette parmi trois : le bandeau d'encre de
  `/a-propos`, avec le don dedans. C'est le seul fond où le jaune signal peut
  porter un bouton (16,01:1 ; 1,05:1 sur fond clair).
- **Le partage** passe par les adresses nues de LinkedIn et de X, sans leur
  SDK, et ne porte que l'adresse du site (§2 règle 1).
- **La mention de transparence** est celle de la propriétaire, **sans** sa
  parenthèse « (déclarées en BNC non professionnels) » : aucune déclaration
  n'avait encore eu lieu, et le lecteur n'en a pas besoin pour donner.
- **`/a-propos`** dit désormais « aucun financement hors dons sur le site », mots
  de la propriétaire, à la place de « aucun financement extérieur ».

## Les alternatives écartées

- **Un widget Ko-fi** : un script tiers, des cookies, et une section des
  mentions légales à créer. Le site cesserait d'être le seul à s'exécuter chez
  le lecteur.
- **Le total des dons des 30 derniers jours, affiché sur le site** : proposé
  par la propriétaire pour la transparence, faisable par une saisie mensuelle à
  la main ou par une tâche quotidienne lisant Stripe avec une clé en lecture
  seule. Elle a préféré la barre d'objectif de Ko-fi, qui existe déjà et reste
  sur Ko-fi.
- **Les boutons de partage sur les fiches** : hors de ce lot, la question reste
  ouverte sur #1033.
