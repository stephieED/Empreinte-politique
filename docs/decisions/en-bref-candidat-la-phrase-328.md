# « En bref » de la fiche candidat : le total en tête, une phrase par rang, un sigle par segment — 11/09/2026 (#328)

`2026-09-11`

> **En bref** — retravaillé en maquette avec la propriétaire (artifact `77a97e12`, copie du rendu réel puis annotations) : dans « Ce que cette personne a engagé, en chiffres », **le nombre d'une cellule devient le TOTAL du rang** — 3 933 interventions au lieu de « 309 sur 3 595 », 36 mandats en commission au lieu de « 16 sur 36 », 2 968 amendements au-dessus de « sur 25 dossiers législatifs » (Mélenchon) — et **la forme « la phrase » remplace les grands chiffres** : le nombre en gras au corps du texte, l'objet à la suite dans la même encre, parce qu'un grand chiffre donnait à 3 933 interventions le poids visuel de 28 textes portés ; **la barre des stades quitte « Textes portés »**, les stades se lisant dans la cascade ; sur la frise du parcours, **un segment parlementaire ne porte que le sigle du groupe et la place dans l'hémicycle** (« FI · opposition ») — plus de nom long, plus de repli sur la fonction, qui répétait la légende ; le sigle se lit dans l'intitulé quand il en a la forme, sinon sur les fiches de groupe du manifeste (« Ensemble pour la République » → EPR), et **ne se fabrique jamais** : un groupe européen ou du Sénat sans sigle publié laisse le segment muet — le sigle européen est collecté mais jeté par la normalisation, #863.

## Ce que la maquette a écarté

| Forme | Pourquoi |
| --- | --- |
| A — le total en gros | juste sur le contenu, insuffisante sur la forme : tous les nombres gardaient la même taille |
| B — A avec une barre de part (16 sur 36) | une barre de part se lit comme un taux |
| C — le registre, nombres alignés à droite | l'aspect « tableau de chiffres » restait |
| « Député(e) » ajouté aux segments | annoté puis remplacé par « sigle et place seulement » |
| Nom long du groupe européen sur le segment | coupé dès que le segment est court ; remplacé par le sigle, à venir (#863) |

## Ce qui reste

Les règles CSS de la barre des stades (`.cp-gc-barre*`, `.cp-gc-stade--*`) restent, sans usage, avec les tests qui les décrivent : les retirer est un nettoyage séparé. Le groupe au Sénat n'est pas affiché — il n'existe que dans l'intitulé du mandat, sans source (#528). Le bloc ne compte toujours pas les amendements et textes européens (Mélenchon : 154 et 4 dans sa fiche).
