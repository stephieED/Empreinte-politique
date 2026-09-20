<a id="notifications-de-suivi"></a>
# Suivre un candidat ou un groupe sans compte, sans donnée personnelle et sans modérer personne (2026-09-13)

`2026-09-13`

> **En bref** — idée **identifiée, pas priorisée**, et instruite assez pour ne pas être re-litigée. La piste retenue est un **flux RSS/Atom par candidat ou par groupe**, généré automatiquement en sortie du pivot à partir du **diff entre deux régénérations** : zéro gestion de compte, zéro donnée personnelle, zéro modération de contenu tiers — les trois coûts qui rendraient un système de notification incompatible avec un projet solo à faible disponibilité. La diffusion croisée est envisagée sur **LinkedIn** (pages vitrine, une par groupe possible, publication **manuelle** d'abord — l'API de publication automatisée demande une validation LinkedIn qui n'est pas garantie) et sur **X** (pas d'équivalent structurel aux pages vitrine ; API payante à l'usage depuis 2026, viable en volume faible, implique un compte développeur). **Reddit : pas de subreddit propre**, et le refus a une raison de responsabilité, pas de goût. Constats de la propriétaire, **non re-vérifiés par l'agent** : les conditions d'API et les règles de plateforme sont des faits externes qui bougent.

## 1. Pourquoi le flux, et pas une liste de diffusion

Un abonnement par courriel ou une notification applicative suppose trois choses que ce projet ne peut pas tenir : **des comptes à gérer**, **des adresses à conserver** — donc de la donnée personnelle, avec ce que ça emporte — et **une disponibilité** pour répondre aux désabonnements et aux incidents.

Le flux RSS/Atom les supprime toutes les trois. L'abonné est chez lui, le site ne sait pas qui il est, et il n'y a rien à modérer.

**Il se dérive de ce que le pipeline produit déjà** : deux régénérations successives de `pivot_data/` se comparent, et la comparaison est précisément le travail que `audit_diff_profils` fait avant chaque commit. Une entrée de flux par changement publié — un mandat qui commence, un vote ajouté, un texte porté — est une lecture du même diff, pas une collecte de plus.

## 2. Ce qui a été instruit sur les plateformes, et qu'il ne faut pas réinstruire

| Plateforme | Ce qui est possible | Ce qui coince |
| --- | --- | --- |
| **LinkedIn** | Pages vitrine, **une par groupe** si on veut. Publication manuelle dès le premier jour | L'API de publication automatisée demande une **validation LinkedIn**, qui n'est pas garantie. Donc manuel d'abord, automatisation seulement si la validation tombe |
| **X** | API accessible, viable **en volume faible** | Pas d'équivalent structurel aux pages vitrine — un compte par groupe n'a pas le même statut. API **payante à l'usage depuis 2026**, et il faut un compte développeur |
| **Reddit** | Poster sur des subreddits **existants**, manuellement et ponctuellement | **Pas de subreddit propre** (§3). Et **jamais d'automatisation** : la plupart des subreddits interdisent les bots sans autorisation préalable des modérateurs, et sanctionnent l'autopromotion détectée (règle « 9:1 » fréquente). Le risque porte sur **le compte**, pas seulement sur le post |

## 3. Le refus du subreddit propre est un refus de responsabilité

Créer un espace ouvert aux tiers, c'est en devenir modérateur. Un contenu illicite **signalé et non retiré** engage alors la responsabilité de qui tient l'espace — et « non retiré » est le cas normal d'un projet solo à faible disponibilité, pas un accident.

Le refus ne dit donc rien de Reddit comme canal : il dit qu'on ne prend pas une obligation de moyens qu'on ne peut pas tenir. Poster ailleurs, chez des modérateurs qui existent, ne pose pas ce problème.

## 4. Ce que ça n'est pas

Ce n'est pas un chantier ouvert. Rien n'est priorisé, rien n'est daté, et la ligne de `ROADMAP.md` le dit. Ce fichier existe pour que l'instruction ci-dessus — surtout les trois refus du §2 et la raison du §3 — ne soit pas repayée le jour où l'idée remonte.

**À re-vérifier avant toute mise en œuvre** : les conditions d'API de LinkedIn et de X, et les règles de bot des subreddits visés. Elles sont datées du 13/09/2026 et changent sans prévenir.
