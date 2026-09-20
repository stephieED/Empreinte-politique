# Le script pose `decline` quand la source nomme la cause (#763)

`2026-09-07`

> **En bref** — trois lots **consommaient** `decline` (périmètre de collecte #760, masquage de fiche #761, rapport #753) et **aucun ne le posait** : les deux valeurs du fichier avaient été écrites à la main, soit trois consommateurs automatiques d'une valeur que seule une main pouvait produire ; simulation à l'appui — Wauquiez remis à `declare`, relance : signalé, statut inchangé, **toujours dans le périmètre** ; le script lit désormais les **deux sections qui nomment la cause** (« Candidatures retirées », « Candidats pressentis ayant décliné » — **26 personnes** mesurées le 07/09/2026) et pose `decline` sur les entrées qu'elles nomment ; **la frontière ne bouge pas d'un pouce** : « figure sous *ayant décliné* » est un **fait lu** et s'écrit, « ne figure plus parmi les déclarés » est une **absence** qui reste signalée sans rien changer — et c'est cette seconde moitié, celle qu'on aurait envie de sacrifier, qui empêche qu'un titre de section renommé décline tout le monde d'un coup ; trois garde-fous : on ne **crée** jamais une entrée depuis une section de sortie (Autain y figure et n'est pas chez nous), **`officiel` ne bascule pas** (il viendra du Conseil constitutionnel, et un article encyclopédique ne renverse pas un acte publié au JO), et **idempotence** ; une sortie nommée part en `::notice::` et non en `::warning::` — le warning reste pour ce qui demande une relecture —, et elle sort du bloc « à relire », que le rapport annonçait **faux** avant correction (« aucune section de sortie ne les nomme » pour les deux que les sections nommaient) ; la note cite le **titre** de la section à la lettre, pas sa paraphrase, avec l'état d'avant, la date et le lien ; **prix assumé** : une fiche disparaît du site sans qu'un humain l'ait décidé — symétrie de l'entrée automatique de #757, arbitrée séparément parce qu'ajouter une fiche se remarque moins que d'en retirer une ; un test de #753 a dû être **restreint** plutôt que supprimé, son invariant ne valant plus que pour les sorties sans cause nommée. 14 tests neufs, suite complète à 4 001, 0 échec.

## Contexte

Trois lots consommaient `statut: decline` :

| Maillon | État |
| --- | --- |
| Ajouter un déclaré, fabriquer son slug, écrire sa correspondance (#757) | automatique |
| Sortir un `decline` du périmètre de collecte (#760) | automatique |
| Masquer sa fiche dans l'interface (#761) | automatique |
| **Poser `decline` quand quelqu'un renonce** | **à la main** |

Le seul statut que le script écrivait était `declare`, pour une entrée neuve.
Les deux `decline` du fichier avaient été posés à la main.

Simulation faite le 07/09/2026 — Laurent Wauquiez remis à `declare` dans une
copie, script relancé :

```
[ENTRÉES QUI NE SONT PLUS DÉCLARÉES — signalées, jamais modifiées]
  ? Laurent Wauquiez (statut: declare, slug: laurent-wauquiez)
→ après passage : statut = declare · dans le périmètre = True
```

Signalé, et rien ne bouge. Un candidat qui renonce serait donc collecté et
publié jusqu'à ce qu'une main ouvre le fichier : **trois consommateurs
automatiques d'une valeur que seule une main pouvait produire**.

## Décision

Le script lit les **deux sections qui nomment la cause** — « Candidatures
retirées » et « Candidats pressentis ayant décliné » — et pose `decline` sur les
entrées qu'elles nomment. Mesuré le 07/09/2026 : **26 personnes** dans ces
sections (2 et 24), dont nos deux.

## Ce qui autorise l'écriture, et ce qui ne l'autorise pas

C'est la frontière du lot, et elle ne bouge pas d'un pouce par rapport à #753 :

- **« figure sous *Candidats pressentis ayant décliné* » est un fait lu** — il
  s'écrit. C'est exactement le standard sur lequel les deux `decline` avaient
  été posés à la main ;
- **« ne figure plus parmi les déclarés » est une absence** — elle ne distingue
  pas un retrait d'un déplacement de section ni d'un renommage. Elle reste
  signalée, et rien ne bouge (§2 règle 5).

La seconde moitié est celle qu'on aurait envie de sacrifier, et c'est celle qui
protège : une refonte de l'article, un titre de section modifié, et la première
règle sans la seconde déclinerait tout le monde d'un coup.

## Trois garde-fous

1. **On ne crée jamais une entrée depuis une section de sortie.** Publier
   quelqu'un pour dire qu'il renonce serait absurde ; seules les entrées déjà
   présentes transitionnent. Clémentine Autain figure dans les retirées et pas
   dans notre fichier : elle ne produit rien.
2. **`officiel` ne bascule pas.** Il viendra de la décision du Conseil
   constitutionnel, seule autorité en la matière, et un article encyclopédique
   ne renverse pas un acte publié au Journal officiel. Une candidature
   officielle qui se retire se corrigera à la main, sur sa source.
3. **Idempotence.** Une entrée déjà `decline` n'est pas réécrite, sinon chaque
   run ferait bouger le fichier sans rien dire de neuf — le défaut que #715 a
   nommé sur `genere_le`.

## Une sortie nommée est un fait, pas une anomalie

Elle part en `::notice::` (`CANDIDATS_SORTIE_NOMMEE`), pas en `::warning::`. Le
`warning` reste pour ce qui demande une relecture : une entrée qui disparaît des
déclarés **sans** qu'aucune section de sortie ne la nomme.

Et une entrée que la source nomme ne figure plus dans le bloc « à relire » du
rapport, qu'elle vienne de transitionner ou qu'elle soit déjà à jour — l'y
laisser demandait un travail déjà fait. Le rapport le disait faux avant
correction : il annonçait « aucune section de sortie ne les nomme » pour les
deux entrées que les sections nommaient précisément.

## La note cite la section à la lettre

`note_de_sortie` écrit le **titre** de la section, pas sa paraphrase, plus
l'état d'avant, la date, et le lien vers la personne :

> Candidature déclinée : figure sous « Candidats pressentis ayant décliné » de
> l'article des candidatures. Statut passé de declare à decline le 2026-09-07
> par src/fetch_candidats_declares.py (#763). Entrée conservée : son slug est
> publié. Source : https://fr.wikipedia.org/wiki/Laurent_Wauquiez

Le titre est ce qu'une relectrice peut retrouver dans l'article, mot pour mot.
Une paraphrase l'obligerait à deviner ce que le script avait lu.

## Le prix

**Une fiche disparaît du site sans qu'un humain l'ait décidé** : #760 la sort du
périmètre de collecte, #761 la masque. C'est la symétrie de l'entrée
automatique arbitrée en #757, et elle n'est pas neutre — ajouter une fiche se
remarque moins que d'en retirer une.

Arbitrage rendu le 07/09/2026, après que la question a été posée séparément :
l'entrée automatique et la sortie automatique sont deux décisions, pas une.

## Ce que la décision ne fait pas

**Dépublier le profil.** `decline` retire la fiche de l'interface et la collecte
du périmètre ; le profil reste dans `pivot_data/`, et la personne reste membre
de son groupe (#760, #761).

**Les autres sections.** « Candidats pressentis » n'est pas une section de
sortie : y figurer ne dit pas qu'on a renoncé, mais qu'on n'a pas encore
déclaré. Le script ne pose donc jamais `pressenti`, et une entrée qui passerait
de « déclaré » à « pressenti » dans l'article resterait signalée sans être
touchée.

## Alternative écartée

**Poser `decline` sur toute disparition de la section des déclarés.** C'est le
geste simple, et il transforme chaque refonte de l'article en purge : un titre
de section renommé, et les 30 entrées deviennent `decline` en un run, avec les
fiches masquées dans la foulée. La cause nommée est ce qui borne le dégât d'une
source qui bouge.
